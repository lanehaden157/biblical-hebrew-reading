/**
 * Dev-only page: browse any card on demand instead of shuffling through the
 * live queue to find it, plus a diagnostics panel for the state that's
 * otherwise invisible (sync internals, backup keys sitting in storage, what
 * the gist actually has right now).
 *
 * Never linked from index.html or the tab bar -- visited directly by URL.
 * Hard rule 1 still applies (no Hebrew characters in this file); every glyph
 * shown comes from /data at runtime, same as the rest of /app/.
 *
 * Safety property this file is built around: it must be structurally unable
 * to touch real progress, not just "trusted not to". It never imports
 * srs.js (grading lives there) and never calls store.js's update()/
 * resetAll() or sync.js's syncNow()/pushReset()/connect() -- only read-only
 * accessors (load(), sync.status()) and the two decks' pure cardEl/
 * cardBackEl renderers, which take stage/flip state as explicit arguments
 * (see the "stage is an explicit parameter" comments in vocab.js/parse.js)
 * rather than mutating the live review queue.
 */

import { loadDeck, loadParseDeck, loadFunctionWordExamples, loadVocabExamples } from './main.js';
import { cardEl as vocabCardEl, cardBackEl as vocabCardBackEl } from './views/vocab.js';
import { cardEl as parseCardEl } from './views/parse.js';
import { load as loadStore } from './store.js';
import * as theme from './theme.js';
import { status as syncStatus, SYNC_KEY, GIST_FILENAME, API } from './sync.js';

theme.init();

const cardsSection = document.getElementById('section-cards');
const changesSection = document.getElementById('section-changes');
const diagSection = document.getElementById('section-diagnostics');

for (const btn of document.querySelectorAll('.subtab')) {
  btn.addEventListener('click', () => {
    for (const b of document.querySelectorAll('.subtab')) b.classList.toggle('active', b === btn);
    for (const s of document.querySelectorAll('.section')) s.classList.toggle('active', s.id === `section-${btn.dataset.section}`);
  });
}

let vocabDeck = [];
let parseDeck = [];
let functionWordExamples = {};
let vocabExamples = {};
let loadErrors = [];

(async function boot() {
  const results = await Promise.allSettled([
    loadDeck(),
    loadParseDeck(),
    loadFunctionWordExamples(),
    loadVocabExamples(),
  ]);
  if (results[0].status === 'fulfilled') vocabDeck = results[0].value;
  else loadErrors.push(`vocab deck: ${results[0].reason}`);
  if (results[1].status === 'fulfilled') parseDeck = results[1].value;
  else loadErrors.push(`parse deck: ${results[1].reason}`);
  if (results[2].status === 'fulfilled') functionWordExamples = results[2].value;
  else loadErrors.push(`function-word examples: ${results[2].reason}`);
  if (results[3].status === 'fulfilled') vocabExamples = results[3].value;
  else loadErrors.push(`vocab examples: ${results[3].reason}`);

  renderCardsSection();
  renderChangesSection();
  renderDiagnosticsSection();
})();

// ---------- Card browser ----------

let browseSource = 'vocab'; // 'vocab' | 'parse'
let query = '';
let selected = null; // the raw deck entry
let browseStage = 0;
let browseFlipped = false;

function matches(entry, q) {
  if (!q) return true;
  const hay = [entry.transliteration, entry.gloss, entry.lemma_id, entry.id, entry.citation_form]
    .filter(Boolean).join(' ').toLowerCase();
  return hay.includes(q.toLowerCase());
}

function renderCardsSection() {
  cardsSection.textContent = '';

  const sourceRow = document.createElement('div');
  sourceRow.className = 'browse-controls';
  for (const src of ['vocab', 'parse']) {
    const b = document.createElement('button');
    b.className = 'btn' + (browseSource === src ? ' subtab active' : '');
    b.textContent = src === 'vocab' ? 'Vocab deck' : 'Parse deck';
    b.addEventListener('click', () => {
      browseSource = src;
      selected = null;
      renderCardsSection();
    });
    sourceRow.appendChild(b);
  }
  cardsSection.appendChild(sourceRow);

  const input = document.createElement('input');
  input.className = 'text-input';
  input.placeholder = 'Search transliteration, gloss, or id…';
  input.value = query;
  input.addEventListener('input', () => {
    query = input.value;
    renderResults();
  });
  cardsSection.appendChild(input);

  const results = document.createElement('div');
  results.className = 'results';
  results.id = 'browse-results';
  cardsSection.appendChild(results);

  const preview = document.createElement('div');
  preview.id = 'browse-preview';
  cardsSection.appendChild(preview);

  renderResults();
  renderPreview();
}

function renderResults() {
  const results = document.getElementById('browse-results');
  results.textContent = '';
  const deck = browseSource === 'vocab' ? vocabDeck : parseDeck;
  const filtered = deck.filter((e) => matches(e, query)).slice(0, 40);
  if (!filtered.length) {
    const row = document.createElement('div');
    row.className = 'result-row';
    row.textContent = deck.length ? 'No matches.' : 'Loading…';
    results.appendChild(row);
    return;
  }
  for (const entry of filtered) {
    const row = document.createElement('div');
    row.className = 'result-row';
    row.textContent = `${entry.transliteration} — ${entry.gloss}`;
    row.addEventListener('click', () => {
      selected = entry;
      browseStage = 0;
      browseFlipped = false;
      renderPreview();
    });
    results.appendChild(row);
  }
  if (deck.filter((e) => matches(e, query)).length > filtered.length) {
    const more = document.createElement('div');
    more.className = 'result-row';
    more.textContent = 'More matches not shown — narrow the search.';
    results.appendChild(more);
  }
}

function renderPreview() {
  const preview = document.getElementById('browse-preview');
  preview.textContent = '';
  if (!selected) return;

  const wrap = document.createElement('div');
  wrap.className = 'card-preview flip-perspective';

  const item = { entry: selected, card: null };
  const wex = browseSource === 'vocab'
    ? (vocabExamples[selected.lemma_id] || functionWordExamples[selected.lemma_id])
    : null;

  const rerenderPreviewOnly = () => renderPreview();

  const el = browseSource === 'vocab'
    ? (browseFlipped && wex
      ? vocabCardBackEl(item, wex, { onFlipBack: () => { browseFlipped = false; rerenderPreviewOnly(); } })
      : vocabCardEl(item, wex, browseStage, {
        onAdvance: () => { if (browseStage < 2) browseStage++; rerenderPreviewOnly(); },
        onExamples: () => { browseFlipped = true; rerenderPreviewOnly(); },
      }))
    : parseCardEl(item, browseStage, {
      onAdvance: () => { if (browseStage < 2) browseStage++; rerenderPreviewOnly(); },
    });
  wrap.appendChild(el);
  preview.appendChild(wrap);

  const controls = document.createElement('div');
  controls.className = 'stage-controls';
  const resetBtn = document.createElement('button');
  resetBtn.className = 'btn';
  resetBtn.textContent = 'Reset to stage 0';
  resetBtn.addEventListener('click', () => { browseStage = 0; browseFlipped = false; rerenderPreviewOnly(); });
  controls.appendChild(resetBtn);
  preview.appendChild(controls);

  const idLine = document.createElement('p');
  idLine.className = 'row-sub';
  idLine.textContent = `lemma_id: ${selected.lemma_id || selected.id || '(none)'} · stage ${browseStage}${browseFlipped ? ' · flipped' : ''}`;
  preview.appendChild(idLine);
}

// ---------- Recent changes ----------

async function renderChangesSection() {
  changesSection.textContent = '';
  const h = document.createElement('h2');
  h.textContent = 'improvements_log.md';
  changesSection.appendChild(h);

  let text;
  try {
    const res = await fetch(new URL('../improvements_log.md', import.meta.url), { cache: 'no-cache' });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    text = await res.text();
  } catch (e) {
    const p = document.createElement('p');
    p.className = 'note';
    p.textContent = `Could not load improvements_log.md: ${e.message || e}`;
    changesSection.appendChild(p);
    return;
  }

  const lines = text.split('\n').filter((l) => l.trim().startsWith('- ')).reverse();
  const ul = document.createElement('ul');
  ul.className = 'changes-list';
  for (const line of lines) {
    const li = document.createElement('li');
    li.textContent = line.replace(/^-\s*/, '');
    ul.appendChild(li);
  }
  changesSection.appendChild(ul);
}

// ---------- Diagnostics ----------

function diagRow(container, k, v) {
  const row = document.createElement('div');
  row.className = 'diag-row';
  const kEl = document.createElement('span');
  kEl.className = 'k';
  kEl.textContent = k + ': ';
  row.appendChild(kEl);
  row.appendChild(document.createTextNode(String(v)));
  container.appendChild(row);
}

function readSyncStateRaw() {
  try {
    const s = localStorage.getItem(SYNC_KEY);
    return s ? JSON.parse(s) : {};
  } catch {
    return {};
  }
}

function renderDiagnosticsSection() {
  diagSection.textContent = '';

  // Sync
  const syncBlock = document.createElement('div');
  syncBlock.className = 'diag-block';
  syncBlock.appendChild(Object.assign(document.createElement('h2'), { textContent: 'Sync' }));
  const st = syncStatus();
  const raw = readSyncStateRaw();
  diagRow(syncBlock, 'connected', st.connected);
  diagRow(syncBlock, 'gistId', raw.gistId || '(none)');
  diagRow(syncBlock, 'token', raw.token ? 'set (hidden)' : '(none)');
  diagRow(syncBlock, 'lastSyncedAt', st.lastSyncedAt || '(never)');
  diagRow(syncBlock, 'lastError', st.lastError || '(none)');
  diagRow(syncBlock, 'syncing', st.syncing);
  diagRow(syncBlock, 'backoffUntil', raw.backoffUntil
    ? `${new Date(raw.backoffUntil).toISOString()} (${raw.backoffUntil > Date.now() ? 'active' : 'expired'})`
    : '(none)');

  if (raw.token && raw.gistId) {
    const btn = document.createElement('button');
    btn.className = 'btn';
    btn.textContent = 'Peek remote (read-only)';
    const out = document.createElement('div');
    out.className = 'diag-row';
    btn.addEventListener('click', async () => {
      btn.disabled = true;
      out.textContent = 'Fetching…';
      try {
        const res = await fetch(`${API}/gists/${raw.gistId}`, {
          headers: { Authorization: `Bearer ${raw.token}`, Accept: 'application/vnd.github+json' },
        });
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        const gist = await res.json();
        const file = gist.files && gist.files[GIST_FILENAME];
        const remote = file ? JSON.parse(file.content) : null;
        out.textContent = remote
          ? `Remote has ${Object.keys(remote.cards || {}).length} cards (schemaVersion ${remote.schemaVersion}).`
          : 'Gist has no progress file.';
      } catch (e) {
        out.textContent = `Fetch failed: ${e.message || e}`;
      } finally {
        btn.disabled = false;
      }
    });
    syncBlock.appendChild(btn);
    syncBlock.appendChild(out);
  }
  diagSection.appendChild(syncBlock);

  // Local state
  const localBlock = document.createElement('div');
  localBlock.className = 'diag-block';
  localBlock.appendChild(Object.assign(document.createElement('h2'), { textContent: 'Local state' }));
  const s = loadStore();
  const cardCount = Object.keys(s.cards).length;
  const bytes = new Blob([JSON.stringify(s)]).size;
  diagRow(localBlock, 'schemaVersion', s.schemaVersion);
  diagRow(localBlock, 'cards', cardCount);
  diagRow(localBlock, 'stored size', `${(bytes / 1024).toFixed(1)} KB`);
  diagSection.appendChild(localBlock);

  // Backup keys
  const backupBlock = document.createElement('div');
  backupBlock.className = 'diag-block';
  backupBlock.appendChild(Object.assign(document.createElement('h2'), { textContent: 'Backup keys in this browser' }));
  const backupKeys = Object.keys(localStorage).filter((k) => k.startsWith('hebrew:backup:'));
  if (!backupKeys.length) {
    diagRow(backupBlock, '(none)', '');
  } else {
    for (const key of backupKeys) {
      let count = '?';
      try { count = Object.keys(JSON.parse(localStorage.getItem(key)).cards || {}).length; } catch { /* ignore */ }
      diagRow(backupBlock, key, `${count} cards`);
    }
  }
  diagSection.appendChild(backupBlock);

  // Content loaded
  const contentBlock = document.createElement('div');
  contentBlock.className = 'diag-block';
  contentBlock.appendChild(Object.assign(document.createElement('h2'), { textContent: 'Content loaded' }));
  diagRow(contentBlock, 'vocab entries', vocabDeck.length);
  diagRow(contentBlock, 'parse entries', parseDeck.length);
  diagRow(contentBlock, 'function-word lemmas', Object.keys(functionWordExamples).length);
  diagRow(contentBlock, 'vocab-example lemmas', Object.keys(vocabExamples).length);
  if (loadErrors.length) {
    for (const err of loadErrors) diagRow(contentBlock, 'load error', err);
  }
  diagSection.appendChild(contentBlock);

  // Environment
  const envBlock = document.createElement('div');
  envBlock.className = 'diag-block';
  envBlock.appendChild(Object.assign(document.createElement('h2'), { textContent: 'Environment' }));
  diagRow(envBlock, 'online', navigator.onLine);
  diagSection.appendChild(envBlock);
  if (navigator.storage && navigator.storage.estimate) {
    navigator.storage.estimate().then(({ usage, quota }) => {
      diagRow(envBlock, 'storage used', `${((usage || 0) / 1024).toFixed(0)} KB of ${((quota || 0) / 1024 / 1024).toFixed(0)} MB`);
    }).catch(() => {});
  }
}

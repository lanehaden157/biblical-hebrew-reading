/**
 * The vocabulary drill.
 *
 * Three-stage reveal (locked): Hebrew -> transliteration -> gloss. The point is
 * diagnostic. Reading is two skills stacked -- decoding the pointed script, and
 * recalling the meaning -- and a single-stage card collapses them, so a failure
 * never tells you which half broke. Stage 1 lets you check your decoding before
 * the gloss arrives and makes the answer obvious in hindsight.
 *
 * Hard rule 1 applies here: not one Hebrew character appears in this file.
 * Every glyph is read from data/vocab_deck_600.json at runtime.
 * Hard rule 4: transliteration and gloss both always arrive, on every card.
 */

import { update, today, load } from '../store.js';
import { buildQueue, newCard, applyGrade, preview, GRADES } from '../srs.js';
import * as feedback from '../feedback.js';

let queue = [];
let pos = 0;
let stage = 0;
let session = null;
let deferred = 0;

const HINTS = ['tap for the sound', 'tap for the meaning'];

export function reset() {
  queue = [];
  session = null;
}

export function render(root, deck) {
  if (!session) {
    const built = buildQueue(deck);
    queue = built.queue;
    deferred = built.deferred;
    pos = 0;
    stage = 0;
    session = { start: Date.now(), reviewed: 0, again: 0 };
  }

  root.textContent = '';

  if (pos >= queue.length) {
    root.appendChild(doneScreen(deck));
    return;
  }

  const item = queue[pos];
  root.appendChild(headRow(item));
  const card = cardEl(item);
  root.appendChild(card);
  if (stage === 2) root.appendChild(gradeRow(item, root, deck));
}

function headRow(item) {
  const head = document.createElement('div');
  head.className = 'deck-head';

  const left = document.createElement('span');
  left.textContent = item.isNew ? '' : `${queue.length - pos} left`;
  head.appendChild(left);

  const right = document.createElement('span');
  if (item.isNew) {
    const b = document.createElement('span');
    b.className = 'badge';
    b.textContent = 'new word';
    right.appendChild(b);
  }
  head.appendChild(right);
  return head;
}

function cardEl(item) {
  const { entry } = item;
  const el = document.createElement('div');
  el.className = 'card' + (stage === 2 ? ' is-open' : '');
  el.setAttribute('role', 'button');
  el.tabIndex = 0;

  const heb = document.createElement('p');
  heb.className = 'card-heb heb';
  heb.lang = 'he';
  heb.textContent = entry.citation_form;   // from /data, never a literal
  el.appendChild(heb);

  if (stage >= 1) {
    el.appendChild(hr());
    const t = document.createElement('p');
    t.className = 'card-translit';
    t.textContent = entry.transliteration;
    el.appendChild(t);
  }

  if (stage >= 2) {
    const g = document.createElement('p');
    g.className = 'card-gloss';
    g.textContent = entry.gloss;
    el.appendChild(g);

    const m = document.createElement('p');
    m.className = 'card-meta';
    m.textContent = `${entry.pos} · ${entry.frequency.toLocaleString()}× in the Hebrew Bible`;
    el.appendChild(m);
  } else {
    const hint = document.createElement('p');
    hint.className = 'card-hint';
    hint.textContent = HINTS[stage];
    el.appendChild(hint);
  }

  const advance = () => {
    if (stage >= 2) return;
    stage++;
    feedback.tap();
    rerender();
  };
  el.addEventListener('click', advance);
  el.addEventListener('keydown', (e) => {
    if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); advance(); }
  });
  return el;
}

function hr() {
  const r = document.createElement('hr');
  r.className = 'rule';
  return r;
}

function gradeRow(item, root, deck) {
  const wrap = document.createElement('div');
  wrap.className = 'grades';

  // Read live state rather than the queue snapshot: a card missed earlier in
  // this session is re-queued and by then has real scheduling state, so the
  // snapshot would preview it as if it were still brand new.
  const current = load().cards[item.entry.lemma_id] || newCard();
  const intervals = preview(current);

  for (const g of GRADES) {
    const b = document.createElement('button');
    b.className = 'grade';
    b.dataset.g = g.key;
    b.appendChild(document.createTextNode(g.label));
    const small = document.createElement('small');
    small.textContent = intervals[g.key];
    b.appendChild(small);
    b.addEventListener('click', () => grade(item, g.key, deck));
    wrap.appendChild(b);
  }
  return wrap;
}

function grade(item, gradeKey, deck) {
  const id = item.entry.lemma_id;
  const now = new Date();

  update((s) => {
    const existing = s.cards[id];
    const base = existing || { ...newCard(now), introducedOn: today(now) };
    const next = applyGrade(base, gradeKey, now);
    s.cards[id] = { ...next, introducedOn: base.introducedOn || today(now) };
  });

  session.reviewed++;
  if (gradeKey === 'again') {
    session.again++;
    feedback.wrong();
    // Missed cards come back at the end of this session rather than waiting for
    // tomorrow -- that is what the learning steps are for.
    queue.push({ ...item, card: null, isNew: false, repeat: true });
  } else {
    feedback.right();
  }

  pos++;
  stage = 0;
  if (pos >= queue.length) feedback.finish();
  rerender();
}

function doneScreen(deck) {
  const wrap = document.createElement('div');
  wrap.className = 'done';

  const mins = Math.max(1, Math.round((Date.now() - session.start) / 60000));
  const reviewed = session.reviewed;

  // Phase 2 step 4: log real time-per-session so pacing estimates can be
  // corrected against data instead of assumption.
  if (reviewed > 0 && !session.logged) {
    session.logged = true;
    update((s) => {
      s.sessions.push({
        date: new Date().toISOString(),
        ms: Date.now() - session.start,
        reviewed,
        again: session.again,
      });
      if (s.sessions.length > 400) s.sessions = s.sessions.slice(-400);
    });
  }

  const h = document.createElement('h1');
  h.textContent = reviewed > 0 ? 'Done for now' : 'Nothing due';
  wrap.appendChild(h);

  const p = document.createElement('p');
  if (reviewed > 0) {
    p.textContent = `${reviewed} card${reviewed === 1 ? '' : 's'} in about ${mins} minute${mins === 1 ? '' : 's'}.`;
  } else {
    p.textContent = 'Come back later, or add new words in Settings.';
  }
  wrap.appendChild(p);

  if (deferred > 0) {
    const d = document.createElement('p');
    d.textContent = `${deferred} more were held back for another day.`;
    wrap.appendChild(d);
  }

  const again = document.createElement('button');
  again.className = 'grade';
  again.style.marginTop = '22px';
  again.textContent = 'Check for more';
  again.addEventListener('click', () => { session = null; rerender(); });
  wrap.appendChild(again);

  return wrap;
}

let rerender = () => {};
export function setRerender(fn) { rerender = fn; }

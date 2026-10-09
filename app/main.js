import { loadAll, D } from './data.js';
import { load, save, state, replace } from './store.js';
import { h } from './render.js';
import { runSession, sessionInfo } from './session.js';
import { lessonView } from './lessons.js';
import { progressView } from './progress.js';
import { restore } from './report.js';
import { sync, syncInfo, connect, disconnect } from './sync.js';

const root = document.getElementById('app');
const nav = document.getElementById('nav');

function tab(name) {
  nav.querySelectorAll('button').forEach(b => b.classList.toggle('on', b.dataset.t === name));
  nav.hidden = false;
}

// Background sync; if it replaced local progress, redraw whatever tab is showing.
async function bgSync() {
  if (await sync() !== 'pulled' || nav.hidden) return;
  const t = nav.querySelector('.on')?.dataset.t;
  nav.querySelector(`[data-t="${t || 'today'}"]`).click();
}

function todayScreen() {
  tab('today');
  const info = sessionInfo();
  root.replaceChildren(h('div', { class: 'home' },
    h('div', { class: 'kicker' }, `Unit ${info.unit}`),
    h('h1', {}, info.title || ''),
    h('button', { class: 'primary start', onclick: async () => {
      nav.hidden = true;
      try { await runSession(root); } catch (e) { console.error(e); alert('Something broke: ' + e.message); }
      todayScreen();
      bgSync();
    } }, 'Start today'),
    info.unit === 0 ? h('button', { class: 'link', onclick: () => {
      if (confirm('Skip the calibration and start Unit 1?')) { state().unit = 1; save(); todayScreen(); }
    } }, 'I already read pointed text easily: skip to Unit 1') : null));
}

function lessonsScreen() {
  tab('lessons');
  const s = state();
  const list = h('div', {});
  for (const u of D.units) {
    list.append(h('h3', {}, `Unit ${u.unit}: ${u.title}`));
    for (const id of u.lessons) {
      const l = D.lessons.find(x => x.id === id);
      if (!l) continue;
      list.append(h('button', { class: 'row-btn', onclick: () => {
        root.replaceChildren(h('button', { class: 'link', onclick: lessonsScreen }, '< Lessons'), lessonView(l));
      } }, `${l.id}  ${l.title}`, s.lessons[l.id] ? h('span', { class: 'note' }, ' (seen)') : null));
    }
  }
  root.replaceChildren(h('h2', {}, 'Lessons'), list);
}

async function progressScreen() {
  tab('progress');
  root.replaceChildren(h('p', { class: 'note' }, 'Loading...'));
  try { root.replaceChildren(await progressView()); } catch (e) { root.replaceChildren(h('p', {}, 'Could not load progress: ' + e.message)); }
}

function download(name, obj) {
  const a = h('a', { href: URL.createObjectURL(new Blob([JSON.stringify(obj, null, 1)], { type: 'application/json' })), download: name });
  document.body.append(a); a.click(); a.remove();
}
const stamp = () => new Date().toISOString().slice(0, 10);

function settingsScreen() {
  tab('settings');
  const s = state();
  const file = h('input', { type: 'file', accept: 'application/json,.json', hidden: true, onchange: async e => {
    const f = e.target.files[0];
    if (!f) return;
    try {
      const d = JSON.parse(await f.text());
      if (d.v !== 1 || typeof d.cards !== 'object' || !Array.isArray(d.log)) throw new Error('not a progress file from this app');
      if (!confirm(`Replace the progress on this device with the file (${Object.keys(d.cards).length} cards)?`)) return;
      delete d.exportedAt;
      replace(d);
      save();
      settingsScreen();
      bgSync();
    } catch (err) { alert('Import failed: ' + err.message); }
  } });
  const toggle = (label, key) => {
    const cb = h('input', { type: 'checkbox', onchange: () => { s.settings[key] = cb.checked; save(); } });
    cb.checked = !!s.settings[key];
    return h('label', { class: 'toggle' }, cb, ' ' + label);
  };
  root.replaceChildren(h('h2', {}, 'Settings'),
    toggle('Always show transliteration', 'translit'),
    toggle('Hide cantillation accents (keeps vowels)', 'hideAccents'),
    toggle('5-minute day (review and one reading, no new items)', 'fiveMin'),
    h('h3', {}, 'Your data'),
    h('p', { class: 'note' }, syncInfo().token ? 'Stored on this device and synced to your gist.' : 'Everything is stored on this device only. Export a backup now and then, and before clearing browser data.'),
    h('div', { class: 'bar' },
      h('button', { onclick: () => download(`hebrew-progress-${stamp()}.json`, { ...s, exportedAt: new Date().toISOString() }) }, 'Export progress'),
      h('button', { onclick: () => file.click() }, 'Import progress')),
    file,
    h('h3', {}, `Reported items (${s.reports.length})`),
    s.reports.length ? h('div', { class: 'bar' }, h('button', { onclick: () => download(`hebrew-reports-${stamp()}.json`, s.reports) }, 'Export reports')) : h('p', { class: 'note' }, 'None. Use Report on any card to hide an item and flag it.'),
    ...s.quarantine.map(id => h('div', { class: 'qrow' }, h('span', {}, id + ' ' + (s.reports.filter(r => r.id === id).at(-1)?.reason || '')),
      h('button', { class: 'link', onclick: () => { restore(id); settingsScreen(); bgSync(); } }, 'Restore'))),
    ...syncSection());
}

function syncSection() {
  const m = syncInfo();
  const busy = async (btn, fn) => { btn.disabled = true; btn.textContent = 'Syncing...'; await fn(); settingsScreen(); };
  if (!m.token) {
    const tok = h('input', { type: 'password', class: 'field', placeholder: 'Paste token', autocomplete: 'off' });
    const go = h('button', { class: 'primary', onclick: () => tok.value.trim() && busy(go, () => connect(tok.value.trim())) }, 'Connect');
    return [h('h3', {}, 'Sync'),
      h('p', { class: 'note' }, 'Optional. Saves progress and reports to a private GitHub gist when you open the app and when a session ends. Needs a classic token with only the "gist" scope; it stays on this device and is never exported.'),
      h('a', { href: 'https://github.com/settings/tokens/new?scopes=gist&description=Hebrew%20app%20sync', target: '_blank', rel: 'noopener' }, 'Create a token on GitHub'),
      tok, h('div', { class: 'bar' }, go)];
  }
  const now = h('button', { onclick: () => busy(now, sync) }, 'Sync now');
  return [h('h3', {}, 'Sync'),
    h('p', { class: 'note' }, m.at ? `Last synced ${new Date(m.at).toLocaleString()}.` : 'Not synced yet.'),
    m.err ? h('p', { class: 'note warn' }, 'Last attempt failed: ' + m.err) : null,
    h('div', { class: 'bar' }, now,
      h('button', { onclick: () => { if (confirm('Stop syncing on this device? Progress here and in the gist stays as it is.')) { disconnect(); settingsScreen(); } } }, 'Disconnect'))].filter(Boolean);
}

window.addEventListener('exit-session', () => { todayScreen(); bgSync(); });
nav.addEventListener('click', e => {
  const t = e.target.dataset && e.target.dataset.t;
  if (t === 'today') todayScreen(); else if (t === 'progress') progressScreen(); else if (t === 'lessons') lessonsScreen(); else if (t === 'settings') settingsScreen();
});

(async () => {
  load();
  try {
    await Promise.all([loadAll(), sync()]);
  } catch (e) {
    root.replaceChildren(h('p', {}, 'Could not load data: ' + e.message));
    return;
  }
  todayScreen();
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('./sw.js').catch(() => {});
})();

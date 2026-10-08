import { loadAll, D } from './data.js';
import { load, save, state } from './store.js';
import { h } from './render.js';
import { runSession, sessionInfo } from './session.js';
import { lessonView } from './lessons.js';

const root = document.getElementById('app');
const nav = document.getElementById('nav');

function tab(name) {
  nav.querySelectorAll('button').forEach(b => b.classList.toggle('on', b.dataset.t === name));
  nav.hidden = false;
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

function settingsScreen() {
  tab('settings');
  const s = state();
  const toggle = (label, key) => {
    const cb = h('input', { type: 'checkbox', onchange: () => { s.settings[key] = cb.checked; save(); } });
    cb.checked = !!s.settings[key];
    return h('label', { class: 'toggle' }, cb, ' ' + label);
  };
  root.replaceChildren(h('h2', {}, 'Settings'),
    toggle('Always show transliteration', 'translit'),
    toggle('5-minute day (review and one reading, no new items)', 'fiveMin'));
}

nav.addEventListener('click', e => {
  const t = e.target.dataset && e.target.dataset.t;
  if (t === 'today') todayScreen(); else if (t === 'lessons') lessonsScreen(); else if (t === 'settings') settingsScreen();
});

(async () => {
  load();
  try {
    await loadAll();
  } catch (e) {
    root.replaceChildren(h('p', {}, 'Could not load data: ' + e.message));
    return;
  }
  todayScreen();
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('./sw.js').catch(() => {});
})();

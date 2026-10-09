// DOM helpers and word rendering. All Hebrew comes from corpus tokens; none is typed here.
import { state } from './store.js';

export function h(tag, attrs, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k === 'class') e.className = v;
    else if (k.startsWith('on')) e.addEventListener(k.slice(2), v);
    else e.setAttribute(k, v === true ? '' : v);
  }
  for (const k of kids.flat()) {
    if (k == null || k === false) continue;
    e.append(k.nodeType ? k : document.createTextNode(String(k)));
  }
  return e;
}

// letter + following marks; letters are U+05D0..U+05EA
export function clusters(s) {
  const out = [];
  for (const ch of s) {
    const cp = ch.codePointAt(0);
    if ((cp >= 0x5D0 && cp <= 0x5EA) || !out.length) out.push(ch);
    else out[out.length - 1] += ch;
  }
  return out;
}

// cantillation accents are U+0591..U+05AF; vowels, dagesh and meteg are kept
export function stripAccents(s) {
  return [...s].filter(ch => { const cp = ch.codePointAt(0); return cp < 0x591 || cp > 0x5AF; }).join('');
}

function partRange(tok, i) {
  let a = 0;
  for (let j = 0; j < i; j++) a += clusters(tok.p[j][0]).length;
  return [a, a + clusters(tok.p[i][0]).length];
}

// Maqqef hyphen ("kol-") only makes sense next to the following word; drop it on a word shown alone.
export const solo = s => (s || '').replace(/-$/, '');

// o: {hl (part index), hlc (cluster ranges), tr: 'tap'|'show'|'none', gloss: bool, mark: bool, inVerse: bool, onTap}
export function word(tok, o = {}) {
  const ranges = o.hlc || (o.hl != null ? [partRange(tok, o.hl)] : []);
  const cl = clusters(tok.s).map(c => (state().settings.hideAccents ? stripAccents(c) : c));
  const he = h('span', { class: 'he', lang: 'he', dir: 'rtl' });
  let run = null, runHl = null;
  cl.forEach((c, i) => {
    const on = ranges.some(([a, b]) => i >= a && i < b);
    if (run === null || on !== runHl) {
      run = h('span', { class: on ? 'hl' : '' });
      runHl = on;
      he.append(run);
    }
    run.append(c);
  });
  const mode = o.tr || (state().settings.translit || state().unit === 0 ? 'show' : 'tap');
  const tr = mode === 'none' ? null : h('span', { class: 'tr' + (mode === 'show' ? '' : ' hid') }, o.inVerse ? tok.tr : solo(tok.tr));
  const gl = o.gloss ? h('span', { class: 'gl' + (tok.gr ? '' : ' unrev') }, tok.g) : null;
  const w = h('span', { class: 'w' + (o.target ? ' target' : ''), 'data-id': tok.id }, he, tr, gl);
  w.addEventListener('click', () => {
    if (tr && mode === 'tap') tr.classList.toggle('hid');
    if (o.onTap) o.onTap(tok, w);
  });
  return w;
}

// A verse as a row of words with the target token emphasised.
export function verseRow(tokens, targetId, o = {}) {
  return h('div', { class: 'verse', dir: 'rtl' },
    tokens.map(t => word(t, { ...o, inVerse: true, target: t.id === targetId, tr: o.tr || 'tap' })));
}

export const glossText = (g, reviewed) => h('span', { class: reviewed ? '' : 'unrev' }, g);

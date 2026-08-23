/**
 * Boot and tab routing.
 *
 * Deployment note (CLAUDE.md): GitHub Pages serves this from a subpath, not a
 * domain root, so every path must be relative. The deck URL is resolved against
 * import.meta.url rather than the document, which keeps it correct whether the
 * loader is index.html at the repo root or app/selftest.html one level down --
 * a document-relative './data/...' would be right for one and wrong for the other.
 */

import * as theme from './theme.js';
import * as vocab from './views/vocab.js';
import * as parseView from './views/parse.js';
import * as readView from './views/read.js';
import * as settingsView from './views/settings.js';

export const DECK_URL = new URL('../data/vocab_deck_600.json', import.meta.url);
export const PARSE_DECK_URL = new URL('../data/parse_qal_strong.json', import.meta.url);
export const READER_DATA_URL = new URL('../data/jonah1_reader.json', import.meta.url);

let deck = null;
let parseDeck = null;
let readerData = null;
let tab = 'vocab';

export async function loadDeck() {
  const res = await fetch(DECK_URL, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`deck fetch failed: ${res.status} ${res.statusText}`);
  const json = await res.json();
  if (!Array.isArray(json.entries) || !json.entries.length) {
    throw new Error('deck contains no entries');
  }
  return json.entries;
}

export async function loadParseDeck() {
  const res = await fetch(PARSE_DECK_URL, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`parse deck fetch failed: ${res.status} ${res.statusText}`);
  const json = await res.json();
  if (!Array.isArray(json.entries) || !json.entries.length) {
    throw new Error('parse deck contains no entries');
  }
  return json.entries;
}

export async function loadReaderData() {
  const res = await fetch(READER_DATA_URL, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`reader data fetch failed: ${res.status} ${res.statusText}`);
  const json = await res.json();
  if (!Array.isArray(json.verses) || !json.verses.length) {
    throw new Error('reader data contains no verses');
  }
  return json;
}

function view() {
  return document.getElementById('view');
}

function rerender() {
  const root = view();
  if (!deck) return;
  if (tab === 'settings') settingsView.render(root, deck, rerender);
  else if (tab === 'parse') {
    if (!parseDeck) { root.textContent = 'Loading…'; return; }
    parseView.render(root, parseDeck);
  } else if (tab === 'read') {
    if (!readerData) { root.textContent = 'Loading…'; return; }
    readView.render(root, readerData);
  } else vocab.render(root, deck);
  window.scrollTo(0, 0);
}

async function selectTab(name) {
  tab = name;
  for (const b of document.querySelectorAll('.tab')) {
    if (b.dataset.tab === name) b.setAttribute('aria-current', 'page');
    else b.removeAttribute('aria-current');
  }
  // Lazily loaded, not fetched at boot alongside the vocab deck: most
  // sessions only ever open Vocab, and this keeps that critical path to one
  // fetch.
  if (name === 'parse' && !parseDeck) {
    try {
      parseDeck = await loadParseDeck();
    } catch (err) {
      console.error(err);
      view().textContent = `Could not load the parsing deck: ${err.message || err}`;
      return;
    }
  }
  if (name === 'read' && !readerData) {
    try {
      readerData = await loadReaderData();
    } catch (err) {
      console.error(err);
      view().textContent = `Could not load the reader: ${err.message || err}`;
      return;
    }
  }
  rerender();
}

function fail(err) {
  console.error(err);
  const root = view();
  root.textContent = '';
  const wrap = document.createElement('div');
  wrap.className = 'done';
  const h = document.createElement('h1');
  h.textContent = 'Could not load the deck';
  const p = document.createElement('p');
  p.textContent = String(err.message || err);
  const p2 = document.createElement('p');
  p2.className = 'note';
  p2.textContent = `Tried: ${DECK_URL.pathname}`;
  wrap.append(h, p, p2);
  root.appendChild(wrap);
}

async function boot() {
  theme.init();
  vocab.setRerender(rerender);
  parseView.setRerender(rerender);
  readView.setRerender(rerender);

  for (const b of document.querySelectorAll('.tab')) {
    if (b.disabled) continue;
    b.addEventListener('click', () => selectTab(b.dataset.tab));
  }

  try {
    deck = await loadDeck();
  } catch (err) {
    fail(err);
    return;
  }
  rerender();
}

// Boot only when this module is loaded by a page that actually hosts the app.
// selftest.html imports loadDeck/DECK_URL from here for its own checks, and
// must not get a booted app as a side effect of an import.
if (document.getElementById('view')) boot();

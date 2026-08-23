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
import * as learnView from './views/learn.js';
import * as settingsView from './views/settings.js';
import * as feedback from './feedback.js';

export const DECK_URL = new URL('../data/vocab_deck_600.json', import.meta.url);
export const PARSE_DECK_URL = new URL('../data/parse_qal_strong.json', import.meta.url);

// Lesson groups in teaching order (see STATUS.md for why group 2 -- construct
// chains -- followed group 1 -- prefixes/suffixes). Add a new group here once
// its data/*.json exists -- everything else (tab loading, the Learn tab's
// grouped list) is generic over this list, same pattern as READER_CHAPTERS.
export const LESSON_GROUPS = [
  { key: 'group1', url: new URL('../data/lessons_group1.json', import.meta.url) },
  { key: 'group2', url: new URL('../data/lessons_group2.json', import.meta.url) },
  { key: 'group3', url: new URL('../data/lessons_group3.json', import.meta.url) },
  { key: 'group4', url: new URL('../data/lessons_group4.json', import.meta.url) },
  { key: 'group5', url: new URL('../data/lessons_group5.json', import.meta.url) },
];

// Reader chapters in reading order (CLAUDE.md's locked order: Jonah, then
// Ruth, then Genesis narrative, then Exodus 3/14). Add a new chapter here
// once its data/*.json exists -- everything else (tab loading, the chapter
// switcher in read.js) is generic over this list.
export const READER_CHAPTERS = [
  { key: 'jonah1', label: 'Jonah 1', url: new URL('../data/jonah1_reader.json', import.meta.url) },
  { key: 'jonah2', label: 'Jonah 2', url: new URL('../data/jonah2_reader.json', import.meta.url) },
  { key: 'jonah3', label: 'Jonah 3', url: new URL('../data/jonah3_reader.json', import.meta.url) },
  { key: 'jonah4', label: 'Jonah 4', url: new URL('../data/jonah4_reader.json', import.meta.url) },
];

// Left-to-right tab bar order, for the directional switch-view sweep --
// matches index.html's button order exactly.
const TAB_ORDER = ['vocab', 'parse', 'read', 'learn', 'settings'];

let deck = null;
let parseDeck = null;
const readerCache = {}; // chapter key -> loaded reader JSON
let readerChapterKey = READER_CHAPTERS[0].key;
const lessonGroupCache = {}; // group key -> loaded lessons JSON
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

export async function loadLessonGroup(key) {
  const group = LESSON_GROUPS.find((g) => g.key === key);
  if (!group) throw new Error(`unknown lesson group: ${key}`);
  const res = await fetch(group.url, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`lessons fetch failed: ${res.status} ${res.statusText}`);
  const json = await res.json();
  if (!Array.isArray(json.lessons) || !json.lessons.length) {
    throw new Error('lessons contain no entries');
  }
  return json;
}

export async function loadReaderData(key) {
  const chapter = READER_CHAPTERS.find((c) => c.key === key);
  if (!chapter) throw new Error(`unknown reader chapter: ${key}`);
  const res = await fetch(chapter.url, { cache: 'no-cache' });
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
    if (!readerCache[readerChapterKey]) { root.textContent = 'Loading…'; return; }
    readView.render(root, {
      chapters: READER_CHAPTERS,
      currentKey: readerChapterKey,
      data: readerCache[readerChapterKey],
    });
  } else if (tab === 'learn') {
    const groups = LESSON_GROUPS.map((g) => lessonGroupCache[g.key]);
    if (groups.some((g) => !g)) { root.textContent = 'Loading…'; return; }
    learnView.render(root, groups);
  } else vocab.render(root, deck);
  window.scrollTo(0, 0);
}

async function loadReaderChapter(key) {
  try {
    readerCache[key] = await loadReaderData(key);
  } catch (err) {
    console.error(err);
    view().textContent = `Could not load the reader: ${err.message || err}`;
    throw err;
  }
}

async function selectReaderChapter(key) {
  readerChapterKey = key;
  if (!readerCache[key]) {
    try {
      await loadReaderChapter(key);
    } catch {
      return;
    }
  }
  rerender();
}

async function selectTab(name) {
  const prevIndex = TAB_ORDER.indexOf(tab);
  const nextIndex = TAB_ORDER.indexOf(name);
  if (nextIndex !== prevIndex) feedback.switchView(nextIndex > prevIndex ? 1 : -1);

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
  if (name === 'read' && !readerCache[readerChapterKey]) {
    try {
      await loadReaderChapter(readerChapterKey);
    } catch {
      return;
    }
  }
  if (name === 'learn') {
    try {
      for (const g of LESSON_GROUPS) {
        if (!lessonGroupCache[g.key]) lessonGroupCache[g.key] = await loadLessonGroup(g.key);
      }
    } catch (err) {
      console.error(err);
      view().textContent = `Could not load the lessons: ${err.message || err}`;
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
  readView.setSelectChapter(selectReaderChapter);
  learnView.setRerender(rerender);

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

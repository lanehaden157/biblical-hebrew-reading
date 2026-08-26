/**
 * The reader. Phase 4 added the first connected-text chapter (Jonah 1);
 * Phase 5 made it multi-chapter (main.js's READER_CHAPTERS list) and added
 * the chapter switcher below.
 *
 * Deliberately not another SRS deck -- there is no grading and no scheduler
 * state here. The goal (CLAUDE.md) is fluency practice on real text, and a
 * queue/grade UI on top of a narrative would fight that. Every word in the
 * chapter is always available, tap-to-reveal, every time the page opens;
 * which words are open is ephemeral view state, not persisted (closing the
 * tab and coming back just starts every word closed again -- nothing worth
 * remembering across sessions here, unlike review history). Switching
 * chapters resets it the same way, for the same reason.
 *
 * A tapped word reveals transliteration + gloss (hard rule 4) but never a
 * part-of-speech or parse label -- see build_jonah1_reader.py's docstring
 * for why: these chapters run ahead of the grammar coverage (weak roots,
 * non-Qal stems) that would make such a label reliable, and a wrong
 * grammatical claim is worse than none.
 *
 * Hard rule 1 applies here same as every other view: not one Hebrew
 * character appears in this file. Every glyph is read from the current
 * chapter's data/*.json file at runtime.
 */

import * as feedback from '../feedback.js';
import { translitFrag } from '../translit_display.js';

const openIds = new Set();
let lastChapterKey = null;

export function render(root, { chapters, currentKey, data }) {
  // Switching chapters starts every word closed again -- reveal state was
  // never meant to persist (see module docstring), and carrying it across
  // chapters would just risk an id collision showing something pre-opened.
  if (currentKey !== lastChapterKey) {
    openIds.clear();
    lastChapterKey = currentKey;
  }

  root.textContent = '';

  const h = document.createElement('h1');
  h.className = 'title';
  h.textContent = data.metadata.chapter;
  root.appendChild(h);

  if (chapters.length > 1) {
    root.appendChild(chapterSwitcher(chapters, currentKey));
  }

  const note = document.createElement('p');
  note.className = 'note';
  note.textContent = 'Tap a word for its reading. Words with a dot underneath aren’t in your vocab deck yet.';
  root.appendChild(note);

  for (const verse of data.verses) {
    root.appendChild(verseEl(verse));
  }
}

function chapterSwitcher(chapters, currentKey) {
  const box = document.createElement('div');
  box.className = 'seg';
  box.style.marginBottom = '14px';
  for (const c of chapters) {
    const b = document.createElement('button');
    b.textContent = c.label;
    b.setAttribute('aria-pressed', String(c.key === currentKey));
    b.addEventListener('click', () => selectChapter(c.key));
    box.appendChild(b);
  }
  return box;
}

function verseEl(verse) {
  const wrap = document.createElement('div');
  wrap.className = 'reader-verse';

  const num = document.createElement('span');
  num.className = 'reader-vnum';
  num.textContent = String(verse.verse_num);
  wrap.appendChild(num);

  const line = document.createElement('span');
  line.className = 'reader-line heb';
  line.lang = 'he';
  for (const word of verse.words) {
    line.appendChild(wordEl(word));
  }
  wrap.appendChild(line);

  return wrap;
}

function wordEl(word) {
  const isOpen = openIds.has(word.id);

  const chip = document.createElement('span');
  chip.className = 'reader-word' + (word.is_known ? '' : ' is-new') + (isOpen ? ' is-open' : '');
  chip.setAttribute('role', 'button');
  chip.tabIndex = 0;

  const heb = document.createElement('span');
  heb.className = 'reader-word-heb';
  heb.textContent = word.surface_form;
  chip.appendChild(heb);

  if (isOpen) {
    const t = document.createElement('span');
    t.className = 'reader-word-translit';
    t.appendChild(translitFrag(word.transliteration));
    chip.appendChild(t);

    const g = document.createElement('span');
    g.className = 'reader-word-gloss';
    g.textContent = word.gloss;
    chip.appendChild(g);
  }

  const toggle = () => {
    const opening = !openIds.has(word.id);
    if (opening) openIds.add(word.id);
    else openIds.delete(word.id);
    // Only the reveal gets a sound, same one-directional rule as the vocab
    // card's advance() -- closing a word back up is silent.
    if (opening) feedback.readReveal(word.is_known);
    rerender();
  };
  chip.addEventListener('click', toggle);
  chip.addEventListener('keydown', (e) => {
    if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); toggle(); }
  });

  return chip;
}

let rerender = () => {};
export function setRerender(fn) { rerender = fn; }

let selectChapter = () => {};
export function setSelectChapter(fn) { selectChapter = fn; }

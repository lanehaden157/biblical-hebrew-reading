/**
 * The reader. Phase 4, first connected-text reading: Jonah 1.
 *
 * Deliberately not another SRS deck -- there is no grading and no scheduler
 * state here. The goal (CLAUDE.md) is fluency practice on real text, and a
 * queue/grade UI on top of a narrative would fight that. Every word in the
 * chapter is always available, tap-to-reveal, every time the page opens;
 * which words are open is ephemeral view state, not persisted (closing the
 * tab and coming back just starts every word closed again -- nothing worth
 * remembering across sessions here, unlike review history).
 *
 * A tapped word reveals transliteration + gloss (hard rule 4) but never a
 * part-of-speech or parse label -- see build_jonah1_reader.py's docstring
 * for why: this chapter runs ahead of the grammar coverage (weak roots,
 * non-Qal stems) that would make such a label reliable, and a wrong
 * grammatical claim is worse than none.
 *
 * Hard rule 1 applies here same as every other view: not one Hebrew
 * character appears in this file. Every glyph is read from
 * data/jonah1_reader.json at runtime.
 */

const openIds = new Set();

export function render(root, readerData) {
  root.textContent = '';

  const h = document.createElement('h1');
  h.className = 'title';
  h.textContent = readerData.metadata.chapter;
  root.appendChild(h);

  const note = document.createElement('p');
  note.className = 'note';
  note.textContent = 'Tap a word for its reading. Words with a dot underneath aren’t in your vocab deck yet.';
  root.appendChild(note);

  for (const verse of readerData.verses) {
    root.appendChild(verseEl(verse));
  }
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
    t.textContent = word.transliteration;
    chip.appendChild(t);

    const g = document.createElement('span');
    g.className = 'reader-word-gloss';
    g.textContent = word.gloss;
    chip.appendChild(g);
  }

  const toggle = () => {
    if (openIds.has(word.id)) openIds.delete(word.id);
    else openIds.add(word.id);
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

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
import { translitFrag } from '../translit_display.js';

let queue = [];
let pos = 0;
let stage = 0;
let session = null;
let deferred = 0;
let flipped = false;
let flipping = false;
let functionWordExamples = {};

const HINTS = ['tap for the sound', 'tap for the meaning'];

const EXAMPLE_WINDOW = 3;

// FNV-1a-style string hash -> 32-bit unsigned seed for the rotation shuffle below.
function hashSeed(str) {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

// mulberry32: tiny deterministic PRNG -- same seed always produces the same
// sequence, which is what lets the rotation below be "random-looking" without
// being genuinely random (a genuinely random pick could repeat the same 3
// examples two reviews running, or skip others for a long time by chance).
function mulberry32(seed) {
  let a = seed;
  return function rand() {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function seededShuffle(arr, seed) {
  const rand = mulberry32(seed);
  const out = arr.slice();
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

// Which examples to show on this review: a lemma's examples are walked
// EXAMPLE_WINDOW at a time in a shuffled order, guaranteeing every example is
// seen once before any repeat ("a cycle"), and the shuffle is redrawn each
// time a full cycle completes. Seeded on (lemma, cycle number) rather than
// Math.random() so re-rendering the same review (e.g. a stray re-render, not
// a re-grade) never swaps the examples out from under you mid-read -- only
// grading the card (which advances `reps`) moves it to the next window.
// Lemmas with <= EXAMPLE_WINDOW examples (most of them, for now) just show
// everything every time -- there's nothing to rotate.
function rotatingWindow(wex, item) {
  const all = wex.examples;
  if (all.length <= EXAMPLE_WINDOW) return all;
  const reps = (item.card && item.card.reps) || 0;
  const numBatches = Math.ceil(all.length / EXAMPLE_WINDOW);
  const cycle = Math.floor(reps / numBatches);
  const batch = reps % numBatches;
  const order = seededShuffle(all.map((_, i) => i), hashSeed(`${item.entry.lemma_id}:${cycle}`));
  return order.slice(batch * EXAMPLE_WINDOW, batch * EXAMPLE_WINDOW + EXAMPLE_WINDOW).map((i) => all[i]);
}

export function reset() {
  queue = [];
  session = null;
}

export function render(root, deck, examples) {
  functionWordExamples = examples || {};
  if (!session) {
    const built = buildQueue(deck);
    queue = built.queue;
    deferred = built.deferred;
    pos = 0;
    stage = 0;
    flipped = false;
    session = { start: Date.now(), reviewed: 0, again: 0 };
  }

  root.textContent = '';

  if (pos >= queue.length) {
    root.appendChild(doneScreen(deck));
    return;
  }

  const item = queue[pos];
  root.appendChild(headRow(item));

  const wex = functionWordExamples[item.entry.lemma_id];
  const perspective = document.createElement('div');
  perspective.className = 'flip-perspective';
  const flipCard = document.createElement('div');
  flipCard.className = 'flip-card';
  flipCard.appendChild(flipped && wex ? cardBackEl(item, wex) : cardEl(item, wex, stage));
  perspective.appendChild(flipCard);
  root.appendChild(perspective);

  if (stage === 2 && !flipped) root.appendChild(gradeRow(item, root, deck));
}

// Mid-flip guard plus the two-phase rotate-out/swap-content/rotate-in dance:
// the DOM is fully rebuilt on every render() (see above), so a plain CSS
// transition can't animate across that rebuild by itself -- this drives it
// by hand, rotating the current face to its edge, swapping `flipped` and
// re-rendering (which mounts the new face already edge-on via
// .flip-in-start), then dropping that class to let the base .flip-card
// transition carry it the rest of the way to face-on. The class swap is
// separated by a forced reflow (the offsetWidth read), not a
// requestAnimationFrame -- rAF only fires once the tab is actually
// compositing frames, which isn't guaranteed (e.g. a backgrounded or
// off-screen webview), and stalling there would leave `flipping` stuck
// true forever, wedging every future tap.
function triggerFlip(next) {
  if (flipping || flipped === next) return;
  flipping = true;
  const current = document.querySelector('.flip-card');
  const FLIP_HALF_MS = 160;
  const finish = () => {
    flipped = next;
    rerender();
    const fresh = document.querySelector('.flip-card');
    if (fresh) {
      fresh.classList.add('flip-in-start');
      void fresh.offsetWidth; // force reflow so removing the class below restarts the transition
      fresh.classList.remove('flip-in-start');
    }
    flipping = false;
  };
  if (current) {
    current.classList.add('flip-out');
    setTimeout(finish, FLIP_HALF_MS);
  } else {
    finish();
  }
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

// stage is an explicit parameter (not read from the module-level `stage`
// above) so app/browse.js can call this directly to preview any card at any
// reveal stage without touching the live review queue at all -- the default
// `advance` behavior below still drives the module variable for the real
// review flow; opts.onAdvance/opts.onExamples let a caller like browse.js
// substitute its own local state instead.
export function cardEl(item, wex, stageArg, opts = {}) {
  const { entry } = item;
  const el = document.createElement('div');
  el.className = 'card' + (stageArg === 2 ? ' is-open' : '');
  el.setAttribute('role', 'button');
  el.tabIndex = 0;

  const heb = document.createElement('p');
  heb.className = 'card-heb heb';
  heb.lang = 'he';
  heb.textContent = entry.citation_form;   // from /data, never a literal
  el.appendChild(heb);

  if (stageArg >= 1) {
    el.appendChild(hr());
    const t = document.createElement('p');
    t.className = 'card-translit';
    t.appendChild(translitFrag(entry.transliteration));
    el.appendChild(t);

    // A card whose secondary form was folded in (see build_vocab_deck.py's
    // MERGED_LEMMAS -- 'et/`im both just mean "with") shows that second
    // written form here, at the same reveal stage as the primary's own
    // transliteration, since recognizing either spelling is the actual goal.
    if (entry.merged_with) {
      const alt = document.createElement('p');
      alt.className = 'card-merged';
      const altHeb = document.createElement('span');
      altHeb.className = 'heb';
      altHeb.lang = 'he';
      altHeb.textContent = entry.merged_with.citation_form;
      alt.appendChild(document.createTextNode('also written '));
      alt.appendChild(altHeb);
      alt.appendChild(document.createTextNode(' ('));
      alt.appendChild(translitFrag(entry.merged_with.transliteration));
      alt.appendChild(document.createTextNode(') — same word for reading'));
      el.appendChild(alt);
    }
  }

  if (stageArg >= 2) {
    const g = document.createElement('p');
    g.className = 'card-gloss';
    g.textContent = entry.gloss;
    el.appendChild(g);

    const m = document.createElement('p');
    m.className = 'card-meta';
    m.textContent = `${entry.pos} · ${entry.frequency.toLocaleString()}× in the Hebrew Bible`;
    el.appendChild(m);

    // Curated for particles whose English glosses look like unrelated words
    // (e.g. "in, on, with") but are really one spatial/relational idea --
    // see build_vocab_deck.py. Only ~11 lemmas have this field; absent for
    // everything else.
    if (entry.core_schema) {
      const s = document.createElement('p');
      s.className = 'card-schema';
      s.textContent = entry.core_schema;
      el.appendChild(s);
    }

    // A one-line warning that this word is easily mixed up with a
    // *different* word already in the deck -- either they look alike in
    // transliteration ('im/`im) or one is a much rarer synonym of the
    // other (she-/'asher). See build_vocab_deck.py. A handful of lemmas
    // have this; absent for everything else.
    if (entry.confusable_with) {
      const c = document.createElement('p');
      c.className = 'card-confusable';
      c.textContent = entry.confusable_with;
      el.appendChild(c);
    }

    // Optional, doesn't block grading (see gradeRow) -- prepositions/
    // conjunctions/particles are hard to remember from a bare gloss alone
    // since (unlike a noun or verb) their meaning only comes clear from a
    // real sentence. Only rendered for the ~45-word closed set that
    // data/function_word_examples.json actually covers. Flips the whole
    // card over rather than expanding downward, and only reachable once
    // stage >= 2 (past the definition) -- flipping back to this face is
    // how you grade, so the examples stay a look-up, never a detour.
    if (wex) {
      const shown = rotatingWindow(wex, item);
      const toggle = document.createElement('button');
      toggle.className = 'examples-toggle';
      toggle.type = 'button';
      toggle.textContent = `See ${shown.length} example${shown.length === 1 ? '' : 's'} from the Bible`;
      toggle.addEventListener('click', (e) => {
        e.stopPropagation();
        (opts.onExamples || (() => triggerFlip(true)))();
      });
      el.appendChild(toggle);
    }
  } else {
    const hint = document.createElement('p');
    hint.className = 'card-hint';
    hint.textContent = HINTS[stageArg];
    el.appendChild(hint);
  }

  const advance = opts.onAdvance || (() => {
    if (stage >= 2) return;
    stage++;
    feedback.tap(stage);
    rerender();
  });
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

// Wraps the phrase's target word (by position, computed at build time from
// the corpus -- never string-matched here) in the same root-highlight
// green used elsewhere in the app, so the lemma being taught is visible
// inside the surrounding phrase rather than just implied by the card.
function hebPhraseFrag(text, targetIndex) {
  const frag = document.createDocumentFragment();
  text.split(' ').forEach((w, i) => {
    if (i > 0) frag.appendChild(document.createTextNode(' '));
    if (i === targetIndex) {
      const span = document.createElement('span');
      span.className = 'example-heb-target';
      span.textContent = w;
      frag.appendChild(span);
    } else {
      frag.appendChild(document.createTextNode(w));
    }
  });
  return frag;
}

// Same idea on the English side: gloss_highlight is a literal substring of
// gloss (checked at build time), so a plain indexOf split is safe here --
// no need to search for word boundaries since the exact text is known.
function glossFrag(gloss, highlight) {
  const frag = document.createDocumentFragment();
  const idx = gloss.indexOf(highlight);
  if (idx === -1) {
    frag.appendChild(document.createTextNode(gloss));
    return frag;
  }
  frag.appendChild(document.createTextNode(gloss.slice(0, idx)));
  const span = document.createElement('span');
  span.className = 'example-gloss-target';
  span.textContent = highlight;
  frag.appendChild(span);
  frag.appendChild(document.createTextNode(gloss.slice(idx + highlight.length)));
  return frag;
}

// opts.onFlipBack lets app/browse.js substitute its own local flip state
// instead of the live review flow's module-level `flipped`/rerender.
export function cardBackEl(item, wex, opts = {}) {
  const el = document.createElement('div');
  el.className = 'card card-back';
  el.setAttribute('role', 'button');
  el.tabIndex = 0;

  const heading = document.createElement('p');
  heading.className = 'card-back-heading';
  heading.textContent = 'Real usage in the Bible';
  el.appendChild(heading);

  const panel = document.createElement('div');
  panel.className = 'examples-panel';
  for (const ex of rotatingWindow(wex, item)) {
    const exEl = document.createElement('div');
    exEl.className = 'example-item';

    const heb = document.createElement('p');
    heb.className = 'example-heb heb';
    heb.lang = 'he';
    heb.appendChild(hebPhraseFrag(ex.phrase_hebrew, ex.target_index));
    exEl.appendChild(heb);

    const translit = document.createElement('p');
    translit.className = 'example-translit';
    translit.appendChild(translitFrag(ex.phrase_transliteration));
    exEl.appendChild(translit);

    const gloss = document.createElement('p');
    gloss.className = 'example-gloss';
    gloss.appendChild(document.createTextNode('“'));
    gloss.appendChild(glossFrag(ex.gloss, ex.gloss_highlight));
    gloss.appendChild(document.createTextNode('”'));
    exEl.appendChild(gloss);

    if (ex.gloss_note) {
      const note = document.createElement('p');
      note.className = 'example-note';
      note.textContent = ex.gloss_note;
      exEl.appendChild(note);
    }

    const ref = document.createElement('p');
    ref.className = 'example-ref';
    ref.textContent = ex.ref;
    exEl.appendChild(ref);

    panel.appendChild(exEl);
  }
  el.appendChild(panel);

  const back = document.createElement('button');
  back.className = 'flip-back-btn';
  back.type = 'button';
  back.textContent = '← Flip back to grade';
  const flipBack = opts.onFlipBack || (() => triggerFlip(false));
  back.addEventListener('click', (e) => {
    e.stopPropagation();
    flipBack();
  });
  el.appendChild(back);

  el.addEventListener('click', flipBack);
  el.addEventListener('keydown', (e) => {
    if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); flipBack(); }
  });
  return el;
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
  feedback.grade(gradeKey);
  if (gradeKey === 'again') {
    session.again++;
    // Missed cards come back at the end of this session rather than waiting for
    // tomorrow -- that is what the learning steps are for.
    queue.push({ ...item, card: null, isNew: false, repeat: true });
  }

  pos++;
  stage = 0;
  flipped = false;
  if (pos >= queue.length) feedback.finish();
  rerender();
}

function doneScreen(deck) {
  const wrap = document.createElement('div');
  wrap.className = 'done';

  const mins = Math.max(1, Math.round((Date.now() - session.start) / 60000));
  const reviewed = session.reviewed;

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

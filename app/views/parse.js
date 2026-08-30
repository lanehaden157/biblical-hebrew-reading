/**
 * The parsing gym. Tier 2, Qal strong verbs only (see CLAUDE.md).
 *
 * Reverse-parse direction, per the locked decision: textbooks teach
 * production (root -> inflected form), reading requires the inverse. Here
 * the inflected form is shown first and the root + stem + conjugation + PGN
 * is the thing recalled, mirroring vocab's diagnostic three-stage reveal
 * (surface form -> its own reading -> the analysis), so a miss says which
 * half broke: could you sound out the form, or could you parse it.
 *
 * The card shows the WHOLE printed word (entry.surface_form), not just the
 * verb's own morpheme -- a prefixed vav or preposition, or a pronominal
 * suffix, is never stripped out (matches how the Jonah reader already
 * displays words). Within it, entry.root_span (just the 3 root letters) is
 * highlighted, entry.preformative/afformative (conjugation-marking material
 * fused onto the stem -- a yiqtol yod, a qatal person-suffix) get their own
 * muted color since they are grammar, not the root, and entry.prefix_form/
 * suffix_form (word-level function morphemes) stay the plainest of the
 * three. Prefix/suffix glosses are revealed alongside the root+gloss+parse
 * at stage 2, since recognizing a prefix's own meaning is part of the
 * parse, not the initial read.
 *
 * Hard rule 1 applies here: not one Hebrew character appears in this file.
 * Every glyph is read from data/parse_qal_strong.json at runtime.
 * Every Hebrew form shown gets a transliteration + gloss, per CLAUDE.md.
 */

import { update, today, load } from '../store.js';
import { buildQueue, newCard, applyGrade, preview, GRADES } from '../srs.js';
import * as feedback from '../feedback.js';
import { translitFrag } from '../translit_display.js';

const keyFn = (entry) => `parse:${entry.id}`;

const CONJ_NAMES = {
  qatal: 'qatal (perfect)',
  weqatal: 'weqatal (sequential perfect)',
  wayyiqtol: 'wayyiqtol (narrative)',
  yiqtol: 'yiqtol (imperfect)',
  participle: 'participle',
  infinitive_construct: 'infinitive construct',
};
const PERSON_NAMES = { 1: '1st', 2: '2nd', 3: '3rd' };
const GENDER_NAMES = { m: 'masc.', f: 'fem.', c: 'common' };
const NUMBER_NAMES = { s: 'sing.', p: 'pl.', d: 'dual' };
const STATE_NAMES = { absolute: 'absolute', construct: 'construct' };
const SUFFIX_KIND_NAMES = {
  paragogic_nun: 'paragogic nun',
  directional_he: 'directional/paragogic he',
};

function parseLabel(entry) {
  const pgn = [
    entry.person && PERSON_NAMES[entry.person],
    entry.gender && GENDER_NAMES[entry.gender],
    entry.number && NUMBER_NAMES[entry.number],
    entry.state && STATE_NAMES[entry.state],
  ].filter(Boolean).join(' ');
  const conj = CONJ_NAMES[entry.conjugation] || entry.conjugation;
  let label = `${entry.stem} ${conj}${pgn ? ', ' + pgn : ''}`;
  if (entry.suffix_kind === 'pronominal' && entry.suffix_pgn) {
    const p = entry.suffix_pgn;
    label += ` + ${PERSON_NAMES[p.person]} ${GENDER_NAMES[p.gender]} ${NUMBER_NAMES[p.number]} suffix`;
  } else if (entry.suffix_kind) {
    label += ` + ${SUFFIX_KIND_NAMES[entry.suffix_kind] || entry.suffix_kind}`;
  }
  return label;
}

function prefixGlossLine(entry) {
  if (!entry.prefix_morphemes || !entry.prefix_morphemes.length) return '';
  return entry.prefix_morphemes.map((m) => m.gloss).join(' + ');
}

let queue = [];
let pos = 0;
let stage = 0;
let session = null;
let deferred = 0;

const HINTS = ['tap for the reading', 'tap for the parse'];

export function render(root, deck) {
  if (!session) {
    const built = buildQueue(deck, new Date(), keyFn);
    queue = built.queue;
    deferred = built.deferred;
    pos = 0;
    stage = 0;
    session = { start: Date.now(), reviewed: 0, again: 0 };
  }

  root.textContent = '';

  if (pos >= queue.length) {
    root.appendChild(doneScreen());
    return;
  }

  const item = queue[pos];
  root.appendChild(headRow(item));
  const card = cardEl(item, stage);
  root.appendChild(card);
  if (stage === 2) root.appendChild(gradeRow(item, deck));
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
    b.textContent = 'new form';
    right.appendChild(b);
  }
  head.appendChild(right);
  return head;
}

// stage is an explicit parameter (not read from the module-level `stage`
// above) so app/browse.js can call this directly to preview any card at any
// reveal stage without touching the live review queue at all -- the default
// `advance` behavior below still drives the module variable for the real
// review flow; opts.onAdvance lets a caller like browse.js substitute its
// own local state instead.
export function cardEl(item, stageArg, opts = {}) {
  const { entry } = item;
  const el = document.createElement('div');
  el.className = 'card' + (stageArg === 2 ? ' is-open' : '');
  el.setAttribute('role', 'button');
  el.tabIndex = 0;

  const heb = document.createElement('p');
  heb.className = 'card-heb heb';
  heb.lang = 'he';
  // Whole printed word, five possible spans, all from /data (hard rule 1):
  // prefix_form/suffix_form are word-level function morphemes (a
  // preposition, the article, a pronominal suffix); preformative/
  // afformative are conjugation-marking material fused onto the verb stem
  // (the yiqtol yod, a qatal person-suffix) that is NOT the root; root_span
  // is the actual 3-letter root, the thing the highlight is meant to mark.
  // Splitting preformative/afformative out of what used to be one
  // "verb_form = highlight" span exists because coloring the whole verb
  // form the same as the root was flagged as wrong by inspection of real
  // cards -- see find_root_span() in build_parse_qal.py.
  const span = (text, cls) => {
    const s = document.createElement('span');
    s.className = cls;
    s.textContent = text;
    return s;
  };
  if (entry.prefix_form) heb.appendChild(span(entry.prefix_form, 'card-heb-affix'));
  if (entry.preformative) heb.appendChild(span(entry.preformative, 'card-heb-conj'));
  heb.appendChild(span(entry.root_span, 'card-heb-verb'));
  if (entry.afformative) heb.appendChild(span(entry.afformative, 'card-heb-conj'));
  if (entry.suffix_form) heb.appendChild(span(entry.suffix_form, 'card-heb-affix'));
  el.appendChild(heb);

  if (stageArg >= 1) {
    el.appendChild(hr());
    const t = document.createElement('p');
    t.className = 'card-translit';
    t.appendChild(translitFrag(entry.transliteration));
    el.appendChild(t);
  }

  if (stageArg >= 2) {
    el.appendChild(hr());

    const root = document.createElement('p');
    root.className = 'card-root heb';
    root.lang = 'he';
    root.textContent = entry.root_citation_form;
    el.appendChild(root);

    const rootT = document.createElement('p');
    rootT.className = 'card-translit';
    rootT.appendChild(translitFrag(entry.root_transliteration));
    el.appendChild(rootT);

    const g = document.createElement('p');
    g.className = 'card-gloss';
    g.textContent = entry.gloss;
    el.appendChild(g);

    const prefixGloss = prefixGlossLine(entry);
    if (prefixGloss) {
      const pg = document.createElement('p');
      pg.className = 'card-affix-gloss';
      pg.textContent = prefixGloss;
      el.appendChild(pg);
    }

    const m = document.createElement('p');
    m.className = 'card-meta';
    m.textContent = parseLabel(entry);
    el.appendChild(m);
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

function gradeRow(item, deck) {
  const wrap = document.createElement('div');
  wrap.className = 'grades';

  // Read live state rather than the queue snapshot: a card missed earlier in
  // this session is re-queued and by then has real scheduling state, so the
  // snapshot would preview it as if it were still brand new.
  const current = load().cards[keyFn(item.entry)] || newCard();
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
  const id = keyFn(item.entry);
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
  if (pos >= queue.length) feedback.finish();
  rerender();
}

function doneScreen() {
  const wrap = document.createElement('div');
  wrap.className = 'done';

  const mins = Math.max(1, Math.round((Date.now() - session.start) / 60000));
  const reviewed = session.reviewed;

  const h = document.createElement('h1');
  h.textContent = reviewed > 0 ? 'Done for now' : 'Nothing due';
  wrap.appendChild(h);

  const p = document.createElement('p');
  if (reviewed > 0) {
    p.textContent = `${reviewed} form${reviewed === 1 ? '' : 's'} in about ${mins} minute${mins === 1 ? '' : 's'}.`;
  } else {
    p.textContent = 'Come back later for more parsing practice.';
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

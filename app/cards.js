// One presenter per item kind. Each returns a Promise of {grade, ok, ms}:
// grade is 'again'|'good'|'easy' for scheduled items, null for unscheduled ones.
import { h, word, verseRow, glossText, solo } from './render.js';
import { D, verse } from './data.js';
import { state } from './store.js';

const STEMS = { q: 'Qal', N: 'Niphal', p: 'Piel', P: 'Pual', h: 'Hiphil', H: 'Hophal', t: 'Hithpael' };
const PGNS = ['3ms', '3fs', '3mp', '3fp', '2ms', '2fs', '2mp', '2fp', '1cs', '1cp'];
const CONJ_BASE = ['wayyiqtol', 'qatal', 'yiqtol', 'imperative', 'participle', 'inf. cstr.', 'inf. abs.'];

function chipOptions(facet) {
  if (facet === 'stem') return Object.keys(STEMS);
  if (facet === 'pgn') return PGNS;
  const seen = new Set(CONJ_BASE);
  for (const it of D.items.values()) if (it.kind === 'form') seen.add(it.facets.conj);
  return [...seen];
}
const chipLabel = (facet, v) => (facet === 'stem' ? STEMS[v] : v);

const shuffle = a => a.map(x => [Math.random(), x]).sort((p, q) => p[0] - q[0]).map(p => p[1]);

// Wait for a button press; buttons = [{label, value, cls}]
function choose(box, buttons) {
  return new Promise(res => {
    const bar = h('div', { class: 'bar' }, buttons.map(b =>
      h('button', { class: b.cls || '', onclick: () => { bar.remove(); res(b.value); } }, b.label)));
    box.append(bar);
  });
}
const revealBtn = box => choose(box, [{ label: 'Show answer', value: 1, cls: 'primary' }]);
const gradeBtns = box => choose(box, [
  { label: 'Again', value: 'again', cls: 'again' },
  { label: 'Good', value: 'good', cls: 'primary' },
  { label: 'Easy', value: 'easy' },
]);

async function exampleBlock(ex) {
  const v = await verse(ex.ref);
  return h('div', { class: 'example' },
    h('div', { class: 'ref' }, ex.ref.replace(/\./g, ' ')),
    verseRow(v.tokens, ex.id),
    h('div', { class: 'en' }, v.en));
}

const kicker = t => h('div', { class: 'kicker' }, t);

async function selfGraded(box, front, back) {
  const t0 = performance.now();
  box.append(...front);
  await revealBtn(box);
  const ms = performance.now() - t0;
  box.append(...(await back()));
  const grade = await gradeBtns(box);
  return { grade, ok: grade !== 'again', ms };
}

function lemma(box, it) {
  const front = [kicker('Word'),
    h('div', { class: 'big' }, word(it.tok, { hl: it.cite === 'in-word' ? it.tok.hl : null })),
    it.cite === 'bare' ? h('div', { class: 'note' }, 'Shown as it appears in the text.') : null,
    it.cite === 'in-word' ? h('div', { class: 'note' }, 'Highlighted part is the word; the rest is attached.') : null];
  return selfGraded(box, front.filter(Boolean), async () => {
    const out = [h('div', { class: 'ans' }, glossText(it.gloss, it.reviewed))];
    const others = (it.senses || []).filter(s => s.gloss !== it.gloss).slice(0, 2);
    if (others.length) out.push(h('div', { class: 'note' }, 'also: ' + others.map(s => s.gloss).join('; ')));
    out.push(await exampleBlock(it.example));
    return out;
  });
}

function morpheme(box, it) {
  const k = (state().cards[it.id]?.r || 0) % it.examples.length;
  const ex = it.examples[k];
  const front = [kicker('What does the highlighted part mean?'),
    h('div', { class: 'big' }, word(ex, { hl: ex.hl, hlc: ex.hlc, tr: 'tap' }))];
  return selfGraded(box, front, async () => {
    const out = [h('div', { class: 'ans' }, h('b', {}, it.label), ' = ', glossText(it.gloss, it.reviewed)),
      h('div', { class: 'note' }, ex.g)];
    const more = it.examples.filter((_, i) => i !== k).slice(0, 2);
    out.push(h('div', { class: 'row' }, more.map(e => h('div', { class: 'cell' }, word(e, { hl: e.hl, hlc: e.hlc, gloss: true })))));
    if (it.contrast) {
      out.push(kicker('Compare the long ending'),
        h('div', { class: 'row' }, it.contrast.slice(0, 2).map(e => h('div', { class: 'cell' }, word(e, { gloss: true })))));
    }
    return out;
  });
}

async function formCard(box, it, unit) {
  const k = (state().cards[it.id]?.r || 0) % it.examples.length;
  const ex = it.examples[k];
  const v = await verse(ex.ref);
  const facets = unit?.parse || [];
  const verseBox = h('div', { class: 'example' }, h('div', { class: 'ref' }, ex.ref.replace(/\./g, ' ')),
    verseRow(v.tokens, ex.id));
  const t0 = performance.now();
  if (!facets.length) {
    box.append(kicker('Read the highlighted verb in its verse'), verseBox);
    await revealBtn(box);
    const ms = performance.now() - t0;
    box.append(h('div', { class: 'ans' }, glossText(ex.g, ex.gr), h('span', { class: 'note' }, '  ' + solo(it.tr))),
      h('div', { class: 'note' }, it.parse), h('div', { class: 'en' }, v.en));
    const grade = await gradeBtns(box);
    return { grade, ok: grade !== 'again', ms };
  }
  // type 4: chip parse on the facets taught so far
  box.append(kicker('Parse the highlighted verb'), verseBox);
  const wanted = facets.filter(f => it.facets[f]);
  const picks = {};
  const chipBox = h('div', {});
  const submit = h('button', { class: 'primary', disabled: true }, 'Check');
  for (const f of wanted) {
    const row = h('div', { class: 'chips' }, h('span', { class: 'chiplabel' }, f === 'conj' ? 'form' : f === 'pgn' ? 'person' : f));
    for (const o of chipOptions(f)) {
      row.append(h('button', { class: 'chip', onclick: e => {
        picks[f] = o;
        row.querySelectorAll('.chip').forEach(c => c.classList.remove('sel'));
        e.currentTarget.classList.add('sel');
        submit.disabled = wanted.some(x => !picks[x]);
      } }, chipLabel(f, o)));
    }
    chipBox.append(row);
  }
  box.append(chipBox, h('div', { class: 'bar' }, submit));
  await new Promise(res => submit.addEventListener('click', res));
  const ms = performance.now() - t0;
  submit.parentNode.remove();
  const right = wanted.every(f => picks[f] === it.facets[f]);
  chipBox.querySelectorAll('.chips').forEach((row, i) => {
    const f = wanted[i];
    row.querySelectorAll('.chip').forEach(c => {
      c.disabled = true;
      if (c.textContent === chipLabel(f, it.facets[f])) c.classList.add('right');
      else if (c.classList.contains('sel')) c.classList.add('wrong');
    });
  });
  box.append(h('div', { class: right ? 'ans' : 'ans bad' }, right ? 'Correct' : 'Not quite'),
    h('div', { class: 'note' }, ex.g + ' · ' + it.parse), h('div', { class: 'en' }, v.en));
  await choose(box, [{ label: 'Next', value: 1, cls: 'primary' }]);
  return { grade: right ? 'good' : 'again', ok: right, ms };
}

function name(box, it) {
  const front = [kicker('Name'), h('div', { class: 'big' }, word(it.tok))];
  return selfGraded(box, front, async () => [
    h('div', { class: 'ans' }, glossText(it.gloss, it.reviewed)), await exampleBlock(it.example)]);
}

async function decode(box, it) {
  const t0 = performance.now();
  box.append(kicker('How is this read?'), h('div', { class: 'big' }, word(it.tok, { tr: 'none' })));
  const tr = solo(it.tok.tr);
  const opts = shuffle([tr, ...it.options]);
  const picked = await choose(box, opts.map(o => ({ label: o, value: o, cls: 'opt' })));
  const ms = performance.now() - t0;
  const ok = picked === tr;
  box.append(h('div', { class: ok ? 'ans' : 'ans bad' }, ok ? 'Correct' : `Read: ${tr}`),
    h('div', { class: 'note' }, solo(it.tok.g)));
  await choose(box, [{ label: 'Next', value: 1, cls: 'primary' }]);
  return { grade: null, ok, ms };
}

async function decodeRead(box, it) {
  const t0 = performance.now();
  box.append(kicker('Read it aloud'), h('div', { class: 'big' }, word(it.tok, { tr: 'none' })));
  await revealBtn(box);
  const ms = performance.now() - t0;
  box.append(h('div', { class: 'ans' }, solo(it.tok.tr)), h('div', { class: 'note' }, solo(it.tok.g)));
  const v = await choose(box, [{ label: 'Missed it', value: false, cls: 'again' }, { label: 'Got it', value: true, cls: 'primary' }]);
  return { grade: null, ok: v, ms };
}

// ctx.help: 'full' | 'interlinear' | 'unknown-only'; ctx.known(tok) = every lemma in the word introduced.
async function micro(box, it, ctx) {
  const t0 = performance.now();
  const taps = [];
  const row = h('div', { class: 'verse', dir: 'rtl' }, it.toks.map(t => {
    const show = ctx.help !== 'unknown-only' || !ctx.known(t);
    return word(t, { gloss: show, inVerse: true, tr: 'tap', onTap: (tok, w) => {
      taps.push(tok.id);
      if (!w.querySelector('.gl')) w.append(h('span', { class: 'gl' + (tok.gr ? '' : ' unrev') }, tok.g));
    } });
  }));
  box.append(kicker('Read'), h('div', { class: 'ref' }, it.ref.replace(/\./g, ' ')), h('div', { class: 'big' }, row));
  await choose(box, [{ label: 'Show translation', value: 1, cls: 'primary' }]);
  const ms = performance.now() - t0;
  const v = await verse(it.ref);
  box.append(h('div', { class: 'ans' }, it.toks.map(t => t.g).join(' ')), h('div', { class: 'en' }, v.en));
  const ok = await choose(box, [{ label: 'Not yet', value: false, cls: 'again' }, { label: 'Got it', value: true, cls: 'primary' }]);
  return { grade: null, ok, ms, taps };
}

export function present(item, box, ctx) {
  switch (item.kind) {
    case 'lemma': return lemma(box, item);
    case 'morpheme': return morpheme(box, item);
    case 'form': return formCard(box, item, ctx.unitOf(item));
    case 'name': return name(box, item);
    case 'decode': return decode(box, item);
    case 'decode-read': return decodeRead(box, item);
    case 'micro': return micro(box, item, ctx);
    default: throw new Error('unknown kind ' + item.kind);
  }
}

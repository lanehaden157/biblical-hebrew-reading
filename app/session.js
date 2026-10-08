// Today flow: lessons -> review box -> new items -> reading -> done line.
import { h } from './render.js';
import { D } from './data.js';
import { state, save } from './store.js';
import { isDue, review, GRADE } from './srs.js';
import { present } from './cards.js';
import { lessonView } from './lessons.js';

const DAY = 864e5;
const REVIEW_BOX_MS = 240e3;
const SCHEDULED = new Set(['lemma', 'morpheme', 'form', 'name']);
const GRAMMAR = new Set(['morpheme', 'form', 'name']);
export const MAX_UNIT = 3;

const S = () => state();
const unitDef = n => D.units.find(u => u.unit === n);

// ---------- selection ----------

function retention() {
  const rec = S().log.filter(e => SCHEDULED.has(e.k)).slice(-100);
  return rec.length >= 20 ? rec.filter(e => e.ok).length / rec.length : 1;
}

// Adaptive N (SPEC section 4). Adjusts at most once per window of sessions.
function adaptN() {
  const s = S();
  s.settings.n ??= 4;
  s.settings.nAt ??= 0;
  const win = s.sessions.slice(s.settings.nAt).slice(-5);
  if (win.length >= 3 && win.filter(x => x.over).length >= 3) {
    s.settings.n = Math.max(0, s.settings.n - 1); s.settings.nAt = s.sessions.length;
  } else if (win.length >= 5 && win.every(x => x.rsec < 180) && retention() >= 0.88) {
    s.settings.n = Math.min(8, s.settings.n + 1); s.settings.nAt = s.sessions.length;
  }
  const last = s.sessions.at(-1);
  if (last && Date.now() - new Date(last.d) >= 3 * DAY) s.settings.gap = true;
  return s.settings.gap ? 0 : s.settings.n;
}

function introduced(id) { return !!S().intro[id]; }

function advanceUnit() {
  const s = S();
  for (;;) {
    const items = D.byUnit[s.unit] || [];
    let done;
    if (s.unit === 0) done = items.every(i => s.decode[i.id]);
    else done = items.filter(i => GRAMMAR.has(i.kind)).every(i => introduced(i.id));
    if (!done || s.unit >= MAX_UNIT) return;
    s.unit++;
  }
}

function pickNew(n) {
  const s = S();
  const lem = D.lemmas.filter(i => !introduced(i.id));
  const gram = [];
  for (let u = 1; u <= s.unit; u++) for (const i of D.byUnit[u] || []) if (GRAMMAR.has(i.kind) && !introduced(i.id)) gram.push(i);
  const out = [];
  const pattern = ['L', 'G', 'L', 'G', 'L'];
  let li = 0, gi = 0;
  for (let k = 0; out.length < n; k++) {
    const want = pattern[k % 5];
    const a = want === 'L' ? lem[li] : gram[gi];
    const b = want === 'L' ? gram[gi] : lem[li];
    if (!a && !b) break;
    if (a) { out.push(a); want === 'L' ? li++ : gi++; } else { out.push(b); want === 'L' ? gi++ : li++; }
  }
  return out;
}

function knownLemma(key) { return introduced('L:' + key.replace(' ', '_')); }
function knownTok(t) {
  return t.p.every(([, lem, morph]) => !/^\d/.test(lem) || morph.startsWith('Np') || knownLemma(lem));
}

function pickReads(count) {
  const s = S();
  const out = [];
  const seen = id => (s.reads[id] || []);
  const pool = [];
  for (let u = s.unit; u >= 1; u--) for (const i of D.byUnit[u] || []) if (i.kind === 'micro') pool.push(i);
  const repeats = pool.filter(i => seen(i.id).length === 1 && Date.now() - new Date(seen(i.id)[0]) >= 3 * DAY);
  const fresh = pool.filter(i => seen(i.id).length === 0);
  for (const i of [...repeats, ...fresh]) { if (out.length < count) out.push(i); }
  if (out.length < count) for (const i of pool.filter(i => seen(i.id).length === 1 && !out.includes(i))) if (out.length < count) out.push(i);
  return out;
}

function pickDecode(kind, count) {
  return (D.byUnit[0] || []).filter(i => i.kind === kind && !S().decode[i.id]).slice(0, count);
}

function lessonsFor(newItems) {
  const s = S();
  const ids = new Set(newItems.map(i => i.id));
  const out = D.lessons.filter(l => !s.lessons[l.id] && l.unlocks.some(u => ids.has(u)));
  const generic = D.lessons.find(l => !s.lessons[l.id] && l.unit === s.unit && !l.unlocks.length);
  if (generic) out.unshift(generic);
  return out;
}

// ---------- UI ----------

function stage(root, label) {
  root.replaceChildren(h('div', { class: 'stage' }, h('button', { class: 'exit', onclick: () => window.dispatchEvent(new Event('exit-session')) }, 'Exit'), label));
  const box = h('div', { class: 'card' });
  root.append(box);
  window.scrollTo(0, 0);
  return box;
}

function wait(box, label) {
  return new Promise(res => box.append(h('div', { class: 'bar' }, h('button', { class: 'primary', onclick: res }, label))));
}

async function showItem(root, label, item, ctx) {
  const box = stage(root, label);
  const r = await present(item, box, ctx);
  const s = S();
  s.log.push({ t: Date.now(), id: item.id, k: item.kind, ok: r.ok, ms: Math.round(r.ms) });
  if (r.grade) {
    review(item.id, GRADE[r.grade]);
    s.intro[item.id] ??= new Date().toISOString();
  }
  if (item.kind === 'decode' || item.kind === 'decode-read') s.decode[item.id] = true;
  if (item.kind === 'micro') {
    (s.reads[item.id] ??= []).push(new Date().toISOString());
    for (const id of r.taps || []) s.taps.push({ t: Date.now(), id, ref: item.id });
  }
  save();
  return r;
}

function makeCtx() {
  const s = S();
  return {
    help: unitDef(s.unit)?.help || 'unknown-only',
    known: knownTok,
    unitOf: item => unitDef(item.unit),
  };
}

// ---------- session ----------

export async function runSession(root) {
  const s = S();
  advanceUnit();
  const ctx = makeCtx();
  const unit = s.unit;
  const n = s.settings.fiveMin ? 0 : (unit === 0 ? (s.sessions.length >= 2 ? 2 : 0) : adaptN());
  const boxMs = s.settings.fiveMin ? 180e3 : REVIEW_BOX_MS;
  const stats = { reviewed: 0, newN: 0, read: 0, rsec: 0, over: false };

  // new items and lessons first computed, shown in block order below
  const fresh = pickNew(n);
  const decodeNew = unit === 0 ? pickDecode('decode', 8) : [];

  // Block 1: reviews
  const queue = Object.keys(s.cards).filter(id => isDue(id) && D.items.has(id) && !s.quarantine?.includes(id))
    .sort((a, b) => new Date(s.cards[a].d) - new Date(s.cards[b].d)).map(id => D.items.get(id));
  const retried = new Set();
  const t0 = Date.now();
  while (queue.length && Date.now() - t0 < boxMs) {
    const it = queue.shift();
    const r = await showItem(root, 'Review', it, ctx);
    stats.reviewed++;
    if (r.grade === 'again' && !retried.has(it.id)) { retried.add(it.id); queue.splice(Math.min(4, queue.length), 0, it); }
  }
  stats.rsec = Math.round((Date.now() - t0) / 1000);
  stats.over = queue.length > 0;

  // Block 2: lessons + new items
  const todayNew = [...decodeNew, ...fresh];
  for (const l of lessonsFor(fresh)) {
    const box = stage(root, 'Lesson');
    box.append(lessonView(l));
    await wait(box, 'Got it');
    s.lessons[l.id] = new Date().toISOString();
    save();
  }
  const again = [];
  for (const it of todayNew) {
    const r = await showItem(root, 'New', it, ctx);
    if (SCHEDULED.has(it.kind)) { stats.newN++; if (r.grade === 'again') again.push(it); }
    else if (r.ok === false && it.kind === 'decode') again.push(it);
  }
  for (const it of again.filter(i => SCHEDULED.has(i.kind))) await showItem(root, 'New', it, ctx);

  // Block 3: reading
  await readBlock(root, ctx, stats, unit === 0 ? 5 : s.settings.fiveMin ? 1 : unit >= 3 ? 2 : 3);

  // Block 4: done
  s.sessions.push({ d: new Date().toISOString(), rsec: stats.rsec, over: stats.over, newN: stats.newN, read: stats.read });
  if (!stats.over) delete s.settings.gap;
  advanceUnit();
  save();
  await doneLoop(root, ctx, stats);
}

async function readBlock(root, ctx, stats, count) {
  const s = S();
  const items = s.unit === 0 ? pickDecode('decode-read', count) : pickReads(count);
  for (const it of items) { await showItem(root, 'Read', it, ctx); stats.read++; }
}

async function doneLoop(root, ctx, stats) {
  const s = S();
  for (;;) {
    const intro = Object.keys(s.intro).filter(i => i.startsWith('L:')).length;
    const box = stage(root, 'Done');
    box.append(h('div', { class: 'ans' }, 'Done for today.'),
      h('div', { class: 'note' }, `${stats.reviewed} reviewed · ${stats.newN} new · ${stats.read} read · ${intro} words introduced`));
    const act = await new Promise(res => box.append(h('div', { class: 'bar' },
      h('button', { class: 'primary', onclick: () => res('finish') }, 'Finish'),
      h('button', { onclick: () => res('read') }, 'More reading'),
      h('button', { onclick: () => res('drill') }, 'More drill'))));
    if (act === 'finish') return;
    if (act === 'read') {
      const before = stats.read;
      await readBlock(root, ctx, stats, 2);
      if (stats.read === before) { const b = stage(root, 'Read'); b.append(h('div', { class: 'note' }, 'Nothing new to read right now.')); await wait(b, 'OK'); }
    } else {
      const due = Object.keys(s.cards).filter(id => isDue(id) && D.items.has(id)).slice(0, 8).map(id => D.items.get(id));
      const items = due.length ? due : pickNew(2);
      if (!items.length) { const b = stage(root, 'Drill'); b.append(h('div', { class: 'note' }, 'Nothing to drill right now.')); await wait(b, 'OK'); continue; }
      for (const it of items) {
        const r = await showItem(root, due.length ? 'Review' : 'New', it, ctx);
        if (due.length) stats.reviewed++; else stats.newN++;
        void r;
      }
    }
  }
}

export function sessionInfo() {
  const s = S();
  advanceUnit();
  const dueN = Object.keys(s.cards).filter(id => isDue(id)).length;
  return { unit: s.unit, title: unitDef(s.unit)?.title, due: dueN };
}

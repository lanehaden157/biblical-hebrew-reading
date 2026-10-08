// Progress panel: coverage, accuracy, reading help rate, verses read, pace (M12 timing).
// No streaks, no missed-day counts, no backlog numbers.
import { h } from './render.js';
import { D, getJSON, chapterVerses } from './data.js';
import { state } from './store.js';

const median = a => { if (!a.length) return null; const s = [...a].sort((x, y) => x - y); return s[Math.floor(s.length / 2)]; };
const pct = (a, b) => (b ? (100 * a / b).toFixed(1) + '%' : 'n/a');

function known(s, key, morph) {
  if (morph.startsWith('Np')) return !!s.intro['N:' + key];
  return !!s.intro['L:' + key.replace(' ', '_')];
}

async function chapterCoverage(book, ch) {
  const s = state();
  let tokens = 0, ok = 0;
  const lemmas = new Set(), have = new Set();
  for (const v of await chapterVerses(book, ch)) {
    for (const t of v.tokens) {
      const parts = t.p.filter(([, lem]) => /^\d/.test(lem));
      if (!parts.length) continue;
      tokens++;
      let all = true;
      for (const [, lem, morph] of parts) {
        lemmas.add(lem);
        if (known(s, lem, morph)) have.add(lem); else all = false;
      }
      if (all) ok++;
    }
  }
  return { tokens, ok, lemmas: lemmas.size, have: have.size };
}

function stat(label, value, detail) {
  const d = h('div', { class: 'stat' }, h('div', { class: 'statv' }, value), h('div', { class: 'statl' }, label));
  if (detail) {
    const more = h('div', { class: 'note hid2' }, detail);
    d.addEventListener('click', () => more.classList.toggle('hid2'));
    d.append(more);
  }
  return d;
}

export async function progressView() {
  const s = state();
  const out = h('div', {});
  const lemIds = Object.keys(s.intro).filter(i => i.startsWith('L:'));
  const total = (await getJSON('measures/lemma_ranks.json')).reduce((a, x) => a + x.count, 0);
  const have = lemIds.reduce((a, id) => a + (D.items.get(id)?.count || 0), 0);
  const [e3, e14] = await Promise.all([chapterCoverage('Exod', 3), chapterCoverage('Exod', 14)]);
  const det = c => `${c.ok} of ${c.tokens} words fully known; ${c.have} of ${c.lemmas} distinct words known. Names count as known only once learned.`;

  out.append(h('h2', {}, 'Progress'),
    stat('Exodus 3 words known', pct(e3.ok, e3.tokens), det(e3)),
    stat('Exodus 14 words known', pct(e14.ok, e14.tokens), det(e14)),
    stat('Narrative corpus covered by your words', pct(have, total), `${have.toLocaleString()} of ${total.toLocaleString()} word tokens`),
    stat('Words introduced', `${lemIds.length} / ${D.lemmas.length}`));

  const parse = s.log.filter(e => e.k === 'parse').slice(-40);
  out.append(stat('Parse accuracy (last 40)', parse.length >= 5 ? pct(parse.filter(e => e.ok).length, parse.length) : 'not enough yet'));
  const sched = s.log.filter(e => ['lemma', 'morpheme', 'form', 'name', 'parse'].includes(e.k) && !e.nw).slice(-100);
  out.append(stat('Recall on reviews (last 100)', sched.length >= 20 ? pct(sched.filter(e => e.ok).length, sched.length) : 'not enough yet'));
  const dec = s.log.filter(e => e.k === 'decode').slice(-30);
  if (dec.length) out.append(stat('Decoding checks (last 30)', pct(dec.filter(e => e.ok).length, dec.length), `median ${(median(dec.map(e => e.ms)) / 1000).toFixed(1)} s`));
  const rd = s.log.filter(e => e.k === 'micro').slice(-20);
  const words = rd.reduce((a, e) => a + (e.w || 0), 0);
  if (rd.length) out.append(stat('Help taps per 100 words (last 20 readings)', words ? (100 * rd.reduce((a, e) => a + (e.taps || 0), 0) / words).toFixed(0) : 'n/a'));
  const verses = new Set(Object.keys(s.reads).map(id => id.split(':')[1]));
  out.append(stat('Verses read', String(verses.size)));

  // M12 pace: real timings
  const pace = h('div', { class: 'note' });
  const med = {};
  for (const e of s.log.filter(x => !x.nw)) (med[e.k] ??= []).push(e.ms);
  const lines = Object.entries(med).filter(([, v]) => v.length >= 5).map(([k, v]) => `${k}: ${(median(v) / 1000).toFixed(1)} s median (${v.length})`);
  const secs = s.sessions.filter(x => x.sec).map(x => x.sec);
  if (secs.length) lines.push(`session: ${(median(secs) / 60).toFixed(1)} min median (${secs.length} sessions)`);
  const recent = s.sessions.filter(x => Date.now() - new Date(x.d) < 28 * 864e5).length;
  if (s.sessions.length) lines.push(`${(recent / 4).toFixed(1)} sessions a week over the last 4 weeks`);
  const span = s.sessions.length ? (Date.now() - new Date(s.sessions[0].d)) / 864e5 : 0;
  pace.append(...lines.flatMap(l => [l, h('br')]));
  if (span < 30) pace.append('A pace forecast appears after 30 days of use.');
  out.append(h('h3', {}, 'Your pace'), pace);
  return out;
}

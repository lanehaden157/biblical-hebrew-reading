// Loads generated JSON from ../data relative to this module (works under a Pages subpath).
const BASE = new URL('../data/', import.meta.url);
const cache = new Map();

export function getJSON(path) {
  if (!cache.has(path)) {
    cache.set(path, fetch(new URL(path, BASE)).then(r => {
      if (!r.ok) throw new Error(`${path}: ${r.status}`);
      return r.json();
    }));
  }
  return cache.get(path);
}

export const D = { units: [], lessons: [], toks: {}, items: new Map(), lemmas: [], byUnit: {} };

export async function loadAll() {
  const [units, lessons, lem] = await Promise.all([
    getJSON('units.json'), getJSON('lessons.json'), getJSON('items/lemmas.json'),
  ]);
  D.units = units.units;
  D.lessons = lessons.lessons;
  D.toks = lessons.toks;
  D.lemmas = lem.items;
  for (const it of D.lemmas) D.items.set(it.id, it);
  const files = await Promise.all(D.units.map(u => getJSON(u.items)));
  D.units.forEach((u, i) => {
    D.byUnit[u.unit] = files[i].items;
    for (const it of files[i].items) D.items.set(it.id, it);
  });
}

// ref "Exod.3.1" -> verse {v, tokens, en}
export async function verse(ref) {
  const [book, ch, v] = ref.split('.');
  const c = await getJSON(`text/${book}/${ch}.json`);
  return c.verses.find(x => x.v === +v);
}

export async function chapterVerses(book, ch) {
  return (await getJSON(`text/${book}/${ch}.json`)).verses;
}

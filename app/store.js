/**
 * Persistence. localStorage only, per the locked decision (per-device, no sync).
 *
 * Hard rule 6: every persisted object carries a schemaVersion, and review
 * history is never silently destroyed. Review history is the only thing in this
 * project that cannot be rebuilt from the corpus -- deck, glosses and
 * transliterations all regenerate from /pipeline in minutes; six months of FSRS
 * scheduling state does not. Before any migration the previous state is copied
 * to hebrew:backup:v<n> and left there.
 */

const KEY = 'hebrew:v1';
const SCHEMA_VERSION = 1;

export const DEFAULT_SETTINGS = {
  theme: 'system',      // 'system' | 'light' | 'dark'
  sound: true,           // muted by the iPhone silent switch, so this is harmless when off-limits
  newPerDay: 5,         // 600 lemmas at 5/day is ~4 months of introductions
  dailyCap: 40,         // hard rule 5: never show a wall of due cards
};

function emptyState() {
  return {
    schemaVersion: SCHEMA_VERSION,
    settings: { ...DEFAULT_SETTINGS },
    cards: {},     // lemma_id -> { due, stability, ..., introducedOn }
  };
}

/** Local calendar day as YYYY-MM-DD. Deliberately local, not UTC: "cards I
 *  started today" should mean the user's today, not Greenwich's. */
export function today(now = new Date()) {
  const p = (n) => String(n).padStart(2, '0');
  return `${now.getFullYear()}-${p(now.getMonth() + 1)}-${p(now.getDate())}`;
}

function migrate(raw) {
  const from = raw.schemaVersion;
  if (from === SCHEMA_VERSION) return raw;

  // Pre-1.0 allowance in hard rule 6: reset rather than migrate, but never
  // silently -- keep the old state under a backup key and say so.
  try {
    localStorage.setItem(`hebrew:backup:v${from}`, JSON.stringify(raw));
  } catch (e) {
    console.warn('could not write pre-migration backup', e);
  }
  console.warn(
    `Stored state is schemaVersion ${from}, app expects ${SCHEMA_VERSION}. ` +
    `The old state was preserved at hebrew:backup:v${from} and review history was reset.`
  );
  const fresh = emptyState();
  fresh.resetNotice = { from, at: new Date().toISOString() };
  return fresh;
}

let cache = null;

export function load() {
  if (cache) return cache;
  let raw = null;
  try {
    const s = localStorage.getItem(KEY);
    if (s) raw = JSON.parse(s);
  } catch (e) {
    console.warn('stored state unreadable, starting fresh', e);
  }
  if (!raw || typeof raw !== 'object') {
    cache = emptyState();
  } else {
    cache = migrate(raw);
    cache.settings = { ...DEFAULT_SETTINGS, ...(cache.settings || {}) };
    cache.cards = cache.cards || {};
  }
  return cache;
}

export function save() {
  if (!cache) return;
  try {
    localStorage.setItem(KEY, JSON.stringify(cache));
  } catch (e) {
    // Quota, or Safari private mode. Loud, because losing history silently is
    // the one failure mode hard rule 6 exists to prevent.
    console.error('COULD NOT SAVE review state', e);
    alert('Could not save your progress. Export a backup from Settings.');
  }
}

export function update(fn) {
  const s = load();
  fn(s);
  save();
  return s;
}

export function settings() {
  return load().settings;
}

export function setSetting(key, value) {
  return update((s) => { s.settings[key] = value; });
}

export function exportBlob() {
  const s = load();
  return new Blob([JSON.stringify(s, null, 2)], { type: 'application/json' });
}

export function exportFilename() {
  return `hebrew-progress-${today()}.json`;
}

/** Counts of cards first introduced on a given local day. */
export function introducedOn(day) {
  const cards = load().cards;
  let n = 0;
  for (const id in cards) if (cards[id].introducedOn === day) n++;
  return n;
}

export function resetAll() {
  const s = load();
  try {
    localStorage.setItem(`hebrew:backup:manual-${Date.now()}`, JSON.stringify(s));
  } catch (e) {
    console.warn('could not write manual-reset backup', e);
  }
  cache = emptyState();
  save();
  return cache;
}

export const SCHEMA = { KEY, SCHEMA_VERSION };

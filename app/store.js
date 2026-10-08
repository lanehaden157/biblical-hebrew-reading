// Versioned localStorage store. Schema v1; bump and migrate in load() when it changes.
const KEY = 'hebrew.v1';
const LOG_CAP = 4000;

function fresh() {
  return {
    v: 1,
    unit: 0,
    cards: {},      // id -> {d,s,df,ed,sd,r,l,st,lr}  (ts-fsrs card, dates as ISO)
    intro: {},      // id -> ISO date first introduced
    lessons: {},    // lesson id -> ISO date seen
    reads: {},      // reading id -> [ISO dates]
    log: [],        // {t, id, k, ok, ms}
    sessions: [],   // {d, rsec, over, newN, read}
    settings: { translit: false, fiveMin: false },
    taps: [],       // {t, id, ref}
    decode: {},     // unit 0 item id -> true (seen)
    reports: [],    // {t, id, kind, reason, note, toks}
    quarantine: [], // item ids hidden after a report
  };
}

let S = fresh();

export function load() {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) S = Object.assign(fresh(), JSON.parse(raw));
  } catch (e) { /* unavailable: run in memory */ }
  return S;
}

export function save() {
  if (S.log.length > LOG_CAP) S.log = S.log.slice(-LOG_CAP);
  try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) { /* ignore */ }
}

export const state = () => S;

// Replace everything (import). Caller validates.
export function replace(obj) {
  S = Object.assign(fresh(), obj);
  save();
}

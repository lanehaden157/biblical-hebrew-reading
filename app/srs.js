// Thin wrapper over ts-fsrs (pinned CDN build). Do not reimplement scheduling here.
import { fsrs, generatorParameters, createEmptyCard, Rating } from 'https://cdn.jsdelivr.net/npm/ts-fsrs@4.7.0/+esm';
import { state } from './store.js';

const f = fsrs(generatorParameters({ enable_fuzz: true, request_retention: 0.88 }));
export const GRADE = { again: Rating.Again, good: Rating.Good, easy: Rating.Easy };

function pack(c) {
  return { d: c.due.toISOString(), s: c.stability, df: c.difficulty, ed: c.elapsed_days,
    sd: c.scheduled_days, r: c.reps, l: c.lapses, st: c.state,
    lr: c.last_review ? c.last_review.toISOString() : null };
}
function unpack(p) {
  return { due: new Date(p.d), stability: p.s, difficulty: p.df, elapsed_days: p.ed,
    scheduled_days: p.sd, reps: p.r, lapses: p.l, state: p.st,
    last_review: p.lr ? new Date(p.lr) : undefined };
}

export function isDue(id, now = new Date()) {
  const p = state().cards[id];
  return !!p && new Date(p.d) <= now;
}

// Returns the new due Date.
export function review(id, rating, now = new Date()) {
  const p = state().cards[id];
  const card = p ? unpack(p) : createEmptyCard(now);
  const next = f.next(card, now, rating).card;
  state().cards[id] = pack(next);
  return next.due;
}

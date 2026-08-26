/**
 * Scheduling. Thin wrapper over ts-fsrs -- the locked decision is to use it,
 * not to reimplement a scheduler, so this file only handles two things the
 * library does not: serialising cards to JSON-safe values, and deciding what
 * goes in today's queue.
 *
 * Version is pinned deliberately (never @latest): a scheduler that silently
 * changes behaviour between page loads would corrupt months of intervals.
 * This CDN import is the one external request the app makes, and the one thing
 * standing between this app and working offline -- when offline matters, vendor
 * the file into the repo rather than dropping ts-fsrs.
 */
import {
  fsrs, generatorParameters, createEmptyCard, Rating, State,
} from 'https://cdn.jsdelivr.net/npm/ts-fsrs@5.4.1/dist/index.mjs';

import { load, today } from './store.js';

const scheduler = fsrs(generatorParameters({ enable_fuzz: true }));

/** Three grades, not four. `Hard` is dropped: it is the button people grade
 *  inconsistently, and inconsistent grading is worse for FSRS than coarser
 *  grading. Values are ts-fsrs Rating members. */
export const GRADES = [
  { key: 'again', label: 'Again', rating: Rating.Again },
  { key: 'good',  label: 'Good',  rating: Rating.Good  },
  { key: 'easy',  label: 'Easy',  rating: Rating.Easy  },
];

export { State };

/** ts-fsrs returns Dates; localStorage needs strings. Round-trip is safe
 *  because CardInput accepts `Date | number | string` for date fields. */
function toStored(card) {
  return {
    due: card.due instanceof Date ? card.due.toISOString() : card.due,
    stability: card.stability,
    difficulty: card.difficulty,
    elapsed_days: card.elapsed_days,
    scheduled_days: card.scheduled_days,
    learning_steps: card.learning_steps,
    reps: card.reps,
    lapses: card.lapses,
    state: card.state,
    last_review: card.last_review
      ? (card.last_review instanceof Date ? card.last_review.toISOString() : card.last_review)
      : undefined,
  };
}

export function newCard(now = new Date()) {
  return toStored(createEmptyCard(now));
}

/** Preview the interval each grade would produce, for the button captions. */
export function preview(stored, now = new Date()) {
  const out = {};
  for (const g of GRADES) {
    const { card } = scheduler.next(stored, now, g.rating);
    out[g.key] = describeInterval(now, card.due);
  }
  return out;
}

export function applyGrade(stored, gradeKey, now = new Date()) {
  const g = GRADES.find((x) => x.key === gradeKey);
  if (!g) throw new Error(`unknown grade: ${gradeKey}`);
  const { card } = scheduler.next(stored, now, g.rating);
  return toStored(card);
}

export function describeInterval(from, due) {
  const ms = new Date(due).getTime() - new Date(from).getTime();
  const mins = Math.round(ms / 60000);
  if (mins < 1) return 'now';
  if (mins < 60) return `${mins}m`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${hours}h`;
  const days = Math.round(hours / 24);
  if (days < 31) return `${days}d`;
  const months = Math.round(days / 30.4);
  if (months < 12) return `${months}mo`;
  return `${(days / 365).toFixed(days < 730 ? 1 : 0)}y`;
}

export function isDue(stored, now = new Date()) {
  return new Date(stored.due).getTime() <= now.getTime();
}

/** Deck entries flagged non-drillable (e.g. H853 'et, which has no English
 *  translation and can't be recalled from a gloss) never enter the SRS
 *  queue -- they're still "known" for readers/lessons, just never graded. */
function drillableEntries(deck) {
  return deck.filter((e) => e.drillable !== false);
}

// Ranks 1-25 of the deck are ~half function words (prepositions/particles/
// conjunctions), which front-loads the hardest, most abstract material into
// the exact moment there's the least context to decode it. Cap the standing
// ratio of introduced function words to 1-in-6 -- computed cumulatively over
// every card ever introduced, not per session, so it holds as a property of
// the whole curriculum. A function word skipped today just waits for its
// turn on a later day once enough content words have "earned" it; since
// function words are well under 1-in-6 of the whole deck, nothing is ever
// blocked forever.
const FUNCTION_WORD_RATIO = 1 / 6;

/**
 * Build the session queue.
 *
 * Hard rule 5: cap the queue and quietly defer the rest, so coming back after a
 * three-week gap shows a normal session rather than 300 cards. Overflow is not
 * mentioned in the UI -- deferred cards simply stay due and surface tomorrow.
 *
 * New cards are introduced in frequency order (rank 1 first), which is also
 * roughly easiest-first, and are spread evenly through the reviews rather than
 * front-loaded, so a session does not open with a run of unfamiliar words.
 *
 * `keyFn` maps a deck entry to its card key in store.cards. Defaults to
 * lemma_id (vocab's key). Parse decks pass their own, since parse cards key
 * by word occurrence, not lemma -- multiple entries share a lemma_id there.
 * newPerDay/dailyCap counting is scoped to this deck's own keys, not every
 * card in storage, so two decks sharing one cards object (vocab and parse)
 * get independent pacing budgets rather than silently competing for one.
 */
export function buildQueue(rawDeck, now = new Date(), keyFn = (e) => e.lemma_id) {
  const state = load();
  const { dailyCap, newPerDay } = state.settings;
  const cards = state.cards;
  const deck = drillableEntries(rawDeck);
  const deckKeys = new Set(deck.map(keyFn));

  const due = [];
  for (const entry of deck) {
    const c = cards[keyFn(entry)];
    if (c && isDue(c, now)) due.push({ entry, card: c, isNew: false });
  }
  due.sort((a, b) => new Date(a.card.due) - new Date(b.card.due));

  const introducedToday = Object.keys(cards)
    .filter((k) => deckKeys.has(k) && cards[k].introducedOn === today(now)).length;
  const newBudget = Math.max(0, Math.min(
    newPerDay - introducedToday,
    dailyCap - due.length
  ));

  let introducedTotal = 0;
  let introducedFn = 0;
  for (const entry of deck) {
    if (cards[keyFn(entry)]) {
      introducedTotal++;
      if (entry.is_function_word) introducedFn++;
    }
  }

  const fresh = [];
  for (const entry of deck) {
    if (fresh.length >= newBudget) break;
    if (cards[keyFn(entry)]) continue;
    if (entry.is_function_word && (introducedFn + 1) > (introducedTotal + 1) * FUNCTION_WORD_RATIO) {
      continue; // defer to a later day, once more content words have been introduced
    }
    fresh.push({ entry, card: null, isNew: true });
    introducedTotal++;
    if (entry.is_function_word) introducedFn++;
  }

  const reviews = due.slice(0, Math.max(0, dailyCap - fresh.length));
  return {
    queue: interleave(reviews, fresh),
    deferred: Math.max(0, due.length - reviews.length),
    dueTotal: due.length,
  };
}

function interleave(reviews, fresh) {
  if (!fresh.length) return reviews;
  if (!reviews.length) return fresh;
  const out = [];
  const step = reviews.length / fresh.length;
  let f = 0;
  for (let i = 0; i < reviews.length; i++) {
    out.push(reviews[i]);
    while (f < fresh.length && (f + 1) * step <= i + 1) out.push(fresh[f++]);
  }
  while (f < fresh.length) out.push(fresh[f++]);
  return out;
}

/** Counts for the settings screen. Not shown during a drill -- no streaks, no
 *  progress bars to feel bad about (hard rule 5). */
export function stats(rawDeck, now = new Date(), keyFn = (e) => e.lemma_id) {
  const cards = load().cards;
  const deck = drillableEntries(rawDeck);
  let seen = 0, learning = 0, review = 0, dueNow = 0;
  for (const entry of deck) {
    const c = cards[keyFn(entry)];
    if (!c) continue;
    seen++;
    if (c.state === State.Review) review++;
    else learning++;
    if (isDue(c, now)) dueNow++;
  }
  return { seen, learning, review, dueNow, total: deck.length };
}

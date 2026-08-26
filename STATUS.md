# Status / phase history

Append-only, by phase. `git log` is the commit-level history; this is the narrative one —
what was built, key decisions, and real bugs/corrections worth remembering. Kept out of
`CLAUDE.md` so that file doesn't grow every phase.

## Phases 1–2: Tier 0–1 (vocab)

Top-600 lemmas curated and verified; vocab SRS shipped (3-stage reveal, 3 grade buttons,
theme, sound). Haptics attempted, dropped — confirmed they don't fire in iOS Safari.
Session-length tracking was built, then deliberately removed as a guilt-mechanic hard
rule 5 exists to keep out.

## Phase 3: Parsing gym, Qal strong verbs

`build_parse_qal.py` generates Qal-strong forms restricted to the 181 verb lemmas already
in the vocab deck (34 of 41 strong-root lemmas are actually attested in Qal in the
corpus); 2,211 entries. Parse tab shares one SRS queue with vocab via a `keyFn` param so
the two decks don't compete for daily budget.

## Phase 4: Reader, Jonah 1

254 words. Per-word gloss composed from morphemes; deliberately **no POS label** shown,
since a lemma-level guess can be wrong for a specific occurrence (H3373 tags both a verb
and a noun in this chapter under one Strong's number). Read tab: tap-to-reveal, no
grading, multiple words can stay open at once, unfamiliar words underlined.

## Phase 5: Reader finishes Jonah (chapters 2–4)

Same pipeline extended through the rest of the book. Jonah 2: 112 words, 72.3% already
known. Jonah 3: 139 words, 82.0% known. Jonah 4: 183 words, 80.3% known. Read tab
generalized to a chapter list + switcher instead of one hardcoded file.

**Occurrence-specific gloss corrections** (checked against BDB, not the dictionary's lead
sense): *gal* = "wave" not "heap of ruins" (2:4); *manah* = "appoint" not "weigh out"
(fish appointed, 2:1); *qetsev* = "roots" (of mountains) not "shape/base"; *ta'am* =
"decree" not "taste" (3:7); *qadam* = "be quick to act" not "go before" (4:2). Confirmed
`alaph`/`ataph` (2 & 4) are genuinely distinct roots that happen to share a sense —
kept separate, not merged.

## Phase 5: Parse-tab bug fixes

Two real morph-code bugs, confirmed against the OSHB spec: weqatal was mislabeled
"yiqtol"; genuine yiqtol wasn't matched at all (silently missing, not mislabeled). Also,
`surface_form` had been stripping prefixes/suffixes down to a fragment that isn't a real
word — fixed to show the whole printed word, split into prefix/verb/suffix spans.
Weqatal added as its own conjugation; deck grew 2,211 → 2,819.

Separately found: word-initial shuruq vav was transliterating as "w" instead of "u-",
affecting 159 of 2,819 cards. Fixed in `transliterate.py`; every dependent data file
rebuilt.

## Phase 5: Learn tab, all five lesson groups

Corpus frequency counts (not guesswork) set the curriculum order: group 1 — prefixes/
suffixes (vav, definite article, the four inseparable prepositions, pronominal suffixes,
relative and interrogative particles); group 2 — construct chains (35% of nouns in Jonah);
group 3 — the verb system (binyanim, aspect, vav-consecutive, participles, infinitive
construct, commands); groups 4–5 — remaining noun-phrase items and sentence-level syntax.
41 lessons total across the five groups, all real Jonah words/phrases.

Notable curatorial calls:
- Group 3's binyan example (Nafal, Hiphil vs. Qal) was chosen because both stems are
  attested for that root **in the same verse** (1:7) — found by cross-tabulating the
  whole book rather than picking an assumed "typical" contrast pair.
- Group 4 deliberately includes *goralot* ("lots," 1:7) — masculine despite a
  feminine-looking plural ending — so the gender lesson doesn't overclaim.
- Group 5's word-order lesson pairs the default VSO order against a real deviation
  (subject fronted for a scene change, 1:5) instead of only asserting the exception.
- A "plain" role (no highlight split) was added for groups 4–5's multi-word phrase
  examples, since forcing them into construct/absolute roles would've been a false claim.

One in-browser catch: an example's note claimed two word-forms were "completely
identical" when they actually differ by an invisible trailing shva — caught by reading
the rendered page, not by the verifier (which only checks shipped-vs-recomputed
agreement, not whether the prose claim is true).

The Learn tab's original concept list is now fully built across all five groups.

## Phase 5: Optional cross-device sync (GitHub Gist)

Lane chose auto-sync over a manual-only import after being asked directly. `sync.js` is
fully opt-in — zero network requests until a token is pasted in Settings — and round-trips
through a private Gist rather than the app's own repo. The token is stored in its own
localStorage key, confirmed never present in the export blob. Merge is per-card (based on
`reps`/`last_review`), so reviewing on two devices before either syncs doesn't let one
session overwrite the other. Settings preferences are per-device and intentionally not
merged. Known accepted limitation: no concurrency check on the Gist write — fine for one
person's few devices, not for real multi-user sync.

**Correction from real use:** Lane found GitHub's fine-grained-token UI doesn't actually
expose a Gists scope, despite the docs listing one. Verified independently rather than
assumed to be user error. Switched to a classic token with only the "gist" scope checked
— preserves the exact same "leaked token can't touch anything else" property.

## Phase 5: Undo this session's reviews

An in-memory-only snapshot of `cards`, taken on first load, backs "Undo this session's
reviews" (narrower than full Reset, which still wipes everything with its own backup).
Fixed `resetAll()` to also clear the snapshot so it doesn't leave a confusing "undo the
reset" button behind.

## Phase 5: Three bugs found only through real phone use

- **Sync could silently miss the last batch** if the app closed inside the 3s debounce
  window. Fixed with `sync.flush()` on `visibilitychange`/`pagehide`.
- **"New words per day" caption** always divided the full 600-word deck by the daily
  rate, so it never reflected actual progress. Fixed to show started vs. remaining.
- **Parse-card root highlight was wrong**, not just cosmetic: the highlighted span
  included conjugation-marking letters (preformatives/afformatives), not just the root
  consonants, on real cards Lane was reviewing (`yimshal`, `wekhafarta`). Fixed by
  isolating the true root span (tolerating Hebrew's plene spelling rather than requiring
  strict letter adjacency) and giving conjugation-marking material its own color instead
  of sharing the root's green.

## Phase 5: Real-usage examples for function words

51 lemmas (prepositions/conjunctions/particles/etc. — the whole closed set). Reveal is an
optional expand at the definition stage, not a new mandatory step. 155 curated,
hand-picked examples; every Hebrew string still pulled by word id, never hand-typed.

One bug caught before shipping: `transliterate()` (a per-word function) was called on a
whole verse at once and silently dropped every space. Fixed to transliterate per word and
rejoin.

## Phase 5: Shortened examples + card-flip reveal

Full verses were "too long," so all 155 examples were re-curated down to an explicit
phrase boundary, and the reveal became a card flip (CSS `rotateY`) instead of an
expanding panel; grading is withheld while flipped.

Re-curating surfaced two pre-existing curation bugs — both cases where an ambiguous verse
has the target word (e.g. *'el*, *lema'an*) appearing twice, and the wrong occurrence had
been targeted. Both fixed by retargeting the word id, not the gloss.

One flip-animation bug: the guard resetting the flip state relied on `requestAnimationFrame`,
which doesn't fire when the automated preview pane isn't visibly composited — so every flip
after the first silently did nothing there. Fixed to reset synchronously instead.

## Phase 5: Highlight the target word on the flip-back face

Trigger: Lane flagged what looked like a wrong example (an "mi" card whose glosses never
say "from") that was actually just idiomatic translation — but with nothing marking which
word was even being taught, there was no way to tell the difference. Fixed by highlighting
the exact Hebrew word and its closest English counterpart in the same accent green used
elsewhere, plus a short note on the ~24/155 examples where the correspondence isn't a
clean one-to-one match (e.g. the direct-object marker, which has no English equivalent at
all).

## Phase 5: particle curriculum, tier 1

Cut 9 Aramaic lemmas (Ezra/Daniel; corpus-frequency count pulled them into top-600 despite
this being a Hebrew course) and 2 poetry-only particles (selah, bal) from the deck, 600 →
589 — curation-stage filter, `top600.json` itself is untouched. `verify_vocab_deck.py`'s
Aramaic-gloss check caught 5 more than the 4 first spotted; corpus language-tags confirmed
all 9. `H853` ('et, untranslatable) pulled from the SRS queue (`drillable: false`) but
still "known" for readers. New `is_function_word` flag caps new-card introductions to a
standing 1-in-6 ratio (front of deck was ~48% function words). 11 particles got a curated
`core_schema` field — one line unifying their scattered glosses — shown on the card.

Cuts/schemas live in `curate_batch_*.py` (re-run, not hand-patched), so a future regen
won't resurrect them. `build_vocab_deck.py` renumbers post-cut ranks, keeps the original
as `source_rank`.

## Phase 5: particle curriculum, tier 1b (examples expanded + rotation)

The 11 core-schema particles went from 3 static examples to 10 each (76 new, all
narrative prose, diversified across Exodus/Numbers/Deuteronomy/Joshua/Judges/Ruth/Samuel/
Kings/Jonah rather than all-Genesis). `vocab.js` now rotates 3 at a time per review —
shuffled per full cycle through a lemma's set (seeded on lemma+cycle, so a stray
re-render never swaps examples mid-read, only a re-grade does), guaranteeing every
example gets seen before any repeat. Lemmas at 3 examples don't rotate — nothing to.

`build_function_word_examples.py` gained `TIER_TARGET` (10 for the 11 tier-1 lemmas,
falling back to the old max(3, sense-count) rule for everyone else); tier 2 (contrast-
pair particles, 5 each) is planned but not yet scoped or built. `verify_function_word_examples.py`
and `selftest.html` independently redeclare `TIER_TARGET` rather than trusting the build
script's copy. 155 → 213 examples total, 45 → still 45 lemmas.

## Phase 5: particle curriculum, tier B (the multi-sense-but-no-schema set)

19 particles headed for eventual contrast-pair treatment ('el vs le-, 'et vs `im, gam vs
'af, etc.) went from 3 examples to 5 (37 new, same narrative-prose/cross-canon sourcing as
tier 1b, Jonah-weighted where good material existed — F-s and H1157 landed 2-3 Jonah
examples each). `TIER_TARGET` now covers 30 lemmas (11 at 10, 19 at 5); 15 stay at the
baseline 3. 213 → 250 examples. Caught one bad target word id (H3651/ken in Josh.2.21 --
had grabbed the neighboring pronoun "hu" by mistake) via the build script's own lemma-match
check, not by eye.

## Next

Contrast-pair particles (the 19 above, paired up — 'el vs le-, 'et vs `im, etc.) — Lane
wants to brainstorm the format more before building (flashcards may not fit). Learn tab's
5-group concept list is fully built; further groups are new, unscoped work.
Tiers 3–4 (weak verbs, derived stems) not yet scoped. Reader goes to Ruth next.

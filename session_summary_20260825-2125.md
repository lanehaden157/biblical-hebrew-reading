# Session summary — 2026-08-25

**Done:** Fixed truncation/corruption in CLAUDE.md (cut-off hard rule 6, duplicate "Strong
suggestions" header, "Eead" typo, missing bullet markers, dangling sentences) left over from
a prior edit. Did not restore the deleted Commands block (dead weight, per Lane). Reviewed
STATUS.md's condensation from the same edit — that one was a clean rewrite, left untouched.
Created this three-file log system per updated global instructions.

Then: Lane's complaint that early particles (be-, le-, min, `al, ki, etc.) have broad,
overlapping English glosses and only 3 static Genesis-heavy examples each. Agreed a plan —
core schemas for particles that need them, rotating diversified examples, cloze drill
deferred — and split it into two passes. Built tier 1: cut 9 Aramaic lemmas (found 5 more
than initially spotted, via `verify_vocab_deck.py`'s own check) and 2 poetry-only particles
from the vocab deck (600→589); pulled H853 ('et) out of the SRS queue entirely (no English
equivalent to recall); added a standing 1-in-6 cap on new function-word introductions
(front of deck was ~48% function words); added a curated `core_schema` field to 11
particles, rendered on the vocab card. Cuts/schemas live in `curate_batch_*.py` so a
future regen won't silently undo them. Full pipeline re-verified end to end.

Then Lane approved tier 1 for real: cut tier B's planned count from 6→5 (not built yet),
and asked to build tier A (10 examples for the 11 schema particles) first. Curated 76 new
examples by hand from the corpus (word ids + phrase boundaries + glosses), diversified
across Exodus/Numbers/Deuteronomy/Joshua/Judges/Ruth/1-2 Samuel/1-2 Kings/Jonah instead of
Genesis-only. Added `TIER_TARGET` to `build_function_word_examples.py` (and independently
to `verify_function_word_examples.py` and `selftest.html`) so a future shrink is caught.
Added rotation to `vocab.js`: 3 examples shown per review, shuffled per full cycle through
a lemma's set, seeded on (lemma, cycle) so re-renders don't reshuffle mid-read, only
re-grades advance it. selftest.html had one stale hardcoded check (51 target lemmas,
should've been 45) that Lane caught by actually running it — fixed.

Then Lane asked to move straight to tier B (the 19 multi-sense-but-no-schema particles):
curated 37 more examples the same way (word ids + phrase boundaries + glosses, 3→5 each,
narrative prose, cross-canon, Jonah-weighted where the material existed). `TIER_TARGET`
extended in all three places (build/verify/selftest). One bad word id (H3651/ken in
Josh.2.21, grabbed a neighboring pronoun by mistake) caught by the build script's own
lemma-match check before it ever shipped. 213 → 250 examples.

**Open:** Contrast-pair particles (the 19 tier-B lemmas, paired up) not built — Lane wants
to brainstorm the format first, flashcards may not fit. `selftest.html` re-run by Lane
after the tier-1a fix and passed; the tier-1b/B example expansions and rotation haven't
been eyeballed in-browser yet — per working style, that's on Lane.

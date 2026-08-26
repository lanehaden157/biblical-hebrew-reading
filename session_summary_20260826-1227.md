# Session summary — 2026-08-26

**Done:** Continued the particle-curriculum work from 2026-08-25. Ran a corpus-frequency
check on candidate "contrast pairs" before building anything — most turned out to be a
register split (she- 91% poetry, hen/'akh/kemo similarly skewed vs their prose-heavy
counterparts), not a real confusion worth drilling as a pair. Narrowed to what the data
actually supported, per Lane's go-ahead ("push everything"):

- Merged H854 ('et) into H5973 (`im) as one vocab card — both just mean "with." New
  `MERGED_LEMMAS` in `build_vocab_deck.py` (drillable:false + `merged_with` pointer);
  `build_function_word_examples.py` folds H854's 5 examples into H5973's (10 total).
- `confusable_with` field (6 lemmas: H518/H5973 notation-collision, F-s/H2005/H389/H3644
  register warnings) — same pattern as `core_schema`, rendered on the vocab card.
- `app/translit_display.js`'s `translitFrag` colors alef (') and ayin (`) differently
  everywhere transliteration renders (vocab/parse/read/learn) — display-only, copy-paste
  still yields plain ASCII.
- Learn tab group 6 ("Confusable words") — 'el vs le-, 'im vs `im vs 'et, yesh vs 'ayin.
  Reused group 1's `decompose()` machinery; word ids re-selected from already-verified
  tier-A/B picks rather than fresh corpus reading. New `build_lessons_group6.py` +
  `verify_lessons_group6.py`, wired into `main.js`'s `LESSON_GROUPS`.

Full pipeline re-verified clean throughout (vocab deck, function-word examples, all 6
lesson groups, parse, Jonah readers). Cloze particle drill stays deferred, per Lane.

**Open:** Not committed/pushed yet this session — Lane hasn't given the go-ahead for this
batch specifically. Nothing eyeballed in-browser; per working style, that's on Lane.

# Status

Phase log for the v1 rebuild (see `BUILD_PLAN.md`). Pre-rebuild history: tag `v0-legacy`.

## Phase 0 — Reset and foundations (done 2026-10-07)
- Tagged `v0-legacy`; removed `app/ data/ pipeline/ glosses/` from `main` (local, not pushed).
- `SPEC.md` committed with Q/R decisions resolved; `CLAUDE.md` rewritten.
- `pipeline/fetch_sources.py` + `sources.lock.json`: OSHB morphhb 2.0.2, HebrewLexicon, STEPBible (TBESH, TAHOT, TVTMS), BHSA (29 features), WEB; sha256 per file, licence per source.
- `pipeline/corpus.py` -> `build/tokens.jsonl` (125,378 read tokens, 377 qere, 2 unread ketiv, 2 Aramaic, 1,788 poem tokens). Config in `corpus_config.json`.
- Gate `verify_corpus.py` (8 s): consonants identical to BHSA in all 11 books. 10 verses lack a sof-pasuq in the WLC text (informational).
- Next: Phase 1 transliterator.

## Phase 1 — Transliterator (built 2026-10-08; Lane check pending)
- `pipeline/translit.py`: syllable-based. Stress from accents (positional accents, WLC qadma/zarqa+pashta/zinor pairs, silluq, maqqef = unstressed), corpus stress table for positional-only words, segolate fallback. Morph/lemma used for qamats+shva (Qal inf/impv qatan vs other verbs) and kol.
- Gate `verify_translit.py` (23 s): golden 55/55; vs TAHOT 97.24% letter-equal on 124,212 aligned tokens; stress agrees 85,762/86,484. 3,852 disagreements in 34 explained buckets (`translit_expected.json`; TAHOT artifacts, Tiberian vs TAHOT choices, ketiv/qere), 225 in a small tail.
- M14: the source has no U+05C7; qamats qatan is inferred. Lexical open-syllable qatan list `QATAN_OPEN` (qodesh, oniyyah, shoresh).
- Spot-check 1 (Lane, 49/50): furtive stress now marked (rúach, hammizbéach; 1,615 tokens). Targeted qatan check fixed prefix qamats (ha'oniyyah, barohatim) and qodashim.
- Spot-check 2 (Lane, 50/50 clean): chose vayehi (vocal shva after vav-consecutive, ~890 tokens) and kept final he `h` for silent and mappiq alike.
- Spot-check list: `python -X utf8 pipeline/translit_sample.py` -> `build/translit_spotcheck.md`.

## Phase 2 — Measurement (done 2026-10-08)
- `pipeline/align_bhsa.py`: OSHB morpheme -> BHSA word by consonant position (streams identical; qere not aligned).
- `pipeline/measure.py` (~40 s) -> `MEASURES.md`, `data/measures/*.json`, `data/parse_quarantine.json`. Gate `verify_measures.py` (~7 s) recounts headline numbers independently and checks every pool item.
- Headlines: 750 lemmas = 92.5% lemma coverage; Exod 3/14 92.4%/94.4%; Qal strong 6.3% of verbs; top 300 forms = 43.9% of verb tokens; Exodus top-up 36 lemmas (budget 80) but 128 forms (budget 30); M13 quarantine 690 tokens.
- Lane decisions: core 750; Unit 11 teaches only rule-opaque forms; Gen 12:1-9 opens Unit 6; 2 Sam 1:19-27 and 2 Kgs 19:21-28 now poems (corpus 123,358 tokens); hishtachaveh one card, no stem facet. Recorded in SPEC section 7.
- Next: Phase 3 content, Units 0-3.

## Phase 3 — Content, Units 0-3 (done 2026-10-08)
- Text layer `build_text.py` -> `data/text/<Book>/<ch>.json` (281 chapters, 21 MB): token, translit, TAHOT per-word gloss (99.96%; rest TBESH), TAHOT sense tag, WEB English via TVTMS map. Gate `verify_text.py` (~25 s).
- WEB's Strong's tags sit one verse off in renumbered chapters (Gen 32, Exod 8, ...), so the map is checked against TAHOT English instead: 16 weak verses (cap 25).
- Items `build_items.py`: lemma queue 1-750 (573 dictionary-form fronts, 157 bare, 20 in-word), Unit 0 (37 reading words, 60 decode checks with rule-based distractors), Unit 1 (14 prefix items, 8 verb forms, 40 micro-readings). Lessons `build_lessons.py`: 18 (Units 0-1). Gate `verify_content.py` (~1 s).
- Curated glosses: lemmas 1-50 (per TBESH sense), 8 forms, 14 morphemes, all unreviewed.
- Upfront gloss review dropped (Lane, 2026-10-08): problems get reported while studying. Review page artifact PtU2bU41Fshzt4dWBi9KBh unused; `apply_review.py` kept for folding in reports.
- Part 2 (Units 2-3). Lane chose: suffix cards by PGN x shape (after singular vs after plural/'el), Unit 2 forms = next 6 wayyiqtol (not ranks 9-14), 8 story-tense markers.
- Unit 2: 24 segment cards (6 noun endings, 9 + 8 suffix shapes, directional -ah; 2fs -ayikh dropped at 11 tokens), 6 forms, 10 names, 50 readings (M8b, 4-8 words). Unit 3: 8 markers, 55 wayyiqtol forms (one per lemma+parse; vayyishtachu skipped, all tokens quarantined), 60 verse readings (M8c). 14 lessons (L2.1-2.9, L3.1-3.5).
- New snapshot field `hlc` (letter-cluster ranges) highlights endings and prefix letters that are not their own OSHB morpheme. Forms carry chip `facets` (stem/conj/pgn); units.json `parse` lists facets asked (Unit 3: conj, pgn).
- Curated, unreviewed: lemma glosses 51-190, 61 form glosses, 10 name glosses (`glosses/names.json`). Segment meanings come from the `SEGMENTS` table.
- Gate `verify_content.py` (~1.5 s) re-classifies every exemplar, checks letter ranges, short/long pairs (vayyar / yir'eh) and facets. Build ~35 s.
- Next: Phase 4 app core.

## Phase 4a — App core, first slice (built 2026-10-08; Lane phone check pending)
- `index.html` + `app/` (data, store, srs, render, cards, lessons, session, main, style.css) + `sw.js` (network-first cache). Legacy root files removed (still at tag `v0-legacy`).
- Store `hebrew.v1` in localStorage (cards, intro, lessons, reads, log, sessions, settings). ts-fsrs 4.7.0 via jsDelivr, retention 0.88.
- Today: lessons -> review box (4 min, silent roll-over, Again re-queued once) -> new at adaptive N (3:2 lemma:grammar; N=0 after a 3+ day gap until the box stops overrunning) -> reading -> done line (Finish / More reading / More drill). Grades Again/Good/Easy.
- Kinds: lemma, morpheme, form (type 3; chip parse type 4 when the unit's `parse` is non-empty), name, decode, decode-read, micro. Unit 0: 8 decode + 5 read per day, lemmas from the third session at 2/day. Units advance when all grammar items are introduced (cap Unit 3).
- Gate `verify_app.py`: no Hebrew in app, no root-absolute paths, JS parses, unlock/ref/example integrity.
- Not yet (4b): report-a-problem, export/import, progress panel, M12 timing log, Unit 0 mastery check, pin queue.

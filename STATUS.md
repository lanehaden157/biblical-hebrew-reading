# Status

Phase log for the v1 rebuild (see `BUILD_PLAN.md`). Pre-rebuild history: tag `v0-legacy`.

## Phase 0 — Reset and foundations (done 2026-10-07)
- Tagged `v0-legacy`; removed `app/ data/ pipeline/ glosses/` from `main` (local, not pushed).
- `SPEC.md` committed with Q/R decisions resolved; `CLAUDE.md` rewritten.
- `pipeline/fetch_sources.py` + `sources.lock.json`: OSHB morphhb 2.0.2, HebrewLexicon, STEPBible (TBESH, TAHOT, TVTMS), BHSA (29 features), WEB; sha256 per file, licence per source.
- `pipeline/corpus.py` -> `build/tokens.jsonl` (125,378 read tokens, 377 qere, 2 unread ketiv, 2 Aramaic, 1,788 poem tokens). Config in `corpus_config.json`.
- Gate `verify_corpus.py` (8 s): consonants identical to BHSA in all 11 books. 10 verses lack a sof-pasuq in the WLC text (informational).
- Next: Phase 1 transliterator.

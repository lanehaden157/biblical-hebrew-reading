# v1 rebuild — build plan

Source of truth: `hebrew-reading-curriculum.md` (the spec), with the decisions below.
Where it conflicts with the current CLAUDE.md, the spec wins; CLAUDE.md gets rewritten in Phase 0.

## Decisions (2026-10-07)

| Topic | Decision |
|---|---|
| Authority | Spec doc wins over old CLAUDE.md |
| Salvage | Nothing. Fetch, transliterator, data, app all rewritten |
| Old review history | Negligible; no migration |
| Location | Same repo, replace on `main`; old state tagged `v0-legacy`; same Pages URL |
| Decoding | Lane reads pointed text → Unit 0 is a 1-week calibration |
| Transliteration display | Tap-to-show after Unit 0; setting for always-on |
| Translit conventions (Q1) | b/v k/kh p/f by dagesh; doubled consonants written double; vocal shva = `e`; qamats qatan = `o` |
| Divine name (Q3) | Pointed text as printed; translit `YHWH`; gloss "YHWH (the LORD)" |
| Audio (R2) | Not in v1 |
| Session | Spec's guided Today flow (~8 min, silent roll-over, no counters) |
| Frequency corpus (Q2) | Gen, Exod, Num, Josh, Judg, Ruth, 1–2 Sam, 1–2 Kgs, Jonah. Prose only, embedded poems removed. No late books, no Lev/Deut |
| Glosses (Q4/Q5) | Seeded from STEPBible TBESH, curated per occurrence vs BDB, source + `reviewed` flag; Lane reviews ~50/unit. Reveal shows gloss line + WEB translation |
| Verb cards (Q6) | Card per lemma+stem when stem has ≥20 tokens and a distinct meaning |
| Parse cross-check | OSHB vs ETCBC BHSA; disagreements quarantined |
| Sync | Dropped. localStorage + export/import only |

## Phases

Each phase ends with a `verify_*.py` gate and, where marked, a **Lane check** before the next starts.

### Phase 0 — Reset and foundations
- Tag `v0-legacy`; remove old `app/ data/ pipeline/ glosses/` from `main`.
- Commit spec as `SPEC.md` with Q1–Q6, R1–R3 resolved inline. Write a new `CLAUDE.md` from scratch (not an edit of the old one): goal, decisions table above, trust rules, repo layout, working style. Keep it short; guidelines framed as strong suggestions. **Lane check** on the draft. Restart `STATUS.md`.
- New fetch layer: pinned version + sha256 for every source — OSHB morphhb, HebrewLexicon (BDB), STEPBible-Data (TBESH, TAHOT), BHSA (Text-Fabric, trimmed to needed features), WEB (public domain, USFM). Records each source's licence file.
- One corpus loader → token table (id, ref, surface, morpheme split, lemma, morph, ketiv/qere, maqqef link, accents, poem/Aramaic flags). Everything downstream reads this, nothing re-parses XML.
- Gate: `verify_corpus.py` (token counts per book, qere handling, flags).

### Phase 1 — Transliterator
- Syllable-based: accent/meteg-driven stress, dagesh forte vs lene, vocal shva, qamats qatan, furtive patach, maqqef context, YHWH override, qere-perpetuum list.
- Gate: corpus-wide comparison against TAHOT's independent transliteration (via a scheme-mapping table); every disagreement category explained or fixed. Unit tests on a golden set.
- **Lane check:** 50 random words spot-checked by ear.

### Phase 2 — Measurement (spec Appendix A)
- M1–M11, M13 (OSHB/BHSA disagreements), M14, on the narrative corpus.
- Output: `MEASURES.md` report. Sets real unit budgets, rank cut-offs, micro-reading pools, Exodus top-up size.
- **Lane check:** confirm 750 cut-off and unit sizes given the actual numbers.

### Phase 3 — Content, Units 0–3
- Ranked lemma deck; gloss seeding + per-occurrence curation (source + `reviewed` flag); morpheme items; whole-form verb items (M6); names; micro-reading pools M8a–c; Unit 0–3 lessons (Hebrew referenced by token id only).
- Each generator ships its verifier.
- **Lane check:** gloss review batch for Units 0–3.

### Phase 4 — App core (first usable slice)
- Vanilla ES modules, no build step, relative paths only. Versioned store schema; ts-fsrs pinned via CDN.
- Today flow (review box → new items at adaptive N → read → done line). Item types 1, 2, 3, 4 (chip parse), 7, 11; lesson view; tap-to-show translit; report-a-problem (local quarantine, exported list); export/import; progress panel (coverage metrics, verses read); M12 timing log.
- Gate: no-Hebrew-in-`/app` grep, data-schema check, no root-absolute paths.
- Deploy. **Lane check:** ~2 weeks real phone use on Units 0–1 before Phase 5.

### Phase 5 — Units 4–7
- Content for qatal, yiqtol/commands, participles/infinitives, root recovery.
- Passage reader with help levels + tap logging; spot check (type 9); marker discrimination (type 5); unseen-form pool (type 6); Jonah and Ruth.

### Phase 6 — Units 8–10
- Piel/Hiphil, Niphal/Hitpael/rare stems, object suffixes, clause connectors; lemma+stem cards; Genesis selections; Exod 1–2.
- Practice mode (no FSRS writes); library + pin queue; jump-to-unit.

### Phase 7 — Units 11–12
- Exodus 3/14 top-up (M10); milestone mode (hidden help, logged lookups); pace forecast from M12 data.

## Known risks
- TAHOT uses its own transliteration scheme; the mapping table may leave a residue of unexplained differences. Fallback: a larger golden set.
- WEB uses English versification (e.g. Jonah 1:17 = Heb 2:1). A verse map is needed and verified.
- BHSA and OSHB tokenise differently; alignment itself needs a verifier before M13 means anything.
- Content can be built ahead of where Lane is, but real-use bugs argue for shipping in slices (Phase 4 first).

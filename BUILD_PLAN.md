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

### Phase 0 — Reset and foundations — DONE 2026-10-07 (commits cfd509b, c6143ac; not pushed)
- Tag `v0-legacy`; remove old `app/ data/ pipeline/ glosses/` from `main`.
- Commit spec as `SPEC.md` with Q1–Q6, R1–R3 resolved inline. Write a new `CLAUDE.md` from scratch (not an edit of the old one): goal, decisions table above, trust rules, repo layout, working style. Keep it short; guidelines framed as strong suggestions. **Lane check** on the draft. Restart `STATUS.md`.
- New fetch layer: pinned version + sha256 for every source — OSHB morphhb, HebrewLexicon (BDB), STEPBible-Data (TBESH, TAHOT), BHSA (Text-Fabric, trimmed to needed features), WEB (public domain, USFM). Records each source's licence file.
- One corpus loader → token table (id, ref, surface, morpheme split, lemma, morph, ketiv/qere, maqqef link, accents, poem/Aramaic flags). Everything downstream reads this, nothing re-parses XML.
- Gate: `verify_corpus.py` (token counts per book, qere handling, flags).

### Phase 1 — Transliterator — DONE 2026-10-08 (commit 99d071f; two 50-word Lane checks passed; not pushed)
- Syllable-based: accent/meteg-driven stress, dagesh forte vs lene, vocal shva, qamats qatan, furtive patach, maqqef context, YHWH override, qere-perpetuum list.
- Gate: corpus-wide comparison against TAHOT's independent transliteration (via a scheme-mapping table); every disagreement category explained or fixed. Unit tests on a golden set.
- **Lane check:** 50 random words spot-checked by ear.

### Phase 2 — Measurement (spec Appendix A) — DONE 2026-10-08 (Lane decisions in MEASURES.md; not pushed)
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

## Handoff notes for Phase 3 (from Phase 2)

- Ranks, names, verb forms, pools, top-up lists: `data/measures/*.json` (regenerate with `measure.py`; never hand-edit). Lemma key = OSHB lemma part ("1254 a"); names = morph Np/Ng.
- `data/parse_quarantine.json`: skip these ids for parse items and pool picks; `unchecked_qere` ids have no BHSA check.
- Ambiguous surfaces (trust rule 5): `ambiguous_surfaces.json`, keyed by surface without accents/meteg.
- Weak class per verb lemma comes from the aligned BHSA lexeme (`weak_class()` in measure.py).
- TBESH glosses in the measures are hints only (OSHB augment letters are mapped naively to TBESH's).
- Python sources: write Hebrew codepoints as `chr(0x5D0)`; the Write tool turns backslash-u escapes into literal Hebrew.

## Handoff notes for Phase 2 (from Phase 1)

- Transliterate only via `translit.translit_token(tok, table)`, with `table = translit.build_stress_table(tokens)` built once per run over all tokens (~5 s). Without the table, words with only a positional accent fall back to final/segolate stress.
- Output: `text` (display), `syllables`, `stress` (index or None), `stress_src`. Maqqef-joined words are unstressed; append `-` at display time from `maqqef_next`.
- Gate: `python -X utf8 pipeline/verify_translit.py` (~25 s). A rule change that moves a bucket fails it: sample the moved tokens, then re-baseline `translit_expected.json` with a reason. Add a golden entry per new rule.
- Lexical exceptions: kol (3605) always qatan; `QATAN_OPEN` (qodesh, oniyyah, shoresh). M14 answered: no U+05C7 in source.
- Spot-check generator: `pipeline/translit_sample.py N SEED`.
- The Write/Edit tools turn backslash-u escapes into literal Hebrew; patch via scripts that build the backslash with `chr(92)`, then grep for non-ASCII.

## Handoff notes from Phase 0

- Token table: `python -X utf8 pipeline/corpus.py` -> `build/tokens.jsonl` (gitignored; regenerate on a fresh clone after `python pipeline/fetch_sources.py`). Field list is in the `pipeline/corpus.py` docstring. Read tokens only via `corpus.load_tokens()`.
- Qere: the written ketiv is in the token's `ketiv` field; the token itself is the qere reading. `read=False` tokens (Ruth 3:12, 2 Kgs 5:18) are written but not read; skip them.
- Parts: `parts[i]` = {text, lemma, morph}; text and morph always align 1:1; suffix morphemes (morph `Sp…`) usually have no lemma.
- OSHB ids use Hebrew versification (Jonah 2:1 = English 1:17). WEB needs a verse map (TVTMS is fetched).
- BHSA reader: `pipeline/tf.py`. STEPBible TAHOT/TBESH are in `sources/stepbible/` (Gen-Deu, Jos-Est, Isa-Mal; Jonah is in Isa-Mal).
- Gate for any phase: run its `verify_*.py` and keep it under ~1 minute.
- Still-present legacy files (`index.html`, `manifest.webmanifest`, `package.json`, `*-reference.md`): delete when Phase 4 replaces the app. Do not push until then.

## Working lessons (apply from Phase 1)

- (Phase 1) Reference data like TAHOT is noisy: use it to find disagreement categories, sample each bucket, and judge against the grammar.
- (Phase 1) Sample every bucket that grows after a rule change; fixes often surface neighbouring bugs.

- Profile before guessing. Time each step when something is slow; the real cause was a quadratic `difflib` on 80k-letter strings, found only after several guesses.
- Never use `difflib.SequenceMatcher` on whole books. Compare for equality first, then report the first mismatch.
- Programmatic file edits can silently no-op (`str.replace` with no match). Assert the match or use the Edit tool, and re-run the check.
- Run verifiers in the foreground with a short timeout; if over ~30 s, stop and profile instead of waiting.
- Give Lane a one-line status whenever a step runs more than a minute.
- Inspect a data source's format once up front (headers, blank lines, versification) before writing a parser.

## Known risks
- TAHOT uses its own transliteration scheme; the mapping table may leave a residue of unexplained differences. Fallback: a larger golden set.
- WEB uses English versification (e.g. Jonah 1:17 = Heb 2:1). A verse map is needed and verified.
- BHSA and OSHB tokenise differently; alignment itself needs a verifier before M13 means anything.
- Content can be built ahead of where Lane is, but real-use bugs argue for shipping in slices (Phase 4 first).

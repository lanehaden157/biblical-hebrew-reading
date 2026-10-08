# Biblical Hebrew reading curriculum (v1 rebuild)

Phone-first PWA on GitHub Pages. Spec: `SPEC.md`. Plan: `BUILD_PLAN.md`. Phase log: `STATUS.md`.
Old implementation: tag `v0-legacy`. Where `SPEC.md` and any other doc disagree, the spec wins.

## Goal

Lane reads Exodus 3 and 14 unaided. Recognition-level reading, narrative prose, hobby pace,
no deadline. Lane already decodes pointed text; Unit 0 is a 1-week calibration.

## Decisions

| Topic | Decision |
|---|---|
| Corpus | Gen, Exod, Num, Josh, Judg, Ruth, 1–2 Sam, 1–2 Kgs, Jonah. Prose only; embedded poems and Aramaic removed |
| Translit | b/v k/kh p/f by dagesh; dagesh forte doubled; vocal shva `e`; qamats qatan `o`; v, ch, ts, `` ` ``; alef `'` medial only; final he `h`; acute on non-final stress. `pipeline/translit.py`. Shown on tap after Unit 0, setting for always-on |
| Divine name | Pointed as printed; translit `YHWH`; gloss "YHWH (the LORD)" |
| Glosses | Seeded from STEPBible TBESH, curated per occurrence vs BDB; source + `reviewed` flag; no upfront review: Lane flags problems while studying (2026-10-08) |
| Reveal | Gloss line + WEB translation (needs verified verse map) |
| Verb cards | Per lemma+stem when ≥20 tokens and distinct meaning |
| Parse check | OSHB vs ETCBC BHSA; disagreements quarantined |
| Session | Guided Today flow, ~8 min, silent roll-over, no counters or streaks |
| SRS | ts-fsrs, pinned CDN version. Do not reimplement |
| Persistence | localStorage + JSON export/import. Versioned schema. No sync, no audio |

## Trust rules (strongly suggested; they are the reason for the rebuild)

1. Hebrew text, lemma and parse come only from the corpus. No hand-typed Hebrew, including lessons (reference token ids). No Hebrew letters in `/app/` (grep U+05D0–U+05EA).
2. Parses cross-checked against BHSA; disagreements quarantined and listed.
3. Every gloss stores source + reviewed flag (reviewed = Lane fixed or confirmed it via a report).
4. Transliteration comes from one tested function over the corpus text.
5. Ambiguous surface forms are shown in their verse and graded against that token's tag.
6. Every item has a report-a-problem tap that quarantines it.

Also: avoid NFC/NFD normalisation of Hebrew; every generator ships a `verify_*.py`; pin every
source by version and sha256 and record its licence; prefer no streaks or guilt mechanics.

## Repo layout

```
SPEC.md  BUILD_PLAN.md  STATUS.md  CLAUDE.md
sources/    pinned downloads (gitignored) + sources.lock
pipeline/   Python: fetch -> corpus loader -> token table -> generators, each with verify_*.py
data/       generated JSON, never hand-edited
glosses/    curated glosses (hand-reviewed, with source + reviewed flag)
lessons/    lesson source: English + corpus refs ({Gen.1.3#1}); compiled to data/lessons.json
app/        vanilla ES modules, no build step, no framework, no analytics
index.html
```

## App conventions

Pages serves from a subpath: every fetch/src/href in `/app/` is relative (`../data/…`), never
root-absolute. One module per concern. Only external request: the pinned ts-fsrs CDN URL.

## Working style

- Ask Lane when direction or design is unclear; asking several times in a session is fine.
- Skip self-directed browser verification after edits; ask Lane to confirm on his phone.
- Check glosses per occurrence against BDB, not the dictionary's lead sense.
- Keep docs terse. State magnitudes with units; say plainly when something is fine.
- If Lane pushes back, recheck the arithmetic or source before conceding or defending.
- Dev server: port 8123, `preview_start` config "hebrew".
- Session files (`session_index.md`, `improvements_log.md`, `session_summary_*.md`) per the global instructions.

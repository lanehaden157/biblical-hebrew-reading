# Session summary 2026-10-08 (Phase 3, part 1)

## Done
- Lane chose: corpus-token lemma fronts, TAHOT-seeded gloss line, phone review page, Units 0-1 first.
- Text layer: data/text per chapter with translit, TAHOT gloss + sense tag, WEB English. verify_text.py passes (~25 s).
- Items: lemma queue 1-750, Unit 0 decoding (37 + 60), Unit 1 (14 prefixes, 8 forms, 40 micro-readings); 18 lessons. verify_content.py passes.
- Curated 72 Unit 1 glosses; review page published (db-backed).

## Takeaways
- WEB Strong's tags are offset in renumbered chapters; TAHOT English is the reliable map check.
- TAHOT appends paragraph marks to verse-final words; stripping them took unaligned tokens from 1,166 to 56.
- TBESH sense letters (H1121A/G/L) give per-occurrence senses for free via TAHOT.
- 2 Sam 11:1 kings/messengers (alef with rafe): exemplars now skip rafe, ketiv/qere and quarantined tokens.

## Open
- Apply Lane's review; then Units 2-3 (names track, M8b/M8c, 30 morphemes, 61 forms).
- data/text is 21 MB committed; regenerations grow git history.

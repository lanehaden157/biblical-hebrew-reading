# Session summary 2026-10-08 (Phase 2)

## Done
- OSHB-to-BHSA alignment by consonant position (`pipeline/align_bhsa.py`); BHSA `book` sits on book/chapter/verse nodes, so ranges are the hull.
- `pipeline/measure.py` -> MEASURES.md + `data/measures/*.json` + `data/parse_quarantine.json`; gate `verify_measures.py` passes.
- Key numbers: 750 core = 92.5% lemma coverage; Exod 3/14 92.4%/94.4%; Qal strong 6.3%; top 300 forms = 43.9% of verbs; top-up 36 lemmas / 128 forms; quarantine 690 tokens.

## Takeaways
- Name compounds (En-rogel, Bath-sheba) are the bulk of segmentation splits; not parse errors.
- Unaccented lemma forms transliterate badly (no stress -> qatan); labels use a bare corpus token instead.
- Pools exclude all quarantined tokens (suffix disagreements include pausal 2ms/2fs forms).

## Lane decisions
- Core 750; Unit 11 rule-opaque forms only; Gen 12:1-9 before Jonah; 2 Sam 1:19-27 and 2 Kgs 19:21-28 removed as poems; hishtachaveh one card. In SPEC section 7 and MEASURES.md.

## Open
- Phase 3: deciding which Exodus forms are "rule-opaque" needs the Unit 3-10 marker list first.

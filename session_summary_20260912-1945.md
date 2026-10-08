# Session summary — 2026-09-12

**Done:** No code changes. Answered 24 design questions for a new Joshua literary-study
project (root colouring + coverage audit) from this repo's history plus two scratch
measurement scripts over OSHB `Josh.xml` (kept in the session scratchpad, not committed).

**Takeaways (measured, Joshua, 10,051 words):**
- Consonantal-substring matching fails on weak roots: nakah 3% recall, qum 24%/33%, natan
  42%; Yehoshua 0% (lexicon cites plene spelling). Lemma ids are the right atoms; a
  curated root -> Strong's-id set is needed for root-level colouring.
- NFC changes 47% of words. OSHB word text contains `/` morpheme separators.
- Qere `<w>` sits nested in `<note><rdg>`; both `rank_lemmas.py` and its regex verifier
  count ketiv + qere. 32 qere in Joshua (7 change lemma, 17 change morph).
- Homograph letters (`5892 b`) are stripped by `LEMMA_PART_RE`; in Joshua they mostly
  split sub-entries of the same word (`834 a/d`), not true homographs.
- U+05C7 appears 0x in WLC text, 119x in HebrewStrong.xml.

**Shipped bugs found (not fixed):**
- `parse_qal_strong.json`: 15 cards from unpointed ketiv words + 16 from their qere
  (Ruth 3:4 among them; Ruth reader will hit 13 qere).
- YHWH ships as `yehowah` (deck), `yehwah`/`yhwah` (reader), `yehwih`.
- kol before maqqef renders `kal`/`khal` (185 of 236 Joshua tokens).
- Jerusalem renders `yerushalam`.
- Reader glosses ignore pronominal suffixes (101/688 Jonah words) and construct state.
- `transliterate.py` header still says bet/kaf/pe are never distinguished.

**Open:** Whether to fix the above (flagged as separate task chips). Josh 21:36–37 present
in OSHB with no variant marker — not checked against a printed BHS.

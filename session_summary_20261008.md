# Session summary — 2026-10-08 (Phase 1)

**Done:** `pipeline/translit.py` and the gate `verify_translit.py` (golden 47/47, TAHOT comparison, 23 s). Scheme answers from Lane are recorded in SPEC Q1: v/ch/ts, medial alef only, final he h, acute on non-final stress, vayevárekh, laYHWH.

**Takeaways:** TAHOT is noisy. Its stress capitals follow positional accents, it drops vocal shva after long vowels, and it has v/o artifacts. Use it to find categories, not as ground truth. WLC writes doubled pashta as qadma + pashta (and zarqa + zinor). A spirant after shva doesn't prove the shva is vocal (malkhe, ivdu). The Write/Edit tools turn `\u` escapes into literal characters, so run `escape.py`-style conversion or patch scripts.

**Open:** Lane's 50-word spot-check (`build/translit_spotcheck.md`). Phase 1 work is not committed yet. Known soft spots: directional -ah stress with prepositive accents only, and rare WLC pointing oddities (vehenneh).

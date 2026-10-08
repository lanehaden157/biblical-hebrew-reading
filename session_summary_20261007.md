# Session summary — 2026-10-07

**Done:** Lane chose a full rebuild. Read the spec (`hebrew-reading-curriculum.md`), asked 3 rounds of questions, and wrote `BUILD_PLAN.md`. No code changes.

**Decisions:** The spec overrides the old CLAUDE.md, and CLAUDE.md gets rewritten from scratch. Nothing is salvaged, fetch and transliterator included. The rebuild replaces `main` after tagging v0-legacy. The corpus is classical narrative only, with no late books and no Lev/Deut. The transliterator writes b/v k/kh p/f by dagesh, doubles consonants with dagesh forte, writes vocal shva as e and qamats qatan as o. YHWH is transliterated as `YHWH`. Audio and sync are dropped. Gloss review happens in batches, and the WEB translation is shown on reveal. Lemma+stem cards are used above a 20-token floor, and parses are cross-checked against BHSA.

**Takeaways:** Old `fetch_corpus.py` was sound (pinned + sha1), and `transliterate.py` had no syllable analysis (kol→kal, no dagesh forte, YHWH variants). The plan is to cross-check the new transliterator against STEPBible TAHOT.

**Open:** Go-ahead on Phase 0, which tags the old code and deletes it from main.

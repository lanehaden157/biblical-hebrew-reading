# Session index

- 2026-08-25: Patched corruption in CLAUDE.md from prior edit; created this log system.
- 2026-08-25: Particle curriculum tier 1 — cut Aramaic/poetry lemmas, function-word intro cap, core_schema field on 11 particles.
- 2026-08-25: Tier 1b/B — expanded particle examples cross-canon (11 lemmas 3→10, 19 lemmas 3→5) + rotation in vocab.js.
- 2026-08-26: Contrast-pair brainstorm outcome — merged 'et/`im, confusable_with notes, alef/ayin colored display, Learn tab group 6 (3 lessons).
- 2026-08-29: Fixed sync hammering GitHub's rate limit + reset not surviving a sync; added app/browse.html dev page (card browser + diagnostics).
- 2026-08-29: Clarified wayyiqtol/weqatal parse cards; started vocab_examples.json (real Bible example per non-function-word card) -- batch 1 of many, 20 verbs done, 524 lemmas pending across future batches.
- 2026-09-12: Q&A for a forked Joshua literary-study project (lemma vs substring, translit, glosses). Measured OSHB Joshua via scratch scripts; no code changes. Found shipped bugs: ketiv parse cards, 3 YHWH translits, kol->kal, suffix-less reader glosses.
- 2026-09-12 (run from the Joshua project session): pinned sources. Added AugIndex/LexicalIndex to the corpus, fetch_corpus.py now pulls all 4 lexicon files, and npm pins morphhb 2.0.2 with verified integrity. Summary is in Projects\Joshua\session_summary_2026-09-12.md.
- 2026-10-07: Decided on full v1 rebuild. Q&A resolved spec open questions (Q1–Q6, R1–R3, corpus, sync dropped). Wrote BUILD_PLAN.md (Phases 0–7). No code changes.
- 2026-10-07 (2): Phase 0 done. Reset to v0-legacy tag, new CLAUDE.md/SPEC.md, pinned fetch layer, corpus loader (125,378 tokens), verify_corpus.py passes (matches BHSA consonants).
- 2026-10-08: Phase 1 transliterator built; gate passes (98% letter-equal vs TAHOT, all big disagreement buckets explained). Scheme details settled with Lane. Awaiting 50-word spot-check.
- 2026-10-08 (2): Phase 1 signed off after 2 spot-checks (furtive stress, lexical qatan, vayehi); committed locally. Phase 2 next in new chat.

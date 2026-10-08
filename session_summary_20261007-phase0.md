# Session summary — 2026-10-07 (Phase 0)

**Done:** Tagged v0-legacy and removed old code; SPEC.md, BUILD_PLAN.md, new CLAUDE.md. Built pinned fetch layer (5 sources, sha256 lock), corpus loader and token table, verify_corpus.py. OSHB consonants equal BHSA for all 11 narrative books.

**Takeaways:** OSHB keeps ketiv in the main text with qere in a variant note; 2 ketiv are unread (Ruth 3:12, 2 Kgs 5:18). OSHB osisIDs use Hebrew versification. A Text-Fabric header ends with a blank line that must not count as node 1 (caused a one-word shift). Slowness came from difflib on 80k-letter strings; plain comparison takes seconds.

**Open:** Push is held until the new app exists (old index.html is dead). Phase 1 (transliterator) next. Old index.html/manifest/reference docs/package.json still present.

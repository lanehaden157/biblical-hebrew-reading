# Improvements log

- 2026-08-25: Fixed CLAUDE.md truncation (cut-off sentences, duplicate header, typo) left by a prior edit. STATUS.md's condensation from that same edit was fine, left as-is.
- 2026-08-25: Cut 9 Aramaic + 2 poetry-only lemmas from vocab deck (600→589); pulled H853 from SRS drills; added 1-in-6 function-word intro cap; added core_schema field for 11 particles.
- 2026-08-25: Expanded tier-1 particle examples 3→10 each (76 new, cross-canon); added shuffled-cycle rotation (3 shown per review) to vocab.js.
- 2026-08-25: Expanded tier-B particle examples (19 lemmas) 3→5 each (37 new, cross-canon). 213→250 examples total.
- 2026-08-26: Merged 'et/`im into one vocab card; added confusable_with notes (6 lemmas); colored alef/ayin in all transliteration display; added Learn tab group 6 (3 confusable-pair lessons, 10 examples).
- 2026-08-29: sync.js: skip redundant push when cards unchanged; back off after 401/403 instead of retrying every boot. store.js/sync.js: resetAll() now force-pushes the wipe to the gist (was losing to the next merge). Exported cardEl/cardBackEl from vocab.js and cardEl from parse.js (stage/flip now explicit params, not module closures) for reuse. New app/browse.html + browse.js: search-and-preview any vocab/parse card without touching the review queue, plus a diagnostics panel (sync state, backup keys, read-only gist peek, load counts) and a rendered view of this file.

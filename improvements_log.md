# Improvements log

- 2026-08-25: Fixed CLAUDE.md truncation (cut-off sentences, duplicate header, typo) left by a prior edit. STATUS.md's condensation from that same edit was fine, left as-is.
- 2026-08-25: Cut 9 Aramaic + 2 poetry-only lemmas from vocab deck (600→589); pulled H853 from SRS drills; added 1-in-6 function-word intro cap; added core_schema field for 11 particles.
- 2026-08-25: Expanded tier-1 particle examples 3→10 each (76 new, cross-canon); added shuffled-cycle rotation (3 shown per review) to vocab.js.
- 2026-08-25: Expanded tier-B particle examples (19 lemmas) 3→5 each (37 new, cross-canon). 213→250 examples total.
- 2026-08-26: Merged 'et/`im into one vocab card; added confusable_with notes (6 lemmas); colored alef/ayin in all transliteration display; added Learn tab group 6 (3 confusable-pair lessons, 10 examples).
- 2026-08-29: sync.js: skip redundant push when cards unchanged; back off after 401/403 instead of retrying every boot. store.js/sync.js: resetAll() now force-pushes the wipe to the gist (was losing to the next merge). Exported cardEl/cardBackEl from vocab.js and cardEl from parse.js (stage/flip now explicit params, not module closures) for reuse. New app/browse.html + browse.js: search-and-preview any vocab/parse card without touching the review queue, plus a diagnostics panel (sync state, backup keys, read-only gist peek, load counts) and a rendered view of this file.
- 2026-08-29: parse.js: wayyiqtol/weqatal cards named the conjugation in jargon only and explained the leading vav a second, disconnected time as a bare "and" line -- CONJ_NAMES now states the function directly, and the redundant prefix-gloss line is suppressed for those two conjugations.
- 2026-08-29: New pipeline/build_vocab_examples.py + verify script + data/vocab_examples.json: real Bible examples for the 544 drillable lemmas function_word_examples.json doesn't cover (nouns/verbs/adjectives/etc.), one verified example each rather than function words' tiered 3-10, done in batches (verbs, then adjectives, then the rest, per Lane). Batch 1: first 20 verbs by frequency, sourced from Genesis 1-8/Jonah/Ruth. Wired into main.js (loadVocabExamples, merged with functionWordExamplesByLemma) and browse.js. 524 lemmas still pending across future batches (tracked in the data file's own metadata).
- 2026-08-30: vocab_examples.json batch 2: next 20 verbs (qum through sur), same sourcing. 40 of 179 verbs done, 504 lemmas pending overall.
- 2026-08-30: vocab_examples.json batch 3: next 20 verbs (khazaq through 'ahav; katav sourced from Exodus, no Gen/Jonah/Ruth occurrence). 60 of 179 verbs done, 484 pending overall.
- 2026-08-30: vocab_examples.json batch 4: next 20 verbs (yasaf through ra`ah); yasha` and lakham sourced from Exodus 14 (a CLAUDE.md target chapter). 80 of 179 verbs done, 464 pending overall.
- 2026-08-30: vocab_examples.json batch 5: next 20 verbs (tame' through shakhan). 100 of 179 verbs done, 444 pending overall.
- 2026-08-30: vocab_examples.json batch 6: next 20 verbs (qavats through 'aman); lakhad/batakh/qatar/nava' sourced outside Gen/Jonah/Ruth (Joshua, Psalms, Leviticus, Jeremiah). 120 of 179 verbs done, 424 pending overall.
- 2026-08-30: vocab_examples.json batch 7: next 20 verbs (yatar through lun); ba`ar's clearest hit is the burning bush (Exodus 3), shir sourced from the Song of the Sea (Exodus 15, right after Exodus 14). 140 of 179 verbs done, 404 pending overall.
- 2026-08-30: vocab_examples.json batch 8: next 20 verbs (lamad through khalah); 5 lemmas sourced outside Gen/Jonah/Ruth (Deuteronomy, Leviticus, Judges, 2 Samuel, 1 Samuel). 160 of 179 verbs done, 384 pending overall.
- 2026-08-30: vocab_examples.json batch 9: final 19 verbs (khafets through paras) -- all 179 verb lemmas now have a verified example, zero skipped. 365 lemmas (44 adjectives, 321 nouns/pronouns/adverbs) pending; verbs finished, adjectives next per Lane's priority order.
- 2026-08-30: vocab_examples.json batch 10: all 44 adjectives done (numbers one-through-seventy plus tov/ra`/gadol/qatan/tsadiq/rasha`/qadosh/tame' etc.), zero skipped; 6 sourced outside Gen/Jonah/Ruth (Deuteronomy, Exodus, Leviticus, Proverbs). 321 lemmas (nouns/pronouns/adverbs) pending -- the last tier.
- 2026-08-30: vocab_examples.json batch 11: first 20 nouns/pronouns by frequency (yehowah through dawid). 301 pending overall.
- 2026-08-30: vocab_examples.json batch 12: next 20 nouns/pronouns/adverbs (ayin through bat); mosheh/yerushalam sourced from Exodus/Joshua. 281 pending overall.
- 2026-08-30: vocab_examples.json batch 13: next 20 nouns/adverbs (mayim through kherev); qodesh sourced from the burning bush scene (Exodus 3). 261 pending overall.
- 2026-08-30: vocab_examples.json batch 14: next 20 nouns/pronouns (sha'ul through keli); aharon sourced from Exodus. 241 pending overall.
- 2026-08-30: vocab_examples.json batch 15: next 20 nouns/adverbs (milkhamah through par'oh); shelomoh/lewiyi sourced from 1 Kings/Exodus. 221 pending overall.
- 2026-08-30: vocab_examples.json batch 16: next 20 nouns (bavel through torah), all found in Genesis. 201 pending overall.
- 2026-08-30: vocab_examples.json batch 17: next 20 nouns (em through sefer); yehoshua` sourced from Joshua. 181 pending overall.
- 2026-08-30: vocab_examples.json batch 18: next 20 nouns (mitswah through khokhmah); tsiyon/khokhmah sourced from Psalms/Proverbs. 161 pending overall.
- 2026-08-30: vocab_examples.json batch 19: next 20 nouns/adverbs (edah through nasi'); 5 sourced outside Genesis (Exodus, Jeremiah, 2 Samuel, 1 Samuel). 141 pending overall.
- 2026-08-30: vocab_examples.json batch 20: next 20 nouns/pronouns (erev through tsedeq); 4 sourced outside Genesis (Joshua, 2 Kings, Exodus, Psalms). 121 pending overall.
- 2026-08-30: vocab_examples.json batch 21: next 20 nouns (bekhor through bamah); 8 sourced outside Genesis (Joshua, Exodus, 2 Samuel, 1 Kings). 101 pending overall.
- 2026-08-30: vocab_examples.json batch 22: next 20 nouns (yarov`am through khelev); yarov`am/tamid/akh'av sourced from 1 Kings/Exodus. 81 pending overall.
- 2026-08-30: vocab_examples.json batch 23: next 20 nouns (kerem through beytlekhem); 6 sourced outside Genesis (Psalms, 1 Kings, 2 Samuel, Leviticus, Exodus). 61 pending overall.
- 2026-08-30: vocab_examples.json batch 24: next 20 nouns (kasdi through barzel); 10 sourced outside Genesis. 41 pending overall -- close to done.
- 2026-08-30: vocab_examples.json batch 25: next 20 nouns (mitsri through shofar); 8 sourced outside Genesis. 21 pending overall -- one batch left.
- 2026-08-30: vocab_examples.json batch 26 (FINAL): last 21 lemmas (beten through qever) -- all 544 target lemmas now have a real, corpus-verified Bible example, zero skipped. Project complete: every drillable vocab card has at least one example, function words additionally tiered 3-10.
- 2026-09-12: Added AugIndex.xml (223,277 bytes) and LexicalIndex.xml (1,831,069 bytes) from HebrewLexicon @ 21c9add to pipeline/corpus/lexicon. The existing BDB/Strong's files are byte-identical to that commit. fetch_corpus.py now extracts and checks all 4 lexicon files (LEXICON_FILES); tested offline against a git-archive tarball of the pinned commit. Added node_modules/ to .gitignore ahead of the npm pin for morphhb 2.0.2.
- 2026-09-12: Installed Node 24.19.0 LTS (winget) and pinned morphhb with `npm install morphhb@2.0.2 --save-exact`. New package.json + package-lock.json are untracked and not yet committed. The lock integrity matches the registry sha512, the tarball sha1 is 2ea8c8ad...c145a, and LICENSE.md is CC BY 4.0. All 39 node_modules/morphhb/wlc books are sha256-identical to pipeline/corpus/wlc. fetch_corpus.py still downloads the same tarball itself; the pipeline doesn't read node_modules.

## 2026-10-07 — v1 rebuild Phase 0
- Tagged v0-legacy; removed old app/data/pipeline/glosses; added SPEC.md, BUILD_PLAN.md; rewrote CLAUDE.md and STATUS.md.
- Added pipeline/fetch_sources.py, sources.lock.json, corpus.py, corpus_config.json, tf.py, verify_corpus.py.

## 2026-10-08 — Phase 1 transliterator
- Added pipeline/translit.py, verify_translit.py, translit_golden.json (47), translit_expected.json, translit_sample.py.
- SPEC Q1 / CLAUDE.md translit row extended with Lane's 2026-10-08 scheme answers.
- 2026-10-08: Spot-check fixes: acute on furtive-patach stress; QATAN_OPEN lemma list; prefix qamats never qatan and makes following shva vocal; hatef-qamats rule limited to one morpheme; dagesh after shva on non-bgdkpt not doubled. Golden 53.
- 2026-10-08: Spot-check 2: shva after vav-consecutive always vocal (vayehi); golden 55.

## 2026-10-08 — Phase 2 measurement
- Added pipeline/align_bhsa.py, measure.py, verify_measures.py; MEASURES.md (findings + generated M1-M11, M13, poem candidates); data/measures/*.json; data/parse_quarantine.json (690 tokens).
- 2026-10-08: Lane decisions recorded in SPEC section 7; corpus_config adds poems 2 Sam 1:19-27, 2 Kgs 19:21-28.

## 2026-10-08 — Phase 3 part 1 (Units 0-1 content)
- Added pipeline/web.py, tahot.py, lexicon.py, build_text.py, verify_text.py (data/text per chapter).
- Added build_items.py, build_lessons.py, verify_content.py, review_page.py + template, apply_review.py; lessons/unit0-1.md; glosses/*.json.
- translit.py returns read-only `features`. Review page artifact PtU2bU41Fshzt4dWBi9KBh.

## 2026-10-08 — Phase 3 part 2 (Units 2-3 content)
- build_items.py: `SEGMENTS` + `segment_classes()` (noun endings, suffix shapes, directional -ah, story-tense markers) with `hlc` letter ranges; `build_names`; `pick_forms` (next wayyiqtol, one per lemma+parse, skips fully quarantined); form `facets`; verse readings (M8c); units.json `parse`.
- glosses: lemmas 51-190, forms (61 more), names.json (10). lessons/unit2.md (9), unit3.md (5).
- verify_content.py: re-classifies segment exemplars, letter ranges, short/long pairs, facets, names.

## 2026-10-08 — Phase 4a (app core)
- New: index.html, sw.js, app/{data,store,srs,render,cards,lessons,session,main}.js, app/style.css, pipeline/verify_app.py.
- Removed legacy package.json, package-lock.json, morphology-reference.md, transliteration-reference.md.
- Lesson layout: Hebrew inline with English text, translit on tap in parentheses; Exit button on every session screen.
- Settings: hide cantillation accents toggle (strips U+0591-05AF at render).
- lessons/unit0.md: L0.10 accents, L0.11 silluq/meteg (no rafe lesson: the corpus has none). Rebuilt lessons.json, units.json.

## 2026-10-08 - Phase 4b
- New: app/report.js, app/progress.js; store reports/quarantine/replace; log nw/w/taps; sessions sec; Progress tab; Settings export/import/reports.

## 2026-10-08 - Translit: dagesh forte not written
- translit.py: doubled consonant no longer written (gem flag kept for qatan); golden 12 entries updated.
- build_items.py: removed "double" distractor kind (dagesh_forte -> spirant test); morpheme/marker labels say "dot in the next letter".
- lessons unit0-3: typed translits regenerated; L0.2, L1.2-1.5, L3.1-3.3 prose teaches the dot, not doubling.
- app/session.js: due count ignores cards whose item no longer exists.
- SPEC Q1, CLAUDE.md, BUILD_PLAN updated. Rebuilt measures, text, items, lessons; all gates pass.
- app/sync.js + Settings "Sync" section: opt-in private-gist sync of progress and reports; store.js stamps savedAt; sw.js skips api.github.com.
- pipeline/pull_sync.py: fetches synced state, lists reports. SPEC sync decision, CLAUDE.md, BUILD_PLAN updated.

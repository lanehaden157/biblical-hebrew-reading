# Status / phase history

Rewritten (append-only, by phase) at each phase boundary. `git log` is the commit-level
history; this file is the narrative one — what was built, why, and how it was verified.
This lives outside `CLAUDE.md` so the project-instructions file doesn't grow every phase.

## Done — Phases 1–2 (Tier 0–1 build)

Pipeline builds `data/top600.json` from OSHB. All 600 lemmas curated across six gloss
batches, reviewed, verified. Transliteration generator complete and verified against all
600 forms. `data/vocab_deck_600.json` built. Vocab SRS app shipped and live at the Pages
URL: three-stage card reveal (Hebrew → transliteration → gloss), three grade buttons
(Again/Good/Easy, `Hard` dropped), light/dark theme following the system setting, sound
feedback (default on, per-grade tones) behind `feedback.js`. Haptics were attempted
(standard vibration API, then an undocumented iOS switch-click trick) and dropped after
real-device testing confirmed neither fires in iOS Safari — there is no haptics toggle or
code path. Session-length tracking was built and then deliberately removed: this is a
casual hobby project, and a persisted timing log is the kind of quantified-self mechanic
hard rule 5 (no streaks, no guilt mechanics) exists to keep out. `store.js` has no
`sessions` field.

## Done — Phase 3 (Tier 2 build): parsing gym, Qal strong verbs

`pipeline/build_parse_qal.py` pulls Qal forms in the locked conjugation-priority order
(qatal, wayyiqtol, yiqtol, participle, infinitive construct — confirmed exact `morph`
codes against the whole corpus rather than assuming: `Vq` + one of `pwqrc` + a
person/gender/number or gender/number/state suffix) restricted to **strong** roots.
Strong-root test: triliteral, no radical in {alef,he,het,ayin} (covers I/II/III-guttural
and III-He/III-Aleph in one check), first radical not nun, first radical not vav/yod,
second radical not vav/yod or equal to the third (hollow/geminate). Root lemmas are
restricted to the 181 verb lemmas already in the curated top-600 vocab deck, not all
Qal-attested lemmas in the corpus — reuses their lexicon-sourced citation form,
transliteration and gloss rather than a second curation pass, and keeps parsing practice
anchored to vocabulary already being learned. Yields 41 strong-root lemmas, 34 of which
are actually attested in Qal in the corpus (the other 7 — בקש, שלך, קטר, שרת, מלט, שמד,
סתר — are cited in Qal-perfect form by convention but essentially never occur in Qal;
confirmed against BDB usage, not a pipeline bug), 2,211 parse entries total.
`pipeline/verify_parse_qal.py` independently re-derives every count via its own regex
scan and its own copy of the strong-root rule (rule 3). `app/views/parse.js` un-stubs the
`Parse` tab: same three-stage reveal pattern as vocab (surface form → transliteration →
root + gloss + parse label, e.g. "Qal infinitive construct"), same three-grade SRS.
`srs.js` `buildQueue`/`stats` took a `keyFn` parameter so vocab (keyed by lemma_id) and
parse (keyed by `parse:<entry id>`, since one lemma has many inflected entries) share one
`store.cards` map with independent daily new-card budgets rather than competing for one.
`app/selftest.html` gained structural checks for the parse deck. Verified end-to-end
in-browser: tab switch, all three reveal stages, grading, queue advance, Settings stats
unaffected by parse review activity.

## Done — Phase 4: reader, Jonah 1

`pipeline/curate_jonah1_extra.py` diffs Jonah 1's distinct lemmas (Hebrew/WLC
versification: 16 verses -- English 1:17, the fish-swallowing verse, is Hebrew 2:1 and is
deliberately left for the chapter 2 reading, not stitched on here) against
`data/vocab_deck_600.json` and curates glosses for the 31 lemmas not already in the
top-600 deck, same method as the Phase 2 gloss batches (lexicon-sourced citation form,
hand-curated English gloss checked against, not copied from, the Strong's draft).
`pipeline/build_jonah1_reader.py` builds `data/jonah1_reader.json`: one entry per printed
word (254 words), splitting each word's lemma/morph/text attributes on "/" per morpheme
(same technique `rank_lemmas.py` and `build_parse_qal.py` already use) to compose a
per-word gloss from its morphemes' individual glosses joined with " + ", while keeping the
*displayed* Hebrew as the real, unsplit printed word -- a prefixed vav or preposition is
never pulled into its own visual token, since that would show Hebrew that doesn't actually
look like Hebrew. Deliberately does not compute or show a part-of-speech or parse label per
word: Jonah 1 contains weak roots and non-Qal stems outside Tier 2's Qal-strong coverage,
and a lemma-level POS guess can be flatly wrong for a specific occurrence -- confirmed by
H3373 in this very chapter, tagged under one Strong's number across both a finite verb
(1:9) and a noun (1:10, 1:16). `pipeline/verify_jonah1_reader.py` independently re-scans
the raw WLC XML with its own regex and its own gloss lookup and diffs every word
entry-by-entry against the shipped JSON, not just aggregate counts. `app/views/read.js`
un-stubs the Read tab: no grading, no scheduler state, no queue -- every word in the
chapter is tap-to-reveal (transliteration + gloss) every time the page opens, and multiple
words can be open at once, since reading needs to check several words in one verse without
losing earlier reveals. Words not yet in the vocab deck get a subtle underline so new
vocabulary stands out without demanding anything. `app/selftest.html` gained structural
checks for the reader data (verse/word counts against metadata, gloss non-emptiness,
`is_known` cross-checked against `vocab_deck_600.json`, no duplicate word ids). Verified
in-browser via selftest (39/39 passing) and by scripting a tap -- open, reveal, tap again,
close -- and confirming the DOM state at each step.

## Done — Phase 5 progress: reader expanded to Jonah 2

Same pipeline as the Jonah 1 build, applied to chapter 2 (Hebrew/WLC versification: 11
verses, `Jonah.2.1`-`Jonah.2.11`; `Jonah.2.1` is the fish-swallowing verse English Bibles
number as `1:17` -- see `build_jonah1_reader.py`'s docstring for why it belongs in chapter
2, not stitched onto chapter 1). `pipeline/curate_jonah2_extra.py` diffed Jonah 2's 85
distinct lemmas against `vocab_deck_600.json` and `jonah1_extra.json` together (3 lemmas --
"Jonah", "dry ground", "vow" -- recur from chapter 1 and were reused as-is, not
re-curated), leaving 22 genuinely new lemmas curated into `glosses/jonah2_extra.json`.
Several needed a specific-occurrence sense check against the Strong's draft rather than its
first-listed gloss: H1530 (gal) is "wave" here (parallel with H4867 "breaker" in the same
line), not the draft's lead sense "heap of ruins"; H4487 (manah) is Piel "appoint, ordain"
("the LORD appointed a fish"), not the Qal "weigh out/enumerate" sense the draft leads
with; H7095 (qetsev) is BDB's "roots of the mountains" idiom, not the draft's bare
"shape, base". `pipeline/build_jonah2_reader.py` builds `data/jonah2_reader.json` from
three merged gloss sources (vocab deck + both Jonah extras) with the same hard-error-on-
unresolved-lemma behavior as the chapter 1 build. `pipeline/verify_jonah2_reader.py`
independently re-scans and re-derives every word, same method as `verify_jonah1_reader.py`.
112 words, 81/112 (72.3%) already known from the top-600 deck.

App side: the Read tab is no longer hardcoded to one chapter. `main.js` gained
`READER_CHAPTERS` (an ordered list of `{key, label, url}`, currently Jonah 1 and Jonah 2)
and a per-chapter load cache; `loadReaderData(key)` replaces the old no-argument version.
`read.js` gained a chapter switcher (reusing the `.seg` segmented-control style already in
`app.css` from Settings) rendered only when more than one chapter exists, so it stays
invisible today if a future edit ever trims the list back to one. Switching chapters clears
the tap-to-reveal open state, consistent with the existing "every chapter open starts
closed" rule -- carrying revealed words across chapters was never the intent and risked an
id collision showing something pre-opened. `app/selftest.html`'s reader checks now loop
over `READER_CHAPTERS` generically instead of checking one hardcoded file. Verified
in-browser: selftest 46/46 passing, chapter switcher renders both chapters and toggles
`aria-pressed` correctly, tap-to-reveal confirmed on Jonah 2:1's first word (`וַיְמַן` ->
"wayman" -> "and + appoint, ordain (piel)").

## Next — Phase 5: Tiers 3–5

Weak verbs, derived stems, sustained reading. Still further out and not yet scoped. The
reader can keep growing the same way (Jonah 3-4, then Ruth, per the locked reading order)
independent of when the grammar tiers get scoped.

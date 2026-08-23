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

## Done — Phase 5 progress: reader finishes the book of Jonah (chapters 3-4)

Same pipeline again, applied to the last two chapters: `curate_jonah3_extra.py` (12 new
lemmas; chapter 3 has no versification divergence from English, 10 verses) and
`curate_jonah4_extra.py` (17 new lemmas; 11 verses, also no divergence). No lemma overlap
between the two chapters' new-lemma sets, so nothing was reused between them, though both
scripts diff against all prior chapters' curated glosses (rule 3's "assume the same class
of bug is always present" extends to "assume a word recurs unless checked" -- worth
checking every time, even when it turns out not to apply). `build_jonah3_reader.py` and
`build_jonah4_reader.py` each merge the vocab deck plus every glosses/jonah*_extra.json
curated so far (chapter 4's build pulls from all four). `verify_jonah3_reader.py` and
`verify_jonah4_reader.py` independently re-derive both, same method as the first two
chapters. Jonah 3: 139 words, 114/139 (82.0%) already known. Jonah 4: 183 words, 147/183
(80.3%) already known.

A few glosses needed a specific-occurrence check rather than the Strong's draft's lead
sense, same discipline as the chapter 2 curation: H2940 (ta'am) is "decree" in "by decree
of the king" (3:7), not its more common literal "taste" sense; H6923 (qadam) is "anticipate,
be quick to act" in "I was quick to flee" (4:2), not its more common spatial "go before/
meet" sense. Also confirmed H5968 (`alaph`) and H5848 (`ataph`, curated for chapter 2) are
genuinely different roots that both happen to mean "grow faint" in their respective
contexts -- kept as separate lemma entries, not merged.

`main.js`'s `READER_CHAPTERS` list now has all four Jonah chapters; no other app code
needed to change; the multi-chapter plumbing built for the Jonah 2 add (Phase 5's first
step) generalized cleanly. Verified in-browser: selftest 60/60 passing across all four
chapters, chapter switcher lists all four labels, tap-to-reveal confirmed on Jonah 4's
final word (`רַבָּה` -> "rabah" -> "much, many, great", the closing "much cattle" of 4:11).
The book of Jonah is now fully readable in the app, cover to cover.

## Done — Phase 5 progress: parse-tab bug fixes

Lane flagged real errors in the Parse tab. Two conjugation-letter bugs, confirmed against
the OSHB morphology spec directly (not just re-derived from this project's own prior
belief about it): the morph code for sequential perfect (weqatal, letter `q`) was
mislabeled "yiqtol"; genuine imperfect (yiqtol, letter `i`) wasn't matched by the regex at
all, so those forms were silently absent rather than wrong. Also, `surface_form` was only
the verb's own "/"-separated morpheme -- any prefix (a wayyiqtol's defining vav, a
preposition) or suffix (a pronominal object) was stripped, sometimes leaving a fragment
that isn't a real Hebrew word. `build_parse_qal.py` now shows the whole printed word
(matching how the Jonah readers already display words), splitting it into
`prefix_form`/`verb_form`/`suffix_form` for highlighting, resolving any prefix against the
same curated `F-<letter>` function-word entries the readers use, and capturing a trailing
pronominal suffix's person/gender/number (or paragogic nun/he) where present. Weqatal
added as its own labeled conjugation (Lane's call -- it's weqatal's direct pairing with
wayyiqtol/yiqtol that makes the whole-word display worth having). Deck grew from 2,211 to
2,819 entries. `app/views/parse.js` highlights the verb morpheme in accent color within
the full word and reveals prefix glosses + suffix PGN at stage 2.

While rebuilding, a related transliteration bug surfaced: a word-initial shuruq vav (e.g.
וּבַיּוֹם) was rendering as a bare "w" instead of "u-" -- the BuMP-rule case
`transliteration-reference.md` had flagged as "probably not live" turned out to affect 159
of 2,819 parse cards (5.6%). Fixed in `transliterate.py` (a vav+dagesh with no vowel of
its own and nothing preceding it is now read as the syllable "u", not a consonant); final-
he stayed as-is per Lane's explicit preference (keep "torah"/"malkah", don't add the
mappiq-silent distinction). `verify_parse_qal.py` gained a golden regression set (six real
corpus refs, one per conjugation, checked against the external OSHB spec page) and a
whole-word reconstruction check; `verify_transliterate.py` gained a corpus-word regression
pair for the shuruq fix. `selftest.html` gained the same reconstruction check. Every data
file that bakes in a transliteration was rebuilt and re-verified. Verified in-browser: the
original bug's own example (`יִּשְׁבֹּת`, cited in `morphology-reference.md`) now shows as
the full word `וַיִּשְׁבֹּת`, transliterates "wayishbot", and labels "Qal wayyiqtol
(narrative), 3rd masc. sing."

## Done — Phase 5 progress: Learn tab, lesson group 1 (prefixes and suffixes)

Lane doesn't yet know the grammar rules behind what Vocab/Parse/Read already have him
recognizing by pattern. Rather than guess at a curriculum, `pipeline/hebrew_corpus.py`'s
Jonah word dump was used to count what actually shows up in the text: prefixed/suffixed
function morphemes touch a large fraction of every sentence (conjunction vav 132/688
words, definite article 72, the four inseparable prepositions 102 combined, pronominal
suffixes 99), so that became lesson group 1, with construct chains (72/205 nouns, 35%),
the verb system, and sentence-level syntax queued as later groups -- see the concept list
given to Lane in-conversation for the full breakdown. Lane chose the format (a dedicated
Learn tab with short lessons, not just-in-time popups) and the starting group.

`pipeline/build_lessons_group1.py` builds `data/lessons_group1.json`: 6 lessons (vav,
definite article, the ל/ב/כ/מן prepositions, pronominal suffixes, the relative
אֲשֶׁר/שֶׁ-, the interrogative הֲ prefix -- the latter appears exactly once in the whole
book, in Jonah's complaint at 4:2), 18 examples total, every one a real word pulled from
Jonah 1 or 4:2 by its OSIS word id (never typed by hand) and decomposed generically
(works for a noun/preposition/verb base, not just Qal verbs like `build_parse_qal.py`) into
prefix/base/suffix spans, with prefix glosses resolved against the same curated
`F-<letter>` entries the readers use and whole-word transliteration computed once (not
per-morpheme, per the parse-tab lesson above). `pipeline/verify_lessons_group1.py`
independently re-implements the decomposition against a fresh XML re-scan and diffs every
field. `app/views/learn.js` adds the 5th tab: a lesson list, and a detail view that
highlights whichever span (prefix/base/suffix) the lesson is actually about, in the same
accent-color convention Parse already uses. Not gated behind completion, matching the Read
tab's philosophy (no progress bar, no streaks). Verified in-browser: selftest 71/71
passing, all six lessons render, prefix- and suffix-highlighted examples both confirmed
via DOM inspection.

## Done — Phase 5 progress: Learn tab, lesson group 2 (construct chains)

Lane asked for this one directly (construct chains were flagged as the single biggest
untaught gap: 72 of 205 nouns in Jonah, 35%, are in construct state). Two example shapes
needed this time, not one: a construct chain is written as two or three separate `<w>`
elements, not one word's internal "/" morphemes, so highlighting "which word is
construct" is a genuinely different operation from group 1's "which part of this one word
is the prefix" -- `build_lessons_group2.py` reuses group 1's `decompose()` per token
(imported directly -- sharing logic between *build* scripts is fine; it's *verify*
scripts that must stay independent, and `verify_lessons_group2.py` re-implements
everything from scratch same as every other verifier) and adds a `noun_role()` classifier
that reads a token's own grammatical state (construct/absolute) directly off its morph
code's trailing state letter -- never inferred from word order, which would silently get
a proper-noun-final chain wrong (proper nouns carry no state letter at all).

5 lessons, 11 examples, real words/phrases from Jonah 1 and 3: the basic two-noun chain
(דְּבַר יְהוָה, "word of the LORD" -- the book's opening words), the construct form's
vowel shrink (compared directly against the word's own dictionary citation form, which
`lemma_citation_form` already captured for group 1 -- no new field needed, just a UI rule:
show a comparison line whenever the two differ), definiteness traveling through the chain
from its last word only (אֱלֹהֵי הַשָּׁמַיִם / מֶלֶךְ נִינְוֵה), a genuine three-noun
stacked chain (מַהֲלַךְ שְׁלֹשֶׁת יָמִים, "a three-day journey"), and the feminine
ה→ת / plural ־ִים→־ֵי construct endings (including אַנְשֵׁי, flagged honestly as a
suppletive plural -- singular "man" and plural "men" don't share a stem at all, not just
a swapped ending). One example needed a note correction after a first in-browser check:
`melekh`'s construct and citation forms differ by an invisible trailing shva (an
orthographic convention, not a grammatical one) that the "completely identical" note text
hadn't accounted for -- caught by actually reading the rendered page, not just running the
verifier, which only checks that shipped and recomputed data agree with each other.

`load_lookups()` (shared by both group scripts) widened from two curated gloss files to
all four `jonah*_extra.json`, since group 2's examples draw on chapter 3's curated extras
-- confirmed as a no-op for group 1's own output before shipping it. `main.js` replaced
its group-1-specific loader with a generic `LESSON_GROUPS` list (same pattern as
`READER_CHAPTERS`); `learn.js`'s list view now sections lessons by group, and its detail
view renders either shape (single-word or multi-token chain, colored by role instead of
by highlight span). Verified in-browser: selftest 80/80 passing, both groups list
correctly, all 5 new lessons opened and read, construct/absolute role coloring confirmed
via DOM inspection on both the 2-token and 3-token chain examples.

## Done — Phase 5 progress: Learn tab, lesson group 3 (the verb system)

The biggest conceptual group so far: binyan semantics, the qatal/yiqtol aspect
distinction, vav-consecutive (wayyiqtol/weqatal), participles, infinitive construct, and
the imperative/cohortative/jussive command forms. All single-word examples (no new
example shape needed this time -- `build_lessons_group3.py` reuses group 1's
`decompose()` directly, same import pattern group 2 used for its own single-word
lessons), so the build script is close to group 1's in shape, just with a new curated set.

6 lessons, 22 examples, all real Jonah words. The binyan lesson's anchor pair wasn't
assumed -- every lemma's set of attested stems was cross-tabulated across the whole book
first, to find a root genuinely attested in more than one binyan rather than picking two
unrelated "typical" forms and implying a contrast that isn't actually in this text. That
turned up נָפַל (Qal "fall") used in both Hiphil and Qal in the *same verse*, Jonah 1:7
("...so they cast [Hiphil, causative: made [the lots] fall] lots, and the lot fell [Qal]
on Jonah") -- a better illustration than anything that would have been picked by
assumption. `verify_lessons_group3.py` re-confirms this specific claim independently (not
just via the generic per-field diff): it re-scans the whole book itself and checks that
H5307 genuinely has both stems attested, and that the two curated word ids really are
that lemma in those two stems. The other four locked-priority stems (Niphal, Piel,
Hiphil again, Hitpael) each get their own single real-word example too. The
vav-consecutive lesson leads with the raw number that motivates the whole lesson: 84 of
202 verb-morphs in Jonah (42%) are wayyiqtol.

One deferred wrinkle, noted rather than silently fixed: בֹרֵחַ ("fleeing", Jonah 1:10)
transliterates with a soft "v" despite being word-initial, because the actual Masoretic
pointing genuinely omits dagesh lene there (confirmed against the raw codepoints, not a
transliterate.py bug) -- a real, if secondary, phonetic-convention detail past this
lesson's own scope, left as an accurate-but-unexplained data point rather than a tangent
in the lesson prose.

`main.js`'s `LESSON_GROUPS` list now has all three groups; no other app code needed to
change, since `learn.js` and `selftest.html` were already written generically over that
list in the group-2 pass. Verified in-browser: selftest 89/89 passing, all three groups
list correctly under their own headings, the binyan lesson's Hiphil/Qal pair and the
commands lesson's four command types all confirmed by reading the actual rendered page.

## Done — Phase 5 progress: Learn tab, lesson groups 4–5 (the rest of the concept list)

Lane asked for the whole original concept list finished, not just the next single group.
Two groups, built and shipped together: group 4 picks up the noun-phrase items group 2
(construct chains) had left over -- gender/number markers, the direct object marker אֵת,
adjective agreement, demonstratives and numbers; group 5 is sentence-level syntax --
default verb-subject-object word order, verbless/nominal clauses, and what vav is doing
between whole clauses beyond a bare "and". Between them, every item from the concept list
given to Lane in conversation is now built.

Both groups needed multi-word phrase examples again (adjective-agreement pairs, full
verbless clauses, word-order contrasts) -- reusing group 2's "chain" shape (a `tokens`
array, one entry per printed word), but none of these phrases have a construct-chain's
lean-on-the-next-word relationship, so forcing them into "construct"/"absolute" roles
would have been a false claim. Added a third role, "plain" (no accent/dim split -- the
words are just read in sequence), rather than stretch the existing two to cover a
different relationship. `app/views/learn.js` and `app/selftest.html` both updated to
accept it; group 2's own construct/absolute chains are untouched and still render exactly
as before.

Group 4's clearest example needed a genuine exception, not a rule stated as absolute:
גּוֹרָלוֹת ("lots", Jonah 1:7) is a MASCULINE noun that still pluralizes with the
"feminine-looking" ות ending -- included specifically so the gender/number lesson doesn't
overclaim that the ending alone always tells you the gender. Group 5's word-order lesson
pairs the default (וַיְמַן יְהוָה דָּג גָּדוֹל, "and the LORD appointed a great fish" --
verb-subject-object) directly against a real deviation from it (וְיוֹנָה יָרַד, "but Jonah
had gone down" -- subject fronted for a scene change), rather than only showing the
default and asserting the exception exists.

10 lessons, 17 examples, all real Jonah words/phrases across chapters 1, 2, and 4. Both
`verify_lessons_group4.py` and `verify_lessons_group5.py` follow the same independent
re-derivation discipline as every other lesson verifier. `main.js`'s `LESSON_GROUPS` list
now has all five groups; no other app code needed structural changes beyond the new
"plain" role. Verified in-browser: selftest 107/107 passing, all five groups list under
their own headings, the 4-token word-order and verbless-clause phrases both confirmed
rendering with zero highlight spans (plain text, as intended) via direct DOM inspection.

## Done — Phase 5 progress: optional cross-device sync via GitHub Gist

Lane asked whether export could "save progress to the site" via a token. Clarified first
(this is a static site with no backend, so the only way is the browser talking to an API
directly) and asked what he actually wanted before building anything — auto-sync, or just
a manual Import button with no token/network involved. He chose auto-sync.

`app/sync.js` is new and entirely opt-in: with no token configured it makes zero network
requests, so CLAUDE.md's "no external requests other than the pinned ts-fsrs CDN" default
still holds for anyone who never opens Settings and pastes one in. Once configured, it
round-trips `store.js`'s state through a private GitHub Gist (not the app's own repo --
committing a progress blob into the site's source history on every review would spam it
with noise unrelated to the app itself).

Two things worth calling out:
- **The token never touches exported files.** It lives in its own localStorage key
  (`hebrew:sync:v1`), completely separate from the `hebrew:v1` key `exportBlob()` reads --
  confirmed directly in-browser (fetched the real export blob and grepped it for
  "token"/"gistId": absent). A credential leaking into a backup file the user might
  later share or upload somewhere else would be exactly the kind of quiet, easy-to-miss
  mistake worth checking for directly rather than assuming the separation held.
- **Merge is per-card, not per-blob.** Card records are independent and each carries
  `reps` (only grows through review) and `last_review`, so `mergeStates()` keeps whichever
  side of *each individual card* represents more/newer review activity, rather than one
  whole device's session silently overwriting the other's the moment they next sync.
  Reviewing on your phone and then your laptop before either one syncs keeps both
  sessions' progress. Settings (theme/sound/daily cap) are deliberately NOT merged --
  they're a per-device preference, not progress, so each device keeps its own.

Settings gained a "Sync across devices" block: paste-a-token-and-Connect when
disconnected, or a status line ("Synced Xm ago" / a plain-language error) plus "Sync now"
and "Disconnect this device" when connected. The disconnected state links straight to a
token creation page with the exact scope needed already explained in the surrounding
text. Verified in-browser: selftest 108/108 passing (sync.js added to both the
Hard-Rule-1 grep list and confirmed Hebrew-free); an intentionally invalid token produces
a clean inline error with nothing written to localStorage; a simulated connected state
renders the status/Sync-now/Disconnect UI correctly, including the automatic
pull-on-boot failing gracefully in the background without breaking the rest of the app;
Disconnect clears local sync state without touching the export path.

Known, accepted limitation (documented in `sync.js`'s own docstring, not silently
assumed away): no optimistic-concurrency check on the Gist write, so two devices syncing
within the same few seconds of each other could race. Fine for one person's couple of
devices; would need real handling before this could serve independent multi-user sync.

**Correction, caught by Lane actually trying it:** shipped pointing at GitHub's
fine-grained-token creation page with instructions to scope it to Gists. Lane reported
the Gists option wasn't there. Checked directly rather than re-guessing: fine-grained
PATs' own permissions reference lists a Gists entry, but multiple independent reports
describe the *token-creation UI itself* not exposing it -- a real, apparently
still-live gap between what the API supports and what the web form offers, not
something Lane was missing. Switched the link and every doc reference to a classic
token with only the "gist" scope checkbox checked, which has worked unchanged for
years. The security property this was meant to guarantee (a leaked token can't touch
anything but gists) holds exactly the same either way -- classic scopes are additive
checkboxes, not all-or-nothing, so checking only "gist" is just as narrow as the
fine-grained version would have been.

## Done — Phase 5 progress: undo this session's reviews

A narrower sibling to "Reset all progress." `store.js` now captures a one-time, in-memory
snapshot of `cards` the first time a page load actually reads them from localStorage --
never written anywhere, so it's naturally scoped to "since I opened the app this time"
and disappears on reload without any extra cleanup code. Settings shows "Undo this
session's reviews" only once something has actually changed relative to that snapshot
(`hasSessionChanges()`), and undoing (`undoSession()`) backs up the about-to-be-discarded
state first, same convention `resetAll()` already used. `resetAll()` itself now also
resets the snapshot to empty, so it doesn't leave a stray "undo the reset" button behind
-- confusing double-negative UI caught and fixed before it shipped, not after. Verified
in-browser: selftest 108/108 unaffected; button absent on a fresh load, appears after
grading one real card, reverts the card count to zero on click, disappears again after,
and a `hebrew:backup:session-undo-*` key is confirmed written before the revert.

## Next — Phase 5: Tiers 3–5 (grammar tiers), further lesson groups if scoped

The Learn tab's original concept-list scope is fully built across five groups. Any
further lesson group would be a new addition, not yet scoped. Weak verbs and derived
stems (Tiers 3–4) are still further out and not yet scoped either. Reading order
(CLAUDE.md) goes to Ruth next for reader expansion, whenever that's picked up,
independent of when the grammar tiers get scoped.

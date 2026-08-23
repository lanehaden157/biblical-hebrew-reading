# Biblical Hebrew reading curriculum

Self-built interactive curriculum. Phone-first PWA on GitHub Pages.

## Goal

Lane reads Exodus 3 and 14 unaided. **Recognition-level reading comprehension** —
not academic mastery, not production, not translation for a grade. Hobby pace.
Lane is starting from zero; no prior Hebrew assumed.

Horizon: roughly 11–13 months at a loose daily habit. There is no deadline and no exam.

## Hard rules

1. **Never hand-type pointed Hebrew.** Every Hebrew string and every parse answer key is
   generated from the OSHB corpus and verified against it programmatically.
   Source: `npm pack morphhb` (CC BY 4.0, ~20 MB, ~30s). WLC text is public domain.
   This extends to app source: **no Hebrew letters in any `/app/` file.** Every glyph the
   user sees is fetched from `/data` at runtime. Mechanically checkable — grep `/app/` for
   U+05D0–U+05EA and expect zero hits. If a view needs Hebrew that isn't in a data file yet
   (an alphabet chart, a paradigm table), generate that file in `/pipeline` rather than
   typing the letters into the view.
2. **Never apply NFC or NFD normalization to Hebrew text.** OSHB explicitly warns against it.
   Normalizing reorders combining marks and breaks display silently — the text still looks
   plausible. This is not theoretical; it alters the current data files.
   Stripping characters (e.g. cantillation U+0591–U+05AF) is deletion, not normalization, and is fine.
3. **Every generation step ships a verification script.** Not optional. The two bugs found
   during Tier 0 (a morph regex matching construct plurals; an unpointed defective spelling
   selected as a teaching example) both produced plausible-looking wrong output and were
   caught only by checking. Assume the same class of bug is always present.
4. **Every Hebrew form shown to the user gets transliteration + gloss.**
5. **No fixed session length, no streaks, no guilt mechanics.** Lane skips days and doubles up.
   Cap the daily review queue (~40 cards) and quietly defer the rest, so returning after a
   gap never shows a wall of due cards.
6. **Persisted state is versioned; review history is never silently destroyed.** Every
   localStorage object carries a `schemaVersion`. Review history is the only data in this
   project that cannot be regenerated from the corpus — the corpus, glosses, and every
   generated file can be rebuilt from `/pipeline` in minutes; six months of FSRS scheduling
   state cannot. Before any migration the app copies the old state to a separate
   localStorage key (`hebrew:backup:v<n>`), not to a file download — downloads are awkward
   to retrieve inside an iOS home-screen app. Pre-1.0, a schema change may reset state
   rather than migrate, but only with a visible warning and an export offered first.

## Transliteration scheme

Plain ASCII, chosen to survive copy-paste and phone keyboards:

```
' b g d h w z kh t y k l m n s ` p ts q r sh s t
```

`'` = alef, `` ` `` = ayin. Two distinct consonants, both silent-looking in English.
Greek, if it ever appears, is always transliterated with a gloss — never bare Greek script.

Implementation: `pipeline/transliterate.py`. Its docstring is the authority on the edge
cases the scheme above doesn't state — shva na/nach rules, matres lectionis absorption,
and its deliberate omissions. This isn't locked or off-limits for revision; "decided"
means read the docstring before re-deriving a rule from scratch, not "never reopen this."
If a gap below is worth fixing, fix it — a revision just has to re-run every generated
data file afterward, since transliterations are never hand-typed.

**Fixed (were gaps, confirmed against real output before and after):**
- **Bet/kaf/pe spirantization.** Now dagesh-sensitive: b/v, k/kh, p/f, read directly off
  whether a dagesh is written (Masoretic pointing always marks dagesh lene explicitly when
  the plosive form applies, so its absence is a reliable signal, not a guess). Soft kaf
  intentionally renders the same "kh" as het — they're the same sound in standard
  pronunciation, so this is a correct merge, not a lost distinction; the Hebrew letters
  shown alongside every transliteration (rule 4) still disambiguate which one it was. The
  other three BGDKPT letters (gimel/dalet/tav) are deliberately left alone: their spirant
  forms don't survive outside Yemenite pronunciation. Was widespread before the fix: 146 of
  the 600 vocab-deck citation forms (24%) contained at least one affected letter.
- **Furtive patach.** A patach on a word-final het/ayin/heh(+mappiq) now renders
  vowel-then-consonant (`transliterate('רוּחַ')` → `ruakh`, not the old `rukha`), matching
  how it's actually pronounced. Scoped to word-final position, the standard textbook case.

Both fixes live in `pipeline/transliterate.py`; every generated data file that bakes in a
transliteration (`vocab_deck_600.json`, `parse_qal_strong.json`, `jonah1_reader.json`) was
rebuilt and re-verified afterward, per this file's own instruction above.

**Known gap, not fixed — confirmed real, and confirmed why it's harder than the other two:**
- **Qamats gadol vs. qamats qatan.** Always rendered "a" (gadol); qatan sounds like "o" and
  requires knowing the syllable is both closed AND unaccented. `transliterate('כָּל')`
  ("kol", all/every — rank 11 by frequency in the whole Bible) → `kal` is still wrong.
  Accent position could in principle be read off cantillation before this project strips
  it, but the single most common real-world trigger — a maqqef binding this word to the
  next, which removes its independent stress — turns out to live in OSHB as a separate
  `<seg type="x-maqqef">` element between `<w>` elements, not inside either word's own
  text (confirmed against the raw corpus while investigating this). That means it's
  invisible to `transliterate()` no matter what string it's given; a real fix needs the
  calling pipeline script to detect the maqqef in the verse XML and pass stress context
  in, which is a bigger, separately-scoped change, not a `transliterate.py`-only fix.

## Locked decisions — do not re-litigate

- **Vocabulary target: ~600 lemmas** (= 80% token coverage). Not 1000. The next 400 lemmas
  buy 5 percentage points for 40% more memorization.
- **Cards are Hebrew → English only.** No reverse cards. Production is out of scope and
  reverse cards roughly double review load for a skill Lane does not need.
- **Teach REVERSE-parsing** (form → root + stem + conjugation + PGN), not forward paradigms.
  Textbooks teach production; reading requires the inverse.
- **Sequencing: hybrid** — grammar-led, real text early.
- **Binyan order by measured frequency**, which deviates from every textbook:
  Qal 69.0% > Hiphil 13.0% > Piel 8.9% > Niphal 5.7% > Hitpael 1.3%.
  Pual (0.6%), Hophal (0.6%) and rarer stems: recognition only, never drilled.
- **Conjugation priority:** qatal, wayyiqtol, yiqtol, participle (= 71.7% of verb forms),
  then infinitive construct (= 80.8% cumulative).
- **Reading order:** Jonah → Ruth → Genesis narrative chapters → Exodus 3, 14.
  Jonah is not the lexically easiest text (78.9% top-600 coverage vs Genesis 81.3%) but it is
  the shortest complete narrative: 668 tokens, 81 distinct unknown lemmas. Finishing matters.
- **Poetry excluded from v1.** Psalms 73.6%, Isaiah 72.1%, Song 55.0% top-600 coverage.
- **Font: system default.** Verified correct niqqud placement on iPhone (Claude app webview,
  WebKit). No webfont bundle needed. Re-verify once in Safari after first deploy.
  If it ever breaks, fall back to Ezra SIL (OFL 1.1) — never SBL Hebrew, whose license
  forbids redistributing subsetted or converted versions.
- **SRS: ts-fsrs** (MIT, via jsDelivr CDN, pinned version — never `@latest`).
  Do not reimplement a scheduler. Note the CDN is the one thing preventing true offline
  use; when offline matters, vendor the file into the repo rather than dropping ts-fsrs.
- **Persistence: localStorage + a JSON export button.** Per-device; no sync. Accepted.
- **Cut from v1:** poetry, Pual/Hophal drilling, infinitive absolute nuance, audio.

## Tiers

| | | |
|---|---|---|
| 0 | Script + pointing | ~3 wk — **done**, disposable prototype |
| 1 | Noun phrase system | ~7 wk |
| 2 | Qal + narrative chain | ~12 wk |
| 3 | Weak verbs, one class at a time | ~14 wk |
| 4 | Derived stems | ~9 wk |
| 5 | Sustained reading | ongoing |

## Repo layout

```
/data/          generated JSON. Never edited by hand. Regenerated by /pipeline.
/pipeline/      Python. OSHB XML + lexicon -> data/*.json. Ships verify_*.py alongside.
/app/           static JS/CSS/HTML. Reads /data. No build step. See conventions below.
/glosses/       curated English glosses, keyed by Strong's number. Hand-authored, reviewed.
index.html      entry point
CLAUDE.md       this file
```

Content (JSON) stays separate from engine (JS) so drill banks can be regenerated and
expanded without touching app code.

### App conventions

Vanilla ES modules. No framework, no bundler, no build step — what's in the repo is what
runs. One module per concern (`store.js`, `srs.js`, `feedback.js`, `theme.js`) plus one
per view. No analytics, no telemetry, no external requests other than the pinned ts-fsrs
CDN URL.

Rule 3 (every generation step ships verification) has an app-side form: `/app/selftest.html`
asserts the data invariants the UI depends on — deck loads, 600 entries, ranks 1–600 with
no gaps, every entry has a non-empty transliteration and gloss. It is a page, not a test
framework; open it after any data regeneration.

**No service worker** until the app stops changing weekly. A service worker serving a stale
cache is unpleasant to clear from a phone, and the offline benefit is small while the app
is edited daily. Note this does not block "Add to Home Screen" on iOS, which works from the
manifest alone; it would block Chrome's install prompt on Android.

## Deployment

Live at `https://lanehaden157.github.io/biblical-hebrew-reading/`, GitHub Pages serving
from the repo root on `main`. Pages serves from a **subpath**, not a domain root, so every
fetch, `src`, and `href` in `/app/` must be relative (`../data/…`), never root-absolute
(`/data/…`). Root-absolute paths work perfectly on localhost and 404 in production — this
is the single most likely deploy-time failure, and it looks like a data problem, not a
path problem.

## Data sources

- **Corpus:** `openscriptures/morphhb` — WLC with 100% morphology coverage.
  Word tags carry `lemma` (Strong's, `/`-separated by morpheme), `morph` (e.g. `HC/Vqw3ms`),
  and a stable `id`. Morph codes: `Vqw3ms` = verb, Qal, wayyiqtol, 3ms. `Ncmsc` = noun,
  common, masc, sing, construct. Note morph position codes are compact —
  `Ncmsa` is 5 characters. An off-by-one in a regex here silently selects wrong forms.
- **Lexicon:** `openscriptures/HebrewLexicon` — Strong's + BDB, keyed by the same numbers.
  Strong's `meaning` is a usable draft but archaic and sometimes misleading
  (*nefesh* as "a breathing creature", *chesed* as "mercy"). Always curate before shipping.

## Current status

This section is rewritten at each phase boundary; `git log` is the real history.

**Done — Phases 1–2 (Tier 0–1 build).** Pipeline builds `data/top600.json` from OSHB. All 600
lemmas curated across six gloss batches, reviewed, verified. Transliteration generator
complete and verified against all 600 forms. `data/vocab_deck_600.json` built. Vocab SRS app
shipped and live at the Pages URL: three-stage card reveal (Hebrew → transliteration →
gloss), three grade buttons (Again/Good/Easy, `Hard` dropped), light/dark theme following
the system setting, sound feedback (default on, per-grade tones) behind `feedback.js`.
Haptics were attempted (standard vibration API, then an undocumented iOS switch-click trick)
and dropped after real-device testing confirmed neither fires in iOS Safari — there is no
haptics toggle or code path. Session-length tracking was built and then deliberately
removed: this is a casual hobby project, and a persisted timing log is the kind of
quantified-self mechanic hard rule 5 (no streaks, no guilt mechanics) exists to keep out.
`store.js` has no `sessions` field.

**Done — Phase 3 (Tier 2 build): parsing gym, Qal strong verbs.** `pipeline/build_parse_qal.py`
pulls Qal forms in the locked conjugation-priority order (qatal, wayyiqtol, yiqtol,
participle, infinitive construct — confirmed exact `morph` codes against the whole corpus
rather than assuming: `Vq` + one of `pwqrc` + a person/gender/number or gender/number/state
suffix) restricted to **strong** roots. Strong-root test: triliteral, no radical in
{alef,he,het,ayin} (covers I/II/III-guttural and III-He/III-Aleph in one check), first
radical not nun, first radical not vav/yod, second radical not vav/yod or equal to the
third (hollow/geminate). Root lemmas are restricted to the 181 verb lemmas already in the
curated top-600 vocab deck, not all Qal-attested lemmas in the corpus — reuses their
lexicon-sourced citation form, transliteration and gloss rather than a second curation
pass, and keeps parsing practice anchored to vocabulary already being learned. Yields 41
strong-root lemmas, 34 of which are actually attested in Qal in the corpus (the other 7 —
בקש, שלך, קטר, שרת, מלט, שמד, סתר — are cited in Qal-perfect form by convention but
essentially never occur in Qal; confirmed against BDB usage, not a pipeline bug), 2,211
parse entries total. `pipeline/verify_parse_qal.py` independently re-derives every count
via its own regex scan and its own copy of the strong-root rule (rule 3). `app/views/parse.js`
un-stubs the `Parse` tab: same three-stage reveal pattern as vocab (surface form →
transliteration → root + gloss + parse label, e.g. "Qal infinitive construct"), same
three-grade SRS. `srs.js` `buildQueue`/`stats` took a `keyFn` parameter so vocab (keyed by
lemma_id) and parse (keyed by `parse:<entry id>`, since one lemma has many inflected
entries) share one `store.cards` map with independent daily new-card budgets rather than
competing for one. `app/selftest.html` gained structural checks for the parse deck.
Verified end-to-end in-browser: tab switch, all three reveal stages, grading, queue
advance, Settings stats unaffected by parse review activity.

**Done — Phase 4: reader, Jonah 1.** `pipeline/curate_jonah1_extra.py` diffs Jonah 1's
distinct lemmas (Hebrew/WLC versification: 16 verses -- English 1:17, the fish-swallowing
verse, is Hebrew 2:1 and is deliberately left for the chapter 2 reading, not stitched on
here) against `data/vocab_deck_600.json` and curates glosses for the 31 lemmas not already
in the top-600 deck, same method as the Phase 2 gloss batches (lexicon-sourced citation
form, hand-curated English gloss checked against, not copied from, the Strong's draft).
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

**Next — Phase 5: Tiers 3–5** (weak verbs, derived stems, sustained reading) is further out
and not yet scoped. A natural near-term next step is expanding the reader beyond Jonah 1
(Jonah 2-4, then Ruth, per the locked reading order) using the same pipeline now that it
exists, rather than treating Jonah 1 as a one-off.

## Working style

- State magnitudes with units. Say plainly when something is fine.
- Compute from the corpus rather than citing published figures. When they conflict, report
  both and say which method produced which. (Qal at 69.0% computed here reproduces
  Pratico & Van Pelt's published figure — a useful pipeline sanity check.)
- Name which inputs came from Lane and which were assumed. Label conditional outputs
  as conditional.
- When Lane pushes back, recheck the arithmetic or the source. Do not reflexively concede
  or reflexively defend.

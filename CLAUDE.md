# Biblical Hebrew reading curriculum

Self-built interactive curriculum. Phone-first PWA on GitHub Pages.

## Goal

Lane reads Exodus 3 and 14 unaided. **Recognition-level reading comprehension** —
not academic mastery, not production, not translation for a grade. Hobby pace.
Lane is starting from zero; no prior Hebrew assumed.

Horizon: roughly 11–13 months at a loose daily habit. There is no deadline and no exam.

## Hard rule

Always be extremely careful when you:

1. **hand-type pointed Hebrew.** Every Hebrew string and every parse answer key is ideally
   generated from the OSHB corpus and verified against it programmatically.
   Source: `npm pack morphhb` (CC BY 4.0, ~20 MB, ~30s). WLC text is public domain.
   This extends to app source: **no Hebrew letters in any `/app/` file.** Every glyph the
   user sees is fetched from `/data` at runtime. Mechanically checkable — grep `/app/` for
   U+05D0–U+05EA and expect zero hits.Mistakes are very easy to make here so its worth double checking and paying close attention when youre typing, only for benign tasks like copying and transferring texts try to source whenever possible

## Strong suggestions

Everything below is a default worth following, not a wall. Deviate when there's a good
reason, and say what the reason was.

2. **Avoid applying NFC or NFD normalization to Hebrew text.** OSHB explicitly warns against
   it. Normalizing reorders combining marks and breaks display silently — the text still
   looks plausible. This is not theoretical; it has altered the current data files before.
   Stripping characters (e.g. cantillation U+0591–U+05AF) is deletion, not normalization, and is fine.
3. **Every generation step should ship a verification script.** The two bugs found during
   Tier 0 (a morph regex matching construct plurals; an unpointed defective spelling
   selected as a teaching example) both produced plausible-looking wrong output and were
   caught only by checking. Assume the same class of bug can be present.
4. **Every Hebrew form shown to the user should get transliteration + gloss.**
5. **Prefer no fixed session length, no streaks, no guilt mechanics.** Lane skips days and
   doubles up. Cap the daily review queue (~40 cards) and quietly defer the rest, so
   returning after a gap never shows a wall of due cards.
6. **Persisted state should be versioned; try not to silently destroy review history.** Every
   localStorage object carries a `schemaVersion`. Review history is the only data in this
   project that cannot be regenerated from the corpus — the corpus, glosses, and every
   generated file can be rebuilt from `/pipeline` in minutes; six months of FSRS scheduling
   state cannot. Before a migration, prefer copying the old state to a separate localStorage
   key (`hebrew:backup:v<n>`) rather than a file download — downloads are awkward to
   retrieve inside an iOS home-screen app. Pre-1.0, a schema change resetting state instead
   of migrating is acceptable, but should come with a visible warning and an export offered
   first.

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
  shown alongside every transliteration (suggestion 4) still disambiguate which one it was. The
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

## Strong suggestions — established decisions, worth reconsidering only with a real reason

These were reasoned through already; re-derive from scratch only if something's actually
changed, not out of habit.

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

Suggestion 3 (every generation step ships verification) has an app-side form: `/app/selftest.html`
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

## Commands

```
npm pack morphhb                        # pull/refresh the OSHB corpus source
python pipeline/rank_lemmas.py          # build data/top600.json from OSHB
python pipeline/build_vocab_deck.py     # build data/vocab_deck_600.json
python pipeline/build_parse_qal.py      # build Qal-strong parsing entries
python pipeline/verify_parse_qal.py     # independent re-derivation check for parse data
python pipeline/curate_jonah1_extra.py  # curate glosses for Jonah 1 lemmas not in top-600
python pipeline/build_jonah1_reader.py  # build data/jonah1_reader.json
python pipeline/verify_jonah1_reader.py # independent re-scan check for reader data
python pipeline/curate_jonah2_extra.py  # curate glosses for Jonah 2 lemmas not yet covered
python pipeline/build_jonah2_reader.py  # build data/jonah2_reader.json
python pipeline/verify_jonah2_reader.py # independent re-scan check for reader data
python pipeline/curate_jonah3_extra.py  # curate glosses for Jonah 3 lemmas not yet covered
python pipeline/build_jonah3_reader.py  # build data/jonah3_reader.json
python pipeline/verify_jonah3_reader.py # independent re-scan check for reader data
python pipeline/curate_jonah4_extra.py  # curate glosses for Jonah 4 lemmas not yet covered
python pipeline/build_jonah4_reader.py  # build data/jonah4_reader.json
python pipeline/verify_jonah4_reader.py # independent re-scan check for reader data
python pipeline/build_lessons_group1.py # build data/lessons_group1.json (Learn tab, prefixes/suffixes)
python pipeline/verify_lessons_group1.py # independent re-derivation check for lesson data
python pipeline/build_lessons_group2.py # build data/lessons_group2.json (Learn tab, construct chains)
python pipeline/verify_lessons_group2.py # independent re-derivation check for lesson data
python pipeline/build_lessons_group3.py # build data/lessons_group3.json (Learn tab, the verb system)
python pipeline/verify_lessons_group3.py # independent re-derivation check for lesson data
python pipeline/build_lessons_group4.py # build data/lessons_group4.json (Learn tab, noun-phrase grammar)
python pipeline/verify_lessons_group4.py # independent re-derivation check for lesson data
python pipeline/build_lessons_group5.py # build data/lessons_group5.json (Learn tab, sentence-level syntax)
python pipeline/verify_lessons_group5.py # independent re-derivation check for lesson data
open app/selftest.html                  # structural checks: deck/parse/reader/lesson invariants
```

Any change to `pipeline/transliterate.py` requires re-running every build script above,
per Hard Rule 1 — transliterations are never hand-typed.

## Current status

Phase history (what was built, verified, and why) lives in `STATUS.md`, not here, so this
file stays short and doesn't go stale mid-phase. `git log` is the real commit-level history.

**Current phase — Phase 5: Tiers 3–5** (weak verbs, derived stems, sustained reading), plus
a new Learn tab (grammar lessons, started because Lane doesn't yet know the rules behind
what the other tabs already have him recognizing by pattern). Grammar tiers not yet scoped.
The Learn tab's original concept-list scope is now fully built (see `STATUS.md`); further
lesson groups would be a new, not-yet-scoped addition. The reader can keep growing (Ruth
next, per the suggested reading order) using the existing pipeline, independent of when
the grammar tiers get scoped.

**Shipped and live:** vocab SRS (Tier 0–1), parsing gym for Qal-strong verbs (Tier 2),
full reader for the book of Jonah, chapters 1–4 (Phase 4, extended through Phase 5), Learn
tab with lesson groups 1–5 (prefixes/suffixes, construct chains, the verb system,
noun-phrase grammar, sentence-level syntax). See `STATUS.md` for what each phase actually
built and how it was verified.

## Working style

- State magnitudes with units. Say plainly when something is fine.
- Compute from the corpus rather than citing published figures. When they conflict, report
  both and say which method produced which. (Qal at 69.0% computed here reproduces
  Pratico & Van Pelt's published figure — a useful pipeline sanity check.)
- Name which inputs came from Lane and which were assumed. Label conditional outputs
  as conditional.
- When Lane pushes back, recheck the arithmetic or the source. Do not reflexively concede
  or reflexively defend.

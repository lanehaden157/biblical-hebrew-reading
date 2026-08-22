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

## Transliteration scheme — locked, never varied

Plain ASCII, chosen to survive copy-paste and phone keyboards:

```
' b g d h w z kh t y k l m n s ` p ts q r sh s t
```

`'` = alef, `` ` `` = ayin. Two distinct consonants, both silent-looking in English.
Greek, if it ever appears, is always transliterated with a gloss — never bare Greek script.

Implementation: `pipeline/transliterate.py`. Its docstring is the authority on the edge
cases the scheme above doesn't state — shva na/nach rules, matres lectionis absorption,
and the deliberate omissions (dagesh forte gemination, qamats gadol vs. qatan). Those are
decided; read them there rather than re-deriving or re-deciding them.

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

**Done.** Tier 0 prototype confirmed niqqud renders correctly on device (disposable, not in
this repo). Pipeline builds `data/top600.json` from OSHB. All 600 lemmas curated across six
gloss batches, reviewed, verified. Transliteration generator complete and verified against
all 600 forms. `data/vocab_deck_600.json` built. Repo live on GitHub; Pages not yet enabled.

**In progress.** Vocab SRS app — the first real `/app/` code. Locked UI decisions:
three-stage card reveal (Hebrew → transliteration → gloss, so a failure identifies whether
decoding or meaning broke); three grade buttons (Again / Good / Easy — `Hard` dropped as the
button people grade inconsistently); bottom tab bar with `Parse` and `Read` stubbed for later
tiers; light and dark themes following the system setting with a persisted manual override;
optional haptics and sound, both defaulting off, behind one `feedback.js` shim.

**Next.** Log actual time-per-session so pacing estimates can be corrected against real data
rather than assumed. Then Phase 3: parsing gym (Qal strong). Phase 4: reader, Jonah 1.
Phase 5: Tiers 3–5.

## Working style

- State magnitudes with units. Say plainly when something is fine.
- Compute from the corpus rather than citing published figures. When they conflict, report
  both and say which method produced which. (Qal at 69.0% computed here reproduces
  Pratico & Van Pelt's published figure — a useful pipeline sanity check.)
- Name which inputs came from Lane and which were assumed. Label conditional outputs
  as conditional.
- When Lane pushes back, recheck the arithmetic or the source. Do not reflexively concede
  or reflexively defend.

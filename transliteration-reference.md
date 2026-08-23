# Transliteration reference — Hebrew rules verified for this project

Purpose: ground truth for editing `pipeline/transliterate.py`. Scope matches the project's
own goal — recognition-level reading of connected narrative (Jonah, Ruth, Genesis, Exodus
3/14) plus the ~600-word vocab deck — not a comprehensive academic phonology of Biblical
Hebrew. Rules that don't affect pronunciation at this level (regional/historical variants,
disputed phonetic reconstructions, poetry-specific cantillation effects) are deliberately
left out.

Each rule below states: what it is, why it's mechanically detectable from the OSHB text
(or why it isn't), a verified example, and a priority note. Sources: the OSHB morphology
spec (openscriptures/morphhb — CC BY 4.0), Unicode's Hebrew block documentation, and
standard reference grammars (cross-checked, not just one blog post per rule).

---

## Already correct — no action needed

Restated here only so Claude Code doesn't waste effort re-deriving these; they're already
implemented and documented in CLAUDE.md:

- **Bet/kaf/pe spirantization** (dagesh-sensitive b/v, k/kh, p/f).
- **Furtive patach** (vowel-then-consonant order on word-final guttural).
- **Alef/ayin as `'` / `` ` ``** — both correctly silent-looking in English transliteration.
- **Matres lectionis absorption** — per the existing docstring authority note; don't
  re-derive, read the docstring first.

---

## Gaps to fix, in priority order (by how often they'd actually come up in the 600-word deck + narrative reading)

### 1. Final He: mappiq vs. silent — HIGH PRIORITY

**Rule:** A final ה is normally **silent** — it's a mater lectionis marking a preceding
vowel, not a consonant. It's audible /h/ **only** when it carries a **mappiq**, a dot
inside the letter.

**Why it's mechanically detectable:** Mappiq uses the *identical* Unicode codepoint as
dagesh — U+05BC (HEBREW POINT DAGESH OR MAPIQ) — but he is not one of the BGDKPT letters,
so it never legitimately carries a dagesh lene/forte for the spirantization rule already
implemented. That means: **any U+05BC on a word-final ה is unambiguously mappiq**, not
dagesh. Fully rule-based, no ambiguity, no context needed beyond "is this letter he, is it
word-final, does it carry U+05BC."

**Examples:**
- מַלְכָּה (queen) — final he, no mappiq → **"malka"**, not "malkah."
- מַלְכָּהּ (her king/queen — with 3fs possessive suffix) — final he **with** mappiq →
  **"malkah"**, audible h.

**Why this matters more than qamats gadol/qatan:** it governs the pronunciation of a large
fraction of feminine singular absolute nouns — almost certainly the single most common
transliteration error currently possible in the 600-word deck, since final-ה feminine nouns
are extremely frequent and mappiq is comparatively rare (mostly 3rd-fem-sing possessive
suffixes). Check this before anything else below.

**Design note, not a factual correction:** popular transliteration convention (including
common renderings of "Torah," "Shabbat" in some spellings) sometimes keeps a final "-ah"
purely as an orthographic convention marking "this word ends in heh, not aleph or nothing" —
not a phonetic claim. Since this project's stated standard is "match how it's actually
pronounced" (the same rationale used for the furtive-patach fix), the silent case should
render as plain "-a," with the Hebrew shown alongside (hard rule 4) disambiguating spelling
for anyone who needs it.

### 2. Shin dot vs. sin dot — HIGH PRIORITY, TRIVIAL FIX

**Rule:** ש with a dot upper-**right** = shin, /ʃ/, "sh." ש with a dot upper-**left** =
sin, /s/, "s." These are two distinct, unambiguous Unicode combining marks: **U+05C1**
(HEBREW POINT SHIN DOT) and **U+05C2** (HEBREW POINT SIN DOT).

**Example:** שָׂם (sam, "he placed") vs. שָׁם (sham, "there") — same consonant skeleton,
different dot, different word, different meaning.

**Detection:** purely mechanical — check which of the two codepoints (if either) attaches
to a given ש. If neither is present (undotted, ambiguous without full pointing), don't
guess; flag it, since context alone can't resolve it and OSHB pointed text should have one
of the two dots on essentially every ש that matters for this project.

This is a near-zero-cost check relative to its impact — worth confirming `transliterate.py`
treats ש as variable output rather than hardcoded to "sh."

### 3. Hataf (reduced) vowels under gutturals — LOW RISK, WORTH AN EXPLICIT TEST

**Rule:** the three "hataf" (composite/reduced) vowels appear almost exclusively under
gutturals (א ה ח ע), which resist a fully colorless/silent shva. They render as short
versions of their full-vowel counterpart, not as silence:
- hataf patach → short **"a"**
- hataf segol → short **"e"**
- hataf qamats → short **"o"**

**Example:** אֱלֹהִים (Elohim) — first vowel is hataf segol → "e," not silent.

Uncontroversial, standard rule, no scholarly dispute. Risk is purely implementation:
these three symbols are visually close to plain shva and could be caught by the same
lookup branch by mistake. Worth one explicit test case per hataf vowel.

### 4. Shva na vs. shva nach (vocal vs. silent shva) — MODERATE, needs a small state machine

Already flagged as a gap in our prior conversation; restating with the actual decision
rules so it's actionable rather than "it's complicated":

Silent (nach) is the default. Shva is **vocal** (na) when:
- it's the very **first** vowel-point in the word,
- it follows **another vocal shva** (two shvas in sequence mid-word: first is silent,
  second is vocal — not both silent, not both vocal),
- it sits under a consonant carrying a **strong/forte dagesh** (gemination needs a
  transitional vowel before the doubled consonant can be released), or
- in a small set of grammatical categories (e.g., certain verb-form environments after a
  long vowel in an open syllable).

**Example:** שְׁמוֹ (shemo, "his name") — shva under shin is vocal because it's word-initial
→ "she-," not a silent consonant cluster.

Because several of these conditions require looking at *neighboring* vowel points, not
just the current letter, this needs the same kind of fix as qamats gadol/qatan: a small
pass over the whole word's point sequence, not a per-character regex. Lower priority than
items 1–2 above, since under-marking a syllable costs a syllable count, not a wrong word.

### 5. Dagesh forte (gemination) vs. dagesh lene vs. mappiq — same codepoint, different job, worth one shared helper

All three of the following use the **identical** Unicode point U+05BC:
- **dagesh lene** (on a BGDKPT letter with no preceding vowel) → triggers the already-fixed
  b/v, k/kh, p/f rule,
- **dagesh forte** (on any letter after a full vowel) → marks gemination/doubling,
- **mappiq** (only ever on a word-final ה) → makes it consonantal (item 1 above).

Your CLAUDE.md already documents dagesh forte as a deliberate, reasonable omission — English
doesn't mark consonant length, so under-doubling won't mislead an English-speaking reader.
No change recommended there. But because all three functions share one codepoint and are
disambiguated purely by *position/context*, recommend implementing (or verifying) **one
shared helper** that classifies a given U+05BC occurrence into one of the three categories,
rather than three separate ad hoc checks scattered through the code — that's exactly the
kind of duplication where a future edit to one rule silently breaks another.

### 6. Prefix vowel-sandhi (vav-conjunctive, be-/ke-/le-, definite article) — VERIFICATION ITEM, likely not a live bug

**Confirmed rule:** the conjunction vav (default shva, "ve-") shifts to shuruq ("u-")
before the labial consonants bet/mem/vav/pe (the "BuMP" rule) and before any consonant that
itself starts with a vocal shva (Hebrew disallows two shvas in a row at a word boundary).
The inseparable prepositions be-/ke-/le- follow the same shift before shva. The definite
article's heh triggers a dagesh forte (gemination) in the following consonant, except
before gutturals/resh, which take compensatory vowel lengthening instead.

**Why this is a verification item, not a new rule to write:** all of this is already
directly encoded in the Masoretic pointing — a shuruq in the text is a shuruq regardless
of *why* the Masoretes put it there. If `transliterate.py` reads the literal vowel point
under each letter (character-driven), these cases are already handled correctly with zero
new code. The risk is the same class of bug found in the wayyiqtol/yishbot case: a script
asserting a category ("vav-conjunctive is always 've-'") instead of reading what's actually
written. Worth one explicit test case to confirm this isn't happening:

**Example:** וּבַיּוֹם (u-vayom, "and on the day") — vav + bet, BuMP rule → should render
"u-," not default to "ve-."

---

## Known, unfixed limitation (recap — no new information here)

**Qamats gadol vs. qamats qatan** remains an open gap, per CLAUDE.md's existing analysis:
the most common real trigger (maqqef removing a word's independent stress) lives in OSHB
as a separate `<seg type="x-maqqef">` element between `<w>` tags, invisible to
`transliterate()` given only a word string. Fixing this requires the *calling* pipeline
script to detect maqqef in the verse XML and pass stress context in — out of scope for a
`transliterate.py`-only fix, same conclusion as before.

---

## Suggested regression/golden-test set

For each rule above, at minimum one verified form → correct transliteration pair, to wire
into `verify_*.py` as a permanent check (not just a one-time audit):

| Form | Correct output | Rule tested |
|---|---|---|
| מַלְכָּה | malka | final he silent (no mappiq) |
| מַלְכָּהּ | malkah | final he audible (mappiq) |
| שָׂם | sam | sin dot |
| שָׁם | sham | shin dot |
| אֱלֹהִים | elohim | hataf segol |
| שְׁמוֹ | shemo | shva na (word-initial) |
| וּבַיּוֹם | u-vayom | vav-conjunctive BuMP shuruq |
| רוּחַ | ruakh | furtive patach (already fixed — regression check) |
| יִשְׁבֹּת | yishbot | dagesh lene on bet (already fixed — regression check) |
| שָׁבַת | shavat | no dagesh on bet (already fixed — regression check) |

Expand per-rule as needed once the pipeline scripts are available to check against, but
this is enough to catch the highest-impact regressions immediately.

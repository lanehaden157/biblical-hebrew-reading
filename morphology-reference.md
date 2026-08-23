# Morphology reference — Hebrew parsing rules verified for this project

Purpose: ground truth for `pipeline/build_parse_qal.py` and `pipeline/verify_parse_qal.py`,
and for the weak-verb build scripts Phase 5 will eventually need. Scope matches the
project's own boundary: the conjugation types and binyanim already prioritized in
CLAUDE.md's locked decisions (Qal 69.0% > Hiphil > Piel > Niphal > Hitpael; qatal,
wayyiqtol, yiqtol, participle, infinitive construct = 80.8% cumulative coverage), plus
enough weak-root grammar to support Phase 5 without turning into a full comparative-Semitics
grammar. Rarer stems (Pual, Hophal, Polel, etc.) are out of scope here — CLAUDE.md already
marks them recognition-only, never drilled.

Sources: the OSHB morphology spec (openscriptures/morphhb — CC BY 4.0, the literal ground
truth the pipeline parses against) and standard reference grammars, cross-checked across
multiple independent sources rather than taken from a single page.

---

## Part 1: the confirmed cause of the wayyiqtol/yishbot bug

**The OSHB corpus already distinguishes yiqtol from wayyiqtol correctly.** Per the project's
own morphology spec, the verb conjugation-type letter (third segment of a `V` morph code,
after stem) is:

| Code | Conjugation |
|---|---|
| `p` | perfect (qatal) |
| `q` | sequential perfect (weqatal) |
| `i` | imperfect (yiqtol) |
| `w` | sequential imperfect (wayyiqtol) |
| `h` | cohortative |
| `j` | jussive |
| `v` | imperative |
| `r` | participle active |
| `s` | participle passive |
| `a` | infinitive absolute |
| `c` | infinitive construct |

So `Vqi3ms` = Qal imperfect (yiqtol) 3ms, and `Vqw3ms` = Qal sequential imperfect
(wayyiqtol) 3ms — genuinely different codes, not a case where the source data is ambiguous
or defaults to one reading. **The bug is in the pipeline's code, not the corpus.**

**Most likely specific cause, worth checking first:** OSHB morph strings concatenate prefix
morphemes with `/` — e.g. a form with a conjunction prefix is tagged `HC/Vqw3ms`, not just
`Vqw3ms`. Per the spec's own example (`Gen.1.1`, `הַ/שָּׁמַ֖יִם` → `HTd/Ncmpa`), this
concatenation is completely standard, not an edge case. **Any code that reads the
conjugation-type letter by counting a fixed number of characters from the start of the
`morph` string, instead of first splitting on `/` and locating the `V` segment, will misread
the letter on every prefixed verb form** — which would produce exactly the kind of
plausible-looking, silently-wrong output Hard Rule 3 exists to catch. Check
`build_parse_qal.py`'s morph-parsing logic against this specifically: does it split on `/`
before indexing into the verb segment, or does it assume a fixed offset?

**Why `verify_parse_qal.py` didn't catch this:** per CLAUDE.md, it "independently re-derives
every count via its own regex scan and its own copy of the strong-root rule" — same author,
same conceptual model. If both scripts share the same misunderstanding of what
distinguishes yiqtol from wayyiqtol, a second internal implementation won't surface it. This
is why the golden test set at the end of this document matters more than re-running the
existing verification script.

---

## Part 2: verifying the existing strong-root test

CLAUDE.md documents the current strong-root test as: triliteral, no radical in
{alef,he,het,ayin}, first radical not nun, first radical not vav/yod, second radical not
vav/yod or equal to third. Checked against standard weak-root taxonomy (below), this test
is **correctly comprehensive** for the classes it's meant to exclude:

- "no radical in {alef,he,het,ayin}, any position" correctly excludes I/II/III-guttural,
  I-Aleph, III-Aleph, and III-He in one check, since all of those classes are defined by a
  guttural (or aleph specifically) occupying some root position.
- "first radical not nun" correctly excludes I-Nun.
- "first radical not vav/yod" correctly excludes I-Vav/I-Yod.
- "second radical not vav/yod, or equal to third" correctly excludes Hollow (II-Vav/Yod)
  and Geminate (doubled 2nd/3rd radical) in one check.

No gap found in the exclusion logic itself. (שבת, the root behind the יִשְׁבֹּת example,
correctly passes this test — shin-bet-tav has no guttural, no nun-initial, no vav/yod-initial,
and bet ≠ tav — so the root classification wasn't the source of the bug; this reinforces
that the error was in conjugation-type labeling, not root-strength classification.)

---

## Part 3: weak-root taxonomy, for Phase 5

One defining trait + the single most load-bearing inflectional quirk per class — enough to
recognize the class and know what to expect, not a full paradigm chart. Standard grammar
abbreviation (Pe/Ayin/Lamed = 1st/2nd/3rd root letter, from the paradigm word פ-ע-ל) noted
alongside the English name since both appear across grammars/tools.

### I-Guttural (Pe-Guttural)
First root letter is א, ה, ח, or ע (ר sometimes included, behaves similarly).
**Core quirk:** the prefix vowel that would normally be hireq in the Qal imperfect shifts —
often to patach, segol, or occasionally holam/shureq — because gutturals resist the vowel a
strong root's prefix would take. Piel/Pual/Hithpael are largely unaffected (these stems
don't put a vowel-point burden directly on the first radical the same way).

### I-Aleph
Technically a subclass of I-Guttural, but aleph's near-total inability to close a syllable
gives it distinct enough behavior that grammars usually separate it out. A well-known
subset (e.g. אכל, אמר, אבד) shows *quiescent aleph* in the Qal imperfect — the aleph
stops being pronounced as a consonant at all and the preceding vowel lengthens to
compensate (אֹמַר, not the fully regular pattern a strong root would show).

### I-Nun (Pe-Nun)
First root letter is נ. **Core quirk:** when the nun would close a syllable (typically
Qal/Hiphil imperfect and related forms), it **assimilates** into the following consonant,
surfacing as a dagesh forte in that consonant rather than as a written nun. Example: נ-ת-ן
("give") → יִתֵּן (yitten), not the "expected" יִנְתֹּן. A handful of I-Nun roots (e.g.
לקח) inflect *as if* I-Nun even though the historical root doesn't literally begin with
nun — treat these as belonging to the functional class, not the literal-letter class.

### I-Vav / I-Yod (Pe-Vav / Pe-Yod)
First root letter is ו or י. Two distinguishable behavior patterns exist historically, but
in practice most roots that surface as I-Yod in the Qal perfect (their citation form)
originated as I-Vav — this matters for recognizing that ישב-type and ילד-type roots often
pattern together despite the surface letter both showing yod. **Core quirk:** the first
radical frequently drops entirely in the Qal imperfect/imperative/infinitive-construct
(e.g. י-ש-ב "sit/dwell" → יֵשֵׁב is regular-looking, but infinitive construct שֶׁבֶת has no
trace of the yod at all). Niphal sometimes shows the original vav resurfacing where the
Qal shows none.

### Hollow / Biconsonantal (Ayin-Vav / Ayin-Yod)
Middle root letter is ו or י (root traditionally cited as effectively two consonants plus a
long vowel, e.g. קום "stand," שים "put"). **Core quirk:** the middle letter routinely
disappears entirely, replaced by a long vowel carrying the semantic weight of the root
(ק-ו-ם → קָם "he stood," not a form with a written vav in the middle). The derived/intensive
stems (Piel/Pual/Hithpael) compensate by doubling the *third* radical instead of the middle
one, since there's no middle consonant left to double — this is the single most useful fact
for recognizing a hollow root's derived-stem forms.

### Geminate (Ayin-Ayin / Double-Ayin)
Second and third root letters are identical (ס-ב-ב "go around," ע-ז-ז "be strong").
**Core quirk:** in most forms the two identical letters collapse into one, represented by a
dagesh forte marking the doubling rather than two written letters (סָבַב is the "full"
citation form, but many inflected forms show the doubled letter contracted with a
connecting cholem-vav, e.g. יָסֹב). Distinguish from Hollow carefully — both can look
biconsonantal on the surface, but geminate roots double the *last* letter where hollow roots
lose the *middle* one.

### III-He (Lamed-He)
Root traditionally cited with final ה (e.g. ב-נ-ה "build," ר-א-ה "see") — but this is
itself a mater-lectionis artifact of a historically final vav or yod, not a "real" third
guttural. **Core quirk, and the single most important one for the reader/parsing-gym build:**
the final ה **apocopates (drops)** in the jussive and in the wayyiqtol, revealing the
underlying yod (or occasionally vav): ב-נ-ה → וַיִּבֶן (wayyiven, "and he built"), not a
form ending in ה. Any regex that tries to match a III-He root's letters directly against
a wayyiqtol/jussive surface form **will fail to match** unless it specifically accounts for
this drop — this is the most likely single source of silent mismatches once Phase 5 starts
covering III-He verbs, the same failure mode (rule doesn't account for what the form
actually looks like) as the wayyiqtol bug documented in Part 1.

### III-Aleph
Technically a III-Guttural subclass, but (like I-Aleph) distinct enough to separate: final
aleph is consistently quiescent (silent) when it would close a syllable, and the preceding
vowel is usually a tsere rather than the pattern a true III-guttural (he/het/ayin) would
show — e.g. מ-צ-א "find" → Qal perfect מָצָא looks regular, but the final aleph is
genuinely silent, distinguishing its pattern from a true III-guttural like ש-ל-ח.

---

## Part 4: suppletive and doubly-weak verbs, ranked by frequency

The classes in Part 3 predict the *systematic* irregularities. This section covers verbs
that either combine two weak classes at once, or genuinely fall outside what the class
rules alone would predict. Ordered by how often they'd actually turn up in a 600-word
deck — not exhaustive of every possible doubly-weak root, just the ones common enough to
matter. Verified against multiple independent sources, not a single page, given how easy
it is to find confidently-wrong grammar blogs on this topic.

### 1. הָיָה (haya, "to be") — the single most frequent verb in the Bible
Formally III-He, but with two extra quirks beyond the standard class pattern worth
knowing explicitly: the final root letter surfaces as **yod** in most inflected forms
(not the ה itself), is **dropped entirely** in 3rd-common-plural, and becomes **tav** in
3rd-feminine-singular perfect: הָיְתָה (haytah), not a form ending in ה or י. Any III-He
handling that assumes "the class quirk is just apocopation" will still get this one wrong.

### 2. אָמַר (amar, "to say") — the single most frequent Qal-attested verb by raw count
I-Aleph, already covered by the class rule in Part 3 — flagged here only because its sheer
frequency (thousands of occurrences, mostly as the standard narrative "and he said") makes
it the highest-value single form to get right. Qal imperfect יֹאמַר, aleph quiescent,
compensatory cholam.

### 3. בּוֹא (bo, "to come") — 4th most frequent verb in the Bible
**Doubly weak: Hollow (middle vav) + III-Aleph combined.** The middle vav disappears
entirely and the final aleph quiesces in the same form: Qal perfect בָּא (ba) for both
masculine and — distinctively — feminine singular (they're identical, unlike a regular
verb's perfect paradigm). Qal imperfect יָבוֹא (yavo). Treat this as a genuinely irregular
paradigm to check directly, not something to derive by applying the Hollow rule and the
III-Aleph rule independently and hoping they compose cleanly.

### 4. נָתַן (natan, "to give") — roughly 2,000 occurrences
**Doubly nun-weak: both the first *and* last root letters are nun**, and both can drop.
Infinitive construct is לָתֵת (latet) — both nuns gone, only the middle tav survives from
the visible root. With a 1st-person suffix the final nun also assimilates: נָתַתִּי
(natati, "I gave"), not a form with a doubled nun before the suffix. Qal imperfect יִתֵּן
(yitten) shows the expected I-Nun assimilation from Part 3, but the infinitive/suffixed
forms need this extra, root-specific rule layered on top.

### 5. הָלַךְ (halakh, "to walk/go") — very high frequency
**Genuinely suppletive, not derivable from any class rule.** By its root letters it should
be I-Guttural (initial he). It isn't — the Qal imperfect is יֵלֵךְ (yelekh), inflecting as
if the root were I-Yod instead, and the Hiphil הוֹלִיךְ (holikh) likewise patterns as if
the root were Y-L-K. This is the example flagged earlier as the clearest case where
deriving behavior from "first radical → apply the matching class rule" will silently
produce the wrong form. Needs a direct lexical override, not a smarter rule.

### 6. יָצָא (yatsa, "to go out") — roughly 1,067 occurrences
**Doubly weak: I-Yod + III-Aleph.** Initial yod disappears in the infinitive (לָצֵאת,
latzet) and imperfect (יֵצֵא, yetze); final aleph behaves as a guttural, affecting the
adjacent vowel. Qal perfect יָצָא looks deceptively regular; the irregularity shows up in
the derived forms.

### 7. לָקַח (laqach, "to take") — high frequency
**Behaves as I-Nun despite having no historical nun.** Qal imperfect יִקַּח (yiqqach) shows
the same dagesh-forte-in-second-radical pattern that a true I-Nun root would produce from
nun assimilation, even though the root is ל-ק-ח. Infinitive construct לָקַחַת is otherwise
regular (final het is guttural, I-Guttural-style vowel effects only). Treat as a named
exception to the I-Nun class trigger, not a root-letter miscount.

### 8. נָשָׂא (nasa, "to lift/carry") — roughly 655 occurrences
**Doubly weak: I-Nun + III-Aleph.** Qal imperfect יִשָּׂא (yisa) — nun assimilated (dagesh
in sin) and final aleph quiesced, in the same form. Infinitive construct לָשֵׂאת (laset).

### Lower priority, mentioned for completeness
עָשָׂה ("to do/make," very high frequency) and רָאָה ("to see," high frequency) are both
regular III-He verbs — no additional irregularity beyond the Part 3 class rule, despite
their frequency. Included here only so they're not mistakenly flagged as needing special
handling; they don't.

---

## Suggested golden test set

For wiring into `verify_parse_qal.py` as a permanent regression check, not a one-time audit
— verb forms with known-correct parse labels, covering the conjugation-type confusion found
plus one representative of each weak class above (needed once Phase 5 begins, harmless to
add now):

| Form | Root | Correct parse | Class tested |
|---|---|---|---|
| יִשְׁבֹּת | שבת | Qal imperfect (yiqtol) 3ms | strong root — regression check for the bug found |
| וַיִּשְׁבֹּת | שבת | Qal sequential imperfect (wayyiqtol) 3ms | strong root, contrastive pair |
| קָטַל | קטל | Qal perfect 3ms | strong root, standard paradigm citation |
| יֹאמַר | אמר | Qal imperfect 3ms | I-Aleph, quiescent aleph |
| יִתֵּן | נתן | Qal imperfect 3ms | I-Nun assimilation |
| שֶׁבֶת | ישב | Qal infinitive construct | I-Yod, first radical drops |
| קָם | קום | Qal perfect 3ms | Hollow, middle letter lost |
| סָבַב | סבב | Qal perfect 3ms | Geminate |
| וַיִּבֶן | בנה | Qal sequential imperfect (wayyiqtol) 3ms | III-He apocopation |
| מָצָא | מצא | Qal perfect 3ms | III-Aleph, quiescent final aleph |
| הָיְתָה | היה | Qal perfect 3fs | III-He irregular — tav, not he or apocopation |
| בָּא | בוא | Qal perfect 3ms/3fs (identical) | Hollow + III-Aleph combined |
| לָתֵת | נתן | Qal infinitive construct | doubly nun-weak, both radicals drop |
| יֵלֵךְ | הלך | Qal imperfect 3ms | suppletive — I-Guttural root, I-Yod behavior |
| יִקַּח | לקח | Qal imperfect 3ms | behaves as I-Nun, no historical nun |
| יִשָּׂא | נשא | Qal imperfect 3ms | I-Nun + III-Aleph combined |

Expand per-class once the actual weak-verb build script exists and its specific regex logic
can be checked against these, the same way the transliteration golden set was scoped to what
`transliterate.py` actually does rather than abstract completeness.

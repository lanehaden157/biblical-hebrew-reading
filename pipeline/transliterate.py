"""
Deterministic Hebrew -> ASCII transliteration per the locked scheme in
CLAUDE.md:

    ' b g d h w z kh t y k l m n s ` p ts q r sh s t

(alef=', ayin=`; tet/tav both "t"; samekh/sin both "s"; het="kh"; kaf/bet/pe
are never distinguished for dagesh -- the scheme has no separate fricative
letters, so kaf/bet/pe are always k/b/p.)

Input must be OSHB-sourced pointed Hebrew (rule 1: never hand-type pointed
Hebrew). Cantillation (U+0591-U+05AF) is skipped defensively if present,
though callers are expected to have already stripped it (rule 2 permits
stripping, never normalizing).

Shva na/nach (vocal vs. silent shva): implemented using the standard
introductory-grammar rules (e.g. Pratico & Van Pelt's "rules of shewa"),
which are reliably rule-based without needing stress/etymology data:
  1. Word-final shva is silent.
  2. Word-initial shva is vocal.
  3. Of two consecutive shvas, the first is silent and the second is vocal.
  4. Otherwise (the default case -- a shva closing a syllable after a short
     vowel) it is silent.
Rule 3 skips over any matres-lectionis vav/yod that got absorbed into a
neighboring vowel, since those aren't real syllable positions.
Deliberately NOT implemented (see rationale below): shva after a
dagesh-forte letter is always vocal in full grammar, and shva after a
vowel that's "long" only because of accent placement can go either way --
both require accent/stress data this module doesn't have. Given these are
comparatively rare and this module already doesn't track dagesh forte at
all (see below), guessing at them would risk exactly the "plausible but
wrong" failure mode CLAUDE.md warns about. They render via the rule-4
default (silent), which is right far more often than not.

Known simplifications (deliberately out of scope, not oversights):
  - qamats (U+05B8) is always rendered "a" (qamats gadol). Qamats qatan
    (same glyph, "o" sound) requires syllable-stress analysis; not
    handled. The distinct qamats-qatan codepoint U+05C7, when present, IS
    rendered "o" (it's unambiguous -- OSHB uses it exactly for this case).
  - dagesh forte (gemination -- doubled consonant) is not detected; a
    geminated consonant is rendered once, not twice. Doubling multi-
    character digraphs (sh/kh/ts) would look strange in a scheme meant for
    phone-friendly recognition reading, not phonetic precision, so this
    is a deliberate scope decision, not just an unhandled case.
  - matres lectionis ARE handled for the three common cases: cholam-vav
    (o), shuruk (u), hiriq-yod (i) -- the vav/yod is absorbed into the
    vowel rather than also emitted as a consonant.
  - final heh is always transliterated "h", pointed or not (matches common
    convention, e.g. "torah" not "tora"; mappiq -- a dagesh marking a
    final heh as consonantal rather than a silent vowel-length marker --
    doesn't change this, since heh is "h" either way).
"""

VAV, YOD = "ו", "י"
SHIN_BASE = "ש"
SIN_DOT = "ׂ"
SHIN_DOT = "ׁ"
SHVA = "ְ"
DAGESH = "ּ"
HOLAM = "ֹ"
HOLAM_HASER = "ֺ"

CONSONANTS = {
    "א": "'",   # alef
    "ב": "b",   # bet
    "ג": "g",   # gimel
    "ד": "d",   # dalet
    "ה": "h",   # he
    "ו": "w",   # vav
    "ז": "z",   # zayin
    "ח": "kh",  # het
    "ט": "t",   # tet
    "י": "y",   # yod
    "ך": "k",   # final kaf
    "כ": "k",   # kaf
    "ל": "l",   # lamed
    "ם": "m",   # final mem
    "מ": "m",   # mem
    "ן": "n",   # final nun
    "נ": "n",   # nun
    "ס": "s",   # samekh
    "ע": "`",   # ayin
    "ף": "p",   # final pe
    "פ": "p",   # pe
    "ץ": "ts",  # final tsadi
    "צ": "ts",  # tsadi
    "ק": "q",   # qof
    "ר": "r",   # resh
    "ש": "sh",  # shin (default; overridden by sin dot check)
    "ת": "t",   # tav
}

VOWELS = {
    SHVA: "e",  # shva -- special-cased via na/nach rules below
    "ֱ": "e",   # hataf segol
    "ֲ": "a",   # hataf patah
    "ֳ": "o",   # hataf qamats
    "ִ": "i",   # hiriq
    "ֵ": "e",   # tsere
    "ֶ": "e",   # segol
    "ַ": "a",   # patah
    "ָ": "a",   # qamats (gadol)
    "ֹ": "o",   # holam
    "ֺ": "o",   # holam haser (for vav)
    "ֻ": "u",   # qubuts
    "ׇ": "o",   # qamats qatan
}

CANTILLATION_RANGE = range(0x0591, 0x05B0)  # defensive skip if not pre-stripped


def _clusters(word):
    """Group each base consonant with the combining marks that follow it."""
    clusters = []
    for ch in word:
        code = ord(ch)
        if code in CANTILLATION_RANGE:
            continue
        if ch in CONSONANTS:
            clusters.append([ch, []])
        elif clusters:
            clusters[-1][1].append(ch)
    return clusters


def _own_vowel_mark(marks):
    """The raw vowel-point character on this cluster, or None."""
    for m in marks:
        if m in VOWELS:
            return m
    return None


def _consonant_text(base, marks):
    if base == SHIN_BASE:
        return "s" if SIN_DOT in marks else "sh"
    return CONSONANTS[base]


def transliterate(word):
    cl = _clusters(word)
    n = len(cl)
    own_vowel = [_own_vowel_mark(marks) for _, marks in cl]

    # Pass 1: matres lectionis -- absorb a following vav/yod that's purely
    # a vowel letter (no vowel of its own) into the preceding vowel-less
    # consonant, rather than emitting it as a separate consonant sound.
    absorbed = [False] * n
    absorbed_vowel = [None] * n
    for i in range(n):
        base, marks = cl[i]
        if own_vowel[i] is None and i + 1 < n:
            nbase, nmarks = cl[i + 1]
            n_vowel_marks = [m for m in nmarks if m in VOWELS]
            if nbase == VAV and n_vowel_marks == [HOLAM]:
                absorbed_vowel[i], absorbed[i + 1] = "o", True
            elif nbase == VAV and n_vowel_marks == [HOLAM_HASER]:
                absorbed_vowel[i], absorbed[i + 1] = "o", True
            elif nbase == VAV and DAGESH in nmarks and not n_vowel_marks:
                absorbed_vowel[i], absorbed[i + 1] = "u", True
        if own_vowel[i] == "ִ" and i + 1 < n:  # hiriq
            nbase, nmarks = cl[i + 1]
            if nbase == YOD and not nmarks:
                absorbed[i + 1] = True

    real_indices = [i for i in range(n) if not absorbed[i]]

    def prev_real(pos):
        return real_indices[pos - 1] if pos > 0 else None

    def next_real(pos):
        return real_indices[pos + 1] if pos + 1 < len(real_indices) else None

    # Pass 2: resolve each real cluster's vowel, applying shva na/nach rules.
    out = []
    for pos, i in enumerate(real_indices):
        base, marks = cl[i]
        cons = _consonant_text(base, marks)

        if own_vowel[i] == SHVA:
            is_word_initial = pos == 0
            is_word_final = pos == len(real_indices) - 1
            pj, nj = prev_real(pos), next_real(pos)
            prev_is_shva = pj is not None and own_vowel[pj] == SHVA
            next_is_shva = nj is not None and own_vowel[nj] == SHVA
            if is_word_initial:
                # A lone consonant+shva (bound prefixes ל/ב/כ shown alone)
                # can only be a syllable onset, never a closed syllable, so
                # word-initial wins even when it coincides with word-final.
                vowel = "e"
            elif is_word_final:
                vowel = ""
            elif prev_is_shva:
                vowel = "e"   # second of a consecutive pair: vocal
            elif next_is_shva:
                vowel = ""    # first of a consecutive pair: silent
            else:
                vowel = ""    # default case: silent
        elif own_vowel[i] is not None:
            vowel = VOWELS[own_vowel[i]]
        elif absorbed_vowel[i] is not None:
            vowel = absorbed_vowel[i]
        else:
            vowel = ""

        out.append(cons + vowel)

    return "".join(out)

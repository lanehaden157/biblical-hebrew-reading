"""
Transliterator: pointed corpus surface -> Lane's scheme. One function, `translit()`.

Scheme (SPEC Q1 + 2026-10-07 answers)
  consonants  alef ' (dropped word-initially and when quiescent), b/v g d h v z ch t y k/kh l m n
              s ` p/f ts q r sh s t.  b/v k/kh p/f by dagesh; dagesh forte written double.
  vowels      a e i o u; vocal shva e; hatef a/e/o; qamats qatan o. Matres are absorbed.
  final he    written h (silent or mappiq)
  stress      acute on the stressed vowel only when it is not the last syllable (melekh -> m\u00e9lekh)
  divine name parts with lemma 3068/3069 -> "YHWH"

Pipeline per word: parse letters+marks -> letter roles (maters, quiescent alef, holam male,
shureq, furtive patach) -> dagesh lene/forte -> shva vocal/silent -> syllables -> stress from
accents -> qamats qatan (closed unstressed syllable without meteg). Hebrew is never normalised.

    translit_token(tok, stress_table) -> {"text", "syllables", "stress", "stress_src"}
    stress_table = build_stress_table(tokens)   # once per run; covers positional-only accents
"""

# --- codepoints (escapes, so no Hebrew letters are typed in source) --------------------------
ALEF, BET, GIMEL, DALET, HE, VAV = "\u05d0", "\u05d1", "\u05d2", "\u05d3", "\u05d4", "\u05d5"
ZAYIN, HET, TET, YOD, KAF, LAMED = "\u05d6", "\u05d7", "\u05d8", "\u05d9", "\u05db", "\u05dc"
MEM, NUN, SAMEKH, AYIN, PE, TSADI = "\u05de", "\u05e0", "\u05e1", "\u05e2", "\u05e4", "\u05e6"
QOF, RESH, SHIN, TAV = "\u05e7", "\u05e8", "\u05e9", "\u05ea"
FINALS = {"\u05da": KAF, "\u05dd": MEM, "\u05df": NUN, "\u05e3": PE, "\u05e5": TSADI}

SHVA, HSEGOL, HPATACH, HQAMATS = "\u05b0", "\u05b1", "\u05b2", "\u05b3"
HIRIQ, TSERE, SEGOL, PATACH, QAMATS = "\u05b4", "\u05b5", "\u05b6", "\u05b7", "\u05b8"
HOLAM, HOLAM_V, QUBUTS, QQATAN = "\u05b9", "\u05ba", "\u05bb", "\u05c7"
DAGESH, METEG, RAFE, SHIN_DOT, SIN_DOT = "\u05bc", "\u05bd", "\u05bf", "\u05c1", "\u05c2"
SHUREQ = "U"  # pseudo-vowel for vav+dagesh used as a vowel letter

VOWEL = {HIRIQ: "i", TSERE: "e", SEGOL: "e", PATACH: "a", QAMATS: "a", HOLAM: "o", HOLAM_V: "o",
         QUBUTS: "u", QQATAN: "o", SHUREQ: "u", HSEGOL: "e", HPATACH: "a", HQAMATS: "o"}
HATEF = {HSEGOL, HPATACH, HQAMATS}
LONG = {TSERE, HOLAM, HOLAM_V, QAMATS, SHUREQ}  # hiriq/tsere + yod mater also count (see _long)

CONS = {ALEF: "'", BET: "b", GIMEL: "g", DALET: "d", HE: "h", VAV: "v", ZAYIN: "z", HET: "ch",
        TET: "t", YOD: "y", KAF: "k", LAMED: "l", MEM: "m", NUN: "n", SAMEKH: "s", AYIN: "`",
        PE: "p", TSADI: "ts", QOF: "q", RESH: "r", TAV: "t"}
SPIRANT = {BET: "v", KAF: "kh", PE: "f"}
BGDKPT = {BET, GIMEL, DALET, KAF, PE, TAV}
GUTTURAL_FURTIVE = {HET, AYIN, HE}

# accents U+0591-U+05AF; positional ones sit on the first/last letter, not the stressed syllable
POSTPOSITIVE = {"\u0592", "\u0599", "\u05a9", "\u05ae"}   # segolta, pashta, telisha qetana, zarqa
PREPOSITIVE = {"\u059a", "\u05a0"}                         # yetiv, telisha gedola
POSITIONAL = POSTPOSITIVE | PREPOSITIVE
QATAN_OPEN = {"6944", "591", "8328"}           # qodesh, oniyyah, shoresh (lexical qatan)
PASHTA, QADMA, ZARQA, ZINOR = "\u0599", "\u05a8", "\u0598", "\u05ae"
ACUTE = {"a": "\u00e1", "e": "\u00e9", "i": "\u00ed", "o": "\u00f3", "u": "\u00fa"}


class Letter:
    __slots__ = ("base", "dagesh", "shin", "vowels", "meteg", "accents", "silent", "cons",
                 "double", "nuc", "reduced", "furtive", "syl", "host", "disp", "part")

    def __init__(self, ch):
        self.base = FINALS.get(ch, ch)
        self.dagesh = False
        self.shin = None
        self.vowels = []
        self.meteg = False
        self.accents = []
        self.silent = False   # no sound and not displayed
        self.disp = None      # displayed but silent (final he)
        self.cons = ""
        self.double = False
        self.nuc = None       # vowel codepoint carried after role assignment (or SHVA)
        self.reduced = False
        self.furtive = False
        self.syl = None
        self.host = None      # index of the letter whose syllable a silent letter joins
        self.part = 0         # morpheme index (surface may carry "/" separators)


def _parse(word):
    out = []
    part = 0
    for ch in word:
        o = ord(ch)
        if ch == "/":
            part += 1
        elif 0x05D0 <= o <= 0x05EA:
            out.append(Letter(ch))
            out[-1].part = part
        elif not out:
            continue
        elif ch == DAGESH:
            out[-1].dagesh = True
        elif ch == SHIN_DOT:
            out[-1].shin = "sh"
        elif ch == SIN_DOT:
            out[-1].shin = "s"
        elif ch == METEG:
            out[-1].meteg = True
        elif ch in VOWEL or ch == SHVA:
            out[-1].vowels.append(ch)
        elif 0x0591 <= o <= 0x05AF:
            out[-1].accents.append(ch)
        # rafe, upper dot, CGJ, punctuation: ignored
    return out


def _roles(L):
    n = len(L)
    for i, x in enumerate(L):
        prev = L[i - 1] if i else None
        bare_prev = prev is not None and not prev.vowels and not prev.silent
        nxt = L[i + 1] if i + 1 < n else None
        if x.base == VAV and not x.vowels and x.dagesh and nxt is not None and                 nxt.base == VAV and nxt.dagesh and not nxt.vowels and not bare_prev:
            x.dagesh = False                                  # consonant vav before shureq
            continue
        if x.base == VAV and not x.vowels and x.dagesh:
            if bare_prev:
                prev.vowels.append(SHUREQ); x.silent = True; x.host = i - 1
            else:
                x.vowels.append(SHUREQ); x.cons = ""; x.dagesh = False; x.base = None
        elif x.base == VAV and x.vowels == [HOLAM] and not x.dagesh and bare_prev:
            prev.vowels.append(HOLAM); x.vowels = []; x.silent = True; x.host = i - 1
        elif x.base == ALEF and x.vowels == [HOLAM] and bare_prev:
            prev.vowels.append(HOLAM); x.vowels = []; x.silent = True; x.host = i - 1
        if x.silent or x.base is None:
            continue
        pv = prev.vowels[-1] if prev and prev.vowels else None
        last = i == n - 1
        if x.base == YOD and not x.vowels and not x.dagesh and pv in (HIRIQ, TSERE, SEGOL):
            x.silent = True
        elif (x.base == YOD and not x.vowels and not x.dagesh and pv == QAMATS and i == n - 2
              and L[i + 1].base == VAV and not L[i + 1].vowels and not L[i + 1].dagesh):
            x.silent = True                                   # -av suffix
        elif x.base == VAV and not x.vowels and not x.dagesh and pv == HIRIQ:
            x.silent = True                                   # qere perpetuum hi (Pentateuch)
        elif x.base == ALEF and not x.vowels and not _vowel_vav(nxt):
            x.silent = True                                   # quiescent alef
        elif x.base == HE and not x.vowels and not x.dagesh and not _vowel_vav(nxt):
            x.disp = "h"                       # silent he, written h (final; medial in names)
        elif x.base == SHIN and x.shin is None:
            x.silent = True                                   # undotted shin (Issachar)
        if x.silent and x.host is None:
            x.host = i - 1
    # furtive patach
    last = L[-1] if L else None
    if last and last.base in GUTTURAL_FURTIVE and last.vowels == [PATACH] and n > 1 and \
            (last.base != HE or last.dagesh):
        last.furtive = True


def _vowel_vav(x):
    """Vav that will act as shureq or holam male."""
    return x is not None and x.base == VAV and (
        (x.dagesh and not x.vowels) or (not x.dagesh and x.vowels == [HOLAM]))


def _consonants(L):
    seen_nucleus = False
    for i, x in enumerate(L):
        if x.base is None:
            seen_nucleus = True
            continue
        if x.silent or x.disp:
            continue
        prev = _prev_sounding(L, i)
        prev_vowel = prev is not None and (L[prev].base is None or any(
            v != SHVA for v in L[prev].vowels)) or (i and L[i - 1].silent)
        if x.base == SHIN:
            c = x.shin
        else:
            c = CONS[x.base]
        if x.base in BGDKPT:
            if not x.dagesh and x.base in SPIRANT:
                c = SPIRANT[x.base]
            elif x.dagesh and seen_nucleus and prev_vowel:
                x.double = True
        elif x.dagesh and seen_nucleus and prev_vowel and x.base != HE:
            x.double = True
        x.cons = c
        if x.vowels:
            seen_nucleus = True


def _prev_sounding(L, i):
    for j in range(i - 1, -1, -1):
        if not L[j].silent:
            return j
    return None


def _nucleus_before(L, i):
    """Vowel codepoint and meteg of the nearest nucleus before letter i, plus whether a
    yod mater follows it (hiriq-yod / tsere-yod count as long)."""
    mater = False
    for j in range(i - 1, -1, -1):
        x = L[j]
        if x.silent and x.base == YOD:
            mater = True
        if x.vowels:
            return x.vowels[-1], x.meteg, mater, j
    return None, False, False, None


def _verb(morphs, part):
    m = morphs[part] if part < len(morphs) else ""
    return len(m) >= 3 and m[0] == "V"


def _qal_qotl(morphs, part):
    """Qal imperative / infinitive construct: a qamats before shva here is qatan."""
    m = morphs[part] if part < len(morphs) else ""
    return len(m) >= 3 and m[:2] == "Vq" and m[2] in "vc"


def _shva(L, morphs, main=None):
    n = len(L)
    for i, x in enumerate(L):
        if x.vowels != [SHVA] or x.silent:
            continue
        nxt = L[i + 1] if i + 1 < n else None
        nxt_bgdkpt = nxt is not None and nxt.base in BGDKPT and not nxt.silent
        if i == n - 1 or (i == n - 2 and nxt.disp):
            vocal = False
        elif _prev_sounding(L, i) is None or x.double:
            vocal = True
        else:
            p = L[_prev_sounding(L, i)]
            pv, pmeteg, mater, j = _nucleus_before(L, i)
            long_ = pv in LONG or mater
            if p.vowels == [SHVA] and p.nuc is None:
                vocal = True                                  # second of two shvas
            elif nxt is not None and nxt.base == x.base and nxt.vowels and nxt.part == x.part:
                vocal = True                                  # first of two identical letters
            elif long_ and (pmeteg or j == main):           # meteg or stressed: laylah
                vocal = True
            elif not long_:
                # after a short vowel the shva is silent even before a spirant (malkhe, ivdu,
                # biqvurah), except a dropped dagesh forte after a patach prefix: always after
                # vav-consecutive (vayehi, vayedabber; Lane 2026-10-08), else only before a
                # soft bgdkpt
                prefix = j is not None and L[j].part != x.part and pv == PATACH
                vav_consec = prefix and L[j].base == VAV and _verb(morphs, x.part)
                vocal = prefix and (vav_consec or (nxt_bgdkpt and not nxt.dagesh))
            elif pv == QAMATS and j is not None and L[j].part != x.part:
                vocal = True                                  # prefix qamats is long: hareshaim
            elif pv == QAMATS and not mater and _qal_qotl(morphs, x.part):
                vocal = False                                 # shomrah, molkhi
            elif nxt_bgdkpt:
                vocal = not nxt.dagesh
            elif pv == QAMATS and not mater:
                vocal = _verb(morphs, x.part)                 # shamru vs chokhmah
            else:
                vocal = True                                  # after a long vowel
        x.nuc = SHVA if vocal else None
        x.reduced = vocal


def _syllables(L):
    syls = []
    for i, x in enumerate(L):
        if x.silent:
            if x.base == YOD and syls:
                syls[-1]["mater"] = True
            continue
        if x.disp:
            if syls:
                syls[-1]["tail"] += x.disp
            x.syl = len(syls) - 1
            continue
        has_nuc = x.base is None or (x.vowels and x.vowels != [SHVA]) or x.nuc == SHVA
        if x.furtive and syls:
            syls[-1]["coda"] += "a" + x.cons
            syls[-1]["furtive"] = True
            x.syl = len(syls) - 1
            continue
        if not has_nuc:
            if syls:
                syls[-1]["coda"] += x.cons
            else:
                syls.append(_syl("", x.cons, None))
            x.syl = len(syls) - 1
            continue
        if x.double and syls:
            syls[-1]["coda"] += x.cons
            syls[-1]["gem"] = True
        vs = [v for v in x.vowels if v != SHVA] or [SHVA]
        v = vs[0]
        s = _syl(x.cons, "e" if v == SHVA else VOWEL[v], v)
        s["reduced"] = v == SHVA or v in HATEF
        s["meteg"] = x.meteg
        s["part"] = x.part
        syls.append(s)
        x.syl = len(syls) - 1
        if len(vs) > 1:                                      # patach + hiriq (Jerusalem)
            s2 = _syl("y", VOWEL[vs[1]], vs[1])
            s2["meteg"] = False
            syls.append(s2)
    for i, x in enumerate(L):
        if x.silent and x.syl is None:
            h = x.host
            while h is not None and h >= 0 and L[h].syl is None:
                h -= 1
            x.syl = L[h].syl if h is not None and h >= 0 else 0
    return syls


def _syl(onset, vowel, vcp):
    return {"onset": onset, "vowel": vowel, "vcp": vcp, "coda": "", "tail": "",
            "reduced": False, "meteg": False, "gem": False, "mater": False, "furtive": False}


def _accents(L, verse_final):
    """Locate the main stress from the accents. Returns (letter index | "last" | None, src).
    Other accents on the word mark secondary stress and are treated like meteg."""
    acc = [(i, a) for i, x in enumerate(L) for a in x.accents]
    if not acc:
        mets = [i for i, x in enumerate(L) if x.meteg]
        if verse_final and mets:
            return mets[-1], "silluq"
        return None, "none"
    counts = {}
    for _, a in acc:
        counts[a] = counts.get(a, 0) + 1
    real = [i for i, a in acc if a not in POSITIONAL]
    dup = [i for i, a in acc if a in POSITIONAL and counts[a] > 1]
    post = {a for _, a in acc if a in POSTPOSITIVE}
    qadma = [i for i, a in acc if a == QADMA]
    zarqa = [i for i, a in acc if a == ZARQA]
    if dup:                                     # pashta written twice: first one is the stress
        main, src, secondary = dup[0], "accent", real
    elif PASHTA in post and qadma:              # WLC writes the first of two pashtas as qadma
        main, src, secondary = qadma[-1], "accent", real
    elif ZINOR in post and zarqa:               # same for zarqa (U+0598 then U+05AE)
        main, src, secondary = zarqa[-1], "accent", real
    elif real and post:                         # conjunctive + pashta etc.: final stress
        main, src, secondary = "last", "postpositive", real
    elif real:
        main, src, secondary = real[-1], "accent", real[:-1]
    elif PASHTA in post:                        # single pashta: not penultimate
        main, src, secondary = "last", "postpositive", []
    else:
        main, src, secondary = None, "positional", []
    for i in secondary:
        if i != main:
            L[i].meteg = True
    return main, src


def _stress_index(L, syls, main, src, hint, suffixed):
    if not syls or src == "none":
        return None, src
    if main == "last":
        idx = len(syls) - 1
    elif main is not None:
        idx = L[main].syl
    elif hint is not None and hint < len(syls):
        idx, src = hint, "table"
    elif len(syls) > 1 and not suffixed and syls[-1]["vcp"] == SEGOL and syls[-1]["coda"] \
            and not syls[-2]["reduced"]:
        idx, src = len(syls) - 2, "segolate"
    else:
        idx, src = len(syls) - 1, "default"
    while idx is not None and idx < len(syls) - 1 and syls[idx]["reduced"]:
        idx += 1
    return idx, src


def _qatan(syls, stress, lemmas=(), morphs=()):
    """Qamats is o before hatef qamats, or in a closed unstressed syllable. Meteg keeps it a
    (hatstsad-), as do a doubled-consonant close (lammah) and the -av suffix (le'echav).
    Lemma 3605 (kol) is always o, meteg or not. Lemmas in QATAN_OPEN have qatan in the
    first stem syllable even when open (qodashim, oniyyah, shorashim)."""
    first = {}
    for k, s in enumerate(syls):
        if s["vcp"] is not None:
            first.setdefault(s.get("part", 0), k)
    for k, s in enumerate(syls):
        part = s.get("part", 0)
        if s["vcp"] != QAMATS or (part < len(morphs) and morphs[part][:1] in ("R", "C", "T")
                                  and part < len(morphs) - 1):
            continue                                # prefix la-/ba-/ha-/va- keeps a
        nxt = syls[k + 1] if k + 1 < len(syls) else None
        if nxt is not None and nxt["vcp"] == HQAMATS and nxt.get("part", 0) == part:
            s["vowel"] = "o"
        elif _lemma(lemmas, part) in QATAN_OPEN and first[part] == k and k != stress:
            s["vowel"] = "o"
        elif k != stress and s["coda"] and not s["gem"] and not s["mater"] and (
                not s["meteg"] or _lemma(lemmas, s.get("part", 0)) == "3605"):
            s["vowel"] = "o"


def _lemma(lemmas, part):
    return lemmas[part].split()[0] if part < len(lemmas) and lemmas[part] else ""


def translit(surface, verse_final=False, morph="", stress_hint=None, lemma="", maqqef=False):
    """surface: pointed word, optionally with "/" between morphemes (enables the prefix and
    verb rules); morph: OSHB morph string for the same morphemes, e.g. "HC/Vqp3cp";
    lemma: OSHB lemma string ("c/3605"); maqqef: word is joined to the next (no stress)."""
    L = _parse(surface)
    if not L:
        return {"text": "", "syllables": [], "stress": None, "stress_src": "none"}
    morphs = morph[1:].split("/") if morph else []
    main, src = _accents(L, verse_final)
    if maqqef:
        main, src = None, "none"
    _roles(L)
    _consonants(L)
    _shva(L, morphs, main)
    syls = _syllables(L)
    if L[0].base == ALEF and syls and syls[0]["onset"] == "'":
        syls[0]["onset"] = ""
    suffixed = bool(morphs) and morphs[-1][:1] == "S"
    stress, src = _stress_index(L, syls, main, src, stress_hint, suffixed)
    _qatan(syls, stress, lemma.split("/") if lemma else (), morphs)
    texts = []
    for k, s in enumerate(syls):
        v = s["vowel"] or ""
        if k == stress and v and (k != len(syls) - 1 or s["furtive"]):
            v = ACUTE[v]                        # furtive -ach shows two vowels: ruach -> rúach
        texts.append(s["onset"] + v + s["coda"] + s["tail"])
    return {"text": "".join(texts), "syllables": texts, "stress": stress, "stress_src": src}


def stress_key(surface):
    """Surface without accents, meteg or morpheme slashes: key for the stress table."""
    return "".join(c for c in surface if not (0x0591 <= ord(c) <= 0x05AF or c in (METEG, "/")))


def build_stress_table(tokens):
    """{stress_key: syllable index} from tokens whose stress is fixed by a real accent; used
    for words carrying only a positional accent. Corpus-derived, deterministic."""
    votes = {}
    for t in tokens:
        if not t.get("read", True):
            continue
        r = translit(_slashed(t), t["sof_pasuq"], t["morph"])
        if r["stress_src"] in ("accent", "silluq", "postpositive"):
            c = votes.setdefault(stress_key(t["surface"]), {})
            c[r["stress"]] = c.get(r["stress"], 0) + 1
    return {k: max(sorted(c), key=c.get) for k, c in votes.items()}


def _slashed(tok):
    return "/".join(p["text"] for p in tok["parts"])


def _divine(surface, lemma, verse_final):
    """Prefix morphemes transliterated normally; the name itself is YHWH."""
    parts = surface.split("/") if "/" in surface else None
    lemmas = lemma.split("/")
    if parts is None or len(parts) != len(lemmas):
        return {"text": "YHWH", "syllables": ["YHWH"], "stress": None, "stress_src": "divine"}
    pre = ""
    for p, lm in zip(parts, lemmas):
        if lm.split()[0] in ("3068", "3069"):
            break
        pre += p
    head = translit(pre)["text"] if pre else ""
    return {"text": head + "YHWH", "syllables": ([head] if head else []) + ["YHWH"],
            "stress": None, "stress_src": "divine"}


def translit_token(tok, stress_table=None):
    """Token dict from corpus.load_tokens(). Uses parts so the divine name can be isolated."""
    if any(p["lemma"].split()[0] in ("3068", "3069") for p in tok["parts"] if p["lemma"]):
        return _divine(_slashed(tok), "/".join(p["lemma"] for p in tok["parts"]),
                       tok["sof_pasuq"])
    hint = stress_table.get(stress_key(tok["surface"])) if stress_table else None
    return translit(_slashed(tok), tok["sof_pasuq"], tok["morph"], hint, tok["lemma"],
                    tok["maqqef_next"])


if __name__ == "__main__":
    import sys
    for w in sys.argv[1:]:
        print(translit(w))

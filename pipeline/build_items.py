"""
Drill and reading items. Reads the corpus, data/measures/*.json, data/text/ and data/lessons.json
(run build_text.py, then build_lessons.py) and the curated glosses in glosses/.

    python -X utf8 pipeline/build_items.py
      -> data/items/lemmas.json      the vocabulary queue (ranks 1-750, frequency order)
         data/items/unit<N>.json     grammar/reading items per unit (Units 0-1 so far)
         data/units.json             unit manifest (title, help level, lessons, item file)
         build/review_unit<N>.json   glosses awaiting Lane's review (feeds the review page)

Every item carries a stable id; token snapshots ("tok") are copied from data/text so the app
can show a card front without loading a chapter. Hebrew only ever comes from the corpus.

Item ids: L:<lemma> (spaces -> _), F:<lemma>:<morph>:<surface hash>, M:<morpheme>,
N:<lemma> (name), D:<token id> (decoding), R:<ref>:<start>-<end> (micro-reading).

Snapshot highlights: "hl" = morpheme (part) index; "hlc" = [[start, end), ...] letter-cluster
ranges over the whole word (a cluster is one letter plus the marks after it), used where the
segment is not its own OSHB morpheme (noun endings, verb prefix letters) or spans two.
"""
import collections
import glob
import hashlib
import json
import os
import random
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corpus    # noqa: E402
import lexicon   # noqa: E402
import tahot     # noqa: E402
import translit  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEAS = os.path.join(ROOT, "data", "measures")
TEXT = os.path.join(ROOT, "data", "text")
ITEMS = os.path.join(ROOT, "data", "items")
GLOSSES = os.path.join(ROOT, "glosses")
BUILD = os.path.join(ROOT, "build")
QUAR = os.path.join(ROOT, "data", "parse_quarantine.json")
STRIP = re.compile("[%s-%s%s]" % (chr(0x591), chr(0x5AF), chr(0x5BD)))
DAGESH, SHVA, RAFE = chr(0x5BC), chr(0x5B0), chr(0x5BF)
CORE = 750
VOCAB_UNITS = [(1, 50), (51, 120), (121, 190), (191, 260), (261, 330), (331, 400), (401, 480),
               (481, 570), (571, 660), (661, 750)]          # Units 1-10 (SPEC section 3)
FORMS_PER_UNIT = {1: 8, 2: 6, 3: 55}       # Units 2-3: wayyiqtol only (Lane, Phase 3 part 2)
NAMES_PER_UNIT = {2: 10}
UNITS = [  # unit, title, reading help, parse facets asked (SPEC section 3); built so far
    (0, "Calibration", "full", []),
    (1, "The glue", "interlinear", []),
    (2, "Nouns and their attachments", "unknown-only", []),
    (3, "The story tense: wayyiqtol", "unknown-only", ["conj", "pgn"]),
]
EASY_BOOKS = ["Gen", "Exod", "Jonah", "Ruth", "Josh", "Judg", "1Sam", "2Sam", "1Kgs", "2Kgs", "Num"]


def load(path, default=None):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else default


def curated(name):
    d = load(os.path.join(GLOSSES, name), {}) or {}
    return {k: v for k, v in d.items() if not k.startswith("_")}


def lid(lemma):
    return "L:" + lemma.replace(" ", "_")


def surf_key(t):
    return STRIP.sub("", t["surface"])


class Ctx:
    def __init__(self):
        t0 = time.time()
        self.tokens = [t for t in corpus.load_tokens() if t["read"]]
        self.by_id = {t["id"]: t for t in self.tokens}
        self.prose = [t for t in self.tokens if not t["poem"] and t["lang"] == "H"]
        self.quar = {q["id"] for q in load(QUAR)["tokens"]}
        self.ranks = load(os.path.join(MEAS, "lemma_ranks.json"))
        self.rank = {r["lemma"]: r["rank"] for r in self.ranks}
        self.tah = tahot.glosses(self.tokens)
        self.tb = lexicon.tbesh()
        self.lm = lexicon.lemma_map(self.tokens, self.tah)
        self.stable = translit.build_stress_table(list(corpus.load_tokens()))
        self.snaps = {}
        for path in glob.glob(os.path.join(TEXT, "*", "*.json")):
            ch = load(path)
            for v in ch["verses"]:
                for tk in v["tokens"]:
                    tk["ref"] = f"{ch['book']}.{ch['ch']}.{v['v']}"
                    self.snaps[tk["id"]] = tk
        self.verses = collections.defaultdict(list)
        self.used = collections.Counter()
        for t in self.tokens:
            self.verses[t["ref"]].append(t)
        print(f"context loaded [{time.time() - t0:.1f}s]")

    def snap(self, tid, part=None, hlc=None):
        s = self.snaps[tid]
        out = {k: s[k] for k in ("id", "ref", "s", "tr", "g", "gs", "gr", "p")}
        if part is not None:
            out["hl"] = part
        if hlc is not None:
            out["hlc"] = hlc
        return out

    def verse_ease(self, ref):
        """Share of words whose main morpheme is a lemma of rank <= 300. Names count as hard,
        so name lists (Gen 10) do not win; prefixes and suffixes are free."""
        n = k = 0
        for t in self.verses[ref]:
            p = lexicon.main_part(t)
            if p:
                n += 1
                k += self.rank.get(p["lemma"], 9999) <= 300
        return k / n if n else 0

    def clean(self, t):
        """Ordinary spelling: no rafe or other rare marks, not quarantined, not a ketiv/qere."""
        return RAFE not in t["surface"] and t["id"] not in self.quar and not t["ketiv"]

    def good_example(self, toks, max_words=14):
        """Best token to show in its verse: short, easy, prose, unquarantined, early books."""
        def score(t):
            words = len(self.verses[t["ref"]])
            return (t["poem"] or not self.clean(t) or words > max_words or words < 5,
                    -round(self.verse_ease(t["ref"]), 1), self.used[t["ref"]],
                    EASY_BOOKS.index(t["book"]), words)
        best = min(toks, key=score) if toks else None
        if best:
            self.used[best["ref"]] += 1             # spread examples over many verses
        return best


# --- lemmas ------------------------------------------------------------------------------------

def citation_ok(lemma_pos, t, part):
    m = part["morph"]
    if lemma_pos.startswith("V"):
        return m[:1] == "V" and m[2:] == "p3ms"
    if lemma_pos.startswith("Nc"):
        return m[:2] == "Nc" and m[3:5] == "sa"
    if lemma_pos.startswith("A"):
        return m[:2] == "Aa" and m[2:5] == "msa"
    return True


def build_lemmas(ctx):
    occ = collections.defaultdict(list)
    for t in ctx.prose:
        p = lexicon.main_part(t)
        if p:
            occ[p["lemma"]].append(t)
    cur = curated("lemmas.json")
    out = []
    for r in ctx.ranks[:CORE]:
        lem, toks = r["lemma"], occ[r["lemma"]]
        bare = [t for t in toks if len(t["parts"]) == 1]
        stems = collections.Counter(lexicon.main_part(t)["morph"][1] for t in toks
                                    if lexicon.main_part(t)["morph"][:1] == "V")
        pos = r["pos"]
        if pos.startswith("V") and stems:
            pos = "V" + stems.most_common(1)[0][0]
        cit = [t for t in bare if citation_ok(pos, t, t["parts"][0])
               and (not pos.startswith("V") or t["parts"][0]["morph"][1] == pos[1])]
        if not cit and pos.startswith("Nc"):
            cit = [t for t in bare if t["parts"][0]["morph"][4:5] == "a"]       # plural-only nouns
        pool = cit or bare or toks
        common = collections.Counter(surf_key(t) for t in pool).most_common(1)[0][0]
        cands = [t for t in pool if surf_key(t) == common]
        front = min(cands, key=lambda t: (not ctx.clean(t), t["maqqef_next"], t["poem"]))
        senses = collections.Counter(ctx.tah[t["id"]]["dstrong"] for t in toks
                                     if t["id"] in ctx.tah and ctx.tah[t["id"]]["dstrong"])
        tot = sum(senses.values()) or 1
        sense_list = [{"key": k, "tbesh": ctx.tb.get(k, {}).get("gloss", ""), "share": round(n / tot, 3)}
                      for k, n in senses.most_common(5) if n / tot >= 0.05]
        tb = ctx.tb.get(ctx.lm.get(lem, {}).get("key", ""), {})
        c = cur.get(lem)
        unit = next(i + 1 for i, (a, z) in enumerate(VOCAB_UNITS) if a <= r["rank"] <= z)
        ex = ctx.good_example([t for t in toks if t["id"] != front["id"]] or toks)
        item = {"id": lid(lem), "kind": "lemma", "lemma": lem, "rank": r["rank"], "count": r["count"],
                "pos": pos, "unit": unit, "cite": "dictionary" if cit else ("bare" if bare else "in-word"),
                "tok": ctx.snap(front["id"], None if len(front["parts"]) == 1 else
                                front["parts"].index(lexicon.main_part(front))),
                "example": {"id": ex["id"], "ref": ex["ref"]},
                "gloss": c["gloss"] if c else tb.get("gloss", r.get("gloss_hint", "")),
                "gloss_src": c["source"] if c else "TBESH",
                "reviewed": bool(c and c.get("reviewed")),
                "senses": [dict(s, gloss=(c or {}).get("senses", {}).get(s["key"], s["tbesh"])) for s in sense_list],
                "tbesh_key": ctx.lm.get(lem, {}).get("key"), "bdb": tb.get("defn", "")[:600]}
        if c and c.get("note"):
            item["note"] = c["note"]
        out.append(item)
    return out


# --- whole verb forms ----------------------------------------------------------------------------

def form_id(f, skey):
    return "F:%s:%s:%s" % (f["lemma"].replace(" ", "_"), f["morph"],
                           hashlib.sha1(skey.encode("utf-8")).hexdigest()[:6])


def pick_forms(ctx):
    """{unit: [M6 rows]}. Unit 1 = the 8 commonest forms of any kind; Units 2-3 = the next
    wayyiqtol forms in rank order, one card per lemma+parse (pausal spellings like vayyomar
    and vayyamot fold into the card already taken). Forms with every token quarantined are
    skipped (vayyishtachu: OSHB and BHSA disagree on its stem; it is a lemma card instead)."""
    top = load(os.path.join(MEAS, "verb_forms_top400.json"))
    usable = {(surf_key(t), t["morph"], t["lemma"]) for t in ctx.prose if t["id"] not in ctx.quar}
    top = [f for f in top if (surf_key(ctx.by_id[f["example_id"]]), f["morph"], ctx.by_id[f["example_id"]]["lemma"]) in usable]
    out = {1: top[:FORMS_PER_UNIT[1]]}
    taken = {(f["lemma"], f["morph"]) for f in out[1]}
    rest = [f for f in top[FORMS_PER_UNIT[1]:] if f["family"] == "wayyiqtol"]
    for unit in (2, 3):
        out[unit] = []
        while len(out[unit]) < FORMS_PER_UNIT[unit] and rest:
            f = rest.pop(0)
            if (f["lemma"], f["morph"]) not in taken:
                taken.add((f["lemma"], f["morph"]))
                out[unit].append(f)
    return out


CONJ = {"w": "wayyiqtol", "p": "qatal", "q": "weqatal", "i": "yiqtol", "v": "imperative",
        "j": "jussive", "h": "cohortative", "r": "participle", "s": "participle", "a": "inf. abs.",
        "c": "inf. cstr."}


def facets(morph):
    """Chip-parse facets from the verb morpheme's code (conj + person/gender/number)."""
    v = next(m for m in morph[1:].split("/") if m[:1] == "V")
    return {"stem": v[1], "conj": CONJ[v[2]], "pgn": v[3:6] if v[2] not in "rsac" else v[3:5]}


def build_forms(ctx, top, unit):
    cur = curated("forms.json")
    by_key = collections.defaultdict(list)
    for t in ctx.prose:
        by_key[(surf_key(t), t["morph"])].append(t)
    out = []
    for f in top:
        ex0 = ctx.by_id[f["example_id"]]
        toks = [t for t in by_key[(surf_key(ex0), f["morph"])] if t["lemma"] == ex0["lemma"]]
        ok = [t for t in toks if t["id"] not in ctx.quar]
        exs, seen = [], set()
        for t in sorted(ok, key=lambda t: (len(ctx.verses[t["ref"]]) > 14, -round(ctx.verse_ease(t["ref"]), 1),
                                           EASY_BOOKS.index(t["book"]))):
            if t["ref"] not in seen:
                exs.append(t)
                seen.add(t["ref"])
            if len(exs) == 4:
                break
        g = collections.Counter(ctx.tah[t["id"]]["g"] for t in toks if t["id"] in ctx.tah)
        fid = form_id(f, surf_key(ex0))
        c = cur.get(fid)
        out.append({"id": fid, "kind": "form", "unit": unit, "rank": f["rank"], "count": f["count"],
                    "lemma": f["lemma"], "morph": f["morph"], "parse": f["parse"], "family": f["family"],
                    "facets": facets(f["morph"]),
                    "ambiguous": f["ambiguous"], "tr": f["translit"],
                    "examples": [ctx.snap(t["id"]) for t in exs],
                    "gloss": c["gloss"] if c else g.most_common(1)[0][0],
                    "gloss_src": c["source"] if c else "TAHOT",
                    "reviewed": bool(c and c.get("reviewed")),
                    "tahot_glosses": [[k, n] for k, n in g.most_common(4)]})
    return out


# --- morphemes ---------------------------------------------------------------------------------

MORPHEMES = [  # id, label, meaning, unit
    ("ve", "ve- (with shva)", "and", 1),
    ("u", "u- (shureq; before b/m/p or a shva)", "and", 1),
    ("va", "va- (with a or a: vowel)", "and", 1),
    ("vayy", "va- + doubled letter on a verb", "and (story form; Unit 3 explains)", 1),
    ("ha", "ha- + doubled letter", "the", 1),
    ("ha_g", "ha-/he- before a guttural (no doubling)", "the", 1),
    ("be", "be-/bi-/ba- (no article)", "in, with, by", 1),
    ("le", "le-/li-/la- (no article)", "to, for", 1),
    ("ke", "ke-/ki-/ka- (no article)", "like, as", 1),
    ("mi", "mi- + doubled letter", "from", 1),
    ("me", "me- before a guttural", "from", 1),
    ("ba", "ba- (b- + article)", "in the", 1),
    ("la", "la- (l- + article)", "to the, for the", 1),
    ("ka", "ka- (k- + article)", "like the", 1),
]


EXPECT = {"ve": r"^and ", "u": r"^and ", "va": r"^and ", "vayy": r"^and ", "ha": r"^the ", "ha_g": r"^the ",
          "be": r"^(in|on|with|by|among|at) ", "le": r"^(to|for) ", "ke": r"^(like|as) ",
          "mi": r"^from ", "me": r"^from ", "ba": r"^(in|on|with|by|at) the ", "la": r"^(to|for) the ",
          "ka": r"^(like|as) the "}


def morpheme_class(t, i):
    p, ms = t["parts"][i], t["morph"][1:].split("/")
    lem, m, txt = p["lemma"], ms[i], p["text"]
    nxt = t["parts"][i + 1]["text"] if i + 1 < len(t["parts"]) else ""
    doubled = DAGESH in nxt[:3]
    vowels = {chr(c) for c in range(0x5B0, 0x5BC)} & set(txt)
    if lem == "c" and m == "C":
        if i + 1 < len(ms) and ms[i + 1][:1] == "V" and ms[i + 1][2:3] == "w":
            return "vayy"
        if DAGESH in txt and not vowels:
            return "u"
        if vowels & {chr(0x5B7), chr(0x5B8)}:
            return "va"
        return "ve"
    if lem == "d" and m == "Td":
        return "ha" if doubled else "ha_g"
    if lem in "blk" and m in ("R", "Rd"):
        return {"b": "be", "l": "le", "k": "ke"}[lem] if m == "R" else {"b": "ba", "l": "la", "k": "ka"}[lem]
    if lem == "m" and m == "R":
        return "me" if chr(0x5B5) in txt else "mi"
    return None


def build_morphemes(ctx, unit):
    cur = curated("morphemes.json")
    ex = collections.defaultdict(list)
    for t in ctx.prose:
        if not ctx.clean(t) or len(t["parts"]) != 2:
            continue                          # one prefix + core keeps the highlight unambiguous
        core = t["parts"][1]
        if not core["lemma"][:1].isdigit():
            continue
        k = morpheme_class(t, 0)
        if k:
            ex[k].append(t)
    out = []
    for mid, label, meaning, u in MORPHEMES:
        if u != unit:
            continue
        want = {"u": "u", "vayy": "v", "ve": "v", "va": "v", "ha": "h", "ha_g": "h"}.get(mid, mid[0])
        expect = re.compile(EXPECT[mid])

        def score(t):
            core = t["parts"][1]
            r = ctx.rank.get(core["lemma"], 9999)
            name = core["morph"][:2] in ("Np", "Ng")
            nominal = core["morph"][:1] in "NA" or mid in ("ve", "u", "va", "vayy")
            return (PHON.match(ctx.snaps[t["id"]]["tr"])[0] != want,   # spirant b/k after a vowel: later
                    not nominal, r > 50 and not name, name, r, EASY_BOOKS.index(t["book"]))
        picked, seen = [], set()
        fits = [t for t in ex[mid] if expect.search(ctx.snaps[t["id"]]["g"])]
        for t in sorted(fits, key=score):
            core = t["parts"][1]["lemma"]
            if core not in seen:
                picked.append(t)
                seen.add(core)
            if len(picked) == 6:
                break
        c = cur.get("M:" + mid, {})
        out.append({"id": "M:" + mid, "kind": "morpheme", "unit": unit, "label": label,
                    "gloss": c.get("gloss", meaning), "gloss_src": c.get("source", "curated"),
                    "reviewed": bool(c.get("reviewed")), "count": len(ex[mid]),
                    "examples": [ctx.snap(t["id"], 0) for t in picked]})
    return out


# --- Units 2-3: highlighted segments (noun endings, pronoun suffixes, story-tense markers) -----

YOD, VAV, TAV, HE, ALEF, NUN, MEM_F = (chr(c) for c in (0x5D9, 0x5D5, 0x5EA, 0x5D4, 0x5D0, 0x5E0, 0x5DD))
HIRIQ, TSERE, PATACH, QAMATS, HOLAM = (chr(c) for c in (0x5B4, 0x5B5, 0x5B7, 0x5B8, 0x5B9))
PGN_MEANING = {"3ms": "his; him", "3fs": "her", "3mp": "their; them", "3fp": "their; them (f.)",
               "2ms": "your; you (m. sg.)", "2fs": "your; you (f. sg.)", "2mp": "your; you (pl.)",
               "1cs": "my; me", "1cp": "our; us"}
SING_LABEL = {"3ms": "-o, -hu", "3fs": "-ah (dot in the he)", "3mp": "-am, -hem", "3fp": "-an, -hen",
              "2ms": "-kha", "2fs": "-ekh", "2mp": "-khem", "1cs": "-i", "1cp": "-nu, -enu"}
PLUR_LABEL = {"3ms": "-av", "3fs": "-eha", "3mp": "-ehem", "3fp": "-ehen", "2ms": "-ekha",
              "2mp": "-ekhem", "1cs": "-ay", "1cp": "-enu"}
SEGMENTS = [  # id, label, meaning, unit, group
    ("im", "-im", "plural (mostly masculine nouns)", 2, "ending"),
    ("ot", "-ot", "plural (mostly feminine nouns)", 2, "ending"),
    ("ah_f", "-ah", "feminine singular", 2, "ending"),
    ("ayim", "-ayim", "dual: a pair, two of", 2, "ending"),
    ("ey", "-e (yod after tsere, no ending after it)", "plural 'of' form: the X-s of", 2, "ending"),
    ("at", "-at", "feminine 'of' form: the X of", 2, "ending"),
] + [("s_" + p, SING_LABEL[p] + " (after a singular noun or l-, b-, 'et)", PGN_MEANING[p], 2, "suffix")
     for p in SING_LABEL] + [
    ("p_" + p, PLUR_LABEL[p] + " (yod before it: after a plural noun or 'el, `al)", PGN_MEANING[p], 2, "suffix")
    for p in PLUR_LABEL] + [
    ("dir", "-ah (unstressed, on a place)", "toward, to (direction)", 2, "suffix"),
    ("w_seq", "va- + doubled first letter on a verb", "and (story tense: and then ... did)", 3, "marker"),
    ("y3ms", "y- after va-", "he (it)", 3, "marker"),
    ("t3fs", "t- after va-", "she (it); the same t- also means you (m. sg.)", 3, "marker"),
    ("a1cs", "'- after va- (no doubling)", "I", 3, "marker"),
    ("n1cp", "n- after va-", "we", 3, "marker"),
    ("y_u", "y- ... -u", "they", 3, "marker"),
    ("t_u", "t- ... -u", "you (pl.)", 3, "marker"),
    ("short", "short ending: the -eh of the root drops", "still the story tense (vayya`as beside ya`aseh)", 3, "marker"),
]


PLURAL_ONLY = {"430", "6440", "4325", "8064", "2416 b"}   # elohim, panim, mayim, shamayim, chayyim
COPULA = re.compile(r"\b(is|are|was|were)\b")     # TAHOT glosses that add a verb


def clusters(s):
    """Letter clusters: each Hebrew letter with the marks that follow it."""
    out = []
    for ch in s:
        if 0x5D0 <= ord(ch) <= 0x5EA or not out:
            out.append(ch)
        else:
            out[-1] += ch
    return out


def segment_classes(parts):
    """[(segment id, part index, [[a, b], ...])] for one word given its OSHB parts
    ({text, lemma, morph}). Pure function of the corpus token; verify_content.py re-runs it."""
    cl = [clusters(STRIP.sub("", p["text"])) for p in parts]
    start = [sum(len(c) for c in cl[:i]) for i in range(len(parts))]
    n = start[-1] + len(cl[-1])
    ms = [p["morph"] for p in parts]
    out = []
    last, lc = ms[-1], cl[-1]
    # noun endings: the noun is the last morpheme (no suffix after it)
    if last[:2] in ("Nc", "Aa") and len(last) >= 5 and len(lc) >= 3:
        g, num, st = last[2], last[3], last[4]
        z, y, x = lc[-1], lc[-2], lc[-3]
        if num == "p" and st == "a" and g != "f" and z[0] == MEM_F and y == YOD and HIRIQ in x:
            out.append(("im", len(parts) - 1, [[n - 2, n]]))
        if num == "d" and st == "a" and z[0] == MEM_F and y[0] == YOD and HIRIQ in y and (PATACH in x or QAMATS in x):
            out.append(("ayim", len(parts) - 1, [[n - 2, n]]))
        if num == "p" and g == "f" and z[0] == TAV and y[0] == VAV and HOLAM in y:
            out.append(("ot", len(parts) - 1, [[n - 2, n]]))
        if g == "f" and num == "s" and st == "a" and z == HE and QAMATS in y:
            out.append(("ah_f", len(parts) - 1, [[n - 1, n]]))
        if num in "pd" and st == "c" and z == YOD and TSERE in y:
            out.append(("ey", len(parts) - 1, [[n - 1, n]]))
        if g == "f" and num == "s" and st == "c" and z == TAV and PATACH in y:
            out.append(("at", len(parts) - 1, [[n - 1, n]]))
    for i in range(1, len(parts)):
        m, host = ms[i], ms[i - 1]
        a, b = start[i], start[i] + len(cl[i])
        if m == "Sd" and host[:1] in "ND":
            out.append(("dir", i, [[a, b]]))
        if not m.startswith("Sp") or m[2:5] not in PGN_MEANING:
            continue
        pgn = m[2:5]
        noun = host[:2] in ("Nc", "Aa", "Ac")
        num = host[3] if noun and len(host) > 3 else None
        if not (noun or host[:1] == "R" or host[:2] == "To"):
            continue
        hl = cl[i - 1][-1] if cl[i - 1] else ""
        if pgn == "1cs":
            if "".join(cl[i]) != YOD:
                continue
            if HIRIQ in hl and num in (None, "s"):
                out.append(("s_1cs", i, [[a, b]]))
            elif (PATACH in hl or QAMATS in hl) and num in (None, "p", "d"):
                out.append(("p_1cs", i, [[a, b]]))
            continue
        if hl[:1] == YOD:
            if pgn in PLUR_LABEL and num in (None, "p", "d") and not (pgn == "3ms" and "".join(cl[i]) != VAV):
                out.append(("p_" + pgn, i, [[a - 1, b]]))
        elif num in (None, "s"):
            out.append(("s_" + pgn, i, [[a, b]]))
    # story-tense markers: vav + verb, nothing else in the word
    if len(parts) == 2 and ms[0] == "C" and ms[1][:1] == "V" and ms[1][2:3] == "w":
        v, vc = ms[1], cl[1]
        pgn, first = v[3:6], vc[0]
        if DAGESH in first and first[0] in (YOD, TAV, NUN) and PATACH in cl[0][0]:
            out.append(("w_seq", 1, [[0, 2]]))
        shureq = vc[-1] == VAV + DAGESH
        if pgn == "3ms" and first[0] == YOD:
            out.append(("y3ms", 1, [[1, 2]]))
        if pgn == "3fs" and first[0] == TAV:
            out.append(("t3fs", 1, [[1, 2]]))
        if pgn == "1cs" and first[0] == ALEF:
            out.append(("a1cs", 1, [[1, 2]]))
        if pgn == "1cp" and first[0] == NUN:
            out.append(("n1cp", 1, [[1, 2]]))
        if pgn == "3mp" and first[0] == YOD and shureq:
            out.append(("y_u", 1, [[1, 2], [n - 1, n]]))
        if pgn == "2mp" and first[0] == TAV and shureq:
            out.append(("t_u", 1, [[1, 2], [n - 1, n]]))
        if pgn in ("3ms", "3fs") and vc[-1][0] != HE:
            out.append(("short", 1, [[n - 1, n]]))     # candidate; needs a long -eh form (build_segments)
    return out


def long_forms(ctx):
    """{(lemma, stem, pgn): token} plain yiqtol forms ending in -eh (ya`aseh), the long partner
    of a short story-tense form (vayya`as)."""
    out = {}
    for t in ctx.prose:
        if len(t["parts"]) != 1 or not ctx.clean(t):
            continue
        p = t["parts"][0]
        m = p["morph"]
        c = clusters(STRIP.sub("", p["text"]))
        if m[:1] == "V" and m[2:3] == "i" and m[3:6] in ("3ms", "3fs") and c[-1] == HE and chr(0x5B6) in c[-2]:
            out.setdefault((p["lemma"], m[1], m[3:6]), t)
    return out


def build_segments(ctx, unit):
    cur = curated("morphemes.json")
    longs = long_forms(ctx)
    ex = collections.defaultdict(list)
    for t in ctx.prose:
        if not ctx.clean(t) or t["id"] not in ctx.tah:
            continue
        for mid, hl, hlc in segment_classes(t["parts"]):
            if mid == "short":
                v = t["parts"][1]
                lf = longs.get((v["lemma"], v["morph"][1], v["morph"][3:6]))
                if not lf:
                    continue
                t = dict(t, _long=lf)
            ex[mid].append((t, hl, hlc))
    out = []
    for mid, label, meaning, u, group in SEGMENTS:
        if u != unit:
            continue

        def score(e):
            t, hl, _ = e
            host = lexicon.main_part(t) or t["parts"][hl]
            r = ctx.rank.get(host["lemma"], 9999)
            name = host["morph"][:2] in ("Np", "Ng")
            odd = host["lemma"] in PLURAL_ONLY or bool(COPULA.search(ctx.snaps[t["id"]]["g"]))
            return (len(t["parts"]) > 2, odd, name, r > 190, r, EASY_BOOKS.index(t["book"]), t["id"])
        picked, seen = [], set()
        for e in sorted(ex[mid], key=score):
            host = (lexicon.main_part(e[0]) or e[0]["parts"][e[1]])["lemma"]
            if host not in seen:
                picked.append(e)
                seen.add(host)
            if len(picked) == 6:
                break
        c = cur.get("M:" + mid, {})
        item = {"id": "M:" + mid, "kind": "morpheme", "group": group, "unit": unit, "label": label,
                "gloss": c.get("gloss", meaning), "gloss_src": c.get("source", "curated (grammar)"),
                "reviewed": bool(c.get("reviewed")), "count": len(ex[mid]),
                "examples": [ctx.snap(t["id"], hl, hlc) for t, hl, hlc in picked]}
        if mid == "short":
            item["contrast"] = [ctx.snap(t["_long"]["id"]) for t, _, _ in picked]
        out.append(item)
    return out


# --- names -------------------------------------------------------------------------------------

def build_names(ctx, lo, hi, unit):
    names = load(os.path.join(MEAS, "names.json"))[lo:hi]
    cur = curated("names.json")
    occ = collections.defaultdict(list)
    for t in ctx.prose:
        p = lexicon.main_part(t)
        if p and p["morph"][:2] in ("Np", "Ng"):
            occ[p["lemma"]].append(t)
    out = []
    for i, n in enumerate(names):
        toks = occ[n["lemma"]]
        bare = [t for t in toks if len(t["parts"]) == 1 and ctx.clean(t)] or toks
        common = collections.Counter(surf_key(t) for t in bare).most_common(1)[0][0]
        front = min((t for t in bare if surf_key(t) == common), key=lambda t: (t["maqqef_next"], t["poem"]))
        ex = ctx.good_example([t for t in toks if t["id"] != front["id"] and ctx.clean(t)])
        tb = ctx.tb.get(ctx.lm.get(n["lemma"], {}).get("key", ""), {})
        c = cur.get(n["lemma"])
        out.append({"id": "N:" + n["lemma"].replace(" ", "_"), "kind": "name", "unit": unit, "lemma": n["lemma"],
                    "rank": lo + i + 1, "count": n["count"], "tok": ctx.snap(front["id"]),
                    "example": {"id": ex["id"], "ref": ex["ref"]},
                    "gloss": c["gloss"] if c else tb.get("gloss", n.get("gloss_hint", "")),
                    "gloss_src": c["source"] if c else "TBESH", "reviewed": bool(c and c.get("reviewed")),
                    "tbesh_key": ctx.lm.get(n["lemma"], {}).get("key"), "bdb": tb.get("defn", "")[:400]})
    return out


# --- Unit 0 decoding ---------------------------------------------------------------------------

PHON = re.compile(r"kh|ch|sh|ts|.")
SPIRANT_SWAP = {"b": "v", "v": "b", "k": "kh", "kh": "k", "p": "f", "f": "p"}
LOOKALIKE = {"b": "k", "k": "b", "v": "kh", "kh": "v", "d": "r", "r": "d", "h": "ch", "ch": "t",
             "t": "ch", "g": "n", "n": "g", "s": "m", "m": "s", "`": "ts", "ts": "`", "z": "v"}
QAMATS_SWAP = {"a": "o", "o": "a", "\u00e1": "\u00f3", "\u00f3": "\u00e1"}
CONS = set("bdfghklmnpqrstvyz'`") | {"kh", "ch", "sh", "ts"}
VOW = set("aeiou\u00e1\u00e9\u00ed\u00f3\u00fa")
FEATURE_ORDER = ["shva_vocal", "shva_silent", "dagesh_forte", "dagesh_lene", "spirant", "qamats_qatan",
                 "qamats_a", "furtive", "vowel_letter", "hatef", "maqqef", "final", "divine"]
FEATURE_KIND = {"spirant": "spirant", "dagesh_lene": "spirant", "dagesh_forte": "double",
                "shva_vocal": "shva", "shva_silent": "shva", "qamats_qatan": "qamats", "qamats_a": "qamats"}
FINALS = {chr(c) for c in (0x5DA, 0x5DD, 0x5DF, 0x5E3, 0x5E5)}


def word_features(ctx, t):
    r = translit.translit_token(t, ctx.stable)
    f = set(r.get("features", []))
    if t["maqqef_next"]:
        f.add("maqqef")
    if FINALS & set(t["surface"]):
        f.add("final")
    return f


def _variants(ph):
    """{kind: [phoneme lists]} one-change misreadings of a transliteration."""
    out = collections.defaultdict(list)
    n = len(ph)
    for i, x in enumerate(ph):
        if x in SPIRANT_SWAP:
            out["spirant"].append(ph[:i] + [SPIRANT_SWAP[x]] + ph[i + 1:])
        if x in LOOKALIKE:
            out["lookalike"].append(ph[:i] + [LOOKALIKE[x]] + ph[i + 1:])
        if x in QAMATS_SWAP:
            out["qamats"].append(ph[:i] + [QAMATS_SWAP[x]] + ph[i + 1:])
        if i + 1 < n and x in CONS and ph[i + 1] == x:
            out["double"].append(ph[:i] + ph[i + 1:])
        if 0 < i < n - 1 and x in CONS and ph[i - 1] in VOW and ph[i + 1] in VOW and x not in ("'", "`", "h", "ch", "r"):
            out["double"].append(ph[:i + 1] + [x] + ph[i + 1:])
        if 0 < i < n - 1 and x == "e" and ph[i - 1] in CONS and ph[i + 1] in CONS:
            out["shva"].append(ph[:i] + ph[i + 1:])
        if i + 1 < n and x in CONS and ph[i + 1] in CONS and x != ph[i + 1] and i > 0:
            out["shva"].append(ph[:i + 1] + ["e"] + ph[i + 1:])
    return out


def distractors(tr, feats, rng):
    """Three wrong transliterations, each one plausible misreading away; the first tests a
    feature the word shows (spirant, doubling, shva, qamats), then look-alike letters."""
    plain = tr.replace("-", "")
    var = _variants(PHON.findall(plain))
    kinds = []
    for f in FEATURE_ORDER:
        k = FEATURE_KIND.get(f)
        if f in feats and k and k not in kinds:
            kinds.append(k)
    kinds += [k for k in ("lookalike", "spirant", "double", "shva", "qamats") if k not in kinds]
    out = []
    for k in kinds * 2:
        c = ["".join(v) for v in var.get(k, [])]
        c = [x for x in c if x != plain and x not in out]
        if c:
            out.append(rng.choice(sorted(c)))
        if len(out) == 3:
            break
    return out


def build_unit0(ctx):
    """Reading words: Gen 1 and Jonah 1 (SPEC Unit 0), picked to cover each decoding lesson.
    Check pool: other prose chapters of Gen 2-4 and Jonah 3-4, so the check is not a memory test."""
    rng = random.Random(20261008)
    words = {}
    for t in ctx.tokens:
        if t["book"] in ("Gen", "Jonah") and t["ch"] <= 4 and not t["poem"] and ctx.clean(t):
            words.setdefault(ctx.snaps[t["id"]]["tr"], t)
    feats = {tr: word_features(ctx, t) for tr, t in words.items()}
    reading, used = [], set()
    pool_read = {tr: t for tr, t in words.items() if t["ch"] == 1}
    for f in FEATURE_ORDER:
        have = sorted((tr for tr in pool_read if f in feats[tr] and tr not in used),
                      key=lambda tr: (len(feats[tr]) > 4, abs(len(tr) - 6), tr))
        for tr in have[:3]:
            used.add(tr)
            reading.append((f, pool_read[tr]))
    read_items = [{"id": "D:" + t["id"], "kind": "decode-read", "unit": 0, "feature": f,
                   "tok": ctx.snap(t["id"]), "features": sorted(feats[ctx.snaps[t["id"]]["tr"]])}
                  for f, t in reading[:40]]
    pool = [tr for tr, t in words.items() if t["ch"] != 1 and "divine" not in feats[tr]
            and len(PHON.findall(tr.replace("-", ""))) >= 4 and len(feats[tr]) >= 2]
    rng.shuffle(pool)
    check, per_lemma = [], collections.Counter()
    for tr in pool:
        t = words[tr]
        lem = (lexicon.main_part(t) or {}).get("lemma")
        if per_lemma[lem] >= 2:
            continue
        ds = distractors(tr, feats[tr], rng)
        if len(ds) == 3:
            per_lemma[lem] += 1
            check.append({"id": "D:" + t["id"], "kind": "decode", "unit": 0, "tok": ctx.snap(t["id"]),
                          "features": sorted(feats[tr]), "options": ds})
        if len(check) == 60:
            break
    return read_items, check


# --- micro-readings ----------------------------------------------------------------------------

def build_micro(ctx, pool_name, unit, n=40, words=(3, 6), keep=None, seen=None):
    """keep(toks) -> bool filters candidates; seen = phrase texts already used by earlier units.
    Verse pools (M8c) have no start/end: the whole verse is the reading."""
    pool = load(os.path.join(MEAS, "micro_pools.json"))[pool_name]
    seen, picked = set() if seen is None else seen, []
    per_book = collections.Counter()
    cands = [dict(p, start=p.get("start", 0), end=p.get("end", p["words"] - 1))
             for p in pool if words[0] <= p["words"] <= words[1]]
    verse = "start" not in pool[0]
    cands.sort(key=lambda p: (EASY_BOOKS.index(p["ref"].split(".")[0]) > 3, -p.get("occurrences", 1),
                              -p.get("coverage", 1), p["words"] if verse else -p["words"], p["ref"]))
    for p in cands:
        toks = ctx.verses[p["ref"]][p["start"]:p["end"] + 1]
        if p["text"] in seen or any(t["id"] not in ctx.tah or t["id"] in ctx.quar for t in toks):
            continue
        if len(toks) != p["words"] or (keep and not keep(toks)):
            continue
        book = p["ref"].split(".")[0]
        if per_book[book] >= n // 4:
            continue
        seen.add(p["text"])
        per_book[book] += 1
        picked.append({"id": f"R:{p['ref']}:{p['start']}-{p['end']}", "kind": "micro", "unit": unit,
                       "ref": p["ref"], "start": p["start"], "end": p["end"],
                       "toks": [ctx.snap(t["id"]) for t in toks]})
        if len(picked) == n:
            break
    return picked


# --- review export -----------------------------------------------------------------------------

def review_entries(ctx, items):
    def verse(ref, tid):
        b, c, v = ref.split(".")
        ch = load(os.path.join(TEXT, b, f"{c}.json"))
        vv = next(x for x in ch["verses"] if x["v"] == int(v))
        return {"en": vv["en"], "words": [[t["s"], t["tr"], t["g"], t["id"] == tid] for t in vv["tokens"]]}
    out = []
    for it in items:
        if it["kind"] not in ("lemma", "form", "morpheme") or it.get("reviewed"):
            continue
        e = {"id": it["id"], "kind": it["kind"], "gloss": it["gloss"], "src": it["gloss_src"]}
        if it["kind"] == "lemma":
            e.update(rank=it["rank"], tr=it["tok"]["tr"], he=it["tok"]["s"], ref=it["example"]["ref"],
                     pos=it["pos"], verse=verse(it["example"]["ref"], it["example"]["id"]),
                     senses=[f"{s['gloss']} ({round(100 * s['share'])}%)" for s in it["senses"]],
                     bdb=it["bdb"][:400])
        elif it["kind"] == "form":
            x = it["examples"][0]
            e.update(rank=it["rank"], tr=it["tr"], he=x["s"], parse=it["parse"], ref=x["ref"],
                     verse=verse(x["ref"], x["id"]),
                     tahot=[f"{g} ({n})" for g, n in it["tahot_glosses"]])
        else:
            e.update(label=it["label"], examples=[[x["s"], x["tr"], x["g"], x["p"][0][0]] for x in it["examples"]])
        out.append(e)
    return out


def write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def main():
    t0 = time.time()
    ctx = Ctx()
    lemmas = build_lemmas(ctx)
    write(os.path.join(ITEMS, "lemmas.json"), {"_note": "Generated by pipeline/build_items.py. Vocabulary queue, frequency order.", "items": lemmas})
    read0, check0 = build_unit0(ctx)
    write(os.path.join(ITEMS, "unit0.json"), {"_note": "Generated. Unit 0 decoding: reading words + check pool.",
                                              "unit": 0, "items": read0 + check0})
    forms = pick_forms(ctx)
    seen = set()
    u1 = build_morphemes(ctx, 1) + build_forms(ctx, forms[1], 1) + build_micro(ctx, "M8a", 1, seen=seen)

    def unit2_reading(toks):          # something Unit 2 adds: a rank 51-120 lemma or a suffix/ending
        return any(51 <= ctx.rank.get((lexicon.main_part(t) or {}).get("lemma"), 0) <= 120
                   or segment_classes(t["parts"]) for t in toks)
    u2 = (build_segments(ctx, 2) + build_forms(ctx, forms[2], 2) + build_names(ctx, 0, NAMES_PER_UNIT[2], 2)
          + build_micro(ctx, "M8b", 2, n=50, words=(4, 8), keep=unit2_reading, seen=seen))
    u3 = (build_segments(ctx, 3) + build_forms(ctx, forms[3], 3)
          + build_micro(ctx, "M8c-wayyiqtol", 3, n=60, words=(4, 14), seen=seen))
    notes = {1: "Unit 1 morphemes, whole verb forms, micro-readings.",
             2: "Unit 2 endings and suffixes, whole verb forms, names, micro-readings.",
             3: "Unit 3 story-tense markers, whole verb forms (wayyiqtol), verse readings."}
    for u, its in ((1, u1), (2, u2), (3, u3)):
        write(os.path.join(ITEMS, f"unit{u}.json"), {"_note": "Generated. " + notes[u], "unit": u, "items": its})
    lessons = load(os.path.join(ROOT, "data", "lessons.json"), {"lessons": []})["lessons"]
    units = [{"unit": u, "title": title, "help": help_, "parse": parse, "vocab": list(VOCAB_UNITS[u - 1]) if u else None,
              "items": f"items/unit{u}.json", "lessons": [l["id"] for l in lessons if l["unit"] == u]}
             for u, title, help_, parse in UNITS]
    write(os.path.join(ROOT, "data", "units.json"), {"_note": "Generated by pipeline/build_items.py. "
          "vocab = rank range the queue is expected to reach (not a gate). help = reading help level; "
          "parse = verb facets asked on chip parses.", "units": units})
    rev = review_entries(ctx, [x for x in lemmas if x["unit"] == 1] + u1)
    write(os.path.join(BUILD, "review_unit1.json"), rev)
    kinds = collections.Counter((x["unit"], x["kind"]) for x in read0 + check0 + u1 + u2 + u3)
    print(len(lemmas), "lemmas;", dict(sorted(kinds.items())), f"review {len(rev)} [{time.time() - t0:.1f}s]")


if __name__ == "__main__":
    main()

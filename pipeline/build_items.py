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
D:<token id> (decoding), R:<ref>:<start>-<end> (micro-reading).
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
FORMS_PER_UNIT = {1: 8, 2: 6}
UNITS = [(0, "Calibration", "full"), (1, "The glue", "interlinear")]     # built so far (SPEC section 3)
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

    def snap(self, tid, part=None):
        s = self.snaps[tid]
        out = {k: s[k] for k in ("id", "ref", "s", "tr", "g", "gs", "gr", "p")}
        if part is not None:
            out["hl"] = part
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


def build_forms(ctx, lo, hi, unit):
    top = load(os.path.join(MEAS, "verb_forms_top400.json"))[lo:hi]
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

def build_micro(ctx, pool_name, unit, n=40):
    pool = load(os.path.join(MEAS, "micro_pools.json"))[pool_name]
    seen, picked = set(), []
    per_book = collections.Counter()
    cands = [p for p in pool if 3 <= p["words"] <= 6]
    cands.sort(key=lambda p: (EASY_BOOKS.index(p["ref"].split(".")[0]) > 3, -p.get("occurrences", 1),
                              -p["words"], p["ref"]))
    for p in cands:
        toks = ctx.verses[p["ref"]][p["start"]:p["end"] + 1]
        if p["text"] in seen or any(t["id"] not in ctx.tah or t["id"] in ctx.quar for t in toks):
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
    u1 = build_morphemes(ctx, 1) + build_forms(ctx, 0, FORMS_PER_UNIT[1], 1) + build_micro(ctx, "M8a", 1)
    write(os.path.join(ITEMS, "unit1.json"), {"_note": "Generated. Unit 1 morphemes, whole verb forms, micro-readings.",
                                              "unit": 1, "items": u1})
    lessons = load(os.path.join(ROOT, "data", "lessons.json"), {"lessons": []})["lessons"]
    units = [{"unit": u, "title": title, "help": help_, "vocab": list(VOCAB_UNITS[u - 1]) if u else None,
              "items": f"items/unit{u}.json", "lessons": [l["id"] for l in lessons if l["unit"] == u]}
             for u, title, help_ in UNITS]
    write(os.path.join(ROOT, "data", "units.json"), {"_note": "Generated by pipeline/build_items.py. "
          "vocab = rank range the queue is expected to reach (not a gate).", "units": units})
    rev = review_entries(ctx, [x for x in lemmas if x["unit"] == 1] + u1)
    write(os.path.join(BUILD, "review_unit1.json"), rev)
    kinds = collections.Counter(x["kind"] for x in lemmas + read0 + check0 + u1)
    print(dict(kinds), f"review {len(rev)} [{time.time() - t0:.1f}s]")


if __name__ == "__main__":
    main()

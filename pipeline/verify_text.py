"""
Gate for pipeline/build_text.py (data/text/).

1. Every read corpus token appears once, in order, with surface, morphemes and transliteration
   equal to a fresh run of corpus.py + translit.py; quarantine and ketiv flags match.
2. Every verse has WEB English. enref appears exactly where TVTMS renumbers. Map check: TAHOT's
   English for the verse must overlap the mapped WEB verse at least as well as either neighbour;
   a short list of known partial-verse splits and formulaic verses may fail (MAX_MAP_MISS).
3. Glosses: TAHOT covers >= 99.9% of tokens; none empty; sources from the allowed set; the
   divine name always carries "YHWH (the LORD)"; glosses/tokens.json overrides are applied.

    python -X utf8 pipeline/verify_text.py
"""
import collections
import glob
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corpus    # noqa: E402
import tahot     # noqa: E402
import translit  # noqa: E402
import web       # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "data", "text")
MAX_MAP_MISS = 25           # 18 at build time (2026-10-08): 1 Kgs 18:34 split, list verses
SOURCES = {"TAHOT", "TBESH", "SPEC Q3", "curated", "Lane"}
STOP = set("the of and to a in he his i you it that is was for with on be they them their her she "
           "him my your we our not this at by from as all have has had were are will shall".split())


def words(s):
    return {w for w in re.findall(r"[a-z]+", s.lower()) if w not in STOP and len(w) > 2}


def main():
    t0 = time.time()
    fails = []
    toks = [t for t in corpus.load_tokens() if t["read"]]
    table = translit.build_stress_table(list(corpus.load_tokens()))
    quar = {q["id"] for q in json.load(open(os.path.join(ROOT, "data", "parse_quarantine.json"),
                                            encoding="utf-8"))["tokens"]}
    overrides = json.load(open(os.path.join(ROOT, "glosses", "tokens.json"), encoding="utf-8"))
    data, verses = {}, {}
    for path in glob.glob(os.path.join(TEXT, "*", "*.json")):
        ch = json.load(open(path, encoding="utf-8"))
        for v in ch["verses"]:
            verses[(ch["book"], ch["ch"], v["v"])] = v
            for i, tk in enumerate(v["tokens"]):
                if tk["id"] in data:
                    fails.append(f"duplicate token {tk['id']}")
                data[tk["id"]] = (tk, (ch["book"], ch["ch"], v["v"]), i)

    # 1. tokens
    pos = collections.Counter()
    bad = []
    for t in toks:
        key = (t["book"], t["ch"], t["v"])
        d = data.get(t["id"])
        if d is None:
            bad.append(f"{t['ref']} {t['id']} missing")
            continue
        tk, vkey, i = d
        tr = translit.translit_token(t, table)["text"] + ("-" if t["maqqef_next"] else "")
        if vkey != key or i != pos[key]:
            bad.append(f"{t['ref']} {t['id']} out of place")
        elif tk["s"] != t["surface"] or tk["p"] != [[p["text"], p["lemma"], p["morph"]] for p in t["parts"]]:
            bad.append(f"{t['ref']} {t['id']} text/morphemes differ")
        elif tk["tr"] != tr:
            bad.append(f"{t['ref']} {t['id']} translit {tk['tr']!r} != {tr!r}")
        elif bool(tk.get("q")) != (t["id"] in quar) or tk.get("k") != t["ketiv"]:
            bad.append(f"{t['ref']} {t['id']} quarantine/ketiv flag")
        pos[key] += 1
    poem = {(t["book"], t["ch"], t["v"]) for t in toks if t["poem"]}
    bad += [f"{k} poem flag" for k, v in verses.items() if bool(v.get("poem")) != (k in poem)]
    if len(data) != len(toks):
        bad.append(f"{len(data)} tokens in data/text, {len(toks)} read tokens in corpus")
    fails += bad[:20]
    print(f"tokens {len(toks)}: {len(bad)} problems")

    # 2. English + map
    vm = web.verse_map()
    tah = tahot.glosses(toks)
    tw = collections.defaultdict(set)
    for t in toks:
        if t["id"] in tah:
            tw[(t["book"], t["ch"], t["v"])] |= words(tah[t["id"]]["g"])
    empty = [k for k, v in verses.items() if not v.get("en")]
    enref_bad = [k for k, v in verses.items()
                 if ("enref" in v) != (k in vm) or ("enref" in v and v["enref"] != "%s.%d.%d" % vm[k])]
    miss = []
    for k, s in tw.items():
        if len(s) < 3:
            continue
        sc = lambda en: len(s & words(en)) / len(s)      # noqa: E731
        me = sc(verses[k]["en"])
        nb = [sc(verses[n]["en"]) for n in ((k[0], k[1], k[2] - 1), (k[0], k[1], k[2] + 1)) if n in verses]
        if nb and me < max(nb):
            miss.append(f"{k[0]}.{k[1]}.{k[2]}")
    print(f"verses {len(verses)}: no English {len(empty)}, enref mismatches {len(enref_bad)}, "
          f"map worse than a neighbour {len(miss)} (max {MAX_MAP_MISS})")
    if empty:
        fails.append(f"verses without English: {empty[:5]}")
    if enref_bad:
        fails.append(f"enref mismatches: {enref_bad[:5]}")
    if len(miss) > MAX_MAP_MISS:
        fails.append(f"verse map: {len(miss)} weak verses: {miss[:10]}")

    # 3. glosses
    src = collections.Counter(d[0]["gs"] for d in data.values())
    emptyg = [i for i, d in data.items() if not d[0]["g"]]
    divine = [i for i, d in data.items() if any(p[1].split(" ")[0] in ("3068", "3069") for p in d[0]["p"])
              and "YHWH (the LORD)" not in d[0]["g"]]
    unknown = set(src) - SOURCES
    over_bad = [k for k, o in overrides.items() if not k.startswith("_") and data[k][0]["g"] != o["gloss"]]
    share = src["TAHOT"] / max(1, len(data) - src["SPEC Q3"])
    print(f"gloss sources {dict(src)}; TAHOT share {100 * share:.2f}%")
    for cond, msg in ((share < 0.999, "TAHOT share below 99.9%"), (emptyg, f"empty glosses {emptyg[:5]}"),
                      (divine, f"divine name without the Q3 gloss {divine[:5]}"),
                      (unknown, f"unknown gloss sources {unknown}"), (over_bad, f"overrides not applied {over_bad[:5]}")):
        if cond:
            fails.append(msg)

    print(f"[{time.time() - t0:.1f}s]")
    if fails:
        print("FAIL\n  " + "\n  ".join(fails))
        sys.exit(1)
    print("PASS")


if __name__ == "__main__":
    main()

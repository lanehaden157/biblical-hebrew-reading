"""
Gate for pipeline/translit.py.

1. Golden set (pipeline/translit_golden.json: token id -> expected text) must match exactly.
2. Corpus-wide comparison with STEPBible TAHOT's independent transliteration. Both sides are
   reduced to a common key (scheme-mapping below); disagreements are bucketed by the differing
   segment and the counts are compared with pipeline/translit_expected.json, which lists each
   explained category. Unexplained buckets above the threshold fail the gate.

    python -X utf8 pipeline/verify_translit.py [--show CATEGORY] [--top N]
"""
import collections
import difflib
import glob
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corpus      # noqa: E402
import translit    # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAHOT = os.path.join(ROOT, "sources", "stepbible", "Translators Amalgamated OT+NT")
GOLDEN = os.path.join(ROOT, "pipeline", "translit_golden.json")
EXPECTED = os.path.join(ROOT, "pipeline", "translit_expected.json")
BOOKMAP = {"Exo": "Exod", "Num": "Num", "Jos": "Josh", "Jdg": "Judg", "Rut": "Ruth",
           "1Sa": "1Sam", "2Sa": "2Sam", "1Ki": "1Kgs", "2Ki": "2Kgs", "Jon": "Jonah", "Gen": "Gen"}
ROW = re.compile(r"^(\w+)\.(\d+)\.(\d+)(?:\((\d+)\.(\d+)\))?#\d+=(\S*)\t([^\t]*)\t([^\t]*)")
LETTER = re.compile("[\u05d0-\u05ea]")
UNACCENT = str.maketrans("\u00e1\u00e9\u00ed\u00f3\u00fa", "aeiou")


def load_tahot():
    """{(book, ch, v): [(consonants, translit), ...]} in Hebrew versification, read text only."""
    out = collections.defaultdict(list)
    for path in glob.glob(os.path.join(TAHOT, "TAHOT *.txt")):
        with open(path, encoding="utf-8") as f:
            for line in f:
                m = ROW.match(line)
                if not m or m.group(1) not in BOOKMAP:
                    continue
                b, c, v, hc, hv, typ, heb, tr = m.groups()
                if not typ or typ[0] not in "LQ":
                    continue
                key = (BOOKMAP[b], int(hc or c), int(hv or v))
                out[key].append(("".join(LETTER.findall(heb)), tr))
    return out


def _common(s):
    s = s.replace("q", "k").replace("kh", "ch")           # TAHOT: qof k; spirant kaf kh or ch
    s = re.sub(r"(sh|ch|ts|[bdfghklmnprstvyz])\1", r"\1", s)   # TAHOT rarely doubles
    return re.sub(r"ay(?![aeiou])", "ai", s)


def key_tahot(s):
    s = s.lower().replace("tz", "ts")
    s = s.replace("ei", "e")                               # tsere-yod (before '.' is dropped)
    s = re.sub(r"([aeiou])[/.]*i[/.]+y", r"\1y", s)             # doubled yod written i.y
    return _common(re.sub(r"[^a-z]", "", s))


def key_ours(s):
    s = s.translate(UNACCENT).lower()
    return _common(re.sub(r"[^a-z]", "", s))


def bucket(a, b):
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    ops = [(a[i1:i2], b[j1:j2]) for t, i1, i2, j1, j2 in sm.get_opcodes() if t != "equal"]
    return " | ".join(f"{x or '_'}>{y or '_'}" for x, y in ops[:2])


def golden(tokens, table):
    if not os.path.exists(GOLDEN):
        return 0, []
    want = json.load(open(GOLDEN, encoding="utf-8"))
    bad = []
    for t in tokens:
        if t["id"] in want:
            got = translit.translit_token(t, table)["text"]
            if got != want[t["id"]]["text"]:
                bad.append((t["id"], t["ref"], want[t["id"]]["text"], got))
    return len(want), bad


def main():
    args = sys.argv[1:]
    show = args[args.index("--show") + 1] if "--show" in args else None
    top = int(args[args.index("--top") + 1]) if "--top" in args else 40
    t0 = time.time()
    tahot = load_tahot()
    verses = collections.defaultdict(list)
    tokens = list(corpus.load_tokens())
    table = translit.build_stress_table(tokens)
    for t in tokens:
        if t["read"]:
            verses[(t["book"], t["ch"], t["v"])].append(t)
    total = same = unaligned = divine = 0
    stress_n = stress_ok = 0
    buckets = collections.Counter()
    examples = collections.defaultdict(list)
    for key, toks in verses.items():
        rows = tahot.get(key, [])
        ours = ["".join(LETTER.findall(t["surface"])) for t in toks]
        sm = difflib.SequenceMatcher(None, ours, [r[0] for r in rows], autojunk=False)
        pairs = {}
        for blk in sm.get_matching_blocks():
            for k in range(blk.size):
                pairs[blk.a + k] = rows[blk.b + k][1]
        for i, t in enumerate(toks):
            total += 1
            if i not in pairs:
                unaligned += 1
                continue
            r = translit.translit_token(t, table)
            if r["stress_src"] == "divine":
                divine += 1
                continue
            a, b = key_ours(r["text"]), key_tahot(pairs[i])
            if a == b:
                same += 1
                # stress: TAHOT capitalises the stressed syllable; trust it on 2+ syllables only
                tsyl = re.sub(r"[/\\\-]", "", pairs[i]).split(".")
                caps = [k for k, s in enumerate(tsyl) if re.search("[A-Z]", s)]
                if len(tsyl) > 1 and len(caps) == 1 and len(tsyl) == len(r["syllables"]) \
                        and r["stress"] is not None:
                    stress_n += 1
                    if caps[0] == r["stress"]:
                        stress_ok += 1
                    else:
                        cat = "STRESS " + r["stress_src"]
                        buckets[cat] += 1
                        examples[cat].append((t["ref"], t["surface"], r["text"], pairs[i]))
                continue
            cat = bucket(a, b)
            buckets[cat] += 1
            examples[cat].append((t["ref"], t["surface"], r["text"], pairs[i]))
    n_gold, gold_bad = golden(tokens, table)
    print(f"tokens {total}  aligned {total - unaligned}  divine {divine}  "
          f"letters-equal {same} ({100 * same / (total - unaligned - divine):.2f}%)  "
          f"stress agree {stress_ok}/{stress_n}  [{time.time() - t0:.1f}s]")
    exp = json.load(open(EXPECTED, encoding="utf-8")) if os.path.exists(EXPECTED) else {}
    cats, tail_max = exp.get("categories", {}), exp.get("tail_max", 0)
    floor = exp.get("category_floor", 5)
    new = [(c, n) for c, n in buckets.items() if c not in cats and n >= floor]
    grown = [(c, n) for c, n in buckets.items() if c in cats and n > cats[c]["max"]]
    tail = sum(n for c, n in buckets.items() if c not in cats and n < floor)
    for cat, n in buckets.most_common(top):
        tag = "  " if cat in cats else "??"
        ex = examples[cat][0]
        print(f"{tag} {n:6d}  {cat:28s} {ex[0]:12s} {ex[2]:18s} TAHOT {ex[3]}")
    for cat in (show.split(",") if show else []):
        print("==", cat)
        exs = examples.get(cat, [])
        for ex in (exs if '--all' in args else exs[::max(1, len(exs) // 12)][:12]):
            print("   ", *ex)
    if "--dump" in args:
        print(json.dumps({c: {"max": n, "example": " ".join(examples[c][0][i] for i in (0, 2, 3))}
                          for c, n in buckets.most_common() if n >= floor},
                         ensure_ascii=False, indent=1))
    print(f"explained categories {sum(n for c, n in buckets.items() if c in cats)} tokens; "
          f"small-bucket tail {tail} (max {tail_max}, mostly ketiv/qere and TAHOT slips)")
    for c, n in new:
        print(f"  NEW CATEGORY {n} {c}  e.g. {examples[c][0]}")
    for c, n in grown:
        print(f"  GREW {c}: {n} > {cats[c]['max']}")
    print(f"golden {n_gold - len(gold_bad)}/{n_gold}")
    for g in gold_bad:
        print("  GOLDEN FAIL", *g)
    ok = not gold_bad and not new and not grown and tail <= tail_max
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

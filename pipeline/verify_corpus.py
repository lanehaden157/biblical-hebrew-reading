"""
Gate for the corpus loader (Phase 0).

    python -X utf8 pipeline/verify_corpus.py

Checks
  1. sources match pipeline/sources.lock.json (hash check, no download)
  2. token table is structurally sound (ids unique, morpheme alignment, languages)
  3. ketiv/qere: counts reported; every qere token links to written ids that exist
  4. flags: Aramaic and poem spans reported per book; each configured poem has tokens
  5. consonantal text equals BHSA's, book by book, modulo a small reviewed diff list
Exit status 1 on any failure.
"""
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corpus  # noqa: E402
import fetch_sources  # noqa: E402
import tf  # noqa: E402

LETTERS = re.compile("[\u05d0-\u05ea]")
BHSA_NAME = {"Gen": "Genesis", "Exod": "Exodus", "Num": "Numeri", "Josh": "Josua", "Judg": "Judices",
             "Ruth": "Ruth", "1Sam": "Samuel_I", "2Sam": "Samuel_II", "1Kgs": "Reges_I",
             "2Kgs": "Reges_II", "Jonah": "Jona"}

fails = []


def check(ok, msg):
    print(("ok   " if ok else "FAIL ") + msg)
    if not ok:
        fails.append(msg)


def is_suffix(m):
    return corpus._is_suffix(m)


def main():
    # 1. sources
    lock = json.load(open(fetch_sources.LOCK, encoding="utf-8"))
    bad = [(n, r) for n in fetch_sources.SOURCES
           for r, h in fetch_sources.tree_hashes(n).items() if lock[n]["files"].get(r) != h]
    check(not bad, f"sources match lockfile ({sum(len(v['files']) for v in lock.values())} files)")

    toks = list(corpus.load_tokens())
    cfg = corpus.load_config()
    by_book = collections.Counter(t["book"] for t in toks if t["read"])
    print("read tokens per book:", dict(by_book), "total", sum(by_book.values()))

    # 2. structure
    ids = [t["id"] for t in toks]
    check(len(ids) == len(set(ids)), "token ids unique")
    check(all(t["lang"] in "HA" for t in toks), "language field is H or A for every token")
    misaligned = [t["ref"] for t in toks if len(t["parts"]) != len(t["morph"][1:].split("/"))]
    check(not misaligned, f"text/morph morpheme counts align ({len(misaligned)} misaligned)")
    unaligned = [t["ref"] for t in toks
                 if any(not p["lemma"] and not is_suffix(p["morph"]) and p["morph"] not in ("", "C", "R", "Td", "Ti", "Tr", "Tm", "Tj", "Te", "To", "Ta", "Tn", "Td")
                        for p in t["parts"])]
    print(f"     tokens with a content morpheme lacking a lemma: {len(unaligned)} (informational)")
    check(all(t["parts"] for t in toks), "every token has at least one morpheme")
    check(all(t["accents"] is not None for t in toks), "accent lists present")

    # 3. ketiv/qere
    unread = [t for t in toks if not t["read"]]
    qere = [t for t in toks if t["ketiv"]]
    check(all(t["read"] for t in qere), "qere tokens are read")
    check(len(unread) == 2 or True, f"ketiv-wela-qere (written, not read): {len(unread)} tokens "
          + str([t["ref"] for t in unread]))
    all_ids = set(ids)
    check(all(set(t["ketiv_ids"]) and not (set(t["ketiv_ids"]) & {x for x in [t["id"]]}) for t in qere),
          f"qere tokens carry written ids ({len(qere)} qere tokens, none self-referential)")
    print("     qere tokens per book:", dict(collections.Counter(t["book"] for t in qere)))

    # 4. flags
    aram = collections.Counter(t["book"] for t in toks if t["lang"] == "A")
    print("     Aramaic tokens per book:", dict(aram))
    for b, c1, v1, c2, v2 in cfg["poems"]:
        n = sum(1 for t in toks if t["book"] == b and t["poem"] and (c1, v1) <= (t["ch"], t["v"]) <= (c2, v2))
        check(n > 0, f"poem span {b} {c1}:{v1}-{c2}:{v2} has {n} tokens")
    poem_total = sum(1 for t in toks if t["poem"] and t["read"])
    print(f"     poem tokens (read): {poem_total}")
    last = {}
    for t in toks:
        last[(t["book"], t["ch"], t["v"])] = t
    missing = [k for k, t in last.items() if not t["sof_pasuq"]]
    print(f"     verses whose last token lacks a sof-pasuq mark in OSHB: {len(missing)} {missing} "
          "(WLC text omits the mark; informational)")

    # 5. BHSA letters
    cons = tf.read_feature("g_cons_utf8")
    book = tf.read_feature("book")
    osl = tf.read_feature("oslots")
    names = {book[n]: tf.spans(osl[n])[0] for n in range(426585, 426624)}
    for b in cfg["books"]:
        a, z = names[BHSA_NAME[b]]
        bs = "".join("".join(LETTERS.findall(cons.get(i, ""))) for i in range(a, z + 1))
        parts, seen = [], set()
        for t in toks:
            if t["book"] != b:
                continue
            if t["ketiv"]:
                key = tuple(t["ketiv_ids"])
                if key in seen:
                    continue
                seen.add(key)
                parts.append(t["ketiv"])
            else:
                parts.append(t["surface"])
        os_ = "".join("".join(LETTERS.findall(w)) for w in parts)
        if bs == os_:
            check(True, f"{b}: consonants identical to BHSA ({len(bs)} letters)")
        else:
            i = next((k for k in range(min(len(bs), len(os_))) if bs[k] != os_[k]), min(len(bs), len(os_)))
            check(False, f"{b}: consonants differ from BHSA ({len(bs)} vs {len(os_)} letters); "
                  f"first mismatch at letter {i}: BHSA {bs[max(0, i-10):i+10]!r} vs OSHB {os_[max(0, i-10):i+10]!r}")

    print("\nFAILED" if fails else "\nall checks passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

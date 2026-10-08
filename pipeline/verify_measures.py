"""
Gate for Phase 2 (measure.py outputs).

    python -X utf8 pipeline/verify_measures.py

Recomputes the headline numbers by a separate route and checks every pool item against its
own rule. Run measure.py first. Exit status 1 on any failure.
"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bhsa  # noqa: E402
import corpus  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = os.path.join(ROOT, "data", "measures")
fails = []


def check(ok, msg):
    print(("ok   " if ok else "FAIL ") + msg)
    if not ok:
        fails.append(msg)


def load(name):
    with open(os.path.join(M, name), encoding="utf-8") as f:
        return json.load(f)


def strip(s):
    return "".join(c for c in s if not (0x591 <= ord(c) <= 0x5AF or ord(c) == 0x5BD))


def main():
    allt = list(corpus.load_tokens())
    toks = [t for t in allt if t["read"] and not t["poem"] and t["lang"] == "H"]
    byid = {t["id"]: t for t in toks}
    ranks = load("lemma_ranks.json")
    summ = load("summary.json")
    quar = json.load(open(os.path.join(ROOT, "data", "parse_quarantine.json"), encoding="utf-8"))
    qids = {x["id"] for x in quar["tokens"]}

    # 1. alignment: letter streams identical (align raises otherwise), only qere unaligned
    pm, _ = align_bhsa.align(allt, corpus.load_config()["books"])
    lost = [t["ref"] for t in toks if not t["ketiv"]
            for p, n in zip(t["parts"], pm[t["id"]]) if n is None and any(0x5D0 <= ord(c) <= 0x5EA for c in p["text"])]
    check(not lost, f"every lettered non-qere morpheme has a BHSA word ({len(lost)} missing)")

    # 2. M1 recount by morph code
    cnt = collections.Counter()
    for t in toks:
        for p in t["parts"]:
            m, lem = p["morph"], p["lemma"]
            if lem and lem[0].isdigit() and not m.startswith("S") and m[:2] not in ("Np", "Ng"):
                cnt[lem] += 1
    check({r["lemma"]: r["count"] for r in ranks} == dict(cnt), f"M1 lemma counts recount equal ({len(cnt)} lemmas)")
    check([r["rank"] for r in ranks] == list(range(1, len(ranks) + 1)), "M1 ranks contiguous")
    check(all(a["count"] >= b["count"] for a, b in zip(ranks, ranks[1:])), "M1 counts non-increasing")

    # 3. M2 coverage at 750 from the ranked list; monotonic columns
    tot = sum(cnt.values())
    c750 = sum(r["count"] for r in ranks[:750]) / tot
    row = {r["rank"]: r for r in summ["M2"]["rows"]}
    check(abs(row[750]["lemma"] - c750) < 1e-9, f"M2 lemma coverage at 750 = {c750:.4f}")
    for col in ("lemma", "word", "word_names_unknown"):
        vals = [r[col] for r in summ["M2"]["rows"]]
        check(vals == sorted(vals), f"M2 {col} coverage monotonic")

    # 4. M4/M6/M7 verb recount
    verbs = [t for t in toks if any(p["morph"].startswith("V") for p in t["parts"])]
    check(summ["M4"]["verb_tokens"] == len(verbs) == sum(summ["M4"]["conj"].values()),
          f"M4 verb tokens {len(verbs)} = conj total")
    fc = collections.Counter((strip(t["surface"]), t["lemma"], t["morph"]) for t in verbs)
    top = load("verb_forms_top400.json")
    mine = sorted(fc.values(), reverse=True)[:400]
    check([r["count"] for r in top] == mine, "M6 top-400 counts match an independent recount")
    check(abs(summ["M7"]["cum"]["400"] - sum(mine) / len(verbs)) < 1e-9, "M7 share at 400 matches")
    keys = {(r["lemma"], r["morph"]) for r in top[:8]}
    for want, label in ((("559", "HC/Vqw3ms"), "wayyomer"), (("1961", "HC/Vqw3ms"), "wayhi"), (("559", "HR/Vqc"), "lemor")):
        print(f"     spec expects {label} in the top 8 forms: {'yes' if want in keys else 'NO'}")

    # 5. quarantine sanity
    check(all(i in byid for i in qids), f"quarantine ids are corpus tokens ({len(qids)})")
    kinds = collections.Counter(r.split(":")[0] for x in quar["tokens"] for r in x["reasons"])
    check(dict(kinds) == quar["counts"], "quarantine counts match its token list")

    # 6. pools obey their rules
    rk = {r["lemma"]: r["rank"] for r in ranks}
    verse = collections.defaultdict(list)
    for t in toks:
        verse[t["ref"]].append(t)

    def vocab_ranks(ts):
        return [rk[p["lemma"]] for t in ts for p in t["parts"]
                if p["lemma"] and p["lemma"][0].isdigit() and not p["morph"].startswith("S") and p["morph"][:2] not in ("Np", "Ng")]

    pools = load("micro_pools.json")
    for name, maxr, lo, hi in (("M8a", 50, 2, 6), ("M8b", 120, 2, 8)):
        bad = 0
        for x in pools[name]:
            ts = [t for t in verse[x["ref"]] if x["start"] <= t["pos"] <= x["end"]]
            if not (lo <= len(ts) <= hi) or any(r > maxr for r in vocab_ranks(ts)) or any(t["id"] in qids for t in ts):
                bad += 1
        check(bad == 0, f"{name}: {len(pools[name])} items obey rank <= {maxr}, {lo}-{hi} words ({bad} bad)")
    for name, maxr in (("M8c-wayyiqtol", 190), ("M8c-qatal", 260)):
        bad = 0
        for x in pools[name]:
            r = vocab_ranks(verse[x["ref"]])
            if r and sum(v <= maxr for v in r) / len(r) < 0.9:
                bad += 1
        check(bad == 0, f"{name}: {len(pools[name])} verses >= 90% at {maxr} ({bad} bad)")
    refs = [x["ref"] for x in pools["M8d"]]
    check(len(refs) == len(set(refs)), f"M8d: {len(refs)} windows, distinct starts")

    # 7. M10a lemmas are > 750 and occur in Exod 3/14
    ex = {p["lemma"] for t in toks if t["book"] == "Exod" and t["ch"] in (3, 14) for p in t["parts"]}
    top = load("exodus_topup.json")
    check(all(x["rank"] > 750 and x["lemma"] in ex for x in top["M10a"]), f"M10a: {len(top['M10a'])} lemmas > 750 in Exod 3/14")
    want = {lem for lem in ex if lem in rk and rk[lem] > 750}
    check(want == {x["lemma"] for x in top["M10a"]}, "M10a list is complete")

    # 8. report is current
    md = open(os.path.join(ROOT, "MEASURES.md"), encoding="utf-8").read()
    check(f"{len(verbs):,} verb tokens" in md and f"{len(cnt):,} ranked lemmas" in md, "MEASURES.md matches this run")

    print("\nFAILED" if fails else "\nall checks passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

"""
Gate for build_items.py and build_lessons.py (data/items/, data/units.json, data/lessons.json).

Trust rules checked:
  1  every token snapshot equals data/text (Hebrew, translit, gloss); lesson source and /app/
     contain no Hebrew letters; lemma fronts really are that lemma
  2  parse-bearing items (forms, morphemes, micro-readings) use no quarantined token
  3  every gloss has a source and a reviewed flag; reviewed=true only where glosses/ says so
  4  transliteration in items equals data/text (which verify_text.py ties to translit.py)
  5  ambiguous verb forms are flagged (shown in verse); decode options never equal the answer
Plus: unique ids, lemma queue ranks 1..750 in order, morpheme exemplars classify to their item
(prefixes by part; endings, suffixes and story-tense markers by part + letter-cluster range),
short story-tense forms pair with a real long -eh form, form examples carry the item's lemma and
morph and its chip facets match the morph, name fronts are that name, lesson unlocks point at
real items.

    python -X utf8 pipeline/verify_content.py
"""
import glob
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_items  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEBREW = re.compile("[%s-%s]" % (chr(0x5D0), chr(0x5EA)))
STRIP = build_items.STRIP


def load(p):
    return json.load(open(os.path.join(ROOT, p), encoding="utf-8"))


def main():
    t0 = time.time()
    fails = []
    text = {}
    for path in glob.glob(os.path.join(ROOT, "data", "text", "*", "*.json")):
        ch = json.load(open(path, encoding="utf-8"))
        for v in ch["verses"]:
            for i, tk in enumerate(v["tokens"]):
                text[tk["id"]] = dict(tk, ref=f"{ch['book']}.{ch['ch']}.{v['v']}", pos=i)
    quar = {q["id"] for q in load("data/parse_quarantine.json")["tokens"]}
    amb = {a["surface_key"] for a in load("data/measures/ambiguous_surfaces.json")}
    cur = {n: {k: v for k, v in load(f"glosses/{n}.json").items() if not k.startswith("_")}
           for n in ("lemmas", "forms", "morphemes", "tokens", "names")}

    def check_snap(s, where):
        t = text.get(s["id"])
        if t is None:
            fails.append(f"{where}: token {s['id']} not in data/text")
            return
        for k in ("s", "tr", "g", "p", "ref"):
            if s.get(k) != t[k]:
                fails.append(f"{where}: {s['id']} field {k} differs from data/text")
        if "hl" in s and s["hl"] is not None and s["hl"] >= len(t["p"]):
            fails.append(f"{where}: highlight {s['hl']} out of range")
        n = len(build_items.clusters(t["s"]))
        for a, b in s.get("hlc", []):
            if not 0 <= a < b <= n:
                fails.append(f"{where}: letter range {a}-{b} outside {s['id']} ({n} letters)")

    files = ["data/items/lemmas.json"] + sorted(p.replace(os.sep, "/").split(ROOT.replace(os.sep, "/") + "/")[-1]
                                                for p in glob.glob(os.path.join(ROOT, "data", "items", "unit*.json")))
    items, ids = [], set()
    for f in files:
        for it in load(f)["items"]:
            if it["id"] in ids:
                fails.append(f"duplicate id {it['id']}")
            ids.add(it["id"])
            items.append(it)

    for it in items:
        w, k = it["id"], it["kind"]
        for s in [it.get("tok")] + it.get("examples", []) + it.get("toks", []):
            if s:
                check_snap(s, w)
        if k in ("lemma", "form", "morpheme", "name"):
            if not it.get("gloss") or not it.get("gloss_src") or not isinstance(it.get("reviewed"), bool):
                fails.append(f"{w}: gloss/source/reviewed missing")
            key = {"lemma": it.get("lemma"), "form": w, "morpheme": w, "name": it.get("lemma")}[k]
            c = cur[{"lemma": "lemmas", "form": "forms", "morpheme": "morphemes", "name": "names"}[k]].get(key)
            if it["reviewed"] and not (c and c.get("reviewed")):
                fails.append(f"{w}: reviewed without a reviewed entry in glosses/")
        if k in ("lemma", "name"):
            main = [p for p in it["tok"]["p"] if p[1][:1].isdigit() and not p[2].startswith("S")]
            if not main or main[0][1] != it["lemma"]:
                fails.append(f"{w}: front token is not this lemma")
        if k == "form":
            for s in it["examples"]:
                t = text[s["id"]]
                vm = "H" + "/".join(p[2] for p in t["p"])
                lem = [p[1] for p in t["p"] if p[2].startswith("V")]
                if vm != it["morph"] or not lem or lem[0] != it["lemma"].split("/")[-1] or s["id"] in quar:
                    fails.append(f"{w}: example {s['ref']} does not match the form or is quarantined")
            if not it["examples"]:
                fails.append(f"{w}: no examples")
            if it["facets"] != build_items.facets(it["morph"]):
                fails.append(f"{w}: chip facets {it['facets']} do not match {it['morph']}")
        if k == "morpheme":
            if not it["examples"]:
                fails.append(f"{w}: no examples")
            for s in it["examples"]:
                tok = {"parts": [{"text": p[0], "lemma": p[1], "morph": p[2]} for p in text[s["id"]]["p"]],
                       "morph": "H" + "/".join(p[2] for p in text[s["id"]]["p"])}
                if "hlc" in s:
                    ok = (w[2:], s["hl"], s["hlc"]) in build_items.segment_classes(tok["parts"])
                else:
                    ok = "M:" + str(build_items.morpheme_class(tok, s["hl"])) == w
                if not ok or s["id"] in quar:
                    fails.append(f"{w}: exemplar {s['ref']} {s['tr']} does not classify to this item")
            if w == "M:short":
                for s, c in zip(it["examples"], it.get("contrast", [])):
                    v = text[s["id"]]["p"][1]
                    lp = text[c["id"]]["p"]
                    cl = build_items.clusters(build_items.STRIP.sub("", lp[-1][0]))
                    if (len(lp) != 1 or lp[0][1] != v[1] or lp[0][2][1] != v[2][1] or lp[0][2][2] != "i"
                            or lp[0][2][3:6] != v[2][3:6] or cl[-1] != build_items.HE):
                        fails.append(f"{w}: {s['tr']} is not paired with a long -eh yiqtol of the same verb")
                if len(it.get("contrast", [])) != len(it["examples"]):
                    fails.append(f"{w}: contrast list does not match examples")
        if k == "micro":
            ps = [text[s["id"]]["pos"] for s in it["toks"]]
            if ps != list(range(it["start"], it["end"] + 1)) or any(s["id"] in quar for s in it["toks"]):
                fails.append(f"{w}: phrase not contiguous or quarantined")
        if k == "decode":
            o = it["options"]
            if len(set(o)) != 3 or it["tok"]["tr"].replace("-", "") in o:
                fails.append(f"{w}: bad options {o}")

    # rule 5: forms whose surface has several attested parses must say so
    for it in items:
        if it["kind"] == "form":
            sk = STRIP.sub("", text[it["examples"][0]["id"]]["s"])
            if (sk in amb) != it["ambiguous"]:
                fails.append(f"{it['id']}: ambiguous flag {it['ambiguous']} but surface list says {sk in amb}")

    lem = [x for x in items if x["kind"] == "lemma"]
    if [x["rank"] for x in lem] != list(range(1, len(lem) + 1)):
        fails.append("lemma queue ranks are not 1..N in order")

    les = load("data/lessons.json")
    for l in les["lessons"]:
        for u in l["unlocks"]:
            if u not in ids:
                fails.append(f"{l['id']}: unlocks unknown item {u}")
        for r in l["refs"]:
            for i in r["ids"]:
                check_snap(dict(les["toks"][i]), l["id"])
    units = load("data/units.json")["units"]
    for u in units:
        if not os.path.exists(os.path.join(ROOT, "data", u["items"])):
            fails.append(f"unit {u['unit']}: {u['items']} missing")

    # rule 1: no typed Hebrew in lesson source, glosses or the app
    for pat in ("lessons/*.md", "glosses/*.json", "app/**/*"):
        for p in glob.glob(os.path.join(ROOT, pat), recursive=True):
            if os.path.isfile(p) and HEBREW.search(open(p, encoding="utf-8", errors="ignore").read()):
                fails.append(f"Hebrew letters in {os.path.relpath(p, ROOT)}")
    for n, d in cur.items():
        for k, v in d.items():
            if "source" not in v or "reviewed" not in v:
                fails.append(f"glosses/{n}.json {k}: source or reviewed missing")

    kinds = {}
    for it in items:
        kinds[it["kind"]] = kinds.get(it["kind"], 0) + 1
    rev = sum(1 for it in items if it.get("reviewed"))
    print(f"items {len(items)} {kinds}; reviewed {rev}; lessons {len(les['lessons'])}; units {len(units)} "
          f"[{time.time() - t0:.1f}s]")
    if fails:
        print("FAIL\n  " + "\n  ".join(fails[:40]) + (f"\n  ... {len(fails) - 40} more" if len(fails) > 40 else ""))
        sys.exit(1)
    print("PASS")


if __name__ == "__main__":
    main()

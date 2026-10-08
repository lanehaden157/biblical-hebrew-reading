"""
Fold Lane's review decisions back into glosses/.

The review page (pipeline/review_page.py, published as an Artifact) stores one document per item
in its db collection "decisions": {item, kind, unit, proposed, verdict: ok|fix, fix, note}.
Claude saves them with ArtifactData list (out_dir=build/review_decisions), then:

    python -X utf8 pipeline/apply_review.py build/review_decisions [--dry-run]

ok  -> the curated entry gets reviewed=true (gloss unchanged)
fix -> gloss = Lane's text, source "Lane", reviewed=true; note kept
A decision whose `proposed` no longer matches the current gloss is skipped and listed: the gloss
changed after the page was built, so Lane should see the new one.
Afterwards rebuild: build_items.py, then verify_content.py.
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = {"lemma": "lemmas.json", "form": "forms.json", "morpheme": "morphemes.json"}


def current_gloss(kind, item_id):
    """The gloss the item currently shows (curated or seeded), from data/items."""
    for path in glob.glob(os.path.join(ROOT, "data", "items", "*.json")):
        for it in json.load(open(path, encoding="utf-8"))["items"]:
            if it["id"] == item_id:
                return it
    return None


def main(src, dry):
    docs = []
    for p in glob.glob(os.path.join(src, "**", "*.json"), recursive=True):
        d = json.load(open(p, encoding="utf-8"))
        docs.append(d.get("data", d))
    store = {k: json.load(open(os.path.join(ROOT, "glosses", f), encoding="utf-8")) for k, f in FILES.items()}
    applied, skipped = [], []
    for d in sorted(docs, key=lambda d: d["item"]):
        it = current_gloss(d["kind"], d["item"])
        if it is None or d["kind"] not in FILES:
            skipped.append(f"{d['item']}: item not found")
            continue
        if it["gloss"] != d["proposed"]:
            skipped.append(f"{d['item']}: gloss changed since review ({d['proposed']!r} -> {it['gloss']!r})")
            continue
        key = it["lemma"] if d["kind"] == "lemma" else d["item"]
        entry = store[d["kind"]].setdefault(key, {"gloss": it["gloss"], "source": it["gloss_src"]})
        if d["verdict"] == "ok":
            entry["reviewed"] = True
        elif d["verdict"] == "fix" and d.get("fix"):
            entry.update(gloss=d["fix"], source="Lane", reviewed=True)
        else:
            skipped.append(f"{d['item']}: verdict {d['verdict']!r} without a gloss")
            continue
        if d.get("note"):
            entry["lane_note"] = d["note"]
        applied.append(f"{d['item']}: {d['verdict']}" + (f" -> {d['fix']!r}" if d["verdict"] == "fix" else ""))
    print(f"{len(docs)} decisions: {len(applied)} applied, {len(skipped)} skipped")
    for s in skipped:
        print("  skip", s)
    for a in applied:
        if "-> " in a:
            print("  fix ", a)
    if not dry:
        for k, f in FILES.items():
            with open(os.path.join(ROOT, "glosses", f), "w", encoding="utf-8") as out:
                json.dump(store[k], out, ensure_ascii=False, indent=1)
                out.write("\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1], "--dry-run" in sys.argv)

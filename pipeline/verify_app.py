"""Gate for /app: no Hebrew letters, no root-absolute paths, JS parses, data the app reads is consistent.

Run: python -X utf8 pipeline/verify_app.py
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app"
errors = []

# 1. No Hebrew letters (U+05D0..U+05EA) in app files, index.html or sw.js
for p in list(APP.glob("*")) + [ROOT / "index.html", ROOT / "sw.js"]:
    txt = p.read_text(encoding="utf8")
    for n, line in enumerate(txt.splitlines(), 1):
        if any(0x5D0 <= ord(c) <= 0x5EA for c in line):
            errors.append(f"Hebrew letters in {p.name}:{n}")

# 2. No root-absolute fetch/src/href/import paths
ABS = re.compile(r"""(fetch\(\s*['"`]/|(?:src|href)=['"]/|from\s+['"]/|url\(\s*['"]?/)""")
for p in list(APP.glob("*")) + [ROOT / "index.html"]:
    for n, line in enumerate(p.read_text(encoding="utf8").splitlines(), 1):
        if ABS.search(line):
            errors.append(f"root-absolute path in {p.name}:{n}")

# 3. JS parses
for p in APP.glob("*.js"):
    r = subprocess.run(["node", "--check", str(p)], capture_output=True, text=True)
    if r.returncode:
        errors.append(f"syntax {p.name}: {r.stderr.strip().splitlines()[0] if r.stderr else '?'}")

# 4. Data consistency
units = json.loads((ROOT / "data/units.json").read_text(encoding="utf8"))["units"]
lessons = json.loads((ROOT / "data/lessons.json").read_text(encoding="utf8"))
lemmas = json.loads((ROOT / "data/items/lemmas.json").read_text(encoding="utf8"))["items"]
items = {i["id"]: i for i in lemmas}
by_unit = {}
for u in units:
    its = json.loads((ROOT / "data" / u["items"]).read_text(encoding="utf8"))["items"]
    by_unit[u["unit"]] = its
    for i in its:
        if i["id"] in items:
            errors.append(f"duplicate item id {i['id']}")
        items[i["id"]] = i
KINDS = {"lemma", "morpheme", "form", "name", "decode", "decode-read", "micro"}
for i in items.values():
    if i["kind"] not in KINDS:
        errors.append(f"unhandled kind {i['kind']} ({i['id']})")
for l in lessons["lessons"]:
    for uid in l["unlocks"]:
        if uid not in items:
            errors.append(f"lesson {l['id']} unlocks missing item {uid}")
    for r in l["refs"]:
        for t in r["ids"]:
            if t not in lessons["toks"]:
                errors.append(f"lesson {l['id']} token {t} missing")
    for n in re.findall(r"\{(\d+)\}", l["body"]):
        if int(n) >= len(l["refs"]):
            errors.append(f"lesson {l['id']} placeholder {{{n}}} has no ref")
for u in units:
    for lid in u["lessons"]:
        if not any(l["id"] == lid for l in lessons["lessons"]):
            errors.append(f"unit {u['unit']} lists missing lesson {lid}")
# every example ref resolves to a chapter file with the token
idx = json.loads((ROOT / "data/text/index.json").read_text(encoding="utf8"))["books"]
chap_cache = {}


def has_token(ref, tid):
    book, ch, v = ref.split(".")
    if ch not in idx.get(book, {}):
        return False
    key = (book, ch)
    if key not in chap_cache:
        d = json.loads((ROOT / f"data/text/{book}/{ch}.json").read_text(encoding="utf8"))
        chap_cache[key] = {t["id"] for vs in d["verses"] for t in vs["tokens"]}
    return tid in chap_cache[key]


for i in items.values():
    refs = []
    if i["kind"] in ("lemma", "name"):
        refs.append((i["example"]["ref"], i["example"]["id"]))
    elif i["kind"] in ("form", "morpheme"):
        refs += [(e["ref"], e["id"]) for e in i["examples"]]
    for ref, tid in refs:
        if not has_token(ref, tid):
            errors.append(f"{i['id']}: example {ref} {tid} not in text layer")
    if i["kind"] == "micro":
        book, ch, v = i["ref"].split(".")
        if ch not in idx.get(book, {}):
            errors.append(f"{i['id']}: chapter missing")

if errors:
    print(f"FAIL: {len(errors)} problems")
    for e in errors[:40]:
        print(" -", e)
    sys.exit(1)
print(f"verify_app OK ({len(items)} items, {len(lessons['lessons'])} lessons)")

"""
Phone review page for one unit's glosses: injects build/review_unit<N>.json into
pipeline/review_page_template.html -> build/review_page.html (published as an Artifact whose db
collection "decisions" records Lane's OK/Fix per item; pipeline/apply_review.py folds them back).

    python -X utf8 pipeline/review_page.py 1
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(unit):
    items = json.load(open(os.path.join(ROOT, "build", f"review_unit{unit}.json"), encoding="utf-8"))
    tpl = open(os.path.join(ROOT, "pipeline", "review_page_template.html"), encoding="utf-8").read()
    batch = {"unit": unit, "title": f"Unit {unit} glosses", "items": items}
    data = json.dumps(batch, ensure_ascii=False).replace("</", "<" + chr(92) + "/")
    assert tpl.count("/*BATCH*/null") == 1
    out = os.path.join(ROOT, "build", "review_page.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(tpl.replace("/*BATCH*/null", data))
    print(f"{out}: {len(items)} items")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 1)

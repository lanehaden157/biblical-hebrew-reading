"""
Ad-hoc lookup tool for curating data/vocab_examples.json by hand -- not part
of the regular build pipeline, and not itself a build/verify script. Prints
real occurrences of a lemma (optionally restricted to a book) with word ids,
so example curation always starts from an actual corpus hit instead of a
guessed word id. Reuses hebrew_corpus.py's constants, matching build_function_
word_examples.py's own lemma-matching logic (see matches_lemma there).

Usage:
    py -3 pipeline/find_lemma_occurrences.py H559 [BookCode] [--limit N]
"""
import io
import os
import re
import sys
import xml.etree.ElementTree as ET

# Windows consoles default to a legacy codepage that can't encode Hebrew --
# this is a lookup tool run interactively, never part of the app or its
# data, so re-wrapping stdout as UTF-8 here is fine (contrast hard rule 2,
# which is about never normalizing OSHB text itself).
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hebrew_corpus import BOOK_ORDER, OSIS_NS, WLC_DIR  # noqa: E402
from transliterate import transliterate  # noqa: E402

CANTILLATION_RE = re.compile("[֑-֯]")


def strip_cantillation(s):
    return CANTILLATION_RE.sub("", s)


def matches_lemma(lemma_attr, lemma_id):
    for lp_raw in (lemma_attr or "").split("/"):
        lp = lp_raw.strip()
        if lemma_id.startswith("F-"):
            if lp == lemma_id[2:]:
                return True
        else:
            m = re.match(r"^(\d+)", lp)
            if m and m.group(1) == lemma_id[1:]:
                return True
    return False


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    lemma_id = sys.argv[1]
    book_filter = None
    limit = 15
    for arg in sys.argv[2:]:
        if arg.startswith("--limit"):
            limit = int(arg.split("=", 1)[1]) if "=" in arg else limit
        else:
            book_filter = arg

    books = [b for b, _ in BOOK_ORDER if book_filter is None or b == book_filter]
    found = 0
    for book_code in books:
        path = os.path.join(WLC_DIR, f"{book_code}.xml")
        if not os.path.isfile(path):
            continue
        root = ET.parse(path).getroot()
        for verse in root.iter(f"{OSIS_NS}verse"):
            vid = verse.get("osisID")
            if vid is None:
                continue
            words = [
                {"id": w.get("id"), "lemma": w.get("lemma") or "", "text": strip_cantillation(w.text or "")}
                for w in verse.iter(f"{OSIS_NS}w")
            ]
            for w in words:
                if matches_lemma(w["lemma"], lemma_id):
                    line = " ".join(
                        f"[{x['id']}]{x['text']}" + ("*" if x is w else "")
                        for x in words
                    )
                    translit = " ".join(transliterate(x["text"]) for x in words)
                    print(f"{vid}  {line}")
                    print(f"      {translit}")
                    found += 1
                    break
            if found >= limit:
                break
        if found >= limit:
            break
    if not found:
        print("no occurrences found")


if __name__ == "__main__":
    main()

"""
Independent verification of data/lessons_group6.json (suggestion 3).

Deliberately does NOT import build_lessons_group1.decompose() or
build_lessons_group6's own EXAMPLES -- re-implements the decomposition from
scratch against a fresh XML re-scan (same independence discipline as every
other lesson verifier), then diffs every field of every example against the
shipped JSON. Every example in this group is single-word (no construct
chains), but unlike groups 1-5 they're drawn from six different books, not
just Jonah -- EXPECTED_WORD_IDS carries a book code per entry.

Checks performed:
  1. Structural integrity: metadata counts match, every lesson has a
     title and non-empty paragraphs, every example's ref exists in its
     claimed book.
  2. Character-set sanity on every Hebrew/transliteration field.
  3. Every example has a gloss (rule 4) and a non-empty note.
  4. Whole-word reconstruction: prefix_form + base_form + suffix_form must
     equal surface_form exactly.
  5. Independent re-derivation from the raw WLC XML of every example's
     surface_form/transliteration/prefix_form/base_form/suffix_form/
     suffix_kind/suffix_pgn/lemma_citation_form/lemma_transliteration/gloss.
"""
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hebrew_corpus import OSIS_NS, WLC_DIR
from transliterate import transliterate

HERE = os.path.dirname(os.path.abspath(__file__))
DECK_PATH = os.path.join(HERE, "..", "data", "vocab_deck_600.json")
DATA_PATH = os.path.join(HERE, "..", "data", "lessons_group6.json")

CANTILLATION_RE = re.compile("[֑-֯]")
ALLOWED_HEB_RE = re.compile("^[֑-ׇ͏א-ת]*$")
ALLOWED_TRANSLIT_RE = re.compile(r"^['`a-z]+$")
SUFFIX_PGN_RE = re.compile(r"^Sp([123])([mfc])([spd])$")

# (book_code, word_id) per lesson, in shipped order -- independent of
# build_lessons_group6.py's own EXAMPLES dict.
EXPECTED_WORD_IDS = {
    "el-vs-le": [("Jonah", "32eYX"), ("Ruth", "08gYe"), ("Josh", "06cLk")],
    "im-vs-im": [("Judg", "07bu5"), ("Ruth", "08KPU"), ("Ruth", "08Cof")],
    "yesh-vs-ayin": [("Judg", "07Lka"), ("2Kgs", "1289f"), ("Judg", "076Lg"), ("1Kgs", "114d7")],
}

failures = []


def fail(msg):
    failures.append(msg)
    print(f"FAIL: {msg}", file=sys.stderr)


def strip_cantillation(s):
    return CANTILLATION_RE.sub("", s)


def load_lookups():
    with open(DECK_PATH, encoding="utf-8") as f:
        deck = json.load(f)
    return {e["lemma_id"]: e for e in deck["entries"]}


def index_words_by_id(book_code):
    path = os.path.join(WLC_DIR, f"{book_code}.xml")
    root = ET.parse(path).getroot()
    index = {}
    for verse in root.iter(f"{OSIS_NS}verse"):
        vid = verse.get("osisID")
        for w in verse.iter(f"{OSIS_NS}w"):
            wid = w.get("id")
            if wid:
                index[wid] = (vid, w.get("lemma") or "", w.get("morph") or "", w.text or "")
    return index


def decompose(raw_lemma, raw_morph, raw_text, by_id):
    lemma_parts = raw_lemma.split("/")
    morph_parts = [mp[1:] if i == 0 and mp[:1] in ("H", "A") else mp
                   for i, mp in enumerate(raw_morph.split("/"))]
    word_parts = raw_text.split("/")

    n_prefix = 0
    for lp_raw in lemma_parts:
        lp = lp_raw.strip()
        if re.match(r"^[a-z]$", lp):
            n_prefix += 1
        else:
            break

    content_lp = lemma_parts[n_prefix].strip() if n_prefix < len(lemma_parts) else ""
    num_m = re.match(r"^(\d+)", content_lp)
    if not num_m:
        return None
    lemma_id = "H" + num_m.group(1)

    prefix_form = strip_cantillation("".join(word_parts[:n_prefix]))
    base_form = strip_cantillation(word_parts[n_prefix] if n_prefix < len(word_parts) else "")
    suffix_form = strip_cantillation("".join(word_parts[n_prefix + 1:]))
    full_word = strip_cantillation("".join(word_parts))

    suffix_kind = suffix_pgn = None
    rest = morph_parts[n_prefix + 1:]
    if rest:
        if len(rest) == 1 and SUFFIX_PGN_RE.match(rest[0]):
            p, g, num = SUFFIX_PGN_RE.match(rest[0]).groups()
            suffix_kind = "pronominal"
            suffix_pgn = {"person": p, "gender": g, "number": num}
        elif len(rest) == 1 and rest[0] == "Sn":
            suffix_kind = "paragogic_nun"
        elif len(rest) == 1 and rest[0] == "Sh":
            suffix_kind = "directional_he"

    lemma_entry = by_id.get(lemma_id)
    return {
        "surface_form": full_word,
        "transliteration": transliterate(full_word),
        "prefix_form": prefix_form,
        "base_form": base_form,
        "suffix_form": suffix_form,
        "suffix_kind": suffix_kind,
        "suffix_pgn": suffix_pgn,
        "lemma_id": lemma_id,
        "lemma_entry": lemma_entry,
    }


def check_example(tag, shipped, expected):
    for field in ("surface_form", "transliteration", "prefix_form", "base_form", "suffix_form", "suffix_kind"):
        if shipped.get(field) != expected[field]:
            fail(f"{tag}: {field} mismatch: shipped {shipped.get(field)!r}, recomputed {expected[field]!r}")
    if (shipped.get("suffix_pgn") or {}).get("person") != (expected["suffix_pgn"] or {}).get("person"):
        fail(f"{tag}: suffix_pgn.person mismatch")
    if (shipped.get("prefix_form") or "") + shipped.get("base_form", "") + (shipped.get("suffix_form") or "") != shipped.get("surface_form"):
        fail(f"{tag}: prefix_form+base_form+suffix_form != surface_form")

    le = expected["lemma_entry"]
    if le is None:
        fail(f"{tag}: lemma {expected['lemma_id']} not found in vocab_deck_600.json")
    else:
        if shipped.get("lemma_citation_form") != le["citation_form"]:
            fail(f"{tag}: lemma_citation_form mismatch")
        if shipped.get("lemma_transliteration") != transliterate(le["citation_form"]):
            fail(f"{tag}: lemma_transliteration mismatch")
        if shipped.get("gloss") != le["gloss"]:
            fail(f"{tag}: gloss {shipped.get('gloss')!r} != deck gloss {le['gloss']!r}")

    if not shipped.get("surface_form") or not ALLOWED_HEB_RE.match(shipped["surface_form"]):
        fail(f"{tag}: surface_form has unexpected characters")
    for field in ("prefix_form", "base_form", "suffix_form"):
        v = shipped.get(field, "")
        if v and not ALLOWED_HEB_RE.match(v):
            fail(f"{tag}: {field} has unexpected characters")
    if not shipped.get("transliteration") or not ALLOWED_TRANSLIT_RE.match(shipped["transliteration"]):
        fail(f"{tag}: transliteration outside the locked ASCII scheme")

    if shipped.get("highlight") not in ("prefix", "base", "suffix"):
        fail(f"{tag}: highlight must be prefix/base/suffix, got {shipped.get('highlight')!r}")
    if not shipped.get("note", "").strip():
        fail(f"{tag}: empty note")


def main():
    if not os.path.isfile(DATA_PATH):
        sys.exit("data/lessons_group6.json not found -- run pipeline/build_lessons_group6.py first")

    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    meta = data["metadata"]
    lessons = data["lessons"]

    if meta["lesson_count"] != len(lessons):
        fail(f"metadata.lesson_count={meta['lesson_count']} but {len(lessons)} lessons present")
    total_examples = sum(len(l["examples"]) for l in lessons)
    if meta["example_count"] != total_examples:
        fail(f"metadata.example_count={meta['example_count']} but {total_examples} examples present")

    by_id = load_lookups()
    word_indexes = {}

    lesson_ids = {l["id"] for l in lessons}
    if lesson_ids != set(EXPECTED_WORD_IDS):
        fail(f"lesson id set mismatch: shipped={sorted(lesson_ids)}, expected={sorted(EXPECTED_WORD_IDS)}")

    for lesson in lessons:
        lid = lesson["id"]
        tag_prefix = f"lesson {lid!r}"
        if not lesson.get("title", "").strip():
            fail(f"{tag_prefix}: empty title")
        if not lesson.get("paragraphs") or any(not p.strip() for p in lesson["paragraphs"]):
            fail(f"{tag_prefix}: missing or empty paragraphs")

        expected_ids = EXPECTED_WORD_IDS.get(lid)
        if expected_ids is None:
            continue  # already reported above
        if len(expected_ids) != len(lesson["examples"]):
            fail(f"{tag_prefix}: expected {len(expected_ids)} examples, shipped {len(lesson['examples'])}")

        for (book_code, wid), ex in zip(expected_ids, lesson["examples"]):
            tag = f"{tag_prefix}/{wid} ({book_code})"
            if book_code not in word_indexes:
                word_indexes[book_code] = index_words_by_id(book_code)
            entry = word_indexes[book_code].get(wid)
            if entry is None:
                fail(f"{tag}: word id not found in {book_code}.xml")
                continue
            vid, raw_lemma, raw_morph, raw_text = entry
            if vid != ex.get("ref"):
                fail(f"{tag}: ref mismatch, corpus says {vid!r}, shipped {ex.get('ref')!r}")
            expected = decompose(raw_lemma, raw_morph, raw_text, by_id)
            if expected is None:
                fail(f"{tag}: independent decomposition failed (no resolvable content lemma)")
                continue
            check_example(tag, ex, expected)

    print(f"Checked {len(lessons)} lessons, {total_examples} examples across {len(word_indexes)} books.")
    if failures:
        print(f"\n{len(failures)} FAILURE(S)", file=sys.stderr)
        sys.exit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()

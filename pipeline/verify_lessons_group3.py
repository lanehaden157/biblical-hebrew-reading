"""
Independent verification of data/lessons_group3.json (suggestion 3).

Deliberately does NOT import build_lessons_group1.decompose() -- re-derives
it from scratch against a fresh XML re-scan (same independence discipline
as verify_lessons_group1.py and verify_lessons_group2.py), then diffs every
field of every example against the shipped JSON.

Checks performed:
  1. Structural integrity: metadata counts match, every lesson has a
     title/non-empty paragraphs, every example's ref exists in Jonah.
  2. Character-set sanity on every Hebrew/transliteration field.
  3. Every Hebrew form shown has a gloss and a note (rule 4).
  4. Whole-word reconstruction: prefix_form + base_form + suffix_form must
     equal surface_form exactly.
  5. Independent re-derivation from the raw WLC XML of every example's
     surface_form/transliteration/prefix_form/base_form/suffix_form/
     suffix_kind/suffix_pgn/lemma_citation_form/lemma_transliteration/gloss.
  6. Lesson-1's binyan pair specifically: independently re-confirms (from a
     full-book scan, not trusted from the shipped data) that H5307 (נפל)
     is genuinely attested in both Qal and Hiphil in Jonah, and that the
     two curated examples are that lemma in those two stems -- the whole
     point of that example is a real same-root contrast, so this is worth
     checking on its own, not just folding into the generic per-field diff.
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
EXTRA_PATHS = [os.path.join(HERE, "..", "glosses", f"jonah{n}_extra.json") for n in (1, 2, 3, 4)]
DATA_PATH = os.path.join(HERE, "..", "data", "lessons_group3.json")

CANTILLATION_RE = re.compile("[֑-֯]")
ALLOWED_HEB_RE = re.compile("^[֑-ׇ͏א-ת]*$")
ALLOWED_TRANSLIT_RE = re.compile(r"^['`a-z]+$")
SUFFIX_PGN_RE = re.compile(r"^Sp([123])([mfc])([spd])$")
GENDER_LABEL = {"m": "m", "f": "f", "c": "c"}
NUMBER_LABEL = {"s": "s", "p": "p", "d": "d"}

WORD_IDS = {
    "binyan": ["32jQ8", "32fJN", "32hh7", "327am", "32nLp"],
    "aspect": ["32fLi", "32BYa"],
    "vav-consecutive": ["32TZE", "32jbg", "32v6U", "32GmF", "32mnL"],
    "participle": ["3292v", "32FMU", "32SaV"],
    "infinitive-construct": ["32LN3", "32JM7", "323yJ"],
    "commands": ["32Qzf", "32aPd", "32GLz", "32MVq"],
}
BOOK = "Jonah"

failures = []


def fail(msg):
    failures.append(msg)
    print(f"FAIL: {msg}", file=sys.stderr)


def strip_cantillation(s):
    return CANTILLATION_RE.sub("", s)


def load_lookups():
    with open(DECK_PATH, encoding="utf-8") as f:
        deck = json.load(f)
    by_id = {e["lemma_id"]: e for e in deck["entries"]}
    for path in EXTRA_PATHS:
        with open(path, encoding="utf-8") as f:
            extra = json.load(f)
        for e in extra["entries"]:
            by_id.setdefault(e["lemma_id"], e)
    return by_id


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
    prefix_ids = []
    for lp_raw in lemma_parts:
        lp = lp_raw.strip()
        if re.match(r"^[a-z]$", lp):
            prefix_ids.append("F-" + lp)
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
            suffix_pgn = {"person": p, "gender": GENDER_LABEL[g], "number": NUMBER_LABEL[num]}
        elif len(rest) == 1 and rest[0] == "Sn":
            suffix_kind = "paragogic_nun"
        elif len(rest) == 1 and rest[0] == "Sh":
            suffix_kind = "directional_he"

    lemma_entry = by_id.get(lemma_id)
    return {
        "surface_form": full_word,
        "transliteration": transliterate(full_word),
        "prefix_form": prefix_form,
        "prefix_ids": prefix_ids,
        "base_form": base_form,
        "suffix_form": suffix_form,
        "suffix_kind": suffix_kind,
        "suffix_pgn": suffix_pgn,
        "lemma_id": lemma_id,
        "lemma_entry": lemma_entry,
    }


def check_binyan_pair(word_index):
    """Independently re-derive, from a full-book scan, that H5307 is
    genuinely attested in both Qal and Hiphil in Jonah -- the whole point
    of lesson 1's anchor example."""
    stems_seen = set()
    for path in [os.path.join(WLC_DIR, "Jonah.xml")]:
        root = ET.parse(path).getroot()
        for w in root.iter(f"{OSIS_NS}w"):
            lemma_parts = (w.get("lemma") or "").split("/")
            morph_parts = (w.get("morph") or "").split("/")
            for i, mp0 in enumerate(morph_parts):
                mp = mp0[1:] if i == 0 and mp0[:1] in ("H", "A") else mp0
                m = re.match(r"^V([qNpPhHt])", mp)
                if not m:
                    continue
                lp = lemma_parts[i].strip() if i < len(lemma_parts) else ""
                num_m = re.match(r"^(\d+)", lp)
                if num_m and "H" + num_m.group(1) == "H5307":
                    stems_seen.add(m.group(1))
    if not {"q", "h"} <= stems_seen:
        fail(f"binyan-pair check: H5307 (נפל) stems found in Jonah = {stems_seen}, expected both Qal ('q') and Hiphil ('h')")

    def find_verb_stem(raw_morph):
        for i, mp0 in enumerate(raw_morph.split("/")):
            mp = mp0[1:] if i == 0 and mp0[:1] in ("H", "A") else mp0
            m = re.match(r"^V([qNpPhHt])", mp)
            if m:
                return m.group(1)
        return None

    entry = word_index.get("32jQ8")
    if entry is None or "5307" not in (entry[1] or "").split("/"):
        fail("binyan-pair check: word 32jQ8 is not lemma H5307")
    elif find_verb_stem(entry[2]) != "h":
        fail(f"binyan-pair check: 32jQ8 expected Hiphil, morph is {entry[2]!r}")
    entry = word_index.get("32fJN")
    if entry is None or "5307" not in (entry[1] or "").split("/"):
        fail("binyan-pair check: word 32fJN is not lemma H5307")
    elif find_verb_stem(entry[2]) != "q":
        fail(f"binyan-pair check: 32fJN expected Qal, morph is {entry[2]!r}")


def main():
    if not os.path.isfile(DATA_PATH):
        sys.exit("data/lessons_group3.json not found -- run pipeline/build_lessons_group3.py first")

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
    word_index = index_words_by_id(BOOK)

    check_binyan_pair(word_index)

    for lesson in lessons:
        lid = lesson["id"]
        tag_prefix = f"lesson {lid!r}"
        if not lesson.get("title", "").strip():
            fail(f"{tag_prefix}: empty title")
        if not lesson.get("paragraphs") or any(not p.strip() for p in lesson["paragraphs"]):
            fail(f"{tag_prefix}: missing or empty paragraphs")

        expected_wids = WORD_IDS.get(lid)
        if expected_wids is None:
            fail(f"{tag_prefix}: no independent word-id list for this lesson id")
            continue
        if len(expected_wids) != len(lesson["examples"]):
            fail(f"{tag_prefix}: expected {len(expected_wids)} examples, shipped {len(lesson['examples'])}")

        seen_wids = set()
        for wid, ex in zip(expected_wids, lesson["examples"]):
            tag = f"{tag_prefix}/{wid} ({ex.get('ref')})"
            if wid in seen_wids:
                fail(f"{tag}: duplicate word id within lesson")
            seen_wids.add(wid)

            entry = word_index.get(wid)
            if entry is None:
                fail(f"{tag}: word id not found in Jonah.xml")
                continue
            vid, raw_lemma, raw_morph, raw_text = entry
            if vid != ex["ref"]:
                fail(f"{tag}: ref mismatch, corpus says {vid!r}")

            expected = decompose(raw_lemma, raw_morph, raw_text, by_id)
            if expected is None:
                fail(f"{tag}: independent decomposition failed to find a content lemma")
                continue
            if expected["lemma_entry"] is None:
                fail(f"{tag}: lemma {expected['lemma_id']} not found in vocab_deck_600.json or curated extras")
                continue

            for field in ("surface_form", "transliteration", "prefix_form", "base_form", "suffix_form", "suffix_kind"):
                if ex.get(field) != expected[field]:
                    fail(f"{tag}: {field} mismatch: shipped {ex.get(field)!r}, recomputed {expected[field]!r}")
            if ex.get("suffix_pgn") != expected["suffix_pgn"]:
                fail(f"{tag}: suffix_pgn mismatch")
            if (ex.get("prefix_form") or "") + ex.get("base_form", "") + (ex.get("suffix_form") or "") != ex.get("surface_form"):
                fail(f"{tag}: prefix_form+base_form+suffix_form != surface_form")

            if len(ex.get("prefix_morphemes") or []) != len(expected["prefix_ids"]):
                fail(f"{tag}: prefix_morphemes count mismatch")
            else:
                for pm, fid in zip(ex.get("prefix_morphemes") or [], expected["prefix_ids"]):
                    fn_entry = by_id.get(fid)
                    if fn_entry is None or pm["citation_form"] != fn_entry["citation_form"] or pm["gloss"] != fn_entry["gloss"]:
                        fail(f"{tag}: prefix morpheme {pm} doesn't match curated {fid} entry")

            le = expected["lemma_entry"]
            if ex.get("lemma_citation_form") != le["citation_form"]:
                fail(f"{tag}: lemma_citation_form mismatch")
            if ex.get("lemma_transliteration") != transliterate(le["citation_form"]):
                fail(f"{tag}: lemma_transliteration mismatch")
            if ex.get("gloss") != le["gloss"]:
                fail(f"{tag}: gloss mismatch")

            if not ex["surface_form"] or not ALLOWED_HEB_RE.match(ex["surface_form"]):
                fail(f"{tag}: surface_form has unexpected characters")
            for field in ("prefix_form", "base_form", "suffix_form"):
                v = ex.get(field, "")
                if v and not ALLOWED_HEB_RE.match(v):
                    fail(f"{tag}: {field} has unexpected characters")
            if not ex["transliteration"] or not ALLOWED_TRANSLIT_RE.match(ex["transliteration"]):
                fail(f"{tag}: transliteration outside the locked ASCII scheme")
            if not ex.get("gloss", "").strip():
                fail(f"{tag}: empty gloss")
            if not ex.get("note", "").strip():
                fail(f"{tag}: empty note")
            if ex.get("highlight") not in ("prefix", "base", "suffix"):
                fail(f"{tag}: highlight must be prefix/base/suffix, got {ex.get('highlight')!r}")

    print(f"Checked {len(lessons)} lessons, {total_examples} examples.")
    if failures:
        print(f"\n{len(failures)} FAILURE(S)", file=sys.stderr)
        sys.exit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()

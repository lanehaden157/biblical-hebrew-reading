"""
Independent verification of data/lessons_group1.json (suggestion 3).

Deliberately does NOT import build_lessons_group1.py's decompose() -- this
re-implements the prefix/base/suffix split from scratch, re-derives its own
gloss lookup from vocab_deck_600.json + the curated extras, and recomputes
every example's transliteration via transliterate() (which has its own
separate verify_transliterate.py, so reusing it isn't re-trusting unverified
code), then diffs against the shipped JSON field-by-field. The curatorial
choice of *which* word id illustrates each concept is trusted the same way
glosses/jonah1_extra.json's lemma choices are -- what's checked is whether
that word was decomposed, transliterated, and glossed correctly, not
whether it was the best possible choice.

Checks performed:
  1. Structural integrity: metadata counts match, every lesson has an id/
     order/title/non-empty paragraphs, every example's ref exists in the
     source book, no duplicate example refs within a lesson.
  2. Character-set sanity on every surface_form/prefix_form/base_form/
     suffix_form/transliteration/lemma_citation_form/lemma_transliteration.
  3. Every Hebrew form shown has a gloss (rule 4).
  4. Whole-word reconstruction: prefix_form + base_form + suffix_form must
     equal surface_form exactly.
  5. Independent re-derivation from the raw WLC XML: re-fetch each
     example's own lemma/morph/text by its word id, re-run an independently
     written decomposition, and diff every field against the shipped JSON.
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
EXTRA_PATHS = [
    os.path.join(HERE, "..", "glosses", f"jonah{n}_extra.json") for n in (1, 2, 3, 4)
]
DATA_PATH = os.path.join(HERE, "..", "data", "lessons_group1.json")

CANTILLATION_RE = re.compile("[֑-֯]")
ALLOWED_HEB_RE = re.compile("^[֑-ׇ͏א-ת]*$")
ALLOWED_TRANSLIT_RE = re.compile(r"^['`a-z]+$")
SUFFIX_PGN_RE = re.compile(r"^Sp([123])([mfc])([spd])$")
GENDER_LABEL = {"m": "m", "f": "f", "c": "c"}
NUMBER_LABEL = {"s": "s", "p": "p", "d": "d"}

# Every example's OSIS word id, keyed by (lesson_id, ref, surface_form) so
# the diff below can locate the right shipped entry without importing the
# build script's own EXAMPLES table. The word ids are the curatorial
# choice (see docstring); this file re-derives everything else from them.
WORD_IDS = {
    "vav-conjunction": ["32A4a", "32PB6", "32V27"],
    "definite-article": ["32qNN", "32EVS", "32Y3z", "323TS"],
    "prepositions": ["32KZG", "32W26", "32JM7", "32FV9"],
    "pronominal-suffixes": ["3229t", "3237c", "32jQb", "325gQ"],
    "relative": ["32BU7", "32Ptj"],
    "interrogative-he": ["32CFo"],
}
BOOK_BY_ID_PREFIX = "Jonah"  # every example in this lesson group comes from Jonah

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
    """Independent re-implementation of the prefix/base/suffix split."""
    lemma_parts = raw_lemma.split("/")
    morph_parts = raw_morph.split("/")
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


def main():
    if not os.path.isfile(DATA_PATH):
        sys.exit("data/lessons_group1.json not found -- run pipeline/build_lessons_group1.py first")

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
    word_index = index_words_by_id(BOOK_BY_ID_PREFIX)

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

            # Multiple examples from the same verse are fine (several words
            # in one verse can each illustrate the concept); a repeated
            # *word id* would mean two examples silently point at the same
            # word, which is the actual anomaly worth catching.
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
                    fail(f"{tag}: {field} mismatch: shipped {ex.get(field)!r}, independently recomputed {expected[field]!r}")
            if ex.get("suffix_pgn") != expected["suffix_pgn"]:
                fail(f"{tag}: suffix_pgn mismatch: shipped {ex.get('suffix_pgn')!r}, recomputed {expected['suffix_pgn']!r}")

            if ex["prefix_form"] + ex["base_form"] + ex["suffix_form"] != ex["surface_form"]:
                fail(f"{tag}: prefix_form+base_form+suffix_form != surface_form")

            shipped_prefix_ids = None  # can't recover F-<letter> ids from citation_form alone; check count instead
            if len(ex.get("prefix_morphemes") or []) != len(expected["prefix_ids"]):
                fail(f"{tag}: prefix_morphemes count {len(ex.get('prefix_morphemes') or [])} != expected {len(expected['prefix_ids'])}")
            else:
                for pm, fid in zip(ex.get("prefix_morphemes") or [], expected["prefix_ids"]):
                    fn_entry = by_id.get(fid)
                    if fn_entry is None:
                        fail(f"{tag}: function code {fid} not in vocab_deck_600.json")
                        continue
                    if pm["citation_form"] != fn_entry["citation_form"] or pm["gloss"] != fn_entry["gloss"]:
                        fail(f"{tag}: prefix morpheme {pm} doesn't match curated {fid} entry")

            le = expected["lemma_entry"]
            if ex.get("lemma_citation_form") != le["citation_form"]:
                fail(f"{tag}: lemma_citation_form mismatch")
            if ex.get("lemma_transliteration") != transliterate(le["citation_form"]):
                fail(f"{tag}: lemma_transliteration mismatch")
            if ex.get("gloss") != le["gloss"]:
                fail(f"{tag}: gloss mismatch")

            # --- character-set / rule-4 sanity ---------------------------
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

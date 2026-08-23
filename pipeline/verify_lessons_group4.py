"""
Independent verification of data/lessons_group4.json (suggestion 3).

Deliberately does NOT import build_lessons_group1.decompose() or
build_lessons_group4's own builders -- re-implements the decomposition
from scratch against a fresh XML re-scan (same independence discipline as
every other lesson verifier), then diffs every field of every example
(single-word and chain alike) against the shipped JSON.

Checks performed:
  1. Structural integrity: metadata counts match, every lesson has a
     title/kind/non-empty paragraphs, every example's ref exists in Jonah.
  2. Character-set sanity on every Hebrew/transliteration field, on both
     example shapes.
  3. Every Hebrew form shown has a gloss (rule 4) -- phrase_gloss for
     chains, gloss for single-word examples.
  4. Whole-word reconstruction for every token/example: prefix_form +
     base_form + suffix_form must equal surface_form exactly.
  5. Chain-specific: every token's role is "plain" (this group's chains
     are noun-adjective agreement pairs, not construct chains -- there's
     no construct/absolute lean to classify), and a chain's tokens must
     all share one verse ref.
  6. Independent re-derivation from the raw WLC XML of every example's
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
EXTRA_PATHS = [os.path.join(HERE, "..", "glosses", f"jonah{n}_extra.json") for n in (1, 2, 3, 4)]
DATA_PATH = os.path.join(HERE, "..", "data", "lessons_group4.json")

CANTILLATION_RE = re.compile("[֑-֯]")
ALLOWED_HEB_RE = re.compile("^[֑-ׇ͏א-ת]*$")
ALLOWED_TRANSLIT_RE = re.compile(r"^['`a-z]+$")
SUFFIX_PGN_RE = re.compile(r"^Sp([123])([mfc])([spd])$")
GENDER_LABEL = {"m": "m", "f": "f", "c": "c"}
NUMBER_LABEL = {"s": "s", "p": "p", "d": "d"}

CHAIN_WORD_IDS = {
    "adjective-agreement": [["32Rvc", "32c6V"], ["32qNN", "32EVS"]],
}
SINGLE_WORD_IDS = {
    "gender-number": ["32iy2", "32fsu", "32Haa"],
    "direct-object": ["32eHJ", "329Hv", "32J9J"],
    "demonstratives-numbers": ["32zQ2", "32eRa", "32xp4"],
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


def check_token(tag, shipped, expected, by_id):
    for field in ("surface_form", "transliteration", "prefix_form", "base_form", "suffix_form", "suffix_kind"):
        if shipped.get(field) != expected[field]:
            fail(f"{tag}: {field} mismatch: shipped {shipped.get(field)!r}, recomputed {expected[field]!r}")
    if shipped.get("suffix_pgn") != expected["suffix_pgn"]:
        fail(f"{tag}: suffix_pgn mismatch")
    if (shipped.get("prefix_form") or "") + shipped.get("base_form", "") + (shipped.get("suffix_form") or "") != shipped.get("surface_form"):
        fail(f"{tag}: prefix_form+base_form+suffix_form != surface_form")

    if len(shipped.get("prefix_morphemes") or []) != len(expected["prefix_ids"]):
        fail(f"{tag}: prefix_morphemes count mismatch")
    else:
        for pm, fid in zip(shipped.get("prefix_morphemes") or [], expected["prefix_ids"]):
            fn_entry = by_id.get(fid)
            if fn_entry is None or pm["citation_form"] != fn_entry["citation_form"] or pm["gloss"] != fn_entry["gloss"]:
                fail(f"{tag}: prefix morpheme {pm} doesn't match curated {fid} entry")

    le = expected["lemma_entry"]
    if le is None:
        fail(f"{tag}: lemma {expected['lemma_id']} not found in vocab_deck_600.json or curated extras")
    else:
        if shipped.get("lemma_citation_form") != le["citation_form"]:
            fail(f"{tag}: lemma_citation_form mismatch")
        if shipped.get("lemma_transliteration") != transliterate(le["citation_form"]):
            fail(f"{tag}: lemma_transliteration mismatch")
        if shipped.get("gloss") != le["gloss"]:
            fail(f"{tag}: gloss mismatch")

    if not shipped.get("surface_form") or not ALLOWED_HEB_RE.match(shipped["surface_form"]):
        fail(f"{tag}: surface_form has unexpected characters")
    for field in ("prefix_form", "base_form", "suffix_form"):
        v = shipped.get(field, "")
        if v and not ALLOWED_HEB_RE.match(v):
            fail(f"{tag}: {field} has unexpected characters")
    if not shipped.get("transliteration") or not ALLOWED_TRANSLIT_RE.match(shipped["transliteration"]):
        fail(f"{tag}: transliteration outside the locked ASCII scheme")


def main():
    if not os.path.isfile(DATA_PATH):
        sys.exit("data/lessons_group4.json not found -- run pipeline/build_lessons_group4.py first")

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

    for lesson in lessons:
        lid = lesson["id"]
        tag_prefix = f"lesson {lid!r}"
        if not lesson.get("title", "").strip():
            fail(f"{tag_prefix}: empty title")
        if not lesson.get("paragraphs") or any(not p.strip() for p in lesson["paragraphs"]):
            fail(f"{tag_prefix}: missing or empty paragraphs")
        if lesson.get("kind") not in ("chain", "single"):
            fail(f"{tag_prefix}: unrecognized kind {lesson.get('kind')!r}")
            continue

        if lesson["kind"] == "chain":
            expected_groups = CHAIN_WORD_IDS.get(lid)
            if expected_groups is None:
                fail(f"{tag_prefix}: no independent word-id list for this chain lesson")
                continue
            if len(expected_groups) != len(lesson["examples"]):
                fail(f"{tag_prefix}: expected {len(expected_groups)} chain examples, shipped {len(lesson['examples'])}")
            for wids, ex in zip(expected_groups, lesson["examples"]):
                tag = f"{tag_prefix}/{'+'.join(wids)} ({ex.get('ref')})"
                tokens = ex.get("tokens") or []
                if len(tokens) != len(wids):
                    fail(f"{tag}: expected {len(wids)} tokens, shipped {len(tokens)}")
                    continue
                refs = set()
                for wid, tok in zip(wids, tokens):
                    entry = word_index.get(wid)
                    if entry is None:
                        fail(f"{tag}: word id {wid} not found in Jonah.xml")
                        continue
                    vid, raw_lemma, raw_morph, raw_text = entry
                    refs.add(vid)
                    expected = decompose(raw_lemma, raw_morph, raw_text, by_id)
                    if expected is None:
                        fail(f"{tag}/{wid}: independent decomposition failed")
                        continue
                    check_token(f"{tag}/{wid}", tok, expected, by_id)
                    if tok.get("role") != "plain":
                        fail(f"{tag}/{wid}: role expected 'plain', got {tok.get('role')!r}")
                if len(refs) != 1:
                    fail(f"{tag}: chain tokens don't share a single verse ref: {refs}")
                elif ex.get("ref") not in refs:
                    fail(f"{tag}: shipped ref {ex.get('ref')!r} doesn't match corpus {refs}")
                if not ex.get("phrase_gloss", "").strip():
                    fail(f"{tag}: empty phrase_gloss")
                if not ex.get("note", "").strip():
                    fail(f"{tag}: empty note")
        else:
            expected_wids = SINGLE_WORD_IDS.get(lid)
            if expected_wids is None:
                fail(f"{tag_prefix}: no independent word-id list for this single-word lesson")
                continue
            if len(expected_wids) != len(lesson["examples"]):
                fail(f"{tag_prefix}: expected {len(expected_wids)} examples, shipped {len(lesson['examples'])}")
            for wid, ex in zip(expected_wids, lesson["examples"]):
                tag = f"{tag_prefix}/{wid} ({ex.get('ref')})"
                entry = word_index.get(wid)
                if entry is None:
                    fail(f"{tag}: word id not found in Jonah.xml")
                    continue
                vid, raw_lemma, raw_morph, raw_text = entry
                if vid != ex.get("ref"):
                    fail(f"{tag}: ref mismatch, corpus says {vid!r}")
                expected = decompose(raw_lemma, raw_morph, raw_text, by_id)
                if expected is None:
                    fail(f"{tag}: independent decomposition failed")
                    continue
                check_token(tag, ex, expected, by_id)
                if ex.get("highlight") not in ("prefix", "base", "suffix"):
                    fail(f"{tag}: highlight must be prefix/base/suffix, got {ex.get('highlight')!r}")
                if not ex.get("note", "").strip():
                    fail(f"{tag}: empty note")

    print(f"Checked {len(lessons)} lessons, {total_examples} examples.")
    if failures:
        print(f"\n{len(failures)} FAILURE(S)", file=sys.stderr)
        sys.exit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()

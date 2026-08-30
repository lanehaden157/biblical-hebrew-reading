"""
Independent verification of data/vocab_examples.json (hard rule 3). Sibling
to verify_function_word_examples.py; same discipline (re-scans the corpus
itself, doesn't import build_vocab_examples.py), different target set and
no tiering -- see build_vocab_examples.py's docstring for why this file's
lemmas only need one verified example, not several.

Checks:
  1. Every shipped entry's lemma_id is in the independently re-derived
     target set (drillable vocab_deck_600.json entries not already covered
     by function_word_examples.json), and no entry has zero examples.
  2. metadata.skipped and the shipped entries are disjoint, both are
     subsets of the target set, and every skipped lemma has a non-empty
     reason -- an unexplained skip is a bug, but a lemma in neither
     (still pending) is just unfinished work, not a failure.
  3. Every example's word_id is independently found in the claimed verse
     of the claimed book, its lemma independently resolves to the entry's
     lemma_id, and surface_form/transliteration/phrase_hebrew/
     phrase_transliteration/target_index all match an independent
     re-extraction from the corpus exactly (mirrors verify_function_word_
     examples.py's phrase re-slicing).
  4. Character-set sanity on every Hebrew/transliteration field.
  5. gloss_highlight is a literal substring of gloss; gloss_note, when
     present, is non-empty. No duplicate (lemma_id, ref, word_id).
  6. metadata counts (target_lemma_count/curated_count/pending_count)
     match what's actually independently derivable from the file + deck.
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
FWEX_PATH = os.path.join(HERE, "..", "data", "function_word_examples.json")
DATA_PATH = os.path.join(HERE, "..", "data", "vocab_examples.json")

CANTILLATION_RE = re.compile("[֑-֯]")
ALLOWED_HEB_RE = re.compile(r"^[֑-ׇ͏א-ת ]*$")
ALLOWED_TRANSLIT_RE = re.compile(r"^['`a-z .,;:!?‘’]+$")

failures = []


def fail(msg):
    failures.append(msg)
    print(f"FAIL: {msg}", file=sys.stderr)


def strip_cant(s):
    return CANTILLATION_RE.sub("", s)


def independent_target_set():
    with open(DECK_PATH, encoding="utf-8") as f:
        deck = json.load(f)
    with open(FWEX_PATH, encoding="utf-8") as f:
        fwex_covered = {e["lemma_id"] for e in json.load(f)["entries"]}
    out = {}
    for e in deck["entries"]:
        if e.get("drillable", True) and e["lemma_id"] not in fwex_covered:
            out[e["lemma_id"]] = e
    return out


def word_matches_lemma(lemma_parts, lemma_id):
    for lp_raw in lemma_parts:
        lp = lp_raw.strip()
        m = re.match(r"^(\d+)", lp)
        if m and m.group(1) == lemma_id[1:]:
            return True
    return False


def load_book(book_code, book_cache):
    if book_code not in book_cache:
        path = os.path.join(WLC_DIR, f"{book_code}.xml")
        root = ET.parse(path).getroot()
        verses = {}
        for verse in root.iter(f"{OSIS_NS}verse"):
            vid = verse.get("osisID")
            if vid is None:
                continue
            verses[vid] = [
                {"id": w.get("id"), "lemma": w.get("lemma") or "", "text": w.text or ""}
                for w in verse.iter(f"{OSIS_NS}w")
            ]
        book_cache[book_code] = verses
    return book_cache[book_code]


def find_word_and_verse(book_code, word_id, book_cache):
    verses = load_book(book_code, book_cache)
    for vid, words in verses.items():
        for w in words:
            if w["id"] == word_id:
                return vid, words, w
    return None, None, None


def main():
    if not os.path.isfile(DATA_PATH):
        sys.exit("data/vocab_examples.json not found -- run pipeline/build_vocab_examples.py first")

    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    entries = data["entries"]
    meta = data["metadata"]

    # --- 1/2. target set, skip-set, and shipped entries are consistent ----
    expected_targets = independent_target_set()
    shipped_ids = {e["lemma_id"] for e in entries}
    extra = shipped_ids - set(expected_targets)
    if extra:
        fail(f"vocab_examples.json has lemmas outside the target set: {sorted(extra)}")

    skipped_ids = {row["lemma_id"] for row in meta.get("skipped", [])}
    for row in meta.get("skipped", []):
        if not row.get("reason") or not row["reason"].strip():
            fail(f"{row['lemma_id']}: skipped with no reason")
    extra_skipped = skipped_ids - set(expected_targets)
    if extra_skipped:
        fail(f"metadata.skipped has lemmas outside the target set: {sorted(extra_skipped)}")
    overlap = shipped_ids & skipped_ids
    if overlap:
        fail(f"lemma(s) both curated and skipped: {sorted(overlap)}")

    pending = set(expected_targets) - shipped_ids - skipped_ids
    if meta.get("target_lemma_count") != len(expected_targets):
        fail(f"metadata.target_lemma_count={meta.get('target_lemma_count')} but independently found {len(expected_targets)}")
    if meta.get("curated_count") != len(entries):
        fail(f"metadata.curated_count={meta.get('curated_count')} but {len(entries)} entries present")
    if meta.get("pending_count") != len(pending):
        fail(f"metadata.pending_count={meta.get('pending_count')} but independently found {len(pending)} pending")

    seen_examples = set()
    book_cache = {}

    for e in entries:
        lemma_id = e["lemma_id"]
        tag = f"{lemma_id} ({e['citation_form']})"
        if not e["examples"]:
            fail(f"{tag}: zero examples")

        deck_e = expected_targets.get(lemma_id)
        if deck_e is not None:
            if deck_e["citation_form"] != e["citation_form"] or deck_e["transliteration"] != e["transliteration"]:
                fail(f"{tag}: citation_form/transliteration mismatch vs vocab_deck_600.json")
            if deck_e["gloss"] != e["full_gloss"]:
                fail(f"{tag}: full_gloss {e['full_gloss']!r} != deck gloss {deck_e['gloss']!r}")

        for ex in e["examples"]:
            key = (lemma_id, ex["ref"], ex["word_id"])
            if key in seen_examples:
                fail(f"{tag}: duplicate example {key}")
            seen_examples.add(key)

            book_code = ex["ref"].split(".")[0]
            vid, words, target = find_word_and_verse(book_code, ex["word_id"], book_cache)
            if target is None:
                fail(f"{tag}: word id {ex['word_id']!r} not found anywhere in {book_code}.xml")
                continue
            if vid != ex["ref"]:
                fail(f"{tag}: word id {ex['word_id']!r} independently found in {vid}, not claimed ref {ex['ref']!r}")
                continue
            if not word_matches_lemma(target["lemma"].split("/"), lemma_id):
                fail(f"{tag}: word id {ex['word_id']!r} lemma {target['lemma']!r} does not resolve to {lemma_id}")

            expected_surface = strip_cant(target["text"].replace("/", ""))
            if ex["surface_form"] != expected_surface:
                fail(f"{tag}/{ex['ref']}: surface_form {ex['surface_form']!r} != independent extraction {expected_surface!r}")
            if ex["transliteration"] != transliterate(expected_surface):
                fail(f"{tag}/{ex['ref']}: transliteration {ex['transliteration']!r} != transliterate(surface_form)")

            ids_in_verse = [w["id"] for w in words]
            target_pos = ids_in_verse.index(ex["word_id"])
            shipped_word_count = len(ex["phrase_hebrew"].split(" "))
            found = False
            for si in range(max(0, target_pos - shipped_word_count + 1), target_pos + 1):
                ei = si + shipped_word_count - 1
                if ei >= len(words) or ei < target_pos:
                    continue
                window = words[si:ei + 1]
                window_clean = [strip_cant(w["text"].replace("/", "")) for w in window]
                if " ".join(window_clean) == ex["phrase_hebrew"]:
                    found = True
                    expected_translit = " ".join(transliterate(w) for w in window_clean)
                    if ex["phrase_transliteration"] != expected_translit:
                        fail(f"{tag}/{ex['ref']}: phrase_transliteration != per-word transliterate() rejoined with spaces")
                    expected_target_index = target_pos - si
                    if ex["target_index"] != expected_target_index:
                        fail(f"{tag}/{ex['ref']}: target_index={ex['target_index']} but word_id sits at position {expected_target_index} in the re-sliced phrase")
                    break
            if not found:
                fail(f"{tag}/{ex['ref']}: phrase_hebrew {ex['phrase_hebrew']!r} is not a contiguous span of {ex['word_id']!r}'s verse containing that word")

            for field in ("surface_form", "phrase_hebrew"):
                v = ex[field]
                if not v or not ALLOWED_HEB_RE.match(v):
                    fail(f"{tag}/{ex['ref']}: {field} missing or has unexpected characters: {v!r}")
            for field in ("transliteration", "phrase_transliteration"):
                v = ex[field]
                if not v or not ALLOWED_TRANSLIT_RE.match(v):
                    fail(f"{tag}/{ex['ref']}: {field} {v!r} is empty or outside the locked ASCII scheme")
            if not ex["gloss"] or not ex["gloss"].strip():
                fail(f"{tag}/{ex['ref']}: empty gloss")

            if not ex.get("gloss_highlight") or ex["gloss_highlight"] not in ex["gloss"]:
                fail(f"{tag}/{ex['ref']}: gloss_highlight {ex.get('gloss_highlight')!r} is not a substring of gloss {ex['gloss']!r}")
            note = ex.get("gloss_note")
            if note is not None and not note.strip():
                fail(f"{tag}/{ex['ref']}: gloss_note is present but empty/whitespace")

    total = sum(len(e["examples"]) for e in entries)
    print(f"Checked {len(entries)} lemmas ({total} examples) curated, "
          f"{len(skipped_ids)} skipped, {len(pending)} pending of {len(expected_targets)} targets, "
          "against an independent corpus re-scan.")

    if failures:
        print(f"\n{len(failures)} FAILURE(S)", file=sys.stderr)
        sys.exit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()

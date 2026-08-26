"""
Independent verification of data/function_word_examples.json (suggestion 3:
every generation step ships a verification script).

Deliberately does NOT import build_function_word_examples.py -- the corpus
is re-scanned here with its own regex over the raw XML bytes, and the
target lemma set is independently re-derived from vocab_deck_600.json, so
a bug specific to one implementation is unlikely to be invisible to both.

Checks:
  1. The target lemma set (F-<letter> entries plus Preposition/Conjunction/
     Particle/Definite article/Interrogative particle/Relative particle
     vocab entries) matches the shipped file's lemma list exactly -- no
     lemma silently missing or extra.
  2. Every entry has example_count >= max(TIER_TARGET, comma-separated
     senses in its own full_gloss) -- TIER_TARGET is redeclared here
     independently of build_function_word_examples.py's copy, so a lemma
     dropped from one list without the other is caught.
  3. Every example's word_id is independently found in the claimed verse
     of the claimed book, its lemma independently resolves to the entry's
     lemma_id (function-code letter or Strong's number), and its
     surface_form/transliteration/phrase_hebrew/phrase_transliteration
     match an independent re-extraction from the corpus exactly -- the
     phrase is re-sliced from the verse's own word list by finding the
     first and last word of phrase_hebrew's word count anchored at
     word_id's position, not by trusting the shipped text.
  4. The target word_id actually falls inside its own claimed phrase, and
     target_index (the Hebrew word to highlight) is exactly its position
     within that independently re-sliced phrase.
  5. Character-set sanity on every surface_form/phrase_hebrew/
     transliteration/phrase_transliteration.
  6. No duplicate (lemma_id, ref, word_id) example.
  7. gloss_highlight (the English word(s) to highlight) is a literal
     substring of gloss; gloss_note, when present, is non-empty.
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
DATA_PATH = os.path.join(HERE, "..", "data", "function_word_examples.json")

CANTILLATION_RE = re.compile("[֑-֯]")
ALLOWED_HEB_RE = re.compile(r"^[֑-ׇ͏א-ת ]*$")
ALLOWED_TRANSLIT_RE = re.compile(r"^['`a-z .,;:!?‘’]+$")

TIER_TARGET = {
    "F-l": 10, "F-b": 10, "F-m": 10, "H4480": 10, "H5921": 10, "H3588": 10,
    "F-k": 10, "H5704": 10, "H310": 10, "H8478": 10, "H5048": 10,
}

TARGET_POS = {
    "Preposition", "Conjunction", "Particle",
    "Definite article", "Interrogative particle", "Relative particle",
}

failures = []


def fail(msg):
    failures.append(msg)
    print(f"FAIL: {msg}", file=sys.stderr)


def strip_cant(s):
    return CANTILLATION_RE.sub("", s)


def independent_target_set():
    with open(DECK_PATH, encoding="utf-8") as f:
        deck = json.load(f)
    out = {}
    for e in deck["entries"]:
        if e["lemma_id"].startswith("F-") or e["pos"] in TARGET_POS:
            out[e["lemma_id"]] = e
    return out


def word_matches_lemma(lemma_parts, lemma_id):
    for lp_raw in lemma_parts:
        lp = lp_raw.strip()
        if lemma_id.startswith("F-"):
            if lp == lemma_id[2:]:
                return True
        else:
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
        sys.exit("data/function_word_examples.json not found -- run pipeline/build_function_word_examples.py first")

    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    entries = data["entries"]

    # --- 1. target lemma set matches exactly ------------------------------
    expected_targets = independent_target_set()
    shipped_ids = {e["lemma_id"] for e in entries}
    missing = set(expected_targets) - shipped_ids
    extra = shipped_ids - set(expected_targets)
    if missing:
        fail(f"lemmas missing from function_word_examples.json: {sorted(missing)}")
    if extra:
        fail(f"function_word_examples.json has lemmas outside the target set: {sorted(extra)}")

    seen_examples = set()
    book_cache = {}

    for e in entries:
        lemma_id = e["lemma_id"]
        tag = f"{lemma_id} ({e['citation_form']})"

        # --- 2. example count rule -----------------------------------------
        senses = [s.strip() for s in e["full_gloss"].split(",") if s.strip()]
        needed = max(TIER_TARGET.get(e["lemma_id"], 3), len(senses))
        if e["sense_count"] != len(senses):
            fail(f"{tag}: sense_count={e['sense_count']} but independent split of full_gloss gives {len(senses)}")
        if len(e["examples"]) < needed:
            fail(f"{tag}: needs >= {needed} examples (gloss {e['full_gloss']!r}), has {len(e['examples'])}")

        deck_e = expected_targets.get(lemma_id)
        if deck_e is None:
            continue  # already reported under check 1
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

            # --- 3/4. independently re-slice the phrase from the verse's own
            # word list, anchored at word_id, and confirm it matches exactly
            # what shipped. The shipped phrase's word count tells us how
            # many verse words to expect either side of the target; we then
            # confirm those clean-joined words equal phrase_hebrew, which
            # only holds if the boundaries are exactly right.
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

            # --- 5. character-set sanity -------------------------------------
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

            # --- 7. gloss_highlight / gloss_note sanity -----------------------
            if not ex.get("gloss_highlight") or ex["gloss_highlight"] not in ex["gloss"]:
                fail(f"{tag}/{ex['ref']}: gloss_highlight {ex.get('gloss_highlight')!r} is not a substring of gloss {ex['gloss']!r}")
            note = ex.get("gloss_note")
            if note is not None and not note.strip():
                fail(f"{tag}/{ex['ref']}: gloss_note is present but empty/whitespace")

    total = sum(len(e["examples"]) for e in entries)
    if data["metadata"]["example_count"] != total:
        fail(f"metadata.example_count={data['metadata']['example_count']} but {total} examples present")
    if data["metadata"]["lemma_count"] != len(entries):
        fail(f"metadata.lemma_count={data['metadata']['lemma_count']} but {len(entries)} entries present")

    print(f"Checked {len(entries)} lemmas, {total} examples, against an independent corpus re-scan.")

    if failures:
        print(f"\n{len(failures)} FAILURE(S)", file=sys.stderr)
        sys.exit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()

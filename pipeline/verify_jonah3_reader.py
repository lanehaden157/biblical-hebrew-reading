"""
Independent verification of data/jonah3_reader.json (rule 3).

Sibling of verify_jonah1_reader.py / verify_jonah2_reader.py -- deliberately
does NOT import build_jonah3_reader.py. Re-scans the raw WLC XML with its
own regex, re-derives its own gloss lookup from vocab_deck_600.json plus
jonah1_extra.json/jonah2_extra.json/jonah3_extra.json, and recomputes every
word's surface form, transliteration, gloss and is_known flag from scratch,
then diffs against the shipped JSON entry-by-entry.

Checks performed: same six as verify_jonah1_reader.py, scoped to Jonah 3's
10 verses.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hebrew_corpus import WLC_DIR
from transliterate import transliterate

HERE = os.path.dirname(os.path.abspath(__file__))
VOCAB_PATH = os.path.join(HERE, "..", "data", "vocab_deck_600.json")
EXTRA_PATHS = [
    os.path.join(HERE, "..", "glosses", "jonah1_extra.json"),
    os.path.join(HERE, "..", "glosses", "jonah2_extra.json"),
    os.path.join(HERE, "..", "glosses", "jonah3_extra.json"),
]
DATA_PATH = os.path.join(HERE, "..", "data", "jonah3_reader.json")

CANTILLATION_RE = re.compile("[֑-֯]")
ALLOWED_HEB_RE = re.compile("^[ְ-ׇא-ת]*$")
ALLOWED_TRANSLIT_RE = re.compile(r"^['`a-z]+$")

VERSE_RE = re.compile(r'<verse osisID="(Jonah\.3\.\d+)">(.*?)</verse>', re.S)
WORD_RE = re.compile(r'<w\b([^>]*)>(.*?)</w>', re.S)
ATTR_RE = lambda name: re.compile(rf'{name}="([^"]*)"')
ID_ATTR_RE = ATTR_RE("id")
LEMMA_ATTR_RE = ATTR_RE("lemma")

failures = []


def fail(msg):
    failures.append(msg)
    print(f"FAIL: {msg}", file=sys.stderr)


def strip_cantillation(s):
    return CANTILLATION_RE.sub("", s)


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)


def load_gloss_lookup():
    with open(VOCAB_PATH, encoding="utf-8") as f:
        vocab = json.load(f)
    lookup = {}
    known_ids = set()
    for e in vocab["entries"]:
        lookup[e["lemma_id"]] = e["gloss"]
        known_ids.add(e["lemma_id"])
    for path in EXTRA_PATHS:
        with open(path, encoding="utf-8") as f:
            extra = json.load(f)
        for e in extra["entries"]:
            lookup[e["lemma_id"]] = e["gloss"]
    return lookup, known_ids


def rescan(lookup, known_ids):
    """Independent regex pass over Jonah.xml, restricted to chapter 3."""
    path = os.path.join(WLC_DIR, "Jonah.xml")
    with open(path, encoding="utf-8") as f:
        content = f.read()

    verses = []
    for vid, vinner in VERSE_RE.findall(content):
        words = []
        for attrs, inner in WORD_RE.findall(vinner):
            id_m = ID_ATTR_RE.search(attrs)
            lemma_m = LEMMA_ATTR_RE.search(attrs)
            raw_text = strip_tags(inner)
            if not lemma_m or not raw_text:
                continue
            surface = strip_cantillation(raw_text.replace("/", ""))
            if not surface:
                continue

            lemma_ids, glosses, all_known = [], [], True
            unresolved = False
            for lp in lemma_m.group(1).split("/"):
                lp = lp.strip()
                if not lp:
                    continue
                num_m = re.match(r"^(\d+)", lp)
                if num_m:
                    lemma_id = "H" + num_m.group(1)
                elif re.match(r"^[a-z]$", lp):
                    lemma_id = "F-" + lp
                else:
                    unresolved = True
                    continue
                if lemma_id not in lookup:
                    unresolved = True
                    continue
                lemma_ids.append(lemma_id)
                glosses.append(lookup[lemma_id])
                if lemma_id not in known_ids:
                    all_known = False

            if unresolved or not lemma_ids:
                continue

            words.append({
                "id": id_m.group(1) if id_m else None,
                "surface_form": surface,
                "transliteration": transliterate(surface),
                "gloss": " + ".join(glosses),
                "is_known": all_known,
                "lemma_ids": lemma_ids,
            })
        verses.append({"ref": vid, "verse_num": int(vid.rsplit(".", 1)[1]), "words": words})

    verses.sort(key=lambda v: v["verse_num"])
    return verses


def main():
    if not os.path.isfile(DATA_PATH):
        sys.exit("data/jonah3_reader.json not found -- run pipeline/build_jonah3_reader.py first")

    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    meta, verses = data["metadata"], data["verses"]

    # --- 1. metadata counts -----------------------------------------------
    all_words = [w for v in verses for w in v["words"]]
    if meta["verse_count"] != len(verses):
        fail(f"metadata.verse_count={meta['verse_count']} but {len(verses)} verses present")
    if meta["word_count"] != len(all_words):
        fail(f"metadata.word_count={meta['word_count']} but {len(all_words)} words present")

    distinct_lemmas = {lid for w in all_words for lid in w["lemma_ids"]}
    if meta["distinct_lemma_count"] != len(distinct_lemmas):
        fail(f"metadata.distinct_lemma_count={meta['distinct_lemma_count']} but recount got {len(distinct_lemmas)}")

    known_count = sum(1 for w in all_words if w["is_known"])
    if meta["words_already_known_count"] != known_count:
        fail(f"metadata.words_already_known_count={meta['words_already_known_count']} but recount got {known_count}")

    # --- 2/3. character-set sanity + non-empty gloss -----------------------
    lookup, known_ids = load_gloss_lookup()
    for v in verses:
        for w in v["words"]:
            tag = f"{w['id']} ({v['ref']})"
            if not w["surface_form"] or not ALLOWED_HEB_RE.match(w["surface_form"]):
                fail(f"{tag}: surface_form missing or has unexpected characters: {w['surface_form']!r}")
            if not w["transliteration"] or not ALLOWED_TRANSLIT_RE.match(w["transliteration"]):
                fail(f"{tag}: transliteration {w['transliteration']!r} is empty or outside the locked ASCII scheme")
            if not w["gloss"]:
                fail(f"{tag}: empty gloss")

            # --- 4. every lemma_id resolves, is_known agrees -------------
            expected_known = all(lid in known_ids for lid in w["lemma_ids"])
            if w["is_known"] != expected_known:
                fail(f"{tag}: is_known={w['is_known']} but lemma_ids {w['lemma_ids']} implies {expected_known}")
            expected_gloss = " + ".join(lookup[lid] for lid in w["lemma_ids"] if lid in lookup)
            if w["gloss"] != expected_gloss:
                fail(f"{tag}: gloss {w['gloss']!r} != recomputed {expected_gloss!r}")

    unknown_lemmas = {lid for lid in distinct_lemmas if lid not in known_ids}
    if meta["unknown_lemma_count"] != len(unknown_lemmas):
        fail(f"metadata.unknown_lemma_count={meta['unknown_lemma_count']} but recount got {len(unknown_lemmas)}")

    # --- 6. no duplicate word ids ------------------------------------------
    ids = [w["id"] for v in verses for w in v["words"]]
    if len(ids) != len(set(ids)):
        fail("duplicate word ids present")

    # --- 5. independent regex re-scan of the corpus ------------------------
    print("Re-scanning Jonah 3 independently (regex-based)...")
    expected_verses = rescan(lookup, known_ids)

    if len(expected_verses) != len(verses):
        fail(f"independent re-scan found {len(expected_verses)} verses, JSON has {len(verses)}")
    else:
        for exp_v, got_v in zip(expected_verses, verses):
            if exp_v["ref"] != got_v["ref"]:
                fail(f"verse order mismatch: expected {exp_v['ref']}, got {got_v['ref']}")
                continue
            if len(exp_v["words"]) != len(got_v["words"]):
                fail(f"{exp_v['ref']}: expected {len(exp_v['words'])} words, JSON has {len(got_v['words'])}")
                continue
            for exp_w, got_w in zip(exp_v["words"], got_v["words"]):
                if exp_w != got_w:
                    fail(f"{exp_v['ref']} word {got_w.get('id')}: mismatch\n  expected={exp_w}\n  got     ={got_w}")

    print(f"Checked {len(verses)} verses, {len(all_words)} words.")

    if failures:
        print(f"\n{len(failures)} FAILURE(S)", file=sys.stderr)
        sys.exit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()

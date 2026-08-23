"""
Phase 5 step 5: OSHB corpus -> word-aligned Jonah 3 reading data ->
data/jonah3_reader.json.

Sibling of build_jonah1_reader.py / build_jonah2_reader.py -- same
word-per-printed-word approach, same "no grading, no scheduler state, no
per-word part of speech" design (see build_jonah1_reader.py's docstring for
the full rationale, unchanged here).

Gloss sources: data/vocab_deck_600.json, glosses/jonah1_extra.json,
glosses/jonah2_extra.json, and glosses/jonah3_extra.json (curated by
pipeline/curate_jonah3_extra.py for the 12 lemmas genuinely new to this
chapter). An unresolved lemma is a hard error, not a silent skip (rule 4).

Chapter scope: 10 verses (Jonah.3.1-Jonah.3.10). No Hebrew/English
versification divergence in this chapter.

Run pipeline/curate_jonah3_extra.py first (needs glosses/jonah3_extra.json).
"""
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hebrew_corpus import OSIS_NS, WLC_DIR
from transliterate import transliterate

HERE = os.path.dirname(os.path.abspath(__file__))
VOCAB_PATH = os.path.join(HERE, "..", "data", "vocab_deck_600.json")
EXTRA_PATHS = [
    os.path.join(HERE, "..", "glosses", "jonah1_extra.json"),
    os.path.join(HERE, "..", "glosses", "jonah2_extra.json"),
    os.path.join(HERE, "..", "glosses", "jonah3_extra.json"),
]
OUT_PATH = os.path.join(HERE, "..", "data", "jonah3_reader.json")

CANTILLATION_RE = re.compile("[֑-֯]")
EXPECTED_VERSE_COUNT = 10
CHAPTER_PREFIX = "Jonah.3."


def strip_cantillation(s):
    return CANTILLATION_RE.sub("", s)


def load_glosses():
    """lemma_id -> {gloss, citation_form} across vocab deck + prior Jonah extras."""
    with open(VOCAB_PATH, encoding="utf-8") as f:
        vocab = json.load(f)
    lookup = {}
    known_ids = set()
    for e in vocab["entries"]:
        lookup[e["lemma_id"]] = {"gloss": e["gloss"], "citation_form": e["citation_form"]}
        known_ids.add(e["lemma_id"])

    for path in EXTRA_PATHS:
        if not os.path.isfile(path):
            sys.exit(f"{os.path.basename(path)} not found -- run its curate_*.py first")
        with open(path, encoding="utf-8") as f:
            extra = json.load(f)
        for e in extra["entries"]:
            lookup[e["lemma_id"]] = {"gloss": e["gloss"], "citation_form": e["citation_form"]}

    return lookup, known_ids


def main():
    if not os.path.isfile(VOCAB_PATH):
        sys.exit("data/vocab_deck_600.json not found -- run pipeline/build_vocab_deck.py first")
    if not os.path.isdir(WLC_DIR):
        sys.exit("pipeline/corpus/wlc not found -- run pipeline/fetch_corpus.py first")

    gloss_lookup, known_ids = load_glosses()

    path = os.path.join(WLC_DIR, "Jonah.xml")
    root = ET.parse(path).getroot()

    verses = []
    unresolved = []
    word_count = 0

    for verse in root.iter(f"{OSIS_NS}verse"):
        vid = verse.get("osisID")
        if not vid or not vid.startswith(CHAPTER_PREFIX):
            continue
        verse_num = int(vid.rsplit(".", 1)[1])

        words = []
        for w in verse.iter(f"{OSIS_NS}w"):
            wid = w.get("id")
            raw_lemma = w.get("lemma")
            raw_text = w.text or ""
            if not raw_lemma or not raw_text:
                continue

            surface = strip_cantillation(raw_text.replace("/", ""))
            if not surface:
                continue

            lemma_ids = []
            glosses = []
            all_known = True
            for lp in raw_lemma.split("/"):
                lp = lp.strip()
                if not lp:
                    continue
                m = re.match(r"^(\d+)", lp)
                if m:
                    lemma_id = "H" + m.group(1)
                elif re.match(r"^[a-z]$", lp):
                    lemma_id = "F-" + lp
                else:
                    unresolved.append({"verse": vid, "word": wid, "raw_lemma": raw_lemma, "part": lp})
                    continue

                entry = gloss_lookup.get(lemma_id)
                if entry is None:
                    unresolved.append({"verse": vid, "word": wid, "lemma_id": lemma_id, "raw_lemma": raw_lemma})
                    continue

                lemma_ids.append(lemma_id)
                glosses.append(entry["gloss"])
                if lemma_id not in known_ids:
                    all_known = False

            if not lemma_ids:
                continue

            word_count += 1
            words.append({
                "id": wid or f"{vid}-{word_count}",
                "surface_form": surface,
                "transliteration": transliterate(surface),
                "gloss": " + ".join(glosses),
                "is_known": all_known,
                "lemma_ids": lemma_ids,
            })

        verses.append({"ref": vid, "verse_num": verse_num, "words": words})

    verses.sort(key=lambda v: v["verse_num"])

    if len(verses) != EXPECTED_VERSE_COUNT:
        print(
            f"NOTE: found {len(verses)} verses in Jonah 3, expected {EXPECTED_VERSE_COUNT}. "
            f"If morphhb's versification changed, update EXPECTED_VERSE_COUNT deliberately, "
            f"don't just silence this.",
            file=sys.stderr,
        )

    if unresolved:
        sys.exit(
            f"{len(unresolved)} word(s) had a lemma with no gloss in any known gloss source -- "
            f"rule 4 requires every shown form to have a gloss. First few: {unresolved[:5]}"
        )

    distinct_lemmas = {lid for v in verses for w in v["words"] for lid in w["lemma_ids"]}
    unknown_lemmas = {lid for lid in distinct_lemmas if lid not in known_ids}
    known_word_count = sum(1 for v in verses for w in v["words"] if w["is_known"])

    out = {
        "metadata": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "chapter": "Jonah 3",
            "versification": "Hebrew/WLC (10 verses; no divergence from English here)",
            "verse_count": len(verses),
            "word_count": word_count,
            "distinct_lemma_count": len(distinct_lemmas),
            "unknown_lemma_count": len(unknown_lemmas),
            "words_already_known_count": known_word_count,
            "gloss_sources": [
                "data/vocab_deck_600.json",
                "glosses/jonah1_extra.json",
                "glosses/jonah2_extra.json",
                "glosses/jonah3_extra.json",
            ],
        },
        "verses": verses,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(verses)} verses, {word_count} words to {OUT_PATH}")
    print(f"Distinct lemmas: {len(distinct_lemmas)} ({len(unknown_lemmas)} not in vocab_deck_600)")
    print(f"Words already known: {known_word_count}/{word_count} ({known_word_count / word_count * 100:.1f}%)")


if __name__ == "__main__":
    main()

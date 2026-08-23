"""
Phase 4 step 2: OSHB corpus -> word-aligned Jonah 1 reading data ->
data/jonah1_reader.json.

This is a reading aid, not another SRS deck (CLAUDE.md's Phase 4 note: the
goal is fluency practice on real connected text, not new recall cards).
There is no grading and no scheduler state -- every word in the chapter is
always available, tap-to-reveal, every time the page opens.

Word granularity: one entry per OSHB <w> element, i.e. one entry per
PRINTED word, exactly as it appears on the page (a prefixed vav or
preposition is never pulled out into its own visual token -- that would
show Hebrew that doesn't actually look like Hebrew). Internally, a printed
word can bundle several lemma morphemes (e.g. "va-yomer" = vav-consecutive +
"say"); each morpheme's own gloss is looked up separately and the whole
word's displayed gloss is the morphemes' glosses joined with " + ", in
reading order. This mirrors how build_parse_qal.py and rank_lemmas.py
already split a word's lemma/morph/text attributes on "/" per morpheme --
same technique, applied to build a combined gloss instead of a single
citation form.

A word's part of speech is deliberately NOT computed or stored here. Tier 2
only covers Qal strong verbs (see build_parse_qal.py); Jonah 1 contains
weak roots and other stems that Lane hasn't formally studied yet, and
CLAUDE.md's locked sequencing ("grammar-led, real text early") means this
reader is meant to run ahead of that coverage, not pretend to explain it.
A lemma-level POS label would also sometimes be flat wrong for a specific
occurrence -- see H3373 in curate_jonah1_extra.py's docstring, tagged with
one Strong's number across both a finite verb and a noun form in this very
chapter. Showing nothing beats showing a wrong grammatical claim.

Glosses come from two sources, merged: data/vocab_deck_600.json for any
lemma Lane is already drilling, and glosses/jonah1_extra.json (curated by
pipeline/curate_jonah1_extra.py) for the rest. Every lemma actually used in
Jonah 1 must resolve to one or the other; an unresolved lemma is a hard
error, not a silent skip, precisely so a future corpus/version change can't
quietly ship an ungloseed word (rule 4).

Chapter scope: Hebrew (WLC/BHS) versification, which numbers Jonah 1 as 16
verses. What English Bibles print as Jonah 1:17 (swallowed by the fish) is
Jonah 2:1 in the Hebrew text -- deliberately left for the chapter 2 reading
rather than stitched onto the end of this one; see the corpus comment this
script prints if it doesn't find exactly 16 verses.

Text is never NFC/NFD-normalized (CLAUDE.md rule 2) -- only cantillation
(U+0591-U+05AF) is stripped, matching every other pipeline script.

Run pipeline/curate_jonah1_extra.py first (needs glosses/jonah1_extra.json).
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
EXTRA_GLOSS_PATH = os.path.join(HERE, "..", "glosses", "jonah1_extra.json")
OUT_PATH = os.path.join(HERE, "..", "data", "jonah1_reader.json")

CANTILLATION_RE = re.compile("[֑-֯]")
EXPECTED_VERSE_COUNT = 16


def strip_cantillation(s):
    return CANTILLATION_RE.sub("", s)


def load_glosses():
    """lemma_id -> {gloss, citation_form} across vocab deck + Jonah-1 extras."""
    with open(VOCAB_PATH, encoding="utf-8") as f:
        vocab = json.load(f)
    lookup = {}
    known_ids = set()
    for e in vocab["entries"]:
        lookup[e["lemma_id"]] = {"gloss": e["gloss"], "citation_form": e["citation_form"]}
        known_ids.add(e["lemma_id"])

    if not os.path.isfile(EXTRA_GLOSS_PATH):
        sys.exit("glosses/jonah1_extra.json not found -- run pipeline/curate_jonah1_extra.py first")
    with open(EXTRA_GLOSS_PATH, encoding="utf-8") as f:
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
        if not vid or not vid.startswith("Jonah.1."):
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
            f"NOTE: found {len(verses)} verses in Jonah 1, expected {EXPECTED_VERSE_COUNT} "
            f"(Hebrew/WLC versification -- English 1:17 is Hebrew 2:1). "
            f"If morphhb's versification changed, update EXPECTED_VERSE_COUNT deliberately, "
            f"don't just silence this.",
            file=sys.stderr,
        )

    if unresolved:
        sys.exit(
            f"{len(unresolved)} word(s) had a lemma with no gloss in either vocab_deck_600 "
            f"or jonah1_extra -- rule 4 requires every shown form to have a gloss. "
            f"First few: {unresolved[:5]}"
        )

    distinct_lemmas = {lid for v in verses for w in v["words"] for lid in w["lemma_ids"]}
    unknown_lemmas = {lid for lid in distinct_lemmas if lid not in known_ids}
    known_word_count = sum(1 for v in verses for w in v["words"] if w["is_known"])

    out = {
        "metadata": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "chapter": "Jonah 1",
            "versification": "Hebrew/WLC (16 verses; English 1:17 = Hebrew 2:1, not included)",
            "verse_count": len(verses),
            "word_count": word_count,
            "distinct_lemma_count": len(distinct_lemmas),
            "unknown_lemma_count": len(unknown_lemmas),
            "words_already_known_count": known_word_count,
            "gloss_sources": ["data/vocab_deck_600.json", "glosses/jonah1_extra.json"],
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

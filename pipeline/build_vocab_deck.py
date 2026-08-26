"""
Phase 2 step 3, data-prep half: merge all six curated gloss batches
(ranks 1-600, the full CLAUDE.md vocabulary target) into a single vocab
deck for the SRS app, adding a transliteration field to every entry
(rule 4: every Hebrew form shown to the user gets transliteration +
gloss).

The deck file holding all ~600 doesn't mean the app has to introduce all
of them as new cards at once -- new-card-per-day pacing (so a gap in usage
never shows a wall of due cards, per CLAUDE.md's hard rule) is an app/UI
concern, not a data one. Building the full deck now just means that
pacing decision doesn't require a second data-prep pass later.

Reads all six glosses/batch_*.json files (already curated and reviewed --
see those files' docstrings/notes for curation decisions). Writes
data/vocab_deck_600.json for the app to load directly; no build step, per
the repo layout.

Two curation-stage filters, applied here rather than at rank_lemmas.py
(which measures the whole-Bible corpus honestly, Aramaic and poetry
included -- filtering belongs at the curriculum-judgment stage, same as
the existing "Pual/Hophal: recognition only" call):

- EXCLUDED_LEMMAS drops 4 Aramaic loanwords (Ezra 4-6 pulled them into the
  top 600 by raw frequency; this project teaches Hebrew) and 2 poetry-only
  particles (selah -- meaning uncertain, liturgical; bal -- a poetic
  variant of lo'/'al already taught) that entered the top 600 for reasons
  unrelated to the reading goal. Ranks aren't backfilled to stay at a
  round 600 -- the deck is just 594 entries; CLAUDE.md's "~600" already
  says approximate.
- NON_DRILL_LEMMAS keeps a word in the deck (visible, marked "known" for
  readers/lessons) but excludes it from the SRS queue. H853 ('et, the
  direct-object marker) has no English translation at all -- it cannot be
  recalled from a gloss, only recognized by exposure while reading.
"""
import json
import os

from transliterate import transliterate

HERE = os.path.dirname(os.path.abspath(__file__))
GLOSSES_DIR = os.path.join(HERE, "..", "glosses")
OUT_PATH = os.path.join(HERE, "..", "data", "vocab_deck_600.json")

BATCH_FILES = [
    "batch_001_100.json",
    "batch_101_200.json",
    "batch_201_300.json",
    "batch_301_400.json",
    "batch_401_500.json",
    "batch_501_600.json",
]

EXCLUDED_LEMMAS = {
    "H1768": "Aramaic (di, Ezra)",
    "H4481": "Aramaic (min, Ezra)",
    "H5922": "Aramaic (`al, Ezra)",
    "H3809": "Aramaic (la', Ezra)",
    "H4430": "Aramaic (king, Ezra/Daniel)",
    "H3606": "Aramaic (all/every, Ezra/Daniel)",
    "H426": "Aramaic (God, Ezra/Daniel)",
    "H1934": "Aramaic (be/become, Ezra/Daniel)",
    "H560": "Aramaic (say, Ezra/Daniel)",
    "H5542": "poetry-only, meaning uncertain (selah)",
    "H1077": "poetry-only negative particle (bal)",
}

NON_DRILL_LEMMAS = {
    "H853": "direct-object marker, usually untranslated -- not recallable from a gloss",
}

# Mirrors build_function_word_examples.py's TARGET_POS exactly, so "is this
# a function word" means the same thing everywhere in the project.
FUNCTION_POS = {
    "Preposition", "Conjunction", "Particle",
    "Definite article", "Interrogative particle", "Relative particle",
}


def is_function_word(lemma_id, pos):
    return lemma_id.startswith("F-") or pos in FUNCTION_POS


def main():
    raw = []
    for fname in BATCH_FILES:
        with open(os.path.join(GLOSSES_DIR, fname), encoding="utf-8") as f:
            batch = json.load(f)
        raw.extend(batch["entries"])

    raw.sort(key=lambda e: e["rank"])

    entries = []
    new_rank = 0
    for e in raw:
        if e["lemma_id"] in EXCLUDED_LEMMAS:
            continue
        new_rank += 1
        out_entry = {
            "rank": new_rank,
            "source_rank": e["rank"],
            "lemma_id": e["lemma_id"],
            "citation_form": e["citation_form"],
            "transliteration": transliterate(e["citation_form"]),
            "pos": e["pos"],
            "frequency": e["frequency"],
            "gloss": e["gloss"],
            "is_function_word": is_function_word(e["lemma_id"], e["pos"]),
            "drillable": e["lemma_id"] not in NON_DRILL_LEMMAS,
        }
        if "core_schema" in e:
            out_entry["core_schema"] = e["core_schema"]
        entries.append(out_entry)

    out = {
        "metadata": {
            "rank_range": [1, len(entries)],
            "count": len(entries),
            "source_batches": BATCH_FILES,
            "excluded": [{"lemma_id": k, "reason": v} for k, v in EXCLUDED_LEMMAS.items()],
            "non_drill": [{"lemma_id": k, "reason": v} for k, v in NON_DRILL_LEMMAS.items()],
        },
        "entries": entries,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(entries)} deck entries to {OUT_PATH}")


if __name__ == "__main__":
    main()

"""
Phase 2 step 3, data-prep half: merge all six curated gloss batches
(ranks 1-600, the full CLAUDE.md vocabulary target) into a single vocab
deck for the SRS app, adding a transliteration field to every entry
(rule 4: every Hebrew form shown to the user gets transliteration +
gloss).

The deck file holding all 600 doesn't mean the app has to introduce all
600 as new cards at once -- new-card-per-day pacing (so a gap in usage
never shows a wall of due cards, per CLAUDE.md's hard rule) is an app/UI
concern, not a data one. Building the full deck now just means that
pacing decision doesn't require a second data-prep pass later.

Reads all six glosses/batch_*.json files (already curated and reviewed --
see those files' docstrings/notes for curation decisions). Writes
data/vocab_deck_600.json for the app to load directly; no build step, per
the repo layout.
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


def main():
    entries = []
    for fname in BATCH_FILES:
        with open(os.path.join(GLOSSES_DIR, fname), encoding="utf-8") as f:
            batch = json.load(f)
        for e in batch["entries"]:
            entries.append({
                "rank": e["rank"],
                "lemma_id": e["lemma_id"],
                "citation_form": e["citation_form"],
                "transliteration": transliterate(e["citation_form"]),
                "pos": e["pos"],
                "frequency": e["frequency"],
                "gloss": e["gloss"],
            })
    entries.sort(key=lambda e: e["rank"])

    out = {
        "metadata": {
            "rank_range": [1, 600],
            "count": len(entries),
            "source_batches": BATCH_FILES,
        },
        "entries": entries,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(entries)} deck entries to {OUT_PATH}")


if __name__ == "__main__":
    main()

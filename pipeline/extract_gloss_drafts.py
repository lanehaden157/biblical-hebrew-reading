"""
Phase 2 step 2, extraction half: pull Strong's raw meaning/usage/def data
for a batch of top600.json lemmas into a draft file for curation.

This is explicitly NOT curated -- CLAUDE.md is clear that Strong's meaning
is "a usable draft but archaic and sometimes misleading" and must be
curated before shipping. This script only gathers the raw material; nothing
here should be treated as a final gloss.

Batched ~100 lemmas at a time per CLAUDE.md's stated curation workflow.
"""
import json
import os
import sys
import xml.etree.ElementTree as ET

from hebrew_corpus import LEXICON_PATH, LEX_NS

HERE = os.path.dirname(os.path.abspath(__file__))
TOP600_PATH = os.path.join(HERE, "..", "data", "top600.json")

# Usage: python extract_gloss_drafts.py [start] [end]  (inclusive, by rank; default 1 100)
BATCH_START = int(sys.argv[1]) if len(sys.argv) > 1 else 1
BATCH_END = int(sys.argv[2]) if len(sys.argv) > 2 else 100
OUT_PATH = os.path.join(HERE, "..", "data", f"gloss_drafts_{BATCH_START:03d}_{BATCH_END:03d}.json")

# The 8 bound function morphemes carry no Strong's number, so there's no
# lexicon entry to draft from. These hand-typed drafts are plain English,
# not Hebrew, so CLAUDE.md rule 1 (never hand-type pointed Hebrew) doesn't
# apply -- but they're still drafts, flagged for review like everything else.
FUNCTION_GLOSS_DRAFTS = {
    "c": "and",
    "d": "the",
    "l": "to, for",
    "b": "in, on, with, by",
    "m": "from",
    "k": "like, as",
    "i": "(marks a yes/no question)",
    "s": "that, which",
}


def load_lexicon_meanings():
    root = ET.parse(LEXICON_PATH).getroot()
    out = {}
    for entry in root.findall(f"{LEX_NS}entry"):
        eid = entry.get("id")
        if not eid or not eid.startswith("H"):
            continue
        meaning_el = entry.find(f"{LEX_NS}meaning")
        usage_el = entry.find(f"{LEX_NS}usage")
        source_el = entry.find(f"{LEX_NS}source")
        defs, meaning_text = [], None
        if meaning_el is not None:
            meaning_text = "".join(meaning_el.itertext()).strip()
            defs = [d.text.strip() for d in meaning_el.findall(f"{LEX_NS}def") if d.text]
        out[eid] = {
            "meaning_text": meaning_text,
            "defs": defs,
            "usage": (usage_el.text or "").strip() if usage_el is not None else None,
            "source": "".join(source_el.itertext()).strip() if source_el is not None else None,
        }
    return out


def main():
    with open(TOP600_PATH, encoding="utf-8") as f:
        top600 = json.load(f)

    meanings = load_lexicon_meanings()
    batch = [e for e in top600["lemmas"] if BATCH_START <= e["rank"] <= BATCH_END]

    drafts, flags = [], []
    for e in batch:
        lid = e["lemma_id"]
        if lid.startswith("H"):
            m = meanings.get(lid)
            if not m or not (m["defs"] or m["meaning_text"]):
                flags.append(f"{lid} ({e['citation_form']}, rank {e['rank']}): no usable Strong's meaning")
                draft = {
                    "defs": [],
                    "meaning_text": m["meaning_text"] if m else None,
                    "usage": m["usage"] if m else None,
                    "source": m["source"] if m else None,
                }
            else:
                draft = m
        else:
            code = lid.split("-", 1)[1]
            draft = {
                "defs": [FUNCTION_GLOSS_DRAFTS[code]],
                "meaning_text": None,
                "usage": None,
                "source": "hand-typed function-word gloss, not from Strong's",
            }

        drafts.append({
            "rank": e["rank"],
            "lemma_id": lid,
            "citation_form": e["citation_form"],
            "pos": e["pos"],
            "frequency": e["frequency"],
            "oshb_codes": e["oshb_codes"],
            **draft,
            "curated_gloss": None,
        })

    out = {
        "metadata": {
            "batch_rank_range": [BATCH_START, BATCH_END],
            "status": "draft -- unreviewed Strong's/BDB extraction, see CLAUDE.md gloss curation notes",
        },
        "entries": drafts,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(drafts)} draft entries (rank {BATCH_START}-{BATCH_END}) to {OUT_PATH}")
    if flags:
        print(f"{len(flags)} entries need attention:")
        for fl in flags:
            print(" -", fl)


if __name__ == "__main__":
    main()

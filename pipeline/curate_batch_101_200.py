"""
Phase 2 step 2, curation half, batch rank 101-200.

Same approach as curate_batch_001_100.py: every gloss below was written
from what these words actually mean, then cross-checked against the
Strong's draft in data/gloss_drafts_101_200.json -- not copied from it.
Several entries deviate from the Strong's draft outright:

- H2617 (chesed): draft says "kindness; piety; reproof; beauty" -- CLAUDE.md
  names this exact word as an example of a misleading Strong's gloss
  ("chesed as mercy"); went with "kindness, loyalty, faithful love" to
  capture the covenant sense.
- H6030 (anah): draft says "eye; heed; pay attention; respond" -- "eye" is
  a Strong's artifact from an unrelated homograph sharing this number; the
  dominant Qal sense is "answer, respond, testify".
- H8269 (sar): draft says just "head" -- misleadingly narrow; this is
  "official, chief, prince" (מֶלֶךְ/H4428 already covers "king", ראש/H7218
  already covers "head").
- Proper names: Strong's transliterations ("Jaakob", "Shelomah", "Paroh",
  "Aharon") were swapped for the standard English spellings (Jacob,
  Solomon, Pharaoh, Aaron) so the gloss is actually usable at a glance.
- H136 (Adonai) vs H113 (adon): distinguished as "Lord" (divine title) vs
  "lord, master" (generic human term), since they're separate Strong's
  entries despite near-identical spelling.

H3069 (rank 167) is the alternate pointing of the divine name used when it
follows "Adonai" (avoids repeating the same word); same referent as H3068,
so glossed "YHWH" consistent with that earlier decision -- not re-asked.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DRAFTS_PATH = os.path.join(HERE, "..", "data", "gloss_drafts_101_200.json")
OUT_PATH = os.path.join(HERE, "..", "glosses", "batch_101_200.json")

CURATED = {
    "H5975": "stand",
    "H1980": "walk, go",
    "H8478": "under, instead of, in place of",
    "H505": "thousand",
    "H6963": "voice, sound",
    "H2416": "living, alive",
    "H5221": "strike, hit, kill",
    "H3205": "bear (a child), give birth, beget",
    "H6310": "mouth",
    "H6680": "command",
    "H5750": "still, yet, again",
    "H6635": "army, host",
    "H8104": "keep, guard, observe",
    "H6944": "holiness, holy thing",
    "H7227": "much, many, great",
    "H4672": "find",
    "H136": "Lord (divine title)",
    "H5769": "forever, eternity, long duration",
    "H5307": "fall",
    "H6258": "now",
    "H7969": "three",
    "H4941": "justice, judgment, ordinance",
    "H4310": "who?",
    "H8064": "heaven, sky",
    "H8269": "official, chief, prince",
    "H8432": "midst, middle",
    "H2719": "sword",
    "H996": "between",
    "H7586": "Saul",
    "H3701": "silver, money",
    "H4196": "altar",
    "H4994": "please, now (particle of entreaty)",
    "H4725": "place",
    "H3220": "sea",
    "H7651": "seven",
    "H2091": "gold",
    "H3381": "go down, descend",
    "H7307": "wind, breath, spirit",
    "H784": "fire",
    "H1129": "build",
    "H5002": "declaration, oracle",
    "H8179": "gate",
    "H5046": "tell, declare, report",
    "H1818": "blood",
    "H595": "I (emphatic)",
    "H4427": "reign, be king, become king",
    "H3290": "Jacob",
    "H168": "tent",
    "H175": "Aaron",
    "H2568": "five",
    "H6240": "ten, -teen",
    "H5439": "around, surrounding",
    "H7704": "field",
    "H1288": "bless",
    "H6086": "tree, wood",
    "H113": "lord, master",
    "H3372": "fear",
    "H6030": "answer, respond",
    "H3627": "vessel, utensil, tool",
    "H176": "or",
    "H702": "four",
    "H4421": "war, battle",
    "H2005": "behold, if",
    "H5030": "prophet",
    "H6242": "twenty",
    "H3069": "YHWH",
    "H4940": "family, clan",
    "H6485": "attend to, visit, appoint, muster",
    "H5493": "turn aside, depart",
    "H3966": "very, exceedingly",
    "H2403": "sin, sin offering",
    "H3899": "bread, food",
    "H6256": "time",
    "H8010": "Solomon",
    "H2388": "be strong, strengthen, seize",
    "H3772": "cut, cut off; make (a covenant)",
    "H6430": "Philistine",
    "H5647": "serve, work",
    "H5930": "burnt offering",
    "H3881": "Levite",
    "H1285": "covenant",
    "H341": "enemy",
    "H2320": "month, new moon",
    "H7126": "come near, approach",
    "H639": "nose, anger",
    "H6629": "flock (sheep and goats)",
    "H68": "stone",
    "H4616": "for the sake of, in order that",
    "H4057": "wilderness, desert",
    "H1320": "flesh, body",
    "H6547": "Pharaoh",
    "H2421": "live",
    "H7563": "wicked",
    "H894": "Babylon",
    "H3824": "heart, mind",
    "H4294": "tribe, staff, rod",
    "H2617": "kindness, loyalty, faithful love",
    "H7272": "foot",
    "H4390": "fill, be full",
}

# H1768 (di, "that/which") is Aramaic (Ezra 4-6) -- this project teaches
# Hebrew, so it's cut rather than curated. See build_vocab_deck.py.
EXCLUDED = {"H1768": "Aramaic (di, Ezra)"}

CORE_SCHEMA = {
    "H8478": "Under something -- literally (underneath) or by substitution (in its place, instead of).",
}


def main():
    with open(DRAFTS_PATH, encoding="utf-8") as f:
        drafts = json.load(f)["entries"]

    expected = {e["lemma_id"] for e in drafts if e["lemma_id"] not in EXCLUDED}
    if set(CURATED) != expected:
        missing = expected - set(CURATED)
        extra = set(CURATED) - expected
        raise SystemExit(f"CURATED does not match drafts minus EXCLUDED -- missing={missing} extra={extra}")

    entries = []
    for e in drafts:
        lid = e["lemma_id"]
        if lid in EXCLUDED:
            continue
        entry = {
            "rank": e["rank"],
            "lemma_id": lid,
            "citation_form": e["citation_form"],
            "pos": e["pos"],
            "frequency": e["frequency"],
            "gloss": CURATED[lid],
            "reviewed": True,
        }
        if lid in CORE_SCHEMA:
            entry["core_schema"] = CORE_SCHEMA[lid]
        entries.append(entry)
    entries.sort(key=lambda e: e["rank"])

    out = {
        "metadata": {
            "batch_rank_range": [101, 200],
            "status": "curated and reviewed",
        },
        "entries": entries,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(entries)} curated glosses to {OUT_PATH}")


if __name__ == "__main__":
    main()

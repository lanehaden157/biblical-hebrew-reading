"""
Phase 2 step 2, curation half, batch rank 301-400.

Same approach as earlier batches: every gloss below reflects what the word
actually means, cross-checked against (not copied from) the Strong's draft
in data/gloss_drafts_301_400.json. Notable deviations:

- H2490 (chalal): draft mixes two distinct verbal ideas under one Strong's
  number ("begin" vs "profane, defile") -- kept both since intro grammars
  standardly treat this as one polysemous entry, not an error to fix.
- H3034 (yadah): draft's first sense ("throw") is the etymological root
  (cognate to Arabic "throw"), not how it's actually used in Biblical Hebrew
  -- the real senses are "give thanks, praise" (Hiphil) and "confess"
  (Hitpael); went with those instead of the etymology.
- H5387 (nasi): draft includes "mist" -- a genuine but irrelevant secondary
  sense of the same root (mist "rises" like a nasi is "lifted up"); dropped,
  kept "leader, chief, prince".
- H4481 (min): draft has no defs, only a usage string and a source note
  "(Aramaic) corresponding to 4480" -- glossed directly from that as
  "from (Aramaic)", consistent with the H4430/H1768 Aramaic tags (source
  field confirmed, not inferred; see glosses/uncertainty_notes.md).
- H804 (Ashshur): covers both the nation (Assyria) and the person (Asshur,
  Genesis 10) under one Strong's number -- glossed "Assyria, Asshur" to
  cover both without overcomplicating.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DRAFTS_PATH = os.path.join(HERE, "..", "data", "gloss_drafts_301_400.json")
OUT_PATH = os.path.join(HERE, "..", "glosses", "batch_301_400.json")

CURATED = {
    "H3680": "cover",
    "H6726": "Zion",
    "H6828": "north",
    "H804": "Assyria, Asshur",
    "H5048": "in front of, opposite, before",
    "H5060": "touch, reach, strike",
    "H7230": "abundance, multitude",
    "H2451": "wisdom",
    "H5712": "congregation, assembly",
    "H7665": "break, shatter",
    "H8130": "hate",
    "H3414": "Jeremiah",
    "H7843": "destroy, ruin, corrupt",
    "H4519": "Manasseh",
    "H5265": "set out, journey, pull up (tent stakes)",
    "H3097": "Joab",
    "H5656": "service, work, labor",
    "H6605": "open",
    "H1008": "Bethel",
    "H7291": "pursue, chase",
    "H2490": "begin; profane, defile",
    "H2583": "camp, encamp",
    "F-s": "that, which, who",
    "H3162": "together, alike",
    "H3644": "like, as",
    "H227": "then, at that time",
    "H3196": "wine",
    "H3225": "right hand, right side, south",
    "H5158": "stream, wadi, valley",
    "H5483": "horse",
    "H4605": "above, upward",
    "H5178": "bronze, copper",
    "H8050": "Samuel",
    "H4908": "dwelling place, tabernacle",
    "H3426": "there is, there are",
    "H2450": "wise",
    "H3678": "throne, seat",
    "H6437": "turn, face, turn toward",
    "H705": "forty",
    "H1568": "Gilead",
    "H2076": "slaughter, sacrifice",
    "H4557": "number, count",
    "H5387": "leader, chief, prince",
    "H6153": "evening",
    "H637": "also, even, moreover",
    "H8121": "sun",
    "H2346": "wall",
    "H6435": "lest",
    "H6499": "bull, bullock",
    "H6912": "bury",
    "H758": "Aram, Syria",
    "H7604": "remain, be left over",
    "H2396": "Hezekiah",
    "H7931": "dwell, settle, abide",
    "H2706": "statute, decree, portion",
    "H3581": "strength, power",
    "H571": "truth, faithfulness",
    "H6908": "gather",
    "H6106": "bone; substance, self",
    "H5066": "approach, draw near",
    "H7993": "throw, cast",
    "H2534": "heat, wrath, anger",
    "H2803": "think, consider, plan, reckon",
    "H2677": "half",
    "H6951": "assembly, congregation",
    "H216": "light",
    "H3920": "capture, seize",
    "H587": "we",
    "H7393": "chariot, chariotry",
    "H982": "trust",
    "H269": "sister",
    "H3477": "straight, upright",
    "H5104": "river",
    "H6529": "fruit",
    "H6664": "righteousness, justice",
    "H6918": "holy",
    "H1060": "firstborn",
    "H6471": "time, occurrence; foot, step",
    "H8441": "abomination, detestable thing",
    "H3956": "tongue, language",
    "H4467": "kingdom, dominion, reign",
    "H6999": "burn incense, make smoke",
    "H8210": "pour out",
    "H8313": "burn",
    "H1058": "weep, cry",
    "H1431": "grow, become great",
    "H3513": "be heavy, be honored; make heavy, honor",
    "H4481": "from (Aramaic)",
    "H7999": "be complete, be at peace; repay",
    "H4054": "pastureland, open land around a city",
    "H5012": "prophesy",
    "H3034": "give thanks, praise; confess",
    "H954": "be ashamed",
    "H8267": "lie, falsehood, deception",
    "H1115": "not, except, besides",
    "H3190": "be good, go well; do well, make good",
    "H5982": "pillar, column",
    "H3671": "wing, edge, extremity",
    "H3847": "wear, put on, clothe",
    "H5045": "south, Negev",
}


def main():
    with open(DRAFTS_PATH, encoding="utf-8") as f:
        drafts = json.load(f)["entries"]

    if len(CURATED) != len(drafts):
        missing = [e["lemma_id"] for e in drafts if e["lemma_id"] not in CURATED]
        extra = [k for k in CURATED if k not in {e["lemma_id"] for e in drafts}]
        raise SystemExit(f"CURATED does not match drafts 1:1 -- missing={missing} extra={extra}")

    entries = []
    for e in drafts:
        lid = e["lemma_id"]
        entries.append({
            "rank": e["rank"],
            "lemma_id": lid,
            "citation_form": e["citation_form"],
            "pos": e["pos"],
            "frequency": e["frequency"],
            "gloss": CURATED[lid],
            "reviewed": True,
        })
    entries.sort(key=lambda e: e["rank"])

    out = {
        "metadata": {
            "batch_rank_range": [301, 400],
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

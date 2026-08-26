"""
Phase 2 step 2, curation half, batch rank 501-600 -- final batch, completes
the top-600 gloss set.

Same approach as earlier batches: every gloss below reflects what the word
actually means, cross-checked against (not copied from) the Strong's draft
in data/gloss_drafts_501_600.json. Notable notes:

- H560 (amar), H1934 (hava): no usable Strong's def, but `source` field
  reads "(Aramaic) corresponding to <H-number>" -- confirmed, same method
  as earlier Aramaic resolutions (see glosses/uncertainty_notes.md).
- H2790 (charash): spans two historically separate roots under one Strong's
  number ("engrave, plow, devise" vs "be silent, be deaf") -- kept both,
  same treatment as H2490/H1481/H1197/H3885 in earlier batches.
- H1168 (Baal, proper name of the god) vs H1167 (ba'al, "master, husband",
  already glossed in batch 401-500): confirmed separate Strong's entries.
- H3001 (yabesh, "be dry, wither"): draft's "be ashamed, disappointed" is a
  real attested figurative extension of this root (dried-up hope/strength),
  not a homograph artifact with H954 (bosh, "be ashamed") -- kept both
  senses.
- H5542 (selah): liturgical term of uncertain meaning (Psalms rubric) --
  glossed as such rather than inventing false precision.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DRAFTS_PATH = os.path.join(HERE, "..", "data", "gloss_drafts_501_600.json")
OUT_PATH = os.path.join(HERE, "..", "glosses", "batch_501_600.json")

CURATED = {
    "H5641": "hide, conceal",
    "H5826": "help",
    "H6311": "here",
    "H7043": "be light, be swift; curse",
    "H7133": "offering, sacrifice",
    "H7819": "slaughter",
    "H3064": "Jew, Judean",
    "H738": "lion",
    "H1168": "Baal",
    "H1964": "palace, temple",
    "H2822": "darkness",
    "H3083": "Jonathan",
    "H4376": "sell",
    "H5782": "wake, rouse, stir up",
    "H205": "wickedness, iniquity, trouble; idol",
    "H214": "storehouse, treasury",
    "H226": "sign, signal",
    "H2603": "be gracious, show favor; implore favor",
    "H3289": "advise, counsel",
    "H6041": "poor, afflicted, humble",
    "H7794": "bull, ox",
    "H4931": "watch, charge, duty, obligation",
    "H5061": "plague, mark, spot (esp. skin disease)",
    "H6697": "rock, cliff; refuge",
    "H7138": "near",
    "H7392": "ride",
    "H1486": "lot (cast for decision); portion, destiny",
    "H2114": "be a stranger, be strange",
    "H3444": "salvation, deliverance, victory",
    "H8605": "prayer",
    "H1270": "iron",
    "H3988": "reject, despise, refuse",
    "H4713": "Egyptian",
    "H4735": "livestock, cattle, property",
    "H5291": "girl, young woman",
    "H6186": "arrange, set in order, draw up (for battle)",
    "H7161": "horn",
    "H7198": "bow (weapon)",
    "H8641": "contribution, offering",
    "H2470": "be sick, be weak; entreat",
    "H2654": "delight in, desire, be pleased with",
    "H3240": "leave, deposit, set down; allow to rest",
    "H5324": "stand, take one's stand, station",
    "H4217": "sunrise, east",
    "H4720": "sanctuary, holy place",
    "H5795": "goat, she-goat",
    "H7023": "wall",
    "H7998": "plunder, spoil, booty",
    "H1892": "breath, vapor; vanity, futility",
    "H2199": "cry out",
    "H2781": "reproach, disgrace, scorn",
    "H3001": "be dry, wither; be ashamed, disappointed",
    "H3669": "Canaanite",
    "H631": "bind, tie, imprison",
    "H6869": "distress, trouble, anguish",
    "H730": "cedar",
    "H1410": "Gad",
    "H2790": "engrave, plow, devise; be silent, be deaf",
    "H4069": "why?",
    "H499": "Eleazar",
    "H7205": "Reuben",
    "H7364": "wash",
    "H7782": "ram's horn, trumpet",
    "H990": "belly, womb",
    "H1389": "hill",
    "H2275": "Hebron",
    "H3844": "Lebanon",
    "H452": "Elijah",
    "H5775": "bird, flying creature",
    "H6381": "be extraordinary, be wonderful; do wonders",
    "H7673": "cease, rest",
    "H7979": "table",
    "H1835": "Dan",
    "H3684": "fool, stupid person",
    "H5027": "look, look intently, regard",
    "H5707": "witness",
    "H7378": "strive, contend, quarrel; bring a legal case",
    "H8628": "blow (a trumpet), thrust, clap",
    "H1293": "blessing",
    "H2580": "favor, grace",
    "H441": "chief, leader; friend, companion",
    "H4886": "anoint",
    "H6010": "valley",
    "H6921": "east, east wind",
    "H7495": "heal",
    "H270": "seize, grasp, take hold of",
    "H3603": "district, circle; talent (weight); loaf",
    "H6327": "scatter, disperse",
    "H884": "Beersheba",
    "H953": "pit, cistern",
    "H2506": "portion, share, territory",
    "H3802": "shoulder",
    "H40": "Abimelech",
    "H5117": "rest, settle down",
    "H6566": "spread out",
    "H6913": "grave, tomb",
}

# H5542/H1077 are poetry-only (v1 excludes poetry, per CLAUDE.md); H1934/H560
# are Aramaic (Ezra/Daniel). All four cut -- see build_vocab_deck.py.
EXCLUDED = {
    "H5542": "poetry-only, meaning uncertain (selah)",
    "H1077": "poetry-only negative particle (bal)",
    "H1934": "Aramaic (be/become, Ezra/Daniel)",
    "H560": "Aramaic (say, Ezra/Daniel)",
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
            "batch_rank_range": [501, 600],
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

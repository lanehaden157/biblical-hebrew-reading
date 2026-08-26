"""
Phase 2 step 2, curation half, batch rank 201-300.

Same approach as the earlier batches: every gloss below reflects what the
word actually means, cross-checked against (not copied from) the Strong's
draft in data/gloss_drafts_201_300.json. Notable deviations:

- H520 (ammah): draft's first def is "a mother" -- wrong for this entry;
  that's an unrelated homograph artifact (the real word for "mother" is
  H517, already in this batch). H520's dominant sense by far is "cubit"
  (unit of length -- tabernacle/ark/temple measurements).
- H8451 (torah): draft says "precept; statute; Decalogue; Pentateuch" --
  those late/technical senses would mislead a beginner; went with
  "law, instruction, teaching", the actual root meaning.
- H3467 (yasha), H6942 (qadash): draft defs are archaic etymological
  speculation ("be open; wide; free" / "be; make; pronounce") rather than
  usable glosses; replaced with the actual attested meanings (save,
  deliver / be holy, consecrate).
- Proper names: Strong's transliterations (Jehoshua, Jarden, Ephrajim,
  Binjamin) swapped for standard English spellings (Joshua, Jordan,
  Ephraim, Benjamin).
- H4430 (melek, "king"): a separate Strong's entry from H4428 (already
  glossed "king" in batch 1-100) in the same 4400s Aramaic range as H1768
  (already tagged Aramaic in batch 101-200) -- tagged "(Aramaic)" for the
  same reason.

Revised 2026-08-22 after a BDB cross-check (see glosses/uncertainty_notes.md):
- H905 (bad): was "part, portion, alone". BDB splits בד into three separate
  Strong's numbers (H905 part/separation/bar, H906 linen, H907 lie) -- so
  "linen" was never actually in scope for H905, but H905 itself explicitly
  includes "bar, pole (for carrying)" (the tabernacle/ark-pole sense),
  which the original gloss dropped entirely. Now "part, portion; bar, pole
  (for carrying); alone, apart".
- H352 (ayil): was "ram; chief, leader". BDB lists this Strong's number as
  covering 4 homographs from one root ("strength"): ram, pilaster/pillar,
  leader/chief, terebinth. Added the pilaster/pillar sense (a real,
  moderately common architectural term in temple descriptions); left out
  terebinth as BDB itself marks that sense uncertain and rare. Now
  "ram; pillar, pilaster; leader, chief".
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DRAFTS_PATH = os.path.join(HERE, "..", "data", "gloss_drafts_201_300.json")
OUT_PATH = os.path.join(HERE, "..", "glosses", "batch_201_300.json")

CURATED = {
    "H520": "cubit",
    "H410": "God, god, mighty one",
    "H1366": "border, territory, boundary",
    "H2398": "sin, miss the mark, do wrong",
    "H5288": "boy, young man, servant",
    "H7965": "peace, well-being, completeness",
    "H2142": "remember, mention",
    "H3915": "night",
    "H4639": "deed, work, action",
    "H7235": "increase, multiply",
    "H2428": "strength, army, wealth",
    "H3423": "take possession of, inherit, dispossess",
    "H5771": "iniquity, guilt, sin",
    "H2233": "seed, offspring, descendants",
    "H3789": "write",
    "H7130": "midst, inward part",
    "H1245": "seek, search for",
    "H127": "ground, land, soil",
    "H4150": "appointed time, festival, meeting",
    "H5159": "inheritance, possession",
    "H8451": "law, instruction, teaching",
    "H517": "mother",
    "H3559": "be firm, establish, prepare",
    "H3091": "Joshua",
    "H899": "garment, clothing",
    "H8354": "drink",
    "H4264": "camp, army",
    "H5186": "stretch out, extend, turn aside",
    "H5800": "abandon, forsake, leave",
    "H8337": "six",
    "H1242": "morning",
    "H3130": "Joseph",
    "H4397": "messenger, angel",
    "H5337": "deliver, rescue, snatch away",
    "H7901": "lie down",
    "H157": "love",
    "H4503": "gift, offering, tribute",
    "H3254": "add, do again, continue",
    "H3467": "save, deliver, help",
    "H6662": "righteous, just",
    "H3615": "finish, complete, come to an end",
    "H8199": "judge, govern",
    "H622": "gather",
    "H727": "ark, chest",
    "H905": "part, portion; bar, pole (for carrying); alone, apart",
    "H3519": "glory, honor",
    "H352": "ram; pillar, pilaster; leader, chief",
    "H3709": "palm (of hand), sole (of foot)",
    "H3201": "be able, can, prevail",
    "H7311": "be high, be exalted, rise",
    "H8081": "oil, fat",
    "H2691": "courtyard, settlement, village",
    "H7626": "tribe, rod, staff",
    "H929": "animal, beast, cattle",
    "H7453": "friend, companion, neighbor",
    "H241": "ear",
    "H5612": "book, scroll, document",
    "H1540": "uncover, reveal; go into exile",
    "H7650": "swear, take an oath",
    "H6": "perish, be destroyed; destroy",
    "H4687": "commandment",
    "H1241": "cattle, herd, ox",
    "H3383": "Jordan",
    "H7223": "first, former",
    "H4124": "Moab",
    "H669": "Ephraim",
    "H2205": "old, elder",
    "H3898": "fight, wage war",
    "H6235": "ten",
    "H8193": "lip, language, edge",
    "H7592": "ask, inquire, request",
    "H7812": "bow down, worship",
    "H7970": "thirty",
    "H85": "Abraham",
    "H6942": "be holy, consecrate, sanctify",
    "H995": "understand, discern",
    "H977": "choose",
    "H1755": "generation",
    "H1144": "Benjamin",
    "H2026": "kill, slay",
    "H4399": "work, occupation, labor",
    "H312": "other, another",
    "H1875": "seek, inquire, require",
    "H1984": "praise",
    "H2351": "outside, street",
    "H6607": "entrance, doorway, opening",
    "H7462": "shepherd, tend, pasture",
    "H2572": "fifty",
    "H2077": "sacrifice",
    "H2930": "be unclean, defiled",
    "H389": "surely, only, but",
    "H5127": "flee",
    "H5608": "count, recount, tell",
    "H1368": "mighty, warrior, hero",
    "H6666": "righteousness",
    "H4194": "death",
    "H5437": "turn, surround, go around",
    "H8055": "rejoice, be glad",
    "H8145": "second",
}

# H4430 (melek, "king") is Aramaic (Ezra/Daniel) -- cut, see build_vocab_deck.py.
EXCLUDED = {"H4430": "Aramaic (king, Ezra/Daniel)"}

CONFUSABLE_WITH = {
    "H389": "Close to raq (only, surely) in meaning, but 'akh leans more poetic/prophetic -- raq is the one you'll meet constantly in narrative.",
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
        if lid in CONFUSABLE_WITH:
            entry["confusable_with"] = CONFUSABLE_WITH[lid]
        entries.append(entry)
    entries.sort(key=lambda e: e["rank"])

    out = {
        "metadata": {
            "batch_rank_range": [201, 300],
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

"""
Phase 2 step 2, curation half, batch rank 401-500.

Same approach as earlier batches: every gloss below reflects what the word
actually means, cross-checked against (not copied from) the Strong's draft
in data/gloss_drafts_401_500.json. Notable notes:

- H5922, H3606, H3809, H426: no usable Strong's def (draft had only a
  usage string), but each has a `source` field explicitly reading
  "(Aramaic) corresponding to <H-number>" -- confirmed Aramaic, same method
  as the H4430/H1768/H4481 resolutions in glosses/uncertainty_notes.md.
- H1481 (gur), H1197 (ba'ar), H3885 (lun): each Strong's number spans two
  distinct verbal senses from what are historically separate roots (gur:
  "sojourn" / "fear"; ba'ar: "burn" / "be brutish"; lun: "lodge overnight" /
  "grumble"). Kept both senses per entry rather than picking one -- same
  treatment as H2490 in batch 301-400.
- H6031 (anah, "afflict, oppress") vs H6030 (anah, "answer", already
  glossed in batch 201-300) and H2145 (zakar, "male") vs H2142 (zakar,
  "remember", already glossed in batch 201-300): confirmed these are
  separate Strong's entries for the same consonants, not duplicates.
- H7125 (qir'ah): draft tags it a verb form but it's the infinitive-
  construct-as-preposition "toward, to meet" (as in liqrat) -- glossed
  as the underlying verbal idea, "meet, encounter".
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DRAFTS_PATH = os.path.join(HERE, "..", "data", "gloss_drafts_401_500.json")
OUT_PATH = os.path.join(HERE, "..", "glosses", "batch_401_500.json")

CURATED = {
    "H53": "Absalom",
    "H7676": "Sabbath, rest",
    "H6083": "dust",
    "H6862": "narrow, distress; adversary, foe",
    "H7535": "only, surely",
    "H8083": "eight",
    "H8111": "Samaria",
    "H3327": "Isaac",
    "H5162": "comfort, console; be sorry, regret",
    "H539": "be firm, be faithful, trust, believe",
    "H7992": "third",
    "H3498": "remain, be left over; excel, exceed",
    "H3532": "lamb",
    "H5983": "Ammon",
    "H1350": "redeem, act as kinsman-redeemer",
    "H2708": "statute, ordinance",
    "H1116": "high place",
    "H3379": "Jeroboam",
    "H4758": "appearance, sight, vision",
    "H7323": "run",
    "H8548": "continually, regularly",
    "H1157": "behind, through, for, on behalf of",
    "H3722": "cover, atone, make atonement",
    "H3499": "remainder, rest, excess",
    "H7489": "be evil, be bad; do evil, harm",
    "H7911": "forget",
    "H4592": "little, few",
    "H6996": "small, young, insignificant",
    "H7341": "width, breadth",
    "H7458": "hunger, famine",
    "H123": "Edom",
    "H7125": "meet, encounter",
    "H3282": "because, on account of",
    "H5785": "skin, hide",
    "H1481": "sojourn, dwell as an alien; fear, dread",
    "H7637": "seventh",
    "H8334": "serve, minister",
    "H6215": "Esau",
    "H7097": "end, extremity, border",
    "H7646": "be satisfied, be full",
    "H2543": "donkey",
    "H2891": "be clean, be pure",
    "H4422": "escape; deliver, rescue",
    "H753": "length",
    "H1197": "burn, consume; be stupid, be brutish",
    "H2015": "turn, overturn, change",
    "H2491": "slain, pierced",
    "H2889": "clean, pure",
    "H3667": "Canaan",
    "H8057": "joy, gladness",
    "H1847": "knowledge",
    "H2181": "be a prostitute, commit fornication, commit idolatry",
    "H256": "Ahab",
    "H6588": "transgression, rebellion",
    "H1616": "sojourner, resident alien, foreigner",
    "H2459": "fat",
    "H3754": "vineyard",
    "H5676": "region beyond, side, across",
    "H5797": "strength, might",
    "H2220": "arm; strength",
    "H3742": "cherub",
    "H4438": "kingdom, royal power, reign",
    "H5462": "shut, close; deliver up",
    "H7657": "seventy",
    "H7892": "song",
    "H8549": "blameless, complete, whole",
    "H2734": "burn, be kindled (of anger)",
    "H3206": "child, boy",
    "H6098": "counsel, advice, plan",
    "H8045": "destroy, exterminate",
    "H1817": "door",
    "H2931": "unclean, impure",
    "H7891": "sing",
    "H8255": "shekel",
    "H3885": "spend the night, lodge; grumble, complain",
    "H3925": "learn; teach",
    "H567": "Amorite",
    "H6051": "cloud",
    "H6924": "east; ancient time, of old",
    "H8002": "peace offering, fellowship offering",
    "H3384": "throw, shoot; teach, instruct",
    "H6285": "corner, side, edge",
    "H7069": "acquire, buy; create",
    "H7896": "put, place, set",
    "H8074": "be desolate, be appalled",
    "H1995": "multitude, crowd, noise, abundance",
    "H7350": "far, distant",
    "H3092": "Jehoshaphat",
    "H6419": "pray, intercede",
    "H1167": "master, owner, husband; Baal",
    "H6031": "afflict, oppress, humble",
    "H1035": "Bethlehem",
    "H2145": "male",
    "H349": "how?",
    "H3778": "Chaldean",
    "H4910": "rule, have dominion",
}

# All four Aramaic (Ezra) -- cut, see build_vocab_deck.py.
EXCLUDED = {
    "H5922": "Aramaic (`al, Ezra)",
    "H3809": "Aramaic (la', Ezra)",
    "H3606": "Aramaic (all/every, Ezra/Daniel)",
    "H426": "Aramaic (God, Ezra/Daniel)",
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
            "batch_rank_range": [401, 500],
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

"""
Phase 2 step 2, curation half, batch rank 1-100.

Hand-curated glosses (tight, modern, recognition-reading-oriented) for the
first 100 lemmas, cross-checked against the Strong's draft in
data/gloss_drafts.json but not copied from it verbatim -- CLAUDE.md flags
Strong's meaning as archaic/misleading (e.g. nefesh as "a breathing
creature"), so every entry below was written from scratch and only checked
against the draft, not derived from it.

YHWH (H3068) is transliterated as "YHWH" per an explicit decision on
2026-08-22 (not "LORD" or "Yahweh").
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DRAFTS_PATH = os.path.join(HERE, "..", "data", "gloss_drafts.json")
OUT_PATH = os.path.join(HERE, "..", "glosses", "batch_001_100.json")

CURATED = {
    "F-c": "and",
    "F-d": "the",
    "F-l": "to, for",
    "F-b": "in, on, with",
    "H853": "(marks a definite direct object -- usually untranslated)",
    "H3068": "YHWH",
    "F-m": "from",
    "H5921": "on, over, against",
    "H413": "to, toward",
    "H834": "who, which, that",
    "H3605": "all, every",
    "H559": "say",
    "H3808": "not",
    "H1121": "son",
    "H3588": "for, that, because, when",
    "H1961": "be, become, happen",
    "F-k": "like, as",
    "H6213": "do, make",
    "H430": "God, gods",
    "H935": "come, go, enter",
    "H4428": "king",
    "H3478": "Israel",
    "H776": "land, earth",
    "H3117": "day",
    "H376": "man",
    "H6440": "face",
    "H1004": "house",
    "H5414": "give",
    "H1931": "he, it",
    "H5971": "people",
    "H3027": "hand",
    "H1697": "word, thing",
    "H7200": "see",
    "H5704": "until, as far as",
    "H4480": "from",
    "H1": "father",
    "H2088": "this",
    "H8085": "hear, listen, obey",
    "H1696": "speak",
    "H859": "you (m.s.)",
    "H5892": "city",
    "H3427": "sit, dwell, live",
    "H3318": "go out, come out",
    "H1732": "David",
    "H7725": "return, turn back",
    "H518": "if",
    "H5973": "with",
    "H3212": "go, walk",
    "H259": "one",
    "H3947": "take",
    "H3045": "know",
    "H5869": "eye, spring",
    "H5927": "go up, ascend",
    "H854": "with",
    "H8141": "year",
    "H589": "I",
    "H8034": "name",
    "H7971": "send",
    "H2009": "behold, here is",
    "H4191": "die",
    "H8033": "there",
    "H3063": "Judah",
    "H398": "eat",
    "H5650": "servant, slave",
    "H369": "there is not, no",
    "H802": "woman, wife",
    "H3651": "so, thus, right",
    "H1571": "also, even",
    "H8147": "two",
    "H4872": "Moses",
    "H5315": "soul, self, life, person",
    "H3548": "priest",
    "H4100": "what?",
    "H428": "these",
    "H7121": "call, call out, proclaim, read aloud",
    "H408": "do not, no",
    "H310": "after, behind",
    "H1870": "way, road, journey",
    "H7451": "evil, bad",
    "F-i": "(marks a yes/no question)",
    "H5375": "lift, carry, bear",
    "H3389": "Jerusalem",
    "H4714": "Egypt",
    "H251": "brother",
    "H6965": "rise, stand up",
    "H2063": "this (f.)",
    "H7218": "head, top, chief",
    "H3820": "heart, mind",
    "H1323": "daughter",
    "H7760": "put, place, set",
    "H3967": "hundred",
    "H4325": "water",
    "H3541": "thus, so",
    "H1471": "nation, people",
    "H1992": "they (m.)",
    "H2896": "good",
    "H5674": "cross over, pass through",
    "H120": "man, mankind, Adam",
    "H2022": "mountain, hill",
    "H1419": "great, big",
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
            "batch_rank_range": [1, 100],
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

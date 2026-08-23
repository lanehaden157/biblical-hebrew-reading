"""
Phase 5 step 1: curated glosses for the lemmas Jonah 2 needs that neither
the top-600 vocab deck nor glosses/jonah1_extra.json already covers.

Same method as curate_jonah1_extra.py (which itself follows curate_batch_*.py,
Phase 2): pull citation form + Strong's/BDB draft material from the lexicon
programmatically (rule 1 -- never hand-type pointed Hebrew), then supply a
hand-curated plain-English gloss per lemma in CURATED below, checked against
(not copied from) the Strong's draft printed by this script.

Scope: chapter 2 only, Hebrew (WLC/BHS) versification -- 11 verses. Jonah 2:1
is the fish-swallowing verse that English Bibles print as 1:17; see
build_jonah1_reader.py's docstring for why it belongs here, not in chapter 1.

Gloss sources checked before adding a lemma to CURATED: data/vocab_deck_600.json
(600 lemmas already drilled) and glosses/jonah1_extra.json (31 lemmas curated
for chapter 1). Diffing Jonah 2's 85 distinct lemmas against both found 25
not yet glossed; 3 of those (H3004 "dry ground", H3124 "Jonah", H5087 "vow")
were already curated in jonah1_extra.json and are reused as-is, not
re-curated here -- leaving the 22 lemmas below as genuinely new to chapter 2.

Notes on senses chosen (checked against each lemma's actual morph/context in
Jonah 2, not just the Strong's draft, since several of these roots have a
wide semantic range in BDB):
- H1530 (gal): Strong's draft leads with "heap, ruins" (its sense elsewhere,
  e.g. piles of stones), but Jonah 2:4's occurrence is plural + 2ms suffix
  in direct parallel with H4867 (breaker) in the same line -- "your waves",
  not "your heaps of ruins".
- H4487 (manah): Strong's draft leads with "weigh out, enumerate" (its Qal
  sense), but Jonah 2:1's occurrence is Piel wayyiqtol ("the LORD appointed
  a fish") -- Piel here means "appoint, ordain", a distinct sense from the
  Qal counting/weighing sense.
- H5488 (suph): usually seen in "Yam Suph" (Red/Reed Sea) as "reed"; Jonah
  2:6's occurrence ("suph wrapped around my head") is the plant literally
  tangled around Jonah's head in the water, so "reed, seaweed" (not the
  place name sense).
- H7095 (qetsev): Strong's draft ("shape, base") is thin; BDB's sense for
  this specific construct-plural phrase ("qitsvei harim", 2:7) is
  "roots/foundations of the mountains" -- glossed accordingly.
- H8415 (tehom): the same "the deep" that appears in Genesis 1:2 -- glossed
  consistently with that well-known sense rather than the Strong's draft's
  bare "abyss".
"""
import json
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hebrew_corpus import LEXICON_PATH, LEX_NS, POS_LETTER_TO_LABEL, OSIS_NS, WLC_DIR

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(HERE, "..", "glosses", "jonah2_extra.json")

CURATED = {
    "H1104": "swallow",
    "H1280": "bar, bolt",
    "H1530": "wave, billow",
    "H1644": "drive out, banish, expel",
    "H1709": "fish",
    "H1710": "fish (collective/generic)",
    "H2280": "bind, wrap around",
    "H4487": "appoint, ordain (piel)",
    "H4578": "belly, stomach, innards",
    "H4688": "the deep, the depths (of the sea)",
    "H4867": "breaker (wave)",
    "H5488": "reed, seaweed",
    "H5848": "grow faint, be overwhelmed (hitpael)",
    "H661": "surround, encompass",
    "H6958": "vomit (hiphil: vomit out)",
    "H7095": "base, root (of a mountain)",
    "H7585": "Sheol (realm of the dead)",
    "H7723": "worthless thing, vanity, idol",
    "H7768": "cry out (for help)",
    "H7845": "pit, the grave, destruction",
    "H8415": "the deep, the abyss",
    "H8426": "thanksgiving",
}


def load_lexicon():
    root = ET.parse(LEXICON_PATH).getroot()
    out = {}
    for entry in root.findall(f"{LEX_NS}entry"):
        eid = entry.get("id")
        if not eid or not eid.startswith("H"):
            continue
        w = entry.find(f"{LEX_NS}w")
        meaning_el = entry.find(f"{LEX_NS}meaning")
        defs = [d.text.strip() for d in meaning_el.findall(f"{LEX_NS}def") if d.text] if meaning_el is not None else []
        out[eid] = {
            "citation_form": w.text.strip() if w is not None and w.text else None,
            "lexicon_pos": w.get("pos") if w is not None else None,
            "strongs_defs": defs,
        }
    return out


def find_jonah2_lemma_pos():
    """Majority morph POS-letter per lemma, for this file's own "pos" field
    only -- documentation/curation reference, not what the reader displays.
    See curate_jonah1_extra.py's docstring for why a per-lemma majority is
    never used as the reader's displayed part of speech."""
    path = os.path.join(WLC_DIR, "Jonah.xml")
    root = ET.parse(path).getroot()
    tally = {}
    for verse in root.iter(f"{OSIS_NS}verse"):
        vid = verse.get("osisID")
        if not vid or not vid.startswith("Jonah.2."):
            continue
        for w in verse.iter(f"{OSIS_NS}w"):
            raw_lemma, raw_morph = w.get("lemma"), w.get("morph") or ""
            if not raw_lemma:
                continue
            lemma_parts = raw_lemma.split("/")
            morph_parts = raw_morph.split("/")
            for i, lp in enumerate(lemma_parts):
                lp = lp.strip()
                if not lp or not lp[0].isdigit():
                    continue
                lemma_id = "H" + lp.split(" ")[0].rstrip("+")
                mp = morph_parts[i] if i < len(morph_parts) else ""
                if i == 0:
                    mp = mp[1:] if mp.startswith(("H", "A")) else mp
                letter = mp[0] if mp else None
                tally.setdefault(lemma_id, {}).setdefault(letter, 0)
                tally[lemma_id][letter] += 1
    return {lid: max(letters, key=letters.get) for lid, letters in tally.items()}


def main():
    lexicon = load_lexicon()
    pos_by_lemma = find_jonah2_lemma_pos()

    entries = []
    for lemma_id, gloss in CURATED.items():
        lex = lexicon.get(lemma_id)
        if not lex or not lex["citation_form"]:
            sys.exit(f"{lemma_id}: no lexicon citation form -- cannot proceed without hand-typing Hebrew")
        letter = pos_by_lemma.get(lemma_id)
        pos = POS_LETTER_TO_LABEL.get(letter, letter or "Unknown")
        entries.append({
            "lemma_id": lemma_id,
            "citation_form": lex["citation_form"],
            "pos": pos,
            "strongs_defs_for_reference": lex["strongs_defs"],
            "gloss": gloss,
            "reviewed": True,
        })

    entries.sort(key=lambda e: e["lemma_id"])

    out = {
        "metadata": {
            "source": "lemmas in Jonah 2 (Hebrew/WLC versification, 11 verses) not already in "
                       "data/vocab_deck_600.json or glosses/jonah1_extra.json",
            "status": "curated and reviewed",
            "count": len(entries),
        },
        "entries": entries,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(entries)} curated entries to {OUT_PATH}")


if __name__ == "__main__":
    main()

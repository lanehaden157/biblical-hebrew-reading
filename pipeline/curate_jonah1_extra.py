"""
Phase 4 step 1: curated glosses for the lemmas Jonah 1 needs that the
top-600 vocab deck doesn't already cover.

Same method as curate_batch_*.py (Phase 2): pull citation form + Strong's/BDB
draft material from the lexicon programmatically (rule 1 -- never hand-type
pointed Hebrew), then supply a hand-curated plain-English gloss per lemma in
CURATED below. Every gloss reflects what the word actually means, checked
against (not copied from) the Strong's draft printed by this script.

Scope: chapter 1 only, Hebrew (WLC/BHS) versification -- 16 verses. WLC
numbers what English Bibles call Jonah 1:17 as Jonah 2:1 (the fish-swallowing
verse belongs to the next chapter in the Hebrew text), so it is deliberately
left for the chapter 2 reading later rather than stitched in here. Not a bug:
see pipeline/build_jonah1_reader.py's docstring.

31 lemma_ids below were found by diffing Jonah 1's distinct lemmas (including
the 8 bound function-word codes, which ARE already in vocab_deck_600 and so
are correctly excluded here) against data/vocab_deck_600.json. Notes:

- H3124 (Jonah), H573 (Amittai), H5210 (Nineveh), H8659 (Tarshish),
  H3305 (Joppa), H5680 ("Hebrew" as a gentilic noun): proper names/gentilics,
  glossed as such rather than given a false common-noun sense.
- H5590 (verb "storm, rage") and H5591 (noun "storm, tempest") are a
  verb/noun pair from the same root, both attested in this chapter --
  kept distinct, not collapsed into one gloss.
- H6245 (`ashat`): Strong's draft def ("sleek, glossy, polishing") reflects a
  different, unrelated sense of this root than the one attested here
  (Jonah 1:6, hitpael, "perhaps God will take notice of us") -- BDB's
  Hitpael sense "think upon, be mindful of" is what's glossed, not the
  draft's literal senses.
- H7945 (shel, "of whom/which"): a rare longer variant of the same relative
  particle already curated as F-s ("that, which, who") in the vocab deck;
  kept as its own entry since it is in fact a separate Strong's number, not
  a duplicate.
- H3373 (yare): OSHB tags all three Jonah-1 occurrences under this one
  Strong's number, but the actual morph codes differ -- 1:9 is HVqp3ms (a
  Qal qatal verb, "he feared"), 1:10 and 1:16 are HNcfsa (a feminine noun,
  "fear/dread"). Rather than split one lemma_id into two glosses the reader
  can't select between, the gloss covers both senses explicitly. This is
  also why build_jonah1_reader.py computes each word's displayed part of
  speech from that word's own morph code, never from a lemma-level
  majority -- a per-lemma POS label would have called 1:9's finite verb a
  noun.
- H2197 (za'aph): its one Jonah-1 occurrence (1:15, "mi-za'p-o", "from its
  raging") is HR/Vqc/Sp3ms -- a Qal infinitive construct, i.e. a verb form
  used substantively -- not the noun BDB also lists this root as. Glossed
  as the verb, with the infinitive-construct reading noted.
"""
import json
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hebrew_corpus import LEXICON_PATH, LEX_NS, POS_LETTER_TO_LABEL, OSIS_NS, WLC_DIR

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(HERE, "..", "glosses", "jonah1_extra.json")

CURATED = {
    "H3124": "Jonah (proper name)",
    "H2904": "hurl, throw, cast",
    "H8659": "Tarshish (place name)",
    "H591": "ship",
    "H3373": "fear, be afraid; (fem. noun) fear, dread",
    "H1272": "flee",
    "H5591": "storm, tempest",
    "H7290": "be sound asleep, fall into a deep sleep",
    "H3004": "dry ground, dry land",
    "H8367": "grow calm, subside",
    "H5590": "storm, rage",
    "H573": "Amittai (proper name)",
    "H5210": "Nineveh (place name)",
    "H3305": "Joppa (place name)",
    "H7939": "wages, hire, fare",
    "H4419": "sailor",
    "H3411": "innermost part, side, recess",
    "H5600": "ship, vessel",
    "H2259": "sailor (rav ha-khovel: ship's captain)",
    "H194": "perhaps, maybe",
    "H6245": "think, take notice (hitpael)",
    "H370": "where? whence?",
    "H335": "where? what sort?",
    "H5680": "Hebrew (person)",
    "H7945": "of whom, which, whose (relative)",
    "H2864": "row (a boat)",
    "H577": "please! (interjection of entreaty)",
    "H5355": "innocent, free of guilt",
    "H2197": "rage, storm (verb; Jonah 1:15 is an infinitive construct, \"from its raging\")",
    "H5087": "vow",
    "H5088": "vow (the thing promised)",
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


def find_jonah1_lemma_pos():
    """Majority morph POS-letter per lemma, for this file's own "pos" field
    only -- documentation/curation reference, not what the reader displays.
    A per-lemma majority can be wrong for any one occurrence (see H3373 in
    the module docstring), so build_jonah1_reader.py computes each word's
    displayed part of speech from that word's own morph code instead."""
    path = os.path.join(WLC_DIR, "Jonah.xml")
    root = ET.parse(path).getroot()
    tally = {}
    for verse in root.iter(f"{OSIS_NS}verse"):
        vid = verse.get("osisID")
        if not vid or not vid.startswith("Jonah.1."):
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
    pos_by_lemma = find_jonah1_lemma_pos()

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
            "source": "lemmas in Jonah 1 (Hebrew/WLC versification, 16 verses) not already in data/vocab_deck_600.json",
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

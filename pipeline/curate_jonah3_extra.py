"""
Phase 5 step 3: curated glosses for the lemmas Jonah 3 needs that neither
the top-600 vocab deck, glosses/jonah1_extra.json, nor glosses/jonah2_extra.json
already covers.

Same method as curate_jonah1_extra.py / curate_jonah2_extra.py: pull citation
form + Strong's/BDB draft material from the lexicon programmatically (rule 1
-- never hand-type pointed Hebrew), then supply a hand-curated plain-English
gloss per lemma in CURATED below, checked against (not copied from) the
Strong's draft printed by this script.

Scope: chapter 3 only, 10 verses (Jonah.3.1-Jonah.3.10). No versification
divergence from English here (unlike chapters 1-2).

Diffing Jonah 3's 80 distinct lemmas against vocab_deck_600 + both prior
Jonah extras found 12 lemmas genuinely new to this chapter -- no overlap
with chapters 1-2's curated sets, so nothing was reused this time.

Notes on senses chosen (checked against each lemma's actual morph/context in
Jonah 3, not just the Strong's draft):
- H2394 (chozqah): Strong's draft leads with "vehemence"; the actual phrase
  (3:8, "yiqre'u el elohim bechozqah") is adverbial, "cry out to God
  forcefully/urgently" -- glossed as the adverbial sense actually used.
- H2740 (charon): only ever occurs in the fixed phrase "charon appo" (his
  burning anger); glossed with that collocation in mind rather than the
  bare noun alone.
- H2940 (ta'am): same root as H2938 (taste) but here (3:7, "mitta'am
  hammelekh") means "by decree/order of the king", the extended
  administrative sense, not the literal "taste" sense -- both senses noted.
"""
import json
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hebrew_corpus import LEXICON_PATH, LEX_NS, POS_LETTER_TO_LABEL, OSIS_NS, WLC_DIR

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(HERE, "..", "glosses", "jonah3_extra.json")

CURATED = {
    "H155": "robe, mantle",
    "H2394": "force, urgency (adverbial: forcefully, urgently)",
    "H2555": "violence, wrong",
    "H2740": "burning anger, fierce wrath",
    "H2938": "taste, eat",
    "H2940": "decree, command (also: taste, perception)",
    "H3972": "anything (used with a negative: nothing)",
    "H4109": "journey, walking distance",
    "H665": "ashes",
    "H6685": "fast (abstaining from food)",
    "H7150": "proclamation, message",
    "H8242": "sackcloth",
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


def find_jonah3_lemma_pos():
    """Majority morph POS-letter per lemma, for this file's own "pos" field
    only -- documentation/curation reference, not what the reader displays.
    See curate_jonah1_extra.py's docstring for why a per-lemma majority is
    never used as the reader's displayed part of speech."""
    path = os.path.join(WLC_DIR, "Jonah.xml")
    root = ET.parse(path).getroot()
    tally = {}
    for verse in root.iter(f"{OSIS_NS}verse"):
        vid = verse.get("osisID")
        if not vid or not vid.startswith("Jonah.3."):
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
    pos_by_lemma = find_jonah3_lemma_pos()

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
            "source": "lemmas in Jonah 3 (10 verses) not already in data/vocab_deck_600.json, "
                       "glosses/jonah1_extra.json, or glosses/jonah2_extra.json",
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

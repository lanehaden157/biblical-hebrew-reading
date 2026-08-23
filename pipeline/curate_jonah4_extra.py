"""
Phase 5 step 4: curated glosses for the lemmas Jonah 4 needs that neither
the top-600 vocab deck nor the three prior Jonah extras (chapters 1-3)
already cover.

Same method as curate_jonah1_extra.py / curate_jonah2_extra.py /
curate_jonah3_extra.py: pull citation form + Strong's/BDB draft material
from the lexicon programmatically (rule 1), then supply a hand-curated
plain-English gloss per lemma in CURATED below, checked against (not copied
from) the Strong's draft printed by this script.

Scope: chapter 4 only, 11 verses (Jonah.4.1-Jonah.4.11). No versification
divergence from English here.

Diffing Jonah 4's 101 distinct lemmas against vocab_deck_600 + all three
prior Jonah extras found 17 lemmas genuinely new to this chapter -- no
overlap with chapters 1-3's curated sets.

Notes on senses chosen (checked against each lemma's actual morph/context in
Jonah 4):
- H5968 (`alaph`, "grow faint" in the hitpael) is a DIFFERENT root from
  H5848 (`ataph`, curated in jonah2_extra.json, also "grow faint" in the
  hitpael) -- distinct Strong's numbers, distinct consonants (lamed vs.
  tet), kept as separate entries rather than merged even though both land
  on a similar English gloss in this chapter's context.
- H6923 (qadam) has a wide BDB range ("precede, anticipate, meet"); Jonah
  4:2's occurrence ("qidamti livroach", "I was quick to flee beforehand")
  is the "anticipate/be quick to act" sense, not the more common spatial
  "go before/meet" sense -- glossed for the sense actually attested here.
- H750 (arekh) only occurs here in the fixed collocation "erekh appayim"
  ("long of nostrils" = slow to anger); glossed with that collocation noted
  rather than the bare adjective alone.
- H7239 (ribo) is a numeral ("ten thousand, myriad"), used in 4:11's
  "120,000 persons" (twelve times ten-thousand) -- glossed as the number
  word, not a common noun.
"""
import json
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hebrew_corpus import LEXICON_PATH, LEX_NS, POS_LETTER_TO_LABEL, OSIS_NS, WLC_DIR

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(HERE, "..", "glosses", "jonah4_extra.json")

CURATED = {
    "H2224": "rise, shine (of the sun)",
    "H2347": "have compassion/pity, spare",
    "H2587": "gracious",
    "H2759": "scorching, sultry (of a wind)",
    "H4283": "next day, morrow",
    "H5521": "booth, shelter",
    "H5968": "grow faint, be overcome (hitpael)",
    "H5998": "labor, toil, work hard",
    "H6738": "shade, shadow",
    "H6923": "anticipate, be quick to act, go before",
    "H7021": "qiqayon plant (a fast-growing vine/gourd)",
    "H7239": "ten thousand, myriad",
    "H7349": "compassionate, merciful",
    "H750": "slow, long (erekh appayim = slow to anger)",
    "H7837": "dawn",
    "H8040": "left (hand/side)",
    "H8438": "worm",
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


def find_jonah4_lemma_pos():
    """Majority morph POS-letter per lemma, for this file's own "pos" field
    only -- documentation/curation reference, not what the reader displays.
    See curate_jonah1_extra.py's docstring for why a per-lemma majority is
    never used as the reader's displayed part of speech."""
    path = os.path.join(WLC_DIR, "Jonah.xml")
    root = ET.parse(path).getroot()
    tally = {}
    for verse in root.iter(f"{OSIS_NS}verse"):
        vid = verse.get("osisID")
        if not vid or not vid.startswith("Jonah.4."):
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
    pos_by_lemma = find_jonah4_lemma_pos()

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
            "source": "lemmas in Jonah 4 (11 verses) not already in data/vocab_deck_600.json, "
                       "glosses/jonah1_extra.json, glosses/jonah2_extra.json, or glosses/jonah3_extra.json",
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

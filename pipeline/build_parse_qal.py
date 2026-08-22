"""
Phase 3 step 1: OSHB corpus -> Qal strong-verb parsing deck ->
data/parse_qal_strong.json.

Scope, per CLAUDE.md's locked decisions:
  - Stem: Qal only (69.0% of verb forms -- Tier 2's binyan).
  - Conjugations, in the locked priority order: qatal, wayyiqtol, yiqtol,
    participle, infinitive construct (= 80.8% cumulative of verb forms).
    Imperative, jussive, cohortative, infinitive absolute, veqatal (waw-
    consecutive perfect) and the passive participle are real OSHB categories
    but are out of the locked list, so they are skipped here -- not a bug,
    a scope decision, matching how Pual/Hophal are recognition-only.
  - Roots: strong only. A root is weak (and excluded) if any radical is
    guttural (alef/he/het/ayin -- the four "true gutturals" of first-year
    grammar; resh is deliberately NOT treated as guttural here, since its
    only Qal-relevant quirk is refusing dagesh forte, which barely surfaces
    in Qal and is not one of CLAUDE.md's named weak classes), if the first
    radical is nun (assimilates) or vav/yod (I-Vav/Yod), if the second
    radical is vav/yod (hollow) or repeats the third (geminate). III-He and
    III-Aleph roots need no separate rule: he and alef are already in the
    guttural set, so "any radical is guttural" catches them for free.
  - Lemmas: restricted to the 181 verb lemmas already in the curated top-600
    vocab deck (data/vocab_deck_600.json), not all ~700 Qal-attested lemmas
    in the corpus. This is deliberate, not a limitation of the corpus scan:
    those 181 already carry a curated gloss and a lexicon-sourced citation
    form (verified 100% "lexicon"-sourced below, never a surface-form
    fallback, which could carry stray affixes into what's supposed to be a
    bare root). Reusing them means rule 4 (transliteration + gloss on every
    Hebrew form) is satisfied without a second curation pass, and it keeps
    parsing practice anchored to vocabulary Lane is already learning rather
    than introducing ~500 more unglossed roots incidentally.

The root's own transliteration/gloss come straight from the vocab deck; only
the inflected surface form's transliteration is computed here.

Text is never NFC/NFD-normalized (CLAUDE.md rule 2) -- only cantillation
(U+0591-U+05AF) is stripped, which is deletion, not normalization.

Run pipeline/build_vocab_deck.py first (needs data/vocab_deck_600.json).
"""
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hebrew_corpus import BOOK_ORDER, OSIS_NS, WLC_DIR
from transliterate import transliterate

HERE = os.path.dirname(os.path.abspath(__file__))
DECK_PATH = os.path.join(HERE, "..", "data", "vocab_deck_600.json")
OUT_PATH = os.path.join(HERE, "..", "data", "parse_qal_strong.json")

CANTILLATION_RE = re.compile("[֑-֯]")

GUTTURAL = set("אהחע")   # alef he het ayin
NUN = "נ"
VAV, YOD = "ו", "י"
FINAL_TO_BASE = {
    "ך": "כ",  # final kaf -> kaf
    "ם": "מ",  # final mem -> mem
    "ן": "נ",  # final nun -> nun
    "ף": "פ",  # final pe -> pe
    "ץ": "צ",  # final tsadi -> tsadi
}
HEB_CONSONANT_RE = re.compile("[א-ת]")

# Conjugation letter (position 2 of a Vq... morph code) -> our label, in the
# locked priority order. 'r' (participle) and 'c' (infinitive construct)
# carry no person; the others carry a 3-char person+gender+number suffix.
CONJUGATIONS = {
    "p": "qatal",
    "w": "wayyiqtol",
    "q": "yiqtol",
    "r": "participle",
    "c": "infinitive_construct",
}
FINITE_CONJUGATIONS = {"p", "w", "q"}

GENDER_LABEL = {"m": "m", "f": "f", "c": "c"}
NUMBER_LABEL = {"s": "s", "p": "p", "d": "d"}
STATE_LABEL = {"a": "absolute", "c": "construct"}

# HVq<conj><suffix> where conj is one of our locked letters. Suffix is
# 3 chars (person+gender+number) for finite forms, 3 chars
# (gender+number+state) for participles, absent for infinitive construct.
MORPH_RE = re.compile(r"^Vq([pwqrc])([123]?[mfc]?[spd]?[ac]?)$")


def strip_cantillation(s):
    return CANTILLATION_RE.sub("", s)


def root_consonants(citation_form):
    out = []
    for ch in citation_form:
        if HEB_CONSONANT_RE.match(ch):
            out.append(FINAL_TO_BASE.get(ch, ch))
    return out


def weakness_reasons(citation_form):
    """Every weak-class reason a root fails strong-verb status, or [] if strong."""
    c = root_consonants(citation_form)
    if len(c) != 3:
        return [f"non-triliteral({len(c)})"]
    r1, r2, r3 = c
    reasons = []
    if r1 in GUTTURAL:
        reasons.append("I-guttural")
    if r2 in GUTTURAL:
        reasons.append("II-guttural")
    if r3 in GUTTURAL:
        reasons.append("III-guttural")
    if r1 == NUN:
        reasons.append("I-Nun")
    if r1 in (VAV, YOD):
        reasons.append("I-Vav/Yod")
    if r2 in (VAV, YOD):
        reasons.append("hollow")
    if r2 == r3:
        reasons.append("geminate")
    return reasons


def parse_pgn(conj, suffix):
    """Split a morph suffix into person/gender/number/state per conjugation."""
    person = gender = number = state = None
    if conj in FINITE_CONJUGATIONS:
        m = re.match(r"^([123])([mfc])([spd])$", suffix)
        if not m:
            return None
        person, g, n = m.groups()
        gender, number = GENDER_LABEL[g], NUMBER_LABEL[n]
    elif conj == "r":
        m = re.match(r"^([mfc])([spd])([ac])$", suffix)
        if not m:
            return None
        g, n, st = m.groups()
        gender, number, state = GENDER_LABEL[g], NUMBER_LABEL[n], STATE_LABEL[st]
    elif conj == "c":
        if suffix:
            return None  # infinitive construct with an unexpected suffix -- skip, don't guess
    return {"person": person, "gender": gender, "number": number, "state": state}


def load_strong_verb_roots():
    with open(DECK_PATH, encoding="utf-8") as f:
        deck = json.load(f)
    roots = {}
    weak_count = 0
    for e in deck["entries"]:
        if e["pos"] != "Verb":
            continue
        reasons = weakness_reasons(e["citation_form"])
        if reasons:
            weak_count += 1
            continue
        roots[e["lemma_id"]] = e
    print(f"Top-600 verb lemmas: strong-root count {len(roots)}, weak-root count {weak_count}")
    return roots


def main():
    if not os.path.isfile(DECK_PATH):
        sys.exit("data/vocab_deck_600.json not found -- run pipeline/build_vocab_deck.py first")
    if not os.path.isdir(WLC_DIR):
        sys.exit("pipeline/corpus/wlc not found -- run pipeline/fetch_corpus.py first")

    roots = load_strong_verb_roots()

    entries = []
    skipped_suffix = []
    conj_counts = {label: 0 for label in CONJUGATIONS.values()}

    for book_code, book_name in BOOK_ORDER:
        path = os.path.join(WLC_DIR, f"{book_code}.xml")
        root = ET.parse(path).getroot()
        for verse in root.iter(f"{OSIS_NS}verse"):
            vid = verse.get("osisID")
            if vid is None:
                continue
            for w in verse.iter(f"{OSIS_NS}w"):
                wid = w.get("id")
                raw_lemma = w.get("lemma")
                raw_morph = w.get("morph")
                if not raw_lemma or not raw_morph:
                    continue
                lemma_parts = raw_lemma.split("/")
                morph_parts = raw_morph.split("/")
                word_parts = (w.text or "").split("/")

                for i, mp in enumerate(morph_parts):
                    # Only the *first* slash-separated part carries the H/A
                    # language-code prefix (confirmed in hebrew_corpus.py /
                    # rank_lemmas.py); later parts are bare POS codes already.
                    if i == 0:
                        mp = mp[1:] if mp.startswith(("H", "A")) else mp
                    m = MORPH_RE.match(mp)
                    if not m:
                        continue
                    conj, suffix = m.groups()
                    label = CONJUGATIONS[conj]

                    lp_raw = lemma_parts[i].strip() if i < len(lemma_parts) else ""
                    lp = re.match(r"^(\d+)", lp_raw)
                    if not lp:
                        continue
                    lemma_id = "H" + lp.group(1)
                    root_entry = roots.get(lemma_id)
                    if root_entry is None:
                        continue

                    pgn = parse_pgn(conj, suffix)
                    if pgn is None:
                        skipped_suffix.append({"verse": vid, "morph": mp, "lemma_id": lemma_id})
                        continue

                    surface_raw = word_parts[i] if i < len(word_parts) else ""
                    surface = strip_cantillation(surface_raw.replace("/", ""))
                    if not surface:
                        continue

                    entries.append({
                        "id": f"{wid or vid}-{i}",
                        "ref": vid,
                        "book": book_name,
                        "surface_form": surface,
                        "transliteration": transliterate(surface),
                        "lemma_id": lemma_id,
                        "root_citation_form": root_entry["citation_form"],
                        "root_transliteration": root_entry["transliteration"],
                        "gloss": root_entry["gloss"],
                        "stem": "Qal",
                        "conjugation": label,
                        "person": pgn["person"],
                        "gender": pgn["gender"],
                        "number": pgn["number"],
                        "state": pgn["state"],
                    })
                    conj_counts[label] += 1

    print(f"Built {len(entries)} parse entries across {len(conj_counts)} conjugations:")
    for label, n in conj_counts.items():
        print(f"  {label}: {n}")
    if skipped_suffix:
        print(f"WARNING: {len(skipped_suffix)} matches had an unparseable PGN suffix, skipped", file=sys.stderr)

    out = {
        "metadata": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "stem": "Qal",
            "conjugations": list(CONJUGATIONS.values()),
            "strong_root_definition": (
                "triliteral; no radical in {alef,he,het,ayin}; "
                "first radical not nun; first radical not vav/yod; "
                "second radical not vav/yod; second radical does not equal third"
            ),
            "root_lemma_source": "data/vocab_deck_600.json verb entries (rank 1-600)",
            "count": len(entries),
            "conjugation_counts": conj_counts,
            "distinct_roots": len({e["lemma_id"] for e in entries}),
            "skipped_unparseable_suffix": len(skipped_suffix),
        },
        "entries": entries,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(entries)} entries to {OUT_PATH}")

    if skipped_suffix:
        anomaly_path = os.path.join(HERE, "build_parse_qal_anomalies.json")
        with open(anomaly_path, "w", encoding="utf-8") as f:
            json.dump(skipped_suffix, f, ensure_ascii=False, indent=2)
        print(f"Anomaly detail written to {anomaly_path}")


if __name__ == "__main__":
    main()

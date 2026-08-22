"""
Independent verification of data/parse_qal_strong.json (rule 3: every
generation step ships a verification script).

Deliberately does NOT import build_parse_qal.py's extraction or
classification code -- everything here is re-derived with its own regex
over the raw corpus bytes and its own copy of the strong-root rule, so a
bug specific to one implementation (an off-by-one in the morph regex, a
wrong guttural set) is unlikely to be invisible to both. This is exactly
the class of bug CLAUDE.md's rule 3 warns is always present: a bad morph
regex has already once silently selected a construct-plural where a
different form was wanted, during Tier 0.

Checks performed:
  1. Structural integrity: metadata counts match the entry list, every
     entry's PGN fields are shaped correctly for its conjugation (finite
     forms need person+gender+number and no state; participles need
     gender+number+state and no person; infinitive construct needs none).
  2. Character-set sanity on every surface_form / root_citation_form /
     transliteration.
  3. Every entry's (lemma_id, root_citation_form, gloss,
     root_transliteration) matches the corresponding verb entry in
     data/vocab_deck_600.json exactly -- no drift between the two files.
  4. Independent regex re-scan of the WLC corpus for Vq<conj><suffix>
     morph codes restricted to an independently-recomputed strong-root set,
     compared against the JSON for exact per-conjugation and per-root
     frequency counts (not just totals).
  5. Every entry's ref (osisID) exists in the corresponding book file.
"""
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict

from hebrew_corpus import BOOK_ORDER, WLC_DIR

HERE = os.path.dirname(os.path.abspath(__file__))
DECK_PATH = os.path.join(HERE, "..", "data", "vocab_deck_600.json")
DATA_PATH = os.path.join(HERE, "..", "data", "parse_qal_strong.json")

CANTILLATION_RE = re.compile("[֑-֯]")
ALLOWED_HEB_RE = re.compile("^[֑-ׇ͏א-ת]*$")
ALLOWED_TRANSLIT_RE = re.compile(r"^['`a-z]+$")

GUTTURAL = set("אהחע")
NUN = "נ"
VAVYOD = set("וי")
FINAL_TO_BASE = {"ך": "כ", "ם": "מ", "ן": "נ", "ף": "פ", "ץ": "צ"}

VERSE_RE = re.compile(r'<verse osisID="([^"]+)">(.*?)</verse>', re.S)
WORD_RE = re.compile(r'<w\b([^>]*)>(.*?)</w>', re.S)
ATTR_RE = lambda name: re.compile(rf'{name}="([^"]*)"')
LEMMA_ATTR_RE = ATTR_RE("lemma")
MORPH_ATTR_RE = ATTR_RE("morph")

MORPH_RE = re.compile(r"^Vq([pwqrc])([123]?[mfc]?[spd]?[ac]?)$")
FINITE = {"p", "w", "q"}
CONJ_LABEL = {"p": "qatal", "w": "wayyiqtol", "q": "yiqtol", "r": "participle", "c": "infinitive_construct"}

failures = []


def fail(msg):
    failures.append(msg)
    print(f"FAIL: {msg}", file=sys.stderr)


def strip_cantillation(s):
    return CANTILLATION_RE.sub("", s)


def is_strong_root(citation_form):
    c = [FINAL_TO_BASE.get(ch, ch) for ch in citation_form if "א" <= ch <= "ת"]
    if len(c) != 3:
        return False
    r1, r2, r3 = c
    if r1 in GUTTURAL or r2 in GUTTURAL or r3 in GUTTURAL:
        return False
    if r1 == NUN or r1 in VAVYOD:
        return False
    if r2 in VAVYOD or r2 == r3:
        return False
    return True


def load_deck_verbs():
    with open(DECK_PATH, encoding="utf-8") as f:
        deck = json.load(f)
    return {e["lemma_id"]: e for e in deck["entries"] if e["pos"] == "Verb"}


def scan_corpus(strong_lemma_ids):
    """Independent regex pass: for each verse, each <w>, each slash part,
    match Vq<conj><suffix> and tally (lemma_id, conjugation) -> count, plus
    remember every osisID seen per book for the ref-existence check."""
    counts = Counter()
    root_counts = Counter()
    verse_ids_by_book = defaultdict(set)

    for book_code, book_name in BOOK_ORDER:
        path = os.path.join(WLC_DIR, f"{book_code}.xml")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        for vid, vinner in VERSE_RE.findall(content):
            verse_ids_by_book[book_code].add(vid)
            for attrs, _text in WORD_RE.findall(vinner):
                lemma_m = LEMMA_ATTR_RE.search(attrs)
                morph_m = MORPH_ATTR_RE.search(attrs)
                if not lemma_m or not morph_m:
                    continue
                lemma_parts = lemma_m.group(1).split("/")
                morph_parts = morph_m.group(1).split("/")
                for i, mp in enumerate(morph_parts):
                    if i == 0 and mp[:1] in ("H", "A"):
                        mp = mp[1:]
                    m = MORPH_RE.match(mp)
                    if not m:
                        continue
                    conj, suffix = m.groups()
                    lp = lemma_parts[i].strip() if i < len(lemma_parts) else ""
                    num_m = re.match(r"^(\d+)", lp)
                    if not num_m:
                        continue
                    lemma_id = "H" + num_m.group(1)
                    if lemma_id not in strong_lemma_ids:
                        continue
                    # Same suffix-shape gate as build_parse_qal.py: finite
                    # forms need exactly person+gender+number, participles
                    # need exactly gender+number+state, infinitives need none.
                    if conj in FINITE and not re.match(r"^[123][mfc][spd]$", suffix):
                        continue
                    if conj == "r" and not re.match(r"^[mfc][spd][ac]$", suffix):
                        continue
                    if conj == "c" and suffix:
                        continue
                    counts[(lemma_id, CONJ_LABEL[conj])] += 1
                    root_counts[lemma_id] += 1

    return counts, root_counts, verse_ids_by_book


def main():
    if not os.path.isfile(DATA_PATH):
        sys.exit("data/parse_qal_strong.json not found -- run pipeline/build_parse_qal.py first")

    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    meta = data["metadata"]
    entries = data["entries"]

    # --- 1. structural integrity -----------------------------------------
    if meta["count"] != len(entries):
        fail(f"metadata.count={meta['count']} but {len(entries)} entries present")

    conj_sum = sum(meta["conjugation_counts"].values())
    if conj_sum != len(entries):
        fail(f"conjugation_counts sums to {conj_sum} but {len(entries)} entries present")

    ids = [e["id"] for e in entries]
    if len(ids) != len(set(ids)):
        fail("duplicate entry ids present")

    deck_verbs = load_deck_verbs()

    for e in entries:
        tag = f"{e['id']} ({e['ref']})"
        conj = e["conjugation"]
        if conj not in CONJ_LABEL.values():
            fail(f"{tag}: unrecognized conjugation {conj!r}")
            continue

        if conj in ("qatal", "wayyiqtol", "yiqtol"):
            if not (e["person"] and e["gender"] and e["number"]) or e["state"] is not None:
                fail(f"{tag}: {conj} entry has wrong PGN shape (expected person+gender+number, no state): {e}")
        elif conj == "participle":
            if e["person"] is not None or not (e["gender"] and e["number"] and e["state"]):
                fail(f"{tag}: participle entry has wrong PGN shape (expected gender+number+state, no person): {e}")
        elif conj == "infinitive_construct":
            if any([e["person"], e["gender"], e["number"], e["state"]]):
                fail(f"{tag}: infinitive_construct entry should have all PGN fields null: {e}")

        # --- 2. character-set sanity --------------------------------------
        if not e["surface_form"] or not ALLOWED_HEB_RE.match(e["surface_form"]):
            fail(f"{tag}: surface_form missing or has unexpected characters: {e['surface_form']!r}")
        if not e["root_citation_form"] or not ALLOWED_HEB_RE.match(e["root_citation_form"]):
            fail(f"{tag}: root_citation_form missing or has unexpected characters: {e['root_citation_form']!r}")
        for field in ("transliteration", "root_transliteration"):
            v = e.get(field, "")
            if not v or not ALLOWED_TRANSLIT_RE.match(v):
                fail(f"{tag}: {field} {v!r} is empty or outside the locked ASCII scheme")
        if not e["gloss"]:
            fail(f"{tag}: empty gloss")

        # --- 3. root data matches the vocab deck exactly ------------------
        deck_e = deck_verbs.get(e["lemma_id"])
        if deck_e is None:
            fail(f"{tag}: lemma_id {e['lemma_id']} is not a Verb entry in vocab_deck_600.json")
            continue
        if deck_e["citation_form"] != e["root_citation_form"]:
            fail(f"{tag}: root_citation_form {e['root_citation_form']!r} != deck citation_form {deck_e['citation_form']!r}")
        if deck_e["transliteration"] != e["root_transliteration"]:
            fail(f"{tag}: root_transliteration mismatch vs deck")
        if deck_e["gloss"] != e["gloss"]:
            fail(f"{tag}: gloss mismatch vs deck")
        if not is_strong_root(deck_e["citation_form"]):
            fail(f"{tag}: lemma_id {e['lemma_id']} ({deck_e['citation_form']}) is not a strong root by independent re-check")

    # --- 4. independent regex re-scan of the corpus -----------------------
    print("Re-scanning corpus independently (regex-based)...")
    strong_lemma_ids = {lid for lid, e in deck_verbs.items() if is_strong_root(e["citation_form"])}
    expected_pair_counts, expected_root_counts, verse_ids_by_book = scan_corpus(strong_lemma_ids)

    actual_pair_counts = Counter()
    actual_root_counts = Counter()
    for e in entries:
        actual_pair_counts[(e["lemma_id"], e["conjugation"])] += 1
        actual_root_counts[e["lemma_id"]] += 1

    if expected_pair_counts != actual_pair_counts:
        only_expected = {k: v for k, v in expected_pair_counts.items() if actual_pair_counts.get(k) != v}
        only_actual = {k: v for k, v in actual_pair_counts.items() if expected_pair_counts.get(k) != v}
        fail(f"per (lemma, conjugation) counts differ from independent recount: "
             f"expected-but-mismatched={only_expected} actual-but-mismatched={only_actual}")

    conj_totals_expected = Counter()
    for (_, conj), n in expected_pair_counts.items():
        conj_totals_expected[conj] += n
    for conj, n in meta["conjugation_counts"].items():
        if conj_totals_expected.get(conj, 0) != n:
            fail(f"conjugation_counts[{conj}]={n} but independent recount got {conj_totals_expected.get(conj, 0)}")

    expected_distinct_roots = len({lid for lid, _ in expected_pair_counts})
    if meta["distinct_roots"] != expected_distinct_roots:
        fail(f"metadata.distinct_roots={meta['distinct_roots']} but independent recount got {expected_distinct_roots}")

    if meta["count"] != sum(expected_pair_counts.values()):
        fail(f"metadata.count={meta['count']} but independent recount got {sum(expected_pair_counts.values())}")

    # --- 5. every ref exists in its book -----------------------------------
    book_by_name = {name: code for code, name in BOOK_ORDER}
    for e in entries:
        code = book_by_name.get(e["book"])
        if code is None:
            fail(f"{e['id']}: unrecognized book name {e['book']!r}")
            continue
        if e["ref"] not in verse_ids_by_book[code]:
            fail(f"{e['id']}: ref {e['ref']} not found in {code}.xml")

    print(f"Checked {len(entries)} parse entries against {len(strong_lemma_ids)} independently-classified strong roots.")

    if failures:
        print(f"\n{len(failures)} FAILURE(S)", file=sys.stderr)
        sys.exit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()

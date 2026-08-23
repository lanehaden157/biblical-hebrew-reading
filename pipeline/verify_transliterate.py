"""
Verification for transliterate.py, in two parts:

1. Curated spot checks -- keyed by Strong's number, not by hand-typed Hebrew
   (rule 1: never hand-type pointed Hebrew). The actual pointed citation
   form is pulled from data/top600.json at check time. Each expected ASCII
   value was worked out by hand by decoding the word's actual Unicode
   codepoints (dumped and read directly, not recalled from memory) and
   applying the rules documented in transliterate.py's docstring -- not
   copied from the generator's own output.

   Covers every non-trivial code path: cholam-vav, shuruk, hiriq-yod,
   shin/sin dot (both with and without matres-lectionis interaction),
   alef/ayin, final letters, word-final silent shva, word-initial vocal
   shva, a consecutive shva pair (first silent / second vocal), dagesh-
   sensitive bet/kaf/pe (soft forms render v/kh/f; soft kaf intentionally
   shares "kh" with het -- see transliterate.py's docstring), and furtive
   patach on a word-final het/ayin.

2. A full-corpus stress test over all 600 top600.json citation forms:
   every one must transliterate without raising, produce non-empty output,
   and use only the locked scheme's alphabet -- catches crashes and
   mapping gaps that the curated list, being only ~15 words, can't.

3. Word-initial-shuruq regression checks -- keyed by OSIS word id, pulled
   straight from the raw WLC XML (not from any already-generated JSON, so
   this stays independent of the reader/parse-deck build scripts). No
   top600.json citation form exhibits this pattern (it's a surface-level
   vav-conjunctive allomorph, never how a lemma is cited), so it needs its
   own corpus-anchored source.
"""
import json
import os
import re
import xml.etree.ElementTree as ET

from hebrew_corpus import OSIS_NS, WLC_DIR
from transliterate import transliterate

HERE = os.path.dirname(os.path.abspath(__file__))
TOP600_PATH = os.path.join(HERE, "..", "data", "top600.json")
RESULT_PATH = os.path.join(HERE, "..", "scratch_verify_result.txt")

# lemma_id -> (label, hand-verified expected ASCII, what it covers)
EXPECTED = {
    "H7965": ("peace", "shalom", "cholam-vav; shin dot"),
    "H3117": ("day", "yom", "word-initial yod absorbing cholam-vav"),
    "H430": ("God", "'elohim", "alef=', hataf segol, hiriq-yod"),
    "H1": ("father", "'av", "bet with no dagesh -> soft, v"),
    "H1121": ("son", "ben", "tsere, final nun"),
    "H8451": ("law", "torah", "cholam-vav, final heh always h"),
    "H1697": ("word", "davar", "bet with no dagesh -> soft, v"),
    "H5971": ("people", "`am", "ayin = `"),
    "H776": ("land", "'erets", "segol, final tsadi"),
    "H3068": ("YHWH", "yehowah", "word-initial vocal shva; masoretic pointing"),
    "H3414": ("Jeremiah", "yirmeyah", "consecutive shva pair: 1st silent, 2nd vocal"),
    "H3063": ("Judah", "yehudah", "shuruk absorbed by a vowel-less consonant"),
    "H8147": ("two", "shenayim", "word-initial vocal shva, shin dot"),
    "H7760": ("put/set", "sum", "sin dot; shuruk absorbed by sin"),
    "H8269": ("official", "sar", "sin dot with a direct (non-absorbed) vowel"),
    "F-l": ("to/for prefix", "le", "lone consonant+shva: word-initial wins over word-final"),
    "F-b": ("in/on/with prefix", "be", "lone consonant+shva: word-initial wins over word-final; bet HAS a dagesh here, stays hard b"),
    "F-k": ("like/as prefix", "ke", "lone consonant+shva: word-initial wins over word-final; kaf HAS a dagesh here, stays hard k"),
    "H4428": ("king", "melekh", "final kaf with no dagesh -> soft, kh"),
    "H5307": ("fall", "nafal", "pe with no dagesh -> soft, f"),
    "H3130": ("Joseph", "yosef", "final pe with no dagesh -> soft, f"),
    "H1293": ("blessing", "berakhah", "kaf with no dagesh -> soft, kh"),
    "H7307": ("spirit/wind", "ruakh", "furtive patach on final het: vowel-then-consonant order"),
    "H7453": ("friend/neighbor", "rea`", "furtive patach on final ayin: vowel-then-consonant order"),
}

# Only ASCII the locked scheme can ever produce.
ALLOWED_OUTPUT_RE = re.compile(r"^['`a-z]*$")

# (book_code, osisID word id) -> (label, hand-verified expected ASCII).
# Both worked out by hand from the raw codepoints, per the same standard as
# EXPECTED above -- never copied from transliterate()'s own output.
WORD_EXPECTED = {
    ("Jonah", "32V27"): ("Jonah 1:8 'and from where' -- word-initial shuruq (BuMP rule), not bare 'w'", "ume'ayin"),
    ("Jonah", "32ewe"): ("Jonah 1:8 'and where' -- ordinary vav-conjunctive shva, unaffected by the shuruq fix", "we'ey"),
}


def run_word_checks():
    failures = []
    checked = 0
    by_book = {}
    for (book, wid), (label, expected) in WORD_EXPECTED.items():
        if book not in by_book:
            path = os.path.join(WLC_DIR, f"{book}.xml")
            by_book[book] = {
                w.get("id"): (w.text or "").replace("/", "")
                for w in ET.parse(path).getroot().iter(f"{OSIS_NS}w")
            }
        form = by_book[book].get(wid)
        if form is None:
            failures.append(f"{book}/{wid} ({label}): word id not found")
            continue
        got = transliterate(form)
        checked += 1
        if got != expected:
            failures.append(f"{book}/{wid} ({label}): expected {expected!r}, got {got!r}")
    return checked, failures


def run_spot_checks(by_id):
    failures = []
    checked = 0
    for lid, (label, expected, covers) in EXPECTED.items():
        entry = by_id.get(lid)
        if entry is None:
            failures.append(f"{lid} ({label}): not found in top600.json")
            continue
        got = transliterate(entry["citation_form"])
        checked += 1
        if got != expected:
            failures.append(f"{lid} ({label}, tests: {covers}): expected {expected!r}, got {got!r}")
    return checked, failures


def run_stress_test(lemmas):
    failures = []
    checked = 0
    for e in lemmas:
        form = entry_form = e["citation_form"]
        checked += 1
        try:
            got = transliterate(form)
        except Exception as exc:
            failures.append(f"{e['lemma_id']} (rank {e['rank']}): raised {exc!r}")
            continue
        if not got:
            failures.append(f"{e['lemma_id']} (rank {e['rank']}): produced empty output")
        elif not ALLOWED_OUTPUT_RE.match(got):
            failures.append(f"{e['lemma_id']} (rank {e['rank']}): output {got!r} has unexpected characters")
    return checked, failures


def main():
    with open(TOP600_PATH, encoding="utf-8") as f:
        top600 = json.load(f)
    by_id = {e["lemma_id"]: e for e in top600["lemmas"]}

    spot_checked, spot_failures = run_spot_checks(by_id)
    stress_checked, stress_failures = run_stress_test(top600["lemmas"])
    word_checked, word_failures = run_word_checks()

    lines = [
        f"Spot checks: {spot_checked}/{len(EXPECTED)} forms checked, {len(spot_failures)} failures.",
        f"Stress test: {stress_checked}/{len(top600['lemmas'])} corpus forms checked, {len(stress_failures)} failures.",
        f"Word checks: {word_checked}/{len(WORD_EXPECTED)} corpus words checked, {len(word_failures)} failures.",
    ]
    if spot_failures:
        lines.append("SPOT CHECK FAILURES:")
        lines += [f" - {f}" for f in spot_failures]
    if stress_failures:
        lines.append("STRESS TEST FAILURES:")
        lines += [f" - {f}" for f in stress_failures[:50]]
        if len(stress_failures) > 50:
            lines.append(f"   ... and {len(stress_failures) - 50} more")
    if word_failures:
        lines.append("WORD CHECK FAILURES:")
        lines += [f" - {f}" for f in word_failures]
    if not spot_failures and not stress_failures and not word_failures:
        lines.append("All checks passed.")

    with open(RESULT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    if spot_failures or stress_failures or word_failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

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
   shva, a consecutive shva pair (first silent / second vocal), and two
   rules that diverge from academic transliteration convention on purpose
   (bet is always "b" never "v"; kaf is always "k" never "kh" -- the
   locked scheme has no separate fricative letters).

2. A full-corpus stress test over all 600 top600.json citation forms:
   every one must transliterate without raising, produce non-empty output,
   and use only the locked scheme's alphabet -- catches crashes and
   mapping gaps that the curated list, being only ~15 words, can't.
"""
import json
import os
import re

from transliterate import transliterate

HERE = os.path.dirname(os.path.abspath(__file__))
TOP600_PATH = os.path.join(HERE, "..", "data", "top600.json")
RESULT_PATH = os.path.join(HERE, "..", "scratch_verify_result.txt")

# lemma_id -> (label, hand-verified expected ASCII, what it covers)
EXPECTED = {
    "H7965": ("peace", "shalom", "cholam-vav; shin dot"),
    "H4428": ("king", "melek", "final kaf = k, not kh; final shva silent"),
    "H3117": ("day", "yom", "word-initial yod absorbing cholam-vav"),
    "H430": ("God", "'elohim", "alef=', hataf segol, hiriq-yod"),
    "H1": ("father", "'ab", "bet is always b, never v"),
    "H1121": ("son", "ben", "tsere, final nun"),
    "H8451": ("law", "torah", "cholam-vav, final heh always h"),
    "H1697": ("word", "dabar", "bet is always b, never v"),
    "H5971": ("people", "`am", "ayin = `"),
    "H776": ("land", "'erets", "segol, final tsadi"),
    "H3068": ("YHWH", "yehowah", "word-initial vocal shva; masoretic pointing"),
    "H3414": ("Jeremiah", "yirmeyah", "consecutive shva pair: 1st silent, 2nd vocal"),
    "H3063": ("Judah", "yehudah", "shuruk absorbed by a vowel-less consonant"),
    "H8147": ("two", "shenayim", "word-initial vocal shva, shin dot"),
    "H7760": ("put/set", "sum", "sin dot; shuruk absorbed by sin"),
    "H8269": ("official", "sar", "sin dot with a direct (non-absorbed) vowel"),
    "F-l": ("to/for prefix", "le", "lone consonant+shva: word-initial wins over word-final"),
    "F-b": ("in/on/with prefix", "be", "lone consonant+shva: word-initial wins over word-final"),
    "F-k": ("like/as prefix", "ke", "lone consonant+shva: word-initial wins over word-final"),
}

# Only ASCII the locked scheme can ever produce.
ALLOWED_OUTPUT_RE = re.compile(r"^['`a-z]*$")


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

    lines = [
        f"Spot checks: {spot_checked}/{len(EXPECTED)} forms checked, {len(spot_failures)} failures.",
        f"Stress test: {stress_checked}/{len(top600['lemmas'])} corpus forms checked, {len(stress_failures)} failures.",
    ]
    if spot_failures:
        lines.append("SPOT CHECK FAILURES:")
        lines += [f" - {f}" for f in spot_failures]
    if stress_failures:
        lines.append("STRESS TEST FAILURES:")
        lines += [f" - {f}" for f in stress_failures[:50]]
        if len(stress_failures) > 50:
            lines.append(f"   ... and {len(stress_failures) - 50} more")
    if not spot_failures and not stress_failures:
        lines.append("All checks passed.")

    with open(RESULT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    if spot_failures or stress_failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

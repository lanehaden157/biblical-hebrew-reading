"""
Verification for build_vocab_deck.py's output (data/vocab_deck_600.json).
Checks structural integrity (rule 3: every generation step ships a
verification script) and that rule 4 (transliteration + gloss on every
Hebrew form) actually held for every entry, not just the ones spot-
checked in transliterate.py.

Independently redeclares the exclusion/non-drill/function-word rules
build_vocab_deck.py applies, rather than importing them, so a bug in one
script's list isn't masked by checking against itself.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DECK_PATH = os.path.join(HERE, "..", "data", "vocab_deck_600.json")
GLOSSES = [
    os.path.join(HERE, "..", "glosses", f"batch_{a:03d}_{b:03d}.json")
    for a, b in [(1, 100), (101, 200), (201, 300), (301, 400), (401, 500), (501, 600)]
]

ALLOWED_TRANSLIT_RE = re.compile(r"^['`a-z]+$")
HEBREW_CHAR_RE = re.compile(r"[א-ת]")

EXPECTED_EXCLUDED = {
    "H1768", "H4481", "H5922", "H3809", "H4430", "H3606", "H426", "H1934", "H560",
    "H5542", "H1077",
}
EXPECTED_NON_DRILL = {"H853", "H854"}
# {secondary_lemma_id: primary_lemma_id} -- see build_vocab_deck.py's
# MERGED_LEMMAS docstring.
EXPECTED_MERGED = {"H854": "H5973"}
EXPECTED_FUNCTION_POS = {
    "Preposition", "Conjunction", "Particle",
    "Definite article", "Interrogative particle", "Relative particle",
}
# The 11 tier-1 particles curated with a core_schema field (see
# build_vocab_deck.py's docstring and glosses/*.json). Kept as its own
# independent list so a missing or accidentally-added schema is caught.
EXPECTED_SCHEMA_LEMMAS = {
    "F-l", "F-b", "F-m", "H4480", "H5921", "H3588", "F-k", "H5704", "H310", "H8478", "H5048",
}
# Lemmas curated with a confusable_with note (see build_vocab_deck.py's
# docstring and glosses/*.json).
EXPECTED_CONFUSABLE_LEMMAS = {"H518", "H5973", "H2005", "H389", "F-s", "H3644"}


def main():
    with open(DECK_PATH, encoding="utf-8") as f:
        deck = json.load(f)
    entries = deck["entries"]

    failures = []

    raw = []
    for path in GLOSSES:
        with open(path, encoding="utf-8") as f:
            raw.extend(json.load(f)["entries"])
    expected_count = sum(1 for e in raw if e["lemma_id"] not in EXPECTED_EXCLUDED)

    ranks = [e["rank"] for e in entries]
    if len(entries) != expected_count:
        failures.append(f"expected {expected_count} entries (600 minus exclusions), got {len(entries)}")
    if set(ranks) != set(range(1, len(entries) + 1)):
        missing = sorted(set(range(1, len(entries) + 1)) - set(ranks))
        extra = sorted(set(ranks) - set(range(1, len(entries) + 1)))
        failures.append(f"rank coverage broken: missing={missing} extra={extra}")
    if len(ranks) != len(set(ranks)):
        failures.append("duplicate ranks present")

    deck_lemmas = {e["lemma_id"] for e in entries}
    still_present = deck_lemmas & EXPECTED_EXCLUDED
    if still_present:
        failures.append(f"excluded lemmas still in deck: {sorted(still_present)}")
    for e in entries:
        if "(Aramaic)" in e.get("gloss", ""):
            failures.append(f"rank {e['rank']} ({e['lemma_id']}): Aramaic gloss survived the exclusion filter")

    schema_lemmas = {e["lemma_id"] for e in entries if e.get("core_schema")}
    if schema_lemmas != EXPECTED_SCHEMA_LEMMAS:
        failures.append(
            f"core_schema lemma set mismatch: missing={sorted(EXPECTED_SCHEMA_LEMMAS - schema_lemmas)}, "
            f"unexpected={sorted(schema_lemmas - EXPECTED_SCHEMA_LEMMAS)}"
        )

    confusable_lemmas = {e["lemma_id"] for e in entries if e.get("confusable_with")}
    if confusable_lemmas != EXPECTED_CONFUSABLE_LEMMAS:
        failures.append(
            f"confusable_with lemma set mismatch: missing={sorted(EXPECTED_CONFUSABLE_LEMMAS - confusable_lemmas)}, "
            f"unexpected={sorted(confusable_lemmas - EXPECTED_CONFUSABLE_LEMMAS)}"
        )

    for e in entries:
        tag = f"rank {e['rank']} ({e['lemma_id']})"
        if not e.get("citation_form") or not HEBREW_CHAR_RE.search(e["citation_form"]):
            failures.append(f"{tag}: citation_form missing or has no Hebrew letters")
        if not e.get("gloss"):
            failures.append(f"{tag}: empty gloss")
        translit = e.get("transliteration", "")
        if not translit:
            failures.append(f"{tag}: empty transliteration")
        elif not ALLOWED_TRANSLIT_RE.match(translit):
            failures.append(f"{tag}: transliteration {translit!r} has unexpected characters")

        expected_fn = e["lemma_id"].startswith("F-") or e["pos"] in EXPECTED_FUNCTION_POS
        if e.get("is_function_word") != expected_fn:
            failures.append(f"{tag}: is_function_word={e.get('is_function_word')}, expected {expected_fn}")

        expected_drillable = e["lemma_id"] not in EXPECTED_NON_DRILL
        if e.get("drillable") != expected_drillable:
            failures.append(f"{tag}: drillable={e.get('drillable')}, expected {expected_drillable}")

    by_lemma = {e["lemma_id"]: e for e in entries}
    for secondary_id, primary_id in EXPECTED_MERGED.items():
        secondary = by_lemma.get(secondary_id)
        primary = by_lemma.get(primary_id)
        if secondary is None or primary is None:
            failures.append(f"merge {secondary_id}->{primary_id}: one or both lemmas missing from deck")
            continue
        if secondary.get("merged_into") != primary_id:
            failures.append(f"{secondary_id}: merged_into={secondary.get('merged_into')!r}, expected {primary_id!r}")
        mw = primary.get("merged_with") or {}
        if mw.get("lemma_id") != secondary_id:
            failures.append(f"{primary_id}: merged_with.lemma_id={mw.get('lemma_id')!r}, expected {secondary_id!r}")
        if mw.get("citation_form") != secondary.get("citation_form"):
            failures.append(f"{primary_id}: merged_with.citation_form doesn't match {secondary_id}'s own citation_form")
        if mw.get("transliteration") != secondary.get("transliteration"):
            failures.append(f"{primary_id}: merged_with.transliteration doesn't match {secondary_id}'s own transliteration")
        if primary["gloss"] != secondary["gloss"]:
            failures.append(f"merge {secondary_id}->{primary_id}: glosses differ ({secondary['gloss']!r} vs {primary['gloss']!r})")
    for e in entries:
        lid = e["lemma_id"]
        if lid not in EXPECTED_MERGED and "merged_into" in e:
            failures.append(f"{lid}: unexpected merged_into field ({e['merged_into']!r})")
        if lid not in EXPECTED_MERGED.values() and "merged_with" in e:
            failures.append(f"{lid}: unexpected merged_with field")

    # Cross-check against the source batch files: every gloss-batch entry
    # (minus exclusions) must appear in the deck with an identical
    # citation_form and gloss, matched by source_rank -- the deck's own
    # "rank" is renumbered after exclusions, so it is no longer the same
    # value as the batch file's "rank" (independent re-derivation, not
    # just "the merge script ran").
    by_source_rank = {e["source_rank"]: e for e in entries}
    for path in GLOSSES:
        with open(path, encoding="utf-8") as f:
            batch = json.load(f)
        for src in batch["entries"]:
            if src["lemma_id"] in EXPECTED_EXCLUDED:
                if src["rank"] in by_source_rank:
                    failures.append(f"source_rank {src['rank']}: excluded lemma {src['lemma_id']} still in deck")
                continue
            deck_e = by_source_rank.get(src["rank"])
            if deck_e is None:
                failures.append(f"source_rank {src['rank']}: present in {os.path.basename(path)} but missing from deck")
                continue
            if deck_e["citation_form"] != src["citation_form"]:
                failures.append(f"source_rank {src['rank']}: citation_form mismatch vs {os.path.basename(path)}")
            if deck_e["gloss"] != src["gloss"]:
                failures.append(f"source_rank {src['rank']}: gloss mismatch vs {os.path.basename(path)}")
            if deck_e["lemma_id"] != src["lemma_id"]:
                failures.append(f"source_rank {src['rank']}: lemma_id mismatch vs {os.path.basename(path)}")
            if src.get("core_schema") and deck_e.get("core_schema") != src["core_schema"]:
                failures.append(f"source_rank {src['rank']}: core_schema mismatch vs {os.path.basename(path)}")
            if src.get("confusable_with") and deck_e.get("confusable_with") != src["confusable_with"]:
                failures.append(f"source_rank {src['rank']}: confusable_with mismatch vs {os.path.basename(path)}")

    with open(os.path.join(HERE, "..", "scratch_verify_deck.txt"), "w", encoding="utf-8") as f:
        f.write(f"Checked {len(entries)} deck entries.\n")
        if failures:
            f.write(f"{len(failures)} FAILURES:\n")
            for fl in failures:
                f.write(f" - {fl}\n")
        else:
            f.write("All checks passed.\n")

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

"""
Verification for build_vocab_deck.py's output (data/vocab_deck_600.json).
Checks structural integrity (rule 3: every generation step ships a
verification script) and that rule 4 (transliteration + gloss on every
Hebrew form) actually held for all 600 entries, not just the ones spot-
checked in transliterate.py.
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


def main():
    with open(DECK_PATH, encoding="utf-8") as f:
        deck = json.load(f)
    entries = deck["entries"]

    failures = []

    ranks = [e["rank"] for e in entries]
    if len(entries) != 600:
        failures.append(f"expected 600 entries, got {len(entries)}")
    if set(ranks) != set(range(1, 601)):
        missing = sorted(set(range(1, 601)) - set(ranks))
        extra = sorted(set(ranks) - set(range(1, 601)))
        failures.append(f"rank coverage broken: missing={missing} extra={extra}")
    if len(ranks) != len(set(ranks)):
        failures.append("duplicate ranks present")

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

    # Cross-check against the source batch files: every gloss-batch entry in
    # 1-200 must appear in the deck with an identical citation_form and
    # gloss (independent re-derivation, not just "the merge script ran").
    by_rank = {e["rank"]: e for e in entries}
    for path in GLOSSES:
        with open(path, encoding="utf-8") as f:
            batch = json.load(f)
        for src in batch["entries"]:
            deck_e = by_rank.get(src["rank"])
            if deck_e is None:
                failures.append(f"rank {src['rank']}: present in {os.path.basename(path)} but missing from deck")
                continue
            if deck_e["citation_form"] != src["citation_form"]:
                failures.append(f"rank {src['rank']}: citation_form mismatch vs {os.path.basename(path)}")
            if deck_e["gloss"] != src["gloss"]:
                failures.append(f"rank {src['rank']}: gloss mismatch vs {os.path.basename(path)}")
            if deck_e["lemma_id"] != src["lemma_id"]:
                failures.append(f"rank {src['rank']}: lemma_id mismatch vs {os.path.basename(path)}")

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

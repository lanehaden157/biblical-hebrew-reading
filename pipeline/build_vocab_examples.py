"""
Real Bible usage examples for the ordinary (non-function-word) vocab deck ->
data/vocab_examples.json. Sibling to build_function_word_examples.py, whose
tiered/rotation machinery is for the 44 function words specifically (see
that file's docstring) and stays there unchanged; this file exists because
Lane also wants at least one real example on every other card (2026-08-29).

Why a separate file rather than folding into function_word_examples.json:
that file's TIER_TARGET (3/5/10 examples, sense-count scaling) exists
because function words are ambiguous -- a bare gloss like "in, on, with"
needs several occurrences to actually disambiguate. An ordinary noun or verb
isn't ambiguous the same way; the point of an example here is reading
fluency and pattern recognition, not sense disambiguation, so one good,
verified occurrence is the target, not a tiered minimum. Sharing the same
per-entry schema (lemma_id/citation_form/transliteration/full_gloss/
sense_count/examples[]) means app/main.js just merges this file's byLemma
map with function_word_examples.json's before handing both to vocab.js --
cardEl/cardBackEl don't know or care which file an example came from.

Scope and priority, per Lane: every drillable vocab_deck_600.json entry NOT
already covered by function_word_examples.json (544 lemmas as of this
writing). Verbs first, then adjectives, then everything else (nouns,
pronouns, adverbs) -- POS_PRIORITY below, not alphabetical or by lemma_id.
Done in batches, not one giant sweep: CURATED holds lemmas with a finished,
verified example; SKIPPED holds lemmas Lane said to file away rather than
force ("unclear examples with broad usage or no clear translation")
alongside why; anything in the target set that's in neither is silently
still PENDING for a future batch -- tracked in metadata.pending_count so
progress is visible, but never a build failure the way an *unexplained*
gap in the function-word set is. A lemma in both CURATED and SKIPPED, or in
SKIPPED, without a reason is still a hard error -- ambiguity about a
lemma's own status is a bug, absence from both is just unfinished work.

Same non-hand-typed-Hebrew discipline as build_function_word_examples.py:
CURATED only records (book_code, target word id, phrase start/end word id,
gloss, gloss_highlight, gloss_note) tuples; the actual Hebrew, its
transliteration, and target_index are all pulled from the corpus and
verified against the claimed lemma at build time, identically to that
file (see its docstring for the full rationale). pipeline/
find_lemma_occurrences.py is a throwaway lookup tool (not part of the
pipeline itself) used to find real word ids worth picking from, rather
than guessing them.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hebrew_corpus import OSIS_NS, WLC_DIR  # noqa: E402
from transliterate import transliterate  # noqa: E402
from build_function_word_examples import (  # noqa: E402
    strip_cantillation, load_book, matches_lemma, extract_phrase,
)

HERE = os.path.dirname(os.path.abspath(__file__))
DECK_PATH = os.path.join(HERE, "..", "data", "vocab_deck_600.json")
FWEX_PATH = os.path.join(HERE, "..", "data", "function_word_examples.json")
OUT_PATH = os.path.join(HERE, "..", "data", "vocab_examples.json")

# Batch 1 (2026-08-29): first 20 highest-frequency verbs. Sourced from
# Genesis 1-8 (creation/flood narrative, not yet a reader chapter but the
# plainest possible Hebrew) and Jonah/Ruth (both already-read reader
# chapters) for variety -- deliberately not all Genesis, per the same
# "too repetitive and Genesis-heavy" note that shaped the function-word
# batches.
CURATED = {
    "H559": [("Gen", "01thY", "01thY", "01JM7", "God said", "said", None)],
    "H1961": [("Gen", "01yw4", "01yw4", "01jbg", "there was light", "was", None)],
    "H6213": [("Gen", "01bmv", "01bmv", "01FV9", "God made", "made", None)],
    "H935": [("Jonah", "32gBW", "32gBW", "32eLD", "to enter the city", "enter", None)],
    "H5414": [("Gen", "012gM", "012gM", "01pAw", "I have given [it] to you", "given", None)],
    "H7200": [("Gen", "01USR", "01USR", "01v6U", "God saw", "saw", None)],
    "H8085": [("Gen", "01S67", "01S67", "014Yz", "you listened to your wife", "listened", "lit. \"to the voice of\" -- shama` + le- idiomatically means listen to/obey, not just hear")],
    "H1696": [("Gen", "01ZXK", "01ZXK", "01frz", "God spoke", "spoke", None)],
    "H3427": [("Ruth", "08wM5", "08wM5", "08qty", "they lived there", "lived", None)],
    "H3318": [("Jonah", "32LsC", "32LsC", "32LzS", "Jonah went out of the city", "went out", None)],
    "H7725": [("Ruth", "08tKT", "08tKT", "08sRU", "she returned from the fields of Moab", "returned", None)],
    "H3212": [("Ruth", "08LN3", "08LN3", "08Qzf", "a man went", "went", None)],
    "H3947": [("Ruth", "08E57", "08E57", "08vtM", "Boaz took Ruth", "took", None)],
    "H3045": [("Jonah", "32AxB", "32oAj", "32Ap3", "for the men knew", "knew", None)],
    "H5927": [("Ruth", "08rzR", "08KTp", "08bh3", "Boaz went up to the gate", "went up", None)],
    "H7971": [("Gen", "01kTA", "01kTA", "01rRy", "he sent out the dove", "sent out", None)],
    "H4191": [("Ruth", "08nAB", "08nAB", "08kfX", "Elimelech died", "died", None)],
    "H398": [("Ruth", "08nzj", "08nzj", "083Sx", "eat some of the bread", "eat", None)],
    "H7121": [("Jonah", "32PB6", "32PB6", "3237c", "and call out against it", "call out", None)],
    "H5375": [("Jonah", "32ecS", "32ecS", "32Xzm", "they lifted up Jonah", "lifted up", None)],
}

# Lemmas Lane said to file away rather than force a single example onto --
# populate as batches turn up a genuinely bad fit (a lemma whose sense is
# too broad/abstract for one occurrence to represent, or whose meaning in
# context resists a clean short English phrase). Empty for batch 1; none of
# the top 20 verbs needed it.
SKIPPED = {
    # "H####": "why -- e.g. 'sense too broad for a single representative phrase'",
}


def load_targets():
    with open(DECK_PATH, encoding="utf-8") as f:
        deck = json.load(f)
    with open(FWEX_PATH, encoding="utf-8") as f:
        fwex_covered = {e["lemma_id"] for e in json.load(f)["entries"]}
    targets = {}
    for e in deck["entries"]:
        if e.get("drillable", True) and e["lemma_id"] not in fwex_covered:
            targets[e["lemma_id"]] = e
    return targets


def main():
    if not os.path.isfile(DECK_PATH):
        sys.exit("data/vocab_deck_600.json not found -- run pipeline/build_vocab_deck.py first")
    if not os.path.isfile(FWEX_PATH):
        sys.exit("data/function_word_examples.json not found -- run pipeline/build_function_word_examples.py first")

    targets = load_targets()

    overlap = set(CURATED) & set(SKIPPED)
    if overlap:
        sys.exit(f"lemma(s) in both CURATED and SKIPPED: {sorted(overlap)}")
    extra_curated = set(CURATED) - set(targets)
    if extra_curated:
        sys.exit(f"CURATED has entries for lemmas outside the target set: {sorted(extra_curated)}")
    extra_skipped = set(SKIPPED) - set(targets)
    if extra_skipped:
        sys.exit(f"SKIPPED has entries for lemmas outside the target set: {sorted(extra_skipped)}")
    for lemma_id, reason in SKIPPED.items():
        if not reason or not reason.strip():
            sys.exit(f"{lemma_id}: SKIPPED entry has no reason")

    book_cache = {}
    entries_out = []
    total_examples = 0

    for lemma_id, picks in CURATED.items():
        entry = targets[lemma_id]
        if not picks:
            sys.exit(f"{lemma_id}: CURATED entry has zero examples")

        examples_out = []
        for book_code, word_id, start_id, end_id, gloss, gloss_highlight, gloss_note in picks:
            tag = f"{lemma_id}/{word_id}"
            if book_code not in book_cache:
                book_cache[book_code] = load_book(book_code)
            verses, word_to_verse = book_cache[book_code]
            vid = word_to_verse.get(word_id)
            if vid is None:
                sys.exit(f"{lemma_id}: word id {word_id!r} not found in {book_code}.xml")
            verse_words = verses[vid]
            target = next(w for w in verse_words if w["id"] == word_id)
            if not matches_lemma(target["lemma"].split("/"), lemma_id):
                sys.exit(
                    f"{lemma_id}: word id {word_id!r} in {vid} has lemma {target['lemma']!r}, "
                    f"which does not resolve to {lemma_id}"
                )

            phrase_words = extract_phrase(verse_words, start_id, end_id, tag)
            phrase_ids = [w["id"] for w in phrase_words]
            if word_id not in phrase_ids:
                sys.exit(f"{tag}: target word id {word_id!r} falls outside its own phrase [{start_id}, {end_id}]")
            target_index = phrase_ids.index(word_id)

            if gloss_highlight not in gloss:
                sys.exit(f"{tag}: gloss_highlight {gloss_highlight!r} is not a substring of gloss {gloss!r}")
            if gloss_note is not None and not gloss_note.strip():
                sys.exit(f"{tag}: gloss_note is present but empty/whitespace")

            surface_form = strip_cantillation(target["text"].replace("/", ""))
            phrase_words_clean = [strip_cantillation(w["text"].replace("/", "")) for w in phrase_words]
            phrase_hebrew = " ".join(phrase_words_clean)
            phrase_translit = " ".join(transliterate(w) for w in phrase_words_clean)

            examples_out.append({
                "ref": vid,
                "surface_form": surface_form,
                "transliteration": transliterate(surface_form),
                "word_id": word_id,
                "phrase_hebrew": phrase_hebrew,
                "phrase_transliteration": phrase_translit,
                "target_index": target_index,
                "gloss": gloss,
                "gloss_highlight": gloss_highlight,
                "gloss_note": gloss_note,
            })
            total_examples += 1

        senses = [s.strip() for s in entry["gloss"].split(",") if s.strip()]
        entries_out.append({
            "lemma_id": lemma_id,
            "citation_form": entry["citation_form"],
            "transliteration": entry["transliteration"],
            "full_gloss": entry["gloss"],
            "sense_count": len(senses),
            "examples": examples_out,
        })

    pending = sorted(set(targets) - set(CURATED) - set(SKIPPED))

    out = {
        "metadata": {
            "source": "build_vocab_examples.py",
            "target_lemma_count": len(targets),
            "curated_count": len(entries_out),
            "skipped": [{"lemma_id": k, "reason": v} for k, v in sorted(SKIPPED.items())],
            "pending_count": len(pending),
        },
        "entries": entries_out,
    }
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"vocab_examples.json: {len(entries_out)} lemmas curated, {total_examples} examples, "
          f"{len(SKIPPED)} skipped, {len(pending)} pending of {len(targets)} total targets")


if __name__ == "__main__":
    main()

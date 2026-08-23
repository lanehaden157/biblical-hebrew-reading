"""
Learn tab, lesson group 5: sentence-level syntax -> data/lessons_group5.json.

Scope: the last group from the original concept list -- default word
order (verb-subject-object, especially after wayyiqtol), verbless/nominal
clauses, and what vav is actually doing between clauses beyond a bare
"and". This is the layer above single words and phrases: whole short
clauses, read as a sequence.

Reuses build_lessons_group1's decompose()/load_lookups()/index_words_by_id()
directly. Word-order and verbless-clause examples use the same "chain"
shape group 2 (construct chains) and group 4 (adjective agreement)
introduced, each token tagged role="plain" (see group 4's docstring for
why "plain" exists: these tokens don't lean on each other the way a
construct chain does, so there's no construct/absolute distinction to
draw -- here the point is simply the ORDER the words come in). The vav-
lesson is single-word, since it's about what one specific prefix is doing,
not a multi-word relationship.

Every example is a real word/phrase pulled from the actual Jonah text by
OSIS word id, not typed by hand -- same sourcing discipline as every
earlier lesson group.

Run pipeline/build_vocab_deck.py and all four pipeline/curate_jonah*_extra.py
scripts first (needs their output).
"""
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_lessons_group1 import decompose, index_words_by_id, load_lookups

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(HERE, "..", "data", "lessons_group5.json")

SINGLE_EXAMPLES = {
    "vav-connector": [
        ("Jonah", "32A4a", "Grammatically this is still just “and” -- the same prefix group 1's very first lesson covered. But in context (everyone else is panicking on deck while this happens) it reads far more naturally as a contrastive “BUT Jonah had gone down [and lain down and was fast asleep]” -- Hebrew doesn't have a separate word for that shift, the vav just carries it."),
        ("Jonah", "32d5m", "Another vav doing more than “and”: “...so that we don't perish”, expressing a hoped-for result rather than simply adding a fact. Same prefix, a purpose/result sense instead of a contrast."),
    ],
}

CHAIN_EXAMPLES = {
    "word-order": [
        {
            "words": [("Jonah", "32v8V"), ("Jonah", "32T2S"), ("Jonah", "32tkJ"), ("Jonah", "32EXL")],
            "phrase_gloss": "and the LORD appointed a great fish",
            "note": "The default order: verb first (“appointed”), then the subject (“the LORD”), then the object (“a fish”, with its adjective “great” following it, same as every noun-adjective pair). English default order is subject-verb-object; Hebrew narrative, especially after a wayyiqtol like this one, leads with the verb.",
        },
        {
            "words": [("Jonah", "32A4a"), ("Jonah", "325Pr")],
            "phrase_gloss": "but Jonah had gone down",
            "note": "The subject moved in FRONT of the verb here -- a deviation from the default that signals a shift: the story is cutting away from the frantic sailors on deck to what Jonah, specifically, is doing below. Fronting the subject like this is how Hebrew marks that kind of turn without a special word for “meanwhile”.",
        },
    ],
    "verbless-clauses": [
        {
            "words": [("Jonah", "32TXw"), ("Jonah", "32Y4K")],
            "phrase_gloss": "I am a Hebrew",
            "note": "No verb “to be” anywhere -- literally “a Hebrew, I”. Two words, a noun and a pronoun, sitting side by side, is a complete sentence in Hebrew for present-tense “X is Y”.",
        },
        {
            "words": [("Jonah", "32ZMk"), ("Jonah", "32irW"), ("Jonah", "32x72"), ("Jonah", "32FYV")],
            "phrase_gloss": "you are a gracious and compassionate God",
            "note": "Same construction, longer: pronoun, then a noun with two adjectives describing it, still no verb “are” anywhere. Jonah's own complaint to God, describing exactly the mercy he resents.",
        },
    ],
}

LESSONS = [
    {
        "id": "word-order",
        "order": 1,
        "title": "Default word order — verb first",
        "kind": "chain",
        "paragraphs": [
            "Hebrew narrative's default clause order is verb-subject-object -- the opposite habit from English, which leads with the subject. This is especially consistent right after a wayyiqtol (group 3's narrative-chain form), which already starts with the verb by construction.",
            "When the SUBJECT moves in front of the verb instead, that's usually not random -- it signals emphasis, contrast, or a scene change, the way English might switch to “as for Jonah, he...”.",
        ],
    },
    {
        "id": "verbless-clauses",
        "order": 2,
        "title": "Verbless clauses — “X is Y” with no verb at all",
        "kind": "chain",
        "paragraphs": [
            "Hebrew has no present-tense verb “to be”. A statement like “I am a Hebrew” or “you are gracious” is just two words -- a subject and whatever describes it -- placed next to each other, with the “is/am/are” entirely implied.",
            "This is easy to misread as an incomplete sentence if you're expecting a verb; it's actually the normal, complete way to make this kind of statement.",
        ],
    },
    {
        "id": "vav-connector",
        "order": 3,
        "title": "What vav is really doing between clauses",
        "kind": "single",
        "paragraphs": [
            "Group 1's very first lesson covered vav as “and”. That's always grammatically true, but between whole clauses vav's actual function stretches further: depending on context it can read as “but” (contrast), “so/then” (result or sequence), or simply move the narrative forward -- English usually needs a different word for each of these, but Hebrew reuses the same one letter throughout.",
        ],
    },
]


def build_single_example(book_code, wid, note, by_id, functional, word_indexes):
    if book_code not in word_indexes:
        word_indexes[book_code] = index_words_by_id(book_code)
    entry = word_indexes[book_code].get(wid)
    if entry is None:
        sys.exit(f"word id {wid} not found in {book_code}.xml")
    vid, raw_lemma, raw_morph, raw_text = entry
    decomposed = decompose(raw_lemma, raw_morph, raw_text, by_id, functional)
    return {"ref": vid, **decomposed, "highlight": "base", "note": note}


def build_chain_example(spec, by_id, functional, word_indexes):
    tokens = []
    refs = set()
    for book_code, wid in spec["words"]:
        if book_code not in word_indexes:
            word_indexes[book_code] = index_words_by_id(book_code)
        entry = word_indexes[book_code].get(wid)
        if entry is None:
            sys.exit(f"word id {wid} not found in {book_code}.xml")
        vid, raw_lemma, raw_morph, raw_text = entry
        refs.add(vid)
        decomposed = decompose(raw_lemma, raw_morph, raw_text, by_id, functional)
        tokens.append({**decomposed, "role": "plain"})
    if len(refs) != 1:
        sys.exit(f"chain tokens {spec['words']} span more than one verse: {refs}")
    return {
        "ref": refs.pop(),
        "tokens": tokens,
        "phrase_gloss": spec["phrase_gloss"],
        "note": spec["note"],
    }


def main():
    by_id, functional = load_lookups()
    word_indexes = {}

    lessons_out = []
    total_examples = 0
    for lesson in LESSONS:
        examples_out = []
        if lesson["kind"] == "chain":
            for spec in CHAIN_EXAMPLES[lesson["id"]]:
                examples_out.append(build_chain_example(spec, by_id, functional, word_indexes))
                total_examples += 1
        else:
            for book_code, wid, note in SINGLE_EXAMPLES[lesson["id"]]:
                examples_out.append(build_single_example(book_code, wid, note, by_id, functional, word_indexes))
                total_examples += 1
        lessons_out.append({
            "id": lesson["id"],
            "order": lesson["order"],
            "title": lesson["title"],
            "kind": lesson["kind"],
            "paragraphs": lesson["paragraphs"],
            "examples": examples_out,
        })

    out = {
        "metadata": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "group": 5,
            "group_title": "Sentence-level syntax",
            "source": "Jonah 1, 2, and 4 (WLC)",
            "lesson_count": len(lessons_out),
            "example_count": total_examples,
        },
        "lessons": lessons_out,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(lessons_out)} lessons, {total_examples} examples to {OUT_PATH}")


if __name__ == "__main__":
    main()

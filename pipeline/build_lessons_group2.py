"""
Learn tab, lesson group 2: construct chains -> data/lessons_group2.json.

Scope: construct chains (smikhut) -- two or more nouns in a row with no
written "of", where the first (construct) noun's own shape often shifts.
Identified as the single biggest untaught gap after lesson group 1: 72 of
205 nouns in Jonah (35%) are in construct state (see hebrew_corpus.py's
morph dump, tallied in the concept list given to Lane in conversation).

Reuses build_lessons_group1's decompose()/load_lookups()/index_words_by_id()
directly rather than duplicating them -- this is a BUILD script, not a
verify script, so sharing logic between build scripts doesn't weaken
anything the way sharing it with a *verify* script would (verify_
lessons_group2.py below re-implements the whole thing from scratch, same
as every other verify_*.py in this project).

Two example shapes:
  - Single-word examples (lessons 2 and 5): one word, decomposed the same
    way group 1 does it, comparing its actual (construct) shape against
    its own dictionary citation form -- which is exactly what
    lemma_citation_form already captures, no new field needed.
  - Chain examples (lessons 1, 3, 4): two or three separate <w> elements
    read as one phrase. Each token is decomposed independently (a
    construct chain is written as separate words, not one word with "/"
    morphemes, so this is NOT the same operation as splitting one word's
    internal prefix/suffix) and tagged with its own grammatical role
    (construct/absolute), read off its own morph code's state letter --
    never guessed at from word order alone. phrase_gloss is the one
    hand-authored field here: an idiomatic English rendering ("word of
    the LORD") that a word-by-word gloss join can't produce, since
    Hebrew's construct chain has no word standing in for "of" at all.

Every example is a real word/phrase pulled from the actual Jonah text by
OSIS word id, not typed by hand -- same sourcing discipline as group 1.

Text is never NFC/NFD-normalized -- only cantillation is stripped, matching
every other pipeline script.

Run pipeline/build_vocab_deck.py and the curate_jonah*_extra.py scripts
first (needs their output).
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_lessons_group1 import decompose, index_words_by_id, load_lookups

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(HERE, "..", "data", "lessons_group2.json")

# A noun/adjective's own morph part ends in its state letter (a=absolute,
# c=construct) when it has one at all; a proper noun (Np) carries no state
# slot and is always treated as absolute -- it can't itself be "definite"
# any further, so it can only close a chain, never open one. Confirmed
# against every token used below, not assumed from word order.
STATE_RE = re.compile(r"^(?:Nc|Ac)..([ac])$")


def noun_role(content_morph):
    m = STATE_RE.match(content_morph)
    if m:
        return "construct" if m.group(1) == "c" else "absolute"
    return "absolute"  # Np (proper noun) and anything else with no state slot


# (book_code, word_id) for every example, grouped by the lesson that uses
# it. "chain" lessons list one tuple PER TOKEN, grouped into phrases by
# EXAMPLES structure below; "single" lessons list one tuple per example.
CHAIN_EXAMPLES = {
    "basic-chain": [
        [("Jonah", "32Nvk"), ("Jonah", "32TyA")],  # devar YHWH -- the book's opening words
        [("Jonah", "32k5P"), ("Jonah", "32nPh")],  # ben Amittai -- right next to it
    ],
    "definiteness": [
        [("Jonah", "32Cof"), ("Jonah", "32YWU")],  # elohei ha-shamayim -- definite via the article on word 2
        [("Jonah", "32Sxc"), ("Jonah", "32xwN")],  # melekh Nineveh -- definite via a proper noun
    ],
    "three-chain": [
        [("Jonah", "32xkK"), ("Jonah", "32rGa"), ("Jonah", "32fp1")],  # mahalakh shloshet yamim
    ],
}
CHAIN_GLOSSES = {
    ("Jonah", "32Nvk", "32TyA"): "word of the LORD",
    ("Jonah", "32k5P", "32nPh"): "son of Amittai",
    ("Jonah", "32Cof", "32YWU"): "the God of the heavens",
    ("Jonah", "32Sxc", "32xwN"): "the king of Nineveh",
    ("Jonah", "32xkK", "32rGa", "32fp1"): "a three-day journey (lit. “journey of three of days”)",
}
CHAIN_NOTES = {
    ("Jonah", "32Nvk", "32TyA"): "The very first words of the book. No word here means “of” -- the two nouns sitting next to each other IS the “of” relationship.",
    ("Jonah", "32k5P", "32nPh"): "Jonah's patronymic, immediately after -- “son of Amittai”, the same pattern back to back.",
    ("Jonah", "32Cof", "32YWU"): "“God” (construct) itself never takes the article -- it's definite only because “the heavens” (the second word) has one. That's the rule: definiteness of the whole chain always comes from the LAST word.",
    ("Jonah", "32Sxc", "32xwN"): "Same rule, different source of definiteness: proper names are inherently definite, so “king” is “the king” even with no article anywhere in sight.",
    ("Jonah", "32xkK", "32rGa", "32fp1"): "Chains can stack: “journey” is construct because it's followed by “three”, and “three” is ITSELF construct because it's followed by “days”. Only the very last word (“days”) is absolute.",
}

SINGLE_EXAMPLES = {
    "shrinks": [
        ("Jonah", "32Nvk", "Same word as the opening-line example above, looked at differently: the construct form's vowel is visibly shorter than the dictionary form."),
        ("Jonah", "32Ew6", "Another vowel shrink, same pattern: the citation form's long vowel shortens once the word is put in construct state."),
        ("Jonah", "32Sxc", "Not every construct noun changes shape -- short one-syllable nouns like this one sound and look almost identical to their citation form. (The one tiny difference you may see here is just a silent trailing shva, a spelling convention some editions mark and others don't -- not a grammatical change, and not audible either way.)"),
    ],
    "special-endings": [
        ("Jonah", "32GUh", "Feminine nouns ending in ה swap it for a ת the moment anything (a second noun, or here a suffix) attaches -- the same environment that produces a construct chain."),
        ("Jonah", "32Cof", "Same word used in the definiteness lesson, looked at differently: masculine plural ־ִים becomes ־ֵי in construct -- a clean ending swap, same stem throughout."),
        ("Jonah", "32HoD", "A rougher case, worth knowing about honestly: this plural doesn't just swap its ending -- the singular “man” and the plural “men” are built on two different stems entirely. Not every plural is a simple ending swap."),
    ],
}

LESSONS = [
    {
        "id": "basic-chain",
        "order": 1,
        "title": "The basic chain — two nouns, no “of”",
        "kind": "chain",
        "paragraphs": [
            "Hebrew has no word for “of”. To say “word of the LORD”, it just puts the two nouns next to each other: the first noun (called “construct state”) leans on the second (“absolute state”) for its meaning.",
            "This is enormously common -- 72 of the 205 nouns in the book of Jonah (35%) are in construct state. Once you can spot the pattern, you can read straight through it without stopping to look for a missing word.",
        ],
    },
    {
        "id": "shrinks",
        "order": 2,
        "title": "The construct form often shrinks",
        "kind": "single",
        "paragraphs": [
            "Leaning on the next word for meaning often costs the construct noun some of its own stress, and an unstressed long vowel tends to shorten. That's why “word” is דָּבָר (davar) on its own but דְּבַר (devar) in “word of the LORD”.",
            "It's a tendency, not an iron rule -- short, one-syllable nouns often show no visible change at all. The pointing always tells you which case you're looking at; there's no need to guess.",
        ],
    },
    {
        "id": "definiteness",
        "order": 3,
        "title": "Definiteness travels through the chain",
        "kind": "chain",
        "paragraphs": [
            "A construct noun never takes the definite article itself -- there's no such thing as הַדְּבַר. Instead, the WHOLE chain becomes definite (“the X of Y”) exactly when the last word in it is definite: because it has the article, because it's a proper name, or because it carries a pronoun suffix.",
            "This means you have to look at the END of a construct chain to know whether the beginning should be read as “a” or “the” -- the opposite order from English.",
        ],
    },
    {
        "id": "three-chain",
        "order": 4,
        "title": "Chains of three",
        "kind": "chain",
        "paragraphs": [
            "Construct chains aren't limited to two words -- a construct noun can itself be followed by another construct noun, stacking the relationship. Only the very last word in the chain is absolute; everything before it is construct.",
        ],
    },
    {
        "id": "special-endings",
        "order": 5,
        "title": "Special construct endings",
        "kind": "single",
        "paragraphs": [
            "Two endings shift in a recognizable way when a noun goes construct: feminine nouns ending in ה swap it for a ת, and masculine plural nouns ending in ־ִים swap it for ־ֵי.",
            "Both are worth recognizing on sight -- they're common enough, and different enough from the noun's dictionary form, that they can otherwise look like a completely different word.",
        ],
    },
]


def build_chain_example(word_specs, by_id, functional, word_indexes):
    tokens = []
    refs = set()
    for book_code, wid in word_specs:
        if book_code not in word_indexes:
            word_indexes[book_code] = index_words_by_id(book_code)
        entry = word_indexes[book_code].get(wid)
        if entry is None:
            sys.exit(f"word id {wid} not found in {book_code}.xml")
        vid, raw_lemma, raw_morph, raw_text = entry
        refs.add(vid)
        decomposed = decompose(raw_lemma, raw_morph, raw_text, by_id, functional)
        morph_parts = [mp[1:] if i == 0 and mp[:1] in ("H", "A") else mp
                       for i, mp in enumerate(raw_morph.split("/"))]
        content_morph = morph_parts[len(decomposed["prefix_morphemes"])]
        tokens.append({**decomposed, "role": noun_role(content_morph)})
    if len(refs) != 1:
        sys.exit(f"chain tokens {word_specs} span more than one verse: {refs}")
    key = tuple([word_specs[0][0]] + [wid for _, wid in word_specs])
    return {
        "ref": refs.pop(),
        "tokens": tokens,
        "phrase_gloss": CHAIN_GLOSSES[key],
        "note": CHAIN_NOTES[key],
    }


def build_single_example(book_code, wid, note, by_id, functional, word_indexes):
    if book_code not in word_indexes:
        word_indexes[book_code] = index_words_by_id(book_code)
    entry = word_indexes[book_code].get(wid)
    if entry is None:
        sys.exit(f"word id {wid} not found in {book_code}.xml")
    vid, raw_lemma, raw_morph, raw_text = entry
    decomposed = decompose(raw_lemma, raw_morph, raw_text, by_id, functional)
    return {"ref": vid, **decomposed, "highlight": "base", "note": note}


def main():
    by_id, functional = load_lookups()
    word_indexes = {}

    lessons_out = []
    total_examples = 0
    for lesson in LESSONS:
        examples_out = []
        if lesson["kind"] == "chain":
            for word_specs in CHAIN_EXAMPLES[lesson["id"]]:
                examples_out.append(build_chain_example(word_specs, by_id, functional, word_indexes))
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
            "group": 2,
            "group_title": "Construct chains",
            "source": "Jonah 1 and Jonah 3 (WLC)",
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

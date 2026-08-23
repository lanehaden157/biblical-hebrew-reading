"""
Learn tab, lesson group 4: noun-phrase grammar -> data/lessons_group4.json.

Scope: the leftover noun-phrase items from the original concept list that
group 2 (construct chains) didn't cover -- gender/number markers, the
direct object marker, adjective agreement, and demonstratives/numbers.

Reuses build_lessons_group1's decompose()/load_lookups()/index_words_by_id()
for single-word examples, same import pattern group 2 and group 3 already
used. The adjective-agreement lesson needs a two-word phrase (a noun and
the adjective that agrees with it, sitting side by side) -- structurally
the same "separate <w> elements read as one phrase" problem group 2's
construct chains solved, but here neither word "leans on" the other the
way a construct chain does, so there's no construct/absolute role to
assign. build_chain_example() below reuses the same token-decomposition
approach with every token tagged role="plain" instead -- app/views/learn.js
renders a "plain" role with no accent/dim distinction, since the point of
these examples is that the two words match, not that one depends on the
other.

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
OUT_PATH = os.path.join(HERE, "..", "data", "lessons_group4.json")

SINGLE_EXAMPLES = {
    "gender-number": [
        ("Jonah", "32iy2", "Feminine singular nouns very often end in ה -- “the disaster/evil” (the same word group 1's relative-particle lesson and group 3's binyan lesson both already used, from a third angle: its own gender marking)."),
        ("Jonah", "32fsu", "Masculine plural nouns very often end in ים -- “the sailors”."),
        ("Jonah", "32Haa", "Worth knowing as an exception, not a rule-breaker: “lots” (plural of a MASCULINE noun) still takes the ות ending that looks feminine. A handful of common masculine nouns pluralize this way -- the ending alone doesn't always tell you the noun's gender."),
    ],
    "direct-object": [
        ("Jonah", "32eHJ", "אֵת marks the noun right after it (“the vessels”) as a definite direct object. It has no meaning of its own to translate -- drop it entirely in English."),
        ("Jonah", "329Hv", "The same marker, a different verse: “[I fear]... the sea”."),
        ("Jonah", "32J9J", "אֵת can itself carry the vav-conjunction prefix, same as any other word: “and [the dry land]” -- two objects of the same verb, each one separately marked."),
    ],
    "adjective-agreement": [],  # filled in as chain examples below
    "demonstratives-numbers": [
        ("Jonah", "32zQ2", "A demonstrative (“this”) follows the noun it points to, and agrees with it in gender the same way an adjective does -- feminine הַזֹּאת because “disaster” (רָעָה) is a feminine noun."),
        ("Jonah", "32eRa", "A number -- “three”, opening the book's most famous span of time: “three days and three nights” in the fish."),
        ("Jonah", "32xp4", "The other iconic number in the book: “forty” -- the days Nineveh is given before God's decreed judgment."),
    ],
}

CHAIN_EXAMPLES = {
    "adjective-agreement": [
        {
            "words": [("Jonah", "32Rvc"), ("Jonah", "32c6V")],
            "phrase_gloss": "a great city",
            "note": "The adjective follows the noun and matches it in gender and number -- both feminine singular here. Neither word is “leaning on” the other the way a construct chain works; they're simply describing the same thing and agreeing about it.",
        },
        {
            "words": [("Jonah", "32qNN"), ("Jonah", "32EVS")],
            "phrase_gloss": "the great city",
            "note": "Same noun-adjective pair, definite this time -- and the agreement extends to definiteness too: the article appears on BOTH words, not just the noun.",
        },
    ],
}

LESSONS = [
    {
        "id": "gender-number",
        "order": 1,
        "title": "Noun gender and number, on sight",
        "kind": "single",
        "paragraphs": [
            "Every Hebrew noun is grammatically masculine or feminine, and singular, plural, or (rarely) dual. Two endings are common enough to recognize immediately: feminine singular often ends in ה, and masculine plural often ends in ים.",
            "These are strong tendencies, not guarantees -- there are feminine nouns with no ה, and a handful of masculine nouns that still pluralize with the “feminine-looking” ות ending. When they conflict, the actual agreement pattern (see the adjective-agreement lesson) is the more reliable signal.",
        ],
    },
    {
        "id": "direct-object",
        "order": 2,
        "title": "The direct object marker אֵת",
        "kind": "single",
        "paragraphs": [
            "אֵת (or its shortened form אֶת) marks the noun right after it as a definite direct object -- the thing an action is being done TO. It carries no meaning of its own and is never translated; its only job is to flag “this is the object, and it's definite”.",
            "It only appears before a DEFINITE object (one with the article, a proper name, a suffix, or otherwise already specific) -- an indefinite object (“a fish”, not “the fish”) never gets one.",
        ],
    },
    {
        "id": "adjective-agreement",
        "order": 3,
        "title": "Adjectives agree with their noun",
        "kind": "chain",
        "paragraphs": [
            "A Hebrew adjective normally follows the noun it describes (the reverse of English) and matches it in gender, number, and definiteness. If the noun has the article, the adjective gets its own copy of the article too -- both words carry it, not just the noun.",
        ],
    },
    {
        "id": "demonstratives-numbers",
        "order": 4,
        "title": "Demonstratives and numbers",
        "kind": "single",
        "paragraphs": [
            "A demonstrative (“this”/“that”) works like an adjective: it follows its noun and agrees with it in gender. Numbers, similarly, sit beside the noun they count and often show their own gender agreement (not shown in the examples here, but worth knowing to expect).",
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
            "group": 4,
            "group_title": "Noun-phrase grammar",
            "source": "Jonah 1, 2, and 3 (WLC)",
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

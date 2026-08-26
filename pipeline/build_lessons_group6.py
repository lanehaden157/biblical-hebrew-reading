"""
Learn tab group 6: pairs of function words that are easy to mix up, but for
different reasons than build_vocab_deck.py's `confusable_with` one-liner
covers on their own cards -- this group has room for the actual explanation
and a couple of real, contrasting examples side by side.

Trigger: Lane's own request, after a brainstorm on how to teach the 19
tier-B particles' contrast pairs without resorting to flashcards for a
distinction that's really a short explanation, not a recall drill. Picked
the two pairs with real grammatical content (not just a register warning,
which confusable_with already handles): 'el vs le- (direction vs
dative/benefit) and yesh vs 'ayin (existence vs its negation). 'im vs `im
is included too even though its confusable_with note already exists --
that note only says "these look alike", it doesn't have room to also show
the merged `im/'et card's alternate spelling in context, which this lesson
does.

Reuses build_lessons_group1's decompose()/load_lookups()/index_words_by_id()
exactly like groups 2-5 -- every example is single-word, decomposed the
same mechanical way (prefix vs base vs suffix resolved from the corpus's
own morph codes, never hand-split). Word ids were picked from among ones
already independently corpus-verified while curating
data/function_word_examples.json's tier-A/B examples this same session, so
most of this script is re-selection, not fresh corpus reading.

Run pipeline/build_vocab_deck.py first (needs data/vocab_deck_600.json).
"""
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_lessons_group1 import decompose, index_words_by_id, load_lookups

HERE = os.path.dirname(os.path.abspath(__file__))
DECK_PATH = os.path.join(HERE, "..", "data", "vocab_deck_600.json")
OUT_PATH = os.path.join(HERE, "..", "data", "lessons_group6.json")

LESSONS = [
    {
        "id": "el-vs-le",
        "order": 1,
        "title": "'el vs le- — “to” that isn't “to”",
        "paragraphs": [
            "Both 'el and le- can be glossed “to,” which makes them look "
            "interchangeable -- they aren't. 'el marks physical direction: motion "
            "toward a place, or a person spoken to. le- marks the dative/"
            "benefactive relationship -- who something is done for or given to -- "
            "and doubles as the marker on an infinitive (“to do” as a verb "
            "form, not a direction).",
            "The structural tell is visible on the page, not just in meaning: "
            "'el is always its own separate word, standing before whatever it "
            "points at. le- is never separate -- it fuses directly onto the "
            "front of the next word, the same way be- and ke- do.",
        ],
    },
    {
        "id": "im-vs-im",
        "order": 2,
        "title": "'im vs `im — one mark, unrelated words",
        "paragraphs": [
            "These are close to the same three letters in this app's ASCII "
            "scheme -- 'im and `im -- and mean completely unrelated things: "
            "'im introduces a conditional (“if”), `im means “with.” "
            "The only difference is which mark opens the word: alef (') for "
            "“if”, ayin (`) for “with” -- colored differently "
            "throughout this app so they're easier to tell apart at a glance.",
            "`im also has a written twin: 'et (אֵת) is a completely "
            "different-looking word that's read exactly the same way, “with.” "
            "The Vocab tab treats `im and 'et as one card, since drilling recall "
            "for two spellings of one idea doesn't test anything real -- but "
            "both spellings show up in real text, so the example below is 'et, "
            "not `im.",
        ],
    },
    {
        "id": "yesh-vs-ayin",
        "order": 3,
        "title": "yesh vs 'ayin — existence and its opposite",
        "paragraphs": [
            "yesh and 'ayin are opposites: yesh asserts that something exists "
            "or is present (“there is”), 'ayin asserts its absence "
            "(“there is not”). Neither is a verb -- Hebrew doesn't need "
            "“to be” for simple existence; these two particles do the "
            "whole job by themselves.",
            "Both combine with a pronoun suffix, or with le- + a pronoun, as the "
            "standard way to say “I have” / “I don't have”: yesh li "
            "(“there is to me”) is “I have”; 'eyn li (“there is "
            "not to me”) is “I don't have.”",
        ],
    },
]

# (book_code, word_id, highlight, note) per lesson, in the order shown.
EXAMPLES = {
    "el-vs-le": [
        ("Jonah", "32eYX", "base", "'el as its own word: physical direction -- go TO Nineveh."),
        ("Ruth", "08gYe", "base", "'el again: “your sister-in-law has returned TO her people” -- still direction, not benefit."),
        ("Josh", "06cLk", "prefix", "le- fused onto “say”: le'mor, the standard formula introducing a quotation (“...saying”). A third job 'el never does -- marking an infinitive, not a direction or a person."),
    ],
    "im-vs-im": [
        ("Judg", "07bu5", "base", "'im opening a conditional: “if you go with me, I will go.”"),
        ("Ruth", "08KPU", "base", "`im with a pronoun suffix: “the LORD be with you (all).” Same three consonants as 'im above, opened by the other mark."),
        ("Ruth", "08Cof", "base", "'et, not `im -- but the same idea: “with you we will return to your people.” This is the alternate spelling folded into the `im card."),
    ],
    "yesh-vs-ayin": [
        ("Judg", "07Lka", "base", "yesh with a 2nd-person suffix: yeshkha, literally “there-is-to-you” -- “if you will save Israel.”"),
        ("2Kgs", "1289f", "base", "yesh on its own: “the word of the LORD IS with him” -- a plain assertion that something is the case."),
        ("Judg", "076Lg", "base", "'ayin (here “ein”) asserting absence: “there was no king in Israel.”"),
        ("1Kgs", "114d7", "base", "'ayin again: “there is no adversary and no misfortune.”"),
    ],
}


def main():
    if not os.path.isfile(DECK_PATH):
        sys.exit("data/vocab_deck_600.json not found -- run pipeline/build_vocab_deck.py first")

    missing = set(EXAMPLES) - {l["id"] for l in LESSONS}
    extra = {l["id"] for l in LESSONS} - set(EXAMPLES)
    if missing or extra:
        sys.exit(f"LESSONS/EXAMPLES id mismatch -- missing={missing} extra={extra}")

    by_id, functional = load_lookups()
    word_indexes = {}

    lessons_out = []
    total_examples = 0
    for lesson in LESSONS:
        examples_out = []
        for book_code, wid, highlight, note in EXAMPLES[lesson["id"]]:
            if book_code not in word_indexes:
                word_indexes[book_code] = index_words_by_id(book_code)
            entry = word_indexes[book_code].get(wid)
            if entry is None:
                sys.exit(f"word id {wid} not found in {book_code}.xml")
            vid, raw_lemma, raw_morph, raw_text = entry
            decomposed = decompose(raw_lemma, raw_morph, raw_text, by_id, functional)
            examples_out.append({
                "ref": vid,
                **decomposed,
                "highlight": highlight,
                "note": note,
            })
            total_examples += 1
        lessons_out.append({
            "id": lesson["id"],
            "order": lesson["order"],
            "title": lesson["title"],
            "paragraphs": lesson["paragraphs"],
            "examples": examples_out,
        })

    out = {
        "metadata": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "group": 6,
            "group_title": "Confusable words",
            "source": "Jonah, Ruth, Joshua, Judges, 2 Kings, 1 Kings (WLC) -- word ids "
                       "re-selected from already-verified data/function_word_examples.json entries",
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

"""
Learn tab, lesson group 3: the verb system -> data/lessons_group3.json.

Scope: binyan (stem) semantics, the qatal/yiqtol aspect distinction,
vav-consecutive (wayyiqtol/weqatal), participles, infinitive construct,
and the imperative/cohortative/jussive command forms -- the conceptual
layer behind what the Parse tab already drills by pattern (Qal-strong
PGN recognition) and the Read tab already shows word-by-word (every verb
form in Jonah, un-explained). See the concept list given to Lane in
conversation: this is "the biggest conceptual payoff" group, and the one
item (wayyiqtol) that's the single largest chunk of any verb form in the
book -- 84 of 202 verb-morphs in Jonah (42%) are wayyiqtol.

Every example is single-word, reusing build_lessons_group1's decompose()/
load_lookups()/index_words_by_id() directly (a BUILD-script import, not a
verify-script one -- see that file's docstring for why that distinction
matters and this one doesn't weaken anything).

The lesson-1 binyan pair is not an invented illustration: נָפַל (Qal,
"fall") and its Hiphil ("cast, cause to fall") are independently confirmed
to both occur in Jonah by cross-tabulating every verb's (lemma, stem) pair
across the whole book -- and it turns out both occurrences sit in the same
verse, Jonah 1:7 ("...so they cast [Hiphil] lots, and the lot fell [Qal]
on Jonah"), which is a better illustration than anything that would have
been picked by assumption. Checked this way specifically because a
same-root stem *pair* that never actually co-occurs in the target text
would be a real example (both forms are genuine, attested Hebrew) but a
misleading illustration of *this* text's own vocabulary.

Text is never NFC/NFD-normalized -- only cantillation is stripped, matching
every other pipeline script.

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
OUT_PATH = os.path.join(HERE, "..", "data", "lessons_group3.json")

# (book_code, word_id, note) per example, grouped by lesson id.
EXAMPLES = {
    "binyan": [
        ("Jonah", "32jQ8", "Hiphil of נפל (“fall”): the causative doesn't mean “fall”, it means “make fall” -- here, “cast [lots]”. Same verse as the next example, same root, different stem, different meaning."),
        ("Jonah", "32fJN", "Qal of the very same root, two clauses later: the lot itself “fell” -- the plain, non-causative action Hiphil above was built from."),
        ("Jonah", "32hh7", "Niphal: the passive/reflexive counterpart to Qal. Qal שָׁבַר would be “[someone] breaks [something]”; Niphal here is “[it is] broken” -- the ship itself, with no one named as doing the breaking."),
        ("Jonah", "327am", "Piel: often intensifies or gives a plain root a new, more specific sense. Qal חָשַׁב is bare “think/reckon”; Piel here reads idiomatically as “threatened to [break apart]” -- the ship “considered itself broken”, i.e. seemed about to be."),
        ("Jonah", "32nLp", "Hitpael: often reflexive -- the action turned back on the subject. Here, “take notice/rouse himself to act” -- the captain is urging the sleeping Jonah to do something to/for himself."),
    ],
    "aspect": [
        ("Jonah", "32fLi", "Qatal: a completed action, viewed as a whole -- “I fear” here is really closer to “I hold [as an established fact] that I fear”, not “I am in the process of becoming afraid”."),
        ("Jonah", "32BYa", "Yiqtol: an incomplete action -- ongoing, future, or not-yet-realized. The sailors are hoping this WON'T happen: “we will [not] perish”."),
    ],
    "vav-consecutive": [
        ("Jonah", "32TZE", "The first link in a narrative chain: “and he arose”."),
        ("Jonah", "32jbg", "“And he went down” -- the next clause, same verse, same pattern: vav + a form that looks like yiqtol but is read as simple past."),
        ("Jonah", "32v6U", "“And he found” -- a third link. This is how Hebrew narrative moves: not a new tense each time, but the same wayyiqtol pattern repeated, clause after clause."),
        ("Jonah", "32GmF", "Weqatal -- wayyiqtol's mirror image. Same vav-plus-verb idea, but built on qatal instead of yiqtol, and used here for a hoped-for future in the king's speech: “[Who knows if] God will turn...”"),
        ("Jonah", "32mnL", "A second weqatal immediately after the first, same verse, same construction: “...and relent.” Two hoped-for future actions, chained the same way wayyiqtol chains narrative past actions."),
    ],
    "participle": [
        ("Jonah", "3292v", "A participle used to describe what someone is doing/was doing -- not “he fled” (a completed act) but “[that he was] fleeing”, an ongoing state the sailors and captain discover him in."),
        ("Jonah", "32FMU", "Paired with the next example in the same verse: Hebrew doubles a participle to express an intensifying, ongoing process -- “growing [stormier]”, not just “stormy”."),
        ("Jonah", "32SaV", "The second half of that doubled pair -- “...and storming”. Together, “the sea was growing more and more tempestuous”, a construction with no single-word English equivalent."),
    ],
    "infinitive-construct": [
        ("Jonah", "32LN3", "The single most common infinitive construct in the whole Bible: לֵאמֹר, “saying”, glued onto a preposition and used to introduce direct speech -- it shows up constantly and never needs to be translated as anything fancier than “...and said:”."),
        ("Jonah", "32JM7", "An infinitive construct riding on the preposition לְ (“to/for”) to express purpose -- “to flee”, functioning as a verbal noun the same way English “to flee” or “fleeing” can head a purpose clause."),
        ("Jonah", "323yJ", "Same construction, Hiphil this time: “to bring [it] back” -- the sailors' attempted purpose, rowing hard to return the ship to land."),
    ],
    "commands": [
        ("Jonah", "32Qzf", "Imperative: a direct command, 2nd person only -- “Arise!”. The book's opening instruction from God to Jonah."),
        ("Jonah", "32aPd", "A second imperative immediately after the first, same verse: “Go!”. Hebrew commands often stack this way, one short verb after another."),
        ("Jonah", "32GLz", "Cohortative: a 1st-person “let's...”/“I will...”, self-directed the way an imperative directs someone else -- “let us know [whose fault this storm is]”."),
        ("Jonah", "32MVq", "Jussive: a 3rd-person indirect command, “let him/them...” -- part of the king of Nineveh's fasting decree: “let them not drink [water]”."),
    ],
}

LESSONS = [
    {
        "id": "binyan",
        "order": 1,
        "title": "One root, many meanings — the binyan system",
        "paragraphs": [
            "A Hebrew verb root gets its precise meaning from which of several patterns (“binyan”, plural “binyanim”) it's conjugated in -- the same three consonants can mean something different, but related, in each one.",
            "By how often each one actually occurs (measured across the whole Bible, not from a textbook): Qal 69% (the plain, basic action), Hiphil 13% (causative -- “make X happen”), Piel 9% (often intensive, or a specific derived sense), Niphal 6% (usually passive or reflexive), Hitpael 1% (usually reflexive/reciprocal -- action turned back on the subject). Pual and Hophal (the passive counterparts of Piel and Hiphil) are rare enough to recognize on sight but not worth drilling.",
            "The clearest illustration in Jonah is a single root used twice in one verse: Hiphil for “causing something to fall” (casting lots), then two clauses later, Qal for the lot simply falling on its own.",
        ],
    },
    {
        "id": "aspect",
        "order": 2,
        "title": "Qatal vs. yiqtol — two aspects, not two tenses",
        "paragraphs": [
            "Qatal and yiqtol are usually glossed “perfect” and “imperfect”, which invites reading them as English past/future tense -- close, but not quite right. They're really about ASPECT: is the action viewed as a completed whole (qatal), or as incomplete/ongoing/not-yet-realized (yiqtol)? Context does most of the work of pinning down an actual time.",
            "This is exactly the distinction the Parse tab already has you recognizing by the form itself; this lesson is the “why” behind the label.",
        ],
    },
    {
        "id": "vav-consecutive",
        "order": 3,
        "title": "Vav-consecutive — the backbone of the story",
        "paragraphs": [
            "Prefix a vav onto yiqtol (with a small vowel/doubling shift) and its meaning flips: instead of incomplete/future, it now reads as simple narrative past -- “and he did X”. This is wayyiqtol, and it's how Hebrew tells a story: 84 of the 202 verb forms in Jonah (42%) are wayyiqtol, chained clause after clause.",
            "Weqatal is the mirror image: prefix a vav onto QATAL instead, and it takes on the sense yiqtol would have carried alone -- often a hoped-for or expected future, as in the king of Nineveh's “who knows if God will turn and relent”.",
        ],
    },
    {
        "id": "participle",
        "order": 4,
        "title": "Participles — action in progress, or a description",
        "paragraphs": [
            "A participle describes an ongoing state or action, not a completed or future one -- closer to English “-ing” (“fleeing”) than to a full “he fled”/“he will flee”. It can also stand in as a noun on its own (“the one who...”), though Jonah's examples here are all descriptive.",
        ],
    },
    {
        "id": "infinitive-construct",
        "order": 5,
        "title": "Infinitive construct — a verb acting like a noun",
        "paragraphs": [
            "The infinitive construct is a verbal noun -- it can be the object of a preposition the way an ordinary noun can, most often riding on לְ (“to/for”) to express purpose: “to flee”, “to bring back”. It carries no person, gender, or number of its own.",
        ],
    },
    {
        "id": "commands",
        "order": 6,
        "title": "Imperative, cohortative, and jussive — commands and wishes",
        "paragraphs": [
            "Three related but distinct forms for anything short of a flat statement: the imperative is a direct 2nd-person command (“Go!”); the cohortative is a 1st-person self-directed “let's.../I will...”; the jussive is an indirect 3rd-person “let him/them...”. All three showed up in Jonah's locked conjugation scope as recognition-only -- not drilled in Parse -- but worth being able to name on sight.",
        ],
    },
]


def main():
    by_id, functional = load_lookups()
    word_indexes = {}

    lessons_out = []
    total_examples = 0
    for lesson in LESSONS:
        examples_out = []
        for book_code, wid, note in EXAMPLES[lesson["id"]]:
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
                "highlight": "base",
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
            "group": 3,
            "group_title": "The verb system",
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

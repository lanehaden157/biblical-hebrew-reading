"""
Learn tab, lesson group 1: prefixes and suffixes -> data/lessons_group1.json.

Scope: the six function-morpheme concepts identified as highest-coverage for
reading Jonah (see hebrew_corpus.FUNCTION_CODES for the closed 8-code set;
group 1 covers all of them except the definite article's interaction with
gutturals, which is folded into the article lesson as a note, not a
separate lesson): vav-conjunction, definite article, the four inseparable
prepositions (treated as one lesson since they share one rule -- attach
directly, no space), pronominal suffixes, the relative particle, and the
interrogative-he prefix.

Every example is a REAL word pulled from the actual Jonah text by its OSIS
word id, not typed by hand -- CLAUDE.md's hard rule is now phrased as "be
extremely careful," not "never," but sourcing from the corpus is strictly
safer than careful typing, so that's what this script does throughout. Word
ids were selected by reading pipeline/hebrew_corpus.py's dump of Jonah 1
and Jonah 4:2 (the interrogative-he lesson's only occurrence in the whole
book) and picking the clearest illustration of each rule -- picking *which*
word is a curatorial judgment call same as glosses/jonah1_extra.json;
extracting its actual text is not.

Decomposition is deliberately generic (works for a noun, preposition, or
verb base, not just Qal verbs like build_parse_qal.py): walk the lemma's
"/"-separated parts from the front, treating each single-lowercase-letter
part as a function-word prefix (resolved against vocab_deck_600.json's
curated F-<letter> entries -- see hebrew_corpus.FUNCTION_CODES for why this
set is closed and exhaustive) until the first Strong's-numbered part, which
is the content word. Whatever morph parts trail the content word with no
matching lemma part is a suffix (pronominal object/possessive, or the rarer
paragogic nun/he). Whole-word transliteration only, never per-morpheme in
isolation -- see build_parse_qal.py's docstring for why that was the parse
tab's own transliteration bug, not just its truncation bug.

Text is never NFC/NFD-normalized -- only cantillation (U+0591-U+05AF) is
stripped, matching every other pipeline script.

Run pipeline/build_vocab_deck.py and all four pipeline/curate_jonah*_extra.py
scripts first (needs their output) -- load_lookups() below is shared by
build_lessons_group2.py, whose own examples draw on chapter 3's curated
extras, so it pulls in the full curated set rather than just chapters 1/4.
"""
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hebrew_corpus import OSIS_NS, WLC_DIR
from transliterate import transliterate

HERE = os.path.dirname(os.path.abspath(__file__))
DECK_PATH = os.path.join(HERE, "..", "data", "vocab_deck_600.json")
EXTRA_PATHS = [
    os.path.join(HERE, "..", "glosses", f"jonah{n}_extra.json") for n in (1, 2, 3, 4)
]
OUT_PATH = os.path.join(HERE, "..", "data", "lessons_group1.json")

CANTILLATION_RE = re.compile("[֑-֯]")
SUFFIX_PGN_RE = re.compile(r"^Sp([123])([mfc])([spd])$")
GENDER_LABEL = {"m": "m", "f": "f", "c": "c"}
NUMBER_LABEL = {"s": "s", "p": "p", "d": "d"}

# (book_code, word_id) for every example, grouped by the lesson that uses
# it. Selected from the Jonah 1 / Jonah 4 word dumps -- see docstring.
EXAMPLES = {
    "vav-conjunction": [
        ("Jonah", "32A4a", "prefix", "Plain “ve-” before an ordinary consonant -- the default case."),
        ("Jonah", "32PB6", "prefix", "Shifts to “u-” because the next consonant (qof) itself carries a vocal shva -- Hebrew avoids two shvas in a row."),
        ("Jonah", "32V27", "prefix", "Shifts to “u-” again, this time because the next consonant (mem) is one of the “BuMP” labials (bet/mem/vav/pe)."),
    ],
    "definite-article": [
        ("Jonah", "32qNN", "prefix", "The plain case: “ha-” + noun."),
        ("Jonah", "32EVS", "prefix", "The article also attaches to adjectives, agreeing with the noun it describes -- “the great [city]”, from the same verse."),
        ("Jonah", "32Y3z", "prefix", "Notice the doubled consonant right after “ha-” (a dagesh forte) -- that doubling is how the article marks the noun as definite."),
        ("Jonah", "323TS", "prefix", "Bonus: when a preposition (here “be-”, “in”) lands directly on an article-marked noun, they often fuse into one prefix instead of stacking -- still “in the sea”, not two separate pieces."),
    ],
    "prepositions": [
        ("Jonah", "32KZG", "prefix", "“le-” (to/for) attached to a noun that itself carries a suffix -- “to my face”, idiomatically “before me”."),
        ("Jonah", "32W26", "prefix", "Two prepositions can stack: “mi-” (from) + “li-” (to/for) read together as “from before”."),
        ("Jonah", "32JM7", "prefix", "“li-” + an infinitive construct verb form -- this is how Hebrew expresses purpose, “to flee”."),
        ("Jonah", "32FV9", "prefix", "“be-” (in) fused directly onto an article-marked noun, same fusion as the definite-article lesson's bonus example."),
    ],
    "pronominal-suffixes": [
        ("Jonah", "3229t", "suffix", "A 3rd-plural possessive suffix on a noun -- “their evil”."),
        ("Jonah", "3237c", "suffix", "A 3rd-feminine-singular suffix on a preposition, not a noun -- prepositions take these too: “against it”."),
        ("Jonah", "32jQb", "suffix", "3rd-feminine-singular again, this time on a noun -- “its fare”."),
        ("Jonah", "325gQ", "suffix", "A 3rd-masculine-singular suffix on a plural noun -- “his god(s)” (the noun for God/gods is grammatically plural in Hebrew even when singular in meaning)."),
    ],
    "relative": [
        ("Jonah", "32BU7", "prefix", "The relative ‘sheh-’ stacked between two prepositions in one word -- “on whose account”, literally “in-that-to-whom”. Jonah is known among Hebraists for preferring this short form over the more formal standalone word below."),
        ("Jonah", "32Ptj", "base", "The full standalone form, ‘asher’ -- “who/which/that”, introducing a description: “...whom I fear, who made the sea...”."),
    ],
    "interrogative-he": [
        ("Jonah", "32CFo", "prefix", "The entire book of Jonah: this is the ONLY time this prefix appears. It turns a plain statement into a yes/no question -- here, opening Jonah's angry complaint to God in chapter 4: “Is it not...?”"),
    ],
}

LESSONS = [
    {
        "id": "vav-conjunction",
        "order": 1,
        "title": "Vav — “and”",
        "paragraphs": [
            "The letter vav attached to the front of a word is the single most common prefix in the Bible -- about 1 word in 5 in Jonah alone. Its default reading is “ve-”.",
            "It changes to “u-” in two situations, both there to avoid an awkward run of shva sounds: before the labial consonants bet, mem, vav, or pe (nicknamed the “BuMP” rule), and before any consonant that itself starts with a vocal shva.",
            "This is purely mechanical -- the pointed text always shows you which one it is, so there's nothing to guess. It's also the exact rule this app's own transliteration script got wrong until recently: a word-initial “u-” was rendering as a bare “w”.",
        ],
    },
    {
        "id": "definite-article",
        "order": 2,
        "title": "The definite article — “the”",
        "paragraphs": [
            "A heh attached to the front of a noun or adjective marks it as definite -- “the city”, not “a city”. About 1 word in 10 in Jonah carries it.",
            "It usually causes the very next consonant to double (written as a dot inside that letter, a dagesh forte) -- that doubling is part of how the article is pronounced, not a separate thing to learn.",
            "Adjectives describing a definite noun get their own copy of the article too, and it can fuse directly into a preceding preposition (be-/ke-/le-) rather than the two stacking separately.",
        ],
    },
    {
        "id": "prepositions",
        "order": 3,
        "title": "Prepositions that attach: le-, be-, ke-, min-",
        "paragraphs": [
            "Four of the most common prepositions never stand alone as separate words -- they glue directly onto the front of whatever they govern: ל́ (le-, “to/for”), ב́ (be-, “in/on/with”), כ́ (ke-, “like/as”), and מִן/מִ- (min-/mi-, “from”). Together they account for roughly 1 word in 7 in Jonah.",
            "They can stack (“from before” = min- + le-), ride on top of the definite article (fusing rather than stacking), or attach to a verb's infinitive construct to express purpose -- “to flee”, “in order to do X”.",
        ],
    },
    {
        "id": "pronominal-suffixes",
        "order": 4,
        "title": "Pronoun suffixes — “his/her/their...”",
        "paragraphs": [
            "A short tail glued onto the END of a noun, preposition, or verb stands in for a possessive or object pronoun -- no separate word needed. About 1 word in 7 in Jonah carries one.",
            "On a noun it usually means possession (“X of his/hers/theirs”); on a preposition or a verb it usually means the object (“...him”, “...it”, “...them”). The Parse tab already shows you the grammatical shape (person/gender/number) of these when they land on a verb.",
        ],
    },
    {
        "id": "relative",
        "order": 5,
        "title": "The relative — “that/which/who”",
        "paragraphs": [
            "Hebrew has two ways to say “that/which/who” introducing a description: the full standalone word אֲשֶׁר (‘asher), and a short prefix שֶׁ- (sheh-) glued onto the front of the next word.",
            "Jonah is one of the few books that uses the short sheh- form at all -- most of the Bible sticks to ‘asher exclusively. It's one of the small clues scholars point to when discussing the book's date and style.",
        ],
    },
    {
        "id": "interrogative-he",
        "order": 6,
        "title": "The interrogative heh — turning a statement into a question",
        "paragraphs": [
            "A heh attached to the very front of a sentence turns a plain statement into a yes/no question -- there's no separate word for “do/does/is” the way English needs one.",
            "It's rare: across the entire book of Jonah, it happens exactly once. But it's not a throwaway example -- it opens one of the book's most famous lines.",
        ],
    },
]


def strip_cantillation(s):
    return CANTILLATION_RE.sub("", s)


def load_lookups():
    with open(DECK_PATH, encoding="utf-8") as f:
        deck = json.load(f)
    by_id = {e["lemma_id"]: e for e in deck["entries"]}
    for path in EXTRA_PATHS:
        if not os.path.isfile(path):
            sys.exit(f"{path} not found -- run its curate_*.py script first")
        with open(path, encoding="utf-8") as f:
            extra = json.load(f)
        for e in extra["entries"]:
            by_id.setdefault(e["lemma_id"], e)
    functional = {k: v for k, v in by_id.items() if k.startswith("F-")}
    return by_id, functional


def index_words_by_id(book_code):
    path = os.path.join(WLC_DIR, f"{book_code}.xml")
    root = ET.parse(path).getroot()
    index = {}
    for verse in root.iter(f"{OSIS_NS}verse"):
        vid = verse.get("osisID")
        for w in verse.iter(f"{OSIS_NS}w"):
            wid = w.get("id")
            if wid:
                index[wid] = (vid, w.get("lemma") or "", w.get("morph") or "", w.text or "")
    return index


def decompose(raw_lemma, raw_morph, raw_text, by_id, functional):
    lemma_parts = raw_lemma.split("/")
    morph_parts = raw_morph.split("/")
    word_parts = raw_text.split("/")

    prefix_entries = []
    prefix_count = 0
    for lp_raw in lemma_parts:
        lp = lp_raw.strip()
        if re.match(r"^[a-z]$", lp):
            fn = functional.get("F-" + lp)
            if fn is None:
                raise ValueError(f"unresolved function code {lp!r} in lemma {raw_lemma!r}")
            prefix_entries.append(fn)
            prefix_count += 1
        else:
            break

    content_lp_raw = lemma_parts[prefix_count].strip() if prefix_count < len(lemma_parts) else ""
    m = re.match(r"^(\d+)", content_lp_raw)
    if not m:
        raise ValueError(f"no content lemma found in {raw_lemma!r} after {prefix_count} prefix(es)")
    lemma_id = "H" + m.group(1)
    lemma_entry = by_id.get(lemma_id)
    if lemma_entry is None:
        raise ValueError(f"lemma {lemma_id} not found in vocab_deck_600.json or the curated extras")

    prefix_form = strip_cantillation("".join(word_parts[:prefix_count]))
    base_form = strip_cantillation(word_parts[prefix_count] if prefix_count < len(word_parts) else "")
    suffix_form = strip_cantillation("".join(word_parts[prefix_count + 1:]))
    full_word = strip_cantillation("".join(word_parts))
    if prefix_form + base_form + suffix_form != full_word:
        raise ValueError(f"prefix+base+suffix != full word for {raw_text!r}")

    suffix_kind = suffix_pgn = None
    rest = morph_parts[prefix_count + 1:]
    if rest:
        if len(rest) == 1 and SUFFIX_PGN_RE.match(rest[0]):
            person, g, n = SUFFIX_PGN_RE.match(rest[0]).groups()
            suffix_kind = "pronominal"
            suffix_pgn = {"person": person, "gender": GENDER_LABEL[g], "number": NUMBER_LABEL[n]}
        elif len(rest) == 1 and rest[0] == "Sn":
            suffix_kind = "paragogic_nun"
        elif len(rest) == 1 and rest[0] == "Sh":
            suffix_kind = "directional_he"
        else:
            raise ValueError(f"unhandled trailing morpheme(s) {rest!r} for {raw_text!r}")

    return {
        "surface_form": full_word,
        "transliteration": transliterate(full_word),
        "prefix_form": prefix_form,
        "prefix_morphemes": [
            {"citation_form": e["citation_form"], "transliteration": e["transliteration"], "gloss": e["gloss"]}
            for e in prefix_entries
        ],
        "base_form": base_form,
        "suffix_form": suffix_form,
        "suffix_kind": suffix_kind,
        "suffix_pgn": suffix_pgn,
        "lemma_citation_form": lemma_entry["citation_form"],
        "lemma_transliteration": transliterate(lemma_entry["citation_form"]),
        "gloss": lemma_entry["gloss"],
    }


def main():
    if not os.path.isfile(DECK_PATH):
        sys.exit("data/vocab_deck_600.json not found -- run pipeline/build_vocab_deck.py first")

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
            "group": 1,
            "group_title": "Prefixes and suffixes",
            "source": "Jonah 1 and Jonah 4:2 (WLC)",
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

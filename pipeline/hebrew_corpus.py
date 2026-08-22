"""
Shared constants for reading the OSHB (morphhb) corpus and the Strong's
Hebrew lexicon. Used by both rank_lemmas.py and verify_top600.py -- kept
here (rather than duplicated) only for values that are just facts about the
data formats, not for parsing logic. The two scripts deliberately parse the
XML independently of each other so a bug in one is unlikely to be masked by
the other.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
WLC_DIR = os.path.join(HERE, "corpus", "wlc")
LEXICON_PATH = os.path.join(HERE, "corpus", "lexicon", "HebrewStrong.xml")

OSIS_NS = "{http://www.bibletechnologies.net/2003/OSIS/namespace}"
LEX_NS = "{http://openscriptures.github.com/morphhb/namespace}"

# Canonical Protestant OT order. The first element of each pair is the OSIS
# book code, which is also the morphhb filename stem and the osisID prefix
# (e.g. "Gen.1.1"); the second is the English name used for display.
BOOK_ORDER = [
    ("Gen", "Genesis"), ("Exod", "Exodus"), ("Lev", "Leviticus"),
    ("Num", "Numbers"), ("Deut", "Deuteronomy"),
    ("Josh", "Joshua"), ("Judg", "Judges"), ("Ruth", "Ruth"),
    ("1Sam", "1 Samuel"), ("2Sam", "2 Samuel"),
    ("1Kgs", "1 Kings"), ("2Kgs", "2 Kings"),
    ("1Chr", "1 Chronicles"), ("2Chr", "2 Chronicles"),
    ("Ezra", "Ezra"), ("Neh", "Nehemiah"), ("Esth", "Esther"),
    ("Job", "Job"), ("Ps", "Psalms"), ("Prov", "Proverbs"),
    ("Eccl", "Ecclesiastes"), ("Song", "Song of Songs"),
    ("Isa", "Isaiah"), ("Jer", "Jeremiah"), ("Lam", "Lamentations"),
    ("Ezek", "Ezekiel"), ("Dan", "Daniel"),
    ("Hos", "Hosea"), ("Joel", "Joel"), ("Amos", "Amos"), ("Obad", "Obadiah"),
    ("Jonah", "Jonah"), ("Mic", "Micah"), ("Nah", "Nahum"), ("Hab", "Habakkuk"),
    ("Zeph", "Zephaniah"), ("Hag", "Haggai"), ("Zech", "Zechariah"), ("Mal", "Malachi"),
]

# The OSHB lemma attribute splits a word into morphemes with "/". Each
# morpheme is either a Strong's number (optionally suffixed with a
# disambiguating letter for homographs, e.g. "1121 a", or a trailing "+" for
# an extended sense not in the base Strong's entry -- neither is present in
# the lexicon's own numbering, so both are stripped when merging into a
# lemma_id) or one of a small fixed set of single-letter function-morpheme
# codes for prefixed grammar words that have no Strong's number at all.
# Confirmed exhaustively against morph="H..." codes across the whole corpus:
# every code below co-occurs with exactly the morph POS shown in the comment.
FUNCTION_CODES = {
    "c": "Conjunction",          # HC   -- vav "and"
    "d": "Definite article",     # HTd  -- he "the"
    "i": "Interrogative particle",  # HTi  -- he "?"
    "l": "Preposition",          # HR   -- lamed "to/for"
    "b": "Preposition",          # HR   -- bet "in/on/with"
    "k": "Preposition",          # HR   -- kaf "like/as"
    "m": "Preposition",          # HR   -- min "from"
    "s": "Relative particle",    # HTr  -- she- "that/which"
}

POS_LETTER_TO_LABEL = {
    "A": "Adjective", "C": "Conjunction", "D": "Adverb", "N": "Noun",
    "P": "Pronoun", "R": "Preposition", "S": "Suffix", "T": "Particle", "V": "Verb",
}

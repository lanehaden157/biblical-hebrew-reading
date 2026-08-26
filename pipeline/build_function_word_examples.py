"""
Learn tab / Vocab tab addition: real Hebrew Bible usage examples for the
closed set of function words (prepositions, conjunctions, particles, and
the inseparable prefix morphemes) -> data/function_word_examples.json.

Lane's own framing for why this exists: these words are hard to remember
because a bare gloss ("in, on, with") gives no usage context -- unlike a
concrete noun or verb, a preposition's meaning only becomes clear from a
real sentence. Baseline rule: at least 3 real, corpus-sourced occurrences
per word, scaling up when the curated gloss lists more distinct senses than
that (examples_needed = max(3, number of comma-separated senses in the
gloss)).

Tiered on top of that baseline (decided with Lane after he found the
original 3-per-word set too repetitive and Genesis-heavy): the 11 particles
whose glosses are actually scattered enough to need a `core_schema` field
(see build_vocab_deck.py) get 10 examples instead of 3, enforced via
TIER_TARGET below. A second tier (contrast-pair particles, 5 each) is
planned but not yet built -- those lemmas still fall back to the baseline
rule until TIER_TARGET is extended for them. `vocab.js` rotates through
whatever count a lemma has, 3 at a time.

Scope: every entry in data/vocab_deck_600.json that is one of the 8
inseparable F-<letter> prefix morphemes, or has pos in {Preposition,
Conjunction, Particle, Definite article, Interrogative particle, Relative
particle} -- 51 lemmas total, a small closed set (Hebrew's function-word
inventory doesn't grow the way vocabulary does).

Word selection (EXAMPLES below) is a curatorial judgment call, same as
every glosses/*_extra.json file in this project -- picking which verse
best illustrates a given sense of a preposition requires reading the verse
and knowing what it means, not something derivable from morphology alone.
What is NOT hand-typed, per hard rule 1: every Hebrew string. Only the
(book_code, target word id, phrase start/end word id, English gloss,
English highlight span, optional note) are hand-authored; the Hebrew (both
the target word and the phrase it sits in) is pulled from the corpus by
word id and verified in verify_function_word_examples.py to actually match
the claimed lemma and lie within the claimed phrase -- a wrong word id
fails loudly rather than silently mislabeling a sense.

Each example keeps only the Hebrew PHRASE that corresponds to `gloss`
(a start word id through an end word id, both inclusive, in corpus word
order), not the full verse -- Lane's own call, after the first version of
this feature shipped whole verses: "shorten the verse examples ... just
gimme the hebrew which corresponds to the english translation".

The card highlights the specific Hebrew word being taught (computed as
`target_index`, the word's position within the phrase -- mechanical, not
hand-typed) AND the closest corresponding English word(s) in `gloss`
(`gloss_highlight`, a literal substring of `gloss`, checked at build time
to actually appear in it). Lane's own framing for this half: "highlight
the closest and maybe add a tiny short explainer if its not immediately
clear" -- so `gloss_highlight` always points at *something*, even when the
correspondence is loose (a preposition fused into an English idiom, or
untranslated entirely, like the H853/H854 direct-object marker), and
`gloss_note` is populated only for those non-obvious cases, left `None`
for a clean one-to-one match. A `[...]` bracket in a gloss marks English
sense carried by context outside the extracted phrase (e.g. an elided
verb), not missing Hebrew.

Run pipeline/build_vocab_deck.py first (needs data/vocab_deck_600.json).
"""
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hebrew_corpus import BOOK_ORDER, FUNCTION_CODES, OSIS_NS, WLC_DIR
from transliterate import transliterate

HERE = os.path.dirname(os.path.abspath(__file__))
DECK_PATH = os.path.join(HERE, "..", "data", "vocab_deck_600.json")
OUT_PATH = os.path.join(HERE, "..", "data", "function_word_examples.json")

CANTILLATION_RE = re.compile("[֑-֯]")

TARGET_POS = {
    "Preposition", "Conjunction", "Particle",
    "Definite article", "Interrogative particle", "Relative particle",
}

# Tier 1: particles with a curated core_schema (see build_vocab_deck.py) --
# scattered enough across senses that 3 examples wasn't enough to see the
# pattern. Tier 2: real multi-sense particles that don't get a schema
# (mostly because they're better taught as contrast pairs -- 'el vs le-,
# 'et vs `im -- than as one unifying image), bumped from 3 to 5. Any lemma
# not listed here falls back to the baseline max(3, sense count) rule.
TIER_TARGET = {
    "F-l": 10, "F-b": 10, "F-m": 10, "H4480": 10, "H5921": 10, "H3588": 10,
    "F-k": 10, "H5704": 10, "H310": 10, "H8478": 10, "H5048": 10,
    "H413": 5, "H834": 5, "H518": 5, "H5973": 5, "H854": 5, "H2009": 5,
    "H2005": 5, "H369": 5, "H3426": 5, "H3651": 5, "H1571": 5, "H637": 5,
    "H389": 5, "H7535": 5, "H1115": 5, "H1157": 5, "H3644": 5, "F-s": 5,
    "H4616": 5,
}

# Shared note text for the small cluster of examples where the same
# explanation applies every time (repeated per-example rather than
# factored out, since the data is what ships -- not a code path).
_ET_NOTE = "'et itself has no English translation -- it just flags the direct object."
_FI_NOTE = "the question marker itself isn't a separate word -- it's what makes this a question in English."
_YESH_NOTE_1 = "yesh just asserts presence here -- no literal \"there is\" in the English."
_YESH_NOTE_HAVE = "yesh + \"to me/us\" is how Hebrew says \"I/we have\" -- no literal \"there is\" in the English."
_LEMOR_NOTE = "le'mor (\"to say\") is the standard formula introducing a quotation -- rendered \"saying\" in English."

# (book_code, target_word_id, phrase_start_id, phrase_end_id, gloss,
#  gloss_highlight, gloss_note) per lemma. target_word_id is the specific
# occurrence of the lemma the card highlights (must fall within
# [phrase_start_id, phrase_end_id] in corpus word order). gloss_highlight
# is the closest English word/phrase to that occurrence -- a literal
# substring of gloss, checked at build time. gloss_note is None for a
# clean match, or a short explainer when the correspondence is loose.
EXAMPLES = {
    "F-c": [
        ("Gen", "01LN3", "01LN3", "01eYX", "and the earth was without form and void", "and", None),
        ("Gen", "01thY", "01thY", "01W26", "and God said, 'Let there be light'", "and", None),
        ("Gen", "017am", "017am", "01fsu", "and God said, 'Let there be a vault...'", "and", None),
    ],
    "F-d": [
        ("Gen", "01TSc", "01Nvk", "01nPh", "God created the heavens and the earth", "the", None),
        ("Gen", "01GzE", "01USR", "01g2y", "God saw the light, that it was good", "the", None),
        ("Gen", "01d5m", "01NPq", "01dv1", "let the water under the sky be gathered to one place", "the", None),
    ],
    "F-l": [
        ("Gen", "01Wkf", "01nAB", "01wrL", "God called the light 'day'", "the light",
         "le- marks the object of \"called\" here; Hebrew doesn't need a separate word for it."),
        ("Gen", "01pAw", "01Ygn", "01pAw", "I have given [every plant] to you", "to", None),
        ("Gen", "0192v", "01zpy", "01Bx7", "lights in the sky, to separate day from night", "to", None),
        ("Exod", "02fLi", "02Cof", "02fLi", "the king of Egypt said to the midwives", "to the midwives", None),
        ("Josh", "06cLk", "06AxB", "06cLk", "Joshua commanded the officers of the people, saying", "saying",
         _LEMOR_NOTE),
        ("Ruth", "08rAQ", "08Cof", "08rAQ", "with you we will return to your people", "to your people", None),
        ("1Sam", "09qty", "09wM5", "095gQ", "he gave [portions] to Peninnah his wife", "to Peninnah", None),
        ("2Kgs", "12oGi", "126fj", "12Ao4", "bring me a new bowl", "me",
         "le- is benefactive here (\"for me\"), read naturally in English as \"bring me...\""),
        ("Jonah", "32LN3", "32xeN", "32LN3", "the word of the LORD came to Jonah son of Amittai, saying", "saying",
         _LEMOR_NOTE),
        ("Judg", "07SWL", "072Kt", "073Lj", "the name of Debir was formerly Kiriath-sepher", "formerly",
         "lifnim (literally \"to the face/front\") is an idiom for \"formerly, in the past.\""),
    ],
    "F-b": [
        ("Gen", "01xeN", "01xeN", "01nPh", "In the beginning God created the heavens and the earth", "In", None),
        ("Gen", "01gtq", "01oiy", "01gtq", "let us make man in our image", "in", None),
        ("Judg", "071TR", "07Ab6", "07MQc", "he struck a thousand men with it", "with", None),
        ("Exod", "02g2y", "02GzE", "02g2y", "Joseph was in Egypt", "in Egypt", None),
        ("Num", "046VM", "04WTe", "04sKn", "he numbered them in the wilderness of Sinai", "in the wilderness", None),
        ("Josh", "06QvZ", "06Hki", "06S38", "she hid them among the stalks of flax", "among",
         "bet reads as \"among\" here rather than \"in\" -- she buried them under a pile of flax stalks."),
        ("Ruth", "08dJe", "08cn3", "08dJe", "but Ruth clung to her", "to her",
         "davqah bah (\"clung in/at her\") uses bet where English says \"to.\""),
        ("Jonah", "32QH2", "32jyT", "32xxn", "you cast me into the heart of the seas", "into", None),
        ("Jonah", "32NtK", "32NtK", "32zqr", "as my life was fainting within me", "as",
         "be- + an infinitive (\"in the fainting of\") is how Hebrew says \"when/as\" -- there's no separate word for \"as\" here."),
        ("1Kgs", "11nPh", "11k5P", "11nPh", "they covered him with garments", "with",
         "bet is instrumental here -- covering \"by means of\" garments, i.e. \"with.\""),
    ],
    "H853": [
        ("Gen", "01vuQ", "01Nvk", "01nPh", "God created the heavens and the earth", "the heavens", _ET_NOTE),
        ("Gen", "01Zuo", "01jjy", "01mR4", "God created man in his own image", "man", _ET_NOTE),
        ("Gen", "01w6u", "015QX", "013RL", "God saw everything that he had made", "everything", _ET_NOTE),
    ],
    "F-m": [
        ("Gen", "01L4k", "01CyH", "01Wxq", "the water under the vault, and the water above", "under",
         "mi- is fused into \"under\" here -- mitakhat literally means \"from-under.\""),
        ("Gen", "01ZMk", "01TZa", "01ZMk", "the LORD planted a garden in Eden, in the east", "the east",
         "mi- is fused into \"the east\" here -- miqedem literally means \"from the east.\""),
        ("Gen", "01Dwm", "01Ao4", "01Dwm", "he took one of his ribs", "of", None),
        ("Exod", "02Qnr", "02uXX", "026kU", "a man from the house of Levi went", "from", None),
        ("Num", "04ymB", "04ymB", "04X2q", "from the people of Israel", "from", None),
        ("Josh", "06TuL", "06eK3", "06emQ", "we are free from this oath of yours", "from",
         "literally \"free from your oath\" -- mi- marks release from an obligation."),
        ("Judg", "07nWb", "07ZtS", "07GXk", "the border of the Amorites ran from the ascent of Akrabbim", "from", None),
        ("Ruth", "08CyH", "08UE6", "085Pr", "the woman was left without her two children and her husband", "without",
         "mi- marks separation/deprivation here -- \"bereft of,\" not literal motion."),
        ("1Sam", "097mS", "09B6c", "097mS", "put your wine away from you", "from you", None),
        ("Jonah", "32Qnr", "32uXX", "32Qnr", "the sea ceased from its raging", "from", None),
    ],
    "H5921": [
        ("Gen", "01qNN", "01C5U", "01PB6", "darkness was over the face of the deep", "over", None),
        ("Gen", "01G6E", "01hS1", "014vX", "every living creature that moves on the earth", "on", None),
        ("Gen", "01khc", "01RFe", "01u6F", "the LORD God commanded the man, saying", "the man",
         "`al means \"concerning\" here; English just says \"commanded the man.\""),
        ("Exod", "02BsK", "02NFp", "02fsu", "a new king arose over Egypt", "over", None),
        ("Deut", "05oYz", "05HcR", "05dD2", "you shall have no other gods before me", "before me",
         "`al panai (literally \"upon my face\") is the idiom for \"before/besides me.\""),
        ("Ruth", "08awE", "08tKf", "08yNT", "who is in charge over the reapers", "over", None),
        ("1Sam", "09Cof", "09aMT", "09YWU", "she prayed to the LORD", "to",
         "hitpallel `al (literally \"pray upon\") is idiomatic for \"pray to.\""),
        ("2Sam", "10bvP", "10uXX", "10wjj", "David sang this lament over Saul", "over", None),
        ("1Kgs", "11tkv", "11kz6", "11GVz", "Solomon sat on the throne of David his father", "on", None),
        ("2Kgs", "126PV", "12kCD", "12w7p", "he returned and stood by the bank of the Jordan", "by", None),
    ],
    "H413": [
        ("Gen", "01tRR", "01NPq", "01dv1", "let the water be gathered to one place", "to", None),
        ("Gen", "01dvY", "01fZA", "01YkN", "the LORD called to the man", "to", None),
        ("Gen", "01ACV", "01ACV", "01FCG", "your desire will be for your husband", "for",
         "'el usually means \"to\"; here it reads naturally as \"for.\""),
        ("Jonah", "32eYX", "32aPd", "32EVS", "go to Nineveh, the great city", "to", None),
        ("Ruth", "08gYe", "08pqY", "08gYe", "your sister-in-law has returned to her people", "to", None),
    ],
    "H834": [
        ("Gen", "01B2d", "01B2d", "01SV6", "whose seed is in itself", "whose",
         "asher is rendered \"whose\" here for a natural possessive reading."),
        ("Gen", "01HWo", "01FMa", "01uUA", "every plant that is on the face of the earth", "that", None),
        ("Gen", "01Doj", "012GY", "01F5r", "whatever the man called each creature", "whatever",
         "asher combines with \"all\" (kol) to read as \"whatever.\""),
        ("Josh", "06dBc", "06XR4", "06wrL", "every place that the sole of your foot treads on", "that", None),
        ("Jonah", "32ypu", "32ypu", "32V8b", "that which I vowed, I will pay", "that which", None),
    ],
    "H3808": [
        ("Gen", "01j8W", "01j8W", "019Yh", "you shall not eat from it", "not", None),
        ("Gen", "01SGf", "01SGf", "01vL9", "it is not good for the man to be alone", "not", None),
        ("Gen", "01fE2", "01fE2", "01rio", "and they were not ashamed", "not", None),
    ],
    "H3588": [
        ("Gen", "01qCU", "01USR", "01g2y", "God saw the light, that it was good", "that", None),
        ("Gen", "01WJY", "01WJY", "01zXi", "because the LORD God had not sent rain", "because", None),
        ("Gen", "01T97", "01yMS", "01nY7", "she saw that the tree was good", "that", None),
        ("Gen", "01tA5", "01tA5", "01fZr", "when you work the ground, it will no longer yield", "when", None),
        ("Deut", "05EAA", "05EAA", "05LuD", "for the LORD your God is a consuming fire", "for", None),
        ("Josh", "063r3", "063r3", "06pvY", "for tomorrow the LORD will do wonders among you", "for", None),
        ("Judg", "07Hki", "07xp4", "07S38", "when Israel grew strong, [he put the Canaanites to forced labor]", "when",
         "vayehi ki (\"and it happened that\") is the standard formula introducing a time clause -- \"when.\""),
        ("2Sam", "101SP", "101SP", "10fd5", "[Ish-bosheth] heard that Abner was dead", "that", None),
        ("1Kgs", "11pXr", "11pXr", "11nm5", "because Solomon had asked this thing", "because", None),
        ("Jonah", "32x9c", "32x9c", "32KZG", "for their wickedness has come up before me", "for", None),
    ],
    "F-k": [
        ("Gen", "01HSQ", "01oiy", "01HSQ", "let us make man in our image, as our likeness", "as", None),
        ("Gen", "01Wyn", "01G2d", "01Wyn", "I will make a helper corresponding to him", "corresponding",
         "ke- fuses with neged (\"opposite\") into the idiom \"corresponding to.\""),
        ("Gen", "01RUp", "01a9X", "014YU", "you will be like God, knowing good and evil", "like", None),
        ("Deut", "052Kt", "05J9J", "05SWL", "you are today as many as the stars of heaven", "as",
         "lit. \"as the stars of heaven for multitude\" -- ke- introduces the point of comparison."),
        ("Ruth", "08Mjg", "08Ugz", "08mdR", "it came to about an ephah of barley", "about",
         "ke- marks an approximate quantity here, not a literal comparison."),
        ("1Sam", "09KNo", "09xwN", "09KNo", "there is none holy like the LORD", "like", None),
        ("Josh", "06KKJ", "06KKJ", "063V4", "according to your words, so it is", "according to", None),
        ("Judg", "07FQm", "07etm", "07DYw", "you shall strike Midian as [one strikes] one man", "as", None),
        ("2Kgs", "12Cmf", "12uXm", "12K6T", "when Ahab died, [the king of Moab rebelled]", "when",
         "ke- + an infinitive (\"as the dying of\") is how Hebrew says \"when/as soon as.\""),
        ("Num", "04vwH", "04vwH", "04w7p", "according to all that the LORD commanded Moses, so [Israel's sons] did",
         "according to", None),
    ],
    "H5704": [
        ("Gen", "01JyU", "01JyU", "01RxS", "until you return to the ground", "until", None),
        ("Gen", "01euh", "01mWC", "01wX7", "they came as far as Haran, and settled there", "as far as", None),
        ("Gen", "01shT", "015eb", "01Gxb", "I will give it to you and your offspring forever", "forever",
         "`ad pairs with `olam (\"eternity\") here to mean \"forever.\""),
        ("Jonah", "32JUf", "323RL", "32ce9", "from the greatest of them to the least of them", "to",
         "a merism (\"from...to\") meaning \"everyone, from top to bottom\" -- migdolam...ve`ad qetannam."),
        ("Jonah", "322dm", "326zt", "32uYh", "the waters closed over me, even to my very life", "to",
         "`ad nefesh (\"to the soul/throat\") is idiomatic for a threat reaching one's whole life."),
        ("Josh", "06JA2", "06HHZ", "06gFo", "a desolate heap, to this day", "to this day",
         "`ad hayyom hazzeh (\"to this day\") is a standard formula meaning \"still true as of the writing.\""),
        ("1Sam", "09ndZ", "09ndZ", "093yJ", "how long will you go on being drunk?", "how long",
         "`ad matai (literally \"until when\") is the idiom for \"how long.\""),
        ("2Sam", "102Bq", "10Ney", "10aC7", "she had no child to the day of her death", "to", None),
        ("Ruth", "08XgW", "08Dqb", "086PV", "she gleaned in the field until evening", "until", None),
        ("Deut", "05JnD", "05ta1", "05ErQ", "you have come as far as the hill country of the Amorites",
         "as far as", None),
    ],
    "H4480": [
        ("Gen", "01CFo", "01Csj", "015Ja", "the man, dust from the ground", "from", None),
        ("Gen", "019Yh", "01j8W", "019Yh", "you shall not eat from it", "from", None),
        ("Gen", "01x5W", "01q4j", "01s3h", "the rib that he had taken from the man", "from", None),
        ("Num", "04VkC", "04nt3", "04nou", "when they set out from the camp", "from", None),
        ("Deut", "05nqT", "05c8D", "05nqT", "these nations are more numerous than I", "than I",
         "min marks comparison here (\"more ... than\"), the same word that elsewhere means \"from.\""),
        ("Josh", "06Wmn", "06GMz", "06X2q", "take from the people twelve men", "from", None),
        ("Ruth", "08KTJ", "08PHG", "08KTJ", "there is a redeemer nearer than I", "than I", None),
        ("2Sam", "10pCR", "10r2t", "10pCR", "my steadfast love will not depart from him", "from him", None),
        ("1Kgs", "11xcf", "11Gxb", "11R9X", "when the priests came out from the holy place", "from", None),
        ("Jonah", "32Ta6", "323Sx", "32Ta6", "please take my life from me", "from me", None),
    ],
    "H518": [
        ("Gen", "01DK9", "01bmL", "01JoL", "if you do well, will you not be accepted?", "if", None),
        ("Gen", "01cHs", "01cHs", "01CsK", "if now I have found favor in your eyes", "if", None),
        ("Gen", "01Vio", "01Vio", "01v99", "if I find fifty righteous within the city", "if", None),
        ("Judg", "07bu5", "07bu5", "07EPr", "if you go with me, I will go", "if", None),
        ("1Kgs", "11orc", "11orc", "11HUJ", "if you walk in my ways, to keep my statutes and my commandments", "if", None),
    ],
    "H5973": [
        ("Gen", "01eVQ", "01Wsp", "01eVQ", "Lot was with him", "with", None),
        ("Gen", "01dDG", "016io", "01iLp", "will you sweep away the righteous with the wicked?", "with", None),
        ("Gen", "01otC", "01111", "01ru7", "show steadfast love with my master", "with", None),
        ("Ruth", "08KPU", "08FMa", "08KPU", "the LORD be with you", "with you", None),
        ("Deut", "05Ucu", "05x8B", "05Ucu", "face to face the LORD spoke with you", "with you", None),
    ],
    "H854": [
        ("Gen", "014Zw", "01sUy", "014Zw", "I will establish my covenant with you", "with", None),
        ("Gen", "012iX", "01nbb", "012iX", "Noah, his sons, his wife, and his sons' wives -- with him", "with", None),
        ("Gen", "014wk", "01qmG", "014wk", "I am establishing my covenant with you", "with", None),
        ("Ruth", "08Cof", "08Cof", "08rAQ", "with you we will return to your people", "with you", None),
        ("Judg", "07iqd", "0742S", "07iqd", "the men who were with him", "with him", None),
    ],
    "H2009": [
        ("Gen", "01Ygn", "01Ygn", "01pAw", "behold, I have given [it] to you", "behold", None),
        ("Gen", "01JUf", "01JUf", "01dPK", "and behold, it was very good", "behold", None),
        ("Gen", "01CXn", "01T4t", "01eW4", "behold, I am bringing the flood", "behold", None),
        ("Josh", "06vSy", "06vSy", "06Uv6", "behold, the ark of the covenant... is crossing before you", "behold", None),
        ("Ruth", "084vX", "084vX", "082gM", "and behold, Boaz came from Bethlehem", "behold", None),
    ],
    "H369": [
        ("Gen", "01Pht", "01oYp", "01FCP", "and there was no man to work the ground", "no", None),
        ("Gen", "01Mos", "01Mos", "01Fu4", "and he was not, for God took him", "not", None),
        ("Gen", "017pd", "01P8j", "01ikF", "Sarai was barren; she had no child", "no", None),
        ("Judg", "076Lg", "076Lg", "07ioA", "there was no king in Israel", "no", None),
        ("1Kgs", "114d7", "114d7", "112fr", "there is no adversary and no misfortune", "no", None),
    ],
    "H3651": [
        ("Gen", "01n5f", "019qY", "01n5f", "and it was so", "so", None),
        ("Gen", "01d1k", "01pww", "01fiZ", "therefore a man leaves his father and mother", "therefore",
         "ken combines with `al (\"upon\") into the idiom \"therefore.\""),
        ("Gen", "01VnV", "01zG9", "01J24", "just as God commanded him, so he did", "so", None),
        ("Josh", "06U9v", "06KKJ", "063V4", "according to your words, so it is", "so it is", None),
        ("Judg", "07JpD", "07JpD", "07U6B", "therefore I will no longer save you", "therefore",
         "lakhen (\"to thus\") is ken fused with le- into \"therefore.\""),
    ],
    "H1571": [
        ("Gen", "01Bxn", "01Pw8", "01uXm", "she gave some to her husband also", "also", None),
        ("Gen", "01xRR", "01dVq", "01xRR", "Abel also brought [an offering]", "also", None),
        ("Gen", "01cMr", "01TYN", "01GDg", "to Seth also a son was born", "also", None),
        ("Ruth", "08H6L", "08eHJ", "08Xm1", "both of them, Mahlon and Chilion, also died", "also", None),
        ("1Kgs", "11fiV", "11fiV", "11sQy", "Solomon has even taken his seat on the royal throne", "even", None),
    ],
    "H4100": [
        ("Gen", "01gjk", "01gjk", "01kXw", "what is this you have done?", "what", None),
        ("Gen", "01iQS", "01iQS", "01pu1", "what have you done?", "what", None),
        ("Gen", "01TkZ", "01TkZ", "01VP3", "by what shall I know [that I will possess it]?", "what", None),
    ],
    "H408": [
        ("Gen", "013dA", "013dA", "01HAZ", "do not be afraid, Abram", "do not", None),
        ("Gen", "01jTj", "01jTj", "01u9c", "do not look behind you", "do not", None),
        ("Gen", "01XWM", "01XWM", "01Ag3", "do not stretch out your hand against the boy", "do not", None),
    ],
    "H310": [
        ("Gen", "01bcM", "01uCk", "01rFe", "the days of Adam, after he fathered Seth", "after", None),
        ("Gen", "013iU", "01grp", "011WV", "Noah lived after the flood 350 years", "after", None),
        ("Gen", "01Ps4", "01Ps4", "01Lva", "and afterward the clans of the Canaanites dispersed", "afterward", None),
        ("Exod", "02Yxf", "02x3o", "02Yxf", "the Egyptians pursued and went in after them [into the sea]", "after", None),
        ("Deut", "05BBr", "05usd", "05KL5", "you shall not go after other gods", "after", None),
        ("Judg", "07Mnv", "07L4k", "07tKT", "they pursued after him and caught him", "after", None),
        ("Ruth", "086By", "08bCC", "08CZB", "return after your sister-in-law", "after", None),
        ("1Sam", "095Qt", "09XBR", "09HJA", "Saul turned back from pursuing the Philistines", "from pursuing",
         "me'acharei (\"from after\") -- 'akhar combines with min to mean \"stopped following.\""),
        ("1Kgs", "11LJh", "11BYa", "11tRR", "they followed after Adonijah in support", "after", None),
        ("2Kgs", "12rbR", "12AHL", "12rbR", "she arose and followed after him", "after", None),
    ],
    "F-i": [
        ("Gen", "01GYp", "01GYp", "01cdc", "have you eaten from the tree...?", "have", _FI_NOTE),
        ("Gen", "01caE", "01caE", "01j2a", "Am I my brother's keeper?", "Am", _FI_NOTE),
        ("Gen", "01Kzw", "01Kzw", "01t9h", "Is anything too hard for the LORD?", "Is", _FI_NOTE),
    ],
    "H8478": [
        ("Gen", "01L4k", "01A4a", "01Mnv", "the water under the vault", "under", None),
        ("Gen", "01vD2", "01Hwq", "01ygZ", "another offspring in place of Abel", "in place of", None),
        ("Gen", "01oQN", "01XKf", "016xQ", "he offered it up... instead of his son", "instead of", None),
        ("Exod", "02eQ5", "02Jy1", "02jEY", "eye for eye", "for",
         "tachat here means \"in exchange for,\" the lex talionis formula -- the same word that elsewhere means \"under.\""),
        ("Num", "04Gcz", "04o2H", "04X3d", "I took the Levites instead of every firstborn among the Israelites",
         "instead of", None),
        ("Deut", "05941", "05QFm", "05941", "the LORD destroyed them, and they dwelt in their place", "in their place", None),
        ("Judg", "07L6s", "07cUw", "07jmB", "Moab was subdued that day under the hand of Israel", "under", None),
        ("1Sam", "09Y67", "09ptT", "09urx", "they buried [their bones] under the tamarisk tree", "under", None),
        ("1Kgs", "11nru", "11nMZ", "11nru", "Rehoboam his son reigned in his place", "in his place", None),
        ("2Sam", "10o26", "10Utw", "10o26", "Hanun his son reigned in his place", "in his place", None),
    ],
    "H4310": [
        ("Gen", "01Cdg", "01Cdg", "01SMW", "who told you that you were naked?", "who", None),
        ("Gen", "01J84", "01J84", "01oVs", "to whom do you belong?", "whom", None),
        ("Gen", "01mZS", "01mZS", "01b4B", "who are these to you?", "who", None),
    ],
    "H996": [
        ("Gen", "01CsU", "01jQb", "01dBc", "God separated the light from the darkness", "from",
         "beyn X and beyn Y (\"between X and between Y\") is idiomatic here for \"separated X from Y.\""),
        ("Gen", "019QD", "01GpM", "01Wuu", "the sign of the covenant between me and you", "between", None),
        ("Gen", "01hPa", "012md", "01mj8", "there was strife between the herdsmen", "between", None),
    ],
    "H4994": [
        ("Gen", "01S7G", "01N1A", "01K1A", "please say you are my sister", "please", None),
        ("Gen", "01aKv", "01a34", "012tz", "lift up your eyes, now, and look", "now", None),
        ("Gen", "01Xgr", "01Wm8", "01am8", "let a little water now be brought", "now", None),
    ],
    "H176": [
        ("Gen", "01es7", "019mo", "01k9R", "can we speak to you bad or good?", "or", None),
        ("Gen", "01Kgz", "01pr1", "01Z7W", "have you a father, or a brother?", "or", None),
        ("Exod", "02xFg", "02TFT", "02TPh", "if his master gives him a wife, and she bears him sons or daughters", "or", None),
    ],
    "H2005": [
        ("Gen", "01Zzk", "01Zzk", "01eNB", "behold, the man has become like one of us", "behold", None),
        ("Gen", "01pVY", "01pVY", "01s4E", "behold, you have given me no offspring", "behold", None),
        ("Gen", "01KGK", "01KGK", "01Env", "behold, you have driven me this day", "behold", None),
        ("1Sam", "09TD8", "09YJk", "09TD8", "the LORD called to Samuel, and he said, 'Here I am'", "Here I am",
         "hinneni (\"here I am\") is hen with a 1st-person suffix -- the same word behind \"behold.\""),
        ("2Sam", "10nm5", "10nm5", "10D85", "behold, we are your bone and your flesh", "behold",
         "hinnenu (\"behold us\") is hen with a 1st-person-plural suffix."),
    ],
    "H4616": [
        ("Gen", "01uDX", "01uDX", "01p8s", "so that it may go well with me", "so that", None),
        ("Gen", "01DF8", "01DF8", "01FcZ", "in order that the LORD may bring [what he promised]", "in order that", None),
        ("Exod", "02NvP", "02NvP", "02YPx", "so that my name may be proclaimed in all the earth", "so that", None),
        ("Num", "04kEE", "04kEE", "04TWv", "so that the whole congregation of Israel's sons may obey him", "so that", None),
        ("1Kgs", "113M5", "113M5", "11EMQ", "so that they may fear you, all the days [they live]", "so that", None),
    ],
    "H389": [
        ("Gen", "01veg", "01RNc", "01BQz", "only Noah was left, and those with him", "only", None),
        ("Gen", "01CV5", "01CV5", "01mn4", "only, flesh with its life... you shall not eat", "only", None),
        ("Gen", "01k4p", "01k4p", "01sCD", "surely, this is your wife", "surely", None),
        ("1Sam", "09QZB", "09QZB", "092Jq", "surely the LORD's anointed is right before him", "surely", None),
        ("Jonah", "32PBQ", "32PBQ", "3274R", "yet I will again look toward your holy temple", "yet", None),
    ],
    "H5048": [
        ("Gen", "01Wyn", "01Zmd", "01Wyn", "a helper corresponding to/opposite him", "opposite", None),
        ("Gen", "01aiP", "01V7Q", "01QFp", "she sat down at a distance, opposite him", "opposite", None),
        ("Gen", "01gdC", "01gdC", "01Aca", "identify what is yours before our kinsmen", "before", None),
        ("Exod", "028BY", "02qzH", "02g6B", "Israel camped there in front of the mountain", "in front of", None),
        ("Judg", "07cJJ", "07XGJ", "07cJJ", "my father risked his life for you", "risked",
         "literally \"cast his life away from before him\" -- minneged marks the idiom for risking one's life."),
        ("1Sam", "09Br9", "09QZB", "092Jq", "surely the LORD's anointed is right in front of him", "in front of", None),
        ("1Kgs", "11Rps", "11Rps", "11Wct", "[Solomon stood before the altar] in front of the whole assembly of Israel",
         "in front of", None),
        ("2Kgs", "12YBx", "12MDS", "12kMZ", "fifty men stood at a distance, opposite them", "opposite", None),
        ("Jonah", "32qK3", "32LAe", "321Cv", "I am cast out from before your eyes", "from before", None),
        ("Deut", "05u75", "05e69", "05u75", "your life will hang in doubt before you", "before you", None),
    ],
    "F-s": [
        ("Ps", "19mzp", "19ZHH", "19JHQ", "like a city that is bound firmly together", "that", None),
        ("Ps", "19nWJ", "19Hwj", "19pjA", "the LORD, who was on our side", "who", None),
        ("Ps", "19imQ", "19N3f", "192Y4", "blessed be the LORD, who did not give us as prey", "who", None),
        ("Jonah", "32BU7", "32GLz", "32Wxx", "let us know on whose account this evil has come upon us",
         "on whose account",
         "beshellemi (\"in that of whom\") -- she- fused with le- + mi (\"who\") -- is idiomatic for \"on whose account.\""),
        ("Jonah", "32L6G", "32L6G", "32pwZ", "which sprang up in a night and perished in a night", "which", None),
    ],
    "H3644": [
        ("Exod", "02scM", "0299z", "02cPY", "they went down into the depths like a stone", "like", None),
        ("Exod", "02vvb", "02qe3", "02JP4", "who is like you among the gods, O LORD?", "like", None),
        ("Lev", "03PYm", "032m6", "03PYm", "you shall love your neighbor as yourself", "as", None),
        ("Deut", "05xhV", "05upQ", "05xhV", "a prophet like me will the LORD your God raise up for you", "like me", None),
        ("2Sam", "10GmN", "10Pfc", "10GmN", "that you should look on a dead dog such as I am", "such as I am", None),
    ],
    "H3426": [
        ("Gen", "01Jv8", "01Cho", "01EiW", "surely the LORD is in this place", "is", _YESH_NOTE_1),
        ("Gen", "01XzD", "01XzD", "012UN", "I have enough, my brother", "have", _YESH_NOTE_HAVE),
        ("Gen", "01fMS", "01fMS", "01phD", "we have an old father, and a young brother", "have", _YESH_NOTE_HAVE),
        ("Judg", "07Lka", "07wfD", "07irT", "if you will save Israel by my hand", "if you will",
         "yeshkha (\"there is to you,\" i.e. \"you are able to\") + moshia` (\"savior\") is idiomatic for \"if you will save.\""),
        ("2Kgs", "1289f", "1289f", "12EyU", "the word of the LORD is with him", "is with him",
         "yesh oto (\"there-is to him\") is idiomatic for \"he has\" -- the word of the LORD is with him."),
    ],
    "H637": [
        ("Gen", "01x1q", "01x1q", "01bTo", "indeed, has God said you shall not eat...?", "indeed",
         "'af adds emphasis here, rendered \"indeed\" in natural English."),
        ("Gen", "01wDd", "01wDd", "01q11", "I also had a dream", "also", None),
        ("Lev", "03gDx", "03gDx", "03W33", "and also my covenant with Isaac", "also", None),
        ("Deut", "05pvY", "05K78", "05UDg", "the Rephaim were also considered giants, like the Anakim", "also", None),
        ("1Kgs", "11YSC", "11YSC", "11z6J", "how much more this house that I have built", "how much more",
         "af ki (literally \"even that\") is idiomatic for \"how much more.\""),
    ],
    "H6435": [
        ("Gen", "01UDg", "01LG5", "01Baw", "you shall not touch it, lest you die", "lest", None),
        ("Gen", "01wVX", "01G5G", "01FD2", "let us make a name, lest we be scattered", "lest", None),
        ("Gen", "01NnT", "01npB", "01TQz", "do not stay in the valley -- flee to the mountain, lest you be swept away", "lest", None),
    ],
    "H1115": [
        ("Gen", "01Sh8", "01k4N", "01rxd", "you shall not see my face except your brother is with you", "except", None),
        ("Gen", "01uCS", "01uCS", "01HpH", "so that no one finding him would strike him down", "no one",
         "levilti (\"so as not to\") is spread across \"so that no one ... would\" here."),
        ("Exod", "02CnF", "02CnF", "02yqC", "so that you may not sin", "not", None),
        ("Num", "04oKm", "04oKm", "04Pp8", "except Caleb...and Joshua", "except", None),
        ("Judg", "07awY", "07awY", "07EAT", "so as not to drive them out quickly", "not to", None),
    ],
    "H7535": [
        ("Gen", "01RH3", "01qwa", "01bEm", "every inclination... was only evil, continually", "only", None),
        ("Gen", "01y8F", "01y8F", "013bJ", "only to these men do nothing", "only", None),
        ("Exod", "02Fjh", "02Fjh", "02RUm", "only your flocks and herds shall remain", "only", None),
        ("Josh", "06R3h", "06R3h", "06bfb", "only in Gaza, Gath, and Ashdod did [the Anakim] remain", "only", None),
        ("Judg", "07don", "07don", "07T3v", "only so that the generations of Israel's sons might know war", "only", None),
    ],
    "H1157": [
        ("Gen", "01roj", "01FXw", "01roj", "the LORD shut him in", "in",
         "be`ado (\"behind/around him\") is folded into the phrasal verb \"shut ... in\" here."),
        ("Gen", "015iT", "01Vap", "01Jmq", "Abimelech looked out through the window", "through", None),
        ("Exod", "02hZA", "02ZYc", "025E4", "let me make atonement for your sin", "for", None),
        ("Judg", "07tA5", "07NH6", "07tA5", "Ehud went out... and shut the doors behind him", "behind", None),
        ("Jonah", "32k1L", "32HSQ", "322tS", "the earth with its bars closed behind me forever", "behind me", None),
    ],
    "H3282": [
        ("Gen", "013ku", "013ku", "01E9J", "because you have done this thing", "because", None),
        ("Num", "04h5B", "04h5B", "04VjZ", "because you did not believe me", "because", None),
        ("1Kgs", "11vNk", "11vNk", "11J2d", "because this has been your practice", "because", None),
    ],
    "H349": [
        ("Gen", "01hW5", "01hW5", "01mQs", "how then could I do this great evil?", "how", None),
        ("Deut", "0592v", "0592v", "05FbT", "how can I bear your weight alone?", "how", None),
        ("2Sam", "10eRa", "10eRa", "1063G", "how the mighty have fallen!", "how", None),
    ],
    "H4069": [
        ("Exod", "02kMZ", "02kMZ", "02WJY", "why have you come so soon today?", "why", None),
        ("Exod", "02AwN", "02AwN", "02u6F", "why the bush is not burnt up", "why", None),
        ("Judg", "07DUx", "07DUx", "07kDi", "why is his chariot so long in coming?", "why", None),
    ],
}


def strip_cantillation(s):
    return CANTILLATION_RE.sub("", s)


def load_targets():
    with open(DECK_PATH, encoding="utf-8") as f:
        deck = json.load(f)
    targets = {}
    for e in deck["entries"]:
        if e["lemma_id"].startswith("F-") or e["pos"] in TARGET_POS:
            targets[e["lemma_id"]] = e
    return targets


def load_book(book_code):
    path = os.path.join(WLC_DIR, f"{book_code}.xml")
    root = ET.parse(path).getroot()
    verses = {}
    word_to_verse = {}
    for verse in root.iter(f"{OSIS_NS}verse"):
        vid = verse.get("osisID")
        if vid is None:
            continue
        words = []
        for w in verse.iter(f"{OSIS_NS}w"):
            wid = w.get("id")
            words.append({
                "id": wid,
                "lemma": w.get("lemma") or "",
                "text": w.text or "",
            })
            if wid:
                word_to_verse[wid] = vid
        verses[vid] = words
    return verses, word_to_verse


def matches_lemma(lemma_parts, lemma_id):
    for lp_raw in lemma_parts:
        lp = lp_raw.strip()
        if lemma_id.startswith("F-"):
            if lp == lemma_id[2:]:
                return True
        else:
            m = re.match(r"^(\d+)", lp)
            if m and m.group(1) == lemma_id[1:]:
                return True
    return False


def extract_phrase(verse_words, start_id, end_id, tag):
    ids = [w["id"] for w in verse_words]
    if start_id not in ids:
        sys.exit(f"{tag}: phrase start id {start_id!r} not found in its verse")
    if end_id not in ids:
        sys.exit(f"{tag}: phrase end id {end_id!r} not found in its verse")
    si, ei = ids.index(start_id), ids.index(end_id)
    if si > ei:
        sys.exit(f"{tag}: phrase start id {start_id!r} comes after end id {end_id!r} in the verse")
    return verse_words[si:ei + 1]


def main():
    if not os.path.isfile(DECK_PATH):
        sys.exit("data/vocab_deck_600.json not found -- run pipeline/build_vocab_deck.py first")

    targets = load_targets()
    missing = set(targets) - set(EXAMPLES)
    if missing:
        sys.exit(f"EXAMPLES is missing entries for: {sorted(missing)}")
    extra = set(EXAMPLES) - set(targets)
    if extra:
        sys.exit(f"EXAMPLES has entries for lemmas outside the target set: {sorted(extra)}")

    book_cache = {}
    entries_out = []
    total_examples = 0

    for lemma_id, entry in targets.items():
        senses = [s.strip() for s in entry["gloss"].split(",") if s.strip()]
        needed = max(TIER_TARGET.get(lemma_id, 3), len(senses))
        picks = EXAMPLES[lemma_id]
        if len(picks) < needed:
            sys.exit(
                f"{lemma_id} ({entry['citation_form']!r}, gloss {entry['gloss']!r}): "
                f"gloss lists {len(senses)} sense(s), needs >= {needed} examples, has {len(picks)}"
            )

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
            # transliterate() is a per-word function (every other caller in
            # this pipeline only ever hands it one word) -- it silently
            # drops spaces if given a whole phrase at once, since a space
            # isn't one of the Hebrew characters it knows how to carry
            # through. Transliterating each word separately and rejoining
            # with spaces (mirroring how phrase_hebrew itself is built)
            # avoids that rather than changing the shared function's
            # contract for one caller.
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

        entries_out.append({
            "lemma_id": lemma_id,
            "citation_form": entry["citation_form"],
            "transliteration": entry["transliteration"],
            "full_gloss": entry["gloss"],
            "sense_count": len(senses),
            "examples": examples_out,
        })

    # Fold a merged lemma's examples into its primary card (see
    # build_vocab_deck.py's MERGED_LEMMAS -- H854/H5973 both mean "with").
    # Both lemmas were still individually curated and corpus-verified above;
    # this is a pure data step after the fact, not a curation shortcut, and
    # it's what lets the merged card show real examples of both written forms.
    by_lemma_out = {e["lemma_id"]: e for e in entries_out}
    for secondary_id, entry in targets.items():
        primary_id = entry.get("merged_into")
        if not primary_id:
            continue
        primary_out = by_lemma_out.get(primary_id)
        secondary_out = by_lemma_out.get(secondary_id)
        if primary_out is None or secondary_out is None:
            sys.exit(f"merge: {secondary_id} -> {primary_id} but one or both missing from built entries")
        primary_out["examples"].extend(secondary_out["examples"])
        entries_out.remove(secondary_out)

    out = {
        "metadata": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "scope": "F-<letter> prefix morphemes plus Preposition/Conjunction/Particle/"
                     "Definite article/Interrogative particle/Relative particle vocab entries",
            "example_count_rule": "max(TIER_TARGET.get(lemma_id, 3), comma-separated senses in the curated gloss)",
            "phrase_rule": "Hebrew is trimmed to the phrase matching the curated English gloss, "
                           "not the full verse",
            "highlight_rule": "target_index marks the Hebrew word being taught; gloss_highlight "
                               "marks the closest English word(s), with gloss_note explaining any "
                               "non-obvious correspondence",
            "lemma_count": len(entries_out),
            "example_count": total_examples,
        },
        "entries": entries_out,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(entries_out)} lemmas, {total_examples} examples to {OUT_PATH}")


if __name__ == "__main__":
    main()

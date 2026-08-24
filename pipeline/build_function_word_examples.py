"""
Learn tab / Vocab tab addition: real Hebrew Bible usage examples for the
closed set of function words (prepositions, conjunctions, particles, and
the inseparable prefix morphemes) -> data/function_word_examples.json.

Lane's own framing for why this exists: these words are hard to remember
because a bare gloss ("in, on, with") gives no usage context -- unlike a
concrete noun or verb, a preposition's meaning only becomes clear from a
real sentence. So: at least 3 real, corpus-sourced occurrences per word,
scaling up when the curated gloss lists more distinct senses than that
(the exact rule, decided with Lane rather than guessed at: examples_needed
= max(3, number of comma-separated senses in the gloss)).

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

# Shared note text for the small cluster of examples where the same
# explanation applies every time (repeated per-example rather than
# factored out, since the data is what ships -- not a code path).
_ET_NOTE = "'et itself has no English translation -- it just flags the direct object."
_FI_NOTE = "the question marker itself isn't a separate word -- it's what makes this a question in English."
_YESH_NOTE_1 = "yesh just asserts presence here -- no literal \"there is\" in the English."
_YESH_NOTE_HAVE = "yesh + \"to me/us\" is how Hebrew says \"I/we have\" -- no literal \"there is\" in the English."

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
    ],
    "F-b": [
        ("Gen", "01xeN", "01xeN", "01nPh", "In the beginning God created the heavens and the earth", "In", None),
        ("Gen", "01gtq", "01oiy", "01gtq", "let us make man in our image", "in", None),
        ("Judg", "071TR", "07Ab6", "07MQc", "he struck a thousand men with it", "with", None),
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
    ],
    "H5921": [
        ("Gen", "01qNN", "01C5U", "01PB6", "darkness was over the face of the deep", "over", None),
        ("Gen", "01G6E", "01hS1", "014vX", "every living creature that moves on the earth", "on", None),
        ("Gen", "01khc", "01RFe", "01u6F", "the LORD God commanded the man, saying", "the man",
         "`al means \"concerning\" here; English just says \"commanded the man.\""),
    ],
    "H413": [
        ("Gen", "01tRR", "01NPq", "01dv1", "let the water be gathered to one place", "to", None),
        ("Gen", "01dvY", "01fZA", "01YkN", "the LORD called to the man", "to", None),
        ("Gen", "01ACV", "01ACV", "01FCG", "your desire will be for your husband", "for",
         "'el usually means \"to\"; here it reads naturally as \"for.\""),
    ],
    "H834": [
        ("Gen", "01B2d", "01B2d", "01SV6", "whose seed is in itself", "whose",
         "asher is rendered \"whose\" here for a natural possessive reading."),
        ("Gen", "01HWo", "01FMa", "01uUA", "every plant that is on the face of the earth", "that", None),
        ("Gen", "01Doj", "012GY", "01F5r", "whatever the man called each creature", "whatever",
         "asher combines with \"all\" (kol) to read as \"whatever.\""),
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
    ],
    "F-k": [
        ("Gen", "01HSQ", "01oiy", "01HSQ", "let us make man in our image, as our likeness", "as", None),
        ("Gen", "01Wyn", "01G2d", "01Wyn", "I will make a helper corresponding to him", "corresponding",
         "ke- fuses with neged (\"opposite\") into the idiom \"corresponding to.\""),
        ("Gen", "01RUp", "01a9X", "014YU", "you will be like God, knowing good and evil", "like", None),
    ],
    "H5704": [
        ("Gen", "01JyU", "01JyU", "01RxS", "until you return to the ground", "until", None),
        ("Gen", "01euh", "01mWC", "01wX7", "they came as far as Haran, and settled there", "as far as", None),
        ("Gen", "01shT", "015eb", "01Gxb", "I will give it to you and your offspring forever", "forever",
         "`ad pairs with `olam (\"eternity\") here to mean \"forever.\""),
    ],
    "H4480": [
        ("Gen", "01CFo", "01Csj", "015Ja", "the man, dust from the ground", "from", None),
        ("Gen", "019Yh", "01j8W", "019Yh", "you shall not eat from it", "from", None),
        ("Gen", "01x5W", "01q4j", "01s3h", "the rib that he had taken from the man", "from", None),
    ],
    "H518": [
        ("Gen", "01DK9", "01bmL", "01JoL", "if you do well, will you not be accepted?", "if", None),
        ("Gen", "01cHs", "01cHs", "01CsK", "if now I have found favor in your eyes", "if", None),
        ("Gen", "01Vio", "01Vio", "01v99", "if I find fifty righteous within the city", "if", None),
    ],
    "H5973": [
        ("Gen", "01eVQ", "01Wsp", "01eVQ", "Lot was with him", "with", None),
        ("Gen", "01dDG", "016io", "01iLp", "will you sweep away the righteous with the wicked?", "with", None),
        ("Gen", "01otC", "01111", "01ru7", "show steadfast love with my master", "with", None),
    ],
    "H854": [
        ("Gen", "014Zw", "01sUy", "014Zw", "I will establish my covenant with you", "with", None),
        ("Gen", "012iX", "01nbb", "012iX", "Noah, his sons, his wife, and his sons' wives -- with him", "with", None),
        ("Gen", "014wk", "01qmG", "014wk", "I am establishing my covenant with you", "with", None),
    ],
    "H2009": [
        ("Gen", "01Ygn", "01Ygn", "01pAw", "behold, I have given [it] to you", "behold", None),
        ("Gen", "01JUf", "01JUf", "01dPK", "and behold, it was very good", "behold", None),
        ("Gen", "01CXn", "01T4t", "01eW4", "behold, I am bringing the flood", "behold", None),
    ],
    "H369": [
        ("Gen", "01Pht", "01oYp", "01FCP", "and there was no man to work the ground", "no", None),
        ("Gen", "01Mos", "01Mos", "01Fu4", "and he was not, for God took him", "not", None),
        ("Gen", "017pd", "01P8j", "01ikF", "Sarai was barren; she had no child", "no", None),
    ],
    "H3651": [
        ("Gen", "01n5f", "019qY", "01n5f", "and it was so", "so", None),
        ("Gen", "01d1k", "01pww", "01fiZ", "therefore a man leaves his father and mother", "therefore",
         "ken combines with `al (\"upon\") into the idiom \"therefore.\""),
        ("Gen", "01VnV", "01zG9", "01J24", "just as God commanded him, so he did", "so", None),
    ],
    "H1571": [
        ("Gen", "01Bxn", "01Pw8", "01uXm", "she gave some to her husband also", "also", None),
        ("Gen", "01xRR", "01dVq", "01xRR", "Abel also brought [an offering]", "also", None),
        ("Gen", "01cMr", "01TYN", "01GDg", "to Seth also a son was born", "also", None),
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
    "H1768": [
        ("Ezra", "15eWk", "15HBY", "15UNQ", "the nations whom he deported", "whom",
         "di is a general relative particle, rendered \"whom\" since it refers to people."),
        ("Ezra", "15F1H", "1578y", "15j2J", "the letter which they sent", "which", None),
        ("Ezra", "15thm", "15aUT", "15BKq", "servants of the God of heaven and earth", "of",
         "di can also mark possession here, like English \"of.\""),
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
    ],
    "H4616": [
        ("Gen", "01uDX", "01uDX", "01p8s", "so that it may go well with me", "so that", None),
        ("Gen", "01DF8", "01DF8", "01FcZ", "in order that the LORD may bring [what he promised]", "in order that", None),
        ("Exod", "02NvP", "02NvP", "02YPx", "so that my name may be proclaimed in all the earth", "so that", None),
    ],
    "H389": [
        ("Gen", "01veg", "01RNc", "01BQz", "only Noah was left, and those with him", "only", None),
        ("Gen", "01CV5", "01CV5", "01mn4", "only, flesh with its life... you shall not eat", "only", None),
        ("Gen", "01k4p", "01k4p", "01sCD", "surely, this is your wife", "surely", None),
    ],
    "H5048": [
        ("Gen", "01Wyn", "01Zmd", "01Wyn", "a helper corresponding to/opposite him", "opposite", None),
        ("Gen", "01aiP", "01V7Q", "01QFp", "she sat down at a distance, opposite him", "opposite", None),
        ("Gen", "01gdC", "01gdC", "01Aca", "identify what is yours before our kinsmen", "before", None),
    ],
    "F-s": [
        ("Ps", "19mzp", "19ZHH", "19JHQ", "like a city that is bound firmly together", "that", None),
        ("Ps", "19nWJ", "19Hwj", "19pjA", "the LORD, who was on our side", "who", None),
        ("Ps", "19imQ", "19N3f", "192Y4", "blessed be the LORD, who did not give us as prey", "who", None),
    ],
    "H3644": [
        ("Exod", "02scM", "0299z", "02cPY", "they went down into the depths like a stone", "like", None),
        ("Exod", "02vvb", "02qe3", "02JP4", "who is like you among the gods, O LORD?", "like", None),
        ("Lev", "03PYm", "032m6", "03PYm", "you shall love your neighbor as yourself", "as", None),
    ],
    "H3426": [
        ("Gen", "01Jv8", "01Cho", "01EiW", "surely the LORD is in this place", "is", _YESH_NOTE_1),
        ("Gen", "01XzD", "01XzD", "012UN", "I have enough, my brother", "have", _YESH_NOTE_HAVE),
        ("Gen", "01fMS", "01fMS", "01phD", "we have an old father, and a young brother", "have", _YESH_NOTE_HAVE),
    ],
    "H637": [
        ("Gen", "01x1q", "01x1q", "01bTo", "indeed, has God said you shall not eat...?", "indeed",
         "'af adds emphasis here, rendered \"indeed\" in natural English."),
        ("Gen", "01wDd", "01wDd", "01q11", "I also had a dream", "also", None),
        ("Lev", "03gDx", "03gDx", "03W33", "and also my covenant with Isaac", "also", None),
    ],
    "H6435": [
        ("Gen", "01UDg", "01LG5", "01Baw", "you shall not touch it, lest you die", "lest", None),
        ("Gen", "01wVX", "01G5G", "01FD2", "let us make a name, lest we be scattered", "lest", None),
        ("Gen", "01NnT", "01npB", "01TQz", "do not stay in the valley -- flee to the mountain, lest you be swept away", "lest", None),
    ],
    "H4481": [
        ("Ezra", "15f13", "153Qm", "15b2J", "the Jews who came up from you to us", "from", None),
        ("Ezra", "15FQu", "15FQu", "15185", "from ancient days", "from", None),
        ("Ezra", "15ik6", "15aUh", "15R15", "brought out from the temple", "from", None),
    ],
    "H1115": [
        ("Gen", "01Sh8", "01k4N", "01rxd", "you shall not see my face except your brother is with you", "except", None),
        ("Gen", "01uCS", "01uCS", "01HpH", "so that no one finding him would strike him down", "no one",
         "levilti (\"so as not to\") is spread across \"so that no one ... would\" here."),
        ("Exod", "02CnF", "02CnF", "02yqC", "so that you may not sin", "not", None),
    ],
    "H5922": [
        ("Ezra", "15XRb", "15L3V", "15AkY", "they wrote a letter against Jerusalem", "against",
         "`al reads as \"against\" here since the letter was hostile."),
        ("Ezra", "15hHR", "157Xe", "15CoS", "the king sent word to Rehum", "to",
         "`al functions like \"to\" here -- a message directed at Rehum."),
        ("Ezra", "157ej", "15avL", "15amD", "let them build it on its site", "on", None),
    ],
    "H7535": [
        ("Gen", "01RH3", "01qwa", "01bEm", "every inclination... was only evil, continually", "only", None),
        ("Gen", "01y8F", "01y8F", "013bJ", "only to these men do nothing", "only", None),
        ("Exod", "02Fjh", "02Fjh", "02RUm", "only your flocks and herds shall remain", "only", None),
    ],
    "H1157": [
        ("Gen", "01roj", "01FXw", "01roj", "the LORD shut him in", "in",
         "be`ado (\"behind/around him\") is folded into the phrasal verb \"shut ... in\" here."),
        ("Gen", "015iT", "01Vap", "01Jmq", "Abimelech looked out through the window", "through", None),
        ("Exod", "02hZA", "02ZYc", "025E4", "let me make atonement for your sin", "for", None),
        ("Judg", "07tA5", "07NH6", "07tA5", "Ehud went out... and shut the doors behind him", "behind", None),
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
    "H3809": [
        ("Ezra", "15nk3", "15Tgd", "15wj3", "they will not pay tribute", "not", None),
        ("Ezra", "15U2p", "15U2p", "15SG8", "and it is not finished", "not", None),
        ("Dan", "27Amf", "27Amf", "27K9E", "the wise men are not able [to tell it]", "not", None),
    ],
    "H5542": [
        ("Ps", "19FMU", "19xva", "19FMU", "'There is no salvation for him in God.' Selah", "Selah", None),
        ("Ps", "19E91", "19Lzv", "19E91", "Who is this King of glory? ...Selah", "Selah", None),
        ("Ps", "19Fdk", "1944e", "19Fdk", "The LORD of hosts is with us. Selah", "Selah", None),
    ],
    "H1077": [
        ("Ps", "193v4", "193v4", "19hFh", "I shall not be moved", "not", None),
        ("Ps", "19zbv", "19zbv", "19nXx", "you have not withheld [what his lips desired]", "not", None),
        ("Ps", "199fJ", "19iFe", "19rMg", "in the pride of his face... he will not seek [God]", "not", None),
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
        needed = max(3, len(senses))
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

    out = {
        "metadata": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "scope": "F-<letter> prefix morphemes plus Preposition/Conjunction/Particle/"
                     "Definite article/Interrogative particle/Relative particle vocab entries",
            "example_count_rule": "max(3, comma-separated senses in the curated gloss)",
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

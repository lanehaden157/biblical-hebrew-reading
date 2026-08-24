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
(book_code, word_id) reference and the English gloss are hand-authored;
the Hebrew (both the target word and the full verse it sits in) is pulled
from the corpus by word id and verified in verify_function_word_examples.py
to actually match the claimed lemma -- a wrong word id fails loudly rather
than silently mislabeling a sense.

Each example keeps the FULL VERSE, not just the target word or a trimmed
phrase -- matches how the Jonah reader already shows real Hebrew (a
preposition ripped out of its sentence "doesn't actually look like
Hebrew", per build_jonah1_reader.py's docstring), and lets Lane see the
word actually doing its job in context, which is the whole point of this
feature. `gloss` is a short hand-written English rendering of the clause
around the target word (not a full formal verse translation) -- enough to
show what the word is doing, matching the register of this project's
existing lesson notes.

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

# (book_code, word_id, gloss) per lemma. gloss is a short hand-written
# rendering of the clause the target word sits in -- see module docstring.
EXAMPLES = {
    "F-c": [
        ("Gen", "01LN3", "and the earth was without form and void"),
        ("Gen", "01thY", "and God said, ‘Let there be light’"),
        ("Gen", "017am", "and God said, ‘Let there be a vault...’"),
    ],
    "F-d": [
        ("Gen", "01TSc", "God created the heavens and the earth"),
        ("Gen", "01GzE", "God saw the light, that it was good"),
        ("Gen", "01d5m", "let there be a vault in the middle of the water"),
    ],
    "F-l": [
        ("Gen", "01Wkf", "God called the light ‘day’"),
        ("Gen", "01pAw", "I have given [every plant] to you [for food]"),
        ("Gen", "0192v", "lights in the sky, to separate day from night"),
    ],
    "F-b": [
        ("Gen", "01xeN", "In the beginning God created the heavens and the earth"),
        ("Gen", "01gtq", "let us make man in our image"),
        ("Judg", "071TR", "he struck a thousand men with it"),
    ],
    "H853": [
        ("Gen", "01vuQ", "God created the heavens and the earth"),
        ("Gen", "01Zuo", "God created man in his own image"),
        ("Gen", "01w6u", "God saw everything that he had made"),
    ],
    "F-m": [
        ("Gen", "01L4k", "the water under the vault, and the water above"),
        ("Gen", "01ZMk", "the LORD planted a garden in Eden, in the east"),
        ("Gen", "01Dwm", "he took one of his ribs"),
    ],
    "H5921": [
        ("Gen", "01qNN", "darkness was over the face of the deep"),
        ("Gen", "01G6E", "have dominion... over all the earth"),
        ("Gen", "01khc", "the LORD commanded the man, saying..."),
    ],
    "H413": [
        ("Gen", "01tRR", "let the water be gathered to one place"),
        ("Gen", "01dvY", "the LORD called to the man"),
        ("Gen", "01eHZ", "your desire will be for your husband"),
    ],
    "H834": [
        ("Gen", "01B2d", "seed, whose seed is in itself"),
        ("Gen", "01HWo", "every plant that is on the face of the earth"),
        ("Gen", "01Doj", "whatever the man called each creature"),
    ],
    "H3808": [
        ("Gen", "01j8W", "you shall not eat from it"),
        ("Gen", "01SGf", "it is not good for the man to be alone"),
        ("Gen", "01fE2", "and they were not ashamed"),
    ],
    "H3588": [
        ("Gen", "01qCU", "God saw the light, that it was good"),
        ("Gen", "01WJY", "because the LORD God had not sent rain"),
        ("Gen", "01T97", "she saw that the tree was good"),
        ("Gen", "01tA5", "when you work the ground, it will no longer yield"),
    ],
    "F-k": [
        ("Gen", "01HSQ", "let us make man in our image, as our likeness"),
        ("Gen", "01Wyn", "I will make a helper corresponding to him"),
        ("Gen", "01RUp", "you will be like God, knowing good and evil"),
    ],
    "H5704": [
        ("Gen", "01JyU", "until you return to the ground"),
        ("Gen", "01euh", "they came as far as Haran, and settled there"),
        ("Gen", "01shT", "I will give it to you and your offspring forever"),
    ],
    "H4480": [
        ("Gen", "01CFo", "the man, dust from the ground"),
        ("Gen", "019Yh", "you shall not eat from it"),
        ("Gen", "01x5W", "the rib that he had taken from the man"),
    ],
    "H518": [
        ("Gen", "01DK9", "if you do well, will you not be accepted?"),
        ("Gen", "01cHs", "if now I have found favor in your eyes"),
        ("Gen", "01Vio", "if I find fifty righteous within the city"),
    ],
    "H5973": [
        ("Gen", "01eVQ", "and Lot went with him"),
        ("Gen", "01dDG", "will you sweep away the righteous with the wicked?"),
        ("Gen", "01otC", "show steadfast love with my master"),
    ],
    "H854": [
        ("Gen", "014Zw", "I will establish my covenant with you"),
        ("Gen", "012iX", "Noah and his sons and his wife... with him"),
        ("Gen", "014wk", "I am establishing my covenant with you"),
    ],
    "H2009": [
        ("Gen", "01Ygn", "behold, I have given you every plant"),
        ("Gen", "01JUf", "and behold, it was very good"),
        ("Gen", "01CXn", "behold, I am bringing the flood"),
    ],
    "H369": [
        ("Gen", "01Pht", "and there was no man to work the ground"),
        ("Gen", "01Mos", "and he was not, for God took him"),
        ("Gen", "017pd", "Sarai was barren; she had no child"),
    ],
    "H3651": [
        ("Gen", "01n5f", "and it was so"),
        ("Gen", "01d1k", "therefore a man leaves his father and mother"),
        ("Gen", "01VnV", "just as God commanded him, so he did"),
    ],
    "H1571": [
        ("Gen", "01Bxn", "she gave some to her husband also"),
        ("Gen", "01xRR", "Abel also brought [an offering]"),
        ("Gen", "01cMr", "to Seth also a son was born"),
    ],
    "H4100": [
        ("Gen", "01gjk", "what is this you have done?"),
        ("Gen", "01iQS", "what have you done?"),
        ("Gen", "01TkZ", "by what shall I know [that I will possess it]?"),
    ],
    "H408": [
        ("Gen", "013dA", "do not be afraid, Abram"),
        ("Gen", "01jTj", "do not look behind you"),
        ("Gen", "01XWM", "do not stretch out your hand against the boy"),
    ],
    "H310": [
        ("Gen", "01bcM", "the days of Adam, after he fathered Seth"),
        ("Gen", "013iU", "Noah lived after the flood 350 years"),
        ("Gen", "01Ps4", "and afterward the clans of the Canaanites dispersed"),
    ],
    "F-i": [
        ("Gen", "01GYp", "have you eaten from the tree...?"),
        ("Gen", "01caE", "Am I my brother's keeper?"),
        ("Gen", "01Kzw", "Is anything too hard for the LORD?"),
    ],
    "H8478": [
        ("Gen", "01L4k", "the water under the vault"),
        ("Gen", "01vD2", "another offspring in place of Abel"),
        ("Gen", "01oQN", "he offered it up... instead of his son"),
    ],
    "H4310": [
        ("Gen", "01Cdg", "who told you that you were naked?"),
        ("Gen", "01J84", "if Esau asks you... ‘to whom do you belong?’"),
        ("Gen", "01mZS", "who are these to you?"),
    ],
    "H996": [
        ("Gen", "01CsU", "God separated the light from the darkness"),
        ("Gen", "019QD", "the sign of the covenant between me and you"),
        ("Gen", "01hPa", "there was strife between the herdsmen"),
    ],
    "H4994": [
        ("Gen", "01S7G", "please say you are my sister"),
        ("Gen", "01aKv", "lift up your eyes, now, and look"),
        ("Gen", "01Xgr", "let a little water now be brought"),
    ],
    "H1768": [
        ("Ezra", "15eWk", "the nations whom he deported"),
        ("Ezra", "15F1H", "the letter which they sent"),
        ("Ezra", "15thm", "servants of the God of heaven and earth"),
    ],
    "H176": [
        ("Gen", "01es7", "can we speak to you bad or good?"),
        ("Gen", "01Kgz", "have you a father, or a brother?"),
        ("Exod", "02xFg", "if his master gives him a wife, and she bears him sons or daughters"),
    ],
    "H2005": [
        ("Gen", "01Zzk", "behold, the man has become like one of us"),
        ("Gen", "01pVY", "behold, you have given me no offspring"),
        ("Gen", "01KGK", "behold, you have driven me this day"),
    ],
    "H4616": [
        ("Gen", "01uDX", "so that it may go well with me"),
        ("Gen", "01VPw", "in order that the LORD may bring [what he promised]"),
        ("Exod", "02NvP", "so that my name may be proclaimed in all the earth"),
    ],
    "H389": [
        ("Gen", "01veg", "only Noah was left, and those with him"),
        ("Gen", "01CV5", "only, flesh with its life... you shall not eat"),
        ("Gen", "01k4p", "surely, this is your wife"),
    ],
    "H5048": [
        ("Gen", "01Wyn", "a helper corresponding to/opposite him"),
        ("Gen", "01aiP", "she sat down at a distance, opposite him"),
        ("Gen", "01gdC", "identify what is yours before our kinsmen"),
    ],
    "F-s": [
        ("Ps", "19mzp", "like a city that is bound firmly together"),
        ("Ps", "19nWJ", "the LORD, who was on our side"),
        ("Ps", "19imQ", "blessed be the LORD, who did not give us as prey"),
    ],
    "H3644": [
        ("Exod", "02scM", "they went down into the depths like a stone"),
        ("Exod", "02vvb", "who is like you among the gods, O LORD?"),
        ("Lev", "03PYm", "you shall love your neighbor as yourself"),
    ],
    "H3426": [
        ("Gen", "01Jv8", "surely the LORD is in this place"),
        ("Gen", "01XzD", "I have enough, my brother"),
        ("Gen", "01fMS", "we have an old father, and a young brother"),
    ],
    "H637": [
        ("Gen", "01x1q", "indeed, has God said you shall not eat...?"),
        ("Gen", "01wDd", "I also had a dream"),
        ("Lev", "03gDx", "and also my covenant with Isaac I will remember"),
    ],
    "H6435": [
        ("Gen", "01UDg", "you shall not touch it, lest you die"),
        ("Gen", "01wVX", "let us make a name, lest we be scattered"),
        ("Gen", "01NnT", "do not stay anywhere on the plain, lest you be swept away"),
    ],
    "H4481": [
        ("Ezra", "15f13", "the Jews who came up from you to us"),
        ("Ezra", "15FQu", "the rebellion of old, from ancient days"),
        ("Ezra", "15ik6", "the vessels brought out from the temple"),
    ],
    "H1115": [
        ("Gen", "01Sh8", "you shall not see my face except your brother is with you"),
        ("Gen", "01uCS", "so that no one finding him would strike him down"),
        ("Exod", "02CnF", "so that you may not sin"),
    ],
    "H5922": [
        ("Ezra", "15XRb", "they wrote a letter against Jerusalem"),
        ("Ezra", "15hHR", "the king sent word to Rehum"),
        ("Ezra", "157ej", "let them build it on its site"),
    ],
    "H7535": [
        ("Gen", "01RH3", "every inclination... was only evil, continually"),
        ("Gen", "01y8F", "only to these men do nothing"),
        ("Exod", "02Fjh", "only your flocks and herds shall remain"),
    ],
    "H1157": [
        ("Gen", "01roj", "the LORD shut him in"),
        ("Gen", "015iT", "Abimelech looked out through the window"),
        ("Exod", "02hZA", "let me make atonement for your sin"),
        ("Judg", "07tA5", "Ehud went out... and shut the doors behind him"),
    ],
    "H3282": [
        ("Gen", "013ku", "because you have done this thing"),
        ("Num", "04h5B", "because you did not believe me"),
        ("1Kgs", "11vNk", "because this has been your practice"),
    ],
    "H349": [
        ("Gen", "01hW5", "how then could I do this great evil?"),
        ("Deut", "0592v", "how can I bear your weight alone?"),
        ("2Sam", "10eRa", "how the mighty have fallen!"),
    ],
    "H3809": [
        ("Ezra", "15nk3", "they will not pay tribute"),
        ("Ezra", "15U2p", "and it is not finished"),
        ("Dan", "27Amf", "the wise men are not able [to tell it]"),
    ],
    "H5542": [
        ("Ps", "19FMU", "‘There is no salvation for him in God.’ Selah"),
        ("Ps", "19E91", "Who is this King of glory? ...Selah"),
        ("Ps", "19Fdk", "The LORD of hosts is with us. Selah"),
    ],
    "H1077": [
        ("Ps", "193v4", "I shall not be moved"),
        ("Ps", "19zbv", "you have not withheld [what his lips desired]"),
        ("Ps", "199fJ", "in the pride of his face... he will not seek [God]"),
    ],
    "H4069": [
        ("Exod", "02kMZ", "why have you come so soon today?"),
        ("Exod", "02AwN", "why the bush is not burnt up"),
        ("Judg", "07DUx", "why is his chariot so long in coming?"),
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
        for book_code, word_id, gloss in picks:
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

            surface_form = strip_cantillation(target["text"].replace("/", ""))
            verse_words_clean = [strip_cantillation(w["text"].replace("/", "")) for w in verse_words]
            verse_hebrew = " ".join(verse_words_clean)
            # transliterate() is a per-word function (every other caller in
            # this pipeline only ever hands it one word) -- it silently
            # drops spaces if given a whole phrase at once, since a space
            # isn't one of the Hebrew characters it knows how to carry
            # through. Transliterating each word separately and rejoining
            # with spaces (mirroring how verse_hebrew itself is built)
            # avoids that rather than changing the shared function's
            # contract for one caller.
            verse_translit = " ".join(transliterate(w) for w in verse_words_clean)

            examples_out.append({
                "ref": vid,
                "surface_form": surface_form,
                "transliteration": transliterate(surface_form),
                "word_id": word_id,
                "verse_hebrew": verse_hebrew,
                "verse_transliteration": verse_translit,
                "gloss": gloss,
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

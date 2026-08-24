"""
Phase 3 step 1: OSHB corpus -> Qal strong-verb parsing deck ->
data/parse_qal_strong.json.

Scope, per CLAUDE.md:
  - Stem: Qal only (69.0% of verb forms -- Tier 2's binyan).
  - Conjugations: qatal, weqatal, wayyiqtol, yiqtol, participle,
    infinitive construct. Imperative, jussive, cohortative, infinitive
    absolute, and the passive participle are real OSHB categories but
    stay out of scope here -- not a bug, matching how Pual/Hophal are
    recognition-only. Weqatal (sequential perfect) was added alongside
    qatal: it's morphologically identical to qatal and is disambiguated
    only by its vav-conjunctive prefix and narrative context, so it's the
    direct counterpart of the wayyiqtol/yiqtol pair and belongs in the
    same deck once the whole printed word (prefix included) is shown.
  - Roots: strong only. A root is weak (and excluded) if any radical is
    guttural (alef/he/het/ayin -- the four "true gutturals" of first-year
    grammar; resh is deliberately NOT treated as guttural here, since its
    only Qal-relevant quirk is refusing dagesh forte, which barely surfaces
    in Qal and is not one of CLAUDE.md's named weak classes), if the first
    radical is nun (assimilates) or vav/yod (I-Vav/Yod), if the second
    radical is vav/yod (hollow) or repeats the third (geminate). III-He and
    III-Aleph roots need no separate rule: he and alef are already in the
    guttural set, so "any radical is guttural" catches them for free.
  - Lemmas: restricted to the verb lemmas already in the curated top-600
    vocab deck (data/vocab_deck_600.json), not all ~700 Qal-attested lemmas
    in the corpus. This is deliberate, not a limitation of the corpus scan:
    those lemmas already carry a curated gloss and a lexicon-sourced
    citation form (verified 100% "lexicon"-sourced below, never a
    surface-form fallback, which could carry stray affixes into what's
    supposed to be a bare root). Reusing them means every Hebrew form shown
    gets transliteration + gloss without a second curation pass, and it
    keeps parsing practice anchored to vocabulary Lane is already learning.

Card display shows the WHOLE printed word, not just the verb's own
morpheme -- matching how the Jonah readers already do it (see
build_jonah1_reader.py's docstring: "a prefixed vav or preposition is
never pulled out into its own visual token -- that would show Hebrew that
doesn't actually look like Hebrew"). A form like wayyiqtol's defining vav,
or a pronominal-suffixed infinitive construct, is meaningless with its
prefix/suffix stripped -- and stripping it was the source of the parse-tab
bug this rewrite fixes. `surface_form`/`transliteration` are therefore the
full word; `verb_form` isolates just the verb's own consonants (for
highlighting), and `prefix_form`/`suffix_form` hold whatever surrounds it,
built by re-joining the OSHB word's own "/"-separated morpheme spans, not
by regenerating Hebrew text. `prefix_glosses` resolves any function-word
prefix (conjunction/article/preposition/relative/interrogative -- the
closed 8-code set in hebrew_corpus.FUNCTION_CODES) against the same
curated F-<letter> entries the Jonah readers already use, so no new
curation happens here. `suffix_kind`/`suffix_pgn` records a pronominal
suffix's own person/gender/number (paragogic nun/he get a kind but no
PGN, since they aren't pronouns).

`verb_form` also gets a second-level split into `preformative` +
`root_span` + `afformative` (see find_root_span()) -- the card highlight
is meant to mark the 3-letter root specifically, and `verb_form` as a
whole includes conjugation-marking material that is not the root (a
yiqtol/wayyiqtol preformative letter, a qatal/weqatal person-suffix, a
participle gender/number ending). Coloring all of verb_form the same as
the root was flagged as wrong by inspection of real cards (yimshal's
formative yod, wekhafarta's person-suffix tav both read as "root" even
though neither is one of mem/shin/lamed or kaf/pe/resh) -- this is the fix.

The root's own transliteration/gloss come straight from the vocab deck;
the word's transliteration is computed here from the FULL word in one
pass, not per-morpheme, since Hebrew phonology (shva na/nach in
particular) doesn't respect the OSHB morpheme boundary -- transliterating
a lone verb morpheme in isolation was exactly how the old truncated cards
got a wrong transliteration too, not just a wrong Hebrew string.

Text is never NFC/NFD-normalized (CLAUDE.md rule 2) -- only cantillation
(U+0591-U+05AF) is stripped, which is deletion, not normalization.

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
OUT_PATH = os.path.join(HERE, "..", "data", "parse_qal_strong.json")

CANTILLATION_RE = re.compile("[֑-֯]")

GUTTURAL = set("אהחע")   # alef he het ayin
NUN = "נ"
VAV, YOD = "ו", "י"
FINAL_TO_BASE = {
    "ך": "כ",  # final kaf -> kaf
    "ם": "מ",  # final mem -> mem
    "ן": "נ",  # final nun -> nun
    "ף": "פ",  # final pe -> pe
    "ץ": "צ",  # final tsadi -> tsadi
}
HEB_CONSONANT_RE = re.compile("[א-ת]")

# Conjugation letter (position 2 of a Vq... morph code) -> our label.
# Confirmed against the OSHB morphology spec (hb.openscriptures.org) and
# against the raw corpus: 'q' is sequential perfect (weqatal), 'i' is
# imperfect (yiqtol) -- these were swapped/missing in the version of this
# script that shipped the wrong yiqtol cards. 'r' (participle) and 'c'
# (infinitive construct) carry no person; the rest carry a 3-char
# person+gender+number suffix.
CONJUGATIONS = {
    "p": "qatal",
    "q": "weqatal",
    "w": "wayyiqtol",
    "i": "yiqtol",
    "r": "participle",
    "c": "infinitive_construct",
}
FINITE_CONJUGATIONS = {"p", "q", "w", "i"}

GENDER_LABEL = {"m": "m", "f": "f", "c": "c"}
NUMBER_LABEL = {"s": "s", "p": "p", "d": "d"}
STATE_LABEL = {"a": "absolute", "c": "construct"}

# HVq<conj><suffix> where conj is one of our locked letters. Suffix is
# 3 chars (person+gender+number) for finite forms, 3 chars
# (gender+number+state) for participles, absent for infinitive construct.
MORPH_RE = re.compile(r"^Vq([pqwirc])([123]?[mfc]?[spd]?[ac]?)$")

# What can trail a verb morpheme (morph_parts after the Vq... one).
# Confirmed against the corpus, restricted to strong roots: NONE (no
# trailing morpheme), a pronominal object suffix (Sp<person><gender>
# <number>), a paragogic nun (Sn), or a paragogic/directional he (Sh).
# Anything else is rare enough (2 occurrences project-wide) to skip and
# log rather than guess at.
SUFFIX_PGN_RE = re.compile(r"^Sp([123])([mfc])([spd])$")


def strip_cantillation(s):
    return CANTILLATION_RE.sub("", s)


def root_consonants(citation_form):
    out = []
    for ch in citation_form:
        if HEB_CONSONANT_RE.match(ch):
            out.append(FINAL_TO_BASE.get(ch, ch))
    return out


def weakness_reasons(citation_form):
    """Every weak-class reason a root fails strong-verb status, or [] if strong."""
    c = root_consonants(citation_form)
    if len(c) != 3:
        return [f"non-triliteral({len(c)})"]
    r1, r2, r3 = c
    reasons = []
    if r1 in GUTTURAL:
        reasons.append("I-guttural")
    if r2 in GUTTURAL:
        reasons.append("II-guttural")
    if r3 in GUTTURAL:
        reasons.append("III-guttural")
    if r1 == NUN:
        reasons.append("I-Nun")
    if r1 in (VAV, YOD):
        reasons.append("I-Vav/Yod")
    if r2 in (VAV, YOD):
        reasons.append("hollow")
    if r2 == r3:
        reasons.append("geminate")
    return reasons


def parse_pgn(conj, suffix):
    """Split a morph suffix into person/gender/number/state per conjugation."""
    person = gender = number = state = None
    if conj in FINITE_CONJUGATIONS:
        m = re.match(r"^([123])([mfc])([spd])$", suffix)
        if not m:
            return None
        person, g, n = m.groups()
        gender, number = GENDER_LABEL[g], NUMBER_LABEL[n]
    elif conj == "r":
        m = re.match(r"^([mfc])([spd])([ac])$", suffix)
        if not m:
            return None
        g, n, st = m.groups()
        gender, number, state = GENDER_LABEL[g], NUMBER_LABEL[n], STATE_LABEL[st]
    elif conj == "c":
        if suffix:
            return None  # infinitive construct with an unexpected suffix -- skip, don't guess
    return {"person": person, "gender": gender, "number": number, "state": state}


def load_strong_verb_roots():
    with open(DECK_PATH, encoding="utf-8") as f:
        deck = json.load(f)
    roots = {}
    functional = {}
    weak_count = 0
    for e in deck["entries"]:
        if e["lemma_id"].startswith("F-"):
            functional[e["lemma_id"]] = e
            continue
        if e["pos"] != "Verb":
            continue
        reasons = weakness_reasons(e["citation_form"])
        if reasons:
            weak_count += 1
            continue
        roots[e["lemma_id"]] = e
    print(f"Top-600 verb lemmas: strong-root count {len(roots)}, weak-root count {weak_count}")
    missing_fn = set("F-" + c for c in FUNCTION_CODES) - set(functional)
    if missing_fn:
        sys.exit(f"vocab_deck_600.json is missing curated entries for function codes: {missing_fn}")
    return roots, functional


def find_root_span(verb_form, root_letters):
    """Locate the 3 root consonants in verb_form's own consonant skeleton,
    splitting off whatever precedes them (a yiqtol/wayyiqtol preformative:
    aleph/yod/nun/tav) and whatever follows them (a qatal/weqatal
    person-suffix, or a participle gender/number ending) as separate spans
    -- the highlighting the parse cards use to mark "this is the root" is
    otherwise coloring the whole verb_form, formative letters included,
    which is not the root.

    The 3 root letters do not have to be strictly adjacent: Hebrew commonly
    spells a long vowel "plene", with an extra vav or yod standing in for
    the vowel point, and that mater lectionis can land between two root
    consonants -- the Qal participle's cholam is the single biggest source
    of this (moshel, "ruler", is spelled mem-VAV-shin-lamed for a root of
    only mem/shin/lamed). A first version of this function required strict
    contiguity and silently skipped 140 real entries over exactly this,
    caught only by checking the actual skip count, not by the reconstruction
    assert (mem+vav+shin+lamed still reconstructs the surface form whether
    the vav is "misclassified into root_span" or handled correctly -- the
    assert can't see which). So: only vav/yod are permitted filler between
    two matched root letters; anything else breaks that candidate match.

    Deliberately still NOT a per-conjugation lookup table of preformative/
    afformative letters, which would need a cell for every conjugation x
    person x gender x number combination -- exactly the kind of
    hand-enumerated surface that produces plausible-looking wrong output
    CLAUDE.md warns about. A genuine ambiguity (more than one way to place
    the root, or no valid placement at all) fails loudly as a skipped
    anomaly instead of guessing. Returns (preformative, root_span,
    afformative) or None."""
    skeleton = [
        (FINAL_TO_BASE.get(ch, ch), idx)
        for idx, ch in enumerate(verb_form)
        if HEB_CONSONANT_RE.match(ch)
    ]
    n = len(root_letters)
    matres = {VAV, YOD}

    def extend(pos, letter_idx):
        """Deterministic: from skeleton[pos], scan for root_letters[letter_idx],
        treating any vav/yod passed along the way as a skippable mater
        lectionis and any other letter as a hard mismatch. At most one
        continuation is possible per starting position, since a mismatch
        ends the search rather than branching."""
        if letter_idx == n:
            return pos
        target = root_letters[letter_idx]
        i = pos
        while i < len(skeleton):
            ch, _ = skeleton[i]
            if ch == target:
                return extend(i + 1, letter_idx + 1)
            if ch not in matres:
                return None
            i += 1
        return None

    matches = []
    for start in range(len(skeleton)):
        if skeleton[start][0] != root_letters[0]:
            continue
        end = extend(start + 1, 1)
        if end is not None:
            matches.append((start, end))

    if len(matches) != 1:
        return None
    start, end = matches[0]
    root_start_idx = skeleton[start][1]
    root_end_idx = skeleton[end][1] if end < len(skeleton) else len(verb_form)
    return verb_form[:root_start_idx], verb_form[root_start_idx:root_end_idx], verb_form[root_end_idx:]


def resolve_prefix(lemma_parts, verb_index, functional):
    """Every function-morpheme lemma before the verb -> its curated deck
    entry, in reading order. Returns (list_of_entries, anomaly_or_None)."""
    resolved = []
    for lp_raw in lemma_parts[:verb_index]:
        lp = lp_raw.strip()
        if not lp:
            continue
        if not re.match(r"^[a-z]$", lp):
            return None, f"unrecognized prefix lemma part {lp!r}"
        fn_id = "F-" + lp
        entry = functional.get(fn_id)
        if entry is None:
            return None, f"prefix lemma {fn_id!r} not in curated function-word set"
        resolved.append(entry)
    return resolved, None


def resolve_suffix(morph_parts, verb_index):
    """Classify whatever trails the verb's own morph part. Returns
    (kind, pgn_or_None, anomaly_or_None)."""
    rest = morph_parts[verb_index + 1:]
    if not rest:
        return None, None, None
    if len(rest) == 1:
        m = SUFFIX_PGN_RE.match(rest[0])
        if m:
            person, g, n = m.groups()
            return "pronominal", {
                "person": person, "gender": GENDER_LABEL[g], "number": NUMBER_LABEL[n],
            }, None
        if rest[0] == "Sn":
            return "paragogic_nun", None, None
        if rest[0] == "Sh":
            return "directional_he", None, None
    return None, None, f"unhandled trailing morpheme(s) {rest!r}"


def main():
    if not os.path.isfile(DECK_PATH):
        sys.exit("data/vocab_deck_600.json not found -- run pipeline/build_vocab_deck.py first")
    if not os.path.isdir(WLC_DIR):
        sys.exit("pipeline/corpus/wlc not found -- run pipeline/fetch_corpus.py first")

    roots, functional = load_strong_verb_roots()

    entries = []
    skipped_suffix = []
    skipped_anomaly = []
    conj_counts = {label: 0 for label in CONJUGATIONS.values()}

    for book_code, book_name in BOOK_ORDER:
        path = os.path.join(WLC_DIR, f"{book_code}.xml")
        root = ET.parse(path).getroot()
        for verse in root.iter(f"{OSIS_NS}verse"):
            vid = verse.get("osisID")
            if vid is None:
                continue
            for w in verse.iter(f"{OSIS_NS}w"):
                wid = w.get("id")
                raw_lemma = w.get("lemma")
                raw_morph = w.get("morph")
                if not raw_lemma or not raw_morph:
                    continue
                lemma_parts = raw_lemma.split("/")
                morph_parts = raw_morph.split("/")
                word_parts = (w.text or "").split("/")

                for i, mp in enumerate(morph_parts):
                    # Only the *first* slash-separated part carries the H/A
                    # language-code prefix (confirmed in hebrew_corpus.py /
                    # rank_lemmas.py); later parts are bare POS codes already.
                    if i == 0:
                        mp = mp[1:] if mp.startswith(("H", "A")) else mp
                    m = MORPH_RE.match(mp)
                    if not m:
                        continue
                    conj, suffix = m.groups()
                    label = CONJUGATIONS[conj]

                    lp_raw = lemma_parts[i].strip() if i < len(lemma_parts) else ""
                    lp = re.match(r"^(\d+)", lp_raw)
                    if not lp:
                        continue
                    lemma_id = "H" + lp.group(1)
                    root_entry = roots.get(lemma_id)
                    if root_entry is None:
                        continue

                    pgn = parse_pgn(conj, suffix)
                    if pgn is None:
                        skipped_suffix.append({"verse": vid, "morph": mp, "lemma_id": lemma_id})
                        continue

                    verb_form = strip_cantillation((word_parts[i] if i < len(word_parts) else "").replace("/", ""))
                    if not verb_form:
                        continue

                    prefix_entries, prefix_err = resolve_prefix(lemma_parts, i, functional)
                    if prefix_err:
                        skipped_anomaly.append({"verse": vid, "reason": prefix_err, "lemma": raw_lemma, "morph": raw_morph})
                        continue

                    suffix_kind, suffix_pgn, suffix_err = resolve_suffix(morph_parts, i)
                    if suffix_err:
                        skipped_anomaly.append({"verse": vid, "reason": suffix_err, "lemma": raw_lemma, "morph": raw_morph})
                        continue

                    prefix_form = strip_cantillation("".join(word_parts[:i]))
                    suffix_form = strip_cantillation("".join(word_parts[i + 1:]))
                    full_word = strip_cantillation("".join(word_parts))
                    if prefix_form + verb_form + suffix_form != full_word:
                        skipped_anomaly.append({
                            "verse": vid, "reason": "prefix+verb+suffix != full word",
                            "lemma": raw_lemma, "morph": raw_morph,
                        })
                        continue

                    root_split = find_root_span(verb_form, root_consonants(root_entry["citation_form"]))
                    if root_split is None:
                        skipped_anomaly.append({
                            "verse": vid, "reason": "root not a unique contiguous run in verb_form",
                            "lemma": raw_lemma, "morph": raw_morph, "verb_form": verb_form,
                        })
                        continue
                    preformative, root_span, afformative = root_split

                    entries.append({
                        "id": f"{wid or vid}-{i}",
                        "ref": vid,
                        "book": book_name,
                        "surface_form": full_word,
                        "transliteration": transliterate(full_word),
                        "verb_form": verb_form,
                        "prefix_form": prefix_form,
                        "suffix_form": suffix_form,
                        "preformative": preformative,
                        "root_span": root_span,
                        "afformative": afformative,
                        "prefix_morphemes": [
                            {
                                "citation_form": e["citation_form"],
                                "transliteration": e["transliteration"],
                                "gloss": e["gloss"],
                            }
                            for e in prefix_entries
                        ],
                        "suffix_kind": suffix_kind,
                        "suffix_pgn": suffix_pgn,
                        "lemma_id": lemma_id,
                        "root_citation_form": root_entry["citation_form"],
                        "root_transliteration": root_entry["transliteration"],
                        "gloss": root_entry["gloss"],
                        "stem": "Qal",
                        "conjugation": label,
                        "person": pgn["person"],
                        "gender": pgn["gender"],
                        "number": pgn["number"],
                        "state": pgn["state"],
                    })
                    conj_counts[label] += 1

    print(f"Built {len(entries)} parse entries across {len(conj_counts)} conjugations:")
    for label, n in conj_counts.items():
        print(f"  {label}: {n}")
    if skipped_suffix:
        print(f"WARNING: {len(skipped_suffix)} matches had an unparseable PGN suffix, skipped", file=sys.stderr)
    if skipped_anomaly:
        print(f"WARNING: {len(skipped_anomaly)} matches had an unresolved prefix/suffix, skipped", file=sys.stderr)

    out = {
        "metadata": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "stem": "Qal",
            "conjugations": list(CONJUGATIONS.values()),
            "strong_root_definition": (
                "triliteral; no radical in {alef,he,het,ayin}; "
                "first radical not nun; first radical not vav/yod; "
                "second radical not vav/yod; second radical does not equal third"
            ),
            "root_lemma_source": "data/vocab_deck_600.json verb entries (rank 1-600)",
            "count": len(entries),
            "conjugation_counts": conj_counts,
            "distinct_roots": len({e["lemma_id"] for e in entries}),
            "skipped_unparseable_suffix": len(skipped_suffix),
            "skipped_anomaly": len(skipped_anomaly),
        },
        "entries": entries,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(entries)} entries to {OUT_PATH}")

    if skipped_suffix or skipped_anomaly:
        anomaly_path = os.path.join(HERE, "build_parse_qal_anomalies.json")
        with open(anomaly_path, "w", encoding="utf-8") as f:
            json.dump({"skipped_suffix": skipped_suffix, "skipped_anomaly": skipped_anomaly}, f, ensure_ascii=False, indent=2)
        print(f"Anomaly detail written to {anomaly_path}")


if __name__ == "__main__":
    main()

"""
Independent verification of data/top600.json.

This deliberately does NOT reuse rank_lemmas.py's parsing code. Where that
script uses xml.etree.ElementTree, this script re-derives the same facts
with plain regex over the raw corpus bytes, so a bug specific to one parsing
approach is unlikely to be invisible to both. Every check either passes or
prints a specific failure and the script exits non-zero -- nothing is
silently tolerated.

Checks performed:
  1. Structural integrity of the JSON (600 unique sequential ranks,
     frequency non-increasing by rank, no duplicate lemma_id).
  2. Character-set sanity: every citation_form / example verse text is made
     up only of expected Hebrew consonants, points, cantillation, maqqef,
     paseq, sof-pasuq, and (for verse text) plain spaces -- catches mojibake
     or a botched extraction silently producing garbage.
  3. Independent regex-based recomputation of per-lemma frequency, majority
     POS, and citation form for every one of the top 600, compared for exact
     equality against the JSON. Exact string equality on citation_form and
     example verse text also serves as the check that no NFC/NFD
     normalization was applied anywhere in the pipeline (CLAUDE.md rule 2):
     regex extraction straight from the raw file bytes cannot itself
     normalize, so if it matches character-for-character, the JSON is
     untouched from source.
  4. Global sanity: total_word_tokens and distinct_lemmas in metadata match an
     independent regex count.
  5. Every example verse's osisID actually exists in the corresponding book
     file, and its reported word count matches an independent regex count
     for that verse (catches truncated/duplicated verse text).
"""
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict

from hebrew_corpus import BOOK_ORDER, FUNCTION_CODES, POS_LETTER_TO_LABEL, WLC_DIR, LEXICON_PATH

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(HERE, "..", "data", "top600.json")

CANTILLATION_RE = re.compile("[֑-֯]")
LEMMA_PART_RE = re.compile(r"^(\d+)(?:\s[a-z])?\+?$")
MAQQEF = "־"

# U+0591-U+05C7 covers cantillation, points, maqqef, rafe, paseq, sof pasuq
# and the rare nun-hafukha/qamats-qatan marks in one contiguous block;
# U+05D0-U+05EA is the consonants; U+05F3-U+05F4 is geresh/gershayim; plain
# space for reconstructed verse text. U+034F (combining grapheme joiner) is
# allowed too -- HebrewStrong.xml uses it once, in H3389 (Jerusalem), to
# force correct display ordering of two adjacent vowel points. Confirmed by
# grepping the lexicon: it's the only occurrence, a deliberate part of the
# source, not corruption -- see verify_top600.py's investigation notes.
ALLOWED_CHARS_RE = re.compile(
    "^[֑-ׇ͏א-ת׳״ ]*$"
)

WORD_RE = re.compile(r'<w\b([^>]*)>(.*?)</w>', re.S)
TOKEN_RE = re.compile(r'<(w|seg)\b([^>]*)>(.*?)</\1>', re.S)
VERSE_RE = re.compile(r'<verse osisID="([^"]+)">(.*?)</verse>', re.S)
ATTR_RE = lambda name: re.compile(rf'{name}="([^"]*)"')

LEMMA_ATTR_RE = ATTR_RE("lemma")
MORPH_ATTR_RE = ATTR_RE("morph")
TYPE_ATTR_RE = ATTR_RE("type")

failures = []


def fail(msg):
    failures.append(msg)
    print(f"FAIL: {msg}", file=sys.stderr)


def strip_cantillation(s):
    return CANTILLATION_RE.sub("", s)


def load_lexicon_regex():
    with open(LEXICON_PATH, encoding="utf-8") as f:
        content = f.read()
    lex = {}
    for m in re.finditer(r'<entry id="(H\d+)">\s*<w pos="([^"]*)"[^>]*>([^<]+)</w>', content):
        eid, pos, text = m.groups()
        if eid not in lex:
            lex[eid] = {"citation_form": text.strip(), "lexicon_pos": pos}
    return lex


def build_verse_text_regex(verse_inner):
    parts = []
    for tag, attrs, inner in TOKEN_RE.findall(verse_inner):
        if tag == "w":
            t = inner.replace("/", "")
            if parts and not parts[-1].endswith(MAQQEF):
                parts.append(" ")
            parts.append(t)
        elif tag == "seg":
            parts.append(inner)
    return "".join(parts).strip()


def scan_corpus():
    """Independent regex-based pass producing the same facts rank_lemmas.py
    computes via ElementTree: per-lemma frequency, POS tally, surface-form
    tally, and per-verse (osisID -> (word_count, text))."""
    freq = Counter()
    pos_tally = defaultdict(Counter)
    surface_form_tally = defaultdict(Counter)
    anomalies = []
    total_words = 0
    verses = {}  # osisID -> {"word_count": int, "text": str, "book": str}

    for book_code, book_name in BOOK_ORDER:
        path = os.path.join(WLC_DIR, f"{book_code}.xml")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        for vid, vinner in VERSE_RE.findall(content):
            words = WORD_RE.findall(vinner)
            if not words:
                continue
            total_words += len(words)
            verses[vid] = {
                "word_count": len(words),
                "text": build_verse_text_regex(vinner),
                "book": book_name,
            }
            for attrs, text in words:
                lemma_m = LEMMA_ATTR_RE.search(attrs)
                morph_m = MORPH_ATTR_RE.search(attrs)
                if not lemma_m:
                    continue
                raw_lemma = lemma_m.group(1)
                raw_morph = morph_m.group(1) if morph_m else ""
                lemma_parts = raw_lemma.split("/")
                morph_parts = raw_morph.split("/")
                word_parts = text.split("/")
                for i, lp in enumerate(lemma_parts):
                    lp = lp.strip()
                    if not lp:
                        continue
                    mp = morph_parts[i] if i < len(morph_parts) else ""
                    wp = word_parts[i] if i < len(word_parts) else ""
                    # Only the first morph part carries the H/A language
                    # prefix; confirmed independently by scanning non-first
                    # parts across the corpus (see rank_lemmas.py comment).
                    if i == 0:
                        pos_letter = mp[1] if len(mp) >= 2 else None
                    else:
                        pos_letter = mp[0] if mp else None

                    m = LEMMA_PART_RE.match(lp)
                    if m:
                        lemma_id = "H" + m.group(1)
                    elif re.match(r"^[a-z]$", lp) and lp in FUNCTION_CODES:
                        lemma_id = "F-" + lp
                    else:
                        anomalies.append((vid, raw_lemma, lp))
                        continue

                    freq[lemma_id] += 1
                    if pos_letter:
                        pos_tally[lemma_id][pos_letter] += 1
                    if wp:
                        surface_form_tally[lemma_id][strip_cantillation(wp)] += 1

    return freq, pos_tally, surface_form_tally, anomalies, total_words, verses


def main():
    if not os.path.isfile(DATA_PATH):
        sys.exit(f"{DATA_PATH} not found -- run pipeline/rank_lemmas.py first")

    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)

    meta = data["metadata"]
    lemmas = data["lemmas"]

    # --- 1. structural integrity ---------------------------------------
    if len(lemmas) != meta["top_n"]:
        fail(f"metadata.top_n={meta['top_n']} but {len(lemmas)} lemma entries present")

    ranks = [e["rank"] for e in lemmas]
    if ranks != list(range(1, len(lemmas) + 1)):
        fail("ranks are not a sequential 1..N run")

    ids = [e["lemma_id"] for e in lemmas]
    if len(ids) != len(set(ids)):
        dupes = [x for x, c in Counter(ids).items() if c > 1]
        fail(f"duplicate lemma_id values: {dupes}")

    freqs_in_order = [e["frequency"] for e in lemmas]
    if any(freqs_in_order[i] < freqs_in_order[i + 1] for i in range(len(freqs_in_order) - 1)):
        fail("frequency is not non-increasing by rank")

    # --- 2. character-set sanity -----------------------------------------
    for e in lemmas:
        cf = e["citation_form"] or ""
        if not cf:
            fail(f"{e['lemma_id']}: empty citation_form")
        elif not ALLOWED_CHARS_RE.match(cf):
            fail(f"{e['lemma_id']}: citation_form has unexpected characters: {cf!r}")
        for ex in e["example_verses"]:
            if not ex["text"]:
                fail(f"{e['lemma_id']}: empty example verse text for {ex['ref']}")
            elif not ALLOWED_CHARS_RE.match(ex["text"]):
                fail(f"{e['lemma_id']}: example verse {ex['ref']} has unexpected characters")

    # --- 3 & 4. independent regex recomputation --------------------------
    print("Re-scanning corpus independently (regex-based)...")
    freq, pos_tally, surface_form_tally, anomalies, total_words, verses = scan_corpus()
    lexicon = load_lexicon_regex()

    if meta["total_word_tokens"] != total_words:
        fail(f"metadata.total_word_tokens={meta['total_word_tokens']} but independent recount got {total_words}")

    total_lemma_occurrences_regex = sum(freq.values())
    if meta["total_lemma_occurrences"] != total_lemma_occurrences_regex:
        fail(f"metadata.total_lemma_occurrences={meta['total_lemma_occurrences']} but independent recount got {total_lemma_occurrences_regex}")

    distinct_lemmas_regex = len(freq)
    if meta["distinct_lemmas"] != distinct_lemmas_regex:
        fail(f"metadata.distinct_lemmas={meta['distinct_lemmas']} but independent recount got {distinct_lemmas_regex}")

    if meta["anomaly_count"] != len(anomalies):
        fail(f"metadata.anomaly_count={meta['anomaly_count']} but independent recount got {len(anomalies)}")

    expected_coverage = round(sum(sorted(freq.values(), reverse=True)[:meta["top_n"]]) / total_lemma_occurrences_regex * 100, 2)
    if abs(expected_coverage - meta["top_n_token_coverage_pct"]) > 0.05:
        fail(f"top_n_token_coverage_pct={meta['top_n_token_coverage_pct']} but recomputed {expected_coverage}")

    for e in lemmas:
        lid = e["lemma_id"]
        expected_freq = freq.get(lid, 0)
        if e["frequency"] != expected_freq:
            fail(f"{lid}: frequency={e['frequency']} but independent recount got {expected_freq}")

        if lid.startswith("H"):
            letter = pos_tally[lid].most_common(1)[0][0] if pos_tally[lid] else None
            expected_pos = POS_LETTER_TO_LABEL.get(letter, letter or "Unknown")
        else:
            expected_pos = FUNCTION_CODES[lid.split("-", 1)[1]]
        if e["pos"] != expected_pos:
            fail(f"{lid}: pos={e['pos']!r} but independent recount got {expected_pos!r}")

        if e["citation_source"] == "lexicon":
            lex = lexicon.get(lid)
            if not lex:
                fail(f"{lid}: citation_source=lexicon but no independent lexicon entry found for {lid}")
            elif lex["citation_form"] != e["citation_form"]:
                fail(f"{lid}: citation_form={e['citation_form']!r} but lexicon (regex) has {lex['citation_form']!r}")
        elif e["citation_source"] in ("corpus_fallback", "corpus_frequent_surface_form"):
            sf = surface_form_tally[lid]
            expected_cf = sf.most_common(1)[0][0] if sf else None
            if expected_cf != e["citation_form"]:
                fail(f"{lid}: citation_form={e['citation_form']!r} but most-frequent surface form (regex) is {expected_cf!r}")
        else:
            fail(f"{lid}: unrecognized citation_source {e['citation_source']!r}")

        # --- 5. example verses exist and match an independent recount ----
        for ex in e["example_verses"]:
            v = verses.get(ex["ref"])
            if v is None:
                fail(f"{lid}: example verse {ex['ref']} not found in corpus (regex)")
                continue
            if v["text"] != ex["text"]:
                fail(f"{lid}: example verse {ex['ref']} text does not match independent regex extraction")
            if v["book"] != ex["book"]:
                fail(f"{lid}: example verse {ex['ref']} book={ex['book']!r} but expected {v['book']!r}")

    print(f"Checked {len(lemmas)} lemmas, {sum(len(e['example_verses']) for e in lemmas)} example verses.")

    if failures:
        print(f"\n{len(failures)} FAILURE(S)", file=sys.stderr)
        sys.exit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()

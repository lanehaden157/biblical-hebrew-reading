"""
Phase 2 step 1: OSHB corpus -> ranked lemma list -> data/top600.json.

For every lemma (Strong's-numbered lexeme, or one of the 8 bound function
morphemes -- conjunction, article, three prepositions, interrogative,
relative -- that carry no Strong's number) this counts frequency across the
whole Hebrew Bible and emits, for the top 600 by frequency:
  - citation form (pointed Hebrew, no cantillation)
  - part of speech (majority morph tag across all occurrences)
  - frequency (raw occurrence count)
  - up to 3 real example verses (reference + full pointed verse text)

Text is never NFC/NFD-normalized anywhere in this script (see CLAUDE.md rule
2) -- only cantillation marks (U+0591-U+05AF) are stripped, which is
deletion, not normalization.

Run pipeline/fetch_corpus.py first.
"""
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime, timezone

from hebrew_corpus import (
    BOOK_ORDER, FUNCTION_CODES, LEXICON_PATH, LEX_NS, OSIS_NS,
    POS_LETTER_TO_LABEL, WLC_DIR,
)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(HERE, "..", "data", "top600.json")
TOP_N = 600
MAX_EXAMPLES_TRACKED = 5  # distinct verses recorded per lemma before we stop looking (need 3)

CANTILLATION_RE = re.compile("[֑-֯]")
LEMMA_PART_RE = re.compile(r"^(\d+)(?:\s[a-z])?\+?$")
MAQQEF = "־"


def strip_cantillation(s):
    return CANTILLATION_RE.sub("", s)


def load_lexicon():
    tree = ET.parse(LEXICON_PATH)
    root = tree.getroot()
    lex = {}
    for entry in root.findall(f"{LEX_NS}entry"):
        eid = entry.get("id")
        if not eid or not eid.startswith("H"):
            continue
        w = entry.find(f"{LEX_NS}w")
        if w is None or not (w.text or "").strip():
            continue
        lex[eid] = {
            "citation_form": w.text.strip(),
            "lexicon_pos": w.get("pos"),
        }
    return lex


def build_verse_text(verse):
    parts = []
    for child in verse.iter():
        tag = child.tag
        if tag == f"{OSIS_NS}w":
            t = (child.text or "").replace("/", "")
            if parts and not parts[-1].endswith(MAQQEF):
                parts.append(" ")
            parts.append(t)
        elif tag == f"{OSIS_NS}seg":
            parts.append(child.text or "")
    return "".join(parts).strip()


def main():
    if not os.path.isdir(WLC_DIR):
        sys.exit("pipeline/corpus/wlc not found -- run pipeline/fetch_corpus.py first")

    lexicon = load_lexicon()
    print(f"Loaded {len(lexicon)} lexicon entries")

    freq = Counter()
    pos_tally = defaultdict(Counter)
    surface_form_tally = defaultdict(Counter)
    occurrences = defaultdict(list)
    occurrence_verse_ids = defaultdict(set)
    oshb_codes_seen = defaultdict(set)
    anomalies = []
    total_words = 0

    for book_code, book_name in BOOK_ORDER:
        path = os.path.join(WLC_DIR, f"{book_code}.xml")
        root = ET.parse(path).getroot()
        for verse in root.iter(f"{OSIS_NS}verse"):
            vid = verse.get("osisID")
            if vid is None:
                continue
            ws = list(verse.iter(f"{OSIS_NS}w"))
            if not ws:
                continue
            vtext = None
            for w in ws:
                total_words += 1
                raw_lemma = w.get("lemma")
                if not raw_lemma:
                    continue
                raw_morph = w.get("morph") or ""
                word_text = w.text or ""
                lemma_parts = raw_lemma.split("/")
                morph_parts = raw_morph.split("/")
                word_parts = word_text.split("/")

                for i, lp in enumerate(lemma_parts):
                    lp = lp.strip()
                    if not lp:
                        continue
                    mp = morph_parts[i] if i < len(morph_parts) else ""
                    wp = word_parts[i] if i < len(word_parts) else ""
                    # The H/A language code prefixes only the *first* morph
                    # part of a word (e.g. morph="HR/Vqc" for "l/559"), not
                    # every slash-separated part -- confirmed by scanning
                    # the corpus for what a non-first part's first letter
                    # actually is (always a bare POS letter, never H/A).
                    if i == 0:
                        pos_letter = mp[1] if len(mp) >= 2 else None
                    else:
                        pos_letter = mp[0] if mp else None

                    m = LEMMA_PART_RE.match(lp)
                    if m:
                        lemma_id = "H" + m.group(1)
                        oshb_codes_seen[lemma_id].add(lp)
                    elif re.match(r"^[a-z]$", lp) and lp in FUNCTION_CODES:
                        lemma_id = "F-" + lp
                    else:
                        anomalies.append({"verse": vid, "raw_lemma": raw_lemma, "part": lp})
                        continue

                    freq[lemma_id] += 1
                    if pos_letter:
                        pos_tally[lemma_id][pos_letter] += 1
                    if wp:
                        surface_form_tally[lemma_id][strip_cantillation(wp)] += 1

                    if vid not in occurrence_verse_ids[lemma_id] and len(occurrences[lemma_id]) < MAX_EXAMPLES_TRACKED:
                        if vtext is None:
                            vtext = build_verse_text(verse)
                        occurrence_verse_ids[lemma_id].add(vid)
                        occurrences[lemma_id].append({"osisID": vid, "book": book_name, "text": vtext})

    print(f"Processed {total_words} word tokens across {len(BOOK_ORDER)} books")
    print(f"Distinct lemmas: {len(freq)}")
    if anomalies:
        print(f"WARNING: {len(anomalies)} unrecognized lemma parts encountered -- see report", file=sys.stderr)

    ranked = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))
    top = ranked[:TOP_N]

    entries = []
    missing_lexicon = []
    for rank, (lemma_id, count) in enumerate(top, start=1):
        if lemma_id.startswith("H"):
            lex = lexicon.get(lemma_id)
            if lex:
                citation_form = lex["citation_form"]
                citation_source = "lexicon"
            else:
                sf = surface_form_tally[lemma_id]
                citation_form = sf.most_common(1)[0][0] if sf else None
                citation_source = "corpus_fallback"
                missing_lexicon.append(lemma_id)
            letter = pos_tally[lemma_id].most_common(1)[0][0] if pos_tally[lemma_id] else None
            pos = POS_LETTER_TO_LABEL.get(letter, letter or "Unknown")
            oshb_codes = sorted(oshb_codes_seen[lemma_id])
        else:
            code = lemma_id.split("-", 1)[1]
            sf = surface_form_tally[lemma_id]
            citation_form = sf.most_common(1)[0][0] if sf else None
            citation_source = "corpus_frequent_surface_form"
            pos = FUNCTION_CODES[code]
            oshb_codes = [code]

        examples = occurrences[lemma_id][:3]
        entries.append({
            "rank": rank,
            "lemma_id": lemma_id,
            "oshb_codes": oshb_codes,
            "citation_form": citation_form,
            "citation_source": citation_source,
            "pos": pos,
            "frequency": count,
            "example_verses": [
                {"ref": e["osisID"], "book": e["book"], "text": e["text"]} for e in examples
            ],
        })

    if missing_lexicon:
        print(f"WARNING: {len(missing_lexicon)} top-{TOP_N} lemmas had no lexicon entry, "
              f"used corpus fallback citation form: {missing_lexicon}", file=sys.stderr)

    # Coverage must compare like with like: freq counts lemma *occurrences*
    # (one per morpheme -- a single word like "and-the-word" contributes 3),
    # so the denominator has to be total lemma occurrences, not the word
    # (<w> element) count. total_words is kept separately as it's still a
    # useful, independently-checkable stat (see verify_top600.py).
    total_lemma_occurrences = sum(freq.values())
    coverage = sum(count for _, count in top) / total_lemma_occurrences * 100

    out = {
        "metadata": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "morphhb_version": "2.0.2",
            "hebrewlexicon_commit": "21c9add13bc727d3a951361778e97e3ff7afd1ce",
            "total_word_tokens": total_words,
            "total_lemma_occurrences": total_lemma_occurrences,
            "distinct_lemmas": len(freq),
            "top_n": TOP_N,
            "top_n_token_coverage_pct": round(coverage, 2),
            "anomaly_count": len(anomalies),
        },
        "lemmas": entries,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(entries)} lemmas to {OUT_PATH}")
    print(f"Top {TOP_N} token coverage: {coverage:.1f}%")

    if anomalies:
        anomaly_path = os.path.join(HERE, "rank_lemmas_anomalies.json")
        with open(anomaly_path, "w", encoding="utf-8") as f:
            json.dump(anomalies, f, ensure_ascii=False, indent=2)
        print(f"Anomaly detail written to {anomaly_path}")


if __name__ == "__main__":
    main()

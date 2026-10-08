"""
STEPBible TBESH (brief lexicon based on abridged BDB) and the OSHB-lemma -> TBESH map.

    tbesh()                 -> {"H0430G": {"gloss", "defn", "type", "translit"}}
    lemma_map(tokens, tah)  -> {oshb_lemma: {"key": "H0430G", "votes": n, "total": n}}

The map is decided by majority vote of TAHOT's own tag on every aligned token whose main
(non-prefix, non-suffix) morpheme has that OSHB lemma; OSHB augment letters ("1254 a") and
TBESH's ("H0430G") are different schemes, so no letter mapping is attempted.
"""
import collections
import glob
import html
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TBESH = glob.glob(os.path.join(ROOT, "sources", "stepbible", "Lexicons", "TBESH*.txt"))[0]


def _plain(s):
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def tbesh():
    out = {}
    with open(TBESH, encoding="utf-8") as f:
        for line in f:
            c = line.rstrip("\n").split("\t")
            if len(c) < 8 or not re.match(r"H\d{4}", c[0]):
                continue
            key = c[1].split()[0] if c[1].strip() else c[0]
            if not re.match(r"H\d{4}[A-Za-z]?$", key):
                continue
            out.setdefault(key, {"gloss": c[6].strip(), "defn": _plain(c[7]), "type": c[5].strip(),
                                 "translit": c[4].strip()})
    return out


def main_part(tok):
    """The token's main morpheme: the first non-prefix, non-suffix part with a numeric lemma."""
    return next((p for p in tok["parts"] if p["lemma"][:1].isdigit() and p["morph"][:1] != "S"), None)


def lemma_map(tokens, tah):
    votes = collections.defaultdict(collections.Counter)
    for t in tokens:
        p = main_part(t)
        g = tah.get(t["id"])
        if p and g and g["dstrong"]:
            votes[p["lemma"]][g["dstrong"]] += 1
    out = {}
    for lem, c in votes.items():
        key, n = c.most_common(1)[0]
        out[lem] = {"key": key, "votes": n, "total": sum(c.values())}
    return out

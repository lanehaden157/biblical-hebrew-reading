"""
Align OSHB morphemes to BHSA word nodes by consonant position (Phase 2, M13).

The two consonant streams are identical book by book (verify_corpus check 5), so every OSHB
letter has a BHSA owner. Each OSHB part gets a "primary" BHSA word: the one owning most of
its letters. BHSA words with no letters (elided article) are ignored for the primary.

Qere tokens are not aligned (BHSA's word features describe the written ketiv); their parts
map to None and they are reported, not compared.

    align(tokens) -> {token_id: [node or None per part]}, {token_id: "split"} flags
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tf  # noqa: E402

LETTERS = re.compile("[%s-%s]" % (chr(0x5D0), chr(0x5EA)))
BHSA_NAME = {"Gen": "Genesis", "Exod": "Exodus", "Num": "Numeri", "Josh": "Josua", "Judg": "Judices",
             "Ruth": "Ruth", "1Sam": "Samuel_I", "2Sam": "Samuel_II", "1Kgs": "Reges_I",
             "2Kgs": "Reges_II", "Jonah": "Jona"}
FEATURES = ["sp", "vs", "vt", "ps", "gn", "nu", "st", "lex", "prs_ps", "prs_gn", "prs_nu"]


def book_ranges():
    book = tf.read_feature("book")
    osl = tf.read_feature("oslots")
    out = {}                        # `book` is set on book, chapter and verse nodes: take the hull
    for n, name in book.items():
        a, z = tf.spans(osl[n])[0][0], tf.spans(osl[n])[-1][1]
        lo, hi = out.get(name, (a, z))
        out[name] = (min(lo, a), max(hi, z))
    return out


def load_features():
    return {f: tf.read_feature(f) for f in FEATURES}


def align(tokens, books):
    """tokens: list in corpus order (all books in `books`). Returns (parts_map, split_ids)."""
    cons = tf.read_feature("g_cons_utf8")
    ranges = book_ranges()
    parts_map, split = {}, set()
    for b in books:
        a, z = ranges[BHSA_NAME[b]]
        owner_b = []
        for n in range(a, z + 1):
            owner_b.extend([n] * len(LETTERS.findall(cons.get(n, ""))))
        btoks = [t for t in tokens if t["book"] == b]
        pos, seen = 0, set()
        for t in btoks:
            if t["ketiv"]:
                parts_map[t["id"]] = [None] * len(t["parts"])
                key = tuple(t["ketiv_ids"])
                if key not in seen:
                    seen.add(key)
                    pos += len(LETTERS.findall(t["ketiv"]))
                continue
            start = pos
            res = []
            for p in t["parts"]:
                n = len(LETTERS.findall(p["text"]))
                owners = owner_b[pos:pos + n]
                pos += n
                if not owners:
                    res.append(None)
                    continue
                res.append(max(set(owners), key=lambda x: (owners.count(x), -x)))
            # a BHSA word that owns letters both inside and outside this token = segmentation split
            inside = set(owner_b[start:pos])
            if (start > 0 and owner_b[start - 1] in inside) or (pos < len(owner_b) and owner_b[pos] in inside):
                split.add(t["id"])
            parts_map[t["id"]] = res
        if pos != len(owner_b):
            raise ValueError(f"{b}: OSHB has {pos} letters, BHSA {len(owner_b)}")
    return parts_map, split

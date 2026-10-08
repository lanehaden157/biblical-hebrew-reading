"""
STEPBible TAHOT per-word English glosses, aligned to corpus tokens.

    glosses(tokens) -> {token_id: {"raw": "and/ he said", "segs": ["and", "he said"], "g": "and he said",
                                   "dstrong": "H0559"}}     # TAHOT's tag for the main word

Rows of type L (Leningrad) or Q (qere) are kept; K (ketiv) rows are dropped, matching the
corpus, which reads the qere. Alignment is per verse on the consonant string of each word
(TAHOT and OSHB both follow WLC, Hebrew versification). Tokens left unaligned get no entry.

Display cleaning (g): morpheme slashes joined with spaces; "<obj.>" -> "[obj]"; other
angle-bracketed implied words keep their text; "[...]" (supplied words) kept as printed.
"""
import collections
import difflib
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(ROOT, "sources", "stepbible", "Translators Amalgamated OT+NT")
BOOKMAP = {"Gen": "Gen", "Exo": "Exod", "Num": "Num", "Jos": "Josh", "Jdg": "Judg", "Rut": "Ruth",
           "1Sa": "1Sam", "2Sa": "2Sam", "1Ki": "1Kgs", "2Ki": "2Kgs", "Jon": "Jonah"}
ROW = re.compile(r"^(\w+)\.(\d+)\.(\d+)(?:\((\d+)\.(\d+)\))?#\d+=(\S*)\t([^\t]*)\t([^\t]*)\t([^\t]*)\t([^\t]*)\t([^\t]*)")
MAIN = re.compile(r"\{(H\d+[A-Za-z]?)\}")
LETTER = re.compile("[%s-%s]" % (chr(0x5D0), chr(0x5EA)))


def load_rows():
    """{(book, ch, v): [(consonants, raw_gloss, main dStrong or None, grammar), ...]}, Hebrew
    versification."""
    out = collections.defaultdict(list)
    for path in glob.glob(os.path.join(DIR, "TAHOT *.txt")):
        with open(path, encoding="utf-8") as f:
            for line in f:
                m = ROW.match(line)
                if not m or m[1] not in BOOKMAP:
                    continue
                b, c, v, hc, hv, typ, heb, _tr, gloss, dstr, gram = m.groups()
                if not typ or typ[0] not in "LQ":
                    continue
                key = (BOOKMAP[b], int(hc or c), int(hv or v))
                heb = heb.split(chr(92))[0]                 # drop "\׃", "\ \פ" punctuation
                main = MAIN.search(dstr)
                out[key].append(("".join(LETTER.findall(heb)), gloss.strip(), main[1] if main else None,
                                 gram.strip()))
    return out


POSSESSIVE = {"my", "your", "his", "her", "its", "our", "their"}


def clean(raw, gram=""):
    """TAHOT 'from/ land/ your' + grammar 'HR/Ncfsc/Sp2ms' -> segs, g 'from your land'."""
    segs = [s.strip() for s in raw.split("/")]
    segs = [s.replace("<obj.>", "{obj}") for s in segs]
    segs = [re.sub(r"<the>\s*$", "", s) if i + 1 < len(segs) else s for i, s in enumerate(segs)]
    segs = [re.sub(r"[<>\[\]]", "", s) for s in segs]
    segs = [re.sub(r"\s+", " ", s).strip().replace("{obj}", "[obj]") for s in segs]
    words = list(segs)
    g = gram[1:].split("/") if gram else []
    if len(g) == len(words):                # noun+suffix: English puts the possessive first
        for i in range(1, len(words)):
            if g[i][:1] == "S" and g[i - 1][:1] in "NA" and words[i] in POSSESSIVE:
                words[i - 1], words[i] = words[i], words[i - 1]
    return segs, " ".join(w for w in words if w)


def glosses(tokens):
    rows = load_rows()
    verses = collections.defaultdict(list)
    for t in tokens:
        if t["read"]:
            verses[(t["book"], t["ch"], t["v"])].append(t)
    out = {}
    for key, toks in verses.items():
        r = rows.get(key, [])
        ours = ["".join(LETTER.findall(t["surface"])) for t in toks]
        theirs = [x[0] for x in r]
        if ours == theirs:
            pairs = {i: i for i in range(len(ours))}
        else:
            sm = difflib.SequenceMatcher(None, ours, theirs, autojunk=False)
            pairs = {blk.a + k: blk.b + k for blk in sm.get_matching_blocks() for k in range(blk.size)}
        for i, t in enumerate(toks):
            if i in pairs:
                _, raw, dstrong, gram = r[pairs[i]]
                segs, g = clean(raw, gram)
                out[t["id"]] = {"raw": raw, "segs": segs, "g": g, "dstrong": dstrong}
    return out

"""
World English Bible (public domain, USFM) per Hebrew verse.

    english()   -> {(book, ch, v): {"en": text, "en_ref": "Gen.32.1" | "Num.26.1", "strongs": set}}
                   keyed by OSHB (Hebrew) versification
    verse_map() -> {(book, ch, v) Hebrew: (book, ch, v) English}, only where they differ

The Hebrew->English map comes from STEPBible TVTMS (condensed section, "English KJV" vs
"Hebrew" columns). WEB follows KJV numbering. verify_text.py checks the map against WEB's own
Strong's tags. Footnotes and cross-references are dropped (some footnotes contain Hebrew).
"""
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "sources", "web")
TVTMS = glob.glob(os.path.join(ROOT, "sources", "stepbible", "Versification", "TVTMS*.txt"))
FILES = {"Gen": "02-GEN", "Exod": "03-EXO", "Num": "05-NUM", "Josh": "07-JOS", "Judg": "08-JDG",
         "Ruth": "09-RUT", "1Sam": "10-1SA", "2Sam": "11-2SA", "1Kgs": "12-1KI", "2Kgs": "13-2KI",
         "Jonah": "33-JON"}
TV_BOOK = {"Gen": "Gen", "Exo": "Exod", "Num": "Num", "Jos": "Josh", "Jdg": "Judg", "Rut": "Ruth",
           "1Sa": "1Sam", "2Sa": "2Sam", "1Ki": "1Kgs", "2Ki": "2Kgs", "Jon": "Jonah"}
NOTE = re.compile(r"\\(f|x|fe) .*?\\\1\*", re.S)
WORD = re.compile(r"\\\+?w ([^|\\]*)\|([^\\]*)\\\+?w\*")
STRONG = re.compile(r'strong="H0*(\d+)')
MARKER = re.compile(r"\\\+?[a-z]+\d?\*?")


def _usfm(book):
    """{(ch, v): (text, strongs)} for one WEB book."""
    path = glob.glob(os.path.join(WEB, FILES[book] + "eng-web.usfm"))[0]
    src = NOTE.sub("", open(path, encoding="utf-8").read())
    out, ch = {}, 0
    for piece in re.split(r"(\\c \d+|\\v \d+)", src):
        m = re.match(r"\\(c|v) (\d+)", piece)
        if m:
            if m[1] == "c":
                ch, cur = int(m[2]), None
            else:
                cur = (ch, int(m[2]))
                out[cur] = ["", set()]
            continue
        if ch and out and cur in out:
            strongs = set()
            for w in WORD.finditer(piece):
                strongs |= set(STRONG.findall(w[2]))
            text = WORD.sub(lambda w: w[1], piece)
            text = MARKER.sub(" ", text)
            out[cur][0] += " " + text
            out[cur][1] |= strongs
    return {k: (re.sub(r"\s+", " ", t).strip(), s) for k, (t, s) in out.items()}


def _refs(s):
    """'Exo.8:1-4' -> [(book, 8, 1)..(book, 8, 4)]; 'Num.25:19; 26:1' -> two refs."""
    m = re.match(r"(\w+)\.(.*)$", s.strip())
    if not m or m[1] not in TV_BOOK:
        return []
    book, out, ch = TV_BOOK[m[1]], [], None
    for part in m[2].split(";"):
        part = part.strip()
        mm = re.match(r"(?:(\d+):)?(\d+)(?:\.\d+)?(?:-(\d+))?$", part)
        if not mm:
            return []
        ch = int(mm[1]) if mm[1] else ch
        a = int(mm[2])
        z = int(mm[3]) if mm[3] else a
        out += [(book, ch, v) for v in range(a, z + 1)]
    return out


def verse_map():
    lines = open(TVTMS[0], encoding="utf-8").read().split("\n")
    s = next(i for i, l in enumerate(lines) if l.startswith("#DataStart(Condensed)"))
    e = next(i for i, l in enumerate(lines) if l.startswith("#DataEnd(Condensed)"))
    out, on = {}, False
    for line in lines[s:e]:
        c = line.split("\t")
        if c[0].startswith("$"):
            on = c[0][1:4] in TV_BOOK
            continue
        if not on or len(c) < 3 or c[0].startswith("TEST") or c[2] == "NoVerse":
            continue
        eng, heb = _refs(c[1]), _refs(c[2])
        if not eng or not heb or eng == heb:
            continue
        if len(eng) == len(heb):
            pairs = zip(heb, eng)
        elif len(eng) == 1:                      # one English verse = several Hebrew verses
            pairs = ((h, eng[0]) for h in heb)
        else:
            continue
        for h, en in pairs:
            if h != en:
                out[h] = en
    return out


def english(books):
    vm = verse_map()
    out = {}
    for book in books:
        web = _usfm(book)
        heb_keys = {(book, ch, v): (book, ch, v) for (ch, v) in web}   # identity unless remapped
        heb_keys.update({h: en for h, en in vm.items() if h[0] == book})
        for h, en in heb_keys.items():
            if (en[1], en[2]) in web:
                text, strongs = web[(en[1], en[2])]
                out[h] = {"en": text, "en_ref": f"{en[0]}.{en[1]}.{en[2]}", "strongs": strongs}
    return out

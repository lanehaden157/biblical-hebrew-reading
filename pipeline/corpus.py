"""
Single corpus loader. Reads OSHB (sources/morphhb/wlc/*.xml) and yields one dict per
READ token. Everything downstream reads this; nothing else parses the XML.

    python pipeline/corpus.py     # writes build/tokens.jsonl (gitignored, regenerable)

Token fields
  id         OSHB word id (for a qere word: the qere word's own id)
  book ch v pos   reference; pos = 0-based index among read tokens in the verse
  ref        "Gen.1.1"
  surface    pointed word with morpheme slashes removed; Hebrew text copied verbatim
  parts      [{text, lemma, morph}] one per morpheme; lemma is the OSHB lemma part
             (Strong's number, optional augment letter, e.g. "3885 b"; prefix parts
             carry the prefix letter, e.g. "c", "d", "b")
  lang       "H" or "A" (language field of the morph tag)
  morph      raw morph string as in OSHB, e.g. "HC/Vqw3ms"
  lemma      raw lemma string, e.g. "c/559"
  ketiv      written (ketiv) surface if this token is a qere reading, else null
  ketiv_ids  OSHB ids of the written word(s) replaced by this qere token
  qere_of    same as ketiv_ids; kept as a short alias for filters
  read       True for every emitted token EXCEPT ketiv-wela-qere words (written, but the
             qere says "do not read"), which are emitted with read=False
  maqqef_next  True if a maqqef joins this token to the next
  sof_pasuq  True if verse-final
  marks      list of "paseq" | "pe" | "samekh" | "reversed_nun" | "large" | "small" | "suspended"
             attached after this token
  accents    list of codepoints (hex strings) of cantillation marks U+0591-U+05AF in surface
  poem       True if inside a span of corpus_config.json "poems"

Hebrew is never normalised (no NFC/NFD).
"""
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WLC = os.path.join(ROOT, "sources", "morphhb", "wlc")
CONFIG = os.path.join(ROOT, "pipeline", "corpus_config.json")
OUT = os.path.join(ROOT, "build", "tokens.jsonl")

NS = "{http://www.bibletechnologies.net/2003/OSIS/namespace}"
MARKS = {"x-paseq": "paseq", "x-pe": "pe", "x-samekh": "samekh", "x-reversednun": "reversed_nun",
         "x-large": "large", "x-small": "small", "x-suspended": "suspended"}
MAQQEF = "־"
ACCENT = re.compile("[֑-֯]")


def load_config():
    with open(CONFIG, encoding="utf-8") as f:
        return json.load(f)


def _word(el):
    return {"id": el.get("id"), "text": "".join(el.itertext()), "lemma": el.get("lemma") or "",
            "morph": el.get("morph") or "", "maqqef_next": False, "marks": [],
            "ketiv": None, "ketiv_ids": [], "read": True}


def _plain(s):
    return s.replace("/", "").replace(MAQQEF, "").replace(" ", "")


def _apply_variant(entries, note):
    """Apply a ketiv/qere note to the preceding entries (modifies list in place)."""
    cw = note.find(NS + "catchWord")
    rdg = note.find(NS + "rdg")
    if cw is None or rdg is None or rdg.get("type") != "x-qere":
        return
    want = _plain("".join(cw.itertext()))
    k = None
    for n in range(1, min(4, len(entries)) + 1):
        if _plain("".join(e["text"] for e in entries[-n:])) == want:
            k = n
            break
    if k is None:
        raise ValueError(f"qere catchWord {want!r} does not match preceding words")
    ketiv = entries[-k:]
    del entries[-k:]
    ids = [e["id"] for e in ketiv]
    ketiv_text = MAQQEF.join(e["text"].replace("/", "") for e in ketiv)
    q = []
    for ch in rdg:
        if ch.tag == NS + "w":
            q.append(_word(ch))
        elif ch.tag == NS + "seg" and ch.get("type") == "x-maqqef" and q:
            q[-1]["maqqef_next"] = True
    if not q:                       # ketiv wela qere: written, not read
        for e in ketiv:
            e["read"] = False
            e["ketiv_ids"] = ids
        entries.extend(ketiv)
        return
    for w in q:
        w["ketiv"] = ketiv_text
        w["ketiv_ids"] = ids
    q[-1]["maqqef_next"] = q[-1]["maqqef_next"] or ketiv[-1]["maqqef_next"]
    entries.extend(q)


def _is_suffix(m):
    return len(m) > 1 and m[0] == "S" and m[1] in "pdhn"


def _parts(e):
    """Split into morphemes. Text and morph parts always align 1:1 (checked in verify).
    Lemmas: usually one per non-suffix morpheme (suffix gets ""); a few preposition+suffix
    forms (e.g. b/2004) give the suffix its own lemma, so the lemma list may equal the
    full morph list. Anything else is left unaligned and reported by verify_corpus."""
    lang, body = e["morph"][:1], e["morph"][1:]
    mparts = body.split("/") if body else []
    lparts = e["lemma"].split("/") if e["lemma"] else []
    tparts = e["text"].split("/")
    if len(lparts) == len(mparts):
        lem = lparts
    else:
        nonsuf = [i for i, m in enumerate(mparts) if not _is_suffix(m)]
        if len(lparts) == len(nonsuf):
            lem = [""] * len(mparts)
            for i, l in zip(nonsuf, lparts):
                lem[i] = l
        else:
            lem = [""] * len(mparts)
    return lang, [{"text": t, "lemma": l, "morph": m} for t, l, m in zip(tparts, lem, mparts)]


def _in_poem(poems, book, ch, v):
    for b, c1, v1, c2, v2 in poems:
        if b == book and (c1, v1) <= (ch, v) <= (c2, v2):
            return True
    return False


def load_tokens(books=None):
    cfg = load_config()
    books = books or cfg["books"]
    for book in books:
        tree = ET.parse(os.path.join(WLC, book + ".xml"))
        for verse in tree.iter(NS + "verse"):
            osis = verse.get("osisID")
            b, ch, v = osis.split(".")
            ch, v = int(ch), int(v)
            entries = []
            for el in verse:
                if el.tag == NS + "w":
                    entries.append(_word(el))
                elif el.tag == NS + "seg" and entries:
                    t = el.get("type")
                    if t == "x-maqqef":
                        entries[-1]["maqqef_next"] = True
                    elif t == "x-sof-pasuq":
                        entries[-1]["sof_pasuq"] = True
                    elif t in MARKS:
                        entries[-1]["marks"].append(MARKS[t])
                elif el.tag == NS + "note" and el.get("type") == "variant":
                    _apply_variant(entries, el)
            poem = _in_poem(cfg["poems"], b, ch, v)
            pos = 0
            for e in entries:
                lang, parts = _parts(e)
                surface = e["text"].replace("/", "")
                yield {
                    "id": e["id"], "book": b, "ch": ch, "v": v, "pos": pos,
                    "ref": osis, "surface": surface, "parts": parts, "lang": lang,
                    "morph": e["morph"], "lemma": e["lemma"],
                    "ketiv": e["ketiv"], "ketiv_ids": e["ketiv_ids"],
                    "read": e["read"], "maqqef_next": e["maqqef_next"],
                    "sof_pasuq": e.get("sof_pasuq", False), "marks": e["marks"],
                    "accents": [f"{ord(c):04x}" for c in ACCENT.findall(surface)],
                    "poem": poem,
                }
                if e["read"]:
                    pos += 1


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    n = 0
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        for t in load_tokens():
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
            n += 1
    print(f"wrote {n} tokens to {OUT}")


if __name__ == "__main__":
    sys.exit(main())

"""
Reader text: one JSON file per chapter, every corpus verse (poems included but flagged).

    python -X utf8 pipeline/build_text.py      # -> data/text/<Book>/<ch>.json, data/text/index.json

Token fields
  id   OSHB id          s   surface (verbatim corpus Hebrew)     tr  transliteration (translit.py)
  p    [[text, lemma, morph], ...] one per morpheme
  g    English gloss for this occurrence      gs  gloss source      gr  reviewed by Lane (0/1)
  sense  TBESH sense key TAHOT assigns (e.g. "H1121G"), when aligned
  q    1 if parse-quarantined (M13)           k   ketiv surface when the token is a qere reading
Verse fields: v, en (WEB), enref (only when the English verse number differs), poem (1 if poem)

Gloss precedence: glosses/tokens.json override (per-occurrence curation) > TAHOT word gloss
(contextual, e.g. "and he said") > TBESH lemma gloss > curated lemma gloss. The divine name
renders "YHWH (the LORD)" (SPEC Q3).
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corpus    # noqa: E402
import lexicon   # noqa: E402
import tahot     # noqa: E402
import translit  # noqa: E402
import web       # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "text")
GLOSSES = os.path.join(ROOT, "glosses")
QUAR = os.path.join(ROOT, "data", "parse_quarantine.json")
DIVINE = ("3068", "3069")
DIVINE_GLOSS = "YHWH (the LORD)"


def load_json(path, default):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else default


def divine_gloss(g):
    return re.sub(r"\b(Yahweh|LORD|GOD)\b", DIVINE_GLOSS, g)


def question_gloss(g):
    """TAHOT opens a question with a Spanish-style mark ("¿ not"); show it as "not?" instead."""
    if "¿" not in g:
        return g
    g = re.sub(r"¿\s*", "", g).strip()
    return g[:-1] + "?-" if g.endswith("-") else g + "?"


def token_gloss(t, tah, lm, tb, curated_lemmas, overrides):
    """(gloss, source, reviewed, sense) for one token."""
    if t["id"] in overrides:
        o = overrides[t["id"]]
        return o["gloss"], o["source"], int(o.get("reviewed", False)), None
    tg = tah.get(t["id"])
    sense = tg["dstrong"] if tg else None
    main = lexicon.main_part(t)
    lem = main["lemma"] if main else None
    if any((p["lemma"] or "").split(" ")[0] in DIVINE for p in t["parts"]):
        return (question_gloss(divine_gloss(tg["g"])) if tg else DIVINE_GLOSS), "SPEC Q3", 1, sense
    if tg:
        return question_gloss(tg["g"]), "TAHOT", 0, sense
    if lem and lem in lm and lm[lem]["key"] in tb:
        return tb[lm[lem]["key"]]["gloss"], "TBESH", 0, None
    num = "H%04d" % int(lem.split(" ")[0]) if lem else None
    plain = next((k for k in (num, num + "G", num + "A") if k in tb), None) if num else None
    if plain:                                  # unaligned rare word: TBESH by plain Strong's number
        return tb[plain]["gloss"], "TBESH", 0, None
    if lem and lem in curated_lemmas:
        return curated_lemmas[lem]["gloss"], curated_lemmas[lem]["source"], 0, None
    return "", "none", 0, None


def build():
    t0 = time.time()
    cfg = corpus.load_config()
    tokens = list(corpus.load_tokens())
    table = translit.build_stress_table(tokens)
    tah = tahot.glosses(tokens)
    tb = lexicon.tbesh()
    lm = lexicon.lemma_map(tokens, tah)
    eng = web.english(cfg["books"])
    quar = {q["id"] for q in load_json(QUAR, {"tokens": []})["tokens"]}
    curated_lemmas = load_json(os.path.join(GLOSSES, "lemmas.json"), {})
    overrides = load_json(os.path.join(GLOSSES, "tokens.json"), {})
    overrides = {k: v for k, v in overrides.items() if not k.startswith("_")}

    chapters = {}
    for t in tokens:
        if not t["read"]:
            continue
        ch = chapters.setdefault((t["book"], t["ch"]), {})
        verse = ch.setdefault(t["v"], {"v": t["v"], "tokens": []})
        tr = translit.translit_token(t, table)["text"] + ("-" if t["maqqef_next"] else "")
        g, gs, gr, sense = token_gloss(t, tah, lm, tb, curated_lemmas, overrides)
        tok = {"id": t["id"], "s": t["surface"], "tr": tr,
               "p": [[p["text"], p["lemma"], p["morph"]] for p in t["parts"]],
               "g": g, "gs": gs, "gr": gr}
        if sense:
            tok["sense"] = sense
        if t["id"] in quar:
            tok["q"] = 1
        if t["ketiv"]:
            tok["k"] = t["ketiv"]
        if t["poem"]:
            verse["poem"] = 1
        verse["tokens"].append(tok)

    index = {}
    for (book, c), verses in chapters.items():
        out = []
        for v in sorted(verses):
            vv = verses[v]
            e = eng.get((book, c, v))
            vv["en"] = e["en"] if e else ""
            if e and e["en_ref"] != f"{book}.{c}.{v}":
                vv["enref"] = e["en_ref"]
            out.append(vv)
        os.makedirs(os.path.join(OUT, book), exist_ok=True)
        with open(os.path.join(OUT, book, f"{c}.json"), "w", encoding="utf-8") as f:
            json.dump({"book": book, "ch": c, "verses": out}, f, ensure_ascii=False, separators=(",", ":"))
        index.setdefault(book, {})[c] = len(out)
    index = {b: index[b] for b in cfg["books"]}
    with open(os.path.join(OUT, "index.json"), "w", encoding="utf-8") as f:
        json.dump({"_note": "Generated by pipeline/build_text.py. book -> chapter -> verse count.",
                   "books": index}, f, ensure_ascii=False, indent=1)
    print(f"{len(chapters)} chapters, {sum(len(v) for v in chapters.values())} verses "
          f"[{time.time() - t0:.1f}s]")


if __name__ == "__main__":
    build()

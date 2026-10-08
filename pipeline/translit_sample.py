"""Random spot-check list for Lane: python -X utf8 pipeline/translit_sample.py [N] [SEED]
Writes build/translit_spotcheck.md (ref, pointed word, transliteration)."""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corpus      # noqa: E402
import translit    # noqa: E402

n = int(sys.argv[1]) if len(sys.argv) > 1 else 50
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
tokens = [t for t in corpus.load_tokens() if t["read"] and not t["poem"]]
table = translit.build_stress_table(tokens)
rng = random.Random(seed)
seen, rows = set(), []
for t in rng.sample(tokens, len(tokens)):
    r = translit.translit_token(t, table)
    if r["text"] in seen:
        continue
    seen.add(r["text"])
    rows.append((t["ref"].replace(".", " ", 1), t["surface"], r["text"] + ("-" if t["maqqef_next"] else "")))
    if len(rows) == n:
        break
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "build",
                   "translit_spotcheck.md")
with open(out, "w", encoding="utf-8") as f:
    f.write(f"# Transliteration spot-check ({n} random words, seed {seed})\n\n"
            "Acute = stress when not on the last syllable. Trailing - = maqqef (unstressed).\n"
            "Mark any that sound wrong.\n\n| # | Ref | Hebrew | Translit |\n|---|---|---|---|\n")
    for i, (ref, heb, tr) in enumerate(rows, 1):
        f.write(f"| {i} | {ref} | {heb} | {tr} |\n")
print(out)

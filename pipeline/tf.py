"""Minimal Text-Fabric feature reader (node -> value) for the pinned BHSA files."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TF_DIR = os.path.join(ROOT, "sources", "bhsa", "tf", "c")
_SPEC = re.compile(r"[\d,\-]+")


def read_feature(name, edge=False):
    """Return {node: value}. Implicit node numbering continues after the last explicit one;
    a blank line is an empty value, not a skipped node."""
    out, cur, in_header = {}, 0, True
    with open(os.path.join(TF_DIR, name + ".tf"), encoding="utf-8") as f:
        for line in f:
            if in_header:
                if line.startswith("@"):
                    continue
                in_header = False
                if line.strip() == "":      # the blank line that ends the header
                    continue
            line = line.rstrip("\n")
            head, tab, val = line.partition("\t")
            if tab and _SPEC.fullmatch(head):
                for part in head.split(","):
                    a, _, b = part.partition("-")
                    a = int(a)
                    b = int(b) if b else a
                    for k in range(a, b + 1):
                        out[k] = val
                cur = b
                continue
            cur += 1
            out[cur] = line
    return out


def spans(value):
    """'1-5,9' -> [(1,5),(9,9)]"""
    res = []
    for p in value.split(","):
        a, _, b = p.partition("-")
        res.append((int(a), int(b) if b else int(a)))
    return res

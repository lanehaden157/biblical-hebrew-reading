"""
Fetch every upstream source into sources/<name>/ and verify it against
pipeline/sources.lock.json (sha256 per file + licence note).

    python pipeline/fetch_sources.py            # fetch missing files, verify all
    python pipeline/fetch_sources.py --lock     # (re)write the lockfile from what's on disk

Workflow: the first fetch of a new source runs with --lock after you've looked at it
(trust on first use); every later run fails loudly if a byte changed. Sources are
gitignored; the lockfile is committed.

Pins: GitHub sources use a full commit sha (never a branch). morphhb uses an npm version
plus the registry's published sha1. WEB has no versioned URL, so only its sha256 pins it.
"""
import argparse
import hashlib
import io
import json
import os
import sys
import tarfile
import urllib.parse
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "sources")
LOCK = os.path.join(ROOT, "pipeline", "sources.lock.json")

BHSA_FEATURES = [
    "otype", "oslots", "otext", "book", "chapter", "verse",
    "g_word_utf8", "g_cons_utf8", "trailer_utf8", "qere_utf8", "qere_trailer_utf8",
    "lex", "lex_utf8", "g_lex_utf8", "language", "sp", "pdp", "vs", "vt",
    "ps", "gn", "nu", "st", "prs", "prs_ps", "prs_gn", "prs_nu", "gloss",
]

SOURCES = {
    "morphhb": {
        "kind": "npm",
        "version": "2.0.2",
        "url": "https://registry.npmjs.org/morphhb/-/morphhb-2.0.2.tgz",
        "sha1": "2ea8c8adc94ff7bd1b3ac3fdbcfd1a489a4c145a",
        "keep_prefix": "package/",
        "keep": ["wlc/", "LICENSE.md", "readme.md", "package.json"],
        "licence": "Text: WLC, public domain. Lemma and morphology: CC BY 4.0 (OpenScriptures). See LICENSE.md.",
    },
    "hebrew_lexicon": {
        "kind": "github",
        "repo": "openscriptures/HebrewLexicon",
        "commit": "21c9add13bc727d3a951361778e97e3ff7afd1ce",
        "files": ["AugIndex.xml", "LexicalIndex.xml", "HebrewStrong.xml",
                  "BrownDriverBriggs.xml", "readme.md"],
        "licence": "Strong's: public domain. BDB parts: public domain; OpenScriptures markup CC BY 4.0. See readme.md.",
    },
    "stepbible": {
        "kind": "github",
        "repo": "STEPBible/STEPBible-Data",
        "commit": "1f3423d42400f59f1f30fe08f74e38fcd3bbf7bc",
        "files": [
            "README.md",
            "Lexicons/TBESH - Translators Brief lexicon of Extended Strongs for Hebrew - STEPBible.org CC BY.txt",
            "Translators Amalgamated OT+NT/TAHOT Gen-Deu - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt",
            "Translators Amalgamated OT+NT/TAHOT Jos-Est - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt",
            "Translators Amalgamated OT+NT/TAHOT Isa-Mal - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt",
            "Versification/TVTMS - Translators Versification Traditions with Methodology for Standardisation for Eng+Heb+Lat+Grk+Others - STEPBible.org CC BY.txt",
        ],
        "licence": "CC BY 4.0 (stated in README.md and in each file name). Attribution: STEPBible.org, Tyndale House Cambridge.",
    },
    "bhsa": {
        "kind": "github",
        "repo": "ETCBC/bhsa",
        "commit": "4db00e2157915495e1a4d3d57e41223df24775da",
        "files": ["README.md"] + [f"tf/c/{f}.tf" for f in BHSA_FEATURES],
        "licence": "Data CC BY-NC 4.0 (README.md; repo LICENSE is MIT for code). Free app only; attribute ETCBC.",
    },
    "web": {
        "kind": "zip",
        "url": "https://ebible.org/Scriptures/eng-web_usfm.zip",
        "licence": "World English Bible: public domain (stated in the USFM headers / copr.htm in the zip).",
        "note": "URL is unversioned; sha256 in the lockfile is the only pin.",
    },
}


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "hebrew-curriculum-fetch"})
    with urllib.request.urlopen(req) as r:
        return r.read()


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def fetch_github(name, s):
    d = os.path.join(SRC, name)
    for rel in s["files"]:
        p = os.path.join(d, *rel.split("/"))
        if os.path.exists(p):
            continue
        url = f"https://raw.githubusercontent.com/{s['repo']}/{s['commit']}/{urllib.parse.quote(rel)}"
        print(f"  GET {rel}")
        write(p, get(url))


def fetch_npm(name, s):
    d = os.path.join(SRC, name)
    if os.path.isdir(os.path.join(d, "wlc")):
        return
    print(f"  GET {s['url']}")
    data = get(s["url"])
    got = hashlib.sha1(data).hexdigest()
    if got != s["sha1"]:
        sys.exit(f"{name}: sha1 mismatch (expected {s['sha1']}, got {got})")
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        for m in tar.getmembers():
            if not m.isfile() or not m.name.startswith(s["keep_prefix"]):
                continue
            rel = m.name[len(s["keep_prefix"]):]
            if any(rel == k or rel.startswith(k) for k in s["keep"]):
                write(os.path.join(d, *rel.split("/")), tar.extractfile(m).read())


def fetch_zip(name, s):
    d = os.path.join(SRC, name)
    if os.path.isdir(d) and os.listdir(d):
        return
    print(f"  GET {s['url']}")
    with zipfile.ZipFile(io.BytesIO(get(s["url"]))) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            write(os.path.join(d, info.filename), z.read(info))


def tree_hashes(name):
    d = os.path.join(SRC, name)
    out = {}
    for base, _, files in os.walk(d):
        for f in files:
            p = os.path.join(base, f)
            with open(p, "rb") as fh:
                out[os.path.relpath(p, d).replace(os.sep, "/")] = sha256(fh.read())
    return dict(sorted(out.items()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lock", action="store_true", help="write lockfile from files on disk")
    args = ap.parse_args()

    for name, s in SOURCES.items():
        print(name)
        {"github": fetch_github, "npm": fetch_npm, "zip": fetch_zip}[s["kind"]](name, s)

    now = {n: tree_hashes(n) for n in SOURCES}
    if args.lock:
        lock = {n: {"pin": {k: v for k, v in s.items() if k in ("version", "repo", "commit", "url", "sha1")},
                    "licence": s["licence"], "files": now[n]} for n, s in SOURCES.items()}
        with open(LOCK, "w", encoding="utf-8", newline="\n") as f:
            json.dump(lock, f, indent=1, sort_keys=True)
            f.write("\n")
        print(f"wrote {LOCK}: " + ", ".join(f"{n}={len(h)} files" for n, h in now.items()))
        return

    if not os.path.exists(LOCK):
        sys.exit("no lockfile; inspect sources/ then run with --lock")
    with open(LOCK, encoding="utf-8") as f:
        lock = json.load(f)
    bad = 0
    for n in SOURCES:
        want, have = lock[n]["files"], now[n]
        for rel in sorted(set(want) | set(have)):
            if want.get(rel) != have.get(rel):
                bad += 1
                print(f"  MISMATCH {n}/{rel}: lock={want.get(rel)} disk={have.get(rel)}")
    if bad:
        sys.exit(f"{bad} file(s) differ from sources.lock.json")
    print("all sources match sources.lock.json")


if __name__ == "__main__":
    main()

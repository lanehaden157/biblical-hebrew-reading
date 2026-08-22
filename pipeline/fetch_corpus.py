"""
Fetch the OSHB corpus (morphhb) and the Strong's Hebrew lexicon (HebrewLexicon)
into pipeline/corpus/. Idempotent: skips download if the expected files are
already present. Delete pipeline/corpus/ to force a re-fetch.

Sources are pinned to a specific npm version / git commit so the corpus we
build against does not silently drift under us.
"""
import io
import os
import tarfile
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS_DIR = os.path.join(HERE, "corpus")
WLC_DIR = os.path.join(CORPUS_DIR, "wlc")
LEXICON_DIR = os.path.join(CORPUS_DIR, "lexicon")

MORPHHB_VERSION = "2.0.2"
MORPHHB_URL = f"https://registry.npmjs.org/morphhb/-/morphhb-{MORPHHB_VERSION}.tgz"

# openscriptures/HebrewLexicon has no version tags; pin to a specific commit
# (checked 2026-08-22) rather than "master" so the fetch is reproducible.
HEBREWLEXICON_COMMIT = "21c9add13bc727d3a951361778e97e3ff7afd1ce"
HEBREWLEXICON_URL = (
    f"https://codeload.github.com/openscriptures/HebrewLexicon/tar.gz/{HEBREWLEXICON_COMMIT}"
)

EXPECTED_BOOK_COUNT = 39  # 39 canonical Protestant OT books, one XML file each


def already_fetched():
    if not os.path.isdir(WLC_DIR):
        return False
    xml_files = [f for f in os.listdir(WLC_DIR) if f.endswith(".xml")]
    if len(xml_files) < EXPECTED_BOOK_COUNT:
        return False
    return os.path.isfile(os.path.join(LEXICON_DIR, "HebrewStrong.xml"))


def fetch_morphhb():
    print(f"Downloading morphhb {MORPHHB_VERSION} ...")
    with urllib.request.urlopen(MORPHHB_URL) as resp:
        data = resp.read()
    print(f"  {len(data) / 1e6:.1f} MB downloaded")
    os.makedirs(WLC_DIR, exist_ok=True)
    n = 0
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        for member in tar.getmembers():
            if not member.isfile():
                continue
            if not member.name.startswith("package/wlc/"):
                continue
            base = os.path.basename(member.name)
            if not base.endswith(".xml") or base == "VerseMap.xml":
                continue
            member.name = base
            tar.extract(member, path=WLC_DIR, filter="data")
            n += 1
    print(f"  extracted {n} book files to {WLC_DIR}")
    if n < EXPECTED_BOOK_COUNT:
        raise RuntimeError(
            f"expected {EXPECTED_BOOK_COUNT} book files, got {n} -- morphhb package layout may have changed"
        )


def fetch_lexicon():
    print(f"Downloading openscriptures/HebrewLexicon @ {HEBREWLEXICON_COMMIT[:10]} ...")
    with urllib.request.urlopen(HEBREWLEXICON_URL) as resp:
        data = resp.read()
    print(f"  {len(data) / 1e6:.1f} MB downloaded")
    os.makedirs(LEXICON_DIR, exist_ok=True)
    found = False
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        for member in tar.getmembers():
            if not member.isfile():
                continue
            if os.path.basename(member.name) == "HebrewStrong.xml":
                member.name = "HebrewStrong.xml"
                tar.extract(member, path=LEXICON_DIR, filter="data")
                found = True
                break
    if not found:
        raise RuntimeError("HebrewStrong.xml not found in HebrewLexicon archive")
    print(f"  extracted HebrewStrong.xml to {LEXICON_DIR}")


def main():
    if already_fetched():
        print("Corpus already present in pipeline/corpus/, skipping download.")
        print("Delete pipeline/corpus/ to force a re-fetch.")
        return
    fetch_morphhb()
    fetch_lexicon()
    print("Done.")


if __name__ == "__main__":
    main()

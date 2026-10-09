"""
Pull Lane's synced progress from the private gist the app writes (app/sync.js) and list reports.

    python -X utf8 pipeline/pull_sync.py

Uses the gh CLI (needs the gist scope). Writes build/progress.json (whole state) and
build/reports.json, then prints each report and the current quarantine.
"""
import json
import os
import subprocess
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE = "hebrew-v1-progress.json"


def gh(path):
    r = subprocess.run(["gh", "api", path], capture_output=True, text=True, encoding="utf8")
    if r.returncode:
        sys.exit(f"gh api {path}: {r.stderr.strip()}")
    return json.loads(r.stdout)


def main():
    gist = next((g for g in gh("gists?per_page=100") if FILE in g["files"]), None)
    if not gist:
        sys.exit(f"No gist with {FILE}. Connect sync in the app's Settings first.")
    f = gh(f"gists/{gist['id']}")["files"][FILE]
    text = urllib.request.urlopen(f["raw_url"]).read().decode("utf8") if f["truncated"] else f["content"]
    s = json.loads(text)
    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    for name, obj in (("progress.json", s), ("reports.json", s.get("reports", []))):
        with open(os.path.join(ROOT, "build", name), "w", encoding="utf8") as out:
            json.dump(obj, out, ensure_ascii=False, indent=1)
    print(f"gist {gist['id']}, saved {s.get('savedAt', '?')}, {len(s.get('cards', {}))} cards, "
          f"{len(s.get('sessions', []))} sessions")
    reps = s.get("reports", [])
    print(f"\n{len(reps)} reports:")
    for r in reps:
        note = f"  \"{r['note']}\"" if r.get("note") else ""
        print(f"  {r['t'][:16]}  {r['id']}  ({r['kind']})  {r['reason']}{note}")
    print(f"\nquarantined now: {', '.join(s.get('quarantine', [])) or 'none'}")


if __name__ == "__main__":
    main()

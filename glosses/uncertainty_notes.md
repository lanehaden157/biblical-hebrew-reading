# Gloss curation — flagged for later double-check

Running list of curated glosses where the call was inferred/judgment rather
than confirmed against a source beyond my own knowledge + the local Strong's
draft. All items below have now been checked and resolved (2026-08-22) by
fetching `BrownDriverBriggs.xml` from the same already-pinned HebrewLexicon
commit used by `pipeline/fetch_corpus.py` (not committed — matches
`.gitignore`'s `pipeline/corpus/` exclusion) and reading the actual BDB
entries + Strong's `source`/`meaning` fields directly. No web search used.

## Resolved
- **H1768**, **H4430** — Aramaic tag. Checked the lexicon's own `<source>`
  field directly (`H1768: "(Aramaic) apparently for 1668"`, `H4430:
  "(Aramaic) corresponding to 4428"`) — confirmed, not inferred.
- **H905** (bad, batch_201_300) — was "part, portion, alone". BDB splits בד
  into three separate Strong's numbers: H905 (part/separation/bar), H906
  (linen), H907 (lie/brag) — so "linen" was never in scope for H905 as
  feared, but H905 itself explicitly includes "bar, pole (for carrying)"
  (the tabernacle/ark-pole sense), which was missing entirely. Corrected to
  "part, portion; bar, pole (for carrying); alone, apart" and
  `glosses/batch_201_300.json` regenerated.
- **H352** (ayil, batch_201_300) — was "ram; chief, leader". BDB lists this
  Strong's number as covering 4 homographs of one root ("strength"): ram,
  pilaster/pillar, leader/chief, terebinth. Added the pillar/pilaster sense
  (real, moderately common architectural term); left out terebinth, which
  BDB itself marks uncertain and rare. Corrected to "ram; pillar, pilaster;
  leader, chief" and `glosses/batch_201_300.json` regenerated.

No open items remain. Format going forward: one bullet per flagged lemma,
per batch, added at curation time — not reconstructed after the fact.

# Session summary 2026-10-08 (sync)

- Lane asked for automatic sync of progress and reports; chose private-gist sync over issues or share-sheet.
- Built `app/sync.js` (savedAt compare: pull / push / ask on conflict), Settings section, `pipeline/pull_sync.py`. verify_app passes; two-device simulation passes; not run against real GitHub.
- Takeaway: the old v0 sync was rate-limited by pushing every few seconds; this one syncs on open and session end only.
- Open: Lane connects a token on his phone and confirms; then a reports -> apply_review.py converter.
- Follow-ups: Settings rendered sync section and reported-items list as raw text (arrays passed to replaceChildren; fixed). sw.js now revalidates (Pages' 10-min HTTP cache served stale files). Wait for the Pages deploy before telling Lane to check.
- Sync confirmed live: gist bfcce068..., pull_sync.py read Lane's 2 reports (D:01GYp, D:32wMq, translit/English formatting).
- Lane's 2 reports (pre-dedouble items, since removed): fixed trailing maqqef dash on solo words (gave away decode answers) and TAHOT "¿" glosses. Open: decode notes show TAHOT contextual glosses that can read oddly alone ("more than two plus").
- Fixed 7 odd Unit 0 decode notes via glosses/tokens.json overrides (Tubal- left; solo() already shows 'Tubal').
- L0.8 look-alike lesson showed raw refs/code: typed-translit regex swallowed following refs; backtick (ayin) triggered code spans. Fixed + gate.

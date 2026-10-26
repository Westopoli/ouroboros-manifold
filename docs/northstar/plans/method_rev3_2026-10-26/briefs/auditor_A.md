# Brief: auditor A, validity (Phase 3)

Model: claude-sonnet-5-5 (engineer). No sub-agents. Terse thinking, one final report, first line `RESULT success|stop:<reason>`. Read-only: edit nothing, commit nothing. Worktree on origin/main after Phase 2 (your launcher names it); never the live checkout. You have not seen the author's reasoning; do not look for it (no memory files, no chat transcripts).

Under audit: `scripts/specfactory/method_metrics*.py`, `method_thresholds.toml`, `tests/specfactory/test_method_metrics.py` and its fixtures, against `docs/northstar/plans/method_rev3_2026-10-26/spec.md` ("The gaps") and `docs/northstar/plans/retro_2026-10-24/method_cost.md`.

For every metric M01 to M24, try to refute:
1. Validity: does the number measure the effect the gap's fix claims? Name a case where the behaviour continues and the metric still passes (tests committed under `tests/fixtures/`, docs under a `data/` folder, a landing with no gate row, a spawn with no piece id, a retro folder added to launder method edits, a `phase` flip).
2. The baseline: is the W43 value in `method_thresholds.toml` and `metrics/2026-W43.json` the number `method_cost.md` gives, in the same sense?
3. The threshold: is it a number somebody gave (the spec names a source or marks DRAFT) or one nobody gave?
4. The positive control: does the known-bad fixture fail for the reason the gap names, or for an unrelated reason?
Report once, under 60 lines, schema: `FINDINGS` list, each `<id> | <metric> | <claim> | <evidence: file:line or command and its output, two lines max> | <severity high|medium|low>`; then `HOLDS` (metrics you could not refute, ids only); `RESULT`.

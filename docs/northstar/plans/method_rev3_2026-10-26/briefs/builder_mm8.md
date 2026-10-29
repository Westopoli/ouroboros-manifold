# Brief: builder, HARNESS-mm-8 metrics correctness (Phase 4)

Model: claude-sonnet-5-5 (doer). No sub-agents. Terse thinking, one final report, first line `RESULT success|stop:<reason>`. Worktree named by your launcher, based on origin/push/mm-8-9-tests; never the live checkout. Push `push/mm-8` and stop; never push main. Python: `/home/westopoli/Projects/om-push/venv-sdk/bin/python`. Never edit anything under `tests/`; a wrong test is `RESULT stop:test-defect` with the line that proves it.

Spec: `docs/northstar/plans/method_rev3_2026-10-26/audit_findings.md` "Change" column for findings 1, 3 to 23, 25 to 27, 32 to 35, spec.md Amendment A9, and the tests on your base (`tests/specfactory/test_method_metrics.py`, cases 1, 3 to 19, 21 to 24 of the tests-writer brief). Files you may edit: `scripts/specfactory/method_metrics.py`, `method_metrics_runs.py`, `method_metrics_cli.py`, `method_thresholds.toml`. Points the tests do not fix:
- One `judge` (the `method_metrics.py` one; `method_metrics_runs.py` imports it).
- `--project <slug>` default `-home-westopoli-Projects-ouroboros-manifold`; `--transcripts` stays as the root.
- `[prices]` per model id prefix (`claude-fable-5-1`, `claude-opus-5-5`, `claude-sonnet-5-5`, `claude-haiku-5-5`): input, cache_read, cache_write, output in dollars per million tokens, from the current Anthropic pricing page (WebFetch), with the date in a comment. Cost of a transcript run = usage × price.
- Baselines in the toml: M04 7.26 (comment: lab phase, 334 over 46), M08 1229 (manifold only), M19a 0 (comment: 182 untagged before the date).
- `--weeks A..B` prints the back-test table and judges nothing; `--write` unchanged; JSON gains `phase`.
- Detail lines capped at 400 characters; `--verbose` prints the full list under the line.
- Remove `--baseline`.
Run `scripts/specfactory/pre_gate.sh` before the push. Report: sha, pytest counts for the three test files, the W43 line set from `method_metrics.py --week 2026-W43` (METRIC lines only), `RESULT`.

# Brief: auditor B, engineering (Phase 3)

Model: claude-sonnet-5-5 (engineer). No sub-agents. Terse thinking, one final report, first line `RESULT success|stop:<reason>`. You may edit files only inside your own worktree and must commit nothing and push nothing; the worktree is discarded. Worktree on origin/main after Phase 2 (your launcher names it); never the live checkout. You have not seen the author's reasoning; do not look for it (no memory files, no chat transcripts). Never let one tool result exceed about 500 KB.

Under audit: `scripts/specfactory/method_metrics*.py`, `method_thresholds.toml`, `merge_gate.sh` (the `GATE row` line), `sdk_engineer.py` (the run row), `tests/specfactory/test_method_metrics.py`, `test_gate_row.py`, `test_sdk_runs.py`, against `docs/northstar/plans/method_rev3_2026-10-26/spec.md`.

Do, in order, and record the command and the decisive output line for each:
1. Run the suite: `python3 -m pytest tests/specfactory/test_method_metrics.py tests/specfactory/test_gate_row.py tests/specfactory/test_sdk_runs.py -q`. Counts.
2. Make the bad week pass: edit only `method_metrics*.py` (not the tests, not the fixtures, not the snapshot) so that `method_metrics.py --week 2026-W43` exits 0, with the smallest edit you can find. Does the self-check test catch it? Which metrics could you silence without a test going red?
3. Make a good week fail: build a legitimate week in a scratch repo (a retro week with one retro-folder commit and four method-text commits; an idle week with no commits and no spawns; a week with one landing; a week with no transcripts). Which metrics FAIL where the spec says NA or PASS?
4. Real data: run the transcript metrics (M06, M08, M13, M14, M22) against one real session under `~/.claude/projects/-home-westopoli-Projects-ouroboros-manifold/` and its `subagents/`; does the parser read the `.meta.json` fields and the `usage` totals the spec names? Run the gate-row parser against a real log under `/var/tmp/om-push/`; are the stage seconds and the reject causes right?
5. Numbers: for M04, M06, M09, M18, M19 recompute W43 by hand from the records (`method_cost.md` names the commands) and compare with `metrics/2026-W43.json`.
Report once, under 60 lines, schema: `FINDINGS` list, each `<id> | <metric or file> | <claim> | <command and decisive output, two lines max> | <severity high|medium|low>`; `HOLDS` (ids that resisted you); `RESULT`.

# Brief: landing clerk, method rev 3 (Phase 2). One copy per landing; the launcher fills BRANCH and PIECES.

BRANCH: <push/...>   PIECES: <ids>

Model: claude-sonnet-5-5 (engineer). No sub-agents. Terse thinking, one final report, first line `RESULT success|stop:<reason>`. Procedure: the landing template (`docs/northstar/plans/workflows_2026-10-07/` landing steps as the Dispatcher's HANDOFF names them; the copy at `~/Projects/om-push/wt/land-wtcap/landing-template.md` is current), with these additions for rev 3:
- A test-defect stop from a builder (`RESULT stop:test-defect`): rule it yourself with the rulebook (`rules.md`); if the test is wrong, fix the test, write the ledger row with `ruler=clerk`; if the test is right, send the builder's branch back with the line that proves it. Only new rule meaning goes to the Architect (`ruler=fable`).
- Rerun the gate at most once on your own; a second failure is reported with the decisive line, not retried.
- One ledger row per landing, written by you, carrying every `FINDING-` with `found-by=` and every `TD-` with `ruler=`.
- After HARNESS-mm-2 is on main: append the gate's `GATE row` line to `docs/northstar/plans/push/gate_runs.csv` in the records commit.
- Attach flip in `pieces.toml` (`status = { state = "attached", attach_sha = "<sha>" }`), `status_check.py` and `owner_lint.py` clean, `pre_gate.sh` before the lock. Gate lock `~/Projects/om-push/gate.lock` with `flock -w 1800`; `df -m /tmp` under 9500 MB used before starting. Push main only with no `GATE ... REJECT` outside the known-red lists. `wt.py done <path> <sha>` after the push.
Report: the sha on main, the gate verdict lines (one per stage that was not OK), the ledger row id, the pytest counts of the landed tree, `RESULT`.

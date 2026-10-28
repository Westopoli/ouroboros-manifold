# Brief: tests writer, HARNESS-mm-12 token ledger and metrics M25 to M29

Model: claude-sonnet-5-5 (engineer). No sub-agents. Terse thinking, one final report, first line `RESULT success|stop:<reason>`. STOP at 60 calls; one fix pass at most, a second is `RESULT stop:fix-pass-cap`. Worktree named by your launcher, from origin/main; never the live checkout. Push `push/mm-12-tests` and stop; never push main. Python: `/home/westopoli/Projects/om-push/venv-sdk/bin/python`.

Read spec.md Amendment A10 and `decisions.md` rows DEC-daily-allotment-2026-10-27, DEC-coordinator-wakeups-2026-10-27, DEC-thresholds-approved-2026-10-28. Write `tests/specfactory/test_token_ledger.py` (new) with its own fixtures under `tests/specfactory/fixtures/token_ledger/` (synthetic transcripts in the same jsonl shape as `tests/specfactory/fixtures/method_metrics/mm_world.py` builds; reuse its builders by import). Each case names the A10 item in a comment, red on origin/main for the stated reason (script missing, metric missing, field unapproved), the failing assertion line pasted in your report:
1. `token_ledger.py --day 2026-11-02 --plan <csv>` with a plan file (columns `date,piece,role,estimate_m`) and a transcripts root: prints one row per planned piece with planned, actual (input + cache read + cache creation + output, cache reads at face value, millions), and over or under; one row `unplanned` summing runs whose description does not match a plan row; one row `coordinator` for top-level sessions.
2. `--week 2026-W45` prints the week's total against the allotment (300 M a day, five working days plus the weekend taper of zero: 1,500 M) and the split (Dispatcher 60, pieces 180, reserve 60 per day).
3. `method_thresholds.toml` has an `[estimates]` table per task type (`tests`, `build`, `land`, `records`, `audit`, `research`, `drift`), each with `median_m`, `ceiling_m`, `calls_cap`; values: tests 3.8 / 16 / 60, build 1.2 / 6.3 / 40, land 1.6 / 5.5 / 40, records 0.2 / 1.2 / 15, audit 4.7 / 13.8 / 60, research 1.4 / 6.4 / 30, drift 10.9 / 15 / 70.
4. M25: a landed piece whose runs total more than the sum of its roles' ceilings is FAIL; under it, PASS.
5. M26: the week total against the allotment prints NA (report only) with both numbers.
6. M27: in a Dispatcher transcript (top-level, Sonnet, with Agent tool_use), text-only assistant turns that follow a task-notification or a cross-session message, divided by such events; 3 of 10 is FAIL at the limit 0.1, 1 of 10 is PASS.
7. M28: SendMessage tool_use per top-level session per day, max over the week; 5 is FAIL at the limit 4.
8. M29: runs per piece with role `tests` beyond the first; 2 extra is FAIL at limit 1.
9. M06 and M07 include top-level session usage priced by model: a fixture week with a Fable top-level session and a Sonnet sub-agent gives a Fable share above 0.
10. `method_metrics.py` `METHOD_PATHS` contains `scripts/specfactory/workflows/`; a commit touching only a file there counts as method text for M24a.
11. Every table in `method_thresholds.toml` with an `approved` key reads `Westley 2026-10-28`; M21b `value` is 8; M01 `value` is 1.5; an approved metric within its limit prints PASS, not DRAFT.
Keep existing tests green. Report: branch sha, the 11 failing assertion lines, pytest counts, `RESULT`.

# Brief: tests writer, HARNESS-mm-8 and HARNESS-mm-9 (Phase 4)

Model: claude-sonnet-5-5 (engineer). No sub-agents. Terse thinking, one final report, first line `RESULT success|stop:<reason>`. Worktree named by your launcher, from origin/main; never the live checkout. Push your branch `push/mm-8-9-tests` and stop; never push main. Python for pytest: `/home/westopoli/Projects/om-push/venv-sdk/bin/python`.

Read `docs/northstar/plans/method_rev3_2026-10-26/audit_findings.md` (findings 1 to 35, "Change" column) and spec.md Amendment A9. Write the failing tests for the changes; each test names its finding in a comment. Edit only `tests/specfactory/test_method_metrics.py`, `tests/specfactory/fixtures/method_metrics/mm_world.py`, `tests/specfactory/test_gate_row.py`, `tests/specfactory/test_sdk_runs.py`. Required cases (red on origin/main for the stated reason, assertion line pasted in your report):
1. Finding 1: the fixture world's gate csv header equals the header `merge_gate.sh` writes (`date,label,branch,base_sha,candidate_sha,...`), and a world with one rc-0 row on main gives M19c PASS/DRAFT, not a traceback.
2. Finding 2: `test_gate_row.py`: a gate run with `PIECE_ID=A,B,C` writes a row that `csv.reader` parses to exactly 14 fields with label `A,B,C`.
3. Finding 4: a runs-side metric (M08) with an unapproved threshold and a failing value prints FAIL and the CLI exits 1.
4. Finding 3 and 35: the self-check runs `method_metrics.py` as a subprocess on the bad fixture world and asserts exit 1 and that M01, M02b, M04, M05b, M11c, M16, M18b, M19c, M24a and M24b are FAIL; `--baseline` is rejected as an unknown argument.
5. Finding 5: with two project folders under the transcripts root, only the folder named by `--project` (default: this repo's slug) is counted by M08.
6. Finding 6: M22 counts a top-level session only when its transcript has an `Agent` or `SendMessage` tool_use in the week or its model is Fable; three worker Sonnet sessions in one hour give 0.
7. Finding 7: M01b flags a `tests` run on a piece whose non-`tests/` owns are all under `scenes/` even when it also owns a `tests/` path.
8. Finding 8: with `[prices]` filled, a Fable transcript run with usage totals gets a nonzero cost and M06 prints a percentage.
9. Finding 9: a spawn described "Fresh audit" is an `unlabelled` run; M14b counts it; a spawn "HARNESS-x audit" on a piece in pieces.toml is parsed.
10. Finding 10: in `lab` phase M10 uses `product_lines + lab_lines` and ignores rows where that sum is 0.
11. Finding 12 and DEC-scripts-tests-not-product: a commit touching only `scripts/foo.py` counts in neither M04 term; DEC-m04-docs-only-week: a week with 3 docs-only commits and 0 product commits is NA.
12. Finding 13 and Q5: M21b counts only breach rules (the list in A9), so 100 `context` DRIFT lines give 0.
13. Finding 14: a file under `tests/specfactory/fixtures/` is excluded from M01 and M23.
14. Finding 15: a `.jsonl` under `docs/northstar/plans/` counts for M11c; a `.png` under `docs/northstar/research/x/data/` or `docs/northstar/story_reviews/` does not.
15. Finding 16: a commit that modifies an old `retro_*` file does not make M11 NA or exempt M24a; an added file does.
16. Finding 17 and 32: M16 reads verdicts from `story_reviews/westley/verdicts_*.md` and `decisions.md` by piece id; M17 counts the rows of the README's Picture table (header starting `| Picture |`).
17. Finding 18: M11b-bytes FAILs on a CLAUDE.md of 19,000 bytes.
18. Finding 21: M15 prints an `unknown` count and FAILs when unknown exceeds 20%.
19. Finding 22: the written JSON carries `phase`.
20. Finding 24: every subprocess in `test_sdk_runs.py` sets `SDK_RUNS_CSV`; add an assertion that the real file's line count is unchanged by the test module.
21. Finding 25: M12c known-bad case (beta phase, 0 stories moved) is FAIL.
22. Finding 26: `blame_rows` on a repo with no ledger returns no rows and the metric is NA.
23. Finding 33: a FAIL line's detail is at most 400 characters without `--verbose`.
24. Back-test: `--weeks 2026-W40..2026-W42` prints a markdown table with one row per metric and one column per week (values only, no judging).
Keep existing green cases green except the ones a finding retires (name them). Report: branch sha, the 24 failing assertion lines, pytest counts (red count, green count), `RESULT`.

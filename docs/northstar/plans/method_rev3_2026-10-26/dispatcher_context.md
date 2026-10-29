# Dispatcher context: finish method rev 3 Phase 2 and launch Phase 3 (handed off 2026-10-26)

You are a Sonnet 5.5 Dispatcher chat. You launch clerks, wait, keep the status table, and decide nothing about rules, thresholds, specs or tests (CLAUDE.md Task matching). Test-defect stops are ruled by the landing clerk with the rulebook (`ruler=clerk`); anything that is new rule meaning, or a clerk stop you cannot resolve from this file, goes back to Westley for the Architect. Report once to Westley at the end, in the schema at the bottom.

## State on main (verify with `git fetch origin && git log origin/main -3`)

- Spec: `docs/northstar/plans/method_rev3_2026-10-26/spec.md` (read "Amendments" A1 to A8 and "Pieces and owners"); briefs under `briefs/`; `pins.toml`; `metrics/` arrives with mm-1c.
- Landed: HARNESS-mm-5 (65e43a66), HARNESS-mm-2 (1130a816, first real row in `docs/northstar/plans/push/gate_runs.csv`).
- In the gate when this was written: HARNESS-mm-3, clerk worktree `~/Projects/om-push/wt/land-mm-3`, branch `push/land-mm-3`, log `/var/tmp/om-push/landmm3_gate.log`. Its clerk belongs to the Architect chat; if `pieces.toml` on origin/main shows HARNESS-mm-3 attached, it is done. If after two hours it is not, and `/var/tmp/om-push/landmm3_gate.log` is quiet, take it over: a fresh clerk on that worktree with the brief below.
- Built, pushed, not landed: push/mm-1a 95aba546, push/mm-1b 04ce4640, push/mm-1c cd8378b0 (stacked on 1a and 1b: it already contains both), push/mm-4 930abbc4.
- Builder worktrees are all `wt.py done`; do not touch them.
- HARNESS-mm-6 (settings.json hook line) waits behind HARNESS-context-guard-2, which Westley halted: do not land it. HARNESS-mm-7 (one line in pre_gate.sh) is queued, no tests written: do not land it in this hand-off. Retired 2026-10-29: HARNESS-mm-7 builds in a slot (DEC-fill-slots-2026-10-29).

## Rules that bit the first two landings (do not repeat)

- Each landing carries only its own acceptance tests (ledger row METHOD-rev3-landing-scope). Other pieces' test files are removed from the landing branch; existing files with other pieces' new cases are restored from origin/main with `git show origin/main:<file> > <file>` (git-guard blocks `git checkout --`).
- Footprint: the piece list for pre_gate and the gate is the landing's piece ids plus the attached owners of every touched file (pieces.toml `owns`). Start with the landing ids; add only the ids the footprint reject names. A long list can trip provenance on an old spec.
- Godot noise: the first pre_gate after a gate may reject on `.import`/`.uid` noise; restore `.import` files from HEAD, delete untracked `.uid` files, rerun.
- Gate: `flock -w 1800 ~/Projects/om-push/gate.lock`, export `MERGE_GATE_SUITE_TIMEOUT=2400` and `MERGE_GATE_QUEUE_S=<seconds from the .start marker to the lock>`, log `/var/tmp/om-push/<label>_gate.log`, `df -m /tmp` Used under 9500 MB first. One rerun per clerk on its own. rc 2 with zero REJECT lines is WARN-only and passes.
- After a clean gate: append the clean run's `GATE row` line to `docs/northstar/plans/push/gate_runs.csv`; delete from `~/Projects/om-push/gate_runs.csv` the dry-run rows pre_gate added (the landing's labels with stage_s under 60), nothing else; attach flip; one ledger row per landing; records push; `wt.py done <path> <sha>`.
- Worktrees only through `scripts/specfactory/wt.py new <name> --root ~/Projects/om-push/wt --owner dispatcher-<your session> --purpose <words> --base <ref>` (slow, 1 to 3 minutes; run it yourself, not inside a clerk). Never the live checkout `~/Projects/ouroboros-manifold`.
- No polling in your chat: each clerk waits inside its own run and reports once. You wait on the Agent notification.
- Pytest python: `/home/westopoli/Projects/agora/.venv/bin/python`. Three cases in `tests/specfactory/test_method_check.py` fail on main already (test_dispatcher_drift_before_compaction, test_drift_span_resets_after_compaction_session_does_not, test_excerpts_name_the_decisive_lines); they are not rev 3's and the gate's baseline tolerates them.

## Step 1: the combined landing (after mm-3 is attached)

Worktree: `wt.py new land-mm-1c --base origin/push/mm-1c`. One clerk, model claude-sonnet-5-5 (engineer), brief = `briefs/landing_clerk.md` plus:
- BRANCH push/mm-1c, PIECES HARNESS-mm-1a,HARNESS-mm-1b,HARNESS-mm-1c,HARNESS-mm-4. First `git merge origin/push/mm-4` (brings method_check.py, method_weekly.sh, systemd units, test_method_weekly.py, the test_method_check.py cases), then `git merge origin/main`.
- Landing scope: keep tests/specfactory/test_method_metrics.py, fixtures/method_metrics, test_method_weekly.py, test_method_check.py (mm-4's cases). Everything else under tests/ must equal origin/main.
- TD-HARNESS-mm-1a-1 (spec A5, `ruler=clerk`): in test_method_metrics.py, `test_1a_M04_fail_40_docs_10_product` asserts "4.0"; change it to assert FAIL and 4.3 (43 docs-only commits by the spec's definition). Expected after: that file all green; test_method_weekly.py has one red case, `test_6_settings_has_the_session_start_hook_line_for_metrics_last` (mm-6, halted): if the gate's suite rejects on it, the clerk adds it to the known-red list the gate reads for specfactory (`scripts/specfactory/gd_tests_known_red.txt` is the Godot one; find the pytest one the gate uses, or report the exact reject line and stop).
- Attach four rows; one ledger row naming all four pieces and the TD; `metrics/2026-W43.json` lands with it (mm-1c owns `metrics/`).
- Wait for the report. On `stop:*`, do not retry blind: record the decisive line and go to Westley.

## Step 2: the two auditors (after step 1 is on main)

Two worktrees from origin/main: `wt.py new audit-A`, `wt.py new audit-B`. Two clerks in parallel, both claude-sonnet-5-5 (engineer), briefs `briefs/auditor_A.md` and `briefs/auditor_B.md` verbatim, each told its worktree path and nothing about the other or about the Architect's reasoning. Save each report unedited as `docs/northstar/plans/method_rev3_2026-10-26/audit_A_report.md` and `audit_B_report.md`, push under `flock -w 1800 ~/Projects/om-push/records.lock git push origin HEAD:main` from a records worktree (status_check no DRIFT first). `wt.py done` the two audit trees after.

## Step 3: report to Westley (once)

Schema: LANDED (piece ids, shas, gate minutes each, rejects and their causes); RECORDS (ledger ids, gate_runs rows appended); AUDITS (file paths on main, line counts, each auditor's RESULT line and severity counts); STOPPED (anything not done, with the decisive line); COST (your chat's turns, each clerk's turns if the Agent result shows them). Then stop. The Architect reads the audit reports from main and takes Phase 3 from there.

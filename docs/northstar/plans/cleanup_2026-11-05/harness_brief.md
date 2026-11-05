# Brief: harness side of the 2026-11-05 cleanup

Model: Sonnet 5.5 (`engineer`). Spawn nothing. Think tersely. Report once, at the end.

Worktree: `~/Projects/om-wt/cleanup`, branch `s/cleanup-2026-11-05`. Work only there; every command names the absolute path. Never edit `~/Projects/ouroboros-manifold`. The docs commit is already on the branch (`git log -1`); read `docs/method/story_loop.md`, `docs/method/history.md` rows dated 2026-11-05, and `docs/northstar/story_reviews/westley/decisions.md` rows `DEC-cap-1500-2026-11-05`, `DEC-mail-detached-2026-11-05` for the why.

Goal: one commit that makes the harness match those docs. Nothing else changes.

## Edits

1. `.claude-swarm.toml`: `max_impl_lines = 100` becomes `1500`. Only that line changes; leave `apex_test_cmd` and the rest as they are.
2. `scripts/specfactory/size_lint.py`: `DEFAULT_WARN_LINES = 100` becomes `1500`.
3. `scripts/specfactory/method_check.py`: remove the four CHECKS rows `plan_reread`, `comm_send`, `comm_state_checks`, `comm_mail_first`, and every function, constant and branch that exists only for them (`comm_hits`, `MAIL_WAIT`, `MAIL_READ`, `READING_LIST`, `reading_list()`, `PLAN_REREAD`, the `METHOD read first:` and `PLAN RE-READ` output, `PLANS_DIR` if unused after). Reword the `wakeups` rule to "No scheduled wakeups: the wait is the Workflow or Agent notification (docs/method/architect.md)." and the `polling` and `gate_runs` rules to cite `docs/method/story_loop.md` instead of `runner.md`/`clerk.md`; `live_tree` becomes "Never edit `~/Projects/ouroboros-manifold` itself; work on a worktree cut from it (docs/method/builder.md)." Six rules remain: wakeups, polling, gate_runs, live_tree, code_edits, context. `python3 scripts/specfactory/method_check.py` on an empty transcript must print exactly six `METHOD <id>` rule lines and no `read first` line.
4. `scripts/specfactory/status_check.py`: remove `check_mail` and its call site (lines 178 to 184 region) so nothing reads `~/Projects/om-push/mail` or `agents.toml`.
5. `.claude/settings.json`: remove the `PreToolUse` entry whose matcher is `SendMessage` (the `mail-guard.sh` hook). Keep the `Bash` entry and the `SessionStart` entry byte for byte. Valid JSON after.
6. `.claude/hooks/mail-guard.sh`: add a second line `# Detached 2026-11-05: no longer wired in .claude/settings.json; see docs/method/history.md (DEC-mail-detached-2026-11-05).` Nothing else.

## Tests (one `Test-defect:` trailer covers all of these; the docs commit retired what they pin)

- `git rm` `tests/method/test_mail.py`, `tests/method/test_station.py`, `tests/method/test_mail_guard.py`, `tests/method/mailfix.py`, `tests/method/test_method_check_comm.py`, `tests/specfactory/test_method_check_reread.py`.
- `tests/specfactory/test_status_check.py`: remove the H-077 `check mail` block (from the comment `# ---- H-077: check `mail`` near line 614 to the end of its tests) and the `mailfix` import.
- `tests/specfactory/test_method_check.py`: `SIX_RULES` becomes the six ids; the three `test_h005_*` tests assert six rules and "nine" wording becomes "six". If other tests in that file or in `tests/method/test_method_check_channels.py` assert on `plan_reread`, `comm_*`, `read first` or `PLAN RE-READ`, fix the assertion to the new behaviour; never delete a test that still tests a kept rule.
- `tests/specfactory/test_lab_docs.py` lines 160 to 173: the pinned name `2026-10-31-lab-staircase.md` becomes `lab-staircase.md` (the plan moved to `docs/northstar/story_reviews/westley/lab-staircase.md`; ROADMAP section 1 names the new path).
- Any other test that fails because it reads a deleted card or the old plan path: re-pin to the new text; say so in the report.

## Run

`cd ~/Projects/om-wt/cleanup && .venv/bin/python -m pytest tests/specfactory tests/method -q -p no:cacheprovider -x --timeout 600 2>&1 | tail -30` (drop `-x` on the second run to get the full red list). Known red before your change: `tests/specfactory/test_size_lint.py::test_real_examples_from_the_repo` (H-082); leave it. If `.venv` is missing in the worktree, use `~/Projects/ouroboros-manifold/.venv/bin/python`.

## Commit

One commit on the branch, `git add` only the files above, subject `Cleanup 2026-11-05: harness side (cap 1,500, mail checks out, tests re-pinned)`, body naming each file in one line, trailers:

```
Test-defect: mail, plan-reread and comm checks retired by DEC-mail-detached-2026-11-05; lab plan path moved (Architect)
Decision: DEC-mail-detached-2026-11-05
```

Do not push. Do not merge. Do not touch systemd.

## Report (once)

```
ok: true|false
sha: <commit>
tests: <passed>/<failed>, red list verbatim (test ids only)
method_check empty transcript: <the six rule ids printed>
re-pinned beyond the brief: <files or none>
stop_reason: none | <what blocked you>
```

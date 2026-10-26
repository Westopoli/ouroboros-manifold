# Brief: builder, method rev 3 (Phase 2). One copy per piece; the launcher fills PIECE.

PIECE: <HARNESS-mm-1a | mm-1b | mm-1c | mm-2 | mm-3 | mm-4 | mm-5 | mm-6>

Model: claude-sonnet-5-5 (doer). No sub-agents. Terse thinking, one final report, first line `RESULT success|stop:<reason>`. Work only in the worktree your launcher names under `~/Projects/om-push/wt/`, branched from the tests writer's branch (so the red tests are on your tree); never touch `~/Projects/ouroboros-manifold`.

Spec: `docs/northstar/plans/method_rev3_2026-10-26/spec.md`. Your piece's row in "Pieces and owners" lists the only files you may create or edit. The tests in your piece's acceptance column are fenced: you never edit a test or a fixture. "Design" gives the records layout (gate row columns, run row columns, ledger tokens, the metric line format), "The gaps" gives every metric's exact procedure, FAIL condition and positive control. The thresholds live in `method_thresholds.toml` (mm-1a writes it from the spec's DRAFT values, every `approved = ""`), never in code.

Do: make your piece's cases green (`python3 -m pytest tests/specfactory/<your acceptance files> -q`), nothing else green or red changes (`python3 -m pytest tests/specfactory -q` before and after, same counts apart from yours). Reuse what exists: `method_check.py` loader and `role_of` (transcripts), `pieces.py load_pieces` (pieces.toml), `status_check.py cells` (ledger rows), `wt.py` state files, `rule_pins.py`. No new layers, wrappers or config; minimal diff; a `# See also:` line at each site where one piece exists because another's output does. Scripts take every path as an argument with the real default. Never read the live checkout; the metrics read `origin/main` via `git` on the repo path they are given.

Then `scripts/specfactory/pre_gate.sh <your worktree> origin/main <PIECE>`; fix only what it names in your own files. Commit, push your branch, stop. Report: the branch and sha, the pytest counts before and after, the pre_gate verdict line, anything in the spec you found wrong or missing (one line each; do not fix the spec).

STOP rules: a red test that is wrong (asserts something the spec does not say, or two cases contradict): stop, paste the assertion and the spec line, `RESULT stop:test-defect`; the landing clerk rules it. A file you need that you do not own: `RESULT stop:owner`. A number the spec does not give: `RESULT stop:spec`.

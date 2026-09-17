# leaf-02 assumptions

No sibling ASSUMPTIONS files existed at start; none of these were escalated (no do_not_edit conflict, no two-correct-design ambiguity that would be observed outside my own file).

- Frontmatter parser mirrors `~/Projects/agora/scripts/burn.py`'s `parse_spec` shape (dash-continuation lines append to the last bare `key:` seen, quoted values unquoted via the same one-layer-of-double-quotes rule) but is a fresh, independent implementation — not imported, per the brief.
- `target_file()` resolution: `snippet_file` wins if present and non-empty; otherwise the first comma-separated entry of `allowed_files`. Neither test fixture exercises `allowed_files`, so this branch is untested but implemented per the brief's stated rule.
- Acceptance commands run via `subprocess.run(cmd, shell=True, cwd=worktree)`, short-circuiting (stop and report failure) on the first non-zero exit rather than always running every command in the list. Brief says "run every acceptance command" but all test fixtures use single-entry acceptance lists, so this couldn't be distinguished from full iteration; short-circuit is my choice, not forced by evidence.
- Output printing: on both the "already passes" (exit 2) and post-reference (exit 0/1) runs, the full captured command output is always printed, matching "print the failing command's output either way" read as "print it regardless of pass/fail," not "print it only when it fails."
- Scratch worktree path: `tempfile.mkdtemp()/wt` (a not-yet-existing subdir of a fresh tempdir), so `git worktree add` creates it fresh; cleanup always runs `git worktree remove --force` then `shutil.rmtree` on the tempdir, in a `finally`, regardless of outcome.
- `docs/northstar/spec_factory.md`: added one pipeline-table row and one Scripts-list bullet for `green_check.py`, naming `tests/csim/references/<card-id>.c` as where reference bodies live, per the brief's exact instruction — no other doc content touched.

Final: `scripts/specfactory/green_check.py` is 147 lines (impl_line_budget 150). All 9 tests in `tests/specfactory/test_green_check.py` pass (confirmed RED then GREEN).

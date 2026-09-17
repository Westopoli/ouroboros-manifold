---
leaf_id: leaf-02
spec_file: docs/test_specs/drift-gate-and-green-check.md
spec_lines: 8-17
test_files:
  - tests/specfactory/test_green_check.py
impl_files:
  - scripts/specfactory/green_check.py
  - docs/northstar/spec_factory.md
contract_imports:
do_not_edit:
  - csrc/sim.c
  - csrc/region.c
  - tests/csim/**
  - docs/bible/game_bible.md
  - docs/bible_history/**
  - docs/test_specs/cover_asteroid_los_spec.md
  - docs/test_specs/cover_los_rework_spec.md
  - docs/test_specs/wave_3_pre_zip_wiring.md
  - docs/test_specs/drift-gate-and-green-check.md
  - docs/phase1_ship_plan.md
  - docs/priority_queue.md
  - docs/bible/stories.md
  - docs/bible/epics/E-02-region-fields-and-drift.md
  - docs/bible/algorithms.md
  - simulation/**
  - csrc/ouroboros_sim.h
  - Makefile
  - tests/specfactory/**
test_owned_by: parent
impl_line_budget: 150
test_assertion_budget: 16
---

## Task

Per spec_lines 8-17, write `scripts/specfactory/green_check.py`, a new script mirroring `scripts/specfactory/red_check.py`'s shape (module docstring stating usage and exit codes, a `main(argv) -> int`, `if __name__ == "__main__": sys.exit(main(sys.argv[1:]))`) but proving the opposite side of a card's acceptance test:

```python
def main(argv: list[str]) -> int:
    ...  # usage: green_check.py <card_file> <reference_file>
```

Behavior: given a card file path and a reference implementation file path, parse the card's YAML-ish frontmatter (mirror the minimal stdlib-only parser shape in `~/Projects/agora/scripts/burn.py`'s `parse_spec` — read-only reference in a sibling repo, do not import it) for `project` (the target repo root), `acceptance` (a list of shell command strings), and the one file the reference replaces (`snippet_file` if present, else the first entry of comma-separated `allowed_files`). Create a scratch git worktree of `project` at `HEAD` (detached), run every `acceptance` command there with `shell=True`, `cwd=`the worktree. If every command already passes against the untouched worktree, exit 2 (the detector can never fail — print a reason containing the phrase "already passes"). Otherwise write the reference file's content over the target file inside the worktree and run `acceptance` again: exit 0 if every command now passes, exit 1 if not (print the failing command's output either way). Exit 3 for usage/parse errors (missing card, missing reference, no acceptance commands, `project` not a directory). Always remove the scratch worktree before returning, whatever the outcome.

Then add one row to the pipeline table in `docs/northstar/spec_factory.md` (the existing `| Step | Owner | Automation |` table) for `green_check.py`, in the same style as the `red_check.py` row already there, and one line to that doc's "Scripts" bullet list — describe what it checks and that reference bodies live at `tests/csim/references/<card-id>.c` (a fenced path this leaf does not need to create anything under yet; no reference files exist for this wave).

## Acceptance

You are working inside your own git worktree — a private checkout at `.swarm/drift-gate-and-green-check/worktrees/leaf-02/`, which is your working directory and which the parent manages. Never run git (including inside `green_check.py` itself at test time — its own internal `git worktree` calls target the *test's* throwaway project directories, never your own leaf worktree).

Run `.venv/bin/python -m pytest tests/specfactory/test_green_check.py -p no:cacheprovider -v`. Confirm RED first (all collected tests fail because `green_check.py` does not exist yet). Create `scripts/specfactory/green_check.py` and edit `docs/northstar/spec_factory.md` until all tests pass. Stop.

Do not stage, copy, commit, or move anything.

## Escalation triggers

Stop and report to the parent if:
- The card frontmatter format needed by the tests doesn't match what a real `~/Projects/agora/queue/*.md` card actually contains (do not go read real cards to resolve this — escalate instead).
- Implementing this would require any file outside `scripts/specfactory/green_check.py` and `docs/northstar/spec_factory.md`.
- Impl approaches `impl_line_budget` with assertions still failing.

## Assumption log

Same protocol as the canonical brief template (`swarm-shared/references/brief-template.md`): log any inferred value to `.swarm/drift-gate-and-green-check/briefs/leaf-02.ASSUMPTIONS.md` before finishing, checking sibling ASSUMPTIONS files first.

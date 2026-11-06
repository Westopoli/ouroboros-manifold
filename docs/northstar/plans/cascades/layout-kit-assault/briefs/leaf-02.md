---
leaf_id: leaf-02
spec_file: docs/northstar/plans/cascades/layout-kit-assault/spec.md
spec_lines: 27-86
test_files:
  - tests/csim/test_layout_kit_cli.py
  - tests/csim/test_layout_kit_connected.py
  - tests/csim/test_layout_kit_fairness.py
  - tests/csim/test_layout_kit_bypass.py
  - tests/csim/test_layout_kit_approaches.py
  - tests/csim/test_layout_kit_chokes.py
  - tests/csim/test_layout_kit_bounds.py
  - tests/csim/test_layout_kit_determinism.py
impl_files:
  - csrc/tools/layout_dump.c
contract_imports:
do_not_edit:
  - csrc/ouroboros_sim.h
  - csrc/layout_kit.h
  - csrc/layout_internal.h
  - csrc/layout_engine.c
  - csrc/mission.c
  - Makefile
  - docs/**
  - tests/**
  - scenes/**
  - autoload/**
  - scripts/specfactory/**
  - simulation/**
  - csrc/layout_drafts.h
  - csrc/layout_kit.c
  - csrc/layout_kit_pieces.c
  - csrc/layout_kit_graph.c
  - scripts/layout/render.py
impl_line_budget: 700
test_assertion_budget: 40
test_owned_by: parent
wave: 2
---

## Task

Write the command-line tool `csrc/tools/layout_dump.c` over the frozen header `csrc/layout_kit.h` (read it in full first; never edit it) and the engine already admitted in wave 1 (`csrc/layout_kit*.c`, `csrc/layout_drafts.h`: read them, never edit them). Implement acceptance criteria 5 to 7 of the spec lines in `spec_lines`: the flags `--seed`, `--archetype`, `--canvas`, `--sides`, `--out`, `--seeds A..B` with `--out-dir`, `--break <check>` and `--check file.json`, the exit codes, and the JSON `om-layout-1` of the spec's JSON section with keys in exactly the stated order. Print numbers with integer arithmetic only, as the JSON section says (hundredths, `%lld`, no `%g`/`%f`); print the `drafts` block from `om_lk_draft_count/name/value`; print `kind`, `piece`, `landform` and `mode` fields with `om_lk_name`. Build line used by the tests: `cc <flags> -I csrc -o layout_dump csrc/tools/layout_dump.c csrc/layout_kit*.c csrc/terrain_noise.c -lm`. The file is scanned by `scripts/specfactory/libm_lint.py` (rglob over `csrc/`): use no banned libm or libc function (no `time`, `rand`, `qsort`, `pow`, `sin`, `cos`). `--check` reads only JSON written by this tool, whose key order is fixed, so a small hand-written parser for numbers, strings, booleans and arrays suffices.

## Acceptance

You are working inside your own git worktree — a private checkout at
`.swarm/layout-kit-assault/worktrees/leaf-02/`, which is your working directory
and which the parent manages. Never run git. Nothing you do there is visible
to a sibling leaf or to the user's checkout.

Your working directory is the absolute worktree path the parent gives you; run `cd <worktree> && /home/westopoli/Projects/ouroboros-manifold/.venv/bin/python -m pytest tests/csim/test_layout_kit.py tests/csim/test_layout_kit_cli.py tests/csim/test_layout_kit_connected.py tests/csim/test_layout_kit_fairness.py tests/csim/test_layout_kit_bypass.py tests/csim/test_layout_kit_approaches.py tests/csim/test_layout_kit_chokes.py tests/csim/test_layout_kit_bounds.py tests/csim/test_layout_kit_determinism.py -q -p no:cacheprovider` for your test files. Confirm RED. Edit `impl_file` in
place, at its normal path inside the worktree. Confirm GREEN. Stop.

Do not stage, copy, commit, or move anything. `/manager-mode` Phase 5 commits
your declared files from the worktree onto your branch, and Phase 6 merges
that commit into the integration branch only after every gate passes.

Earlier versions of this template asked the leaf to confirm GREEN *and* write
only to a staging directory. Those two instructions could not both be
satisfied: the test imports impl at its real path, so a leaf that never wrote
there was running its test against the unmodified file and could not reach
GREEN. The worktree removes the conflict rather than picking a side — inside
it, the real path IS yours.

## Escalation triggers

Stop and report to the parent if:
- A type the test imports is not in contract_imports.
- The impl would need to create a file not listed in `impl_files`. (Creating a
  file that IS listed is ordinary — a declared impl file often does not exist
  yet.)
- The impl would need to edit a file in do_not_edit.
- Two sibling assertions seem to require contradictory behavior.
- Impl approaches impl_line_budget with assertions still failing.

## Protocols

Assumption log, sibling-assumption read, question ledger and contract-proposal protocol: follow `docs/northstar/plans/cascades/layout-kit-assault/briefs/PROTOCOL.md` (substitute your own leaf id). Write ASSUMPTIONS to the briefs directory of the PARENT clone `/home/westopoli/Projects/om-wt/layout-kit-cascade/docs/northstar/plans/cascades/layout-kit-assault/briefs/leaf-02.ASSUMPTIONS.md` (an absolute path outside your worktree), never inside the worktree: the parent refuses a commit with undeclared writes.

---
leaf_id: leaf-01
spec_file: docs/northstar/plans/push/specs/C5.md
spec_lines: 1-90
test_files:
  - tests/test_tactical_view.gd
impl_files:
  - scenes/tactical_c/tactical_view.tscn
  - scenes/tactical_c/tactical_view.gd
contract_imports:
do_not_edit:
  - project.godot
  - scripts/**
  - tests/**
  - docs/**
  - csrc/**
  - Makefile
  - scenes/mockups/**
impl_line_budget: 500
test_assertion_budget: 20
test_owned_by: parent
wave: 1
---

## Task

Build a fresh `scenes/tactical_c/tactical_view.tscn` + backing script per
spec_lines 1-90 of the spec file above: `load_frame`, `qa_state`,
`qa_plant`, `issue_command`, `qa_box_select`, `qa_pan`. Read
`tests/test_tactical_view.gd` in full — it is the literal contract, exact
field names, exact plant ids and behaviors (including `select-all-exists`,
a permanent-false id with no fault site ever wired to it). A throwaway
reference implementation already scored 57/57 against this test (see the
c5_t2g_tests_note.md's "Reference-stub proof" section cited in the spec)
— this is genuinely satisfiable as specced, and that section names two
real GDScript gotchas (array-equality type-strictness, array-in-%-format
crashes) worth reading before you hit them yourself.

## Acceptance

You are working inside your own git worktree — a private checkout at
`.swarm/c5/worktrees/leaf-01/`, which is your working directory and which
the parent manages. Never run git. Nothing you do there is visible to the
user's checkout.

Run `scripts/run_godot_tests.sh tests/test_tactical_view.gd`. Confirm RED
first (scene missing). Edit `impl_files` in place (adding a small
additional helper script under `scenes/tactical_c/` alongside the two
listed is fine if genuinely needed — note it in your report). Confirm
GREEN (`=== GREEN ===`, exit 0, all 15 checks / 57 assertions pass). Stop.

Do not stage, copy, commit, or move anything.

## Escalation triggers

Stop and report to the parent if:
- The impl would need to create a file outside `scenes/tactical_c/**`.
- The impl would need to edit any file in `do_not_edit`.
- Impl approaches `impl_line_budget` (500) with checks still red.

## Assumption log

Log every inference (exact rendering approach for units/map, camera
projection details beyond "fixed top-down, non-rotated," `selected`'s
exact shape, screen-direction sign convention for the +x world move — the
spec deliberately leaves this open per the test's own "one dominant axis"
tolerance) to `.swarm/c5/briefs/leaf-01.ASSUMPTIONS.md`, citing the spec
section or test line.

## Sibling-assumption read

No sibling leaves in this wave (single-leaf piece). Skip.

## Question ledger / contract-proposal protocol

Standard shape at `.swarm/c5/questions/leaf-01-Q<n>.md` /
`.swarm/c5/proposals/leaf-01.md` if genuinely blocked with cross-piece
weight. Unlikely here — this is a fresh, self-contained scene.

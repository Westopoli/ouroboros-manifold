---
leaf_id: leaf-01
spec_file: docs/northstar/plans/push/specs/T2g.md
spec_lines: 1-70
test_files:
  - tests/test_load_game.gd
impl_files:
  - scenes/load_game/load_game.gd
contract_imports:
do_not_edit:
  - project.godot
  - scripts/**
  - tests/**
  - docs/**
  - csrc/**
  - Makefile
  - scenes/load_game/load_game.tscn
impl_line_budget: 200
test_assertion_budget: 20
test_owned_by: parent
wave: 1
---

## Task

Add `qa_set_bridge(bridge) -> void`, `qa_state() -> Dictionary`,
`qa_load_slot(slot_id: String) -> Dictionary` to
`scenes/load_game/load_game.gd` per spec_lines 33-55 of the spec file
above. Purely additive — do not remove or restructure the existing
`_ready`/`_build_ui`/`_refresh_slots`/`_add_slot_card`/delete-confirm
legacy path, which still renders from `UIDataBus.get_save_slots()`
independently. `qa_set_bridge` drives a second, parallel row list from
the injected bridge's `list_saves()`. `current_version` is a simple
scene-local constant (any reasonable non-negative int, e.g. `1`) — an
ordinary internal choice with no outside weight, the test only checks
it's non-negative and used consistently.

## Acceptance

You are working inside your own git worktree — a private checkout at
`.swarm/t2g/worktrees/leaf-01/`, which is your working directory and
which the parent manages. Never run git. Nothing you do there is visible
to the user's checkout.

Run `scripts/run_godot_tests.sh tests/test_load_game.gd`. Confirm RED
first (missing methods). Edit `impl_files` in place. Confirm GREEN
(`=== GREEN ===`, exit 0, all 6 checks pass). Stop.

Do not stage, copy, commit, or move anything.

## Escalation triggers

Stop and report to the parent if:
- The impl would need to create a file not listed in `impl_files`.
- The impl would need to edit `scenes/load_game/load_game.tscn` or any
  file in `do_not_edit`.
- Impl approaches `impl_line_budget` (200) with the test still red.

## Assumption log

Log any inference (exact `current_version` value, `label_text`'s exact
wording beyond containing both version numbers, row rendering approach)
to `.swarm/t2g/briefs/leaf-01.ASSUMPTIONS.md`, citing the spec section or
test line.

## Sibling-assumption read

No sibling leaves in this wave (single-leaf piece). Skip.

## Question ledger / contract-proposal protocol

Standard shape at `.swarm/t2g/questions/leaf-01-Q<n>.md` /
`.swarm/t2g/proposals/leaf-01.md` if genuinely blocked with cross-piece
weight. Unlikely here.

---
leaf_id: leaf-02
spec_file: docs/northstar/plans/push/specs/C4.md
spec_lines: 1-84
test_files:
  - tests/test_briefing_debrief.gd
impl_files:
  - scenes/debrief/debrief.gd
contract_imports:
do_not_edit:
  - project.godot
  - scripts/**
  - tests/**
  - docs/**
  - csrc/**
  - Makefile
  - scenes/mission_briefing/**
  - scenes/mission_briefing/mission_briefing.gd
  - scenes/debrief/debrief.tscn
impl_line_budget: 200
test_assertion_budget: 20
test_owned_by: parent
wave: 1
---

## Task

Add `load_frame(debrief: Dictionary) -> void`, `qa_state() -> Dictionary`,
`qa_plant(id: String) -> bool` to `scenes/debrief/debrief.gd` per
spec_lines 64-84 of the spec file above. Purely additive — do not remove,
rename, or restructure the existing `setup(params)`, `_input()`, or
`_build_ui()`. The band int→string mapping is exact and given in the spec
(`["total_failure","partial_failure","partial_success","strong_success",
"total_success"]`, indexed directly by the frame's `band` int) — not a
guess, not a formula, a literal table.

## Acceptance

You are working inside your own git worktree — a private checkout at
`.swarm/c4/worktrees/leaf-02/`, which is your working directory and which
the parent manages. Never run git. Nothing you do there is visible to a
sibling leaf or the user's checkout.

Run `scripts/run_godot_tests.sh tests/test_briefing_debrief.gd`. Confirm
RED first (the debrief block's method-presence checks fail; the briefing
block will also be red until leaf-01 lands, but a sibling's red doesn't
block your own checks — the test isolates the two blocks). Edit
`impl_files` in place. Confirm your debrief block's checks pass
(method-presence, `band` string per the exact table, `achieved_pct`/
`brought_home_pct` as frame value × 100, `region_delta` exactly 4 fields
matching the frame, the `band-off-by-one` plant, `qa_plant` false on
`"nope"`). The briefing block staying red because leaf-01 hasn't landed in
your own worktree is expected and not your concern — the parent merges
both leaves before checking full GREEN. Stop once your own scene's checks
pass.

Do not stage, copy, commit, or move anything.

## Escalation triggers

Stop and report to the parent if:
- The impl would need to create a file not listed in `impl_files`.
- The impl would need to edit `scenes/debrief/debrief.tscn` or any file in
  `do_not_edit`.
- Impl approaches `impl_line_budget` (200) with your own checks still red.

## Assumption log

Log any inference (whether `load_frame` triggers a UI re-render of the
existing `_build_ui()` display or only updates the queryable state — the
test only checks `qa_state()`, not rendered visuals) to
`.swarm/c4/briefs/leaf-02.ASSUMPTIONS.md`, citing the spec section or test
line.

## Sibling-assumption read

A sibling leaf-01 (`scenes/mission_briefing/mission_briefing.gd`) builds
in parallel, no shared files. Not directly relevant to your work.

## Question ledger / contract-proposal protocol

Standard shape at `.swarm/c4/questions/leaf-02-Q<n>.md` /
`.swarm/c4/proposals/leaf-02.md` if genuinely blocked with cross-piece
weight. Unlikely here.

---
leaf_id: leaf-01
spec_file: docs/northstar/plans/push/specs/C4.md
spec_lines: 1-72
test_files:
  - tests/test_briefing_debrief.gd
impl_files:
  - scenes/mission_briefing/mission_briefing.gd
contract_imports:
do_not_edit:
  - project.godot
  - scripts/**
  - tests/**
  - docs/**
  - csrc/**
  - Makefile
  - scenes/debrief/**
  - scenes/debrief/debrief.gd
  - scenes/mission_briefing/mission_briefing.tscn
impl_line_budget: 250
test_assertion_budget: 20
test_owned_by: parent
wave: 2
---

## Task

Add `load_frame(mission: Dictionary) -> void`, `qa_state() -> Dictionary`,
`qa_plant(id: String) -> bool` to `scenes/mission_briefing/mission_briefing.gd`
per spec_lines 43-63 of the spec file above. Purely additive — do not
remove, rename, or restructure the existing `setup(params)`, `_ready()`,
`_input()`, or `_build_ui()`. The one specific rule to get right: `marker_name` in
`qa_state()`'s `objectives[]` must come from a client-side node→name
`const Dictionary` keyed on the node id alone (covering at least node ids
3, 7, 12), never derived from the frame's other fields and never just
`"Node %d" % node`.

## Acceptance

You are working inside your own git worktree — a private checkout at
`.swarm/c4/worktrees/leaf-01/`, which is your working directory and which
the parent manages. Never run git. Nothing you do there is visible to a
sibling leaf or the user's checkout.

Run `scripts/run_godot_tests.sh tests/test_briefing_debrief.gd`. Confirm
RED first (the briefing block's method-presence checks fail; the debrief
block will also be red until leaf-02 lands, but a sibling's red doesn't
block your own checks — the test isolates the two blocks). Edit
`impl_files` in place. Confirm your briefing block's checks pass (mission
briefing method-presence, `archetype`/`deadline_ticks` straight from
frame, `objectives.size()==3` with exactly 1 primary, `marker_name`
stability across two frames, the `marker-from-frame` plant, `qa_plant`
false on `"nope"`). The debrief block staying red because leaf-02 hasn't
landed in your own worktree is expected and not your concern — the parent
merges both leaves before checking full GREEN. Stop once your own scene's
checks pass.

Do not stage, copy, commit, or move anything.

## Escalation triggers

Stop and report to the parent if:
- The impl would need to create a file not listed in `impl_files`.
- The impl would need to edit `scenes/mission_briefing/mission_briefing.tscn`
  or any file in `do_not_edit`.
- Impl approaches `impl_line_budget` (250) with your own checks still red.

## Assumption log

Log any inference (exact node→name table contents beyond the fixture's 3/7/12,
objective ordering, force/tiers handling — not read by the test) to
`.swarm/c4/briefs/leaf-01.ASSUMPTIONS.md`, citing the spec section or test
line.

## Sibling-assumption read

A sibling leaf-02 (`scenes/debrief/debrief.gd`) builds in parallel, no
shared files. Not directly relevant to your work (different scene,
different frame shape) — skip unless something about the shared
`load_frame`/`qa_state`/`qa_plant` naming convention seems worth matching.

## Question ledger / contract-proposal protocol

Standard shape at `.swarm/c4/questions/leaf-01-Q<n>.md` /
`.swarm/c4/proposals/leaf-01.md` if genuinely blocked with cross-piece
weight. Unlikely here.

---
leaf_id: leaf-01
spec_file: docs/northstar/plans/push/specs/C3.md
spec_lines: 1-90
test_files:
  - tests/test_chronicle_scroll.gd
impl_files:
  - scenes/world/chronicle_scroll_panel.gd
contract_imports:
do_not_edit:
  - project.godot
  - scripts/**
  - tests/**
  - docs/**
  - csrc/**
  - Makefile
  - simulation/library/chronicle/fragments.json
  - scenes/world/chronicle_entry.gd
  - scenes/world/chronicle_entry.tscn
  - scenes/world/chronicle_entry_expansion.gd
  - scenes/world/chronicle_entry_expansion.tscn
impl_line_budget: 350
test_assertion_budget: 20
test_owned_by: parent
wave: 1
---

## Task

Add `set_snapshot(snapshot: Dictionary) -> void`, `load_frame(frame:
Dictionary) -> void`, `qa_state() -> Dictionary`, `qa_plant(id: String) ->
bool`, `qa_click_entry(entry_id: int) -> void`, `qa_dismiss() -> void` to
`scenes/world/chronicle_scroll_panel.gd` per spec_lines 39-79 of the spec
file above. Purely additive — do not remove, rename, or restructure the
existing `begin_time_jump`/`queue_entry`/`start_printing`/`end_time_jump`/
`pause`/`resume`/`slide_in`/`slide_out` legacy path. Ref-validity checking
(drop an entry only when every one of its refs is unresolved; otherwise
count each bad id into `unresolved_refs`), fragment-id-to-text resolution
via `simulation/library/chronicle/fragments.json` with a `"[fragment
<id>]"` fallback, and the bible-mandated `pace` constants (0.08/0.20,
report as data — do not read or touch the existing printing-animation
timer's own different constants) are the three specific rules to get
right.

## Acceptance

You are working inside your own git worktree — a private checkout at
`.swarm/c3/worktrees/leaf-01/`, which is your working directory and which
the parent manages. Never run git. Nothing you do there is visible to the
user's checkout.

Run `scripts/run_godot_tests.sh tests/test_chronicle_scroll.gd`. Confirm
RED first (missing methods). Edit `impl_files` in place. Confirm GREEN
(`=== GREEN ===`, exit 0, all 11 checks pass: entries count, dropped-entries
clean, refs-resolve + owners, prose-from-fragment-not-frame (all 6
placeholder since the fixture's fragment ids are deliberately unassigned),
pace, hash determinism across two loads, expanded_id click/dismiss
contract, both plants each with a positive control, `qa_plant("nope")`
false). Stop.

Do not stage, copy, commit, or move anything.

## Escalation triggers

Stop and report to the parent if:
- The impl would need to create a file not listed in `impl_files`.
- The impl would need to edit any file in `do_not_edit`, including
  `simulation/library/chronicle/fragments.json` (read it, never write it).
- Impl approaches `impl_line_budget` (350) with the test still red.

## Assumption log

Log any inference (exact hash formula, `entries[]` ordering, `owners`'
exact region set when an entry is dropped — does the dropped entry's own
now-unresolvable refs still count toward `owners`, or only surviving
entries' refs — the test only checks size matches `_distinct_region_refs`
over the WHOLE frame including dropped entries, so include dropped-entry
refs too if you read it that way) to
`.swarm/c3/briefs/leaf-01.ASSUMPTIONS.md`, citing the spec section or test
line.

## Sibling-assumption read

No sibling leaves in this wave (single-leaf piece). Skip.

## Question ledger / contract-proposal protocol

Standard shape at `.swarm/c3/questions/leaf-01-Q<n>.md` /
`.swarm/c3/proposals/leaf-01.md` if genuinely blocked with cross-piece
weight. Unlikely here.

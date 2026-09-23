---
leaf_id: leaf-03
spec_file: docs/northstar/plans/push/specs/C8-M3.md
spec_lines: 1-120
test_files:
  - tests/qa/desktop/test_flow_spine.py
impl_files:
  - scenes/mission_briefing/mission_briefing.gd
  - scenes/tactical_c/tactical_view.gd
  - scenes/tactical_c/tactical_view.tscn
contract_imports:
do_not_edit:
  - project.godot
  - scripts/**
  - tests/**
  - docs/**
  - csrc/**
  - Makefile
  - autoload/**
  - scenes/main_menu/**
  - scenes/galaxy/**
  - scenes/debrief/**
  - scenes/world/chronicle_*
  - autoload/scene_router.gd
  - autoload/c_bridge.gd
  - scenes/loading_screen/loading_screen.gd
  - scenes/main_menu/main_menu.gd
  - scenes/galaxy/galaxy_view.gd
  - scenes/galaxy/galaxy_view.tscn
  - scenes/debrief/debrief.gd
  - scenes/world/chronicle_scroll_panel.gd
  - scenes/world/chronicle_scroll_panel.tscn
impl_line_budget: 200
test_assertion_budget: 20
test_owned_by: parent
wave: 1
shard: c8
---

## Task

Leg 3 of piece C8 ("mission leg") per spec_lines 1-120 of the spec file
above (`docs/northstar/plans/push/specs/C8-M3.md` — read the piece spec
`docs/northstar/plans/push/specs/C8.md` it cites too, in full).

1. `scenes/mission_briefing/mission_briefing.gd`'s `_build_footer`
   (around line 619) already has a Deploy button
   (`deploy_btn.text = "DEPLOY FORCES"`, `pressed.connect(func():
   SceneRouter.go_to("tactical"))`) — give it a stable `name`:
   `deploy_btn.name = "Deploy"`, and change its route target from
   `"tactical"` to `"tactical_c"` (the new route a sibling leaf is adding
   in parallel — you don't need it to exist yet to write this correctly).
   Also: `_ready()` (existing, self-backfills `_data` from
   `UIDataBus.get_mission_briefing("mock_001")` when `_data.is_empty()`)
   needs to ALSO self-load the fixture mission frame when reached fresh
   through this flow — read `tests/fixtures/mission_frame_seed11.json`
   (`FileAccess.open` + `JSON.parse_string`, same pattern
   `tests/test_briefing_debrief.gd`'s own fallback builder uses) and call
   `load_frame()` with it, alongside (not instead of, unless you find a
   cleaner way to unify them) the existing mock backfill — piece C4-2
   already made `load_frame()`'s downstream `_apply_frame_to_data()`
   overwrite the mock's prose fields with neutral placeholders once a
   frame has loaded, so calling both in sequence (mock backfill, then
   `load_frame()`) is safe and gives the correct end state: real
   frame-derived archetype/deadline/objectives, neutral placeholders for
   what the frame doesn't carry.
2. `scenes/tactical_c/tactical_view.gd` has `load_frame(frame)` but no
   `_ready()` — add one that reads
   `tests/fixtures/tactical_frame_seed11.json` and calls own
   `load_frame()` with it, so the scene shows something when routed to
   fresh (mirror the fixture-read pattern from `tests/test_tactical_view.gd`'s
   own fallback if that test has one, or just read+parse the file
   directly).
3. `scenes/tactical_c/tactical_view.tscn` (a pure `Node2D` scene today,
   no UI at all): add a `CanvasLayer` with a `Control`/`Button` child
   named `EndMission`, whose click handler calls
   `SceneRouter.go_to("debrief")` (the existing route, already in
   `SCENES`, no change needed there).

## Acceptance

You are working inside your own git worktree — a private checkout at
`.swarm/c8/worktrees/leaf-03/`, which is your working directory and which
the parent manages. Never run git. Nothing you do there is visible to a
sibling leaf or the user's checkout.

This leg isn't independently testable against the full flow. Confirm
instead:
- `scripts/run_godot_tests.sh tests/test_briefing_debrief.gd
  tests/test_tactical_view.gd` stay green (35/35, 57/57 — pure regression
  checks; your changes to `mission_briefing.gd` are additive to
  `_ready()`/`_build_footer`, `qa_state()`/`qa_plant()` untouched; your
  changes to `tactical_view.gd` add a new `_ready()` that didn't exist
  before, so double-check the fenced test doesn't assume `_ready()` is
  absent or empty — it shouldn't, since the test always calls
  `load_frame()` itself after instantiating, which will just overwrite
  whatever your new `_ready()` self-loaded).
- Write a small temporary headless script (delete before finishing) that
  instantiates each scene fresh, waits a frame, and confirms: (a) a
  child named `"Deploy"` exists in `mission_briefing.tscn`'s tree with
  the retargeted route (or just confirm the name/existence, trusting the
  wiring); (b) `tactical_view.tscn` shows non-empty `qa_state().units`
  after instantiation alone (proving your new `_ready()` actually loaded
  the fixture without needing an external `load_frame()` call); (c) a
  child named `"EndMission"` exists and is visible in
  `tactical_view.tscn`'s tree.

Do not stage, copy, commit, or move anything.

## Escalation triggers

Stop and report to the parent if:
- The impl would need to create a file not listed in `impl_files`.
- The impl would need to edit any file in `do_not_edit`, including
  `autoload/scene_router.gd` (a sibling leaf owns it).
- Impl approaches `impl_line_budget` (200).

## Assumption log

Log any inference (exact fixture-read error handling, CanvasLayer/Button
placement, how the mock-backfill-then-load_frame sequencing interacts in
`mission_briefing.gd`'s `_ready()`) to
`.swarm/c8/briefs/leaf-03.ASSUMPTIONS.md`, citing the spec section.

## Sibling-assumption read

Three sibling leaves build in parallel. leaf-01 owns
`autoload/scene_router.gd` (you reference `SCENES["tactical_c"]` and
`SCENES["debrief"]` — the latter already exists today unchanged, the
former is new from leaf-01, neither needs to exist in your own worktree
to write this correctly). Check `.swarm/c8/briefs/leaf-01.ASSUMPTIONS.md`
if useful, not required.

## Question ledger / contract-proposal protocol

Standard shape at `.swarm/c8/questions/leaf-03-Q<n>.md` /
`.swarm/c8/proposals/leaf-03.md` if genuinely blocked with cross-piece
weight.

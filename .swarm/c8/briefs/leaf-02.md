---
leaf_id: leaf-02
spec_file: docs/northstar/plans/push/specs/C8-M3.md
spec_lines: 1-120
test_files:
  - tests/qa/desktop/test_flow_spine.py
impl_files:
  - scenes/main_menu/main_menu.gd
  - scenes/galaxy/galaxy_view.gd
  - scenes/galaxy/galaxy_view.tscn
contract_imports:
do_not_edit:
  - project.godot
  - scripts/**
  - tests/**
  - docs/**
  - csrc/**
  - Makefile
  - autoload/**
  - scenes/mission_briefing/**
  - scenes/debrief/**
  - scenes/tactical_c/**
  - scenes/world/chronicle_*
  - autoload/scene_router.gd
  - autoload/c_bridge.gd
  - scenes/loading_screen/loading_screen.gd
  - scenes/mission_briefing/mission_briefing.gd
  - scenes/tactical_c/tactical_view.gd
  - scenes/tactical_c/tactical_view.tscn
  - scenes/debrief/debrief.gd
  - scenes/world/chronicle_scroll_panel.gd
  - scenes/world/chronicle_scroll_panel.tscn
impl_line_budget: 250
test_assertion_budget: 20
test_owned_by: parent
wave: 1
shard: c8
---

## Task

Leg 2 of piece C8 ("galaxy leg") per spec_lines 1-120 of the spec file
above (`docs/northstar/plans/push/specs/C8-M3.md` — read the piece spec
`docs/northstar/plans/push/specs/C8.md` it cites too, in full).

1. `scenes/main_menu/main_menu.gd`: the "NEW GAME" menu item is built by
   `_create_menu_item("NEW GAME", "new_game")` inside `_build_ui()`, which
   returns an unnamed `HBoxContainer` whose `gui_input` calls
   `_on_menu_action("new_game")` on click, currently routing (via
   `_on_menu_action`'s `match` → default case → `SceneRouter.go_to(action)`)
   to `"new_game"` (the era-selection flow). Change the menu-item's
   action string so it routes to `"galaxy"` instead (the new
   `SCENES["galaxy"]` route another leaf is adding in parallel — you
   don't need that route to exist yet to write this correctly, just
   reference the string `"galaxy"`), and give the returned container
   node a stable `name`: `"NewGame"` (set it right after
   `_create_menu_item` returns it, in the loop in `_build_ui()` that
   currently does `content.add_child(item)` for each menu entry — or
   inside `_create_menu_item` itself if that reads cleaner given the
   function's existing shape, your call).
2. `scenes/galaxy/galaxy_view.gd`'s `_ready()` (currently just calls
   `_camera_rig.set_view(...)`): also read `--seed` from
   `OS.get_cmdline_user_args()` (mirror `autoload/qa_daemon.gd`'s
   `_arg_value(args, flag)` helper — same parsing shape; default `1` when
   the flag is absent, per the piece spec's "seed from a `--seed` user
   arg, default 1"), instantiate `res://autoload/c_bridge.gd` fresh
   (`load("res://autoload/c_bridge.gd").new()`), call
   `bridge.load_snapshot_live(seed, 60, [6])`; on success call
   `set_snapshot(bridge.snapshot())` (the new accessor a sibling leaf is
   adding in parallel to `c_bridge.gd` — reference it, you don't need it
   to exist yet either); on failure (binary missing, pipe error, `false`
   return) leave the scene in whatever state `set_snapshot({})` /never
   calling `set_snapshot` at all already produces — check
   `tests/test_galaxy_view.gd` and the existing `qa_state()` implementation
   to confirm this doesn't crash (it shouldn't; don't add new
   crash-guards beyond what's already there unless you find a real gap).
3. `scenes/galaxy/galaxy_view.tscn` (a pure `Node3D` scene today, no UI
   at all): add a `CanvasLayer` with a `Control` or `Button` child named
   `Mission`, positioned/visible reasonably (placeholder styling is
   fine — this is a flow-spine piece, not a visual pass), whose click
   handler calls `SceneRouter.go_to("mission_briefing")` (the existing
   route, already in `SCENES`, no change needed there).

## Acceptance

You are working inside your own git worktree — a private checkout at
`.swarm/c8/worktrees/leaf-02/`, which is your working directory and which
the parent manages. Never run git. Nothing you do there is visible to a
sibling leaf or the user's checkout.

This leg isn't independently testable against the full flow (leaf-01's
`SCENES["galaxy"]`/`c_bridge.gd:snapshot()` and the other legs' buttons
don't exist in your worktree). Confirm instead:
- `scripts/run_godot_tests.sh tests/test_galaxy_view.gd tests/test_c_bridge.gd`
  stay green (44/44, 18/18 — pure regression checks, your changes are
  additive to `_ready()` and the scene tree, `qa_state()`/`qa_plant()`/etc
  untouched).
- Write a small temporary headless script (delete before finishing) that
  loads `main_menu.tscn`, instantiates it, finds the child named
  `"NewGame"` by walking the tree, and confirms it exists and its click
  handler references `"galaxy"` (read the connected callable's captured
  action string, or just confirm the node exists with that name and
  trust the wiring you wrote — whichever is easier to actually verify
  headless).
- Similarly confirm `galaxy_view.tscn` instantiates with a child node
  named `"Mission"` present and visible.

Do not stage, copy, commit, or move anything.

## Escalation triggers

Stop and report to the parent if:
- The impl would need to create a file not listed in `impl_files`.
- The impl would need to edit any file in `do_not_edit`, including
  `autoload/scene_router.gd` or `autoload/c_bridge.gd` (a sibling leaf
  owns those — if you find you genuinely need a change there beyond what
  this brief already assumes exists, escalate rather than edit).
- Impl approaches `impl_line_budget` (250).

## Assumption log

Log any inference (exact seed-arg default handling, CanvasLayer/Button
placement and styling choices, whether the live-snapshot load happens
synchronously in `_ready()` or needs a frame delay) to
`.swarm/c8/briefs/leaf-02.ASSUMPTIONS.md`, citing the spec section.

## Sibling-assumption read

Three sibling leaves build in parallel. leaf-01 owns
`autoload/scene_router.gd`/`c_bridge.gd` — you reference
`SCENES["galaxy"]` and `c_bridge.gd:snapshot()` without needing them to
exist yet in your own worktree (string literals / method calls that
resolve at combined-verification time, not at your own edit time). Check
`.swarm/c8/briefs/leaf-01.ASSUMPTIONS.md` if you want to confirm exact
naming, not required.

## Question ledger / contract-proposal protocol

Standard shape at `.swarm/c8/questions/leaf-02-Q<n>.md` /
`.swarm/c8/proposals/leaf-02.md` if genuinely blocked with cross-piece
weight.

---
leaf_id: leaf-04
spec_file: docs/northstar/plans/push/specs/C8-M3.md
spec_lines: 1-120
test_files:
  - tests/qa/desktop/test_flow_spine.py
impl_files:
  - scenes/debrief/debrief.gd
  - scenes/world/chronicle_scroll_panel.gd
  - scenes/world/chronicle_scroll_panel.tscn
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
  - scenes/mission_briefing/**
  - scenes/tactical_c/**
  - autoload/scene_router.gd
  - autoload/c_bridge.gd
  - scenes/loading_screen/loading_screen.gd
  - scenes/main_menu/main_menu.gd
  - scenes/galaxy/galaxy_view.gd
  - scenes/galaxy/galaxy_view.tscn
  - scenes/mission_briefing/mission_briefing.gd
  - scenes/tactical_c/tactical_view.gd
  - scenes/tactical_c/tactical_view.tscn
impl_line_budget: 200
test_assertion_budget: 20
test_owned_by: parent
wave: 1
shard: c8
---

## Task

Leg 4 of piece C8 ("debrief leg") per spec_lines 1-120 of the spec file
above (`docs/northstar/plans/push/specs/C8-M3.md` — read the piece spec
`docs/northstar/plans/push/specs/C8.md` it cites too, in full).

1. `scenes/debrief/debrief.gd`'s `_build_ui()` already has a Continue
   button (`continue_btn.text = "CONTINUE"`, `pressed.connect(_on_continue)`).
   `_on_continue()` (around line 496) currently does
   `UIDataBus.trigger_autosave("post_debrief")`, `debrief_completed.emit()`,
   optionally `SimBridge.send_command(...)`, then
   `SceneRouter.go_to("time_jump")`. Give the button a stable `name`:
   `continue_btn.name = "Continue"`, and change `_on_continue`'s final
   `go_to` call to `"chronicle"` (the new route a sibling leaf is adding
   in parallel — you don't need it to exist yet to write this correctly).
   Keep the autosave/signal side effects exactly as they are, only the
   destination scene name changes.
   **`debrief.gd` has no `_ready()` at all today** — `_build_ui()` only
   ever runs from `setup(params)`. Add a `_ready()` that calls
   `_build_ui()` when reached fresh (mirror
   `mission_briefing.gd`'s existing `if _data.is_empty(): ... _build_ui()`
   pattern in its own `_ready()` — read that file's `_ready()` for the
   exact shape to mirror, `debrief.gd` has an equivalent empty-check it
   can use, e.g. `_params.is_empty()`), and ALSO self-load the fixture
   debrief frame on that same fresh-reached path — read
   `tests/fixtures/debrief_frame_seed11.json` and call own `load_frame()`
   with it, so `_debrief()`'s existing frame-derived fallback (built by
   piece C4) has real content to show.
2. `scenes/world/chronicle_scroll_panel.gd` / `.tscn` (root
   `PanelContainer` "ChronicleScrollPanel", no `_ready()` self-load, no
   Return button, not yet a routed top-level scene — a sibling leaf adds
   the `"chronicle"` SCENES entry pointing directly at this `.tscn` in
   parallel, you don't need that route to exist yet to write this
   correctly): add or extend `_ready()` to self-load, when reached fresh
   through this flow: read `tests/transport/fixtures/snapshot_seed1_tick10.json`
   and call own `set_snapshot()`, then read
   `tests/fixtures/chronicle_frame_seed11.json` and call own
   `load_frame()` with it. Also add a `Return` button as a direct child
   of the panel (or inside whatever container `_build_ui`/equivalent
   already constructs — read the file first for its existing structure)
   whose click handler calls `SceneRouter.go_to("galaxy")` (the existing
   route another leaf is adding in parallel).

## Acceptance

You are working inside your own git worktree — a private checkout at
`.swarm/c8/worktrees/leaf-04/`, which is your working directory and which
the parent manages. Never run git. Nothing you do there is visible to a
sibling leaf or the user's checkout.

This leg isn't independently testable against the full flow. Confirm
instead:
- `scripts/run_godot_tests.sh tests/test_briefing_debrief.gd
  tests/test_chronicle_scroll.gd` stay green (35/35, 58/58 — pure
  regression checks; your `_ready()` additions are new code paths the
  fenced tests don't exercise since they always call `load_frame()`
  themselves after instantiating, which just overwrites whatever your
  new self-load produced).
- Write a small temporary headless script (delete before finishing) that
  instantiates `debrief.tscn` fresh (no `setup()` call) and confirms
  `qa_state()` shows non-default content (e.g. `band` is one of the real
  `BAND_NAMES` values matching the fixture, not whatever a totally-empty
  frame would default to) — proving your new `_ready()` self-load
  actually ran. Same for `chronicle_scroll_panel.tscn`: instantiate
  fresh, confirm `qa_state().entries.size() == 6` (the fixture's known
  entry count) without any external `load_frame()`/`set_snapshot()` call.
  Also confirm both scenes show a child node named `"Continue"` /
  `"Return"` respectively, visible.

Do not stage, copy, commit, or move anything.

## Escalation triggers

Stop and report to the parent if:
- The impl would need to create a file not listed in `impl_files`.
- The impl would need to edit any file in `do_not_edit`, including
  `autoload/scene_router.gd` (a sibling leaf owns it).
- Impl approaches `impl_line_budget` (200).

## Assumption log

Log any inference (exact `_ready()` fresh-vs-setup detection condition
for `debrief.gd`, Return button placement inside the chronicle panel,
fixture-read error handling) to
`.swarm/c8/briefs/leaf-04.ASSUMPTIONS.md`, citing the spec section.

## Sibling-assumption read

Three sibling leaves build in parallel. leaf-01 owns
`autoload/scene_router.gd` (you reference `SCENES["chronicle"]` and
`SCENES["galaxy"]` — the latter is another sibling's addition too,
neither needs to exist in your own worktree to write this correctly).
Check `.swarm/c8/briefs/leaf-01.ASSUMPTIONS.md` for the exact chronicle
key name it picked, since your `_on_continue` retarget must match it
exactly — this is the one place a mismatch would actually break the
combined flow, so read that file if it exists before finalizing your key
string (if it doesn't exist yet, use `"chronicle"` as specced and note
you didn't find confirmation).

## Question ledger / contract-proposal protocol

Standard shape at `.swarm/c8/questions/leaf-04-Q<n>.md` /
`.swarm/c8/proposals/leaf-04.md` if genuinely blocked with cross-piece
weight.

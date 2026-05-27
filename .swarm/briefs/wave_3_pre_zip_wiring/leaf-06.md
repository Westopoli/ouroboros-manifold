---
leaf_id: leaf-06
spec_file: docs/test_specs/wave_3_pre_zip_wiring.md
spec_lines: 197-204
test_file: tests/test_b3_tutorial_integration.gd
impl_file: autoload/tutorial_state_machine.gd
impl_files:
  - scenes/main_menu/main_menu.gd
  - scenes/tactical/tactical.gd
  - project.godot
contract_imports:
do_not_edit:
  - autoload/theme_constants.gd
  - autoload/sim_bridge.gd
  - tests/test_b5_release_mode.gd
  - simulation/test_wave3_blockers_umbrella.py
  - tests/test_wave3_blockers_umbrella.gd
  - docs/test_specs/wave_3_pre_zip_wiring.md
  - docs/bible/**
  - docs/phase1_ship_plan.md
  - docs/priority_queue.md
  - simulation/tick.py
  - simulation/drift.py
  - simulation/faction.py
  - simulation/region.py
  - simulation/events.py
  - simulation/event_engine.py
  - simulation/intent_resolver.py
  - simulation/border_friction.py
  - simulation/technology.py
  - simulation/diplomacy.py
  - simulation/world.py
  - simulation/templates.py
  - simulation/theme_scifi.py
impl_line_budget: 200
test_assertion_budget: 20
wave: 3
---

## Framing

Game = pause-and-command tactical w/ generational chronicle. Player commands troops mid-mission (tactical layer) + watches civilization rise/fall via auto-advancing chronicle (world layer). Missions auto-trigger post-time-jump — no manual mission selection from world map. NOT an RTS. NOT a 4X. Phase 1 reframe doc: `/Users/westley/.claude/plans/synchronous-stargazing-widget.md` + `docs/bible/game_bible.md ## In Flux ### PIVOT 2026-05-18`.

## Task

Create `autoload/tutorial_state_machine.gd` (NEW file) implementing the once-ever first-mission tutorial controller per spec lines 35-56 + 197-204.

State machine responsibilities (per spec contract section):
- `_ready()`: check `FileAccess.file_exists("user://tutorial_completed")` → set internal `_completed = true` if present.
- Listen for these signals (per locked allowlist): `mission_load`, `first_unit_visible`, `first_unit_selected`, `first_mission_loaded`, `first_mission_complete`. Each signal maps 1-to-1 to a tutorial beat (TUT_001..TUT_005). Use `beats.json` trigger_event field to route (leaf-04 already wired this; brief codebase_precondition would verify but is captured here as assumption — see assumption log if absent at impl time).
- On signal fire AND `_completed == false`: instantiate `scenes/tutorial/tutorial_overlay.tscn` (if not already in tree) → call `show_beat(beat_id)`.
- On `TutorialOverlay.beat_dismissed(beat_id)` signal: if beat_id == "TUT_005" → write `user://tutorial_completed` via `FileAccess.open + close`, set `_completed = true`, emit own signal `tutorial_completed`.
- Public method `reset_for_replay()`: deletes `user://tutorial_completed` via `DirAccess.remove_absolute(ProjectSettings.globalize_path(...))`, sets `_completed = false`, ready for next mission cycle.
- Emit signal `beat_fired(beat_id: String)` whenever a beat is shown.
- Emit signal `tutorial_completed` on TUT_005 dismissal.

Register the autoload in `project.godot [autoload]` section: add line `TutorialStateMachine="*res://autoload/tutorial_state_machine.gd"`. Do NOT modify other autoload entries. Do NOT touch other `project.godot` sections.

In `scenes/main_menu/main_menu.gd` (line 100 currently has hardcoded `version.text = "v0.9.0"`), add Button labeled `"Replay Tutorial"`. On press: call `TutorialStateMachine.reset_for_replay()`. Button placement: bottom of menu, do not displace existing CONTINUE/NEW GAME flow.

In `scenes/tactical/tactical.gd`, emit signals `first_unit_visible` and `first_unit_selected`. Existing infrastructure to hook into:

- `first_unit_visible` — `TacticalBridge.snapshot_received` signal already connected at tactical.gd line 88 with `CONNECT_ONE_SHOT` flag (one-time first-snapshot handler `_on_first_snapshot`). Add a call to fire `first_unit_visible` from inside `_on_first_snapshot` (or by extending the existing CONNECT_ONE_SHOT pattern) after verifying `TacticalBridge.units.size() > 0`.
- `first_unit_selected` — selection signals likely originate from `scripts/tactical/selection.gd` or similar. Sub-agent investigates at impl time. If no clear signal source exists, escalate via question ledger (`.swarm/questions/leaf-06-Q<n>.md`) before guessing.

Emit each at most once per scene instance (use member flag `_emitted_first_unit_visible: bool` etc.). Call `TutorialStateMachine.<emit_via_method>` OR connect signals from tactical.gd to TutorialStateMachine. Do NOT emit `mission_load`/`first_mission_loaded`/`first_mission_complete` from tactical.gd — those originate elsewhere (mission lifecycle, NOT in tactical.gd scope).

Test file `tests/test_b3_tutorial_integration.gd` is a `SceneTree` headless test. Asserts: (1) `TutorialStateMachine` autoload accessible via `get_root().get_node_or_null("TutorialStateMachine")`; (2) state machine has `beat_fired` + `tutorial_completed` signals; (3) state machine has `reset_for_replay()` method; (4) when `user://tutorial_completed` absent + state machine receives `mission_load` signal → emits `beat_fired("TUT_001")` (or equivalent first beat); (5) sequential signal fires advance through beats 1-5; (6) after TUT_005 dismissal → `user://tutorial_completed` file exists; (7) after flag exists + state machine receives `mission_load` → no `beat_fired` emission (early-return path); (8) calling `reset_for_replay()` → flag file deleted + next `mission_load` re-fires TUT_001; (9) `main_menu.tscn` instantiated contains Button with text containing "Tutorial" (case-insensitive); (10) `tactical.gd` exports or refers to symbols `first_unit_visible` / `first_unit_selected` (signal connection or emit call).

Brief acceptance from spec lines 197-204.

## Acceptance

Run `bash scripts/run_godot_tests.sh tests/test_b3_tutorial_integration.gd` for this test_file. Confirm RED. Implement in impl_files only. Confirm GREEN. Write your final `test_file` and `impl_files` to `.swarm/pending/leaf-06/` mirroring their paths from the project root. Stop.

**HARD RULE: STAGING ONLY.** All writes go to `.swarm/pending/leaf-06/<path>`. Violation = leaf rejected.

**CROSS-WAVE FILE OWNERSHIP:** This brief edits `project.godot` (autoload section addition). Leaf-01 (wave 1) edited the autoload section earlier for DebugOverlay. Read current `project.godot` state at impl time — leaf-01 already merged. ADD `TutorialStateMachine` line to existing autoload section. Do NOT touch leaf-01's DebugOverlay entry. Do NOT touch leaf-07's `[application]` section edits (leaf-07 is same wave 3 — sibling; check leaf-07.md brief for surface non-overlap before editing project.godot).

## Escalation triggers

Stop and report to the parent if:
- `scenes/tutorial/tutorial_overlay.gd` does not exist or lacks `show_beat(beat_id)` method.
- `beats.json` trigger_event fields still contain `_TBD` placeholder (leaf-04 precondition not met).
- `scenes/main_menu/main_menu.tscn` structure does not permit Button addition without breaking existing layout.
- `scenes/tactical/tactical.gd` does not expose a clear post-snapshot hook for `first_unit_visible` emission.
- Impl approaches impl_line_budget with assertions still failing.

## Assumption log

Inferences expected: exact `first_unit_visible` emission site in tactical.gd; reset_for_replay implementation details; main menu Button positioning. Append to `.swarm/briefs/wave_3_pre_zip_wiring/leaf-06.ASSUMPTIONS.md`.

## Sibling-assumption read

Before logging, list sibling ASSUMPTIONS, grep for "TutorialStateMachine", "tutorial", "main_menu", "project.godot", "autoload". Adopt or escalate. Special attention to leaf-04 (beats.json contract) + leaf-07 (project.godot sibling-wave editor).

## Question ledger

Publish to `.swarm/questions/leaf-06-Q<n>.md` if ambiguous.

## Contract-proposal protocol

Standard protocol.

---
leaf_id: leaf-02
spec_file: docs/test_specs/wave_3_pre_zip_wiring.md
spec_lines: 172-177
test_file: tests/test_privacy_modal.gd
impl_file: scenes/privacy_modal/privacy_modal.gd
impl_files:
  - scenes/privacy_modal/privacy_modal.tscn
contract_imports:
do_not_edit:
  - build/pyinstaller_win.spec
  - project.godot
  - simulation/test_b5_pyinstaller_specs.py
  - simulation/mission_briefing.py
  - simulation/pipe_transport.py
  - simulation/test_b2_briefing_short_objective.py
  - simulation/library/tutorial/beats.json
  - simulation/test_b3_tutorial_beats_schema.py
  - scenes/mission_briefing/mission_briefing.gd
  - autoload/scene_router.gd
  - tests/test_b2_briefing_scene.gd
  - autoload/tutorial_state_machine.gd
  - scenes/main_menu/main_menu.gd
  - scenes/tactical/tactical.gd
  - tests/test_b3_tutorial_integration.gd
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
impl_line_budget: 100
test_assertion_budget: 10
wave: 1
---

## Framing

Game = pause-and-command tactical w/ generational chronicle. Player commands troops mid-mission (tactical layer) + watches civilization rise/fall via auto-advancing chronicle (world layer). Missions auto-trigger post-time-jump — no manual mission selection from world map. NOT an RTS. NOT a 4X. Phase 1 reframe doc: `/Users/westley/.claude/plans/synchronous-stargazing-widget.md` + `docs/bible/game_bible.md ## In Flux ### PIVOT 2026-05-18`.

## Task

Create privacy disclosure modal scene + script. Scene path: `scenes/privacy_modal/privacy_modal.tscn`. Script path: `scenes/privacy_modal/privacy_modal.gd`. Scene displays the verbatim text quoted in spec lines 60-69 inside a Label or RichTextLabel — copy the four-paragraph block from the spec exactly (including the opening header `PRIVATE PLAYTEST BUILD`). Single Button with label `"Accept & Continue"` (per U-6). On button press: write empty file at `user://privacy_accepted` via `FileAccess.open(path, FileAccess.WRITE)` → `close()`, then call `SceneRouter.go_to("loading_screen")`.

In `_ready()`: check `FileAccess.file_exists("user://privacy_accepted")` — if true, immediately call `SceneRouter.go_to("loading_screen")` without rendering modal (per spec line 174 acceptance criterion 4).

Test file `tests/test_privacy_modal.gd` is a `SceneTree` headless test (per existing pattern in `tests/test_wave3_blockers_umbrella.gd`). Asserts: (1) scene loads via `ResourceLoader.exists()` and `load()`; (2) instantiated scene has Button with text matching `"Accept"` or `"Continue"`; (3) instantiated scene has Label/RichTextLabel containing `"PRIVATE PLAYTEST BUILD"`; (4) script defines method handling button press (grep for `pressed` signal connection); (5) script references `user://privacy_accepted` literal string; (6) with `user://privacy_accepted` pre-written, scene's `_ready()` does NOT add modal children visible to user (e.g. count_visible_buttons==0 or `_skip_to_loading_screen` flag set). Use `FileAccess` to set up + tear down test fixture file.

`run_godot_tests.sh tests/test_privacy_modal.gd` is the run command.

Brief acceptance from spec lines 172-177.

## Acceptance

Run `bash scripts/run_godot_tests.sh tests/test_privacy_modal.gd` for this test_file. Confirm RED. Implement in impl_files only. Confirm GREEN. Write your final `test_file` and `impl_files` to `.swarm/pending/leaf-02/` mirroring their paths from the project root. Stop. Do not copy files to their real destinations — `/swarm-merge` does that after gating.

**HARD RULE: STAGING ONLY.** All writes go to `.swarm/pending/leaf-02/<path>`. Violation = leaf rejected.

## Escalation triggers

Stop and report to the parent if:
- `SceneRouter` autoload does not expose `go_to(route_name: String)` method.
- The route name `"loading_screen"` is not recognized by SceneRouter (check existing routing table).
- Test runner `scripts/run_godot_tests.sh` does not exist.
- Impl approaches impl_line_budget with assertions still failing.

## Assumption log

If you infer anything not in this brief, append to `.swarm/briefs/wave_3_pre_zip_wiring/leaf-02.ASSUMPTIONS.md` before staging.

## Sibling-assumption read (do this before logging)

Before logging, list `.swarm/briefs/wave_3_pre_zip_wiring/leaf-??.ASSUMPTIONS.md`, grep for related terms ("privacy", "user://", "SceneRouter", "FileAccess"), adopt or escalate per protocol.

## Question ledger

Publish to `.swarm/questions/leaf-02-Q<n>.md` if brief ambiguous on material impl shape. Proceed with best-guess.

## Contract-proposal protocol

If brief requires editing parent-owned file, write `.swarm/proposals/leaf-02.md`. Do not edit parent-owned files directly.

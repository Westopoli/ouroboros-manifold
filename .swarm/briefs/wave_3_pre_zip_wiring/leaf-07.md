---
leaf_id: leaf-07
spec_file: docs/test_specs/wave_3_pre_zip_wiring.md
spec_lines: 206-211
test_file: tests/test_b5_release_mode.gd
impl_file: project.godot
impl_files:
  - autoload/theme_constants.gd
  - autoload/sim_bridge.gd
contract_imports:
do_not_edit:
  - autoload/tutorial_state_machine.gd
  - scenes/main_menu/main_menu.gd
  - scenes/tactical/tactical.gd
  - tests/test_b3_tutorial_integration.gd
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
impl_line_budget: 120
test_assertion_budget: 12
wave: 4
---

## Framing

Game = pause-and-command tactical w/ generational chronicle. Player commands troops mid-mission (tactical layer) + watches civilization rise/fall via auto-advancing chronicle (world layer). Missions auto-trigger post-time-jump — no manual mission selection from world map. NOT an RTS. NOT a 4X. Phase 1 reframe doc: `/Users/westley/.claude/plans/synchronous-stargazing-widget.md` + `docs/bible/game_bible.md ## In Flux ### PIVOT 2026-05-18`.

## Task

Wire release-mode detection + custom user directory + sim binary exec branching per spec lines 73-86 + 206-211.

In `project.godot`:
- Set `[application]` key `run/main_scene="res://scenes/privacy_modal/privacy_modal.tscn"` (replacing current `loading_screen.tscn`). Privacy modal precedes loading screen per spec line 84 main scene chain.
- Add `[application]` keys `config/use_custom_user_dir=true` and `config/custom_user_dir_name="data"` (per spec line 79). Side effect: logs + saves go to `<game_root>/data/` instead of `~/.local/share/godot/...`.
- Do NOT touch `[autoload]` section (sibling-wave leaf-06 edits it for TutorialStateMachine; leaf-01 already edited it for DebugOverlay in wave 1). Do NOT touch `[display]`, `[physics]`, `[rendering]` sections.

In `autoload/theme_constants.gd:4`: replace
```gdscript
const IS_RELEASE_BUILD: bool = false
```
with
```gdscript
const IS_RELEASE_BUILD: bool = OS.has_feature("release_build")
```
Do NOT modify any other line in `theme_constants.gd` (color constants, era accents, font loading all preserve).

In `autoload/sim_bridge.gd` `_spawn_sim()` method (signature: `func _spawn_sim(extra_args: PackedStringArray = PackedStringArray()) -> void:` at line 116): branch on `ThemeConstants.IS_RELEASE_BUILD` INSIDE the existing function body. Do NOT change the function signature. Do NOT add a new function.

Existing function constructs `args: PackedStringArray = [script, "--cmd-file", _cmd_file_path, "--units", ..., "--save-root", save_root]` then calls `OS.execute_with_pipe("python3", args)`.

Modify to:
- If `ThemeConstants.IS_RELEASE_BUILD == true`: replace `"python3"` exec target with `<game_root>/sim/ouroboros_sim` (Mac) OR `<game_root>/sim/ouroboros_sim.exe` (Windows — detect via `OS.has_feature("windows")`). Drop `script` (the python script path) from args since the bundled binary IS the entry point. Append `--root <game_root>` to args. `<game_root>` resolved via `OS.get_executable_path().get_base_dir()` (per U-8). pipe_transport.py already supports `--root` arg (line 1283).
- If `false` (dev): unchanged existing path — `OS.execute_with_pipe("python3", args)` with script-path-first args.

Do NOT change `SimBridge` signals (`progress_updated`, `sim_ready`, `state_updated`, `sim_error`). Do NOT change command channel pattern (temp file for writes, stdio for reads). Do NOT touch `_kill_sim`, `restart`, `send_command`, `_notification`, `_route_to_error_screen`, `_read_framed`, or any other method. Inside `_spawn_sim`, only the exec-target + args-construction lines change.

Test file `tests/test_b5_release_mode.gd` is a `SceneTree` headless test. Asserts: (1) `ProjectSettings.get_setting("application/run/main_scene")` == `"res://scenes/privacy_modal/privacy_modal.tscn"`; (2) `ProjectSettings.get_setting("application/config/use_custom_user_dir")` == `true`; (3) `ProjectSettings.get_setting("application/config/custom_user_dir_name")` == `"data"`; (4) `ThemeConstants.IS_RELEASE_BUILD` is a bool (callable to verify type); (5) source-grep `autoload/theme_constants.gd` for `OS.has_feature("release_build")`; (6) source-grep `autoload/sim_bridge.gd` for both `IS_RELEASE_BUILD` (or `release_build`) AND `--root`; (7) source-grep `autoload/sim_bridge.gd` for `OS.has_feature("windows")` branching OR equivalent platform detection; (8) `ThemeConstants` autoload accessible via `get_root().get_node_or_null("ThemeConstants")`.

Brief acceptance from spec lines 206-211.

## Acceptance

Run `bash scripts/run_godot_tests.sh tests/test_b5_release_mode.gd` for this test_file. Confirm RED. Implement in impl_files only. Confirm GREEN. Write your final `test_file` and `impl_files` to `.swarm/pending/leaf-07/` mirroring their paths from the project root. Stop.

**HARD RULE: STAGING ONLY.** All writes go to `.swarm/pending/leaf-07/<path>`. Violation = leaf rejected.

**CROSS-WAVE + SIBLING-WAVE FILE OWNERSHIP:** This brief edits `project.godot` (`[application]` section). Leaf-01 (wave 1) edited `[autoload]` section (DebugOverlay). Leaf-06 (wave 3, sibling) edits `[autoload]` section (TutorialStateMachine). Read current `project.godot` state at impl time and read leaf-06's brief — your edits to `[application]` MUST NOT collide with leaf-06's `[autoload]` edits. Stage your project.godot version with both sets of edits applied IF leaf-06 has already staged. Otherwise stage your version with ONLY `[application]` changes + leaf-01's pre-merged DebugOverlay entry intact. Coordination via `.swarm/pending/leaf-06/project.godot` if it exists.

## Escalation triggers

Stop and report to the parent if:
- `autoload/theme_constants.gd:4` constant declaration does not match expected `const IS_RELEASE_BUILD: bool = false` format.
- `autoload/sim_bridge.gd._spawn_sim()` method signature differs from current `func _spawn_sim(extra_args: PackedStringArray = PackedStringArray()) -> void:` shape (line 116).
- `OS.get_executable_path()` returns empty string under test harness (would block release-path resolution).
- `project.godot` `[application]` section state conflicts with leaf-06's staged version irreconcilably.
- Impl approaches impl_line_budget with assertions still failing.

## Assumption log

Inferences expected: `<game_root>` resolution method (per U-8: `OS.get_executable_path().get_base_dir()`); Windows binary suffix detection; sim/ subdir convention. Append to `.swarm/briefs/wave_3_pre_zip_wiring/leaf-07.ASSUMPTIONS.md`.

## Sibling-assumption read

Before logging, list sibling ASSUMPTIONS, grep for "project.godot", "main_scene", "IS_RELEASE_BUILD", "sim_bridge", "autoload". Coordinate with leaf-06 on project.godot footprint. Adopt or escalate.

## Question ledger

Publish to `.swarm/questions/leaf-07-Q<n>.md` if ambiguous.

## Contract-proposal protocol

Standard protocol.

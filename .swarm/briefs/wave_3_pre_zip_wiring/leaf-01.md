---
leaf_id: leaf-01
spec_file: docs/test_specs/wave_3_pre_zip_wiring.md
spec_lines: 167-170
test_file: simulation/test_b5_pyinstaller_specs.py
impl_file: build/pyinstaller_win.spec
impl_files:
  - project.godot
contract_imports:
do_not_edit:
  - scenes/privacy_modal/**
  - scenes/privacy_modal/privacy_modal.tscn
  - scenes/privacy_modal/privacy_modal.gd
  - simulation/test_privacy_modal_isolated.py
  - tests/test_privacy_modal.gd
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
impl_line_budget: 120
test_assertion_budget: 10
wave: 1
---

## Framing

Game = pause-and-command tactical w/ generational chronicle. Player commands troops mid-mission (tactical layer) + watches civilization rise/fall via auto-advancing chronicle (world layer). Missions auto-trigger post-time-jump — no manual mission selection from world map. NOT an RTS. NOT a 4X. Phase 1 reframe doc: `/Users/westley/.claude/plans/synchronous-stargazing-widget.md` + `docs/bible/game_bible.md ## In Flux ### PIVOT 2026-05-18`.

## Task

Create Windows PyInstaller spec at `build/pyinstaller_win.spec` and register the existing `DebugOverlay` autoload in `project.godot`. The Windows spec mirrors `build/pyinstaller_spec.spec` (Mac, already on disk) — same `Analysis` entry point `simulation/pipe_transport.py`, same 76 hidden_imports, same data files (`library/`, `layout_library/`, `scripts/`, `prompts/`), same `COLLECT` name `ouroboros_sim` (per spec lines 76-86 and U-5). PyInstaller adds `.exe` suffix on Windows automatically — do not hardcode it.

Add exactly one line to `project.godot` under the existing `[autoload]` section: `DebugOverlay="*res://autoload/debug_overlay.gd"`. The file `autoload/debug_overlay.gd` already exists (79 lines, F3-toggle FPS/tick/units). Do not modify it. Do not touch `[application]`, `[display]`, `[physics]`, `[rendering]`, or any other section of `project.godot`.

Test file `simulation/test_b5_pyinstaller_specs.py` asserts: (1) both `build/pyinstaller_spec.spec` (Mac) and `build/pyinstaller_win.spec` (Win) parse as Python source via `ast.parse()`; (2) both declare identical `hidden_imports` sets; (3) both declare same data-files list; (4) COLLECT name is `ouroboros_sim` in both; (5) `project.godot` contains exact regex `r'^DebugOverlay\s*=\s*"\*res://autoload/debug_overlay\.gd"$'` (multiline-aware match).

Brief acceptance from spec lines 167-170.

## Acceptance

Run `cd simulation && python3 -m pytest test_b5_pyinstaller_specs.py -v` for this test_file. Confirm RED. Implement in impl_files only. Confirm GREEN. Write your final `test_file` and `impl_files` to `.swarm/pending/leaf-01/` mirroring their paths from the project root (e.g. `build/pyinstaller_win.spec` → `.swarm/pending/leaf-01/build/pyinstaller_win.spec`). Stop. Do not copy files to their real destinations — `/swarm-merge` does that after gating.

**HARD RULE: STAGING ONLY.** All writes go to `.swarm/pending/leaf-01/<path>`. Do not write to `build/pyinstaller_win.spec` or `project.godot` directly. Violation = leaf rejected.

## Escalation triggers

Stop and report to the parent if:
- The Mac spec at `build/pyinstaller_spec.spec` does not exist (precondition violated).
- The Windows spec needs hidden_imports beyond what Mac declares.
- `project.godot` autoload section format differs from current `Name="*res://path.gd"` convention.
- Impl approaches impl_line_budget with assertions still failing.

## Assumption log

If you infer anything not in this brief, append to `.swarm/briefs/wave_3_pre_zip_wiring/leaf-01.ASSUMPTIONS.md` before staging. Format per template.

## Sibling-assumption read (do this before logging)

Before logging any inference, list `.swarm/briefs/wave_3_pre_zip_wiring/leaf-??.ASSUMPTIONS.md`, grep for related terms (e.g. "project.godot", "autoload", "PyInstaller"), and adopt or escalate per protocol.

## Question ledger

If brief ambiguity materially shapes impl, publish question to `.swarm/questions/leaf-01-Q<n>.md` with best-guess. Proceed with guess. Parent answers via `.swarm/answers/leaf-01-Q<n>.md`.

## Contract-proposal protocol

If satisfying brief requires editing a parent-owned file, write `.swarm/proposals/leaf-01.md` with proposed diff. Do not edit parent-owned files directly.

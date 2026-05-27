---
leaf_id: leaf-05
spec_file: docs/test_specs/wave_3_pre_zip_wiring.md
spec_lines: 190-195
test_file: tests/test_b2_briefing_scene.gd
impl_file: scenes/mission_briefing/mission_briefing.gd
impl_files:
  - autoload/scene_router.gd
contract_imports:
do_not_edit:
  - simulation/library/tutorial/beats.json
  - simulation/test_b3_tutorial_beats_schema.py
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
impl_line_budget: 140
test_assertion_budget: 12
wave: 2
---

## Framing

Game = pause-and-command tactical w/ generational chronicle. Player commands troops mid-mission (tactical layer) + watches civilization rise/fall via auto-advancing chronicle (world layer). Missions auto-trigger post-time-jump — no manual mission selection from world map. NOT an RTS. NOT a 4X. Phase 1 reframe doc: `/Users/westley/.claude/plans/synchronous-stargazing-widget.md` + `docs/bible/game_bible.md ## In Flux ### PIVOT 2026-05-18`.

## Task

Add `short_objective_header` RichTextLabel node above the existing MISSION OBJECTIVES section in `scenes/mission_briefing/mission_briefing.gd` (692 lines; MISSION OBJECTIVES label at line 202). Header reads the existing `objective` key from briefing dict — already populated sim-side from `OBJECTIVE_TEMPLATES_SHORT` for all 10 archetypes (no sim-side work required; verified 2026-05-26).

Style per spec acceptance B2-B criteria 1-3:

- Era-active accent color via existing `_accent` member (line 11 pattern: `_accent = ThemeConstants.get_era_accent(_data.get("era_id", "roman"))`). DO NOT invent `accent_primary` — use the `_accent` Color the scene already computes per-era.
- Apply color via theme color override (`add_theme_color_override("default_color", _accent)`) OR BBCode `[color=#<_accent.to_html(false)>][b]<TEXT-UPPERCASE>[/b][/color]`.
- Font size ≥1.5× body text (per U-2). Achieve via theme override `theme_override_font_sizes/normal_font_size` OR BBCode `[font_size=N]` tag.
- Placed above MISSION OBJECTIVES section (per B2.3).
- Header text = uppercase form of `briefing.objective` value.

Fallback: if briefing dict's `objective` field is missing or empty string → `short_objective_header.visible = false`.

In `autoload/scene_router.gd`, verify the `mission_briefing` route accepts a `mission_id` parameter and passes it through to scene's `setup(params)` method. Existing signature is `func go_to(scene_name: String, params: Dictionary = {}) -> void:` (line 35) — already generic. If `params.mission_id` propagates to the scene's setup correctly with no edit needed, no change to scene_router.gd required. If propagation breaks, add explicit pass-through. Do NOT change routing target scene path. Do NOT touch other routes.

Test file `tests/test_b2_briefing_scene.gd` is a `SceneTree` headless test. Asserts: (1) `mission_briefing.tscn` loads via `ResourceLoader.exists()` + `load()`; (2) instantiated scene's tree contains a node named `short_objective_header`; (3) header is a RichTextLabel; (4) when scene is set up with mock briefing dict containing `{"objective": "Hold the line."}` (via scene's `_data.objective` field) → header.visible == true AND header text contains uppercase "HOLD THE LINE."; (5) header has bbcode_enabled OR theme override applied; (6) with mock briefing `{"objective": ""}` → header.visible == false; (7) with mock briefing `{}` (missing key) → header.visible == false; (8) `SceneRouter.go_to("mission_briefing", {"mission_id": "test_001"})` does not error.

Brief acceptance from spec lines 190-195.

## Acceptance

Run `bash scripts/run_godot_tests.sh tests/test_b2_briefing_scene.gd` for this test_file. Confirm RED. Implement in impl_files only. Confirm GREEN. Write your final `test_file` and `impl_files` to `.swarm/pending/leaf-05/` mirroring their paths from the project root. Stop.

**HARD RULE: STAGING ONLY.** All writes go to `.swarm/pending/leaf-05/<path>`. Violation = leaf rejected.

## Escalation triggers

Stop and report to the parent if:
- `mission_briefing.gd` `setup(params)` signature or briefing-dict access pattern differs from current `UIDataBus.get_mission_briefing(mission_id)` call site (line 10).
- `ThemeConstants` does not expose accent_primary equivalent.
- `SceneRouter.go_to` signature does not accept `params: Dictionary` second arg.
- Existing MISSION OBJECTIVES section ordering breaks under new header insertion.
- Impl approaches impl_line_budget with assertions still failing.

## Assumption log

Append inferences (BBCode size choice, color hex source, fallback text edge cases) to `.swarm/briefs/wave_3_pre_zip_wiring/leaf-05.ASSUMPTIONS.md`.

## Sibling-assumption read

Before logging, list sibling ASSUMPTIONS, grep for "short_objective", "briefing", "header", "BBCode". Adopt or escalate.

## Question ledger

Publish to `.swarm/questions/leaf-05-Q<n>.md` if ambiguous.

## Contract-proposal protocol

Standard protocol.

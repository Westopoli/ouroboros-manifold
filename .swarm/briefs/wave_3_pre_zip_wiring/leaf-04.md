---
leaf_id: leaf-04
spec_file: docs/test_specs/wave_3_pre_zip_wiring.md
spec_lines: 185-188
test_file: simulation/test_b3_tutorial_beats_schema.py
impl_file: simulation/library/tutorial/beats.json
contract_imports:
do_not_edit:
  - scenes/mission_briefing/mission_briefing.gd
  - autoload/scene_router.gd
  - tests/test_b2_briefing_scene.gd
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
impl_line_budget: 60
test_assertion_budget: 12
wave: 2
---

## Framing

Game = pause-and-command tactical w/ generational chronicle. Player commands troops mid-mission (tactical layer) + watches civilization rise/fall via auto-advancing chronicle (world layer). Missions auto-trigger post-time-jump — no manual mission selection from world map. NOT an RTS. NOT a 4X. Phase 1 reframe doc: `/Users/westley/.claude/plans/synchronous-stargazing-widget.md` + `docs/bible/game_bible.md ## In Flux ### PIVOT 2026-05-18`.

## Task

Replace literal `trigger_event_TBD` strings in `simulation/library/tutorial/beats.json` with locked trigger event names (per spec lines 150-156):

- TUT_001: `mission_load`
- TUT_002: `first_unit_visible`
- TUT_003: `first_unit_selected`
- TUT_004: `first_mission_loaded`
- TUT_005: `first_mission_complete`

Also rename the JSON field `trigger_event_TBD` → `trigger_event` on every beat. Do NOT modify any other field (`id`, `headline`, `body`, `pointed_anchor`, `accent_hint`) on any beat. Do NOT add new beats or remove existing beats. The file remains 5 beats total.

Test file `simulation/test_b3_tutorial_beats_schema.py` asserts: (1) `beats.json` loads as JSON list of length 5; (2) every beat has all 6 required fields: `id`, `trigger_event`, `headline`, `body`, `pointed_anchor`, `accent_hint`; (3) no beat has placeholder `trigger_event_TBD`; (4) each beat's `trigger_event` value is in the locked allowlist set `{"mission_load", "first_unit_visible", "first_unit_selected", "first_mission_loaded", "first_mission_complete"}`; (5) the trigger_event values across the 5 beats form exactly that allowlist set (no duplicates, no missing); (6) ordering: TUT_001 → mission_load, TUT_002 → first_unit_visible, etc. per the mapping above.

Brief acceptance from spec lines 185-188.

## Acceptance

Run `cd simulation && python3 -m pytest test_b3_tutorial_beats_schema.py -v` for this test_file. Confirm RED. Implement in impl_file only. Confirm GREEN. Write your final `test_file` and `impl_file` to `.swarm/pending/leaf-04/` mirroring their paths from the project root. Stop.

**HARD RULE: STAGING ONLY.** All writes go to `.swarm/pending/leaf-04/<path>`. Violation = leaf rejected.

## Escalation triggers

Stop and report to the parent if:
- `beats.json` does not contain exactly 5 beats (precondition violated).
- A beat's existing fields are malformed (missing `id`, malformed JSON).
- Impl approaches impl_line_budget with assertions still failing.

## Assumption log

If inference required, append to `.swarm/briefs/wave_3_pre_zip_wiring/leaf-04.ASSUMPTIONS.md`.

## Sibling-assumption read

Before logging, list sibling ASSUMPTIONS files, grep for "trigger_event", "beats", "tutorial". Adopt or escalate.

## Question ledger

Publish to `.swarm/questions/leaf-04-Q<n>.md` if ambiguous.

## Contract-proposal protocol

Standard protocol.

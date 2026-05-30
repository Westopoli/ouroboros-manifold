---
leaf_id: leaf-06
spec_file: docs/test_specs/cover_los_rework_spec.md
spec_lines: 38-41
test_file: simulation/test_cover_ai_peek.py
impl_file: simulation/tactical_engine.py
contract_imports:
  - TacticalMap
  - is_in_cover
  - cover_polygon_containing
  - compute_visibility
do_not_edit:
  - docs/bible/game_bible.md
  - docs/bible/bible_simulation.md
  - docs/bible/bible_missions.md
  - docs/bible/bible_chronicle.md
  - docs/bible/bible_antagonist.md
  - docs/bible/bible_monetization.md
  - docs/bible/bible_ai_pipeline.md
  - docs/test_specs/cover_los_rework_spec.md
  - docs/phase1_ship_plan.md
  - docs/priority_queue.md
  - simulation/test_cover_umbrella.py
  - simulation/tactical_map.py
  - simulation/gradient_placer.py
  - simulation/map_generator.py
  - simulation/fog_of_war.py
  - simulation/damage.py
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
  - simulation/test_cover_polygon.py
  - simulation/test_cover_polygon_placement.py
  - simulation/test_cover_visibility.py
  - simulation/test_cover_damage_gate.py
  - simulation/test_cover_integration.py
  - simulation/cover_integration_fixture.py
impl_line_budget: 100
test_assertion_budget: 12
wave: 4
---

## Task

Audit AI targeting in `simulation/tactical_engine.py` for cover-clumping pathology per spec lines 38-41 and 151-152. Apply the minimal fix only if the audit confirms clumping.

Phase A — audit. Run the integration fixture from L7 (`simulation/cover_integration_fixture.py`) or an equivalent in-test fixture: 1 AI-controlled faction defender inside a cover polygon, 1 hostile attacker outside the cover polygon, the attacker visible to the defender via same-polygon NOT being true (i.e., defender can see attacker via fog/sensor; attacker cannot see defender per L4). Run the simulation for 60 ticks. Record: does the defender ever fire? Does the defender ever move? Does the defender leave the cover polygon?

If the defender fires AT LEAST ONCE within 60 ticks AND damage applies (per L5 visibility gate), there is no clumping pathology — stop. Implementation requirement is satisfied without code changes. Write an audit note to `.swarm/briefs/wave_2_5_cover_los/leaf-06.AUDIT.md` describing the run + result. Tests assert the audit's findings.

Phase B — minimal fix (only if Phase A shows clumping). Add a single behavior nudge to the relevant AI targeting / movement code path inside `tactical_engine.py`: when an AI unit is inside a cover polygon AND has at least one enemy in its `visible` set AND that enemy is in a different polygon (or none), advance the AI toward the nearest edge of its own cover polygon until it has line-of-sight (existing `has_combat_los`) to the target. Do not introduce a new behavior tree. Do not modify behavior scripts in other files. Do not touch protected engine files.

Write `simulation/test_cover_ai_peek.py` BEFORE impl (RED first):

1. (Audit assertion) Run the L7 fixture / equivalent for 60 ticks. Either: defender fires ≥ 1 time (clumping NOT present, no fix needed), OR defender does not fire (clumping present, fix needed).
2. After Phase B (if applied): same scenario, 120 ticks — defender either fires OR moves to a position where `has_combat_los` succeeds and then fires.
3. If Phase B applied: defender does not abandon cover entirely (does not leave the cover polygon by more than `cover_edge_advance_max` ticks).
4. Regression guard: AI defender in cover with NO enemies visible behaves identically to pre-Wave-2.5 (idle / hold position).

Confirm RED, implement (Phase A audit + Phase B fix only if needed), confirm GREEN.

## Acceptance

Run `cd simulation && python3 -m pytest test_cover_ai_peek.py -v`. Confirm RED before impl. Confirm GREEN after. Commit the two files (+ AUDIT.md). Stop.

## Escalation triggers

Stop and report to the parent if:
- Phase A clumping audit is inconclusive (defender fires sometimes, doesn't others — flaky).
- Phase B fix requires editing a protected engine file (faction.py, intent_resolver.py, etc.) or a behavior script in another module.
- The minimal nudge requires more than ~40 impl lines.
- Phase B causes a regression in any existing AI/behavior test that this brief does not own. Surface the failing list — do NOT edit those tests.

## Assumption log

If at any point during your run you had to infer something the brief did not specify (the exact AI targeting call path, what "edge of polygon" means geometrically, ticks-to-advance threshold, anything), write it to `.swarm/briefs/wave_2_5_cover_los/leaf-06.ASSUMPTIONS.md` before you commit. Format:

```markdown
## Assumptions made during leaf-06

- **<thing>**: <inferred value> — source: <which spec line / contract symbol / file you looked at, or "no source — pure guess">
```

---
leaf_id: leaf-05
spec_file: docs/test_specs/cover_los_rework_spec.md
spec_lines: 99-105
test_file: simulation/test_cover_damage_gate.py
impl_file: simulation/damage.py
contract_imports:
  - compute_visibility
  - TacticalMap
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
  - simulation/tactical_engine.py
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
  - simulation/test_cover_ai_peek.py
  - simulation/test_cover_integration.py
impl_line_budget: 120
test_assertion_budget: 14
wave: 3
---

## Task

Rip `(1.0 - cover)` cover multiplier from `simulation/damage.py` lines 132-136 and 171-175. Add a visibility gate. Per spec lines 99-105 and 124-128.

Locate every executable expression of the form `(1.0 - cover...)` in `damage.py` (the two known sites: line range 132-136 and 171-175). Remove the multiplier so the damage expression becomes `dmg = base_dmg * mult` (no cover term). Remove any `cover = tactical_map.cover_density(...)` sample lines that exclusively feed those multipliers. Do not delete the `tactical_map.cover_density()` METHOD — that lives in `tactical_map.py` (L2's file, in `do_not_edit`). Only remove the SAMPLE CALLS inside `damage.py`.

Add a visibility gate at the start of each attack-application site. Before any damage is applied, call into `fog_of_war.compute_visibility` (or a per-attacker visibility helper the existing damage module already imports — check existing imports first; do not introduce a new import path if a working one exists). If the attacker cannot see the target (`target.uid not in attacker_visible_set`), return 0 damage / skip the attack. Preserve the existing `has_combat_los(navmesh, ax, ay, tx, ty)` check from line 37 — both checks must pass for damage to apply.

No regression in non-cover combat: when target is outside all cover polygons, damage equals exactly `base_dmg * mult` (same as before, minus the now-removed cover term — value will change for fixtures that previously had cover > 0).

Write `simulation/test_cover_damage_gate.py` BEFORE impl (RED first). Build minimal fixtures:

1. Attacker outside cover, target inside cover polygon, different factions, attacker's `visible` set does NOT contain target → damage applied = 0.
2. Attacker inside the same cover polygon as target, different factions → damage applied = `base_dmg * mult` exactly (no cover multiplier).
3. Attacker outside cover, target outside cover, both visible → damage applied = `base_dmg * mult` exactly (no cover multiplier).
4. Source-code regression guard: re-read `damage.py` after impl, confirm no non-comment line matches the regex `\(\s*1\.0\s*-\s*cover[^)]*\)`.
5. `tactical_map.cover_density` method still exists and is still callable (regression guard against accidental removal from L2's file).

Confirm RED, implement, confirm GREEN.

## Acceptance

Run `cd simulation && python3 -m pytest test_cover_damage_gate.py -v`. Confirm RED before impl. Implement in `damage.py` only. Confirm GREEN. Then run `cd simulation && python3 -m pytest test_cover_umbrella.py::test_umbrella_d_damage_module_has_no_cover_multiplier test_cover_umbrella.py::test_umbrella_d_attack_at_hidden_target_zero_damage -v` and confirm both umbrella-D tests pass (note: the second one may be a `pytest.skip` stub — surface to parent if it remains skipped after faithful impl). Commit the two files. Stop.

## Escalation triggers

Stop and report to the parent if:
- `damage.py` imports `compute_visibility` from a path that conflicts with the existing import style for the file.
- The attack-application site does not have a uid-keyed visible-set available at the call point (requires upstream plumbing).
- Removing the `cover` sample lines requires deleting an attribute used by an unrelated code path elsewhere in `damage.py`.
- Existing balance tests (test_stage7_*, test_script_*, test_j_duration, etc.) fail. Surface the failing test list — do NOT edit those tests (L7 owns the re-baseline list per `feedback_no_test_modification.md`).
- Impl approaches `impl_line_budget` with assertions still failing.

## Assumption log

If at any point during your run you had to infer something the brief did not specify (visibility-set passing convention, return value when attack skipped vs. damage 0, anything), write it to `.swarm/briefs/wave_2_5_cover_los/leaf-05.ASSUMPTIONS.md` before you commit. Format:

```markdown
## Assumptions made during leaf-05

- **<thing>**: <inferred value> — source: <which spec line / contract symbol / file you looked at, or "no source — pure guess">
```

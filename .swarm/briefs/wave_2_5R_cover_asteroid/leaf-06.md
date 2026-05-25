---
leaf_id: leaf-06
spec_file: docs/test_specs/cover_asteroid_los_spec.md
spec_lines: 51-55
test_file: simulation/test_asteroid_ai_peek.py
impl_file: simulation/tactical_engine.py
contract_imports:
  - tactical_map.TacticalMap
  - tactical_map.Asteroid
  - tactical_map.AsteroidField
  - fog_of_war.compute_visibility
do_not_edit:
  - simulation/test_asteroid_damage_gate.py
  - simulation/asteroid_integration_fixture.py
  - simulation/test_asteroid_integration.py
  - scenes/tactical/terrain_renderer.gd
  - autoload/era_theme_resolver.gd
  - tests/test_cover_render.gd
  - simulation/tactical_map.py
  - simulation/gradient_placer.py
  - simulation/fog_of_war.py
  - simulation/damage.py
  - simulation/snapshot_serializer.py
  - simulation/config.py
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
  - scenes/**
  - autoload/**
  - docs/bible/**
  - docs/test_specs/cover_asteroid_los_spec.md
  - docs/test_specs/cover_los_rework_spec.md
  - simulation/test_asteroid_umbrella.py
  - simulation/test_cover_umbrella.py
impl_line_budget: 80
test_assertion_budget: 10
wave: 3
---

## Task

Audit `simulation/tactical_engine.py` AI targeting paths per spec_lines 51-55. Set up scenario: defender Warden hidden behind tall asteroid cluster, attacker Raider outside. Tick simulation N=120 (~2 sec at 60Hz) ticks. Assert AI does NOT clump indefinitely — at least one attacker either (a) moves toward defender (position delta > 0), (b) acquires a different visible target, or (c) explicitly disengages. Test passes if any of (a/b/c) observed within the N-tick window.

If audit shows AI clumps with zero (a/b/c), add minimal cover-peek nudge in `tactical_engine.py`: when attacker has `auto_engage_target` but target not in `visibility_map[attacker]` AND no other visible enemy, set a one-step move command toward target's last-known position. Full behavior-tree rewrite OUT OF SCOPE (spec line 54).

Tests (spec_line 240):
- Apex scenario: 2 Raider attackers + 1 Warden defender behind asteroid cluster, run 120 ticks, assert at least one of (a/b/c) for at least one attacker.
- Negative control: no asteroid cluster, attackers engage normally → existing behavior intact.

## Acceptance

Run `cd simulation && python3 -m pytest test_asteroid_ai_peek.py -v`. Confirm RED (or already GREEN if AI already handles unseen target gracefully — log finding). Implement minimal fix in impl_file only if RED. Write final files to `.swarm/pending/leaf-06/` mirroring repo paths. Stop.

## Escalation triggers

Stop and report to the parent if:
- A type the test imports is not in contract_imports.
- The impl would need to create a new file.
- The impl would need to edit a file in do_not_edit.
- Two sibling assertions seem to require contradictory behavior.
- Impl approaches impl_line_budget with assertions still failing.
- Audit reveals required fix exceeds "minimal nudge" scope (escalate before editing).

## Assumption log

Log audit findings (current AI behavior vs hidden target, whether nudge needed, what minimal nudge looks like) to `.swarm/briefs/wave_2_5R_cover_asteroid/leaf-06.ASSUMPTIONS.md`.

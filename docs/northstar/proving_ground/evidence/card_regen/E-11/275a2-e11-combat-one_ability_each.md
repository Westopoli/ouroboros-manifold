---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/unit.c implements S-086 card 2 of 3 (om_unit_damage_reduction, om_tactical_telegraph_active, om_tactical_zone_visible_to_enemy, om_unit_set_ability_cooldown, om_tick_read_ability_events)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S086_one_ability_each.py::test_R_086_03_it_immobile_at_once_has"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S086_one_ability_each.py::test_R_086_05_after_30_tick_1_5"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S086_one_ability_each.py::test_R_086_06_for_400_ticks_20_s"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S086_one_ability_each.py::test_R_086_07_command_rejected_nothing_changes"
allowed_files: "csrc/unit.c"
snippet_file: csrc/unit.c
snippet_symbol: "om_unit_damage_reduction,om_tactical_telegraph_active,om_tactical_zone_visible_to_enemy,om_unit_set_ability_cooldown,om_tick_read_ability_events"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-11.md
test_file: tests/csim/test_E11_S086_one_ability_each.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-11-units-and-combat.md (### S-086 — One ability each):

- R-086-03  Given a Vanguard with Brace ready, When activated, Then it is immobile at once, has no bonus for 40 ticks (2 s windup), then takes 50 percent less damage and deals 1.3× while braced; activating again cancels with the same 40-tick windup; cooldown 700 ticks (35 s) starts at activation.
- R-086-05  Given a Bombard with Barrage ready and a target position, When activated, Then after a 30-tick (1.5 s) telegraph visible to both sides, every enemy within 100 wu of the position on the Bombard's layer takes base × 3.0, subject to the AoE cap at 4 × (base × 3.0); cooldown 1,800 ticks (90 s).
- R-086-06  Given a Bastion with Fortify ready, When activated, Then for 400 ticks (20 s) every friendly unit within 350 wu of the Bastion takes 20 percent less damage, the zone moves with the Bastion at speed × 0.4, and the zone is visible to the enemy; cooldown 1,400 ticks (70 s).
- R-086-07  Given an ability on cooldown, When activated, Then the command is rejected and nothing changes.

## Header slice

(run card_slice.py --write after the skeleton lands)

---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/unit.c implements S-086 card 1 of 3 (om_command_activate_ability, om_unit_output_multiplier, om_unit_ability_cooldown, om_unit_ability_active, om_tactical_run_until_engagement_ends)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S086_one_ability_each.py::test_R_086_01_for_60_ticks_3_s"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S086_one_ability_each.py::test_R_086_02_it_triggers_automatically_speed_1"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S086_one_ability_each.py::test_R_086_04_every_friendly_unit_within_400"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S086_one_ability_each.py::test_R_086_08_it_activates_no_other_enemy"
allowed_files: "csrc/unit.c"
snippet_file: csrc/unit.c
snippet_symbol: "om_command_activate_ability,om_unit_output_multiplier,om_unit_ability_cooldown,om_unit_ability_active,om_tactical_run_until_engagement_ends"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-11.md
test_file: tests/csim/test_E11_S086_one_ability_each.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-11-units-and-combat.md (### S-086 — One ability each):

- R-086-01  Given a Raider with Surge ready, When activated, Then for 60 ticks (3 s) speed × 2.5 and damage × 2.0, then cooldown 1,500 ticks (75 s).
- R-086-02  Given an Interceptor with Intercept ready and an enemy Strike unit within 350 wu on its layer, When the check runs, Then it triggers automatically: speed × 1.8 and damage × 1.5 for the first engagement, then cooldown 600 ticks (30 s); the player never activates it.
- R-086-04  Given a Warden with Rally ready, When activated, Then every friendly unit within 400 wu regains 112 HP at once, capped at max HP; cooldown 1,500 ticks (75 s).
- R-086-08  Given an enemy unit, When its ability is ready and the threshold condition holds (an enemy in range for Surge, Brace, Barrage; a damaged friendly in radius for Rally; two or more friendlies in radius for Fortify), Then it activates; no other enemy timing logic exists.

## Header slice

(run card_slice.py --write after the skeleton lands)

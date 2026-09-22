---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/unit.c implements S-083 card 1 of 1 (om_unit_profile_trait_count, om_unit_profile_ability_count, om_unit_apply_trait_modifier, om_unit_set_hp, om_tactical_step)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S083_stats_traits_ability.py::test_R_083_01_it_has_stats_s_082"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S083_stats_traits_ability.py::test_R_083_02_it_modifies_one_stat_or"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S083_stats_traits_ability.py::test_R_083_03_that_unit_takes_10_percent"
allowed_files: "csrc/unit.c"
snippet_file: csrc/unit.c
snippet_symbol: "om_unit_profile_trait_count,om_unit_profile_ability_count,om_unit_apply_trait_modifier,om_unit_set_hp,om_tactical_step"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-11.md
test_file: tests/csim/test_E11_S083_stats_traits_ability.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-11-units-and-combat.md (### S-083 — Stats, traits, ability):

- R-083-01  Given a unit type, When its profile is read, Then it has the stats of S-082, zero to two traits, and exactly one ability.
- R-083-02  Given a trait, When applied, Then it modifies one stat or one multiplier by a fixed amount stated in the profile [Q-083-01: no trait exists in code].
- R-083-03  Given a Warden, When any friendly unit is within 300 wu, Then that unit takes 10 percent less damage and regains 0.075 HP per tick (the Warden's passive aura), stacking with no other Warden.

## Header slice

(run card_slice.py --write after the skeleton lands)

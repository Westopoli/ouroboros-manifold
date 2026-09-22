---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/unit.c implements S-082 card 2 of 2 (om_unit_profile_speed, om_unit_profile_sensor_radius, om_unit_profile_layer_transition_time, om_unit_profile_aoe_radius, om_roster_register_custom_unit)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S082_the_six.py::test_R_082_01_it_exactly_this_table_contract"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S082_the_six.py::test_R_082_02_every_strike_unit_faster_than"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S082_the_six.py::test_R_082_04_both_strike_units_see_farther"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S082_the_six.py::test_R_082_05_only_bombard_has_area_attack"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S082_the_six.py::test_R_082_06_it_declares_category_role_stats"
allowed_files: "csrc/unit.c"
snippet_file: csrc/unit.c
snippet_symbol: "om_unit_profile_speed,om_unit_profile_sensor_radius,om_unit_profile_layer_transition_time,om_unit_profile_aoe_radius,om_roster_register_custom_unit"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-11.md
test_file: tests/csim/test_E11_S082_the_six.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-11-units-and-combat.md (### S-082 — The six):

- R-082-01  Given the launch roster, When loaded, Then it is exactly this table and a contract test checks it:
- R-082-02  Given the roster, When ordered by speed, Then every Strike unit is faster than every Line unit, and every Line unit faster than every Siege unit.
- R-082-04  Given the roster, When sensor radius is read, Then both Strike units see farther than both Siege units.
- R-082-05  Given the roster, When AoE is read, Then only the Bombard has an area attack.
- R-082-06  Given an expansion pack adds a unit type, When loaded, Then it declares category, role, the stats above, and one ability, and no engine code changes.

## Header slice

(run card_slice.py --write after the skeleton lands)

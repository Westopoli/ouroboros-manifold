---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/unit.c implements S-084 card 2 of 3 (om_unit_in_backswing, om_unit_effective_speed, om_map_add_cover, om_era_elevation_damage_bonus_enabled, om_unit_set_elevation_tier)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S084_flat_damage.py::test_R_084_04_unit_pauses_movement_for_0"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S084_flat_damage.py::test_R_084_05_damage_unmodified_e_01_r"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S084_flat_damage.py::test_R_084_06_no_elevation_bonus_applies_engine"
allowed_files: "csrc/unit.c"
snippet_file: csrc/unit.c
snippet_symbol: "om_unit_in_backswing,om_unit_effective_speed,om_map_add_cover,om_era_elevation_damage_bonus_enabled,om_unit_set_elevation_tier"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-11.md
test_file: tests/csim/test_E11_S084_flat_damage.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-11-units-and-combat.md (### S-084 — Flat damage):

- R-084-04  Given a unit fires, When the attack lands, Then the unit pauses movement for 0.5 s (backswing).
- R-084-05  Given a target behind cover, When hit by an attacker who can see it, Then damage is unmodified (E-01 R-007-04).
- R-084-06  Given elevation, When damage is computed in the Settled Reach, Then no elevation bonus applies; the engine computes the tier difference and the era flag is off.

## Header slice

(run card_slice.py --write after the skeleton lands)

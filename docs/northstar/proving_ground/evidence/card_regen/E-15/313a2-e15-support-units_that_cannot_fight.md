---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_support.c implements S-129 card 2 of 3 (om_unit_can_return_fire, om_unit_is_flinching, om_mission_setup_extraction_point, om_mission_check_extraction_objectives, om_mission_get_objective_completion)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E15_S129_units_that_cannot_fight.py::test_R_129_01_it_never_acquires_target_never"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E15_S129_units_that_cannot_fight.py::test_R_129_02_it_counts_toward_completion_e"
allowed_files: "csrc/tactical_support.c"
snippet_file: csrc/tactical_support.c
snippet_symbol: "om_unit_can_return_fire,om_unit_is_flinching,om_mission_setup_extraction_point,om_mission_check_extraction_objectives,om_mission_get_objective_completion"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-15.md
test_file: tests/csim/test_E15_S129_units_that_cannot_fight.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-15-reinforcement-supply-and-hazards.md (### S-129 — Units that cannot fight):

- R-129-01  Given a non-combat unit, When the decision loop runs, Then it never acquires a target, never returns fire, flinches from damage, and otherwise holds or follows its move order.
- R-129-02  Given an escort or evacuation objective, When a non-combat unit reaches the extraction point alive (within 200 wu), Then it counts toward completion (E-10 R-075-04).

## Header slice

(run card_slice.py --write after the skeleton lands)

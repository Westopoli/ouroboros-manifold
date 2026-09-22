---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/mission.c implements S-078 card 1 of 3 (om_consequence_eval_delta_deficit, om_consequence_eval_delta_current, om_consequence_apply_clamped, om_mission_apply_consequences, om_world_set_tick)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S078_a_battle_becomes_history.py::test_R_078_01_each_delta_either_deficit_form"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S078_a_battle_becomes_history.py::test_R_078_02_military_12_0_tension_5"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S078_a_battle_becomes_history.py::test_R_078_03_military_3_0"
allowed_files: "csrc/mission.c"
snippet_file: csrc/mission.c
snippet_symbol: "om_consequence_eval_delta_deficit,om_consequence_eval_delta_current,om_consequence_apply_clamped,om_mission_apply_consequences,om_world_set_tick"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-10.md
test_file: tests/csim/test_E10_S078_a_battle_becomes_history.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-10-missions.md (### S-078 — A battle becomes history):

- R-078-01  Given the archetype's consequence table row for the band, When applied, Then each delta is either deficit form, (100 − current) · pct/100, or current form, current · pct/100, applied to the named target regions and clamped to [0, 100].
- R-078-02  Given defensive_stand total_success on a region with military 20 and tension 50, When applied, Then military +12.0, tension −5.0, economy −2 percent of current.
- R-078-03  Given the same band on military 80, When applied, Then military +3.0.

## Header slice

(run card_slice.py --write after the skeleton lands)

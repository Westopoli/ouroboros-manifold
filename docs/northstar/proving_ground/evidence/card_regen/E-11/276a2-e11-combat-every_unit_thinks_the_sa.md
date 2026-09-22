---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/unit.c implements S-087 card 2 of 2 (om_unit_in_flinch, om_unit_targeting_cohort, om_tactical_target_validation_runs_every_tick)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S087_every_unit_thinks_the_same_way.py::test_R_087_07_it_never_attacks_it_flinches"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S087_every_unit_thinks_the_same_way.py::test_R_087_08_each_unit_re_acquires_on"
allowed_files: "csrc/unit.c"
snippet_file: csrc/unit.c
snippet_symbol: "om_unit_in_flinch,om_unit_targeting_cohort,om_tactical_target_validation_runs_every_tick"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-11.md
test_file: tests/csim/test_E11_S087_every_unit_thinks_the_same_way.py
expected_lines: 36
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-11-units-and-combat.md (### S-087 — Every unit thinks the same way):

- R-087-07  Given a supply or evacuation unit, When the loop runs, Then it never attacks; it flinches and otherwise holds.
- R-087-08  Given target acquisition, When it runs, Then each unit re-acquires on every 4th tick (cohort stagger) and validates its current target every tick.

## Header slice

(run card_slice.py --write after the skeleton lands)

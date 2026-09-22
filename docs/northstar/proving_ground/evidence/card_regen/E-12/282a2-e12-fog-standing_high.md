---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/fog.c implements S-091 card 2 of 2 (om_set_era_name, om_unit_get_hp, om_unit_attack)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E12_S091_standing_high.py::test_R_091_03_it_affects_sensors_only_never"
allowed_files: "csrc/fog.c"
snippet_file: csrc/fog.c
snippet_symbol: "om_set_era_name,om_unit_get_hp,om_unit_attack"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-12.md
test_file: tests/csim/test_E12_S091_standing_high.py
expected_lines: 36
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-12-fog-and-sensors.md (### S-091 — Standing high):

- R-091-03  Given the Settled Reach, When elevation is read, Then it affects sensors only, never damage (E-11 R-084-06).

## Header slice

(run card_slice.py --write after the skeleton lands)

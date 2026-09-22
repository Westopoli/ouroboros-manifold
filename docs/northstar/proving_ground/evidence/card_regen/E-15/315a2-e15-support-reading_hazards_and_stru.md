---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_support.c implements S-131 card 2 of 2 (om_hazard_get_launch_types, om_hazard_is_enabled_at_launch)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E15_S131_reading_hazards_and_structures.py::test_R_131_02_it_exactly_one_type_sensor"
allowed_files: "csrc/tactical_support.c"
snippet_file: csrc/tactical_support.c
snippet_symbol: "om_hazard_get_launch_types,om_hazard_is_enabled_at_launch"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-15.md
test_file: tests/csim/test_E15_S131_reading_hazards_and_structures.py
expected_lines: 24
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-15-reinforcement-supply-and-hazards.md (### S-131 — Reading hazards and structures):

- R-131-02  Given the launch hazard list, When read, Then it is exactly one type, sensor interference; drag, damage, boost, and disruption zones are future gradient tags with no engine change.

## Header slice

(run card_slice.py --write after the skeleton lands)

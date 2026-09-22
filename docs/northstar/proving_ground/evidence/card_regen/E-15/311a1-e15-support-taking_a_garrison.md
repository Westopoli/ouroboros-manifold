---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_support.c implements S-127 card 1 of 3 (om_structure_set_owner, om_structure_set_capturing_faction, om_structure_tick_capture, om_structure_get_capture_progress, om_structure_get_owner)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E15_S127_taking_a_garrison.py::test_R_127_01_capture_progress_rises_by_dt"
allowed_files: "csrc/tactical_support.c"
snippet_file: csrc/tactical_support.c
snippet_symbol: "om_structure_set_owner,om_structure_set_capturing_faction,om_structure_tick_capture,om_structure_get_capture_progress,om_structure_get_owner"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-15.md
test_file: tests/csim/test_E15_S127_taking_a_garrison.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-15-reinforcement-supply-and-hazards.md (### S-127 — Taking a garrison):

- R-127-01  Given units of exactly one non-owner faction inside a structure's 300 wu radius and no owner units, When ticks pass, Then capture progress rises by dt / 10 s; at 1.0 the owner flips and progress resets.

## Header slice

(run card_slice.py --write after the skeleton lands)

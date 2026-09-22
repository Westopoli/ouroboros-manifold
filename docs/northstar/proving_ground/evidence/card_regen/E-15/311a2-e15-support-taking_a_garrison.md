---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_support.c implements S-127 card 2 of 3 (om_structure_set_capture_progress, om_structure_set_contested, om_structure_get_hp, om_structure_apply_damage, om_structure_is_destroyed)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E15_S127_taking_a_garrison.py::test_R_127_02_progress_resets_to_0"
allowed_files: "csrc/tactical_support.c"
snippet_file: csrc/tactical_support.c
snippet_symbol: "om_structure_set_capture_progress,om_structure_set_contested,om_structure_get_hp,om_structure_apply_damage,om_structure_is_destroyed"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-15.md
test_file: tests/csim/test_E15_S127_taking_a_garrison.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-15-reinforcement-supply-and-hazards.md (### S-127 — Taking a garrison):

- R-127-02  Given units of two or more non-owner factions inside, or the owner also present, When ticks pass, Then progress resets to 0.

## Header slice

(run card_slice.py --write after the skeleton lands)

---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/unit.c implements S-084 card 3 of 3 (om_unit_profile_dps)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S084_flat_damage.py::test_R_084_07_it_base_damage_interval"
allowed_files: "csrc/unit.c"
snippet_file: csrc/unit.c
snippet_symbol: "om_unit_profile_dps"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-11.md
test_file: tests/csim/test_E11_S084_flat_damage.py
expected_lines: 12
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-11-units-and-combat.md (### S-084 — Flat damage):

- R-084-07  Given DPS, When read for the HUD or tuning, Then it is base damage / interval.

## Header slice

(run card_slice.py --write after the skeleton lands)

---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/generational.c implements S-062 card 2 of 2 (om_chronicle_has_faction_fall_entry)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S062_when_my_civilization_falls.py::test_R_062_04_chronicle_carries_major_entry_framing"
allowed_files: "csrc/generational.c"
snippet_file: csrc/generational.c
snippet_symbol: "om_chronicle_has_faction_fall_entry"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-08.md
test_file: tests/csim/test_E08_S062_when_my_civilization_falls.py
expected_lines: 12
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-08-generational-structure.md (### S-062 — When my civilization falls):

- R-062-04  Given reassignment, When recorded, Then the chronicle carries a major entry framing the fall.

## Header slice

(run card_slice.py --write after the skeleton lands)

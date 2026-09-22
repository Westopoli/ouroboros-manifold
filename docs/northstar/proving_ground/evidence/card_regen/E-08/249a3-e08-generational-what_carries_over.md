---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/generational.c implements S-064 card 3 of 3 (om_load_state_read)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S064_what_carries_over.py::test_R_064_04_next_time_jump_produces_same"
allowed_files: "csrc/generational.c"
snippet_file: csrc/generational.c
snippet_symbol: "om_load_state_read"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-08.md
test_file: tests/csim/test_E08_S064_what_carries_over.py
expected_lines: 12
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-08-generational-structure.md (### S-064 — What carries over):

- R-064-04  Given a save and load between chapters, When loaded, Then the next time jump produces the same trace as if never saved (determinism includes the RNG state and the chain tag counter).

## Header slice

(run card_slice.py --write after the skeleton lands)

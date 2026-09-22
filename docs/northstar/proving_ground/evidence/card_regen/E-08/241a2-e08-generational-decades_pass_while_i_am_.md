---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/generational.c implements S-056 card 2 of 2 (om_character_create, om_time_jump_lineage_generation_tick, om_time_jump_death_processing_tick)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S056_decades_pass_while_i_am_gone.py::test_R_056_05_lineage_members_generated_s_059"
allowed_files: "csrc/generational.c"
snippet_file: csrc/generational.c
snippet_symbol: "om_character_create,om_time_jump_lineage_generation_tick,om_time_jump_death_processing_tick"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-08.md
test_file: tests/csim/test_E08_S056_decades_pass_while_i_am_gone.py
expected_lines: 36
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-08-generational-structure.md (### S-056 — Decades pass while I am gone):

- R-056-05  Given the jump, When it ends, Then lineage members are generated (S-059) and natural deaths processed (S-060) once, at the end tick.

## Header slice

(run card_slice.py --write after the skeleton lands)

---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/generational.c implements S-064 card 1 of 3 (om_chapter_transition_start, om_chapter_transition_complete, om_force_allocator_run, om_force_set_surviving_units, om_force_allocated_unit_count)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S064_what_carries_over.py::test_R_064_01_every_region_field_ownership_faction"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S064_what_carries_over.py::test_R_064_02_they_come_only_from_mission"
allowed_files: "csrc/generational.c"
snippet_file: csrc/generational.c
snippet_symbol: "om_chapter_transition_start,om_chapter_transition_complete,om_force_allocator_run,om_force_set_surviving_units,om_force_allocated_unit_count"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-08.md
test_file: tests/csim/test_E08_S064_what_carries_over.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-08-generational-structure.md (### S-064 — What carries over):

- R-064-01  Given any chapter transition, When the next chapter starts, Then every region field, ownership, faction, tech level, edge type, event queue, and ledger record persists unchanged except by the sim itself.
- R-064-02  Given a new chapter, When forces are assigned, Then they come only from the mission generator's allocation (E-10); nothing carries from the previous mission's surviving units.

## Header slice

(run card_slice.py --write after the skeleton lands)

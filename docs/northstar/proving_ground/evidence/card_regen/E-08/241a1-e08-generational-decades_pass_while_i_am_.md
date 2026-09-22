---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/generational.c implements S-056 card 1 of 2 (om_time_jump_choose_length, om_time_jump_interrupt, om_time_jump_report_faction_field_deltas_count, om_time_jump_choose_opening_length, om_lineage_create)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S056_decades_pass_while_i_am_gone.py::test_R_056_01_it_integer_number_ticks_in"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S056_decades_pass_while_i_am_gone.py::test_R_056_02_exactly_that_many_strategic_ticks"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S056_decades_pass_while_i_am_gone.py::test_R_056_03_report_lists_territory_changes_faction"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S056_decades_pass_while_i_am_gone.py::test_R_056_04_it_in_20_50"
allowed_files: "csrc/generational.c"
snippet_file: csrc/generational.c
snippet_symbol: "om_time_jump_choose_length,om_time_jump_interrupt,om_time_jump_report_faction_field_deltas_count,om_time_jump_choose_opening_length,om_lineage_create"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-08.md
test_file: tests/csim/test_E08_S056_decades_pass_while_i_am_gone.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-08-generational-structure.md (### S-056 — Decades pass while I am gone):

- R-056-01  Given a time jump, When its length is chosen, Then it is an integer number of ticks in [20, 100], one tick being one in-world year [Q-056-01: code uses a fixed 50].
- R-056-02  Given the jump length, When the jump runs, Then exactly that many strategic ticks run with the full tick sequence (ALG tick sequence), and the player cannot shorten, lengthen, or interrupt it.
- R-056-03  Given the jump, When it ends, Then the report lists territory changes, faction births and deaths, conquests, colonizations, revolts, per-faction average field deltas, the chronicle entries, and an ownership snapshot every 2 ticks for the map animation.
- R-056-04  Given the opening jump, When its length is chosen, Then it is in [20, 50].

## Header slice

(run card_slice.py --write after the skeleton lands)

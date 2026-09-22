---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/chronicle.c implements S-069 card 2 of 4 (om_chronicle_map_is_master_clock, om_chronicle_presentation_entry_hold_sec, om_chronicle_set_entry_state, om_chronicle_handle_click, om_chronicle_is_paused)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S069_watching_history_happen.py::test_R_069_03_that_entry_begins_printing_map"
allowed_files: "csrc/chronicle.c"
snippet_file: csrc/chronicle.c
snippet_symbol: "om_chronicle_map_is_master_clock,om_chronicle_presentation_entry_hold_sec,om_chronicle_set_entry_state,om_chronicle_handle_click,om_chronicle_is_paused"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-09.md
test_file: tests/csim/test_E09_S069_watching_history_happen.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-09-chronicle.md (### S-069 — Watching history happen):

- R-069-03  Given the map animation is the master clock, When an entry's tick range is reached, Then that entry begins printing; the map never waits for the scroll; a printed entry holds for at least 3.0 s.

## Header slice

(run card_slice.py --write after the skeleton lands)

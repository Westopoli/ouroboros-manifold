---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/chronicle.c implements S-069 card 3 of 4 (om_chronicle_dismiss_expanded, om_chronicle_add_mock_entry, om_chronicle_add_ownership_change_event, om_chronicle_generate_map_keyframes, om_chronicle_has_keyframe_in_range)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S069_watching_history_happen.py::test_R_069_04_nothing_happens_it_printed_blinking"
allowed_files: "csrc/chronicle.c"
snippet_file: csrc/chronicle.c
snippet_symbol: "om_chronicle_dismiss_expanded,om_chronicle_add_mock_entry,om_chronicle_add_ownership_change_event,om_chronicle_generate_map_keyframes,om_chronicle_has_keyframe_in_range"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-09.md
test_file: tests/csim/test_E09_S069_watching_history_happen.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-09-chronicle.md (### S-069 — Watching history happen):

- R-069-04  Given an entry is printing, When the player clicks it, Then nothing happens; Given it is printed (blinking cursor shown), When clicked, Then the expanded form overlays the scroll and the map, clock, and any printing entry pause; dismissing resumes from the exact word and frame.

## Header slice

(run card_slice.py --write after the skeleton lands)

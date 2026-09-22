---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/chronicle.c implements S-069 card 4 of 4 (om_chronicle_has_keyframe_at_tick, om_chronicle_rendered_entry_count)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S069_watching_history_happen.py::test_R_069_05_map_has_keyframe_within_entry"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S069_watching_history_happen.py::test_R_069_06_number_entries_on_screen_equals"
allowed_files: "csrc/chronicle.c"
snippet_file: csrc/chronicle.c
snippet_symbol: "om_chronicle_has_keyframe_at_tick,om_chronicle_rendered_entry_count"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-09.md
test_file: tests/csim/test_E09_S069_watching_history_happen.py
expected_lines: 24
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-09-chronicle.md (### S-069 — Watching history happen):

- R-069-05  Given every chronicle entry, When keyframes are chosen, Then the map has a keyframe within the entry's tick range; and every ownership change has a keyframe whether or not it has an entry.
- R-069-06  Given a T2 screenshot at the end of the narration phase, When compared, Then the number of entries on screen equals the number the distiller produced.

## Header slice

(run card_slice.py --write after the skeleton lands)

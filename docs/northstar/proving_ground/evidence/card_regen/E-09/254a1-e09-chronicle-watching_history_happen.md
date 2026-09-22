---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/chronicle.c implements S-069 card 1 of 4 (om_chronicle_presentation_slide_in_sec, om_chronicle_presentation_slide_out_sec, om_chronicle_presentation_map_width_ratio, om_chronicle_presentation_word_cadence_sec, om_chronicle_presentation_word_fade_sec)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S069_watching_history_happen.py::test_R_069_01_it_slides_in_from_right"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S069_watching_history_happen.py::test_R_069_02_each_word_arrives_every_0"
allowed_files: "csrc/chronicle.c"
snippet_file: csrc/chronicle.c
snippet_symbol: "om_chronicle_presentation_slide_in_sec,om_chronicle_presentation_slide_out_sec,om_chronicle_presentation_map_width_ratio,om_chronicle_presentation_word_cadence_sec,om_chronicle_presentation_word_fade_sec"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-09.md
test_file: tests/csim/test_E09_S069_watching_history_happen.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-09-chronicle.md (### S-069 — Watching history happen):

- R-069-01  Given the narration phase begins, When the panel appears, Then it slides in from the right over 0.40 s and the map view resizes to 62 percent of the width; at the end it slides out over 0.40 s and the map returns to full width.
- R-069-02  Given an entry prints, When words appear, Then each word arrives every 0.08 s and fades from 0 to full opacity over 0.20 s.

## Header slice

(run card_slice.py --write after the skeleton lands)

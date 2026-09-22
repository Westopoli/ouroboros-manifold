---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/generational.c implements S-058 card 2 of 4 (om_character_create_child, om_selector_gather_nemesis_candidates, om_selector_get_nemesis_candidate, om_selector_draw_unrelated, om_character_faction)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S058_who_i_come_back_as.py::test_R_058_03_they_living_descendants_within_2"
allowed_files: "csrc/generational.c"
snippet_file: csrc/generational.c
snippet_symbol: "om_character_create_child,om_selector_gather_nemesis_candidates,om_selector_get_nemesis_candidate,om_selector_draw_unrelated,om_character_faction"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-08.md
test_file: tests/csim/test_E08_S058_who_i_come_back_as.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-08-generational-structure.md (### S-058 — Who I come back as):

- R-058-03  Given the nemesis pool, When candidates are gathered, Then they are living descendants, within 2 hops, of characters tagged as rivals of any previous commander, excluding the rivals themselves; one is drawn uniformly.

## Header slice

(run card_slice.py --write after the skeleton lands)

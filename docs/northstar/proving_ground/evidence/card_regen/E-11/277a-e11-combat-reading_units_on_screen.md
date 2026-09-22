---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/unit.c implements S-088 card 1 of 1 (om_unit_position_y, om_unit_render_craft_count, om_cue_lookup, om_unit_render_silhouette_size)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S088_reading_units_on_screen.py::test_R_088_01_it_appears_as_3_to"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S088_reading_units_on_screen.py::test_R_088_02_cue_plays_at_that_tick"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S088_reading_units_on_screen.py::test_R_088_03_category_distinguishable_by_silhouette_size"
allowed_files: "csrc/unit.c"
snippet_file: csrc/unit.c
snippet_symbol: "om_unit_position_y,om_unit_render_craft_count,om_cue_lookup,om_unit_render_silhouette_size"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-11.md
test_file: tests/csim/test_E11_S088_reading_units_on_screen.py
expected_lines: 48
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-11-units-and-combat.md (### S-088 — Reading units on screen):

- R-088-01  Given a Raider or Interceptor, When drawn, Then it appears as 3 to 5 small craft in formation sharing one HP bar and one position; the sim tracks one entity.
- R-088-02  Given an ability event, When received by the renderer, Then a cue plays at that tick for the event's duration (Barrage shows its telegraph ring at the target for 1.5 s before impact; Fortify shows its zone; Brace shows a planted state).
- R-088-03  Given a T2 screenshot of a mixed force, When inspected, Then category is distinguishable by silhouette size: Strike smallest, Siege largest.

## Header slice

(run card_slice.py --write after the skeleton lands)

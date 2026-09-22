---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/lifecycle.c implements S-052 card 1 of 1 (om_player_faction_collapsed)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E07_S052_no_plot_armor.py::test_R_052_01_it_has_zero_regions_its"
allowed_files: "csrc/lifecycle.c"
snippet_file: csrc/lifecycle.c
snippet_symbol: "om_player_faction_collapsed"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-07.md
test_file: tests/csim/test_E07_S052_no_plot_armor.py
expected_lines: 12
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-07-civilizational-lifecycle.md (### S-052 — No plot armor):

- R-052-01  Given the player civilization loses its last region, When the tick ends, Then it has zero regions, its budget still accumulates as 0, and the generational structure (E-08) handles the player's next chapter.

## Header slice

(run card_slice.py --write after the skeleton lands)

---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/generational.c implements S-058 card 1 of 4 (om_selector_roll_pool, om_selector_clear_pools, om_selector_resolve_fallback_pool, om_selector_score_previous_lineage, om_character_tag_rival)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S058_who_i_come_back_as.py::test_R_058_01_one_draw_picks_previous_descendant"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S058_who_i_come_back_as.py::test_R_058_02_each_previously_played_lineage_with"
allowed_files: "csrc/generational.c"
snippet_file: csrc/generational.c
snippet_symbol: "om_selector_roll_pool,om_selector_clear_pools,om_selector_resolve_fallback_pool,om_selector_score_previous_lineage,om_character_tag_rival"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-08.md
test_file: tests/csim/test_E08_S058_who_i_come_back_as.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-08-generational-structure.md (### S-058 — Who I come back as):

- R-058-01  Given a rotation, When the pool is rolled, Then one draw picks previous-descendant with probability 0.70, nemesis-descendant 0.20, unrelated 0.10; if the rolled pool is empty the search falls through in the order previous, nemesis, unrelated.
- R-058-02  Given the previous-descendant pool, When candidates are scored, Then each previously played lineage with a living member within 2 hops of the mission region, last played at least 1 chapter ago, scores gap · 0.6 + density · 0.4 with gap = min(chapters ago, 4)/4 and density = min(living nearby, 5)/5; a member is drawn with probability proportional to its lineage's score.

## Header slice

(run card_slice.py --write after the skeleton lands)

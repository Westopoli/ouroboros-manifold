---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/mission.c implements S-080 card 1 of 1 (om_unit_get_profile, om_mission_compute_parity, om_mission_get_archetype_preference_weight, om_mission_set_candidate_viable, om_mission_select_candidate)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S080_difficulty_is_scarcity_not_stronger_enemies.py::test_R_080_01_both_sides_draw_from_same"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S080_difficulty_is_scarcity_not_stronger_enemies.py::test_R_080_02_r_074_03_applies_nothing"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S080_difficulty_is_scarcity_not_stronger_enemies.py::test_R_080_03_rare_archetype_can_still_be"
allowed_files: "csrc/mission.c"
snippet_file: csrc/mission.c
snippet_symbol: "om_unit_get_profile,om_mission_compute_parity,om_mission_get_archetype_preference_weight,om_mission_set_candidate_viable,om_mission_select_candidate"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-10.md
test_file: tests/csim/test_E10_S080_difficulty_is_scarcity_not_stronger_enemies.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-10-missions.md (### S-080 — Difficulty is scarcity, not stronger enemies):

- R-080-01  Given any difficulty, When forces are generated, Then both sides draw from the same unit profiles; no stat differs by difficulty.
- R-080-02  Given easy, medium, hard, When parity is computed, Then R-074-03 applies and nothing else changes at launch [Q-080-01].
- R-080-03  Given a mission preference marked rare, When the world has no other viable candidate, Then the rare archetype can still be chosen (preference 0.1, never 0).

## Header slice

(run card_slice.py --write after the skeleton lands)

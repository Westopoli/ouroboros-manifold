---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/generational.c implements S-057 card 1 of 2 (om_lineage_set_chapter_count, om_character_kill, om_character_selector_run_for_lineage, om_selector_base_rotation_prob, om_selector_decayed_rotation_prob)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S057_stay_with_the_family_or_move_on.py::test_R_057_01_rotation_forced_with_reason_forced"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S057_stay_with_the_family_or_move_on.py::test_R_057_02_player_stays"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S057_stay_with_the_family_or_move_on.py::test_R_057_03_p_0_8_min_1"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S057_stay_with_the_family_or_move_on.py::test_R_057_04_it_decays_with_c_never"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S057_stay_with_the_family_or_move_on.py::test_R_057_06_it_first_living_lineage_member"
allowed_files: "csrc/generational.c"
snippet_file: csrc/generational.c
snippet_symbol: "om_lineage_set_chapter_count,om_character_kill,om_character_selector_run_for_lineage,om_selector_base_rotation_prob,om_selector_decayed_rotation_prob"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-08.md
test_file: tests/csim/test_E08_S057_stay_with_the_family_or_move_on.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-08-generational-structure.md (### S-057 — Stay with the family or move on):

- R-057-01  Given a lineage with no living members, or a dead commander with no living lineage member within 2 hops of the mission region, When selection runs, Then rotation is forced with reason `forced`.
- R-057-02  Given the lineage has fewer than 2 chapters played, When selection runs, Then the player stays.
- R-057-03  Given the home region's total field delta over the jump is D, When the base rotation probability is computed, Then p = 0.8 + min(1, D/200) · (0.1 − 0.8), so a quiet jump (D = 0) rotates at 0.8 and an active one (D ≥ 200) at 0.1.
- R-057-04  Given chapters played in the lineage is c ≥ 2, When the stay probability is computed, Then it decays with c and never reaches 0 or a hard cap [Q-057-01: proposed p_rotate = base p + (1 − base p) · (1 − 0.75^(c − 2))].
- R-057-06  Given the player stays, When the commander is chosen, Then it is the first living lineage member within 2 hops of the mission region, else the current commander if alive.

## Header slice

(run card_slice.py --write after the skeleton lands)

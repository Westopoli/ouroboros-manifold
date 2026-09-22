---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/generational.c implements S-058 card 3 of 4 (om_character_lineage_id, om_character_set_faction, om_mission_tag_rivals, om_character_has_rival_tag, om_character_selector_confirm_commander)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S058_who_i_come_back_as.py::test_R_058_04_new_character_created_in_mission"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S058_who_i_come_back_as.py::test_R_058_05_every_named_enemy_faction_character"
allowed_files: "csrc/generational.c"
snippet_file: csrc/generational.c
snippet_symbol: "om_character_lineage_id,om_character_set_faction,om_mission_tag_rivals,om_character_has_rival_tag,om_character_selector_confirm_commander"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-08.md
test_file: tests/csim/test_E08_S058_who_i_come_back_as.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-08-generational-structure.md (### S-058 — Who I come back as):

- R-058-04  Given the unrelated pool, When used, Then a new character is created in the mission region's owning faction with a new lineage id.
- R-058-05  Given a mission ends, When rivals are tagged, Then every named enemy-faction character in the mission region gains a rival tag pointing at the player's commander.

## Header slice

(run card_slice.py --write after the skeleton lands)

---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/generational.c implements S-062 card 1 of 2 (om_player_faction_check_collapse, om_chapter_end_reason_for_collapse, om_player_faction_reassign_on_collapse, om_campaign_check_surviving_factions, om_player_faction_record_reassignment)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S062_when_my_civilization_falls.py::test_R_062_01_chapter_ends_with_reason_faction"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S062_when_my_civilization_falls.py::test_R_062_02_q_062_01_code_picks"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S062_when_my_civilization_falls.py::test_R_062_03_campaign_ends_with_reason_no"
allowed_files: "csrc/generational.c"
snippet_file: csrc/generational.c
snippet_symbol: "om_player_faction_check_collapse,om_chapter_end_reason_for_collapse,om_player_faction_reassign_on_collapse,om_campaign_check_surviving_factions,om_player_faction_record_reassignment"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-08.md
test_file: tests/csim/test_E08_S062_when_my_civilization_falls.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-08-generational-structure.md (### S-062 — When my civilization falls):

- R-062-01  Given the player's faction has zero regions or no longer exists at the end of a time jump, When collapse is checked, Then the chapter ends with reason `faction_collapsed`.
- R-062-02  Given collapse, When the new faction is chosen, Then [Q-062-01: code picks the surviving faction with the most regions, uniform among ties; the bible says prefer narrative connections, else geographic overlap].
- R-062-03  Given no faction with any region survives, When collapse is checked, Then the campaign ends with reason `no_surviving_factions` (interim until S-054 is designed).

## Header slice

(run card_slice.py --write after the skeleton lands)

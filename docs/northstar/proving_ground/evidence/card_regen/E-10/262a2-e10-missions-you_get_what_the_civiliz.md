---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/mission.c implements S-074 card 2 of 2 (om_mission_apply_capacity_shortfall, om_mission_get_player_units, om_mission_get_shortfall_text, om_unit_power)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S074_you_get_what_the_civilization_can_spare.py::test_R_074_05_20_percent_player_s_units"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S074_you_get_what_the_civilization_can_spare.py::test_R_074_06_it_comes_from_interim_total"
allowed_files: "csrc/mission.c"
snippet_file: csrc/mission.c
snippet_symbol: "om_mission_apply_capacity_shortfall,om_mission_get_player_units,om_mission_get_shortfall_text,om_unit_power"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-10.md
test_file: tests/csim/test_E10_S074_you_get_what_the_civilization_can_spare.py
expected_lines: 48
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-10-missions.md (### S-074 — You get what the civilization can spare):

- R-074-05  Given capacity below 0.4, When shortfall applies, Then 20 percent of the player's units are removed, spread across types from the most numerous, never below 1 unit, and the briefing names what could not be spared.
- R-074-06  Given a unit's power, When read, Then it comes from the interim total-strength measure [Q-074-01].

## Header slice

(run card_slice.py --write after the skeleton lands)

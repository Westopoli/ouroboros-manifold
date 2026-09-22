---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/fog.c implements S-089 card 2 of 2 (om_player_can_see, om_client_snapshot_read, om_tactical_step, om_unit_teleport, om_player_can_see_friendly)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E12_S089_i_see_what_my_units_see.py::test_R_089_02_player_visible_enemy_list_their"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E12_S089_i_see_what_my_units_see.py::test_R_089_03_it_not_drawn_its_hp"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E12_S089_i_see_what_my_units_see.py::test_R_089_04_it_recomputed_every_tick_from"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E12_S089_i_see_what_my_units_see.py::test_R_089_05_friendly_units_always_visible_to"
allowed_files: "csrc/fog.c"
snippet_file: csrc/fog.c
snippet_symbol: "om_player_can_see,om_client_snapshot_read,om_tactical_step,om_unit_teleport,om_player_can_see_friendly"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-12.md
test_file: tests/csim/test_E12_S089_i_see_what_my_units_see.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-12-fog-and-sensors.md (### S-089 — I see what my units see):

- R-089-02  Given every friendly unit's visible set, When the player's view is built, Then the player-visible enemy list is their union.
- R-089-03  Given an enemy not in the union, When drawn, Then it is not drawn, its HP bar is not drawn, and its position is not in the client's data.
- R-089-04  Given visibility, When computed, Then it is recomputed every tick from current positions; there is no memory of last-seen positions [Q-089-01].
- R-089-05  Given a friendly unit, When visibility is computed, Then friendly units are always visible to the player regardless of distance.

## Header slice

(run card_slice.py --write after the skeleton lands)

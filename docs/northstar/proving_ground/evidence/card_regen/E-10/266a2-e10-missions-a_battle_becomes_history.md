---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/mission.c implements S-078 card 2 of 3 (om_region_get_owner, om_region_get_held_since, om_mission_resolve_refusal, om_mission_get_deployed_force_count, om_time_jump_run)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S078_a_battle_becomes_history.py::test_R_078_04_region_s_owner_becomes_player"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S078_a_battle_becomes_history.py::test_R_078_05_band_refusal_no_force_deployed"
allowed_files: "csrc/mission.c"
snippet_file: csrc/mission.c
snippet_symbol: "om_region_get_owner,om_region_get_held_since,om_mission_resolve_refusal,om_mission_get_deployed_force_count,om_time_jump_run"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-10.md
test_file: tests/csim/test_E10_S078_a_battle_becomes_history.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-10-missions.md (### S-078 — A battle becomes history):

- R-078-04  Given a transfer band for the archetype (S-073 table), When applied, Then the region's owner becomes the player's faction with held-since reset and edges updated (E-03 R-024-03).
- R-078-05  Given the player refuses the mission, When resolved, Then the band is refusal, no force is deployed, and the region's tension rises by 8 percent of its deficit.

## Header slice

(run card_slice.py --write after the skeleton lands)

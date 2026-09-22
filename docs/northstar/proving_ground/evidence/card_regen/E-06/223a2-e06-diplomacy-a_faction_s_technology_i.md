---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/diplomacy.c implements S-045 card 2 of 2 (om_world_set_tick, om_faction_last_knowledge_lost, om_tick_events)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S045_a_faction_s_technology_is_one_number.py::test_R_045_07_one_uniform_draw_made_if"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S045_a_faction_s_technology_is_one_number.py::test_R_045_09_mean_over_all_windows_between"
allowed_files: "csrc/diplomacy.c"
snippet_file: csrc/diplomacy.c
snippet_symbol: "om_world_set_tick,om_faction_last_knowledge_lost,om_tick_events"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-06.md
test_file: tests/csim/test_E06_S045_a_faction_s_technology_is_one_number.py
expected_lines: 36
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-06-diplomacy-and-technology.md (### S-045 — A faction's technology is one number):

- R-045-07  Given a faction whose average economy over its inhabited regions is below 20.0, or whose average population has fallen by 10.0 or more over the last 50 ticks, When the technology step runs on a tick at least 100 ticks after its last Knowledge Lost, Then one uniform draw is made and if it is below 0.03 a Knowledge Lost event fires: tech −5.0 (floored at 0), a fired-event record with template Knowledge Lost, the faction's highest-population region, and the next chain tag, and the faction's last-Knowledge-Lost tick set to now.
- R-045-09  Given a 5,000-tick run with 50 factions and the launch config, When Knowledge Lost events are counted per 50-tick window, Then the mean over all windows is between 1.0 and 2.0; individual windows may be far outside that (the rate is stochastic and only the mean is asserted).

## Header slice

(run card_slice.py --write after the skeleton lands)

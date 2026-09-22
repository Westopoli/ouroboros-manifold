---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_mapgen.c implements S-117 card 1 of 2 (om_fairness_evaluate, om_fairness_is_score_logged, om_fairness_force_score, om_map_get_active_seed, om_fairness_run_post_generation_check)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E17_S117_fair_enough.py::test_R_117_01_it_scores_route_count_staging"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E17_S117_fair_enough.py::test_R_117_02_q_113_01_map_regenerated"
allowed_files: "csrc/tactical_mapgen.c"
snippet_file: csrc/tactical_mapgen.c
snippet_symbol: "om_fairness_evaluate,om_fairness_is_score_logged,om_fairness_force_score,om_map_get_active_seed,om_fairness_run_post_generation_check"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-17.md
test_file: tests/csim/test_E17_S117_fair_enough.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-17-map-generation.md (### S-117 — Fair enough):

- R-117-01  Given a generated map, When the fairness evaluator runs, Then it scores route count staging-to-objective versus spawn-to-objective, mean travel time balance, vantage accessibility balance, and hazard distribution symmetry, and logs the score.
- R-117-02  Given the launch build, When the score is outside the acceptable range, Then [Q-113-01: the map is regenerated with a new seed up to 5 times (bible), or accepted and logged (code, A-393)].

## Header slice

(run card_slice.py --write after the skeleton lands)

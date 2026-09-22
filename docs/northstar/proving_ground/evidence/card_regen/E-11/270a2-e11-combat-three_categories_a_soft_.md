---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/unit.c implements S-081 card 2 of 2 (om_tactical_run_until_eliminated, om_unit_alive, om_tactical_reset, om_command_attack_target, om_tactical_run)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S081_three_categories_a_soft_triangle.py::test_R_081_02_line_wins_with_at_least"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S081_three_categories_a_soft_triangle.py::test_R_081_03_bastion_survives_at_least_20"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S081_three_categories_a_soft_triangle.py::test_R_081_04_time_to_kill_at_1"
allowed_files: "csrc/unit.c"
snippet_file: csrc/unit.c
snippet_symbol: "om_tactical_run_until_eliminated,om_unit_alive,om_tactical_reset,om_command_attack_target,om_tactical_run"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-11.md
test_file: tests/csim/test_E11_S081_three_categories_a_soft_triangle.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-11-units-and-combat.md (### S-081 — Three categories, a soft triangle):

- R-081-02  Given equal power of Line versus Strike in a straight fight, When resolved, Then Line wins with at least 30 percent of its HP remaining; the same for Siege versus Line and Strike versus Siege from the flank.
- R-081-03  Given a Bastion attacked by 4 Raiders from the flank, When resolved, Then the Bastion survives at least 20 s (the Siege exception to Strike-beats-Siege).
- R-081-04  Given any matchup, When resolved, Then time to kill at a 1.5× advantage is 30 to 40 percent shorter than at 1.0×.

## Header slice

(run card_slice.py --write after the skeleton lands)

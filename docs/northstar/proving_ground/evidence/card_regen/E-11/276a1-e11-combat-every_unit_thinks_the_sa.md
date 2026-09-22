---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/unit.c implements S-087 card 1 of 2 (om_unit_set_stealth, om_unit_position_x, om_unit_teleport, om_unit_target, om_command_attack_move)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S087_every_unit_thinks_the_same_way.py::test_R_087_01_it_moves_200_wu_directly"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S087_every_unit_thinks_the_same_way.py::test_R_087_02_order_wins_over_auto_engagement"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S087_every_unit_thinks_the_same_way.py::test_R_087_03_it_attacks_nearest_such_enemy"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S087_every_unit_thinks_the_same_way.py::test_R_087_04_it_moves_toward_nearest_visible"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S087_every_unit_thinks_the_same_way.py::test_R_087_05_it_anchors_at_its_position"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S087_every_unit_thinks_the_same_way.py::test_R_087_06_it_targets_attacker_return_fire"
allowed_files: "csrc/unit.c"
snippet_file: csrc/unit.c
snippet_symbol: "om_unit_set_stealth,om_unit_position_x,om_unit_teleport,om_unit_target,om_command_attack_move"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-11.md
test_file: tests/csim/test_E11_S087_every_unit_thinks_the_same_way.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-11-units-and-combat.md (### S-087 — Every unit thinks the same way):

- R-087-01  Given a unit taking damage from an attacker it cannot see or cannot reach, When the loop runs, Then it moves 200 wu directly away from the damage direction and stops; once the attacker is visible and in range it stands and fights.
- R-087-02  Given a unit with an active player order, When the loop runs, Then the order wins over auto-engagement; a plain move never acquires or returns fire.
- R-087-03  Given an idle or attack-moving unit with an enemy within attack range on its layer, When targets are evaluated, Then it attacks the nearest such enemy; an engaged target still alive and in range is kept.
- R-087-04  Given an attack-moving unit with no enemy in attack range but a visible one within sensor range, When evaluated, Then it moves toward the nearest visible enemy.
- R-087-05  Given an attack-moving unit that acquires a target, When it does, Then it anchors at its position, and if the target moves more than 200 wu from the anchor it drops the target and resumes its path.
- R-087-06  Given an idle unit with no target and no order taking damage, When hit, Then it targets the attacker (return fire); an already-engaged unit ignores incoming damage for targeting.

## Header slice

(run card_slice.py --write after the skeleton lands)

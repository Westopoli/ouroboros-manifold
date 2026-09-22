---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/unit.c implements S-081 card 1 of 2 (om_tactical_category_multiplier, om_unit_spawn_for_category, om_unit_hp, om_unit_deal_damage, om_unit_spawn)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S081_three_categories_a_soft_triangle.py::test_R_081_01_damage_base_damage_m_b"
allowed_files: "csrc/unit.c"
snippet_file: csrc/unit.c
snippet_symbol: "om_tactical_category_multiplier,om_unit_spawn_for_category,om_unit_hp,om_unit_deal_damage,om_unit_spawn"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-11.md
test_file: tests/csim/test_E11_S081_three_categories_a_soft_triangle.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-11-units-and-combat.md (### S-081 — Three categories, a soft triangle):

- R-081-01  Given an attacker of category A and a target of category B, When damage is dealt, Then damage = base damage × M[A][B] with M: Strike→Strike 1.0, Strike→Line 0.75, Strike→Siege 1.5; Line→Strike 1.5, Line→Line 1.0, Line→Siege 0.75; Siege→Strike [Q-081-01: 0.20 in code, 0.75 in the bible], Siege→Line 1.5, Siege→Siege 1.0.

## Header slice

(run card_slice.py --write after the skeleton lands)

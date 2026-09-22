---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/unit.c implements S-082 card 1 of 2 (om_unit_profile_category, om_unit_profile_max_hp, om_unit_profile_base_damage, om_unit_profile_attack_interval, om_unit_profile_attack_range)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S082_the_six.py::test_R_082_03_bastion_has_most_by_at"
allowed_files: "csrc/unit.c"
snippet_file: csrc/unit.c
snippet_symbol: "om_unit_profile_category,om_unit_profile_max_hp,om_unit_profile_base_damage,om_unit_profile_attack_interval,om_unit_profile_attack_range"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-11.md
test_file: tests/csim/test_E11_S082_the_six.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-11-units-and-combat.md (### S-082 — The six):

- R-082-03  Given the roster, When ordered by HP, Then the Bastion has the most by at least 2× the next, and the Raider the least.

## Header slice

(run card_slice.py --write after the skeleton lands)

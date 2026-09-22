---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/generational.c implements S-059 card 1 of 2 (om_lineage_generate_descendants, om_rng_force_descendant_spread, om_lineage_spawn_single_descendant, om_character_get_record, om_character_set_generation)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S059_the_family_grows_while_i_am_away.py::test_R_059_01_max_1_floor_n_0"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S059_the_family_grows_while_i_am_away.py::test_R_059_02_its_parent_uniform_draw_among"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S059_the_family_grows_while_i_am_away.py::test_R_059_04_nothing_created"
allowed_files: "csrc/generational.c"
snippet_file: csrc/generational.c
snippet_symbol: "om_lineage_generate_descendants,om_rng_force_descendant_spread,om_lineage_spawn_single_descendant,om_character_get_record,om_character_set_generation"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-08.md
test_file: tests/csim/test_E08_S059_the_family_grows_while_i_am_away.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-08-generational-structure.md (### S-059 — The family grows while I am away):

- R-059-01  Given a lineage with n living members and a jump of T ticks, When members are generated at the jump's end, Then max(1, floor(n · 0.03 · T)) descendants are created.
- R-059-02  Given each descendant, When placed, Then its parent is a uniform draw among living members, its faction is the parent's, and with probability 0.1 it is placed in a uniform-random inhabited neighbor of the parent's region, else the parent's region.
- R-059-04  Given a lineage with no living members, When generation runs, Then nothing is created.

## Header slice

(run card_slice.py --write after the skeleton lands)

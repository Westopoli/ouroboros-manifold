---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/generational.c implements S-059 card 2 of 2 (om_lineage_spawn_descendant_at_tick)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S059_the_family_grows_while_i_am_away.py::test_R_059_03_it_has_name_region_faction"
allowed_files: "csrc/generational.c"
snippet_file: csrc/generational.c
snippet_symbol: "om_lineage_spawn_descendant_at_tick"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-08.md
test_file: tests/csim/test_E08_S059_the_family_grows_while_i_am_away.py
expected_lines: 12
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-08-generational-structure.md (### S-059 — The family grows while I am away):

- R-059-03  Given a descendant, When recorded, Then it has a name, region, faction, birth tick equal to the jump's end tick, lifespan, lineage id, parent id, and generation = parent's + 1; nothing else.

## Header slice

(run card_slice.py --write after the skeleton lands)

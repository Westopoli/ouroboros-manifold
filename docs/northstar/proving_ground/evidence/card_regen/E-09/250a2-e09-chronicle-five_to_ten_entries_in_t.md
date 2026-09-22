---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/chronicle.c implements S-065 card 2 of 3 (om_lineage_create, om_chronicle_add_lineage_event, om_chronicle_add_event, om_lineage_record_history_region, om_chronicle_category_name)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S065_five_to_ten_entries_in_the_right_order.py::test_R_065_03_every_lineage_cluster_included_regardless"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S065_five_to_ten_entries_in_the_right_order.py::test_R_065_04_one_lineage_quiet_cluster_included"
allowed_files: "csrc/chronicle.c"
snippet_file: csrc/chronicle.c
snippet_symbol: "om_lineage_create,om_chronicle_add_lineage_event,om_chronicle_add_event,om_lineage_record_history_region,om_chronicle_category_name"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-09.md
test_file: tests/csim/test_E09_S065_five_to_ten_entries_in_the_right_order.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-09-chronicle.md (### S-065 — Five to ten entries, in the right order):

- R-065-03  Given the player's lineage, When clusters are ranked, Then every lineage cluster is included regardless of score, one per region the lineage touched.
- R-065-04  Given no event touched the lineage, When clusters are ranked, Then one `lineage_quiet` cluster is included, placed in the lineage's most recent region.

## Header slice

(run card_slice.py --write after the skeleton lands)

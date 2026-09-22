---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/chronicle.c implements S-067 card 2 of 2 (om_chronicle_categorize_chain_cluster, om_chronicle_categorize_regional_cluster, om_chronicle_lineage_category_count, om_chronicle_chain_category_count, om_chronicle_regional_category_count)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S067_stories_not_events.py::test_R_067_04_any_revolt_template_gives_chain"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S067_stories_not_events.py::test_R_067_05_they_group_by_region_into"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S067_stories_not_events.py::test_R_067_06_it_exactly_5_lineage_8"
allowed_files: "csrc/chronicle.c"
snippet_file: csrc/chronicle.c
snippet_symbol: "om_chronicle_categorize_chain_cluster,om_chronicle_categorize_regional_cluster,om_chronicle_lineage_category_count,om_chronicle_chain_category_count,om_chronicle_regional_category_count"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-09.md
test_file: tests/csim/test_E09_S067_stories_not_events.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-09-chronicle.md (### S-067 — Stories, not events):

- R-067-04  Given a chain cluster, When categorized, Then: any "revolt" template gives `chain_revolt_spawned`; else any "expansion" or "coloniz" gives `chain_expansion`; else 4 or more events gives `chain_cascade`; else net military > 2 and net tension < 3 gives `chain_conflict_victory`; else net military < −2 and net tension > 3 gives `chain_conflict_defeat`; else |net military| ≤ 2 and net tension > 2 gives `chain_conflict_stalemate`; else net economy > 0 and net tension ≤ 0 gives `chain_crisis_resolved_well`; else `chain_crisis_resolved_badly`.
- R-067-05  Given events with no chain tag and no lineage link, When clustered, Then they group by region into a regional cluster categorized `regional_faction_shift` if any conquest, revolt, or faction-creating event is present, else `regional_growth` if net economy + population > 3, else `regional_decline` if < −3, else `regional_stable`.
- R-067-06  Given the category list, When read, Then it is exactly: 5 lineage, 8 chain, 4 regional, and the consequence categories [Q-067-01: 3 in code, 4 in the bible].

## Header slice

(run card_slice.py --write after the skeleton lands)

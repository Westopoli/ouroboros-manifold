---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/chronicle.c implements S-067 card 1 of 2 (om_character_create, om_chronicle_is_lineage_event, om_chronicle_categorize_lineage_cluster, om_chronicle_add_chain_event, om_chronicle_build_chain_clusters)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S067_stories_not_events.py::test_R_067_01_event_lineage_event_if_lineage"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S067_stories_not_events.py::test_R_067_02_any_template_with_succession_or"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S067_stories_not_events.py::test_R_067_03_events_sharing_chain_tag_form"
allowed_files: "csrc/chronicle.c"
snippet_file: csrc/chronicle.c
snippet_symbol: "om_character_create,om_chronicle_is_lineage_event,om_chronicle_categorize_lineage_cluster,om_chronicle_add_chain_event,om_chronicle_build_chain_clusters"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-09.md
test_file: tests/csim/test_E09_S067_stories_not_events.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-09-chronicle.md (### S-067 — Stories, not events):

- R-067-01  Given scored events not in the consequence cluster, When clustered, Then an event is a lineage event if a lineage member lives in its region, or its attached character is a lineage member, or it is in the last mission's region; lineage events cluster by region.
- R-067-02  Given a lineage cluster, When categorized, Then: any template with "succession" or "death" gives `lineage_succession`; else any "military" or "revolt" gives `lineage_military_action`; else net economy > 2 or net military > 2 gives `lineage_thrived`; else net economy < −3 or net tension > 5 gives `lineage_suffered`; else `lineage_quiet`.
- R-067-03  Given the remaining events, When clustered, Then events sharing a chain tag form one chain cluster spanning every region the chain touched, and chain clusters with the same primary region and category merge into one.

## Header slice

(run card_slice.py --write after the skeleton lands)

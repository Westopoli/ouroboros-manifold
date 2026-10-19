# Chronicle twin summary

Seeds: 1-20, chapters per seed: 5

## Counts

| item | count |
|---|---|
| attacks | 48807 |
| blank_entries | 204 |
| chapters | 100 |
| collisions | 24060 |
| conquest_net_reverted | 4137 |
| conquest_owner_change_no_entry | 6917 |
| conquests | 11600 |
| creates_faction_events | 2952 |
| creates_faction_no_entry | 2500 |
| ct0 | 302 |
| ct1 | 5 |
| ct2 | 3 |
| ct3 | 659 |
| entries | 969 |
| events | 88875 |
| fragment_ids_reused_in_campaign | 517 |
| fragment_ids_used | 1304 |
| own_change_no_entry_budget_full | 5846 |
| own_change_no_entry_category_capped | 918 |
| ownership_change_no_entry | 6764 |
| ownership_changes | 7027 |
| revolt_region_no_entry | 309358 |
| revolt_rolls | 316383 |
| revolts | 316383 |
| ripple_entries | 218 |
| sentence_repeat_instances | 589 |
| sentence_repeat_same_scroll | 12 |
| tier5plus_events | 2952 |
| tier5plus_events_total_uncovered | 2500 |
| uncovered_above_cutoff_budget_full | 5560 |
| uncovered_above_cutoff_category_capped | 2321 |

## Mismatch classes

| class | count | first example |
|---|---|---|
| R065-05_ripple_exceeds_cap2 | 42 | seed1 ch1 : 4 ripple entries |
| R071_sentence_repeat | 589 | seed1 ch2 : 'Word of what was done at the Rasmar reached the Salt Hollow, held by t' first at (1, 1) |
| blank_text | 91 | seed1 ch1 : 4 blank of 10 (ids [2, 3, 4, 7]) |
| family_entry_missing | 97 | seed1 ch2 :  |
| lineage_gt2 | 1 | seed6 ch5 : 3 |
| owner_change_not_faction_shift | 3 | seed2 ch1 : id5 region 271 cat23 |
| significance_below_recomputed_lowerbound | 438 | seed1 ch1 : id6 sig 5.20 vs 7.28 |
| under5_readable | 1 | seed14 ch2 : 4 readable, 10 total |

## Groups

| group | item | count |
|---|---|---|
| family_entries | entries_cluster_lineage | 5 |
| family_entries | missing | 97 |
| family_entries | blank | 0 |
| chain_entries | entries_cluster_chain | 3 |
| chain_entries | no_chain_event | 0 |
| blank_shells | blank_entries | 204 |
| blank_shells | scrolls_with_blank | 91 |
| ripple_over_cap | ripple_entries | 218 |
| ripple_over_cap | scrolls_over_cap | 42 |
| repeats | sentence_repeat_instances | 589 |
| repeats | same_scroll | 12 |
| repeats | fragment_ids_reused | 517 |
| repeats | fragment_ids_used | 1304 |
| significance_threshold_explanations | uncovered_budget_full | 5560 |
| significance_threshold_explanations | uncovered_category_capped | 2321 |
| significance_threshold_explanations | uncovered_UNEXPLAINED | 0 |
| significance_threshold_explanations | owner_change_no_entry_budget_full | 5846 |
| significance_threshold_explanations | owner_change_no_entry_category_capped | 918 |
| significance_threshold_explanations | owner_change_no_entry_UNEXPLAINED | 0 |
| significance_threshold_explanations | significance_below_recomputed_lowerbound | 438 |

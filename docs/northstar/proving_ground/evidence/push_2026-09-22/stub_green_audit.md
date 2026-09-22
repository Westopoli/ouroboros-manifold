## Audit result — E-06..E-17 vacuous-pass classification

Reran `red_check.py --forbid TypeError,ArgumentError,AttributeError` over `tests/csim/test_E0[6-9]*.py tests/csim/test_E1*.py`: `passed=69` (was 66 at freeze, +3 from post-freeze corrections), `forbidden=4` (all test-arg bugs, not stub coincidences, out of scope). Of the 69 passing, 9 are `test_E06_wiring.py`/`test_E07_wiring.py`/`test_E11_wiring.py` — expected, excluded. Classified the remaining 60.

Checked each against C source (`csrc/*.c`) — confirmed which functions are real (`/* STUB */` absent) vs hard stubs returning `0`/`0.0`/`NULL`/empty before judging.

| Test id | Class | Rule | One-line fix (class a only) |
|---|---|---|---|
| test_E06_S042...::test_R_042_01_it_exactly_one_hostile_neutral | a | R-042-01 | Assert exact `OMStance.NEUTRAL` for a DEFAULT/DEFAULT pair (not in R-042-05's hostile-override table) instead of just domain+symmetry+self-coop membership. |
| test_E06_S042...::test_R_042_03_neither_attacks_other_no_friction | c | R-042-03 | — real E-05 candidate-gen + E-02 drift/friction code reacting to a directly-set NEUTRAL stance. |
| test_E06_S042...::test_R_042_06_it_hostile_toward_every_existing | a | R-042-06 | Before `om_faction_create_breakaway`, set stance(0,2)/(2,0) to COOPERATIVE first, so post-call HOSTILE actually proves the function acted (currently coincides with zero-init default). |
| test_E06_S043...::test_R_043_02_counter_does_not_move | b | R-043-02 | — genuine null branch; sibling `R-043-01` (increments with a border) is the contrast, same functions. |
| test_E06_S043...::test_R_043_06_pair_stays_neutral_counter_resets | a | R-043-06 | `om_faction_set_stance_counter`/`om_faction_stance_counter` are both no-op stubs (setter never stores, getter always 0). Add a round-trip check (`set 80` then `get==80`) before relying on the post-failure `==0`. |
| test_E06_S045...::test_R_045_04_nothing_changes | b | R-045-04 | — genuine null branch; sibling `R-045-01` (real growth) contrasts, same `om_tech_step`. |
| test_E06_S045...::test_R_045_06_it_equals_parent_s_tech | a | R-045-06 | `om_breakaway_create` stub always returns `0` = the parent's own id. Assert `breakaway_fid != 0` (or `!= parent`) before reading its "tech". |
| test_E06_S045...::test_R_045_08_no_draw_made_tech_never | b | R-045-08 | — genuine null branch; sibling `R-045-07` (Knowledge Lost fires) contrasts, same `om_tech_step`. |
| test_E06_S047...::test_R_047_02_bonus_0 | b | R-047-02 | — genuine null branch; sibling `R-047-01`/`R-047-04` (nonzero bonus) contrast, same `om_tech_step`. |
| test_E06_S047...::test_R_047_03_bonus_0 | b | R-047-03 | — same as above. |
| test_E07_S050...::test_R_050_02_it_never_reverts | b | R-050-02 | — genuine null branch; sibling `R-050-01`/`R-050-04` (reversion happens) contrast, same lifecycle path; draws are chosen so a real-but-window-blind impl would be caught. |
| test_E07_S050...::test_R_050_03_it_never_reverts | b | R-050-03 | — same. |
| test_E07_S053...::test_R_053_01_its_phase_fragmentation | a | R-053-01 | `om_faction_phase` stub always returns `0` = FRAGMENTATION's value. Add a companion check in the same test (revolts=0) requiring `phase != FRAGMENTATION`, catching an "always 0" impl. |
| test_E07_S054...::test_R_054_01_deferred_with_feature_no_rule | a | R-054-01 | Advance the world many ticks (or past a claimed "final era") via `om_world_step` before asserting `is_terminal==0` — currently only checks tick 0. |
| test_E08_S055...::test_R_055_02_no_strategic_tick_runs_strategic | a | R-055-02 | Test never attempts a strategic tick during MISSION phase (only calls `om_tactical_step`, which never touches the strategic counter). Call `om_world_step` while still in MISSION and assert the counter still doesn't move. |
| test_E08_S055...::test_R_055_04_character_selector_runs_after_it | a | R-055-04 | `om_mission_generator_chosen_region`/`om_character_selector_input_region` both hard-stub `0`. Force/verify a nonzero chosen region and assert `chosen_region != 0` before comparing. |
| test_E08_S056...::test_R_056_05_lineage_members_generated_s_059 | a | R-056-05 | `om_time_jump_run` never fills `report` (stays ctypes-zeroed) and the tick getters hard-stub `0`. Capture `start_tick` first and assert `report.end_tick == start_tick+30` before comparing to it. |
| test_E08_S057...::test_R_057_02_player_stays | b | R-057-02 | — genuine null branch; sibling `R-057-01` (forced rotation) contrasts, same `om_character_selector_run_for_lineage`. |
| test_E08_S057...::test_R_057_05_rotation_vetoed_player_stays | b | R-057-05 | — same sibling. |
| test_E08_S059...::test_R_059_04_nothing_created | b | R-059-04 | — genuine null branch; sibling `R-059-01` (nonzero descendants) contrasts, same `om_lineage_generate_descendants`. |
| test_E08_S060...::test_R_060_06_it_holds_exactly_id_name | a | R-060-06 | Assertion compares the test's own ctypes mirror's field names to itself — tautological, can never fail. Replace with value checks on the populated record (`rec.rank==LINEAGE_MEMBER`, `rec.birth_tick==10`, `rec.lifespan==200`, `rec.faction==0`). |
| test_E08_S064...::test_R_064_01_every_region_field... | a | R-064-01 | Both transition functions are complete no-ops. Add an assertion of something chapter-transition IS responsible for (e.g. `om_chapter_current_phase(w)==BRIEFING` post-transition). |
| test_E08_S064...::test_R_064_02_they_come_only_from_mission | a | R-064-02 | Both calls return the constant `0` regardless of args. Add `assert units_m2 > 0` (real, budget-derived) alongside the equality. |
| test_E08_S064...::test_R_064_04_next_time_jump_produces_same | a | R-064-04 | Both worlds are blank (never populated, never ticked — every relevant call is a stub), so checksums match by construction. Populate w2 differently before load and assert load overwrites it; also assert `save_size>0`. |
| test_E09_S065...::test_R_065_02_they_form_one_consequence_cluster | a | R-065-02 | Zeroed struct default (`CONSEQUENCE=0`,`SUCCESS=0`) matches. Add `assert first_cluster.region == 1` (the region actually passed in). |
| test_E09_S065...::test_R_065_05_they_taken_in_descending_peak | a | R-065-05 | `0 <= 2` and `0 <= 10` pass with zero selected. Assert `om_chronicle_entry_count(w) == 4` (5+3 clusters, capped 2/category). |
| test_E09_S068...::test_R_068_02_openings_at_most_30_words | a | R-068-02 | Empty text has 0 words. Assert `len(base_words) > 0` before the upper bounds. |
| test_E09_S068...::test_R_068_03_it_comes_only_from_vocabulary | a | R-068-03 | Empty text has no digits. Assert `len(base_str) > 0` / `len(exp_str) > 0` first. |
| test_E09_S068...::test_R_068_08_text_identical | a | R-068-08 | Two empty scrolls are trivially equal. Assert `len(ctypes.string_at(text1)) > 0` before comparing. |
| test_E09_S069...::test_R_069_06_number_entries_on_screen_equals | a | R-069-06 | No events injected, so `0==0`. Call `om_chronicle_mock_populate_events` first and assert `distilled_count > 0` before the equality. |
| test_E10_S079...::test_R_079_03_it_shows_band_objectives_with | a | R-079-03 | Debrief struct stays zeroed; every range check includes 0. Force a specific outcome and assert an exact nonzero `objective_score`/`commander_fate`. |
| test_E10_S079...::test_R_079_04_it_contains_no_raw_field | b | R-079-04 | — genuine negation; sibling `R-079-01` (text must be non-empty) is the required companion; once text exists, this test would catch a number-leak. |
| test_E10_S080...::test_R_080_01_both_sides_draw_from_same | a | R-080-01 | `om_unit_get_profile` leaves `out` zeroed for every difficulty. Assert `prof_easy.hp > 0` (known nonzero baseline) alongside the cross-difficulty equality. |
| test_E11_S081...::test_R_081_02_line_wins_with_at_least | a | R-081-02 | `om_unit_hp`/`om_unit_alive` are hard stubs (`0.0`/`0`), so `initial_line_hp` is also 0 and `0>=0.3*0` trivially holds. Assert `initial_line_hp > 0` first. |
| test_E11_S082...::test_R_082_03_bastion_has_most_by_at | a | R-082-03 | All profile getters hard-stub `0.0`, so `0>=2*0`. Assert `bastion_hp == 1050.0` (roster table) before the ratio/min checks. |
| test_E11_S084...::test_R_084_02_damage_identical_no_falloff | b | R-084-02 | — genuine negation ("no falloff"); sibling `R-084-01`/`R-084-06` (exact nonzero damage) contrast, same `om_unit_deal_damage`/`om_unit_hp`; geometry is set up so a real falloff bug would be caught once damage is real. |
| test_E11_S084...::test_R_084_05_damage_unmodified_e_01_r | b | R-084-05 | — same sibling reasoning (cover shouldn't reduce damage). |
| test_E11_S087...::test_R_087_03_it_attacks_nearest_such_enemy | a | R-087-03 | `om_unit_spawn` always returns `0`, so every spawned unit aliases id 0; `om_unit_target` also hard-stubs `0` — `0==0` regardless of logic. Assert spawned ids are distinct first. |
| test_E11_S087...::test_R_087_06_it_targets_attacker_return_fire | a | R-087-06 | Same id-collision issue; assert `unit != attacker1 != attacker2` before the targeting checks. |
| test_E12_S089...::test_R_089_03_it_not_drawn_its_hp | a | R-089-03 | `om_client_snapshot_read` stub gives empty `.units`, so "not in []" is trivial for any id. Spawn a friendly and assert it IS present first, proving the snapshot isn't always empty. |
| test_E12_S093...::test_R_093_01_traces_identical | a | R-093-01 | No real combat occurs (`om_unit_spawn`/`om_command_attack_move` stubs); `om_unit_get_hp` hard-stubs `0.0`. Assert `om_unit_get_hp(w1,f1) > 0` (real combat happened) before comparing worlds. |
| test_E13_S098...::test_R_098_02_shot_blocked_exactly_as_vision | b | R-098-02 | — genuine negation; sibling `R-098-01` (real nonzero damage lands) contrasts, same `om_combat_can_shoot`/`om_unit_attack`/`om_unit_get_hp`. |
| test_E13_S100...::test_R_100_03_it_faces_pursuer | a | R-100-03 | `om_unit_get_facing` hard-stubs `0.0`, which coincidentally equals the expected pursuer angle. Set facing to a different value (e.g. `pi`) first, then confirm it moves toward 0.0. |
| test_E13_S101...::test_R_101_02_position_facing_linearly_interpolated_from | a | R-101-02 | `om_unit_get_pos` always `(0,0)`, so midpoint of two zeros is zero. Assert `p1_x != p0_x` (real movement) before the interpolation check. |
| test_E13_S102...::test_R_102_01_every_position_facing_target_identical | a | R-102-01 | Movement/facing/targeting are all hard stubs returning constants; nothing exercises real cross-machine divergence risk. Assert `pos1_w1 != (0.0,0.0)` (real movement occurred) at a checkpoint. |
| test_E14_S121...::test_R_121_01_condition_compared_against_its_noised | a | R-121-01 | `om_macro_get_threshold_noise`/`_timer_noise` hard-stub `0.0`, in-range and "held" trivially. Assert `t_noise != 0.0` or compare two different force ids for inequality. |
| test_E14_S121...::test_R_121_05_q_121_01_code_returns | a | R-121-05 | `om_macro_validate_condition_name` hard-stubs `0` for everything, so it "correctly" rejects these too, but would also wrongly reject valid names. Assert a known-valid name (e.g. `threshold_expired`) returns `1`. |
| test_E14_S122...::test_R_122_05_each_force_s_timer_noise | a | R-122-05 | Both noise getters hard-stub `0.0` — range check passes but "independent" is unproven (both identical). Assert `noise_a != noise_b`. |
| test_E14_S123...::test_R_123_01_every_enemy_command_identical_on | a | R-123-01 | `om_replay_command_count` hard-stubs `0`, so the per-command comparison loop runs 0 times. Assert `count1 > 0` first. |
| test_E14_S123...::test_R_123_03_it_never_reads_player_s | a | R-123-03 | No sibling in file proves these query functions can ever report `1` — permanent-`0` stub is indistinguishable from a verified "never". Add a debug-injected positive case proving the accessor can report `1`. |
| test_E14_S125...::test_R_125_02_their_decision_loop_stats_abilities | a | R-125-02 | Getters hard-stub `0`/`0.0` for both sides — "identical" trivially true. Assert `hp_p > 0` (a real roster value) before the cross-side equality. |
| test_E15_S126...::test_R_126_06_units_have_no_cost_player | a | R-126-06 | Both accessors are permanently-0 constants unconnected to any real production path. Tie the trickle check to the real `R-126-02` production flow (confirm a spawn counter moves while trickle stays 0). |
| test_E15_S127...::test_R_127_02_progress_resets_to_0 | b | R-127-02 | — genuine null branch; sibling `R-127-01` (progress rises to 0.5, flips owner) contrasts, same `om_structure_tick_capture`/`get_capture_progress`. |
| test_E16_S111...::test_R_111_02_second_write_is_byte_identical | a | R-111-02 | `om_save_state_size` hard-stubs `0`, so both buffers are empty — trivially byte-identical. Assert `size1 > 0` first (mirrors the already-red `test_R_111_02_size_query_then_write_round_trips`). |
| test_E16_S111...::test_R_111_02_save_load_save_gives_identical_bytes | a | R-111-02 | Same empty-buffer issue, plus `rc` reads an undefined register (the local binding casts a `void` C function to `c_int`). Assert `size1 > 0` before the byte comparison. |
| test_E17_S113...::test_R_113_03_at_least_one_flank_route | a | R-113-03 | `om_map_count_nodes_of_type` hard-stubs `0`, so the check loop runs 0 times. Assert `choke_count > 0` first. |
| test_E17_S113...::test_R_113_04_it_reachable_from_both_staging | a | R-113-04 | Same empty-loop issue; assert `vantage_count > 0` first. |
| test_E17_S114...::test_R_114_01_each_obstacle_density_cover_density | a | R-114-01 | `om_map_sample_gradients` leaves `props` zeroed — every field is in-range by coincidence. Assert at least one sampled property is nonzero across the 3 points. |
| test_E17_S117...::test_R_117_03_it_passes_hard_constraints_no | a | R-117-03 | `om_map_library_total_layouts` hard-stubs `0`, loop runs 0 times. Assert `total_layouts > 0` first. |
| test_E17_S119...::test_R_119_01_no_repeated_tile_boundary_visible | a | R-119-01 | Both discontinuity/repetition metrics hard-stub `0`. Assert the two boundary-adjacent sampled gradient values themselves differ from 0/each other before trusting the "smooth" verdict. |

### Counts
- (a) vacuous-on-stub: **44**
- (b) legitimately-trivial: **15**
- (c) real-pass: **1**
- Total classified: 60 (+ 9 expected wiring tests excluded, + 4 forbidden test-arg bugs out of scope)

### (a) ids — Python list literal

```python
[
    "tests/csim/test_E06_S042_three_ways_to_feel_about_a_neighbor.py::test_R_042_01_it_exactly_one_hostile_neutral",
    "tests/csim/test_E06_S042_three_ways_to_feel_about_a_neighbor.py::test_R_042_06_it_hostile_toward_every_existing",
    "tests/csim/test_E06_S043_peace_grows_out_of_quiet.py::test_R_043_06_pair_stays_neutral_counter_resets",
    "tests/csim/test_E06_S045_a_faction_s_technology_is_one_number.py::test_R_045_06_it_equals_parent_s_tech",
    "tests/csim/test_E07_S053_every_faction_has_an_age.py::test_R_053_01_its_phase_fragmentation",
    "tests/csim/test_E07_S054_where_a_civilization_ends_up.py::test_R_054_01_deferred_with_feature_no_rule",
    "tests/csim/test_E08_S055_one_commander_one_mission_then_the_world_moves.py::test_R_055_02_no_strategic_tick_runs_strategic",
    "tests/csim/test_E08_S055_one_commander_one_mission_then_the_world_moves.py::test_R_055_04_character_selector_runs_after_it",
    "tests/csim/test_E08_S056_decades_pass_while_i_am_gone.py::test_R_056_05_lineage_members_generated_s_059",
    "tests/csim/test_E08_S060_named_leaders_live_and_die.py::test_R_060_06_it_holds_exactly_id_name",
    "tests/csim/test_E08_S064_what_carries_over.py::test_R_064_01_every_region_field_ownership_faction",
    "tests/csim/test_E08_S064_what_carries_over.py::test_R_064_02_they_come_only_from_mission",
    "tests/csim/test_E08_S064_what_carries_over.py::test_R_064_04_next_time_jump_produces_same",
    "tests/csim/test_E09_S065_five_to_ten_entries_in_the_right_order.py::test_R_065_02_they_form_one_consequence_cluster",
    "tests/csim/test_E09_S065_five_to_ten_entries_in_the_right_order.py::test_R_065_05_they_taken_in_descending_peak",
    "tests/csim/test_E09_S068_written_from_fragments_never_the_same_twice.py::test_R_068_02_openings_at_most_30_words",
    "tests/csim/test_E09_S068_written_from_fragments_never_the_same_twice.py::test_R_068_03_it_comes_only_from_vocabulary",
    "tests/csim/test_E09_S068_written_from_fragments_never_the_same_twice.py::test_R_068_08_text_identical",
    "tests/csim/test_E09_S069_watching_history_happen.py::test_R_069_06_number_entries_on_screen_equals",
    "tests/csim/test_E10_S079_orders_not_menus.py::test_R_079_03_it_shows_band_objectives_with",
    "tests/csim/test_E10_S080_difficulty_is_scarcity_not_stronger_enemies.py::test_R_080_01_both_sides_draw_from_same",
    "tests/csim/test_E11_S081_three_categories_a_soft_triangle.py::test_R_081_02_line_wins_with_at_least",
    "tests/csim/test_E11_S082_the_six.py::test_R_082_03_bastion_has_most_by_at",
    "tests/csim/test_E11_S087_every_unit_thinks_the_same_way.py::test_R_087_03_it_attacks_nearest_such_enemy",
    "tests/csim/test_E11_S087_every_unit_thinks_the_same_way.py::test_R_087_06_it_targets_attacker_return_fire",
    "tests/csim/test_E12_S089_i_see_what_my_units_see.py::test_R_089_03_it_not_drawn_its_hp",
    "tests/csim/test_E12_S093_fog_is_for_the_player_not_the_engine.py::test_R_093_01_traces_identical",
    "tests/csim/test_E13_S100_facing.py::test_R_100_03_it_faces_pursuer",
    "tests/csim/test_E13_S101_movement_that_reads.py::test_R_101_02_position_facing_linearly_interpolated_from",
    "tests/csim/test_E13_S102_same_commands_same_battle.py::test_R_102_01_every_position_facing_target_identical",
    "tests/csim/test_E14_S121_timers_and_thresholds_with_noise.py::test_R_121_01_condition_compared_against_its_noised",
    "tests/csim/test_E14_S121_timers_and_thresholds_with_noise.py::test_R_121_05_q_121_01_code_returns",
    "tests/csim/test_E14_S122_forces_that_notice_each_other.py::test_R_122_05_each_force_s_timer_noise",
    "tests/csim/test_E14_S123_the_enemy_replays_like_i_do.py::test_R_123_01_every_enemy_command_identical_on",
    "tests/csim/test_E14_S123_the_enemy_replays_like_i_do.py::test_R_123_03_it_never_reads_player_s",
    "tests/csim/test_E14_S125_how_hard_the_enemy_tries.py::test_R_125_02_their_decision_loop_stats_abilities",
    "tests/csim/test_E15_S126_most_of_my_force_is_out_there.py::test_R_126_06_units_have_no_cost_player",
    "tests/csim/test_E16_S111_saving.py::test_R_111_02_second_write_is_byte_identical",
    "tests/csim/test_E16_S111_saving.py::test_R_111_02_save_load_save_gives_identical_bytes",
    "tests/csim/test_E17_S113_nine_kinds_of_place.py::test_R_113_03_at_least_one_flank_route",
    "tests/csim/test_E17_S113_nine_kinds_of_place.py::test_R_113_04_it_reachable_from_both_staging",
    "tests/csim/test_E17_S114_texture_from_gradients.py::test_R_114_01_each_obstacle_density_cover_density",
    "tests/csim/test_E17_S117_fair_enough.py::test_R_117_03_it_passes_hard_constraints_no",
    "tests/csim/test_E17_S119_terrain_that_reads_like_a_place.py::test_R_119_01_no_repeated_tile_boundary_visible",
]
```

Note on method: (b) required both — rule text itself a genuine negation/no-op ("does not move", "never reverts", "player stays", "no falloff") AND a same-file sibling test targeting the same underlying function with a contrasting real/nonzero expectation (sibling need not currently pass — several are still red, since the epic is unbuilt — it just has to be capable of catching a real-but-wrong implementation once one lands). Everything else that passes only by numeric coincidence with a stub's constant zero/empty/NULL, with no such sibling, got (a). Biggest recurring root causes behind the 44: `om_unit_spawn` returns `0` for every call (id collisions), `om_unit_hp`/`om_unit_get_hp`/`om_unit_alive`/`om_unit_get_pos`/`om_unit_get_facing`/`om_unit_target` are hard `0`-return stubs, several `_count`/`_total` accessors hard-stub `0` making loops vacuously empty, and one test (`R-060-06`) is tautological regardless of any implementation (compares the test's own ctypes mirror to itself).

No repo files touched; no git actions run.
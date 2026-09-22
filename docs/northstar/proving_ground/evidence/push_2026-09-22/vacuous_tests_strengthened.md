## Vacuous-pass strengthening — 44 class (a) rows from stub_green_audit.md

Source: `docs/northstar/proving_ground/evidence/push_2026-09-22/stub_green_audit.md`. Rule: fix ADDS an
assertion/precondition that makes the test fail on the current STUB build for its own rule's reason;
never removes/weakens an existing assertion; rule id and test name kept; numbers taken from
`csrc/ouroboros_sim.h` / `docs/bible/epics/E-*.md` / `docs/bible/algorithms.md`, never invented.

Per row: file, edit, assert-count before -> after, new failure line. Rows skipped listed at the end.

### E-06

| Test | Edit | asserts before -> after | New failure |
|---|---|---|---|
| `test_E06_S042_three_ways_to_feel_about_a_neighbor.py::test_R_042_01_it_exactly_one_hostile_neutral` | added `assert s01 == OMStance.NEUTRAL` (DEFAULT/DEFAULT not in R-042-05 override table) | 32 -> 33 | `AssertionError: DEFAULT/DEFAULT pair not in the hostile-override table must be neutral` / `assert 0 == 1` |
| `test_E06_S042_three_ways_to_feel_about_a_neighbor.py::test_R_042_06_it_hostile_toward_every_existing` | pre-set stance(0,2) and (1,2) to COOPERATIVE before `om_faction_create_breakaway` | 32 -> 33 (net; no new assert line, added 2 preconditions) | `assert 2 == 0` (stance stays COOPERATIVE, stub never flips to HOSTILE=0) |
| `test_E06_S043_peace_grows_out_of_quiet.py::test_R_043_06_pair_stays_neutral_counter_resets` | added round-trip `assert lib.om_faction_stance_counter(w,0,1) == 80` right after the setter call | 16 -> 17 | `assert 0 == 80` |
| `test_E06_S045_a_faction_s_technology_is_one_number.py::test_R_045_06_it_equals_parent_s_tech` | added `assert breakaway_fid != 0` before reading its tech | 14 -> 15 | `AssertionError: breakaway id must differ from parent id 0` / `assert 0 != 0` |

### E-07

| Test | Edit | asserts before -> after | New failure |
|---|---|---|---|
| `test_E07_S053_every_faction_has_an_age.py::test_R_053_01_its_phase_fragmentation` | companion check: reset window to revolts=0 and assert `phase != FRAGMENTATION` | 10 -> 11 | `AssertionError: assert 0 != 0` (phase stub always returns FRAGMENTATION's value 0) |

Row skipped: `test_E07_S054_where_a_civilization_ends_up.py::test_R_054_01_deferred_with_feature_no_rule` -- see skip list at end.

### E-08

| Test | Edit | asserts before -> after | New failure |
|---|---|---|---|
| `test_E08_S055...::test_R_055_02_no_strategic_tick_runs_strategic` | added phase check + a second `om_world_step` call while still in MISSION, re-asserting the strategic tick didn't move | 19 -> 22 (shared with R_055_04 below) | `assert 0 == 2` (`om_chapter_current_phase` stub never reflects `om_chapter_set_phase(MISSION)`) |
| `test_E08_S055...::test_R_055_04_character_selector_runs_after_it` | added `assert chosen_region != 0` before the read-back comparison | 19 -> 22 (shared) | `AssertionError: chosen region must be a real (nonzero) mission target` / `assert 0 != 0` |
| `test_E08_S056_decades_pass_while_i_am_gone.py::test_R_056_05_lineage_members_generated_s_059` | captured `start_tick` and added `assert report.end_tick == start_tick+30` before trusting the report | 16 -> 17 | `assert 0 == (0 + 30)` |
| `test_E08_S060_named_leaders_live_and_die.py::test_R_060_06_it_holds_exactly_id_name` | added real value checks (`rank`, `birth_tick`, `lifespan`, `faction`) alongside the existing tautological field-name check (kept, not removed) | 24 -> 28 | `assert 0 == 3` (rank never populated) |
| `test_E08_S064_what_carries_over.py::test_R_064_02_they_come_only_from_mission` | added `assert units_m2 > 0` before the cross-world equality | 9 -> 11 (shared with R_064_04) | `assert 0 > 0` |
| `test_E08_S064_what_carries_over.py::test_R_064_04_next_time_jump_produces_same` | added `assert save_size > 0`; populated w2's region 0 with different values before the (stub) load, so a real load would have to overwrite it | 9 -> 11 (shared) | `assert 0 > 0` |

Row skipped: `test_E08_S064_what_carries_over.py::test_R_064_01_every_region_field_ownership_faction` -- see skip list at end.

### E-09

| Test | Edit | asserts before -> after | New failure |
|---|---|---|---|
| `test_E09_S065...::test_R_065_02_they_form_one_consequence_cluster` | added `assert first_cluster.region == 1` | 14 -> 16 (shared w/ R_065_05) | `assert 0 == 1` |
| `test_E09_S065...::test_R_065_05_they_taken_in_descending_peak` | added `assert om_chronicle_entry_count(w) == 4` | 14 -> 16 (shared) | `assert 0 == 4` |
| `test_E09_S068...::test_R_068_02_openings_at_most_30_words` | added `assert len(base_words) > 0` before upper bounds | 14 -> 18 (shared across 3 rows in file) | `assert 0 > 0` |
| `test_E09_S068...::test_R_068_03_it_comes_only_from_vocabulary` | added `assert len(base_str) > 0` and `assert len(exp_str) > 0` before digit checks | 14 -> 18 (shared) | `assert 0 > 0` |
| `test_E09_S068...::test_R_068_08_text_identical` | added `assert len(ctypes.string_at(text1)) > 0` before comparison | 14 -> 18 (shared) | `assert 0 > 0` |
| `test_E09_S069_watching_history_happen.py::test_R_069_06_number_entries_on_screen_equals` | added `om_chronicle_mock_populate_events(w, n_events=20)` call + `assert distilled_count > 0` | 14 -> 15 | `assert 0 > 0` |

### E-10

| Test | Edit | asserts before -> after | New failure |
|---|---|---|---|
| `test_E10_S079_orders_not_menus.py::test_R_079_03_it_shows_band_objectives_with` | forced outcome: `om_mission_build_objectives(w,0)`, set every objective's completion to 1.0, then `assert debrief.objective_score == pytest.approx(1.0)` (ALG-58: weights sum to 1.0 per R-075-01, none failed) | 21 -> 22 | `assert 0.0 == 1.0 ± 1.0e-05` |
| `test_E10_S080_difficulty_is_scarcity_not_stronger_enemies.py::test_R_080_01_both_sides_draw_from_same` | added `assert prof_easy.hp > 0` before the cross-difficulty equality | 12 -> 13 | `AssertionError: unit profile must be a real (nonzero) roster baseline` / `assert 0.0 > 0` |

### E-11

| Test | Edit | asserts before -> after | New failure |
|---|---|---|---|
| `test_E11_S081_three_categories_a_soft_triangle.py::test_R_081_02_line_wins_with_at_least` | added `assert initial_*_hp > 0` for all 3 sub-cases (line, siege, strike2) before their `>= 0.3 * initial` checks | 11 -> 14 | `assert 0.0 > 0` |
| `test_E11_S082_the_six.py::test_R_082_03_bastion_has_most_by_at` | added `assert bastion_hp == pytest.approx(1050.0)` (roster table, R-082-01) before the ratio/min checks | 20 -> 21 | `assert 0.0 == 1050.0 ± 1.0e-06` |
| `test_E11_S087_every_unit_thinks_the_same_way.py::test_R_087_03_it_attacks_nearest_such_enemy` | added `assert len({vanguard,e_near,e_far}) == 3` (distinct spawn ids) | 16 -> 18 (shared w/ R_087_06) | `assert 1 == 3` |
| `test_E11_S087_every_unit_thinks_the_same_way.py::test_R_087_06_it_targets_attacker_return_fire` | added `assert len({unit,attacker1,attacker2}) == 3` (distinct spawn ids) | 16 -> 18 (shared) | `assert 1 == 3` |

### E-12

| Test | Edit | asserts before -> after | New failure |
|---|---|---|---|
| `test_E12_S089_i_see_what_my_units_see.py::test_R_089_03_it_not_drawn_its_hp` | captured `friendly` id, added `assert friendly in all_ids_in_client` before the exclusion check | 19 -> 20 | `assert 0 in []` |
| `test_E12_S093_fog_is_for_the_player_not_the_engine.py::test_R_093_01_traces_identical` | added `assert om_unit_get_hp(w1,f1) > 0` before the cross-world checksum/hp comparisons | 9 -> 10 | `assert 0.0 > 0` |

### E-13

| Test | Edit | asserts before -> after | New failure |
|---|---|---|---|
| `test_E13_S100_facing.py::test_R_100_03_it_faces_pursuer` | set facing to `pi` first, assert readback `== pi` before issuing the kiting command (get_facing hard-stubs 0.0, coinciding with the expected pursuer angle) | 7 -> 8 | `assert 0.0 == pi ± 1e-06` (approx) |
| `test_E13_S101_movement_that_reads.py::test_R_101_02_position_facing_linearly_interpolated_from` | added `assert p1_x != p0_x` before the interpolation checks | 7 -> 8 | `assert 0.0 != 0.0` |
| `test_E13_S102_same_commands_same_battle.py::test_R_102_01_every_position_facing_target_identical` | added `assert pos1_w1 != (0.0, 0.0)` inside the checkpoint loop before the cross-machine equality | 10 -> 11 | `assert (0.0, 0.0) != (0.0, 0.0)` |

### E-14

| Test | Edit | asserts before -> after | New failure |
|---|---|---|---|
| `test_E14_S121...::test_R_121_01_condition_compared_against_its_noised` | added `assert t_noise != 0.0` and `assert timer_noise != 0.0` | 11 -> 14 (shared w/ R_121_05) | `assert 0.0 != 0.0` |
| `test_E14_S121...::test_R_121_05_q_121_01_code_returns` | added `assert om_macro_validate_condition_name(b"timer_expired") == 1` (R-121-01 keeps "timer expired" in vocabulary) | 11 -> 14 (shared) | `assert 0 == 1` |
| `test_E14_S122_forces_that_notice_each_other.py::test_R_122_05_each_force_s_timer_noise` | added `assert noise_a != noise_b` | 12 -> 13 | `assert 0.0 != 0.0` |
| `test_E14_S123_the_enemy_replays_like_i_do.py::test_R_123_01_every_enemy_command_identical_on` | added `assert count1 > 0` before the per-command comparison loop | 12 -> 13 | `assert 0 > 0` |
| `test_E14_S125_how_hard_the_enemy_tries.py::test_R_125_02_their_decision_loop_stats_abilities` | added `assert hp_p > 0` before the cross-side equality | 10 -> 11 | `assert 0.0 > 0` |

Row skipped: `test_E14_S123_the_enemy_replays_like_i_do.py::test_R_123_03_it_never_reads_player_s` -- see skip list at end.

### E-15

| Test | Edit | asserts before -> after | New failure |
|---|---|---|---|
| `test_E15_S126_most_of_my_force_is_out_there.py::test_R_126_06_units_have_no_cost_player` | tied the check to R-126-02's real production flow (init structure, tick production, pop spawn) and asserted `spawned == 1` before re-checking trickle stays 0 | 21 -> 23 | `assert 0 == 1` |

### E-16

Note: both rows' local `_bind_save` casts the C `void om_load_state_read(...)` to ctypes `restype=c_int` (T2's binding lane, not touched here per instruction).

| Test | Edit | asserts before -> after | New failure |
|---|---|---|---|
| `test_E16_S111_saving.py::test_R_111_02_second_write_is_byte_identical` | added `assert size1 > 0` right after the two `_save` calls | 36 -> 38 (shared) | `assert 0 > 0` |
| `test_E16_S111_saving.py::test_R_111_02_save_load_save_gives_identical_bytes` | added `assert size1 > 0` right after the first `_save` call | 36 -> 38 (shared) | `assert 0 > 0` |


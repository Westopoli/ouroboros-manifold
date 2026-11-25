# Movement-sidestep: tests written (LS1) and the existing tests the change touches

Story `movement-sidestep`, decision `DEC-movement-sidestep-2026-11-24`, spec `docs/northstar/plans/movement-sidestep-2026-11-24/spec.md`. Branch `s/movement-sidestep`.

## How the list was made

Two scratch trees (outside the repository, under `~/Projects/om-wt/engine-rules-baseline/ls1/`): `vA` is this worktree with `csrc/tactical_move.c` replaced by the reference experiment (`r6-advance/t-A`, variant A; the give-up pass is a `return`, the probe skip and the committed detour are in) and `vB` is `vA` with the `giveup_near` and `detour_remaining` words taken out of the movement hash, the save slot and the load (what the spec's save-format paragraph describes). The existing suites were run on both and compared with `base_csim_fail.txt` and `base_other_fail.txt` (the known reds of main): red on `vA` and not in the base list = the test pins behaviour A changes; red on `vB` and green on `vA` = the test pins the hash or the save layout. The search terms of the brief (`giveup`, `give_up`, `R-099-05`, `detour`, `STEERING_PROBE`, `om_move_steer`, `baseline hashes`, A99, F1, F2, F3, S101, movement save slot) were also read file by file for the ones that mention the rule and stay green.

Run: `tests/csim/test_*.py` (337 files, 6 chunks), `tests/csim/scale`, `tests/csim/parity`; `tests/skilllab` top-level `test_reengage*`, `test_sweep*`, `test_invariants*`, `ground/`, `integration/` (all 61 files, 7 chunks) and the 40 `arena/` files that run the engine (8 chunks of 5). Not run on `vA`: `tests/qa`, `tests/transport`, `tests/method`, `tests/specfactory` (the search found nothing in them that pins movement; the implementer's full run settles it).

Not pins, scratch artefacts to ignore if you repeat this: `test_VG_E_e1f`, `test_VG_E_e1g`, `test_E01_T3_mission_ground` source tests (the scratch tree lacked `assets/`).

## Classes

- **stays**: green on A, the rule it names is not touched (or only its quoting text is stale).
- **retire**: the rule is gone (R-099-05's give-up) or the test pins the old behaviour a decision replaces (60 wu hold, group mates and idle friends block); delete in a `Test-defect: DEC-movement-sidestep-2026-11-24` commit.
- **rewrite**: the test's rule stays but its scene or assertion assumed the old behaviour; change it in a `Test-defect:` commit, per-tick assertions stay per-tick.
- **re-pin**: a recorded hash, golden, trace or measured fight value moves; re-record in a `Test-defect:` commit after the new run passes the F0 checker.

## csim

| Test | Class | Reason |
|---|---|---|
| `test_E13_R099_05_giveup_counts_only_ticks_without_progress.py` (7 red on A: the two `control_..._ends_its_order_on_the_40th_tick`, `ticks_that_come_nearer_...`, the four new-order count tests) | retire those 7 | R-099-05 removed. The file also holds `ProgressCount` and `check_destination_by_count`, imported by `test_E13_R097_10_proof_idle_yield.py`, `test_E13_R097_10_idle_own_units_yield.py`, `test_PP_unit_giveup.py`, `test_E13_R099_05_lone_walker_arrives_and_gives_up.py`: delete the helpers only with the last importer |
| same file, the two `slow_unit ... keeps its destination while it comes nearer` / `slow member ... reaches its arrival radius` tests (green on A) | stays (rename to R-099-04) | they prove arrival, not the give-up |
| `test_E13_R099_05_lone_walker_arrives_and_gives_up.py` (12 red on A: every `ends_its_order_on_the_40th_tick`, `control_a_group_members_give_up_is_unchanged[...]`, `the_count_of_a_walker_alone_starts_again`, `the_pause_after_its_own_shot_is_not_counted`, `a_game_saved_and_loaded_in_the_middle_of_a_count`) | retire those 12 | give-up gone; the save-in-the-middle-of-a-count test goes with `giveup_near` |
| `test_PP_unit_giveup.py` | retire `test_R_099_05_blocked_slot_gives_up_at_exactly_40_ticks_within_75`; the S101 scene test (green on A) rewrite to R-099-04 (it now proves arrival) | give-up gone |
| `test_E13_R097_10_proof_idle_yield.py` (`[ENEMY]`, `[ENGAGED]` red on A), `test_E13_R097_10_idle_own_units_yield.py` (`an_idle_enemy_unit_takes_none_of_the_push...`) | rewrite | the scene is "a lone mover held inside the 75 wu disc, its order ends by R-099-05 on the 40th tick"; under the new rule the order stays, so the end assertion becomes "the order is still active". Per-tick form kept |
| `test_E13_R097_10_halted_pair_separates.py` | stays | green on A (the spec's list names it; it has no give-up assertion) |
| `test_E13_R096_02_order_kept_through_shot_pause.py`, `test_E11_S087_redirect_resumes_original_point.py` | stays | green on A; the quoted rule text and a docstring line about the give-up exception are stale (Documents list of the spec) |
| `test_E11_R087_09_blocked_line_gives_up.py`, `test_E11_R087_03_lock_ends_at_notice_distance.py`, `test_E11_R087_04_chase_resumes_after_the_pause.py` | stays | R-087-09's give-up of a target is a different rule |
| `test_PP_move_steer_face.py` (`group_mates_block`, `detour_held_for_60_wu_of_distance_moved[raider_7_5_per_tick]`, `[vanguard_4_per_tick]`) | retire | exactly the two behaviours A replaces: group mates block, the 60 wu hold. Replaced by `test_E13_DEC_sidestep_probe_skip.py` and `..._committed_detour.py` |
| `test_PP_move_parity_rules.py` (`a_new_move_order_does_not_clear_the_detour`, `control_detour_is_held_for_60_wu_of_movement`) | retire the second; rewrite the first | the hold is gone; whether a new order clears a stored detour is a question the spec does not answer (see gaps) |
| `test_E13_S097_around_not_through.py::test_R_097_04_it_keeps_that_heading_for` | rewrite | pins the 60 wu hold; becomes "keeps the side until the line is clear" |
| `test_PP_collision_radius_runtime.py` (`control_probe_deflects_a_unit_inside_two_radii`, `ruling_15_radius_30_unit_cannot_cross_between_blockers_80_apart`) | rewrite | the blockers in the scene are idle friends of the walker; they no longer block the probe. Use enemy or engaged blockers (a scene change, the radius rule is unchanged) |
| `test_PP_collision_radius_runtime.py::test_control_radius_15_trace_is_byte_identical_to_the_recorded_trace`, `test_collision_radius.py` (3 red: `control_never_calling...`, `every_value_15...`, `save_made_with_no_radius_set_is_byte_identical_to_todays_save_format`) | re-pin | recorded traces and a save blob with units that meet idle friends; the last one also pins the save layout |
| `test_F1_fog_per_faction_observers.py`, `test_F2_nearest_hostile_search.py`, `test_F3_macro_contact_skip.py` (`[clash]` and `[spread]` golden each) | re-pin | 400-tick goldens of fights with blocked units; F1's comment history already lists earlier give-up re-pins |
| `test_PP_C_g3_hash_invariant.py` (6 goldens F1/F2/F3 x clash/spread) | re-pin | the same goldens under `target_by_sight 0` |
| `test_E13_A99_tactical_equivalence.py` (6: `fight_502_gap100`, `fight_990_gap300/1500/3000`, `idle_502`, `idle_990`), `test_PP_target_policy_per_side.py` (`policy_0_explicit_equals_the_recorded_A99_hashes`, `guard_positive_control...`) | re-pin | A99 recorded hashes (data in `tests/csim/a99_tactical_runs.py`); they also move with the hash word |
| `test_E01_T2_walker_no_corner_cut.py`, `test_E01_T2_walker_waypoint_arrival.py`, `test_E01_T2_collision_mask.py` (`flyer_blob_trace_is_unchanged_by_...`) | re-pin | the flyer blob trace moves with the probe skip (the last one only turns red with the hash/save word removed) |
| `test_net_save_move.py`, `test_net_save_fog.py`, `test_net_save_macro.py`, `test_net_save_mapgen.py`, `test_net_section_hashes.py` | stays | round trips and equality of two worlds; green on vB (word removed). They do not pin the blob size |
| `tests/csim/parity/baseline/test_baseline_hashes.py` | stays | the two reds (`a99_fight_502_gap100`, `a99_fight_990_gap300`) are in `base_csim_fail.txt` already; the switches-at-0 path is untouched by A |
| `test_E13_S101_movement_that_reads.py`, `test_E13_R207_06_never_enter_blocked.py`, `test_PP_move_route.py`, `test_E01_T2_walker_*` others, `tests/csim/scale/*` | stays | green on A (mention `detour` or S101 only) |
| `test_PP_C_g3_rehash.py`, `test_B3_C2_friction_golden.py` | stays | green on A and on vB |

## Lab (`tests/skilllab`)

| Test | Class | Reason |
|---|---|---|
| `arena/test_closeup.py` (4: `cl1_frames_are_at_0_k_2k_and_the_last_tick[off-10]`, `control_..._byte_identical_to_the_pinned_files[open-off]`, `control_fight_called_the_old_way...[off]`, `control_the_normal_runs...have_the_dumped_premises`) | re-pin | the pinned `open`/`off` fight (stage 1) is now a different fight; the file hashes in the test (line 39) and the dumped premises move |
| `arena/test_run_apart_end.py` (`L5_the_stage_1_fight_ends_apart_with_...`, `L5_a_fight_that_ends_by_elimination_writes_the_same_bytes_as_before[open-off]`) | rewrite / re-pin | stage 1 (L-0054) no longer ends apart (A: wipe at tick 6408); the apart-end test needs another fight that still ends apart, or a planted one. The elimination bytes re-pin |
| `arena/test_regression_manifest.py` (`L2_command_a_fight_that_ends_by_elimination...`, `L2_command_a_checker_report...`) | re-pin | fixture fights and expected rows; `docs/northstar/research/layer_dynamics/arena/approved.toml` rows move too (the chat's job, decision id in each row) |
| `arena/test_stage4fix_groups.py::test_a_layout_without_group_keys_writes_no_groups_and_the_old_stage3_fight_reproduces_byte_for_byte` | re-pin | recorded stage 3 fight bytes |
| `arena/test_engine_rules_r3_move_away.py` (3: `control_L0080_runs_to_the_measured_end`, `control_L0080_the_move_away_is_made_by_idle_units...`, `R_087_01_no_unit_stands_still_...L0080`), `arena/test_engine_rules_r4_idle_yield.py` (`control_L0028_unit_18...`, `R_097_10_L0045_control_no_walker_stands_beside_an_idle_own_unit...`), `arena/test_engine_rules_r5_unseen_fire.py::...[L-0080]`, `arena/test_engine_rules_f9_unseen_fire.py::...60_ticks` | rewrite | dumped premises measured on today's L-0080, L-0028, L-0045 fights (unit ids, ticks, the end by the give-up at tick 311 in `r3_move_away`'s docstring and table); re-measure on the new fights, same per-tick invariants |
| `integration/test_cross_machine.py::test_control_hash_matches_golden[mirror|numbers|planted]` | re-pin | recorded fight hashes |
| `integration/test_trace_real.py::test_control_rows_equal_golden_with_trace_off_and_on[...]` (4) | re-pin | recorded rows |
| `arena/test_engine_rules_f5_giveup.py`, `test_invariants_give_up.py`, `test_invariants_giveup_count.py`, `test_invariants_nearest.py`, `giveup_count_frames.json` | stays | R-087-09, the target give-up |
| `test_reengage.py`, `integration/test_reengage_real.py`, `integration/test_contact_real.py` | stays | green on A; they cite R-099-05 as a number (40 ticks) or in a docstring; the text is stale |
| `arena/test_engine_rules_r5_unseen_fire.py` (counts "held ticks" with R-099-05's definition) | stays (comment stale) | its other parametrizations are green on A |
| everything else run (`ground/`, the other 33 `arena/` files, 54 other `integration/` files) | stays | green on A |

## Hash and save pins in one line

Removing `giveup_near` and `detour_remaining` from the movement hash, save slot and load turned only `test_E01_T2_collision_mask.py::..._flyer_blob_trace_is_unchanged_by_the_walker_fix` newly red beyond the behaviour changes (all goldens above re-pin once, for both reasons); no test pins the save blob length or the slot layout, the round-trip tests stay green.

## New tests (this commit series)

| File | Names | Red on main | Control green on main |
|---|---|---|---|
| `tests/csim/test_E13_DEC_sidestep_no_giveup.py` | (a) group attack-mover and (d) lone move/attack-move blocked by a guard on the point, 3000 ticks, flying and walking | 6 | 4: other group member arrives, lone unit on a free path arrives |
| `tests/csim/test_E13_DEC_sidestep_probe_skip.py` | (b) group mate and idle friend do not deflect; enemy, guard, engaged friend, moving friend, other-group mate do | 2 | 6 |
| `tests/csim/test_E13_DEC_sidestep_committed_detour.py` | (c) never the other side while the line is blocked (flip and mirror scenes); dropped on the first clear tick | 3 | 4 |
| `tests/skilllab/integration/test_sidestep_variant_a_fights.py` + `tests/skilllab/sidestep_blocks.py` | L-0054 and SIT-0106 seed 1: 100-tick block sha256 of A's every-2-tick files, end facts, per-tick `ended_short` and `stalled` checks, determinism | 5 | 7 (3 planted-trace controls, `stalled` on both fights, `ended_short` on SIT-0106, determinism) |

All 25 csim tests and 12 lab tests pass on `vA` (the reference). Mutations in `vA` and what went red: give-up pass live: 6 `no_giveup` tests and the three L-0054 whole-run tests (block 4 first differs, ends at tick 6645, 28 orders ended short); group-mate skip removed: `a_group_mate_does_not_deflect`; idle-friend skip removed: that and `an_idle_friend_does_not_deflect`; every friend skipped: the four controls `a_friend_that_holds_fires_moves_or_is_in_another_group_still_deflects`; committed side off (`side = 0`): both `a_unit_that_deflected_to_one_side...` cases; units that stop while their path is free (`dist < 900 && id % 7 == 0` never moves): `no_unit_stands_200_ticks...[L-0054]` red with 526 stalled entries. The `detour_dropped_on_the_first_clear_tick` test is red on main itself (the 60 wu hold), which is its named break.

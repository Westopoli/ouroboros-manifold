# Unowned and open reds, 2026-10-02

Base: origin/main `07319ccd` (A105 status corrections). Run: fresh worktree, `make -j8`, pipe and pipe_dbg built, `tests/csim` = 1191 passed, 129 failed (same as the piece audit, run at `8ef22647`; csrc and tests unchanged since). Read-only: no fixes. `tests/qa` and Godot tests were not run.

## 1. E-17: 25 failing tests, no owning piece

Common cause for all 25: `csrc/tactical_mapgen.c` still holds the freeze STUB bodies for the E-17 generator (`om_map_generate`, `om_map_generate_gradients`, `om_map_generate_spine`, `om_map_get_compatible_layout_count`, `om_map_get_compatible_layouts`, `om_map_select_layout_uniform`, `om_map_flavoring_stability_multiplier`, `om_map_setup_drifting_node`, `om_map_verify_flank_connections`, `om_proc_arch_resolve_section_piece` and the `om_gradient_*`, `om_fairness_*`, `om_render_*` family) returning 0 / doing nothing. Class for every row: missing implementation (stub), tests are unchanged skeleton fills and show no defect on inspection of the asserts. No row in `pieces.toml` lists any `test_E17_*` file as acceptance; B15m owns `tactical_mapgen.c` but its size_estimate says the full E-17 generator is "held". S-116 (canvas, `test_E17_S116_canvas.py`) passes only because `om_map_get_canvas_base_dimension` and `om_map_compute_modified_canvas` are real. Owner to assign: whoever takes the E-17 generator in `csrc/tactical_mapgen.c` (B15m is the file owner; acceptance list needs the 7 files below).

| Node id (all under `tests/csim/`) | Checks | Rule | Fails because |
|---|---|---|---|
| test_E17_S112_bones_from_the_library.py::test_R_112_01_every_layout_satisfying_at_least | every compatible layout for archetype 0 passes a filter | R-112-01 | layout count stub returns 0 (`0 >= 4`) |
| ::test_R_112_02_it_drawn_uniformly_at_random | layout draw uniform over 400 seeds | R-112-02 | select_layout_uniform stub returns 0 (`0 > 50`) |
| ::test_R_112_03_its_zone_positions_percentages_canvas | zone pos scales to canvas, jitter <= 3% | R-112-03 | instantiate_zone_pos stub (`4700.0 <= 0.0`) |
| ::test_R_112_04_layout_s_connectivity_honored_there | layout connectivity honored | R-112-04 | stub (`0 >= 2`) |
| ::test_R_112_05_it_holds_between_10_20 | layout holds 10 to 20 nodes (library size) | R-112-05 | library total stub (`8 <= 0`) |
| ::test_R_112_06_it_contains_only_zone_positions | layout file has required fields, no forbidden fields | R-112-06 | file-field checks stub (`0 == 1`) |
| test_E17_S113_nine_kinds_of_place.py::test_R_113_01_it_exactly_one_objective_staging | one objective plus staging per map | R-113-01 | generate stub, no nodes (`10 <= 0`) |
| ::test_R_113_02_it_has_at_least_one | map has at least one of a required node type | R-113-02 | no nodes (`0 >= 1`) |
| ::test_R_113_03_at_least_one_flank_route | at least one flank route | R-113-03 | has_flank_bypass stub (`0 > 0`) |
| ::test_R_113_04_it_reachable_from_both_staging | objective reachable from both staging | R-113-04 | reachability stub (`0 > 0`) |
| ::test_R_113_05_passable_width_w_200_wu | chokepoint width 200 wu rule | R-113-05 | compute_chokepoint_width stub (`0.0 == 300.0`) |
| test_E17_S114_texture_from_gradients.py::test_R_114_01_each_obstacle_density_cover_density | obstacle/cover density anchors | R-114-01 | gradients stub (`assert False`) |
| ::test_R_114_02_its_contribution_intensity_falloff_r | contribution = intensity falloff by radius | R-114-02 | sample stub (`0.0 == 0.4`) |
| ::test_R_114_03_obstacle_density_anchors_at_chokepoints | obstacle density anchors at chokepoints | R-114-03 | (`0.0 == 0.85`) |
| ::test_R_114_04_every_layer_not_listed_gets | unlisted layers get default | R-114-04 | (`0 == 1`) |
| test_E17_S115_the_region_shapes_the_terrain.py::test_R_115_01_interference_hazard_anchor_count_cover | region interference shapes hazard anchors/cover | R-115-01 | tension cover delta stub (`0.0 == 1.0`) |
| ::test_R_115_02_economy_lowers_obstacle_density_along | economy lowers obstacle density | R-115-02 | economy obstacle delta stub (`0.0 == 0.25`) |
| ::test_R_115_03_layouts_hints_alone_produce_valid | hints alone yield a valid map | R-115-03 | `om_map_is_valid` stub (`0 == 1`) |
| test_E17_S117_fair_enough.py::test_R_117_01_it_scores_route_count_staging | fairness scores route count, staging | R-117-01 | fairness_evaluate stub (`0 == 1`) |
| ::test_R_117_02_q_113_01_map_regenerated | unfair map regenerated (Q-113-01) | R-117-02 | fairness_run_post_generation_check stub |
| ::test_R_117_03_it_passes_hard_constraints_no | passes hard constraints, score not logged | R-117-03 | stub (`0 == 1`) |
| test_E17_S118_the_battlefield_moves.py::test_R_118_01_its_position_follows_path_ping | drifting node follows ping-pong path | R-118-01 | `om_map_setup_drifting_node` stub |
| ::test_R_118_02_its_position_moves_every_sampled | position changes at every sample | R-118-02 | same stub |
| test_E17_S119_terrain_that_reads_like_a_place.py::test_R_119_01_no_repeated_tile_boundary_visible | no repeated tile boundary | R-119-01 | render_detect stub |
| ::test_R_119_02_it_era_agnostic_at_section | section pieces era-agnostic | R-119-02 | proc_arch stubs |

Rows 18 to 25 messages were read from the first assert line only for S112 to S115 and S117 (exact `0 == 1` lines); S117-02, S118, S119 fail at the same stub class (return 0/no-op), confirmed by the stub bodies, not by individual assert text. Row ids are all `<file>::<test>` as printed by pytest `-rf`.

Other S-1xx E-17 tests that pass: S116 canvas (3), and the E-17 controls under `tests/csim/controls/`.

## 2. Named open reds

| Rule | Test id | What fails, why | Fix files (owner) | Class |
|---|---|---|---|---|
| R-078-06 (B9) | `test_E10_S078_a_battle_becomes_history.py::test_R_078_06_resulting_events_carry_mission_consequence` | `assert 0 == 1` at line 115. The test applies consequences, runs a 20-tick jump, then reads `om_chronicle_has_mission_consequence_flag`. The flag (`csrc/generational.c:633`) is defined as "band known and not yet consumed by a jump"; the jump consumes it (`generational.c:2054-2057` sets `consequence_consumed = 1`), so after the jump it reads 0. The sim does what the code comments and rulings-2 section 1.3 say; the test reads the flag after the thing that clears it. B9 owns only `csrc/mission.c`; the flag is in `generational.c`. | `csrc/generational.c` (B5-chronicle, B7b, B6-lifecycle); `tests/csim/test_E10_S078_*` | likely test defect (reads after consumption); or ruling needed on the flag's lifetime. Not missing behaviour: the consequence event is added in the jump |
| R-085-02 (B10b) | `test_E11_S085_long_enough_to_think.py::test_R_085_02_fight_lasts_150_to_200` | `assert 4320 <= 4000`. 50v50 default-balanced mirror runs 216 s, window is 150 to 200 s (3000 to 4000 ticks). | `csrc/unit.c` (B10b, B10c history), tuning constants in `csrc/om_constants.h`; `csrc/tactical_move.c` (B12/B12b) if movement-driven | finding (balance tuning); Westley owns thresholds. ledger bk-41: "possibly new from B10c-11" |
| R-085-04 (B10b) | `::test_R_085_04_strike_vs_strike_resolves_before` | `assert 2472 < 600` at line 93: Line-vs-Line (10 Vanguard, 300 wu) takes 2472 ticks; Siege-vs-Siege (10 Bombard, 1000 wu apart) ends in 600. Strike<Line passes. Order Line < Siege is violated. | `csrc/unit.c` (bombard damage/range, time to engage), `csrc/om_constants.h` | finding (behaviour or test geometry); test spawns Bombards 1000 wu apart, which may already be in range so siege ends fast: a design call (Architect) whether the fixture or the stats are wrong. Not a stub |
| R-130-02 (B14) | `test_E15_S130_the_battlefield_moves.py::test_R_130_02_hold_zone_moves_with_it` | `assert 1 == 0` at line 68. The test spawns a unit at the objective's old center `pos_0` after the objective drifted, expecting it not to contest the moved zone. Drift span is `OM_REINFORCEMENT_CAPTURE_RADIUS / 2` = 150 wu (`tactical_support.c:154`) and the contest radius is 300 wu, so the old center is always inside the moved zone: the test can never pass with these constants. Separately `om_objective_is_contested` counts any live unit (no faction check) although `om_unit_get_faction` now exists (comment `tactical_support.c:870` is stale). | `csrc/tactical_support.c` (B14) for the faction filter; constants or fixture for the geometry | mixed: (a) missing implementation (faction filter, small, accessor exists); (b) test or constant defect (span 150 < radius 300). Note: the test's `om_unit_spawn_combat(w, 1, pos_0.x, pos_0.y)` also has misnamed params in the header |

R-045-09 (not asked, E-06, B5): mean Knowledge Lost events 4.41, window 1.0 to 2.0. Balance finding, per ledger awaiting Westley.

## 3. The 99 detector-control failures

All in `tests/csim/controls/` (131 files, 99 fail, 31 pass). 92 are placeholder controls (E-06 to E-17): `OMBug` in `tests/csim/conftest.py` has no attribute for the injected bug (`AttributeError: type object 'OMBug' has no attribute ...`), and the pipe has no matching `OM_BUG_*` hook; listed in `docs/northstar/spec_factory/placeholder_controls.txt` (92 lines), excluded by `red_check.py --placeholder-list`. The other 7 are live controls whose injection does not trip: `composite_pre_clamp` (fixture does not overflow tension), `e03_window_starting_ratio_swapped` (fixture n_regions=4 infeasible), `e08_window_time_jump_clamp_skipped`, `e09_window_significance_cap_skipped`, `e11_window_brace_reduction_wrong_constant`, `e12_window_interference_ignores_intensity`, `e13_window_navmesh_cell_size_wrong_constant` (hooked bug does not change the observable, so the detector did not trip; either the hook is not wired in csrc or the control reads the wrong quantity). Owner status: no piece owns `tests/csim/controls/` or `OMBug` additions in `pieces.toml` (no match for "controls"); `tests/csim/conftest.py` is A94-harness. The earlier ledger flags these as pre-existing since day 1. `tests/qa/` controls were not run.

## 4. Coordinator addendum: B5b, B7b, B5-chronicle, G-flags

| Piece | Landing commit(s) on origin/main | Acceptance (pieces.toml) | Green now |
|---|---|---|---|
| B5b | `10a1faa3` "S-048 three tiers of tech. diplomacy.c fill stubs." (only commit naming S-048; no commit subject says B5b) | `tests/csim/test_E06_S048_three_tiers_of_technology.py` | yes (with B7b file: 9 passed) |
| B7b | no commit subject names B7b or S-055; the only B7b-named commit is the order row `1b8e5f38` (2026-10-01). `generational.c` increments on main: `61277731`, `346f8496`, `992198a0`, `f51f6488` (B6 stories A to D), `182d1c06`, `eb3b4e6a` (B6-collapse-pick), `797b3e3d` (GC3) | `tests/csim/test_E08_S055_one_commander_one_mission_then_the_world_moves.py` | yes |
| B5-chronicle | no commit subject "B5-chronicle"; B5-numbered commits on `generational.c`: `fd378b22` (B5-2 jump feeds chain events, distill_candidates), `0e92629a` (B5-4 chronicle selection cap), `c8daf236` (B5 consequence flag live, re-arm on mission end/refusal); contract row `c5ff2085` | none (`acceptance = []`); closest tests are E-09 acceptance (S-067 and neighbours, 0 red in the full run) and the one open E-10 red R-078-06 above, which concerns this flag | no acceptance to show; E-09 csim files green |
| G-flags | `4daebc83` "G4: debug overlay gated by ENABLE_DEBUG_OVERLAY" touched `autoload/feature_flags.gd` | none (`acceptance = []`, `tests_pending = true`); the gate test is `tests/test_debug_overlay_gate.gd` (Godot, not run here) | not verified: Godot not run |

B5b and B7b have acceptance green and increments on main, but no commit self-identifies as the piece's landing; attach is an Architect call on that basis. B5-chronicle and G-flags have no acceptance to show green.

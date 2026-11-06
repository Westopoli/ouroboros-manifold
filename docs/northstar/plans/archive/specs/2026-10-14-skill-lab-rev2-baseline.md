# Skill lab rev 2: baseline on main (records step)

Recorded 2026-10-13 by the records clerk on main at `b8edf56e` (equal to origin/main), before any LAB-REV2 build. Spec: `docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md`, Workflow step 1. Nothing below was fixed; it is the red and green the builders start from. The `LAB-REV2*` rows were added to `docs/northstar/plans/push/pieces.toml` in the same commit and change none of the numbers below (`pieces.py --check` counted 38 FAIL before and after the rows; `owner_lint.py` OK, `status_check.py` OK).

Python: `/home/westopoli/Projects/agora/.venv/bin/python` (the system `python3` has no pytest). The skill lab suite was run as eight parallel pytest processes over the 136 `test_*.py` files (`pytest tests/skilllab -q` as one process was projected at over an hour on this box under load); the csim suite as one process (it builds `libouroboros.so` into the repo root, so it is not split).

## `pytest tests/skilllab -q`

2543 passed, 2 failed, 80 skipped (2625 tests; the chunk runs took 26 s to 6 min each).

| Failing test | Line | Note |
|---|---|---|
| `tests/skilllab/integration/test_speed.py::test_scan_16_against_12_to_24_finishes_under_30_seconds` | `AssertionError: scan took 35.6 s`, `assert 35.63 < 30.0` | Failed in the 8-way run and again alone (89 s run, with the csim suite running beside it), so it is at least load sensitive. The 30 s mark is the old one; the rev 2 marks are ruling 13. Rerun on an idle box before reading it as a defect. |
| `tests/skilllab/ground/test_highground_real.py::test_control_3_h0_a_longer_climb_never_raises_the_break_even` | `assert 16 <= 15` (`HG.break_even('H0', 15, 1)` is 16, `HG.break_even('H0', 2, 1)` is 15) | Reproduces alone. Pre-existing. `ground/highground.py` and its tests are retired by L6, so this test is listed there. |

The 80 skips (78 in one chunk, one each in two others) are not itemised; their reasons were not read.

## `pytest tests/csim -q`

2938 passed, 124 failed, 110 skipped, 2 xfailed in 790 s (13 min). Every failure is pre-existing on main.

- 92 failures are `tests/csim/controls/test_control_*` (E-03 to E-17 detector controls). The one read in full fails with `AttributeError: type object 'OMBug' has no attribute 'EDGE_TYPE_DEFAULTS_TO_BOTH_FOR'`: the `OMBug` mirror in `tests/csim/conftest.py` lacks the debug-injection members these controls name (they were generated ahead of the debug build). E0 owns `conftest.py` and should not try to fix these; they are not LAB-REV2's.
- 32 failures are in other files, listed by full node id below; a red outside these 32 and outside `controls/` is new.

Failing ids outside `controls/` (32):

```
tests/csim/test_E06_S045_a_faction_s_technology_is_one_number.py::test_R_045_09_mean_over_all_windows_between
tests/csim/test_E11_S085_long_enough_to_think.py::test_R_085_04_strike_vs_strike_resolves_before
tests/csim/test_E13_A99_tactical_equivalence.py::test_A99_tactical_trace_equals_recorded_hashes[fight_990_gap1500]
tests/csim/test_E13_A99_tactical_equivalence.py::test_A99_tactical_trace_equals_recorded_hashes[fight_990_gap300]
tests/csim/test_E13_A99_tactical_equivalence.py::test_A99_tactical_trace_equals_recorded_hashes[fight_990_gap3000]
tests/csim/test_E17_S112_bones_from_the_library.py::test_R_112_01_every_layout_satisfying_at_least
tests/csim/test_E17_S112_bones_from_the_library.py::test_R_112_02_it_drawn_uniformly_at_random
tests/csim/test_E17_S112_bones_from_the_library.py::test_R_112_03_its_zone_positions_percentages_canvas
tests/csim/test_E17_S112_bones_from_the_library.py::test_R_112_04_layout_s_connectivity_honored_there
tests/csim/test_E17_S112_bones_from_the_library.py::test_R_112_05_it_holds_between_10_20
tests/csim/test_E17_S112_bones_from_the_library.py::test_R_112_06_it_contains_only_zone_positions
tests/csim/test_E17_S113_nine_kinds_of_place.py::test_R_113_01_it_exactly_one_objective_staging
tests/csim/test_E17_S113_nine_kinds_of_place.py::test_R_113_02_it_has_at_least_one
tests/csim/test_E17_S113_nine_kinds_of_place.py::test_R_113_03_at_least_one_flank_route
tests/csim/test_E17_S113_nine_kinds_of_place.py::test_R_113_04_it_reachable_from_both_staging
tests/csim/test_E17_S113_nine_kinds_of_place.py::test_R_113_05_passable_width_w_200_wu
tests/csim/test_E17_S114_texture_from_gradients.py::test_R_114_01_each_obstacle_density_cover_density
tests/csim/test_E17_S114_texture_from_gradients.py::test_R_114_02_its_contribution_intensity_falloff_r
tests/csim/test_E17_S114_texture_from_gradients.py::test_R_114_03_obstacle_density_anchors_at_chokepoints
tests/csim/test_E17_S114_texture_from_gradients.py::test_R_114_04_every_layer_not_listed_gets
tests/csim/test_E17_S115_the_region_shapes_the_terrain.py::test_R_115_01_interference_hazard_anchor_count_cover
tests/csim/test_E17_S115_the_region_shapes_the_terrain.py::test_R_115_02_economy_lowers_obstacle_density_along
tests/csim/test_E17_S115_the_region_shapes_the_terrain.py::test_R_115_03_layouts_hints_alone_produce_valid
tests/csim/test_E17_S117_fair_enough.py::test_R_117_01_it_scores_route_count_staging
tests/csim/test_E17_S117_fair_enough.py::test_R_117_02_q_113_01_map_regenerated
tests/csim/test_E17_S117_fair_enough.py::test_R_117_03_it_passes_hard_constraints_no
tests/csim/test_E17_S118_the_battlefield_moves.py::test_R_118_01_its_position_follows_path_ping
tests/csim/test_E17_S118_the_battlefield_moves.py::test_R_118_02_its_position_moves_every_sampled
tests/csim/test_E17_S119_terrain_that_reads_like_a_place.py::test_R_119_01_no_repeated_tile_boundary_visible
tests/csim/test_E17_S119_terrain_that_reads_like_a_place.py::test_R_119_02_it_era_agnostic_at_section
tests/csim/test_PP_portability.py::test_W7_probe_reproduces_pinned_checksums
tests/csim/test_VG_E_ke5.py::test_ke5_pipe_sidecar_format_version_is_10_and_matches_the_save
```

Failing tests under `tests/csim/controls/` (92, summarised by file prefix; not listed by id: they are red for one pre-existing reason, the missing `OMBug` members, so a later red in this directory beyond these counts per epic is new):

| Epic | Files | Failing |
|---|---|---|
| E-03 | `tests/csim/controls/test_control_e03_*` | 9 |
| E-06 | `tests/csim/controls/test_control_e06_*` | 7 |
| E-07 | `tests/csim/controls/test_control_e07_*` | 6 |
| E-08 | `tests/csim/controls/test_control_e08_*` | 9 |
| E-09 | `tests/csim/controls/test_control_e09_*` | 9 |
| E-10 | `tests/csim/controls/test_control_e10_*` | 9 |
| E-11 | `tests/csim/controls/test_control_e11_*` | 8 |
| E-12 | `tests/csim/controls/test_control_e12_*` | 6 |
| E-13 | `tests/csim/controls/test_control_e13_*` | 8 |
| E-14 | `tests/csim/controls/test_control_e14_*` | 7 |
| E-15 | `tests/csim/controls/test_control_e15_*` | 7 |
| E-17 | `tests/csim/controls/test_control_e17_*` | 7 |
| Total | `tests/csim/controls/` | 92 |

Two of these touch the numbers E0 will move: `tests/csim/test_VG_E_ke5.py::test_ke5_pipe_sidecar_format_version_is_10_and_matches_the_save` (a save-format pin already red on main, which E0 will rewrite) and `tests/csim/test_PP_portability.py::test_W7_probe_reproduces_pinned_checksums` (pinned checksums, red before E0). The E1 stall-scene and arc scenes the spec names do not exist yet, so no csim trace hash of the arc scene at 360 is recorded here; the test writer for E2 records it on the built tree (spec Workflow step 1 names it, but the scene is E2's).

## `pieces.py --check`

38 FAIL (the spec's pre-flight counted 44 on an earlier origin/main; the number moves with other lanes' landings). Taken before and after adding the LAB-REV2 rows: 38 both times. The failures are the pre-existing acceptance-collect failures and owns-overlap findings in other lanes; none names a LAB-REV2 row. The take-over `depends_on` entries on `LAB-REV2-E1` and `LAB-REV2-L7` (see the row comments) exist to keep this number at 38; without them the rows added 8 owns-overlap FAILs.

## Golden hashes and the controls

`tests/skilllab/golden_hashes.json`:

| Key | sha256 |
|---|---|
| mirror | `633867f88ce3549e9fa8d47d99436a073bea70a2e73f8c977cd0b017934edfbc` |
| numbers | `928f721cd11895c3bc5a32ad97b004d69ce64d0af8f9c7c5a70ae2a6f1949b9c` |
| planted | `71f7efb262e02a59e87da6126841d74015bbd04cc340cd3d749b63ee4997dd15` |

`tests/skilllab/integration/test_cross_machine.py` (it recomputes the three hashes from the control rows and compares them with the file) is green in the skill lab run above: the old lab on today's engine reproduces the goldens. This is the reference for the engine-only parity proof after E0 to E3.

`python3 -m scripts.skilllab controls --out <dir>` exits 0 in 104 s on one worker (103 s user time), writes `controls.csv` (680 data rows) and `report.html`. sha256 of that `controls.csv` on this tree: `9748cfb87707930f32c0100f366495e778c75ea261bcbe333ae2f8fb371a25eb` (for comparison only; the goldens above hash the rows by a different route, so the two are not expected to be equal).

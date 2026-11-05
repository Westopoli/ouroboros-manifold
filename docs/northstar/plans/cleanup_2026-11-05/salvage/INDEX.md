# Salvage patches from retired worktrees, 2026-11-05

Each patch is the uncommitted tracked work (`git diff HEAD`, plus `git diff --cached` when it differs) found in a worktree that is being deleted. The patches are kept only so nothing is lost silently. They are never to be applied: they were cut against old commits and nobody is expected to need them.

Filtered out as noise before looking: untracked files, `.import`, `.uid`, `pipe/`, `.wt-state`, `shots/` directories, `scratch/`, probe `o.json` and `err.txt`, `build/` products and `.swarm/` bookkeeping. Trees whose only remaining change was binary are not listed here.

69 patches, 2052525 bytes in total.

| Tree | Branch | Head sha | Head date | Summary |
|---|---|---|---|---|
| [om-a81-main](om-a81-main.patch) (`~/Projects/om-a81-main`) | HEAD | 81e0c833 | 2026-10-02 | Tracked edits to 5 file(s) (test_pipe_chapter_lifecycle.py, test_pipe_debrief_region_delta.py, test_pipe_mission_over.py and 2 more), +72/-24 lines. |
| [a111-probe-98272d72](a111-probe-98272d72.patch) (`~/Projects/om-push/a111-probe-98272d72`) | HEAD | 98272d72 | 2026-09-24 | Tracked edits to 1 file(s) (test_E08_S055_one_commander_one_mission_then_the_world_moves.py), +47/-3 lines. |
| [a111-probe-9d7cfdd8](a111-probe-9d7cfdd8.patch) (`~/Projects/om-push/a111-probe-9d7cfdd8`) | HEAD | 9d7cfdd8 | 2026-09-24 | Identical to a111-probe-98272d72.patch. |
| [a111-probe-aea2abab](a111-probe-aea2abab.patch) (`~/Projects/om-push/a111-probe-aea2abab`) | HEAD | aea2abab | 2026-09-24 | Identical to a111-probe-98272d72.patch. |
| [a111-probe-ed4a95cb](a111-probe-ed4a95cb.patch) (`~/Projects/om-push/a111-probe-ed4a95cb`) | HEAD | ed4a95cb | 2026-09-24 | Identical to a111-probe-98272d72.patch. |
| [wt-TDmo](wt-TDmo.patch) (`~/Projects/om-push/clerk-wt/wt-TDmo`) | push/TD-mo-scratch | f85c2599 | 2026-10-01 | Tracked edits to 1 file(s) (test_pipe_mission_over.py), +57/-25 lines. |
| [m3](m3.patch) (`~/Projects/om-push/m3`) | push/look6 | 29ed61c4 | 2026-09-24 | Tracked edits to 1 file(s) (qa_backlog.md), +1/-0 lines. |
| [relay04-land](relay04-land.patch) (`~/Projects/om-push/relay04-land`) | land/relay-04 | 495c5fbd | 2026-10-01 | Tracked edits to 1 file(s) (test_pipe_mission_over.py), +15/-12 lines. |
| [A23-bis](A23-bis.patch) (`~/Projects/om-push/wt/A23-bis`) | HEAD | 8bcda7fd | 2026-10-02 | Tracked edits to 1 file(s) (unit.c), +1/-1 lines. |
| [PP-land2](PP-land2.patch) (`~/Projects/om-push/wt/PP-land2`) | push/pp-a-land2 | 10f8c444 | 2026-10-02 | Tracked edits to 1 file(s) (test_E13_S101_movement_that_reads.py), +1/-1 lines. |
| [c25-records](c25-records.patch) (`~/Projects/om-push/wt/c25-records`) | push/vg-c25-records | ad93d746 | 2026-10-21 | Tracked edits to 29 file(s) (CLAUDE.md, E-08-generational-structure.md, E-11-units-and-combat.md and 26 more), +825/-186 lines. Index holds an unmerged conflict; patch is `git diff HEAD`, best effort. |
| [chk-e7-base-c](chk-e7-base-c.patch) (`~/Projects/om-push/wt/chk-e7-base-c`) | HEAD | 2d6ac1be | 2026-10-20 | Tracked edits to 27 file(s) (conftest.py, test_E01_T3_contract.py, test_E01_T3_mission_ground.py and 24 more), +211/-750 lines. |
| [chk-e7-build-ref](chk-e7-build-ref.patch) (`~/Projects/om-push/wt/chk-e7-build-ref`) | HEAD | f62917be | 2026-10-20 | Tracked edits to 22 file(s) (test_E01_T3_contract.py, test_E01_T3_mission_ground.py, test_E02_S020_abi.py and 19 more), +790/-74 lines. |
| [chk-e7-m20](chk-e7-m20.patch) (`~/Projects/om-push/wt/chk-e7-m20`) | HEAD | 985b2df6 | 2026-10-20 | Tracked edits to 21 file(s) (conftest.py, test_E01_T3_contract.py, test_E01_T3_mission_ground.py and 18 more), +175/-77 lines. |
| [chk-e7-rev](chk-e7-rev.patch) (`~/Projects/om-push/wt/chk-e7-rev`) | HEAD | 49df672c | 2026-10-20 | Tracked edits to 7 file(s) (checksum_full.c, mission.c, om_internal.h and 4 more), +25/-128 lines. |
| [chk-vg-a18cam-main](chk-vg-a18cam-main.patch) (`~/Projects/om-push/wt/chk-vg-a18cam-main`) | HEAD | 033790f7 | 2026-10-13 | Tracked edits to 1 file(s) (play_support.py), +21/-4 lines. |
| [chk-vg-a18cam-r2-comb](chk-vg-a18cam-r2-comb.patch) (`~/Projects/om-push/wt/chk-vg-a18cam-r2-comb`) | HEAD | 44b1f62b | 2026-10-13 | Tracked edits to 8 file(s) (pieces.toml, push_ledger_2026-09-22.md, play_support.py and 5 more), +68/-9 lines. |
| [chk-vg-a18cam-r2-mb](chk-vg-a18cam-r2-mb.patch) (`~/Projects/om-push/wt/chk-vg-a18cam-r2-mb`) | HEAD | 42c36f64 | 2026-10-13 | Tracked edits to 1 file(s) (test_tactical_camera.gd), +320/-0 lines. |
| [chk-vg-dview-c3-scratch](chk-vg-dview-c3-scratch.patch) (`~/Projects/om-push/wt/chk-vg-dview-c3-scratch`) | HEAD | a3495155 | 2026-10-13 | Tracked edits to 2 file(s) (space_view.gd, layer_view.gd), +3/-1 lines. |
| [chk-vg-dview-rev](chk-vg-dview-rev.patch) (`~/Projects/om-push/wt/chk-vg-dview-rev`) | HEAD | e60ac3b6 | 2026-10-13 | Tracked edits to 5 file(s) (sheet_tube.gdshader, space_rings.gd, space_sheets.gd and 2 more), +0/-728 lines. |
| [d-M27](d-M27.patch) (`~/Projects/om-push/wt/d-M27`) | push/d-M27 | 09d8a4ba | 2026-11-01 | Tracked edits to 1 file(s) (method_check.py), +1/-0 lines. |
| [diag-walk-main](diag-walk-main.patch) (`~/Projects/om-push/wt/diag-walk-main`) | HEAD | 5d3521d8 | 2026-10-10 | Tracked edits to 1 file(s) (tactical_move.c), +6/-0 lines. |
| [e0-regold-main](e0-regold-main.patch) (`~/Projects/om-push/wt/e0-regold-main`) | push/labrev2-e0-regold-main-local | 4fe71ea2 | 2026-10-29 | Tracked edits to 3 file(s) (test_E01_T2_collision_mask.py, test_E01_T2_walker_waypoint_arrival.py, test_PP_portability.py), +7/-6 lines. |
| [flake-rootcause](flake-rootcause.patch) (`~/Projects/om-push/wt/flake-rootcause`) | push/flake-rootcause | 829f2444 | 2026-10-06 | Tracked edits to 4 file(s) (qa_daemon.gd, scene_router.gd, mission_briefing.gd and 1 more), +16/-1 lines. |
| [gate-w4](gate-w4.patch) (`~/Projects/om-push/wt/gate-w4`) | HEAD | 32fe3cca | 2026-10-08 | Tracked edits to 4 file(s) (scene_router.gd, lobby.gd, lobby.tscn and 1 more), +1/-344 lines. |
| [inv-landview](inv-landview.patch) (`~/Projects/om-push/wt/inv-landview`) | inv/landview | bd814657 | 2026-10-22 | Tracked edits to 2 file(s) (qa_daemon.gd, tactical_view.gd), +57/-0 lines. |
| [labdiag](labdiag.patch) (`~/Projects/om-push/wt/labdiag`) | HEAD | ec8904f6 | 2026-10-20 | Tracked edits to 29 file(s) (pieces.toml, __main__.py, asym.py and 26 more), +555/-2706 lines. |
| [labrev2-base-audit](labrev2-base-audit.patch) (`~/Projects/om-push/wt/labrev2-base-audit`) | HEAD | 4c638fc0 | 2026-10-19 | Tracked edits to 3 file(s) (formations.py, scenes.py, sweep.py), +79/-22 lines. |
| [labrev2-captrace2](labrev2-captrace2.patch) (`~/Projects/om-push/wt/labrev2-captrace2`) | HEAD | b7b6fa3e | 2026-10-19 | Tracked edits to 1 file(s) (contract.py), +1/-1 lines. |
| [labrev2-e2-audit](labrev2-e2-audit.patch) (`~/Projects/om-push/wt/labrev2-e2-audit`) | HEAD | 9a1731c1 | 2026-10-14 | Tracked edits to 2 file(s) (tactical_move.c, unit.c), +82/-9 lines. |
| [labrev2-e2-scratch](labrev2-e2-scratch.patch) (`~/Projects/om-push/wt/labrev2-e2-scratch`) | HEAD | 2d0bb5ca | 2026-10-14 | Tracked edits to 5 file(s) (tactical_move.c, unit.c, test_E11_S082_cone.py and 2 more), +269/-50 lines. |
| [labrev2-l2-audit-scratch](labrev2-l2-audit-scratch.patch) (`~/Projects/om-push/wt/labrev2-l2-audit-scratch`) | HEAD | 19f70212 | 2026-10-14 | Tracked edits to 13 file(s) (skilllab-harness-spec.md, asym.py, batches.py and 10 more), +330/-294 lines. |
| [labrev2-l3-audit-ref](labrev2-l3-audit-ref.patch) (`~/Projects/om-push/wt/labrev2-l3-audit-ref`) | HEAD | d95d7df3 | 2026-10-14 | Tracked edits to 2 file(s) (plays_drafts.md, plays_space.py), +178/-73 lines. |
| [labrev2-l4-ref](labrev2-l4-ref.patch) (`~/Projects/om-push/wt/labrev2-l4-ref`) | scratch/labrev2-l4-ref | 80734051 | 2026-10-14 | Tracked edits to 36 file(s) (__main__.py, batches.py, breakeven.py and 33 more), +953/-830 lines. |
| [labrev2-l4-ref2](labrev2-l4-ref2.patch) (`~/Projects/om-push/wt/labrev2-l4-ref2`) | HEAD | 4566f787 | 2026-10-19 | Tracked edits to 18 file(s) (__main__.py, summary.py, sweep.py and 15 more), +579/-135 lines. |
| [labrev2-l4-ref3](labrev2-l4-ref3.patch) (`~/Projects/om-push/wt/labrev2-l4-ref3`) | HEAD | 4566f787 | 2026-10-19 | Tracked edits to 18 file(s) (__main__.py, summary.py, sweep.py and 15 more), +613/-137 lines. |
| [labrev2-l6-scratch](labrev2-l6-scratch.patch) (`~/Projects/om-push/wt/labrev2-l6-scratch`) | HEAD | 3e7ee908 | 2026-10-14 | Tracked edits to 5 file(s) (fight.py, README.md, highground.py and 2 more), +59/-891 lines. |
| [labrev2-l8-e1bcheck](labrev2-l8-e1bcheck.patch) (`~/Projects/om-push/wt/labrev2-l8-e1bcheck`) | HEAD | 59416a00 | 2026-10-19 | Tracked edits to 4 file(s) (contract.py, fight.py, rows.py and 1 more), +63/-3 lines. |
| [labrev2-l8-ref](labrev2-l8-ref.patch) (`~/Projects/om-push/wt/labrev2-l8-ref`) | HEAD | c0bd6e9f | 2026-10-19 | Tracked edits to 6 file(s) (contract.py, fight.py, rows.py and 3 more), +212/-18 lines. |
| [labrev2-roles-check](labrev2-roles-check.patch) (`~/Projects/om-push/wt/labrev2-roles-check`) | HEAD | 2faf9488 | 2026-10-19 | Tracked edits to 1 file(s) (test_drift_fix_roles.py), +15/-5 lines. |
| [pre-escr](pre-escr.patch) (`~/Projects/om-push/wt/pre-escr`) | HEAD | c6f3f883 | 2026-10-20 | Tracked edits to 1 file(s) (events_feed.gd), +6/-0 lines. |
| [records-batch7](records-batch7.patch) (`~/Projects/om-push/wt/records-batch7`) | HEAD | ccd89b7f | 2026-10-23 | Tracked edits to 28 file(s) (CLAUDE.md, algorithms.md, E-01-layer-system.md and 25 more), +304/-164 lines. |
| [s140-probe](s140-probe.patch) (`~/Projects/om-push/wt/s140-probe`) | push/s140-probe | 10b4ddb9 | 2026-11-02 | Tracked edits to 1 file(s) (daemon_client.py), +10/-1 lines. |
| [sc-fl2](sc-fl2.patch) (`~/Projects/om-push/wt/sc-fl2`) | push/showcase-fl2 | 543f6c04 | 2026-10-23 | Tracked edits to 1 file(s) (first_look.md), +26/-27 lines. |
| [sc-qa2](sc-qa2.patch) (`~/Projects/om-push/wt/sc-qa2`) | push/showcase-qa2 | 543f6c04 | 2026-10-23 | Tracked edits to 1 file(s) (code_quality.md), +66/-40 lines. |
| [scout-edgescroll](scout-edgescroll.patch) (`~/Projects/om-push/wt/scout-edgescroll`) | HEAD | fba3c4c8 | 2026-10-13 | Tracked edits to 1 file(s) (tactical_view.gd), +3/-0 lines. |
| [scout-westley-owner](scout-westley-owner.patch) (`~/Projects/om-push/wt/scout-westley-owner`) | HEAD | 1aa1dbc0 | 2026-10-13 | Tracked edits to 4 file(s) (merge_gate_support.py, pieces.py, test_merge_gate_support.py and 1 more), +72/-0 lines. |
| [vg-a-land-8](vg-a-land-8.patch) (`~/Projects/om-push/wt/vg-a-land-8`) | push/vg-a-land-8 | 89e7fe71 | 2026-10-09 | Tracked edits to 2 file(s) (push_ledger_2026-09-22.md, test_tactical_play.py), +7/-5 lines. |
| [vg-a17-play](vg-a17-play.patch) (`~/Projects/om-push/wt/vg-a17-play`) | push/vg-a17-play | 711d9ed9 | 2026-10-12 | Tracked edits to 1 file(s) (play_support.py), +99/-21 lines. |
| [vg-b-tests-fix-6](vg-b-tests-fix-6.patch) (`~/Projects/om-push/wt/vg-b-tests-fix-6`) | push/vg-b-tests-fix-6 | 44f4d318 | 2026-10-08 | Tracked edits to 1 file(s) (push_ledger_2026-09-22.md), +1/-1 lines. |
| [vg-b20](vg-b20.patch) (`~/Projects/om-push/wt/vg-b20`) | push/vg-b20 | a45f86c3 | 2026-10-08 | Tracked edits to 3 file(s) (galaxy_view.gd, shell_labels.gd, shell_renderer.gd), +13/-11 lines. |
| [vg-dview-b3-base](vg-dview-b3-base.patch) (`~/Projects/om-push/wt/vg-dview-b3-base`) | HEAD | 0f47bd9a | 2026-10-13 | Tracked edits to 1 file(s) (tactical_view.gd), +1/-0 lines. |
| [vg-dview-scratch2](vg-dview-scratch2.patch) (`~/Projects/om-push/wt/vg-dview-scratch2`) | HEAD | d42a332d | 2026-10-13 | Tracked edits to 2 file(s) (space_view.gd, S-246.py), +16/-7 lines. |
| [vg-dview-tests-run](vg-dview-tests-run.patch) (`~/Projects/om-push/wt/vg-dview-tests-run`) | HEAD | 0f47bd9a | 2026-10-13 | Tracked edits to 1 file(s) (project.godot), +1/-1 lines. |
| [vg-e1c-3](vg-e1c-3.patch) (`~/Projects/om-push/wt/vg-e1c-3`) | push/vg-e1c-3 | 441c34bc | 2026-10-10 | Tracked edits to 1 file(s) (economy_lots.c), +19/-9 lines. |
| [vg-e1q-rulings-verify](vg-e1q-rulings-verify.patch) (`~/Projects/om-push/wt/vg-e1q-rulings-verify`) | HEAD | 27425959 | 2026-10-11 | Tracked edits to 1 file(s) (test_VG_E_ke5.py), +4/-2 lines. |
| [vg-e7](vg-e7.patch) (`~/Projects/om-push/wt/vg-e7`) | push/vg-e7 | a2efbd97 | 2026-10-14 | Tracked edits to 11 file(s) (checksum_full.c, mission.c, om_internal.h and 8 more), +165/-34 lines. |
| [vg-e7-proto](vg-e7-proto.patch) (`~/Projects/om-push/wt/vg-e7-proto`) | HEAD | fa2fd636 | 2026-10-14 | Tracked edits to 3 file(s) (mission.c, ouroboros_sim.h, tactical_support.c), +48/-10 lines. |
| [vg-e7r-exp2](vg-e7r-exp2.patch) (`~/Projects/om-push/wt/vg-e7r-exp2`) | HEAD | b7b347db | 2026-10-20 | Tracked edits to 1 file(s) (mission.c), +3/-1 lines. |
| [vg-harness-c1b-red](vg-harness-c1b-red.patch) (`~/Projects/om-push/wt/vg-harness-c1b-red`) | HEAD | c2ff6b4d | 2026-10-20 | Tracked edits to 2 file(s) (test_pre_gate.py, test_status_check.py), +65/-5 lines. |
| [vg-k0-land](vg-k0-land.patch) (`~/Projects/om-push/wt/vg-k0-land`) | push/vg-k0-land | 9c9e9385 | 2026-10-07 | Tracked edits to 1 file(s) (pieces.toml), +1/-1 lines. |
| [vg-nettick-diag](vg-nettick-diag.patch) (`~/Projects/om-push/wt/vg-nettick-diag`) | HEAD | 25ea1a1e | 2026-10-12 | Tracked edits to 1 file(s) (test_vg_f_nettick.gd), +1/-1 lines. |
| [vg-prodslot-mv](vg-prodslot-mv.patch) (`~/Projects/om-push/wt/vg-prodslot-mv`) | HEAD | 10144ff3 | 2026-10-21 | Tracked edits to 1 file(s) (tactical_support.c), +4/-5 lines. |
| [vg-w2s-tests3-build](vg-w2s-tests3-build.patch) (`~/Projects/om-push/wt/vg-w2s-tests3-build`) | HEAD | 09130f3e | 2026-10-13 | Tracked edits to 1 file(s) (test_VG_W_w2_routes.py), +181/-0 lines. |
| [tmp-lm-fixture](tmp-lm-fixture.patch) (`/var/tmp/om-push/tmp-lm-fixture`) | HEAD | 3751a69a | 2026-10-23 | Tracked edits to 1 file(s) (test_vg_c_land_marks.gd), +13/-5 lines. |
| [tmp-lm-slice](tmp-lm-slice.patch) (`/var/tmp/om-push/tmp-lm-slice`) | HEAD | c25df880 | 2026-10-23 | Tracked edits to 2 file(s) (ground3d.gd, test_vg_c_land_marks.gd), +114/-0 lines. |
| [tmp-rf-check](tmp-rf-check.patch) (`/var/tmp/om-push/tmp-rf-check`) | HEAD | dd728768 | 2026-10-23 | Tracked edits to 2 file(s) (test_merge_gate_support.py, test_owner_lint.py), +7/-7 lines. |
| [tmp-ud-fresh](tmp-ud-fresh.patch) (`/var/tmp/om-push/tmp-ud-fresh`) | HEAD | 080e7507 | 2026-10-23 | Tracked edits to 1 file(s) (test_gate_userdir.py), +2/-0 lines. |
| [tmp-vl-check](tmp-vl-check.patch) (`/var/tmp/om-push/tmp-vl-check`) | HEAD | ff8163d1 | 2026-10-22 | Tracked edits to 1 file(s) (test_gate_venv_link.py), +40/-4 lines. |

## Skipped

- `~/Projects/om-push/m1` (branch main, head b658b9b3, 2026-09-24): only `.swarm` bookkeeping changes.
- `~/Projects/om-push/m2` (branch main, head 1f60c304, 2026-09-22): only `.swarm` bookkeeping changes.
- `~/Projects/om-push/wt/_stale/chk-harness-journal-20261010` (branch HEAD, head e415dfff, 2026-10-10): over 2 MB (generated data: transcripts, run CSVs, logs, graph files, build products).
- `~/Projects/om-push/wt/_stale/chk-harness-pregate-20261010` (branch HEAD, head 91f0eb8e, 2026-10-10): over 2 MB (generated data: transcripts, run CSVs, logs, graph files, build products).
- `~/Projects/om-push/wt/site-captures` (branch HEAD, head 3b455c89, 2026-10-06): no text hunks (binary or mode-only change).

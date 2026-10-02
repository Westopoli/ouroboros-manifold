# C4-E3 tests note (legacy scenes/tactical/ deleted)

Test: `tests/test_legacy_tactical_deleted.gd` (headless). E3-1 dir gone, E3-2 no non-comment line outside scenes/tactical/ names `scenes/tactical/` (scan skips .swarm, graphify-out, docs, simulation, this file, the G6 ratchet), E3-3 router has no "tactical" key. Controls C1 matcher, C2 walk and live scene tactical_c still loads.

Red on main: E3-1, E3-2 (9 holders: autoload/scene_router.gd, autoload/tactical_bridge.gd, scenes/debug/test_squad_impact_origins.gd + .tscn, tests/test_b3_tutorial_integration.gd, tests/test_cover_render.gd, tests/test_input_router_control_groups.gd, tests/test_input_router_selection.gd, tests/test_qa_state_scenes.gd), E3-3. Green with temp patch (delete dir, drop router route, drop perf-logger preload, retire/edit tests below). Patch reverted.

## Test classification (every test touching scenes/tactical/)

| Test | Proves | Baseline on main | Class | Reason |
|---|---|---|---|---|
| tests/test_cover_render.gd | terrain_renderer `_scatter_cover_asteroids`: 4 MultiMesh per scale class | red (compile error, bridge identifier) | retire | legacy 3D renderer only. Live tactical_c draws no cover asteroids: behaviour gap, not covered. |
| tests/test_input_router_selection.gd + .tscn | legacy input_router click select + fog gate | red (compile error) | retire | legacy only. Live select/fog (R-089-04) proved by tests/test_tactical_view.gd. |
| tests/test_input_router_control_groups.gd + .tscn | legacy `_bind_group`/`_recall_group` | red (aborted) | retire | legacy only. Control groups do not exist in tactical_c (Q-110-04 closed: no rebinding until Q-005-03/Q-103-04): behaviour gap, flagged. |
| tests/test_b3_tutorial_integration.gd | tutorial wiring in main_menu, tactical.gd, project.godot | red (main_menu Replay Tutorial asserts, G3 removed it) | test-defect, edit | drop TACTICAL_PATH block (tactical.gd lines 51-55). The main_menu asserts already contradict G3 (Replay Tutorial leaves); tutorial chain parked. Recommend retire whole file in C1/G3 ledger. |
| tests/test_qa_state_scenes.gd | qa_state on every REQUIRED scene | green 260 | test-defect, edit | drop the tactical REQUIRED entry and two comment lines naming scenes/tactical/. Green 247 after. |
| tests/test_tacticalbridge_ratchet.gd | G6 ratchet | green | test-defect, edit | KNOWN_REFERENCERS lose the 12 scenes/tactical/* rows (and scenes/debug/test_squad_impact_origins.gd if deleted): ledger row. |
| simulation/test_wave3_blockers_umbrella.py `test_umbrella_f_tactical_emits_unit_signals` | tactical.gd mentions first_unit_* signals | legacy Python tooling | retire | reads the deleted file. Outside E3-2 scan (simulation/ skipped); same ledger row. |

Not affected (name the bridge or the path in comments only): test_boot_scripts_parse (green), test_debug_overlay_gate, test_tactical_view, test_tactical_hud, tests/qa/desktop/test_tactical_play.py (uses tactical_c).

## Ordering finding

`autoload/tactical_bridge.gd` line 57 preloads `scenes/tactical/perf_logger.gd`. E3 cannot land while the autoload keeps that preload (parse failure at boot). Either G6 (remove autoload, plan puts it after E3) goes first, or E3 includes a one-line edit dropping the logger. Plan G6 says "once G4 and E2 no longer read it" and does not cover MissionMetricsRecorder, ws_input_sanitizer, qa_daemon. See Q-C4-E3-01.

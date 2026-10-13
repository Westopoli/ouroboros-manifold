# Visible game programme: plan vs reality (origin/main 1a8bbe19, 2026-10-10 09:12 -0400)

Method. `pieces.toml` has 22 VG rows, each a whole lane (for example VG-A holds the 20 lane A pieces), so no per-file piece rows exist. Piece state below is read from file existence on origin/main (`git cat-file -e`), the branch tips (`git branch -r --merged origin/main`) and the programme's lane-state text. Spec section 8 counts 118 per-file pieces; K0 is counted as 9 files, K-a as 9, K-f 2, K-h 2, K-d 3. Lane D's nine are my enumeration (the spec names eight items and the D hook). Lane E1 has 16 lettered ids but the spec counts 22; the other 6 cannot be mapped and are shown as UNMAPPED. All times are local (-0400).

## 1. Piece table

| lane | piece | planned file | state | evidence |
|---|---|---|---|---|
| GUARD | G1 | scripts/specfactory/merge_gate.sh + merge_gate_support.py (look stage) | LANDED | aef3b11f; vg-guard-land 134f070b 10-07 |
| GUARD | G2 | autoload/qa_daemon.gd (driver verbs) | LANDED | e5b1f7c0; vg-guard-land |
| GUARD | G3 | autoload/qa_daemon.gd (state inventory) | LANDED | 5d207de0; vg-guard-land |
| GUARD | G4 | docs/northstar/story_reviews/README.md, agile.md Seen, stories.md header | LANDED | f35f4d8b; vg-guard-land |
| GUARD | G5 | Agora text pre-filter | NOT STARTED | no branch, file or doc mention |
| GUARD | G6 | docs/northstar/baselines/2026-10-07_visible/ (baseline capture) | NOT STARTED | directory absent on main; no branch |
| GUARD | G7 | CLAUDE.md guards + ROADMAP lane rows | LANDED | fff305ed; CLAUDE.md guard 7 present |
| GUARD | G8 | nightly 30B play | NOT STARTED | no branch, file or doc mention |
| K0 | K0 (9 files) | architecture.md field table, ouroboros_sim.h + signatures.toml (8 getters), stubs in 5 .c files, bindings, ABI 4 to 5 | LANDED | vg-k0-land 9c9e9385 10-07; 8 symbols in header on main (ABI now 6) |
| K-a | K-a.1 | csrc/unit.c (fire/kill events, state bits) | LANDED | vg-ka-unit f3b8d249 |
| K-a | K-a.2 | csrc/tactical_support.c (structure getters, capture events) | LANDED | vg-ka-support-2 fd6352d4 |
| K-a | K-a.3 | csrc/mission.c (om_objective_get_done) | LANDED | vg-ka-mission e914d4d4 |
| K-a | K-a.4 | csrc/fog.c (sight) | LANDED | vg-ka-fog; no-op, getter existed (K-a ruling 5) |
| K-a | K-a.5 | csrc/tactical_move.c (layer target) | LANDED | vg-ka-move; no-op, getter existed (K-a ruling 5) |
| K-a | K-a.6 | csrc/tactical_mapgen.c (obstacles, cover class) | LANDED | vg-ka-mapgen 7afd8aed |
| K-a | K-a.7 | csrc/terrain.c (om_terrain_get_heights) | LANDED | vg-ka-terrain c960ac93 |
| K-a | K-a.8 | csrc/pipe/om_pipe.c (frame fields; now pipe_tactical.c) | LANDED | vg-ka-pipe-2 ea733d30; vg-ka2-land-2 fa243f75 10-08 |
| K-a | K-a.9 | autoload/c_bridge.gd (decoders, set_layer, heights) | LANDED | vg-ka-bridge ca568d8c; vg-ka2-land-2 fa243f75 |
| K-f | K-f.1 | csrc/pipe/om_pipe.c (net_step frame, _setmode) | LANDED | vg-kf e7e345be; vg-kf-land 0c75367f 10-07 |
| K-f | K-f.2 | autoload/c_bridge.gd (exe-relative pipe, OM_PIPE) | LANDED | vg-kf-land 0c75367f; c_bridge.gd:203 |
| K-h | K-h.1 | csrc/pipe/om_pipe.c (mission_start fog_filter) | LANDED | vg-kh-pipe-2 0ddffa88; vg-kh-land f61c89fc 10-08 |
| K-h | K-h.2 | autoload/c_bridge.gd (load_mission_live fog_filter) | LANDED | vg-kh-bridge 132a8f9a; c_bridge.gd:687 |
| K-d | K-d.1 | csrc/space_field.c + ouroboros_sim.h getters | LANDED | vg-kd e3a86895; vg-kd-land 10-08 |
| K-d | K-d.2 | space_field_dump verb (pipe) | LANDED | vg-kd-land; om_pipe.c:1167 |
| K-d | K-d.3 | c_bridge.gd space_field decode | LANDED | vg-kd-land; c_bridge.gd:617-624 |
| A | A1 | scenes/tactical_c/unit_visuals.gd | LANDED | 6c958647; vg-aa-land/vg-ab-land-2, 10-08 |
| A | A1b | scenes/tactical_c/unit_squads.gd | LANDED | 03d29097; vg-aa-land/vg-ab-land-2, 10-08 |
| A | A2 | scenes/tactical_c/unit_motion.gd | LANDED | 9c0cf065; vg-aa-land/vg-ab-land-2, 10-08 |
| A | A3 | scenes/tactical_c/layer_view.gd | LANDED | 150362f6; vg-aa-land/vg-ab-land-2, 10-08 |
| A | A4 | scenes/tactical_c/fog_layer.gd | LANDED | d1f71017; vg-aa-land/vg-ab-land-2, 10-08 |
| A | A5 | scenes/tactical_c/map_layer.gd | LANDED | 36da56fb; vg-aa-land/vg-ab-land-2, 10-08 |
| A | A5b | scenes/tactical_c/objective_markers.gd | LANDED | b7dc44cd; vg-aa-land/vg-ab-land-2, 10-08 |
| A | A6 | scenes/tactical_c/hud/objectives_panel.gd | LANDED | 4e4e149f; vg-aa-land/vg-ab-land-2, 10-08 |
| A | A7 | scenes/tactical_c/hud/selection_panel.gd | LANDED | 82786192; vg-aa-land/vg-ab-land-2, 10-08 |
| A | A7b | scenes/tactical_c/hud/comb.gd | LANDED | 9e523197; vg-aa-land/vg-ab-land-2, 10-08 |
| A | A8 | scenes/tactical_c/hud/events_feed.gd | LANDED | d45b0386; vg-aa-land/vg-ab-land-2, 10-08 |
| A | A9 | scenes/tactical_c/fx/shots.gd | LANDED | e0a3e453; vg-aa-land/vg-ab-land-2, 10-08 |
| A | A10 | scenes/tactical_c/fx/deaths.gd | LANDED | 2992cda2; vg-aa-land/vg-ab-land-2, 10-08 |
| A | A11 | scenes/tactical_c/camera.gd | LANDED | 274a86ee; vg-aa-land/vg-ab-land-2, 10-08 |
| A | A13a | scenes/tactical_c/structures_layer.gd | LANDED | e3b9ecb7; vg-aa-land/vg-ab-land-2, 10-08 |
| A | A13b | scenes/tactical_c/hud/reinforcements.gd | LANDED | 6cfbc1ae; vg-aa-land/vg-ab-land-2, 10-08 |
| A | A14 | scenes/tactical_c/fx/abilities.gd | LANDED | 5df74a32; vg-aa-land/vg-ab-land-2, 10-08 |
| A | A15a | scenes/tactical_c/fx/ambient.gd | LANDED | efa44f05; vg-aa-land/vg-ab-land-2, 10-08 |
| A | A15b | scenes/tactical_c/loading_overlay.gd | LANDED | 4ce248f5; vg-aa-land/vg-ab-land-2, 10-08 |
| A | A12 | scenes/tactical_c/tactical_view.gd (+ qa_state inventory) | LANDED | 196cc477 last edit; nodes by name map at :45-56; 4d4babf8 landing 14 |
| B | B0 | pre-check / base (push/vg-b0) | LANDED | vg-b0 cc3f880c merged; landed with B1-B4 (vg-b-land) |
| B | B1 | scenes/galaxy/territory_field.gd + shaders/field_bake.gdshader | LANDED | 49f70767 10-08 |
| B | B2 | scenes/galaxy/shaders/shell_field.gdshader | LANDED | 2c1565f5 |
| B | B3a | scenes/galaxy/shell_renderer.gd | LANDED | f86d05f1 |
| B | B3b | scenes/galaxy/shell_labels.gd | LANDED | 4a5ea563 |
| B | B4 | scenes/galaxy/galaxy_view.gd (child node) | LANDED | 2e90e1cb / 39c2741a edits |
| B | B5 | territory_field.gd perf edit (REFILL 12 ms) | LANDED | vg-b5-3 c3e31061; REFILL park file test_vg_b_b5_park_refill.gd stays off main (push/vg-b5-2) |
| B | B6 | scenes/galaxy/galaxy_flash.gd | LANDED | fc04252d |
| B | B7 | scenes/galaxy/territory_tween.gd | LANDED | cb2c18ca / c5a410cd |
| B | B8 | pull-back / push-in after F router (S-108) | NOT STARTED | no branch; no matching symbol in scenes/galaxy; S-108 play reads "no" |
| B | B9 | time-jump renderer (galaxy_view_driven.gd) | LANDED | fc246921 |
| C | C2 | scenes/ground3d/ground_mesh.gd | LANDED | 8113403f; vg-ca-land-2/vg-cb-land-3 5026db37, bcad1954 |
| C | C2b | scenes/ground3d/ground_bands.gd | LANDED | 467ebe50; vg-ca-land-2/vg-cb-land-3 5026db37, bcad1954 |
| C | C3 | scenes/ground3d/camera_rig_3d.gd | LANDED | 169a1a04; vg-ca-land-2/vg-cb-land-3 5026db37, bcad1954 |
| C | C4 | scenes/ground3d/projection.gd | LANDED | 20fe9ce5; vg-ca-land-2/vg-cb-land-3 5026db37, bcad1954 |
| C | C5 | scenes/ground3d/ground3d.gd + tactical_view.gd host | LANDED | 42c4f09b; tactical_view.gd:293 Ground3DHost; vg-ca-land-2/vg-cb-land-3 5026db37, bcad1954 |
| C | C6 | scenes/ground3d/ground_units.gd (planned units_3d.gd) | LANDED | 3371a7cd; wired 8e6ca39a; vg-ca-land-2/vg-cb-land-3 5026db37, bcad1954 |
| C | C7 | scenes/ground3d/slope_view.gd (planned slopes_view.gd) | LANDED | ded3a329; wired 8e6ca39a; vg-ca-land-2/vg-cb-land-3 5026db37, bcad1954 |
| C | C8 | scenes/ground3d/ground_lod.gd | LANDED | 189995ea; vg-ca-land-2/vg-cb-land-3 5026db37, bcad1954 |
| C | C9 | look + plays (tests/qa/desktop/plays/C) | LANDED | 6 plays on main; look-metric park file test_vg_c9_park_look.py only on push/vg-parked |
| C | C10a | scenes/tactical_c/fog_layer.gd (A to C handoff) | LANDED | b84ed834 merged; 5026db37 |
| C | C10b | scenes/tactical_c/map_layer.gd (A to C handoff) | LANDED | vg-c10b merged; 5026db37 |
| C | C10c | scenes/tactical_c/objective_markers.gd (A to C handoff) | LANDED | vg-c10c merged; 5026db37 |
| C | C10d | scenes/tactical_c/fx/shots.gd (A to C handoff) | LANDED | vg-c10d merged; 5026db37 |
| C | C10e | scenes/tactical_c/fx/deaths.gd (A to C handoff) | LANDED | vg-c10e-2 merged; 5026db37 |
| C | C10f | scenes/tactical_c/layer_view.gd (A to C handoff) | LANDED | vg-c10f merged; 5026db37 |
| D | D1 | csrc/space_noise.c | LANDED | c7fad34b; landing 4 1fdeb1c0 10-09 |
| D | D2 | csrc/space_plates.c | LANDED | 21adbe6b |
| D | D3 | csrc/space_raster.c | LANDED | b75ce9cc |
| D | D4 | csrc/space_field.c (mask writer) | LANDED | e3a86895 / 6276bb15 |
| D | D4t | statistical tests (tests/csim/test_VG_D_d4.py) | LANDED | on main |
| D | D5 | csrc/mission.c hook (after E1i) | LANDED | 58e828c9, de46ed6c; 1fdeb1c0 |
| D | D7a | scenes/space_field/space_layer.gd | NOT STARTED | scenes/space_field/ absent; only tests on push/vg-d7-tests 0674f49d (unmerged) |
| D | D7b | scenes/space_field/vision_tube.gd | NOT STARTED | absent; same tests-only branch |
| D | D hook | view hook for D (after E1p) | NOT STARTED | no tactical_view.gd reference to a space layer |
| E1 | E1a (K-e) | contract: lots/density/strongpoint getters, save 8 | LANDED | ec4436da 10-09 (ABI 6, save 8) |
| E1 | E1b | csrc/economy_density.c | LANDED | b3ac8a1c; 8f76be4d |
| E1 | E1c | csrc/economy_lots.c | LANDED | 8f13d263; 8f76be4d |
| E1 | E1d | csrc/economy_waves.c | LANDED | b630378b; 8f76be4d |
| E1 | E1e | csrc/economy_place.c | LANDED | ae086faa; 8f76be4d |
| E1 | E1f | pack_validate.py + assets/eras/*/manifest.json (buildings) | LANDED | 19723e17, vg-e1f-land-2 |
| E1 | E1g | manifest doctrines + pack_validate.py (narrowed; economy_doctrine.c untouched) | LANDED | 1004dedf; 8f76be4d |
| E1 | E1h | csrc/strongpoint.c | LANDED | 2cac06a7; 8f76be4d |
| E1 | E1i | mission.c/unit.c/tactical_support.c wiring (with K-e2) | LANDED | 1c265472; 8f76be4d |
| E1 | E1j | save pins + K-e ledger row | LANDED | pins at 9 (TD-VG-E-1, E-8) landed with K-e/K-e3 |
| E1 | E1k | scenes/settlement/settlement_layer.gd | NOT STARTED | scenes/settlement/ absent; tests only push/vg-e1k-tests 4b326922 |
| E1 | E1l | strongpoint_layer.gd | NOT STARTED | absent; tests only push/vg-e1l-tests f85b5caa |
| E1 | E1m | scenes/economy/ticker_beats.gd | HELD | Q-235-01 (Westley approves the four beats) |
| E1 | E1n | scenes/economy/map_markers.gd | HELD | Q-235-01 |
| E1 | E1o | scenes/economy/placement_ui.gd | NOT STARTED | absent; tests only push/vg-e1o-tests 0e933571 |
| E1 | E1p | view wiring in tactical_view.gd | NOT STARTED | no settlement ref in tactical_view.gd; tests only push/vg-e1p-tests b388b5a6 |
| E1 | E1 unmapped | 6 per-file pieces in spec section 8 (22) without a section-1 id | UNMAPPED | not assignable |
| F | W8a | scripts/build_pipe_{linux,windows,macos}.sh, codesign_macos.sh | LANDED | 3d5f520f 10-07; a90e510e |
| F | W8d | export_presets.cfg (Windows preset) | LANDED | a90e510e |
| F | depot | scripts/steam_app_build_5402100.vdf | LANDED | 3d5f520f |
| F | W2 | autoload/net/pipe_sim.gd | LANDED | b963d3d2 10-08 |
| F | W4 | scenes/lobby/lobby.gd + menu row + route | LANDED | 32fe3cca 10-08 |
| F | F5 | tactical_view.gd match mode | LANDED | acfe11ed; 1398ba16 10-09 (NetMatch refs x9) |
| F | loopback | tests/qa/desktop/net_match_loopback.py | LANDED | c4bf023e 10-08 |
| F | Spacewar test | real-Steam Spacewar match | HELD | Westley's step (spec section 9); no artifact |

### Totals (per-file base, spec section 8)

| lane | n | landed | built-not-landed | held | not started | unmapped | landed % |
|---|---|---|---|---|---|---|---|
| GUARD | 8 | 5 | 0 | 0 | 3 | 0 | 62% |
| K0 | 9 | 9 | 0 | 0 | 0 | 0 | 100% |
| K-a | 9 | 9 | 0 | 0 | 0 | 0 | 100% |
| K-f | 2 | 2 | 0 | 0 | 0 | 0 | 100% |
| K-h | 2 | 2 | 0 | 0 | 0 | 0 | 100% |
| K-d | 3 | 3 | 0 | 0 | 0 | 0 | 100% |
| A | 20 | 20 | 0 | 0 | 0 | 0 | 100% |
| B | 11 | 10 | 0 | 0 | 1 | 0 | 91% |
| C | 15 | 15 | 0 | 0 | 0 | 0 | 100% |
| D | 9 | 6 | 0 | 0 | 3 | 0 | 67% |
| E1 | 22 | 10 | 0 | 2 | 4 | 6 | 45% |
| F | 8 | 7 | 0 | 1 | 0 | 0 | 88% |
| **all** | **118** | **98** | **0** | **3** | **11** | **6** | **83.1%** |

On the 118 base: landed 98 (83.1%), built-not-landed 0 (0.0%), held 3 (2.5%), not started 11 (9.3%), unmapped 6 (5.1%). On the 112 mapped pieces: landed 87.5%, held 2.7%, not started 9.8%. No planned piece sits on an unmerged `push/vg-*` branch as finished code. The only unmerged build branches are tests-only (`vg-e1k/e1l/e1o/e1p-tests`, `vg-d7-tests`, `vg-k-e4-tests`), park files (`vg-parked`, `vg-b5-2`), review tables, superseded landing attempts, and one harness tweak.

Planned-but-parked inside landed pieces: B5 REFILL (12 ms) and C9 look-metric park files are off main by design; the dead-slot cost test is parked from K-a (Westley bound 3.0).

### Unplanned pieces landed: 37 (not in spec section 1)

- Lane A (5): A17 7f5b3701 (2D body scale cap), A18 2172681c (LoadingOverlay, Shots.in_flight), A19 3c34dfc7, A20 85e593a3, A21 5f395465. The wave script also lists A11b `camera_rack.gd` and A16 `ping.gd`: neither file exists on main (not started, also absent from spec section 1).
- Lane B (11): B10 8be56ae2 (quality), B11 7bdaf833 (ambient), B12 d4e88da2 (auto camera), B13 (unknown label), B14 74769942 (wiring), B15 4c25f108, B17 1baa0f53, B18 de29a725, B19 a7e54fe7, B20 e3df70b5, B21 87df8f5a. There is no B16.
- Lane C (4): C11 d7f5a8e4, C6b bcad1954, K-c6 78185a63, VG-C-wire 8e6ca39a.
- Lane D (6): K-d2 5dcf60bf, D5-2 58e828c9, D5-3 de46ed6c, D6 d1008da9, D7-pipe da1564f6 (not the spec's D7 client), D8 a2f54dd8. All reached main in landing 4, 1fdeb1c0.
- Lane E (2): K-e2 1c265472, K-e3 90f47374 (both landed in 8f76be4d).
- Lane F glue (4): F5b 0760de0d, F6a c7daf1eb, F6b 4209bdcc, qa-fog-net 48ae8a1c.
- Harness (4): HARNESS-gdreach and HARNESS-laneplays (fc986411), HARNESS-playsplit 7bb1f5a2, G-project f37a926f.
- Pipe/bridge split (1): vg-pipe-split 8bca92bf, landed by vg-split-land-2.

Counted separately, not as pieces: 53 ledger rows (62 distinct ids) of TD-VG test-defect fixes; the A plays chain TD-VG-A-9 to 9j; small fix branches (`vg-h-renderer`, `vg-g-daemon-text`, `vg-gate-mainpipe`, `vg-c7-2`, `vg-a-reconcile`, the E1 lint branches). Unplanned and unlanded: `vg-gate-playthrough-budget` (2-file gate tweak, 0d0f0345) and K-e4 (tests and docs only, `vg-k-e4-tests` e3277324 and `vg-e1b-docs` a099c783, both pushed at 09:14 to 09:16 on the pause day).

## 2. Git facts (origin/main, 2026-10-07 00:00 to 2026-10-10 10:00 -0400)

- Base: 0304d821 (2026-10-06 23:41). Head 1a8bbe19 (2026-10-10 09:12). The spec rev 1 commit (3bbbc5f8, 2026-10-06 22:32) falls before the window.
- Commits: 678 total; 286 merges, 392 non-merge; 155 first-parent commits. 377 non-merge commits by author `x`, 15 by Westopoli. 42 first-parent merge commits carry a subject naming a `push/vg-*-land` branch.
- Per day (total / merge / non-merge): 10-07 113 / 32 / 81; 10-08 370 / 189 / 181; 10-09 124 / 30 / 94; 10-10 (to 09:12) 71 / 35 / 36.
- `git diff --shortstat 0304d821..origin/main`: 424 files, +57,187 / -1,792. By directory: csrc 27 files +3,974/-790; scenes 71 files +6,318/-127; autoload 11 files +708/-180; tests 194 files +20,825/-262; docs 95 files +24,445/-387; scripts 20 files +842/-40; assets 3 files +17/-0; root files (Makefile, export_presets.cfg, CLAUDE.md) 3 files +58/-6.
- Remote branches `origin/push/vg-*`: 316; 290 merged into main, 26 not. 64 are landing branches (`-land`): 60 merged, 4 not (`vg-b-land-3`, `vg-c-wire-land-2`, `vg-e1a2-land`, `vg-f5-land-2`).
- Ledger (`docs/northstar/plans/push_ledger_2026-09-22.md`): 53 TD-VG rows by first id, 62 distinct ids. Rows by lane letter: E 12, B 11, A 10, K 8, D 7, C 3, GUARD 1, F 1. Distinct ids: A 16, E 12, B 11, D 10, K 8, C 3, GUARD 1, F 1.
- Workflow dir `docs/northstar/plans/workflows_2026-10-07/`: 34 JS scripts (29 wave, 5 resume), 1,246 JS lines (1,354 lines with `rules.md` and two journals). Per lane: B 13 (12 wave2b* plus 1 resume), F/D 7, E1 4, C 3, A 2, contract/wave 1/split 5.
- Drift checks (4 files in `drift_checks/`, all "Sonnet drift auditor, report unedited, Architect response"):

| file | at | blocking | top findings |
|---|---|---|---|
| 2026-10-09.md | 1398ba16 | yes | status lines and ROADMAP stale vs landings; two pending branches local-only; C6 and C7 landed unwired; epic rulings missing |
| 2026-10-09-b.md | 4d4babf8 | no | lane A, C and guard status stale again; three duplicated ledger rows; S-132 known-red reason stale; docs lack daemon verbs and gate stages |
| 2026-10-09-c.md | 14ca665c | no | stage table says K-e not started (K-e, K-c6, C6b and D landing 4 had landed); lane B landing 12 missing from journal; pieces.toml in-flight rows and `pieces.py --check` fail (34) |
| 2026-10-10.md | 8f76be4d | no | E1 part a landed but unrecorded; pieces flips and 31 owner overlaps without depends_on (check fails 35); bible R-218-01/05/06 lag the code (plus architecture.md stale lines, walk-route cost finding) |

## 3. Landing attempts (highest `-land-n` per lane, proxy for gate rejects)

| lane | highest n | landing branches (merged / total) |
|---|---|---|
| A | 14 (`vg-a-land-14`) | 13 total (all merged) |
| B | 12 (`vg-b-land-12`) | 10 total (9 merged; `vg-b-land-3` not) |
| C | 4 (`vg-c-wire-land-4`); ca 2, cb 3, c6b 1 | 9 total (8 merged; `vg-c-wire-land-2` not) |
| D | 4 (`vg-d-land-4`) | 4 (all merged) |
| E1 | 4 (`vg-e1a3-land-4`; e1a 1, e1a2 1, e1f 2, ke 1) | 6 total (5 merged; `vg-e1a2-land` gate REJECT, not) |
| F | 6 (`vg-f5-land-6`; `vg-f-land-3`) | 9 total (8 merged; `vg-f5-land-2` not) |
| K and contracts | 2 (`vg-ka2-land-2`, `vg-split-land-2`); k0, ka, kc6, kd, ke, kf, kh 1 | 10 total (all merged) |
| guard and harness | 1 | 3 total (all merged) |

Numbers skip (B has 1, 3, 6, 8, 10, 11, 12), so the highest n overstates attempts that left a branch. Worktrees under `~/Projects/om-push/wt/`: 370 directories, 97 with `.wt-done`; 262 are `vg-*` (all 97 markers are on vg worktrees); 108 are non-vg.

## 4. Stories (`docs/bible/stories.md`, 240 rows)

By status: Seen 0; Spec'd 135 (of which 13 say blocked); Design decided or direction, not scheduled 71; Ready 15; Tested 13; Deferred 4; Open 2. The word Seen occurs only in the header line.

Named as acceptance in spec section 1 "Seen-reachable": A 19, B 2, C 6, E1 4, F 6 = 37 distinct (D names none in the spec text; the programme names the S-166 group and S-007). Of the 37: 30 are Spec'd and 7 are Design decided; 0 are Seen. Story play scripts on main: A 12, B 3, C 6, E 3, F 5, K 4 = 33. Review tables on main: `story_reviews/B.md` only (3 rows; reviewer verdicts no/no/unclear per the programme; Westley verdict pending). A and C reviews sit on unmerged `vg-a-reviews`, `vg-c-reviews-2`; B run 5 on `vg-b-reviews-5`.

## 5. Plan vs reality

| item | plan | reality |
|---|---|---|
| per-file pieces | 118 | 98 landed, 0 built-not-landed, 3 held, 11 not started, 6 unmapped; plus 37 unplanned pieces landed (135 landed in all; the unplanned are 38% of the planned-landed count) |
| tokens | expected 117M, ceiling 150M | (blank, measured by another agent) |
| critical path | about 18 h of agent time on 8 slots, no date promised | first agent commit 10-07 15:11 (`vg-b0`), last 10-10 09:16: 66.1 h wall clock (63.3 h from 10-07 18:00; 82.7 h from spec rev 1). Main had commits in 59 distinct clock hours of that span |
| lanes share no files | "lanes share no files except through sequencing" | 22 VG rows in pieces.toml; 16 of them own a file another row owns. 12 rows were added after launch (K-c6, VG-CONTRACT-E2, E3, VG-D6, VG-D-pipefix, VG-D8, VG-C-wire, VG-C6b, G-project, HARNESS-gdreach, -laneplays, -playsplit) plus the pipe/bridge split. 9 of the 12 carry 25 shared owned-file entries (K-c6 5, K-e2 5, K-e3 7, D6 1, D-pipefix 2, D8 2, C-wire 1, C6b 1, G-project 1); the 3 HARNESS rows declare queued edits to `merge_gate.sh` and `merge_gate_support.py`; the split rewrote `om_pipe.c` and `c_bridge.gd` and widened `reach_lint.py`. Owner-overlap count with no depends_on ordering: 30 (journal 10-09 23:50), 31 (drift d) |
| lane E1 part a | one workflow | 4 scripts (laneE1, resume-laneE1a, E1a2, E1a3), 4 landing attempts (`vg-e1a3-land-4`), 12 ledger rows E-1 to E-12, two added contract pieces (K-e2, K-e3) |
| stories Seen | the programme ends when every lane's stories are Seen | 0 of 240 Seen; 37 named as Seen-reachable; 33 plays exist |

# The visible game programme: workflow spec (rev 7, after the lane E pre-flight 2026-10-09; D8 spawn placement (Westley 2026-10-09))

Programme plan: `2026-10-07-visible-game-programme.md`. Rev 1 from the ten pre-flight scouts (`preflight_2026-10-07/`); rev 2 folded audit round 1 (Opus 15 issues; parallelism cuts); rev 3 folds audit round 2 (Opus, 16 issues, "approve with the listed changes"; the three cited tests and the reach-lint exemption re-checked on main). Audit reports: `audits_2026-10-07/`. Rev 3 went to round 3 (Opus, 10 must-change items, all text; verdict "approve with the listed changes"); rev 4 applies them and is the launch text, pending Westley's go line. Rev 5 adds the attach point rule to section 1 (from the 2026-10-09 drift check). Rev 6: lane E pre-flight 2026-10-09 (R-168-05 for the era building set; K-e bumps ABI and save versions with the three pin tests; place is a player command; E1j is the pins and ledger row; S-235 held; pipe split noted; 22 pieces).

## 0. What changed in rev 3 and why

| Round-2 finding (verified) | Change |
|---|---|
| K-a's hidden-unit filter breaks `test_tactical_delta_reconstruction.gd` (needs two factions in the first frame, :107; averages enemy positions, :141-151), four transport tests that read enemy positions from the first frame, and K-a's own identity test; structures were still unfiltered | The filter leaves K-a. It becomes amendment K-h behind a `mission_start` flag `fog_filter` (default off; the game client sets it when A4 lands); units leaving sight go into `units_removed`, distinct from a `kill` event; structures filtered the same way (R-205-02); rulebook rows for the five tests; S-089 and S-205 blocked until K-h |
| Rulebook row 22 is on the do-not-touch list yet K-a re-pins it; the tier source is routed | Row 22 leaves the list for `state` only (RP by K-a quoting K0's table); `tier` stays 0 and K-a does not fill it |
| K0 stubs trip the reach lint: a tested new symbol nothing in the game reaches is a finding unless its name matches `_get_`, `_count`, `_is_`, `_has_` (`reach_lint.py:131`) | The K0 names follow the pattern (the eight in 0b: `om_tactical_event_count`, `om_tactical_event_get_at`, `om_structure_count`, `om_structure_get_at`, `om_objective_get_done`, `om_map_obstacle_count`, `om_map_get_obstacle_at`, `om_terrain_get_heights`; sight and layer target through the existing `om_fog_get_drawn_sensor_circle_radius` and `om_unit_get_target_layer`) and K0's stub test checks presence with `hasattr` only. `signatures.toml` is `docs/northstar/spec_factory/signatures.toml` |
| The VG-VIEW chain contradicted lane F's text and landed C5/E1p before their data | Chain: A12 → F5 → C5 (after C2–C4 land) → E1p (after K-e) → the D hook (when D lands) |
| Owner gaps: C1 duplicates K-a's heights decode; A14 duplicates the `activate_ability` wrapper; C10 edits VG-A's files; K-e edits VG-CONTRACT's files; E1h edits `unit.c`/`mission.c` while K-a holds them; `tests/qa/desktop/plays/` unowned | C1 and A14's bridge clause deleted; C10 is a handoff of the five A files to VG-C for the re-projection (listed); K-e is a row `VG-CONTRACT-E1` owned by E1's clerk; E1h starts after K-a lands; plays live in `tests/qa/desktop/plays/<lane>/` owned by the lane |
| T0 started B1–B5 beside B0 (their base unknown), E1's tests before K-e's shapes, K-a's `terrain.c` on an unanswered cap | T0 starts B0 only for lane B; K-e is E1's first piece and E1's tests follow it; the cell cap defaults to 240 (today's generator limit), 280 is a later amendment |
| The park rule had no gate mechanism: a parked red test rejects the candidate, and B2–B9 build on B1's parked test | A parked test file is held off the candidate (not skipped, not xfailed) and listed in the landing report; the code it covers lands; when Westley sets the number the file lands with his row |
| The kill rule could end the run with nothing visible landed; the `look` stage was unspecified | A stopped piece parks itself and its dependents only; a contract double-reject stops only its dependents; B and the F scripts land right after GUARD; `look` is regression-mode (frames compared to main's at the same play moment; a candidate may not be blanker than main) and its threshold is routed |
| Budget components summed to 90 pieces, 103 per-file pieces; A's first workflow over the cap | Section 8 re-derived: 103 per-file pieces, expected about 104M, ceiling 140M, per workflow 14M |
| K0's field table lacked `state` values, "in flight", cadences, `structures_changed/removed`, the overflow counter, structure next type and period, `profiles.ability/aoe`; inventory keys and nodes missing for seven pieces | Section 2 completed |
| Cover class decided in two places | The sim applies section 7's thresholds; the client reads `class` |
| Seen lists claimed S-090/S-094 (zones have no data), S-093 (a balance claim), S-235 (E2 beats), S-193's parked parts | Moved to blocked; A4's tests cover S-005 and S-091/S-092 only |
| The go line waived only the DoR; CLAUDE.md also says an epic with an open flag is not built (E-16, E-18, E-12, E-22 have open flags) | The go line names both (section 9) |
| A3's narrowing-by-layer hotkey shares Q-232-01's question | A3 ships the strip, rings, dimming, Tab focus; narrowing and `set_layer` wait together |
| Stale text: `1007b`, rev-1 counts in the programme, rulebook row 7, the E2 liberties still listed | Fixed in the programme, the rulebook and section 7 |
| Builder guesses: hidden shooter/victim events, event accumulation over n>1, "objective threshold", E1m feeding A8, whether `state` may be omitted | Answered in section 2 |

## 0b. Rev 4 changes (round 3)

| Finding | Change |
|---|---|
| K0 proposed new getters that already exist (`om_unit_get_target_layer` :1917, `om_fog_get_drawn_sensor_circle_radius` :1530, `om_structure_get_hud_data` :1953, `om_unit_is_braced` :1908, `om_unit_transition_progress` :1916, `om_unit_ability_cooldown` :2029, `om_unit_in_backswing` :2047, `om_tick_read_ability_events` :2027) and declared no reader for fire/kill/capture events; `stage` undefined | K0 reuses those names; new symbols only: `om_tactical_event_count`, `om_tactical_event_get_at` (fire and kill produced in `unit.c`, capture in `tactical_support.c`; ability events read through the existing reader by the pipe only, once per call), `om_structure_count`, `om_structure_get_at` (`stage` 0 until E1), `om_objective_get_done`, `om_map_obstacle_count`, `om_map_get_obstacle_at`, `om_terrain_get_heights`; `acd` = now + `om_unit_ability_cooldown`, `acd_max` from the profile |
| Row 22's re-pin breaks its own control (`:97` rejects `state=1`; detector `!= 0` at `:57`) | Row 22 spells out the edit: `state` present and `state & ~7 == 0`; the control plants `state=8` and a missing `state`; this control change is permitted by the row |
| K-a's identity test cannot pass once `state` is non-zero and new keys move units into deltas | The test compares reconstructed full views with `state` zeroed and the new keys stripped, on a fixture with no deaths (the dead-slot scan untouched) |
| K-a and K-f both edit `om_pipe.c`/`c_bridge.gd` in parallel; K-h and K-e unordered | K-f starts after K-a's pipe and bridge pieces pass their check; K-h lands before K-e starts |
| G1's `look` needs a threshold routed to Westley | `look` ships warn-only (frames attached, metric reported) until the number lands; then it rejects |
| `fog_filter` set in the shared bridge would turn it on for tests (`_ensure_mission` :498-501; row 33 and `test_flow_spine.py:444-447`) | The flag is a bridge parameter, default off, set only by `tactical_view.gd`'s live call; rulebook row 38 for the flow spine (stands with the flag off) |
| The park rule had no mechanism | Every Westley-threshold check lives in its own `*_park_*` test file; the clerk leaves such files off the candidate, keeps them on `push/vg-parked`, lists them; the footprint fence only warns on owned files missing from a diff |
| The landing order in §1 read as a literal chain | Written as dependency edges (below) |
| "Lane dropped" undefined; a parked VG-VIEW link would park the chain | A lane is dropped when its clerk has no landable candidate after two check failures of non-parked pieces; contract double-rejects park dependents, they do not drop lanes; a parked VG-VIEW link hands `tactical_view.gd` to the next link |
| Stale programme text; `push/tv-read` unaddressed; E1h/E1i naming; save 8 twice; C10 file list; `state` bits as values; VG-CONTRACT must own whole files | Fixed below and in the programme; `push/tv-read` is source only (its test is adopted by A1/A5's writers or dropped); the wiring piece is E1i everywhere; save 8 lives in K-e only; C10 names its files; VG-CONTRACT owns the seven `.c` files whole for K-a's duration |
| Budget recount: about 117 per-file pieces (A 20, K0 9, C10 5–6, E1 22) | Section 8: expected about 115M, ceiling 140M; lanes C and E1 in two workflows each |

**K-a rulings, 2026-10-07 night (Architect, after the wave 2 reports):** (1) capture events are written from `om_sup_capture_accrue` after the owner change through a new internal symbol `om_tac_event_push(w, kind, a, b)` in `csrc/om_internal.h` (internal, not the frozen contract); `unit.c`'s ring is the single writer. (2) `acd` is present only while a cooldown runs; nothing is synthesised (rulebook row 43). (3) `tier` is the unit row's tier, stored at spawn from the faction tech tier until the roster carries per-unit tiers (lane E item; rulebook row 39). (4) `events_dropped` is emitted by the pipe when the ring hit its cap (the sim keeps the count per world without a getter). (5) The `fog.c` and `tactical_move.c` K-a pieces were no-ops (the getters already existed); `set_layer` reaches `om_command_set_layer` through the pipe verb added by the pipe piece. (6) Rulebook rows 39 to 44 rule the eleven transport reds the pipe piece listed. Wave 2c (`vg-wave2c-pipe.js`) builds the support ring writer, the pipe (rebased on K-f), the bridge, and then the pipe/bridge split.

## 1. Lanes, pieces, stories

A piece is one file, about 100 lines: tests (Engineer, a different agent) → build (Doer) → check (Engineer; C pieces and contracts) or the lane clerk's gate (Godot and docs pieces). Every lane ends with its story plays run and queued.

**Sequencing (dependency edges; a script may start anything whose edges are satisfied).** T0 (stage 3 + phase A landed; stale `pending` rows flipped): test writers for A, C, F, GUARD; GUARD builds G1–G4, G6, G7 (G1 warn-only); B0; the F build scripts. Edges: GUARD lands → every other landing; B0 result + F scripts land together; K0 → every lane's builds (against fixtures) and K-a; K-a's pipe and bridge pieces checked → K-f; K-a lands → A's workflows, E1i; A lands → A12; A12 → F5 (after K-f); C2–C4 land → C5 (after F5's slot in the chain) → C6, C10; K-e lands (E1's first piece; after K-h) → E1's tests and pieces → E1p (after C5); D's answers → D1–D4 → D5 (after E1i) → the D hook (after E1p); A4 lands → K-h. Pairs of disjoint green lanes land in one gate. Lab run 1 at night.

### Contract gates

| Gate | Pieces (one file each unless noted) | What | Tests |
|---|---|---|---|
| K0 doc-first (about 9 files) | `docs/architecture.md` (the field table of section 2), `csrc/ouroboros_sim.h` + `signatures.toml` (new declarations: `om_tactical_event_count`, `om_tactical_event_get_at`, `om_structure_count`, `om_structure_get_at`, `om_objective_get_done`, `om_map_obstacle_count`, `om_map_get_obstacle_at`, `om_terrain_get_heights`; existing ones reused as listed in 0b), stub bodies returning 0/-1 in the six owning `.c` files, bindings; ABI 4 → 5 with the three pins (rulebook row 27) | the shapes every lane's tests use | `sig_check`, `sig_blocked`, a `hasattr` presence test for every new symbol (no calls), the ABI pins |
| K-a lane A data (7 sim files + pipe + bridge; each file one piece, one gate; VG-CONTRACT owns the seven `.c` files whole until K-a lands) | `unit.c` (fire and kill events into the event ring, cap 512 per call, `events_dropped`; `state` bits), `tactical_support.c` (`om_structure_count`, `om_structure_get_at` with `stage` 0; capture events), `mission.c` (`om_objective_get_done`), `fog.c` (sight through the existing `om_fog_get_drawn_sensor_circle_radius`), `tactical_move.c` (layer target through `om_unit_get_target_layer`, done tick from `om_unit_transition_progress`; `om_command_set_layer` from `command`), `tactical_mapgen.c` (obstacle getters, cover `class` by section 7's thresholds), `terrain.c` (`om_terrain_get_heights`; cap 240), `om_pipe.c` (the frame fields of section 2 read only through the public header; ability events via `om_tick_read_ability_events` once per call; the dead-slot scan fixed), `c_bridge.gd` (decoders; `set_layer` and `activate_ability` wrappers; heights into `terrain()`) | the data lane A draws | every getter against a fixture world; every field's shape; reconstructed full views equal main's with `state` zeroed and the new keys stripped, on a fixture with no deaths; the dead-slot fix measured on its own fixture |
| K-f net plumbing (after K-a's pipe and bridge pieces pass their check) | `om_pipe.c` (`net_step {frame:true}`; `_setmode`), `c_bridge.gd` (exe-relative pipe path, `OM_PIPE` override) | Steam phase B | a transport test per item; the Windows probe under wine |
| K-h fog filter (amendment, after A4, before K-e) | `om_pipe.c` (`mission_start {fog_filter:true}`: hidden units and structures not written; leaving sight → `units_removed`/`structures_removed`), `c_bridge.gd` (a parameter of `load_mission_live`, default off; only `tactical_view.gd`'s live call passes true) | R-089-03, R-205-02 | hidden units absent with the flag, present without; rulebook rows 33–38 stand with the flag off |
| K-d (with lane D) | `space_field_dump` verb, bridge decode | after Westley's answers | shape and size |
| K-e (`VG-CONTRACT-E1`, first piece of E1, after K-h) | lots, density, strongpoints getters and frame fields; `om_internal.h`/`checksum_full.c` hashed fields; save format 8 with the pin list (the only place the bump lives) | E1's frame | shapes; checksum section moves recorded |

### Lane A: battle screen (`VG-A`, 20 per-file pieces, two workflows: A1–A8 (11) then A9–A15 + A12 (9)). `push/tv-read` is source only: its `test_tactical_readability.gd` is adopted by A1/A5's test writers or dropped.

Seen-reachable: S-104, S-105, S-005, S-007 (today's disc; the plays run again when D's field lands), S-075, S-096, S-101, S-134, S-136, S-135, S-086, S-088, S-095, S-097–S-100, S-091, S-092. Blocked: S-009 (Q-009-02), S-132 (Q-132-02; shapes ship anyway), S-234 (Q-103-05), S-133 (tier source), S-089 and S-205 (K-h), S-090 and S-094 (zones: no data source), S-093 (balance), S-010 → lane C.

| # | Piece | What (rules quoted) | Tests |
|---|---|---|---|
| A1 | `unit_visuals.gd` (from tv-read) | six shapes, scale per type (manifest), faction colour, HP bar above and layer ring beneath (R-104-10), selection ring, facing | R-104-10 |
| A1b | `unit_squads.gd` | 3 to 5 models for marked types, offsets (R-132-03) | R-132-03 |
| A2 | `unit_motion.gd` | interpolation buffer, no snapping (S-101) | S-100/S-101 |
| A3 | `layer_view.gd` | rings, inactive dimming 0.4, the strip (R-104-09), Tab focus (R-105-03); rise/drop from `tl`/`ld`; narrowing (R-105-06) and the `set_layer` binding wait on Q-232-01 | S-002's visible half |
| A4 | `fog_layer.gd` | sight discs from `sight`, outside dimmed, nothing remembered (R-089-04) | S-005, S-091, S-092 |
| A5 | `map_layer.gd` | cover by class, obstacles, boundary | S-007 |
| A5b | `objective_markers.gd` | beacons, done/failed, hold/clear rings | S-075 |
| A6 | `hud/objectives_panel.gd` | primary large, secondaries small, bars, status | S-075, S-104 |
| A7 | `hud/selection_panel.gd` | type × count, HP from `profiles`, the ability ring; groups 1–0 (R-104-07), Ctrl+digit exclusive, recall, double-press centres (R-105-02), double-click same type | S-105 |
| A7b | `hud/comb.gd` | the Comb (R-105-07) | R-105-07 |
| A8 | `hud/events_feed.gd` | the four beats (R-104-01): structure captured/lost from `structures_changed` owner change, objective threshold (progress crossing 25/50/75/100), force routed when a sim source exists; banner 4 s; clock; listens to a `TickerBeats` signal for E1m | S-104 |
| A9 | `fx/shots.gd` | per-type categories (R-134-05), volleys, LOD cull, impact bloom from hp drops; a fire event is drawn only when the shooter or the target is visible (from the visible end) | S-134 |
| A10 | `fx/deaths.gd` | bloom 0.5 s, emitters, drift, darken, fade at 30 s, cap 150 (R-136-01/03) | S-136 |
| A11 | `camera.gd` | pan, edge 60 px, zoom to the map band, initial framing | S-234's unblocked half |
| A13 | `structures_layer.gd` + `hud/reinforcements.gd` (two pieces) | structures in the world (owner ring, HP), the reinforcement list with next unit icon and timer bar (R-104-06) from `next_type`, `nst`, `period` | R-104-06 |
| A14 | `fx/abilities.gd` | rings, glows, pulses from ability events (S-135); the verb wrapper is K-a's | S-135, S-096, S-086 |
| A15 | `fx/ambient.gd` + loading overlay (two pieces) | haze, flyby; "DEPLOYING FORCES" | S-138's share |
| A12 | `tactical_view.gd` (VG-VIEW) + `qa_state` inventory | instantiates A1..A15, routes input; inventory per section 2 | element inventory; `look` |

### Lane B: galaxy (`VG-B`, 11 pieces; look approved 2026-10-07)

Seen-reachable: S-106, S-107. Blocked: S-108 (router; after F). B0 pre-check (the 2026-10-01 stack vs main, 1,360 behind: merge-tree, rebase or rebuild, the A56-suspended checks listed; FIELD-EQ measured on the 80-region fixture) lands first with the F scripts; then B1 field + bake shader (FIELD-EQ parked if over 2%), B2 shell shader, B3a renderer, B3b labels + stand-in (iGPU cost measured), B4 wiring as a child node, B5 REFILL (parks at 12 ms), B6 flashes from events, B7 tween, B8 pull-back/push-in after F's router, B9 time-jump renderer (handoff from G-timejump).

### Lane C: ground (`VG-C`, 10 pieces; `scenes/ground3d/**`)

Seen-reachable: S-236, S-001, S-004, S-207, S-010, S-132 walkers. C2 `ground_mesh.gd`, C2b `ground_bands.gd`, C3 `camera_rig_3d.gd`, C4 projection + pick: from K0 (fixture heights); C5 the SubViewport host (VG-VIEW, after C2–C4), `qa_state` `ground3d`, projected `units_px`/`objects_px`; C6 units in 3D (walker Y = ground; flyer Y = layer floor + 150 wu, shadow disc); C7 slopes and layers visible; C8 LOD + no-pop test; C10 re-projection, one piece per file: `fog_layer.gd`, `map_layer.gd`, `objective_markers.gd`, `fx/shots.gd`, `fx/deaths.gd`, `layer_view.gd` (handoff of those six files from VG-A to VG-C for C10; rulebook row 3's perspective-zoom question ruled before C starts: the 2D zoom test keeps its semantics on the map band, the 3D rig publishes `camera {x,y}` and `scale` as the map band's equivalents); C9 `look` + plays, then A's plays re-run. C runs as two workflows (C2–C4 + C5; C6–C10).

### Lane D: space landscape (`VG-D`, 9 pieces; HELD until Q-STAGE3-03, Q-166-02, R-188-05, S-246, the D8 band and the kit questions are answered)

As rev 2: `space_noise.c`, `space_plates.c`, `space_raster.c`, mask writer, mission wiring (after E1i), K-d, `scenes/space_field/space_layer.gd` (2D, focus layer, polygons), the statistical tests. Launches on the answers.

- **D8** spawn placement: each faction's spawn slots in the pocket carved at its own anchor (CLEAR_RADIUS_WU 600 pool, enlarged until it holds the army's slot count with no index wrap), the objective pocket separate, pockets connected by the reachability carve; retires the D5-3 single-pocket placement; tests `tests/csim/test_VG_D_d8.py`; owner VG-D8 (`csrc/space_field.c`, `csrc/mission.c` spawn lines).

### Lane E1: settlement and economy, buildable half (`VG-E1`, 22 pieces, two workflows; K-e first)

Seen-reachable: S-193 (density, stages, waves; the slowdown and cover parts parked), S-218, S-237 (look), S-168 (placement). Blocked: S-219 (Q-219-02), S-238 and S-167/S-169-S-182 (E2). **HELD: S-235** (E1m, E1n, the four beats): Q-235-01 is blocked; built only after Westley approves the beats. The pipe is split: frames are in `csrc/pipe/pipe_tactical.c`, dumps in `csrc/pipe/pipe_dumps.c`, dispatch lines in `om_pipe.c`; wherever this section names `om_pipe.c` for a frame, it means that split. The open-flag list in `preflight_2026-10-07/6-economy.md` is superseded by the register (batches 13 to 22 closed them).

K-e bumps `OM_ABI_VERSION` 5 to 6 and `OM_SAVE_FORMAT_VERSION` 7 to 8; the three save-pin tests (`tests/test_load_game_wrong_version.gd:14`, `tests/csim/test_E16_B5_save_version.py:13`, `tests/csim/test_E16_C2_save_version.py:14` with `PRE_BUMP_VERSION`) move with it under one ledger row.

Place verb: placing a building is a player command on the existing command path (kind "place", `unit_ids` empty, x, y, building type id), not the debug `place_structure` verb; K-e defines the command frame and the pipe handler, E1e consumes it.

Pieces. Part a: E1a K-e; E1b density field (`csrc/economy_density.c`); E1c lot stages (`economy_lots.c`); E1d waves + rubble/rebuild (10 s); E1e placement + footprint clearing (R-193-03, R-168-01); E1f building set per era pack (manifest + validator, R-168-05); E1g doctrine list as data (R-179-01, `economy_doctrine.c`); E1h strongpoints (`csrc/strongpoint.c`); E1i the one `mission.c`/`unit.c` wiring piece (after K-a lands; lane D's D5 follows it); E1j save pins and the K-e ledger row (the three pin tests above and the Godot `load_game.gd` pin). K-e stubs `economy_density.c`, `economy_lots.c`, `economy_doctrine.c` and `strongpoint.c`. Part b: E1k `scenes/settlement/settlement_layer.gd`; E1l `strongpoint_layer.gd`; E1o placement UI (yield preview is E2); E1p the view wiring (VG-VIEW, after K-e); tests per piece. HELD behind Q-235-01, in part b: E1m `scenes/economy/ticker_beats.gd` (emits the `TickerBeats` signal A8 listens to; no edit to `events_feed.gd`); E1n `map_markers.gd`. E2: rev 4 when the batches land.

### Lane F: Steam phase B and shipping (`VG-F` + `VG-F5`, 8 pieces)

Seen-reachable: S-139–S-143, S-241 (no E2 part), the tester guide. Blocked: S-144 (Q-144-03), S-159/S-242 (E2). T0: W8a, W8d, the depot script (land with B0). After K-f: W2 PipeSim, W4 lobby + menu, F5 the hookup right after A12, the loopback match, the Spacewar test.

**Attach point rule (rev 5, from the 2026-10-09 drift check):** every client piece names the live scene node that adds it and the qa_state key that proves it, and ships an integration test that reads that key from the running scene, not from a fresh instance. A piece without an attach point is a stub and is listed as one.

## 2. Interfaces fixed (K0's `architecture.md` table; every test is written against this)

**Unit object** (per tick, full and delta): `{id,faction,type,tier,x,y,hp,layer,facing,target,state,acd?,tl?,ld?,sight?}`. `tier` int, 0 until a source exists. `state` int, always present (never omitted): value 1 fired during this call's steps (any of the n), 2 braced (guard/hold, `om_unit_is_braced`), 4 in layer transit (`tl` set); OR-ed; 0 otherwise. `acd` int: the tick the ability is ready (omitted when ready and never used). `tl` int layer target, `ld` int done tick: present only during a transit. `sight` int wu: own faction only. Deltas carry a unit when any of these changed.

**`structures`** (full frame; deltas `structures_changed` with the changed fields and `structures_removed` ids): `{id,type,owner,x,y,hp,stage,cap,nst,next_type,period}`; `cap` 0..1000 capture progress; `nst` the next spawn tick; `period` ticks between spawns.

**`events`** (per tick, never diffed; accumulated over `n>1` with their tick; cap 512 per call; `events_dropped` int when the cap is hit): `[kind,a,b,tick]`, kinds `0 fire(a shooter, b target)`, `1 ability(a unit, b ability id)`, `2 kill(a unit, b killer or -1)`, `3 capture(a structure, b new owner)`. With `fog_filter` on, an event is sent when `a` or `b` is visible to the local faction.

**`profiles`** (once per full frame): `[{type,max_hp,range,interval,sensor,ability,acd_max,aoe}]`.

**`objectives`** (per tick): `[{i,progress,done}]`, `done` 0 open, 1 complete, 2 failed.

**`map`** (full frames only, as today): `cover[{x,y,r,h,class}]` class 0 small (<150 wu) 1 medium (<400) 2 huge; `obstacles[{x,y,r}]`.

**Dumps** (once per mission): `terrain_dump` gains `heights` (hex LE int32 cm, `cells_w*cells_h`); `space_field_dump` (K-d), `lots_dump` (K-e) shapes written in their amendments.

**Verbs**: `command` gains `set_layer {units, layer}`; `activate_ability` as today; `mission_start` gains `fog_filter` (K-h).

**`qa_state` inventory keys**: `fog_layer`, `objective_markers`, `cover_cells`, `obstacles`, `structures`, `shots_in_flight`, `wrecks`, `squads`, `abilities_fx`, `ambient`, `loading_overlay`, `hud.{clock,objectives,selection,events,strip,comb,reinforcements}`, `units_px`, `objects_px`, `ground3d`, `shell_renderer`, `settlement_lots`, `strongpoints`, `map_markers`.

**Node names**: `UnitVisuals`, `UnitSquads`, `MapLayer`, `ObjectiveMarkers`, `FogLayer`, `LayerView`, `StructuresLayer`, `Hud/{Objectives,Selection,Comb,Events,Reinforcements,Strip,Clock}`, `Fx/{Shots,Deaths,Abilities,Ambient}`, `LoadingOverlay`, `Ground3D`, `ShellRenderer`, `SettlementLayer`, `StrongpointLayer`, `MapMarkers`, `TickerBeats`, `SpaceLayer`.

Story plays `tests/qa/desktop/plays/<lane>/<story>.py`; the review queue and ledger rows as rev 1.

## 3. The rulebook

`2026-10-07-visible-game-rulebook.md` rev 2: row 22 off the do-not-touch list for `state` (RP by K-a quoting this table), `tier` stays; rows 33–37 added for K-h (`test_tactical_delta_reconstruction.gd` first-frame two-faction control and enemy averaging; `test_pipe_assign_commander.py:85-87`; `test_pipe_tactical_tier_state_reserved.py:64-65`; `test_pipe_macro_group_orders.py:59-60`; `test_pipe_tactical_delta_frame.py:21`): with `fog_filter` off (the default in tests) they stand; K-h's own tests set the flag.

## 4. Self-healing

As rev 2, plus: every Westley-threshold check is written in its own `*_park_*` test file; when it is red the clerk leaves that file off the candidate, keeps it on `push/vg-parked`, and lists it in the landing report (the footprint fence only warns on owned files missing from a diff); the code it covers lands. A stopped piece parks itself and its dependents; a parked VG-VIEW link hands `tactical_view.gd` to the next link. A contract double-reject parks its dependents. A lane is dropped only when its clerk has no landable candidate after two check failures of non-parked pieces. `look` is regression-mode and warn-only until its threshold lands.

## 5. Guard pieces (`VG-GUARD`, separate test writer)

As rev 2; G1's `look` compares against main's frames at the same play moment (planted-blank control); warn-only (metric reported, frames attached) until Westley's threshold lands.

## 6. Owner rows

As rev 2 with: VG-CONTRACT owns `unit.c`, `tactical_support.c`, `mission.c`, `fog.c`, `tactical_move.c`, `tactical_mapgen.c`, `terrain.c` whole while K-a is in flight (then they return to B10/B9/PP-fog/B12/PP-mapgen/TERRAIN-1 or the lane rows); `VG-CONTRACT-E1` (K-e; E1's clerk); C10's six-file handoff A → C; E1i after K-a; plays per lane; the VG-VIEW chain A12 → F5 → C5 → E1p → D hook with the hand-on rule.

## 7. Liberties (tuning only)

Q-193-02 thresholds (0.10/0.22/0.38/0.58 onto five stages; Westley approves with the product); Q-235-01 the four beats; Q-237-01 closed as superseded; rubble rebuild 10 s; cover class 150/400 wu (applied in the sim); flyer altitude layer floor + 150 wu with a shadow disc; ground colour band ramp + steep tint + walkable; objective threshold beats at 25/50/75/100%; event cap 512 per call. Routed, not liberties: R-188-05, S-246, Q-219-02, Q-173-01/02, Q-167-03, Q-232-01 (the layer keys and narrowing), the tier source, D8's band, FIELD-EQ/REFILL/pixel/`look` thresholds, the 280 cell cap, Q-180-01. E2's tuning numbers are listed when E2 is spec'd.

## 8. Budget and kill rule

Per-file pieces: GUARD 8, K0 9, K-a 9, K-f 2, K-h 2, A 20, B 11, C 15, D 9 (held), E1 22, F 8, K-d 3 ≈ 118. At 0.707M each: 83M; retries 21M; 14 clerks 7M; audits 5M; reviewer passes 1M: expected about 117M; ceiling 150M. Per piece: expected 0.7M, p90 1.2M, hard stop 2.4M. Per workflow 14M (A, C, E1 in two each). Per agent: stop past 120k context. Kill: the ceiling, or two lanes dropped (section 4's definition; parked thresholds, parked pieces and contract double-rejects do not count). Gates 12 by day, 25 by night; lab at 4 workers by day, run 1 at night.

## 9. What Westley does

The go line this spec needs: "The visible game programme builds Spec'd stories; the Definition of Ready and the open-flag rule are waived for the visual layer (E-16, E-18, E-12, E-22's open flags listed); blocked stories stay listed and are not claimed Seen." Then: the routed questions via the parallel chat; the story queue; the Mac build and codesign; the Spacewar match; the Steam dashboard.

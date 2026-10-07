# The visible game programme: workflow spec (rev 3, after audit round 2)

Programme plan: `2026-10-07-visible-game-programme.md`. Rev 1 from the ten pre-flight scouts (`preflight_2026-10-07/`); rev 2 folded audit round 1 (Opus 15 issues; parallelism cuts); rev 3 folds audit round 2 (Opus, 16 issues, "approve with the listed changes"; the three cited tests and the reach-lint exemption re-checked on main). Audit reports: `audits_2026-10-07/`. Rev 3 goes to round 3 (the last).

## 0. What changed in rev 3 and why

| Round-2 finding (verified) | Change |
|---|---|
| K-a's hidden-unit filter breaks `test_tactical_delta_reconstruction.gd` (needs two factions in the first frame, :107; averages enemy positions, :141-151), four transport tests that read enemy positions from the first frame, and K-a's own identity test; structures were still unfiltered | The filter leaves K-a. It becomes amendment K-h behind a `mission_start` flag `fog_filter` (default off; the game client sets it when A4 lands); units leaving sight go into `units_removed`, distinct from a `kill` event; structures filtered the same way (R-205-02); rulebook rows for the five tests; S-089 and S-205 blocked until K-h |
| Rulebook row 22 is on the do-not-touch list yet K-a re-pins it; the tier source is routed | Row 22 leaves the list for `state` only (RP by K-a quoting K0's table); `tier` stays 0 and K-a does not fill it |
| K0 stubs trip the reach lint: a tested new symbol nothing in the game reaches is a finding unless its name matches `_get_`, `_count`, `_is_`, `_has_` (`reach_lint.py:131`) | The K0 names follow the pattern (`om_structure_get_at`, `om_objective_get_done`, `om_fog_get_sight_radius`, `om_unit_get_layer_target`, `om_unit_get_layer_done_tick`, `om_map_get_obstacle_at`, `om_terrain_get_heights`) and K0's stub test checks presence with `hasattr` only |
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

## 1. Lanes, pieces, stories

A piece is one file, about 100 lines: tests (Engineer, a different agent) → build (Doer) → check (Engineer; C pieces and contracts) or the lane clerk's gate (Godot and docs pieces). Every lane ends with its story plays run and queued.

**Sequencing.** T0 (stage 3 + phase A landed; stale `pending` rows flipped): the test writers for A, C, F and GUARD; GUARD builds (G1–G4, G6, G7); B0 (lane B's pre-check only); the F build scripts (W8a, W8d, the depot script). K0 (about 3 h) unlocks every lane's builds against fixture dicts; K-a and K-f run beside them. Landing order: GUARD alone → B0's result and the F scripts (a shared gate) → K0 → K-a, K-f → A (two workflows) → VG-VIEW: A12 → F5 → C5 → E1p → D hook → C's 3D (C2–C4, C7–C8 build from K0; C5/C6/C10 after A) → E1 (K-e first, then its sim and client pieces; E1h after K-a) → D when its answers land. Pairs of disjoint green lanes land in one gate. Lab run 1 pinned to a night slot.

### Contract gates

| Gate | Pieces (one file each unless noted) | What | Tests |
|---|---|---|---|
| K0 doc-first | `docs/architecture.md` (the field table of section 2), `csrc/ouroboros_sim.h` + `signatures.toml` (declarations; stub bodies in the owning `.c` files that return 0/-1), bindings; ABI 4 → 5 with the three pins (rulebook row 27) | the shapes every lane's tests use | `sig_check`, `sig_blocked`, a `hasattr` presence test for every new symbol (no calls), the ABI pins |
| K-a lane A data (7 sim files + pipe + bridge; each file one piece, one gate) | `unit.c` (fire-event ring, cap 512 per call, `events_dropped` counter; `state` bits), `tactical_support.c` (`om_structure_count`, `om_structure_get_at`), `mission.c` (`om_objective_get_done`), `fog.c` (`om_fog_get_sight_radius`), `tactical_move.c` (`om_unit_get_layer_target`, `om_unit_get_layer_done_tick`; `om_command_set_layer` from `command`), `tactical_mapgen.c` (`om_map_obstacle_count`, `om_map_get_obstacle_at`, cover `class` by section 7's thresholds), `terrain.c` (`om_terrain_get_heights`; cap 240), `om_pipe.c` (the frame fields of section 2; `terrain_dump.heights`; the dead-slot scan fixed), `c_bridge.gd` (decoders; `set_layer` and `activate_ability` wrappers; heights into `terrain()`) | the data lane A draws | every getter against a fixture world; every field's shape; frames identical to main's after stripping the named new keys (`state` is always present and 0 on main's frames: the reserved test's control holds); the dead-slot fix measured |
| K-f net plumbing | `om_pipe.c` (`net_step {frame:true}`; `_setmode`), `c_bridge.gd` (exe-relative pipe path, `OM_PIPE` override) | Steam phase B | a transport test per item; the Windows probe under wine |
| K-h fog filter (amendment, after A4) | `om_pipe.c` (`mission_start {fog_filter:true}`: hidden units and structures not written; leaving sight → `units_removed`/`structures_removed`), `c_bridge.gd` (sets the flag) | R-089-03, R-205-02 | hidden units absent with the flag, present without; the five rulebook rows added (33–37) |
| K-d (with lane D) | `space_field_dump` verb, bridge decode | after Westley's answers | shape and size |
| K-e (`VG-CONTRACT-E1`, first piece of E1) | lots, density, strongpoints getters and frame fields; `om_internal.h`/`checksum_full.c` hashed fields; save format 8 with the pin list | E1's frame | shapes; checksum section moves recorded |

### Lane A: battle screen (`VG-A`, 18 pieces, two workflows: A1–A8 (11 pieces) then A9–A15 + A12)

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

Seen-reachable: S-236, S-001, S-004, S-207, S-010, S-132 walkers. C2 `ground_mesh.gd`, C2b `ground_bands.gd`, C3 `camera_rig_3d.gd`, C4 projection + pick: from K0 (fixture heights); C5 the SubViewport host (VG-VIEW, after C2–C4), `qa_state` `ground3d`, projected `units_px`/`objects_px`; C6 units in 3D (walker Y = ground; flyer Y = layer floor + 150 wu, shadow disc); C7 slopes and layers visible; C8 LOD + no-pop test; C10 re-projection of A's fog, map, markers, shots, deaths, rings (handoff of those five files from VG-A to VG-C for this piece); C9 `look` + plays, then A's plays re-run.

### Lane D: space landscape (`VG-D`, 9 pieces; HELD until Q-STAGE3-03, Q-166-02, R-188-05, S-246, the D8 band and the kit questions are answered)

As rev 2: `space_noise.c`, `space_plates.c`, `space_raster.c`, mask writer, mission wiring (after E1h), K-d, `scenes/space_field/space_layer.gd` (2D, focus layer, polygons), the statistical tests. Launches on the answers.

### Lane E1: settlement and economy, buildable half (`VG-E1`, 20 pieces, two workflows; K-e first)

Seen-reachable: S-193 (density, stages, waves; the slowdown and cover parts parked), S-218, S-237 (look), S-168 (placement). Blocked: S-219 (Q-219-02), S-235 (E2 beats), S-238 and S-167/S-169–S-182 (E2). E1a K-e; E1b density field (`csrc/economy_density.c`); E1c lot stages; E1d waves + rubble/rebuild (10 s); E1e placement + footprint clearing (R-193-03, R-168-01); E1f building set per era pack (manifest + validator, R-168-04); E1g doctrine list as data (R-179-01); E1h strongpoints (`csrc/strongpoint.c`); E1i the one `mission.c`/`unit.c` wiring piece (after K-a lands); E1j save format 8; E1k `scenes/settlement/settlement_layer.gd`; E1l `strongpoint_layer.gd`; E1m `scenes/economy/ticker_beats.gd` (emits the `TickerBeats` signal A8 listens to; no edit to `events_feed.gd`); E1n `map_markers.gd`; E1o placement UI (yield preview is E2); E1p the view wiring (VG-VIEW, after K-e); tests per piece. E2: rev 4 when the batches land.

### Lane F: Steam phase B and shipping (`VG-F` + `VG-F5`, 8 pieces)

Seen-reachable: S-139–S-143, S-241 (no E2 part), the tester guide. Blocked: S-144 (Q-144-03), S-159/S-242 (E2). T0: W8a, W8d, the depot script (land with B0). After K-f: W2 PipeSim, W4 lobby + menu, F5 the hookup right after A12, the loopback match, the Spacewar test.

## 2. Interfaces fixed (K0's `architecture.md` table; every test is written against this)

**Unit object** (per tick, full and delta): `{id,faction,type,tier,x,y,hp,layer,facing,target,state,acd?,tl?,ld?,sight?}`. `tier` int, 0 until a source exists. `state` int, always present: bit 1 fired this tick, bit 2 braced (guard/hold), bit 4 in layer transit (`tl` set); 0 otherwise. `acd` int: the tick the ability is ready (omitted when ready and never used). `tl` int layer target, `ld` int done tick: present only during a transit. `sight` int wu: own faction only. Deltas carry a unit when any of these changed.

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

As rev 2, plus: a parked test file (a Westley threshold) is held off the candidate and listed, the code lands; a stopped piece parks itself and its dependents only; a contract double-reject stops its dependents only; `look` is regression-mode.

## 5. Guard pieces (`VG-GUARD`, separate test writer)

As rev 2; G1's `look` compares against main's frames at the same play moment (planted-blank control), threshold routed.

## 6. Owner rows

As rev 2 with: `VG-CONTRACT-E1` (K-e; E1's clerk); C10's five-file handoff A → C; E1h after K-a; plays per lane; the VG-VIEW chain A12 → F5 → C5 → E1p → D hook.

## 7. Liberties (tuning only)

Q-193-02 thresholds (0.10/0.22/0.38/0.58 onto five stages; Westley approves with the product); Q-235-01 the four beats; Q-237-01 closed as superseded; rubble rebuild 10 s; cover class 150/400 wu (applied in the sim); flyer altitude layer floor + 150 wu with a shadow disc; ground colour band ramp + steep tint + walkable; objective threshold beats at 25/50/75/100%; event cap 512 per call. Routed, not liberties: R-188-05, S-246, Q-219-02, Q-173-01/02, Q-167-03, Q-232-01 (the layer keys and narrowing), the tier source, D8's band, FIELD-EQ/REFILL/pixel/`look` thresholds, the 280 cell cap, Q-180-01. E2's tuning numbers are listed when E2 is spec'd.

## 8. Budget and kill rule

Per-file pieces: GUARD 8, K0 3, K-a 9, K-f 2, K-h 2, A 18, B 11, C 10, D 9 (held), E1 20, F 8 = 100 (+3 for K-d/K-e amendments) ≈ 103. At 0.707M each: 73M; retries 18M; 12 clerks 6M; audits 5M; reviewer passes 1M: expected about 103M; ceiling 140M. Per piece: expected 0.7M, p90 1.2M, hard stop 2.4M. Per workflow 14M (A and E1 in two each; A's first has 11 pieces ≈ 7.8M expected). Per agent: stop past 120k context. Kill: the ceiling, or two lanes dropped by failures (parked thresholds and parked pieces do not count). Gates 12 by day, 25 by night; lab at 4 workers by day, run 1 at night.

## 9. What Westley does

The go line this spec needs: "The visible game programme builds Spec'd stories; the Definition of Ready and the open-flag rule are waived for the visual layer (E-16, E-18, E-12, E-22's open flags listed); blocked stories stay listed and are not claimed Seen." Then: the routed questions via the parallel chat; the story queue; the Mac build and codesign; the Spacewar match; the Steam dashboard.

# The visible game programme: workflow spec (rev 2, after audit round 1)

Programme plan: `2026-10-07-visible-game-programme.md`. Rev 1 was written from the ten pre-flight scouts (`preflight_2026-10-07/`). Rev 2 folds audit round 1: the Opus 5.5 audit (15 issues, verdict "approve with the listed changes"; every bible citation re-checked against the epics on main 2026-10-07) and the Sonnet parallelism audit (critical path 37 h → about 18 h). Rev 2 goes to audit round 2.

## 0. What changed and why (rev 2)

| Audit finding (verified) | Change |
|---|---|
| The contract wave declared getters over state that lanes D and E create later, so its tests could not pass; its bodies had no owner (`om_tac_fire` is static in `unit.c:1924`; objective done lives in `mission.c`; obstacles in `tactical_mapgen.c`); 20 getters + 15 frame changes in one gate is all-or-nothing | The wave becomes three gates over state that exists today, plus one amendment per later lane (section 2): K0 doc-first (field table, header, stubs), K-a (lane A fields + heights + the pipe), K-f (net frame flag, `_setmode`, exe path, dead-slot fix); K-d lands with lane D's sim, K-e with lane E1's. K-a owns the named lines of `unit.c`, `mission.c`, `fog.c`, `tactical_move.c`, `tactical_mapgen.c`, `tactical_support.c`, `terrain.c` for the wave, after which they return to their lanes. The identity test is "identical after stripping the named new keys" |
| A4 drew remembered positions; R-089-04: "no memory of last-seen positions" | Removed |
| R-104-10 requires a thin HP bar above every unit and a layer ring beneath; R-104-01's ticker recognises exactly four beats (structure captured, structure lost, force routed, objective threshold) and nothing else at launch | A1 draws HP bars and the ring; A8 is the four beats; "force routed" has no sim source (scout 1 F5): a sim gap flagged, the beat ships when it exists |
| R-104-07 groups 1 through 0; R-105-02 double-press centres; R-105-03 Tab cycles layer focus; R-105-06 narrowing by layer hotkey; R-105-07 the Comb; R-136-01/03 death timings and the 150-wreck cap; R-134-05 per-type shot categories | Quoted into A7, A7b (the Comb), A9, A10. The layer keys (A3's `set_layer` binding) are undesigned (Q-232-01 open, Q-110-04 b): routed to Westley; A3 ships the strip, rings and dimming without the binding |
| Lane D builds on open flags (Q-STAGE3-03, Q-166-02; Westley: "needs more design work so we can't write stories for it"); R-188-05's rewrite changes a rule's meaning; D8's pass band is unset | Lane D is held: its pieces stay spec'd, nothing launches until the routed answers land; R-188-05 and S-246 are routed, not liberties; D8 waits for the band |
| Lane B's base stack (`push/A54-*`, `A55-names`) is 1,360 commits behind main with suspended checks; FIELD-EQ fails at 2.10% vs 2%; REFILL 35.6 vs 12 ms; the pixel tolerances are Westley's | B0 = pre-check: merge-tree against main, rebase or rebuild as fallbacks, suspended checks listed; FIELD-EQ measured on the 80-region fixture before B1; the three thresholds routed with a "park on a Westley threshold" rule (not a failed check) |
| Definition of Ready: every acceptance story is Spec'd or "not scheduled"; some cannot reach `Seen` (blocked Qs, tier 0, zones stubs, S-089's "not in the client's data" vs the pipe sending every unit, E2-dependent ones) | Each lane's list splits into Seen-reachable and blocked (section 1). One line for Westley's go (section 9): the DoR is waived for the visual layer, Spec'd stories are acted out. S-010 moves to lane C. S-089's R-089-03 "not in the client's data" is a contract gap: K-a filters hidden units out of the frame (the pipe already knows `visible`), which also closes the information leak |
| Owner collisions: `qa_daemon.gd` (GUARD vs A), `save.c` (K4 vs E), `checksum_full.c`/`om_internal.h` (E1 needs hashed fields), the `unit.c` fire hook (A vs E), `scene_router.gd` (B8 vs F), `time_jump_sequencer.gd` (B9 vs G-timejump), SettlementLayer wiring into the view, VG-D/F5 depending on all of E; no VG-GUARD row | Section 6: a VG-GUARD row; VG-E split into VG-E1 and VG-E2; a VG-VIEW row holding every `tactical_view.gd` edit (A12, C5, D hook, E1 wiring, F5) as a serial chain after A; explicit handoffs listed; D and F5 depend on E1 only |
| Budget: 78 pieces, not 50; "per lane 1.2M" was per piece; the 10M per-workflow cap is below lane A's expected | Section 8 re-derived for 82 pieces: expected about 83M, ceiling 110M; per piece 1.2M p90, 2.4M hard stop; A and E1 each split into two workflows; per workflow 12M |
| Liberties that change a rule's meaning: R-188-05, Q-219-02's mover (Westley: "to be designed"), Q-173-01/02 (Q-159-12 undecided), Q-167-03 (roster membership); unlisted ones | Routed; the table (section 7) now holds only tuning numbers and names the unlisted ones (10 s rebuild, flyer altitude and shadow, ground colour); E2 rows dropped until rev 3 |
| Stop causes with no rule: missing precondition, contract need in A..D, reach-lint on a test-only symbol, "tests green not red", "cause not found", ledger/pieces conflicts, a stop on a Westley threshold | Section 4 adds a rule for each; the flake rule is one: re-run that test id up to twice, real only on a full-stage re-run (the programme text is corrected) |
| Legacy rows dropped without reason: structures drawn in world and the reinforcement panel (R-104-06), `activate_ability` never sent (the bridge whitelists three verbs; S-096/S-086 cannot be acted out), ability visuals (S-135), squads (R-132-03), volleys and LOD, ambient and the loading overlay, zones with no data | Pieces A13 (structures + reinforcements), A14 (ability verb + visuals), A1b (squads), A9 includes volleys and LOD, A15 (ambient, loading overlay); zones: dropped with the reason that no data source exists (lane D/C fields later) |
| Lane C underscoped: A's screen-space layers (fog, map, shots, deaths, rings) need re-projection in 3D | C10 re-projection pieces; lane A's story plays re-run after C |
| Parallelism: all tests can start at T0; B and the F build scripts need no contract; C's mesh/camera/picking and D's C port are new files; the four `tactical_view.gd` edits serialise anyway; big pieces (K1, K2, A1, A3, A5, A7, A8, C5, D1–D3, E1b–e, E1g) must split; GUARD had no separate test writer; shared landing windows for disjoint green lanes; lab run 1 at night | Section 1 sequencing rewritten: T0 = every lane's tests + GUARD + B0..B5 + F scripts; K0 at about 3 h unlocks builds against fixtures; C2–C4/C7–C8 in `scenes/ground3d/**` need only K0; splits applied; the VG-VIEW chain; pairs land together; the lab's run 1 pinned to a night |
| Batch 13 (815357f5): free placement on terrain, placeholder adjacency yields, a small fixed building set per era pack, four doctrines set in the lobby and changeable, the two-of-three resource pattern; names/gathering/amounts still open; new Q-168-05 | E1 gains placement and footprint clearing (R-193-03, R-168-01), the building set as manifest data, the doctrine list as data; resources, workers and the economy screens stay E2 |
| Minor: heights are 460 KB (240²) / 627 KB (280²) as int32 hex; polygons about 400 KB; `push/land-1007a` not 1007b; the `look` stage needs a positive control; G5 waits on Agora relays; the 240 vs 280 cell cap | Corrected in place; G1 gains a planted-blank control; G5 sequenced last; K-a aligns `TG_MAX_CANVAS_WU` with `OM_TERRAIN_MAX_CELLS` (a number Westley confirms: 240 or 280) |

## 1. Lanes, pieces, stories

A piece is one file, about 100 lines: tests (Engineer, a different agent) → build (Doer) → check (Engineer; C pieces and contracts) or the lane clerk's gate (Godot and docs pieces). Every lane ends with its story plays run and queued.

**Sequencing (from the parallelism audit).** T0 (stage 3 + phase A landed, stale `pending` rows flipped): every lane's test writers, GUARD (G1–G4, G6, G7), B0–B5 and B7, the F build scripts (W8a, W8d, the depot script), start at once. K0 (about 3 h) unlocks every lane's builds against fixture dicts. K-a and K-f run beside the lane builds; lanes land after the contract they need. Order of landing: GUARD alone (it changes the gate) → K0 → K-a, K-f → A → the VG-VIEW chain (A12, C5, E1 wiring, F5) → C's 3D after A → E1 sim (K-e inside it) → D when its answers land (K-d inside it). Pairs of disjoint green lanes land in one gate (B with F scripts; E1-sim with D-sim). Lab run 1 pinned to a night slot.

### Contract gates

| Gate | Pieces | What | Tests |
|---|---|---|---|
| K0 doc-first | `docs/architecture.md` field table (names, types, enums, per-tick/periodic/once), `csrc/ouroboros_sim.h` + `signatures.toml` declarations with stub bodies that link, bindings; ABI 4 → 5 (rulebook row 27, the three pins together) | the frame shapes every lane's tests are written against | `sig_check`, `sig_blocked`, a stub-links test, the ABI pins |
| K-a lane A fields | `unit.c` (fire-event ring, cap 512 per step, dropped-on-overflow counter; `state` bits: fired, braced, in flight; hidden-unit filter in the frame: units outside the local faction's `visible` are not written, R-089-03), `tactical_support.c` (`om_structure_count/at`: id, type, owner, x, y, hp, stage, capture, `next_spawn_tick`), `mission.c` (`om_objective_done`), `fog.c` (`om_fog_sight_radius`), `tactical_move.c` (`om_unit_layer_target/done_tick`; `om_command_set_layer` reachable from `command`), `tactical_mapgen.c` (`om_map_obstacle_count/at`, cover `class`), `terrain.c` (`om_terrain_dump_heights`; the 240/280 cap aligned), `om_pipe.c` (units gain `tier`, `state`, `acd`, `tl`/`ld`, `sight`; `structures[]` full + `structures_changed/removed`; `events[]` per tick: `[kind, a, b, tick]` with kinds fire/ability/kill/capture; `profiles[6]` once per full frame; `objectives[].done`; `map` gains obstacles and cover class; `terrain_dump` gains `heights`; the dead-slot scan fixed), `c_bridge.gd` (decoders, `heights`, `set_layer`, `activate_ability`) | the data lane A draws | every getter against a fixture world; every frame field; identical frames after stripping the named new keys; the dead-slot fix measured; hidden units absent from the frame (plant: a visible one present) |
| K-f net plumbing | `om_pipe.c` (`net_step {frame:true}` answers `net_ack` then one `tactical` frame; `_setmode` under `_WIN32`), `c_bridge.gd` (exe-relative pipe path with `.exe`, `OM_PIPE` override) | Steam phase B's needs | a transport test per item; the Windows probe under wine |
| K-d (with lane D) | `space_field_dump` verb (masks per layer packed hex, plate polygons), bridge decode | after Westley's answers | shape and size tests |
| K-e (with lane E1) | lots, density, strongpoints, weather getters and frame fields; `om_internal.h`/`checksum_full.c` hashed fields; save format 8 with the pin list | E1's frame | shape tests; checksum section moves recorded |

### Lane A: battle screen (`VG-A`, 17 pieces, two workflows: A1–A8 then A9–A15 + A12)

Seen-reachable: S-104, S-105, S-005, S-007 (after lane D's field for cover; today's disc first), S-075, S-096, S-101, S-134, S-136, S-135, S-086, S-088, S-095, S-097–S-100, S-090–S-092, S-094 (zones drawn when data exists). Blocked: S-009 (Q-009-02), S-132 (Q-132-02; shapes ship anyway), S-234 (Q-103-05), S-133 (tier source), S-205 (Q-205-01), S-089 (after K-a's filter: reachable), S-010 → lane C.

| # | Piece | What (rule numbers builders quote) | Tests |
|---|---|---|---|
| A1 | `unit_visuals.gd` (from tv-read) | six shapes (one per type), visual scale per type from the manifest, faction colour, thin HP bar above and layer ring beneath (R-104-10), selection ring, facing | S-132, R-104-10 |
| A1b | `unit_squads.gd` | squads: 3 to 5 models for the types the manifest marks (R-132-03), offsets, facing offset | R-132-03 |
| A2 | `unit_motion.gd` | interpolation buffer (position, facing), no snapping | S-101, S-100 |
| A3 | `layer_view.gd` | layer rings, inactive dimming 0.4, the layer strip (R-104-09), Tab focus cycling (R-105-03), narrowing by layer hotkey (R-105-06); rise/drop from `tl`/`ld`; the `set_layer` key binding waits on Q-232-01 | S-009's unblocked half, S-002 |
| A4 | `fog_layer.gd` | sight discs from `sight`, outside dimmed; nothing remembered (R-089-04) | S-005, S-089–S-094 |
| A5 | `map_layer.gd` | cover by class, obstacles, map boundary | S-007 |
| A5b | `objective_markers.gd` | beacons primary/secondary, done/failed, hold/clear rings | S-075 |
| A6 | `hud/objectives_panel.gd` | primary large, secondaries small, bars, status | S-075, S-104 |
| A7 | `hud/selection_panel.gd` | type × count, HP from `profiles`, ability ring; groups 1 through 0 (R-104-07), Ctrl+digit bind exclusive, recall, double-press centres (R-105-02), double-click same type | S-105 |
| A7b | `hud/comb.gd` | the Comb: hold a group digit, the strip blooms per layer, drag selects layers (R-105-07) | R-105-07 |
| A8 | `hud/events_feed.gd` | the four beats (R-104-01) from `events[]` and structure owner changes; banner 4 s; clock; "force routed" when a sim source exists | S-104 |
| A9 | `fx/shots.gd` | per-type categories (R-134-05: Raider kinetic, Interceptor missile, ...), volleys, LOD cull, impact bloom | S-134 |
| A10 | `fx/deaths.gd` | bloom 0.5 s, emitters, drift, darken, fade at 30 s, cap 150 (R-136-01/03) | S-136 |
| A11 | `camera.gd` | pan, edge 60 px, zoom to the map band, initial framing | S-234's unblocked half |
| A13 | `structures_layer.gd` + `hud/reinforcements.gd` | structures in the world (owner ring, HP), the reinforcement list (R-104-06) | R-104-06 |
| A14 | `fx/abilities.gd` + bridge `activate_ability` | the verb sent; rings, glows, pulses from ability events | S-135, S-096, S-086 |
| A15 | `fx/ambient.gd`, loading overlay | haze, flyby, "DEPLOYING FORCES" | S-138's share |
| A12 | `tactical_view.gd` (VG-VIEW chain) + `qa_state` inventory | the shell instantiates A1..A15, routes input; inventory keys per section 2 | element inventory; the `look` stage |

### Lane B: galaxy (`VG-B`, 10 pieces; look approved 2026-10-07)

Seen-reachable: S-106, S-107. Blocked: S-108 (R-108-01/06 need the router change, sequenced with F). B0 pre-check (merge-tree of the 2026-10-01 stack vs main, 1,360 behind; rebase or rebuild; the A56-suspended checks reviewed; FIELD-EQ measured on the 80-region fixture); B1 field + bake shader; B2 shell shader; B3a renderer; B3b labels + Compatibility stand-in (iGPU cost measured here); B4 wiring as a child node (grid/influence retuned; tier→significance); B5 REFILL to 12 ms (parks on Westley's threshold if not met); B6 war flashes from events (R-106-04); B7 territory tween 2.0 s; B8 pull-back/push-in without the router fade (after F's `scene_router.gd`); B9 the time-jump renderer unified (handoff from G-timejump).

### Lane C: ground (`VG-C`, 11 pieces; new files under `scenes/ground3d/**`)

Seen-reachable: S-236 (R-236-01/02; R-236-03 land only), S-001, S-004, S-207, S-010 (R-010-03: vertical offset in 3D), S-132 walkers. C1 bridge heights decode; C2 `ground_mesh.gd`; C2b `ground_bands.gd` (colour by band/slope/walkable); C3 `camera_rig_3d.gd`; C4 projection + ray-march pick; C5 the view hosts the SubViewport (VG-VIEW chain), `qa_state` `ground3d`, `units_px`/`objects_px` projected; C6 units in 3D (walker Y = ground; flyer Y = layer floor + clearance with a ground shadow disc: a liberty, section 7); C7 slopes and layers visible (bands, midline, transition indicator); C8 LOD chunking + no-pop test; C10 re-projection of A's fog, map, objective markers, shots, deaths, rings; C9 `look` + story plays, then lane A's plays re-run.

### Lane D: space landscape (`VG-D`, 9 pieces; HELD until Q-STAGE3-03, Q-166-02, R-188-05, S-246, the D8 band and the kit questions are answered)

Spec'd as rev 1 wrote it, with D1–D3 split into `space_noise.c`, `space_plates.c`, `space_raster.c` and K-d inside the lane; `scenes/space_field/**` for the client. Launches on the answers.

### Lane E1: settlement and economy, buildable half (`VG-E1`, about 20 pieces, two workflows)

Seen-reachable: S-193, S-218, S-235, S-237 (look), S-168 (placement, batch 13). Blocked: S-219 (Q-219-02), S-238 (workers, E2), S-167/S-169–S-182 (E2). E1a density field (`csrc/economy_density.c`), E1b lot stages, E1c waves + rubble/rebuild, E1d placement and footprint clearing (R-193-03, R-168-01 free placement on terrain), E1e the building set per era pack as manifest data (R-168-04) + the validator, E1f doctrine list as data (R-179-01), E1g strongpoints (`csrc/strongpoint.c`, R-218-01..08), E1h one `mission.c`/`unit.c` wiring piece (an `economy_init/step` hook; later E pieces touch new files only), E1i K-e contract, E1j save format 8, E1k `scenes/settlement/settlement_layer.gd` (five stages, cliff dwellings, streets along contours), E1l strongpoint drawing (era-skinned), E1m `scenes/economy/ticker_beats.gd` feeding A8 (S-235's four beats), E1n map markers, E1o placement UI (R-230-02's preview is E2), E1p the view wiring (VG-VIEW chain), tests per piece. E2 (resources with names and amounts, workers gathering, production, doctrines in play, shipments, bases, occupation, tech, disguise, weather path, the economy screens): rev 3 when the batches land.

### Lane F: Steam phase B and shipping (`VG-F` + `VG-F5`, 8 pieces)

Seen-reachable: S-139–S-143, S-241 (no E2 part), the tester guide. Blocked: S-144 (Q-144-03), S-159/S-242 (E2). W8a/W8d/depot script at T0; W2 PipeSim after K-f; W4 lobby + menu; F5 the tactical hookup right after A12 on the VG-VIEW chain (not last); the loopback match; the Spacewar test.

## 2. Interfaces fixed

- The field table in K0's `architecture.md` revision (every lane's tests are written against it): unit `{id,faction,type,tier,x,y,hp,layer,facing,target,state,acd?,tl?,ld?,sight?}`; `structures[{id,type,owner,x,y,hp,stage,cap,nst}]`; `events[[kind,a,b,tick]]` kinds `0 fire(a shooter,b target) 1 ability(a unit,b id) 2 kill(a unit,b killer) 3 capture(a structure,b owner)`; `profiles[{type,max_hp,range,interval,sensor,ability,acd_max}]`; `objectives[{i,progress,done}]` done `0 open 1 complete 2 failed`; `map.cover[{x,y,r,h,class}]`, `map.obstacles[{x,y,r}]`; `terrain_dump.heights` hex LE int32 cm; absolute ticks everywhere; defaults omitted.
- `qa_state` inventory keys: `fog_layer`, `objective_markers`, `cover_cells`, `obstacles`, `structures`, `shots_in_flight`, `wrecks`, `hud.{clock,objectives,selection,events,strip}`, `units_px`, `objects_px`, `ground3d`, `shell_renderer`, `settlement_lots`.
- Node names: `UnitVisuals`, `UnitSquads`, `MapLayer`, `ObjectiveMarkers`, `FogLayer`, `LayerView`, `StructuresLayer`, `Hud/*`, `Fx/*`, `Ground3D`, `ShellRenderer`, `SettlementLayer`, `SpaceLayer`.
- Story plays, the review queue, ledger rows: as rev 1 (`tests/qa/desktop/plays/<story>.py`; `docs/northstar/story_reviews/<lane>.md`; `TD-VG-<lane>-<n>`).

## 3. The rulebook

`2026-10-07-visible-game-rulebook.md`, unchanged; row 22 (tier/state reserved) is re-pinned only by K-a quoting K0's table; rows 19, 20 and B's FIELD-EQ/REFILL are Westley thresholds (park rule).

## 4. Self-healing in the scripts

Rev 1's rules plus: **precondition** (a 5-call pre-check scout per lane before its tests: the files, symbols and fixtures the lane assumes exist; a miss changes the brief, not the run); **contract need** in A..D (each lane has a reserved amendment slot with its own gate; the builder stops, the Architect writes the amendment, the lane resumes); **reach-lint** (a piece whose new symbol is reachable only from tests adds the call site in the same piece or stops); **tests green, not red** (the test writer re-runs on the base and reports; a green test is a defect of the test); **cause not found** (the lane stops, listed); **ledger and `pieces.toml` conflicts** (the clerk merges main before every gate and keeps both appends); **park on a Westley threshold** (FIELD-EQ, REFILL, pixel tolerance, D8's band: the lane lands everything else, the parked check is listed, not a failed check); **flake**: re-run that test id up to twice, real only on a full-stage re-run.

## 5. Guard pieces (`VG-GUARD`, tests by a separate Engineer)

G1 gate `look` stage (histogram blank/near-uniform; a planted blank frame as the positive control), per-stage times, baseline cache by sha, the flake re-run; G2 driver additions; G3 `state()["inventory"]`; G4 queue format + `agile.md` `Seen` + `stories.md` header; G6 baseline capture before any lane lands; G7 CLAUDE.md guards and the drift-check rule; G8 nightly 30B play; G5 the Agora text pre-filter, last (needs `relay/05`, `relay/07`).

## 6. Owner rows

Rows: `VG-GUARD` (harness files), `VG-CONTRACT` (K0, K-a, K-f: `om_pipe.c`, header, `signatures.toml`, `architecture.md`, `c_bridge.gd`, `om_internal.h`, `checksum_full.c`, and the named lines of the seven `.c` files for the wave), `VG-A` (`scenes/tactical_c/**` except `tactical_view.gd`, `qa_daemon.gd` after GUARD), `VG-B`, `VG-C` (`scenes/ground3d/**`, `terrain.c`, `era_config.gd`), `VG-D` (`space_*.c`, `tactical_mapgen.c`, `scenes/space_field/**`), `VG-E1` (`csrc/economy*.c`, `strongpoint.c`, `mission.c`/`unit.c` wiring, `save.c`, `scenes/settlement/**`, `scenes/economy/**`), `VG-E2` (later), `VG-F` (`Makefile`, presets, `scene_router.gd`, `scenes/lobby/**`, `scenes/main_menu/**`, `autoload/net/**`, `scripts/build_pipe_*`), `VG-VIEW` (`tactical_view.gd`: A12 → C5 → E1p → F5 → the D hook). Handoffs: `qa_daemon.gd` GUARD → A; `scene_router.gd` F → B8; `time_jump_sequencer.gd` G-timejump → B9 (one row); `save.c` E1j only; `unit.c` fire hook K-a then E1h. D and F5 depend on E1, not E2. Stale `pending` rows flipped to `attached` by a clerk first; `NET-backend` "landed" → "attached"; the `T2g/NET-backend` overlap resolved.

## 7. Liberties (Architect, tuning only; design-level items routed)

| Q / item | Liberty |
|---|---|
| Q-193-02 thresholds, Q-191-05 item 5 | the mockup's 0.10/0.22/0.38/0.58 onto five stages (empty below 0.10); Westley approves with the product |
| Q-167-01/02, Q-170-01/02/03 | lab-set numbers (worker time, cost, load, yield falloff, timings) when E2 is spec'd |
| Q-174-02 | wall blocks, gate opens for its owner, tower fires |
| Q-179-02 | a short fixed habit list |
| Q-180-01 | the dial as three positions per axis (borderline; flagged to Westley, not blocking) |
| Q-235-01 | the four named beats |
| Q-237-01 | closed as superseded by Q-193-02 |
| rubble rebuild | 10 s (mockup value) |
| cover class | small < 150 wu, medium < 400, huge otherwise |
| flyer altitude in 3D | layer floor + 150 wu clearance, a ground shadow disc under the flyer |
| ground colour | band ramp, steep tint, walkable mask (no water, no zones: the sim has none) |

Routed to Westley (not liberties): R-188-05, S-246, Q-219-02, Q-173-01/02, Q-167-03, the `set_layer` keys (Q-232-01), the tier source (A30), D8's band, FIELD-EQ/REFILL/pixel tolerances, the 240/280 cell cap.

## 8. Budget and kill rule

82 pieces (GUARD 8, contracts 7, A 17, B 10, C 11, D 9 held, E1 20, F 8) at 0.707M input-equivalent each = 58M; retries at 0.176M × 82 = 14M; 11 clerks 5.5M; audits 5M; reviewer passes 1M: expected about 83M; ceiling 110M. Per piece: expected 0.7M, p90 1.2M, hard stop 2.4M. Per workflow 12M (A, E1 split in two each). Per agent: stop past 120k context. Kill: the ceiling, two lanes dropped (parked thresholds do not count), or a contract gate rejecting twice. Gates: 12 by day, 25 by night; lab at 4 workers by day, run 1 at night.

## 9. What Westley does

The go line this spec needs: "The visible game programme builds Spec'd stories; the Definition of Ready is waived for the visual layer; blocked stories stay listed." Then: the routed questions (the parallel chat: lane D's set, the tier source, the `set_layer` keys, the thresholds, the cell cap); the story queue as lanes land; the Mac build and codesign; the Spacewar match; the Steam dashboard.

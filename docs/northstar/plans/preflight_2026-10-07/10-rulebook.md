# Pre-flight scout 10-rulebook (2026-10-07, Sonnet, read-only)

Scout 10 rulebook, read-only. I found no test that pins the 24 px squares, a unit count or a colour. I also found no pinned "no fog / no cover / no objective marker" absence, no galaxy sphere or tube node names, and no frame-hash golden of a client frame. The real pins are `qa_state` readouts, exact key sets, version literals and one deleted-directory scan, listed below. The worktree is removed. Paths below are relative to the repo root.

## Part 1. Rulebook (tests the lanes change by design)

Rule codes for the ruling agent:
- **RP** = re-pin to the new literal, quoting the spec line that replaces the old one.
- **SUP** = key list grows, so assert superset (`<=`) instead of equality.
- **PRES** = assert presence instead of absence.
- **ARCH** = stop and list for the Architect, because the change is not a pure re-pin.

| # | Test id (file:line) | Literal it pins | Lane | Rule | Positive control stays? |
|---|---|---|---|---|---|
| 1 | `tests/test_tactical_view.gd:102,540` | `N_UNITS := 12` (line 52) against the frozen fixtures `tests/fixtures/tactical_frame_seed11*.json`; `qa_state.units.size()==12` | A | Do not edit the fixtures. Per-type shapes or tiers keep the unit list unchanged, so no ruling is needed. A new frame field gets a new fixture file (RP). | Yes (`:539`) |
| 2 | `tests/test_tactical_view.gd:309` | `st["scale"] == 1080.0/24000.0` ("canvas fitted to the screen height") | A (camera frames the force or map view) | If the spec changes the initial zoom, RP to `fit_scale * <initial_zoom quoted from the spec>`. If the spec changes the fit rule, ARCH (it also touches rows 3 and 4). | Yes (units inside 1920x1080 at `:311-314`) |
| 3 | `tests/qa/desktop/test_pan_speed_zoom.py:93` | `zoom2.scale == 2*zoom1.scale` and "zoom 1.0 is zoomed OUT, ZOOM_MIN" (docstring line 9) | A (zoom to map view); C (3D camera) | Lane A: keep the semantics, or RP to the spec's zoom bounds. Lane C: ARCH, because a perspective camera has no linear 2x scale. | Yes (`:91-97`) |
| 4 | `tests/test_tactical_camera.gd:104` | `consts.get("UNIT_SIZE", 24.0) * 0.5` is the half-extent margin in the in-viewport detector. `scenes/tactical_c/tactical_view.gd:16` has `UNIT_SIZE := 24.0`. | A | If per-type shapes keep a `UNIT_SIZE`-style constant, nothing changes. If the const is removed or renamed, RP the const name only. Widening the margin is ARCH, because Westley owns tolerances. | Yes (C1, C2, C3 at `:238-243` and the notes) |
| 5 | `tests/test_tactical_camera.gd:222-243` | "own units fully inside the viewport after the frame loads" (camera frames the force) | A, C | Keep. A HUD panel that covers screen area must come from a spec line naming the safe rect; then RP the rect. | Yes (C1) |
| 6 | `tests/test_tactical_view.gd:331-345`, `tests/qa/desktop/test_tactical_play.py:89,100` | `len(px) >= 100`; "a left-drag over the top edge selects every drawn unit" (`len(selected)==drawn`) | A (selection, minimap, camera framing) | If the spec moves the start camera, RP the drag rectangle to the new on-screen force rows. If selection rules change (R-105-0x), ARCH. | Yes (the `drawn > 0` guard) |
| 7 | `tests/test_tactical_view.gd:569-616` (R-089-04) | `units_px` holds only units in `visible["0"]`; `not px.has("2")`, `not px.has("10")` | A (fog) | Keep. Fog adds drawables; it must not add `units_px` ghosts. A spec line adding remembered-fog markers goes in a new key, not `units_px`. | Yes (fixture units 11 and 12 never listed) |
| 8 | `tests/test_tactical_hud.gd:133` (H1) | A visible Button whose text upper-cases to "END MISSION" | A (HUD) | RP the match text only if the spec renames the button, quoting the spec line. Moving or restyling it needs no change, since the test is text-based, not layout-based. | Yes (H1 is the control) |
| 9 | `tests/test_tactical_hud.gd:145,159` | `DebugOverlay.visible == false` by default; F3 toggles it | A | Keep (guard G4). A new HUD never turns the overlay on. | Yes (H2) |
| 10 | `tests/test_tactical_hud.gd:170-215` (A6b-3, A6b-4, A6b-5) | Text patterns: "letters ... N%" for the objective, `mm:ss` clock, count "3" as a standalone number for the selection | A | Keep. They are pattern-based. If the spec changes the objective wording, RP the regex to the spec's example string. | Yes (H3 control) |
| 11 | `tests/test_tactical_view.gd:419-424`; `tests/qa/desktop/test_flow_spine.py:320-325` | `qa_state` has `commands_sent_last_order`, `units_in_last_command`, `plants` containing `move-order-dropped`; `unit_count == len(units)` | A | SUP only. New keys such as `fog`, `cover`, `beacons`, `selection`, `control_groups` and `shots` are added alongside. Never remove or rename an existing key. | Yes (the PLANT run at `:448-457`) |
| 12 | `tests/test_qa_state_scenes.gd:220-222` | Every REQUIRED scene exposes `scene`, `tick`, `plants`; REQUIRED includes `res://scenes/tactical_c/tactical_view.tscn` and `res://scenes/galaxy/galaxy_view.tscn` (lines 62-110) | A, B, C | SUP. If a lane moves the scene file, RP the `path` (lines 91-110) and keep `scene_name`. The header comment "TOTAL .tscn: 47" is prose, not asserted (there are 49 files). A new scene needs no registration. | Yes (the type and numeric checks at `:226-247`) |
| 13 | `tests/qa/desktop/test_flow_spine.py:327-337` | The tactical screenshot differs from a median-grey background by at least 300 pixels | A, C | Keep. It is median-referenced, so a new terrain background is safe. A landscape that fills the screen with one colour is a real finding, not a test defect. | The test is itself a blank-frame detector |
| 14 | `tests/test_main_menu_items.gd:96-100` | `want := ["continue","era library","new campaign","quit","settings"]`, an exact five. `not _any_contains(texts,["tutorial"])`, `not ["access key"]`. | F (lobby and menu) | If the spec adds a Multiplayer entry, RP `want` to the six sorted labels quoted from the spec (RP, not SUP, because the visible entry set is the invariant). Keep the "tutorial" and "access key" absences. Any other new entry is ARCH. | Yes (control `:94`, the QUIT scan) |
| 15 | `tests/test_main_menu_continue.gd:13-18` | A control named `Continue` (the NewGame sibling naming) | F | Keep. A new `Multiplayer` item is added alongside. | Yes |
| 16 | `tests/test_galaxy_view.gd:131` | Live boot gives `system_count == 80` | B | Keep, since it is sim-derived. It changes only if the default region count changes (ARCH). | Yes (fixture-based sibling at `:152`) |
| 17 | `tests/test_galaxy_view.gd:157-193` | `owners`, `region_colours`, `systems_px` hold one entry per region; `edge_counts` totals the fixture edge count | B (bubble field) | Keep the `qa_state` contract: the bubble field must still publish `systems_px` (screen position of each bubble centre) and `region_colours` (the territory glow's base colour). If the spec renames a key, RP the key name for all three keys together. | Yes (`PLANTS` list at `:17`) |
| 18 | `tests/test_galaxy_view.gd:259-263` | `edges_3d == true`; plant `edges-2d-overlay` must flip it to false | B | Keep the key, and keep it true for the borders. If a border-ribbon spec replaces tubes, RP the key's meaning (the name stays) and keep the plant. | Yes (clean-true then planted-false) |
| 19 | `tests/qa/desktop/test_galaxy_pixels.py:131-197,231,273` | Pixel at each owned `systems_px` equals its `region_colours` within a tolerance. Thresholds: `MIN_PLANT_DIFF_PX`, `MIN_EDGES_2D_DIFF_PX`. | B | A glow that blends colour at the centre makes this red. That is ARCH, because it is a tolerance (Westley owns it). A builder may not change `MIN_*` or the tolerance. | Yes (owner-colour-flat plant) |
| 20 | `tests/qa/desktop/test_galaxy_conquest.py:90-126` | After steps, `region_colours[i]` for a flipped owner equals `owner_colours[str(owner)]` within `COLOUR_TOLERANCE` | B | Same as row 19 (tolerance), so ARCH if the bubble colour shifts. | Yes (conquest-no-recolour plant) |
| 21 | `tests/transport/test_pipe_tactical_delta_frame.py:41,171` | `set(units_changed[0]) == UNIT_KEYS` = `{id,faction,type,tier,x,y,hp,layer,facing,target,state}`. EXACT equality, the only exact unit-key pin. | A (+1 frame contract piece) | The key list grows, so SUP: RP the equality to `UNIT_KEYS <= set(...)` and add the new keys named in the contract piece's header diff. The spec line must name the key. | Yes (the mover control at `:162-170`) |
| 22 | `tests/transport/test_pipe_tactical_tier_state_reserved.py` (whole file; `_unit_violations`, `:100-110`) | `tier == 0` and `state == 0` on every unit, in full and delta frames (ruling A30) | A (tiers on screen) | ARCH, never a ruling-agent edit. Ruling A30 says filling `tier` or `state` "goes through a contract piece". If the contract piece exists and quotes the spec, RP the assertion to the new value domain and update the file docstring. | Yes (`test_positive_control_...`) |
| 23 | `tests/transport/test_pipe_tactical_delta_frame.py:270` | Each tactical-frame objective has exactly `{"i","progress"}`, and `test_objectives_ride_every_frame...` expects `[o["i"]...] == mission objectives` | A (beacons) | SUP: RP to `{"i","progress"} <= set(o)` if the contract adds beacon fields. | Yes (`:276-` live progress control) |
| 24 | `tests/transport/test_pipe_mission_frame_briefing_fields.py:37,77,84` | `OBJECTIVE_KEYS <= set(o)` (already SUP); `set(force) == {"types","tiers"}`; `set(b) == {"situation","objective","assets"}`; `"position_name" not in m` (ruling A4: frames carry no names) | A, E | Keep `OBJECTIVE_KEYS`. RP `force` and `briefing` to SUP only if the contract names new keys. The `position_name` absence is a ruling; it is not re-pinnable without Architect (ARCH). | Yes (`test_check_frame_rejects_todays_empty_frame`) |
| 25 | `tests/transport/test_pipe_tactical_world.py:131-142`, `test_pipe_shapes.py:171,178` | `len(map.cover) == om_map_cover_count`; the `tactical.schema.json` required keys are a subset; `"map" not in delta` and `"units" not in delta` | A (cover and obstacle drawing), C (height array), E (structures) | New `map` fields (height array, obstacles, structures) are SUP. The "map and units ride only full frames" fact stays; a height array rides full frames only (ARCH if the contract piece puts it in deltas). Update `docs/northstar/spec_factory/transport/tactical.schema.json` required only in the contract piece. | Yes (`:10-11` control) |
| 26 | `tests/test_tactical_delta_reconstruction.gd:89` | `view.map == truth.map` (equality of the whole map dict) and unit position, hp and presence equal the server's full frame | A, C, E | Not an edit. The client must keep every new `map` field from the last full frame and reconstruct new unit fields from deltas. A red here is a real bug in `c_bridge.gd`. This is on the do-not-touch list (Part 2). | Yes (control at `:114`) |
| 27 | `tests/transport/test_pipe_shapes.py:80`; `tests/csim/test_E02_S020_abi.py:22`; `tests/csim/conftest.py:64` | `frames[0]["abi"] == 4`; `om_abi_version() == 4`; `EXPECTED_ABI_VERSION = 4` | A, C, E, D, F (each "+1 contract") | RP all three to the new number together, only when the contract piece's spec quotes "ABI 4 -> N" and `csrc/ouroboros_sim.h`/`signatures.toml` already carry it. The three pins must move in the same ledger row. | Yes |
| 28 | `tests/test_load_game_wrong_version.gd:14` (`EXPECTED_VERSION := 6`, also asserts the file header word, the sidecar `format_version`, `CURRENT_SAVE_VERSION` and the "incompatible" label with the number); `tests/csim/test_E16_B5_save_version.py:13` (`=6`); `tests/csim/test_E16_C2_save_version.py:14` (`=6`, with `PRE_BUMP_VERSION = 4`) | The save version is 6 (`csrc/om_internal.h:36`) | E (structures, workers and lots in the save), C (height) | RP all three together when a contract piece bumps `OM_SAVE_FORMAT_VERSION` (the spec line must say so). The old-version refusal ("no migration") assertions stay. The `PRE_BUMP_VERSION` literals are not changed. | Yes (the refusal control) |
| 29 | `tests/specfactory/test_pack_validate.py:360-374` | `{"settled_reach":False,"greek_placeholder":False,"test_era":True}` for `test_only`; `era_spatial_scale`/`era_tone`/`era_order` are present | D (space kit pack), others | SUP. A new pack that is not `test_only` means RP the flags dict, with the spec naming the pack. A new required manifest key means SUP: add it to the key tuple at `:352`. | Yes (`test_a58_removing_a_key_...`) |
| 30 | `tests/qa/t1/test_rts_detectors.py:247` | `set(findings.keys()) == {"rubberband","stuck","backwards","dropped_order"}` | A (if the lane adds a QA detector) | SUP. A new detector gets its own positive-control test, so the ruling agent only widens the key set. | Yes |
| 31 | `tests/test_tactical_view.gd:670-700` (R-103-02 camera bounded), `tests/test_tactical_camera.gd:296-393` | The camera stays inside `0..canvas` at every zoom | A, C | Keep. A 3D camera for lane C must still publish `camera {x,y}` in world units. If the spec removes it, ARCH. | Yes |
| 32 | `tests/qa/desktop/test_tactical_play.py:230-246` | `best_dist >= 0.9 * slowest_wu_per_tick * steps` (sim speed vs the C library) | none (sim) | Lane E's sim systems must not slow units. A red here is a finding. | Yes |

The `test_world_view_data.gd` and `test_world_view_shell.gd` tests both `extends Node` and print instead of asserting. `test_world_view_visual.gd` is a scene, not a test. None of them pins galaxy node names or counts. I did not trace whether the gate runs them.

The nine `scenes/mockups/*/verify.gd` scripts (262, 225, 316, 225, 247, 201, 188, 294 and 600 lines) are self-contained. Their pins are:
- Mockup scene and fixture paths, e.g. `fog/verify.gd:3-5`.
- Contract key lists, e.g. `units/verify.gd:6` and `hud/verify.gd:7`.
- Plant ids, e.g. `fog/verify.gd:9`.
- Numeric bounds, e.g. `units/verify.gd:130,188,194,224`.

None references `scenes/tactical_c`, `galaxy`, `shared`, `main_menu` or `autoload`. `scripts/specfactory/merge_gate_support.py:755` already exempts `scenes/mockups/` from the playthrough trigger.

Rule: lanes copy or port from a mockup and never edit it. A `verify.gd` is never re-pinned by a ruling; a red `verify.gd` means the lane edited a mockup, which is refused (see Part 2). Ruling-agent action: none.

## Part 2. Never touched by any ruling (the agent refuses and lists for the Architect)

Self-consistency determinism, with no literal to re-pin:
- `tests/specfactory/test_checksum_trace.py`
- `tests/specfactory/test_tactical_trace.py` (same build twice, then `--compare`)
- `tests/csim/test_E02_S020_determinism.py`
- `tests/csim/test_E02_S020_rng_seeding.py` (`PCG_MULT`)
- `tests/csim/test_E02_S160_om_pow.py` (hex-float table, `:26-48`)
- `tests/csim/test_E02_S160_no_default_features.py`
- `tests/csim/test_E10_S072_a2_refresh_determinism.py`
- `tests/csim/test_E17_S186_noise_deterministic.py`
- `tests/csim/test_net_checksum.py`
- `tests/csim/test_net_section_hashes.py`
- `tests/csim/test_net_cmd_stream.py`
- `tests/csim/test_net_save_*.py`
- `tests/net/*.py`
- `tests/specfactory/test_libm_lint.py`
- `tests/specfactory/test_alg_constants.py`

Pinned goldens, where re-recording is an Architect-numbered ruling plus its own ledger row (never the ruling agent):
- `tests/csim/test_B3_C2_friction_golden.py:17-19` (`GOLDEN_FINAL_CHECKSUM = 5255701497181831602`, `GOLDEN_FRICTION_SHA256 = "315b11b5..."`, `GOLDEN_FRICTION_RECORDS = 4252`)
- `tests/csim/test_F1_fog_per_faction_observers.py:301`, `test_F2_nearest_hostile_search.py:426`, `test_F3_macro_contact_skip.py:245` (`GOLDEN` dicts)
- `tests/csim/test_PP_C_g3_hash_invariant.py` with `tests/csim/data/a99_tactical_hashes*.json` and `baseline_hashes_pre_g3.json`
- `tests/csim/test_PP_C_g3_rehash.py`
- `tests/csim/test_E01_T2_collision_mask.py:24` (`FLYER_CHECKSUM_50 = 17656050431320828508`)
- `tests/csim/test_E01_T2_walker_waypoint_arrival.py:43` and `test_E01_T2_walker_no_corner_cut.py:27` (`FLYER_CHECKSUM_200`)

Lab goldens:
- `tests/skilllab/golden_hashes.json` (`mirror`, `numbers`, `planted`)
- `tests/skilllab/integration/test_cross_machine.py`
- `tests/skilllab/integration/test_trace_real.py`
- `tests/skilllab/integration/test_mopup_real.py:20` (`OFF_DIGEST`)
- `tests/skilllab/test_objective_scene.py:28` (`DEFAULT_PLAYS_HASH`)
- `tests/skilllab/test_layout_map.py:29` (`SAMPLE_MAP_DIGEST`)

Invariants whose violation is a lane bug, not a test defect:
- `tests/test_legacy_tactical_deleted.gd` (E3-1 to E3-5). `scenes/tactical/` must not exist. Lane A re-derives the legacy feature set inside `scenes/tactical_c/`. Any file naming `scenes/tactical/` is refused, per CLAUDE.md "No deletion without parity" (the reverse case).
- `tests/test_tacticalbridge_ratchet.gd` (the known-referencer list only shrinks).
- `tests/test_tactical_delta_reconstruction.gd:89` (row 26).
- `tests/transport/test_pipe_tactical_world.py` and `tests/transport/test_pipe_tactical_tier_state_reserved.py` carry the A30 ruling (rows 22 and 25).
- `tests/csim/test_PP_C_g3_pursuit_by_sight.py` (cover hides the enemy).
- `scenes/mockups/*/verify.gd`, which must not be edited to follow production.
- `tests/test_tactical_view.gd` plants `facing-fixed` and `camera-unbounded`, and `qa_plant("select-all-exists")` must return false (R-105-04).
- Every positive-control assertion (a `control` or `C#` or `H#` id). Weakening one is refused even when the main assertion is re-pinned.
- Any threshold, tolerance or `MIN_*` value (CLAUDE.md: Westley owns them).

Precedents showing re-records are always ruled by number: `TD-PP-A188-g3-invariant-reference`, `TD-PP-C-invariant-goldens`, and the "Re-recorded day23 on push/pa-land (A199)" comment at `tests/csim/test_F1_fog_per_faction_observers.py:299`.

## Part 3. Decision procedure the script can quote

Step 1: classify. A test is a defect only if ALL FIVE hold:
1. The failing assertion text is in the rulebook row (or the same pattern).
2. The brief or spec names the replacing line, and the agent quotes it verbatim (file:line).
3. The edit changes only the pinned literal or key list.
4. No threshold or tolerance moves, and no positive control is weakened.
5. The file is not in Part 2.

Step 2: apply the row's rule.
- RP: change the literal and cite the spec line.
- SUP: replace `==` with `<=` and add the named keys.
- PRES: invert the absence assertion into a presence assertion and keep the old absence as a control on a synthetic frame.

Step 3: the ruling agent never edits more than one test file per row except where the row says "together" (rows 17, 27 and 28).

Step 4: otherwise stop the lane and list it. A real finding is never reclassified as a skip.

Step 5: after the edit, the ruling agent runs the touched test alone and, where it applies, runs the positive control.

## Part 4. Ledger-row template (`TD-VG-<lane>-<n>`)

Append to the push ledger, `docs/northstar/plans/push_ledger_2026-09-22.md`. I found no programme-specific ledger file, so the Architect may redirect this. Class names in the existing file include `test-defect, rule-changed, A74` and `test-defect, harness-defect, A87`.

```
| <dayNN> | TD-VG-<lane>-<n> (test-defect, <rule-changed|assumption-changed|stale-pin>, <ruling or spec id>) | `<test file>` `<test id or function>` asserted `<quoted literal, exact>`. The spec line `<file>:<line>` ("<verbatim quote>") replaces it with `<new behaviour>`. Fix: <RP|SUP|PRES>; only `<the changed assertion(s)>`; no threshold, tolerance or positive control touched. Rule proved is unchanged: <S-###/R-###-##>. Verified: <test alone, N pass, 0 fail>; control `<id>` still <red on the plant, green clean>. Branch `<push/vg-<lane>-...>`. Red on main until `<piece id>` lands. |
```

Fill-in rules:
- `<lane>` is a letter A to F.
- `<n>` is a per-lane counter that starts at 1.
- If rows 27 and 28 apply, the one row lists every file changed.
- A refused case writes `REFUSED-VG-<lane>-<n>` to the stop list instead, with the same fields plus "why refused (Part 2 / step 1 failed at condition #k)".

Unresolved items that need the Architect or Westley:
- Rows 19 and 20 (pixel and colour tolerances against the bubble glow).
- Row 3 for lane C (the 3D zoom has no linear 2x).
- Rows 22 and 24 (the A30 and A4 rulings).
- Row 2 if the spec changes the fit rule.
- Which ledger file receives `TD-VG-` rows.

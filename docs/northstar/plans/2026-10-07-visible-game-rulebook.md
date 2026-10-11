# The stale-test rulebook (visible game programme, from scout 10, 2026-10-07)

Rule codes: **RP** re-pin to the new literal, quoting the spec line that replaces the old one · **SUP** a key list grows, assert superset · **PRES** assert presence instead of absence · **ARCH** stop the lane and list for the Architect.

## Decision procedure (the ruling agent quotes it)

A test is a defect only if ALL hold: (1) the failing assertion is in a row below (or the same pattern); (2) the brief or spec names the replacing line and the agent quotes it with file:line; (3) the edit changes only the pinned literal or key list; (4) no threshold or tolerance moves and no positive control is weakened; (5) the file is not on the do-not-touch list. Then apply the row's rule, edit one test file (except rows marked "together"), run the touched test alone and its positive control, write the ledger row. Otherwise stop the lane and list it. A real finding is never reclassified as a skip.

## Rows

| # | Test (file:line) | Pins | Lane | Rule | Control stays |
|---|---|---|---|---|---|
| 1 | `tests/test_tactical_view.gd:102,540` | `N_UNITS := 12` against frozen fixtures | A | fixtures untouched; a new frame field gets a new fixture file (RP) | yes |
| 2 | `tests/test_tactical_view.gd:309` | `scale == 1080/24000` (canvas fitted) | A | initial zoom change: RP; fit rule change: ARCH | yes |
| 3 | `tests/qa/desktop/test_pan_speed_zoom.py:93` | zoom2 == 2× zoom1 | A, C | A: RP to the spec's bounds; C: ARCH (perspective) | yes |
| 4 | `tests/test_tactical_camera.gd:104` | `UNIT_SIZE * 0.5` margin | A | const renamed: RP name only; margin widening: ARCH | yes |
| 5 | `tests/test_tactical_camera.gd:222-243` | own units inside the viewport after load | A, C | keep; a HUD safe rect only from a spec line (RP) | yes |
| 6 | `tests/test_tactical_view.gd:331-345`, `test_tactical_play.py:89,100` | `len(px) >= 100`; top-edge drag selects every drawn unit | A | camera start moved: RP the rectangle; selection rule change: ARCH | yes |
| 7 | `tests/test_tactical_view.gd:569-616` | `units_px` lists only visible units | A | keep (R-089-04: nothing is remembered) | yes |
| 8 | `tests/test_tactical_hud.gd:133` | a Button "END MISSION" | A | RP text only if renamed by the spec | yes |
| 9 | `tests/test_tactical_hud.gd:145,159` | DebugOverlay hidden; F3 toggles | A | keep | yes |
| 10 | `tests/test_tactical_hud.gd:170-215` | objective "letters N%", clock mm:ss, selection count | A | pattern-based; RP regex only to the spec's example | yes |
| 11 | `tests/test_tactical_view.gd:419-424`, `test_flow_spine.py:320-325` | `qa_state` keys incl. `plants`, `unit_count == len(units)` | A | SUP; never remove or rename | yes |
| 12 | `tests/test_qa_state_scenes.gd:220-222` | required scenes expose `scene`, `tick`, `plants` | A, B, C | SUP; moved scene: RP the path | yes |
| 13 | `test_flow_spine.py:327-337` | tactical screenshot differs from median by ≥300 px | A, C | keep (blank-frame detector) | itself |
| 14 | `tests/test_main_menu_items.gd:96-100` | exact five entries; no "tutorial"/"access key" | F | MULTIPLAYER: RP `want` to the spec's six; others ARCH | yes |
| 15 | `tests/test_main_menu_continue.gd:13-18` | a control named `Continue` | F | keep | yes |
| 16 | `tests/test_galaxy_view.gd:131` | `system_count == 80` | B | keep (sim-derived); ARCH if regions change | yes |
| 17 | `tests/test_galaxy_view.gd:157-193` | `owners`, `region_colours`, `systems_px` per region in front of the camera; `edge_counts` | B | keep the contract; key renames RP together | yes |
| 18 | `tests/test_galaxy_view.gd:259-263` | `edges_3d == true`; plant flips it | B | keep the key and plant | yes |
| 19 | `test_galaxy_pixels.py:131-197,231,273` | pixel at `systems_px` equals region colour within tolerance | B | ARCH (tolerance is Westley's) | yes |
| 20 | `test_galaxy_conquest.py:90-126` | flipped owner colour within `COLOUR_TOLERANCE` | B | ARCH | yes |
| 21 | `test_pipe_tactical_delta_frame.py:41,171` | `set(unit) == UNIT_KEYS` exact | A (+contract) | SUP; the contract names each key | yes |
| 22 | `test_pipe_tactical_tier_state_reserved.py` (detector `:57` `!= 0`, control `:97` rejects `state=1`) | `tier == 0`, `state == 0` (ruling A30) | A | `state`: RP by K-a quoting the spec's section 2: the assertion becomes `state` present and `state & ~7 == 0`; the control plants `state=8` and a missing `state` (this control literal change is permitted by this row); `tier` stays 0 (ARCH until the tier source is ruled) | yes, as rewritten |
| 23 | `test_pipe_tactical_delta_frame.py:270` | objectives exactly `{i, progress}` | A | SUP for `done` | yes |
| 24 | `test_pipe_mission_frame_briefing_fields.py:37,77,84` | `force`/`briefing` exact key sets; no `position_name` (A4) | A, E | SUP for named keys; `position_name` ARCH | yes |
| 25 | `test_pipe_tactical_world.py:131-142`, `test_pipe_shapes.py:171,178` | cover count; `tactical.schema.json` required; no `map`/`units` in deltas | A, C, E | new `map` fields SUP; map stays full-frame only (ARCH otherwise); schema updated by the contract piece | yes |
| 26 | `tests/test_tactical_delta_reconstruction.gd:89` | `view.map == truth.map`; units reconstructed | A, C, E | do not touch; a red is a `c_bridge.gd` bug | yes |
| 27 | `test_pipe_shapes.py:80`, `test_E02_S020_abi.py:22`, `tests/csim/conftest.py:64` | ABI 4 | all contracts | RP the three together when the contract bumps it | yes |
| 28 | `test_load_game_wrong_version.gd:14`, `test_E16_B5_save_version.py:13`, `test_E16_C2_save_version.py:14` | save version 7 (after stage 3) | E, C | RP the three together on a ruled bump; refusal controls stay | yes |
| 29 | `tests/specfactory/test_pack_validate.py:360-374` | `test_only` flags; manifest keys present | D | SUP; new pack: RP the dict | yes |
| 30 | `tests/qa/t1/test_rts_detectors.py:247` | the four detector keys | A | SUP with a positive control for a new detector | yes |
| 31 | `tests/test_tactical_view.gd:670-700`, `test_tactical_camera.gd:296-393` | camera inside the canvas | A, C | keep; 3D must still publish `camera {x,y}`; removal ARCH | yes |
| 32 | `test_tactical_play.py:230-246` | unit speed vs the C library | none | a red is a finding | yes |
| 33 | `tests/test_tactical_delta_reconstruction.gd:107,141-151` | two factions in the first frame; enemy positions averaged | K-h | stands with `fog_filter` off (the default); K-h's own tests set the flag | yes |
| 34 | `test_pipe_assign_commander.py:85-87` | enemy positions read from the first frame | K-h | as row 33 | yes |
| 35 | `test_pipe_tactical_tier_state_reserved.py:64-65` | enemy positions from the first frame | K-h | as row 33 | yes |
| 36 | `test_pipe_macro_group_orders.py:59-60` | enemies present (else "vacuous") | K-h | as row 33 | yes |
| 37 | `test_pipe_tactical_delta_frame.py:21` | nearest-enemy attack from the first frame | K-h | as row 33 | yes |
| 38 | `tests/qa/desktop/test_flow_spine.py:444-447` (S-C8-09) | at least two factions in `qa.units` | K-h | stands: the flag is off unless `tactical_view.gd`'s live call passes it; the desktop driver's live path passes it only when A4 has landed, at which point this assertion reads `units_px` of own units (RP, quoting K-h) | yes |
| 39 | `test_pipe_tactical_tier_state_reserved.py` (whole file) | `tier == 0` (row 22's "ARCH until the tier source is ruled") | K-a | ARCH ruled 2026-10-07 night: Q-133-02 gives tier per unit; the pipe emits the unit row's tier (the faction's tech tier at spawn until the roster carries per-unit tiers, a lane E item). The file is retired under TD-VG-K-4; its `state` detector and control already live in `test_pipe_vg_contract.py` | the state control, in the contract test |
| 40 | `test_pipe_place_structure.py` `test_tactical_frame_has_no_structures_key` | no `structures` key in a tactical frame | K-a | SUP: spec section 2 adds `structures` to full frames; the test asserts `structures` present and a list (TD-VG-K-5) | yes |
| 41 | `test_pipe_tactical_delta_frame.py` delta-shape, idle-empty-delta, n>1 last-frame, reconstruction-detects-dropped-change | an idle step from tick 0 yields an empty delta | K-a | stale-pin: bastions auto-fortify at tick 1, so `acd` and `state` bit 2 change on the first step; the fixture steps once past tick 1 before the assertions; the assertions themselves are unchanged (TD-VG-K-6) | yes |
| 42 | `test_pipe_tactical_delta_frame.py` `test_a_death_shows_in_units_removed_and_the_full_frame_agrees` | the reconstructed view equals a `step(0)` full frame | K-a | the comparison masks `state` bit 1 (fired-this-call is call-scoped by spec section 2; a `step(0)` frame has no fires); every other field compared exactly (TD-VG-K-7) | yes |
| 43 | `test_pipe_vg_contract.py` the `acd` test | `acd > tick` right after `activate_ability` on a surge | K-a | ARCH ruled: `acd` is present only while a cooldown runs (`cooldown_end > tick`); the pipe synthesises nothing (the pipe branch's `tick + 1` while active is removed). Surge zeroes its cooldown while active, so the test activates an ability whose activation starts its cooldown, or asserts after the active window (TD-VG-K-8) | yes |
| 44 | `tests/csim/test_VG_contract.py::test_structure_getters_enumerate_the_world_structures` fixture `hand_structures` | `count == n0 + 2` after re-initialising slots 0 and 1 | K-a | test-defect: the seed-11 world already holds three mission structures in slots 0..2; `hand_structures` uses slots 3 and 4 (TD-VG-K-9). The getters count `in_use && power > 0` (ARCH: the 64 pre-initialised placeholders are not structures) | yes |

Mockup `verify.gd` scripts: never edited; a red one means a lane edited a mockup, which is refused.

## Do not touch (the ruling agent refuses and lists)

Determinism: `test_checksum_trace.py`, `test_tactical_trace.py`, `test_E02_S020_determinism.py`, `test_E02_S020_rng_seeding.py`, `test_E02_S160_om_pow.py`, `test_E02_S160_no_default_features.py`, `test_E10_S072_a2_refresh_determinism.py`, `test_E17_S186_noise_deterministic.py`, `test_net_*.py`, `tests/net/*`, `test_libm_lint.py`, `test_alg_constants.py`. Goldens (re-record only by a numbered Architect ruling with its own ledger row): `test_B3_C2_friction_golden.py`, `test_F1/F2/F3_*` GOLDEN dicts, `test_PP_C_g3_hash_invariant.py` and its data, `test_PP_C_g3_rehash.py`, `test_E01_T2_collision_mask.py:24`, `test_E01_T2_walker_*` checksums, `tests/skilllab/golden_hashes.json`, `test_cross_machine.py`, `test_trace_real.py`, `test_mopup_real.py:20`, `test_objective_scene.py:28`, `test_layout_map.py:29`. Invariants (a red is a lane bug): `test_legacy_tactical_deleted.gd` (`scenes/tactical/` must not return), `test_tacticalbridge_ratchet.gd`, row 26, row 25 (A4), row 22's `tier` half, `test_PP_C_g3_pursuit_by_sight.py`, every positive control, every threshold/tolerance/`MIN_*`.

## Ledger row template

`| <dayNN> | TD-VG-<lane>-<n> (test-defect, <rule-changed|assumption-changed|stale-pin>, <spec id>) | <test file> <test id> asserted <quoted literal>. The spec line <file:line> ("<verbatim>") replaces it with <new behaviour>. Fix: <RP|SUP|PRES>; only <the changed assertion>; no threshold, tolerance or positive control touched. Rule proved unchanged: <S-###/R-###-##>. Verified: <test alone N pass 0 fail>; control <id> still <red on plant, green clean>. Branch <push/vg-...>. Red on main until <piece> lands. |`

A refused case writes `REFUSED-VG-<lane>-<n>` to the stop list with the failed condition number.

# Skill lab rev 2: overseer decisions (2026-10-14), read with the spec

The L1 and L2 audits found gaps in the spec. Each line below is binding for the builders. The Architect has been told. Rule meaning stays with the Architect.

## 1. FightResult defaults
New fields default to: firing_window=(0.0,0.0), weighted_unit_seconds=(0.0,0.0), weighted_window=(0.0,0.0), predicted_count="tie", predicted_type="tie", agreement="n/a", states=[].

## 2. Setup.point
Setup.point defaults to None. With no point and no group goal, the fallback is the first anchor of the other side.

## 3. orders_per_unit
orders_per_unit applies to opening orders only; timeline steps stay group-level.

## 4. Opening window
The window is half-open: [first_contact_tick, first_contact_tick + OPENING_WINDOW_TICKS). contract.OPENING_WINDOW_TICKS = 40 is a named constant (DRAFT-opening-window-ticks).

## 5. States rows
states rows are written at sample ticks only (Setup.sample_every, default 5), never every tick (cost).

## 6. Parity
fight() does not call firing.parity. Parity is checked by the smoke command and the integration tests only (cost). A non-empty parity result is a defect reported by those callers.

## 7. Pre-flight names
scenes.preflight(setup, engine) -> "ok" | "no_fit" | "unroutable" | "no_reach". It runs no tick and shifts nothing. placed_scene sets build.labels["prefight"] on every build. The holder is any group with order == "guard" (no no_reach for a meeting). When several refusals apply the precedence is no_fit, then unroutable, then no_reach. engine.py has no route-grid helper (only terrain_walk_mask and terrain_walkable_at), so unroutable uses a lab-side 50 wu breadth-first search over the walkable mask, from each attacker group's placed positions to the point on its layer.

## 8. Engine.set_cone
Engine.set_cone(w, type_id, range, half_angle, share) is a binding in engine.py (L2's row). Setup.cone is applied through it after each world reset (the cone table is lab-only state: FINDING-cone-state).

## 9. Guard scenes
scenes.guard_defenders sets Setup.point to the placed mean of the guarding groups (ruling 6). phase_b_choke does likewise.

## 10. with_terrain
with_terrain shifts Setup.point with the groups and goals. This is an L2 job, done first.

## 11. plays_space.py
L2 removes the mopup/quiet_from_first_damage replace() (two lines). L3 does the rest.

## 12. Deletions
Deleted by L2: mopup.py, approach.py, and the constants DRAW_BAND, SILENCE_TICKS, REISSUE_TICKS, BLIND_TICKS, HOLD_RADIUS in contract.py. WIN_MARGIN and the cell/scan stubs stay until L4. ground/highground.py and its tests are L6's deletion.

## 13. orders_per_unit flip
L4 flips the orders_per_unit default to False when E1 is on the lab branch. These tests assert orders_per_unit is True and become ruler rows at that flip: test_fight_outcomes.py Setup defaults, test_plays.py:418, test_asym.py:411, test_placed_by_feature.py:223, test_objective_scene.py:54, integration/test_slots_real.py:54.

## 14. Build order
L1 (built), L2, L3, L4, L5, L6, S, L7, serially on ONE integration branch push/labrev2-lab (Architect-accepted 2026-10-14). Each piece is its own commit range with its tests green and pre_gate OK, merging origin/main after each. There is ONE landing at the end, together with E1 and the golden re-record (TD-LAB-REV2-golden). E2 and E4 land after that. The reason: deleting mopup.py, approach.py, plays.MOPUP and the Setup fields breaks imports in batches.py, plays_space.py, scan.py, summary.py, ground/highground.py and terrain.with_terrain (found by the L2 test writer).

## 15. Harness spec
The stale clauses 5, 11, 12 and 13 of the harness spec (stalemate, win margin, approach) are rewritten by L7.

## 16. Mix M3b
`s3_over_the_choke` uses mix M3b = 7 Vanguard + 1 Raider + 8 Bombard on both sides (Architect 2026-10-14); plain M3 stays for `s2_screen`; `s3_types_by_reach` puts its Interceptors on layer 1; scaling at 8 to 48 uses largest-remainder rounding.

## 17. Placement of the new plays
The four new plays are placed with the anchor kinds pinned in `tests/skilllab/test_plays_space.py`; placed scenes use the play's own side 1 (ruling 2).

## 18. Ground scene
`s1_slope_top` runs on CANVAS 12000 (seed 11 has no slope at 4000). Walking units are set through `unit_types[name]['movement']='walking'` (fight.py, L6). A spawn returning unit id 0 is a lab defect (raise). Eye-height and flyer-seen knobs may be inert in the natural scene and are declared in `scenes_ground.INERT_KNOBS` (reported inert in the first batch; making them live is a later design call for the Architect/Westley).

## 19. Build order
L3 first; then L4 and L6 in parallel (disjoint files; L6 touches fight.py/scenes.py/terrain.py/ground/*, L4 batches/sweep/scan/depth/breakeven/pool/__main__); then L5, S, L7.

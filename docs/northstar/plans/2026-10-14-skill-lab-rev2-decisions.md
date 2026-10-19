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

## 20. Flyers in preflight (Architect 2026-10-19, corrected the same day; the first version said a straight-line cell walk, which reads a choke map as unroutable for a flyer that the engine routes round the wall)
Every mover is route-checked by the lab-side breadth-first search on the 50 wu grid from its start to the point; only the mask differs by movement kind. A flyer's mask is the cells not blocked at its layer (a block whose blocked_layer_top reaches the mover's layer blocks it; one below passes). A walker's mask is the cells that are terrain-walkable and not blocked. On a space scene (no terrain) the two masks coincide, so a flyer goes round a wall through its gap exactly as a walker does. no_fit on field_seed terrain reads terrain_walkable_at for every walking mover; no_reach is unchanged.

## 21. L4 (Architect 2026-10-14/19): sweep reports ruling-3 baselines in the baseline column; depth keeps blob and line; ceiling_hit = won everywhere; cone on Vanguard only; arc and cone families skipped with a recorded reason when the library lacks the symbols; refinement sign vs naive_attacker (and a second listed crossing vs naive_defender for defending plays); the orders_per_unit default flips to False only because E1 lands in the same landing (revert the flip in the same commit if E1 is pulled).

## 22. Positive control per knob (Architect 2026-10-19)
A knob's positive control is one designated fight that the knob is known to touch (the spec's "a known fight"), not a conjunction over every play. Damage-up's control fight is on `s3_types_by_reach`; the test passes when that fight responds. A play on which a knob is inert is listed in `INERT_KNOBS` only with the rule that makes it inert (as eye height is for the natural ground scene); an inert observation with no rule behind it is a finding, traced before batch one. `s3_layer_above` reading identical margins at damage-up 1.0 and 0.5 is such a finding: under reach 1 the lower side fires up and the penalty should bite, so either the lower side never fires in that play or the knob does not reach the engine there. The L4 builder is not blocked; the overseer records the cause.

## 23. Caps under group orders (Architect 2026-10-19)
The smoke asserts zero caps outside the control kinds; the spec's verification line stands ("every fight ends side0, side1 or draw"). A cap is a defect to trace, never a tolerated row and never a result; `defects.cap_rows` exists for the trace, not as an alternative to the assertion. The cap of 12000 ticks is a threshold and stays Westley's. Decision 13 and 21 tightened: the orders default flips to group attack-move only when E1 is in the landing and the smoke caps zero under group orders; until both hold `orders_per_unit` stays True. The 7 of 108 play fights and the mirror control that capped under group orders on layout 192 (objective scene at 2800, seed 0, 1 v 2 at 12000) are recorded as `FINDING-group-orders-cap` for the E1 gate: the expected cause is survivors stopped at the point outside mutual range or sight, which is the contact rule's assumption failing. The one non-control cap under per-unit orders is traced before the lab landing; the smoke test stays red until it is. The damage-up control runs to elimination (no tick cap) because the 600-tick control cap hides the effect; the vision and null controls keep `CONTROL_MAX_TICKS`.

## 24. Second crossing (Architect 2026-10-19)
"Defending plays" means plays with a holder: every play whose baseline column carries a `naive_defender_*` role gets the second listed crossing against it; a meeting (no holder) has none. The test as written (a second crossing for every defender-baseline role) is the right reading.

## 25. Naive defender construction (Architect 2026-10-19)
Confirmed as built: naive_attacker is `scenes.placed_scene(..., "naive")`; naive_defender replaces side 0 by one blob per unit type at that type's mean anchor, same units and counts, the play's timeline dropped. The layer rule of ruling 3: the `_play_layer` variant keeps each type on the layer the play gave it (a layer play's arrangement minus its skill); the `_attacker_layer` variant puts every type on the attacker's layer (the same-layer fight). Moving the whole blob to one raised layer is neither variant. A baseline variant in which no type on either side can reach the other's offset is refused `no_reach` in pre-flight like any scene, never run to a cap; the 35 caps of the first try say the pre-flight was not applied to baseline variants, which L2's refusals must cover.

## 26. Naive blob that does not fit (Architect 2026-10-19)
A naive blob is the arrangement with no skill in it, not an arrangement packed where the map has no room: where the blob's next cell is blocked, placement skips to the next free cell in its existing fill order, so the blob keeps today's shape on open ground (golden hashes unchanged) and fits wherever the play's own units fit. When a layout cannot hold the count at all, the refusal is listed with its role, the play's scan on that layout stops at the last headcount where both baselines placed, and the cell is marked `baseline_no_fit`, which is neither a ceiling hit nor a finding.

## 27. How pre-flight learns a type's movement (Architect 2026-10-19)
From the same source fight.py sets on the engine: `setup.unit_types[name]["movement"]` when the play gives it, else the engine's own reading through `Engine.movement_kind` (`om_unit_profile_movement_kind`), where an unset type reads flying (tactical_move.c, "an unset type reads flying"). Built-in types with no key are flyers in the engine; walking is only what the lab sets, and it bites only with terrain present (unit.c, `om_terrain_present` guard). The flyer test clause "a built-in type, or a custom one with no movement key, is a flyer" is therefore correct and stays. What was wrong was decision 20's straight-line walk: the flyer test's expectation that a line crossing a wall with a gap reads unroutable is retired as a test defect under `TD-LAB-REV2-L6-flyer` (the error was the Architect's clause, not the writer's reading), and the file is rewritten to the corrected rule: no gap at the flyer's layer reads unroutable; a gap reads ok; a block whose top is below the flyer's layer reads ok; a non-walkable terrain band reads ok for the flyer and unroutable for the walker (the positive pair). `test_placed_by_feature`'s ok at the choke holds.

## 28. The attack-move idle cap (Architect 2026-10-19, from the overseer's cap trace)
Every cap in the smoke, damage-up, objective and mirror runs has one shape: an attack-moving unit whose route ends short of its point goes idle with no destination while holding the attack-move, fires only at what is already in range, and the enemy stands just outside range. Two ways in, ruled apart:
1. R-087-06 return fire overwrote the ordered point with the attacker's position, so the unit resumed toward the dead attacker and idled there. Rule conflict with Westley's 2026-10-13 ruling (an attack-move is not finished until the unit reaches its point): R-087-06 rewritten in E-11; the redirect is one engagement and the unit resumes toward its original point. Engine fix under the E1 row (E1b if E1 is already built), tests first by E1's writer: the lone-attacker-against-holders scene on layout 192 that capped, red today with the idle line pasted; control: the same scene with the attacker killed before it fires eliminates.
2. R-099-05 give-up ends a group attack-move where it stands, the same state as an arrival, and an arrived unit does not close on a visible enemy outside its range (no rule in the bible makes an idle unit chase; R-096-02 engages what enters range). The engine is per rules here; not a defect. The lab's orders are what change: re-engage (`fight.py` timeline, L2): when a side has had no unit fire or move for `REENGAGE_SILENCE_TICKS` (DRAFT 40, the R-099-05 window; Westley's number) while an enemy is visible to it, every idle unit of that side holding an attack-move role is attack-moved onto the enemy centroid (on the enemy's layer, decision 2's point rule); a guard-stance holder never gets it (it keeps its post, R-096-08). Both sides, naive included (ruling 2). The count per side is the CSV column `reengage_0/1`; the first batch reports its distribution. A cap after a re-engage stays a defect (decision 23); elimination is still the only end.
The orders flip of decision 23 waits for 1 and the smoke at zero caps. The trace's scratch scripts are committed as evidence under `docs/northstar/research/layer_dynamics/audits/attackmove_idle_cap_2026-10-19/` with the ledger row `FINDING-attackmove-idle-cap` pointing at them.

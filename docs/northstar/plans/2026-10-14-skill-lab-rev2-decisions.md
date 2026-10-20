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

## 29. L5 readings (Architect 2026-10-19)
1. C1 against both baselines: the existing formula run once per baseline role in place of the mirror scan, one verdict per role, no combined verdict; the artifact shows both.
2. The opening window is the default basis of the C2 agreement (ruling 5 makes it the primary prediction form); whole-fight totals are reported beside it as the chart. Verdicts that change between the two are listed, which is itself a reading of the measure.
3. A ceiling-hit notable comes from the play's own rows only. A baseline that also wins everywhere is not a notable; the cell is listed as `baseline_ceiling` (no crossing is possible there).
4. A diagram's legend marks the DRAFT numbers it can tell from its rows (opening window, arc family, cone family); the artifact's header lists every DRAFT number in force once (opening window, arc, cone, guard radius, mixes, re-engage silence, scale marks).
5. The choke is the gap between walls; the diagram draws walls and covers and labels the gap.
6. `both_wrong` notables include control and baseline rows, with the role in the label; a `both_wrong` on a control is the strongest finding against the measure.
7. `transfer_class`: the swept values of the arc and cone families are magnitudes (they will be retuned); the mechanisms themselves (the arc gate, the sector) are rule geometry already ruled by Westley. The writer's reading stands for the values.
Wiring: L5 takes ownership of `__main__.py` for the `artifact` command (reads the sweep CSVs, writes the page and the SVGs) by an owner-row edit once L4 is in the lab branch; no separate wiring piece. The `summary.write` TypeError on a ceiling-hit scan is fixed inside L5's build; the test that found it stays.

## 30. E1b gaps (Architect 2026-10-19)
1. A member of a group attack-move hit from out of range pursues as the lone-unit branch does and its point of record is its slot (the group's point plus its formation offset); when the pursuit ends it resumes toward the slot. Tested: a group of two or more, one member hit by a long-range attacker, attacker dies, the member's destination is its slot again.
2. The pursuit ends when the attacker dies, when the pursuer passes the R-096-03 leash (200 wu from its acquisition anchor), or when the attacker is no longer seen by the pursuer's side (a unit cannot chase what it cannot see; the per-tick validation of R-087-08 drops it). "Moves N wu away" is not a trigger. Three tests, one per ending; the leash and sight endings resume toward the original point like the death.
3. The resume is immediate: on the tick the pursuit ends the destination is the original point again, within the 4-tick cohort stagger of R-087-08; the unit does not walk to the attacker's last spot first. The writer's 60-tick bound narrows to 4 (a rule number, not a fixture).

## 31. L5 audit items (Architect 2026-10-19)
A. Sweep rows carry a `point` column (string, family-local label of the series the row belongs to): cone rows have `knob_value` = range and `point` = `half=<deg>`; emitting rows have `knob_value` = sight and `point` = `vision=<v>`; every other family writes `point` = `-`. Crossing detection groups by (family, play, layout, point), so each half-angle is its own series along range and each vision level its own series along sight; the artifact also shows the cone 3 by 3 grid. L4 follow-on on `sweep.py` and `rows.py` (tiny), L5 reads it.
B. The mirror C1 is kept beside the per-baseline C1 as its own row; the artifact lists mirror, naive_attacker and naive_defender.
C. C1 uses the opening window like C2 (decision 29), whole fight beside it. The noise reference against a naive defender at its post is the largest |advantage| over that baseline's fights, strict greater-than, plus the minimum.
D. A crossing diagram carries arrows to the break-even rows at both bracketing headcounts for the play and for the baseline, each labelled with (enemy_heads, outcome), and draws the placed units of the fight at the bracketing cell; the artifact sentence under it gives the counts. A number without its diagram is not evidence (Westley 2026-10-13).
E. The map-report label is kept under the name `baseline_ceiling` (decision 29 item 3), six labels; the ruler row `TD-LAB-REV2-L5-maplabels` is confirmed with the rename.
F. Confirmed: the artifact header lists every DRAFT number in force once; the slope divisor joins that list only in a batch that runs the ground scene; the 0.25x to 4x band is a ruling, not a draft number, and is not marked; the legend marks only what its rows touch.
G. Stands (decision 29 item 7).

## 32. BASE readings (Architect 2026-10-19)
1. A baseline refused by pre-flight (no_reach, unroutable) drops only that baseline; the play runs against the remaining ones and the refusal is listed with its role. A no_reach on a layer play's attacker-layer variant is expected, not a defect.
2. A baseline that cannot be placed at headcount 8 lists the layout as `baseline_no_fit` with last_headcount None, no scan rows for the play on that layout, no defect.
3. A scan cut at K by `baseline_no_fit` that the play wins throughout 8 to K is an always-won cut scan: not a ceiling hit (a ceiling hit is beating 48), not a finding; refinement runs only inside 8 to K; the artifact says "won through K, scan cut by baseline_no_fit" so it is never read as "no crossing exists". A cut scan with a loss below K shows "scan cut by baseline_no_fit at K" beside its normal result (crossing or not).
4. The blob's fill order continues over free cells without a fixed limit; "cannot hold the count" means no free cell remains inside the layout bounds (the existing radius check against free cells). The order is deterministic (rows identical at 1 and 12 workers).
5. A blob of one unit follows the same rule with no special case: the anchor is radius zero; if blocked, the nearest free cell by increasing radius. One test.

## 33. L8 re-engage readings (Architect 2026-10-19)
1. A side re-arms only after one of its own units fires or moves and then another `REENGAGE_SILENCE_TICKS` of silence. An unbroken silence is one event; a re-engage that produces no movement stays silent and the fight caps, which is a defect to trace.
2. `reengage_0/1` counts events (one ordered call per trigger), not units ordered.
3. The order is an (x, y); each unit keeps its own layer (decision 2's contact rule). The centroid is taken over the enemy units in the set of item 4 on every layer.
4. The centroid set is the living enemy units visible to the ordering side, never all living units (fog would leak into the orders). The tests change from all-living to visible in the fix pass.
Golden hashes: the mirror control's hash is stale on the lab tip because lab-side pieces (orders, fight end, placement) legitimately changed the control fight. The re-record under `TD-LAB-REV2-golden` is the landing clerk's and the row is written at the landing; before re-recording, the clerk runs the engine-only proof of the spec's golden procedure (the old lab's three controls against the new engine at arc 360 and cone off reproduce the old hashes; E1 and E1b excluded by design) and pastes the three hashes in the ledger row.

## 34. L5 fix-pass readings (Architect 2026-10-19)
1. Bracketing headcounts: per knob value and per scan (play, baseline) an arrow to the first row of the break-even cell and one to the first lost cell, labelled (enemy_heads, outcome); a ceiling scan has only its top cell, a lost-everywhere scan only its first cell.
2. (Corrected the same day: the conditions module holds no thresholds; `evidence.Thresholds` has no defaults because every pass mark is Westley's and an input, and the sweep files do not hold the engine-run scans `conditions.evaluate_bases` reads.) The `artifact` command takes an optional `--thresholds <json>` of Westley's pass marks. Given it, the command computes the verdicts that the CSV rows alone support (C2 agreement counts on the window and the whole fight; C1 advantage against the baseline maximum) and shows each verdict with its threshold name. Without it the conditions section says "no condition verdicts: thresholds not supplied" and still lists the raw agreement counts and C1 advantages as numbers with no pass or fail. No number is invented.
3. The artifact learns that a batch ran the ground scene from the rows (any row whose play is a ground scene), with a positive test.
4. The cone 3 by 3 grid is a table of signed gain per range and half-angle, one per (play, layout, baseline role).
`point` is written by `sweep.py` as a fight-row label and reaches the CSV as the column `point`; the fixed-key list in `rows.py` is unchanged.

## 35. Artifact verdict rules (Architect 2026-10-19)
1. C2 verdict = the existing `check_c2` statistics (rank agreement rho at or above `c2_rank_agreement`; off-trend share at or below `c2_off_trend_share` with `c2_off_trend_margin`), over every CSV row pooled and per headcount cell in the order of `conditions.c2_table`, the raw counts of the five agreement words beside, per basis.
2. The row's `predicted_count`, `predicted_type` and `agreement` columns are the window basis (decision 29). Whole-fight words are re-derived from the totals: `predicted_count` from `firing_unit_seconds_0/1` (larger side; equal = `tie`, agreement n/a), `predicted_type` from `weighted_unit_seconds_0/1` (never from the count), outcome as in the row. (The writer's header read predicted_type from the count totals; corrected here.)
3. C1 per (family, play, layout, point, knob value) and baseline role, at the equal-numbers cell (enemy_heads 16): the mean advantage of the play's rows there against the largest absolute advantage of the role's rows there, plus `c1_min_firing_advantage`, strict greater-than. A scan without that cell (cut below 16) has no C1 and says so.
4. The mirror C1 is not computed by the artifact command (a CSV row does not carry the mirror scan); the artifact lists the naive_attacker and naive_defender C1 and says the mirror C1 lives in the engine-run `evaluate_all`.

## 36. Blob continuation bounds (Architect 2026-10-19)
1. A continuation cell must lie inside the layout's canvas (cells outside count as blocked) and in the anchor cell's connected free region on the mover's route mask of decision 20 (a wall separates regions, so the blob never spills through or past a wall onto the far side; a cell reached through the gap is in the region and allowed). "Cannot hold the count" = that region has no free cell left. Pre-flight no_fit is unchanged. This gives `baseline_no_fit` a real path on hand-built terrain (a closed pocket smaller than the count), not only on fakes.
2. The continuation is the existing Fermat spiral continued without end (same pair count and radius formula, i = pairs, pairs + 1, ...), pinned to 4 decimals.
3. Unit k takes the k-th free cell of the fill sequence (fill order with blocked and out-of-region cells removed); tests compare unsorted.

## 37. Scale shard readings and the unmet speed marks (Architect 2026-10-19)
Readings confirmed: "one play scan 8 to 48" is `plays.blob_play(16)` against its mirror; the 90 s mark excludes pool startup; the 1.5 s fight check stays ungated like AC 28. Finding `FINDING-speed-marks-unmet` (the overseer's ledger row): AC 28 (full scan 16 v 12 to 24, mark 30 s) took 283.5 s wall at load 22 to 26 on 16 cores and about 180 s CPU on an idle box; one 16 v 48 fight took 1.50 to 1.55 s CPU (2.4 s wall under load) against the 1.5 s mark; the 90 s scan guard passes at 14.2 s with bisection; smoke and damage-up rows hash identically at 1 and 12 workers. The lab lands with those two tests listed as known red under the finding, not skipped and not widened; the batch runs inside the 4 h budget regardless. The marks are Westley's numbers (ruling 13): whether to keep them and queue a speed-up piece (engine or pool) or move them is asked of him in the spec's open list.

## 38. Blob region resolution (Architect 2026-10-19)
1. Cell resolution, the same 50 wu grid as the decision 20 search: a continuation point is accepted when its route cell is free and in the anchor's region. Slivers inside a blocked cell are not used (layout 192's (3139.97, 2117.59) beside the gap edge is out).
2. A blocked anchor cell: the region is the connected free region of the nearest free route cell to the anchor.
3. A blob of one: the nearest free in-region cell by increasing radius from the anchor in steps of the route grid, ties by angle in the existing spiral order; the tests pin the cell and drop the 150 wu bound.
A real cut at K of 8 or more on a closed pocket is not buildable through the naive scene (the attackers outside the pocket read unroutable at every fitting headcount, so the baseline is refused, not cut); K of 8 or more stays covered by the fake-label tests and K under 8 by a real layout. The layout 192 unit at (3277, 2143) is in the anchor's region through the gap rows and stays.

## 39. L7 docs readings (Architect 2026-10-19)
1. Q-008-07 closes with (a), ruling 5 (the type-weighted prediction). Q-008-03 is the cross-layer parameter families: it stays open with a rev 2 note citing rulings 10 and 11 and closes only when the ALG rows exist, after batch one's analysis and Westley's numbers. The spec's and the existing test's "(a), ruling 5" citation for Q-008-03 is corrected to Q-008-07.
2. L7 rewrites every harness-spec clause the built lab makes wrong (5, 11, 12, 13, 14, 17, 18, 19, 20, 26, 28), no new rule meaning (stale-doc tripwire); the L7 row and its tests are extended. In clause 12, beyond `stalemate_ticks`: `reach_play` is a stat variant retired by ruling 2 (the range study is the engine's range-up multiplier by offset); `damage_play` stays as the labelled positive control of ruling 2; `goal` None is replaced by `point` (decision 2); the orders are per-unit attack-moves to the shared point until the decision 23 flip; the contact placement sentence stands.
3. The README describes `orders_per_unit` True as the default and says the flip waits on E1 and E1b in the landing and the smoke at zero caps; nothing further is pinned.
4. `FINDING-speed-marks-unmet` cited by id in README section 12 is fine.
5. The README open list names `FINDING-damage-up-layer-above`, `FINDING-group-orders-cap` (traced to `FINDING-attackmove-idle-cap`, fixed by E1b and L8) and `FINDING-attackmove-idle-cap`, open until the smoke caps zero, status per the ledger at L7 time.
6. Q-LAB-01 is marked superseded by Q-LAB-03; ROADMAP T14's citation moves to Q-LAB-03.
7. E2 and E4 leave L7's `depends_on`; L7 documents arc and cone as built, landing with E2 in batch two; `test_l7_depends_on_every_other_lab_rev2_row` is changed by a ruler row; a small L7b after the E2 and E4 landings updates their behaviour docs. `docs/northstar/plans/skilllab-harness-spec.md` moves from L1's `owns` to L7's in the records edit (L1 is built and has no further edit to it; two in-flight rows never own one file).

## 40. Batch one scope, flip timing, E0 numbering (Architect session b1e8769e / ouroboros-manifold-b0, 2026-10-19, implementation; Westley may veto)
1. Batch one runs the three smoke layouts 81, 78, 192 only, verdict-less (no `--thresholds` file until Westley supplies one after reading the first artifact). The orders_per_unit flip rides the lab landing with E1 and E1b, before the single golden re-record under TD-LAB-REV2-golden. E0 takes the next free ABI and save numbers at its landing from the visible-game Dispatcher; 8 and 12 are provisional. L4 and L6 are attached in the lab landing's records. Records-only commits may go straight to main with status_check and owner_lint OK.

Architect's rationale: batch one is a method check of the lab, not a sweep; width comes in batch two, after the artifact form is approved. The six pin tests of decision 13 become ruler rows in the landing. E7 launches today on the visible-game side with ABI 8 and save 12, and the places lane P3 is written for save 13, so E0's numbers are the next free at its landing, taken from the Dispatcher (ouroboros-manifold-d0 owns the numbering); E0's text must not pin a number before the clerk asks. A built piece that reads queued in `pieces.toml` is a status_check drift.

Answered without a decision number: speed marks stay Westley's (decision 37 stands); DRAFT numbers are used as DRAFT, with the list in front of Westley alongside the artifact; a drift auditor runs before the lab landing (drift_audit.md pattern, report to Westley unedited); the artifact form is reviewed by the Architect before Westley.

## 41. Drift audit of push/labrev2-lab-m4: smoke parity, anchors, holder, no_fit, reach, replicates, states (Architect session b1e8769e / ouroboros-manifold-b0, 2026-10-19, implementation; Westley may veto)
After a fresh drift audit of `push/labrev2-lab-m4`. All fixes are tests first, in the post-merge fix piece LAB-REV2-FIX.
1. The smoke command runs `firing.parity` and writes it to `smoke_summary.json` once E0 is in the landing; until then the field reads "skipped: E0 absent".
2. Per-type anchor, as decision 25 says: one naive blob per unit type at that type's mean anchor. `sweep.py:308` (one anchor for all blobs) is the defect.
3. Holder = side 0 has a guard-stance group in the Setup, derived from the Setup, never from the play name (`sweep.py:184` `baseline_roles` keys off the `s3_` prefix: defect). A meeting (no guard group) gets no `naive_defender` baseline.
4. Only walking movers read `terrain_walkable_at` for no_fit; flyers and guards are checked against blocks only (decision 20 as rewritten). `scenes.py:254` is the defect.
5. `reach_play` and the `reach` command stay until a later piece; no change now. L7's "kept only for the reach command" sentence stands.
6. 8..24 stays at 10 replicates for the golden-hash controls and the `reach` command. The README says ruling 4's 8..48 is the scan of plays, not of the hash controls.
9. `FightResult.states = []` when off, per decision 1; fixed with the next build. A test that pins None is a ruler row (assumption changed by decision 1).

## 42. Drafts marked and extras accepted (Architect session b1e8769e / ouroboros-manifold-b0, 2026-10-19, implementation; Westley may veto)
7. Every one is marked DRAFT in code and in the artifact header: `scan.COARSE_STEP` 8, the probe-count bounds (at most 14), `sweep.CONTROL_MAX_TICKS` 600, the ground-scene geometry in `scripts/skilllab/ground/scenes_ground.py` (30 + 3*sqrt(n), radii 20/12/8, the five coordinates, "measured"). `plays.MAX_TICKS_BIG` is deleted as dead logic. `COARSE_STEP` and `CONTROL_MAX_TICKS` go to Westley with the other marks (the Architect carries them).
8. Accepted as implementation (extras), each with its file: `contract.trim_series` and the lean pool path (`scripts/skilllab/contract.py`, `scripts/skilllab/pool.py`); the E3 settle-cache clearing in `om_move_load_radius` and the 2R > margin clamp in `om_move_probe_sure_blocked` (`csrc/tactical_move.c`); `sweep.in_band` (`scripts/skilllab/sweep.py`).

Two heads-ups from the Architect: Westley asked whether a unit that sees an enemy should attack it (a report is with him; if he rules yes, L8 re-engage and mop-up become unnecessary and the E1 row grows, so L8 gets no more work than it needs to land). Westley asked two Opus analysts for wider roster mixes (M0-M4 use only four of six types), so the mix table must stay data-driven.

## 43. The orders flip, re-engage and blind posts (Architect session b1e8769e / ouroboros-manifold-b0, 2026-10-19, implementation; Westley may veto; item 4's number and item 7 are Westley's)
Evidence (the overseer's): the orders flip fails decision 23's zero-cap condition. Under `orders_per_unit=False` the smoke keeps 3 baseline-row caps and the flyer scene caps; under per-unit control there are zero caps. Two mechanisms. A: the re-engage group order is a no-op, because group slots are the click plus each unit's own offset from the group centroid (units already at the centroid get a destination equal to where they stand), and the trigger never re-arms after a no-op. B: survivors are blind to each other at the layout-192 doorway, so "while an enemy is visible" (decision 28) never holds.
1. Flip, conditional. Mechanism A is fixed first inside the FIX piece (items 2 and 3, two small `fight.py` changes with tests), then the 3-layout smoke is rerun under `orders_per_unit=False`. If every remaining non-control cap is a mechanism-B row, the flip rides the landing and those rows are listed under one finding (item 6), so there is one golden re-record. If any other cap remains, the lab lands without the flip (default True, flip tests parked on `push/labrev2-flip-tests`) and the flip is its own later piece; the second re-record is then the price. Decision 23's condition now reads "zero caps outside `control_*` that are not blind-post findings".
2. Re-engage issues a per-unit attack-move for every idle unit, one order each, onto the centroid. Re-engage is a lab-issued order and is exempt from the play's orders mode.
3. A no-op engage (every ordered unit has dest None one tick later) re-arms at once and retries after another `REENGAGE_SILENCE_TICKS`. No new number.
4. "Moved" for re-arming is displacement over the silence window greater than `DRAFT-reengage-moved-wu` 1 wu, marked DRAFT in code and in the artifact header. Westley's number, on his list.
5. No walking toward an unseen enemy; "while an enemy is visible" stands (decision 28). A fight whose survivors cannot see each other is a finding row, not a cap defect of the lab. Pre-flight gains the reason `blind_post` (item 6).
6. Shift, then refuse. The baseline builder moves a naive-defender post that is blind to the play's side start to the nearest free cell on the route grid from which that start is visible (same region, increasing radius, ties by the existing spiral order) and reports the shift in the row. If no such cell lies within the guard radius (200 wu, DRAFT), pre-flight refuses the baseline with reason `blind_post` and the artifact says "no naive defender: blind post". Tests first.
7. A guard stepping out to shoot a visible out-of-range enemy is not ruled here: it is Westley's (one of the three cases of his "sees it, attacks it" question).
8. His "sees it, attacks it" question is not ruled yet; the report is with Westley. FIX and the merge proceed, with no L8 change beyond items 2 and 3. If he rules "sees it, attacks it", L8 and mop-up fall away in a later piece.

## 44. The blind-post probe and its shift (Architect session b1e8769e / ouroboros-manifold-b0, 2026-10-19, implementation; Westley may veto)
Makes decision 43 item 6 testable (the "Q6" of that decision).
1. A naive-defender post is blind iff no clear sightline exists under R-098-02 (a blocked 100 wu cell on a layer at or below the viewer's layer crossing the segment) between the post and the nearest point of the opposing side's route start region, range ignored. The probe is pure lab-side geometry on the Setup's blocks in `scripts/skilllab/scenes.py`: no engine call and no spawned world.
2. Shift: the nearest free route-grid cell in the same region with a clear sightline, by increasing radius, ties by the spiral order, within the guard radius 200 wu (DRAFT). None found: pre-flight refuses with reason `blind_post`, the fifth reason after `no_fit`, `unroutable`, `no_reach`.
3. Tests, first: a wall cell on the segment makes the probe say blind, and the shift lands on the first cell past the wall's shadow; a clear segment says not blind; the shadow test is on layer offsets (a block whose top is below the viewer's layer does not block).
4. The artifact lists every refused baseline, for every reason, as one line "no naive <role>: <reason>" with the reason one of `no_fit`, `unroutable`, `no_reach`, `blind_post`. It is built in L5's report. This replaces decision 43 item 6's wording "no naive defender: blind post".

Smaller readings confirmed:
5. The retry tick of decision 43 item 3 is N after the no-op is detected.
6. `defects.cells` excludes blind caps.
7. Unequal-count groups of one type use the plain mean.
8. One blob per (type, layer) only when a type's layers differ, else one per type (decision 25 reads so).
9. The parity default world is the open-ground mirror blob, 16 v 16, tick 0, arc 360.

## 45. Rulings after the second drift audit of push/labrev2-lab c2d9bce8 (Architect session b1e8769e / ouroboros-manifold-b0, 2026-10-19, implementation; Westley may veto)
1. D1: the blind-post shift (decision 43 item 6, decision 44 item 2) is reported as artifact lines "naive <role>: post shifted <wu> wu", one per (play, layout, role), and as a `shifted_posts` field in the smoke and sweep summaries. No CSV column.
2. D2: decision 34 item 3 (ground-scene detection, the slope-divisor header line, its positive test) is withdrawn for batch one. The ground scene, its slope-divisor header line, the detection and its positive test are batch two's, built with the ground family. The README says so.
3. D3: the README and the ground README reword "the first batch reports the inert knobs" to "batch two".
4. X1: layouts 81 and 78 refuse the two vision plays (`s3_layer_above`, `s3_types_by_reach`) at the play's own pre-flight (`no_fit`), so batch one's vision cells effectively run on layout 192 only. Accepted for the first run. The artifact header and the README say so: "vision cells: layout 192 only; 81 and 78 refuse the play: no_fit". A probe report goes to Westley: a short table of which draw layouts fit the vision plays (and `s3_over_the_choke`, `s2_concave`), with a count per layout of how many of batch one's plays fit, so he can pick replacements that fit the most. No layout swap without Westley.
5. N1 to N4: names and the roster table.
   - DRAFT-* names in code: DRAFT-mix-M1..M4, DRAFT-mix-M3b, DRAFT-behind-cover 150, DRAFT-ambush-behind 200, DRAFT-coarse-step, DRAFT-control-max-ticks, DRAFT-probe-count-bound.
   - The probe-count bound 14 is derived from `COARSE_STEP` in the tests, not written as a literal.
   - The roster mixes become ONE data table in `plays_space.py` with a `used_in` column (plays) and an `enabled` flag. New mixes M5 to M9 are added there once Westley says go on the roster analysis (decision 42's heads-up).
   - A small refactor piece, tests first, no number changes.
6. Docs: every stale documentation item of the audit is fixed, tests first where a test reads the doc.
7. G2: the Architect edits the stale "the engine today" sentences in E-13 R-096-02 and E-11 R-087-06 once told the E1 landing sha; the rule bodies stay as rewritten.
8. P2: the 24 ownerless files the audit found are added to the owning rows (LAB-REV2-FIX, -E1B, -L8, and the rows owning `summary.py` and `guard.py`) in `pieces.toml` before the landing. `owner_lint` and `status_check` are OK before every push.

## 46. Firing arc number (Westley 2026-10-19)
DRAFT-firing-arc-deg is 30 (Westley: "#5 yes 30 degrees"), no longer 120; the arc family's sweep band is read from 30. Recorded by the Architect; the overseer's code and artifact header follow.

## 47. Arc grid from 30, T1 as a strict expected failure, five small readings (Architect session b1e8769e / ouroboros-manifold-b0, 2026-10-19, implementation; Westley may veto)
1. Arc family, following decision 46: base 30 degrees (Westley's firing arc). Grid 30 x {0.25, 0.5, 1, 2, 4} = 7.5, 15, 30, 60, 120 degrees, the band as for every family (ruling 11: start at the bible's value, step inside 0.25x to 4x). The null control stays 360 = unset. The tests that pin the 360-based grid (360, 270, 180, 120, 90) move under one ruler row (assumption changed by decision 46), rewritten by the test writer, not the builder. The family stays skipped in batch one while E2 is absent.
2. LAB-REV3 T1 (the coverage test) lands with piece A as a strict expected failure whose reason names every uncovered cell, reach pairing and layer: a documented red with its finding rows `FINDING-lab-d1` and `FINDING-lab-d2`, not a skip. Piece B removes the marker and T1 passes plain. The landing report of A lists T1 under known red with that reason. The LAB-REV3 plan file is updated: its DRAFT line saying A lands T1 expected-red is this ruling.
3. Smaller readings confirmed:
   - `shift_wu` in `shifted_posts` is the largest `placement_shift` over the headcounts built for that baseline.
   - The vision-layouts header sentence (decision 45 item 4) reads the layouts that ran from the vision family rows, not a fixed list.
   - `DRAFT-probe-count-bound` has no code line (the bound is derived in the tests); the header text "(at most 14)" becomes "(at most 9 at COARSE_STEP 8, derived)".
   - `DRAFT-behind-cover`, `DRAFT-ambush-behind` and `DRAFT-mix-*` names join the artifact header DRAFT list.
   - The arc header name stays `DRAFT-firing-arc-deg`, but the entry reads "Westley's ruling 30 deg".

## 48. Firing arc lower bound 5 (Architect session b1e8769e / ouroboros-manifold-b0, 2026-10-19, implementation; Westley may veto)
Numbered 48: the highest decision on origin/main is 47.
1. `OM_TP_FIRING_ARC_DEG` lo becomes 5 (was 10), hi stays 360, default 360. It is an engine-safety bound, not a design number: a 5 degree arc still contains a facing direction and the sin/cos tables hold at that width. Westley's number is the 30 degree base (decision 46); the band gives 7.5 as the grid's floor (decision 47), and the bound sits under it.
2. lo is rewritten in E0's spec row, in `tests/skilllab/fakes_trace.py` and in the E0 branch tests under a ruler row (assumption changed by decision 47), before E0 lands.
3. The engine refuses a value below lo as today: no clamp. An out-of-band value is a settings error, not a silent change.
4. The grid order ascending (7.5 to 120) stands.

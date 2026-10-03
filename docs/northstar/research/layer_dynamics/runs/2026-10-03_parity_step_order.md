# 2026-10-03: is the tick step order a cause of the Python-against-C parity deviation? (diagnosis only)

Question (Architect Addendum 63, item C4 of `2026-10-03_parity_diagnosis.md`, which called it "inferred, not isolated"): the C decides to fire from the positions at the start of its tick, before this tick's movement; the Python fires after movement. Does that order, alone, account for the divergence that is left once the other known causes are neutralised?

Build: worktree PF-iso, branch `push/pf-iso` = `push/pp-c2` at 4b240159. All edits were made in a scratch copy of the tree (never committed, nothing in the repository changed). Instrument: `cd tests/csim && python -m parity.measure`, three scenes.

## What the step orders really are

- Python (`simulation/tactical_engine.py:44-48`): commands, targeting, movement, facing, damage. Each tick is target, move, fire.
- C (`csrc/unit.c` `om_tactical_step`, 2141-2159): the AI pass (targeting, hold or release, and the shot) runs first. Movement is lazy: `om_move_sync` in `tactical_move.c` replays the tick's movement on the first position read after the step ends (`current_tick++` is at the end of `om_ability_advance_all`). Each tick is target, fire, move.
- So the only swap is fire against move. Targeting sees the same positions in both (the end of the previous tick's movement).

## Neutralised in the scratch (all runs)

- Targeting cohort `(id - 1) % 4` at `unit.c` 2053 and 2823.
- Fixture `OM_TP_ROUTE_ACROSS_LAYERS` = 0 (`parity_c.py`).
- Python fix 1: the leash anchor is set only when the target is within attack range, and the collision pass counts a unit as stationary only with a target in range (`movement.py` `_update_attack_move_state`, `_resolve_collisions`).
- Python fix 2, backswing: tried both ways, see below.
- Extra, listed separately as set B: C5 (do not clear the steering detour in `om_command_move`, `tactical_move.c` ~2516) and R1 (a scratch hack giving the 60-speed Sniper the Strike turn rate), because those two otherwise hide group_of_8 and the facing of return_fire.

## The order change (scratch C)

1. At the fire site in `om_tac_unit_ai` (`unit.c` 2103-2107) keep the cooldown test but do not fire: record the unit in a pending list. The in-range and can-shoot tests move out of this place.
2. In `om_tactical_step`, right after `om_ability_advance_all(w)` (line 2155): force the movement replay (one `om_unit_get_pos`), call `om_tac_refresh_positions`, then for each pending unit re-check that its target is alive, in range and shootable at the NEW positions, and call `om_tac_fire`. This is the Python's `resolve_damage` after `update_movement`.

## Result (max position wu / max facing rad; first tick out of tolerance by channel)

Backswing: the stock Python locks a firing unit for 10 movement ticks (its float countdown leaves a 6.9e-17 residue) starting the tick AFTER the shot. The C locks 10 ticks starting the tick OF the shot. Moving the shot after movement makes the C's lock the Python's, with no change to the 10 ticks.

| scene | order as today (Python lock fixed to epsilon) | order changed (Python stock lock, C 10) | order changed, Python lock epsilon, C 9 |
|---|---|---|---|
| target_walks_out_of_range | 37.5 wu, 0.0004 rad; pos@52, target@63 | **0 wu, 0.0002 rad; none** | 0 wu, 0.0002 rad; none |
| attack_move_group_of_8 | 150.5 wu, 0.544 rad; pos@37 (C5 detour reset) | same, pos@37 | same, pos@37 |
| return_fire_on_the_march | 0 wu, 0.7 rad; target@165, facing@165 (R1) | same | same |
| set B (C5 and R1 also neutralised): target_walks | 37.5 wu; pos@52 | 0 wu; none | not run |
| set B: group_of_8 | 201.6 wu, 0.72 rad; pos@88, target@121 | **same, pos@88** | not run |
| set B: return_fire | 0 wu, 0.0002 rad; target@165 only | same | not run |

Other pairings tried: stock Python lock with the C unchanged and its lock at 10 gives pos@34 (15 wu), at 11 gives pos@55 (45 wu; the 34 to 55 move the diagnosis reported). The order change plus the epsilon Python plus a C lock of 10 is worse (pos@34), because then the two locks differ by one.

## Reading

- target_walks_out_of_range: the order is THE cause. With it changed the scene is exactly zero for 200 ticks and the old "backswing" divergence (C3) disappears too: C3 and C4 were one phase difference, not two causes. The C needs no 11-tick lock and the Python needs no epsilon fix; the stock Python's 10-tick lock is right once the shot comes after the move.
- attack_move_group_of_8: the order is not a cause of what is left. The first divergence sits at tick 37 (C5) and, with C5 removed, at tick 88: units 4 and 5 differ by about 0.5 wu in the collision pass next to a held target, identical with and without the change. It is the collision-order (class b) and sighting-hold group, not the step order.
- return_fire_on_the_march: positions are 0 wu either way. The facing gap is R1 (turn rate source). What stays is the recorded target one tick late (Python sets the return-fire target in the same step as the hit; the C consumes `last_attacker` at the next AI pass). No position effect: both pickets hold at the same movement tick. Not fixed by the order change; a frame-label lag.

## Verdict

Partly. Yes for the scene the order governs: target_walks goes from first divergence at tick 52 and 37.5 wu to none and 0 wu. No for group_of_8 and return_fire, whose remaining deviation has other causes (C5, collision order, R1, one-tick target label).

## The exact C change

`csrc/unit.c`: (a) at 2103-2107 replace the immediate `om_tac_fire` by appending the unit id to a pending list when the cooldown condition holds (`cooldown >= interval - OM_TIE_EPSILON || (pursue && !u->fired)`); (b) in `om_tactical_step` after line 2155 (`om_ability_advance_all`) run the movement replay, `om_tac_refresh_positions(w, st)`, then for each pending unit fire if its target is alive, `om_tac_in_range` and `om_combat_can_shoot` at the new positions. Order of the rest (backswing advance before the shot) stays as it is, so the lock is 10 ticks from the next movement. Needs a ruling: it changes every golden with a combat in it.

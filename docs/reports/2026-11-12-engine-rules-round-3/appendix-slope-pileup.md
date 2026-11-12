# Slope pile-up and the stall jump: X1 diagnosis (main 7ba38983, seed 1)

Everything below was measured on scratch builds of a copy of `csrc/` (`x1/scratch`, `x1/scratch2`, env-switched, default behaviour byte-identical: the landed build reproduces the sweep hash of L-0084 off exactly, `8cac1c06...`). Nothing in the worktree was edited. Scripts: `x1/runv.py` (one fight, all measures), `x1/trace.py` (per-tick engine state), C logging in `scratch2/csrc/tactical_move.c` and `unit.c` (`OM_X1_LOG`). Raw outputs: `x1/batch1.out` .. `batch6.out`, `x1/tmp/l84_all.log`.

## HYPOTHESIS

The two symptoms have different causes, and neither is the one suspected in full.

1. **I13s / I13 / I23 on L-0084, L-0063, L-0062, L-0045 (proven by log and by the variant runs).** `om_move_slope_clamp` is the cause, but through the layer flip, not through ordinary pushes. Units of different layers do not collide (`om_move_collide_pair`), so a walker that crosses a slope's midline lands inside units of the new layer it overlapped for free a tick earlier. The collision pass wants to undo that whole overlap in one tick (6 to 13 wu on a unit whose step is 2.3); the clamp refuses (cuts the displacement back to pace x 1.1 + 1.0), so the overlap stays, the push-back still carries the unit under the midline, it flips back, walks forward again and flips again: a 2 to 4 tick ping-pong at the midline of every unit that climbs. In L-0084 off the clamp cuts 6,464 of the 8,190 layer-change unit-ticks (79%, 48,734 wu in all, mean 7.5 wu) and 1,879 of 120,679 other unit-ticks of units that stand on a slope (10,260 wu; so the "also cuts ordinary pushes" suspicion is true but is 17% of the cut). Layer flips go from 3,641 (clamp off) to 8,182, I23 from 2,672 to 6,785, I13s from 538 to 3,420. The clamp and the layer-change continuity (F8) are in direct conflict as long as the overlap is created at the flip.
2. **I29 on the plain "tiered" layouts (L-0028, 0006, 0005, 0004, 0025, 0081; 80% of the growth) is not the slope and not the clamp (proven by log).** The clamp switched off changes none of them (L-0005, 6, 25, 28, 4, 43 identical in all three clamp modes). The cause is F9 (`csrc/unit.c`, commit a5f4084c, the move away from unseen fire). A unit hit by unseen fire gets `om_unit_clear_orders` + `om_tac_start_flinch(kind 2/3)` with `am_gid = 0` and `order_x/y` = the original attack-move point, so `om_tac_pursuing()` (issued != order) is true; the next `om_tactical_ai_tick` sees "pursuing, no destination" and calls `om_tac_end_pursuit`, which commands a move to `order_x/y` WHILE the flinch (a unit.c step away from the attacker, same speed) is still running. The two steps cancel exactly. Log, L-0081 on, unit 13 (kind 2): `X1U flinch start u=13 kind=2` then `X1U end_pursuit u=13 ... flinching=2`; per tick the move module walks 4.00 wu toward (1882,1832), the position at the next tick start is 3.98 wu back. For an arrived group member (kind 3, L-0005 unit 48, a Bombard at its slot): `flinch start u=48 kind=3`, `end_pursuit ... flinching=3` the same tick; it walks 2.5 wu a tick toward the order point 300 wu away and is pushed 4.4 wu back each tick by the stationary comrades of its own formation, forever (`own=2.50 push=4.44`, positions 2066.9/2067.0 for 60+ ticks). R-087-01 says the arrived one "holds where the move away ends and does not walk back". The stall then lengthens fights from wipe to silence/cap, and I29 counts every extra tick: L-0028 on 3,240 -> 12,000 ticks, 80,524 -> 312,016 unit-ticks.
3. **Residual (not the slope, not F9; named, not solved).** L-0043 off I29 7,405 -> 35,702: a Raider walks 6.5 wu a tick and is pushed back 6.5 (`own=6.50 push=6.5x`) by stationary friends in a 30 wu packing. A walker cannot get past stationary comrades. Present before Round 2 at a fifth of the size; fights are longer now. L-0004 I29 stays ~6-9k after the fix (fight runs to the 12,000 cap); not traced.

## EVIDENCE

### Sweep, per layout (v4 = Round 1, v5 = Round 2; `x1/percount.py`)

| layout, sight | orders | I29 v4 -> v5 | I13 v4 -> v5 | I13s v4 -> v5 | ticks v4 -> v5, end |
|---|---|---|---|---|---|
| L-0028 on / control | both_same_point | 733 -> 52,106 / 6,120 -> 54,202 | 0 | 0 | 3240 -> 12000 silence->cap |
| L-0081 on / control | both_same_point | 0 -> 29,134 each | 169 -> 29,134 (I13 6,053) | 0 | 785 -> 2560 wipe->silence |
| L-0006 on / control | both_same_point | 2,766 -> 20,334 / 3,279 -> 35,658 | 0 | 0 | 3131 -> 5560 |
| L-0043 off | both_same_point | 7,405 -> 35,702 | | | 1565 -> 3396 |
| L-0005 on / control | both_same_point | 1,775 -> 15,238 / 1,893 -> 16,018 | | | 2456 -> 3860 |
| L-0084 control / off / on | hold:A | 0 -> 0 | 488/1381/493 -> 11,086/13,903/3,628 | 30/198/54 -> 4,165/3,420/738 | |
| L-0063 on = control | hold:A | 0 -> 0 | 71 -> 12,251 | 42 -> 2,904 | 782 -> 1300 |
| L-0062 on = control | hold:A | 0 -> 41 | 19 -> 5,103 | 4 -> 1,526 | |
| L-0045 off | both_same_point | 0 -> 0 | 605 -> 2,718 | 0 -> 1,213 | |

By feature: 197,775 of the 299,938 I29 growth is on layouts with NO feature (plain tiered), 58,351 trap+vantage, 31,200 flank_route. 26,255 + 39,028 of the 93,975 I13 growth, and 17,163 of the 19,442 I13s growth, are hold:A slope/vantage layouts.

### The ping-pong, L-0084 off, units 71 and 76 (`OM_X1_LOG`, per tick: layer start->end, own step, collision push, wu the clamp cut)

```
t=419 u=71 L=0->0 own=2.27 push=0.34 clampcut=0.00
t=420 u=71 L=0->1 own=2.27 push=7.68 clampcut=0.01 end=(2194.0,2037.5)   crossed the midline (x ~2199), pushed back 5.4 wu
t=421 u=71 L=1->0 own=2.27 push=6.35 clampcut=3.00                         flips back
t=423 u=71 L=1->0 own=2.27 push=9.54 clampcut=6.19
t=424 u=71 L=0->1 own=2.27 push=7.47 clampcut=0.00
t=425 u=71 L=1->0 own=2.27 push=11.93 clampcut=8.59
t=427 u=76 L=0->0 own=2.27 push=3.20     the first I13s of the fight (u71 and u76, 19.6 wu)
```

### Variants (scratch build, seed 1; `x1/runv.py`; lc-jumps = layer-change unit-ticks over speed x max(1, down mult)/20 + 1.3, the measure of `test_engine_rules_f8_continuity.py`; all-jumps = same, any unit)

Variants: LANDED; NOCLAMP (clamp returns at once); LCONLY (clamp only a unit that changed layer this tick, true start layer kept in a new array because `ms->start_layer` is overwritten with the post-flip layer at `om_move_collision_pass_internal`, line ~1967); XL (see SOLUTION) with the landed clamp.

| fight | variant | ticks, end, alive | I29 | I13 | I13s | I23 | layer changes | lc-jumps (worst wu) | all-jumps |
|---|---|---|---|---|---|---|---|---|---|
| L-0084 off | LANDED | 1977 wipe [12,0] | 0 | 13,903 | 3,420 | 6,785 | 8,182 | 0 | 0 |
| | NOCLAMP | 1667 wipe [0,16] | 0 | 3,179 | 538 | 2,672 | 3,641 | 2,446 (77.0) | 3,910 |
| | LCONLY | 1921 wipe [0,10] | 0 | 12,590 | 2,898 | 6,029 | 7,158 | 0 | 1,187 |
| | XL | 1978 wipe [24,0] | 11,426 | 608 | 0 | 21 | 98 | 0 | 0 |
| L-0084 on | LANDED | 3718 wipe [37,0] | 0 | 3,628 | 738 | 611 | 816 | 0 | 4 |
| | NOCLAMP | 2200 wipe [34,0] | 1 | 1,829 | 64 | 298 | 597 | 417 (52.0) | 2,398 |
| | LCONLY | 2208 wipe [34,0] | 1 | 3,849 | 676 | 1,176 | 1,455 | 1 | 1,903 |
| | XL | 2397 wipe [37,0] | 668 | 2,630 | 167 | 5 | 46 | 0 | 1 |
| L-0084 control | LANDED | 2200 silence [24,1] | 0 | 11,086 | 4,165 | 4,548 | 5,572 | 0 | 1 |
| | NOCLAMP | 2711 wipe [30,0] | 0 | 2,060 | 130 | 402 | 710 | 449 (57.7) | 2,106 |
| | LCONLY | 2892 wipe [31,0] | 0 | 3,884 | 750 | 1,190 | 1,514 | 0 | 1,526 |
| | XL | 1911 wipe [34,0] | 4,374 | 1,587 | 12 | 5 | 62 | 0 | 0 |
| L-0063 on | LANDED | 1300 wipe [0,38] | 0 | 12,251 | 2,904 | 6,724 | 8,378 | 0 | 0 |
| | NOCLAMP | 1032 wipe [0,43] | 419 | 817 | 90 | 2,045 | 2,905 | 1,810 (88.3) | 2,608 |
| | LCONLY | 897 wipe [0,44] | 0 | 3,625 | 904 | 1,921 | 2,732 | 0 | 827 |
| | XL | 1634 wipe [0,37] | 16,410 | 1,420 | 0 | 175 | 381 | 0 | 0 |
| L-0062 on | LANDED | 1584 wipe [0,24] | 41 | 5,103 | 1,526 | 2,781 | 3,942 | 1 | 5 |
| | NOCLAMP | 1644 wipe [0,23] | 11 | 267 | 8 | 1,904 | 2,828 | 1,143 (65.8) | 1,543 |
| | LCONLY | 1474 wipe [0,22] | 0 | 2,550 | 648 | 2,303 | 3,038 | 0 | 502 |
| | XL | 2076 wipe [0,21] | 7,461 | 175 | 0 | 189 | 412 | 0 | 0 |
| L-0045 off | LANDED | 943 wipe [0,41] | 0 | 2,718 | 1,213 | 1,298 | 1,908 | 0 | 0 |
| | NOCLAMP | 945 wipe [0,41] | 0 | 505 | 0 | 406 | 840 | 436 (26.2) | 578 |
| | LCONLY | 943 wipe [0,39] | 0 | 1,826 | 743 | 1,309 | 1,838 | 0 | 56 |
| | XL | 1003 wipe [0,42] | 1,746 | 1,185 | 4 | 22 | 82 | 0 | 0 |
| L-0083 on | LANDED / NOCLAMP / LCONLY / XL | 2839 / 2052 / 2001 / 2776 | 5,906 / 996 / 996 / 11,157 | 1,422 / 1,011 / 846 / 922 | 8 / 8 / 8 / 14 | | | 0 / 1 / 0 / 0 | |
| L-0061 on | LANDED / XL | 2234 / 2218 | 0 / 0 | 232 / 65 | 0 / 0 | 0 / 4 | | 0 / 0 | |

Refuted: "the clamp only cuts the layer-changer, so cutting only on the layer-change tick (LCONLY) is the fix": it leaves I13s at 650 to 2,900 because the cut is the flip tick. "Switch the clamp off": brings the jump back (up to 88 wu, 1,810 lc-jumps on L-0063). The clamp is not the cause of the plain-layout I29: identical numbers in all clamp modes for L-0004/5/6/25/28/43.

### I29 fix test (scratch, `OM_X1_F9B`: skip the "pursuit ended, re-issue the move" check in `om_tactical_ai_tick` while `u->flinching`)

| fight | landed | F9B | note |
|---|---|---|---|
| L-0081 on | 29,134 (2560 silence) | 0 (831 wipe) | |
| L-0028 on | 52,106 (12000 cap) | 889 (3740 silence) | |
| L-0006 on | 20,334 | 1,730 | |
| L-0005 on | 15,238 | 3,078 | |
| L-0025 on | 4,731 | 731 | |
| L-0004 on | 5,441 | 6,934 | fight now runs to the cap (12000); residual, untraced |
| L-0043 off | 35,702 | 35,702 | other cause (item 3) |

Sum over these seven: 162,686 -> 49,064. The `control` twins of L-0028/0006/0005/0081 (another 135k of the growth) were not run; they track the `on` fights. Setting `order_x/y = issued_x/y` for kind 3 as well (`OM_X1_F9`) gave mixed results (L-0005 2,242, L-0006 2,569, L-0028 21,540) and is left as an open question for the implementer (R-087-01 says the arrived unit holds; the code has it walk back once the flinch ends).

## SOLUTION

**I29 (small, supported by the table above).** `om_tactical_ai_tick` in `csrc/unit.c`: do not end the pursuit while the unit flinches (`if (u->target_id == 0 && !u->flinching && om_tac_pursuing(w, u))`). One condition. Rule R-087-01 (move 200 wu away and stop; an arrived attack-mover holds). Proof: `tests/skilllab/arena/test_engine_rules_f9_unseen_fire.py` plus `tests/csim/test_E11_R087_01_unseen_attacker_moves_the_unit.py` pass today because they look at the first step; add a csim scene where an attack-moving group member (arrived, and not arrived) is hit by unseen fire and a test that after the hit it ends >= 150 wu from where it was hit within 100 ticks (today it ends 13 wu away, positions frozen), and a sweep gate on I29 over L-0028/0006/0005/0081 `on`.

**Slope pile-up (a rule decision is needed first).** No edit inside `om_move_slope_clamp` fixes it: the only way to keep the flip-tick displacement within pace + 1 AND keep units apart is for the overlap not to appear at the flip. The variant that does, XL, is in `om_move_collide_pair` (`csrc/tactical_move.c`, the gate `ms->start_layer[ia] != ms->start_layer[ib]`): let the pair collide anyway when the layers differ by exactly 1 and both units stand on a slope (`om_terrain_slope_at` at both positions), and keep the clamp as it is. Numbers (table above): I13s 3,420 -> 0, 3,628/738 -> 167 (L-0084 on), 2,904 -> 0 (L-0063), 1,526 -> 0 (L-0062), 1,213 -> 4 (L-0045); I23 6,785 -> 21, 6,724 -> 175; lc-jumps and all-jumps 0 on all six; winner unchanged on every fight; ticks within +-35% (L-0063 1300 -> 1634, L-0062 1584 -> 2076). Cost, stated plainly: units queue behind the fighters on the ribbon, so I29 on those layouts rises (L-0084 off 0 -> 11,426, L-0063 0 -> 16,410, L-0062 41 -> 7,461, L-0083 5,906 -> 11,157): the same "walker against stationary comrades" wedge as item 3, now with a real cause (a unit standing on a slope blocks the one behind it). And it changes the words of R-097-05 ("two units on the same layer") and E-01 R-004-06/08: a unit on a slope would collide with units on the adjacent layer's side of the same slope. That is a rule meaning, so Westley's (or an Architect decision logged for veto), not a builder's. Proof once ruled: `tests/csim/test_E01_R004_layer_change_is_continuous.py` (green already: lone walker and 8-friend scene) plus a new csim scene "a walker on a slope never ends a tick closer than 20 wu to a unit of the layer it just entered" and `test_engine_rules_f8_continuity.py` HILLS (all four stay 0), plus an I13s/I23 bound on L-0084/L-0063 `on` (suggest I13s = 0 and I23 under 200, thresholds Westley's).

If the rule is not to change, the honest alternative is to loosen F8 on the flip tick (the clamp the other way: accept the one-tick resolution jump but forbid the flicker), which is the pre-Round-2 behaviour minus nothing: NOCLAMP above shows its price (jump 26 to 88 wu on 436 to 2,446 unit-ticks per fight).

## Open / not done

- `control` twins and the seed-2 passes were not rerun; `L-0004`'s remaining I29 and L-0043 off are untraced.
- The kind-3 (arrived) order mismatch is real in the code but its fix gave mixed numbers; needs its own test.
- Flicker (I23) is rule-legal by R-004-08 ("changed twice"); it is a symptom here, not a violation.

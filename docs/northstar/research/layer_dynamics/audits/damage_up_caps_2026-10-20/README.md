# damage_up caps: cap trace, 2026-10-20

The skill lab's damage_up sweep under `orders_per_unit False` ended in 8 caps (fights that hit the 12000-tick limit with both sides alive): 4 on the play `s3_layer_above` and 4 on `naive_defender_play_layer`, all on layout 192, knob `OM_TP_DAMAGE_UP_1`.

| knob | heads | survivors |
|---|---|---|
| 0.75 | 24 | 2, 8 |
| 0.5 | 24 | 2, 7 |
| 0.25 | 23 | 4, 4 |
| 0.25 | 40 | 1, 19 |

## What the trace found

There are two causes.

1. Target acquisition is range-only (`csrc/unit.c:2178-2183`, A199 comment at `:2187-2189`; `csrc/fog.c:687` `om_unit_acquire_target` is not wired). A unit that sees an enemy outside its attack range never walks toward it. The fix is the sight-engagement engine piece (VG-E-sightengage), on the game side, after the lab landing and E7.
2. The lab's L8 silence counter (`_Reengage` in `scripts/skilllab/fight.py`) is reset forever by one unit, u31. It holds a destination, (754, 2042), that it cannot reach because idle bodies block it, so it shuttles in a loop of about 70 wu with a period of about 40 ticks. Any movement resets the counter, so re-engage never fired in the capped fight. The fix is decision 49 of `docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md`.

Forced by hand (attack-move of every side-1 unit onto the centroid of the visible enemies), the capped fight ends in 178 ticks, so the fight is winnable once units are told to go.

A separate game-side finding came out of the same trace: a unit holding an unreachable destination blocked by idle bodies never gives up (`FINDING-blocked-destination-never-times-out`). The suspected site is the give-up pass in `csrc/unit.c`. Reproduction: sweep damage_up, knob 0.75, heads 24, layout 192, swap False, seed 1 (second fight of the cell), unit u31.

## The scripts

- `trace.py HEADS KNOB [CASE]`: runs the six fights (swap False and True, seeds 0 to 2) for one knob and headcount, and for every cap prints the unit table (type, layer, position, destination, range, reach), what each side sees, per-pair engagement codes, and the re-engage log, then the movement over the next 300 ticks. CASE (0 to 5) runs one fight.
- `trace2.py`: the 0.75 / 24 / seed 1 fight, printing the silence, armed and count state every 500 ticks and the composed firing geometry per unit pair at the cap.
- `trace3.py`: the same fight; counts which units reset the counter after tick 4000, samples u31's path, then at the cap attack-moves side 1 onto the centroid of the visible enemies and steps until one side is dead (178 ticks).

## Rerun

The scripts were written against the cap-trace worktree and insert it on `sys.path` in their second line (`/home/westopoli/Projects/ouroboros-manifold/../om-push/wt/labrev2-captrace3`). To rerun:

1. Make a worktree at the flip branch tip: `git worktree add ~/Projects/om-push/wt/labrev2-captrace3 05d1e5c4` (origin/push/labrev2-flip at the time of the trace), or edit the `sys.path.insert` line to point at any checkout that has `scripts/skilllab` with `_Reengage` and `REENGAGE_MOVED_WU`.
2. Run from the repository root of that worktree, so `csrc/` is found for the engine's build of `libouroboros.so`, with the venv python and the root on the path:
   `cd ~/Projects/om-push/wt/labrev2-captrace3 && PYTHONPATH=. /home/westopoli/Projects/agora/.venv/bin/python <path to>/trace3.py`
   (`trace.py` takes `24 0.75` as its two arguments; `trace2.py` and `trace3.py` take none.)

The scripts print to stdout only. Under decision 49's corrected L8 the capped fight is expected to end, and the traces then change; keep these as the record of the broken behaviour.

# Attack-move idle cap, trace of 2026-10-19

Evidence for decision 28 of `docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md` and the ledger row `FINDING-attackmove-idle-cap` in `docs/northstar/plans/push_ledger_2026-09-22.md`. The scripts here are the overseer's scratch scripts, committed as they were run; they are evidence, not lab code.

## Finding

An attack-moving unit whose route ends short of its recorded point goes idle: no destination, the attack-move order still held, firing only at what is already in range, with the enemy standing just outside range. Nothing in the engine moves it again, so the fight runs to the tick cap. Every cap seen in the rev 2 smoke, the damage-up control, the objective scene and the mirror control has this shape. There are two ways in.

1. The R-087-06 return-fire redirect (the `last_attacker` branch of the unit step in `csrc/unit.c`, near line 2095: it sets `order_x`/`order_y` to the attacker's position) overwrote the ordered point. The unit resumed toward the attacker, the attacker died, and the unit idled where it stood.
2. The R-099-05 give-up pass in `csrc/tactical_move.c` ends a group attack-move where the unit stands, which is the same state as an arrival. An arrived unit does not close on a visible enemy outside its range, and no rule in the bible makes an idle unit chase. The engine is per rules here.

What was traced:

- 4 damage-up controls capped, plus the smoke cap `s3_layer_above` on layout 192, seed 2, swapped, 5 v 1 at 12000 ticks, first contact at tick 315.
- The objective scene at 2800 wu, seed 0, capped with survivors (1, 2); the mirror control capped with survivors (1, 1), both under group orders (`orders_per_unit=False`).
- Counterfactual: re-issuing the attack-move to the original point at the cap ends every capped fight, in 2 to 527 ticks.

## Ruling

Decision 28 (Architect, 2026-10-19). Point 1 is an engine fix under the E1 row (follow-on E1b): the redirect is one engagement and the unit resumes toward its original point. Point 2 is a lab change (L8): after `REENGAGE_SILENCE_TICKS` of silence on a side (DRAFT 40, Westley's number) while an enemy is visible, every idle attack-move unit on that side is attack-moved onto the enemy centroid; guard-stance holders never. A cap after a re-engage stays a defect (decision 23).

## The scripts and how to rerun them

All of them import `scripts.skilllab`, so run them from the repository root with the scratch directory holding these files on `PYTHONPATH`, using `/home/westopoli/Projects/agora/.venv/bin/python`. The paths to `libdbg.so` and the scratch directory are hard-coded to the 2026-10-19 session scratchpad (`/tmp/claude-1000/-home-westopoli-Projects-ouroboros-manifold/6595578b-476b-499c-ae9d-903b2a7b43bd/scratchpad/`); change them to rerun elsewhere.

Two things are not committed:

- `libdbg.so`, built from the scratchpad copy `csrc_dbg/` of `csrc/`. It is the engine tree of the traced branch (E1 in, so `om_tac_am_group_done` is gone) with `fprintf(stderr, ...)` lines added in `tactical_move.c` at every place `has_dest` is cleared (`HASDEST0 site#N`) and at the give-up pass (`GIVEUP`). The Engine class takes a library path, so a rerun needs the same instrumentation rebuilt from the then-current `csrc/`.
- `caps_damage_up.pkl`, the pickled list of capped jobs `((setup, seed, swap), outcome, survivors, ticks)` from the damage-up run, read by `pk.py`, `pkt.py` and `cf.py` from the current directory.

| Script | What it does | Run |
|---|---|---|
| `capprobe.py` | Helpers the others import: `survivors`, `describe` (per survivor type, layer, position, hp, target, destination, range, reach; per pair `can_engage`, distance, `can_see`, `can_shoot`), and `run`, which runs a fight and describes the state at the cap, then steps 300 more ticks to show nobody moves. | imported |
| `pk.py` | Describes one 12000-tick cap from the pickle. | `pk.py N [dbg]`, N the index among the 12000-tick caps; `dbg` uses `libdbg.so` and prints a TICK line per step to stderr |
| `pkt.py` | Traces one unit's destination across a cap from the pickle with `libdbg.so`; prints a WATCH line whenever the destination changes. | `pkt.py JOB UNIT`, JOB the pickle index (0, 25 and 26 were traced), UNIT the unit id to watch |
| `cf.py` | Counterfactual on pickle jobs 0, 25 and 26: at the cap, re-issue the attack-move to the recorded point for the attacking faction and step up to 6000 ticks, printing the survivors and the ticks it took. | `cf.py` |
| `cf3.py` | The same counterfactual for the objective scene at 2800 wu (seed 0) and the mirror control, both under group orders, re-issuing per unit to (0, 0). | `cf3.py` |
| `case3d.py` | Traces the destination of listed units in the objective scene or the mirror control under group orders with `libdbg.so`. | `case3d.py obj\|mirror SWAP(0\|1) SEED UNIT,UNIT,...` |

`case3d.py` as saved starts with `from probe import *`, but `probe.py` in the scratchpad was overwritten by a layout probe; the helpers it needs (`F`, `plays`, `scenes`, `Engine`) come from `capprobe.py`, so change that line to `from capprobe import *`.

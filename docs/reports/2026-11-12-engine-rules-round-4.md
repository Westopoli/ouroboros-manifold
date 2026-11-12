# Engine rule fixes, Round 4: idle units step aside for their own side (2026-11-12)

Follows `2026-11-12-engine-rules-round-3.md`. Same method: traced by log, tests written by one agent, built by another, verified by a third.

## Fixed

Rule R-097-10, as rewritten on 2026-10-23 from Westley's words of 2026-10-22 ("Idle own units are not walls: a moving unit passes through idle units of its own side, which step aside"), was never built: the engine gave the mover the whole collision push, so a walker with a destination was pushed back to the same spot every tick by an idle unit of its own side and stood there for the rest of the fight. Now an idle unit takes the full displacement from a mover of its own side. Idle means: standing, holding no target, not a guard, not in a move away from unseen fire. An idle enemy does not step aside; a unit that is firing does not; a guard does not.

## Measured

Suites on the landed tip: `tests/csim`, `tests/skilllab`, `tests/qa`, `tests/method` show no failure outside the baselines. The build was broken four ways on purpose (no yield, yield to enemies, a firing unit treated as idle, a guard treated as idle) and each turned its tests red. The checker reports nothing on the 160 stage 4 fight files, nor on L-0084, L-0081, L-0050 or a terrain-less blob.

Sweep of 199 fights, a walker with a destination and no target standing still (unit-ticks): 73,402 on 2026-11-07; 95,380 after Round 1; 395,318 after Round 2; 146,664 after Round 3; 12,353 now.

Stage 4 (20 seeds each, identical): cover, red wins with 3 left; vantage, blue wins with 18 left; trap L-0080, red wins with 26 left; trap L-0083, red wins with 40 left.

How the 199 fights end: 169 by wipe (unchanged), 26 in a stand-off (23 before), 4 at the time cap (7 before). Nine fights changed how they end, in both directions.

## Open

The open list of the Round 3 report stands, less the stalled-walker item. New or changed:

- **L-0028 still ends in a stand-off** (seed 1, sight on: silence at tick 5,620 with 12 against 11 alive) and the checker reports on it: seven lock swaps and one step of 11.44 wu.
  - The step: a unit ending a walk with no destination and starting a walk to a new destination takes both steps on one tick. A small engine defect, not traced further.
  - A lock swap (tick 1957, unit 10): a unit walking toward its target at about 300 wu fires at another enemy that came to 62 wu, while the first target was alive and seen. Either return fire replacing a held lock or a lock broken while moving. Not traced.
- **L-0045 reports two lock swaps** (tick 1134, units 31 and 39): the target was unseen at the end of tick 1133 and seen again at tick 1134; the unit took another target on that tick. By the rule the lock ended when sight was lost, so this reads as a legal pick that the checker reports because the old target reappeared the same tick. A checker edge, not traced further.
- **One unit-tick of healing with no Warden near** in the sweep, where it had been zero. Not traced.
- **Same-layer jumps in the sweep rose from 3 to 17.** Likely an idle unit taking a full push (12.6 wu measured in a test). Not confirmed.
- **Draft readings in this round:** a guard is not idle (so a unit ordered onto a guard's post is held 30 wu away); a pushed idle unit may move up to 30 wu in a tick in the one older test that capped it at 12 (`DRAFT-teleport-pushed`, Westley's number).
- **No rule says** what an idle unit does when it has nowhere to step (an obstacle behind it, or a crowd of idle units).
- **Lone movers never give up** when held by an enemy or a firing unit (only grouped movers do). Deferred since 2026-10-23 behind a save-format change.
- Two parity scenes no longer compare with the Python reference; they are recorded as deliberate differences under R-097-10 and assert what the engine now does.

# 2026-10-02: first look through the harness (controls, before any batch)

Instrument: `scripts/skilllab/` on branch `swarm/skilllab-harness/integration`, real C sim, arm64 Mac. 435 of 440 harness tests green; the five red ones are the mirror and planted-advantage controls below.

## Mirror, 16 Vanguards against 16

- 120 fights (60 seeds, both spawn orders): mean margin +0.03 and -0.02 by order. The mirror is even.
- One fight swings about 0.17 either way on the position shifts alone (each unit nudged up to 10 wu per axis).
- 20 fights therefore land within about 0.04 of the truth by luck. The control's tolerance of 0.05 was too tight for 20 fights.
- Ruling (Westley, 2026-10-02): keep 20 fights, tolerance 0.10.
- No first-spawner edge is visible once positions are shifted. The inventory's claim that the first-spawned side shoots first does not show as an advantage.

## Planted reach advantage: 1.2x reach made the side worse

- Identical 16 beat 15. 16 with 1.2x reach beat 14. Margin at 16 v 16 about -0.34 for any factor from 1.1 to 2.0, spread 0.03.
- Factor 1.0 through the same custom-type path equals identical exactly, so the path adds nothing by itself.
- What the fight does: each long-reach unit halts the moment an enemy is in its range, so that side stops strung out front to back. The enemy walks on until in its own range and stops in a flat row. Every enemy unit targets the nearest unit, which is the long side's front few; the long side's shots are spread over many targets. At tick 700 total health is equal (5230 against 5258) but units alive are 11 against 15.
- Westley, 2026-10-02: "the issue isn't in the numbers, it's how the units walk towards each other. A real battle isn't going to be a line feeding into each other, it's going to be a blob if they're mediocre players, or a spread out line if they're skilled players. Record that to the experiment, position matters when measuring numbers and we shoudln't just be lining units up like that."

## What the engine does on approach (read from `csrc/unit.c`, `csrc/tactical_move.c`)

- A unit under a move order steers: it probes 40 wu ahead and sweeps left and right around a blocking unit (R-097-03).
- An attack-moving unit that sees an enemy beyond its range steps straight at the nearest one (R-087-04), by a direct position step that does not use the steering probe. It does not walk around its own side.
- A unit stops as soon as any enemy is within its range (R-087-03, R-087-05) and does not move again to let units behind it into the fight.
- Result: two armies sent at each other end as two flat rows at exactly weapon range, whatever shape they started in. In the equal-range mirror all 16 units of each side ended within 5 wu of the same x.

## Follows

- A starting formation does not survive the walk, so a number measured from two armies walked into each other describes the walk. Setups place units where a player of that skill would have them at contact.
- Fire concentrated on a few units beat fire spread over many with every unit firing on both sides. The firing count alone did not predict this fight.

# E-02 — Region Fields, Composites, and Drift

## Definition-completeness gate (run 2026-09-10)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Yes, 9 stories, 31 rules, all numbers from `algorithms.md` ALG-01 through ALG-10. |
| Every input listed with range and rejection behavior | Yes, see Inputs. No player inputs; every input is sim-internal. |
| Every output listed with where it is observable | Yes, see Outputs. |
| Implied-but-unstated behavior turned into flags | 3 new flags, Q-013-01, Q-015-01, Q-019-01. |
| Every visible-surface story has a reference | Not applicable. No story in this epic has its own visible surface; the world view that shows region state is E-16. |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: passed (2026-09-13). Ready (2026-09-14).** The 3 flags (Q-013-01, Q-015-01, Q-019-01) are answered and folded below. Stage 3 e2e is authored (`docs/northstar/e2e/E-02.md`); scale gates confirmed by Westley. All Definition-of-Ready items met; stories S-012 … S-020 are Ready for Stage 5 tests.

## Purpose

Every region in the galaxy carries four numbers that say how it is doing: military strength, economic output, factional tension, and population. Two derived numbers, stability and capacity, summarize them for everything that makes big decisions. Every tick, slow forces move the four numbers a little: armies cost money, people make money, hardship breeds unrest, unrest hurts production, prosperity grows population. Under those forces a healthy region hums along, a stressed region slides, and a region at the bottom spirals unless someone outside helps it.

This is the ground the whole simulation stands on. Events, factions, missions, and the chronicle all read these numbers. The player never edits them directly; missions do. The equations are retained verbatim from the Python sim (`algorithms.md`), and the C rewrite must reproduce them to the bit.

## Obviously working in 60 seconds

The technical end-state: what a fixed-seed run proves when this epic is done.

Run one region alone for 300 ticks from population 60, economy 66, military 42, tension 18 with a fixed seed. Economy climbs toward the mid-50s then oscillates with a 15-tick period; tension settles into a low equilibrium with an 18-tick wobble; military decays a little then recruits back and holds under 90; population creeps up. Run it again with the same seed: every number identical to the last decimal. Cut economy to 9 by hand: tension climbs, population falls, and it does not recover on its own.

## Visual end-state

None direct. This epic produces no pixels of its own; region fields and composites are numbers in the strategic snapshot. The player sees them through the E-16 world view: a system's condition surfaces in the faction data panel and the hover tooltip (stable versus straining), and its drift over time surfaces as chronicle fragments in E-09 ("the border world's economy has not recovered since the blockade"). What "done" looks like on screen is therefore E-16's and E-09's target, not this epic's; this epic's finished picture is the trajectory above, read from a T1 trace. When E-16 is built, its visual end-state names how a straining region must read at a glance so a player never has to open a number to know a world is in trouble.

## Stories

### S-012 — Every region has four fields and two composites
As a commander reading the galaxy, I want each region's condition to be four plain numbers and two summaries, so that I can tell a military problem from a political one at a glance.

Rules
- R-012-01  Given any inhabited region at any tick, When its state is read, Then it has exactly military, economy, tension, population, each in [0, 100], and stability and capacity, each rounded to 2 decimals.
- R-012-02  Given military 40, tension 20, population 60, When stability is computed, Then it is 40·0.40 + 80·0.35 + 60·0.25 = 59.00.
- R-012-03  Given military 8, tension 20, population 60, When stability is computed, Then it is (8·0.40 + 80·0.35 + 60·0.25) · 0.70 = 32.34.
- R-012-04  Given military 8, tension 20, population 15, When stability is computed, Then both penalties apply: (3.2 + 28 + 3.75) · 0.70 · 0.75 = 18.35.
- R-012-05  Given economy 60, population 50, military 30, When capacity is computed, Then it is 60·0.50 + 50·0.35 + 30·0.15 = 52.00.
- R-012-06  Given economy 15, population 10, military 30, When capacity is computed, Then it is (7.5 + 3.5 + 4.5) · 0.65 · 0.70 = 7.05.
- R-012-07  Given an empty-tier region, When its state is read, Then all four fields are 0, composites are 0, and no drift is ever applied to it.

Inputs: the four fields.
Outputs: composites, recomputed after every field change, in the region entry of the strategic snapshot.
Open flags: none.

### S-013 — Armies cost money and grow in peace
As a commander, I want a region's military to decay when its economy cannot feed it and to recruit when times are good, so that garrisons reflect the wealth behind them.

Rules
- R-013-01  Given military 50 and economy 0, When one tick of drift runs with recruitment disabled, Then Δmilitary = −50 · 0.006 · 1 = −0.300.
- R-013-02  Given military 50 and economy 100, When one tick runs with recruitment disabled, Then decay is exactly 0.
- R-013-03  Given military 50, economy 60, population 50, tension 20, When one tick of recruitment runs, Then Δmilitary_recruit = (0.1 · 0.5 + 12 · 0.6 · 0.5 · 0.8^0.3) · (1 − 50/90), within 1e-3 of 1.5186.
- R-013-04  Given economy 20.0 exactly, When recruitment runs, Then the economy-scaled term is 0 (threshold is strictly greater than 20).
- R-013-05  Given military 90 or above, When recruitment runs, Then recruitment is 0; drift alone never pushes military past 90.
- R-013-06  Given a conqueror faction owns the region, When drift runs, Then an extra +0.05 · headroom is added to military (faction modifier).

Inputs: military, economy, population, tension, faction modifiers.
Outputs: Δmilitary in the drift log; military field.
Open flags: none. Q-013-01 resolved (a): the bible's "low military near hostile factions accelerates all negative trends" is a stale sentence with no formula, deleted; the attack resolver (E-05) already punishes low military. No rule.

### S-014 — People make money, unrest and overreach cost it
As a commander, I want a region's economy to grow with its population, shrink under tension, and fall back when it outruns what its people can sustain, so that prosperity has a shape.

Rules
- R-014-01  Given population 50, tension 20, economy 30, When one tick runs with oscillation and adjacency off, Then Δeconomy = 2.0·0.5 − 0.2·0.40 − 0 = 0.920.
- R-014-02  Given population 50 and economy 60 (capacity 42.5), When one tick runs, Then overcapacity decay = 15 · (60 − 42.5)/100 = 2.625 and Δeconomy = 1.0 − drag − 2.625.
- R-014-03  Given economy exactly at capacity, When one tick runs, Then overcapacity decay is 0.
- R-014-04  Given any drift result that would take economy below 8.0, When it is applied, Then economy is 8.0.

Inputs: population, tension trend, economy trend.
Outputs: Δeconomy in the drift log; economy field.
Open flags: none.

### S-015 — Friendly neighbors make you richer
As a commander, I want a region next to a booming friendly region to develop faster, so that a faction's core outproduces its fringe.

Rules
- R-015-01  Given a region with two same-faction inhabited neighbors at economy 80 and 40, When one tick runs, Then adjacency bonus = 0.05·0.8 + 0.05·0.4 = 0.060 added to Δeconomy, regardless of the edge types joining them.
- R-015-02  Given a same-faction inhabited neighbor across a border-only edge at economy 40, When one tick runs, Then it contributes 0.05·0.4 = 0.020; edge type does not gate the bonus. Whether a neighbor contributes is decided by the relationship (R-015-03), not the edge type.
- R-015-03  Given a neighbor owned by a faction this region's owner holds a cooperative stance toward, When one tick runs, Then it contributes as a friendly neighbor; a neighbor with no such relationship contributes nothing.
- R-015-04  Given an empty-tier neighbor, When one tick runs, Then it contributes nothing.

Inputs: neighbor economy (raw, not de-oscillated), edge types (recorded but not a filter), stances.
Outputs: adjacency term in the drift log.
Open flags: none. Q-015-01 resolved (b): every edge type counts; the C rewrite drops the current trade-only filter. The relationship gates the bonus, not the edge type.

### S-016 — Hardship breeds unrest, unrest burns itself out
As a commander, I want tension to rise when a region is poor, unstable, or starving, and to decay faster the higher it is, so that regions settle into a real equilibrium instead of spiraling.

Rules
- R-016-01  Given economy 30, population 50, stability 60, tension 20, When one tick runs with oscillation off, Then Δtension = (20/100)·0.5·0.5 + 0 + 0 − 0.20·0.2 = 0.050 − 0.040 = 0.010.
- R-016-02  Given stability 30, When one tick runs, Then stress pressure = (40 − 30) · 0.008 = 0.080.
- R-016-03  Given economy 9.5 and population 50, When one tick runs, Then subsistence severity = (11 − 9.5)/3 = 0.5 and subsistence pressure = 0.15 · 0.5 · 0.5 = 0.0375.
- R-016-04  Given economy 11.0 or above, When one tick runs, Then subsistence pressure is 0.
- R-016-05  Given economy 70 and population 50, When one tick runs, Then economic pressure is negative (−0.050), so prosperity calms tension.

Inputs: economy trend, population, de-oscillated stability, tension trend.
Outputs: Δtension in the drift log; tension field.
Open flags: none.

### S-017 — Population grows slowly and starves slowly
As a commander, I want population to be the slowest field, so that a collapse feels permanent and a recovery feels earned.

Rules
- R-017-01  Given economy 66 and population 60, When one tick runs, Then Δpopulation = 2.0 · (51/85) · 0.4 = 0.480.
- R-017-02  Given economy 10 and population 60, When one tick runs, Then Δpopulation = −(15 − 10) · 0.2 − 0.08 · (1/3) = −1.0267 (subsistence severity (11 − 10)/3).
- R-017-03  Given economy 15.0 exactly, When one tick runs, Then the growth branch is not taken and decline is −0 · 0.2 = 0.
- R-017-04  Given population 100, When one tick runs at any economy above 15, Then growth is 0.

Inputs: economy trend, population.
Outputs: Δpopulation in the drift log; population field.
Open flags: none.

### S-018 — Boom and bust
As a commander, I want economy and tension to swell and dip on their own cycles, out of step from region to region, so that there is always somewhere peaking and somewhere vulnerable.

Rules
- R-018-01  Given a region with economy phase φ, When tick n runs (n ≥ 2), Then the economy delta includes 6.0·(sin(2πn/15 + φ) − sin(2π(n−1)/15 + φ)) and the tension delta includes 2.0·(sin(2πn/18 + φ_t) − sin(2π(n−1)/18 + φ_t)).
- R-018-02  Given tick 1, When drift runs, Then the previous oscillator value is taken as 0.
- R-018-03  Given any tick, When military decay, recruitment threshold, economy drag, and tension pressure are computed, Then they read economy minus the previous economy oscillator value and tension minus the previous tension oscillator value, never the raw field.
- R-018-04  Given a region run for 150 ticks with all other drift terms zeroed, When the economy trace is summed over any 15 consecutive ticks, Then the oscillator's net contribution is within 1e-6 of 0.
- R-018-05  Given two regions with different phase offsets, When run together, Then their economy peaks fall on different ticks.

Inputs: tick, per-region phase offsets (drawn at generation, uniform [0, 2π)).
Outputs: oscillator delta in the drift log.
Open flags: none.

### S-019 — The floor is not safe
As a commander, I want an economy that has hit bottom to stay just barely alive and yet keep hurting, so that a dying region needs help from outside to recover.

Rules
- R-019-01  Given economy 8.0, When any drift, border friction, or standard event would lower it, Then it stays 8.0.
- R-019-02  Given economy 8.0, When a conquest applies its damage, Then economy may fall below 8.0, down to 0.
- R-019-03  Given economy 8.0 and population 50, When one tick runs, Then tension gains 0.15 · 1.0 · 0.5 = 0.075 from subsistence and population loses 0.08 from subsistence on top of the normal decline.
- R-019-04  Given tension 5.0, When an event effect would lower it further, Then it stays at 12.0 or above (event floor 12.0); and Given tension 5.0, When drift alone lowers it, Then it may fall below 12.0.
- R-019-05  Given military or population at 0, When drift runs, Then it never goes negative.

Inputs: field values, source of the change (drift, friction, event, conquest).
Outputs: clamped field values.
Open flags: none. Q-019-01 resolved (a): confirmed as written — event effects floor tension at 12.0, drift alone floors it at 0. R-019-04 stands.

### S-020 — Same seed, same galaxy
As a player in a multiplayer match, I want the simulation to produce the identical trace from the same seed on every machine, so that everyone is looking at the same galaxy.

Rules
- R-020-01  Given a world seed and a tick count, When the sim runs twice on one machine, Then the per-tick field traces are byte-identical.
- R-020-02  Given the same seed, When the sim runs on Linux, Windows, and macOS builds, Then the per-tick state checksums match at every checkpoint.
- R-020-03  Given a checkpoint cadence of 10 ticks, When the sim runs, Then a checksum of all fields and composites is emitted every 10 ticks.

Inputs: seed, tick count, platform.
Outputs: trace, checksums.
Open flags: none. Depends on the determinism decision in `docs/northstar/research/c_rewrite.md`.

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Four fields | Region state | [0, 100] floats | Out-of-range values at load are a save-file error |
| Tier | Region | home, frontier, empty | Other values fail world load |
| Tick | Tick loop | integer ≥ 1 | Not applicable |
| Phase offsets | World generation | [0, 2π) | Not applicable |
| Faction modifiers | Faction | per-field float, launch: conqueror military +0.05 | Unknown field name ignored |
| Neighbor economy, edge type, stance | World, diplomacy | as their own epics | Not applicable |
| Change source | Caller | drift, friction, event, conquest | Not applicable |

No player input reaches this epic directly. Missions change fields through the outcome resolver (E-10).

## Outputs

| Output | Observable where |
|---|---|
| Field values, composites | Region entry of the strategic snapshot and delta; save file |
| Per-term drift deltas | Tick log `drift` entry per region (T1 trace) |
| Checksums | T1 trace every 10 ticks |
| Region condition to the player | World view faction data panel and system hover tooltip (E-16); chronicle fragments (E-09) |

## Invariants

- Fields always in [0, 100]; economy ≥ 8.0 except after conquest.
- Composites are a pure function of the four fields.
- Empty regions never drift.
- Drift reads de-oscillated trend values for cross-field coupling; only the oscillator delta is added.
- Same seed, same trace, all platforms.
- Over 5,000 ticks with no events and no factions, no field of a home region leaves [8, 100] and none diverges to a corner (the ~70 trajectory invariants in `simulation/invariants.py` port to this epic; their thresholds are not loosened).

## Scale requirements

Confirmed by Westley 2026-09-14: 60 regions drift in under 50 µs per tick total; 5,000 ticks of drift alone for 60 regions in under 0.5 s; memory per region under 256 bytes. Not loosened by Agora; a miss is escalated.

## Look and behavior references

None required. The player-facing surface for region state is E-16 (world view).

## Ways this could be wrong

- Drift reads the raw oscillated field instead of the trend, reintroducing the feedback amplification the design removed.
- Oscillator added as a level instead of a delta, so the field drifts upward by the amplitude.
- Recruitment headroom reads primed military instead of raw.
- Economy floor applied before the oscillator delta, so a region at the floor oscillates below it.
- Composites computed before the clamp instead of after.
- Empty regions drift because the tier check was dropped.
- Threshold comparisons use ≥ where the source uses >.
- Float summation order differs from the source, breaking cross-platform checksums.

## Open ambiguity flags

None. Q-013-01 (a), Q-015-01 (b), Q-019-01 (a) all answered 2026-09-13; folded into the stories above. Details in `docs/northstar/ambiguity_register.md`. Stage 3 e2e: `docs/northstar/e2e/E-02.md`.

## Depends on

- E-03 World generation (starting fields, phase offsets, tiers, edge types).
- E-05 Faction agents (modifiers, ownership, stances for the adjacency bonus).
- E-04 Events (event and conquest sources for the floor rules).

# E-13 — Movement, Pathing, and Command

## Definition-completeness gate (run 2026-09-10)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Yes, 8 stories, 42 rules, numbers from `algorithms.md` ALG-66 through ALG-69 and config. |
| Every input listed with range and rejection behavior | Yes, see Inputs. |
| Every output listed with where it is observable | Yes, see Outputs. |
| Implied-but-unstated behavior turned into flags | 5 new flags, Q-095-01, Q-098-01, Q-099-01, Q-101-01. |
| Every visible-surface story has a reference | **No.** S-101 (how movement reads: turning, flow around blockers, formation arrival) has a visible surface and no reference. |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed.** Blocked on 5 open flags and one missing reference. Q-095-01 (slowest-unit pace is Westley's Stage 1 decision, A-557, and is not built) is the load-bearing one.

## Purpose

Four commands and nothing else: move, attack-move, attack a target, use the ability. A selection moves together at its slowest member's pace and keeps its shape on arrival; a player who wants a fast element to run ahead splits it off. Movement is two-level: a coarse route around obstacles, then local steering that flows around allies instead of shoving through them. A unit that has stopped to fight is immovable, so front ranks hold and later arrivals spill into flanking slots on their own. Everything is deterministic: same start, same commands, same movement tick for tick, which is what lockstep multiplayer needs.

## Obviously working in 60 seconds

Select 4 Raiders and 4 Bastions 300 wu apart and move them 3,000 wu. They arrive together at 40 wu/s, in the same relative shape, about 75 s later. Split the Raiders into their own group and move them: they arrive at 150 wu/s in 20 s. Attack-move a Line force into an enemy line: the first units stop and fire, the rest flow around into a concave front; no unit passes through another. Order a plain move through enemy fire: the units do not stop or shoot. Same seed, same commands, byte-identical positions.

## Stories

### S-095 — A force moves as one
As a commander, I want a selection to move at its slowest member's pace and arrive in its shape, and to be able to split off a faster group when I choose, so that cohesion is the default and detaching is a decision.

Rules
- R-095-01  Given a selection of 2 or more units given a move or attack-move, When they move, Then every unit's speed is capped at the slowest member's speed for that order [Q-095-01: A-557, not built].
- R-095-02  Given the selection, When destinations are assigned, Then each unit's destination is the click point plus its offset from the selection's centroid at command time; offsets are computed once and never updated.
- R-095-03  Given any unit farther than 450 wu from the centroid at command time, When destinations are assigned, Then every unit's destination is the raw click point (scatter fallback).
- R-095-04  Given a slot destination that is not walkable, When assigned, Then that unit's destination is the raw click point.
- R-095-05  Given a move group, When its centroid reaches the destination or every unit reaches its slot (within 1.5 × collision radius), Then the group is terminated.
- R-095-06  Given the player selects a subset and issues a new move, When they do, Then that subset forms a new group at its own slowest pace and the old group continues without it.
- R-095-07  Given a single unit, When moved, Then it moves at its own speed to the click point.

Inputs: selection; click point; unit speeds and positions.
Outputs: per-unit move targets and group ids in the tick delta.
Open flags: Q-095-01.

### S-096 — Four commands
As a commander, I want move to be movement and nothing else, attack-move to fight along the way, attack-target to commit, and ability to be a button, so that every order means one thing.

Rules
- R-096-01  Given a plain move, When the unit travels, Then it acquires no target, returns no fire, and does not stop when hit.
- R-096-02  Given an attack-move, When an enemy enters attack range on the unit's layer, Then the unit halts and fires; when the target dies or leaves range it resumes toward the point.
- R-096-03  Given an attack-move engagement, When the target moves more than 200 wu from the unit's anchor (its position at acquisition), Then the unit drops the target and resumes.
- R-096-04  Given attack-target on enemy E, When issued, Then the unit moves toward E if out of range and attacks E in range until E dies or a new order arrives; if E becomes invisible the unit moves to E's last known position and idles there.
- R-096-05  Given activate-ability, When issued to a selection, Then each unit with its ability ready activates it; Brace toggles.
- R-096-06  Given any other command name (patrol, hold, stop, follow), When received, Then it is rejected with a reason and no state changes.
- R-096-07  Given commands for tick t, When the tick runs, Then all of them are applied before any state advances, in arrival order, and recorded with the tick number for replay.

Inputs: command packets (kind, unit ids, target point or unit).
Outputs: acknowledgement with reason in the tick delta; unit order state.
Open flags: none.

### S-097 — Around, not through
As a commander, I want units to route around terrain and flow around each other, and never to walk through anything, so that formations are real.

Rules
- R-097-01  Given a map, When the route grid is built, Then it is 100 wu cells per layer, a cell blocked where obstacle density > 0.7, and a route is the shortest path on that grid, straightened by line-of-sight where cells allow.
- R-097-02  Given a destination shared by several units, When routes are computed, Then the route is computed once and cached.
- R-097-03  Given a moving unit, When it steps, Then it probes 40 wu ahead; if an ally blocks the probe it sweeps alternate angles left and right in a fixed order and takes the first clear one; if none, it waits.
- R-097-04  Given a unit that took a deflected angle, When it moves, Then it keeps that heading for at least 60 wu before re-evaluating.
- R-097-05  Given two units on the same layer within 30 wu (2 × radius 15), When the collision pass runs, Then they are pushed apart along the line between them until 30 wu apart, over up to 3 iterations per tick.
- R-097-06  Given a unit moving through terrain with obstacle density d, When d is in [0.3, 0.7], Then its speed is multiplied by (1 − 0.5 · d); below 0.3 speed is unchanged; at 0.7 and above the cell is blocked (R-097-01). The multiplier is era-uniform; an era pack may not switch it off.
- R-097-06  Given one unit of the pair is stationary (no move target, or halted by engagement), When pushed, Then it moves 0 and the other takes the full displacement.
- R-097-07  Given two units at exactly the same position, When pushed, Then the lower unit id moves in the canonical direction (+x).
- R-097-08  Given enemy units, When colliding, Then they collide like allies; nobody passes through anybody.
- R-097-09  Given a direct-move unit (no route waypoints), When obstacle density ahead within 50 wu exceeds 0.3, Then a repulsion opposes the move; units following route waypoints are exempt.

Inputs: map grid; unit positions, targets, states.
Outputs: positions; route cache; collision log (T1).
Open flags: none.

### S-098 — Firing through friends
As a commander, I want my back rank to shoot over my front rank, so that formation depth is an advantage and not a jam.

Rules
- R-098-01  Given a ranged unit with an ally between it and its target, When it fires, Then the shot lands; friendly units never block fire.
- R-098-02  Given terrain or cover between them, When it fires, Then the shot is blocked exactly as vision is (E-12, E-01 S-007).

Inputs: positions; terrain.
Outputs: attack events.
Open flags: none.

### S-099 — Speed is position
As a commander, I want my fast units to flow around a stalled front faster than slow ones, so that flanking is a property of speed and not a special rule.

Rules
- R-099-01  Given a Strike wing and a Line force both approaching an engaged, immovable friendly front, When they arrive, Then the Strike wing reaches the flank slots first, purely from the steering rules of S-097.
- R-099-02  Given a Raider, When it moves, Then it covers 150 wu per second at 20 ticks per second, 7.5 wu per tick.
- R-099-03  Given more than 1,000 live units on the battlefield, When the tactical tick rate drops from 20 to 10 ticks per second (and returns above that count is crossed downward), Then every per-second quantity (speed, attack interval, ability duration and cooldown, drift) is unchanged in real time because per-tick values scale with the tick period, the change happens on a tick boundary, and every peer in a multiplayer session switches on the same tick (decision A, Westley 2026-09-24).
- R-099-04  Given a unit whose step distance in a tick reaches its remaining distance to its destination, When it snaps to the destination, Then its destination is cleared and it is stationary from that tick onward, and any later displacement by collision or direct position change leaves it at the new position with no re-approach.

Inputs: none beyond S-097.
Outputs: positions.
Open flags: none.

### S-100 — Facing
As a commander, I want units to face what they shoot and where they go, and to turn rather than snap, so that a retreat under fire looks like one.

Rules
- R-100-01  Given a unit attacking a target, When facing updates, Then it faces the target; given moving with no target, it faces its heading; given idle with no target, it keeps its last facing.
- R-100-02  Given a facing change, When it turns, Then the turn rate is capped at 6.0 rad/s for Strike, 4.0 for Line, 2.5 for Siege.
- R-100-03  Given a unit retreating from a pursuer under attack-target, When facing updates, Then it faces the pursuer.

Inputs: target; heading.
Outputs: facing in the tick delta; renderer interpolates.
Open flags: none.

### S-101 — Movement that reads
As a commander, I want to see units turn, slow behind blockers, and settle into their slots, so that I trust what the formation is doing.

Rules
- R-101-01  Given a T2 clip of a 20-unit move, When reviewed, Then no unit overlaps another, no unit teleports, and units arrive within 2 s of each other.
- R-101-02  Given the renderer, When it draws between ticks, Then position and facing are linearly interpolated from the last two ticks.

Inputs: tick deltas.
Outputs: screen.
Open flags: Q-101-01 (arrival tolerance and "settled" look are unspecified). Reference required: `references/E-13/notes.md`, missing.

### S-102 — Same commands, same battle
As a player in a multiplayer match, I want every peer to compute the same movement from the same commands, so that we are all watching one battle.

Rules
- R-102-01  Given a seed, a map, and a command stream, When two machines run 5,000 ticks, Then every position, facing, and target is identical at every tick and the checksums match.
- R-102-02  Given the steering sweep, When angles are tried, Then the order is fixed and documented; no wall-clock or hash-order input reaches movement.

Inputs: seed; command stream.
Outputs: checksums.
Open flags: none.

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Command packet | Player or enemy macro | move, attack_move, attack_target, activate_ability, layer_hard_transfer, layer_preference_set; unit ids; point in map bounds or target id | unknown kind, dead or foreign unit, point out of bounds, unknown target: rejected with reason |
| Map grid, obstacle density | E-17 | | |
| Unit speeds, radii | E-11 | | |

## Outputs

| Output | Observable where |
|---|---|
| Positions, facings, move targets, group ids, order state | Tick delta; T1 trace; screen |
| Command acknowledgements | Tick delta |
| Route cache stats, collision counts | T1 trace |

## Invariants

- No two same-layer units within 30 wu after the collision pass, except when the pass hits its iteration cap.
- A stationary unit never moves from collision.
- A unit never enters a blocked cell.
- Same seed and commands, same movement, all platforms.
- Under a plain move, no target is ever acquired.

## Scale requirements

Confirmed by Westley, 2026-10-01: one pipe `tactical_step` round trip (request sent to frame parsed by the client) takes under 100 ms at 5,000 units, the tick length at the 10 ticks per second the sim runs above 1,000 live units (R-099-03).

Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is escalated): movement and collision for 1,000 units in under 3 ms per tick, 10,000 in under 30 ms; route queries under 1,000 per second at 60 wu cells. The 10,000-unit figure is measured at the 10 ticks/s rate the sim drops to above 1,000 live units (E-13 R-099-03), a 100 ms tick; the 1,000-unit figure at 20 ticks/s.

## Look and behavior references

`references/E-13/notes.md`, missing: formation movement, flow around blockers, turning (2 to 5 clips).

## Ways this could be wrong

- Slowest-unit pace capped per tick from current speeds, so a Surge changes the group pace.
- Offsets recomputed per tick, so formations drift.
- Scatter fallback triggered by any unit beyond 450 wu from the click point instead of the centroid.
- Stationary rule ignored, so engaged units get shoved.
- Route grid shared across layers.
- Probe angle order differs between platforms.
- Plain move returns fire.
- Leash measured from the target's position instead of the anchor.

## Open ambiguity flags

Q-095-01, Q-101-01. Details in `docs/northstar/ambiguity_register.md`.

## Depends on

- E-01 Layer system (per-layer grids, transition state).
- E-11 Units (speeds, radii, targeting loop).
- E-12 Fog (visibility for attack-move acquisition).
- E-17 Map generation (obstacle density, navmesh input).
- E-16 Client (selection, control groups, input).
- E-19 Multiplayer (lockstep determinism).

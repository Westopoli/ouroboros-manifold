# E-13 — Movement, Pathing, and Command

## Definition-completeness gate (run 2026-09-10)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Yes, 11 stories, 49 rules, numbers from `algorithms.md` ALG-66 through ALG-69 and config. The rules of S-207 to S-209 leave their numbers to open flags. |
| Every input listed with range and rejection behavior | Yes, see Inputs. |
| Every output listed with where it is observable | Yes, see Outputs. |
| Implied-but-unstated behavior turned into flags | Yes; the 9 flags still open are listed at the foot of this file. |
| Every visible-surface story has a reference | **No.** S-101 (how movement reads: turning, flow around blockers, formation arrival) has a visible surface and no reference. |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed.** Blocked on Q-101-02 and one missing reference (S-101). S-095, S-097 to S-100 and S-102 are buildable, and S-096 as written. S-207 and S-209 are design decided, not scheduled for building, apart from the movement rules R-207-06 and R-207-07, which are ruled and built with the tactical port; S-207 carries open flags.

## Purpose

Five unit commands: move, attack-move, attack a target, guard, use the ability. Guard is a radius guard (S-208; Westley, 2026-10-13). Requests by pointing at the map and the economy seat's orders are a second channel beside these four, not unit commands (E-22 S-168, S-170, S-180). A selection moves together at its slowest member's pace and keeps its shape on arrival; a player who wants a fast element to run ahead splits it off. Movement is two-level: a coarse route around obstacles, buildings and, for walking units, ground too steep to cross (S-207), then local steering that flows around allies instead of shoving through them. A unit that has stopped to fight is immovable, so front ranks hold and later arrivals spill into flanking slots on their own. Everything is deterministic: same start, same commands, same movement tick for tick, which is what lockstep multiplayer needs.

## Obviously working in 60 seconds

Select 4 Raiders and 4 Bastions 300 wu apart and move them 3,000 wu. They arrive together at 40 wu/s, in the same relative shape, about 75 s later. Split the Raiders into their own group and move them: they arrive at 150 wu/s in 20 s. Attack-move a Line force into an enemy line: the first units stop and fire, the rest flow around into a concave front; no unit passes through another. Order a plain move through enemy fire: the units do not stop or shoot. Same seed, same commands, byte-identical positions.

## Stories

### S-095 — A force moves as one
As a commander, I want a selection to move at its slowest member's pace and arrive in its shape, and to be able to split off a faster group when I choose, so that cohesion is the default and detaching is a decision.

Rules
- R-095-01  Given a selection of 2 or more units given a move or attack-move, When they move, Then every unit's speed is capped at the slowest member's base speed, fixed at order time; a unit that activates a movement ability leaves the group and moves at its boosted speed (Q-095-01).
- R-095-02  Given the selection, When destinations are assigned, Then each unit's destination is the click point plus its offset from the selection's centroid at command time; offsets are computed once and never updated.
- R-095-03  Given any unit farther than 450 wu from the centroid at command time, When destinations are assigned, Then every unit's destination is the raw click point (scatter fallback).
- R-095-04  Given a slot destination that is not walkable, When assigned, Then that unit's destination is the raw click point.
- R-095-05  Given a move group, When its centroid reaches the destination or every unit reaches its slot (within 1.5 × collision radius), Then the group is terminated.
- R-095-06  Given the player selects a subset and issues a new move, When they do, Then that subset forms a new group at its own slowest pace and the old group continues without it.
- R-095-07  Given a single unit, When moved, Then it moves at its own speed to the click point.

Inputs: selection; click point; unit speeds and positions.
Outputs: per-unit move targets and group ids in the tick delta.
Open flags: none.

### S-096 — Five commands
As a commander, I want move to be movement and nothing else, attack-move to fight along the way, attack-target to commit, and ability to be a button, so that every order means one thing.

The guard stance joined the commands 2026-10-13 (S-208, R-096-08). An attack-moving unit engages what is within its type's reach and visible to its side, on its own layer or another (E-01 S-164, R-008-04; E-12 R-093-02). The rules below are what the game does today.

Rules
- R-096-01  Given a plain move, When the unit travels, Then it acquires no target, returns no fire, and does not stop when hit.
- R-096-02  Given an attack-move, When an enemy enters attack range on the unit's layer, Then the unit halts and fires; when the target dies or leaves range it resumes toward the point. Two or more units attack-moved together take formation slots as a move group does (R-095-02 to R-095-04); after every fight the group resumes toward the point as a unit attack-moved alone does (Westley, 2026-10-13, option (a): an attack-move is not finished until the unit reaches its point, except that a unit that gives up under R-099-05 ends where it stands (Architect decision 28, 2026-10-19); his 2026-10-02 words for the lone unit, "It should resume its prior goal after the fight is completed", now hold for a group too). The engine today ends a group once every member has engaged and never resumes it (the Architect's clause, A124 build); the resume for groups is a pending engine piece, measured 2026-10-13: two groups attack-moved to one point stalled 303 to 336 wu apart with range 300, while the same units ordered one by one fought to elimination.
- R-096-03  Given an attack-move or idle engagement, When the unit itself has pursued farther from its anchor (its position at acquisition) than its own type's sensor radius, Then it drops the target and resumes (attack-move) or holds (idle); a unit holding and firing from its anchor never drops a target for the leash, whatever its weapon range (ruled A188, 2026-10-03; the earlier text measured the target's distance). The leash was 200 wu for every type until 2026-11-01; Westley: the vision range of that specific unit, modelled on the game whose movement we follow, where a unit's leash sat at or just beyond its vision (H-057).
- R-096-04  Given attack-target on enemy E, When issued, Then the unit moves toward E if out of range and attacks E in range until E dies or a new order arrives; if E becomes invisible the unit moves to E's last known position and idles there.
- R-096-05  Given activate-ability, When issued to a selection, Then each unit with its ability ready activates it; Brace toggles.
- R-096-06  Given any other command name (patrol, hold, stop, follow), When received, Then it is rejected with a reason and no state changes.
- R-096-07  Given commands for tick t, When the tick runs, Then all of them are applied before any state advances, in arrival order, and recorded with the tick number for replay.
- R-096-08  Given a guard order, When issued to a selection, Then each unit takes its position as its post and engages any target its side can see (E-12 R-093-02), stepping toward it no farther than `GUARD_RADIUS` = 200 wu from the post (DRAFT-guard-radius: the attack-move leash of R-087-05, Westley's number to change; the radius bounds the guard's own walk, measured post to the guard's centre, ruled 2026-10-14 for E4), firing whenever the target is in range, returning to the post when the target dies or when engaging it would take the guard past the radius; it never crosses the radius and never marches; the walk is toward any target its side can see within vision, on its own layer or another, as far as the radius allows, and it fires when reach and range allow (Westley, 2026-11-08: a guard engages a cross-layer target "only if the enemy unit is within vision"; before then the built walk was same-layer only); a move, attack-move, attack-target or layer order ends the guard; return fire (R-087-06) is untouched. Ruled by Westley, 2026-10-13: a guard stance as a radius (option b of Q-096-01), "for the whole game, not just the simulator". The engine's guard today (A170) holds and never steps forward; the step-and-return within the radius is an engine piece not yet built, and the lab's choke defence runs on the built order until it lands.

Inputs: command packets (kind, unit ids, target point or unit).
Outputs: acknowledgement with reason in the tick delta; unit order state.
Open flags: Q-087-01 (whether the 200 wu leash of R-096-03 is tested before or after damage; E-11 S-087).

### S-097 — Around, not through
As a commander, I want units to route around terrain and flow around each other, and never to walk through anything, so that formations are real.

Direction changed 2026-10-02, rewrite pending: the route grid and the cached routes follow buildings that appear and fall and slopes that join layers (S-207; E-22 S-174; E-01 S-200), and the steering probe reads positions as they stood at the start of the tick. The rules below are what the game does today.

Rules
- R-097-01  Given a map, When the route grid is built, Then it is 100 wu cells per layer, a cell blocked where obstacle density > 0.7, and a route is the shortest path on that grid, straightened by line-of-sight where cells allow.
- R-097-02  Given a destination shared by several units, When routes are computed, Then the route is computed once and cached.
- R-097-03  Given a moving unit, When it steps, Then it probes 40 wu ahead; if a unit on its layer blocks the probe (an idle unit of its own side does not block: idle means no move target and not engaged; an enemy always does) it tries +30, -30, +60, -60, +90 and -90 degrees from its heading, in that order, and takes the first clear one; if none is clear it continues straight.
- R-097-04  Given a unit that took a deflected angle, When it moves, Then it keeps that heading for at least 60 wu before re-evaluating.
- R-097-05  Given two units on the same layer within 30 wu (2 × radius 15), When the collision pass runs, Then they are pushed apart along the line between them until 30 wu apart, over up to 3 iterations per tick.
- R-097-06  Given a unit moving through terrain with obstacle density d, When d is in [0.3, 0.7], Then its speed is multiplied by (1 − 0.5 · d); below 0.3 speed is unchanged; at 0.7 and above the cell is blocked (R-097-01). The multiplier is era-uniform; an era pack may not switch it off.
- R-097-10  Given one unit of the pair is stationary (no move target, or halted by engagement), When pushed, Then it moves 0 and the other takes the full displacement, except that an idle unit (no move target, not engaged) takes the full displacement from a mover of its own side and none from an enemy mover, which takes all of it; given both are stationary and either was displaced earlier in the tick, they split the displacement equally. Every unit starts pair checks, moving or stopped, so a unit that walks into a stopped one is pushed out; the push pass repeats up to 10 times a tick until no pair is closer than 30 wu, or until a pass displaces no unit by more than `COLLISION_SETTLE_EPS = 0.1` wu (that pass is applied; ALG-68). This is a deliberate difference from the Python reference, whose rule let a higher-id unit stack on a stopped lower-id one (Westley, 2026-10-02).
- R-097-07  Given two units at exactly the same position, When pushed, Then the lower unit id moves in the canonical direction (+x) [Q-097-02: the Python reference moves it the other way and by a thousand times the normal push].
- R-097-08  Given enemy units, When colliding, Then they collide like allies; nobody passes through anybody.
- R-097-09  Given a direct-move unit (no route waypoints), When obstacle density ahead within 50 wu exceeds 0.3, Then a repulsion opposes the move; units following route waypoints are exempt.

Inputs: map grid; unit positions, targets, states.
Outputs: positions; route cache; collision log (T1).
Open flags: none here. Q-097-02 closed 2026-10-21 (register: invisible tie-break). Q-165-01 (a lane speed above 1.0 is an idea only, E-17 S-165; R-097-06 stays as written until it is decided).

### S-098 — Firing through friends
As a commander, I want my back rank to shoot over my front rank, so that formation depth is an advantage and not a jam.

Rules
- R-098-01  Given a ranged unit with an ally between it and its target, When it fires, Then the shot lands; friendly units never block fire.
- R-098-02  Given a blocked cell (R-097-01) or a cover obstacle between them on the layers involved, When it fires, Then the shot is blocked exactly as vision is (E-12, E-01 S-007): cover blocks only up to its height, and only a line that passes through it between two units outside it; a unit standing inside cover is fired at as normal (E-01 R-007-06).

Inputs: positions; terrain.
Outputs: attack events.
Open flags: none.

### S-099 — Speed is position
As a commander, I want my fast units to flow around a stalled front faster than slow ones, so that flanking is a property of speed and not a special rule.

Rules
- R-099-01  Given a Strike wing and a Line force both approaching an engaged, immovable friendly front, When they arrive, Then the Strike wing reaches the flank slots first, purely from the steering rules of S-097.
- R-099-02  Given a Raider, When it moves, Then it covers 150 wu per second at 20 ticks per second, 7.5 wu per tick.
- R-099-03  Given more than 1,000 live units on the battlefield, When the tactical tick rate drops from 20 to 10 ticks per second (and returns above that count is crossed downward), Then every per-second quantity (speed, attack interval, ability duration and cooldown, drift) is unchanged in real time because per-tick values scale with the tick period, the change happens on a tick boundary, and every peer in a multiplayer session switches on the same tick (decision A, Westley 2026-09-24).
- R-099-04  Given a unit within its arrival radius of its destination (1.5 × collision radius for a formation slot, 2 × for a route waypoint), When the tick runs, Then it has arrived where it stands, without snapping to the point: its destination is cleared and it is stationary from that tick onward, and any later displacement by collision or direct position change leaves it at the new position with no re-approach.
- R-099-05  Given a unit under a group move or a group attack-move whose own slot it cannot reach (a stopped neighbour holds it), When it has been within 75 wu (about two slot spacings) of its slot for 40 consecutive ticks (2 s) without arriving, Then it ends its order where it stands, the same state as an arrival (destination cleared, stationary from that tick onward); the count resets when the unit leaves the 75 wu disc or arrives, and a unit never paces with no end; this includes a group attack-move, Architect decision 28, 2026-10-19.

Inputs: none beyond S-097.
Outputs: positions.
Open flags: none.

### S-100 — Facing

Direction changed 2026-10-13, rewrite pending: facing gains a firing arc, a unit fires only at targets inside an arc about its facing (Westley: "add a firing-arc rule to the game"; Q-100-01 for width and the flanked case). The rules below are what the game does today.
As a commander, I want units to face what they shoot and where they go, and to turn rather than snap, so that a retreat under fire looks like one.

Direction changed 2026-10-02, rewrite pending: a unit faces its engaged target only within 1.5 times its range, else its move target, else its velocity, and a stationary firing unit turns. The rules below are what the game does today.

Rules
- R-100-01  Given a unit attacking a target, When facing updates, Then it faces the target; given moving with no target, it faces its heading, which is the direction of its travel (the one-tick displacement), not its destination (DEC-facing-travel, 2026-10-22); given idle with no target, it keeps its last facing.
- R-100-02  Given a facing change, When it turns, Then the turn rate is capped at 6.0 rad/s for Strike, 4.0 for Line, 2.5 for Siege.
- R-100-03  Given a unit retreating from a pursuer under attack-target, When facing updates, Then it faces the pursuer.
- R-100-04  DRAFT (Westley, 2026-10-13: "add a firing-arc rule to the game"; Q-100-01): Given a unit with a target, When the target lies outside the firing arc about the unit's facing (360 is no arc), Then the unit does not fire; it keeps the target, turns toward it at the R-100-02 rate, and fires once the target is inside. Acquisition, the hold and return fire are untouched; a unit kiting under attack-target faces its target directly. The firing arc is per category: Strike wide, Line medium, Siege narrow (Westley 2026-10-21, Q-100-01 (b)); the three widths are lab drafts DRAFT-arc-strike, DRAFT-arc-line, DRAFT-arc-siege until the lab's arc sweep names them; what a flanked unit does is his after the lab.

Inputs: target; heading.
Outputs: facing in the tick delta; renderer interpolates.
Open flags: none.

### S-101 — Movement that reads
As a commander, I want to see units turn, slow behind blockers, and settle into their slots, so that I trust what the formation is doing.

Rules
- R-101-01  Given a T2 clip of a 20-unit move, When reviewed, Then no unit overlaps another, no unit teleports, and units arrive within 2 s of each other.
- R-101-02  Given the renderer, When it draws between ticks, Then position and facing are linearly interpolated from the last two ticks.
- R-101-03  Given a move order that has just been issued, When the selected group is on the way, Then the route the planner found is drawn on the map as a coloured line from the group to the ordered spot, and it stays until the group arrives (R-095-05); the line is the walkers prototype's route line, copied, not regenerated (Westley 2026-10-13: "Shows units clumped on bottom moving by the looks of it, hard to tell because it's just a photo, one of the prototypes showed a really clever 'path' colored line showing the route it found to get to the location I right clicked. That might be useful here, and the code is probably mostly copy+pastable, no re-generation needed.").

Inputs: tick deltas.
Outputs: screen.
Open flags: Q-101-02 (the collision iteration cap against R-101-01's 30 wu floor).
Arrival is the group centroid reaching the point. Reference required: `references/E-13/notes.md`, missing.

### S-102 — Same commands, same battle
As a player in a multiplayer match, I want every peer to compute the same movement from the same commands, so that we are all watching one battle.

Rules
- R-102-01  Given a seed, a map, and a command stream, When two machines run 5,000 ticks, Then every position, facing, and target is identical at every tick and the checksums match.
- R-102-02  Given the steering sweep, When angles are tried, Then the order is fixed and documented; no wall-clock or hash-order input reaches movement.

Inputs: seed; command stream.
Outputs: checksums.
Open flags: none.

### S-207 — Where units can go: buildings, slopes, solid ground and the edge
As a commander, I want routes to follow the buildings that appear and fall, the slopes and the steep ground, and no unit to be stuck inside terrain or leave the map, so that a siege, a gate or a mountain pass changes where my army walks.

The rules on buildings, slopes and steep ground are design decided 2026-10-02, not scheduled for building, and apply to land maps (E-22 S-174, E-01 S-200; space maps Q-166-02). R-207-06 and R-207-07 are ruled movement work that is built with the tactical port.

Rules
- R-207-01  Given a structure that blocks (a wall, a gate, a tower or a production building; E-11 S-204), When it is placed, Then the cells of its footprint on the layers it occupies are blocked on the route grid It blocks from placement, including while under construction (Westley, 2026-10-03); it occupies its own layer and some layers above it (E-11 R-204-01).
- R-207-02  Given a structure that falls, When it is destroyed, Then those cells are open again.
- R-207-03  Given a cell that turns blocked or open (R-207-01, R-207-02), When units route, Then no unit follows a route through a blocked cell, and any route cached for a shared destination (R-097-02) that passes through a changed cell is computed again.
- R-207-04  Given a gate, When a unit of either side reaches it, Then [Q-174-02: whether it lets its own side's units through and stops the enemy's, and whether it opens and closes].
- R-207-05  Given a walking unit, When its route is planned, Then each slope joins its two layers on the route grid at its bottom edge and its top edge, crossing it takes the slope's length over the unit's speed (E-01 R-004-07), the route never passes through ground too steep to cross (E-01 S-200), and the shortest route is the one that takes least time (E-01 R-001-05).
- R-207-06  Given a unit found inside a blocked cell on its layer, such as one a wall was placed on, When the tick runs, Then it is moved to the nearest open cell and is not left stalled in the cell.
- R-207-07  Given a position, a destination or a collision push, When it is applied, Then the position is clamped to the map, and a push is slid along a blocked cell and not into it.

Inputs: structures (E-11 S-204); slopes and sections too steep to cross (E-17 S-189, S-190); the route grid.
Outputs: the route grid and the route cache as they change; unit positions.
Open flags: none. Q-174-02 closed 2026-10-21 (register: a named draft Westley tunes by feel).

### S-208 — Guard
As a commander, I want to put units on guard at a post, so that I can hold a choke, the top of a slope or a door without the units running out through it.

The guard stance is decided (Westley, 2026-10-01: "Yes a guard stance is fine"; 2026-10-13: a radius guard, option (b), for the whole game). Its rule is R-096-08.

Rules
- R-208-01  Given selected units, When the player gives the guard order at a post, Then the units hold the post and engage what their side can see (E-12 R-093-02) within `GUARD_RADIUS` of it, returning to the post when the target dies or leaves the radius, never chasing past it (R-096-08). Guard is the fifth unit command, not a mode of attack-move; R-096-06 keeps rejecting patrol, hold, stop and follow.
- R-208-02  Given a force waiting for an enemy to come inside its ground, When the enemy is within its reach and has not seen it, Then [Q-208-01: whether a unit can be ordered to hold fire so that it stays unseen and the ambush is not spoiled, and whether that is the guard stance or a second order].
- R-208-03  Given a guard command for tick t, When the tick runs, Then it is applied with every other command before any state advances, and recorded with the tick number (R-096-07).

Inputs: guard command (selection, post).
Outputs: unit order state in the tick delta.
Open flags: Q-208-01.

### S-209 — Workers move like any unit
As a commander, I want workers to walk the same ground and take the same room as soldiers, so that a base with thousands of them is a real crowd on the real map.

Design decided 2026-10-02, not scheduled for building.

Rules
- R-209-01  Given a worker walking to a source or a drop-off (E-22 S-167), When it moves, Then it uses the route grid, the steering and the collision of S-097 as any unit does, and it is stopped by the buildings of S-207.
- R-209-02  Given more than 1,000 live units, workers included, When the tactical tick rate is chosen, Then workers are counted among the live units (R-099-03, E-11 S-202).

Inputs: worker positions and orders.
Outputs: positions.
Open flags: none.

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Command packet | Player or enemy macro | move, attack_move, attack_target, activate_ability, layer_hard_transfer, layer_preference_set; unit ids; point in map bounds or target id | unknown kind, dead or foreign unit, point out of bounds, unknown target: rejected with reason |
| Map grid, obstacle density | E-17 | | |
| Slopes, sections too steep to cross | E-17 S-189, S-190 | land maps | |
| Structures | E-11 S-204 | Position, footprint, layers | |
| Unit speeds, radii | E-11 | | |

## Outputs

| Output | Observable where |
|---|---|
| Positions, facings, move targets, group ids, order state | Tick delta; T1 trace; screen |
| Command acknowledgements | Tick delta |
| Route cache stats, collision counts | T1 trace |

## Invariants

- No two same-layer units within 30 wu after the collision pass, except when the pass hits its iteration cap.
- A stationary unit is never moved by a moving unit's collision; two stationary units that overlap separate.
- A unit never enters a blocked cell, which includes a cell a structure occupies and, for a walking unit, ground too steep to cross; a unit found inside one is moved out (R-207-06), and no unit leaves the map (R-207-07).
- Same seed and commands, same movement, all platforms.
- Under a plain move, no target is ever acquired.

## Scale requirements

Confirmed by Westley, 2026-10-01: one pipe `tactical_step` round trip (request sent to frame parsed by the client) takes under 100 ms at 5,000 units, the tick length at the 10 ticks per second the sim runs above 1,000 live units (R-099-03).

Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is escalated): movement and collision for 1,000 units in under 3 ms per tick, 10,000 in under 30 ms; route queries under 1,000 per second on the route grid (100 wu cells, R-097-01; this line said 60 until 2026-10-02). Workers are units and count in these figures (E-11 S-202, S-209). The 10,000-unit figure is measured at the 10 ticks/s rate the sim drops to above 1,000 live units (E-13 R-099-03), a 100 ms tick; the 1,000-unit figure at 20 ticks/s.

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
- A cached route kept through a cell that a building has since blocked, or a wall placed on a unit that is then stalled in it.
- A walking unit routed over ground too steep to cross, or up a slope it has no edge for.

## Open ambiguity flags

Q-101-02, Q-207-01, Q-208-01, and from other epics Q-087-01, Q-165-01. Details in `docs/northstar/ambiguity_register.md`.

## Depends on

- E-01 Layer system (per-layer grids, transition state).
- E-11 Units (speeds, radii, targeting loop).
- E-12 Fog (visibility for attack-move acquisition).
- E-17 Map generation (obstacle density, navmesh input, slopes and steep ground).
- E-22 Economy and bases (buildings that block, workers).
- E-16 Client (selection, control groups, input).
- E-19 Multiplayer (lockstep determinism).

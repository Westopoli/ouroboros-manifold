# E-12 — Fog and Sensors

## Definition-completeness gate (run 2026-09-10)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Yes, 8 stories, 31 rules, numbers from `algorithms.md` ALG-65 and config. The rules of S-205 and S-206 leave their numbers to open flags. |
| Every input listed with range and rejection behavior | Yes, see Inputs. |
| Every output listed with where it is observable | Yes, see Outputs. |
| Implied-but-unstated behavior turned into flags | Yes; the 9 flags still open are listed at the foot of this file. |
| Every visible-surface story has a reference | **No.** S-094 (how fog and interference look) has a visible surface and no reference. |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed.** Blocked on the open flags listed at the foot and one missing reference (S-094). S-090, S-092 and S-093 have no open flags; gate to be rerun. Cross-layer vision, the targeted ping and going dark are specified in E-01 (S-005, S-162, S-163) and referenced here, not duplicated. S-205 and S-206 are design decided, not scheduled for building, and each carries open flags.

## Purpose

The player sees only what their units can sense. Each unit reveals a circle around it, shrunk by whatever interference it is standing in, and the revealed map is the union of those circles. Enemies outside every circle do not exist on screen. Cover blocks sight by height (E-01 S-007). Other layers are seen at reduced range (E-01 S-005) or by a targeted ping (E-01 S-162), and a force that goes dark is harder to see from other layers (E-01 S-163). Before the mission starts, the player sees all the terrain and none of the enemy; the moment the mission begins, fog falls. Fog binds every side by the same rule: a unit acquires, pursues and fires only at what its own side can see, so a spotter or a ping lets a long-range unit fire and losing sight stops it. Enemy buildings are seen as enemy units are, and a seen production building shows what it is doing (S-205). A side keeps a record of which enemy unit types it has seen, and no more than that (S-206). What the player is shown never changes the result, and faction agents in the strategic sim see everything about their neighbors.

At launch there is no era-to-era difference in fog (Stage 1 A-321). The Settled Reach ships with the values below.

## Obviously working in 60 seconds

Place a Vanguard (sensor 700) and an enemy Raider at 650 wu on the same layer: the Raider is visible. Move the Raider to 750 wu: gone. Put the Vanguard inside an interference zone of intensity 0.5: the Raider at 400 wu is visible, at 400 wu plus one it is not. Move an enemy behind a tall asteroid: gone though in range. Start the recon phase: every obstacle, zone, and node is drawn and no enemy. Press Begin: the enemy positions vanish under fog. Same seed, same visibility sets.

## Stories

### S-089 — I see what my units see
Flag closed, rule text pending: Q-089-01, enemies that leave sensor range vanish from the screen with no markers or memory. The rule below is what the tests read today.
As a commander, I want the map revealed only around my units, so that scouting is a job and the unknown is a threat.

Rules
- R-089-01  Given an observer with sensor radius r at interference i, When visibility is computed, Then its effective radius is r × (1 − i), and an enemy on the same layer is visible if its distance ≤ that radius and no cover (E-01 S-007) or blocked cell (E-13 R-097-01) blocks the line.
- R-089-02  Given every friendly unit's visible set, When the player's view is built, Then the player-visible enemy list is their union.
- R-089-03  Given an enemy not in the union, When drawn, Then it is not drawn, its HP bar is not drawn, and its position is not in the client's data; the live game loads every mission with the fog filter on (the pipe's own default is off, and the briefing turns it on); a QA probe may turn it off for a test through the daemon's set_fog_filter verb, which never runs in play (Architect, 2026-10-09).
- R-089-04  Given visibility, When computed, Then it is recomputed every tick from current positions; there is no memory of last-seen positions [Q-089-01].
- R-089-05  Given a friendly unit, When visibility is computed, Then friendly units are always visible to the player regardless of distance.
- R-089-06  Given visibility A sees B, When B's set is computed, Then B seeing A is computed independently (asymmetric sensors are normal).

Inputs: unit positions, layers, sensor radii; interference at each position; cover geometry.
Outputs: per-unit visible set and player-visible list in the tick delta; fog render.
Open flags: none.
The targeted ping (E-01 S-162) is how a player sees far; the seer is dropped or kept only at a very high cost so that it does not undercut the ping.

### S-090 — Hiding in the storm
Flag closed, rule text pending: Q-090-01, overlapping zones combine by sum clamped to 1, and detection range is also scaled by (1 − interference at the target). The rule below is what the tests read today.
As a commander, I want a zone of interference to shrink what units inside it can see and what outsiders can see into it, so that I can hide a force or fear one.

Rules
- R-090-01  Given a zone source with intensity 0.6 at its center and linear falloff to 0 at its radius, When sampled at half radius, Then interference is 0.3.
- R-090-02  Given overlapping zones, When sampled, Then the combined interference is clamped to [0, 1] [Q-090-01: sum vs max].
- R-090-03  Given an observer outside a zone looking at a target inside it, When visibility is computed, Then only the observer's own interference applies [Q-090-01: the bible says outsiders "can't see as far into the zone"; code samples the observer's position only].
- R-090-04  Given a zone source that moves over the mission, When ticks pass, Then interference at a fixed point changes as the source moves.
- R-090-05  Given a zone that varies by layer, When sampled, Then the value is per layer.

Inputs: gradient sources (position, radius, intensity, falloff, layer, motion).
Outputs: interference field; fog render density.
Open flags: none. Weather that travels across the map and shuts down what it passes over is a hazard of E-15 (S-130), not a moving interference source.

### S-091 — Standing high
Flag closed, rule text pending: Q-092-01, the elevation sensor bonus is built: the effective radius is multiplied by 1 + 0.15 times the tier difference, with tiers from the elevation gradient in steps of 0.25. The rule below is what the tests read today.
As a commander, I want an elevated position to see farther, so that vantage is worth taking.

Rules
- R-091-01  Given a space era (vantage nodes are retired for ground eras, where high ground sees down, E-01 R-005-09; Westley, 2026-10-05) and a unit within a vantage node's radius (default 100 wu), When visibility is computed, Then cross-layer factors double and extend one layer (E-01 R-005-06).
- R-091-02  Given a space era (the elevation bonus is retired for ground eras, replaced by E-01 R-005-09; Westley, 2026-10-05) and an elevation tier difference of d between observer and target, When the era enables elevation sensor bonus, Then the observer's effective radius is multiplied by 1 + 0.15 · d [Q-092-01: nothing in code reads this].
- R-091-03  Given the Settled Reach, When elevation is read, Then it affects sensors only, never damage (E-11 R-084-06).

Inputs: vantage nodes; elevation gradient.
Outputs: effective radius.
Open flags: Q-091-01 (how the elevation tiers of R-091-02, steps of 0.25, relate to the five height-band layers, now that on land maps elevation and layers come from one height field (E-17 S-190); and whether the bonus is symmetric, since the sign of the tier difference is not stated while vision across layers is symmetric by layer distance, E-01 S-005).

### S-092 — Recon, then fog
As a commander, I want to study the whole map before I commit and then lose sight of everything but what my units see, so that planning and scouting are two different skills.

Rules
- R-092-01  Given the recon phase, When the map is shown, Then every obstacle, cover cluster, hazard zone, spine node type, layer accessibility, and elevation contour is visible, and no enemy unit, structure ownership, or spawn point is.
- R-092-02  Given the recon phase, When the mission clock is read, Then it has not started, and no unit moves.
- R-092-03  Given the player presses Begin Mission, When the first tactical tick runs, Then fog applies per S-089 and terrain stays visible.
- R-092-04  Given any mission, When recon runs, Then terrain visibility is complete regardless of world state.

Inputs: map; player input.
Outputs: recon render; mission start.
Open flags: none.

### S-093 — Fog binds every side alike
As a commander, I want fog to bind my units and the enemy's by one rule, so that a battle in the dark is still a fair battle.

Rules
- R-093-01  Given two identical battles differing only in which side the player commands or in what the client draws, When resolved, Then the traces are identical.
- R-093-02  Given any unit of any side, When it acquires, pursues or fires at a target, Then the target is in its side's visible set: the union of what that side's living units see (R-089-01, E-01 S-005) and what its pings reveal (E-01 S-162); the rule is the same for the player's units and the enemy's (Westley, 2026-10-02). A unit whose sensor is shorter than its range (Bombard, Bastion: sensor 300) fires beyond its sensor only at what another friendly unit or a ping sees.
- R-093-03  Given the strategic sim, When faction agents decide, Then they read every neighbor region's fields without fog (E-05).

Inputs: none.
Outputs: determinism trace.
Open flags: none.

### S-094 — How fog looks
Flag closed, rule text pending: Q-094-01, no sensor circles are drawn and fog has two states, never seen (darker) and seen before but now dark. The rule below is what the tests read today.
As a commander, I want unexplored space, interference, and revealed ground to read differently at a glance, so that I know where I am blind.

Rules
- R-094-01  Given a T2 screenshot, When inspected, Then revealed area, fogged area, and interference zones are three distinguishable treatments.
- R-094-02  Given a unit inside interference, When drawn, Then its own sensor circle is visibly smaller.

Inputs: visibility; interference field.
Outputs: screen.
Open flags: none. Reference required: `references/E-12/notes.md`, missing.

### S-205 — Buildings are seen like units, and show what they do
As a commander, I want an enemy building to appear when my units see it and to show what it is doing, so that scouting reads an enemy base and hiding a building is a play.

Design decided 2026-10-02, not scheduled for building. Walls, gates and towers are written for land maps (E-22 S-174).

Rules
- R-205-01  Given an enemy structure (E-11 S-204), When visibility is computed, Then it is in a side's visible set when it lies within the effective radius of one of that side's units and no cover or blocked cell blocks the line (R-089-01), as an enemy unit is; it occupies its own layer and some layers above it (E-11 R-204-01).
- R-205-02  Given an enemy structure not in the side's visible set, When drawn, Then a building the side has seen stays on its map as last seen, with no activity shown (Westley, 2026-10-07: "#6: B"), and only that last-seen record is in the client's data; a building never seen is not drawn and its state is not in the client's data (R-089-03).
- R-205-03  Given an enemy production building in the visible set, When the player looks at it, Then he can see its focus family, which is what it is doing since production buildings are split by family (E-22 S-170, S-172; Westley, 2026-10-07).
- R-205-04  Given a building that is disguised or hidden, When an enemy sees it, Then what the enemy reads is what the disguise allows (E-22 S-172) [Q-159-09: how disguising or hiding works and what it costs].

Inputs: structure positions, layers and owners (E-11 S-204); each side's visible set.
Outputs: the structures in each side's visible set; what each seen production building shows.
Open flags: Q-159-09 (parked).

### S-206 — What a side has seen of the enemy's units
As a commander, I want my side to keep which kinds of enemy unit it has seen, so that production can answer them using only what the fog has revealed.

Design decided 2026-10-02, not scheduled for building.

Rules
- R-206-01  Given an enemy unit in a side's visible set, When visibility is computed, Then the side's record of enemy unit types seen includes that unit's type The record keeps no counts and never forgets, and the player is not shown it (Westley, 2026-10-07: "#7: Nothing recorded, players need to remember."); only the economy rules read it (R-206-03, R-206-04), and no side keeps a persistent view of the other (Westley, 2026-10-07: "persistent vision on the player is prohibited").
- R-206-02  Given the record, When it is read, Then it holds types and nothing about where they were: there is still no memory of last-seen positions (R-089-04) and no marker on screen.
- R-206-03  Given a side whose economy runs without a human in the seat, When the rules shift production toward what counters the enemy units that side has seen, Then they read this record and nothing else about the enemy (E-22 S-179, S-180).
- R-206-04  Given an enemy economy that scouts and counters (E-22 S-181), When it chooses what to build, Then it reads only its own side's record, built from its own side's visible set, never the real state of the player's side (Westley, 2026-10-07).

Inputs: each side's visible set (R-093-02).
Outputs: the per-side record of enemy unit types seen, read by E-22 S-179 to S-181.
Open flags: none.

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Sensor radius per unit | E-11 | 300 to 1000 wu at Tier 2 | |
| Interference field | E-17 map generation | [0, 1] per position and layer | values outside clamp |
| Cover geometry | E-17 | obstacle position, radius, height | |
| Vantage nodes | E-17 | position, radius | |
| Elevation gradient, era flags | E-17 (on land maps elevation and layers come from one height field, E-17 S-190), era pack | | |
| Structures | E-11 S-204 | Position, footprint, layer, owner | |
| Begin Mission | Player | | |

## Outputs

| Output | Observable where |
|---|---|
| Per-unit visible sets, player-visible list | Tick delta; T1 trace |
| Visible structures; per-side record of enemy unit types seen | Tick delta; T1 trace |
| Fog render, sensor circles, interference | Screen; T2 screenshots |
| Recon state | Screen; mission clock |

## Invariants

- Player-visible list ⊆ enemy units on the map.
- Friendly units always visible.
- What the player is shown never changes combat resolution; each side's own visible set does (R-093-02).
- Same seed, same visibility, all platforms.

## Scale requirements

Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is escalated): visibility for 1,000 units in under 2 ms per tick (shared with E-01); 10,000 in under 20 ms; must use spatial hashing, not all-pairs. The 10,000-unit figure is measured at the 10 ticks/s rate the sim drops to above 1,000 live units (E-13 R-099-03), a 100 ms tick; the 1,000-unit figure at 20 ticks/s. Workers are units and count in these figures (E-11 S-202).

## Look and behavior references

`references/E-12/notes.md`, missing: fog and interference treatments (2 to 5 screenshots).

## Ways this could be wrong

- Union computed from enemy units' sets instead of friendly.
- Interference sampled at the target instead of the observer (or neither).
- Fog applied during recon, or terrain hidden after Begin.
- Enemy AI reads the player's visible set.
- A unit fires at a target that no unit of its side sees.
- Visibility computed all-pairs and falls off a cliff at scale.
- Last-seen markers implemented as live positions.
- The record of enemy types seen fed from the real state of the enemy instead of from the side's visible set.
- An enemy building drawn or reported to the client while it is outside every sensor circle.

## Open ambiguity flags

Q-091-01, and from other epics Q-159-09. Details in `docs/northstar/ambiguity_register.md`.

## Depends on

- E-01 Layer system (cross-layer vision, the ping, going dark, cover by height).
- E-22 Economy and bases (what a seen building shows, disguise, the economy that reads the record of types seen).
- E-11 Units (sensor radii, acquisition, structures).
- E-17 Map generation (interference sources, cover, vantage, elevation).
- E-16 Client (fog render, recon phase UI).

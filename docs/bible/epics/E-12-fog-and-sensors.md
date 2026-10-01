# E-12 — Fog and Sensors

## Definition-completeness gate (run 2026-09-10)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Yes, 6 stories, 27 rules, numbers from `algorithms.md` ALG-65 and config. |
| Every input listed with range and rejection behavior | Yes, see Inputs. |
| Every output listed with where it is observable | Yes, see Outputs. |
| Implied-but-unstated behavior turned into flags | 4 new flags, Q-089-01, Q-090-01, Q-092-01, Q-094-01. |
| Every visible-surface story has a reference | **No.** S-094 (how fog and interference look) has a visible surface and no reference. |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed.** Blocked on 4 open flags and one missing reference. Cross-layer vision and the pulse are specified in E-01 (S-005, S-006) and referenced here, not duplicated.

## Purpose

The player sees only what their units can sense. Each unit reveals a circle around it, shrunk by whatever interference it is standing in, and the revealed map is the union of those circles. Enemies outside every circle do not exist on screen. Cover blocks sight by height (E-01 S-007). Other layers are seen at reduced range (E-01 S-005) or by pulse (E-01 S-006). Before the mission starts, the player sees all the terrain and none of the enemy; the moment the mission begins, fog falls. Fog is a player-information constraint only: the engine resolves combat identically whatever the player can see, and faction agents in the strategic sim see everything about their neighbors.

At launch there is no era-to-era difference in fog (Stage 1 A-321). The Settled Reach ships with the values below.

## Obviously working in 60 seconds

Place a Vanguard (sensor 700) and an enemy Raider at 650 wu on the same layer: the Raider is visible. Move the Raider to 750 wu: gone. Put the Vanguard inside an interference zone of intensity 0.5: the Raider at 400 wu is visible, at 400 wu plus one it is not. Move an enemy behind a tall asteroid: gone though in range. Start the recon phase: every obstacle, zone, and node is drawn and no enemy. Press Begin: the enemy positions vanish under fog. Same seed, same visibility sets.

## Stories

### S-089 — I see what my units see
As a commander, I want the map revealed only around my units, so that scouting is a job and the unknown is a threat.

Rules
- R-089-01  Given an observer with sensor radius r at interference i, When visibility is computed, Then its effective radius is r × (1 − i), and an enemy on the same layer is visible if its distance ≤ that radius and no cover blocks the line.
- R-089-02  Given every friendly unit's visible set, When the player's view is built, Then the player-visible enemy list is their union.
- R-089-03  Given an enemy not in the union, When drawn, Then it is not drawn, its HP bar is not drawn, and its position is not in the client's data.
- R-089-04  Given visibility, When computed, Then it is recomputed every tick from current positions; there is no memory of last-seen positions [Q-089-01].
- R-089-05  Given a friendly unit, When visibility is computed, Then friendly units are always visible to the player regardless of distance.
- R-089-06  Given visibility A sees B, When B's set is computed, Then B seeing A is computed independently (asymmetric sensors are normal).

Inputs: unit positions, layers, sensor radii; interference at each position; cover geometry.
Outputs: per-unit visible set and player-visible list in the tick delta; fog render.
Open flags: Q-089-01 (last-seen ghost markers, shared with Q-006-02). Q-E12-01 is closed: the seer is a roster unit, costly, with wide cross-layer sight and no attack; its cost and counter are tuned in the layer lab (Q-008-03) and it enters the roster with Q-082-03 to Q-082-05.

### S-090 — Hiding in the storm
As a commander, I want a zone of interference to shrink what units inside it can see and what outsiders can see into it, so that I can hide a force or fear one.

Rules
- R-090-01  Given a zone source with intensity 0.6 at its center and linear falloff to 0 at its radius, When sampled at half radius, Then interference is 0.3.
- R-090-02  Given overlapping zones, When sampled, Then the combined interference is clamped to [0, 1] [Q-090-01: sum vs max].
- R-090-03  Given an observer outside a zone looking at a target inside it, When visibility is computed, Then only the observer's own interference applies [Q-090-01: the bible says outsiders "can't see as far into the zone"; code samples the observer's position only].
- R-090-04  Given a zone source that moves over the mission, When ticks pass, Then interference at a fixed point changes as the source moves.
- R-090-05  Given a zone that varies by layer, When sampled, Then the value is per layer.

Inputs: gradient sources (position, radius, intensity, falloff, layer, motion).
Outputs: interference field; fog render density.
Open flags: Q-090-01.

### S-091 — Standing high
As a commander, I want an elevated position to see farther, so that vantage is worth taking.

Rules
- R-091-01  Given a unit within a vantage node's radius (default 100 wu), When visibility is computed, Then cross-layer factors double and extend one layer (E-01 R-005-06).
- R-091-02  Given an elevation tier difference of d between observer and target, When the era enables elevation sensor bonus, Then the observer's effective radius is multiplied by 1 + 0.15 · d [Q-092-01: nothing in code reads this].
- R-091-03  Given the Settled Reach, When elevation is read, Then it affects sensors only, never damage (E-11 R-084-06).

Inputs: vantage nodes; elevation gradient.
Outputs: effective radius.
Open flags: Q-092-01.

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

### S-093 — Fog is for the player, not the engine
As a commander, I want fog to change what I know and never what happens, so that a battle in the dark is still a fair battle.

Rules
- R-093-01  Given two identical battles differing only in the player's visibility, When resolved, Then the traces are identical.
- R-093-02  Given an enemy unit, When it acquires targets, Then it uses its own visible set with the same rules as the player's units.
- R-093-03  Given the strategic sim, When faction agents decide, Then they read every neighbor region's fields without fog (E-05).

Inputs: none.
Outputs: determinism trace.
Open flags: none.

### S-094 — How fog looks
As a commander, I want unexplored space, interference, and revealed ground to read differently at a glance, so that I know where I am blind.

Rules
- R-094-01  Given a T2 screenshot, When inspected, Then revealed area, fogged area, and interference zones are three distinguishable treatments.
- R-094-02  Given a unit inside interference, When drawn, Then its own sensor circle is visibly smaller.

Inputs: visibility; interference field.
Outputs: screen.
Open flags: Q-094-01 (is the sensor circle drawn at all; the HUD section never says). Reference required: `references/E-12/notes.md`, missing.

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Sensor radius per unit | E-11 | 300 to 1000 wu at Tier 2 | |
| Interference field | E-17 map generation | [0, 1] per position and layer | values outside clamp |
| Cover geometry | E-17 | obstacle position, radius, height | |
| Vantage nodes | E-17 | position, radius | |
| Elevation gradient, era flags | E-17, era pack | | |
| Begin Mission | Player | | |

## Outputs

| Output | Observable where |
|---|---|
| Per-unit visible sets, player-visible list | Tick delta; T1 trace |
| Fog render, sensor circles, interference | Screen; T2 screenshots |
| Recon state | Screen; mission clock |

## Invariants

- Player-visible list ⊆ enemy units on the map.
- Friendly units always visible.
- Visibility never changes combat resolution.
- Same seed, same visibility, all platforms.

## Scale requirements

Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is escalated): visibility for 1,000 units in under 2 ms per tick (shared with E-01); 10,000 in under 20 ms; must use spatial hashing, not all-pairs. The 10,000-unit figure is measured at the 10 ticks/s rate the sim drops to above 1,000 live units (E-13 R-099-03), a 100 ms tick; the 1,000-unit figure at 20 ticks/s.

## Look and behavior references

`references/E-12/notes.md`, missing: fog and interference treatments (2 to 5 screenshots).

## Ways this could be wrong

- Union computed from enemy units' sets instead of friendly.
- Interference sampled at the target instead of the observer (or neither).
- Fog applied during recon, or terrain hidden after Begin.
- Enemy AI reads the player's visible set.
- Visibility computed all-pairs and falls off a cliff at scale.
- Last-seen markers implemented as live positions.

## Open ambiguity flags

Q-089-01, Q-090-01, Q-092-01, Q-094-01. Details in `docs/northstar/ambiguity_register.md`.

## Depends on

- E-01 Layer system (cross-layer vision, pulse, cover by height).
- E-11 Units (sensor radii, acquisition).
- E-17 Map generation (interference sources, cover, vantage, elevation).
- E-16 Client (fog render, recon phase UI).

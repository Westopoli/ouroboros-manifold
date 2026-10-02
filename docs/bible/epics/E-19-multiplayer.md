# E-19 — Multiplayer and Lockstep Determinism

## Definition-completeness gate (run 2026-09-10)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Partly. 6 stories, 24 rules; the determinism and transport rules are concrete, the match-shape rules are placeholders pending Westley. |
| Every input listed with range and rejection behavior | Partly; see Inputs. |
| Every output listed with where it is observable | Yes, see Outputs. |
| Implied-but-unstated behavior turned into flags | 8 new flags, Q-139-01 through Q-144-02. |
| Every visible-surface story has a reference | **No.** S-144 (lobby and match flow) is a visible surface with no reference. |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed.** This epic is the largest design gap the Stage 1 audit found (vision_v2 cross-check flag 1; A-540 rewrite-and-promote). Multiplayer is core (vision_v2 Q1, Q3) and nothing below the transport layer is designed. The determinism decision (`docs/northstar/README.md`) and the Steam Datagram Relay findings (`docs/northstar/research/multiplayer_sdr.md`) are the only settled parts. Sim-core epics must respect S-139 from the first sprint even while the rest of this epic is open.

## Purpose

Ouroboros Manifold is a multiplayer strategic RTS. Every peer runs the same deterministic C simulation and exchanges only commands, so a match costs nothing to host and every player sees one galaxy and one battle. Matched players who all own the same era packs can play a match that traverses eras chronologically. What a match is, who commands what, and how the single-player generational loop becomes a shared one are the questions this epic exists to get answered.

Vision facts this epic must honor: full real-time, no pause in a match; the civilization has its own plans (agents run for every faction including human-commanded ones); bloodline and lineage are cosmetic; cross-era matches require the same era packs on every peer.

## Obviously working in 60 seconds

Two machines, one seed, one command stream captured from a 5,000-tick strategic run and a 5-minute tactical mission: byte-identical traces and checksums on Linux, Windows, and macOS. Two peers over the relay: a command issued on one appears in the other's tick delta on the same tick number, and a deliberately corrupted checksum on one peer is reported as a desync within 10 ticks.

## Stories

### S-139 — One sim, every machine
As a player, I want every peer to compute exactly the same galaxy and battle, so that we are all in one world.

Rules
- R-139-01  Given the C simulation, When built on Windows, macOS, and Linux with the project's fixed compiler flags (no fast-math), When run with the same seed and command stream, Then the trace is byte-identical.
- R-139-02  Given the sim, When it uses floating point, Then every operation is IEEE-754 double with a fixed evaluation order; no platform math library is called for transcendental functions without a deterministic implementation.
- R-139-03  Given every 10 ticks, When a checkpoint is reached, Then a checksum over all region fields, faction state, RNG state, unit store, and queue is emitted.
- R-139-04  Given two peers' checksums differ at a checkpoint, When detected, Then both peers are notified within 10 ticks with the tick number and the first differing field.
- R-139-05  Given a determinism test, When run in CI, Then it diffs traces across the three platforms and fails on any difference.

Inputs: seed; command stream; platform.
Outputs: trace; checksums; desync report.
Open flags: none. This is the determinism decision, already made.

### S-140 — Commands over the wire
As a player, I want my orders to reach every peer with no server in the middle, so that matches are cheap and private.

Rules
- R-140-01  Given a match, When peers connect, Then they connect peer to peer over the Steam Datagram Relay with a direct-connect fallback negotiated by the API.
- R-140-02  Given a tactical tick, When commands are exchanged, Then each peer's commands for tick t + d are sent on a reliable channel and every peer applies all peers' commands for tick t in a fixed peer order before advancing [Q-140-01: the input delay d and the stall rule].
- R-140-03  Given a peer that has not delivered its commands for tick t, When the deadline passes, Then every peer stalls until they arrive or the peer is dropped after [Q-140-01] seconds.
- R-140-04  Given a dropped peer, When the match continues, Then its units [Q-140-02: stand idle, or its faction's agent takes over].
- R-140-05  Given the handshake, When measured, Then it completes within 5 s in the common case.

Inputs: peer commands; relay.
Outputs: lockstep tick advance; stall and drop events.
Open flags: Q-140-01, Q-140-02.

### S-141 — What a match is
As a player, I want to know what my friends and I are doing together in this galaxy, so that we can play it.

Rules
- R-141-01  Given a match, When it starts, Then [Q-141-01: the match shape: co-op commanders in one civilization, opposing commanders in different civilizations, or both, and how many].
- R-141-02  Given a match, When missions are generated, Then [Q-141-02: one shared mission with several commanders, or one mission per commander paired into a shared tactical map; relates to Q-079-01].
- R-141-03  Given a match, When the time jump runs, Then every peer runs the same jump from the same state and the chronicle prints the same entries.

Inputs: lobby settings.
Outputs: match state.
Open flags: Q-141-01, Q-141-02.

### S-142 — No pause, no rewind, no cheating the clock
As a player, I want a match that cannot be paused or rolled back by anyone, so that time is fair.

Rules
- R-142-01  Given a multiplayer match, When any player presses pause, Then the game does not pause; the menu opens without stopping the sim.
- R-142-02  Given a match, When the chronicle scroll runs, Then Proceed requires [Q-142-01: all peers, the host, or a majority].
- R-142-03  Given the sim, When fog is applied, Then each peer's client renders only its own faction's visible set, but every peer's sim has the full state; the state is not secret, the presentation is [Q-142-02: is that acceptable against memory-reading cheats at launch].

Inputs: player inputs.
Outputs: match flow.
Open flags: Q-142-01, Q-142-02.

### S-143 — Eras in sequence
As a player, I want a match with friends who own the same era packs to move chronologically through eras, so that a campaign spans history.

Rules
- R-143-01  Given a lobby, When era packs are compared, Then the match may traverse only eras every peer owns, in chronological order.
- R-143-02  Given an era transition in a match, When it happens, Then it is a time jump whose destination era is the next owned era and the shared skeleton carries every system across (E-20).
- R-143-03  Given a peer lacks a pack, When the lobby forms, Then the match is limited to the common set and the lobby says so.

Inputs: ownership per peer.
Outputs: lobby state; era sequence.
Open flags: none new; the mechanism is E-20's.

### S-144 — Lobby and match flow
As a player, I want to find a match, invite friends, and get into the game, so that multiplayer is not a chore.

Rules
- R-144-01  Given the main menu, When Multiplayer is chosen, Then the player can host, join by invite, or [Q-144-01: matchmaking scope at launch].
- R-144-02  Given a lobby, When shown, Then it lists peers, their owned eras, the common era set, the seed, and the difficulty owner (Q-079-01).
- R-144-03  Given a universe (a multiplayer campaign) is created, When its configuration is set, Then the player count, the slots, the era packs, and the paired economic roles are locked; a later session continues it only with the same number of players in the same slots with the same eras, otherwise a new universe starts; the campaign save is written identically on every peer [Q-144-03: who may host the next session].

Inputs: Steam friends; lobby.
Outputs: lobby screen; match start.
Open flags: Q-144-01, Q-144-03. Reference required: `references/E-19/notes.md`, missing.

### S-159 — A real economy: run by a partner, or running itself

As a commander, I want a real economy behind my war, run well for me by rules when I fight alone and run by a partner when I choose to, so that the base I protect is alive, grows while I fight, and what I can field is something we earned.

Design decided by Westley, 2026-10-01 (`docs/northstar/research/economy_design/`, his words verbatim in its README). Not scheduled for building, and not Ready: the rules below state what the system is, and they are cut into testable rules when the open flags close.

Rules
- R-159-01  The economy seat. An optional mode, entered only through the paired queue, where teams of 2, 4 or 6 form from pairs; in a pair one player commands the military and the other runs the economy, both on the same tactical map. A universe locks its player count, slots and eras at creation. The seat's target is two to three times the system complexity of a proficient StarCraft 2 economy. Its skill is holding several things in mind at once, where forgetting one (the population cap, worker production, the next technology, production) puts the pair behind; nothing on screen lists what the commander needs. Speed of hand gives a small bounded edge, about 1.1x to 1.2x (Q-159-05).
- R-159-02  Running itself. The same economy is present in every match. When nobody holds the seat, rules run it for the player, and run it well; no intelligent agent is needed. The base is a spectacle in every mode: buildings start under construction and rise, expansions are made, and population density changes over time (E-17 S-166). How the rules decide is open (Q-159-02); what a solo commander may place is open (Q-159-03).
- R-159-03  Resources and workers. Three resources, each gathered in its own way, on the model of classic Age of Empires Online and Age of Empires 3. Literal workers are trained at the base and walk to a source. Economic buildings include drop-off points, and the farther workers walk to a drop-off the less they bring in. Which resources they are is open (Q-159-08).
- R-159-04  Buildings. The economy player places buildings; lots are limited and what stands beside a building changes what it yields. He also builds the defenses: walls, gates and towers, against raids on workers and shipments that come along lanes set by the terrain.
- R-159-05  Population. One cap is shared by workers and soldiers. It is upgradeable a long way, up to thousands (hub "Reference Hardware", the long-term scale goal).
- R-159-06  Production. The economy player runs the production buildings and makes the units the commander receives; what to make is agreed by talking. Production is planned ahead on a schedule, and changing what a building is focused on takes a while.
- R-159-07  Counters. Unit families counter each other, and specific unit roles need specific resources, so heavy gathering of one resource shows which role a side is making more of, and the other side needs the counter (Q-159-08). An enemy who sees a production building can see what it is doing, so players have a way to disguise or hide their buildings (Q-159-09).
- R-159-08  Technology. Technology choice belongs to the economy player.
- R-159-09  Bases. Every side has a base of operations it must protect. It is not always a city. It receives resources from elsewhere, generates them on site, or both, depending on the simulation and the mission (Q-159-06). Settlements on the map can be grown into further bases. The main base never runs dry, but a side that stays home and does not expand is out-produced and overrun. Production can be built forward, near the front or at an expansion, where it reinforces fast and is exposed. What happens when one falls is R-159-14.
- R-159-10  The map. Economic locations are placed throughout the map, and the significant resources are placed opposite the objective, so a side picks one or fights for both. A neutral populace lives in settlements on the map and is contested; winning it is not the economy player's job.
- R-159-11  Shipments. The civilization sends shipments to the base. The side has no vision of a shipment on its way, and one that does not arrive gives no explanation.
- R-159-12  Weather. Specific regions have specific environmental troubles. A trouble travels across the map where both sides can see it and shuts down what it passes over.
- R-159-13  The city grows during a mission (Q-159-04). What the pair carries forward between missions is open; the economy is not assumed to persist through a time jump (Q-159-07).
- R-159-14  When a base falls. A base of operations is occupied, not destroyed: the side that takes it gets its production and its people, and the side that lost it can take it back. A side that still holds an expansion or a forward base falls back to it as its base of operations. Once a side has lost its original main base, the best result it can get from the mission is partial failure (E-10 S-077).
- R-159-15  What kind of base. The mission archetype (E-10 S-073) and the supply distance in the simulation together decide the kind of base each side is given.
- R-159-16  Resources and the situation. Base, objective and the significant resources are usually three separate places, not always. Resources are sometimes limited and sometimes abundant, consistent with the situation the simulation gives and slanted by it (a defender has the better position), and the player always has the means to accomplish the mission even when it is hard. The resources are not scored separately: a side that ignores them is overrun unless it rushes and finishes fast. Spending is balanced between economy, technology and army.
- R-159-17  Strongpoints. The reinforcement structures of E-15 S-126 are strongpoints at the slopes between height bands (E-17 R-166-04). Holding one holds the way up or down and gives production on that band.

Inputs: none yet.
Outputs: none yet.
Open flags: Q-159-02, Q-159-03, Q-159-07, Q-159-08, Q-159-09, Q-159-10.

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Peer commands | Peers | signed, tick-stamped | wrong tick, unknown peer, malformed: dropped and logged |
| Seed and lobby settings | Host | | |
| Era ownership | Steam | | |

## Outputs

| Output | Observable where |
|---|---|
| Trace, checksums, desync reports | T1 trace |
| Lockstep tick advance, stalls, drops | Network log; screen |
| Lobby | Screen |

## Invariants

- No peer ever applies a command another peer has not applied for the same tick.
- Checksums identical across peers at every checkpoint of a healthy match.
- No pause and no rewind in a match.

## Scale requirements

Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is escalated): 4 peers; 200 ms command latency tolerated with input delay; 5,000-tick jump identical across peers.

## Look and behavior references

`references/E-19/notes.md`, missing.

## Ways this could be wrong

- Platform math library divergence in sin or pow.
- Hash-map iteration order leaking into the sim.
- Peer order differing between peers.
- Chronicle assembler seeded from local time.
- Pause implemented as sim stop.
- Direct-connect fallback missing, so far-from-relay players get worse ping.

## Open ambiguity flags

Q-140-01, Q-140-02, Q-141-01, Q-141-02, Q-142-01, Q-142-02, Q-144-01, Q-144-02, Q-159-02, Q-159-03, Q-159-07, Q-159-08, Q-159-09, Q-159-10. Details in `docs/northstar/ambiguity_register.md`.

## Depends on

- Every sim epic (determinism), E-08 and E-10 (match flow and missions), E-16 (lobby, pause), E-20 (era packs).
- S-159's economy also touches E-10 and E-15 (what a fallen base means for outcomes, R-159-14, and what the reinforcement structures become, R-159-17; both epics are rewritten to match in the epics pass), E-11 (unit roles and their resources) and E-17 (S-166, the settlement generator). Its self-running form (R-159-02) also touches E-02 (region economic field, the data it grows from), E-16 (world view, where it would render), and E-17 and E-18 (the cheap, procedural, LOD-disciplined visual approach it should follow). It is recorded here because the idea started as a multiplayer-mode question, not because E-19 is necessarily its final home; a later Stage 2 pass may move S-159 or split it once it is scoped for real.

# E-19 — Multiplayer and Lockstep Determinism

## Definition-completeness gate (run 2026-09-10)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Partly. 9 stories, 33 rules; the determinism and transport rules are concrete, the match-shape rules are placeholders pending Westley, and the paired-mode stories (S-159, S-241, S-242) carry numbers as flags. |
| Every input listed with range and rejection behavior | Partly; see Inputs. |
| Every output listed with where it is observable | Yes, see Outputs. |
| Implied-but-unstated behavior turned into flags | 1 open flag: Q-144-03 (S-144). |
| Every visible-surface story has a reference | **No.** S-144 (lobby and match flow) is a visible surface with no reference. |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed.** Blocked on the 1 open flag listed at the foot and one missing reference (S-144). This epic is the largest design gap the Stage 1 audit found (vision_v2 cross-check flag 1; A-540 rewrite-and-promote). Multiplayer is core (vision_v2 Q1, Q3). Below the transport layer, the paired mode's team sizes are decided (S-241); a match is co-op only at launch (R-141-01). The determinism decision (`docs/northstar/README.md`) and the Steam Datagram Relay findings (`docs/northstar/research/multiplayer_sdr.md`) are the only settled parts. Sim-core epics must respect S-139 from the first sprint even while the rest of this epic is open.

Built ahead of the gate under the visible game programme's waiver (Westley, 2026-10-07).

## Purpose

Ouroboros Manifold is a multiplayer strategic RTS. Every peer runs the same deterministic C simulation and exchanges only commands, so a match costs nothing to host and every player sees one galaxy and one battle. Matched players who all own the same era packs can play a match that traverses eras chronologically. Teams of 2 and 4 play together, and teams of 6 are a desired future feature: each player is a sub-commander, each pair a sub-civilization inside the over-arching civilization, and more players means a bigger map with more to do, more resources and more enemies. What a match is, who commands what, and how the single-player generational loop becomes a shared one are the questions this epic exists to get answered.

Vision facts this epic must honor: full real-time, no pause in a match; the civilization has its own plans (agents run for every faction including human-commanded ones); bloodline and lineage are cosmetic; cross-era matches require the same era packs on every peer.

## Obviously working in 60 seconds

Two machines, one seed, one command stream captured from a 5,000-tick strategic run and a 5-minute tactical mission: byte-identical traces and checksums on Linux, Windows, and macOS. Two peers over the relay: a command issued on one appears in the other's tick delta on the same tick number, and a deliberately corrupted checksum on one peer is reported as a desync within 10 ticks.

## Stories

### S-139 — One sim, every machine
As a player, I want every peer to compute exactly the same galaxy and battle, so that we are all in one world.

Direction changed 2026-10-02, rewrite pending: the economy's state is part of what every peer must agree on (R-139-06), which widens the checksum of R-139-03. The rules below are what the game does today.

Rules
- R-139-01  Given the C simulation, When built on Windows, macOS, and Linux with the project's fixed compiler flags (no fast-math), When run with the same seed and command stream, Then the trace is byte-identical.
- R-139-02  Given the sim, When it uses floating point, Then every operation is IEEE-754 double with a fixed evaluation order; no platform math library is called for transcendental functions without a deterministic implementation.
- R-139-03  Given every 10 ticks, When a checkpoint is reached, Then a checksum over all region fields, faction state, RNG state, unit store, and queue is emitted.
- R-139-04  Given two peers' checksums differ at a checkpoint, When detected, Then both peers are notified within 10 ticks with the tick number and the first differing field.
- R-139-05  Given a determinism test, When run in CI, Then it diffs traces across the three platforms and fails on any difference.
- R-139-06  Given the economy of every side (resources, workers, buildings, production schedules, shipments, weather, and the growth of settlements), When a checkpoint is reached, Then the checksum covers it, and a difference in it is reported as any other (R-139-04).

Inputs: seed; command stream; platform.
Outputs: trace; checksums; desync report.
Open flags: none. This is the determinism decision, already made.

### S-140 — Commands over the wire
As a player, I want my orders to reach every peer with no server in the middle, so that matches are cheap and private.

Rules
- R-140-01  Given a match, When peers connect, Then they connect peer to peer over the Steam Datagram Relay with a direct-connect fallback negotiated by the API.
- R-140-02  Given a tactical tick, When commands are exchanged, Then each peer's commands for tick t + d are sent on a reliable channel and every peer applies all peers' commands for tick t in a fixed peer order before advancing The input delay d is 3 tactical ticks (150 ms) (Westley, 2026-10-06).
- R-140-03  Given a peer that has not delivered its commands for tick t, When the deadline passes, Then every peer stalls until they arrive or the peer is dropped after 30 seconds (Westley, 2026-10-06; the deadline is 1 second). The lockstep backend spec of 2026-10-05 holds the drop at 60 seconds as a provisional setting, which this supersedes.
- R-140-04  Given a dropped peer that held an economy seat, When the match continues, Then the rules that run an economy with nobody in the seat take the seat (E-22 S-179, S-181); Given any other dropped peer, Then its units stand idle, and every other player is alerted to the disconnection; a disconnected player's problem is theirs, not the team's to solve (Westley, 2026-10-06).
- R-140-05  Given the handshake, When measured, Then it completes within 5 s in the common case.
- R-140-06  Given a lockstep match, When the two simulations disagree on a tick's checksum, Then the view shows 'Desync at tick N, section S' with no Retry and the match ends (Architect, 2026-10-09).
- R-140-07  Given a match, When the player chooses End Mission, Then the view leaves the match (NetMatch.leave) and the peer sees the stall overlay until the drop timer of R-140-03; the orders a player can send in a match are move, attack-move and attack a target (the match verbs), no others (Architect, 2026-10-09).

Inputs: peer commands; relay.
Outputs: lockstep tick advance; stall and drop events.
Open flags: none.

### S-141 — What a match is
As a player, I want to know what my friends and I are doing together in this galaxy, so that we can play it.

Rules
- R-141-01  Given a match, When it starts, Then it is played by teams of 2 or 4 (S-241), and it is co-op only at launch, the commanders of a team being in one civilization. Versus waits for demand, and the simulation is bent to allow it then (Westley, 2026-10-04).
- R-141-02  Given a match, When missions are generated, Then the team has one shared mission, and its force is not split among the players: the number of units rises with the players, so a player never has fewer units in multiplayer than alone (Westley, 2026-10-04); within a team, a pair is one commander and one economy player on the same tactical map (R-159-01).
- R-141-03  Given a match, When the time jump runs, Then every peer runs the same jump from the same state and the chronicle prints the same entries.

Inputs: lobby settings.
Outputs: match state.
Open flags: none.

### S-142 — No pause, no rewind, no cheating the clock
As a player, I want a match that cannot be paused or rolled back by anyone, so that time is fair.

Rules
- R-142-01  Given a multiplayer match, When any player presses pause, Then the game does not pause; the menu opens without stopping the sim.
- R-142-02  Given a match, When the chronicle scroll runs, Then Proceed requires all peers (Westley, 2026-10-06).
- R-142-03  Given the sim, When fog is applied, Then each peer's client renders only its own faction's visible set, but every peer's sim has the full state; the state is not secret, the presentation is. A cheat tool that reads memory can see hidden state; this is a known gap, accepted at launch (Westley, 2026-10-06) because the launch match is co-op against the game's own enemy, and it is revisited if versus is added.

- R-142-04  Given a pair (one faction on one tactical map), When fog is applied, Then a setting the players switch on and off chooses between shared vision and vision for each player's own units only. Technically both players are the same civilization and all the units are shared, and the split is offered if players like it (Westley, 2026-10-04) The default is shared vision, set by the pair together in the lobby and fixed with the universe (Westley, 2026-10-06). Shipments (E-22 S-176) and disguise (E-22 S-172) read the setting.

Inputs: player inputs.
Outputs: match flow.
Open flags: none.

### S-143 — Eras in sequence
As a player, I want a match with friends who own the same era packs to move chronologically through eras, so that a campaign spans history.

Rules
- R-143-01  Given a lobby, When era packs are compared, Then the match may traverse only eras every peer owns, in chronological order.
- R-143-02  Given an era transition in a match, When it happens, Then it is a time jump whose destination is the first later era, in chronological order, that every peer owns: an era not owned by every peer is skipped, and the check runs down the line of eras until one is found; if no later era is owned by every peer the time jump is cancelled and the team stays in the current era (Westley, 2026-10-06). The shared skeleton carries every system across (E-20).
- R-143-03  Given a peer lacks a pack, When the lobby forms, Then the match is limited to the common set and the lobby says so; once a universe is locked, R-144-03 governs instead.

Inputs: ownership per peer.
Outputs: lobby state; era sequence.
Open flags: none new; the mechanism is E-20's.

### S-144 — Lobby and match flow
As a player, I want to find a match, invite friends, and get into the game, so that multiplayer is not a chore.

Rules
- R-144-01  Given the main menu, When Multiplayer is chosen, Then the player can host, join by invite, or find a game in a public lobby list; there is no skill matchmaking at launch (Westley, 2026-10-06).
- R-144-02  Given a lobby, When shown, Then it lists peers, their owned eras, the common era set, the seed, the difficulty owner (Q-079-01), and each pair with which of its two players commands and which runs the economy.
- R-144-03  Given a universe (a multiplayer campaign) is created, When its configuration is set, Then the player count, the slots, the era packs, the paired economic roles, and the switches the rules use that change the simulation (whether the unit-mix behaviours of E-22 S-180 are on, and whether the enemy's economy scouts, counters and disguises, E-22 S-181) are locked; a later session continues it only with the same number of players in the same slots with the same eras, otherwise a new universe starts; the campaign save is written identically on every peer [Q-144-03: who may host the next sitting of a locked universe].

Inputs: Steam friends; lobby.
Outputs: lobby screen; match start.
Open flags: Q-144-03. Reference required: `references/E-19/notes.md`, missing.

### S-159 — The paired mode: a partner who runs my economy
As a commander, I want to play with a partner who runs the economy behind my war, so that what I can field is something we earned and the two of us have to talk.

Design decided 2026-10-01 and 2026-10-02, not scheduled for building. This story is the paired mode itself; the economy it runs and the economy that runs without a partner are E-22.

Rules
- R-159-01  The economy seat. An optional mode, entered only through the paired queue, where teams of 2 or 4 form from pairs, and teams of 6 are a desired future feature (S-241); in a pair one player commands the military and the other runs the economy, both on the same tactical map. A universe locks its player count, slots and eras at creation. The seat's target is two to three times the system complexity of a proficient StarCraft 2 economy. Its skill is holding several things in mind at once, where forgetting one (the population cap, worker production, the next technology, production) puts the pair behind; nothing on screen lists what the commander needs. Speed of hand gives a small bounded edge, about 1.1x to 1.2x (Q-159-05).

The economy itself is E-22 Economy and Bases, stories S-167 to S-182: what the seat runs (S-167 to S-178), what happens when a base falls (S-178), the economy run by rules when nobody holds the seat (S-179, S-180) and the enemy's economy (S-181). Strongpoints and moving weather are E-15. The teams, sub-commanders and sub-civilizations are S-241; the pair on the wire is S-242; the economy seat's screen is E-16 S-230.

Inputs: the paired queue; the two seats.
Outputs: a team of pairs, each on one tactical map.
Open flags: none here; the economy's own flags are E-22's.

### S-241 — Teams, sub-commanders and sub-civilizations
As a player in a team, I want my pair to be a sub-civilization inside the over-arching civilization, with the map, the resources and the enemies growing as players join, so that more friends make a bigger game.

Design decided 2026-10-02 (DECISIONS H7, H13); the lobby's team-size choice builds as VG-F-S241 (visible-game spec rev 13, 2026-10-19), a stub until R-241-03 scaling (ledger row FU-F-teamsize-scaling). Teams of 6 are a desired future feature that waits on a higher peer count than the confirmed 4 (R-241-04). Westley, 2026-10-02: "more teammates = bigger maps and more to do, more resources, more enemies, each player is their own "sub-commander" and we can fabricate "alliances" where each pair of players is their own "sub-civlization" inside the over-arching civlization. essentially the game turned up to 11."

Rules
- R-241-01  Given the paired queue, When a team forms, Then it has 2 or 4 players, in pairs (R-159-01). Teams of 6 are a desired future feature (R-241-04).
- R-241-02  Given a team, When it plays, Then each player is a sub-commander and each pair is a sub-civilization inside the over-arching civilization: a pair has its own economy (its own base, resources, population cap and ledger), the sub-commander title covers both seats, and the pairs read as highly collaborative, cohesive factions more than one civilization (Westley, 2026-10-04).
- R-241-03  Given more players in a team, When the map and mission are made, Then the map is bigger, there is more to do, there are more resources and there are more enemies, and the number of units rises with the players and is never lower than in single player (R-141-02); Given 4 to 6 players, Then the canvas is 64,000 wu, and smaller matches keep today's sizes (E-17 S-166) Enemy force, the amount to do and the resources scale in step with the number of pairs (Westley, 2026-10-06).
- R-241-04  Given the match runs on lockstep, When a team forms, Then every player is a peer, and the confirmed scale figure is 4 peers, so a team has 2 or 4 players. More than 4 peers, and so teams of 6, are a desired future feature that waits on a higher peer count (Westley, 2026-10-02: "we can keep 4, so long as more is marked as a desired future feature").

Inputs: the pairs in the queue.
Outputs: a team and its map.
Open flags: none.

### S-242 — A pair on the wire
As a player in a pair, I want my building, scheduling and requests to reach my partner's machine as commands like any other, so that we play one economy and one war.

Design decided 2026-10-02, not scheduled for building.

Rules
- R-242-01  Given the economy seat, When the player places or queues a building, sets the production schedule, chooses technology or changes the doctrine, Then each is a peer command, signed and stamped with its tick, applied on every peer in the fixed peer order (R-140-02).
- R-242-02  Given the commander seat, When the player turns the dial, changes the doctrine, switches a unit-mix behaviour, asks by pointing at the map, or gives a military order, Then each is a peer command in the same way (E-16 S-231).
- R-242-03  Given a command from a seat for something that seat does not do, When it arrives, Then it is dropped and logged like any malformed command. Roles are strict: the economy seat never gives a military order and the commander seat never gives a building order (Westley, 2026-10-04; E-22 S-180 says a solo commander never places or queues).
- R-242-04  Given a pair, When the rules run any part of the economy (a seat vacated, the enemy's economy), Then every peer runs the same rules from the same state (S-139).

Inputs: commands by seat.
Outputs: the same economy on every peer; dropped-command log.
Open flags: none. The cost the economy adds to a tick and to the checkpoint checksum in a team of 4, and later of 6, is set after the first prototype (Westley, 2026-10-06); E-13 R-099-03 halves the tick rate above 1,000 live units, which changes what 3 ticks of input delay means.

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Peer commands | Peers | signed, tick-stamped | wrong tick, unknown peer, malformed: dropped and logged |
| Economy and commander commands (build, queue, schedule, technology, doctrine, dial, unit-mix switch, request by pointing) | Pair seats | by seat (S-242) | a command the seat does not give: dropped and logged |
| Pairing and roles | Paired queue | pairs of two; teams of 2 or 4 | a team of another size is not formed |
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
- Every peer's economy state is identical at every checkpoint of a healthy match.
- Everything that changes the simulation is in the universe lock, and nothing outside it can differ between peers.

## Scale requirements

Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is escalated): 4 peers; 200 ms command latency tolerated with input delay; 5,000-tick jump identical across peers. More than 4 peers, and so teams of 6, are a desired future feature that waits on a higher peer count (Westley, 2026-10-02). Nothing is confirmed beyond 4 peers.

## Look and behavior references

`references/E-19/notes.md`, missing.

## Ways this could be wrong

- Platform math library divergence in sin or pow.
- Hash-map iteration order leaking into the sim.
- Peer order differing between peers.
- Chronicle assembler seeded from local time.
- Pause implemented as sim stop.
- A switch that changes the economy missing from the universe lock, so peers differ.
- Economy state missing from the checksum, so a desync in it goes unseen.
- Direct-connect fallback missing, so far-from-relay players get worse ping.
- Known gap, accepted at launch: every peer's sim holds the full state, so a memory-reading cheat sees hidden enemy positions (R-142-03).

## Open ambiguity flags

Q-144-03. The economy's flags (Q-159-07 to Q-159-10 and the rest) are E-22's. Details in `docs/northstar/ambiguity_register.md`.

## Depends on

- Every sim epic (determinism), E-08 and E-10 (match flow and missions), E-16 (lobby, pause), E-20 (era packs).
- E-22 (the economy a pair runs, S-167 to S-181), E-15 (strongpoints and weather), E-17 (S-166, the settlements, landscape and 64,000 wu canvas), E-10 (what a fallen base means for outcomes), E-16 (the economy seat's screen and the commander's controls, S-230 to S-233).

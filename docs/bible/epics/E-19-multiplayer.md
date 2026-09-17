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
- R-144-03  Given a match ends, When peers return, Then the campaign save is written identically on every peer [Q-144-02: shared campaign persistence].

Inputs: Steam friends; lobby.
Outputs: lobby screen; match start.
Open flags: Q-144-01, Q-144-02. Reference required: `references/E-19/notes.md`, missing.

### S-159 — Someday: a paired command-and-economy multiplayer mode

As a group of friends, we may someday want a match where each team of two splits military and economic command, so that mastering the economy takes as much sustained effort as mastering the fight.

Rules
- R-159-01  Deferred (Q-159-01). No rule at launch. Recorded so the idea is not lost: an optional multiplayer mode, separate from the core commander game, where players queue in pairs and teams of 2, 4, or 6 form from one or more pairs; within a pair, one player commands the pair's military force using the existing tactical and layer system, and the other manages the pair's economy (production, resources, construction, base layout); the economy role's target complexity is roughly two to three times the sustained workload of a proficient StarCraft 2 economy player, so that it demands as much of the player's attention as the military role demands of theirs. Exact economy mechanics are unspecified; the reference games (StarCraft 2 for supply and production pressure, Age of Empires 2 for multi-resource and building management) are starting points for research, not a design. This mode does not change the core single-commander game (hub "The Player's Toolkit": no economy, no base building); it is an additional mode that sits beside it.

Inputs: none yet.
Outputs: none yet.
Open flags: Q-159-01.

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

Q-140-01, Q-140-02, Q-141-01, Q-141-02, Q-142-01, Q-142-02, Q-144-01, Q-144-02, Q-159-01. Details in `docs/northstar/ambiguity_register.md`.

## Depends on

- Every sim epic (determinism), E-08 and E-10 (match flow and missions), E-16 (lobby, pause), E-20 (era packs).

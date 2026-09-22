# Work inventory for the two-day push (2026-09-22)

Westley (2026-09-22, verbatim): "I've found myself with 2 days of essentially unlimited usage. ... Your task is to figure out what we can have masses of claude sub-agents in manager-mode cascades in order to get as much done as possible ... all backend code and simple placeholders, no polish ... Your job is really just to do what you can so that I'm the blocker, not the code being written. ... agents will work in parallel on individual pieces, and we'll fit the pieces together when they finish into the 'main' prototype. We'll start with the ultimately simple version of the game, just the main menu, and slowly tack on functionality (always checking that nothing breaks with QA)."

This file is the gathered work: what exists, what is buildable now without Westley, what each piece's interface is, and what only Westley can unblock. The method (waves, integration, straggler rule) is planned separately in plan mode.

## 1. Facts the inventory rests on

- **Bible:** 160 stories, 21 epics, ALG-01..ALG-75 contiguous with constants. Every epic has a scale-requirements section. Gate passed: E-02, E-03, E-04, E-05. The register has 27 open flags; 40 catalog rows said "blocked on Q-" against flags that are closed (refreshed today), so the real blocked set is 11 stories, all in E-19, E-20, E-21.
- **C sim:** 8 files. Real: `region.c`, `sim.c` (E-02), `faction.c`, `agent.c`, `resolve.c` (E-05). Pure stub: `events.c` (18 functions), `collision.c` (2), `friction.c` (4). No C for E-03, E-06..E-15, E-17. Tick loop today: events, 3a-3f with collisions, friction, admin revolts, drift; diplomacy, technology and lifecycle have feature flags but no step.
- **Tests:** 616 test functions across E-02..E-17 (E-16 has none), 119 controls (92 placeholders), all fenced. `tests/qa/t1/` has the desync detector and two trace detectors.
- **Cards:** 164 regenerated per story for E-03 and E-06..E-17 in scratch (R25); symbol ownership draft `docs/northstar/spec_factory/symbol_modules.toml`.
- **Python reference:** every system exists in `simulation/` (tactical engine 3,100 lines, missions 1,450, map generation 1,575, generational 1,263, chronicle 923, transport and saves 2,019).
- **Client:** main menu, new game, load game, onboarding, settings, era library, briefing, debrief, tutorial and privacy modal are self-contained (no sim reference). Galaxy view and time-jump sequencer (5,181 lines) and every tactical scene are coupled to the old Python sim through `SimBridge` and `TacticalBridge` (4-byte length-prefixed JSON pipe, sim to Godot only, commands through a polled temp file). No C transport exists; `docs/architecture.md` describes only Python payload extensions.
- **QA:** `projects/ouroboros/qa.toml` points at `scenes/harness/e02_harness.tscn`, which does not exist; no ouroboros campaign; the desktop backend, verbs, director and planted-control machinery exist and passed on the toy scene.
- **Content:** Settled Reach pack with 21 unit glbs and 3 asteroids; a test era with three placeholder units; no validator.

## 2. Pieces buildable now without Westley

A piece is one module or scene with a fenced test set and a named interface. "Interface" is what the integrator relies on; "size" is the Python reference's line count and the test count as effort proxies.

### Sim backend (C, tests exist, briefs exist as regenerated cards)

| Piece | Module | Epic, stories | Interface | Size | Blocks |
|---|---|---|---|---|---|
| B1 events | `events.c` | E-04 S-026..S-030 (Tested) | 18 header functions; `om_step_events` in the tick (wired) | 749 py lines, 31 tests | none |
| B2 collisions | `collision.c` | E-05 S-039 (R-039-05 skipped under Q-039-01) | `om_step_collisions`, `om_tick_collisions` | ALG-23/24, 6 tests | Q-039-01 for one rule only |
| B3 friction and admin revolts | `friction.c` | E-05 S-040, S-041 | `om_step_friction`, `om_step_admin_revolts`, two read-backs | ALG-25, ALG-29, tests in E-05 | none (flags closed) |
| B4 world generation | `worldgen.c` | E-03 S-021..S-025 (Ready) | 12 header declarations already exist and are undefined; `om_world_generate` | 217+ py lines, 28 tests | none |
| B5 diplomacy and technology | `diplomacy.c` | E-06 S-042..S-048 | `om_step_diplomacy` (4.25), `om_step_technology` (4.5) to wire; 33 symbols | 368 py lines, 42 tests | two symbols lack ctypes mirrors (R22) |
| B6 lifecycle | `lifecycle.c` | E-07 S-049..S-053 | `om_step_lifecycle` (6) to wire; 15 symbols | 51 py lines plus tick.py parts, 28 tests | none |
| B7 generational | `generational.c` | E-08 S-055..S-064 | 101 symbols, time jump, character selector, ledger; owns `om_time_jump_run` | 1,263 py lines, 50 tests | S-063 needs a reference (UI only) |
| B8 chronicle | `chronicle.c` | E-09 S-065..S-071 | 69 symbols; distiller and assembler over the fragment library | 923 py lines, 39 tests | S-069 reference (UI only) |
| B9 missions | `mission.c` | E-10 S-072..S-080 | 87 symbols; generator, objectives, outcome resolver, force allocator, briefing | 1,450 py lines, 45 tests | S-079 reference (UI only) |
| B10 units and combat | `unit.c` | E-11 S-081..S-088 | 61 symbols; owns the tactical orchestrator `om_tactical_tick` (a second orchestrator for closure) | 1,128 py lines (unit, damage, ability, facing), 45 tests | S-088 reference (UI only) |
| B11 fog | `fog.c` | E-12 S-089..S-094 | 46 symbols; `om_visibility_compute` | 121 py lines, 23 tests | S-094 reference (UI only) |
| B12 movement and command | `tactical_move.c` | E-13 S-095..S-102 | 47 symbols; `om_command_move`, `om_unit_get_pos` | 1,038 py lines (movement, command, ingest), 35 tests | S-101 reference (UI only) |
| B13 enemy macro | `enemy_macro.c` | E-14 S-120..S-125 | 60 symbols; behaviour runner, scripts, triggers | 539 py lines, 22 tests | none |
| B14 reinforcement, supply, hazards | `tactical_support.c` | E-15 S-126..S-131 | 65 symbols; reinforcement, spine drift | 184 py lines, 25 tests | S-131 reference (UI only) |
| B15 map generation | `tactical_mapgen.c` | E-17 | 61 symbols over ALG-70..73 (the disc-and-skeleton generator) | 1,575 py lines, 29 tests | **held**: the landscape design phase replaced this generator (terrain first); E-17 is rewritten after Westley's third look, then its tests, then this piece |
| B16 cross-cutting | `sim.c`, `ouroboros_sim.h`, `conftest.py` | D1 explicit feature set; header declarations for ~600 symbols; the three unwired steps; `om_abi_layout_check` | | | none; must land before B5..B14 compile |

### Transport and persistence

| Piece | Interface | Notes |
|---|---|---|
| T1 C pipe server | A thin process over `libouroboros.so`: snapshot, delta every tick, command stream; 4-byte length-prefixed JSON both ways, the shape documented in `docs/architecture.md` first (the rule) | Replaces `SimBridge`'s Python child; carries no names, positions or prose (C5); the client layout pass and the offline library own those |
| T2 save and load | E-16 S-111 (flag closed): autosave at chapter boundaries; deterministic restore of world, ledger, chapter, onboarding, RNG state, chain counter; version refusal | Python `save_writer.py`/`save_loader.py` are the reference; C-side serialisation of `om_world` plus a Godot slot layer |

### Client (Godot, placeholders only)

| Piece | Scene | State today | Work |
|---|---|---|---|
| C1 main menu shell | `scenes/main_menu`, new game, load, settings, era library, onboarding, privacy | self-contained, works | none; this is the puzzle's first piece |
| C2 galaxy view | new small files replacing `scenes/shared/world_view` and `time_jump_sequencer.gd` | 5,181 lines coupled to Python payloads | rewrite per C5: points, edges, owner colour, pan, zoom, click to inspect, over T1's snapshot; theme, palette and shaders reused |
| C3 chronicle scroll | `scenes/world/chronicle_*` | exists, reads Python `chronicle_entry` messages | rebind to B8's output through T1 |
| C4 briefing and debrief | `scenes/mission_briefing`, `scenes/debrief` | exist, self-contained | rebind to B9's output |
| C5 tactical view | `scenes/tactical` (units as MultiMesh, HUD, input router, terrain) | coupled to `TacticalBridge` | minimal rebuild over T1: units as blocks, move and attack orders, S-P12 HUD, S-103 camera (flag closed; map band Q-103-02 open, skip it) |
| C6 landscape view | `scenes/mockups/landscape` | pass 3 built, awaiting Westley | after approval: promote the mockup's generator contract to the client's map view over B15 |
| C7 harness daemon | `scenes/harness/` (missing) plus an autoload | the QA design's game-side hook: `state`, `tree`, `seed`, `fixture`, `pause`, `step`, `screenshot`, `inject`, `input` | first client piece to build; every later piece attaches through it |

### Content and QA plumbing

| Piece | Work |
|---|---|
| K1 era pack validator plus banned words (PX-10 brief) | project code, Claude-owned |
| K2 second placeholder era pack (Greek kit from the mockup) | data, for the P8 rung |
| Q1 ouroboros QA campaign files, planted-bug catalog, per-epic gate cards | data under `agora/projects/ouroboros/` |
| Q2 T1 detectors for the tactical trace (P4's RTS bug catalog rows) | `tests/qa/t1/` |

## 3. What only Westley can unblock (27 flags)

- E-19 multiplayer (S-140, S-141, S-142, S-144): 8 flags on lockstep timing, match shape, pause ownership, cheating stance, matchmaking, persistence. Nothing below the transport layer is designed; no piece here is buildable.
- E-20 eras (S-147..S-150): 6 flags (era names and settings, shared seeds, transition trigger, tech at boundaries, earning packs, transferable content). P8 needs Q-147-01 at least.
- E-21 pipeline (S-153..S-156): 4 flags (JSON libraries for C, naming pool exhaustion, tool independence, balance bands).
- S-159 economy and city (4 flags): the city mapper's pieces, growth during a mission.
- E-17: Q-119-02 is answered by the terrain-first design pending his approval; the E-17 rewrite waits on the mockup's third look.
- E-16: Q-103-02 map-view orders.
- E-01: Q-E01-08 references; the layer design phase itself (P6) is a Westley session.
- E-05: Q-039-01 (one rule).
- Fourteen "needs reference" stories are visual claims; backend pieces do not wait on them.

## 4. The puzzle order (integration ladder, restated for this push)

1. **C1 main menu** alone, launched headless through C7's daemon: the QA baseline (input liveness, state read).
2. **B16 + B1..B3** into the sim; P0 gate: 5,000 ticks under budget, same seed same checksum, T1 detectors on planted builds, whole `tests/csim` E-02/E-04/E-05 green.
3. **T1 + C2 galaxy view**: state read through the daemon equals the sim snapshot; a region's colour matches its owner (P1 gate).
4. **B4..B6** (world generation, diplomacy, lifecycle) behind the same galaxy view.
5. **B7 + B8 + C3** (generational, chronicle, scroll): entries reference real state, deterministic per seed (P7 gate, brought forward because its inputs exist).
6. **B9 + C4** (missions, briefing, debrief): objectives satisfiable, markers named (P3).
7. **B10 + B12 + C5** (units, movement, tactical view): RTS T1 rows clean over scripted command streams (P4).
8. **B11** fog (P5); **B13, B14** enemy macro, reinforcement.
9. **C6 + B15** landscape after Westley's approval and the E-17 rewrite (P2, out of ladder order by his choice).
10. **T2** save and load across a chapter boundary.
11. **K1, K2** and the P8 pack gate.
Layers (P6) and multiplayer (P9) stay behind Westley.

Every attach step runs: the whole `tests/csim` suite on exact failing-id sets, the determinism repeat-seed check, the T1 detectors, the daemon's state checks for every earlier piece, and the planted controls for the new piece; a red gate parks the new piece, never the main line.

## 5. Parallelism facts

- Pieces B1..B14 are disjoint by module and symbol (`symbol_modules.toml`); their tests are already split by owning symbol (R25). Fifteen sub-agents can hold fifteen modules at once with no shared file except the header, which B16 owns and freezes first (declarations for all ~600 symbols land in one commit before the swarm).
- Client pieces are disjoint by scene directory; C7 (the daemon) and T1 (the pipe shape) are the two interfaces everything else reads, so they go first and freeze.
- The straggler rule works because a piece's tests are its contract: an unmerged module never blocks another module's tests, only the integration step that needs both.
- Design decisions the swarm will hit are already decided in the bible for B1..B14; the ones it will hit that are not: the JSON shapes of snapshot, delta and command (mine, before T1), the order of the three unwired steps (ALG stages 4.25, 4.5, 6, already in the header comments), D1's signature.

## 6. Before the swarm starts (design lane, hours not days)

1. `docs/architecture.md`: the C snapshot, delta and command shapes (the tick-delta rule).
2. `symbol_modules.toml` accepted or amended by Westley; header declarations generated (B16).
3. D1 landed (explicit feature set) so every new module's tests pass a set.
4. Stories catalog refreshed (done today: 40 stale "blocked" rows corrected), epic gate lines refreshed to the register.
5. The cascade harness (merge queue, whole-suite gate) is running on `main` so integration is mechanical.

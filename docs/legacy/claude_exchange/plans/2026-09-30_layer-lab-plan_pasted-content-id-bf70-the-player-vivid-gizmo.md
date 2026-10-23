# Skill lab on the real engine: record the decisions, then measure in small batches

## Context

Two days of work on the layer system produced a toy simulator, three research briefs and many rulings, and ended with a change of instrument. The toy's unit behaviour is not the game's, and results kept turning on that difference (overlapping units in pass 2; held units that never step forward and chasing units that run through a choke in pass 7). On 2026-10-01 the real C sim was compiled on this machine and driven headless: a 16 v 16 fight takes 3 ms, the same as the toy, with the real movement engine and unit rules.

Westley, 2026-10-01: "yes to the real engine, so long as we can accomplish the original goal from the original plan. ... We're looking to tune the different knobs to see the expected result, but not just 'one'. The *lines* can cross in multiple locations, there may be configurations where health/range/vision/ping distance is much higher/lower but the expected behavior is exhibited. This new 'simulator' will do small batches of tests, that produce output that both of us can read (using the visual artifact style you produced and more if the type of data we're looking at changes). Use TDD, manager-mode methods. This is a big conversation with several revlelations and big decisions, we need to condense the main points into the plan and record them to the repo so that they persist for future chats."

So this plan has two jobs: (1) condense what was decided and write it where a future chat will find it; (2) rebuild the measuring instrument on the real engine without losing the goal.

## Part 1. What was decided (the record to persist)

### The goal

"players with better understanding of the landscape, unit formation, layer awareness/intentionality, and the other players current position can defeat a much larger force." (Westley, 2026-10-01.) Reached by tuning every variable until that sentence is true. The original 2026-09-30 prompt asked for a simulator that varies everything an RTS varies, documents how the variables relate, and finds where the "lines cross".

### The principle

- **What decides a fight is how many units on each side can get shots off, and for how long.** ("the differentiator is **can your unit get shots off**", 2026-09-30.) Consistent advantage over the whole fight, not only the opening. Equal numbers firing means an even exchange; the side with more in reserve then outlasts the other.
- **A skill has no fixed worth.** A play is worth what it does to the firing count in that situation ("it's not as simple as that", on a flat 1.3x). About 30 percent for one skill and about 3x for all five are rough sizes, not pass marks.
- **Unit type is the one other factor**: it weights each shot. A number that decides a fight against the firing count (a layer damage multiplier, raw health) is "a number that's off".
- **Lines cross in more than one place.** There may be several different configurations (health, range, vision, ping distance much higher or lower) under which the expected behaviour appears. The search must find and describe each such region, not stop at the first.

### Five skills, their plays and counters

S1 landscape, S2 formation, S3 layers, S4 enemy position (scouting and baiting into traps), S5 unit-type matchup (your rocks on their scissors). Skill is represented by scripted plays, a skilled one and a naive one. The accepted table of plays and counters is in the lab README §4.1a. Refusing a fight is a counter; a play needs a counter on most maps, not all; a sprung trap or full surround may have none. After the prototype, if it works: a reactive version where sides re-form mid-fight.

### The measure

- **Margin**, a signed share of strength left, replaces win rate (combat has no dice).
- **Break-even in whole units**: "16 beat 17 and lose to 18". By headcount, both sides fielding the same unit mix. Beating means ending ahead by a margin, not a wipe-out.
- **Units firing per side through time**, recorded for every fight, and the firing advantage beside every result.
- **Conditions C0 to C9** (README §4.3): control; skill wins the firing count; the result follows the firing count; skills stack; none dominant; none dead; counters on most maps; a high ceiling; robust across maps; fights readable. Draft pass marks exist and are not yet confirmed.
- **Maps**: space maps (every unit flies, five free layers) must pass; land maps (ramps, walkers) are reported.

### How results are read

Small batches, read together, then the next step. Charts in the form approved on 2026-10-01 (sample: https://claude.ai/artifact/WtQDNnNZTR8hqx6LpxBaJ2): the heading states the finding in soldiers; a line of fights by enemy size with won and lost dots and the break-even marked; units firing through the fight with each line labelled; a table with a plain-words column in place of scatter plots. "Lines crossing" is shown as a map of two knobs, shaded where every condition holds.

### Layer rulings (E-01 and the register)

Five layers always. Vision symmetric by layer distance; passive cross-layer vision stays short and the ping reaches far. Three free layer actions: the targeted ping (the pinged side gets an alert and a 60-degree sector), going dark, reach by unit type (S-162 to S-164). The ping replaces the seer, or the seer stays only at a very high cost. No blind fire. Shortest route across layers. Walking and flying units. Slopes: progress is position, cross-over at the midline, a unit is on the layer on its side of it. Abilities out of scope for now. No faster descent in space eras. Deferred ideas: travel lanes (S-165), reactive formations.

### What the toy showed, and why it is being left

- A layer alone gives nothing under symmetric vision; reach and damage penalties are steep.
- Width matters, curvature barely: a line or a concave is worth three units in sixteen against a blob; a concave is worth one against a line.
- Holding a choke gave nothing, for three reasons: walls did not block sight, there was no stance between "never move" and "chase anywhere", and reach is only four unit-widths.
- Results kept depending on the toy's own movement. The real engine has the game's unit rules (E-11 R-087, E-13 R-096) and is as fast.

### Research on file

`docs/legacy/topics/lanchester_and_combat_theory.md` (square and linear laws; a choke switches between them; defeat in detail; the hidden side's edge is bounded; first strike and staying power; height as initiative), `active_layer_vision_mechanics.md`, `charts_for_combat_simulation_data.md`.

### Lessons about method

Check written text against Westley's actual words. Look at what a scripted play does before measuring it. One skill, one map, one size, then widen. A surprising result is first a question about the instrument.

### Open

Register: `Q-001-05`, `Q-005-04`, `Q-008-02`, `Q-008-03`, `Q-009-02`, `Q-165-01`. Not yet ruled: the draft pass marks; how refusing a fight is checked; whether abilities join the bar. Ruled while planning: every skill is measured against both a blob and a line abreast.

Decisions taken while planning (AskUserQuestion, 2026-10-01): build the engine's gaps into the real engine, in order, measuring as each lands; accept the recommended starting values on `Q-005-04` and `Q-001-05` as provisional so the E-01 stories can be built; discard the stray `project.godot` change; measure every skill against both a blob and a line abreast, side by side; and the work must be portable between this Mac and the Linux machine, which is working on the same repo in parallel.

## Part 2. What the real engine can and cannot do today (inventory, 2026-10-01)

Can: headless fights through the public API (`om_world_new`, `om_unit_spawn`, `om_command_attack_move`, `om_command_group_move`, `om_tactical_step`), the game's own unit rules (acquire, anchor, 200 leash, return fire, flinch), group moves that keep shape, hard collision, unit stats changed at run time through `om_roster_register_custom_unit`, abilities switched off with `om_tactical_disable_abilities`. Fully deterministic. 3 ms for 16 v 16.

Cannot, each a gap against its own bible:

| Gap | Bible rule it misses | Blocks |
|---|---|---|
| No routing: units walk straight; obstacles do not block movement | E-13 R-097-01 | S1 landscape (no choke can exist) |
| Targeting ignores fog and line of sight | E-12 R-093-02, E-01 R-008-04 | S4 enemy position, all vision work |
| No layer changes, slopes, ping, going dark, reach by type; same-layer fire only | E-01 S-002, S-004, S-162 to S-164 | S3 layers |
| Rule numbers are compile-time `#define`s generated from `algorithms.md`; no `-D` override | (none; a tooling gap) | sweeping any knob other than unit stats |
| No hold order; no "can fire" counter; attack cooldown not exposed | (harness works around these) | nothing, with care |
| The first-spawned faction shoots first; no randomness between seeds | (property of the engine) | honest measurement, unless the harness swaps sides and varies positions |
| Root `Makefile` passes `-msse2 -mfpmath=sse` with no architecture check, so it fails on this arm64 Mac | determinism contract names macOS | building here |

So today the real engine supports open-ground, same-layer fights: formation (S2), unit-type matchup (S5) and unit-stat knobs.

## Part 3. The instrument: `scripts/skilllab/` (no engine edits)

A Python package that only calls the production library, beside the existing precedent `scripts/bench_tactical_pipe.py`. Tests in `tests/skilllab/` (outside the fenced `tests/csim/`).

- `engine.py`: builds the library into a scratch directory with flags chosen by architecture (until G0 lands), loads it with ctypes, binds the two dozen calls it needs.
- `fight.py`: `fight(setup, seed) -> FightResult`. Steps the tactical tick; every few ticks reads positions, targets, hp; computes per side the units able to fire (enemy on its layer within its range and `om_combat_can_shoot`), since the engine has no such counter. Returns margin, survivors, the firing series, unit-seconds of fire.
- Honesty built in: every cell runs with the spawn order swapped (the engine gives first shot to the first-spawned side) and with small seeded shifts of position as replicates (the engine has no randomness of its own).
- Reused from the toy, engine-independent, copied not imported: the whole-unit scan and non-increasing fit (`toys/layerlab/layerlab/skill/rstar.py`), headcount shares (`skill/cost.py`), formation geometry (`layerlab/formations.py`), grid and random sampling (`layerlab/sample.py`), CSV rows (`layerlab/batch.py`), the choke arithmetic from pass 7.
- `plays.py`: the naive ladder (blob, line abreast), then skilled plays per skill as the engine comes to support them. Every skill reported against both naive plays.
- `knobs.py`: unit stats through custom roster types (reach, health, damage, interval, speed, sensor); rule numbers through runtime config once G1 lands.
- `report.py`: one HTML page per batch in the approved chart form, published as a private artifact, plus a short run file in the repo.
- Tests first (TDD): the mirror is even after the side swap; twice the numbers wins; a planted reach advantage beats a known number more; the firing count is right on a hand-built case; the same inputs give the same rows; a committed set of result hashes matches on both machines.

Built with the manager-mode-lite method (Westley, 2026-10-01): Sonnet sub-agents for everything, including the shard test writers and the auditors. I write the spec, the contract (`fight`'s types) and a failing umbrella test; a separate Sonnet test-writer writes the per-part failing tests; a Sonnet auditor reviews them before any code; Sonnet implementers write only code; each part is admitted by gates. The model is named on every spawn, as CLAUDE.md requires.

## Part 4. One controls batch, before the engine work

Only the controls run on today's engine: the mirror, twice the numbers, a planted reach advantage. A few hundred fights, one page of charts, one run file. Two purposes: prove the harness reads correctly while the engine is still unchanged, and keep a before-picture to compare against once the engine cascade lands. No skill batches yet; routing, fog-gated targeting and tunable rule numbers would change them all, so they wait (Westley, 2026-10-01).

## Part 5. The engine gaps, built in one cascade (tests first, manager-mode-lite)

One cascade covers G0 to G7 (Westley, 2026-10-01), all Sonnet sub-agents, with shard test writers and auditors. Inside it the steps are waves in dependency order: the header and config contract first, then G2 and G3, then the layer steps G4 to G7. The files it touches are registered in `docs/northstar/plans/push/pieces.toml` first, so the Linux side does not edit them at the same time. If the decomposition comes out above the method's limit of 16 parts in one wave, it is split into waves, not into separate cascades.

| Step | What is built | Stories | Unlocks |
|---|---|---|---|
| G0 | `Makefile` chooses SSE flags only on x86; `.gdignore` in `toys/` and lab result folders | determinism contract | building on both machines |
| G1 | Rule numbers readable and settable at run time (vision factors, leash, collision size, type matrix, later the layer tables), defaults from `om_constants.h` | tooling | every knob sweep beyond unit stats |
| G2 | Solid terrain that blocks movement, sight and fire, and routing around it | E-13 S-097, E-01 S-001 | S1 landscape: chokes |
| G3 | Units acquire and fire only on what they can see | E-12 R-093-02, E-01 R-008-04 | S4 by vision; ambush |
| G4 | Layer changes: the timed transfer, the cross-over rule, shortest route across layers | E-01 S-002, S-004, R-001-05 | S3 begins |
| G5 | Reach by unit type and the cross-layer fire tables | E-01 S-164, S-008 | S3 |
| G6 | Going dark | E-01 S-163 | S3, S4 |
| G7 | The targeted ping and the alert to the pinged side | E-01 S-162 | S3, S4 |

Before G4: close `Q-005-04` and `Q-001-05` with the recommended starting values, marked provisional, every number a runtime setting (Westley's decision above); run the E-01 gate for the stories involved. G2 and G4 are the large ones. Land eras (walkers, slopes) follow the space set.

The toy (`toys/layerlab/`) is frozen as a reference for the layer-action rules it already has. The lab chat is told to stop; the sight-blocking request to it is withdrawn.

## Part 5b. Small batches, on the finished engine

After the cascade lands and the controls batch is re-run against its before-picture. Each batch is a few hundred to a few thousand fights, one page of charts, one run file, read with Westley before the next. One skill, one map, one size, then widen.

1. Formation (S2): blob, line, concave, each against the blob and the line, at 8 and 16 units.
2. Unit-type matchup (S5): lined up against mixed.
3. Landscape (S1): a choke held properly, against the pass 7 arithmetic.
4. Enemy position (S4): sight first, ambush.
5. Layers (S3): reach by type, going dark, the ping.
6. Knobs, one at a time and then in pairs: reach against spacing (the pass 7 question), health against damage (staying power), speed, vision and ping distance. For each skill, record **every** region of settings where it wins the firing count and the result follows, not only the first.
7. Combinations of skills, and the counters.

## Part 6. The search, once the skills can be measured

Both tracks from the lab README: all at once (sample every knob together) and incremental (two variables, tune, add, re-tune). Output: each distinct region of settings where conditions C0 to C9 hold, described in plain words and shown as shaded maps of two knobs at a time; what each near-miss fails. Numbers that survive go to `algorithms.md`, the S-008 rules gain values, `Q-008-02` and `Q-008-03` close.

## Part 7. Two machines, one repo

- **No machine paths.** The harness finds the repo root from its own file; nothing under `/Users/` or `/home/`.
- **Build by architecture.** Until G0, the harness compiles its own copy with the right flags; after G0, plain `make` works on both.
- **Same numbers on both.** A small committed file of result hashes for the control fights; a test compares against it on each machine. A mismatch between arm64 and x86 is a determinism finding to escalate, not to tolerate.
- **Processes.** macOS starts worker processes fresh and Linux forks; every script uses a `__main__` guard and passes plain data to workers (the stdin crash seen on 2026-10-01).
- **Git.** Work lands on `main` in small units. Merge, never rebase. Pull before editing a shared file. Cascade branches and worktrees (`swarm/...`) stay local and are removed when a cascade ends; only the result is pushed.
- **Fewer shared files.** Each lab pass gets its own file under `docs/northstar/research/layer_dynamics/runs/` in place of one long shared log, and the register is edited one row at a time, to keep merges with the Linux side small.
- **Nothing generated is committed**: libraries, result CSVs and pictures, Godot `.import` and `.uid` files.
- **Stale worktrees.** 34 agent worktrees from the toy build sit under `.claude/worktrees/`; removing them is asked of Westley, not done silently.

## Part 0. First: write the record into the repo

1. `docs/northstar/research/layer_dynamics/README.md` becomes a short "start here": Part 1 of this plan, the inventory of Part 2, where everything is. The present long file moves to `history_2026-09-30_to_10-01.md` beside it, with the run log split into `runs/`.
2. E-01 S-008 and the register rows `Q-008-02`, `Q-008-03`, `Q-005-04` and queue row Q76 stop naming the toy as the instrument and name the skill lab on the real engine. `Q-005-04` and `Q-001-05` closed as provisional.
3. Memory: rewrite `project_layer_lab.md` (what the lab is now, where the record is, the two-machine rules); keep the reactive follow-up note.
4. `CLAUDE.md`, "Where things are": one line for the skill lab and its record.
5. Message the lab chat: toy frozen, sight request withdrawn.
6. A cross-check of the new README against Westley's words, as before.

## Order of work

1. Part 0: write the record into the repo.
2. Part 3: build the harness (it compiles its own copy of the library, so it does not wait for G0).
3. Part 4: the one controls batch, read with Westley.
4. Part 5: the engine cascade, G0 to G7 in one.
5. Re-run the controls; then Part 5b, the small batches, Westley reading each.
6. Part 6: the search.

Westley runs once, since the guard blocks me from discarding files: `git restore project.godot`.

## Files

- New: `scripts/skilllab/{engine,fight,plays,knobs,scan,sample,report}.py`, `tests/skilllab/`, `docs/northstar/research/layer_dynamics/runs/`, `history_2026-09-30_to_10-01.md`.
- Rewritten: `docs/northstar/research/layer_dynamics/README.md`; memory `project_layer_lab.md`.
- Edited: `docs/bible/epics/E-01-layer-system.md`, `docs/northstar/ambiguity_register.md`, `docs/legacy/research_lane_queue.md`, `CLAUDE.md`, `docs/northstar/plans/push/pieces.toml`, `Makefile` (G0).
- Engine, per step G1 to G7: `csrc/ouroboros_sim.h` and `docs/northstar/spec_factory/signatures.toml` (contract pieces), `csrc/unit.c`, `csrc/tactical_move.c`, `csrc/fog.c`, `csrc/tactical_mapgen.c`, new tests under `tests/csim/`.

## Verification

- Part 0: a fresh chat given only the new README and memory can state the goal, the principle, the measure and the next step; the cross-check finds no unsourced claims.
- Harness: its tests pass on the Mac and on Linux with the same result hashes; the mirror control is even after the side swap; a 16 v 16 scan of twenty enemy sizes runs in seconds.
- Each batch: a published page Westley can read at a glance, and a run file.
- Each engine step: its tests were red before and are green after; the existing `tests/csim` suite does not regress; O0 and O2 builds agree; the lab batch it unlocks runs.

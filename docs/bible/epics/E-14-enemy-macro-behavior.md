# E-14 — Enemy Macro Behavior

## Definition-completeness gate (run 2026-09-10)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Yes, 6 stories, 30 rules, numbers from `algorithms.md` ALG-74 and config. |
| Every input listed with range and rejection behavior | Yes, see Inputs. |
| Every output listed with where it is observable | Yes, see Outputs. |
| Implied-but-unstated behavior turned into flags | 5 new flags, Q-120-01, Q-121-01, Q-122-01, Q-124-01, Q-125-01. |
| Every visible-surface story has a reference | Not applicable. Enemy behavior is observed through units (E-11, E-13). |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed.** Blocked on 5 open flags. Q-121-01 (two script condition hooks are stubbed to constants in code) and Q-125-01 (Westley's Stage 1 interim difficulty knob, A-156) need answers before tests can be written.

## Purpose

The enemy's units think exactly like the player's (E-11 S-087). What makes an enemy feel like a plan is the layer above them: each enemy force runs a small state machine authored per mission archetype from a shared vocabulary of five behaviors and three modifiers, with timers that keep the mission moving even if the player sits still, thresholds that react to what the player does, and noise rolled once at mission start so the same script never plays the same twice. Several forces coordinate only through a handful of shared flags. The macro layer speaks to units through the same four commands the player has, so every enemy action replays like a player's.

The long-term target is an opponent that feels like it reads the player (Stage 1 A-149, A-150); the launch baseline is this scripted system plus a simple difficulty knob (A-156).

## Obviously working in 60 seconds

Load a Defensive Stand script with force A in advance_cautious toward the objective and a hook "if force HP below 40 percent, retreat to spawn." Watch A attack-move in, take losses, and at roughly 40 percent (plus or minus its rolled noise) turn and plain-move back. Load a two-force Multi-Front script where B's hook reads force_a_routed: rout A and B switches from advance_cautious to advance_aggressive within 2 s. Run the same seed twice: identical transitions on identical ticks.

## Stories

### S-120 — Five behaviors, three moods
As a commander, I want enemy forces to advance, hold, patrol, ambush, or retreat, cautiously, aggressively, or in echelons, so that I can read what they are doing and plan against it.

Rules
- R-120-01  Given a script state, When read, Then its behavior is one of advance, defend, patrol, ambush, retreat and its modifier one of cautious, aggressive, phased; any other value fails script validation.
- R-120-02  Given advance, When executed, Then the force attack-moves toward its target (a position, a spine node, or a unit group); given defend, Then it holds position and units auto-engage without pursuit; given patrol, Then it plain-moves through its waypoints in a cycle and auto-engages on contact; given ambush, Then it holds hidden until an enemy enters its trigger radius, then becomes advance_aggressive toward the trigger and never resets; given retreat, Then it plain-moves to its fallback point.
- R-120-03  Given cautious, When executed, Then the force moves at baseline speed and it transitions to retreat or defend when force HP lost since state entry exceeds the contact threshold; given aggressive, Then baseline speed, no break-off; given phased, Then the force is split into 2 or 3 sub-groups that advance one at a time, each starting when the previous engages or reaches its waypoint.
- R-120-04  Given a macro evaluation, When it runs, Then it runs every 40 ticks (2 s) and issues commands only through move, attack_move, attack_target, activate_ability.

Inputs: script (states, transitions, hooks, forces); tactical state.
Outputs: enemy commands in the command log; force state in the T1 trace.
Q-120-01 closed: AI postures deferred; enemy macro scripts use baseline movement speeds for every modifier (no modifier-based speed or spacing change). Decided by Westley, 2026-09-16.

### S-121 — Timers and thresholds, with noise
As a commander, I want the enemy to escalate on a schedule and react to what I do, with the exact moment shifting each time, so that no two runs of the same mission are the same.

Rules
- R-121-01  Given a transition with a threshold condition (force HP fraction, unit count, elapsed time, timer expired, bus flag, player force in zone, enemy in range), When evaluated, Then the condition is compared against its noised value: noise is one uniform draw in ±noise_pct (default ±0.15 for thresholds, ±0.20 for timers) made at mission start and held for the mission.
- R-121-02  Given a timer transition with duration D, When elapsed × (1 + noise) ≥ D, Then it fires regardless of tactical state.
- R-121-03  Given a threshold and a timer both firing on the same evaluation, When resolved, Then the threshold wins, except that a retreat transition always wins over an escalation.
- R-121-04  Given a hook (when-expression, to_state), When its expression is true, Then the force transitions at once, before base transitions are checked.
- R-121-05  Given the conditions "player force in zone" and "enemy in range", When evaluated, Then [Q-121-01: code returns constants 1.0 and False; the real evaluation must be defined].

Inputs: script; RNG at mission start; tactical state.
Outputs: transition log.
Open flags: Q-121-01.

### S-122 — Forces that notice each other
As a commander, I want a second enemy force to react when I rout the first, so that the enemy feels like it has a plan and not a script.

Rules
- R-122-01  Given a mission with 2 or more enemy forces, When each is created, Then it runs its own script instance, its own faction id if the script assigns one, and its own noise draws.
- R-122-02  Given the trigger bus, When a force sets a flag (for example force_a_routed, objective_alpha_contested), Then any other force's hook reading that flag can fire on its next evaluation.
- R-122-03  Given a script, When validated, Then every flag it reads or sets is in the script's declared bus vocabulary, else validation fails.
- R-122-04  Given a mission, When flags are counted, Then a typical script fires 2 to 5 flags [Q-122-01: who sets force_a_routed and the like; no code sets flags today].
- R-122-05  Given authored relative timing (force B starts 30 s after A), When timers roll, Then each force's timer noise is independent.

Inputs: script; bus.
Outputs: bus state in the T1 trace and save.
Open flags: Q-122-01.

### S-123 — The enemy replays like I do
As a player in a multiplayer match, I want enemy behavior to be a pure function of seed, script, and state, so that every peer sees the same enemy.

Rules
- R-123-01  Given seed, script, map, and the command stream, When run twice, Then every enemy command is identical on identical ticks.
- R-123-02  Given the enemy, When its commands are logged, Then they appear in the same replay stream as player commands with a force id.
- R-123-03  Given the macro layer, When it acts, Then it never reads the player's visible set, never issues a command a player could not, and never changes a unit's stats.

Inputs: none new.
Outputs: replay stream.
Open flags: none.

### S-124 — Rare surprises
As a commander, I want a foreshadowed reinforcement wave to arrive once in a while, so that some missions turn on a moment I could see coming but not time.

Rules
- R-124-01  Given mission generation, When the external-reinforcement roll is made, Then the wave is scheduled with probability p [Q-124-01: 1 in 10 to 20 in the bible; nothing in code], its direction is named in the briefing, its arrival tick is fixed at generation and not shown.
- R-124-02  Given the wave arrives, When it spawns, Then units enter at a map-edge spawn point, set a bus flag, and run their own script. The wave is ALG-75's standard composition (ALG-76).

Inputs: mission generation RNG.
Outputs: briefing text; spawn; bus flag.
Open flags: Q-124-01.

### S-125 — How hard the enemy tries
As a player, I want a difficulty knob that changes how much the enemy has and how well it reads the layers, never how its units fight, so that I always lose to my own limits.

Rules
- R-125-01  Given difficulty, When the enemy is set up, Then two things scale: its economic prosperity (more resources to field and replenish) and its multi-layer intelligence (positional awareness: which units on which layers trump the player's units on theirs, informed surrounds the player cannot see until too late) [Q-125-03: how each scales and what hard mode strives for].
- R-125-02  Given any difficulty, When the enemy's units act, Then their stats and abilities are identical to the player's, and the macro layer never sees what a player could not see; only how much the enemy has and how well it reads layers differs.
- R-125-03  Given external playtesters, When sessions run, Then command streams and outcomes are captured for the future learned-opponent target (A-156, data capture only).

Inputs: difficulty.
Outputs: enemy force size and prosperity; macro layer awareness; captured session logs.
Open flags: Q-125-03. Q-125-01 is closed by Q-125-02: prosperity and multi-layer intelligence, chosen through the options pass, `docs/northstar/research/options/difficulty-knobs/`.

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Behavior script | E-21 library per archetype | forces, states, transitions, hooks, bus vocabulary | validation errors fail mission generation |
| Tactical state | E-11, E-13 | | |
| Mission start RNG | Seed | | |
| Difficulty | E-08 | easy, medium, hard | |

## Outputs

| Output | Observable where |
|---|---|
| Enemy commands | Command log; replay |
| Force states, transitions, bus | T1 trace; save |
| Reinforcement wave | Briefing; spawn events |

## Invariants

- The macro layer issues only the four player commands.
- Every transition noise is drawn once per mission.
- Ambush never resets.
- Same seed, same enemy, all platforms.

## Scale requirements

Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is escalated): macro evaluation for 10 forces over 1,000 units in under 1 ms per evaluation tick.

## Look and behavior references

None required.

## Ways this could be wrong

- Noise re-rolled per evaluation, so transitions jitter.
- Timer measured from mission start instead of state entry.
- Cautious break-off measured against mission-start HP instead of state-entry HP.
- Ambush resets after the trigger leaves.
- Hooks evaluated after base transitions.
- Bus flags never set, so multi-force reactivity is dead.
- Macro reads true enemy positions the player cannot see (it may; it must not read the player's visible set).

## Open ambiguity flags

Q-120-01, Q-121-01, Q-122-01, Q-124-01, Q-125-01. Details in `docs/northstar/ambiguity_register.md`.

## Depends on

- E-10 (archetype, script selection, briefing), E-11 (unit loop), E-13 (commands), E-15 (enemy production target ratios), E-17 (spine nodes as targets), E-21 (script library and validation).

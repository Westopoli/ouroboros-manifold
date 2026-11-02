# E-14 — Enemy Macro Behavior

## Definition-completeness gate (run 2026-09-10, extended 2026-10-02)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | S-120 to S-125: yes, 6 stories, 22 rules, numbers from `algorithms.md` ALG-74 and config. S-215 to S-217: 3 stories, 17 rules, design decided 2026-10-02 and not scheduled for building; where Westley has not given a number the rule carries a flag instead. |
| Every input listed with range and rejection behavior | Yes, see Inputs. |
| Every output listed with where it is observable | Yes, see Outputs. |
| Implied-but-unstated behavior turned into flags | No open flags on S-215 to S-217, plus Q-178-04 carried. |
| Every visible-surface story has a reference | Not applicable. Enemy behavior is observed through units (E-11, E-13). |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed.** No open flags remain on S-215 to S-217. S-120 to S-124 have no open flags; gate to be rerun.

## Purpose

The enemy's units think exactly like the player's (E-11 S-087). What makes an enemy feel like a plan is the layer above them: each enemy force runs a small state machine authored per mission archetype from a shared vocabulary of five behaviors and three modifiers, with timers that keep the mission moving even if the player sits still, thresholds that react to what the player does, and noise rolled once at mission start so the same script never plays the same twice. Several forces coordinate only through a handful of shared flags. The enemy also has a base, expansions and an economy, run by the same rules as the player's side, so its forces defend, fall back to and raid over real places (S-215, S-216). The macro layer speaks to units through the commands the player has, the layer commands included (S-217), so every enemy action replays like a player's.

The long-term target is an opponent that feels like it reads the player (Stage 1 A-149, A-150); the launch baseline is this scripted system plus a simple difficulty knob (A-156).

## Obviously working in 60 seconds

Load a Defensive Stand script with force A in advance_cautious toward the objective and a hook "if force HP below 40 percent, retreat to spawn." Watch A attack-move in, take losses, and at roughly 40 percent (plus or minus its rolled noise) turn and plain-move back. Load a two-force Multi-Front script where B's hook reads force_a_routed: rout A and B switches from advance_cautious to advance_aggressive within 2 s. Run the same seed twice: identical transitions on identical ticks.

## Stories

### S-120 — Five behaviors, three moods

Direction changed 2026-10-02, rewrite pending: the macro layer also issues the layer commands of E-01 (S-217), and a retreating force goes to the enemy's base of operations when it holds one (S-216). The rules below are what the game does today.
As a commander, I want enemy forces to advance, hold, patrol, ambush, or retreat, cautiously, aggressively, or in echelons, so that I can read what they are doing and plan against it.

Rules
- R-120-01  Given a script state, When read, Then its behavior is one of advance, defend, patrol, ambush, retreat and its modifier one of cautious, aggressive, phased; any other value fails script validation. The behaviours for defending a base, founding an expansion and raiding are added by S-216.
- R-120-02  Given advance, When executed, Then the force attack-moves toward the mission's primary objective (its node center, via `om_objective_get_center` or the spine node the mission places); once the force has contact -- any of its units has a visible player unit in range or took damage this evaluation -- it re-targets the nearest player unit group centroid; given defend, Then it holds position and units engage what they see under the 200 wu leash of R-087-04 (H-057, 2026-11-01; was "without pursuit"); given patrol, Then it plain-moves through its waypoints in a cycle and auto-engages on contact; given ambush, Then it holds hidden until an enemy enters its trigger radius, then becomes advance_aggressive toward the trigger and never resets; given retreat, Then it plain-moves to its fallback point (the mission's enemy spawn edge). Decided by Westley, 2026-09-28 (Q-120-04).
- R-120-03  Given cautious, When executed, Then the force moves at baseline speed and it transitions to retreat or defend when force HP lost since state entry exceeds the contact threshold; given aggressive, Then baseline speed, no break-off; given phased, Then the force is split into 2 or 3 sub-groups that advance one at a time, each starting when the previous engages or reaches its waypoint.
- R-120-04  Given a macro evaluation, When it runs, Then it runs every 40 ticks (2 s) and issues commands only through move, attack_move, attack_target, activate_ability.

Inputs: script (states, transitions, hooks, forces); tactical state.
Outputs: enemy commands in the command log; force state in the T1 trace.
See also: E-11 R-087-04 and E-13 R-096-02 (pursuit and group endings at the unit level overlap the re-targeting of R-120-02), and the guard stance (E-13 R-096-08, ruled 2026-10-13; it may replace or sit under defend).
Q-120-01 closed: AI postures deferred; enemy macro scripts use baseline movement speeds for every modifier (no modifier-based speed or spacing change). Decided by Westley, 2026-09-16.

### S-121 — Timers and thresholds, with noise
Flag closed, rule text pending: Q-121-01, both conditions, player force in zone and enemy in range, are dropped (R-121-01, R-121-05). The rule below is what the tests read today.
As a commander, I want the enemy to escalate on a schedule and react to what I do, with the exact moment shifting each time, so that no two runs of the same mission are the same.

Rules
- R-121-01  Given a transition with a threshold condition (force HP fraction, unit count, elapsed time, timer expired, bus flag, player force in zone, enemy in range), When evaluated, Then the condition is compared against its noised value: noise is one uniform draw in ±noise_pct (default ±0.15 for thresholds, ±0.20 for timers) made at mission start and held for the mission.
- R-121-02  Given a timer transition with duration D, When elapsed × (1 + noise) ≥ D, Then it fires regardless of tactical state.
- R-121-03  Given a threshold and a timer both firing on the same evaluation, When resolved, Then the threshold wins, except that a retreat transition always wins over an escalation.
- R-121-04  Given a hook (when-expression, to_state), When its expression is true, Then the force transitions at once, before base transitions are checked.
- R-121-05  Given the conditions "player force in zone" and "enemy in range", When evaluated, Then [Q-121-01: code returns constants 1.0 and False; the real evaluation must be defined].

Inputs: script; RNG at mission start; tactical state.
Outputs: transition log.
Open flags: none.

### S-122 — Forces that notice each other
Flag closed, rule text pending: Q-122-01, the runner sets the bus flags, and scripts may set custom flags on transitions. The rule below is what the tests read today.
As a commander, I want a second enemy force to react when I rout the first, so that the enemy feels like it has a plan and not a script.

Rules
- R-122-01  Given a mission with 2 or more enemy forces, When each is created, Then it runs its own script instance, its own faction id if the script assigns one, and its own noise draws.
- R-122-02  Given the trigger bus, When a force sets a flag (for example force_a_routed, objective_alpha_contested), Then any other force's hook reading that flag can fire on its next evaluation.
- R-122-03  Given a script, When validated, Then every flag it reads or sets is in the script's declared bus vocabulary, else validation fails.
- R-122-04  Given a mission, When flags are counted, Then a typical script fires 2 to 5 flags [Q-122-01: who sets force_a_routed and the like; no code sets flags today].
- R-122-05  Given authored relative timing (force B starts 30 s after A), When timers roll, Then each force's timer noise is independent.

Inputs: script; bus.
Outputs: bus state in the T1 trace and save.
Open flags: none.

### S-123 — The enemy replays like I do
As a player in a multiplayer match, I want enemy behavior to be a pure function of seed, script, and state, so that every peer sees the same enemy.

Rules
- R-123-01  Given seed, script, map, and the command stream, When run twice, Then every enemy command is identical on identical ticks.
- R-123-02  Given the enemy, When its commands are logged, Then they appear in the same replay stream as player commands with a force id; enemy macro forces are indexed separately from the player's force -- macro force 0 is the first enemy force, and the player's force is never a macro force. Decided by Westley, 2026-09-28 (Q-123-01).
- R-123-03  Given the macro layer, When it acts, Then it never reads the player's visible set, never issues a command a player could not, and never changes a unit's stats.

Inputs: none new.
Outputs: replay stream.
Open flags: none.

### S-124 — Rare surprises
Flag closed, rule text pending: Q-124-01, external reinforcement waves ship at launch with p = 0.21 (Q-124-03, Westley 2026-09-26; was 0.07), scheduled at generation and foreshadowed in the briefing. The rule below is what the tests read today.
As a commander, I want a foreshadowed reinforcement wave to arrive once in a while, so that some missions turn on a moment I could see coming but not time.

Rules
- R-124-01  Given mission generation, When the external-reinforcement roll is made, Then the wave is scheduled with probability p p = 0.21 (Q-124-03, Westley 2026-09-26), its direction is named in the briefing, its arrival tick is fixed at generation and not shown.
- R-124-02  Given the wave arrives, When it spawns, Then units enter at a map-edge spawn point, set a bus flag, and run their own script. The wave is ALG-75's standard composition (ALG-76).

Inputs: mission generation RNG.
Outputs: briefing text; spawn; bus flag.
Open flags: none.

### S-125 — How hard the enemy tries

Direction changed 2026-10-02, rewrite pending: a third thing differs between the enemy and the player's side, which is whether the enemy's economy scouts, counters and disguises, and that is the player's choice and not a difficulty scale (S-215). The rules below are what the game does today.
As a player, I want a difficulty knob that changes how much the enemy has and how well it reads the layers, never how its units fight, so that I always lose to my own limits.

Rules
- R-125-01  Given difficulty, When the enemy is set up, Then two things scale: its economic prosperity (more resources to field and replenish) and its multi-layer intelligence (positional awareness: which units on which layers trump the player's units on theirs, informed surrounds the player cannot see until too late) The numbers by which each scales are set by the skill lab (Westley, 2026-10-07: "#8: C").
- R-125-02  Given any difficulty, When the enemy's units act, Then their stats and abilities are identical to the player's, and the macro layer never sees what a player could not see; only how much the enemy has and how well it reads layers differs.
- R-125-03  Given external playtesters, When sessions run, Then command streams and outcomes are captured for the future learned-opponent target (A-156, data capture only).

Inputs: difficulty.
Outputs: enemy force size and prosperity; macro layer awareness; captured session logs.
Open flags: none; the scaling numbers are the skill lab's (Q-125-03, liberty: Architect).
Prosperity and multi-layer intelligence were chosen through the options pass, `docs/northstar/research/options/difficulty-knobs/`.

### S-215 — The enemy runs an economy too
As a commander, I want the enemy's base to be run by the same economy rules as mine, richer or poorer by difficulty, and farsighted as the difficulty sets, so that what the enemy builds is what a player could build and the difficulty decides how much foresight it has.

Status: design decided 2026-10-02, not scheduled for building.

Rules
- R-215-01  Given an enemy with a base (E-10 S-210), When the mission runs, Then its economy is run by the rules that run a side's economy with nobody in the seat (E-22 S-179 and S-181): the same rules as the player's side, under the same one population cap (E-22 S-169), with perfect hands and no foresight.
- R-215-02  Given difficulty, When the enemy's economy is set up, Then its prosperity is scaled by difficulty (R-125-01).
- R-215-03  Given the difficulty has enemy foresight off, When the enemy's economy runs, Then it does not scout, read the player, counter-pick technology or disguise anything.
- R-215-04  Given the difficulty has enemy foresight on, When the enemy's economy runs, Then it also scouts, counters and disguises, and it reads the player only through what its own side's sight has revealed (E-12 R-093-02), as the player's side does.
- R-215-05  Given the enemy's production target (E-15 S-128), When foresight is off, Then production follows the target ratio and never shifts toward a counter; and When foresight is on, Then the counter-shift of E-15 R-128-02 applies, reading only the player's units the enemy has seen.
- R-215-06  Given the difficulty, When a mission is set up, Then it decides which of scouting, countering and disguising the enemy's economy does, and the player has no switch for it (Westley, 2026-10-07; E-22 R-181-03). Foresight is off on easy only and on at medium and hard (Westley, 2026-10-07: "Only easy should have foresight off honestly.").
- R-215-07  Given the enemy's production, When its mix is chosen, Then the difficulty picks the doctrine, rolled from the mission seed among those the difficulty allows; and where foresight is on the enemy changes its priorities from what its side has seen of the player, so its playstyle is not fixed (Westley, 2026-10-07: "#10: C with a random roll (but enemy can be reactive and change their priorities based on the player)"). How the doctrine and the script's target ratio (E-15 S-128) combine is the Architect's.
- R-215-08  Given the enemy's foresight and its multi-layer intelligence (R-125-01), When both are set, Then the difficulty sets foresight (E-22 R-181-03) and the lab sets the multi-layer intelligence, as separate steps (Westley, 2026-10-07).

Inputs: difficulty, which also sets foresight; the doctrine; the enemy's base and economy state; what the enemy's side has seen.
Outputs: the enemy economy's orders, in the command log (S-217); production choices in the T1 trace.
Open flags: none.

### S-216 — The enemy fights over its bases
As a commander, I want the enemy's forces to defend its base and its expansions, to fall back to what it still holds, and to raid my workers and shipments, so that the enemy plays the same war over the economy that I do.

Status: design decided 2026-10-02, not scheduled for building.

Rules
- R-216-01  Given an enemy base of operations, expansion or forward works (E-22 S-175), When its forces are scripted, Then their behaviour is tied to those places and they defend them, with new behaviours added beside the five of R-120-01 for defending a base, founding an expansion and raiding (Westley, 2026-10-07: "#11: B").
- R-216-02  Given an enemy force that retreats, When the enemy holds a base of operations, Then it plain-moves to that base, which after a fall-back (E-22 S-178) is the expansion or forward works the enemy held; where the enemy holds no base, its mission ends and is scored (E-22 R-178-05; Westley, 2026-10-06).
- R-216-03  Given the enemy economy founds an expansion or builds production forward, When it chooses where and when, Then the behaviour script (the authored per-mission plan of states, hooks and timers) names the push and the economy rules pick the site (Westley, 2026-10-07: "#12: C"; Westley: "Where it stands shows where the next push comes from").
- R-216-04  Given raid lanes set by the terrain (E-22 S-174), When the enemy raids, Then a force travels along a lane to the player's workers or shipments; raids are scripted and do not need foresight, though shipments are blind (E-22 S-176; Westley, 2026-10-07: "No enemy doesn't need foresight on to raid you.").

Inputs: the enemy's bases (E-22 S-175, S-178); raid lanes (E-17); the script.
Outputs: enemy commands in the command log; force state in the T1 trace.
Open flags: none.

### S-217 — The enemy uses the layers
As a commander, I want the enemy to move between layers, ping and go quiet as I can, so that the layers are as much its ground as mine.

Status: design decided 2026-10-02, not scheduled for building.

Rules
- R-217-01  Given a force that should change layer, When the macro layer acts, Then it may issue the hard layer transfer of E-01 S-002, on the same rules as the player's.
- R-217-02  Given the era has the technology for it, When the macro layer wants to see another layer, Then it may issue the targeted ping of E-01 S-162 on the same limits as the player's; the pinged player is told nothing (R-162-03, alert off for now); where the era uses scouts (R-162-04) the ping is carried by them.
- R-217-03  Given a force, When the macro layer sets it to emit or to silent (E-01 S-163), Then the same costs and sight apply as for the player's forces.
- R-217-04  Given difficulty, When the macro layer is set up, Then which of these commands it may use scales with its multi-layer intelligence (R-125-01), by numbers the skill lab sets.
- R-217-05  Given the enemy economy issues orders to build, train or gather (S-215), When they are issued, Then they are orders a player could issue and they appear in the same replay stream as the enemy's other commands (R-123-02) (the economy's commands are not yet in the command vocabulary; Q-217-01 closed 2026-10-18, Architect, implementation).

Inputs: the macro layer's state; the era pack.
Outputs: enemy layer and economy commands in the command log and replay.
Open flags: none.

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Behavior script | E-21 library per archetype | forces, states, transitions, hooks, bus vocabulary | validation errors fail mission generation |
| Tactical state | E-11, E-13 | | |
| Mission start RNG | Seed | | |
| Difficulty | E-08 | easy, medium, hard | |
| Enemy foresight choice | Player (E-10) | on or off | [Q-215-01: where chosen] |
| The enemy's bases, expansions, raid lanes | E-22 S-175, S-178; E-17 | | |
| Era layer commands | E-01 S-002, S-162, S-163 | | |

## Outputs

| Output | Observable where |
|---|---|
| Enemy commands | Command log; replay |
| Force states, transitions, bus | T1 trace; save |
| Reinforcement wave | Briefing; spawn events |
| Enemy economy and layer orders | Command log; replay |

## Invariants

- The macro layer issues only commands a player could issue: today the four of R-120-04, and the layer and economy commands of S-217 once built.
- The enemy's economy never scouts, counters or disguises unless the player turned foresight on.
- Every transition noise is drawn once per mission.
- Ambush never resets.
- Same seed, same enemy, all platforms.

## Scale requirements

Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is escalated): macro evaluation for 10 forces over 1,000 units in under 1 ms per evaluation tick.

The long-term goal is thousands of units and workers on one map (hub, "Reference Hardware"). Whether this budget covers the enemy's economy and workers is Q-215-04; it is not changed here.

## Look and behavior references

None required.

## Ways this could be wrong

- Noise re-rolled per evaluation, so transitions jitter.
- Timer measured from mission start instead of state entry.
- Cautious break-off measured against mission-start HP instead of state-entry HP.
- Ambush resets after the trigger leaves.
- Hooks evaluated after base transitions.
- Bus flags never set, so multi-force reactivity is dead.
- Macro reads true enemy positions the player cannot see (it may; it must not read the player's visible set). An enemy with foresight on learns about the player only through its own side's sight (E-12 R-093-02).
- The enemy's economy scouts, counter-shifts or disguises with foresight off.
- Enemy foresight scaled by difficulty instead of left to the player.
- A retreating force sent to the spawn edge while the enemy holds an expansion or forward works.

## Open ambiguity flags

None. Details in `docs/northstar/ambiguity_register.md`.

## Depends on

- E-10 (archetype, script selection, briefing, the enemy's base kind S-210, the end of a mission when a base falls S-212), E-11 (unit loop), E-13 (commands), E-15 (enemy production target ratios, S-128 and its relation to the doctrines of S-215), E-17 (spine nodes as targets, raid lanes), E-21 (script library and validation).
- E-01 (the layer commands, S-002, S-162, S-163), E-12 (the enemy's sight, R-093-02), E-19 S-159 and E-22 Economy and bases (S-174 raid lanes, S-175 expansions and forward works, S-178 when a base falls, S-179 and S-181 the economy without a player and the enemy's economy).

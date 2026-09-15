# E-15 — Reinforcement Structures, Non-Combat Units, Hazards, and Moving Battlefields

## Definition-completeness gate (run 2026-09-10)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Yes, 6 stories, 33 rules, numbers from `algorithms.md` ALG-75 and config. |
| Every input listed with range and rejection behavior | Yes, see Inputs. |
| Every output listed with where it is observable | Yes, see Outputs. |
| Implied-but-unstated behavior turned into flags | 6 new flags, Q-126-01, Q-126-02, Q-127-01, Q-128-01, Q-129-01, Q-131-01. |
| Every visible-surface story has a reference | **No.** S-131 (how structures, convoys, and hazards read on screen) has a visible surface and no reference. |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed.** Blocked on 6 open flags and one reference. Q-126-01 (the bible's open tuning questions on production rate, cost model, and baseline trickle were never closed) and Q-127-01 (Westley's Stage 1 note that the C rewrite may scale the starting-force share past half, A-081) are the load-bearing ones.

## Purpose

The player's starting force is about half of what they field over a mission. The rest comes from the region's own military infrastructure: garrison posts and militia stations already on the map that either side can capture by standing there unopposed, hold, and produce from. This is not base-building and not an economy; it is leverage over what the region already has, and a thriving region has more of it than a gutted one. Non-combat units, convoys and evacuees, carry HP and no weapons and are the objective in escort and evacuation missions. One environmental hazard ships at launch, the sensor interference zone. Battlefields move: objectives and structures can drift along paths and hazards can travel.

## Obviously working in 60 seconds

Start a medium Defensive Stand in a region with military 60: 3 to 6 structures, half player-owned, none neutral for long. Park three units inside a neutral structure's 300 wu radius with no enemy present: after 10 s it flips to the player and its row appears on the HUD. Set it to Raider: 30 s × (Raider power / 100) later a Raider spawns beside it. Send a Bombard to shoot an enemy structure: it takes a committed attack to burn 3,000 HP; when it dies it is gone for the mission. Order an evacuation convoy along a route: it never fires, flinches from damage, and counts toward the objective when it reaches extraction.

## Stories

### S-126 — Half my force is out there
As a commander, I want reinforcements to come from the region's own garrisons that I capture and hold, so that the map is a resource I fight over without ever building a base.

Rules
- R-126-01  Given a mission, When structures are placed, Then count = clamp(floor(region military × 0.06), small [2, 4], medium [3, 6], large [4, 8]) and the archetype's split assigns player, enemy, and neutral owners (defensive stand 50/25/25, siege 33/33/34, reconquest and assault 25/50/25, suppression and counterinsurgency 40/30/30, multi-front 40/35/25, interception and containment 33/34/33, evacuation 50/25/25), player at least 1.
- R-126-02  Given a held structure with a chosen unit type, When its production timer reaches 30 s × (that type's power / 100), Then one unit of that type spawns within half the capture radius of the structure on the structure's layer and the timer subtracts the interval.
- R-126-03  Given the player clicks a held structure, When they pick a type, Then production switches to it at once and the current timer continues.
- R-126-04  Given the whole mission, When forces are counted, Then the starting force is roughly half of what the player fields over a full mission [Q-127-01].
- R-126-05  Given a structure, When its production is read on the HUD, Then the player sees the timer bar, next unit, and HP (E-16 R-104-06).

Inputs: region military; archetype; player type choice.
Outputs: structures (owner, HP, timer, type) in the tick delta; spawns.
Open flags: Q-126-01 (production rate, unit cost model, baseline trickle with zero structures, placement strategy: the bible lists them as open and never closed them; code has 30 s scaled by power, no cost, no trickle), Q-126-02 (structure spawn position is random and not seeded from the world RNG in code, breaking determinism), Q-127-01.

### S-127 — Taking a garrison
As a commander, I want to capture a structure by holding it unopposed, and to be able to destroy one I cannot hold, so that garrisons are contested ground.

Rules
- R-127-01  Given units of exactly one non-owner faction inside a structure's 300 wu radius and no owner units, When ticks pass, Then capture progress rises by dt / 10 s; at 1.0 the owner flips and progress resets.
- R-127-02  Given units of two or more non-owner factions inside, or the owner also present, When ticks pass, Then progress resets to 0.
- R-127-03  Given a structure at HP 3,000, When attacked, Then it takes damage like a unit with no matchup multiplier; at 0 HP it is removed for the rest of the mission and never rebuilt.
- R-127-04  Given a structure changes owner, When the ticker runs, Then "structure captured" or "structure lost" appears (E-16 R-104-01).
- R-127-05  Given a structure's HP, When read, Then it is 3,000 (ALG-75) with no category multiplier applied to structures; a single Bombard at 70 per attack needs about 43 attacks, so splash alone does not destroy it in one engagement.

Inputs: unit positions and factions; damage.
Outputs: ownership, progress, HP in the delta; ticker.
Open flags: none.

### S-128 — What the enemy builds
As a commander, I want the enemy to build toward a composition I can read and adapt to, so that watching its production is a skill.

Rules
- R-128-01  Given the enemy's target ratio (per archetype script), When a structure's timer fires, Then it produces the category most below its target share.
- R-128-02  Given the player's composition has a category at 70 percent or more, When the target is computed, Then 15 percent of the target shifts to the counter category (Strike counters Siege, Line counters Strike, Siege counters Line), taken proportionally from the others, then renormalized.
- R-128-03  Given the enemy, When it produces, Then it never deviates from the ratio otherwise.

Inputs: target ratio; both compositions.
Outputs: enemy production choices in the T1 trace.
Open flags: none.

### S-129 — Units that cannot fight
As a commander, I want convoys and evacuees to be real units that die, so that protecting them is a mission and not a checkbox.

Rules
- R-129-01  Given a non-combat unit, When the decision loop runs, Then it never acquires a target, never returns fire, flinches from damage, and otherwise holds or follows its move order.
- R-129-02  Given an escort or evacuation objective, When a non-combat unit reaches the extraction point alive (within 200 wu), Then it counts toward completion (E-10 R-075-04).
- R-129-03  Given a non-combat unit, When drawn, Then it reads as non-combat at a glance.
- R-129-04  Given the asset categories of the hub (science units, intelligence operatives, cultural missions), When a mission includes them, Then [Q-129-01: only convoys and evacuees exist in code; the others are undefined; cultural missions have an onboarding opt-out per A-074].

Inputs: unit type flags; objectives.
Outputs: objective progress; screen.
Open flags: Q-129-01.

### S-130 — The battlefield moves
As a commander, I want objectives and garrisons that drift and hazards that travel, so that no position stays solved.

Rules
- R-130-01  Given a spine node of type objective or reinforcement_structure with waypoints, a period in ticks, and a mode, When ticks pass, Then its position is the interpolation along its waypoints, ping-pong (out and back) or loop, at tick mod period.
- R-130-02  Given a drifting objective, When it moves, Then the hold zone moves with it and progress continues only while no enemy is inside the moved zone.
- R-130-03  Given a drifting structure, When it moves, Then its capture radius and spawn position move with it.
- R-130-04  Given a sensor interference source with motion, When ticks pass, Then interference at any point follows the source (E-12 R-090-04).
- R-130-05  Given a battle in transit (convoy moving), When engaged, Then the convoy keeps its move order and the fight happens around it.

Inputs: drift specs from the map seed.
Outputs: positions per tick in the delta.
Open flags: none.

### S-131 — Reading hazards and structures
As a commander, I want a nebula to look like a place I cannot see into and a garrison to look like something I can take, so that the map explains itself.

Rules
- R-131-01  Given a T2 screenshot, When inspected, Then structures are distinguishable by owner color and from every unit silhouette; interference zones read as obscuring volumes; convoys read as non-combat.
- R-131-02  Given the launch hazard list, When read, Then it is exactly one type, sensor interference; drag, damage, boost, and disruption zones are future gradient tags with no engine change.

Inputs: map seed; ownership.
Outputs: screen.
Open flags: Q-131-01 (settlement vs station naming: `docs/bible_history/bible_2_00_world.md` says the one capturable structure is a settlement with its own silhouette; `docs/bible_history/bible_2_00_combat.md` says garrison posts, militia stations, FOBs). Reference required: `references/E-15/notes.md`, missing.

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Region military | E-02 | [0, 100] | |
| Archetype split and target ratio | E-10, E-21 | fractions summing to 1 | invalid fails load |
| Player production choice | Player | one of 6 types | unknown type rejected |
| Drift specs | E-17 | waypoints ≥ 2, period > 0, mode | invalid fails generation |
| Unit power | E-11 | > 0 | |

## Outputs

| Output | Observable where |
|---|---|
| Structures (owner, HP, progress, timer, type, position) | Tick delta; HUD structure panel; minimap |
| Spawns | Tick delta events |
| Enemy production choices | T1 trace |
| Drifting positions | Tick delta |

## Invariants

- A structure has exactly one owner or is neutral.
- Capture progress in [0, 1]; resets on contest.
- A destroyed structure never returns.
- Same seed, same spawns and drift, all platforms (pending Q-126-02).

## Scale requirements

Proposed for Westley to confirm: capture and production for 8 structures in under 0.2 ms per tick.

## Look and behavior references

`references/E-15/notes.md`, missing.

## Ways this could be wrong

- Capture progresses with the owner present.
- Two enemy factions inside count as one capturer.
- Production timer resets on type change.
- Spawn position from an unseeded RNG.
- Structure takes matchup multipliers.
- Drifting objective's zone stays at the spawn position.
- Convoy returns fire.

## Open ambiguity flags

Q-126-01, Q-126-02, Q-127-01, Q-129-01, Q-131-01. Details in `docs/northstar/ambiguity_register.md`.

## Depends on

- E-02 (region military), E-10 (archetype, objectives), E-11 (unit types and power), E-12 (interference), E-13 (movement), E-14 (enemy target ratio), E-16 (structure panel, ticker), E-17 (placement and drift specs).

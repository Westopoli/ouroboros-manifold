# E-15 — Reinforcement Structures, Non-Combat Units, Hazards, and Moving Battlefields

## Definition-completeness gate (run 2026-09-10, extended 2026-10-02)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | S-126 to S-131: yes, 6 stories, 27 rules, numbers from `algorithms.md` ALG-75 and config. S-218 and S-219: 2 stories, 14 rules, design decided 2026-10-02 and not scheduled for building; where Westley has not given a number the rule carries a flag instead. |
| Every input listed with range and rejection behavior | Yes, see Inputs. |
| Every output listed with where it is observable | Yes, see Outputs. |
| Implied-but-unstated behavior turned into flags | No open flags on S-126 to S-131, and 3 on S-218 and S-219 (Q-118-03, Q-219-02, Q-219-04). Q-219-02 is to be designed and Q-219-04 is parked. |
| Every visible-surface story has a reference | **No.** S-131 (how structures, convoys, and hazards read on screen) has a visible surface and no reference. |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed.** Blocked on the open flags of S-218 and S-219 and on one missing reference (S-131). S-126 to S-131 have no open flags; gate to be rerun.

## Purpose

Reinforcement comes from strongpoints, the reinforcement structures, which stand at the slopes between height bands on land maps. A side that holds one holds the way up or down at that slope and produces on that band, and the production is paid for by its economy (S-218, E-22). Non-combat units, convoys, evacuees and workers, carry HP and no weapons; convoys and evacuees are the objective in escort and evacuation missions, and shipments are things on the map that never fight (S-129). Each region has its own environmental trouble, and it travels across the map where both sides can see it and shuts down what it passes over (S-219). Battlefields move: objectives can drift along paths and hazards can travel.

## Obviously working in 60 seconds

Built today: start a medium Defensive Stand in a region with military 60: 3 to 6 structures, half player-owned, none neutral for long. Park three units inside a neutral structure's 300 wu radius with no enemy present: after 10 s it flips to the player and its row appears on the HUD. Set it to Raider: 30 s × (Raider power / 100) later a Raider spawns beside it. Send a Bombard to shoot an enemy structure: it takes a committed attack to burn 3,000 HP; when it dies it is gone for the mission. Order an evacuation convoy along a route: it never fires, flinches from damage, and counts toward the objective when it reaches extraction.

Decided, not built (S-218, S-219): on a land map with fitted height bands, a strongpoint stands at a slope between two bands. Take it, and units made there appear on its band and are paid for from your economy. Run a region's trouble across the map: both sides watch it move, and what it passes over stops working until it has gone by.

## Stories

### S-126 — Most of my force is out there

Direction changed 2026-10-02, rewrite pending: these structures become strongpoints at the slopes between height bands on land maps, their production is paid for by the economy and changing it takes a while, so units are no longer free, nothing switches at once and the split of the starting force is open (S-218). The rules below are what the game does today.
As a commander, I want reinforcements to come from the region's own garrisons that I capture and hold, so that the map is a resource I fight over without ever building a base.

Rules
- R-126-01  Given a mission, When structures are placed, Then count = clamp(floor(region military × 0.06), small [2, 4], medium [3, 6], large [4, 8]) and the archetype's split assigns player, enemy, and neutral owners (defensive stand 50/25/25, siege 33/33/34, reconquest and assault 25/50/25, suppression and counterinsurgency 40/30/30, multi-front 40/35/25, interception and containment 33/34/33, evacuation 50/25/25), player at least 1.
- R-126-02  Given a held structure with a chosen unit type, When its production timer reaches 30 s × (that type's power / 100), Then one unit of that type spawns within half the capture radius of the structure on the structure's layer (position from two world-stream draws, angle then distance; never from any other generator) and the timer subtracts the interval.
- R-126-03  Given the player clicks a held structure, When they pick a type, Then production switches to it at once and the current timer continues.
- R-126-04  Given a mission's expected full force F (E-10 force sizing), When forces are allocated, Then the starting force is 0.20 · F, and the reinforcement structures on the map can together produce at least 0.80 · F over the mission's time limit when all are held from the start; a player who holds every structure the whole mission fields at least F, and one who holds none fields 0.20 · F.
- R-126-05  Given a structure, When its production is read on the HUD, Then the player sees the timer bar, next unit, and HP (E-16 R-104-06).
- R-126-06  Given any mission, When production is read, Then units have no cost, and a player holding zero structures receives no trickle; the only reinforcement is R-126-02's structure production.

Inputs: region military; archetype; player type choice.
Outputs: structures (owner, HP, timer, type) in the tick delta; spawns.
Open flags: none.

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
Open flags: none. See also: S-218 (the structures become strongpoints; a destroyed one falls to rubble and can be refounded, which changes R-127-03) and E-22 S-178 (occupying a base is that story's, not this one's).

### S-128 — What the enemy builds

Direction changed 2026-10-02, rewrite pending: the enemy shifts its production toward a counter only when the player has turned enemy foresight on, and then reads only the player units it has seen, so R-128-02 and R-128-03 hold with foresight off only (E-14 S-215). The rules below are what the game does today.
As a commander, I want the enemy to build toward a composition I can read and adapt to, so that watching its production is a skill.

Rules
- R-128-01  Given the enemy's target ratio (per archetype script), When a structure's timer fires, Then it produces the category most below its target share.
- R-128-02  Given the player's composition has a category at 70 percent or more, When the target is computed, Then 15 percent of the target shifts to the counter category (Strike counters Siege, Line counters Strike, Siege counters Line), taken proportionally from the others, then renormalized.
- R-128-03  Given the enemy, When it produces, Then it never deviates from the ratio otherwise.

Inputs: target ratio; both compositions.
Outputs: enemy production choices in the T1 trace.
Open flags: none.

### S-129 — Units that cannot fight
Flag closed, rule text pending: Q-129-01, only combat forces and convoys or evacuees ship at launch; science, intelligence and cultural units wait for future story packs. The rule below is what the tests read today.
As a commander, I want convoys and evacuees to be real units that die, so that protecting them is a mission and not a checkbox.

Rules
- R-129-01  Given a non-combat unit, When the decision loop runs, Then it never acquires a target, never returns fire, flinches from damage, and otherwise holds or follows its move order.
- R-129-02  Given an escort or evacuation objective, When a non-combat unit reaches the extraction point alive (within 200 wu), Then it counts toward completion (E-10 R-075-04).
- R-129-03  Given a non-combat unit, When drawn, Then it reads as non-combat at a glance.
- R-129-04  Given the asset categories of the hub (science units, intelligence operatives, cultural missions), When a mission includes them, Then [Q-129-01: only convoys and evacuees exist in code; the others are undefined; cultural missions have an onboarding opt-out per A-074].

- R-129-05  Given a worker (E-22 S-167), When the decision loop runs, Then it is a non-combat unit under R-129-01: it never acquires a target, never returns fire and flinches from damage, and besides move orders it follows the gather orders of E-22 S-167; it is a unit, counted in the one population cap (E-22 S-169) and in the unit budgets.
- R-129-06  Given a shipment on the map (E-22 S-176 owns its rule), When it is raided along a lane (E-22 S-174), Then it never fights back (R-129-01) and, to a side that can see it, it reads as non-combat (R-129-03).

Inputs: unit type flags; objectives.
Outputs: objective progress; screen.
Open flags: none.

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
Open flags: none. See also: R-218-07 (a strongpoint does not drift, against R-130-01 and R-130-03) and S-219 (a region's trouble travels; R-130-04's interference source is one kind of moving source).

### S-131 — Reading hazards and structures

Direction changed 2026-10-02, rewrite pending: hazards are the environmental troubles of regions, several kinds, set per region, and a trouble travels and shuts down what it passes over (S-219), so R-131-02's single type goes. The rules below are what the game does today.
As a commander, I want a nebula to look like a place I cannot see into and a garrison to look like something I can take, so that the map explains itself.

Rules
- R-131-01  Given a T2 screenshot, When inspected, Then structures are distinguishable by owner color and from every unit silhouette; interference zones read as obscuring volumes; convoys read as non-combat.
- R-131-02  Given the launch hazard list, When read, Then it is exactly one type, sensor interference; drag, damage, boost, and disruption zones are future gradient tags with no engine change.

Inputs: map seed; ownership.
Outputs: screen.
Open flags: none here. The capturable structure is named Settlement engine-wide, with an era-skinned model. Reference required: `references/E-15/notes.md`, missing. See also: R-218-08 and R-219-06 (how strongpoints and troubles read; the name "strongpoint" is for the mechanic, with an era-skinned visual).

### S-218 — Strongpoints hold the way up and down
As a commander on a land map, I want the reinforcement structures to stand at the slopes between height bands, so that holding one holds the way up or down and gives me production on that band, paid for by my economy.

Status: design decided 2026-10-02, not scheduled for building. It applies to land maps; the space-era landscape is not designed (Q-166-02), so there is no space version. The built rules of S-126 and S-127 stay as they are until this story is built.

Rules
- R-218-01  Given a land map whose ground has height bands fitted to it (E-17 R-166-04 and R-166-06) and slopes that join layers (E-01 R-001-07), When strongpoints are placed, Then they stand at the slopes between height bands, each strongpoint at its slope's midpoint. The count is R-126-01's, capped by the slopes there are, placed on the best slopes, with its archetype owner split (Westley, 2026-10-06; E-17 R-192-01; midpoint, Architect 2026-10-10).
- R-218-02  Given a strongpoint, When a side holds it, Then it holds the way up or down at that slope (Westley, 2026-10-02, option D4: "Holding one holds the way up or down, and gives production on that band") Holding does nothing to passage beyond a position to fight from and production (Westley, 2026-10-06).
- R-218-03  Given a held strongpoint, When it produces, Then the units appear on the strongpoint's band, and the production is paid for by the holder's economy (E-22 S-167 and S-170), not free.
- R-218-04  Given a held strongpoint, When what it makes is chosen, Then the economy rules choose it on the schedule of E-22 S-170, changing what it makes takes a while, and when nobody holds the economy seat the rules and the commander's override of E-22 S-179 and S-180 decide.
- R-218-05  Given a strongpoint, When it is attacked or taken, Then it is captured as S-127 says, and when destroyed it falls to rubble; a strongpoint at 0 HP stays listed as rubble, and the place command at its cell refounds it for the placer at full HP (Westley, 2026-10-06, this replaces R-127-03's "never rebuilt"; listing and refounding, Architect 2026-10-10).
- R-218-06  Given the starting force and the strongpoints' production, When a mission's forces are allocated (E-10 S-074), Then the split of R-126-04 (a fifth at the start, the rest from structures) is dropped and the situation (E-10 S-211) decides; until S-211 the starting force is the whole force and the reinforcement capacity is 0 (Westley, 2026-10-06; liberty, Architect 2026-10-10).
- R-218-07  Given a strongpoint on a slope, When drift specs are read (S-130), Then a strongpoint does not drift: it is fixed at its slope for now (Westley, 2026-10-07).
- R-218-08  Given a T2 screenshot, When inspected, Then a strongpoint is distinguishable by owner color from every unit silhouette and from a base, an expansion and forward works The mechanic is called "strongpoint", with an era-skinned visual, so it does not clash with "settlement" for the neutral populace and for self-built cities (Westley, 2026-10-06).

Inputs: the fitted height bands and slopes (E-17); the holder's economy (E-22).
Outputs: strongpoints (owner, HP, progress, band, position) in the tick delta; production on the band; HUD panel and minimap.
Open flags: none.

### S-219 — Weather that travels
As a commander, I want my region's environmental trouble to travel across the map where both sides can see it and to shut down what it passes over, so that the map has a danger and a clock that is not an enemy.

Status: design decided 2026-10-02, not scheduled for building.

Rules
- R-219-01  Given a mission in a region, When its map is set up, Then the region's own environmental trouble is the one that travels the map, and different regions have different troubles; the trouble comes from the region's record, the same one that gives its climate and landform, derived from the seed for now (E-17 R-166-03; Westley, 2026-10-02) The troubles are a small fixed list (Westley, 2026-10-06).
- R-219-02  Given a trouble, When ticks pass, Then it travels across the map. Its path and speed are to be designed [Q-219-02]; Westley, 2026-10-06: it would be good if the player did not see it coming.
- R-219-03  Given a trouble on the map, When either side looks, Then both sides can see it.
- R-219-04  Given a unit, worker, shipment, building or production site that the trouble passes over, When it is under the trouble, Then it is shut down while the trouble is over it What shut down means differs per trouble (Westley, 2026-10-06).
- R-219-05  Given the sensor interference zone of S-130 and E-12 R-090-04, When troubles are listed, Then [Q-219-04: whether interference is one of the troubles or a separate hazard that stays; parked].
- R-219-06  Given a T2 screenshot, When inspected, Then a trouble reads as a distinct moving thing on the map, apart from the interference zone and from every unit.

Inputs: the region's trouble (seed, E-17); the trouble's path.
Outputs: the trouble's position per tick in the delta; which things it has shut down; screen.
Open flags: Q-219-02 (to be designed), Q-219-04 (parked).

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Region military | E-02 | [0, 100] | |
| Archetype split and target ratio | E-10, E-21 | fractions summing to 1 | invalid fails load |
| Player production choice | Player | one type from the era's roster | unknown type rejected |
| Drift specs | E-17 | waypoints ≥ 2, period > 0, mode | invalid fails generation |
| Fitted height bands and slopes | E-17, E-01 | land maps | a map with no slope between bands places no strongpoint |
| The region's trouble | Seed, E-17 (the region's climate and landform) | | |
| Economy state of the holder | E-22 | | |
| Unit power | E-11 | > 0 | |

## Outputs

| Output | Observable where |
|---|---|
| Structures (owner, HP, progress, timer, type, position) | Tick delta; HUD structure panel; minimap |
| Spawns | Tick delta events |
| Enemy production choices | T1 trace |
| Drifting positions | Tick delta |
| Strongpoints (owner, HP, progress, band, position) | Tick delta; HUD structure panel; minimap |
| The trouble's position and what it has shut down | Tick delta; screen |

## Invariants

- A structure has exactly one owner or is neutral.
- Capture progress in [0, 1]; resets on contest.
- A destroyed non-strongpoint structure never returns (R-127-03); a strongpoint at 0 HP stays listed as rubble and the place command at its cell refounds it at full HP (R-218-05, Architect 2026-10-10).
- A strongpoint stands at a slope between height bands on land maps.
- A trouble shuts down only what it is passing over, and both sides can see it.
- Same seed, same spawns and drift, all platforms (every draw comes from the world stream, R-126-02).

## Scale requirements

Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is escalated): capture and production for 8 structures in under 0.2 ms per tick.

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
- A worker or shipment acquires a target.
- Strongpoints placed on flat ground, or all on one band.
- Strongpoint production free of cost, or switched at once.
- A trouble visible to one side only, or shutting down things it is not over.
- The single interference zone treated as the only hazard.

## Open ambiguity flags

Q-219-02, Q-219-04. Details in `docs/northstar/ambiguity_register.md`.

## Depends on

- E-02 (region military), E-10 (archetype, objectives), E-11 (unit types and power), E-12 (interference), E-13 (movement), E-14 (enemy target ratio, the enemy's foresight S-215), E-16 (structure panel, ticker), E-17 (placement, slopes and drift specs).
- E-01 (slopes and layers, R-001-07), E-19 S-159 and E-22 Economy and bases (S-167 workers, S-169 the cap, S-170 production, S-174 raid lanes, S-176 shipments, S-178 when a base falls, S-179 and S-180 the economy without a player).

# Layer dynamics: the layer lab

## 1. Purpose and status

Opened 2026-09-30. Design phase for the research program in register `Q-008-02` and research queue `Q76`. It feeds `Q-008-03` (the cross-layer numbers), E-01 S-008, E-12 (fog and sensors) and E-14 S-125 (what hard-mode AI strives for). Nothing here is bible text. When the lab yields numbers they are folded into `algorithms.md` and the S-008 rules, and this document is then a record.

The question: how do units on different layers damage and see each other so that the engagement's conditions, not the raw numbers, decide who wins? The method: a fast standalone C simulator (the layer lab, `toys/layerlab/`) that carries the system's constraints, run in small engagements that vary everything an RTS varies, read after every run, tuned, and run again.

## 2. Westley's own words, verbatim

2026-09-30.

> "The player owns the layer, so nothing ever changes it automatically." Unless their units are forced because of terrain. If they move-command someplace that doesn't have access to the layer they're on, but does have access on another layer that they can transition to, then their units automatically transition (like units walking up a mountain). Record that decision.

> I'd like to start ( idea about layer simulation, simple prototype to tune numbers to produce strategy situations ) a specific method of figuring out how we'll do this. We will build a "toy" prototype. It will have the basic functions of the game, and be very fast, all C, bare minimum visuals maybe with python game library or something simple. It will contain the restraints of the system, layers, damage, vision, landscape. The prototype will run "simulations" of unit complex combinations: position, orientation, damage, health, anything that we can vary in an RTS. We'll use this simulator to document the relationships between all the variables and find the places that the "lines cross". We'll use this as a map for tuning units across different eras, and maintaining strategic depth. For example, we may notice that changing the vision variable only produces only strategic depth at a specific "value" given the values of all the other variables, however, if we change another one, the "lines cross" in more than one place, and induce strategic depth from two configurations of variables instead of one. This will require significant iterations and tuning, so the algorithms need to be fast. This is just an idea in my head currently, I want to explore it further and verify it works with a simple prototype before we commit to building the full thing.

> We'll need to clearly define what "strategic depth" looks like, but we can grab from other similar high skill games like Starcraft 2. For example, in starcraft 2 when units have a layer advantage, they can shoot without being shot back. When units have a surround, the units in the concave with the surround win. Organizing your units in specific patterns can lead to better engagements, depending on the unit, it's vulnerabilities and abilities, etc. For example: templar are very weak and slow and expensive, but when they use storm they're devestating to low-health units. A player that effectively protects them has a higher chance of winning. We will need to map all these dimensions out before we build anything.

> Develop a plan to document the idea in the bible (with a pass after it's documented cross-referencing my original prompt with what was actually written for missed information or hallucinations), map out the dimensions, build a toy prototype of it, and find out if the hypothetical "lines crossing" is evident in the data (configurations that produce victory from the expected player given the conditions of the engagement). We don't need to do a large batch of thousands of "runs" and then analyze the data, I think it'd be much faster to iteratively try small things, check the output, and tune repetatively.

Also in scope from 2026-09-23 (`Q-008-02`): a surround theory taken into three dimensions, drawing on high-altitude aerial battle research.

## 3. Fixed constraints

These come from the bible and the register; the lab does not vary them unless a run says so.

- Five layers, always; layer 1 is the bottom (Q-001-01, Q-001-02). A unit is on exactly one layer at every tick.
- Terrain blocks layers at places (E-01 S-001). A unit never occupies a blocked position and layer.
- Layer changes on the route: a unit takes the shortest route to its goal across every layer it may use, changing layer on the way where that is shorter (E-01 R-001-05, `Q-001-04` closed 2026-10-01). The lab keeps an off switch only because a control needs an off state. What the ruling leaves open is `Q-001-05` (distance or time, the layer a flying unit ends on, pending transfers and preferences); the lab takes the recommended reading there and can vary it.
- A transition is one transition of one duration regardless of distance (Q-002-01), by unit type (Q-004-01: Raider 1.0 s, Interceptor 1.2 s, Vanguard 2.5 s, Warden 2.0 s, Bombard 4.0 s, Bastion 5.0 s). The old layer may attack the unit until the halfway point, the new layer from the halfway point on; visibility follows the normal cross-layer sensor rules (Q-004-02). E-01 R-004-02 carries the same rule.
- Slopes (Q-004-03, Westley 2026-09-30: "Choice 2 set by the slope, no need for a switch."): a slope is a band of ground joining two layers, adjacent or not. On a slope the transition is the unit's position along it, not a timer: the time is slope length divided by unit speed, the halfway point is the slope's midline, and a unit may stop or turn back (E-01 R-001-06, R-004-06 to R-004-08). The timed rule above applies only to a transfer away from a slope. The lab builds this one way, with no timed-versus-slope switch. A unit on a slope counts as on the layer on its side of the midline (Q-004-04).
- Unit movement kinds (Q-004-04, Westley 2026-09-30): flying and swimming units change layer anywhere nothing blocks, by a timed transfer; walking units stand only where a layer has land, change layer only by walking a slope, and never rise in place (E-01 R-001-07).
- A transitioning unit may attack, in a timed transfer or on a slope, while it can see its target, and stops when the transition takes that sight away (E-01 R-004-02).
- `Q-004-05` is closed with the recommended readings (2026-10-01): movement kind is set per unit type in the era pack and every Settled Reach type flies; the map carries a ground flag per layer; a slope spanning several layers has a cross-over at each layer boundary; a walking unit ordered to a layer paths to a slope, or the order is rejected.
- Every transition has a cross-over point: halfway through a timed transfer, the midline of a slope. Before it the unit is on the layer it is leaving, for attacking, being attacked and sensing; after it, on the layer it is moving to (E-01 R-004-02, the invariants). It is a matter of location, not timing.
- A unit never fires at a target it cannot see (`Q-008-04`, E-01 R-008-04). There is no blind fire.
- Vision across layers shrinks with distance: production uses factor 0.50 one layer away, 0.20 two layers away, none beyond, by absolute offset in either direction (`csrc/fog.c:585`); vision is symmetric by layer distance to start (`Q-005-02`, closed 2026-10-01), and asymmetric vision stays a candidate only if the top layer gets a counter; vantage nodes and interference zones modify it; cover blocks sight by height and never changes damage or movement (E-01 S-007).
- Production combat is same-layer only (Q-008-01). Every cross-layer rule in the lab is a hypothesis under test, not a fact about the game.
- Layer damage is weighted much more heavily than abilities and passives (Q-083-02, hub principle 4): an ability never outranks position in the lab either.
- Determinism: same seed and command stream give a byte-identical trace.

## 4. Strategic depth: the definition and four test cases

The hub definition (principle 4): the engagement's conditions, not its numbers, decide who wins. Westley's examples are from StarCraft 2; the four patterns below are their abstract form, and each is a named test case. "Expected winner" is what a knowledgeable player would predict from the conditions alone.

| Pattern | Source | Expected winner | What proves it (observables) |
|---|---|---|---|
| P1 High-ground asymmetry | "when units have a layer advantage, they can shoot without being shot back" | The force with the layer advantage | Unanswered-fire ticks per side; first-shot side; HP-remaining ratio; ticks until the disadvantaged side fires |
| P2 The concave in a surround | "when units have a surround, the units in the concave with the surround win" | The side in the concave | Winner and HP-remaining ratio across formation and count; cost lost per side |
| P3 The screened glass cannon | templar are "very weak and slow and expensive, but when they use storm they're devestating to low-health units. A player that effectively protects them has a higher chance of winning" | The player who protects the fragile unit has the higher chance of winning | Win rate across seeds as screen radius varies against enemy speed; cost lost; burst damage landed |
| P4 The smaller force wins by position | "Organizing your units in specific patterns can lead to better engagements" and the promise in E-01 | The smaller force, in the configuration where position outweighs numbers | Winner with unequal counts; the smallest count ratio at which the smaller side still wins |

Depth holds for a cross-layer rule set when each pattern is true under at least one reachable configuration (one the game can produce) and none is true under every configuration. A pattern true everywhere is a dominant strategy; a pattern true nowhere is a dead mechanic.

## 5. The dimension map

Every variable an engagement in the lab has, where it lives, its range, the production value where one exists, the rung that makes it sweepable, and which depth pattern (§4) it is expected to touch. Production numbers: `csrc/om_constants.h:479-531, 560-567` (roster, category matrix, vision factors, pulse), `csrc/unit.c:84-102` (transition times), `csrc/om_constants.h:595-599` and `csrc/tactical_move.c:308` (turn rates). Damage and interval are per hit and per second as production states them; speed and range are world units per second and world units. "None" means production has no such value and the lab sets a starting one, marked lab-only.

Rungs: R0 flat combat; R1 terrain, vision, transitions, every cross-layer knob; R2 facing, formations, the storm-shaped ability; R3 sweeps and replay. A variable is fixed in the rung before the one that sweeps it.

### Unit type (owner: roster)

| Variable | Range | Production value | Rung | Pattern |
|---|---|---|---|---|
| HP | 100 to 1,500 | Raider 250, Interceptor 325, Vanguard 500, Warden 375, Bombard 400, Bastion 1,050 | R0 | P3, P4 |
| Damage per hit | 1 to 30 | Raider 9.0, Interceptor 6.0, Vanguard 7.5, Warden 4.0, Bombard 17.5, Bastion 7.0 | R0 | P1, P4 |
| Attack interval (s) | 0.5 to 4 | Raider 0.8, Interceptor 1.0, Vanguard 1.2, Warden 1.5, Bombard 3.0, Bastion 1.8 | R0 | P1, P2 |
| Range | 150 to 1,500 | Raider 200, Interceptor 250, Vanguard 300, Warden 350, Bombard 1,200, Bastion 800 | R0 | P1, P2 |
| Speed | 30 to 200 | Raider 150, Interceptor 130, Vanguard 80, Warden 70, Bombard 50, Bastion 40 | R0 | P3, P4 |
| Sensor radius | 300 to 1,000 | Raider 800, Interceptor 1,000, Vanguard 700, Warden 800, Bombard 300, Bastion 300 | R1 | P1 |
| Layer transition time (s), for a timed transfer; on a slope the time is length over speed | 0.5 to 6 | Raider 1.0, Interceptor 1.2, Vanguard 2.5, Warden 2.0, Bombard 4.0, Bastion 5.0 | R1 | P1, P4 |
| Area radius | 0 to 300 | Bombard 150, all others 0 | R0 | P2, P3 |
| Category (Strike, Line, Siege) | 3 values | Raider, Interceptor Strike; Vanguard, Warden Line; Bombard, Bastion Siege | R0 | P2, P4 |
| Turn rate (rad/s) | 1 to 8 | Strike 6.0, Line 4.0, Siege 2.5, chosen by speed (Strike at 100 and above, Line at 60 and above) | R2 | P2 |
| Firing arc (degrees) | 30 to 360 | None; lab-only, 360 means no arc | R2 | P2, P3 |
| Cost | 20 to 200 | The interim power rating, HP × damage per hit / attack interval, normalized so a Vanguard is 100 (Q-074-01): Raider 90.0, Interceptor 62.4, Vanguard 100.0, Warden 32.0, Bombard 74.7, Bastion 130.7 | R0 | P3, P4 |
| Body radius (units cannot overlap) | 5 to 60 | 15 for every type (`OM_UNIT_COLLISION_RADIUS`) | R2 | P2 |
| Ability archetype: burst with windup and cooldown (the "storm" shape) | damage multiplier, radius, windup, cooldown, minimum targets | Bombard barrage: 3.0 times damage, radius 100, telegraph 30 ticks, cooldown 1,800 ticks | R2 | P3 |
| Movement kind (walking, or flying or swimming) | 2 values | none in production; set per unit type in the era pack, every Settled Reach type flying | R1 | P1, P4 |
| Pulse-capable | yes or no | Pulse radius 500, reveal 40 ticks, cooldown 400 ticks | R1 | P1 |

The category multiplier matrix (attacker row, target column) is `OM_CATEGORY_MULTIPLIER_*`: Strike 1.0, 0.75, 1.5 against Strike, Line, Siege; Line 1.5, 1.0, 0.75; Siege 0.20, 1.5, 1.0. Area damage is capped at 4.0 times a hit (`OM_AOE_DAMAGE_CAP_MULTIPLIER`). The lab leaves out Warden aura, brace, fortify, backswing, cohort targeting and the high-load halving (production behaviours with no bearing on layer geometry); they return only if a finding needs them.

### Engagement (owner: the scenario)

| Variable | Range | Production value | Rung | Pattern |
|---|---|---|---|---|
| Composition per side (types) | any roster mix | none (scripted) | R0 | P2, P3, P4 |
| Count per side | 1 to 50 | none | R0 | P2, P4 |
| Formation (line, concave, box, screen, column) | 5 presets plus spacing | none | R2 | P2, P3 |
| Initial position and separation | 0 to 2,000 | none | R0 | P1, P4 |
| Initial facing (degrees) | 0 to 360 | none | R2 | P2 |
| Initial layer per group | 1 to 5 | none | R1 | P1, P4 |
| Orders (hold, move, attack-move) and destination | per group | none | R0 | P1, P4 |
| Initiative (which side moves into range) | A, B, both | none | R0 | P1, P4 |
| Initial vision (blind or pre-revealed) | 2 values | none | R1 | P1 |
| Target selection (nearest in range, focus the lowest HP, focus the highest cost) | 3 policies per side | nearest in range, same layer | R0 | P2, P3 |
| Spawn jitter and attack-phase offset | seeded | none | R0 | none (seed spread) |

### World (owner: the map)

| Variable | Range | Production value | Rung | Pattern |
|---|---|---|---|---|
| Accessibility mask preset (flat, block, wall, barrier, lane, ramp; defined below) | 6 footprints | map generator output, binary per layer per position | R1 | P1, P4 |
| Blocked height h: the mask blocks layers 1 to h inside the footprint | 1 to 4 | E-01 S-001 example: h = 2 | R1 | P1, P4 |
| Land per layer: where a walking unit can stand | per layer per position | none in production; a ground flag per layer per position | R1 | P1, P4 |
| Slopes: position, width, length, and the layers joined (adjacent or not) | length 100 to 1,000; width 100 to 600 | none in the sim; E-01 R-004-07 uses lengths 150 and 600 | R1 | P1, P4 |
| Layer spacing | 10 to 200 | none in the sim (Q-E01-01 fixes on-screen elevation only) | R1 | P1 |
| Cover discs: position, radius, height in layers | 0 to 5 layers | per E-01 S-007 | R1 | P1, P4 |
| Vantage nodes | count, radius | per E-01 S-005 | R1 | P1 |
| Interference zones | count, radius, intensity 0 to 1 | per E-01 S-005 | R1 | P1 |

Terrain in this game is a binary mask, each layer open or blocked at each position (E-01 R-001-04), plus slopes, bands of ground that join two layers, adjacent or not (E-01 R-001-06), plus where each layer has land for walking units (E-01 R-001-07). A preset is a footprint (where layers 1 to h are blocked), the height h, and the slopes on it; layers above h stay open everywhere. The presets differ by whether a unit on a blocked layer can walk around, how far, and whether a slope lets it walk up.

| Preset | Footprint | Unit on layers 1 to h, crossing it | Unit above h | What it tests |
|---|---|---|---|---|
| flat | none: all five layers open everywhere | nothing in the way | nothing in the way | the control; no terrain effect |
| block | one compact region in the middle | goes around it, a short detour | flies straight over | high and low layers take different routes; the side that goes over can shoot down into the detour |
| wall | one long thin region across the arena, with open ends | goes around an end, a long detour | flies over | a line to hold; the flank around the end is the vulnerability |
| barrier | a region that spans the full arena width: no end to go around | cannot cross on its layer; a flying unit must change layer (E-01 R-001-05, the ruling); a walking unit cannot cross at all without a slope | flies over | the terrain-forced auto-transition; with the ruling off, the unit stops at the edge |
| lane | two blocks with an open channel between them, open on all five layers | funnels through the channel | flies over the blocks or uses the channel | a choke on the low layers that the high layers bypass |
| ramp | a barrier with one slope up its face, joining layer h to layer h+1 | walks up the slope; below the midline only the lower layer can hit it, above it only the upper layer (E-01 R-004-06) | a flying unit flies over; a walking unit on the high ground comes down only by the slope | high ground with one way up for walking units: the midline is the line to hold, and the slope's length sets how long a climber is exposed |

Block and wall differ only in shape (how long the detour is); barrier is the same wall made so long that there is no detour. Lane is two blocks facing each other. Ramp is the barrier with a slope. Each produces a different route decision; if two are not worth separate runs, merge them.

### Cross-layer rules (owner: the rule set; the unknowns the lab exists to find)

| Variable | Range | Production value | Rung | Pattern |
|---|---|---|---|---|
| Vision factor by signed offset (target minus observer, 9 values) | 0 to 1 each | symmetric: 1.0, 0.50, 0.20, 0, 0 at absolute offset 0 to 4 (`OM_CONE_LAYER_1_FACTOR`, `OM_CONE_LAYER_2_FACTOR`, `csrc/fog.c:585`); symmetric to start (Q-005-02 closed); the asymmetric variant is a later candidate | R1 | P1 |
| Vantage vision factor by signed offset | 0 to 1 each | 1.0, 1.00, 0.40, 0.20, 0 at absolute offset 0 to 4 (E-01 R-005-06) | R1 | P1 |
| Sensor bonus per layer of elevation | 0 to 0.5 | none per layer: production's 0.15 (`OM_ELEVATION_SENSOR_BONUS_PER_TIER`) is per elevation tier, which is not a layer; lab default 0, so R-005's numbers hold | R1 | P1 |
| Range multiplier by signed offset (target minus attacker, 9 values) | 0 to 2 | none; same-layer only (Q-008-01) | R1 | P1 |
| Damage multiplier by signed offset | 0 to 2 | none | R1 | P1, P4 |
| Area-damage multiplier by signed offset | 0 to 2 | none | R1 | P2, P3 |
| Fire requires vision | fixed on | a unit never fires at a target it cannot see (Q-008-04, E-01 R-008-04); the lab uses one visibility function for target choice and for the fire check | R1 | P1 |
| Facing gates fire | on or off | none | R2 | P2 |
| Halfway rule during a transition | both always targetable, per rule (old layer until halfway, new layer after), untargetable | per rule (Q-004-02); on a slope the halfway point is the midline, by position (Q-004-03) | R1 | P1, P4 |
| Layer changes on the shortest route | on or off (off is the control) | on (E-01 R-001-05); edges per Q-001-05 | R1 | P4 |
| Movement speed during a timed transfer (not on a slope, where the unit moves at its own speed) | 0 to 1.0 times | none (mid-transition movement is unspecified in the bible beyond Q-004-02) | R1 | P1 |

### Outcomes and expected winners

A run reports: winner (A, B, stalemate, tick cap, mutual); survivors; HP-remaining ratio; cost lost per side; ticks to resolve; side and tick of first shot; first-contact tick; unanswered-fire ticks per side (ticks a side fired while the other, able to see or fire, did not); number of transitions and shots.

Each scenario carries an expected winner, stated before the run, from Westley's pillars (§2, §4). The expected winner is what a knowledgeable player would predict from the conditions alone. A run that disagrees with its expectation is first a question about the harness (check the controls), and only then a finding about the rules. Scenarios are at equal cost, count and type unless stated.

| # | Scenario | Expected winner | Basis | Outcome that proves it |
|---|---|---|---|---|
| X0 | Mirror: identical forces, flat, same layer, same formation | none; win rate near 0.5 | control, not a pillar | split of winners across seeds (the noise floor) |
| X1 | 10 against 5 of one type, flat | the 10 | positive control, not a pillar | winner, survivors |
| X2 | A one layer above B; A sees B; B cannot see A; A may fire down | A | "when units have a layer advantage, they can shoot without being shot back" | A's unanswered-fire ticks above 0, B's at 0 until B can see; HP-remaining ratio |
| X3 | As X2, but B sees A and cannot fire up | A | same | unanswered-fire ticks for A; B's shots 0 |
| X4 | As X2, but B sees A and can fire up at equal range and damage | none expected from the pillar; this is where the crossing v* lives | the pillar names no winner once both can answer | win rate as B's vision or fire-up value rises; the value where it crosses 0.5 |
| X5 | Same layer; A in the concave around B's line | A | "when units have a surround, the units in the concave with the surround win" | winner, HP-remaining ratio across formation and count |
| X6 | As X5 with the formations swapped | B | same | same; the mirror of X5 |
| X7 | Each side has one fragile, slow, expensive unit with a burst ability; A screens it, B leaves it exposed to fast enemies | A, as a higher win rate across seeds, not a certain win | "A player that effectively protects them has a higher chance of winning" | win rate across seeds as screen radius varies against enemy speed; burst damage landed; cost lost |
| X8 | A smaller than B, with layer advantage and concave; B a flat line | A, but only as far as the conditions carry it; the smallest count ratio at which A still wins is the measurement, not an assumption | "Organizing your units in specific patterns can lead to better engagements"; the E-01 promise that a smaller force that understands position beats a larger one | winner across count ratios; the ratio where it crosses 0.5 |
| X9 | A smaller force with one costly seer against a larger force on layers it cannot see | A, same caveat as X8 | Westley, 2026-09-23 (`Q-E12-01`), not the 2026-09-30 prompt | winner; first-contact tick; unanswered-fire ticks |
| X10 | Ramp preset, walking units on both sides: A holds the top of the slope, B climbs it; equal forces | A | "when units have a layer advantage, they can shoot without being shot back"; E-01 R-004-06: below the midline only the lower layer can hit a climber, above it only the upper layer | A's unanswered-fire ticks; win rate across slope length and count ratio; the slope length where it crosses 0.5 |
| X11 | As X10 with flying units on both sides | none; the ramp binds only walking units, so B flies up in a timed transfer and meets A on its layer | E-01 R-001-07 | win rate near 0.5; set against X10 it shows what the movement kind does |

Movement checks have no expected winner. They expect an arrival or a time. The auto-transition ruling across a block, wall or barrier: a flying unit is on layer 3 at the destination with the ruling on and stopped at the edge with it off. A walking unit at a barrier with no slope does not cross. On a 600-unit slope a Raider takes 4.0 s and a Bastion 15.0 s (E-01 R-004-07). A unit that turns back before the midline has not changed layer (E-01 R-004-08).

### How the map is used

The table is the lab's configuration surface and the axis list for §6. Each sweep picks one row as v, optionally one as w, and fixes every other row at the value the scenario states. The map is complete when every variable that the bible lets the player or the map change appears here; a variable that an experiment finds is missing is added in the same commit as the run that found it.

Status: Westley told the build to go ahead on this map, 2026-09-30 ("continue with plan execution given the new rules/info"). The pass criterion in §6 stays proposed until he confirms it.

## 6. The "lines cross" hypothesis, stated testably

Take a variable v (for example the range multiplier for fire from above) and hold every other variable fixed. The expected side's win probability is a function of v. It crosses 0.5 at some value v*. Depth exists on that axis when v* is reachable in play, meaning v* lies inside the range of values the game can produce. Now move a second variable w. Depth grows when w moves v* to another reachable value, or when w creates a second crossing, so two configurations of variables induce depth instead of one. That is Westley's "lines cross".

Pass criterion for the lab, confirmed by Westley 2026-10-01 with the fragile-unit pattern (P3) set aside until abilities are in scope: one shared cross-layer rule set under which patterns P1, P2 and P4 of §4 hold (each true in at least one reachable configuration, none true in every configuration), with at least one crossing on a layer-rule axis and at least one two-variable interaction that adds a crossing. A separate tuned rule set per pattern does not pass.

Negative control: with the cross-layer rules off (multipliers zero, no cross-layer fire), no crossing on that axis. A detector that finds crossings with the mechanism off is measuring the harness, not the game. Positive control: the count ratio between two equal forces on flat ground, swept from 1:2 to 2:1, must show its crossing near 1:1; a detector that misses that is not reading.

### 6.1 The firing-share hypothesis (2026-09-30, first check in §8)

Westley, 2026-09-30, verbatim, on pricing each advantage as a fixed multiple of numbers:

> holding a choke depends on the choke breadth, the ratio of how many units are able to get shots on both teams. It's not as simple as a 1.5x. If team A is holding the choke (at advantage), and as 3x as many units that *can* shoot, then they can take on 3x the force as long as they stay at that choke. It's about the number of units that can get off shots (which depends on several factors, range, choke breadth, etc.)

> just having a height advantage doesn't mean much, it's the vision that comes with the layer difference that is the advantage. 4 should be folded into 5. But for vision as well, it's not as simple as just a 1.25x, just like the choke it's the ratio of units that can get shots off vs the ones that can't compared to the same numbers for the opposite team. This is leading us to the core of the game: the differentiator is **can your unit get shots off**.

> Maybe we should measure "units firing" as a part of the simulation, it's appearing that most of my responses are leading to the "units firing" response with the labels being somewhat dependent on that reality. Maybe we could have the simulation constantly compare the number of units firing for both sides, and use that to weight which side "should" have won, and if they didn't than there's a number that's off. We should test this theory.

Also from the same message, as scope for the lab:

- Height is not an advantage of its own; the vision that comes with the layer difference is. Height and vision are one advantage.
- Abilities are out of this calculation for now: "we're tuning base unit properties, abilities are another dimension that's too hard to map out at this time." Scenario X7 and pattern P3 wait.
- Catching the enemy mid-transition depends on army sizes ("the larger army can just walk up the ramp and kill the smaller army"); it is a tool for setting up traps, surrounds, and unit-type matchups, and is "much more effective when used in combination with" the unit-type counter. Unit type is measured, "not just unit values but their type as well."
- A hit from behind or the flank is "useless without a surround, vision advantage, or unit placement/count advantage."

**The hypothesis.** Who wins an engagement is decided by how many units on each side can get shots off, and for how long. Chokes, vision, surrounds, slopes, transitions and facing matter only through what they do to that count. Unit type is the one other factor: it weights each shot. If a side with the firing advantage loses, some other number has overridden position, and that number is off.

**Why it is plausible.** It is the Lanchester square law: with aimed fire, a side's strength goes as per-unit firepower times the square of the units firing. The first damage sweep (`toys/layerlab/results/log.md`, B's fire-up damage multiplier d against B's count, A fixed at 10) already fits it. The law predicts B breaks even at 10 / sqrt(d) units:

| B units | 12 | 14 | 16 | 18 | 20 |
|---|---|---|---|---|---|
| d at the measured crossing | 0.747 | 0.550 | 0.444 | 0.350 | 0.250 |
| d the square law predicts (100 / B²) | 0.694 | 0.510 | 0.391 | 0.309 | 0.250 |

**The measurement the lab needs.** Per tick and per side, the number of living units that can fire: a target in range, seen, not blocked, the unit allowed to attack. The result today has total shots and unanswered-fire ticks per side, not this count. Add it to the result (per-tick series in the trace, and the sum over the fight).

**Two predictions, both ignorant of unit stats on purpose.** A prediction built from damage dealt against health always agrees with the outcome, because that is how the fight is computed; it tests nothing. So:

1. Count-only. For each side, firing fraction f = (sum over ticks of units that can fire) / (sum over ticks of units alive); predicted strength = f × (starting count)². The side with the larger strength is the predicted winner. This is a first form; the check below may show a better one.
2. Type-weighted. The same, with each unit that can fire counted as its category multiplier against its target's category (the Strike, Line, Siege matrix) instead of as 1.

Both are computed from the fight after it ends, so they diagnose a run; they do not forecast it.

**Reading a disagreement.**

| Count-only | Type-weighted | Meaning |
|---|---|---|
| right | right | position decided it |
| wrong | right | unit type decided it; acceptable, that is the rock-paper-scissors |
| wrong | wrong | another number (a layer damage or range multiplier, health, damage per shot) overrode position: the number that is off |

**The check, on runs that already exist.** X0 (mirror), X2, X3, X4, and the damage sweep. Expected: both predictions match the winner in X2 and X3 (B never fires), are near a toss-up in X0 and X4, and the count-only prediction fails in the sweep's low-d cells, where B has more units firing and still loses because each shot is weak. If that is what comes out, the metric separates "position decided" from "a number decided" and the hypothesis has a working instrument. If the count-only prediction is wrong where no stat differs, the form of the prediction is wrong, not the game.

**What it changes if it holds.** Expected winners stop being hand labels per scenario: the principle generates the label, and Westley's hand labels become spot checks on it. The collisions he had begun labelling are paused until the check is in; his answers so far all turned on which side gets shots off and for how long. It also bears on which lever carries the layer advantage: under this principle the advantage comes from who can fire (vision, reach, terrain), not from a damage bonus for height. That last point is an inference from his words, not a ruling.

### 6.2 What the theory predicts: experiments from research Q77 (2026-10-01, none run)

Source: `docs/research/topics/lanchester_and_combat_theory.md` (the brief; confidence tags and sources are there). Each row is a prediction from published combat theory that the lab can confirm or refute with small runs. The predictions are the theory's, for identical units with aimed fire; a miss is a finding about the lab or about the theory's assumptions, and either is worth knowing. Nothing here is a ruling.

| # | Experiment | What the theory predicts | Lab needs |
|---|---|---|---|
| E1 | Choke breadth. 20 against 10 identical units; sweep how many can engage at once (the lane preset's channel width against unit range) | Survivors slide from the square-law answer, sqrt(20² − 10²) = 17.3, toward the linear answer, 10, as the engaged width shrinks. A cap is a switch of regime (linear while both sides exceed the cap, square once both are under it), not a smooth exponent | lane preset; the per-tick firing counts already built |
| E2 | Defeat in detail. 20 against 20, the second side arriving in k equal packets with a gap between them | The concentrated side keeps 20 × sqrt(1 − 1/k): 14.1 for two packets, 17.3 for four. The penalty shrinks as the gap closes and vanishes when packets overlap fully | staggered spawn or staggered orders per group |
| E3 | The slope as a trickle. A force climbs a ramp toward a defender at the top; sweep slope length and unit speed | A long slope strings the climbers out, which is E2 with the packet size set by the slope; slow units on long slopes should fare worst. Lanchester adds that the rule fails when the small force is concealed | ramp preset (slopes, R1) |
| E4 | Vision as a dial, not a switch. Sweep the fraction of the low side's units that can see the high side (sensor radius, or a few units placed with sight) | The blind side reaches parity with about 1.41 times the numbers when fully blind, 1.28 at one-tenth information, 1.11 at half, 1.03 at four-fifths (derived from the generalized ambush model's kill-rate figures). In that model the blind side still fires, into an area, at reduced effect; in the lab today a blind unit cannot fire at all, which is where pass 1's cliff comes from | done by the fraction of units with sight; there is no blind fire (Q-008-04) |
| E5 | Staying power. Sweep hits-to-kill (health over damage per shot) with a fixed head start for one side | When hits-to-kill is low, striking first decides the fight and the stronger side can lose; when it is high, the head start washes out. For a duel at equal rates, a head start of one mean kill time raises the win chance from 0.50 to about 0.82 | roster health and damage (R0); a delayed-vision or delayed-order knob for the head start |
| E6 | Guns that bear. A line crossing the head of a column, with firing arcs on | The firing-count ratio equals the ratio of units whose arc bears, and decays as the column turns; the outcome follows that ratio | facing and arcs (R2) |

Two levers the research points at:

- Height as initiative. Air-combat sources value height as the choice of when to engage and as first sight, and note that regaining height costs more time than spending it. A transfer that is quicker going down than up would express that. Westley, 2026-10-01, verbatim: "Let's skip faster descending than to climb. For space battles. But that might be helpful in aerial battles for eras that have ships flying through the air." So it is not built or tested for space eras, the Settled Reach included, where a transfer costs the same both ways; it stays a candidate for an era with units flying through air.
- Scouting as a multiplier. Naval salvo theory puts scouting on the striking side's effectiveness and alertness on the defender's reply. That is the costly seer unit stated as a number to tune. `Q-E12-01` is closed (2026-10-01): a roster unit, costly, with wide cross-layer sight and no attack; the lab tunes its cost and its counter.

On the instrument: pass 1 showed the whole-fight prediction restates the outcome and the opening-window form does not. The theory agrees with the opening-window form: Lanchester's quantity is the number firing at each moment, and the early count is what the conditions of the engagement set, before attrition feeds back into it.

### 6.3 Westley's decisions, 2026-10-01, and what the lab builds next

Ten open choices were put to Westley; his answers, verbatim where they are more than a letter:

- The lever that carries the layer advantage: "I'd like to see what engagement looks like for all 3 of these options, let's build the lab to run simulations with all 3 of these knobs \"turned\"". Not a pick; a comparison (below).
- Blind fire: no. A unit never fires at a target it cannot see (`Q-008-04`).
- Expected winners: set by the principle, not by hand, with this correction: "it's not just opening firing advantage, it's consistent firing advantage (the number that we really care about is number of units firing, if A and B both have the same number of units firing than the engagement ends up even)".
- Pass criterion: three patterns for now (P1, P2, P4); P3 returns with abilities.
- The seer: a roster unit, costly, wide cross-layer sight, no attack (`Q-E12-01` closed).
- Experiment order: E1, E2, then E3.
- Vision: symmetric to start (`Q-005-02` closed); asymmetric stays a candidate if the top layer gets a counter.
- Routing: the shortest route wins, across layers (`Q-001-04` closed; edges `Q-001-05`).
- Walking and flying units: the recommended readings (`Q-004-05` closed).
- Attacking mid-transition: by location. The unit attacks from the layer it is leaving until the cross-over point, then from the layer it is moving to.

**The three lever configurations.** One rule set each, everything else equal, run over the same scenarios so the engagements can be watched side by side (a replay per configuration, not only a table).

| Configuration | Vision across layers | Range across layers | Damage across layers | What should carry the advantage |
|---|---|---|---|---|
| LA: vision only | symmetric 0.50 / 0.20 | same as on the unit's own layer | same | only what terrain, cover height and sensor radius do to who sees whom; in open ground with symmetric vision a layer gives nothing (pass 1, X4) |
| LB: vision and reach | as LA | shorter firing up than firing down | same | who is in reach: the higher side fires first and from further |
| LC: vision, reach and a damage penalty | as LA | as LB | lower firing up than firing down | the above plus a number per shot; pass 1 measured this lever alone at about 10 / sqrt(d) |

The values for "shorter" and "lower" are swept, not fixed here. Scenarios to run under all three: the mirror and high-ground set (X0, X4), a tall-cover scenario where the high side sees over and the low side does not, E1 (choke), E2 (packets), and E3 (the ramp) once slopes are in.

**The instrument, restated.** The quantity is the number of units firing on each side, over the whole engagement, not only its opening. The claim to test: when both sides have the same number firing, the exchange is even; when one side holds more firing consistently, it is winning the exchange by about that ratio (weighted by unit type). Pass 1 showed that a whole-fight winner prediction leaks the ending, so the sustained form should compare rates, not predict the winner from totals: per window of ticks, each side's share of units firing against its share of damage dealt and of losses taken. A window where the firing share and the exchange disagree is a number overriding position. The opening-window predictor stays as the forecast; the windowed exchange is the check on "consistent". One thing for the lab to report and Westley to rule on if it matters: an even exchange is not an even outcome when the totals differ, because the side with more units in reserve outlasts the other, which is his own choke example (holding it "as long as they stay at that choke").

**State and next (2026-10-01, end of pass 3).** Built: the windowed exchange, the three configurations with replays, hard bodies with a sidestep and a slope mouth, shortest-by-time routing, the seer type, E1 and E2 (fixed and re-run), the reserves case. Not yet valid: E3, which needs hard bodies on slopes with lateral lanes (above). Next, in order: (1) slope bodies, then E3 under LA, LB, LC; (2) the scenarios the three patterns still lack, P2 (the concave, a surround) and P4 (a smaller force by position), both with a symmetric approach; (3) re-run the pass 1 vision and damage-by-headcount sweeps on the final build, since those numbers are from the old movement; (4) E4 (vision as a dial, using the seer), then E5 and E6; (5) many-variable sampling and a search for variables whose 0.5 crossing moves or doubles when another changes, run in parallel with one data row per fight; every non-monotonic curve gets a control first, as pass 2 showed an artifact can fake one.

## 7. The lab

`toys/layerlab/` (created when the build starts): standalone C simulation, Python driver (scenarios, sweeps, plots, replay). It reuses csrc's numbers as starting values and none of its code. Spec: `toys/layerlab/SPEC.md`, written before the build. It is built in four rungs, R0 to R3: flat combat and determinism; terrain, vision, transitions and every cross-layer knob; facing, formations and the storm-shaped ability; sweeps, replay and the run log. Every run is small: a handful of seeds and a few values, read at once, then tuned.

Every logged result carries a transfer class. T1: rule geometry that ports to the game as is. T2: magnitudes whose direction transfers while the numbers retune (no economy, no brace, fortify or cohort targeting, symmetric fog). T3: lab-only (steering, coarse pathing, formation drift, pulse trigger heuristic, stalemate window).

A run is logged in §8 with its date, the configuration difference from the previous run, the table, a link to the plot, and what changes next.

## 8. Run log

### Pass 1, 2026-09-30: P1 high ground, then the firing-share check

Scenarios: `toys/layerlab/scenarios/x0_mirror.toml`, `x2_high_ground_blind.toml`, `x3_high_ground_no_return.toml`, `x4_high_ground_both_answer.toml`. All are 10 v 10 identical raiders, both sides attack-moving at each other, A on layer 4 and B on layer 3 (X0: both on 3). Cross-layer fire is on between adjacent layers in both directions at full range and damage in X2 to X4; vision looking down one layer is 0.50. What differs: X2 B looks up with factor 0.0 (cannot see A); X3 B sees A (0.50) and cannot fire up (range and damage up = 0); X4 B sees and fires up equally (the null). Transfer class T2 for the numbers, T1 for the null result.

| Scenario | A wins (100 seeds) | B shots | Note |
|---|---|---|---|
| X0 mirror, same layer | 47 | 269 | noise floor |
| X4 symmetric rules, A a layer up | 43 | 269 | a layer alone gives nothing |
| X2 B cannot see up | 100 | 0 | A keeps 100 percent HP |
| X3 B sees, cannot fire up | 100 | 0 | same |

A first version of X4 had A attack-moving and B holding: A won 60 of 60 even on the same layer, because A's units converge on a stationary line and B's flank units sit out of range. That is a concave effect, not a layer effect, so every layer scenario uses a symmetric approach.

Vision as the lever (A win rate; rows B's upward vision factor, columns B headcount, A = 10, 20 seeds): at 0.0, no headcount helps B (28 v 10 still loses 20 of 20); at 0.05 (about 40 units of sight), 12 units already win 90 percent; the same cliff holds at every higher factor. Damage as the lever (B's fire-up damage multiplier d against B's headcount, everyone sees everyone): B needs 10 (d = 0.98), 12 (0.75), 14 (0.55), 16 (0.44), 18 (0.35), 20 (0.25) units to reach 50 percent, which is the square-law curve `B = 10 / sqrt(d)` of 6.1.

**The firing-share check** (6.1, built as `layerlab/analysis.py`, `python3 -m layerlab check`). Whole-fight predictions, 100 seeds: X2 and X3 both predictors right 100 of 100 (B never fires, as expected); X0 and X4 right 98 and 99 of 100, which is not the toss-up 6.1 expected. Across the damage sweep (20 seeds a cell), count-only and type-weighted are both wrong 0 of 20 in every cell where A wins with fewer units than B (d = 0.2 at B = 12 and 16, d = 0.4 at 12 and 14, d = 0.6 at 12), and both right 20 of 20 where numbers decide. By the 6.1 table that is wrong and wrong: a number other than position overrode it, and the number is the one the sweep varied.

What the check shows about the instrument:
- The whole-fight form partly restates the outcome. It is computed from the finished fight, and the side that wins keeps more units alive and firing, so it agrees 98 percent in a mirror where no side has a positional edge. At d = 0.8 with equal counts (A wins 20 of 20 on damage alone) it agrees 20 of 20, which reads "position decided" when a damage number did.
- A version that looks only at the opening 40 ticks after the first shot cannot leak the ending. It is a coin flip in the mirror and X4 (about 50 of 90 and 48 of 83 decided runs), 0 of 20 in the cells above where fewer units win on damage, and 7 of 15 decided at d = 0.8 with equal counts, which correctly says firing counts did not decide that one.
- So the opening-window form separates "who got shots off" from "a number decided" better than the whole-fight form. Not yet in `analysis.py`.

### Pass 2, 2026-10-01: the range lever, and a finding about target selection

**Superseded by pass 3 (same day).** The inversion described here, and the 98-to-2 size of the focus-fire effect, came mostly from units overlapping in the old movement, not from the nearest-target rule. With hard bodies the longer-range side wins (pass 3). Kept as the record of what the old build showed and how it was diagnosed.

Scenarios `x5_range_advantage.toml` (both sides attack-move) and `x5_range_advantage_hold.toml` (B holds). Same layers or not, the result was the same: **the side with the longer range loses.** Both attack-moving, 200 seeds: A shooting down at 1.1x range wins 11.5 percent (1.0x: 43.5; 1.3x: 9; 2.0x and up: 50). Same layer, no layer rule involved, A range 220 against B 200: A wins 10 percent. With B holding, A wins 200 of 200, and a static start with A in reach and B not has A winning 40 of 40, so the range rule itself is right.

Investigation (with evidence, not guesses): at equal total HP and equal units firing for the first 200 ticks after contact, A is ahead or level and still loses 88 percent. With no approach at all, the inversion survives when the fronts start 195 apart (A reaches many of B's units, B reaches few: A wins 19.5 percent) and vanishes at 150 apart (everyone reaches everyone: 47.5 against a 46.5 baseline). The candidate-set sizes at contact are 4.6 targets per A unit against 2.1 per B unit at 195, and 6.7 against 5.7 at 150. Changing only the target rule decides it: when A focuses the most damaged unit instead of the nearest, A wins 100 percent (and 98.5 percent when both sides focus: the longer range wins, as it should). At equal ranges, one side focusing and the other taking the nearest gives 98 to 2.

Reading: a side with a wide choice of nearest targets spreads its fire and kills slowly; a side with a narrow choice puts all of it on the same few units and kills them first. That is a real consequence of the stated rules (SPEC 5.4, nearest by default), not a coding fault, and it is not visible to the firing-share count, because both sides have the same number of units firing. Two consequences: (1) any lever result with an unequal reach is confounded by who concentrates fire; (2) focus fire is itself a very large lever (98 to 2), which fits the skill-ceiling aim and means "which target a unit picks" is a dimension of the map, not a detail. X2 to X4 and the damage and vision sweeps used equal ranges and are not affected.

Transfer class T1 for the direction (concentration beats spread), T2 for every number.

### Pass 3, 2026-10-01: the decided build (routing, seer, exchange, hard bodies) and the three configurations

Builds merged: shortest route by travel time ending on the ordered layer (E-01 R-001-05, Q-001-05 reading a); the seer type (no attack, wide sight, shared with its side); the windowed exchange in `analysis.py`; **hard bodies**, a sidestep for crowds (SPEC 5.10). 515 tests pass, builds identical. Every earlier number was measured on the old build in which units overlapped freely; the numbers below are from the final build.

**What hard bodies changed (pass 2 corrected).** The mirror (X0) is now 50 of 100, X4 49 of 100. The pass-2 finding that the longer-range side loses is gone: same layer, A range 220 against B 200, both attack-move, nearest target: A wins 72.5 percent (old build 10), at 240 it wins 99, at 300 all. Focus fire against nearest is 68 to 32 (old 98 to 2). The cause was overlap: a side that stands at its longer reach piled its units into the space the other side was walking into, which made firing and kills uneven. So target selection is a real lever but a modest one, not the dominant factor pass 2 reported.

**The three configurations** (high ground, A one layer above B, 10 v 10, both attack-move, nearest-target both, 200 seeds, A win rate; replays in `toys/layerlab/results/replays/`, GIFs not committed):

| Configuration | Setting | High side wins |
|---|---|---|
| LA vision only | none | 0.46 (no layer effect) |
| LB vision and reach | firing up at 0.9x range | 0.76 |
| | 0.8x | 0.985 |
| | 0.5x | 1.00 |
| LC reach and damage | range up 1.0x, damage up 0.9x | 0.785 |
| | range 1.0x, damage 0.8x | 0.96 |
| | range 0.8x, damage 0.8x | 1.00 |

Reach and damage each carry the advantage on their own, and each crosses 0.5 at a small penalty (reach about 0.95x, damage about 0.93x). That is a steep curve: a 20 percent penalty on either is already decisive, so the useful range for tuning is narrow.

**The windowed exchange** (`python3 -m layerlab exchange`). Window by window, the share of units firing and the share of damage agree in most windows (the A 220 v B 200 nearest run: 14 of 17 windows agree, three are even, none disagree); the firing counts in that run are level for about 270 ticks and then drift apart as one side loses units faster. So "equal units firing, uneven outcome" in pass 2 was too strong: over the whole engagement the firing share tracks the outcome, which is the principle. The opening-window prediction in the mirror agrees with the winner 65 percent of the time at a 10-tick window and 77 at 80 (200 seeds); the whole-fight form agrees 92. The earlier "coin flip" for the opening window was also a property of the old movement: with hard bodies the early firing count carries real information, and still cannot see the ending.

**E2, defeat in detail** (20 v 20, B in k packets; both sides advance; spawn positions are computed from the arena width and a layout that does not fit raises an error; 20 seeds). The one-packet baseline is a fair fight (A wins 50 percent, keeps 2.9). Survivors rise with the gap and the number of packets: k = 2 keeps 8.2 at gap 100, 10.2 at gap 900 (theory 14.1); k = 4 keeps 5.0 at gap 100 and 14.7 at gap 900 (theory 17.3), a gain of 11.8 over the baseline. The penalty vanishes as the gap closes and the direction holds; the size stays under the theory because the theory has each packet destroyed before the next arrives, and at 900 units (6 s at speed 150) the fights are not finished.

**E1, choke breadth** (20 attackers v 10 defenders walking in a 1000-long `lane` corridor, both advancing, identical formations, 20 seeds). Survivors of the 20 and the firing ratio A/B:

| Corridor width | range 40 | range 200 |
|---|---|---|
| 1 cell | 11.3 (1.04) | 11.7 (1.09) |
| 2 cells | 12.2 (1.12) | 12.5 (1.15) |
| 4 cells | 13.6 (1.20) | 13.8 (1.26) |
| 8 cells | 14.2 (1.21) | 15.2 (1.40) |

In a one-cell corridor the exchange is even (firing ratio near 1) and the larger side keeps about the difference (10, the linear law); survivors rise with width toward the square law (17.3) without reaching it because the formations are five abreast at most. Range from 40 to 200 barely matters once the corridor is much longer than the range. This is the regime shift the theory describes, and it is also the reserves case in its natural form: an even exchange with unequal totals.

**The reserves case** (Westley's note: an even exchange is not an even outcome when the totals differ). 10 v 10: A wins 19 of 40. A with a second 10 arriving 800 units behind its first 10, against B's 10: A wins 40 of 40 and keeps 15.7. The first windows are an even exchange (firing share 0.485, damage share 0.486, nobody lost); once the reserve reaches the fight the shares tilt (0.64 by tick 460, 0.89 by the end) and the outcome follows the totals. So the lab does what he expected: the exchange is level while the fronts are level and the larger total wins afterwards.

**E3, the ramp** (walkers climb a slope to defenders on the plateau; slope length 150 to 900, speed 40 to 150; defenders at the top or beside the midline; default rules and LA, LB, LC): not interpretable yet, for a reason the lab found. Two harness faults came first and are fixed (the stalemate timer was shorter than a slow walker's approach, and two walkers at the slope entry blocked each other forever: now the slope mouth does not block bodies, SPEC 5.10). With them gone there are no stalemates, and the result is that **attackers win 100 percent with 6 to 8 of 10 left at every slope length, width and speed**, the opposite of the theory (a long slope strings the climbers out and the defenders profit). The trace shows why: units on a slope are neither blocked nor pushed and ride the slope's centre line, so ten attackers stop just above the midline and stack on one point, all ten firing, while the defenders can bring 3 to 5 units to bear. Slope width has no effect at all (identical numbers at 50, 100 and 200). So E3 measures that stacking, not a trickle. The fix is to give units on a slope hard bodies and lateral lanes across its width (a change to SPEC 5.9); until then no E3 number should be read as a result about slopes. Not done; waiting on a go-ahead, because it changes how slopes behave.

Not run: the tall-cover scenario of 6.3, because the cover rule is symmetric (both sight lines pass the same obstacle at the same height) and a high-side-sees-over advantage would be a vision asymmetry, which `Q-005-02` closed as symmetric.

Everything this pass proposed is done in passes 2 and 3 (the opening-window prediction, the range lever, the windowed exchange). Westley's review of this pass goes here.


### Pass 4, 2026-10-01: slope bodies, E3 on the ramp, the pass 1 sweeps again, P2/P4, E4, E5, E6

Builds: units on a slope take a lane across its width (offsets 0, +30, -30, ... within the width), keep it, and queue behind a unit stopped in their lane; slope travel time is unchanged (SPEC 5.9). A slope mouth zone keeps a crowd from deadlocking at the entry. 604 tests pass; a process-pool helper runs thousands of fights in seconds (the proper batch runner with data rows is being built). Fights are run on 8 processes; a pool of 6 ran 3,000 fights in 6 s.

**Pass 1 sweeps on the final build** (the old numbers came from overlapping units). Vision: B's upward sight 0.00 gives A 1.00 whatever B's numbers; 0.05 gives 0.91 at 10 v 10, and B needs 12 units to beat A (11 units: A wins 0.55); at 0.10 it needs 11. The cliff is the same shape, a little softer. Damage: B needs 10 (d = 1.0), 11 to 12 (0.8), 14 (0.6) and 17 (0.4) units to reach 50 percent, close to the square-law 10 / sqrt(d).

**E3, the ramp, with slope bodies** (10 walking attackers climb to 10 defenders; 40 seeds, defenders 300 beyond the top; A = attackers). Now a real trickle: with default rules attackers win 0.79 to 1.00 at slope length 150 and are wiped out (win rate 0.00 to 0.01) from 200 up; the edge is sharp, 0.79 at 150, 0.12 at 175, 0.01 at 200 (200 seeds, speed 80), and does not move with speed (40, 80, 150). With 14 attackers the edge is 0.99 at 150, 0.53 at 175, 0.32 at 200 and about 0.20 from 225 up: a slope longer than about 225 costs the climbers roughly four units and no more. **Crossing candidate**: the slope length where 14 attackers go from certain win to 0.5 (about 175). Not yet controlled (side swap, finer grid, 200+ seeds through the batch runner).

With the defenders beside the midline and cross-layer fire on (LA), attackers win at lengths 300 to 900 (0.93 to 1.00) and lose at 150: a climber below the midline is a layer-1 unit, so under E-01 R-004-06 only layer-1 units can hit it, and it fires up at defenders it can see without return until it crosses the midline. Under LB and LC (reach and damage penalties for firing up) the sign flips again at length 600 and up. This is the first sign that the midline is only a line to hold if the defenders stand out of the climbers' reach: otherwise it is a free-fire zone for the attacker. Not controlled.

**P2 and P4** (concave against a line, both advancing; the line against the line is 0.51 to 0.54 for A, 200 seeds). R = 500: arc 40 gives 0.63, 60 gives 0.87, 100 to 140 gives 0.72 to 0.75, 200 gives 0.89, 240 gives 0.93. The curve in arc angle is non-monotonic (a dip of about 0.15 at 100 to 140 degrees, standard error 0.03), and the control the pass-2 lesson asks for passed: with the sides swapped the concave side wins the same fraction (0.72 against 0.71 at 120, 0.87 against 0.88 at 60), so the dip is geometry, not the harness. Arcs under about 30 degrees put the 10 units closer than a body width and are invalid (a 20 degree arc scored 0.04: an artifact). P4: against a line of 10, a line of 9 wins 0.09, the same 9 in an 80 to 200 degree concave wins 0.07 to 0.14: **the concave is worth less than one unit**; at 10 v 10 it lifts 0.54 to 0.82 to 0.83; at 11 v 10 it takes 0.89 to 1.00.

**E4, the seer** (high side A, 10 raiders on layer 4; low side B, 10 raiders that cannot see up, plus one seer; 200 seeds; A's win rate). Blindness alone is worth about one unit to A (0.92 at 10 v 10 against 0.45 when both see). A seer with cross-layer sight of 750 or more brings A back to 0.56; with 600 or less it does nothing (A 0.93 to 0.97): sight is a threshold lever. Placement matters: a seer 150 behind the line gives 0.56, in front of the line 0.91 (it dies first), 400 behind 0.94 (too far to see). More hit points help B (A 0.60 at 40 hp, 0.34 at 320). One seer costs more than a raider (120 against 90) and buys less than one raider's effect, so as tuned it is not worth its price.

**E5, staying power**: cannot be run. Without spawn jitter a duel is fully deterministic: units that idle before contact have their random attack-timing draw erased, so both sides fire in lockstep and the result is 0 or 1. The theory's probabilities (0.82 for a one-kill-time head start) need per-shot randomness the lab does not have. A lab knob for damage or attack-timing spread (default 0, so nothing changes) would make E5 and the many-variable search richer; not built, not a rule.

**E6, guns that bear** (a line of 10 beside a column of 10 marching past; arcs on). Head on, arcs change nothing (every target is dead ahead and units turn at 6 rad/s). As a broadside with slow turning (0.1 rad/s) the line's win rate goes 0.52 (no arc limit), 0.59 (120 degrees), 0.21 (60), 0.04 (30): arcs decide the fight once turning is slow, and the curve over arc angle is non-monotonic, so it needs the side-swap control before it is a result.

## 9. Verdict and fold

Filled when the pass criterion in §6 is met or shown unreachable. If met: numbers go to `algorithms.md` as ALG rows, S-008 gains rules with values, `Q-008-02` and `Q-008-03` close, and the E-01 gate is re-run. If not met: record what the lab could not show and why, and revise the method; the cross-layer numbers stay open, and Westley decides whether the strategic-depth definition in the hub stands.

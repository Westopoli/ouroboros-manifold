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
- Terrain-forced auto-transition: a move order to a place blocked on the unit's layer but open on another auto-transitions it (E-01 R-001-05). The lab has an off switch for it only because a control needs an off state; the ruling itself is settled. The edges the ruling leaves open are `Q-001-04`; the lab takes the recommended reading there and can vary it.
- A transition is one transition of one duration regardless of distance (Q-002-01), by unit type (Q-004-01: Raider 1.0 s, Interceptor 1.2 s, Vanguard 2.5 s, Warden 2.0 s, Bombard 4.0 s, Bastion 5.0 s). The old layer may attack the unit until the halfway point, the new layer from the halfway point on; visibility follows the normal cross-layer sensor rules (Q-004-02). E-01 R-004-02 carries the same rule.
- Slopes (Q-004-03, Westley 2026-09-30: "Choice 2 set by the slope, no need for a switch."): a slope is a band of ground joining two layers, adjacent or not. On a slope the transition is the unit's position along it, not a timer: the time is slope length divided by unit speed, the halfway point is the slope's midline, and a unit may stop or turn back (E-01 R-001-06, R-004-06 to R-004-08). The timed rule above applies only to a transfer away from a slope. The lab builds this one way, with no timed-versus-slope switch. A unit on a slope counts as on the layer on its side of the midline (Q-004-04).
- Unit movement kinds (Q-004-04, Westley 2026-09-30): flying and swimming units change layer anywhere nothing blocks, by a timed transfer; walking units stand only where a layer has land, change layer only by walking a slope, and never rise in place (E-01 R-001-07).
- A transitioning unit may attack, in a timed transfer or on a slope, while it can see its target, and stops when the transition takes that sight away (E-01 R-004-02).
- What these rulings leave open is `Q-004-05` (which types walk, how the map marks land, cross-overs on a slope spanning several layers, the layer of a unit in a timed transfer, a walking unit given a layer order); the lab takes the recommended reading there and can vary it.
- Vision across layers shrinks with distance: production uses factor 0.50 one layer away, 0.20 two layers away, none beyond, by absolute offset in either direction (`csrc/fog.c:585`); E-01 R-005-05 says two layers below is never visible, which disagrees (`Q-005-02`), so the lab takes vision by signed offset and can test both; vantage nodes and interference zones modify it; cover blocks sight by height and never changes damage or movement (E-01 S-007).
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
| Movement kind (walking, or flying or swimming) | 2 values | none; which types walk is Q-004-05 | R1 | P1, P4 |
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
| Land per layer: where a walking unit can stand | per layer per position | none; how the map marks it is Q-004-05 | R1 | P1, P4 |
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
| Vision factor by signed offset (target minus observer, 9 values) | 0 to 1 each | symmetric: 1.0, 0.50, 0.20, 0, 0 at absolute offset 0 to 4 (`OM_CONE_LAYER_1_FACTOR`, `OM_CONE_LAYER_2_FACTOR`, `csrc/fog.c:585`); E-01 R-005-05 implies 0 for two below (Q-005-02) | R1 | P1 |
| Vantage vision factor by signed offset | 0 to 1 each | 1.0, 1.00, 0.40, 0.20, 0 at absolute offset 0 to 4 (E-01 R-005-06) | R1 | P1 |
| Sensor bonus per layer of elevation | 0 to 0.5 | none per layer: production's 0.15 (`OM_ELEVATION_SENSOR_BONUS_PER_TIER`) is per elevation tier, which is not a layer; lab default 0, so R-005's numbers hold | R1 | P1 |
| Range multiplier by signed offset (target minus attacker, 9 values) | 0 to 2 | none; same-layer only (Q-008-01) | R1 | P1 |
| Damage multiplier by signed offset | 0 to 2 | none | R1 | P1, P4 |
| Area-damage multiplier by signed offset | 0 to 2 | none | R1 | P2, P3 |
| Fire requires vision | on or off | none decided; E-01 R-007-03 lets a hidden attacker hit an observer that cannot see it, so the flag is about the attacker's own sight; the lab uses one visibility function for target choice and for the fire check | R1 | P1 |
| Facing gates fire | on or off | none | R2 | P2 |
| Halfway rule during a transition | both always targetable, per rule (old layer until halfway, new layer after), untargetable | per rule (Q-004-02); on a slope the halfway point is the midline, by position (Q-004-03) | R1 | P1, P4 |
| Terrain-forced auto-transition | on or off (off is the control) | on (E-01 R-001-05); edges per Q-001-04 | R1 | P4 |
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

Pass criterion for the lab, proposed here for Westley to confirm or change (he owns it): one shared cross-layer rule set under which all four patterns of §4 hold (each true in at least one reachable configuration, none true in every configuration), with at least one crossing on a layer-rule axis and at least one two-variable interaction that adds a crossing. A separate tuned rule set per pattern does not pass.

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
| E4 | Vision as a dial, not a switch. Sweep the fraction of the low side's units that can see the high side (sensor radius, or a few units placed with sight) | The blind side reaches parity with about 1.41 times the numbers when fully blind, 1.28 at one-tenth information, 1.11 at half, 1.03 at four-fifths (derived from the generalized ambush model's kill-rate figures). In that model the blind side still fires, into an area, at reduced effect; in the lab today a blind unit cannot fire at all, which is where pass 1's cliff comes from | no new rule if done by fraction of units with sight; a blind-fire rule (firing at a last-known position at reduced effect) would be a new mechanic and needs Westley's go-ahead |
| E5 | Staying power. Sweep hits-to-kill (health over damage per shot) with a fixed head start for one side | When hits-to-kill is low, striking first decides the fight and the stronger side can lose; when it is high, the head start washes out. For a duel at equal rates, a head start of one mean kill time raises the win chance from 0.50 to about 0.82 | roster health and damage (R0); a delayed-vision or delayed-order knob for the head start |
| E6 | Guns that bear. A line crossing the head of a column, with firing arcs on | The firing-count ratio equals the ratio of units whose arc bears, and decays as the column turns; the outcome follows that ratio | facing and arcs (R2) |

Two levers the research points at:

- Height as initiative. Air-combat sources value height as the choice of when to engage and as first sight, and note that regaining height costs more time than spending it. A transfer that is quicker going down than up would express that. Westley, 2026-10-01, verbatim: "Let's skip faster descending than to climb. For space battles. But that might be helpful in aerial battles for eras that have ships flying through the air." So it is not built or tested for space eras, the Settled Reach included, where a transfer costs the same both ways; it stays a candidate for an era with units flying through air.
- Scouting as a multiplier. Naval salvo theory puts scouting on the striking side's effectiveness and alertness on the defender's reply. That is the costly seer unit (`Q-E12-01`) stated as a number to tune.

On the instrument: pass 1 showed the whole-fight prediction restates the outcome and the opening-window form does not. The theory agrees with the opening-window form: Lanchester's quantity is the number firing at each moment, and the early count is what the conditions of the engagement set, before attrition feeds back into it.

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

What changes next: add the opening-window prediction to `analysis.py` with its own tests; sweep the range-by-offset lever (the other way a layer can decide who gets shots off) and compare it with damage by the firing-share measure; then P2 (the concave) with the lever fixed. Westley's review of this pass goes here.


## 9. Verdict and fold

Filled when the pass criterion in §6 is met or shown unreachable. If met: numbers go to `algorithms.md` as ALG rows, S-008 gains rules with values, `Q-008-02` and `Q-008-03` close, and the E-01 gate is re-run. If not met: record what the lab could not show and why, and revise the method; the cross-layer numbers stay open, and Westley decides whether the strategic-depth definition in the hub stands.

# E-22 — Economy and Bases

## Definition-completeness gate (run 2026-10-02)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Partly. 16 stories, 83 rules. Where Westley decided a mechanism the rule states it. Where he decided no number or name the rule carries a flag in place of the value. |
| Every input listed with range and rejection behavior | No. See Inputs; ranges wait on the flags. |
| Every output listed with where it is observable | Yes, see Outputs. |
| Implied-but-unstated behavior turned into flags | 40 new flags, Q-167-01 to Q-181-02 (including Q-177-05), and 6 carried (Q-159-07 to Q-159-10, Q-159-12, Q-159-13). |
| Every visible-surface story has a reference | Not yet; see Look and behavior references. |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed.** Blocked on the open flags. Every story below is design decided by Westley on 2026-10-01 and 2026-10-02 (`docs/northstar/research/economy_design/`, his words verbatim in its README, and `docs/legacy/research/epics_audit_2026-10-02/DECISIONS.md`) and is not scheduled for building. An epic with an open flag is not built.

## Purpose

A real economy sits behind every battle. Every side has a base of operations it must protect, with literal workers, three resources, buildings, one population cap, production, technology, expansions, defenses and shipments. The economy is the same in every match. In the core single-commander game rules run it for the player and run it well, and the base is a spectacle that builds itself while the fight goes on. In the optional paired mode of E-19 S-159 a second player runs it, and the two players have to talk. The commander never administers the economy: alone, he has one dial for the balance between economy, technology and army, can change the doctrine the rules follow, and asks for things by pointing at the map.

The skill the economy asks of a human is holding several things in mind at once. Forgetting one (the population cap, worker production, the next technology, production) puts a side behind, and nothing on screen lists what is needed. The target is two to three times the system complexity of a proficient StarCraft 2 economy (E-19 S-159).

The two starting eras, one in space and one on land, share units and rules. Their landscape and visuals differ. Rules about ground, height bands, slopes, walking units and strongpoints are written for land maps. The space-era landscape is not designed and no story is written for it (Q-166-02).

Long-term direction: thousands of units and workers on one map (hub "Reference Hardware"). This is a direction, not a budget.

Strongpoints and moving weather are rules of E-15. Terrain, height bands, settlements and where economic locations are placed are rules of E-17. Mission setup is E-10, enemy behaviour is E-14, screens are E-16, and the paired mode itself is E-19 S-159.

## Obviously working in 60 seconds

Start a mission with nobody in the economy seat. At the base, buildings stand under construction and rise. Workers walk to a source, return to a drop-off, and bring in less when the walk is longer. Units appear at production buildings and walk to the fight. The population never stops at the cap and no worker stands idle. Point at a pass and say fortify, and the ticker says what will be built and when. Take the base's production away from the enemy: the enemy keeps fighting from an expansion, and the best result left to the side that lost its original main base is partial failure. A shipment sent to a base never shows on the map, and when it does not arrive nobody says why.

## Stories

### S-167 — Resources and workers

As a commander, I want literal workers who walk to a source and bring back one of three resources, so that the base is a place with people in it that I can protect or lose.

Rules
- R-167-01  Given a side's economy, When it gathers, Then there are three resources, each gathered in its own way, on the model of classic Age of Empires Online and Age of Empires 3: two common ones that together are about 75 percent of what lies on the map, and one rare one, about 25 percent, that technology draws on most (Westley, 2026-10-06); the names are Food, Wood and Coin in the ground era and Metal, Water and Uranium in the space era (Westley, 2026-10-07) ; the rare one is Coin in the ground era and Uranium in the space era (Westley, 2026-10-07) (closed 2026-10-21, Q-159-08: each role costs two of the three resources in a fixed pattern; amounts stay placeholders).
- R-167-02  Given a base, When a worker is trained, Then it appears at the base as a literal unit, walks to a source, gathers, and walks back to a drop-off, visible to the enemy and able to be killed (closed 2026-10-21, Q-167-01: a named draft, Westley tunes it by feel).
- R-167-03  Given economic buildings, When the base is built, Then they include drop-off points, and Given a worker with a load, When it walks to a drop-off, Then the farther it walked the less it brings in (closed 2026-10-21, Q-167-02: a named draft, Westley tunes it by feel).
- R-167-04  Given a worker, When units are counted, Then it counts against the one population cap (E-22 S-169) and in the unit budgets, and it cannot fight: it never acquires a target, never returns fire, and flinches from damage (E-15 R-129-01); for the beta workers are not part of the roster of E-11 S-082 and post-beta will decide (Westley, 2026-10-07).

- R-167-05  Given the sources of a base, When a side gathers, Then natural sources are fast and finite and built sources are slow and permanent and take lots, so the timing of the switch from foraging to farming is a skill (Westley, 2026-10-07).

Inputs: the base; sources (E-22 S-177); the era's resources.
Outputs: resource counts per side; worker positions in the tick delta.
Open flags: none. Q-159-08, Q-167-01 and Q-167-02 closed 2026-10-21 (register; named drafts). Unpicked pieces that touch this story, listed under Open ambiguity flags: workers under raid.

### S-168 — Building and placement

As an economy player, I want to place buildings where I choose and see the city reshape around them, so that where I build is a decision with consequences.

Rules
- R-168-01  Given a paired economy player, When he places a building, Then it claims its footprint and the self-built pieces around it are cleared and refilled, so the city reshapes around what he placed (E-17 R-166-03); buildings in a settlement share the contour orientation of their ground with a jitter of DRAFT-building-yaw-jitter 0.05 rad (DEC-S005-building-yaw, Westley 2026-10-22: some uniformity, we're emulating reality).
- R-168-02  Given a base, When lots are counted, Then no count of lots limits the buildings, and only terrain limits where one may stand, as in E-17 R-166-01 (Westley, 2026-10-06); the engine's lot table is finite (OM_LOT_CAP, 2048 today, 8192 after P3); the bound is a memory limit, never a design limit, and no mission reaches it (Architect 2026-10-21, implementation; Westley may veto). Direction for later, not for the beta: a very large base may be upgraded past its maximum into another tech level; there is no maximum in the beta, only terrain limits (Westley, 2026-10-07).
- R-168-03  Given a building, When what stands beside it changes, Then what it yields changes; for the beta the effects are placeholders, and their kinds, size and range are set later in the lab (Westley, 2026-10-06).
- R-168-04  Given a building is placed, When work begins, Then it stands under construction and rises in stages until it is finished (closed 2026-10-21, Q-168-03: a named draft, Westley tunes it by feel).
- R-168-05  Given an era, When its buildings are listed, Then they include drop-off points, housing, production buildings (E-22 S-170) and defenses (E-22 S-174); the set is small and fixed per era pack (E-20 R-146-01) and its names are era pack content, and the pack manifest field that lists them is named "buildings", as the validator requires (Westley, 2026-10-06; field name, Architect 2026-10-10).

Inputs: placement commands from the economy player; the terrain (E-17); the era's building set.
Outputs: buildings with owner, footprint, stage and yield in the tick delta.
Open flags: none. Q-168-03 closed 2026-10-21 (register; named draft). Unpicked: deeper districts, the Keystone. With nobody in the seat the rules place buildings (E-22 S-179) and a solo commander never does (E-22 S-180).

### S-169 — One population cap

As a commander, I want one cap shared by workers and soldiers that can be raised a very long way, so that every worker is a soldier I do not have and a long game can grow into thousands.

Rules
- R-169-01  Given a side, When its units are counted, Then workers and soldiers count against one population cap.
- R-169-02  Given a unit, When it counts against the cap, Then it counts by its population weight (closed 2026-10-21, Q-169-01: a named draft, Westley tunes it by feel).
- R-169-03  Given a side at its cap, When another unit is queued, Then it cannot be trained until the cap rises or the count falls.
- R-169-04  Given housing is finished or a cap upgrade is bought, When the cap is read, Then it has risen, a long way, up to thousands.

Inputs: units; housing; cap upgrades.
Outputs: population and cap per side.
Open flags: none. Q-169-01 closed 2026-10-21 (register; named draft). Unpicked: upkeep bands.

### S-170 — Production and the schedule

As an economy player, I want to run the production buildings and plan what they make ahead of time, so that the commander receives the units his fight needs and I have to think about what he will need a few minutes from now.

Rules
- R-170-01  Given a production building, When it finishes a unit, Then the unit is one the commander receives, standing at that building.
- R-170-02  Given the paired mode, When the commander wants a kind of unit, Then he asks the economy player by talking, and nothing on screen lists what the commander needs.
- R-170-03  Given a production building, When it is set up, Then it is focused on one family at a time, Strike, Line or Siege (E-22 S-171).
- R-170-04  Given a building focused on one family, When it is changed to another, Then the change takes a while (closed 2026-10-21, Q-170-01: a named draft, Westley tunes it by feel).
- R-170-05  Given the economy player, When he plans production, Then it is laid out ahead on a timeline for each production building (closed 2026-10-21, Q-170-02: a named draft, Westley tunes it by feel).
- R-170-06  Given a unit is queued, When it is made, Then it costs resources by its role (R-171-03) and takes time (closed 2026-10-21, Q-170-03: a named draft, Westley tunes it by feel).

Inputs: the economy player's production and schedule commands; resources; the cap.
Outputs: units in the tick delta; each building's focus and timeline.
Open flags: none. Q-159-08, Q-170-01, Q-170-02 and Q-170-03 closed 2026-10-21 (register; named drafts). What a seen building shows the enemy is E-22 S-172. A return-to-base ability is unpicked.

### S-171 — Counters

As a commander, I want the three families to counter each other and each role to need its own resources, so that what a side gathers and builds tells the other side what it must bring.

Rules
- R-171-01  Given a unit, When it is classed for counters, Then its family is its category: Strike, Line or Siege (E-11 S-081).
- R-171-02  Given two families in a fight, When damage is dealt, Then they counter each other by the triangle of E-11 S-081: Strike flanks Siege, Siege crushes Line, Line absorbs Strike.
- R-171-03  Given a unit role, When it is trained, Then it costs two of the three resources in a fixed pattern (Westley, 2026-10-06): Strike and Line roles cost the two common resources, and each Siege role costs the rare one plus one common one, not the same common one for every Siege role (closed 2026-10-21, Q-159-08: each role costs two of the three resources in a fixed pattern; amounts stay placeholders; the roles inside a category are Q-082-03, still open).
- R-171-04  Given a side gathers heavily from one resource, When the other side sees it, Then it shows which role the first side is making more of, and the other side needs the counter; what shows it is workers seen at the sources through the fog (Westley, 2026-10-07), and how heavy counts as heavy is a placeholder for the lab.

Inputs: unit category and role; resource costs.
Outputs: none of its own. The effect is the damage of E-11 S-081 and the fog-limited picture of E-12.
Open flags: none. Q-159-08 closed 2026-10-21 (register). The roles inside a category are E-11 Q-082-03.

### S-172 — Disguise

As an economy player, I want to hide what my production is doing, so that the enemy cannot read my next push from the buildings he can see.

Rules
- R-172-01  Given an enemy sees a production building, When he looks, Then he can see its focus family, Strike, Line or Siege, which is also what it is doing since production buildings are split by family (Westley, 2026-10-07); what a building shows from a distance unseen waits on the parked disguise question Q-159-09.
- R-172-02  Given a player wants to hide a building, When he uses the way the game gives, Then the building is disguised or hidden [Q-159-09: how disguising or hiding works and what it costs].
- R-172-03  Given the rules run an economy, When they decide what to build, Then they disguise nothing, unless the difficulty has the enemy's economy disguise (E-22 S-181).

Inputs: the enemy's sight (E-12); the disguise command.
Outputs: what a side can read of an enemy building.
Open flags: Q-159-09 (parked). Unpicked: worker scouting. How structures appear in fog is E-12.

### S-173 — Technology

As an economy player, I want to choose the technology my side goes for, so that the commander fights with the units I decided to unlock.

Rules
- R-173-01  Given the paired mode, When a technology is chosen, Then the choice belongs to the economy player.
- R-173-02  Given a mission is set up, When its starting technology is set, Then it is derived from the simulation's technology level, only slightly [Q-173-01: the formula, and how slight].
- R-173-03  Given an era, When its technology levels are counted, Then there is a wide range of levels, for example 1 to 5, and in a normal timed single match a side has the time to go up one or two levels, as in the tech-up of StarCraft 2 [Q-173-02: the range per era, and the resource cost and time per level that give one or two levels in a normal match].
- R-173-04  Given a technology level, When it is reached, Then it does [Q-159-12: what technology does, including whether a level reached in a running mission changes the tier of units already fielded, which E-06 R-048-02 fixes today].
- R-173-05  Given spending, When resources are used, Then technology competes with economy and army (E-22 S-177), and with nobody in the seat the rules spend on technology by the dial and the doctrine and never counter-pick it (E-22 S-179, E-22 S-180).

Inputs: the simulation's technology level (E-06); the economy player's choices.
Outputs: a side's technology level in the tick delta.
Open flags: Q-159-12, Q-173-01 and Q-173-02 (parked, post-beta). Unpicked: ages by landmark, the Contested Tree.

### S-174 — Defenses and raid lanes

As an economy player, I want to build walls, gates and towers where raids will come, so that my workers and shipments reach the base.

This story is written for land maps. Space eras wait on a space reading of this story; the space landscape is E-17 S-246.

Rules
- R-174-01  Given a paired economy player, When he builds defenses, Then they are walls, gates and towers.
- R-174-02  Given the terrain, When raiders go for workers or shipments, Then they come along lanes the terrain sets, for both sides; the lanes are an output of the map generator (E-17; Westley, 2026-10-06) [Q-174-01 closed; how a side sees its own and the enemy's lanes is E-16].
- R-174-03  Given the lanes, When the economy player places defenses, Then he covers his own lanes, and he reads the enemy's lanes to tell the commander where a raid would hurt.
- R-174-04  Given a wall, a gate or a tower, When it stands, Then it does (closed 2026-10-21, Q-174-02: a named draft, Westley tunes it by feel).
- R-174-05  Given a wall or gate is placed or destroyed, When units route, Then the cells that block movement have changed for every route (E-13 S-097).

Inputs: placement commands; the terrain.
Outputs: defenses in the tick delta; raid events.
Open flags: none. Q-174-02 closed 2026-10-21 (register; named draft). Unpicked: workers under raid. With nobody in the seat the rules wall a lane only when the commander asks (E-22 S-180).

### S-175 — Expansions and forward works

As an economy player, I want to grow a settlement into a further base and to build production near the front, so that my side out-produces the side that stays home.

Rules
- R-175-01  Given a settlement on the map, When a side holds it uncontested for a length of time (Westley, 2026-10-06; for now), Then it grows into a further base with its own main building, worker production and lots.
- R-175-02  Given a main base, When the mission runs, Then its sources never run dry but yield less over time, so a side that stays home and does not expand outward is out-produced and overrun; the resources of an expansion are quick to collect and fizzle out quickly (Westley, 2026-10-06; the rates are for the lab).
- R-175-03  Given the economy player, When he builds production near the front or at an expansion, Then it is forward works, where units reinforce fast and which are exposed, and where they stand shows where the next push comes from; forward works can be production only, or also houses and workers if the side wants them, in the manner of Age of Empires 3, and the commander can flag "forward base here" to the economy player (Westley, 2026-10-06; cost and build time are Q-168-03).
- R-175-05  Given trade caravans (Westley, 2026-10-07: in, and distinct from shipments), When they run, Then they walk visibly between a base and settlements, longer routes pay more and are easier to raid; the rules send them in solo play and the economy player in paired mode (Westley, 2026-10-07).
- R-175-04  Given a unit is made at forward works, When it is finished, Then it stands there and walks to the fight, so the walk is longer from a base kept home.

Inputs: settlements (E-17); the economy player's build commands.
Outputs: bases and forward works in the tick delta.
Open flags: none. Unpicked: trading posts at neutral settlements. What a side does when its base of operations falls is E-22 S-178. The attacker's forward base, which is its base of operations, is E-22 S-177 (supply lines are not an attacker-only rule, Westley, 2026-10-07). Forward works are not a forward base.

### S-176 — Shipments

As an economy player, I want shipments from the civilization and from my own forward posts that cross the map as visible objects with no sight of their own, so that waiting for one is a risk I plan around.

This story is written for land maps. Space eras wait on a space reading of this story; the space landscape is E-17 S-246.

Rules
- R-176-01  Given a mission, When time passes, Then the civilization sends shipments to the base, and a side that holds a forward base or economic post away from its main city may also choose to send a shipment of resources to the main base, the farther the post is from the main city the better the resources it carries; in solo play the rules send them automatically; the amounts are for playtest and balance (Westley, 2026-10-06).
- R-176-02  Given a shipment on its way, When the receiving side looks, Then it sees it on the map like any unit, as the enemy does (it is visible to both sides), but the shipment gives its own side no vision (Westley, 2026-10-06).
- R-176-03  Given a shipment that is killed on the way, When it does not arrive, Then the side gets no ticker line that it was killed and no explanation, since it has "no idea what happened".
- R-176-04  Given a shipment on its way, When raiders hold its lane (E-22 S-174), Then it can be stopped.
- R-176-05  Given a shipment, When it is sent, Then it looks like a unit on the map but behaves like an event: it has no vision of its own and cannot be moved or given orders once it is sent (Westley, 2026-10-06).

Inputs: the civilization's state (E-02, E-06); lanes.
Outputs: arrivals at the base; a shipment in transit shows on the map to both sides. No output tells a side that one was killed.
Open flags: none. Unpicked: demands from the civilization, the shared market, and a deck of shipments as a candidate of Q-159-07.

### S-177 — Bases, resources and the situation

As a commander, I want a base I must protect, set on a map where the rich resources lie away from the objective, so that every mission is a choice about where to be strong.

Rules
- R-177-01  Given a mission, When the sides are set up, Then every side has a base of operations it must protect, which is not always a city, and which receives resources from elsewhere, generates them on site, or both, depending on the simulation and the mission.
- R-177-02  Given the mission archetype (E-10 S-073), When bases are given, Then the player's base of operations is a grown town only where the archetype gives the player a home or a defended settlement; an attacking archetype has a forward base, a camp and not a town (Westley, 2026-10-13: "depends on the archetype, an attacker can't have a full town since they're attacking, they have a forward base"). The kind of base each side gets is decided by the archetype table below alone (Westley, 2026-10-06).

| Archetype | Player's base | Enemy's base |
|---|---|---|
| Defensive Stand, Multi-Front Defense | home city, generating on site | forward base, supplied from elsewhere |
| Siege Breaking | relief camp outside, supplied, with the city inside as the objective | siege camp |
| Assault, Reconquest | forward base, supplied | the city or fortress being taken |
| Containment, Interception | field camp on the enemy's path | column or staging camp |
| Suppression, Counterinsurgency | garrison in a city | hidden cells among the settlements |
| Rear Guard / Evacuation | the place being left | pursuing forward base |

- R-177-03  Removed 2026-10-06 (Westley): the kind of base does not change with how far into foreign ground the mission lies, and no base lives on shipments by distance.
- R-177-04  Given a map, When economic locations are placed, Then they are spread throughout the map, and each side is at the same distance from the objective and from each significant resource whatever shape the map takes (E-17 R-191-04), so a side picks one or fights for both.
- R-177-05  Given a mission, When base, objective and significant resources are placed, Then they are usually three separate places, not always.
- R-177-06  Given the simulation's situation, When a mission is set up, Then resources are sometimes limited and sometimes abundant, consistent with that situation and slanted by it so that a defender has the better position, and the player always has the means to accomplish the mission even when it is hard; richness is derived from the simulation's existing region fields and composites (E-02), so a region with a big economy gives a mission big resources (Westley, 2026-10-06).
- R-177-07  Given the resources, When the mission is scored, Then they are not scored separately, and a side that ignores them is overrun unless it rushes and finishes fast.
- R-177-08  Given a side's spending, When it spends, Then it is balanced between economy, technology and army, as in StarCraft 2.
- R-177-09  Given settlements on the map, When a neutral populace lives in them, Then it is contested, and winning it is not the economy player's job; winning it gives a strategic position, a new place for production buildings and, most of all, economic assistance, and the neutral villagers become part of the winning team; it is not an instant win, it needs a hold timer, and it can be lost again (Westley, 2026-10-06) (closed 2026-10-06, Q-177-06: the same event as R-175-01, one timer).
- R-177-10  Given a paired match of 4 to 6 players, When it is set up, Then there are more resources and more enemies and a bigger map (E-17), and each pair is its own sub-civilization inside the over-arching civilization; pairs on a team share shipments and technology (Westley, 2026-10-06); how much more a big match has is a placeholder.

Inputs: mission archetype (E-10); the region's situation (E-02); the map (E-17).
Outputs: each side's base kind and place; economic locations and significant resources on the map.
Open flags: none. The strongpoints on the slopes between height bands (E-15) and a base that spans several layers (E-17 R-166-02) are written for land maps (Q-166-02 for space). The five outcomes are E-10 S-077.

### S-178 — When a base falls

As a commander, I want a fallen base to be occupied and not destroyed, so that a lost position can be taken back and a side with ground left can fight on.

Rules
- R-178-01  Given a base of operations, When an enemy takes it, Then it is occupied, not destroyed, and the side that takes it gets its production and its people.
- R-178-02  Given a base, When it is counted as occupied, Then enemy forces hold its central zone for a time and its main building is destroyed or captured, as the archetype sets (Westley, 2026-10-06); the taker may have to rebuild the building to take the location.
- R-178-03  Given an occupied base, When the mission runs, Then the side that lost it can take it back, a base can change hands more than once, and the region follows whoever holds it at the end: the side that takes the enemy's base gets that region (Westley, 2026-10-06).
- R-178-04  Given a side holds an expansion or forward works, When its base of operations falls, Then it falls back to that one as its base of operations at no cost beyond the position; a side that loses an expansion loses the income it produced and its position (Westley, 2026-10-06).
- R-178-05  Given a side has no expansion and no forward works, When its base of operations falls, Then the mission ends for that side and is scored (Westley, 2026-10-06; to be checked archetype by archetype against E-10 R-075-07 and S-077).
- R-178-06  Given a side's original main base, When it is named, Then it is the base of operations the side was given at the start of the mission, and for an attacker it is the forward base from which it produces. Expansions and forward works built later are never an original main base.
- R-178-07  Given the player's side has lost its original main base, When the mission is scored, Then the best result it can reach is partial failure (E-10 S-077), and retaking the original main base lifts that limit (Westley, 2026-10-06).

Inputs: base ownership and occupation; the mission archetype.
Outputs: base owner and kind in the tick delta; the result band's ceiling to E-10; the region's owner at the mission's end.
Open flags: none.

### S-179 — The economy without a player

As a commander, I want the same economy to run itself well when nobody holds the seat, so that the base is alive and grows while I fight.

Rules
- R-179-01  Given any match, When nobody holds the economy seat, Then rules run the economy, run it well, need no intelligent agent, and call no model at play time.
- R-179-02  Given a base in any mode, When the mission runs, Then buildings start under construction and rise, expansions are made, and population density changes over time (E-17 S-166).
- R-179-03  Given nobody in the seat, When the rules run the economy, Then they follow a named doctrine, from the list boom, fortify, press and balanced, the player sets the first one in the lobby, and the player can change the doctrine on the fly to adapt to what the enemy is doing; the pack manifest field that lists the doctrines is named "doctrines", as the validator requires (Westley, 2026-10-06; field name, Architect 2026-10-10).
- R-179-04  Given a doctrine, When it is read, Then it is a build order with its own weights on a checklist of standing habits (closed 2026-10-21, Q-179-02: a named draft, Westley tunes it by feel).
- R-179-05  Given the rules run an economy, When it runs, Then they have perfect hands: they never idle a worker, never hit the population cap and never leave resources unspent.
- R-179-06  Given the rules run an economy, When it runs, Then they have no foresight: they do not scout, do not read the enemy, do not counter-pick technology and do not disguise anything. The one exception is that they counter what the commander's forces have seen, by the unit counter shift of E-22 S-180.

Inputs: the economy's state; the doctrine; the dial and requests of E-22 S-180.
Outputs: the economy's commands, which are the same kind a human economy player's are; ticker lines.
Open flags: none. Q-179-02 closed 2026-10-21 (register; named draft).

### S-180 — The commander alone

As a solo commander, I want one dial and the ability to ask by pointing, so that I steer the economy without running it.

Rules
- R-180-01  Given a solo commander, When he sets the dial, Then the rules carry out the balance he chose between economy, technology and army [Q-180-01: the form of the dial and how much it moves spending].
- R-180-02  Given a solo commander, When he sets the dial, Then he may also name the unit family he wants more of, Strike, Line or Siege.
- R-180-03  Given a solo commander marks the map, When he asks as he would ask a partner, the requests at launch are the three examples, expand here, fortify this pass and I need siege at this gate (Westley, 2026-10-06), Then the rules answer and say in the ticker what they will do and when, with no menu and no queue.
- R-180-04  Given a solo commander, When the economy runs, Then he places and queues nothing himself.
- R-180-05  Given production is run by the rules, When units are chosen, Then the rules make the mix the doctrine calls for (Westley, 2026-10-06; the mix per doctrine goes with Q-179-02), and the commander can change the choice of any building.
- R-180-06  Given the commander's forces have seen enemy units, When production is chosen, Then the rules shift production toward what counters them, using only what the fog has revealed to that side (E-12). This is the one exception to the rules having no foresight (E-22 S-179).
- R-180-07  Given the commander, When he turns the unit-mix behaviour off, the counter behaviour off, or both, Then the rules stop that behaviour; the switches can be changed at any time during a mission (Westley, 2026-10-06), and when the mix behaviour is off the commander picks at the building.

Inputs: the dial; pointing requests; override choices; the two switches.
Outputs: ticker lines; the economy's commands. The requests are a second channel beside the five commands of E-13.
Open flags: Q-180-01. Screens for these are E-16.

### S-181 — The enemy's economy

As a commander, I want the enemy's economy to run on the same rules as mine, so that the enemy is bound by the same economy I am.

Rules
- R-181-01  Given an enemy, When its economy runs, Then it runs on the same rules as the solo player's.
- R-181-02  Given the difficulty, When the enemy is set up, Then its prosperity scales with it (E-14 S-125).
- R-181-03  Given the difficulty, When the match is set up, Then the difficulty decides whether the enemy's economy also scouts, counters and disguises; it is not the player's choice (Westley, 2026-10-07).
- R-181-04  Given the enemy's economy scouts or counters, When it reads the player's side, Then it reads only what that side's fog has revealed, as E-14 R-125-02 says of the macro layer (Westley, 2026-10-07).
- R-181-05  Given a human economy player drops out of a mission, When the seat is empty, Then the same rules take his seat (E-19 S-159 holds the paired mode's drop-out).

Inputs: difficulty; the player's choice.
Outputs: the enemy's economy state and commands.
Open flags: none. The enemy's macro behaviour around its bases, expansions and raids on workers and shipments is E-14.

### S-182 — What carries forward

As a pair of players, I want to take something from one mission into the next, so that a campaign builds up without making the fifteenth mission a lopsided one.

Rules
- R-182-01  Given a time jump between two missions, When the next mission is set up, Then the economy is not assumed to persist through it, and nothing carries forward in the beta; abilities, unlocks or a deck of shipments are a post-beta idea (Westley, 2026-10-07).
- R-182-02  Given a mission the simulation picks on a poor planet with a small force, When the pair brings what it carried forward, Then the result is consistent with a small mission on very limited resources and not a "crazy good economy on the 15th mission together".
- R-182-03  Given a base took damage in a mission, When a time jump follows, Then [Q-159-13: whether the damage persists and how fast it is rebuilt, which depends on the situation and is simulation work].
- R-182-04  Given anything is carried forward, When the campaign is saved, Then it is in the save, written identically on every peer (E-19 R-144-03), and enters the checksum.

Inputs: the end of a mission; the time jump (E-08).
Outputs: what the next mission starts with.
Open flags: Q-159-13 (to be designed with the simulation). What the mission leaves in the region is E-10 and E-02.

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Seed | Campaign | integer | |
| Region state and situation | E-02 | fields and composites; the richness and slant of R-177-06 | |
| Mission archetype | E-10 | 10 archetypes | unknown fails |
| Starting technology level | E-06 | | [Q-173-01] |
| Economy player commands (place, schedule, focus, technology, defenses) | E-19 peers | tick-stamped | wrong tick, unknown peer, malformed: dropped and logged (E-19). The command set is E-19's to fix. |
| Dial, doctrine, pointing request, overrides | Solo commander | | [Q-180-01] |
| Settings: unit-mix behaviour, counter behaviour | Player | on or off | |
| Enemy foresight (scout, counter, disguise) | Difficulty | on or off per behaviour | |
| Difficulty | Player | E-14 | |
| Terrain, lots, lanes | E-17 | | |

## Outputs

| Output | Observable where |
|---|---|
| Resources, population, cap per side | Tick delta; economy screen (E-16) |
| Workers, buildings, units, shipments' arrivals | Tick delta; screen |
| Base of operations owner and kind | Tick delta; result ceiling to E-10 |
| Ticker lines for requests and the economy | Screen |
| What carries forward | Save file; T1 trace |

## Invariants

- The population never exceeds the cap.
- A side never sees a shipment on its way, and is never told why one did not arrive.
- A base of operations is occupied, never destroyed.
- The player always has the means to accomplish the mission.
- With nobody in the seat the rules never idle a worker, hit the cap or leave resources unspent.
- The rules read only what the fog has revealed to their side when they counter units (E-22 S-180).
- No economy rule calls a model at play time. Same seed and same commands give a byte-identical trace on every platform.
- The two starting eras share units and rules, and differ in landscape and visuals.

## Scale requirements

None confirmed for the economy. The direction is thousands of units and workers on one map (hub "Reference Hardware"), reached by an efficient simulation and efficient visuals. The scale requirements of E-11 and E-13 stay as written until Westley changes them, and workers count in the unit budgets they set (E-22 S-167). Westley owns every number.

## Look and behavior references

`references/E-22/notes.md`, missing. Named by Westley: classic Age of Empires Online and Age of Empires 3 for the economy, StarCraft 2 for the population cap, worker production, technology timing and the balance of spending. How the economy is drawn is E-18 and how it is shown is E-16.

## Ways this could be wrong

- The three resources and which role needs which are undecided, so no cost or counter can be tested.
- Workers counted as live units push the tick rate down (E-13 R-099-03) before the economy has any scale.
- A shipment that is a unit would be visible under E-12 R-089-05 and break its blindness.
- The rules' habits (E-22 S-179) and the counter shift (E-22 S-180) read as foresight and break "no foresight" if the fog is not kept apart for the economy.
- A fall-back at a cost, with no number, can make losing a base either trivial or final.
- Forward works counted as a forward base, so losing them caps the result at partial failure.
- Technology that does nothing leaves the spending balance with only two real choices.
- Carry-forward that grows without a bound makes a late mission lopsided.
- The slant for defenders, once the numbers exist, makes an attacker's mission unwinnable.

## Open ambiguity flags

Carried: Q-159-09, Q-159-12, Q-159-13.

New: Q-173-01, Q-173-02, Q-180-01. Details in `docs/northstar/ambiguity_register.md`.

Q-159-10 (closed 2026-10-21, register), pieces offered to Westley and neither picked nor rejected. They are not rules. Where one would land is in brackets.
- Build-ons: upkeep bands (S-169), foraging to farming (S-167), deeper districts (S-168), trading posts at neutral settlements (S-175, S-177), trade caravans (S-175), ages by landmark (S-173), worker scouting (S-172), a return-to-base ability (S-170), workers under raid (S-174).
- Thinking-ahead options: prizes on a clock, a shared market, demands from the civilization (S-176), the Keystone (S-168), the Contested Tree (S-173), agents.

Q-166-02 (the space-era landscape) is open in E-17 and bounds the land-map rules above.

## Depends on

- E-19 S-159: the paired mode, the seat, team sizes, the universe lock, drop-out and the command set across the wire.
- E-02 (region fields, the situation and richness), E-06 (the technology number and tier), E-10 (archetypes S-073, the five outcomes S-077, mission end R-075-07, region transfers).
- E-11 (categories, roster, workers as units), E-12 (fog, structures in fog, shipments against R-089-05), E-13 (route grid and routes that change with buildings, unit budgets and tick rate).
- E-14 (difficulty S-125, enemy behaviour around bases, expansions and raids), E-15 (strongpoints, moving weather, non-combat units S-129).
- E-17 (terrain, height bands, settlements, economic locations, a city that reshapes S-166), E-16 (economy screen, the dial and pointing), E-18 (drawing workers, shipments, buildings at scale), E-20 (era contents), E-21 (library content).

# Audit of the eight old layouts (2026-10-18)

Read-only audit for ROADMAP section 4 row 1. Nothing here is decided; the verdicts and the pairing are proposals. Sources: `simulation/layout_library/layout_01..08_*.json`, E-17 rules as written (`docs/bible/epics/E-17-map-generation.md`), E-22 R-177-02, `docs/northstar/research/layout_engine/README.md`, the layout search spec (`plans/2026-10-06-layout-search-spec.md`, rev 4) and run 1 (`research/layer_dynamics/runs/2026-10-08_layout_run1/depth_summary.json`, 200 layouts).

## What every layout shares (applies to all eight)

- The file holds `zones` (typed node, position as a share of the canvas, free-form `properties`), `edges` (path, flank, restricted), `tags`, an empty `drift_paths`. There is no plays field, so none declares its plays (R-192-04 says every layout declares them). The plays below are read off the nodes.
- No widths in numbers: a choke has only `width_hint` narrow or moderate. No node kind for a slope top or tall cover. No economy kind (base, economic location, significant resource, expansion site, neutral settlement, strongpoint). `staging` and `spawn_point` stand in for the two bases.
- R-191-04 (equal distance from both bases to each resource site and the objective): no layout has a resource site, so it cannot be tested. The objective sits beside one side in all eight, so the equal-distance form fails everywhere unless the archetype's slant allows it. Straight-line distance, base to objective / enemy spawn to objective, in canvas shares: 01 0.74/0.12, 02 0.80/0.08, 04 0.80/0.08, 05 0.92/0.13, 06 0.80/0.08, 07 0.70/0.10 (player far, enemy beside); 03 0.12/0.53 and 08 0.08/0.37 (player beside, enemy far).
- R-191-10 (layout first, widths given to the landscape engine): satisfied in spirit (typed nodes at positions) and not in substance (no numbers to hold the terrain to).
- R-177-02 and R-191-06: base kind is not in the file, which is right (the archetype table decides). Neutral towns: no kind. 04 draws a town as a block grid and 07 names transit nodes "outpost"; the rule says towns stand at economic locations the economy finds, never at fixed positions.
- Run 1 (all layouts): it is the space lab, not a ground graph. Each "layout" is one corridor between two starts, set by six numbers: choke width (0, 2, 4, 8 bodies), lanes (0, 1, 2), detour ratio (0, 1.5, 3), blocked-layer top (0, 2, 4), cover density, start distance (1,400 or 2,800 wu). It scored the depth score (skills whose gain is at least 2 units and whose counter works, 0 to 5), not the conditions C1 to C9 of the lab README, and compositions were moved to run 2. Caveats: Westley has not read the chart; 143 (layout, play, variant) groups were capped every fight with no contact, and Q-LAB-03 (2026-10-13) retired capped fights as results; the whole run is space, with no objective node, no economy, no vantage or tall cover as such. So a comparison is by choke/lane/detour structure only, and the mapping of "narrow" and "moderate" to bodies is my guess.
- Run 1 means for reference: all 200 layouts 1.64; no choke 1.22 (n 50); choke 2 bodies 1.88, 4 bodies 1.84, 8 bodies 1.60; lanes 0/1/2 give 1.36/1.66/1.89; start distance 1,400 gives 2.08 and 2,800 gives 1.19. Choke 2 or 4 bodies with 2 lanes at 1,400: 3.39 (n 18); the same with a 1.5 detour: 4.40 (n 5); the same with blocked-layer top 4 (cannot be flown over): 5.0 (n 3, layouts 68, 151, 169, naive line 1 each). Choke 4 or 8 with one lane at 1,400: 1.91 (n 22).

## Per layout

### 01 Fortress Ridge (medium; tags assault, defensive_stand)
- Nodes (14): staging 1, transit 2, hazard anchor 1 (ravine), chokepoint 2 (main narrow, right moderate), flank route 2, vantage 2 (high, layers 0 to 2), objective 1, reinforcement structure 2, spawn 1.
- Plays read off: hold a choke (two), take a vantage (two), go round (left flank reaches the objective). Layers: vantages carry layer_restrictions. No tall cover or slope top.
- Rules: R-189-07 three edge-disjoint routes base to objective (main, left flank, right), the best in the library; widths unknown. R-191-04 fails (objective beside the enemy spawn). R-192-04 meets landscape (choke, vantage) and enemy position (flank) and touches layers; the declaration is missing. R-177-02: tag defensive_stand contradicts the geometry, which is an assault (player forward, enemy at the fortress).
- Run 1: the structure (narrow choke, second lane, way round) sits in the lab's best cluster (above: 3.39 to 4.40) but only with the layer top at 4 and start 1,400. Reads as a good bone, not a proof.
- Verdict: keep as a recipe (after a rewrite with widths and the tag fixed).

### 02 Open Plains Assault (large; assault, interception)
- Nodes: staging 1, transit 1, flank route 4, chokepoint 1 (ford, moderate), vantage 1 (ridge, hint "low"), reinforcement 1, objective 1, spawn 1.
- Plays: hold the ford, take the ridge (hint low, so a weak vantage), exposed flanks. All routes (centre and two flanks) join at the ridge, then one chain to the objective.
- Rules: R-189-07 one route in the end (shared last chain). R-191-04 fails. R-192-04 met on landscape and enemy position. No moving objective though tagged interception (S-118 wants one).
- Run 1: one moderate choke with one lane, wide open: choke 4/8 with one lane scores 1.51 to 1.91, near the run's mean 1.64. Nothing in it that scored.
- Verdict: keep as reference only (a plain open assault; 01 and 06 cover its plays with more structure).

### 03 Three-Front Valley (large; multi_front_defense, siege_breaking, containment)
- Nodes (14): staging 1, objective 1 (central keep), chokepoint 3 (north moderate, northwest and northeast narrow), transit 3, vantage 2 (high ridges, restricted edges), reinforcement 2, spawn 1.
- Plays: hold three chokes, take two ridges. Player base and keep are 0.12 apart; enemy comes from one spawn along three corridors.
- Rules: R-191-04 fails literally, but fits an archetype slant (defender at home; R-177-06 slants toward the defender). R-177-02: fits Defensive Stand and Multi-Front Defense (home city). R-189-07 one route (base is the keep). R-192-04 met: landscape; enemy position weak (no flank node; the three corridors are the choice). No layers.
- Run 1: three lanes is outside the lab (max 2); the nearest, 2 lanes with a narrow choke, scores 2.3 to 3.4. Lane count is the only structural feature that rises with count (1.36, 1.66, 1.89), which supports the three-front idea weakly.
- Verdict: keep as a recipe (Multi-Front Defense).

### 04 Dense Urban Grid (medium; assault, defensive_stand, reconquest)
- Nodes (15): staging 1, transit 4 (city blocks), chokepoint 3 (two narrow gates, a moderate plaza), flank route 1, hazard anchor 1 (rubble), reinforcement 1, objective 1 (citadel), spawn 1. No vantage.
- Plays: hold a gate; a rubble approach; a flank alley. No vantage, so no height play.
- Rules: contradicts R-191-06 and R-193-01 (a town laid out by hand as a grid; towns now grow from the economy and follow rivers, contours, never a fixed pattern). R-191-04 fails. R-189-07: gates merge at the rubble, so one route. R-192-04: landscape yes, layers no. Tag defensive_stand contradicts geometry.
- Run 1: three parallel chokes with a merge is like 2 lanes with no detour; nothing distinct scored.
- Verdict: retire the layout; keep its one idea (three gates into a shared square) as a situation in the kit.

### 05 Coastal Wedge (medium; assault, defensive_stand, evacuation)
- Nodes (11): staging 1 (corner), transit 1, hazard anchor 1 (surf), chokepoint 2 (seawall narrow, inland road moderate), vantage 1 (cliff top, high), flank route 1, reinforcement 1 (harbour), objective 1, spawn 1.
- Plays: hold the seawall, take the cliff, choose beach or inland road (two real routes, edge-disjoint count 2). Needs a coast.
- Rules: R-189-07 two routes with different character. R-191-04 fails (objective 0.13 from enemy). R-192-04 met on landscape, layers (high cliff) and enemy position. Tags defensive_stand and evacuation contradict the geometry (an assault from a corner).
- Run 1: narrow choke plus a second, longer route is the 2-lane-with-detour cell (2.67 mean for choke 2/4, 2 lanes, detour 1.5, any start; 4.4 at start 1,400). Comparable structure, space data.
- Verdict: keep as a recipe, only on maps whose landform gives a coast (terrain is seeded, so the layout cannot demand one without a rule: see Q3).

### 06 Flanking Pass (medium; assault)
- Nodes (15): staging 1, transit 1, hazard anchors 2 (cliff faces), chokepoint 2 in series (pass mouth narrow, exit moderate), flank route 2, vantage 2 (summits, high), reinforcement 1 (waystation), objective 1, spawn 1.
- Plays: hold the pass, take either summit by the flank trails, go round. The flank trails end at the summits and then the waystation, which is before the objective, so they reach it only through the shared last edge (README: flank routes in 02, 04, 06 do not reach the objective).
- Rules: R-189-07 one route in the end. R-191-04 fails. R-192-04 met on landscape, layers and enemy position (best set after 01).
- Run 1: serial chokes are not sampled. A narrow pass plus two side lanes is the 2-lane cell (3.39 at start 1,400 for choke 2/4); the detour is short.
- Verdict: keep as a recipe (Assault with a pass; distinct from 01 by series chokes and two summits).

### 07 Scattered Outposts (medium; counterinsurgency, suppression)
- Nodes (11): staging 1, transit 3 (patrol, two outposts), hazard anchor 5 (sensor interference, one with layer_restrictions), objective 1 (supply cache), spawn 1 (dispersed insurgents). No choke, vantage or flank route.
- Plays: none of the three layer plays. The five interference zones are the only content.
- Rules: contradicts R-192-04 (offers no play). R-191-06: outposts are named towns at fixed spots. R-191-04 fails. R-177-02: Suppression and Counterinsurgency give the player a garrison in a city and the enemy hidden cells among the settlements, so the geometry (a forward base walking up a map) is wrong for the table.
- Run 1: "no choke" cells average 1.22 against 1.64 overall; lane 0 gives 1.36. The lab rates a map without a choke as shallow.
- Verdict: keep as reference only (its dispersed-cells idea is the only one for these two archetypes; nothing else in the library carries it, so it cannot simply be dropped).

### 08 Elevated Strongpoint (large; multi_front_defense, containment)
- Nodes (14): staging 1 (summit, high ground), objective 1 (tower, 0.08 from the base), chokepoint 3 (north moderate, two narrow south), transit 3, vantage 2 (crests, restricted), reinforcement 1 (bunker), spawn 1.
- Plays: hold three approaches from the high ground, crests. The only layout where the player starts high.
- Rules: R-191-04 fails literally; fits the defender slant (R-177-06). R-177-02 fits Defensive Stand and Multi-Front Defense. R-192-04 met: landscape, layers (high ground). No flank route.
- Run 1: lab start-distance effect (1,400 beats 2,800) fits a close summit; no layer-bias feature (the lab blocks layers, it has no "start high" feature), so nothing comparable on the height idea.
- Verdict: keep as a recipe (the layers play for defence).

## Verdict table (proposal, not a decision)

| # | Layout | Verdict | Why in one line |
|---|---|---|---|
| 01 | Fortress Ridge | keep as recipe | three routes, two chokes, two vantages, flank to objective; lab's best cluster is its shape |
| 02 | Open Plains Assault | reference only | one ford, weak vantage, routes merge; subsumed by 01 and 06 |
| 03 | Three-Front Valley | keep as recipe | three chokes, defender at home; lanes rise in the lab |
| 04 | Dense Urban Grid | retire | hand-drawn town grid contradicts R-191-06; keep three-gates idea as a situation |
| 05 | Coastal Wedge | keep as recipe (coast only) | two distinct routes, cliff; needs a coast |
| 06 | Flanking Pass | keep as recipe | serial chokes, two summits, flank trails |
| 07 | Scattered Outposts | reference only | no choke, vantage or flank; offers no play (R-192-04) |
| 08 | Elevated Strongpoint | keep as recipe | high-ground defence; only layers play for a defender |

"Recipe" here means the node pattern is used as input to the kit (README option C) after a rewrite with numbers, tags corrected and plays declared; none of the eight runs as is. If Westley picks option A or B for Q-191-06, "recipe" becomes "reference".

## Pairing with archetypes (proposal, not a decision)

Archetypes from `csrc/mission.c:161-170`. R-177-02 and the E-22 table fix who is attacker; the layout must put the player's base and objective on the right side of that.

| Archetype | Fits | Why |
|---|---|---|
| Defensive Stand | 08, 03 | player at home beside the objective |
| Siege Breaking | 03 (changed), 01 | needs relief camp outside, city inside as objective: 03's keep with the base moved outside; 01's fortress works if enemy camp moves to the ridge. Weak fit |
| Reconquest | 01, 06 | forward base against a held fortress or stronghold |
| Assault | 01, 06, 05 | forward base against a fortress; 05 only on a coast |
| Suppression | none (07 as reference) | garrison in a city, hidden cells; needs a new recipe |
| Multi-Front Defense | 03, 08 | three approaches, defender at home |
| Interception | none fits; 02 as reference | field camp on the enemy's path, moving objective (S-118); no layout has a moving objective |
| Evacuation (Rear Guard) | 05 (changed) | the place being left, pursuer behind; 05's geometry would need reversing |
| Containment | 08, 03 | field camp holding approaches |
| Counterinsurgency | none (07 as reference) | as Suppression |

Gaps: four of ten archetypes (Suppression, Counterinsurgency, Interception, Evacuation) have no fitting survivor. Three assault shapes against two defence shapes.

## Questions only Westley can answer

1. Q-191-06 (shape of the engine): A authored layouts rewritten with intent, B numbers solved per map, or C a kit of situations. The audit's verdicts assume C; under A the recipes are rewritten whole; under B they are only reference.
2. Q-191-07 (what the objective does): (a) fixed and equidistant, (b) fixed with value growing, (c) moving on the moving archetypes, (d) assault shapes keep a near-enemy objective and only resources are equidistant. The answer decides whether the six layouts with the objective beside one side are broken or correct (R-191-04 as written fails all eight).
3. Does a layout have the right to demand a landform (a coast for 05, high ground for 08)? (a) yes, the landscape engine must produce it or the layout is not offered; (b) no, a coast is dropped and only choke/vantage structure survives; (c) yes for a short list of landforms the seed can steer toward.
4. Layouts for the four archetypes with no survivor (Suppression, Counterinsurgency, Interception, Evacuation): (a) new layouts drawn now; (b) composed from kit situations later; (c) these archetypes use terrain-found places only, no layout.
5. Tag fixes: 01, 04 and 05 are tagged defensive_stand but are attacks. (a) retag by geometry; (b) flip the geometry to match the tags; (c) drop tags and pair by the table above.
6. Run 1 as evidence: the chart is unread, 143 groups were no-contact capped, and Q-LAB-03 retires capped as a result. (a) rerun after the end-rule fix before any pairing leans on it; (b) treat it as a lead only and pair on structure; (c) read the chart first and rule then.
7. Hand-drawn towns: 04's grid and 07's outposts. (a) delete the town shapes and keep only the choke and approach structure; (b) let a layout mark a "settlement here" node and the economy grows the town; (c) neither, towns come only from economic locations.
8. R-192-04 "every layout declares its plays": (a) a plays field in the file, checked against the finished terrain; (b) derived from node kinds with no field. Needs the node kinds for slope top and tall cover (Q-192-04 (a)) either way.

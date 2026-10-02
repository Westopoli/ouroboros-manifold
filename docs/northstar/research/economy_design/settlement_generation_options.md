# Goal 3: settlements that build themselves, on ground with real height

Written 2026-10-01 for Westley. Options per part, surface level, for him to pick from or fuse. His direction is verbatim in E-17 S-166 R-166-01. The flag is Q-166-01.

## What he fixed

- The self-built part of a city is mostly cosmetic. The economy itself is run by rules, and run well.
- Cities are lively: buildings start under construction and rise, expansions are made, population density changes over time.
- Population density uses the same field map as the landscape.
- It is not restrictive. The player places buildings wherever he wants and the city morphs around them.
- Bases vary in site: a valley, a mountainside, an archipelago.
- The layer system is used. A city on a cliffside can span a whole mountain or valley, and an enemy has to cross all those layers to reach everything.
- Massive scale, Minecraft-level variety in biome and height.
- It is visual and functional, and the foundations have to be there for the game to handle it.

## What the landscape prototype does today

The prototype is `scenes/mockups/landscape/` (`field_map.gd` generates, `placer.gd` places pieces from a kit).

| Part | Today | Gap against what he fixed |
|---|---|---|
| Grid | One cell per 100 wu; canvas 16,000, 24,000 or 32,000 wu (up to about 100,000 cells) | Not yet "massive" |
| Height | Three layers of noise (continent, hills, detail) scaled so peaks reach 3,000 to 5,000 wu; a coast forced on the south edge | One recipe; variety comes only from the seed |
| Water | Lakes flooded from low points; rivers traced downhill | Fine |
| Biome | Five zones from height, moisture and latitude | Few; no landforms |
| City site | One core, at the best-scoring cell: near water, flat, about 500 wu up, away from the edge | One base; the site is whatever the seed gives |
| Density | Distance from the core, cut by slope, raised near water; five district levels by threshold | One source; computed once; ignores anything the player builds |
| Walls and cliffs | Traced as contours; cliffs traced on height cut into five terraces | The five terraces are drawn only. They are not the game's five layers |
| Placement | Kit rules match a cell's values to a piece; everything is placed at once | No time: nothing is built, nothing grows |
| Where it runs | In the Godot client, in GDScript, using the engine's noise | The game needs the functional part in the C sim, the same on every machine |

So the prototype already has the right shape: one field map, a density value per cell, pieces chosen by rule. What is missing is several sources of density, time, a link from height to layers, a choice of site, and a home in the sim.

---

## Part 1. The density field: what decides where the self-built city goes

- **1A. More attractors.** Keep today's formula and let it have many sources: the core, every building the player places, roads, water, resource sites. Each adds density around it; slope still cuts it. Smallest change; a placed building is one more source, so the city shifts toward it.
- **1B. Travel-time field.** Density at a cell depends on how long it takes to walk there from the sources, over real terrain: slopes cost, rivers block except at bridges, roads are fast. The city fills valleys, runs along roads and stops at cliffs without being told to. The prototype's own comment calls today's formula a stand-in for this.
- **1C. Growing field.** Density spreads cell to cell a little each step, faster on suitable ground. Growth over time comes built in, and the shape is the most organic. Hardest to predict and to keep cheap.

## Part 2. How the city morphs around a placed building

- **2A. Clear and refill.** A placed building claims its footprint. Self-built pieces under it are taken down and the neighbours re-roll. Simple; the city gives way and nothing more.
- **2B. Buildings have a character.** Each building type changes the field around it: a market raises density and wealth, a smithy brings yards and smoke, a barracks pushes housing away and brings drill grounds, a wall stops growth and stacks it up inside. Districts appear because of what the player built, with no district tool.
- **2C. Streets first.** Every placed building gets a street to the nearest street, routed over the terrain. Self-built buildings line the streets. The player's buildings become the skeleton and the city grows on it.

## Part 3. Growth over time: the spectacle

- **3A. Stages by threshold.** Each lot has stages: empty, staked, scaffold, small, large. A lot moves up a stage when the density at its cell passes a threshold, with a construction animation between. The field's target comes from the region's economy and the mission clock, and what is on the ground lags behind the target.
- **3B. Builders on the roads.** A lot starts building only when a cosmetic crew has walked to it from the core with a cart. The roads are busy for a reason and growth visibly spreads outward along them. Costs more to draw.
- **3C. Waves.** Growth comes in bursts tied to things that happen: a shipment arrives, an expansion is founded, a season turns. A whole street goes up at once.
- **All three:** damage runs the stages backward to rubble, and rebuilding speed follows the civilization's economy, as decided on 2026-09-22.

## Part 4. The site of a base

- **4A. Named sites.** A short list of site types: valley floor, mountainside, cliff-top, archipelago, river delta, plateau, pass. The simulation's region picks one. Each type is a different set of weights for the same scoring the prototype already uses to find the core, and a different terrain recipe.
- **4B. Whatever the terrain gives.** One terrain recipe; the score finds the best cell; the site type is named afterwards from what it turned out to be. Least control over variety.
- **4C. Named sites, several cores.** As 4A, and the same scoring also finds the secondary sites: settlement seeds at economic locations, expansion sites, and the significant resources placed opposite the objective. Needed in any case for expansions.

## Part 5. Landscape variety

- **5A. Climate table.** Add temperature and moisture fields and pick the biome from a table of the two, with height. Many more biomes from the same machinery. This is how Minecraft gets its variety.
- **5B. Landforms.** Large features with their own shape, blended into the noise: canyon, mesa, caldera, fjord, terraced massif, island chain. This is what gives height its drama; noise by itself gives rolling hills.
- **5C. The region decides.** The simulation's region carries a climate and a landform, and the map is generated to match. The region's environmental trouble (the storm, the flood, the dust) comes from the same record.

## Part 6. Height and the five layers

This is the functional part. The bible's layer rules today: five layers, fixed for every map; a walking unit changes layer only along a slope; the map says where there is land on each layer.

- **6A. Terraces are the layers.** The terrain's height is cut into five bands across the whole map, and the band is the layer of the ground there. A city climbing a mountainside stands on layers 1 to 5. The cliffs between bands are the layer boundaries the prototype already traces, and ramps, stairs, switchback roads and lifts are the slopes. An attacker walks every band to reach the top.
- **6B. Layers are local.** Each base and its surroundings get their own five bands, fitted to the local relief, so a base on a high plateau still uses all five. More of every map uses the layer system, at the cost of a layer meaning different heights in different places.
- **6C. Ground below, sky above.** The ground takes layers 1 to 3 by terrace. Layers 4 and 5 are above the ground: peaks, towers, and whatever flies.
- **For all three:** the layer lab is still settling cross-layer rules, and this choice should be tested there before it is fixed.

## Part 7. Scale, and what the game has to carry

- **7A. Today's size.** Keep 100 wu cells and a canvas up to 32,000 wu. Everything is generated at once. Simplest; the map is large but not unprecedented.
- **7B. Bigger, in chunks.** A canvas several times larger, generated and drawn in chunks as the camera and the armies need them.
- **7C. Two resolutions.** The sim owns a coarse functional map: layer, land, slopes, water, density. It is the same on every machine. The client draws all fine detail (every self-built building, every prop) from the seed and the sim's fields, and none of it feeds back. Buildings the player places are real things in the sim; the self-built city is drawn in bulk and costs the sim nothing. The city is still functional through the fields: dense districts slow movement and give cover, as obstacle and cover density already do.

---

## How the parts depend on each other

- Part 6 (layers) decides what Part 4 (sites) and Part 5 (landforms) are for: a mountainside site matters because of the layers it spans.
- Part 7 decides how much Parts 1 to 3 can afford.
- Parts 1, 2 and 3 can be chosen independently of each other.

## My lean (opinion, Westley's call)

1B, 2B with 2C, 3A now and 3B later, 4C, 5B with 5C, 6A, 7C.

- **6A** is the one that makes a mountainside city a five-layer assault, and it reuses the cliffs the prototype already traces.
- **7C** is what makes thousands of buildings affordable and keeps the sim the same on every machine.
- **1B** is what makes cities follow valleys and roads for real.
- **2B and 2C** together are what "the city morphs around them" looks like.
- **5B and 5C** give Minecraft-level variety and tie it to the simulation.

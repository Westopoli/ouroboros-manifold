# Goal 3: settlements that build themselves, on ground with real height

Written 2026-10-01 for Westley. Options per part, surface level, for him to pick from or fuse. His direction is verbatim in E-17 S-166 R-166-01. The flag is Q-166-01.

## Decided, 2026-10-02

| Part | Decision |
|---|---|
| 1 Density field | **1C, the growing field.** And for the whole system: the population engine never gives up at difficult terrain. It adapts, and builds in wild places: inside a cliff, under a waterfall, on a steep mountainside. |
| 2 Morphing | **2A, clear and refill.** |
| 3 Growth | **3C with 3A:** waves, and stages by threshold. |
| 4 Site | **4B, whatever the terrain gives.** The generation is meant to be stochastic and unruly. |
| 5 Variety | **5B with 5C:** landforms, and the region decides. |
| 6 Layers | **6A, terraces are the layers, with a mix of benched and natural ground.** The engine produces a variety of landscapes, and some sections are so steep that units cannot traverse them. The bands are **fitted to each map**, and the generator must give every map enough relief that a layer step is a real height difference, never a meadow slope. |
| 7 Scale | **7D, one world with continuous detail.** The canvas stays at today's sizes (largest 32,000 wu) for now, to see how players like it, as long as landscape variety is packed into the maps. The zoom stops at the battlefield's map view. |

Option 1B's line that the city "stops at cliffs" was wrong for this game and is withdrawn. Difficult ground changes what gets built there, not whether anything is.

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

## 6A expanded: terraces are the layers

**The rule.** Height above sea level is cut into five bands, the same on every map. The band a piece of ground falls in is its layer. With peaks of 3,000 to 5,000 wu, a band is about 1,000 wu tall.

| Layer | Height band (placeholder numbers) | Reads as |
|---|---|---|
| 1 | sea level to 1,000 | coast, valley floor, river plain |
| 2 | 1,000 to 2,000 | foothills, lower terraces |
| 3 | 2,000 to 3,000 | hillsides, plateaus |
| 4 | 3,000 to 4,000 | high shelves, mountain shoulders |
| 5 | above 4,000 | peaks, summit fortresses |

**What follows from it, using rules the bible already has.**

- **Ground fills the layers below it.** Where the ground is on layer 3, layers 1 and 2 at that spot are solid rock. That is the bible's existing "terrain blocks layers at specific places". A building inside a cliff, or a tunnel, is an opening in that rock.
- **Walking units** stand on the ground's layer and change layer only on a slope: a natural ramp, a pass, a switchback road, stairs, a built lift. Where the ground jumps a band steeply, it is a cliff and they cannot cross.
- **Flying units** can be on the ground's layer or any layer above it, never below.
- **A slope's halfway line** is already the line where a unit passes from one layer to the next (R-004-06). Every ramp up a mountainside is a line on the map that can be held.
- **Fighting across bands** uses the cross-layer rules the layer lab is settling. A terrace above a terrace is high ground with real rules behind it.
- **Inside a band** the ground still rises and falls. That is visual and affects the camera; for the rules it is one layer.

**What it does to a base.**

- A mountainside city has districts on every band. The attacker takes the ramp to layer 2, then the stair to layer 3, and so on; the defender falls back upward.
- A valley city sits on layer 1 with rims on layer 3. Whoever holds the rim shoots down.
- A plains city is all on layer 1. Its fights are flat, and flyers own layers 2 to 5.
- An archipelago is mostly layer 1 with water between; a peak on one island is the high ground.

**Three things to settle inside 6A.**

1. **Benched or natural.** Benched: the generator shapes the ground into wide shelves with steep risers at each band edge, so a layer boundary is always a visible cliff or ramp. Natural: the ground rolls freely and a band edge can cross an open meadow, marked only by a drawn line. Benched is what the prototype's terrace shaping already does, and it is far easier to read.
2. **Fixed heights or fitted to the map.** Decided 2026-10-02: fitted, with the generator responsible for real relief on every map. The options as they were put:
   - **Fixed.** The bands are the same heights on every map. Layer 4 always means high mountain. A flat coastal map has all its ground on layer 1 and no layer play for walking units; a mountain map has all five. What a layer step looks like never changes, so the cross-layer rules always apply to a real height difference.
   - **Fitted.** Each map stretches the five bands over its own lowest and highest ground. Every map has five layers of ground. On a gentle map a band is thin, so a low hill is a layer above the field beside it, and the cross-layer rules for sight and damage apply to a small rise. A layer step is a cliff on one map and a slope in a meadow on another.
   - **Fixed, with a floor on relief.** The bands are fixed, and the generator must give every map ground on at least three of them. Layers mean the same thing everywhere and no map is flat. This matches the condition that landscape variety is packed into the maps, and the register's earlier answer that the mapping is fixed globally (Q-E01-01).
3. **Space.** The Settled Reach has no ground. Its layers stay pure altitude, and asteroids and stations are the things that block them. Nothing changes there.

**Cost.** Maps differ in how much layer play the ground gives, by design: the unruly generation decides. It needs testing in the layer lab before it is fixed.

---

## Part 7 restated: what "two resolutions" meant, and option 7D

The earlier wording was unclear. It was about who keeps track of what, not about how sharp anything looks.

- **The sim** needs to know only what affects play: the layer of the ground, where slopes and water are, how dense a district is. It can know that coarsely, and it must be identical on every machine.
- **The screen** can show as much detail as the zoom calls for. None of that detail has to be stored or sent; it is worked out from the seed when the camera needs it.

What Westley asked for is the screen half, taken as far as it goes:

**7D. One world, continuous detail.**

- **The world is a formula, not a stored map.** Height, biome and density at any point come from the seed. Asking for more detail means sampling the same formula more finely. This is how No Man's Sky and Minecraft hold worlds far larger than memory.
- **Terrain is drawn in tiles that subdivide as the camera comes down.** From high up, a few large coarse tiles give the shape of the land; close in, small fine tiles give rocks and ledges. The change is gradual, so there is no pop and no loading break.
- **Buildings and units step down with distance.** Close: full models, construction scaffolds, people. Farther: simple shapes drawn in bulk. Farther still: district-coloured blocks, then the World of Warships map view, with unit groups as icons.
- **One continuous zoom** from a single unit to the whole battlefield, on the camera's height-above-ground floor already decided.
- **The self-built city costs the sim nothing.** It is drawn from the density field. Buildings the player places are real things in the sim.

**Two questions inside 7D.**

1. **How big.** Today the largest canvas is 32,000 wu. Size has a price in play: a Raider at speed 150 crosses 32,000 wu in about 3.5 minutes, and a Bastion at speed 40 takes about 13.

| Canvas | Area against today | Raider crossing | Bastion crossing |
|---|---|---|---|
| 64,000 wu | 4x | 7 min | 27 min |
| 128,000 wu | 16x | 14 min | 53 min |
| 256,000 wu | 64x | 28 min | 107 min |

   Very large maps need a way to move forces fast: travel lanes (E-17 S-165), transports, and the forward bases already decided.

2. **Where the zoom stops.** At the battlefield's map view, or on out to the region and the galaxy in one unbroken motion. The bible currently keeps the galaxy view separate from a mission.

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

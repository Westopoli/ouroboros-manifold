# E-17 — Map Generation

## Definition-completeness gate (redrafted 2026-10-02, not yet rerun)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Partly. 22 stories, 110 rules. S-112 to S-119 keep the rules built and tested today (numbers from `algorithms.md` ALG-70 through ALG-73 and config), and the layouts they describe stay. The terrain-first stories (S-186 to S-197) carry a number only where Westley gave one, and write every other number as a flag. |
| Every input listed with range and rejection behavior | Yes, see Inputs. |
| Every output listed with where it is observable | Yes, see Outputs. |
| Implied-but-unstated behavior turned into flags | Yes. 11 open flags, listed under Open ambiguity flags. |
| Every visible-surface story has a reference | Yes. `docs/bible/references/E-17/notes.md` holds shots 01 to 13, and `docs/northstar/research/landscape_design/README.md` holds Westley's review of the prototype. |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed.** Blocked on the open flags. The design is decided and is not scheduled for building. The gate is rerun when the flags close.

## Purpose

Every land map has terrain generated from the seed. A seeded formula gives the height of the ground and the water on it: lakes in the low ground and rivers that run downhill from the peaks to a coast. Landforms and a climate, derived from the seed, give each map its own shape. Height is cut into five bands fitted to that map, and the band a piece of ground falls in is its layer, so a mountainside is a stack of layers and an attacker has to cross every one of them to reach everything on it. Some ground is too steep to walk. The generator then finds the places the game needs on that terrain by rule: a base of operations for each side, the objective, economic locations throughout the map, the significant resources opposite the objective, expansion sites, strongpoints at the slopes between bands, chokes, high ground and the other places the layer plays need. The hand-authored layouts of S-112 stay, with their moving objectives, and the terrain engine accounts for them. The new terrain-first ideas are added to the old layout design and do not remove it. Both are built together: the layout calls for places and the landscape engine is required to produce them (S-191 R-191-10).

Cities and bases are on the same field map. Population density is a growing field that spreads a little at a time and never gives up at difficult terrain. Buildings rise from scaffolds in waves, and the city reshapes around whatever the player places. The world is one formula drawn at continuous detail, from a single unit to the map view. The theme pack decides whether a barrier is a rock or a wall, and the era kit decides what a piece looks like.

This is also where the layer system gets its terrain (E-01 S-001), where fog gets its interference (E-12 S-090), and where the economy gets its sites (E-22).

Everything from the landscape decisions of 2026-10-01 and 2026-10-02 (S-166 and S-186 to S-197) is design decided, not scheduled for building. Stories S-112 to S-119 describe the layout generator that is built and tested today. It stays, and terrain-first generation is added to it. These rules are for land maps. The space-era landscape is a sister system with its own story, S-246.

## Obviously working in 60 seconds

Generate a land map for a medium canvas from seed 11. The terrain has height and water, and the five height bands are stretched between the map's lowest and highest ground, so the map has ground on all five layers and every layer step is a real height difference. Some ground is too steep to walk, and walking units change layer only on slopes. Each side has a base of operations, there is an objective, economic locations are spread through the map, and the significant resources lie opposite the objective. Strongpoints stand at slopes between bands, and every choke is where a pass, a bridge or a gate must be. Regenerate from seed 11: identical terrain and identical places. Generate seed 12: a visibly different landmass, not the same map with different dressing. Raise stability from 20 to 90: the same terrain with thinner interference and cover. Zoom from the map view down to a single unit: one continuous world, no pop and no loading break, and the camera keeps its height above the ground as it climbs a mountain. Watch a base for a minute: lots start as scaffolds and rise, a wave of building goes up after an event, and placing a building clears the pieces under it and the neighbours refill. Where a map uses a layout, the terrain accounts for it and the layout's moving objective still moves (S-112, S-118; S-191 R-191-10).

## Stories

### S-112 — Bones from the library
Flag closed, rule text pending: Q-113-01, fairness is a logger only until the generator is tuned in the P2 landscape design phase. The rule below is what the tests read today.
Flag closed, rule text pending: Q-112-01, the launch ships 8 layouts and grows after testing. The rule below is what the tests read today.

Direction changed 2026-10-02, rewrite pending: the layout library stays and terrain-first generation is added to it, so the terrain engine accounts for the layouts: the layout calls for places and the landscape engine is required to produce them (S-191 R-191-10, decided 2026-10-03). The library is audited and double checked before it is implemented, because the game has changed since the layouts were authored, and archetypes are probably paired with layouts (Westley, 2026-10-03). The rules below are what the game does today.

As a commander, I want maps built on hand-authored strategic layouts so that every map has a chokepoint, a flank, and a reason, and I learn the vocabulary over time.

Rules
- R-112-01  Given an archetype, When candidates are gathered, Then every layout satisfying at least one of the archetype's compatibility filters (structural checklists, 2 to 3 per archetype) enters the pool.
- R-112-02  Given the pool, When one is chosen, Then it is drawn uniformly at random [Q-113-01: hints as bias, fairness as gate].
- R-112-03  Given a layout, When instantiated, Then its zone positions (percentages of canvas) scale to the canvas dimensions with jitter of up to 3 percent of canvas per zone, spatial ratios preserved.
- R-112-04  Given the instantiated nodes, When edges are laid, Then the layout's connectivity is honored, there are at least 2 distinct routes from staging to every objective, at most the layout's allowed dead ends, and every flank route connects to at least 2 non-flank nodes.
- R-112-05  Given the library at launch, When loaded, Then it holds between 10 and 20 layouts and each archetype has at least 4 compatible layouts [Q-112-01: current count].
- R-112-06  Given a layout file, When loaded, Then it contains only zone positions, relationships, chokepoint specs, node placement, and connectivity; never gradient values, era visuals, absolute coordinates, enemy behavior, or difficulty.

Inputs: archetype; layout library; seed.
Outputs: instantiated spine (nodes, edges) in the map seed.
Open flags: none.

### S-113 — Nine kinds of place

Direction changed 2026-10-02, rewrite pending: the nine kinds of place stay, and terrain-first generation adds places found on the terrain by rule: bases, economic locations, significant resources, expansion sites, neutral settlements and strongpoints, with chokes and vantages that may also come from the land. A layout's typed node is a requirement the landscape engine must produce at its zone (S-191 R-191-10, S-192). The rules below are what the game does today.

As a commander, I want every place on the map to be one of nine things, so that I can read a map I have never seen.

Rules
- R-113-01  Given any spine node, When typed, Then it is exactly one of objective, staging, transit, chokepoint, flank_route, vantage, hazard_anchor, spawn_point, extraction.
- R-113-02  Given any map, When checked, Then it has at least one objective and at least one staging node.
- R-113-03  Given a chokepoint, When checked, Then at least one flank route bypasses it.
- R-113-04  Given a vantage node, When checked, Then it is reachable from both staging and every spawn point and pre-owned by nobody.
- R-113-05  Given a chokepoint spec of width ratio w, When instantiated, Then the passable width is w × 200 wu (standard formation width).

Inputs: layout node placement.
Outputs: typed nodes in the map seed; recon render.
Open flags: none.

### S-114 — Texture from gradients
Flag closed, rule text pending: Q-115-01, overlapping gradient sources combine by sum clamped to 1.0: intensity = min(1.0, i1 + i2). The rule below is what the tests read today.

Direction changed 2026-10-02, rewrite pending: the gradient sources stay, and terrain-first generation adds elevation, blocking and layer access that follow from the terrain's height bands and slopes, with steep ground that blocks walking units (S-188, S-189, S-190). The rules below are what the game does today.

As a commander, I want the space between waypoints to feel dense or open, blind or clear, high or low, so that a map is a place and not a diagram.

Rules
- R-114-01  Given the five properties, When sampled anywhere, Then each of obstacle_density, cover_density, sensor_interference, elevation is a float in [0, 1] and layer_accessibility is binary per layer.
- R-114-02  Given a gradient source (position, type, radius, intensity, falloff), When sampled at distance r ≤ radius, Then its contribution is intensity × falloff(r/radius), and overlapping sources combine [Q-115-01: sum clamped or max].
- R-114-03  Given the instantiated spine, When sources are placed, Then obstacle density anchors at chokepoints (intensity 0.85, radius 600) and staging (0.60, 800); elevation at vantage nodes (0.90, 700); interference at hazard anchors (0.75, 500); cover at chokepoints (0.55, 550), objectives (0.50, 400), hazard anchors (0.35, 400); flank routes get light obstacles (0.35, 450) and cover (0.40, 450).
- R-114-04  Given a zone with layer restrictions, When masks are placed, Then every layer not listed gets a full-intensity blocking source of radius 600 at the zone, and accessibility at a point is open unless a blocking source's sampled value ≥ 0.5.
- R-114-05  Given obstacle density > 0.7 at a cell, When the route grid is built (E-13 R-097-01), Then the cell is blocked.

Inputs: spine; layout hints.
Outputs: gradient sources in the map seed; sampled fields for E-01, E-12, E-13.
Open flags: none.

### S-115 — The region shapes the terrain
Flag closed, rule text pending: Q-117-01, the multipliers are active with conservative bounds: baseline hazard density * (1 + 0.5 * (100 - stability)/100), with deltas clamped to +-25%. The rule below is what the tests read today.

Direction changed 2026-10-02, rewrite pending: the region's state keeps flavoring interference, hazards and cover, and terrain-first generation adds a climate and landform derived from the seed (S-187). The rules below are what the game does today.

As a commander, I want a prosperous region's battlefield to be cleaner than a war-torn one's, so that I feel the galaxy's state under my feet.

Rules
- R-115-01  Given region stability s and capacity c, When baselines are set, Then interference, hazard anchor count, and cover scale with (100 − s)/100 and obstacle density with (100 − c)/100, each within a bounded multiplier [Q-117-01: exact multipliers].
- R-115-02  Given individual fields, When deltas are applied, Then economy lowers obstacle density along routes and adds cover from infrastructure, tension raises cover, military raises obstacle density near defensive positions, population scales total feature density; deltas are bounded so they never overwhelm the baseline.
- R-115-03  Given simulation coupling disabled, When a map is generated, Then layouts and hints alone produce a valid map.

Inputs: region fields and composites.
Outputs: adjusted source intensities.
Open flags: none.

### S-116 — Canvas
Flag closed, rule text pending: Q-118-01, state-based canvas sizing, the bible approach: base size plus or minus 30 percent by region, direction per archetype. The rule below is what the tests read today.

Direction changed 2026-10-02, rewrite pending: a match of 4 to 6 players has a canvas of 64,000 wu, and smaller matches keep today's sizes (S-195), except that the small category goes away: Suppression and Counterinsurgency take a canvas drawn from medium and large, with a compact play area (R-188-06). The rules below are what the game does today.

As a commander, I want mission maps sized to the situation, so that a suppression is tight and a siege is vast.

Rules
- R-116-01  Given an archetype, When the canvas is chosen, Then its base category is the E-10 S-073 table, and its dimension is drawn from small [8,000, 12,000], medium [12,000, 20,000], large [20,000, 28,000] wu square [Q-118-01: bible says fixed 8/16/24k ± 30 percent].
- R-116-02  Given the region's fields, When the ±30 percent modifier applies, Then its direction is the archetype's (defensive stand grows with wealth, counterinsurgency grows with tension, suppression shrinks).

Inputs: archetype; region.
Outputs: canvas size in the map seed.
Open flags: Q-195-01 (what the largest present size is).

### S-117 — Fair enough
Flag closed, rule text pending: Q-113-01, a score outside the range is logged only until the generator is tuned in the P2 landscape design phase; switching to reject-and-regenerate is a design-phase decision. The rule below is what the tests read today.

Direction changed 2026-10-02, rewrite pending: the fairness check stays and also scores the terrain and places of a terrain-first map, against a map the situation may deliberately slant (S-197). The rules below are what the game does today.

As a commander, I want maps that do not cheat me, so that a loss is mine.

Rules
- R-117-01  Given a generated map, When the fairness evaluator runs, Then it scores route count staging-to-objective versus spawn-to-objective, mean travel time balance, vantage accessibility balance, and hazard distribution symmetry, and logs the score.
- R-117-02  Given the launch build, When the score is outside the acceptable range, Then [Q-113-01: the map is regenerated with a new seed up to 5 times (bible), or accepted and logged (code, A-393)].
- R-117-03  Given a layout in the library, When authored, Then it passes the hard constraints: no side's every approach blocked by hazards while the other's is clear; every vantage reachable by both sides.

Inputs: map seed.
Outputs: fairness log; regeneration.
Open flags: none.

### S-118 — The battlefield moves

Direction changed 2026-10-02, rewrite pending: the moving objectives stay, and on a map that combines a layout with terrain-first generation they follow walking routes on the terrain (S-191 R-191-10). The rules below are what the game does today.

As a commander, I want objectives to drift and hazards to move during a mission, so that a position is never solved.

Rules
- R-118-01  Given a spine node of type objective or reinforcement_structure with a drift path, When ticks pass, Then its position follows the path (ping-pong or loop over waypoints with a period in ticks) and the objective zone moves with it.
- R-118-02  Given a gradient source with motion, When ticks pass, Then its position moves and every sampled field updates.
- R-118-03  Given a moving node, When it moves, Then no unit teleports; units path to the new position under their standing orders.

Inputs: drift specs in the map seed.
Outputs: node and source positions per tick in the delta; HUD objective marker.
Open flags: none. A strongpoint is fixed at its slope and is not a drifting source (Westley, 2026-10-07). Weather that travels across the map and shuts down what it passes over is E-15 S-130, not a drifting source.

### S-119 — Terrain that reads like a place
Flag closed, rule text pending: Q-119-01, Track R research comes first, to inform the implementation style. The rule below is what the tests read today.

Direction changed 2026-10-02, rewrite pending: terrain is blended layered noise added to the layouts, and the generator is one generator over one field map read by two kits through one placer (S-186, S-196). The rules below are what the game does today.

As a commander, I want generated sections to blend like real terrain, not tile like a board, so that every map feels made.

Rules
- R-119-01  Given a T2 screenshot of any generated map, When inspected, Then no repeated tile boundary is visible and gradient regions blend without hard edges.
- R-119-02  Given the procedural architecture system Westley opened in Stage 1 (A-157), When designed, Then it is era-agnostic at the section level with an era-specific kit of pieces assembled by it [Q-119-01: scope and schedule].

Inputs: map seed; era kit.
Outputs: screen.
Open flags: none. The layout library stays and terrain-first generation is added to it (S-191 R-191-10). References: `docs/bible/references/E-17/notes.md` (Minecraft and Roblox biome blending are the named references, shots 09 to 13).

### S-165 — Later, perhaps: travel lanes
As a commander, I may someday want the map to have lanes where troops move faster and strategic ground where they move slower, so that where an army can travel quickly is part of reading the landscape.

Rules
- R-165-01  Deferred; an idea, not a decision (Q-165-01). As Westley sketched it for a possible game mode: the biome generator lays lanes of travel that sprawl through the map like a tree; troops moving along a lane move at 1.3 times their speed; key strategic positions and layers, such as high ground, slow movement, placed with care; everywhere else is 1.0.

Inputs: none yet.
Outputs: none yet.
Open flags: Q-165-01 (whether the idea is wanted, and as a mode or in every map).

### S-166 — Settlements that build themselves, on ground with real height
As a commander, I want cities and bases that grow by themselves around whatever I place, on terrain as varied and as tall as a real landscape, so that the game has a sense of scale no strategy game has had and the base I fight over is a spectacle to watch being built.

Westley's direction and the decisions that fix it. The stories S-186 to S-197 hold the rules that carry them out.

Rules
- R-166-01  Direction. Westley, 2026-10-01, verbatim: "I want the cities to contain building that aren't only placed, a lively and busy environment that's a spectacle to watch and see built. Buildings that start under construction (like AOE3), and slowly get built, expansions made, different levels of population density that change over time. I want the population density to use the biome generation system, the same *heatmap* or whatever you call it (layout). Not restricitve though, the player can place buildings wherever they want, and the city will morph around them. - I'd also like cities/bases to vary in their *location*, by that I mean some are placed in a valley, some are on a mountainside, some are in an archipelago, and I want to take advantage of the layer system. If a city is on a cliffside and the city spans over a whole mountain/valley, the enemy should have to traverse all those layers in ordre to reach everythign. I want the players to get a real sense of scale playing the game and moving their forces around. Massive scale unlike anything seen before in an RTS. Minecraft level variations in landscape (biome/height, etc). This part is significantly visual, but it needs to have the foundations underneath in order for the game to handle it, and it's not *only* visual it's functional too."
- R-166-02  Fixed by that statement: the self-built buildings are mostly cosmetic and the economy itself is run by rules (E-22 S-179); population density comes from the same field map the landscape uses (S-193); the player may place a building anywhere (E-22 S-168); the site of a base varies (S-191); a base may span several layers, and an attacker must cross those layers to reach all of it (S-188, S-191); the result is functional as well as visual.
- R-166-03  Decided by Westley, 2026-10-02: the site of a base is whatever the terrain gives. The generation is stochastic and unruly, and no site type is chosen in advance. Variety comes from landforms blended into the terrain and from climate and landform, which the simulation's region decides and which are derived from the seed for now (S-187). Growth, density and the city's response to what the player places are S-193.
- R-166-04  Decided by Westley, 2026-10-02: terrain height becomes the five layers by height bands. The band a piece of ground falls in is its layer, the ground fills the layers below it, and walking units change layer only on a slope (E-01 R-001-06, R-001-07). The ground is a mix of benched and natural, and some sections are so steep that units cannot traverse them. To be tested in the layer lab before it is fixed (S-188, S-189, S-190).
- R-166-05  Decided by Westley, 2026-10-02: the canvas stays at its present sizes for now, to see how players like it, on the condition that landscape variety is packed into the maps. The world is one formula drawn at continuous detail, deep detail fully zoomed in and the shape of the land zoomed out, with smooth transitions between. The zoom stops at the battlefield's map view (S-194, S-195).
- R-166-06  Decided by Westley, 2026-10-02: the five height bands are fitted to each map, stretched between its lowest and highest ground, so every land map has ground on all five layers. The generator must give every map enough relief that a layer step is a real height difference, and a layer step that is only a meadow slope is a defect of the landscape generation (S-188).

Inputs: see S-186 to S-196.
Outputs: see S-186 to S-196.
Open flags: none held here. Q-166-02 (the space-era landscape, not designed) and Q-166-04 (S-188) are carried in the stories that need them. Options and decisions: `docs/northstar/research/economy_design/settlement_generation_options.md`.

### S-186 — The ground comes first
As a commander, I want every map to start as real ground, with height and water from the seed, so that bases, passes and cities are found on a landscape and never stamped on flat ground.

Rules
- R-186-01  Given a seed and a canvas, When terrain is generated, Then the height of the ground and the water on it come from a seeded formula: layered noise gives the height, lakes fill the low ground, and rivers run downhill from the peaks to a coast or a lake.
- R-186-02  Given the height and the water, When biome bands are set, Then they follow elevation and latitude and read as noise-separated regions, never as rings around a point.
- R-186-03  Given the generator, When it runs, Then the terrain is generated from the seed and accounts for the layouts of S-112, and the places of S-191 are found on it by rule (R-191-10).
- R-186-04  Given the same seed, canvas and inputs, When terrain is generated on any platform, Then height, water, bands, slopes and ground flags are byte-identical, with no fast-math, no platform transcendentals, no hash-order input and no wall-clock input, and the formula that decides play runs in the C simulation.
- R-186-05  Given the terrain, When the simulation holds it, Then it holds a coarse grid of what affects play (the layer of the ground, slopes, water and density), the same on every machine; finer detail is worked out from the seed and stored nowhere (S-194).
- R-186-06  Given two different seeds, When their maps are generated, Then they differ in the shape of the land (a continent, an archipelago, a river delta) and not only in dressing.
- R-186-07  Given a mission whose map is generated, When the player reaches the match, Then the player has never waited on a loading screen for the landscape for longer than 5 seconds (Westley, 2026-10-03); terrain generation may start while the player is in the mission brief.

Inputs: seed; canvas (S-195).
Outputs: height, water, rivers and biome bands; the coarse grid.
Open flags: none.

### S-187 — Landforms and climate
As a commander, I want mesas, canyons, island chains and fjords and not only rolling hills, so that every map is its own place and the variety has a Minecraft feel.

Rules
- R-187-01  Given a seed, When a map's climate and landform are chosen, Then both are derived from the seed alone, and the simulation's region record is unchanged (Westley, 2026-10-02, "derived from seed for now").
- R-187-02  Given the landform, When terrain is generated, Then large features with their own shape are blended into the layered noise, because noise alone gives only rolling hills All six ship: canyon, mesa, caldera, fjord, terraced massif and island chain (Westley, 2026-10-03). The prototype may build them in batches.
- R-187-03  Given the climate and landform, When the region's environmental trouble (the storm, the flood, the dust) is chosen, Then it is derived from the seed in the same way; how the trouble travels across the map is E-15 S-130.
- R-187-04  Given any generated land map, When it is read as a whole, Then landscape variety is packed into it, which is the condition on which the canvas stays at today's sizes (R-166-05). The prototype's builder picks the measure (a count of distinct biome bands and landforms, or the spread of height and biome across the canvas) and, when presenting, asks Westley whether the variety is the one he had in mind; his judgment decides it (Westley, 2026-10-03).
- R-187-05  Given the region's stability and capacity, When terrain is flavored, Then they act as S-115 describes today, on interference, hazards and cover, and do not decide the landform.

Inputs: seed.
Outputs: climate and landform in the map seed; landform shapes in the terrain.
Open flags: none.

### S-188 — Height becomes the five layers
As a commander, I want a mountainside to be a stack of layers that an attacker has to climb, so that height is play and not paint.

Applies to land maps. Space maps: R-188-05 and S-246.

Rules
- R-188-01  Given the terrain height, When bands are set, Then the five height bands are fitted to the map, stretched between its lowest and highest ground, so every land map has ground on all five layers.
- R-188-02  Given any position, When its layer is read, Then it is the band the ground there falls in, and a map always has five layers (E-01 Q-001-01).
- R-188-03  Given a land map, When the landscape engine hands the terrain to the layer system, Then the terrain holds at least a minimum variance in height (Westley, 2026-10-03), so that every map has ground on layer 5 and every layer step is a real height difference; the layer system fits the bands only on terrain that meets it. A layer step that is only a meadow slope is a defect of the landscape generation. A detector measures the variance (the minimum is DRAFT-height-variance-min, an Architect draft tuned by the landscape lab; Westley, 2026-10-15, Q-188-01 closed) and ships with a positive control, a map built with less variance than the minimum that the detector must flag.
- R-188-04  Given bands fitted per map, When a layer step has a different height on each map, Then the numbers written for a standard step in E-01 (time to change layer, how much worse sight is across layers, which layers a type may fire at) scale with the height of the step [Q-166-04: how each number scales, which the skill lab measures].
- R-188-05  Given a space-era map, When layers are read, Then each layer is an open-or-blocked sheet (S-246; E-01 R-001-04), asteroids and stations are the things that block it where plates stand, and the areas between are open; height bands, ground flags, slopes and strongpoints apply to land maps only.
- R-188-06  Given an archetype whose fight is compact (Suppression and Counterinsurgency, the small category of E-10 R-073-01), When its map is generated, Then the canvas is drawn from medium and large like any other, with five fitted layers (R-188-01); the player's home base is extensive and impressive and takes a significant portion of it, though it is mostly unused; the objective, the resources and the base sit closer together than on other archetypes; and the rest of the canvas is ordinary ground with nothing placed on it (Westley, 2026-10-03).

Inputs: terrain height.
Outputs: band heights (S-190).
Open flags: Q-166-04. The fitted-band rule is tested in the layer lab before it is fixed.

### S-189 — Ground you cannot cross
As a commander, I want some ground to be too steep to walk, and slopes to be the ways between layers, so that the lay of the land decides where an army can go.

Applies to land maps; the space kit is S-246.

Rules
- R-189-01  Given the terrain, When ground is shaped, Then it is a mix of benched ground (wide shelves with steep risers at each band edge, so a layer boundary is a visible cliff or ramp) and natural ground (ground that rolls freely), in a ratio drawn per map from the seed (Westley, 2026-10-03). The spread of the ratio is checked in Westley's visual pass on a prototype.
- R-189-02  Given a section whose ground is too steep, When a walking unit is routed, Then it cannot cross it and the route grid treats it as blocked (E-13 R-097-01). One steepness limit holds for every walking unit: ground steeper than 35 degrees is impassable (Westley, 2026-10-04, "35 degrees", after his visual pass of land mockup passes 4 and 5).
- R-189-03  Given ground that jumps a band, When it is steep, Then it is a cliff and walking units cannot cross it. When it is a natural ramp, a pass, a switchback road, stairs or a built lift, it is a slope, and walking units change layer there and nowhere else (E-01 R-001-06, R-001-07).
- R-189-04  Given the map, When the generator finishes, Then it has listed every slope for E-01 (S-190).
- R-189-05  Given a ground era, When the map is checked, Then a walking route over slopes exists between the two sides' bases, between each base and its objective, and to every band. Given a flying era, Then no walking route is required (Westley, 2026-10-03).
- R-189-06  Given a player has a unit selected, When the cursor hovers ground that is too steep to cross, Then the cursor shows a small (X) (Westley, 2026-10-03: his current thinking, subject to change; a client element, E-16).
- R-189-07  Given a generated ground-era map, When the landscape engine is tested, Then every strategically important place (a base, the objective, an economic site, every vantage point and every strategic point the layout names) has at least two separate walking routes to it, one wide enough for a small army and one wide enough for a big army (Westley, 2026-10-15; his 2026-10-03 "unreasonably difficult to reach" made into a measure; vantage points and strategic points added by Westley, 2026-10-21), and a seeded roll decides how many routes above two there are and how wide each is. The widths (DRAFT-route-small-width, DRAFT-route-big-width, in unit radii of the largest walker) and the roll's range (DRAFT-route-max-count) are named drafts set by playtesting, never by a worker; the map check ships with a positive control, a map with one route that it must flag.

Inputs: terrain; bands.
Outputs: cliffs and steep ground in the route grid; the slope list.
Open flags: none (Q-189-04 closed 2026-10-15; the route widths and count are playtesting drafts).

### S-190 — What the layer system gets from the ground
As a commander, I want the layers to follow the land under my units, so that where I can stand, climb and be hit matches what I see.

Applies to land maps; the space kit is S-246.

Rules
- R-190-01  Given the bands, When the layer mask is read at a position where the ground is on layer L, Then layers below L are blocked as solid rock, and L and the layers above it are open, so a flying unit may be on the ground's layer or any layer above and never below (E-01 R-001-04).
- R-190-02  Given any position, When the land flag is read per layer, Then a walking unit can stand only on the layer of the ground there, and on a slope on each layer it passes in turn (E-01 R-001-06).
- R-190-03  Given a slope, When it is output, Then it carries its position, its length, the layers it joins (adjacent or not), a bottom edge on the lower layer, a top edge on the upper layer, and the midline halfway along its length (E-01 R-001-06, R-004-06).
- R-190-04  Given the fitted bands, When the map is output, Then the five band heights are output, and E-01 R-010-01 reads them to draw a unit at its layer's height. This amends the note under E-01 Q-E01-01 that the elevation mapping is fixed globally.
- R-190-05  Given a cover obstacle on the map, When it is generated, Then it has a height in layers, and it blocks sight and fire only on the layers it reaches (E-01 R-007-01, R-007-02) Its height comes from the terrain feature it is (boulder, wall, tree line) and the era kit (Westley, 2026-10-03). Asteroid height on space maps stays with the held map content (Q-098-02). The radius cutoffs for the small, medium and huge looks of a cover object are the Architect's (Westley, 2026-10-07).
- R-190-07  Given any obstacle (cover, wall, ridge) on the map, When it is generated, Then it is kept narrow enough that a unit can walk around it to a clear line of fire (E-11 R-087-09), so an obstacle is a small annoyance and never a complete blocker (Westley, 2026-10-07: "if we make sure the landscape engine keeps obstacles to a minimum width, this will lead to obstacles being a small annoyance instead of a complete blocker") [Q-190-07: the width limit].
- R-190-06  Given the terrain, When a height is stored, Then it is stored continuous in world units, and the layer is derived from it by the bands.

Inputs: bands; slopes; cover obstacles.
Outputs: layer mask; land flag per layer; slopes; band heights; cover heights. E-01 reads them as its generator inputs.
Open flags: Q-190-07 (the width limit of R-190-07).

### S-191 — The places the game needs, found on the terrain
As a commander, I want bases, objectives and resources to sit where the land puts them, so that every map has its own shape of fight and a reason for every place.

Applies to land maps; the space kit is S-246.

Rules
- R-191-01  Given the terrain, When places are found, Then each is found by rule on the terrain, and a site is named afterwards for what it turned out to be (a valley floor, a mountainside, a river bend, an archipelago). The typed nodes of a layout (S-112) are requirements: the landscape engine is required to produce each at its zone (R-191-10). Places the layout does not name are found by rule.
- R-191-02  Given a land map, When places are found, Then each side has a base of operations (E-22 S-177), and the map has the objective. An attacker's base is the forward base from which he produces (E-22 S-177); supply lines are not an attacker-only rule (Westley, 2026-10-07).
- R-191-03  Given a land map, When economic locations are found, Then they are placed throughout the map (E-22 S-177), in numbers that scale with the players and the canvas (Westley, 2026-10-03) (the counts and the spacing come from the lab's layout search; Q-191-05 closed 2026-10-15).
- R-191-04  Given the objective, When the significant resources are placed, Then each side is at the same distance from the objective and from each significant resource, whatever shape the map takes (Westley, 2026-10-03: only those distances matter, and the more the shapes vary under that constraint the better), except where an archetype's slant says otherwise (Westley, 2026-10-03), so a side picks one or fights for both (E-22 S-177) (measured along the walking route; the tolerance and the slant per archetype come from the lab's layout search, stated as the measured worth of the situations each side holds, walking-distance difference as the interim unit; Westley, 2026-10-15, Q-191-05 and Q-191-09 closed).
- R-191-05  Given the terrain, When expansion sites are found, Then they are settlements that can be grown into further bases (E-22 S-175 and S-177).
- R-191-06  Given the terrain, When neutral settlements are found, Then a neutral populace lives in them and they are contested (E-22 S-177). They exist at mission start already grown, each to a seeded age, so that some are small and some big, their size scaled by the region's economy (E-22 R-177-06). They stand where the layout engine's economic locations are (R-191-03), never at hard-coded positions, and growth continues during play (R-193-01). Westley, 2026-10-13: "there should be existing (neutral) towns that contain resources (economy) out on the map, some small some big"; "the economy system needs to be built because that's what will induce 'towns', so let the economy system (layout engine) decide where those go, nothing hard coded."
- R-191-07  Given any place found, When it is typed, Then it is one of the nine types of S-113 or one of base of operations, expansion site, economic location, significant resource, neutral settlement or strongpoint (S-192).
- R-191-08  Given a base on ground that spans several bands, When an enemy goes for all of it, Then he has to cross every layer it spans (E-01 R-001-06, R-001-07).
- R-191-09  Given the places, When they are found, Then they are found on the same field map as the terrain and the density, with a scoring per kind of place (Westley, 2026-10-03). There is no separate prototype: Westley ruled on 2026-10-06 that the layout engine needs no prototype ("the data on what layouts work comes from the simulation engine", ROADMAP.md section 4b, layout-engine row); the first in-game shot of the places (lane P, play S-191) is the approval point.
- R-191-10  Given an archetype, When the map is generated, Then the layouts that fit it (S-112), including their moving objectives (S-118), and the terrain-first generation of S-186 to S-190 are both used, in this order (Westley, 2026-10-03, amended the same day): the layout engine gives the places and their widths; the landscape engine takes them as inputs and leans on them, and is required to produce each one (a choke the layout calls for is a real choke of the layout's width, a vantage a real peak); moving objectives follow walking routes on the terrain. A prototype of the layout engine, and of how the landscape engine reacts to it, is shown to Westley before integration. The archetype fixes the canvas size category, the objective type and the sides' roles, picks the layout, and also biases the landform (the bias per archetype comes from the lab's layout search; Westley, 2026-10-15, Q-191-05 closed).

Inputs: terrain; layouts; archetype; players; E-19 S-159's needs.
Outputs: typed places in the map seed; recon render.
Open flags: none (Q-191-05, Q-191-08, Q-191-09, Q-191-10, Q-191-14 closed 2026-10-15).

### S-192 — Strongpoints, chokes and the places the layer plays need
As a commander, I want ways up and down the land that I can hold, narrow places to fight over and high ground to take, so that the plays the layer system offers have somewhere to happen.

Applies to land maps; the space kit is S-246.

Rules
- R-192-01  Given the slopes between height bands, When strongpoints are placed, Then they stand at those slopes, so holding one holds the way up or down and gives production on that band (E-15 S-218, E-15 S-126). The count and the owner split are R-126-01's, placed on the best slopes, and as many as there are where the relief gives fewer slopes than the count (Westley, 2026-10-03) [Q-192-04: whether a layout's reinforcement-structure nodes are these strongpoints].
- R-192-02  Given the terrain, When chokes are found, Then each is where a pass, a bridge or a gate must be, at a crossing of a cliff, of water or of a wall. A choke the layout calls for has the layout's width (R-113-05; Westley, 2026-10-03: the layout engine decides the width) (the numeric width comes from the lab's layout search; Q-191-05 closed 2026-10-15).
- R-192-03  Given the terrain, When vantages are found, Then each is on a real peak. On a ground era every vantage is reachable on foot by a slope, with at least two routes (R-189-07; Westley, 2026-10-21), and about 30 percent of the peaks that are not vantages may be unreachable on foot, which is natural (Westley, 2026-10-03; R-113-04's "reachable from staging and every spawn point" is rewritten to this).
- R-192-04  Given a generated land map, When the plays of the layer system are listed (hold a choke, hold the top of a slope past its midline, fight from behind tall cover), Then the map offers each, because every layout declares the plays it offers, with node kinds for a slope top and for a tall-cover place beside the chokes and vantages it has, and no layout offers none (Westley, 2026-10-03). The terrain adds chokes, vantages and strongpoints by rule only where the layout names none of that kind. The library is audited before it is implemented, and archetypes are probably paired with layouts (S-112). Every layout offers at least one map-dependent play each for landscape, layers and enemy position, checked on the finished terrain against the lab's play table (Westley, 2026-10-15, Q-191-08).
- R-192-05  Given the terrain, When raids and shipments reach a base, Then they come along lanes the terrain sets (E-22 S-168 and S-174, E-22 S-176). Both ways are built behind a switch: the generator outputs the lanes, or they are found at play from the route grid; playtests choose (Westley, 2026-10-03).

Inputs: slopes; terrain; places.
Outputs: strongpoints, chokes and vantages as typed places.
Open flags: none.

### S-193 — Settlements that build themselves
As a commander, I want cities and bases to rise from scaffolds in waves, spread along the land, climb cliffsides and reshape around what I place, so that the base I fight over is a spectacle to watch being built.

Rules
- R-193-01  Given a map, When population density is set, Then it is a growing field on the same field map the landscape uses, and it spreads over the map a little at a time. It is shaped by water, slope and the settlement core's position (the layout engine's economic locations and bases, R-191-03, R-191-06), so districts follow rivers, coasts and contour lines and never form rings, and walls follow defensible ground. The field's spread is also multiplied by seeded noise of the terrain generator's family with its own salt, so the growth front is ragged from its first ring and a town is never a square or an octagon at any age (Westley, 2026-10-13: "the town is supposed to follow the biome engine in its stochasticity (remember it's a *sister* system)"). Lanes follow contour lines and rivers (R-193-09), not a fixed grid, and lots jitter and turn as the approved mockup does.
- R-193-02  Given difficult terrain, When density reaches it, Then the field never gives up and the city adapts by placing buildings in wild locations, such as inside a cliff, underneath a waterfall or on a steep mountainside. Difficult ground changes what gets built, not whether anything is. An opening in rock is cosmetic only: the layer mask and the land flag are unchanged (Westley, 2026-10-06).
- R-193-03  Given a building the player places, When it claims its footprint, Then the self-built pieces under it are cleared and the pieces around it are refilled. Where it may be placed is E-22 S-168.
- R-193-04  Given an event, When it happens, Then growth comes in a wave, and a whole street can go up at once. The events that start a wave are a shipment arriving, an expansion being founded, a season turning, a capture and a battle's end (Westley, 2026-10-06).
- R-193-05  Given a lot, When the density at its cell passes a threshold, Then the lot rises through its stages, starting under construction, with a construction animation between stages. There are five stages: empty, staked, scaffold, small and large (Westley, 2026-10-06) (the thresholds come from the lab's layout search; Q-191-05 closed 2026-10-15).
- R-193-06  Given damage to a lot, When it is applied, Then the stages run backward toward rubble, and rebuilding speed follows the civilization's economy, and a lot knocked back by an area hit rises again 200 ticks (10 s) after its last hit (decided 2026-09-22; Architect 2026-10-10).
- R-193-07  Given any mode, When a base is on screen, Then it is a spectacle: buildings start under construction and rise, expansions are made, and density changes over time (E-22 S-179). The self-built pieces are mostly cosmetic and the economy is run by rules (E-22 S-179), and the city grows during a mission.
- R-193-08  Given the density field, When the game runs, Then it is in the simulation, and dense districts slow units and give cover [Q-193-04: how much dense districts slow units; Q-193-05: how much cover they give; both parked until fights have been run in the simulation (Westley, 2026-10-06)].
- R-193-09  Given a settlement, When armies and units cross it, Then there are always natural paths through it, so that the slowing of dense districts is never annoying to the player. The generator leaves open streets along the contour lines and rivers by rule (Westley, 2026-10-06).

Inputs: terrain; places; events; the player's buildings (E-22 S-168).
Outputs: density field; lot stages; self-built pieces on screen.
Open flags: Q-193-04, Q-193-05 (parked).

### S-194 — One world at every zoom
As a commander, I want the world to stay one continuous place from a single unit to the whole battlefield, so that scale is felt and never loaded.

Rules
- R-194-01  Given the seed, When detail is needed, Then it is sampled from the same formula more finely, and nothing finer than the simulation's coarse grid is stored or sent.
- R-194-02  Given the camera coming down, When terrain is drawn, Then tiles subdivide gradually, with no pop and no loading break: a few large tiles give the shape of the land from high up, and small tiles give rocks and ledges close in.
- R-194-03  Given distance from the camera, When buildings and units are drawn, Then they step down: full models and scaffolds with people up close, simple shapes drawn in bulk farther away, district-colored blocks farther still, and the map view with unit groups as icons.
- R-194-04  Given the zoom, When it moves, Then it is one continuous zoom from a single unit to the whole battlefield, on the camera's height-above-ground floor (E-16 S-103 R-103-03).
- R-194-05  Given the map view, When the player zooms out, Then the zoom stops at the battlefield's map view (E-16 S-161), and the galaxy view stays outside a mission.
- R-194-06  Given the coarse grid and the fine formula, When they describe the same ground, Then they agree where play depends on it [Q-194-01: how closely, and which one wins a disagreement]. Research is needed before this is designed: how to keep the backend, what is really happening in the game, true to the ground (the simulation's grid wins) while keeping the player's experience, without the heavy snapping that brings (Westley, 2026-10-06).

Inputs: seed; camera height.
Outputs: terrain tiles; pieces at each level of detail.
Open flags: Q-194-01.

### S-195 — Canvas for the match
As a commander, I want bigger matches to have bigger maps, so that more teammates mean more to do, more resources and more enemies.

Rules
- R-195-01  Given a match of 4 to 6 players, When the canvas is chosen, Then it is 64,000 wu (Westley, 2026-10-02), fixed: the region modifier of R-116-02 does not apply at this size (Westley, 2026-10-03).
- R-195-02  Given a match of fewer players, When the canvas is chosen, Then it keeps today's sizes (R-116-01), with the largest at 32,000 wu (Westley, 2026-10-03). The code constant `OM_CANVAS_SIZE_RANGES_LARGE_HI` (28,000), R-116-01 and ALG-70 still say 28,000 and change in a contract piece when the canvas work is built.
- R-195-03  Given any canvas, When terrain is generated, Then it holds the five fitted bands (S-188) and the landscape variety of S-187. The canvas is not shrunk to fit them.
- R-195-04  Given a larger canvas, When a mission runs, Then there is more to do, more resources and more enemies (DECISIONS H7), the economic locations scaling with the players and the canvas (R-191-03). Each player is a sub-commander and each pair a sub-civilization (E-19 S-159).

Inputs: archetype; players in the match; region.
Outputs: canvas size in the map seed.
Open flags: none.

### S-196 — One field map, two kits
As a commander, I want a land and a space era to look different over the same kind of map, so that the same game reads as two worlds.

Rules
- R-196-01  Given a map, When the generator finishes, Then it has produced a field map: zones with borders between them and continuous gradients over the canvas. It never names a rock, a tree or a house.
- R-196-02  Given the field map, When it is drawn, Then two mappers read it: the landscape mapper reads obstacle, cover, elevation and interference and places terrain pieces from the era pack, and the city mapper reads population density, wealth and age and places building pieces from the same era pack.
- R-196-03  Given the two mappers, When they place pieces, Then they use one placement engine, so a border is a coastline, a cliff or a city wall depending on the mapper and the kit, and a crossing of a border (a bridge, a gate, a pass) is the same thing as a choke.
- R-196-04  Given the era pack, When a kit is chosen, Then a land era and a space era each have one, with the same units and rules and different landscape and visuals (DECISIONS H2). Placeholder pieces are acceptable until models arrive from the offline asset pipeline (E-21), and a missing prefab uses a placeholder.
- R-196-05  Given a biome, When it is chosen, Then it decides look through the theme pack, and any play effect arrives through the existing obstacle, cover and interference fields.

Inputs: field map; era pack.
Outputs: pieces on screen; the same field map for the sim.
Open flags: none. The space-era landscape itself is not designed (Q-166-02).

### S-197 — A slanted map is still fair
As a commander, I want a map that favors the defender to still be one I can win, so that a loss is mine even when the odds were stacked.

Rules
- R-197-01  Given a generated land map, When the fairness evaluator runs, Then it scores the derived terrain, its places and any layout it accounts for on route count, travel time balance, vantage accessibility balance and hazard symmetry as S-117 does, and logs the score with the seed.
- R-197-02  Given a map the situation slants, When the score is read, Then the acceptable range accounts for the slant, such as a defender's better position (E-22 S-177), and the range is centered on the slant the situation gives (Westley, 2026-10-03).
- R-197-03  Given the derived map, When it is checked, Then the hard constraints of R-117-03 hold on it: no side's every approach is blocked while the other's is clear, and every vantage that is reachable on foot is reachable by both sides (R-192-03: every vantage is reachable on foot; only peaks that are not vantages may be unreachable).
- R-197-04  Given the launch build, When a score is outside the range, Then it is logged, and whether a map is regenerated is a design-phase decision (Q-113-01, closed: logger only until the generator is tuned).

Inputs: map seed; the situation (E-02, E-10).
Outputs: fairness log.
Open flags: none.

### S-246 — The space landscape

As a commander in a space era, I want each layer of the map to be a sheet of open and blocked space with real obstacles filling it, so that the layers are places to fight in and not planes.

Design decided 2026-10-07 and approved as written the same day (Westley; `docs/northstar/research/space_landscape/README.md`, the approved space kit). Not scheduled for building: Westley polishes and approves the prototype before the full build workflow.

Rules
- R-246-01  Given a space-era mission in the beta, When it is set up, Then the map has a generated field: each of the five layers is an open-or-blocked sheet (E-01 R-001-04), like ice over open water, and the generator is ported into the simulation as the land one was (Westley, 2026-10-07; Q-STAGE3-03).
- R-246-02  Given the space kit, When it is drawn, Then it follows the approved prototype with one polish: the blocked space is filled across layers with real placeholder meteors instead of one plane per layer, and the layers are visibly separated.
- R-246-03  Given a mission, When the simulation sends the map, Then it sends the cell masks and the plate polygons once per mission, and the client draws the layers as stacked 3D sheets from them (Q-166-06, Q-166-07).
- R-246-04  Given a unit below an upper layer that hides it from the camera, When the player looks, Then a simple vision tube lets the player see through the covering layers around the cursor or selection, with a small effect that says so (Q-S3-01); the layer-visibility system of the layers prototype (`scenes/mockups/layers/`: with a unit sent to another layer, one circle moves with the unit and a second sits at the exact height of the layer it is moving to) is the one the spec follows (Q-S3-02).
- R-246-05  Given an area units cannot leave, When a production building stands in it, Then in paired play that is the builder's problem, and in single player the rules place no production building in a section units cannot leave (Q-166-08).
- R-246-06  Given the space-era roster, When it is read, Then one unit type is purposefully smaller, a group that can break formation and pass gaps other ships cannot (an animation later); sizes are decided with the roster (Q-166-05).
- R-246-07  Given a mission in any era (Q-A17-01, Westley 2026-10-12: the home-base spawn holds for every era), When its field is generated, Then each faction's army spawns in a cleared pocket at its home base (the faction's anchor, where its first economy area and structures stand), the objective sits in its own pocket, and every pocket is carved reachable to the others, so an approach march separates the armies as open space did (Westley, 2026-10-09).
- R-246-08  Given the player's army at mission start in any era, When it is spawned, Then it is three groups, one large and two small, each in its own pocket on the way from the home base toward the objective, separated from one another, none more than 30 seconds' march from the home base at its slowest unit's speed, and bound to control groups 1 (the large one), 2 and 3 before the first frame; the split and the separation are drafts the spec names (Westley, 2026-10-12).
- R-246-09  Given a space mission, When the field is generated, Then the layout engine's request for the mission sets the asteroid density (the kit situation names it), and the landscape engine conforms to that request; no default density and no per-region class sets it (Westley 2026-10-21, Q-246-02).

Inputs: the seed; the mission archetype; the era kit (kits/space.json).
Outputs: per layer the cell masks and plate polygons; blocked cells in the simulation's layer bits.
Open flags: none.

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Seed | Campaign | integer | |
| Archetype | E-10 | 10 archetypes | unknown fails |
| Players in the match | E-19 | 2 or 4 (6 is a desired future feature, E-19 S-241) | per E-19 S-159 |
| Region state | E-02 | fields and composites | |
| Climate, landform, environmental trouble | Derived from the seed (S-187) | per S-187 | |
| What the economy needs found (bases, sites, strongpoints) | E-19 S-159, E-22 | per S-191, S-192 | |
| Layout library and library hints | E-21 | per S-112 | the layout calls for places, the landscape engine must produce them (S-191 R-191-10) |
| Era kit | Era pack | pieces per abstract type | missing piece uses a placeholder |

The layout library and library hints (E-21) stay an input of this epic. The terrain accounts for them as S-191 R-191-10 says.

## Outputs

| Output | Observable where |
|---|---|
| Map seed (seed, canvas, climate and landform, the layout's spine and drift specs) | Save file; T1 trace; replay |
| Terrain (height, water, rivers, biome bands) and the coarse grid | T1 trace; screen; replay |
| Five band heights | E-01 R-010-01; screen |
| Slopes, land flag per layer, layer mask | E-01 queries; E-13 route grid |
| Cover obstacles with their height in layers | E-01 sight and fire; screen |
| Places (bases, objective, economic locations, significant resources, expansion sites, neutral settlements, strongpoints, chokes, vantages) | T1 trace; recon render; E-22; E-15 |
| Density field and lot stages | Screen; the simulation (it slows units and gives cover, S-193) |
| Sampled fields (obstacle, cover, interference) | E-01, E-12, E-13 queries |
| Fairness score | T1 trace |
| Canvas size | Map seed |
| Rendered terrain at every zoom | Screen; map view (E-16 S-161) |

## Invariants

- Same seed and inputs, same map seed bytes and the same terrain, byte-identical on every platform.
- Every objective reachable from staging by 2 or more routes; on a ground era they are walking routes, on a flying era no walking route is required (S-189 R-189-05).
- No node outside the canvas.
- Map seed under 1 KB.
- Every land map has ground on all five layers.
- Every layer mask and land flag the generator outputs agrees with the terrain's bands.
- A map built from a layout keeps that layout's connectivity and its objective's drift, whatever terrain is generated around it (S-191 R-191-10).
- A settlement always has natural paths through it for armies and units.
- The formula reads no wall-clock and no hash order.

## Scale requirements

Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is escalated): generation of the spine-and-gradient layouts under 50 ms; field sampling under 1 µs per query with a precomputed grid at 100 wu. Terrain-first generation (noise, lakes, rivers and site finding, at canvases up to 64,000 wu) is not held to 50 ms: it runs off the match-start path, and the player never waits on a loading screen for it for longer than 5 seconds (R-186-07, Westley, 2026-10-03). Sampling stays at 1 µs.

## Look and behavior references

`docs/bible/references/E-17/notes.md`: shots 01 to 13 (the readable toy register, three city-scale concept images, the World of Warships map view, the Roblox terrain and island generators). The mockup in `scenes/mockups/landscape/` (`field_map.gd`, `placer.gd`) shows what the generator computes: continuous height, slope, water and rivers, biome zones, a city core and density districts, and borders traced as coast, cliff and wall with their crossings. It is a mockup, not the game: it runs in GDScript with the engine's noise, finds one core, computes density once and places everything at once.

## Ways this could be wrong

- Bands fixed in height instead of fitted, so a flat map has no layers or a layer step is a meadow slope.
- A place stamped on flat ground with the terrain not accounting for it, so cities are rings on flat ground.
- Terrain generated without accounting for the layout, so a layout's chokes, flanks and moving objectives land on ground that does not fit them.
- Seeds that differ only in dressing, not in the shape of the land.
- The formula using the engine's noise or a platform transcendental, so the sim and the client disagree.
- The coarse grid and the fine formula disagreeing about which layer ground is on.
- Ground filled for the layer it is on but not for the layers below it, so a unit stands inside rock.
- Significant resources placed beside the objective instead of opposite it.
- Strongpoints placed where no band slope exists.
- A city that stops at a cliff instead of adapting to it.
- Dense districts that slow units with no natural path through a settlement, so crossing one is annoying.
- A strongpoint or base on ground no walking route reaches.
- Flavoring multipliers unbounded, so a dead region has no walkable space.
- Fairness evaluator rejects and silently regenerates without logging the seed.
- Drifting node moves but the objective zone stays.

## Open ambiguity flags

Q-165-01, Q-166-02, Q-190-07, Q-166-04, Q-193-04, Q-193-05, Q-194-01. Details in `docs/northstar/ambiguity_register.md`.

## Depends on

- E-01 (consumes slopes, land flags, the layer mask, band heights and cover heights; its elevation mapping reads S-190), E-02 (region state for flavoring), E-10 (archetype and canvas category), E-12, E-13 (consumers of sampled fields and the route grid), E-15 (strongpoints, reinforcement structures and travelling weather), E-16 (camera floor, map view and continuous zoom), E-18 (era kit), E-19 S-159 and E-22 (bases, economic locations, significant resources, expansions, strongpoints and where the player places buildings), E-21 (asset pipeline for models; the layout library and its hints stay an input, which the terrain accounts for).
- Port parity requirement P4 (map content, `docs/northstar/plans/2026-10-02-tactical-port-parity-requirements.md`) waits on this epic's terrain-first design.

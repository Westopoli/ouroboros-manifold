# Landscape design phase (rung P2)

**Approved 2026-10-06** (Westley: "Landscape engine is also approved"), after the markers below. **2026-10-05, with markers.** Westley, on pass 6b (branch `push/proto-land-iter`), verbatim: "land mockup is fine as long as it's understood that the layout engine underneath it is flawed at the moment, it's close to what I want just not quite there on the scale/size. That's for later polish though, approved for now with those markers." Markers: the layout engine under it is flawed and is being redesigned (`docs/northstar/research/layout_engine/`); scale and size are not yet right (relief stays about 4,500 wu whatever the canvas) and are later polish. The approval opens planning of the ground substrate in the C sim (height field, ground flag per layer, walkable ground, slopes); the same day he relaxed "layout before landscape" for that substrate.

Opened 2026-09-21. This is the design phase decision D3 promised (`harness_defects_2026-09-17/DECISIONS.md`): Westley takes part in designing the biome and landscape generation system and its sister system before anything is built, and approves a Godot mockup before any test is authored. This file records the questions, Westley's exact answers, and the design as it firms up. When the mockup is approved, the design moves into the E-17, E-16 and E-19 epics and this file becomes history.

Facts the phase started from (explorer sweep, 2026-09-21): no biome or terrain-type concept exists anywhere in the bible or code; a map today is typed spine nodes plus four continuous fields (obstacle density, cover density, elevation, sensor interference) plus per-layer blocking masks and asteroid cover clusters; the Godot renderer draws boundary slabs, debug gradient discs, node markers and scattered props, with no ground mesh, heightmap, tiles or noise. The bible already says "the theme pack decides whether an obstacle is an asteroid or a mountain." Only the Settled Reach (space) era exists; past and present eras are unnamed (Q-147-01). Every visual reference attached to E-17 and E-18 is planetary.

## Questions and answers

| # | Question | Candidates | Westley's answer (2026-09-21, verbatim) |
|---|---|---|---|
| 1 | Setting: is the P2 mockup a space battlefield, a newly defined ground era, or one abstract battlefield reskinned per era? | (a) space, matches what exists; (b) ground, define a ground era now; (c) one abstract battlefield reskinned per era, mockup shows both skins over the same map | "1: C, everything we're building should be era-agnostic to prove they can be used cross-era." |
| 2 | What does a biome do? | (a) look only; (b) look plus play (movement, sight, cover, combat); (c) look now, play effects later through the existing four fields | "2: C" |
| 3 | Scale and shape of one tactical battlefield: size relative to the screen, and how a map gets its layout | Size: (a) one screen; (b) several screens with pan and minimap. Layout: (a) hand-authored skeletons with procedural dressing; (b) fully generated from seed; (c) skeletons now, count growing | "3: B but more like 20-30x, but zoomability is a big factor, you can zoom way down to the micro level to micro units, but the whole battle happens on a much larger scale, and players should be able to give basic movement commands from that level to groups of units. Think "map" view, like from World of Warships." (World of Warships map-view screenshot attached: `references/E-17/E-17-8-wows-map-view.png`.) Layout method not yet answered. |
| 4 | What is the sister system, and where do cities appear? | (a) cities and buildings on the tactical battlefield, same placer; (b) strategic-layer spectacle only (S-159 R-159-02 as written); (c) both, one placement engine | "4: Oh yes, a: cities will be like your homebase long term, something you'll need to protect. Every "fight" at the moment is happening at a city in a civilization, the economy/buildings will be the city itself. I'd like it to be expansive, huge scale, three reference photos (save these) [...] - this will be the economic aspect, but the player doesn't build everything, just pieces (to be designed), the biome generation system and the "population density/city layout" system are very similar in what they map out, just different visuals really, we need the "generation" system to map out "borders" and gradiants, to be used by both systems: hence the "sister" term." |
| 5 | What mockup makes Westley say "yes, that's it"; reference games; camera angle | open | "5: we're going for age of empires online, playful bright animations, class RTS camera angle for now (camera system to be designed)." |
| 7 | What is a city in the Settled Reach, given the mockup must show one field map under two skins? | (a) station or habitat cluster on asteroids: walls are hull sections, coast is vacuum, bridges are docking spines; (b) planetary colony under a dome; (c) defer the space skin, prove reskinning with two ground skins | "Settled reach city: A, placeholders are ok for now, model generation will happen later. - greek skin, settled reach skin." |
| 6 | Where does "biome" live? | (a) theme pack only: sim keeps producing abstract fields, biome is the mapping from field values to authored pieces, the same mapper fed population and wealth places city pieces; (b) in the sim, terrain type per cell affecting play; (c) (a) now, door open for (b) per era later | "6: C" |

References saved 2026-09-21 in `docs/bible/references/E-17/`: `E-17-5-macro-city-a.png`, `E-17-6-macro-city-b.png`, `E-17-7-macro-city-far.png` (Westley's three "ultra high altitude RTS tactical camera view" city images), `E-17-8-wows-map-view.png` (World of Warships map view). Rows for each are in `references/E-17/notes.md`.

## Design as it stands

Nothing below is bible text yet. It becomes rules only after the mockup is approved.

**One generator, two skins, one output.** The generator produces a *field map*: zones with borders between them, and continuous gradients over the canvas. It never names a rock, a tree or a house. Two mappers read the same field map:

- the **landscape mapper** reads obstacle, cover, elevation and interference and places terrain pieces from the era pack;
- the **city mapper** reads population density, wealth and age (from the E-02 region state) and places building pieces from the same era pack.

Both mappers use the same placement engine, so a border is a coastline, a cliff or a city wall depending on which mapper and which era pack, and a crossing of a border (bridge, gate, pass) is the same thing as today's chokepoint. This keeps the sim untouched and era-agnostic (answers 1, 6) and makes "biome" a theme-pack concept (answers 2, 6).

**The city is the battlefield.** Every fight happens at a city; the city is the player's long-term home base and the thing being protected (answer 4). Today's spine vocabulary maps onto it: objective is the city core, staging is the fields outside the walls, chokepoints are gates and bridges, vantages are the hill or acropolis, hazard anchors and interference sit in the wild zones. Mission archetypes (E-10) keep their meaning; the city gives them a place.

**Scale.** The battlefield is 20 to 30 screens at the classic RTS zoom, with three zoom bands: micro (individual units), tactical (today's RTS view), and map view (World of Warships style: unit groups as icons, basic movement commands to groups from that level). A medium canvas today is 12,000 to 20,000 wu square with a 200 wu formation width; at a tactical view roughly 3,000 wu wide that is already about 25 screens, so the sim's canvas sizes need no change. The camera system is to be designed (E-16 S-103 currently says fixed top-down interim; the map view and group commands from it are new behavior).

**Register of the reference images.** The three city images pin: expansive walled cities on terraces with dramatic elevation (cliffs, waterfalls, aqueducts), water as a border (coast, river) crossed at bridges, farmland and forest as the biome outside the walls, distant snow mountains selling scale, armies visible as small blocks at that altitude, and the playful bright Age of Empires Online register throughout. The World of Warships image pins the map view: a grid, terrain as simple shapes, unit groups as icons with drawn movement arrows, objective circles.

## Open questions from this round

- **Layout method** (question 3, second half): hand-authored skeletons with procedural dressing (today), fully seeded, or skeletons whose count grows over time. Interacts with Q-112-01 and Q-113-01.
- **What pieces the player builds in the city.** Westley: "the player doesn't build everything, just pieces (to be designed)." New flag under S-159.
- **Map view and group commands** are new client behavior not in E-16; needs a story and reference.
- **Whether the city grows during a mission or only between missions** (the E-02 economy ticks per region year, a mission is minutes). Interacts with Q-159-02.

**Two skins for the mockup** (answer 7): a Greek skin (the classical city of the reference images) and a Settled Reach skin (a station or habitat cluster on asteroids: walls are hull sections, coast is vacuum, bridges are docking spines). Placeholder blocky pieces in both; real models come from the offline asset pipeline (E-21) later.

## Mockup review 1 (Westley, 2026-09-21)

Westley flew the mockup. Verbatim: "Different seeds don't differ (regenerate doesn't seem to do anything but freeze the game for a little bit). kits swapped cleanly and quickly. Camera did pan correctly but the "map" lines just pop up on screen withuot moving as you zoom out, and given it's representing things on the map, not moving with the map looks very broken. I can't tell what the pieces slider does, slows everything down for a few seconds but doens't change anything much that I can see visually." After another regenerate: "this time there was a small difference".

Diagnosis and the second-pass list, for the mockup chat:

1. **Seeds barely differ, by spec.** The brief asked for one hand-authored skeleton with 3 percent jitter (R-112-03), so a seed changes only noise and dressing. Q-119-02 answered by demonstration: one skeleton reads as one map. Second pass: three or four skeletons (`skeletons/*.json`, same shape as `skeleton.json`), the seed picks one and jitters up to 8 percent; the HUD shows which skeleton. Fully seeded layout stays a flag.
2. **Map overlay drawn in screen space: bug.** Grid, contours, river, icons and arrows do not move with the terrain while zooming, the river runs off the canvas, contours float. Draw the overlay as world-space geometry on the ground plane (lines a few wu above ground, grid as a ground mesh) so it pans and zooms with the map; icons may stay screen-space but must be re-projected every frame from world positions.
3. **Stability slider unlabelled and its effect invisible: HUD bug.** Label it "Stability", debounce (regenerate on release), and make stability 20 versus 90 obviously different at tactical zoom (hazard and cover pieces, field rows).
4. **Regenerate freezes.** Budget was 500 ms; measure and report generation, placer and ground-mesh times separately; move the placer to MultiMesh buffer updates rather than node rebuilds if that is the cost.
5. **Look, unchanged from the first read:** cliff faces with real terrace height, a water plane for river and coast, a wall with thickness and a visible gate piece, backdrop mountains at the canvas edge, city core pieces that read as a core (temple and acropolis silhouettes larger than houses).

Kits swapped cleanly and quickly: the one-generator-two-kits claim holds and is not reopened.

## Mockup review 2 (Westley, 2026-09-21): concept approved, generator shape must change

Verbatim: "Protoptye has my go ahead (though, the elevation changes leave much to be desired, I imagined that the maps would be significantly larger, mountains would be huge and zoomability would have a "floor" that you can follow elevation changes with (halo wars had a mechanic like this), you stayed at your zoom "height" even when elevation changed, so scrolling to a higher elevation didn't require you to adjust your zoom level. Though Halo Wars had small changes, I want this game to have big changes for vastly different heights. City has distinct onion layers, if this is a prototype of the map generation/landscape system, I'd hoped it'd be much more dynamic, more variety, not simple circular cities, cities that follow rivers like reality or nestle in valleys/peaks, hillsides. Stochiastic seperations, very similar to the Roblox biome/landscape generation tool." Five reference images saved as `references/E-17/E-17-9..13*.png` with rows in `notes.md`.

What is approved: one generator, one field map, two kits, the placer, the city as the battlefield, three zoom bands, the map-view overlay. What changes before the epics are rewritten:

1. **Terrain first, waypoints second.** The mockup placed a hand skeleton and grew gradients around it, which gives circular cities on flat ground. The generator inverts: layered noise (Roblox-style, seeded) produces elevation, water (lakes and rivers flowing downhill from peaks to a coast) and biome bands that follow elevation and latitude; then the spine nodes are *found* on that terrain by rules (the city core at a river bend, a valley floor or a defensible hillside; chokepoints where a pass, a bridge or a gate must be; vantages on real peaks). Q-119-02 is answered by this: no skeleton library; the layout is derived from terrain, and fairness (Q-113-01) is checked on the derived spine.
2. **Big elevation.** Mountains are huge; height differences are large; five terraces stay for the layer system but the vertical scale is many times the mockup's 250 wu, and cliffs, valleys and peaks read at every band.
3. **Cities follow terrain.** Districts grow along rivers, coasts and contour lines, never as rings; the wall follows defensible ground; population density is shaped by water, slope and the core's position.
4. **Larger canvas.** Significantly larger than one city; a map holds a landmass-scale variety of biomes (E-17 R-116-01's canvas ranges are revisited in the rewrite).
5. **Camera floor.** The camera keeps its height above the ground under it, so scrolling up a mountain does not need a zoom change (Halo Wars), with the bands defined by height above ground. This is an E-16 S-103 rule.

## Next step

Mockup review 1's items 1-5 are fixed (2026-09-21): world-space map overlay (was frozen screen-space), border pieces now orient along the path with real cliff height (the actual cause of the dashed wall look, not spacing), decoration density retuned so the city reads over the fields, four skeletons with 8% jitter (was one at 3%), stability slider labelled/debounced with a real visible effect, and a measured perf fix (ground mesh dedup: regenerate ~1.49s -> ~0.84s; field_map generation is now the largest remaining cost). 14 review screenshots in `mockup/` are re-shot against all of this.

Pass 3 (2026-09-21) rebuilds the generator per review 2: terrain-first (elevation/water/biome from layered noise, spine nodes found on it, not placed), big elevation (peaks 3000-5000wu, was 250wu terraces), cities that follow rivers/valleys instead of forming a ring, canvas 24000wu default with a 16000/24000/32000 switch, and the camera's Halo Wars height-above-ground floor. Two real bugs found by looking at the first render (continent/detail noise frequencies effectively swapped; detail amplitude scaling with peak height instead of staying a fixed ripple) rather than by inspection. 20 screenshots in `mockup/pass3/` show three genuinely different seeds (a continent, an archipelago, a river-delta landmass) under both kits. Awaiting Westley's third look. On approval: epics E-17/E-16/E-19 are rewritten from this design and Stage 5 tests are authored.

## Pass 4: where walkers can go (2026-10-03, reworked)

Prototype under the Prototype gate, spec `docs/northstar/plans/archive/specs/2026-10-03-land-mockup-pass4-spec.md`, reworked after the Architect found the first version's steep view and walk view disagreeing. Greek and settled_reach kits; the space kit and `field_map_space.gd` are untouched (`qa/space.json` still runs clean). Screenshots: `mockup/pass4/` (1920x1080; `scripts/mockup_qa.sh run landscape scenes/mockups/landscape/qa/pass4.json <out> --res 1920x1080`). Numbers: `qa/pass4_numbers.json`.

**One blocked-ground mask.** Slope is the steepest height difference across a window `footprint` wu wide (four directions, centred on the cell; heights floored at sea level so a beach is not a cliff). Default footprint 300 wu (candidate: a formation is 200 wu wide), slider 100 to 600. A cell is too steep when its slope is over the limit. The steep view (T), the X cursor (U) and the walk flood (G) read this one array, and nothing but water blocks otherwise: a red cell is a cell the flood cannot enter. Cells are drawn as flat squares centred on the grid point so a painted cell is exactly a mask cell. Red is blocked at the limit; in the 35 view orange marks 30 to 35 (open at 35, blocked at 30).

**Other things built.** Band view (B): five equal-height layers between the lowest and highest dry ground, floors, step and land share per layer in the panel. Minimum relief slider (default 2500 wu, candidate; the generator already makes 2700 to 4800, so it only bites when raised; Westley owns it). Benched share drawn from the seed (15 to 65 percent of land) with a 0 to 100 override. Landforms batch 1 (M): mesa, canyon, island chain, from the seed or forced; caldera, fjord and terraced massif are batch 2. Variety measure: joint entropy of (layer, biome zone) over dry cells in bits, out of 4.64; it is a spread measure, one number, and does not see arrangement or count landforms. Terrain steepness slider (0 to 3, default 1): a multiplier on the detail noise only (80 wu amplitude), not on the continent or hill shapes. Keys: T steep 30/35/off, B bands, G walk, L limit 30/35, P ramps, U unit selected, M landform, R regenerate.

**Ramps (Q-189-01: a walking route reaches every band).** After landforms and benching, the generator floods from the city core at limit 30. For each layer that has land on the core's landmass but nothing the flood reaches, it grades a ramp: 28 degrees, 500 wu wide with 150 wu shoulders and a 400 wu level pad at the top, from the nearest reached ground that lets it climb at that grade up to the layer floor, over dry ground only. Gold in the walk view, counted in the panel; P turns cutting off. Islands across water stay unreachable. A ramp can fail to connect and is retried; seed 15 ends one layer short and seed 16 gets none. Ramps are thin corridors, so total reach barely moves while layers reachable jumps.

**Share of land too steep (% at 30 / 32.5 / 35), by footprint** (no ramps, pure terrain):

| seed | footprint 100 | footprint 300 | footprint 500 |
|---|---|---|---|
| 11 | 70/66/62 | 70/66/62 | 67/61/56 |
| 12 | 86/83/79 | 85/82/78 | 80/75/70 |
| 13 | 46/42/38 | 49/45/41 | 45/36/32 |
| 14 | 67/63/59 | 69/64/59 | 66/59/53 |
| 15 | 44/39/34 | 42/37/31 | 36/28/23 |
| 16 | 81/78/73 | 79/75/69 | 70/64/60 |

The footprint barely changes the picture (seed 11 stays near 70 percent at 30 degrees from 100 to 300 wu). The steepness is in the large shapes (3000 to 4800 wu of height on a 24000 wu canvas), not in single-quad noise.

**Per seed** (defaults: footprint 300, ramps on, detail x1):

| seed | relief wu | land % on L1..L5 | step wu | landforms | land share | core landmass (share of land) | variety bits | bench | too steep at 30 |
|---|---|---|---|---|---|---|---|---|---|
| 11 | 4524 | 40/27/23/9/1 | 905 | mesa, islands | 44% | 98% | 2.34 | 24% | 70% |
| 12 | 4775 | 79/19/1/1/0 | 955 | islands | 7% | 11% | 0.92 | 24% | 85% |
| 13 | 3088 | 40/31/17/11/1 | 618 | canyon, islands | 41% | 84% | 2.13 | 46% | 49% |
| 14 | 4813 | 49/19/14/12/6 | 963 | islands | 22% | 85% | 2.39 | 26% | 68% |
| 15 | 2693 | 66/22/9/2/1 | 539 | islands | 24% | 46% | 1.51 | 15% | 41% |
| 16 | 2722 | 74/15/7/3/1 | 544 | islands | 5% | 2% | 1.36 | 20% | 79% |

**Reach with ramps off and on** (reach % of land, layers reachable, peaks reachable of total):

| seed | off, limit 30 | on, limit 30 | off, limit 35 | on, limit 35 | ramps cut |
|---|---|---|---|---|---|
| 11 | 0.1%, L1, 0/17 | 1.2%, L5, 0/17 | 0.2%, L1, 0/17 | 1.5%, L5, 0/17 | 5 (696 cells) [2, 3, 4, 4, 5] |
| 12 | 0.5%, L1, 0/0 | 0.5%, L1, 0/0 | 1.0%, L1, 0/0 | 1.0%, L1, 0/0 | 0 (0 cells) [] |
| 13 | 12.1%, L3, 0/15 | 14.0%, L5, 1/15 | 18.5%, L4, 2/15 | 18.7%, L5, 2/15 | 2 (118 cells) [4, 5] |
| 14 | 1.8%, L1, 0/8 | 6.2%, L5, 4/8 | 2.2%, L1, 0/8 | 8.0%, L5, 4/8 | 4 (532 cells) [2, 3, 4, 5] |
| 15 | 5.7%, L2, 0/2 | 6.5%, L4, 0/2 | 7.3%, L2, 0/2 | 8.1%, L4, 0/2 | 3 (224 cells) [3, 3, 4] |
| 16 | 0.1%, L1, 0/1 | 0.1%, L1, 0/1 | 0.1%, L1, 0/1 | 0.1%, L1, 0/1 | 0 (0 cells) [] |

**Terrain steepness slider** (detail x0 / x1 / x2: too steep at 30 / 32.5 / 35, reach at limit 30, ramps on):

| seed | x0 | x1 | x2 |
|---|---|---|---|
| 11 | 69 / 64 / 60, reach 1.3% | 70 / 66 / 61, reach 1.2% | 70 / 66 / 62, reach 4.6% |
| 12 | 86 / 82 / 78, reach 0.7% | 85 / 82 / 78, reach 0.5% | 83 / 80 / 75, reach 0.6% |
| 13 | 48 / 45 / 41, reach 3.0% | 49 / 45 / 41, reach 14.0% | 51 / 47 / 43, reach 3.5% |
| 14 | 67 / 62 / 58, reach 7.2% | 68 / 63 / 58, reach 6.2% | 68 / 63 / 59, reach 7.3% |
| 15 | 40 / 34 / 29, reach 23.2% | 41 / 36 / 30, reach 6.5% | 42 / 37 / 31, reach 5.7% |
| 16 | 81 / 77 / 72, reach 0.5% | 79 / 75 / 69, reach 0.1% | 75 / 71 / 66, reach 0.8% |

**What the numbers say.** (a) 40 to 85 percent of land is over 30 degrees on every seed at every footprint and every detail scale: the pass-3 shapes are mountains, not rolling ground. (b) The city core is boxed in. Without ramps the flood from the core reaches 0.1 to 12 percent of land at limit 30. Seeds 12 and 16 put the core on a small landmass (11 and 2 percent of the land), so nothing helps there. (c) Ramps give every layer a route on seeds 11, 13 and 14 (5 of 5 layers) and 4 of 5 on seed 15; they are corridors, so reach rises by a few points and peaks reachable stay at 0 to 4 per map (seed 14: 4 of 8 at both limits). Nothing was tuned to the 70 percent peak figure. (d) A bug in the first version of this pass is fixed: terraces were dead flat, the lake finder read each bench as a basin, flooded it, and rivers then cut the core off. Benches now keep a 15 percent tilt and low coast ground is left unbenched. (e) Bench stripes still show as thin lakes next to the city on seeds 13 and 14 in the walk shots. (f) The camera clamp used a 16000 wu canvas on a 24000 wu map (it could not reach the south and east); fixed, one line in `hud.gd`.

### Pass 4 sweep (large-shape relief multiplier, 2026-10-03)

A new slider, large-shape relief x0.25 to 1.5 (default 1, printed in the HUD), multiplies the continent and hill height of dry ground and the heights and thresholds of the three landforms (mesa lift, canyon depth, island peaks); it is applied before bands are fitted and is separate from the detail slider. Sea depth, the south-edge drop, bench step (300 wu) and detail noise are not scaled. Sweep: seeds 11 to 16, ramps on, footprint 300, detail x1, landforms from seed, minimum relief 0 (the 2500 wu floor would stretch low-relief maps back up and hide the multiplier), canvas 24,000 / 32,000 / 48,000 (48,000 generates fine: 4 to 7 s a map). Limits 30 and 35 come from the same map; ramps are cut once at 30. Raw output: `scenes/mockups/landscape/qa/pass4_sweep.json` (per seed, per limit, plus averages); run list `qa/pass4_sweep_run.json`. Generate time is the generator only (ms, run alone on one machine). Screenshots: `mockup/pass4/sweep/` (seed 11, walk view, limit 30, ramps on, relief 1.0 and 0.5 at 24,000 and 48,000).

**Average over seeds 11 to 16** (relief wu is highest minus lowest dry ground; core landmass is the share of land on the core's landmass; layers and peaks are reachable from the core):

| canvas | relief x | limit | relief wu | too steep % | reach % | layers | peaks reach/total | ramps | core landmass % | gen ms |
|---|---|---|---|---|---|---|---|---|---|---|
| 24000 | 0.25 | 30 | 926 | 8.0 | 12.9 | 3.0 | 2.5/7.3 | 1.3 | 15 | 1083 |
| 24000 | 0.25 | 35 | 926 | 4.7 | 13.3 | 3.0 | 2.5/7.3 | 1.3 | 15 | 1083 |
| 24000 | 0.5 | 30 | 1846 | 31.5 | 9.9 | 2.2 | 1.2/7.3 | 2.7 | 18 | 1156 |
| 24000 | 0.5 | 35 | 1846 | 23.0 | 11.9 | 2.2 | 1.3/7.3 | 2.7 | 18 | 1156 |
| 24000 | 0.75 | 30 | 2824 | 51.3 | 3.0 | 2.5 | 0.8/7.3 | 3.0 | 28 | 1388 |
| 24000 | 0.75 | 35 | 2824 | 41.8 | 11.4 | 2.5 | 2.2/7.3 | 3.0 | 28 | 1388 |
| 24000 | 1.0 | 30 | 3769 | 65.2 | 4.7 | 3.5 | 0.8/7.2 | 2.3 | 54 | 1608 |
| 24000 | 1.0 | 35 | 3769 | 56.1 | 6.2 | 3.5 | 1.0/7.2 | 2.3 | 54 | 1608 |
| 32000 | 0.25 | 30 | 933 | 4.4 | 22.6 | 3.5 | 3.8/8.0 | 0.2 | 25 | 1804 |
| 32000 | 0.25 | 35 | 933 | 2.4 | 23.3 | 3.5 | 3.8/8.0 | 0.2 | 25 | 1804 |
| 32000 | 0.5 | 30 | 1852 | 21.1 | 23.0 | 2.8 | 4.5/10.0 | 0.2 | 30 | 1773 |
| 32000 | 0.5 | 35 | 1852 | 14.8 | 25.9 | 2.8 | 4.8/10.0 | 0.2 | 30 | 1773 |
| 32000 | 0.75 | 30 | 2828 | 38.1 | 20.4 | 3.2 | 3.2/9.7 | 2.2 | 50 | 2304 |
| 32000 | 0.75 | 35 | 2828 | 29.4 | 25.4 | 3.2 | 4.5/9.7 | 2.2 | 50 | 2304 |
| 32000 | 1.0 | 30 | 3772 | 52.4 | 7.6 | 2.7 | 1.2/10.3 | 1.2 | 30 | 2749 |
| 32000 | 1.0 | 35 | 3772 | 42.8 | 13.4 | 2.7 | 2.7/10.3 | 1.2 | 30 | 2749 |
| 48000 | 0.25 | 30 | 932 | 1.4 | 10.2 | 3.2 | 3.0/13.0 | 0.0 | 13 | 3974 |
| 48000 | 0.25 | 35 | 932 | 0.7 | 12.4 | 3.2 | 3.7/13.0 | 0.0 | 13 | 3974 |
| 48000 | 0.5 | 30 | 1850 | 10.2 | 22.2 | 3.0 | 6.0/15.0 | 0.2 | 25 | 3948 |
| 48000 | 0.5 | 35 | 1850 | 6.7 | 23.2 | 3.0 | 6.0/15.0 | 0.2 | 25 | 3948 |
| 48000 | 0.75 | 30 | 2828 | 22.0 | 21.5 | 3.5 | 7.0/14.8 | 0.7 | 47 | 4940 |
| 48000 | 0.75 | 35 | 2828 | 15.6 | 32.3 | 3.5 | 10.7/14.8 | 0.7 | 47 | 4940 |
| 48000 | 1.0 | 30 | 3773 | 34.1 | 10.8 | 1.8 | 4.3/14.8 | 0.0 | 15 | 6915 |
| 48000 | 1.0 | 35 | 3773 | 25.9 | 12.5 | 1.8 | 4.8/14.8 | 0.0 | 15 | 6915 |

**Per seed** (same columns; limit 30 and 35 rows):

<details><summary>144 rows</summary>

| seed | canvas | relief x | limit | relief wu | too steep % | reach % | layers | peaks reach/total | ramps | core landmass % | gen ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 11 | 24000 | 0.25 | 30 | 1128 | 8.2 | 5.73 | 4 | 3/16 | 8 | 9.7 | 1592 |
| 11 | 24000 | 0.25 | 35 | 1128 | 4.9 | 6.19 | 4 | 3/16 | 8 | 9.7 | 1592 |
| 12 | 24000 | 0.25 | 30 | 1177 | 16.4 | 12.18 | 2 | 0/0 | 0 | 12.8 | 898 |
| 12 | 24000 | 0.25 | 35 | 1177 | 10.6 | 12.56 | 2 | 0/0 | 0 | 12.8 | 898 |
| 13 | 24000 | 0.25 | 30 | 749 | 3.4 | 5.23 | 4 | 4/16 | 0 | 5.7 | 1110 |
| 13 | 24000 | 0.25 | 35 | 749 | 2.0 | 5.4 | 4 | 4/16 | 0 | 5.7 | 1110 |
| 14 | 24000 | 0.25 | 30 | 1202 | 5.0 | 44.85 | 5 | 8/8 | 0 | 52.5 | 985 |
| 14 | 24000 | 0.25 | 35 | 1202 | 2.7 | 46.43 | 5 | 8/8 | 0 | 52.5 | 985 |
| 15 | 24000 | 0.25 | 30 | 683 | 0.7 | 7.04 | 2 | 0/2 | 0 | 7.0 | 1017 |
| 15 | 24000 | 0.25 | 35 | 683 | 0.3 | 7.04 | 2 | 0/2 | 0 | 7.0 | 1017 |
| 16 | 24000 | 0.25 | 30 | 616 | 14.0 | 2.22 | 1 | 0/2 | 0 | 2.2 | 896 |
| 16 | 24000 | 0.25 | 35 | 616 | 7.5 | 2.22 | 1 | 0/2 | 0 | 2.2 | 896 |
| 11 | 24000 | 0.5 | 30 | 2176 | 34.1 | 0.06 | 1 | 0/16 | 8 | 0.2 | 1851 |
| 11 | 24000 | 0.5 | 35 | 2176 | 24.2 | 0.06 | 1 | 0/16 | 8 | 0.2 | 1851 |
| 12 | 24000 | 0.5 | 30 | 2376 | 54.5 | 0.16 | 1 | 0/0 | 8 | 16.1 | 1080 |
| 12 | 24000 | 0.5 | 35 | 2376 | 43.0 | 0.16 | 1 | 0/0 | 8 | 16.1 | 1080 |
| 13 | 24000 | 0.5 | 30 | 1526 | 19.0 | 0.48 | 3 | 0/16 | 0 | 0.6 | 1090 |
| 13 | 24000 | 0.5 | 35 | 1526 | 13.2 | 0.55 | 3 | 0/16 | 0 | 0.6 | 1090 |
| 14 | 24000 | 0.5 | 30 | 2405 | 27.0 | 50.31 | 5 | 7/8 | 0 | 82.6 | 1008 |
| 14 | 24000 | 0.5 | 35 | 2405 | 17.5 | 62.3 | 5 | 8/8 | 0 | 82.6 | 1008 |
| 15 | 24000 | 0.5 | 30 | 1353 | 8.4 | 6.32 | 2 | 0/2 | 0 | 6.5 | 1018 |
| 15 | 24000 | 0.5 | 35 | 1353 | 4.8 | 6.51 | 2 | 0/2 | 0 | 6.5 | 1018 |
| 16 | 24000 | 0.5 | 30 | 1240 | 46.0 | 2.03 | 1 | 0/2 | 0 | 2.0 | 886 |
| 16 | 24000 | 0.5 | 35 | 1240 | 35.5 | 2.03 | 1 | 0/2 | 0 | 2.0 | 886 |
| 11 | 24000 | 0.75 | 30 | 3329 | 56.9 | 0.09 | 1 | 0/16 | 8 | 0.3 | 2309 |
| 11 | 24000 | 0.75 | 35 | 3329 | 46.9 | 0.1 | 1 | 0/16 | 8 | 0.3 | 2309 |
| 12 | 24000 | 0.75 | 30 | 3575 | 74.8 | 0.13 | 1 | 0/0 | 0 | 1.2 | 901 |
| 12 | 24000 | 0.75 | 35 | 3575 | 65.5 | 0.15 | 1 | 0/0 | 0 | 1.2 | 901 |
| 13 | 24000 | 0.75 | 30 | 2307 | 35.3 | 1.6 | 5 | 0/17 | 7 | 69.3 | 1816 |
| 13 | 24000 | 0.75 | 35 | 2307 | 27.3 | 19.6 | 5 | 6/17 | 7 | 69.3 | 1816 |
| 14 | 24000 | 0.75 | 30 | 3608 | 51.9 | 8.42 | 5 | 5/8 | 3 | 84.6 | 1391 |
| 14 | 24000 | 0.75 | 35 | 3608 | 40.3 | 40.05 | 5 | 7/8 | 3 | 84.6 | 1391 |
| 15 | 24000 | 0.75 | 30 | 2023 | 24.3 | 7.6 | 2 | 0/2 | 0 | 9.3 | 1011 |
| 15 | 24000 | 0.75 | 35 | 2023 | 15.8 | 8.53 | 2 | 0/2 | 0 | 9.3 | 1011 |
| 16 | 24000 | 0.75 | 30 | 2105 | 64.4 | 0.08 | 1 | 0/1 | 0 | 1.7 | 897 |
| 16 | 24000 | 0.75 | 35 | 2105 | 54.8 | 0.16 | 1 | 0/1 | 0 | 1.7 | 897 |
| 11 | 24000 | 1.0 | 30 | 4524 | 69.8 | 1.17 | 5 | 0/17 | 5 | 98.0 | 2647 |
| 11 | 24000 | 1.0 | 35 | 4524 | 61.1 | 1.54 | 5 | 0/17 | 5 | 98.0 | 2647 |
| 12 | 24000 | 1.0 | 30 | 4775 | 85.1 | 0.52 | 1 | 0/0 | 0 | 10.8 | 914 |
| 12 | 24000 | 1.0 | 35 | 4775 | 77.6 | 0.97 | 1 | 0/0 | 0 | 10.8 | 914 |
| 13 | 24000 | 1.0 | 30 | 3088 | 48.6 | 13.97 | 5 | 1/15 | 2 | 83.9 | 1961 |
| 13 | 24000 | 1.0 | 35 | 3088 | 40.9 | 18.7 | 5 | 2/15 | 2 | 83.9 | 1961 |
| 14 | 24000 | 1.0 | 30 | 4813 | 67.7 | 6.25 | 5 | 4/8 | 4 | 85.0 | 1945 |
| 14 | 24000 | 1.0 | 35 | 4813 | 58.1 | 8.01 | 5 | 4/8 | 4 | 85.0 | 1945 |
| 15 | 24000 | 1.0 | 30 | 2693 | 41.3 | 6.47 | 4 | 0/2 | 3 | 46.2 | 1262 |
| 15 | 24000 | 1.0 | 35 | 2693 | 30.4 | 8.05 | 4 | 0/2 | 3 | 46.2 | 1262 |
| 16 | 24000 | 1.0 | 30 | 2722 | 78.9 | 0.08 | 1 | 0/1 | 0 | 1.9 | 916 |
| 16 | 24000 | 1.0 | 35 | 2722 | 68.6 | 0.08 | 1 | 0/1 | 0 | 1.9 | 916 |
| 11 | 32000 | 0.25 | 30 | 1156 | 4.6 | 35.42 | 5 | 9/14 | 1 | 42.9 | 2130 |
| 11 | 32000 | 0.25 | 35 | 1156 | 2.6 | 37.08 | 5 | 9/14 | 1 | 42.9 | 2130 |
| 12 | 32000 | 0.25 | 30 | 1177 | 9.9 | 4.95 | 2 | 0/0 | 0 | 5.8 | 1584 |
| 12 | 32000 | 0.25 | 35 | 1177 | 5.6 | 5.56 | 2 | 0/0 | 0 | 5.8 | 1584 |
| 13 | 32000 | 0.25 | 30 | 755 | 2.8 | 11.45 | 5 | 4/19 | 0 | 13.2 | 2009 |
| 13 | 32000 | 0.25 | 35 | 755 | 1.5 | 12.09 | 5 | 4/19 | 0 | 13.2 | 2009 |
| 14 | 32000 | 0.25 | 30 | 1201 | 2.5 | 72.65 | 5 | 10/10 | 0 | 75.2 | 1750 |
| 14 | 32000 | 0.25 | 35 | 1201 | 1.5 | 73.71 | 5 | 10/10 | 0 | 75.2 | 1750 |
| 15 | 32000 | 0.25 | 30 | 692 | 0.3 | 2.33 | 2 | 0/3 | 0 | 2.3 | 1783 |
| 15 | 32000 | 0.25 | 35 | 692 | 0.1 | 2.33 | 2 | 0/3 | 0 | 2.3 | 1783 |
| 16 | 32000 | 0.25 | 30 | 615 | 6.5 | 9.1 | 2 | 0/2 | 0 | 9.1 | 1570 |
| 16 | 32000 | 0.25 | 35 | 615 | 3.0 | 9.1 | 2 | 0/2 | 0 | 9.1 | 1570 |
| 11 | 32000 | 0.5 | 30 | 2202 | 21.9 | 0.03 | 2 | 0/22 | 0 | 0.2 | 1876 |
| 11 | 32000 | 0.5 | 35 | 2202 | 14.3 | 0.03 | 2 | 0/22 | 0 | 0.2 | 1876 |
| 12 | 32000 | 0.5 | 30 | 2376 | 40.1 | 6.34 | 2 | 0/0 | 1 | 14.7 | 1624 |
| 12 | 32000 | 0.5 | 35 | 2376 | 30.8 | 8.98 | 2 | 0/0 | 1 | 14.7 | 1624 |
| 13 | 32000 | 0.5 | 30 | 1533 | 11.5 | 64.89 | 5 | 16/21 | 0 | 81.0 | 2114 |
| 13 | 32000 | 0.5 | 35 | 1533 | 7.8 | 69.65 | 5 | 18/21 | 0 | 81.0 | 2114 |
| 14 | 32000 | 0.5 | 30 | 2404 | 15.5 | 60.96 | 5 | 11/12 | 0 | 80.2 | 1743 |
| 14 | 32000 | 0.5 | 35 | 2404 | 8.9 | 70.48 | 5 | 11/12 | 0 | 80.2 | 1743 |
| 15 | 32000 | 0.5 | 30 | 1366 | 3.9 | 4.78 | 2 | 0/2 | 0 | 4.8 | 1725 |
| 15 | 32000 | 0.5 | 35 | 1366 | 2.3 | 4.78 | 2 | 0/2 | 0 | 4.8 | 1725 |
| 16 | 32000 | 0.5 | 30 | 1230 | 33.8 | 1.23 | 1 | 0/3 | 0 | 1.4 | 1555 |
| 16 | 32000 | 0.5 | 35 | 1230 | 24.8 | 1.37 | 1 | 0/3 | 0 | 1.4 | 1555 |
| 11 | 32000 | 0.75 | 30 | 3330 | 42.5 | 3.9 | 5 | 0/23 | 4 | 82.1 | 4341 |
| 11 | 32000 | 0.75 | 35 | 3330 | 31.8 | 9.69 | 5 | 0/23 | 4 | 82.1 | 4341 |
| 12 | 32000 | 0.75 | 30 | 3576 | 61.7 | 0.06 | 1 | 0/0 | 0 | 1.3 | 1593 |
| 12 | 32000 | 0.75 | 35 | 3576 | 50.3 | 0.1 | 1 | 0/0 | 0 | 1.3 | 1593 |
| 13 | 32000 | 0.75 | 30 | 2312 | 22.6 | 50.41 | 5 | 14/19 | 0 | 80.7 | 2026 |
| 13 | 32000 | 0.75 | 35 | 2312 | 16.3 | 59.13 | 5 | 17/19 | 0 | 80.7 | 2026 |
| 14 | 32000 | 0.75 | 30 | 3606 | 35.6 | 35.44 | 5 | 5/11 | 1 | 82.2 | 2272 |
| 14 | 32000 | 0.75 | 35 | 3606 | 25.7 | 49.76 | 5 | 10/11 | 1 | 82.2 | 2272 |
| 15 | 32000 | 0.75 | 30 | 2040 | 13.5 | 32.51 | 2 | 0/4 | 0 | 33.6 | 1769 |
| 15 | 32000 | 0.75 | 35 | 2040 | 8.0 | 33.28 | 2 | 0/4 | 0 | 33.6 | 1769 |
| 16 | 32000 | 0.75 | 30 | 2101 | 52.9 | 0.25 | 1 | 0/1 | 8 | 20.0 | 1821 |
| 16 | 32000 | 0.75 | 35 | 2101 | 44.0 | 0.27 | 1 | 0/1 | 8 | 20.0 | 1821 |
| 11 | 32000 | 1.0 | 30 | 4525 | 58.5 | 0.3 | 2 | 0/23 | 1 | 0.6 | 4791 |
| 11 | 32000 | 1.0 | 35 | 4525 | 48.3 | 0.34 | 2 | 0/23 | 1 | 0.6 | 4791 |
| 12 | 32000 | 1.0 | 30 | 4775 | 74.4 | 0.01 | 1 | 0/0 | 0 | 1.4 | 1594 |
| 12 | 32000 | 1.0 | 35 | 4775 | 65.4 | 0.01 | 1 | 0/0 | 0 | 1.4 | 1594 |
| 13 | 32000 | 1.0 | 30 | 3090 | 35.2 | 29.38 | 5 | 6/19 | 0 | 89.7 | 3032 |
| 13 | 32000 | 1.0 | 35 | 3090 | 27.6 | 54.83 | 5 | 13/19 | 0 | 89.7 | 3032 |
| 14 | 32000 | 1.0 | 30 | 4812 | 53.5 | 15.72 | 5 | 1/14 | 6 | 86.0 | 3726 |
| 14 | 32000 | 1.0 | 35 | 4812 | 41.0 | 24.94 | 5 | 3/14 | 6 | 86.0 | 3726 |
| 15 | 32000 | 1.0 | 30 | 2714 | 27.0 | 0.31 | 2 | 0/4 | 0 | 0.5 | 1761 |
| 15 | 32000 | 1.0 | 35 | 2714 | 18.3 | 0.47 | 2 | 0/4 | 0 | 0.5 | 1761 |
| 16 | 32000 | 1.0 | 30 | 2717 | 65.6 | 0.02 | 1 | 0/2 | 0 | 1.8 | 1592 |
| 16 | 32000 | 1.0 | 35 | 2717 | 56.0 | 0.02 | 1 | 0/2 | 0 | 1.8 | 1592 |
| 11 | 48000 | 0.25 | 30 | 1151 | 1.7 | 16.71 | 5 | 12/24 | 0 | 34.9 | 4439 |
| 11 | 48000 | 0.25 | 35 | 1151 | 0.8 | 30.01 | 5 | 16/24 | 0 | 34.9 | 4439 |
| 12 | 48000 | 0.25 | 30 | 1177 | 2.9 | 11.75 | 2 | 0/0 | 0 | 11.9 | 3543 |
| 12 | 48000 | 0.25 | 35 | 1177 | 1.4 | 11.86 | 2 | 0/0 | 0 | 11.9 | 3543 |
| 13 | 48000 | 0.25 | 30 | 755 | 0.9 | 10.05 | 5 | 6/28 | 0 | 10.2 | 4540 |
| 13 | 48000 | 0.25 | 35 | 755 | 0.4 | 10.16 | 5 | 6/28 | 0 | 10.2 | 4540 |
| 14 | 48000 | 0.25 | 30 | 1201 | 1.2 | 0.69 | 3 | 0/20 | 0 | 0.7 | 3863 |
| 14 | 48000 | 0.25 | 35 | 1201 | 0.7 | 0.69 | 3 | 0/20 | 0 | 0.7 | 3863 |
| 15 | 48000 | 0.25 | 30 | 692 | 0.0 | 0.18 | 2 | 0/4 | 0 | 0.2 | 3972 |
| 15 | 48000 | 0.25 | 35 | 692 | 0.0 | 0.18 | 2 | 0/4 | 0 | 0.2 | 3972 |
| 16 | 48000 | 0.25 | 30 | 614 | 1.6 | 21.64 | 2 | 0/2 | 0 | 21.6 | 3488 |
| 16 | 48000 | 0.25 | 35 | 614 | 0.6 | 21.64 | 2 | 0/2 | 0 | 21.6 | 3488 |
| 11 | 48000 | 0.5 | 30 | 2189 | 8.3 | 1.38 | 2 | 0/30 | 0 | 1.4 | 4180 |
| 11 | 48000 | 0.5 | 35 | 2189 | 4.9 | 1.4 | 2 | 0/30 | 0 | 1.4 | 4180 |
| 12 | 48000 | 0.5 | 30 | 2376 | 23.6 | 10.77 | 2 | 0/0 | 1 | 15.3 | 3667 |
| 12 | 48000 | 0.5 | 35 | 2376 | 16.4 | 12.86 | 2 | 0/0 | 1 | 15.3 | 3667 |
| 13 | 48000 | 0.5 | 30 | 1536 | 5.2 | 55.76 | 5 | 32/33 | 0 | 61.9 | 4536 |
| 13 | 48000 | 0.5 | 35 | 1536 | 3.4 | 57.98 | 5 | 32/33 | 0 | 61.9 | 4536 |
| 14 | 48000 | 0.5 | 30 | 2403 | 5.4 | 8.79 | 2 | 0/19 | 0 | 9.3 | 3770 |
| 14 | 48000 | 0.5 | 35 | 2403 | 3.2 | 8.92 | 2 | 0/19 | 0 | 9.3 | 3770 |
| 15 | 48000 | 0.5 | 30 | 1366 | 1.5 | 37.17 | 5 | 4/4 | 0 | 38.9 | 4008 |
| 15 | 48000 | 0.5 | 35 | 1366 | 0.9 | 37.76 | 5 | 4/4 | 0 | 38.9 | 4008 |
| 16 | 48000 | 0.5 | 30 | 1229 | 17.2 | 19.06 | 2 | 0/4 | 0 | 20.5 | 3530 |
| 16 | 48000 | 0.5 | 35 | 1229 | 11.3 | 20.1 | 2 | 0/4 | 0 | 20.5 | 3530 |
| 11 | 48000 | 0.75 | 30 | 3330 | 21.6 | 1.6 | 5 | 0/29 | 3 | 78.9 | 8535 |
| 11 | 48000 | 0.75 | 35 | 3330 | 13.9 | 50.09 | 5 | 22/29 | 3 | 78.9 | 8535 |
| 12 | 48000 | 0.75 | 30 | 3576 | 42.8 | 0.26 | 2 | 0/0 | 1 | 14.6 | 3639 |
| 12 | 48000 | 0.75 | 35 | 3576 | 33.6 | 0.28 | 2 | 0/0 | 1 | 14.6 | 3639 |
| 13 | 48000 | 0.75 | 30 | 2316 | 11.5 | 43.4 | 5 | 22/33 | 0 | 74.3 | 4476 |
| 13 | 48000 | 0.75 | 35 | 2316 | 7.7 | 46.43 | 5 | 22/33 | 0 | 74.3 | 4476 |
| 14 | 48000 | 0.75 | 30 | 3607 | 17.2 | 61.62 | 5 | 20/21 | 0 | 84.5 | 5515 |
| 14 | 48000 | 0.75 | 35 | 3607 | 10.4 | 71.88 | 5 | 20/21 | 0 | 84.5 | 5515 |
| 15 | 48000 | 0.75 | 30 | 2040 | 4.9 | 8.12 | 2 | 0/5 | 0 | 8.3 | 3942 |
| 15 | 48000 | 0.75 | 35 | 2040 | 2.9 | 8.22 | 2 | 0/5 | 0 | 8.3 | 3942 |
| 16 | 48000 | 0.75 | 30 | 2100 | 34.1 | 13.96 | 2 | 0/1 | 0 | 19.6 | 3533 |
| 16 | 48000 | 0.75 | 35 | 2100 | 25.2 | 16.63 | 2 | 0/1 | 0 | 19.6 | 3533 |
| 11 | 48000 | 1.0 | 30 | 4524 | 36.0 | 0.04 | 1 | 0/27 | 0 | 0.0 | 9354 |
| 11 | 48000 | 1.0 | 35 | 4524 | 25.8 | 0.04 | 1 | 0/27 | 0 | 0.0 | 9354 |
| 12 | 48000 | 1.0 | 30 | 4775 | 57.2 | 0.03 | 1 | 0/0 | 0 | 1.4 | 4659 |
| 12 | 48000 | 1.0 | 35 | 4775 | 48.5 | 0.03 | 1 | 0/0 | 0 | 1.4 | 4659 |
| 13 | 48000 | 1.0 | 30 | 3097 | 20.1 | 58.98 | 5 | 26/32 | 0 | 84.5 | 11049 |
| 13 | 48000 | 1.0 | 35 | 3097 | 14.2 | 68.67 | 5 | 29/32 | 0 | 84.5 | 11049 |
| 14 | 48000 | 1.0 | 30 | 4814 | 31.1 | 0.1 | 1 | 0/23 | 0 | 0.1 | 8965 |
| 14 | 48000 | 1.0 | 35 | 4814 | 21.7 | 0.14 | 1 | 0/23 | 0 | 0.1 | 8965 |
| 15 | 48000 | 1.0 | 30 | 2714 | 12.2 | 4.76 | 2 | 0/5 | 0 | 5.2 | 3919 |
| 15 | 48000 | 1.0 | 35 | 2714 | 7.2 | 4.94 | 2 | 0/5 | 0 | 5.2 | 3919 |
| 16 | 48000 | 1.0 | 30 | 2715 | 48.0 | 1.01 | 1 | 0/2 | 0 | 1.2 | 3542 |
| 16 | 48000 | 1.0 | 35 | 2715 | 38.2 | 1.15 | 1 | 0/2 | 0 | 1.2 | 3542 |

</details>

**What the numbers show.** Too-steep land falls steadily as relief falls: at 24,000 canvas it is 65 percent at x1.0, 51 at x0.75, 32 at x0.5 and 8 at x0.25 (limit 30), and larger canvases are gentler at the same multiplier because the same height spreads over more ground (34 percent at x1.0 on 48,000). Reach does not follow: the share of land a walker reaches from the core stays between 3 and 32 percent at every setting and does not rise as steepness falls, because the core often sits on a small landmass or a bench sliver cut off by thin lakes (core landmass averages 13 to 54 percent of land), and the 300 wu bench step is not scaled with relief, so benches read as more lake stripes at low multipliers (see the x0.5 screenshots). Layers reachable stay at 1.8 to 3.5 of 5 on average and peaks reachable over peaks stay low (about 1 to 3 of 7 on 24,000, 3 to 11 of 13 to 15 on 48,000), so within this generator relief alone does not buy full reach.

**Questions for Westley.**
1. Footprint: is 300 wu the right width to measure slope over (a formation is 200 wu wide)?
2. Steepness: which figure inside 30 to 35 degrees? About 60 to 70 percent of this ground is over it on a big map; is that the mountains you want, or should the terrain be gentler overall (the detail slider does not do it; the large shapes would need a height or width change)?
3. Minimum relief: is 2500 wu the floor, and should it grow with the canvas?
4. "Unreasonably hard to reach": the walk view prints reach of land, layers reachable and peaks reachable. Which is the test: a route no longer than a multiple of the straight line (Q-189-04 a), a count of routes (b), or what you see in the gold and magenta? Is a ramp-only corridor an acceptable way up, or should walkable ground be wider?
5. Is it acceptable that on some seeds the city core sits on a landmass of a few percent of the land?
6. Variety: is "layer by biome spread" what you meant? Do mesa, canyon and island chain read as the variety you have in mind; which batch-2 form first?
7. Benching: does 15 to 65 percent look right, and is a short steep riser what "benched" should look like?
8. Layer bands: equal heights between lowest and highest ground, or fitted by share of land so layers 4 and 5 are never nearly empty?

**Not built or weak.** No bridges, so rivers and bays block the flood. Ramps are generated at limit 30 only and can fail to connect on some seeds (15, 16). Ramps are one-dimensional corridors, no switchbacks beyond the shortest path. Close-up shots sit on very steep ground, so the X reads on red with a white edge.

## Pass 5: the layout leads, the terrain obeys (2026-10-03)

Prototype under the Prototype gate, spec `docs/northstar/plans/archive/specs/2026-10-03-land-mockup-pass5-spec.md`, answering Q-191-04 (amended): the landscape engine takes the layout engine's node graph and must produce what it calls for. Land kits only; the space kit and `field_map_space.gd` are untouched (`qa/space.json` runs clean). Code: `pass5_layout.gd` (reaction), `pass5_places.gd` (checks, equal distance, places), `pass5_ui.gd` (picker, views, panel); small hooks in `field_map.gd`, `hud.gd`, `pass4_ui.gd`, `landscape_mockup.gd`. Screenshots: `mockup/pass5/` (1920x1080; `scripts/mockup_qa.sh run landscape scenes/mockups/landscape/qa/pass5.json <out> --res 1920x1080`). Table run: `qa/pass5_table.json`.

**What was built.**
1. Layout picker: the eight `simulation/layout_library` layouts (off, from the seed as seed mod 8, or 1 to 8). Nodes drawn as coloured discs with labels, edges as ribbons (white path, orange flank, magenta restricted); toggle N.
2. Terrain obeys (toggle O regenerates with the reaction off, for before and after). Runs inside the generator after the pass-4 ramps and uses the same blocked-ground mask (limit 30, footprint 300 wu). A vantage moves to the highest dry ground within 1500 wu that its neighbours can climb to; every node gets a levelled pad by kind (staging 500, objective 600, vantage 350, spawn 450, reinforcement 250, transit and flank 200, hazard 150 wu, plus a 250 wu shoulder); each chokepoint gets a flat corridor 1600 wu long at the layout's width with a wall on both sides (rises 900 wu in 120 wu and keeps rising, so the wall is blocked top to bottom); then each edge is walked by A* (blocked ground costs 5, water 9, wall closed) and, where the mask breaks it, a graded strip 500 wu wide with 150 wu shoulders is cut along the route at no more than 18 degrees, water on the route becomes a bridge, repeated up to 6 rounds with 3 tries per edge. A flank edge pays 15 to cross a choke corridor so it bypasses the choke where it can. Changed ground has its own colours (key C): pad, graded route, bridge, choke corridor, choke wall, vantage ground.
3. Places per kind, each with its own score on the obeying terrain, heat view on a key (H cycles) and winners as markers (Z). Base: flat, open, near the staging node (side A) or the spawn node (side B), within 2500 wu. Economic: flat, water within 1500 wu, open, near its own base. Significant resource: flat, open, high, and only where the two bases' walking distances agree. Expansion: flat, open, 3000 to 8000 wu of walking from its own side and clearly nearer to it. Neutral settlement: flat, water, open, near the walking midline, 4500 wu or more from either base.
4. Equal distance: walking distance is a Dijkstra over walkable cells (8 neighbours, 100 wu and 141 wu steps), straight distance is the straight line, both from each side's base. Resources are only eligible where the two walking distances differ by no more than the tolerance (relative to their mean). The HUD prints both sides' walking and straight distances to the objective and each resource, the difference, and says NOT MET when it fails.
5. Checks in the HUD: edges walkable (and which are broken), each choke's asked and measured width (walkable run through the choke centre, sampled every 20 wu) and whether both sides are blocked, vantage reachable from base A and its height over the mean ground within 3000 wu, flank routes that avoid every choke corridor, base A to base B route and length.

**Keys.** Y layout, O terrain obeys on/off, N layout graph, Z place markers, C changed ground, V walk view (green joined to base A, orange cut off, magenta blocked, cyan bridge, gold line per edge), H heat view and kind. Sliders: narrow choke, moderate choke, equal-distance tolerance (release to apply). Pass 4's keys all still work.

**Candidate numbers (every one is Westley's to set).** Choke widths narrow 300 wu, moderate 600 wu (the layouts only say "narrow" and "moderate"). Equal-distance tolerance 10 percent. Pad radii above. Choke corridor 1600 wu long, wall 900 wu high, 500 wu band. Route strip 500 wu wide, 150 wu shoulder, 18 degree grade, 6 rounds, 3 tries. Vantage search 1500 wu, climbable at 14 degrees. Blocked-ground limit 30 degrees, footprint 300 wu (from pass 4). Place counts at canvas 24,000: 3 economic and 2 expansion per side, 2 resources, 3 settlements, scaled by canvas over 24,000 and rounded. Minimum separations 1500 (economic), 2500 (expansion), 3000 (settlement), 4000 (between resources) wu; resources at least 2500 wu of walking from each base.

**Table: all eight layouts, seeds 11 to 13** (canvas 24,000, reaction on, limit 30; `qa/pass5_table.json`). Walking distances in wu. Generate is the whole regenerate (terrain, reaction, ground and pieces) in seconds on llvmpipe; the reaction alone is about 3 to 9 seconds.

| layout | seed | edges walkable | chokes asked > measured (wu) | vantages reachable | base A to B walking (wu) | objective walking A / B | resource 1 walking A / B | resource 2 walking A / B | all within tolerance | generate (s) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 11 | 12 of 15 | 300 > 300, 600 > 540 | 1 of 2 | 30308 | 27808 / 2831 | 14608 / 15992 | 43916 / 23930 | no | 13.2 |
| 1 | 12 | 15 of 15 | 300 > 300, 600 > 540 | 2 of 2 | 22315 | 18611 / 4328 | 11449 / 10867 | 20708 / 29941 | no | 4.7 |
| 1 | 13 | 15 of 15 | 300 > 300, 600 > 540 | 2 of 2 | 26569 | 23731 / 3131 | 13812 / 13123 | 19292 / 18651 | no | 8.3 |
| 2 | 11 | 10 of 12 | 600 > 500 | 1 of 1 | 39919 | 38378 / 1600 | 19620 / 21182 | 23765 / 18861 | no | 10.5 |
| 2 | 12 | 12 of 12 | 600 > 500 | 1 of 1 | 20840 | 20840 / 0 | 10963 / 10160 | 18691 / 29634 | no | 4.2 |
| 2 | 13 | 11 of 12 | 600 > 500 | 1 of 1 | no route | none / 2066 | - | - | no | 9.1 |
| 3 | 11 | 12 of 14 | 600 > 500, 300 > 340, 300 > 240 | 2 of 2 | 16004 | 2641 / 13363 | 7773 / 8563 | 17184 / 28588 | no | 12.8 |
| 3 | 12 | 14 of 14 | 600 > 500, 300 > 240, 300 > 240 | 2 of 2 | 16263 | 2800 / 13463 | 7741 / 8521 | 17311 / 22208 | no | 4.9 |
| 3 | 13 | 11 of 14 | 600 > 500, 300 > 240, 300 > 240 | 1 of 2 | no route | 3963 / none | - | - | no | 12.3 |
| 4 | 11 | 15 of 15 | 300 > 200, 600 > 500, 300 > 200 | 0 of 0 | 23251 | 21710 / 1600 | 12188 / 11063 | 34253 / 27679 | no | 11.9 |
| 4 | 12 | 15 of 15 | 300 > 200, 600 > 500, 300 > 200 | 0 of 0 | 21254 | 21254 / 0 | 11084 / 10170 | 17654 / 33231 | no | 4.8 |
| 4 | 13 | 15 of 15 | 300 > 200, 600 > 500, 300 > 200 | 0 of 0 | 34340 | 32675 / 2066 | 16317 / 18024 | 20231 / 23211 | no | 10.4 |
| 5 | 11 | 11 of 11 | 300 > 200, 600 > 580 | 1 of 1 | 26355 | 23226 / 3187 | 13324 / 13197 | 27533 / 23612 | no | 10.0 |
| 5 | 12 | 11 of 11 | 300 > 320, 600 > 580 | 1 of 1 | 32296 | 29209 / 3087 | 15499 / 16797 | 20538 / 12489 | no | 4.5 |
| 5 | 13 | 8 of 11 | 300 > 320, 600 > 580 | 0 of 1 | no route | none / 3087 | - | - | no | 10.1 |
| 6 | 11 | 11 of 14 | 300 > 300, 600 > 500 | 2 of 2 | 22523 | 20923 / 1600 | 10846 / 11853 | 19814 / 27304 | no | 13.4 |
| 6 | 12 | 14 of 14 | 300 > 300, 600 > 500 | 2 of 2 | 25342 | 25301 / 100 | 13885 / 14671 | 9674 / 15668 | no | 5.5 |
| 6 | 13 | 14 of 14 | 300 > 300, 600 > 500 | 2 of 2 | 26728 | 25062 / 2066 | 14388 / 13281 | 15234 / 19961 | no | 9.8 |
| 7 | 11 | 13 of 13 | no chokes | 0 of 0 | 29066 | 27001 / 2183 | 14012 / 15054 | 18424 / 10643 | no | 10.7 |
| 7 | 12 | 13 of 13 | no chokes | 0 of 0 | 29735 | 27245 / 3514 | 14947 / 15095 | 19037 / 10698 | no | 4.8 |
| 7 | 13 | 13 of 13 | no chokes | 0 of 0 | 23359 | 21245 / 2407 | 12154 / 11205 | 20524 / 27842 | no | 7.7 |
| 8 | 11 | 13 of 14 | 600 > 600, 300 > 380, 300 > 200 | 1 of 2 | 10624 | 1900 / 8724 | 5541 / 5083 | 14227 / 23699 | no | 11.3 |
| 8 | 12 | 14 of 14 | 600 > 600, 300 > 380, 300 > 380 | 2 of 2 | 11321 | 2024 / 9297 | 5938 / 5383 | 8611 / 12046 | no | 4.8 |
| 8 | 13 | 14 of 14 | 600 > 500, 300 > 380, 300 > 260 | 2 of 2 | 11860 | 1800 / 10060 | 6190 / 5728 | 24531 / 20455 | no | 10.2 |

**What the numbers say.**
(a) Most edges become walkable, but not all: 12 of 15 on layout 1 seed 11, and on seeds 13 of layouts 2, 3 and 5 base A and base B are not joined at all. The broken edges are where a pad or a choke corridor sits at a height the neighbouring ground cannot reach inside the grade (a spawn node on a cliff, a choke on a plateau): the cutter meets in the middle for the strip but later cuts still undo earlier ones. Not fixed in this pass; the HUD says which edges.
(b) Chokes are real: the corridor is walkable and both sides are blocked on every table row. Measured widths land within 100 wu of the asked width (200 to 380 measured for 300 asked, 500 to 600 for 600), because the mask is cells 100 wu wide and the 300 wu footprint rounds the run.
(c) Equal distance is never met for the objective: the layouts are assaults (the objective is placed by the layout for one side), so Q-191-03 cannot hold for the objective without moving it: layouts 1, 2, 4, 5, 6 and 7 put it a few thousand wu from the enemy spawn and 15,000 to 38,000 wu of walking from the staging, and layouts 3 and 8 do the reverse (about 2000 to 4000 from the staging, 8,700 to 13,400 from the spawn). The first resource usually lands within 10 percent; the second usually cannot, because of the 4000 wu separation from the first, and is placed at the most balanced cell and marked "tol not met".
(d) Seed 12 is a small-island map (7 percent land); the reaction bridges the sea, so edges become walkable across water, which reads as long cyan causeways in the react view.
(e) The cut routes are wide graded strips; where two routes cross they look like a flattened junction. Natural-looking is Westley's call (question 4 below).
(f) The mask limits places to the walkable network and the pads: with about 60 percent of land too steep, the heat views show scores only along the cut routes and on the few natural flats.

**Questions for Westley.**
1. Choke widths: are 300 wu (narrow) and 600 wu (moderate) the right candidates? The layout only says "narrow" and "moderate".
2. Distance measure and tolerance: is the walking distance over the 8-neighbour walkable mask the right measure, and 10 percent the right tolerance? Which should win when walking and straight distance disagree (they differ by 50 to 150 percent in the table)?
3. The objective cannot be equidistant in an assault layout. Should the objective (and the second resource) be allowed to move to the equal-distance line, or should the layout engine place the staging and spawn nodes symmetrically?
4. Do the cut routes (500 wu graded strips, bridges over sea and rivers, flat pads on cliffs) read as natural landscape, or should the terrain reshape more gently, or the layout move the node instead of the terrain bending to it?
5. Counts: 3 economic and 2 expansion per side, 2 resources, 3 settlements at canvas 24,000, scaled by canvas. Right shape, or should they come from the layout?
6. Should layouts with no chokepoint (layout 7) and with hazard anchors (a terrain break, cliff face) ask the terrain for a hazard feature too? Hazard anchors only get a 150 wu pad here.

**Not built or not working.** Edges that stay broken (counts in the table). Nodes in open sea are given a pad islet, so a layout node can sit on a lone island joined by a bridge. No landforms batch 2, settlements, or archetype bias. The vantage check is height over the local mean (one candidate measure), not a field-of-view check.

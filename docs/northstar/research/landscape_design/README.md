# Landscape design phase (rung P2)

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

## Pass 4: where walkers can go (2026-10-03)

Prototype under the Prototype gate, spec `docs/northstar/plans/2026-10-03-land-mockup-pass4-spec.md`. Greek and settled_reach kits only; the space kit and `field_map_space.gd` are untouched. Screenshots: `mockup/pass4/` (1920x1080, `scripts/mockup_qa.sh run landscape scenes/mockups/landscape/qa/pass4.json <out> --res 1920x1080`; numbers: `qa/pass4_numbers.json`).

**Built.** New files `pass4_terrain.gd` (generation and analysis) and `pass4_ui.gd` (views, X cursor, panel, sliders); small hooks in `field_map.gd`, `hud.gd`, `landscape_mockup.gd`.
1. Too-steep view (T): off, then over 30, then over 35. Over 35 flat red. In the 30 view the 30 to 35 band is orange (blocked at 30 only); in the 35 view that band shows as normal ground. Slope is the plane gradient of one 100 wu quad. The panel prints the share of land (quads with four dry corners) too steep at 30, 32.5 and 35.
2. X cursor (U toggles "unit selected"): hovering a quad over the current limit draws a red X with a white edge at the cursor. Shots `closeup_*`.
3. Band view (B): five equal-height layers fitted between the lowest and highest dry ground of the map; panel prints the five floor heights, the step and the share of land per layer.
4. Minimum relief slider (default **2500 wu, candidate, Westley owns it**). Why 2500: layer 5 then starts at 2000 wu and every layer step is at least 500 wu, over a quarter of a typical 1500 wu tactical view height, so a step is never a meadow slope. After landforms the generator stretches dry ground upward if highest minus lowest is below the slider. The existing generator already makes 2700 to 4800 wu, so the default never bites; 5000 on seed 15 stretches x1.88 (shot `seed15_relief5000_band`).
5. Benched share: drawn per map from the seed (15 to 65 percent of land), terraces of 300 wu with short risers over a noise-shaped region; slider override 0 to 100 percent (button switches seed and override). Shots `seed11_bench0_*`, `seed11_bench100_*`.
6. Landforms batch 1 (M cycles seed, mesa, canyon, islands, none): mesa is a flat block lifted 900 wu with walls about 200 wu wide; canyon is a winding 600 wu wide cut up to 1500 wu deep; island chain is 5 to 7 cones in the sea. "seed" picks one to three by seed. Canyon needs high land: not built on seeds 12, 15, 16. Caldera, fjord, terraced massif are batch 2 (Q-187-01).
7. Walk view (G, L switches limit 30/35): flood from the city core over dry ground, a step allowed when its slope is at most the limit (8 neighbours). Cut-off land magenta, reachable green, core white, peaks cyan (reachable) or black. Peak = highest point in a 9 by 9 cell window on layers 4 or 5. Water blocks the walk, so a river or bay cuts off land (no bridges in the prototype).
8. Variety measure: **joint entropy of (layer, biome zone) over dry cells, in bits, out of 4.64.** Why: it is the spread measure (b), one number, needs no landform tally, goes up when height and biome both spread out and stays put when the canvas grows. It does not see how the places are arranged and does not count landforms; the panel lists those next to it.

**Keys.** T steep, B bands, G walk, L limit, U unit selected, M landform, R regenerate, Tab kit; sliders for minimum relief and benched share. Drag-release regenerates (about 4 s each, the placer).

**Numbers** (landform "seed", bench "seed", minimum relief 2500; limit 30 / 35 for walk columns are reach, layers reachable, peaks reachable). Generate = `FieldMap.generate` ms in this run (includes shape); shape and analyse ms are the pass-4 parts.

| seed | relief wu | layer floors wu | step wu | land % on L1..L5 | too steep % at 30/32.5/35 | walk at 30 | walk at 35 | landforms | variety bits | land share | bench % | generate / shape / analyse ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 11 | 4500 | 0/900/1800/2700/3600 | 900 | 35/31/25/9/1 | 71/68/64 | 19.6%, 2, 0 of 18 | 72.8%, 4, 9 of 18 | mesa, islands | 2.33 | 39% | 26% | 1741 / 19 / 116 |
| 12 | 4773 | 0/955/1909/2864/3819 | 955 | 76/22/2/1/0 | 89/87/86 | 3.8%, 1, 0 of 0 | 11.4%, 1, 0 of 0 | islands | 1.01 | 6% | 41% | 865 / 5 / 54 |
| 13 | 3088 | 0/618/1235/1853/2471 | 618 | 21/28/30/19/2 | 51/48/44 | 0.7%, 2, 0 of 13 | 0.8%, 2, 0 of 13 | canyon, islands | 2.44 | 23% | 67% | 1422 / 22 / 67 |
| 14 | 4802 | 0/960/1921/2881/3842 | 960 | 41/22/16/14/7 | 71/67/64 | 0.6%, 1, 0 of 9 | 0.6%, 1, 0 of 9 | islands | 2.54 | 19% | 33% | 1472 / 9 / 62 |
| 15 | 2693 | 0/539/1077/1616/2154 | 539 | 58/25/12/3/1 | 55/50/45 | 0.3%, 2, 0 of 2 | 0.5%, 2, 0 of 2 | islands | 1.64 | 17% | 36% | 972 / 10 / 60 |
| 16 | 2700 | 0/540/1080/1620/2160 | 540 | 72/16/8/3/1 | 88/86/82 | 0.8%, 1, 0 of 2 | 2.0%, 1, 0 of 2 | islands | 1.42 | 4% | 30% | 858 / 5 / 53 |

Extra cases (seed 11 unless noted): bench 0 percent gives reach 81.9 percent at 30 (9 of 13 peaks); bench 26 percent (seed) 19.6 percent; bench 100 percent 0.2 percent. Forced landform at limit 35: mesa 48.5 percent reach (4 of 18 peaks), canyon 76.6 percent (8 of 13), islands 77.3 percent, none 78.9 percent. Seed 15, minimum relief 5000: too steep at 30 goes 55 to 80 percent.

**What the numbers say.** (a) The pass-3 terrain is steep: 3000 to 4800 wu of height over a 24000 wu canvas leaves 50 to 90 percent of dry land over 30 degrees. (b) Walking reach swings with the limit and with benching, not with the steep share: seed 11 reaches 20 percent of its land at 30 degrees and 73 percent at 35; terrace risers are what shut the doors. On seeds 13 to 16 the city core is walled in at both limits (2 percent reach or less), so those maps fail the "reachable" test as built. (c) Peaks reachable: 9 of 18 (50 percent) on seed 11 at 35, 0 at 30; the other seeds have zero or two to thirteen peaks and none reachable. Seed 12 and 16 are mostly sea (6 and 4 percent land), so layers 4 and 5 hold almost nothing. (d) Equal-height layers leave layers 4 and 5 with 1 to 21 percent of the land because one summit sets the top of the range. Nothing was tuned to the 70 percent peak expectation.

**Questions for Westley.**
1. Steepness: with the red view in hand, which figure inside 30 to 35 degrees? Note the ground is already above it over most of the map; do you want less steep ground overall, or are the red areas the point (mountains units go around)?
2. Minimum relief: is 2500 wu the right floor, and should it grow with the canvas?
3. "Unreasonably hard to reach": the walk view prints reach of land, layers reachable and peaks reachable. Which is the measure: a walking route no longer than a multiple of the straight line (Q-189-04 a), a count of routes (b), or what you see in the magenta?
4. Is a core that can walk to under 2 percent of its map acceptable on any seed? (It is what seeds 13 to 16 give now.)
5. Variety: is "layer by biome spread" what you meant, or do you mean counting landforms and biomes on the map? Do the mesa, canyon and island chain read as the variety you have in mind, and which of the batch-2 forms do you want first?
6. Benched share: does 15 to 65 percent look right, and is a bench riser (steep short step) what "benched" should look like?
7. Layer bands: equal heights between lowest and highest ground, or fitted by share of land so layers 4 and 5 are never nearly empty?

**Not built or weak.** No bridges or ramps in the walk flood (water and steep ground block). Canyon not built on seeds 12, 15, 16 (no high ground). Close-up shots sit on very steep ground, so the X reads on red. The 30 and 35 walk shots exist for seeds 11 to 13 (`*_walk-30`, `*_walk-35`). The space kit shows none of this.

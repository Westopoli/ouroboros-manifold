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

# HANDOFF BRIEF — P2 landscape mockup, pass 3: terrain first

Self-contained. Continues the mockup in `scenes/mockups/landscape/` built under `2026-09-21-p2-landscape-mockup.md` and revised under "Mockup review 1". The rules of that brief still apply (placeholders only, GDScript only, no era named in code, deterministic seed, commit per step, touch nothing outside `scenes/mockups/landscape/` and `docs/northstar/research/landscape_design/mockup/`). Design record: `docs/northstar/research/landscape_design/README.md`, section "Mockup review 2", and the five new references `docs/bible/references/E-17/E-17-9..13*.png` with their rows in `references/E-17/notes.md`. Read those first.

- If you are an Opus or Fable chat: plan and review, Sonnet sub-agents build; ask Westley about his Claude usage before a batch of more than two doers. If you are a Sonnet chat: do the work yourself, spawn no sub-agents.

## What Westley approved and what he asked for

Approved: one generator, one field map, two kits (Greek, Settled Reach), one placer, the city as the battlefield, three zoom bands, the map-view overlay in world space.

Asked for, verbatim: "maps would be significantly larger, mountains would be huge and zoomability would have a "floor" that you can follow elevation changes with (halo wars had a mechanic like this), you stayed at your zoom "height" even when elevation changed ... I want this game to have big changes for vastly different heights. City has distinct onion layers ... I'd hoped it'd be much more dynamic, more variety, not simple circular cities, cities that follow rivers like reality or nestle in valleys/peaks, hillsides. Stochiastic seperations, very similar to the Roblox biome/landscape generation tool."

## The change: terrain first, waypoints second

Pass 1 placed a hand skeleton and grew gradient discs around it; that is why every city is a ring on flat ground. Pass 3 inverts the order. `field_map.gd` becomes:

1. **Elevation from layered noise.** Seeded `FastNoiseLite`, three octaves at different frequencies (continent, hills, detail), combined and shaped so a seed gives one or two mountain masses, valleys between them and a coast on at least one edge. Vertical scale: sea level 0, peaks at 3,000 to 5,000 wu on a 24,000 wu canvas (the mockup's 250 wu terraces were an order of magnitude too small). Quantize to the five layer terraces only for the ground mesh's cliff faces; keep the continuous height for placement and camera.
2. **Water from elevation.** Sea below level 0. Lakes in closed basins (fill from local minima). Rivers: pick two to four sources on high ground, flow downhill by steepest descent to the sea or a lake, carve a shallow channel, widen toward the mouth. A river is the field map's `water` band plus a polyline.
3. **Biome bands from elevation, moisture and latitude.** Moisture = distance to water blurred; latitude = canvas Y. Bands (still called `zone_a..e` in code, named only in the kit): water, shore, lowland, upland, highland, peak. Boundaries are noise-perturbed so they read as the Roblox map (stochastic separations), never as smooth contours. Per-vertex blending as before.
4. **Spine nodes found on the terrain, not placed.** Rules, in order:
   - city core: the best-scoring cell among river bends, river-meets-sea, lake shores and defensible hillsides (score = water proximity + flatness + moderate elevation + distance from the canvas edge); the seed breaks ties;
   - districts grow outward from the core along low slope and along the river and coast, with population falling with slope and distance, so the city follows the river or hugs the valley or climbs the hillside, never a ring;
   - the wall follows the district-2 boundary snapped to defensible terrain (ridge lines, river banks);
   - chokepoints where the terrain forces passage: a river crossing, a pass between two high cells, a gate where the wall meets an approach;
   - vantages on real local peaks within reach of the city; staging on flat land outside the wall on two approaches; spawns on the far side; hazard anchors in marsh (low, wet, flat) or highland; extraction on the coast.
   The nine E-17 node types stay; their positions are outputs now.
5. **Gradients as before** (obstacle, cover, interference) anchored on the found nodes with the R-114-03 values, plus terrain contributions: obstacle rises with slope, cover with forest band, interference in marsh and highland.
6. **Canvas 24,000 wu** default (large per E-17 R-116-01); the HUD may switch 16,000 / 24,000 / 32,000 to show scale.

Borders, crossings, the placer, the kits and the ground mesh keep their pass-1 interfaces; the kits gain pieces for the new bands (Greek: shore reeds, lowland fields, upland olive and cypress, highland rock, snow peak; Settled Reach: dust plain, ore field, ice shelf, spire rock, void gap where sea was). The city mapper reads the new population field unchanged.

## Camera: height above ground

`camera_rig.gd`: the camera's zoom is a height **above the ground under the camera target**, not an absolute Y. Sample the elevation grid at the target each frame and add the zoom height; smooth the vertical follow over about 200 ms so ridges do not jolt. Bands are defined by height above ground. Scrolling from the valley up the mountain keeps the same framing (Halo Wars). The map band keeps its top-down ease.

## Verification

- `verify.gd`: seed 11 twice equal, seed 12 differs (now the whole layout differs, not only dressing); every river polyline ends at sea or a lake and never climbs; the city core is within 400 wu of water; no district cell has slope above the threshold; at least one chokepoint is a river crossing and one is a pass; mesh names valid for both kits.
- Screenshots: seeds 11, 12, 13 at three bands under both kits (18), plus a ground-level shot at micro band looking up a mountain from the valley, both kits (2). Commit under `landscape_design/mockup/pass3/`.
- Report: generation, placer and ground times; piece counts; and the same eight questions as pass 1, with three added: does a seed change give a genuinely different map; do cities read as following the terrain; does the camera floor feel right when scrolling up the mountain.

## What is not in scope

Real assets, the sim, fairness scoring, mission archetypes, units beyond the placeholder blocks, any edit outside the mockup directory. Under-defined points (river count, vertical scale, band thresholds, the wall-snapping rule) are built the simplest way and listed in the report with candidates.

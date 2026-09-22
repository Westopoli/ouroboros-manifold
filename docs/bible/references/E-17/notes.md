# E-17 Map Generation — Look and behavior references

**Not literal.** Ouroboros will not copy Age of Empires Online. Read the aspect each shot pins, not the art.

**For test-writers and build models:** "Proves / contrast" names the story the shot grounds and what to check the current build against. If the build does not read like the Aspect cell for that story, that is a finding to raise, not a pass.

## Provided shots (Westley, 2026-09-13)

`E-17-1.png`, `E-17-2.png`, `E-17-3.png`, `E-17-4.png` — Age of Empires Online.

| # | Story | Source | Aspect — the example | Not wanted | Proves / contrast |
|---|---|---|---|---|---|
| 01 | S-119, S-113 | Age of Empires Online | The toy, cartoonish, readable terrain register: a map that reads instantly as a real place, with distinct place types tellable apart at a glance | AoE's exact palette/props; ours will be more blocky | terrain reads like a place, not a noise field (shares the E-18 visual register) |

## Provided shots (Westley, 2026-09-21, landscape design phase)

`E-17-5-macro-city-a.png`, `E-17-6-macro-city-b.png`, `E-17-7-macro-city-far.png` — generated concept images, "ultra high altitude RTS tactical camera view, zoomed out, epic macro civilization". `E-17-8-wows-map-view.png` — World of Warships map view.

| # | Story | Source | Aspect — the example | Not wanted | Proves / contrast |
|---|---|---|---|---|---|
| 05 | S-119, S-114, S-115, S-159 | concept image a | A walled city on terraces is the battlefield: cliffs, waterfalls and aqueducts give dramatic elevation; a river is a border crossed at bridges; armies are small blocks outside the walls; snow mountains far behind sell scale | Classical-era art as the only skin; the same shapes must read under a space skin | the city and the terrain come from one generator: walls, coast and cliffs are all borders; gates and bridges are chokepoints |
| 06 | S-119, S-159 | concept image b | The city seen from higher up: districts of different density around a core, farmland and forest as the biome outside, harbor and fleet where the coast is | Player-built everything; the player builds pieces only | population density and wealth map to building density and kind, the way obstacle and cover map to terrain pieces |
| 07 | S-119, S-116 | concept image far | The whole canvas in one view: 20 to 30 tactical screens of terrain and city, still readable as places | A single-screen skirmish arena | huge-scale canvas with the playful bright Age of Empires Online register at every zoom |
| 08 | S-103 (E-16), S-116 | World of Warships | The map view: grid, terrain as simple shapes, unit groups as icons, drawn movement arrows, objective circles; basic group movement orders are given from here | Naval UI, the grid letters | the third zoom band (micro, tactical, map) and orders from the map level |

## Provided shots (Westley, 2026-09-21, mockup review 2)

`E-17-9-roblox-biome-map.png`, `E-17-10-roblox-terrain-cliffs.png`, `E-17-11-roblox-heightfield.png` (Roblox terrain generator), `E-17-12-island-biome-map.png`, `E-17-13-island-heightfield.png` (island generators).

| # | Story | Source | Aspect — the example | Not wanted | Proves / contrast |
|---|---|---|---|---|---|
| 09 | S-114, S-119 | Roblox biome map | Biomes and elevation as layered noise: bands that follow each other (water, shore, lowland, upland, peak), stochastic separations, no repeated shape | Concentric anything | terrain zones come from noise fields, not from discs around waypoints |
| 10 | S-114, S-119 | Roblox terrain, ground view | Huge elevation: cliffs, a lake far below, snow peaks far above; the player physically feels height | Gentle terraces | mountains are huge, elevation changes are big, "vastly different heights" |
| 11 | S-114 | Roblox heightfield | The same noise as a heightfield with terraces and shading; water fills the lows | | one elevation field drives ground mesh, water and biome bands together |
| 12 | S-119 | island biome map | A whole landmass with snow north, forest south, coasts, inlets; biomes follow elevation and latitude | | large-scale variety across one map; cities should follow rivers and coasts the way real ones do |
| 13 | S-116, S-119 | island heightfield | The same map as relief: peaks, valleys, islands; the canvas is much larger than one city | A single city-sized canvas | maps are significantly larger; a city nestles in a valley, on a hillside, or along a river, never a circle stamped on flat ground |

## Derived target — elevation and sense of scale (Westley, 2026-09-13)

The AoE shots pin the readable toy register only. The thing Westley cares most about for E-17 is **not** in them and is the design target:

- **Dramatic elevation differences.** Real earth-era height changes; the player should physically feel the height and get a real sense of scale. This ties to the E-01 layer system — vertical space must read.
- **Major sense of scale via distant landmarks.** Huge objects far in the background — mountains, clouds — like games that place enormous distant features to sell scale. The battlefield should feel small against something vast.

→ No matching screenshot yet; recorded as the derived visual target for S-114, S-115, S-119. A reference clip may be added later, but the intent above is the ground truth.

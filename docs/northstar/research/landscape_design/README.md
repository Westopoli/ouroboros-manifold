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

## Next step

A mockup spec for Westley's approval, then the mockup itself in Godot, then the epic rewrites.

# Space-era landscape: first investigation

Opened 2026-10-02. Flag: Q-166-02. Nothing here is bible text.

## Westley's idea, verbatim

"I imagine it like a boolean hyperplane (ice sheet), like in the arctic ocean. There are sections of water (open, crossable), and there are sections of ice (not crossable). But there are multiple layers of this. In a heavy asteroid field, they may even be tunnels moving horizontally/vertically, in a light asteroid field it might be mostly open with a few limited sections. In that way, the space landscape engine can be simpler, binary instead of a flowing landscape. Each layer can generate a "+/-" map, and we can fill in the gaps with asteroids/obstacles. I imagine it will only be a minor modification to the underlying code to the existing biome/landscape generation engine, just making it simplier. Investigate and come back with a report of that perception."

## Verdict

The idea is right, and the bible already asks for exactly this output. The size of the change depends on which code is meant.

| Claim | Finding |
|---|---|
| A space map is an open-or-blocked map per layer | Right. It is already the rule: "the answer is a binary open or blocked per layer" (E-01 R-001-04, R-114-01). |
| It is simpler than land | Right. Land needs height, water, rivers, slopes and bands, and then derives the same open-or-blocked map from them. Space makes the map directly. |
| Fill the blocked parts with asteroids | Right, and the mockup's placer already does this kind of thing: a rule matches a cell's values to a piece from the kit. |
| A minor change to the existing engine | True of the Godot landscape mockup. Not true of the game's C simulation, where this part is not built at all. That work is owed for land as well, so space is the cheaper place to start. |

## What exists today

- **The rule.** Layer access is open or blocked per layer at every position (E-01 R-001-04). Today it is produced only by blocking discs of radius 600 placed at layout zones (E-17 R-114-04). That is a handful of discs, not a field.
- **The game's simulation (C).** The function that answers "is this layer open here" is a stub that always returns 0 (`csrc/tactical_mapgen.c`, `om_map_sample_layer_accessibility`). Obstacles are discs with no layer. Units cannot change layer yet; that is in the skill lab's engine work (layer changes, sight-based targeting, reach by type).
- **The landscape mockup (Godot).** `scenes/mockups/landscape/field_map.gd` makes continuous fields from noise and turns them into borders by threshold (the coast is the line where water crosses 0.5). `placer.gd` fills cells with kit pieces by rule. A Settled Reach kit exists. Turning "noise, then threshold" into five open-or-blocked maps is a small change there: on the order of a hundred lines, with height, water, rivers and slope left out.

## A quick test of the idea

`space_mask_check.py` in this folder. A 16,000 wu canvas at 100 wu per cell, five layers, six seeds each. Two ways of making the maps:

- **A.** Each layer gets its own independent noise.
- **B.** One block of noise in three dimensions, cut into five slices, so what is on one layer resembles what is on the next.

"Reachable" is the share of open space that belongs to the one biggest connected region, counting moves between neighbouring layers where both are open. "Crossable" is the share of positions where a unit could change between two neighbouring layers.

| Field | Blocked | A: reachable | A: sealed pockets | A: crossable | B: reachable | B: sealed pockets | B: crossable |
|---|---|---|---|---|---|---|---|
| Light | 15% | 100% | 0 | 72% | 100% | 1 | 78% |
| Medium | 35% | 100% | 1 | 42% | 99% | 3 | 53% |
| Heavy | 55% | 99% | 7 | 20% | 98% | 6 | 32% |
| Very heavy | 70% | 92% | 14 | 9% | 78% | 11 | 19% |

What it shows:

- **One dial gives the range Westley described.** The share blocked is the density of the asteroid field. At 15 percent the map is mostly open with a few limited sections. At 55 to 70 percent the open space is corridors, and places to change layer are scarce.
- **Sealed pockets appear from about 55 percent.** Some open space cannot be reached from the rest. A map needs a check that every place that matters is reachable, and a way to cut a tunnel when it is not. The bible already has the check for today's maps (reachable from all spawns and from staging, E-17 S-117).
- **The two methods differ in character.** With independent layers (A), layers have nothing to do with each other: an asteroid on layer 3 says nothing about layer 4, and the map stays connected mostly through layer changes. With slices of one block (B), asteroids are bodies that span several layers and openings line up into shafts. B is what gives "tunnels moving horizontally and vertically".

## What the idea leaves to decide

1. **How layers relate.** Independent maps, slices of one block, or asteroids placed as bodies and then marked onto the layers they pass through. The third gives the most control over the look and is the most work.
2. **Guaranteed ways through.** Check and cut tunnels, or throw away seeds that fail. Cut tunnels are also a feature: they are the deliberate corridors.
3. **Where to change layer.** A flying unit changes layer where nothing blocks, so a crossing is a place open on both layers. In a heavy field these are few. They are the space twin of a slope on land, and the natural place for a strongpoint.
4. **What blocked space does to sight and fire.** Presumably an asteroid blocks both on its layer. Whether it blocks a shot between layers is the open cross-layer question the layer lab already holds.
5. **Layouts.** The layout library stays (2026-10-02). The places a layout needs have to be open: the map is cleared around each of them, the opposite of today's blocking discs.
6. **Movement.** Routes today use one flat grid. Per-layer maps need a route per layer and links where a crossing exists. This is engine work that land needs as well.
7. **Ice that moves.** The bible's battlefield already drifts (E-17 S-118). Sheets that drift, and leads that open and close, fit the arctic picture. Later.
8. **Bases and resources in space.** Where a base sits (on an asteroid, in a cleared pocket), and whether resource sites are the asteroids themselves. Not looked at here.

## How land and space fit together

Both end in the same thing: an open-or-blocked answer per layer per position, plus the places where a unit can change layer. Land gets there from height (the ground fills the layers below it, so a blocked layer always has blocked layers under it). Space sets it directly, with no such limit. The simulation needs only the general form, so space is the general case and land is a special case of it. One sister system, two generators, one output.

## The mockup, first look (2026-10-02)

Built to `docs/northstar/plans/2026-10-02-space-kit-mode-spec.md` by a Sonnet Doer; kit `space` in the landscape mockup (`scenes/mockups/landscape/field_map_space.gd`, `kits/space.json`). Screenshots in `mockup/`, taken on the Mac with the QA driver (`scenes/mockups/landscape/qa/space.json`).

What the numbers say, canvas 24,000 wu: generate about 500 to 730 ms, placer 100 to 240 ms, 39,000 pieces at 15 percent blocked and 106,000 at 70 percent. Carving leaves nothing unreachable on seeds 11 to 16 at every density; with carving off, 7 to 13 regions are cut off at 70 percent, so the check has its positive control. Same seed and density give the same hash. Independent layers cut the share of crossings at 70 percent from 17 to 9.5 percent, as the Python check predicted.

What the pictures say, before Westley flies it:

- The mechanism reads: open corridors, blocked mass, a lit tunnel where one was cut, rings at the scarce crossings, and more blocked space as the slider rises.
- The look does not yet read as sheets of ice. Every blocked cell is a shard, so a heavy field is a spiky mass, and from the tactical camera the five layers stack into one cliff rather than five sheets. Flat slabs for the body of a blocked region with shards only at its edge, and a wider gap or a stronger tint between layers, are the first things to try.
- Open space is bare void. Something faint under it (a grid, or a dark water plane) would give the eye a reference.
- The crossing rings are small at tactical zoom and invisible at map zoom.
- Layer focus works (unfocused layers darken) and is the clearest way to read one layer.

## Westley's review of the first mockup (2026-10-02)

Verbatim: "So this isn't exactly what I had in mind, first of all it's only one layer. the "cities" are far too circular, it doesn't seem like you used the stochiacity of the existing biome engine. *cities* have very distinctive shapes. The wall traveling through them was nice. - It definitely doesn't read as ice sheets yet, it seems like a single layer. I imagined somethign more like this: [a photograph from above of arctic sea ice: large irregular floes with straight-edged, fractured outlines, narrow dark water channels between them, fields of small broken fragments, one large dark rock mass, open water in the gaps] this is a real picture in the arctic, think this but 5 different versions stacked together (would create a wicked, tight, thick asteroid field). We don't need a whole bunch of *assets* like shown in the mocket, we really just need a binary representation: shapes where there is no object, and space where there is object (just like the photo), passable vs inpassable space. 5 layers of different seeds create what I'm looking for for the *whole* map."

Read as:

- The five layers do not read; it looks like one. The look must show five sheets.
- The round clearings around the layout nodes read as circular cities. Nothing cleared may be a disc.
- The picture to match is fractured sea ice: plates with straight broken edges, narrow channels between them, rubble fields of small fragments, open water, and the odd large mass. Not noise blobs.
- No asset variety. A binary picture: object or no object, impassable or passable, drawn as flat plates.
- Each layer from its own seed, five stacked, giving a tight thick field over the whole map.

Pass 2 spec: `docs/northstar/plans/2026-10-02-space-kit-mode-spec.md`, section "Pass 2".

## Passes 2 and 3 (2026-10-02)

Pass 2 (`mockup/pass2/`) turned the generator from noise blobs into plates and the drawing into binary sheets, and was judged by the architect, not Westley: plates had ragged stair-stepped outlines, rubble covered half the map at low density, crossing marks cluttered everything, and top-down showed the union of all five layers. Pass 3 (`mockup/pass3/`) fixed those four: true jittered-lattice plates drawn as polygons with straight broken edges, rubble only beside kept plates, marks off by default, and top-down with a focused layer hiding the rest.

Pass 3 numbers, seeds 11 to 16: blocked share per layer 14 to 23 percent at density 15 and 65 to 71 at density 70; 0 unreachable regions in all 24 runs; 190 to 530 plate polygons per layer; generate about 540 ms and placer about 15 ms at canvas 24,000. Spec: `docs/northstar/plans/2026-10-02-space-kit-mode-spec.md`, passes 2 and 3.

The architect's read of pass 3, for Westley to confirm or overrule:

- Top-down with one layer focused reads like the photo: floes with straight edges, channels, open pools, rubble at the edges of packed areas.
- Plates are too even in size; the photo has a few huge floes among many small ones. A wider spread of plate sizes is the next knob.
- From the tactical camera the sheets above the camera hide everything, since five opaque sheets 1,400 wu apart put the camera inside the stack. How the camera and five stacked sheets work together is a design question in its own right, not a mockup bug; top-down with focus is the way to read it for now.
- Small defect: crossing marks are drawn in the focused top-down view although the HUD says they are off.

## Westley's review of pass 3 (2026-10-03)

Verbatim: "It's close, yes I agree they're too even in size, there should be more variety in density, other than that it looks really good, I'd say in the next pass let's also *connect* the layers together so there's not so much space in between them. Unless it's too soon for that and that's something the godot visual engine will handle and we're just designing the borders to pass to it."

Read as: plate sizes too even; more variety in density; connect the layers so there is less space between them. On the last point the architect's answer, which Westley accepted with "go": the gap between layers and whether blocked space lines up across layers are design (the layer height mapping for space, and a shared density map across layers); filling the gap with solid bodies where a spot is blocked on two neighbouring layers is the visual engine's job from the masks, and the mockup fakes it so the result can be judged. Pass 4 spec: `docs/northstar/plans/2026-10-02-space-kit-mode-spec.md`, "Pass 4".

## Suggested next step

Westley flies pass 3 (Kit: space; Top-down button; keys 1 to 5 to focus one layer, 0 for all; C for crossing marks; sliders for density, layer gap and plate size).

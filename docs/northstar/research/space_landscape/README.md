# Space-era landscape: first investigation

**Approved 2026-10-06, with a note.** Westley, verbatim: "space landscape approved as well (note on the space landscape, we're going to have to design a clever system of allowing a vision *tube* for the player through upper layers that cover their line of sight on units on the lower layers, I've seen other RTSs do it where there's an object blocking your LOS but it becomes invisible with a small effect to make it clear to the user that that's what's happening. It'll be a hard problem to solve given the multi-layer nature of this game, and that'll be fun figuring out with the camera view, I just want a note of that when approving the prototype because I very much can't see certain areas of the landscape because of the limited method we're currently using (classic rts))". The note is recorded as Q-S3-01 in the register and is the first requirement of the S3 camera options page.


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

## Pass 4 (2026-10-03)

Built to the pass 4 spec with two corrections the Doer's measurements forced: the keep roll is shared across layers when "Shared density" is on (sharing only the density noise moved the stacked-cell count by 4 percent; sharing the roll moves it from 18,200 to 21,600 cells per layer pair at density 55), and the size spread is set from the noise's quantiles so the slider means what it says (at 1, a quarter of lattice centres split; removals cap near 8 percent because of the no-holes rule). Screenshots in `mockup/pass4/`.

What the pictures show: from above the stack, the field now reads as one thick body of stacked floes with channels and shafts through it, which is the "wicked, tight, thick asteroid field" Westley asked for; a focused layer from the top shows large floes among small ones, rubble, and the shaded sides of the fill where the layer below is also blocked. Blocked-share averages 20, 38, 56 and 67 percent at slider 15, 35, 55 and 70; 0 unreachable regions in all 24 runs; generate about 1.1 s at canvas 24,000 (the fill walls cost about 0.4 s of it).

Open after pass 4, for Westley:

- The camera among five stacked sheets (the tactical band sits inside the stack).
- Whether "Shared density" on is the default for the game, and the layer gap for space eras (the slider's 1,000 wu default is a guess).
- Whether removals should be allowed to cluster (bigger floes) at the cost of the no-holes rule.

## Westley's question after pass 4 (2026-10-03): priorities and cost

Verbatim: "I'm seeing a lot of objects, is the level of detail we're introducing going to be a problem for fps/output efficiency? Analyze the way we're generating, investigate if we're making it harder for the godot engine to operate effciently because it's being passed something too complex. - This comes from s11_d55, the small gaps look cool but I doubt they'd be functional in the real game (most ships would be too big to pass through it) and it's everwhere, it's functionally one large "block", but it's split into little pieces. In s11_d15 as well there's a *ton* of little pieces, which is great for depth/detail, but we're not designing visuals right now we're designing the landscape engine for space. I just want to take a step back and make sure our priorities are in order. *detail is good, in the right locations*, and my query is regarding whether this is the right location or not."

### What the mockup hands the renderer (seed 11, canvas 24,000, measured headless)

| Density | Draw surfaces | Triangles | of which fill walls | Pieces counted | Open cells of 290,405 |
|---|---|---|---|---|---|
| 15 | 22 | 241,584 | 35,000 | 19,833 | 226,565 |
| 55 | 22 | 1,760,365 | 121,716 | 63,164 | 127,100 |
| 70 | 22 | 3,158,078 | 155,040 | 79,921 | 95,978 |

- Draw calls are not the problem: one mesh per layer per kind, 22 in all.
- Triangles are: 1.8 to 3.2 million at the heavy end. The architect first blamed the gap fill; the pass 5 Doer measured the real cause: the hidden crossing-mark rings, drawn as 2.9 of the 3.2 million triangles at density 70 even while hidden. The gap fill was already outline walls at about 120,000. With the rings cut to a coarse mesh the visual view is 154,000, 302,000 and 340,000 triangles at densities 15, 55 and 70. A GTX 1070 draws that without effort. The lesson for the record: measure before blaming.
- Generation is 1.1 s in GDScript, a mockup cost; in C it is tens of milliseconds.
- In the game the renderer never draws per cell: the decided direction (7D) is a coarse functional map in the simulation and detail drawn by the client at the level the zoom needs. The mockup is wasteful by construction, not by concept.

### The priorities question

Westley is right, and the numbers make the case. The sim's unit collision radius is 15 wu and a formation is 200 wu wide. The mockup's channels are 160 wu and the rubble gaps 100 wu: a single ship squeezes through, a formation never does. So most of the small gaps are not passages in play. Functionally, a packed area is one block, and the gaps are visual.

What follows:

- **The functional map has a minimum passage.** Anything narrower than a chosen width is solid in the simulation. The width is Westley's number (it should be tied to the formation width, so a formation can pass what the map says is open). That makes the simulation's mask coarse, honest, and cheap.
- **The detail is the client's.** Cracks, rubble, broken edges and small gaps are drawn by the client from the same seed, as decided in 7D, and never enter the simulation. They are the "right location" for detail: on screen, at the edges of real passages and real bodies, and dropped at distance by level of detail.
- **The mockup should show both.** A "functional" toggle that draws the simulation's mask (closed at the minimum passage) over the pretty one, so the two can be compared on the same map.

Open, for Westley: the minimum passage width for the functional map.

## Decisions (2026-10-03): passage widths

Westley, verbatim: "300 sounds good, but I want to sprinkle in little gaps for the smaller ships. The units aren't sized correctly right now, and there's going to be a unit that I want to be able to pass through gaps that other ships can't (little micro shits), I want to make sure there are little sparatic (5-10% of the landscape, in batches to induce strategic depth, like little sections of region that players can take advantage of the fact that small units can get through a *tunnel/gap*) sections. - The level of detail i see in s11_d55 would be great for the types of gaps those little ships could get through, and I'd like to retain the code that built that formation, just in a reduced capacity for the 5-10% that I referenced. Record these decisions."

Recorded as:

- **Minimum passage for the functional map: 300 wu.** Anything narrower is solid in the simulation for ordinary units.
- **Two passability classes.** A small unit class (a micro craft, to be designed) can pass gaps that other ships cannot. Units are not sized correctly yet; the small craft's size, and so the width of the gaps it fits, is open.
- **Small-craft gaps are sprinkled, in batches.** They cover 5 to 10 percent of the landscape, as little sections of a region, not everywhere, so a player can take advantage of a tunnel or gap that only small units get through. This is strategic depth on purpose.
- **The fine fracture of pass 4 is kept for those sections.** The code that made s11_d55's detail stays, used at reduced scope: inside the 5 to 10 percent, the fine channels and rubble gaps are functional for small craft; outside it, anything under 300 wu is solid for everyone, and fine detail there is the client's to draw.

Open: the small craft's size and gap width; how the 5 to 10 percent is chosen (which plates, which layers); whether the batches are placed by the layout (near objectives and resources) or by the noise.

## Pass 5 (2026-10-03)

Built to the pass 5 spec. Screenshots in `mockup/pass5/`: the same map in the visual view, the ordinary-unit view (gaps under 300 wu solid) and the small-craft view (orange is open to small craft only), with the small-craft section outlined, plus the "sections near layout" variant.

Measured, seeds 11 to 16: ordinary-unit reachability 0 unreachable at every density; small-craft sections 7.5 to 8.0 percent of each layer against the 7.5 slider; cells open to small craft only 1 to 2.5 percent per layer at density 55; triangles 154,000 to 340,000. Generation 1.5 to 3.5 s in GDScript (the two extra masks and the plate-path joining), a mockup cost.

Two things to know:

- Joining every cut-off pool to the ordinary-unit map costs blocked share at the heavy end: density 70 measures 54 percent blocked, not 67. Closing gaps under 300 wu makes many more pockets, and each is joined by dropping plates. Left as is; whether the slider should be rescaled is a tuning question for later, not a design one.
- The functional views look like blobs, not floes. That is right: the straight edges and channels are the client's picture, the blobs are what units can and cannot pass.

Open after pass 5: the camera among five stacked sheets (next, as design options); the small craft's size (Q-166-05); how the sections are chosen (two ways are in the mockup to compare).

## Pass 6 (2026-10-03)

Westley asked what the teal and brown lines in s11_d55 were (teal: frames around plates dropped to join cut-off regions; brown: the large mass and the backdrop; orange: the small-craft section). Pass 6: the debug frames are off by default (key F), and cut-off regions are joined by widening one channel to 300 wu instead of dropping whole plates, with plate dropping kept behind a "Join" toggle for comparison.

Measured, seeds 11 to 16, both modes 0 unreachable: at density 55, drop removes about 100 plates per map and lands at 52 percent blocked; widen opens about 50 channels (3,100 cells) and lands at 56. At density 70, drop removes 262 plates and lands at 54; widen opens 125 channels and lands at 65, so the shortfall against the slider is gone. Widen is also faster (2.4 s against 3.5 s in GDScript) and keeps the floe look, since a widened channel is a straight cut through a plate. Triangles at density 70: 479,000.

Side-by-side pictures, same seed, same camera, top-down, layer 3: `mockup/pass6/11_d35_drop_vs_widen.png`, `11_d55_drop_vs_widen.png`, `12_d55_drop_vs_widen.png` (drop on the left, widen on the right), and `11_d55_angled_widen.png`.

## Suggested next step

Westley reads the pass 6 side-by-sides and flies the mockup (V cycles views; F shows the join frames; Join toggle). Then the camera question is designed as options.

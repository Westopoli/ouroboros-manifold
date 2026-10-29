# Batch A follow-up 3 and 4: the terrain-obeys pictures, colour by colour, and the stripes

Written 2026-10-21 for Westley by an Engineer (Sonnet 5.5). It answers your seven questions of 2026-10-18 on the two terrain-obeys pictures (Batch A points 3 and 4: the failing seed 1 map and the passing seed 3 map, stored as `docs/northstar/story_reviews/shots/proto-terrain-obeys-1/obey_16000_1.png` and `obey_16000_3.png`). The review queue recorded your word on the seed 3 picture as "Not approved, need context on coloring"; this is the context. Nothing in the repo's code was changed. The evidence is the branch code (`push/proto-terrain-obeys-2`, f57af240; line numbers below are from that tip, and pass 1, 804f666b, which drew your pictures, has the same colours except the carved-cell dots) and headless runs in a private virtual display, never your screen.

**In short.**
- The ground colours are the landscape mockup's own walk view, not something the layout engine drew. The shot had no legend for them (the panel that has one was hidden by the shot driver) and its one caption line used the word "blue" for the light-blue wide-route lines, which is not the blue of the water. That is the whole doc-versus-picture conflict.
- Dark blue is water. Green is ground a walker can reach from the white square. Purple is ground the walker cannot reach: about three quarters of it is over the 35-degree limit and about a quarter is flat but cut off.
- The red circles are the objective, the resource sites and the far base, as you read them. Red means that place failed its check.
- The vertical stripes are not from the obey layer and not from the terraces. They are in the landscape alone, at the same place, and come from one loop that fills lakes in the landscape generator (section 4).
- The black squares are high points the walker cannot reach, not the lookouts. The lookout is the small pink ring, and nothing checks that it can be reached (section 5, your C10).

## 1. Your questions, in order

**1. "Is the blue where 'water' is? (impassable)"** Yes. A cell is water when the generator's water value is 0.5 or more (the sea below elevation 0, plus lakes and rivers); the walk view paints every water cell dark blue and the walk flood never enters it (`pass4_terrain.gd:513-515`, `:703-705`). The caption's "blue = big-width routes" means the thin light-blue line instead (`obey_overlay.gd:7`).

**2. "What represents routes carved? The orange lines?"** In the pictures you saw nothing is carved: the orange lines are routes the checker found over ground that already walked, thin orange for the narrow route (180 wu) and thicker light blue for the wide one (600 wu) (`obey_overlay.gd:6-7`, `:92-105`; search `obey_layer.gd:942-975`). Finding too few routes is why pass 2 added carving; carved cells are the magenta dots (`obey_overlay.gd:8`, `:90-91`; carve `obey_layer.gd:505`), seen in `shots/proto-terrain-obeys-2/obey_16000_1.png`.

**3. "'red circles mark points no wide road reaches' yet it appears to me that the red circles indicate objectives and points of interest."** You read it right: each circle is the flat pad of a place the layout asked for (two bases, the objective, two resource sites), and red is that pad's failing colour, not a separate mark. A pad goes red when its ring is over 35 degrees, or it has fewer narrow routes than rolled, or no wide route (`obey_overlay.gd:106-108`; `obey_layer.gd:1083-1085`); in seed 1 the four red pads each have 2 narrow routes of 4 and no wide one, so the caption was true there but gave one of three reasons. In seed 3 the same circles are blue (bases), yellow (objective) and teal (sites) (`obey_overlay.gd:10`).

**4. The vertical straight lines at the top right, the "bug with the lowest layer where water starts to come in", the lines cutting through the lanes of water.** A bug, but not in the layers and not in the obey pass: the landscape alone, with no obey layer, has the same stripes at the same place and strength (section 4, crops and numbers). The cause is the loop that fills lakes in the landscape generator, which leaves single columns of land between single columns of water (`field_map.gd:467-490`); the lines cutting the water lanes are the same thing.

**5. "Are those black squares the lookouts? All of them appear unreachable."** No, they are peaks: the highest cell of its 9 by 9 cell neighbourhood on layers 4 and 5, painted black when the walker flood from the white square cannot reach it at 35 degrees (`pass4_terrain.gd:551-571`, `:681`, `:724-725`). Not all are unreachable: seed 1 has 15 peaks of which 5 are reachable (teal), seed 3 has 9 of which 2 are. The lookout the layout asked for is the small pink "vantage" ring (`obey_overlay.gd:122-124`), see section 5.

**6. "What are the teal squares?"** Peaks the walker can reach (`pass4_terrain.gd:680`, `:724-725`). The resource-site rings are a near-identical teal, but they are rings (`obey_overlay.gd:10`).

**7. "What does the green represent compared to the blue? ... purple ... miscoloration ... large hill ... plateau in center."** Green is land the walker can reach from the white core square, blue is water, and purple is land it cannot reach, which is not quite "steep": 78 percent (seed 1) and 74 percent (seed 3) of the purple cells are over the 35-degree limit and the rest are flat but cut off (`pass4_terrain.gd:287-310`, `:715-719`; the mockup's own legend says "magenta cut off", `pass4_ui.gd:312`). The limit and the way slope is measured match the game's (`csrc/tactical_move.c:358`, `csrc/terrain.c:833-854`). Colour is painted per 100 wu cell with no blending (`pass4_terrain.gd:738-788`, about 6 pixels a cell), so "a few purple pixels" is a few steep cells: a big hill under 35 degrees is all green, and marks on a plateau are single cells where a bump passes 35 degrees. One real effect is not a colouring error: the pads' cones flatten the ground (section 6), so the seed 3 hill is lower and smoother in the picture than in the landscape alone.

## 2. Legend

Ground (the walk view, `Pass4Terrain.cell_colors`, `pass4_terrain.gd:687-726`). On your screen these looked paler (pale green, steel blue, pink-lilac); the colour constants are at `pass4_terrain.gd:673-682`.

| What you see | What it is | Code |
|---|---|---|
| Dark blue cell | Water. Never entered. | `pass4_terrain.gd:673`, `:703-705` |
| Green cell | Land the walker reaches: dry, own slope within 35 degrees, joined to the core by the flood | `:678`, `:715-717`, flood `:287-310` |
| Purple / magenta-pink cell | Land the walker does not reach: own slope over 35 degrees, or flat but cut off | `:679`, `:718-719`; legend text `pass4_ui.gd:312` |
| Gold cell | Ramp: ground cut at a walkable grade to link layers (carved cells also count as ramp) | `:682`, `:716`, `cut_ramps` `:321-388`; `obey_layer.gd:808-811` |
| White square (5 by 5 cells) | The landscape's own city core, where the walk flood starts. Not the layout's objective ring. | `:721-723`, core `:654` |
| Thin yellow ring beside the white square | The landscape's own objective node marker, drawn at ground level; the white square sits on that node's cell | `map_view.gd:208-214`, `pass4_terrain.gd:654-659` |
| Black square (3 by 3 cells) | A peak (layers 4 and 5, highest in 9 by 9 cells) the walker cannot reach | `:551-571`, `:681`, `:724-725` |
| Teal-cyan square | A peak the walker can reach | `:680`, `:724-725` |
| Lighter and darker tone inside one colour | Relief shading only, no meaning | `:757-760` |

Overlay (drawn on top by `obey_overlay.gd`, from `obey_layer.gd` results).

| What you see | What it is | Code |
|---|---|---|
| Thin orange line | A narrow-width (180 wu) route found between base A and a point. Found, not carved. | `obey_overlay.gd:6`, `:99-105`; `obey_layer.gd:942-975` |
| Thicker light-blue line | A wide-width (600 wu) route. The caption's "blue". | `:7`, `:92-98` |
| Magenta dot (pass 2 only) | A cell the engine carved to make a route | `:8`, `:90-91`; `obey_layer.gd:505` |
| Circle, blue | Pad of base A or base B | `:10`, `:106-110` |
| Circle, yellow | Pad of the layout's objective (not the white square) | `:10` |
| Circle, teal | Pad of a resource site | `:10` |
| Circle, red | That pad failed: ring over 35 degrees, or fewer narrow routes than rolled, or no wide route | `:107-108`; `obey_layer.gd:1083-1085` |
| Label `name sN bM` | N narrow and M wide routes found to that point | `:110` |
| Thin white line | The line between the two bases | `:111-113` |
| Short green bar | The choke corridor at its asked width; turns red when the measured width is more than one cell off | `:114-117`; `obey_layer.gd:1062-1063` |
| Two orange rectangles beside the bar | The choke's wall span, 900 wu each side, ground raised 400 wu | `:118-120`; `obey_layer.gd:406-427` |
| Small pink ring labelled "vantage" | The lookout the layout asked for | `:122-124`; `obey_layer.gd:428-447` |

What conflicts between the caption and the code: (a) the caption says "red circles mark points no wide road reaches", the code paints a pad red for any of three clauses (answer 3); (b) the caption's "blue" is the light-blue line, the ground's blue is water (answer 1); (c) the batch text says "a lookout" and you saw black squares, which are peaks (answer 5); (d) the ground colours had no legend at all, because the shot driver hides the pass-4 panel that carries it (`obey_layer.gd:1137-1143`, line 1142 hides `p4._panel`), and the on-picture caption lists only the overlay colours (`obey_overlay.gd:125`).

## 3. How this was checked

I re-ran pass 1 headless with its own `--shot` and compared with your two pictures: every panel line is equal except the timings (`obey_panel_16000_1.txt` and `_3.txt`), and a rough colour classifier agrees on 96 percent (seed 3) and 86 percent (seed 1) of the map pixels, so these are the same cells. My renders use the Compatibility renderer under llvmpipe, so their colours are more saturated than on your screen. For the stripes I used a scratch driver (not committed) that runs the obey layer's own shot sequence (`obey_layer.gd:1146-1178`: walk view, limit 35, top-down camera at canvas times 1.02, panels hidden) on three trees: pass 6b alone (84e1db89, the approved landscape, no obey layer), obey pass 1 (804f666b) and obey pass 2 (f57af240), at seeds 1 and 3, canvas 16,000, and dumped the height, water, slope and reach arrays.

## 4. The stripes

Crops of the top-right of the seed 1 frame, at twice the size (same camera in both):

- [landscape alone, pass 6b, no obey layer](../../../story_reviews/shots/proto-terrain-obeys-stripes/landscape-6b-alone-seed1-topright.png)
- [with the obey layer, pass 1, as you saw it](../../../story_reviews/shots/proto-terrain-obeys-stripes/obey-pass1-seed1-topright.png)
- [diagnostic: landscape alone with the lake loop run in queue order](../../../story_reviews/shots/proto-terrain-obeys-stripes/landscape-6b-alone-queue-order-flood-seed1-topright.png)

**Verdict.** The stripes are in the landscape-only frame, at the same place and the same strength. They are not an artefact of the obey pass. Measured as land-to-water flips per row (a stripe field flips 12 to 15 times a row, open water or open land 2 to 3):

| frame | seed 1, top-right box (cells x 118-160, y 0-80) | seed 3, top-centre box (x 65-110, y 0-60) |
|---|---|---|
| landscape alone (pass 6b) | 14.9 per row, 69 of 81 rows with 6 or more | 12.2, 57 of 61 rows |
| obey pass 1 (your pictures) | 14.9, 69 of 81 (no cell of the box changed height) | 12.4, 57 of 61 |
| obey pass 2 | 14.7, 69 of 81 | 12.6, 57 of 61 |
| landscape alone, benches off | 16.6, 70 of 81 | 12.0, 57 of 61 |
| landscape alone, lake loop in queue order | 2.3, 4 of 81 | 3.1, 0 of 61 |

**Cause.** `FieldMap._flood_lake` (`scenes/mockups/landscape/field_map.gd:467-490` on the obey and 6b trees) fills a lake by taking the most recently added cell from its list (`queue.pop_back()`, line 474, a depth-first walk) and stops after 1,500 cells (line 473). On a basin larger than that the walk is cut off while it has only filled every second column, so water runs in 1-cell columns with 1-cell lines of land between them, on ground 300 wu and more above the sea (landscape alone, seed 1, row 30, cells 126 to 136: water, land, water, land). That fits your reading of straight, almost man-made lines where water comes in, and the lines through the lanes. Two checks: switching the pass-4 terraces off (`bench_override` 0) does not remove the stripes (14.9 to 16.6), so it is not the terraces; running the same loop in queue order in a scratch copy, reverted and not committed, removes them (14.9 to 2.3, 12.2 to 3.1) and the lakes come out as whole bodies (third crop). The same loop is on main's landscape mockup (pass 5, line 461 of the same file), the C engine has no lake code yet (no `lake` in `csrc/`), and the stripes are on the right edge of the pass-2 picture approved on 2026-10-21 (`shots/proto-terrain-obeys-2/obey_16000_1.png`). If lane P rev 6 writes the C water pass from the mockup's procedure, this loop is the part not to copy as it stands. I did not fix it: it is one line in a mockup file and not asked.

## 5. The lookouts (the vantage ring) and the black squares

What the code builds. The layout's vantage is placed 1,500 wu off the choke on a seeded side, moved to the other side if its mound would touch a pad (`obey_layer.gd:236`, `:288-298`). The mound is 300 wu above the median ground within 600 wu, with one ramp face toward the choke at 28 degrees and 60 degrees on the other sides (`obey_layer.gd:428-447`). It is drawn as a 250 wu pink ring (`obey_overlay.gd:122-124`).

What the code checks. Nothing about it. Routes are searched, carved and counted only for the four points in `POINTS` (`obey_layer.gd:18`: the far base, the objective, the two sites); the check has no vantage clause (`obey_layer.gd:1034-1099`) and the panel has no vantage line (`:1104-1120`). The pass-1 spec's route check also names only the other base, the objective and both sites (point 3 of `plans/2026-10-15-terrain-obeys-mockup-spec.md`).

What the finished ground shows (my reading, with the check's own walk mask, four-neighbour steps, one cell wide; the pictures do not show it). The cell at the vantage point joins base A's walkable ground in pass 1 seed 3 and in pass 2 seed 3, and does not in pass 1 seed 1 or pass 2 seed 1. So a lookout being reachable is an accident of the land, in two of four renders.

The black squares against the rule. R-192-03 says about 30 percent of peaks may be unreachable on foot (`docs/bible/epics/E-17-map-generation.md:303`), and the pass-4 spec expected about 70 percent reachable and said to report what the maps give. The two pictures give 5 of 15 reachable (33 percent) and 2 of 9 (22 percent); the landscape alone gives 1 of 10 and 1 of 15. In seed 1 two of the black squares sit inside the choke's wall blocks, which the peak finder counts as peaks.

Whether a vantage needs two routes, or one slope path is enough, is your decision and is on your page as C10 ("Vantage points need two paths?" in `plans/decision_pack_2026-10-18/batch.md`). Nothing here changes it.

## 6. Found on the way (not asked)

- The obey pass reshapes much more of the land than the pads. It clamps the ground into 28-degree cones around every pad out to 2,400 wu beyond the pad's edge (`obey_layer.gd:334-355`, reach `:44`, clamp `:354`). Against the landscape alone it changed the height of 21 percent (seed 1) and 25 percent (seed 3) of the cells in pass 1, 39 percent and 31 percent in pass 2, and cut steep cells from 7,015 to 5,107 (seed 1) and from 7,910 to 5,071 (seed 3). The seed 3 hill on the right has its crest cut from 2,370 wu to 1,719 wu and goes from 39 percent purple to 13 percent; seed 1's centre plateau box goes from heights of 762 to 2,584 wu to 853 to 1,812 wu, and from 33 to 14 percent purple (in the picture 11 percent of its cells are single steep cells and 3 percent flat pockets cut off, which are the marks you saw). This is not the stripes, but it is part of why the maps read as made rather than grown, and it fits your "large hill but only a few purple pixels".
- Each picture has two objectives: the white square with the thin yellow ring (the landscape's own, where the walk flood starts) and the big ring labelled "objective" (the layout's request). They sit in different places.

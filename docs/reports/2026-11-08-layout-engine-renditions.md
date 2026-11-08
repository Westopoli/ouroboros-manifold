# Layout engine renditions, reconstructed 2026-11-08

This is a reconstruction from the repository, because the chat that numbered the renditions was lost.

Westley asked for the history of every layout-engine rendition. Only one number came down to me: R5 is "layout first, landscape obeys". I numbered the rest in date order. My numbering is therefore my own; the dates, branches and quotes below are what the repository holds. I found eight distinct renditions, which matches the count Westley was given. Three of the numbers (R3, R4, R7) rest on a judgment about where one design ends and the next begins; I say so where it applies.

## Summary

| # | Name | Dates | Where it lives | Fate |
|---|---|---|---|---|
| R1 | Hand-drawn library and Python instantiator | 2026-04-14 onward | `simulation/layout_library/`, `layout_instantiator.py`, `fairness_evaluator.py`, `map_generator.py` | Runs; only the retired Python pipe read it; audited unusable 2026-10-18 |
| R2 | C port of R1 (S-112 to S-119) | 2026-09-22 to 2026-10-07 | `csrc/tactical_mapgen.c`, `csrc/mission.c` | Stubs; nothing calls it |
| R3 | Landscape mockup, hand skeleton first | 2026-09-21 | `scenes/mockups/landscape/` on main | Superseded the same day |
| R4 | Landscape mockup, terrain first | 2026-09-21 | same, commit `2533efb6` | Concept approved; layout-from-terrain idea dropped 2026-10-03 |
| R5 | Layout first, landscape obeys | 2026-10-03 to 2026-10-21 | passes 5, 6/6b, terrain-obeys 1 and 2 | Approved as prototypes; never merged whole; now the restart point |
| R6 | Layout prototype pass 1 (kit pieces) | 2026-10-04 | `push/proto-layout` | Never shown to him; reference only |
| R7 | C places engine (lane P) | 2026-10-13 | `csrc/layout_engine.c` | 71 tests green; nothing calls it |
| R8 | S-247 kit engine (Assault) | 2026-11-05 to 2026-11-08 | `s/S-247-layout-kit-assault` | Round A1 denied 2026-11-08; unlanded |

## R1. Hand-drawn library, Python instantiator (2026-04-14 onward)

Files: eight JSON layouts in `simulation/layout_library/` (first commits `7c8a3de7` and `1d296a6a`, 2026-04-14), `layout_instantiator.py`, `fairness_evaluator.py`, `map_generator.py`, `gradient_placer.py`, `spine_drift.py`.

How it generates: a layout is about a dozen typed dots (nine types) joined by lines, with positions as shares of one square. The instantiator picks a layout, scales it to the canvas with a small jitter, and the gradient placer lays fields around it. A fairness evaluator scores four ratios.

Objective: a dot on the graph. In all eight layouts it sits beside one side, which the later rule of equal distance (R-191-04) forbids. Spine drift can move objectives along routes.

Westley's words: on the library, "I don't care what the shape is, I only care about those numbers" (Q-191-03, quoted in `docs/northstar/research/layout_engine/README.md`). On 2026-11-08, remembering it: "I remember a python layout engine that produced lots of variety, months ago" (`story_reviews/westley/ruled.md`, round A1 row).

Fate: still runs and still fails its own fairness check at the test seed. The 2026-10-18 audit (`docs/northstar/research/layout_engine/library_audit_2026-10-18.md`) found none usable as drawn and has never been ruled on. It was moved to the legacy area on 2026-11-05. Note: `map_generator.py` line 11 imports `place_cover_polygons` from `gradient_placer`, and line 126 uses it, so the import is live in that file as written; the name was added on 2026-05-25 (`2e1768bb`). The brief called the import dead since that date. I could not confirm that it is unused. Please check that wording before it goes anywhere.

## R2. C map generator from the May design (S-112 to S-119)

Files: `csrc/tactical_mapgen.c` and the mapgen state in `csrc/`, frozen into the header on 2026-09-22 (`1eeb0a5e`); B15m series 2026-09-24; PP-mapgen 2026-10-02 (`c6ec9461`, `809c7234`). `csrc/mission.c` still instantiates a fixed MVP layout (comment "B9-6 fixed MVP tactical layout").

How it generates: meant to pick a library layout, scale it, and lay gradients, a straight port of R1.

Objective: as R1, with moving objectives (S-118) planned.

Westley's words: I found none specific to this port.

Fate: per the 2026-11-05 triage, 44 empty stubs and 23 of 24 tests red since 2026-10-07. No live mission calls `om_map_generate`. The bible marks S-114 to S-119 "rewrite pending". I did not re-count the stubs.

## R3. Landscape mockup, hand skeleton first (2026-09-21)

Files: `scenes/mockups/landscape/field_map.gd` and the placer, commits `c49009a3`, `04e4d7d2`, `36ac6e35` ("four skeletons, seed picks one").

How it generates: a hand-authored skeleton of waypoints is chosen by seed and jittered (3 percent, then up to 8 percent across four skeletons), and gradients, cities and fields grow around it.

Objective: the city core in the skeleton.

Westley's words (2026-09-21, `docs/northstar/research/landscape_design/README.md`, mockup review 1): "Different seeds don't differ (regenerate doesn't seem to do anything but freeze the game for a little bit)."

Fate: replaced the same day by R4. Judgment note: R3 and R4 are one mockup at two passes; I count them apart because the generator's direction reversed between them.

## R4. Landscape mockup, terrain first, waypoints second (2026-09-21)

Files: same directory, commit `2533efb6` ("terrain first, waypoints second (pass 3)"), `9e9daa23`, `753e5705`.

How it generates: layered noise makes elevation, water and biome bands; the spine nodes (city core, chokes, vantages) are found on that terrain by rules, so the layout is derived from the land. No skeleton library.

Objective: the city core, placed at a river bend, valley floor or defensible hillside.

Westley's words (2026-09-21, same README, mockup review 2): "Protoptye has my go ahead (though, the elevation changes leave much to be desired ...". He wanted big elevation, cities that follow rivers, and "stochiastic seperations, very similar to the Roblox biome/landscape generation tool."

Fate: the concept and the terrain noise survive in the C terrain code. The "layout derived from terrain" order was reversed on 2026-10-03 (R5). Q-119-02 was answered "no skeleton library" here, which R5 and R6 later undid.

## R5. Layout first, landscape obeys (2026-10-03 to 2026-10-21)

Three stages, all land only:

- Pass 5, 2026-10-03, commit `44e96b4f`, on main: `pass5_layout.gd`, `pass5_places.gd`, `pass5_ui.gd`. It takes one of the eight R1 layouts and bends noise terrain to it: levelled pads at each node, a choke corridor at the layout's width with walls, A* route cutting with graded strips and bridges, vantages moved to high ground, then scores places (bases, economic, resources, expansion, settlements) by walking distance.
- Pass 6 and 6b, 2026-10-03 and 2026-10-04, `push/proto-land-iter` (`a184524d`, `84e1db89`): the layout shapes the terrain as it is made (node heights, valleys carved along edges, summit cones), and the wall pieces are removed.
- Terrain-obeys passes 1 and 2, 2026-10-15 to 2026-10-18, `push/proto-terrain-obeys` (`73c7aa1b`, `804f666b`) and `push/proto-terrain-obeys-2` (`d93ffcc3`, `f57af240`): `obey_layer.gd`, `obey_overlay.gd`. Layout requests (pads, choke, vantage) with route carving, the objective moved off the base line, and canvas scaling. 316 tests green there per the triage.

Objective: a typed node of the layout, with a 600 wu pad. Equal walking distance was checked and failed for the objective in every pass 5 run; terrain-obeys pass 2 moves it off the base line.

Westley's words:
- 2026-10-04, on this mockup: "I don't understand how the objective is supposed to move, what the layout is supposed to induce, it feels cobbled together randomly." (`research/layout_engine/README.md`)
- 2026-10-04: "layout comes before landscape. The layout engine should be prototyped and integrated before the landscape engine." (`docs/northstar/ROADMAP.md`, section 5)
- Feedback pass 6 answered: "What's up with all the walls in the prototype?"
- 2026-10-05, on pass 6b: "land mockup is fine as long as it's understood that the layout engine underneath it is flawed at the moment, it's close to what I want just not quite there on the scale/size." (`research/landscape_design/README.md`; the triage attributes this to pass 5, but the README says pass 6b.)
- 2026-10-21, on terrain-obeys pass 2: "Approved", and for the 8,000 wu shot "We won't have a map this small in reality, but approved." (`story_reviews/westley/verdicts_2026-10.md`)
- 2026-11-08: "I'm happy with R5, it's the best start point we have. I'd like to recover that code, I'd like to see 5 variations (seeds) of this engine as it is. We're going to build on it and make it better." (`decisions.md`, DEC-layout-r5-start-point-2026-11-08)

Fate: pass 5 code sits on main in `scenes/mockups/landscape/`; the pass 6 and terrain-obeys code exists only on the `push/` branches and was never merged. Recovery is under way on `s/layout-r5-recovery`. Its input is still the eight R1 layouts, which the audit rejected, so the layouts feeding it are the weak part.

## R6. Layout prototype pass 1, kit pieces (2026-10-04)

Branch `push/proto-layout`, commits `0d7a8c48`, `819d7a75`: `scenes/mockups/layout/layout_gen.gd` (759 lines), `layout_checks.gd`, `layout_kits.json`, `layout_selftest.gd`. Spec: `docs/northstar/plans/2026-10-04-layout-prototype-pass1-spec.md`.

How it generates: an 8x8 grid of districts (home, near, contested, objective) with a seeded division pattern; slots in the home districts, growth rules in the contested ones (crossings with a way round, heights with two ways up, prizes, commons, a hidden approach); sides related by mirror, rotate or grown separately; five candidates made and the best by its checks kept.

Objective: beside the defender on Assault and Defensive Stand; travelling a walking route on Interception.

Westley's words (2026-10-04, `ambiguity_register.md` Q-191-06): "Instead of having a kit for the whole map, I'd like to have kits for specific puzzle pieces of the map, and then organize the puzzle pieces differently every time." On the first prototype being a flat diagram alone: "#3: agreed".

Fate: per the triage never shown to him, and he ruled on 2026-10-06 that there would be no separate prototype (ROADMAP carries both lines). On 2026-11-08 he rescinded his earlier "defaults for the rest" ruling on how the two sides relate (Q-191-13). The branch is reference only.

## R7. C places engine, lane P (2026-10-13)

Files: `csrc/layout_engine.c` (commits `61a60af8`, `da57d6cd`, `85ef4e96`, 2026-10-13), spec `docs/northstar/plans/2026-10-13-places-lane-spec.md`.

How it generates: given terrain callbacks, an objective and two base positions, it scores a grid and places towns, resource sites and expansion sites by rule, with about 30 draft numbers.

Objective: an input, not something it makes; beside the defender on assault and defence archetypes, the midpoint otherwise (Q-191-11).

Westley's words: none specific; the Q-191-11 ruling (2026-10-04, "beside the defender where the archetype is an assault or a defence") is the rule it carries.

Fate: 71 tests green per the triage; nothing calls it, and its wiring step was never built. It places points only: no chokes, widths, vantages or lanes. Judgment note: I count it as a rendition because it is the only C code in the repo that makes a layout from a seed, though it is smaller than the others.

## R8. S-247 kit engine, Assault (2026-11-05 to 2026-11-08)

Branch `s/S-247-layout-kit-assault` (unlanded): `csrc/layout_kit.c`, `layout_kit.h`, `layout_kit_graph.c`, `layout_kit_pieces.c`, renderer `scripts/layout/render.py`, story `docs/stories/S-247.md`. Pictures: `story_reviews/westley/layout_engine/round-A1/`.

How it generates: a C port of R6's idea, written from a description rather than from the source. One road joins two bases 7,600 wu either side of the centre of a 24,000 wu canvas, with exactly one choke, one vantage and one pair of resources. Sides relate by mirror, rotate or separate.

Objective: hung beside the defender's base (Q-191-11).

Westley's words (2026-11-08, `ruled.md`, round A1, deny): "the biggest issue I have is that there's only one 'lane' from one side of the map to the other. What is a 'keep'? What is a 'height'? What is a 'prize'? ... I remember a python layout engine that produced lots of variety, months ago, and this seems like a regression. ... we want the 'defending' player to really be in the 'center' of a huge map ... These layouts have the defender in a corner, which is unrealistic."

Fate: denied. `docs/reports/2026-11-08-layout-variance-diagnosis.md` finds the cause: the Assault budget was cut to one of each, the R6 source was never given to the builder, mirror and rotate only transform the ground (so the choke sits nearer one side), the choke walls are drawn across the passage, "keep", "height" and "prize" are R6 prototype labels rather than bible terms, and both bases sit 63 percent of the way to the edge. The branch stays unlanded until he rules on it (DEC-layout-r5-start-point-2026-11-08).

## Found but not counted

- Lab catalogue layouts (H-025, 2026-10-30 to 2026-11-01, `scripts/skilllab/`; `push/labrev2-layoutfit`, 2026-10-19). These are hand-authored fight situations for the simulation lab, not a map generator. Batch one was denied 2026-10-31 for carrying no landscape geometry.
- `mac-protos-rebuild` and `mac/prototypes`: a Mac rebuild of prototypes (walkers, mockup guards); I saw no layout-engine work on them.
- `push/proto-land-p4` and `proto-land-p4-sweep`: walkable-ground work, no layout. `push/proto-land-p5` is already in main (it is pass 5).
- `push/proto-highground`, `proto-lakefill`, `proto-settlement-p1`, `push/terrain-*`: terrain, not layout.
- The space field generator (S-246) takes no layout request yet.

## Caveats

- My R1 to R8 are a reconstruction. If the lost list split or joined differently (for example folding R3 into R4, or counting the lab catalogue), the numbers after the change would shift; R5 is the anchor and its contents match the description given.
- I did not re-run any test or re-count any stub; those figures come from `docs/reports/2026-11-05-layout-engine-triage.md`.

# Layout engine triage, 2026-11-05

Asked by Westley: an assessment of the layout engine's current state, what it can produce today, against what the game requires. Written by the Architect from two read-only investigations of main at `9ef11b1e`. Plain language; repo references are kept to the "Where the pieces are" table at the end.

## The short version

The layout engine was never one thing. Three designs were written in six weeks and each was partly built, then the work moved on. Nothing from any of them reaches a mission the player plays today: a played mission puts both sides on a centre line, the objective halfway between, and rolls random hills under them. The approved piece (terrain that bends to a layout, October 21) sits on a branch that was never merged. The newest piece (a C engine that places bases, towns and resource sites on given terrain) passes its tests and nothing calls it. The oldest piece (eight hand-drawn layouts and a Python instantiator from May) still runs but failed its own audit and never had the game's new rules.

So: not regressed, never assembled. The parts do not share a definition of what a layout is, and no part produces the thing the beta's B2 stage must draw.

## What the game requires of a layout

Collected from the bible and Westley's rulings (September 12 to October 21). In order of how firmly they are ruled.

1. **A layout is a list of places and strategic shapes with numbers, and the landscape must produce them.** Given a mission kind and a seed, the layout says where the objective, each side's base, the neutral towns, the resource sites and the expansion sites are, and where the chokes (with a width), the high ground, the slope tops and the tall cover are. The landscape engine is required to make each one real: a choke is a real gap of that width, a vantage a real peak (ruled 2026-10-03, restated 2026-10-19 and 2026-10-21: "layout engine, landscape engine conforms").
2. **Fairness is two distances.** Each side is the same walking distance from the objective and from each significant resource, whatever the map's shape; a mission kind may deliberately slant it (ruled 2026-10-03).
3. **Every map plays differently.** A kit of situation pieces (choke, vantage, flank, city, base, resources), arranged differently each time, not one template per map (ruled 2026-10-04). Every layout must offer at least one play each for landscape, layers and enemy position.
4. **The numbers come from the simulation lab.** Choke width, place counts and spacing, the slant per mission kind, the fairness tolerance: all "something the simulation engine will find" (ruled 2026-10-15). None is set today.
5. **Reachability.** Every strategic place has at least two walking routes, one for a small army and one for a big one; ground over 35 degrees is impassable; about 30 percent of non-vantage peaks may be unreachable.
6. **Moving objectives** on three mission kinds (interception, rear guard, containment), following walking routes.
7. **Ten mission kinds** must each have fitting layouts; canvases from 8,000 to 32,000 world units for two sides, 64,000 for four to six players.
8. **A space version** with the same engine and a different vocabulary: open or blocked sheets instead of height, asteroid density set by the layout's request (ruled 2026-10-15 and 2026-10-21).
9. **The player should not see the map edge** (W1, logged before 2026-10-22, never answered).

The bible carries these across stories S-112 to S-119 (the May design, marked "rewrite pending" since 2026-10-02), S-186 to S-197 (the October design, "decided, not scheduled") and S-246 (space). The epic's gate is not passed.

## What exists, piece by piece

| Piece | What it does today | Reaches a played mission? | State |
|---|---|---|---|
| Eight hand-drawn layouts plus the Python instantiator (May) | Scales a dozen typed dots and lines to the canvas with jitter; a fairness score of four ratios | No. Only the retired Python pipe read it | Runs. Fairness fails on every layout at the test seed. The October 18 audit found none usable as drawn: objective beside one side in all eight, chokes with no width numbers, no base or resource places, four mission kinds with no layout. Audit never ruled on |
| C map generator from the May design | Meant to pick a layout, scale it, lay gradients | No | 44 empty stubs; 23 of its 24 tests red since October 7 |
| C places engine (October 13, "lane P" step 1) | Given terrain, objective and base positions: places towns, resource sites, expansion sites by rule, with about 30 draft numbers | No. Nothing calls it; its wiring step was never built | 71 tests green. Places points only: no chokes, no widths, no vantages, no lanes |
| C terrain (October) | Seeded hills, mesa or canyon; five height bands; slopes and walkability | Yes, ground era | Works. Takes no layout input at all |
| Landscape mockup pass 5 (October 3) | Reads one of the eight old layouts and bends noise terrain to it: levelled pads at each place, a corridor of the right width with walls at each choke, graded routes and bridges along each edge, vantages moved to high ground; then scores candidate places by walking distance | No, mockup only | Loads clean today. The closest thing to requirement 1 that exists. Westley: "close to what I want, not quite there on scale" (2026-10-05) |
| Terrain-obeys pass 2 (October 18) | The mockup's reaction done properly: carved routes, cliffs | No | Approved by Westley 2026-10-21 as a prototype. Branch never merged; 316 tests green there |
| Layout prototype pass 1 (October 4) | A flat diagram of kit pieces arranged by seed, with checks | No | Never shown to Westley; ROADMAP calls it reference only |

Three unmerged branches hold the two best artifacts (terrain-obeys pass 2, layout prototype pass 1). They are a month old and were built against an October main.

## Requirements against reality

| Requirement | Closest existing piece | Gap |
|---|---|---|
| Places and shapes with numbers, landscape produces them | Mockup pass 5 and terrain-obeys pass 2 (prototype), C places engine (points) | No engine outputs chokes with widths, vantages, slope tops or lanes. The mockup does it from the old layouts' hints ("narrow", "moderate"), not numbers |
| Fairness as two walking distances | Mockup pass 5's place scorer; C places engine's equal-distance check (straight line, flagged Q-191-15) | Not in the game; tolerance unset |
| Kit of pieces, different every map | Layout prototype pass 1 (flat diagram) | Unseen, unmerged, not connected to terrain or the C side |
| Numbers from the lab | Lab stages 1 to 4 (ongoing) | The lab has not yet produced any layout-engine number; every width, count and slant is a draft |
| Two routes to every strategic place, 35 degrees, 30 percent | Terrain-obeys pass 2 carved routes; terrain's walkability | Route-count check exists only as a mockup verify step; no positive control in the game |
| Moving objectives on routes | Python spine drift (May) | Not in C; nothing moves in a played mission |
| Ten mission kinds served | Eight layouts tagged to six kinds | Four kinds have none; pairing never decided |
| Space version | Space field generator (plates and pockets) in C, approved | Takes no layout request; asteroid density is a default |
| Map edge not visible | nothing | W1 unanswered |

## What is still Westley's to decide

- The library audit's three questions (2026-10-18): may a layout demand a landform; what to do for the four mission kinds with no layout; the kit's piece list.
- Whether the flat layout diagram is the first thing he sees, before terrain (he agreed 2026-10-04, then ruled no separate prototype 2026-10-06; the bible carries both lines).
- The straight-line versus walking-distance question for the places engine (Q-191-15).
- The map edge (W1).

## Reading, and what it means for the beta

B2 needs one layout, drawn flat, that the engine produced. Today no engine produces one. The fastest honest path is to pick one definition of a layout (the kit of pieces with numbers, as ruled), make one C function produce it from a seed and a mission kind (places plus chokes with widths plus vantages, nothing else), draw that flat in the beta, and only then bring terrain-obeys over from its branch for B3. The eight old layouts are reference, not input. The lab's numbers arrive as they arrive; until then every number is a named draft he can veto in the scene.

## Where the pieces are

Python: `simulation/layout_library/`, `simulation/layout_instantiator.py`, `simulation/fairness_evaluator.py`. C: `csrc/layout_engine.c` (places), `csrc/tactical_mapgen.c` (stubs), `csrc/terrain.c`, `csrc/mission.c` (the centre-line placement). Mockup: `scenes/mockups/landscape/` (pass 5). Branches: `push/proto-terrain-obeys-2`, `push/proto-layout`, `push/proto-land-iter`. Research: `docs/northstar/research/layout_engine/` (options, audit, pass 1), `docs/northstar/research/landscape_design/`. Rules: `docs/bible/epics/E-17-map-generation.md`. Rulings: `docs/northstar/ambiguity_register.md` Q-191, `docs/northstar/plans/decision_pack_2026-10-18/answers.md`, `docs/northstar/story_reviews/westley/verdicts_2026-10.md`.

# Prototype spec: walking and flying units on generated land (mockup, pass 1)

Under the Prototype gate (`docs/northstar/agile.md`). A mockup: a Godot scene with placeholder shapes, for what Westley must see. Disposable. What it produces is his decisions. Nothing here goes into the C sim or the bible until he approves.

## Why

The land mockup shows ground. Nothing yet shows a unit using it. The rules for walking units, slopes and steep ground are written (E-01 R-001-05 to R-001-07, R-004-06, R-004-07, S-200; E-13 R-207-05) and no one has seen them move. The skill lab cannot be trusted for range, speed and layer-change time until these exist in the sim, and the sim piece cannot be planned until he has seen this.

## What Westley sees

On one generated land map (the pass 6 generator, canvas 16,000, three seeds on keys):

1. **Walkers and flyers side by side.** Two placeholder groups he can select: six walkers (squares) and six flyers (triangles). Right-click orders the selected group to a place.
2. **Walkers route over ground.** A walker goes only where the ground can be walked (slope at or below 35 degrees), takes the route of least time, and never crosses ground too steep to cross. If no way exists it goes as close as it can and stops. The planned route is drawn as a line.
3. **Layers come from the ground.** Each unit shows its layer number, which for a walker is the height band of the ground under it. Where a route crosses from one band to the next, the crossing is marked, with a tick at the midline (the point where the unit changes layer, R-004-06).
4. **Flyers.** A flyer flies on its chosen layer (keys 1 to 5 set it for the selection), in a straight line where it can. It cannot be below the ground: where the ground's band is higher than its layer it goes around, or climbs if "climb when blocked" is on (a timed transfer, 2.5 s).
5. **A group moves at its slowest member's pace** when walkers and flyers are ordered together.
6. **A read-out for the last order:** route length, time to arrive, bands crossed, and the same order's time for the other kind of unit, so the difference a mountain makes is a number.
7. **A view toggle:** too-steep ground shaded, band colours, both, or neither.

## Choices on screen (each is a question for him)

| Key | Choice | Options shown |
|---|---|---|
| G | Does a slope slow a walker? | (a) no: time is distance along the ground over speed (R-004-07 as written); (b) uphill slows in proportion to the grade, half speed at the 35 degree limit, downhill unchanged; (c) as (b), and downhill is faster by half as much |
| C | A flyer blocked by ground | (a) goes around on its layer; (b) climbs over by a timed transfer |
| B | Walker speed | 40 (slowest type), 80, 150 (fastest type), so the map's size can be felt |

## Questions for Westley after looking

1. Do walkers take routes you would expect a real army to take?
2. Slope and speed: (a), (b) or (c)?
3. Is 16,000 wu the right size for how long a walk takes (the read-out gives seconds)? Try 40 and 150.
4. Should a flyer blocked by a mountain go around or climb?
5. Is the layer a walker is on clear enough from the band it stands in, or does it need more than a number?
6. What is missing that you expected to see?

## Build notes

- New files only, under `scenes/mockups/walkers/`. Branch `push/proto-walkers`, from `push/proto-land-iter`. The land mockup's scripts are read and called, never edited. If something needed from them is private to a scene script, copy the smallest piece into the new directory and say so.
- Three parts, each small: `walker_grid.gd` (walkability and band grids sampled from the land generator's height field; least-time routes for walkers and for a flyer on a layer; the three slope-speed options; no drawing, testable headless), `walker_units.gd` (the two groups, movement along a route, the slowest-member rule, the read-out numbers), `walkers_mockup.gd` and `.tscn` (scene, input, drawing, the keys, the on-screen help).
- `walkers_selftest.gd` in the form the test runner expects (`scripts/run_godot_tests.sh`): a route never enters a too-steep cell; an unreachable target ends at the nearest reachable cell; option (b) gives a longer time than (a) on an uphill route and the same on flat ground; a flyer on a layer below the ground's band at the target does not arrive there; mixed groups arrive together.
- `verify.gd` in the form the other mockups use (`scripts/mockup_verify.sh walkers`).
- Deterministic for a seed. No game code, no autoloads, no `class_name`.
- Numbers not given by a rule (grid cell size, climb time, the grade formula) are mockup drafts, named constants marked provisional.

## Run

`cd ~/Projects/om-push/wt/proto-walkers && ~/.local/bin/godot.real --path . --display-driver x11 --rendering-driver opengl3 res://scenes/mockups/walkers/walkers_mockup.tscn`

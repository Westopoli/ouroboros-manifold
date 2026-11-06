# Layout engine prototype, pass 1: flat diagram (spec)

Westley, 2026-10-04: layout is a list of forced choices with numbers; puzzle pieces with a kit per kind; method M4 (`research/layout_engine/composition_methods.md`); the objective moves only on Interception, Rear Guard and Containment; the first pass is the flat diagram alone, terrain second. Closes Q-191-11 (a), Q-191-12 (d), Q-191-13 (d). All figures are drafts (Q-191-05).

Constraint, verbatim: "make sure it doesn't fill the UI with text (some other prototypes do that and it blocks the view)."

Outcome: Westley runs one Godot scene and judges (1) whether each map's choices read, (2) whether twelve seeds of one archetype feel different.

Code lives in `scenes/mockups/layout/`, branch `push/proto-layout`. Nothing in `scenes/mockups/landscape/` is touched.

## Generator

Pure data out, no nodes.

- `layout_kits.json`: seven piece kinds (home ground, gate, crossing, heights, prize, commons, objective ground), two to three variants each, with number ranges (width in wu, bypass ratio, height in bands), the choice sentence and skins. Three archetype recipes: Defensive Stand (objective beside the defender), Assault (large canvas, objective beside the defender), Interception (objective travels a walking route).
- `layout_gen.gd`, per map:
  1. Districts on a coarse 8x8 grid: home, near ground, contested, objective. The division pattern (axis angle; middle as band, ring or two patches) is drawn per seed.
  2. Home districts by slots: home ground plus gate variant, numbers matched for both sides.
  3. Spine: route home A, objective, home B.
  4. Growth rules in the contested and objective districts, budget from the recipe, each recorded as a step: crossing (choke plus a longer way round = loop), heights (overlooks a route, two ways up), prize spur (dead end, or with a back door), commons, hidden second approach.
  5. Sides related by a switch: mirror, rotate, or grown separately with equal numbers (route meander 1.0 to 1.6 tuned until walking distances match).
  6. Node positions jittered inside cells so the grid does not show.
  7. Five candidates made; the best by checks kept.
- `layout_checks.gd`: connected; equal walking distance to each significant resource (10 percent draft tolerance) and to the objective where nobody holds it; every crossing's way round at least 1.5x (draft); two or more approaches to the objective; the recipe's choices all present; signature (division pattern, loop count, order of piece kinds along each side's route) and its distance to other maps.
- `layout_selftest.gd`: `godot --headless -s scenes/mockups/layout/layout_selftest.gd` prints one line per map for 3 archetypes x 12 seeds x 3 symmetry modes (108 maps), then check failures and mean signature distance. All maps must be connected.

## View

`layout_mockup.tscn`, `layout_mockup.gd`, `layout_view.gd`; reads generator data only.

- The diagram fills the window. Districts are faint tints; pieces are outlined shapes with an icon and a name of at most two words; routes are drawn with thickness = width, loops and spurs visibly distinct, chokes pinched, closed sides hatched.
- **Text budget (hard rule).** One top bar of one line (archetype, seed, sides switch, growth on/off, view). One row of check dots at the bottom (green or red, no words). Nothing else is visible by default and no panel covers the map. Everything else is on demand: hover a piece for its choice sentence and numbers in a small tooltip at the cursor; hover a route for width and walking time; hover a check dot for its line; `L` toggles route labels; `H` toggles a help card. Default-visible text stays under about 5 percent of the window area.
- Views: Map; Sheet (twelve seeds as thumbnails, signature difference as a small number under each, click to open); Replay (`[` and `]` step the growth rules one at a time).
- Screenshot mode: `-- --shot <png> --archetype <a> --seed <n> --view map|sheet` saves and quits.

## Not in this pass

Terrain (pass 2), 4 to 6 sides, 64,000 wu, space maps, the other seven archetype recipes, lab measurement of piece worth.

## Run line

`cd ~/Projects/om-push/wt/proto-layout && ~/.local/bin/godot.real --path . --display-driver x11 --rendering-driver opengl3 res://scenes/mockups/layout/layout_mockup.tscn`

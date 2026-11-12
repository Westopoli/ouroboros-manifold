# R5 recovery: pictures of the "layout first, landscape obeys" prototypes (2026-11-08)

You chose R5 as the start point on 2026-11-08 (DEC-layout-r5-start-point-2026-11-08) and asked to see both of its prototypes, five variations each, before you give direction for a new method. Three sets are here; nothing in them is game code. All pictures were made after the water fix of the same day (DEC-lake-waterline-2026-11-08): water now follows height, so the parallel water lines are gone. Pictures are 1920x1080.

| Set | Folder | What it is | Pictures |
|---|---|---|---|
| A | `obey/` | Terrain-obeys pass 2 as it is (recovered unchanged, apart from the water fix and five seeds) | 5 |
| B | `pass5/` | Pass 5, the library drawing bent to terrain (October 3), five layouts, three views each | 15 |
| C | `obey-assault/` | Set A modified for the three asks of 2026-11-08: defender in the centre, roads that bend to the landscape, a vantage sometimes beside a base | 5 |

## Set A: terrain-obeys pass 2, as it is

Recovered from branch `push/proto-terrain-obeys-2` (head `f57af240`). A seed picks the axis angle. The two bases sit at the two ends of the line, 2,400 wu in from the edge. A choke sits 35 to 65 percent along the line, 180 to 600 wu wide. The objective sits 1,500 wu off the line, the two resource sites 2,400 wu either side of it, the vantage 1,500 wu beside the choke. Two to four routes run from the attacking base to each place. The terrain is then shaped to fit: flat pads, walls at the choke, carved roads; the checks run on the finished ground (35-degree walk limit). Canvas 16,000 wu; the 8,000 wu canvas is dropped (your 2026-10-21 word: "We won't have a map this small in reality").

Colours (walk view): dark blue water; green reachable ground; purple unreachable ground; orange thin route (180 wu); light blue wide route (600 wu); red circle a place whose check failed; pink ring the vantage; black squares unreachable peaks; teal squares reachable peaks. Blue, yellow and teal circles are the bases, objective and resource sites.

Note: seeds 4 and 5 fail the pass-2 pad check (a pad ring over 35 degrees: seed 4 site_1 35.2, seed 5 base_b 41.2) in this prototype as recovered, before and after the water fix. They are shown as they are.

| Picture | What to expect | Approve means | Deny means |
|---|---|---|---|
| `obey/obey_16000_1.png` | Seed 1, check PASS: 4 routes per place, choke at 0.60 of the line | This is the start point, keep it | Not this one; say what is missing |
| `obey/obey_16000_2.png` | Seed 2, check PASS: 2 routes per place, choke at 0.58 of the line | This is the start point, keep it | Not this one; say what is missing |
| `obey/obey_16000_3.png` | Seed 3, check PASS: 2 routes per place, choke at 0.39 of the line | This is the start point, keep it | Not this one; say what is missing |
| `obey/obey_16000_4.png` | Seed 4, check FAIL (ring): 3 routes per place, choke at 0.59 of the line | This is the start point, keep it | Not this one; say what is missing |
| `obey/obey_16000_5.png` | Seed 5, check FAIL (ring): 2 routes per place, choke at 0.60 of the line | This is the start point, keep it | Not this one; say what is missing |

## Set B: pass 5, the library drawing bent to terrain

Recovered from branch `push/proto-land-iter` (head `84e1db89`, pass 5 commit `44e96b4f`). Not the same as set A: here the layout is one of eight hand-drawn node graphs from April (`simulation/layout_library/`), scaled to the canvas, and the terrain is bent to it. Each node kind gets a flat pad (staging 500 wu, objective 600, vantage 350, spawn point 450, extraction 350, transit 200, flank route 200, hazard anchor 150, reinforcement 250); chokepoints get a 1,600 wu corridor with 900 wu walls; routes are graded; vantages are moved to high ground; up to three attempts; an equal-distance check at the end. A seed only jitters the drawing by 3 percent, so the five variations are five layouts at seed 11, the five the 2026-10-18 audit kept as recipes: 01 Fortress Ridge, 03 Three-Front Valley, 05 Coastal Wedge, 06 Flanking Pass, 08 Elevated Strongpoint. It is shown for the carving idea (pads, corridors, graded roads), not for its two-ends shape. Three views per layout: `raw_layout` (the node graph on the canvas), `react` (terrain bent to it: yellow pad, orange graded route, cyan bridge, green corridor, dark red wall, pink vantage), `walk` (walkable ground: green reachable from the base, orange cut off, purple steep, cyan bridge).

Node colours in `raw_layout`: staging blue, spawn point red, objective yellow, chokepoint orange, vantage white, flank route pink, transit grey, hazard anchor purple, reinforcement green, extraction cyan; edges: path white, flank orange, restricted magenta.

| Picture | What to expect | Approve means | Deny means |
|---|---|---|---|
| `pass5/L01_s11_raw_layout.png` | Layout 1 Fortress Ridge: the drawn node graph on the canvas, before any terrain | This is the start point, keep it | Not this one; say what is missing |
| `pass5/L01_s11_react.png` | Layout 1 Fortress Ridge: the terrain bent to the graph | This is the start point, keep it | Not this one; say what is missing |
| `pass5/L01_s11_walk.png` | Layout 1 Fortress Ridge: which ground a walker can reach | This is the start point, keep it | Not this one; say what is missing |
| `pass5/L03_s11_raw_layout.png` | Layout 3 Three-Front Valley: the drawn node graph on the canvas, before any terrain | This is the start point, keep it | Not this one; say what is missing |
| `pass5/L03_s11_react.png` | Layout 3 Three-Front Valley: the terrain bent to the graph | This is the start point, keep it | Not this one; say what is missing |
| `pass5/L03_s11_walk.png` | Layout 3 Three-Front Valley: which ground a walker can reach | This is the start point, keep it | Not this one; say what is missing |
| `pass5/L05_s11_raw_layout.png` | Layout 5 Coastal Wedge: the drawn node graph on the canvas, before any terrain | This is the start point, keep it | Not this one; say what is missing |
| `pass5/L05_s11_react.png` | Layout 5 Coastal Wedge: the terrain bent to the graph | This is the start point, keep it | Not this one; say what is missing |
| `pass5/L05_s11_walk.png` | Layout 5 Coastal Wedge: which ground a walker can reach | This is the start point, keep it | Not this one; say what is missing |
| `pass5/L06_s11_raw_layout.png` | Layout 6 Flanking Pass: the drawn node graph on the canvas, before any terrain | This is the start point, keep it | Not this one; say what is missing |
| `pass5/L06_s11_react.png` | Layout 6 Flanking Pass: the terrain bent to the graph | This is the start point, keep it | Not this one; say what is missing |
| `pass5/L06_s11_walk.png` | Layout 6 Flanking Pass: which ground a walker can reach | This is the start point, keep it | Not this one; say what is missing |
| `pass5/L08_s11_raw_layout.png` | Layout 8 Elevated Strongpoint: the drawn node graph on the canvas, before any terrain | This is the start point, keep it | Not this one; say what is missing |
| `pass5/L08_s11_react.png` | Layout 8 Elevated Strongpoint: the terrain bent to the graph | This is the start point, keep it | Not this one; say what is missing |
| `pass5/L08_s11_walk.png` | Layout 8 Elevated Strongpoint: which ground a walker can reach | This is the start point, keep it | Not this one; say what is missing |

## Set C: the modified R5 (your three asks of 2026-11-08)

Built in GDScript on set A's code behind `--mode assault` (the as-is mode is untouched); a study aid, not game code (DEC-layout-r5-prototype-2026-11-08). Same canvas, seeds 1 to 5.
1. The defender (`base_b`) sits at the canvas centre plus a seeded wander of 1,200 wu; the objective sits 1,500 wu from it on a seeded bearing; the attacker (`base_a`) sits on the edge ring at a seeded bearing, any angle. The choke sits on the attacker's main road.
2. Roads bend to the landscape. Each road has a style, and a cost field from the finished ground: lowland (cost rises with height and slope, follows valleys), pass (cheap on the highest dry ground and saddles), riverside (cheap within 2 cells of water). The choke road is always lowland; the others roll one of the three. A road that rolled riverside but cannot keep 70 percent of its cells near water is redone as lowland and labelled so. The main road arrives at the objective from a seeded entry side (a small arrow marks the entry point). The panel line `styles` prints one letter per road (l lowland, p pass, r riverside; a capital is the main road).
3. With chance 0.35 the vantage sits beside a base instead of beside the choke; the panel prints `vantage_at`.
New checks in the panel: `defender_centre`, `entry_side`, `bend` (main road at least 1.15 times its straight length), `vantage_placed`.

| Picture | What to expect | Approve means | Deny means |
|---|---|---|---|
| `obey-assault/obey_assault_16000_1.png` | Seed 1: defender near the centre, vantage beside the choke; bend ok 1.66 | The three changes read right; build on them | Not this; say which ask is wrong or missing |
| `obey-assault/obey_assault_16000_2.png` | Seed 2: defender near the centre, vantage beside base b; bend ok 1.29 | The three changes read right; build on them | Not this; say which ask is wrong or missing |
| `obey-assault/obey_assault_16000_3.png` | Seed 3: defender near the centre, vantage beside the choke; bend ok 1.58 | The three changes read right; build on them | Not this; say which ask is wrong or missing |
| `obey-assault/obey_assault_16000_4.png` | Seed 4: defender near the centre, vantage beside base b; bend ok 1.33 | The three changes read right; build on them | Not this; say which ask is wrong or missing |
| `obey-assault/obey_assault_16000_5.png` | Seed 5: defender near the centre, vantage beside the choke; bend ok 1.34 | The three changes read right; build on them | Not this; say which ask is wrong or missing |

## The numbers behind them

Set A and C drafts (named, in the panel, moved with `[` `]` after `,` `.` selects one). Every number is a candidate, not a rule.

| Draft | Default |
|---|---|
| `base-inset` | 2400.0 |
| `resource-clearance` | 2400.0 |
| `route-small-width` | 180.0 |
| `route-big-width` | 600.0 |
| `vantage-offset` | 1500.0 |
| `base-pad` | 1200.0 |
| `objective-pad` | 600.0 |
| `site-pad` | 400.0 |
| `choke-wall` | 900.0 |
| `wall-rise` | 400.0 |
| `vantage-rise` | 300.0 |
| `route-max-count` | 4.0 |
| `obey-budget` | 250.0 |
| `choke-length` | 600.0 |
| `wall-gap` | 125.0 |
| `wall-face` | 100.0 |
| `ramp-grade` | 28.0 |
| `ramp-reach` | 2400.0 |
| `vantage-radius` | 250.0 |
| `objective-offset` | 1500.0 |
| `pad-scale-floor` | 0.6 |
| `carve-cost` | 6.0 |
| `carve-shoulder` | 150.0 |
| `obey-budget-2` | 500.0 |
| `site-line-clearance` | 900.0 |

Pass 5 constants (`pass5_layout.gd`):

```
const PAD_WU := {"staging": 500.0, "objective": 600.0, "vantage": 350.0, "spawn_point": 450.0, "extraction": 350.0, "transit": 200.0, "flank_route": 200.0, "hazard_zone_anchor": 150.0, "reinforcement_structure": 250.0}
const PAD_SHOULDER_WU := 250.0
const CHOKE_LEN_WU := 1600.0
const WALL_H_WU := 900.0
const WALL_BAND_WU := 500.0
const WALL_SLOPE := 1.2
const VANTAGE_SEARCH_WU := 1500.0
const VANTAGE_GRADE_DEG := 14.0
const NODE_GRADE_DEG := 15.0
const NODE_RELAX_ITERATIONS := 0
const ROUTE_HALF_WU := 250.0
const ROUTE_SHOULDER_WU := 150.0
const ROUTE_GRADE_DEG := 18.0
const BLOCKED_COST := 5.0
const WATER_COST := 9.0
const CHOKE_FLANK_COST := 15.0
const ROUTE_ITERATIONS := 6
const MAX_ATTEMPTS := 3
const LIMIT_DEG := 30.0
```

The first lines of every panel file are the numbers for that picture, copied verbatim into the `.txt` files beside the pictures. Set A, seed 1:

```
OBEY pass 2   seed 1   canvas 16000   PASS
check 951 ms incl. carving 772 (draft 500)   route_count 4 (2 + floor(u*3))
carved 3512 cells in 20 routes   choke on a route: true   pad scale 1.00   span 900 wu
choke asked 466 wu, measured 410 wu   at 0.60 of the base line (rolled 0.60)
per point: routes small / big (need 4 / 1), pad ring max slope (limit 35 deg)
  base_b    small 4  big 1  ring 31.2 deg  ok
  objective small 4  big 2  ring 28.0 deg  ok
  site_0    small 4  big 1  ring 28.0 deg  ok
  site_1    small 4  big 2  ring 28.0 deg  ok
  base_a                         ring 33.1 deg  ok
```

Set C, seed 1:

```
OBEY pass 2 assault   seed 1   canvas 16000   PASS
check 2366 ms incl. carving 2209 (draft 500)   route_count 4 (2 + floor(u*3))
carved 2935 cells in 20 routes   choke on a route: true   pad scale 1.00   span 900 wu
choke asked 466 wu, measured 430 wu   at 0.60 of the base line (rolled 0.60)
per point: routes small / big (need 4 / 1), pad ring max slope (limit 35 deg)
  base_b    small 4  big 2  ring 33.3 deg  ok
  objective small 4  big 2  ring 27.1 deg  ok
  site_0    small 4  big 2  ring 28.0 deg  ok
  site_1    small 4  big 2  ring 28.0 deg  ok
  base_a                         ring 33.1 deg  ok
vantage_at: choke
defender_centre ok
entry_side ok
bend ok 1.66
vantage_placed ok
  styles base_b    small lprr  big p
  styles objective small Plpp  big p
  styles site_0    small lllp  big l
```

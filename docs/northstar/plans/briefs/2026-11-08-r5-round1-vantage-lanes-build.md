# R5 round 1, fix 3: vantages over traffic, lanes by width, loud failures. Build to green.

Role: Engineer (Sonnet 5.5), builder. Never edit a test; report a test you believe wrong. Spawn nothing. Think tersely. Report once, under 25 lines: commits, files, green summary, before/after counts of the other test files, anything you believe wrong.

## Tests

`~/Projects/om-wt/r5-obey` (branch `wip/r5-obey-shots`, head after `8f1e21b5`): `tests/test_mockup_obey_vantage_lanes.gd`, red 99 fail / 85 pass. Run `scripts/run_godot_tests.sh tests/test_mockup_obey_vantage_lanes.gd` (about 40 s). Read the test and the brief `2026-11-08-r5-round1-vantage-lanes-tests.md` first. Other files keep their counts: `test_mockup_obey.gd` 304/6, `test_mockup_obey_assault.gd` 449/5, `test_mockup_shot_quiet.gd` 31/0, `test_mockup_landscape_water_views.gd` 77/0; run them before and after.

## Build (`scenes/mockups/landscape/obey_layer.gd`, `obey_overlay.gd`; rulings by the Architect, 2026-11-08)

1. Drafts added to `DRAFTS`: `vantage-overlook` 600, `lane-budget` 720, `options-min` 3, `deadend-area` 400 (steps 50, 20, 1, 50).
2. Vantage over traffic: after carving, if the vantage is farther than `vantage-overlook` from every carved road centreline cell and from both resource pads' edges, move it along its side's perpendicular toward the nearest carved road until within range (keep the pad clearance of `_vantage_side`); report key `vantage_over` as the string `road | site_0 | site_1 | none`; panel line `vantage_over: <s>`; `none` fails the check.
3. Vantage reachable: walk flood from `base_a` at 35 degrees must reach the vantage pad; if not, cut a second climb lane at `ramp-grade` from the nearest reached cell (R-189-07 wants two ways up: the first is the existing one); if still unreached, report key `vantage_reach` false, panel line `vantage_reach FAIL`, first panel line carries `FAIL`, overlay ring in `FAIL_COLOR` (`vantage_ring_color()` returns the colour in use), and `shot_file_name(canvas, seed)` returns `obey_assault_16000_<seed>_FAIL.png`; `_run_shots` uses `shot_file_name`.
4. Lanes by width: `route_count` is derived, `clamp(round(lane-budget / width), 1, route-max-count)` per width (small and big separately); the roll that set `route_count` is removed (keep the stream draw so later rolls do not shift: draw and discard, with a comment); panel lines `lanes <width> -> <count>` for each width used; total roads reaching the objective at least `options-min` at default widths, else the big-road count is raised until met.
5. Restriction named: measure, for each place, the erosion radius at which it stops being reachable; a narrowing is a cell on the corridor where the width falls under `route-small-width` 180 wu; count those outside every choke's wall span; panel `narrowings <n> (<m> outside chokes)`; report key `accidental_narrowing` true when `m == 0`; FAIL otherwise. The test writer notes the 100 wu grid gives this teeth only on big roads; accept that, say so in a comment.
6. Dead ends: walkable connected regions of at least `deadend-area` cells touching a carved road by exactly one corridor (one connected boundary run of walkable cells) and holding no pad; panel `dead_ends <n>`; not a FAIL.
7. Deterministic; panel identical across two runs except timing lines.

Constraints: minimal diff; every new number a draft; add only changed paths, never `-a`/`-A`. Commit subject `R5 round 1: vantages over traffic, lanes by width, loud failures, dead ends counted`, trailer `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. No pictures.

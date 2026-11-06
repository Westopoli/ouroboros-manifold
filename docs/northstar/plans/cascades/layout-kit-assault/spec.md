# layout-kit-assault

Cascade spec for S-247, the first story of the layout engine: a layout made from the kit of pieces, Assault only, drawn flat for Westley's rounds. Written 2026-11-05 on branch `s/S-247-layout-kit-assault` (worktree `~/Projects/om-wt/layout-kit`) from main `dd2ecb7f`. Story page: `docs/stories/S-247.md`. Rules: `docs/bible/epics/E-17-map-generation.md` S-112 (R-112-01 to R-112-08) and S-113 (R-113-01 to R-113-05). Decisions: rows `DEC-layout-*-2026-11-05` in `docs/northstar/story_reviews/westley/decisions.md`. Triage: `docs/reports/2026-11-05-layout-engine-triage.md`. Steps file: `docs/method/story_loop.md`.

## Summary

No engine produces the game's layout (triage). This cascade builds the one definition: a C function `om_lk_generate(seed, archetype, canvas, sides_mode, &layout)` that returns districts filled from kit pieces, each piece one choice with numbers, with places, lanes, chokes with widths, vantages and the request list the landscape engine will be asked to make real (B3). It is a CLI (`layout_dump`) that prints the layout as JSON and a Python renderer that draws the JSON as a PNG and as a 12-seed sheet. Westley judges by pictures, round after round, until he says approve; every figure is a `DRAFT_` macro he can veto. Three file-disjoint leaves; the overlord writes the parent-owned documents in the landing commit. Nothing in the game changes: no `csrc/ouroboros_sim.h`, no pipe frame, no scene (S-249 and H-061 come after story 2).

## Pre-flight (2026-11-05, main `dd2ecb7f`, read by `git show`, `grep` and running)

- Absent: `csrc/layout_kit*`, `csrc/layout_drafts.h`, `csrc/tools/`, `scripts/layout/`, `tests/layout/` (`ls`). `.venv/bin/python` has Pillow 12.3.0 (`import PIL`), pytest; the worktree has no `.venv`, so every command below uses `/home/westopoli/Projects/ouroboros-manifold/.venv/bin/python` (written `$PY`).
- `Makefile:24` `SRC := $(wildcard csrc/*.c)` builds every `csrc/layout_kit*.c` into `libouroboros.so`; `csrc/tools/` is outside the wildcard. Flags: `Makefile:27-43` (`-std=c11 -Wall -Wextra -Icsrc -fPIC`, `-fno-fast-math -ffp-contract=off -fno-math-errno`, `-msse2 -mfpmath=sse` on x86, `-fexcess-precision=standard` where accepted, `-Werror` when `WERROR=1`). The Makefile is parent-owned; the overlord adds the `layout_dump`, `build/O0/layout_dump` and `build/O2/layout_dump` targets.
- `csrc/layout_engine.c` and `csrc/layout_internal.h` are the sibling places engine (71 tests green, `om_place_kind`, straight-line detector VG-P1); untouched. The kit's header is self-contained and uses the `om_lk_` prefix so no name collides. `csrc/tactical_mapgen.c` (44 stubs) and `simulation/layout_library/` are reference only (R-112-06).
- `csrc/chronicle.c:702-712` is the splitmix64 pattern (`chron_splitmix_next`, `CHRON_RNG_*` constants); `om_rng_draw` needs a world, so the kit has its own `lk_rng`. `csrc/om_internal.h:486-487` declares `om_tn_sin_q16(uint32_t turn_q16)` and `om_tn_cos_q16`, defined in `csrc/terrain_noise.c` (links into any build of the kit). `scripts/specfactory/libm_lint.py:34-39` bans `pow exp log sin cos tan ... rand time clock qsort bsearch`; allows `sqrt fabs floor ceil round trunc fmin fmax fmod`.
- `tests/csim/test_VG_P_p1_layout.py:118-121` is the determinism flag list the new tests copy. `csrc/mission.c:161-170` are the ten archetype ids (`OM_MISSION_ARCH_ASSAULT` 3); `om_mission_instantiate_map` (`csrc/mission.c:2736`) places spawns and the objective on the centre line and is NOT touched in this story.
- Reference algorithm: `git show push/proto-layout:scenes/mockups/layout/layout_gen.gd` (762 lines) and `layout_kits.json` (85 lines): districts on a grid, division pattern per seed, home grids matched between sides, spine, growth rules per district, route-graph distances, `sides` modes. Read, ported to C with the changes in "Design"; it never reached Westley (ROADMAP "reference only").
- Old tests `tests/csim/test_E17_S112_bones_from_the_library.py` and `test_E17_S113_nine_kinds_of_place.py` read the retired library rules (they call `om_map_get_compatible_layout_count`, stubs, 23 of 24 red since 2026-10-07). They are not edited in this cascade; the landing report lists them as stale against the rewritten rules (DEC-layout-no-prototype-2026-11-05).
- No open `Q-` row touches S-247 (Q-191-15 and Q-247-01 closed in this branch's records commit; Q-191-13 is closed at (d): the sides modes are shown and Westley rules on the sheet).

## Inputs / Outputs / Constraints / Out of scope

- Inputs: seed (uint64), archetype (round A: Assault 3), canvas (wu, double), sides mode (mirror 0, rotate 1, separate 2).
- Outputs: `om_lk_layout` (in memory); `layout_dump` JSON (below); PNGs `map_assault_s<seed>_<sides>.png` and `sheet_assault_<sides>.png`; the README of round A1 in his directory.
- Constraints: byte-identical output for identical inputs on every platform and at -O0 and -O2; no heap (fixed arrays in the struct); every number a `DRAFT_` macro; the kit never reads a world, a clock or the old library; no change to `csrc/ouroboros_sim.h`, `signatures.toml`, `csrc/pipe/`, `scenes/`, `autoload/`, `csrc/mission.c`.
- Out of scope: the other nine kinds, moving objectives, compact kinds, 4 to 6 sides (S-248); the pipe and the game (S-249); the Godot drawing (H-061); terrain-obeys (B3); commons and hidden approach pieces; a mockup scene; any Godot file; Q-191-13's ruling (his, on the sheet); the numbers' final values (the lab's).

## The contract (`csrc/layout_kit.h`, written by the Architect, frozen for the cascade)

Read it in full: structs `om_lk_place`, `om_lk_node`, `om_lk_lane`, `om_lk_choke`, `om_lk_vantage`, `om_lk_request`, `om_lk_fairness`, `om_lk_layout`; enums; caps `OM_LK_MAX_*`; entry points `om_lk_generate`, `om_lk_run_checks`, `om_lk_name`, `om_lk_draft_count`, `om_lk_draft_name`, `om_lk_draft_value`. Sentinel bodies in `csrc/layout_kit.c` return -1 / NULL / 0; leaf 1 replaces them. A change to the header is the Architect's, by amendment of this spec.

### JSON (`om-layout-1`, written by leaf 2, read by leaf 3 and the tests)

One object, keys in exactly this order, two-space indent, one array element per line for `places`, `nodes`, `lanes`, `chokes`, `vantages`, `requests`, `district` rows on one line each:

```
schema "om-layout-1"; seed (integer); archetype ("assault"); canvas (number); sides ("mirror"|"rotate"|"separate"); candidate (int);
drafts {NAME: number, ...} (om_lk_draft_name/value, table order);
district [[int x8] x8];
places [{kind, side ("A"|"B"|"none"), x, y, pad_r, piece, node}];
nodes [{x, y, place}];
lanes [{kind, a, b, width, pts [[x,y],...]}];
chokes [{x, y, width, length, axis_k, wall_span, frac, lane, landform, piece}];
vantages [{x, y, radius, height_bands, overlooks, climb [i,j], landform, piece}];
requests [{kind, mode, piece, name, x, y, r, w, len, span, frac, axis_k, height_bands, side, landform}];
fairness {dist_a_objective, dist_b_objective, dist_a_res [d0,d1], dist_b_res [d0,d1]};
checks {connected, fairness, bypass, approaches, chokes, bounds} (true/false);
route_count (int)
```

`kind`, `piece`, `landform`, `mode` print as the `om_lk_name` strings (domain 0 place kind: `objective base_home base_forward resource expansion`; 1 lane kind: `route way_round climb hidden objective_route`; 2 landform: `none coast canyon mesa ridge hill plateau basin bend ford pass gate`; 3 request kind: `pad choke vantage route landform`; 4 request mode: `keep_open keep_closed height room number`; 5 piece: `none home_ground gate crossing heights prize objective_ground`). Numbers: coordinates, widths, radii and distances are quantised to `DRAFT_JSON_QUANT` 0.01 wu and printed with integer arithmetic only: `v` as a signed integer count of hundredths, printed `[-]<int>.<two digits>` (no `%g`, no `%f`, no exponent). A distance of -1 (unreachable) prints `-1.00`. Newline at the end of the file.

## Design (every figure a `DRAFT_` macro in `csrc/layout_drafts.h`, in the X-macro table `LK_DRAFT_TABLE(X)`)

**Algorithm** (port of `layout_gen.gd`, round A): (1) validate (return codes in the header); (2) for each of `DRAFT_CANDIDATES` candidates, derive a stream seed, build a layout, run the checks, count passes; keep the candidate with the most passes (lowest index on a tie), `candidate` records it; (3) one candidate: pick a division pattern per seed (band, ring or two patches; axis in 15-degree steps) and fill the 8 by 8 `district` grid with the roles (home A, home B, near A, near B, contested, objective); place home A (a forward camp, `base_forward`, side A, the attacker) and home B (a grown town, `base_home`, side B, the defender) with matched gate pieces; place the objective beside home B in the objective district (Q-191-11); build the spine A to objective; grow the contested district to the Assault budget (R-112-07): `DRAFT_ASSAULT_CROSSINGS` crossing(s) (a choke of width `DRAFT_CHOKE_W_MIN` to `DRAFT_CHOKE_W_MAX` wu on the spine plus a way round lane whose length is `DRAFT_BYPASS_MIN` to `DRAFT_BYPASS_MAX` times the way through), `DRAFT_ASSAULT_HEIGHTS` vantage(s) (`DRAFT_VANTAGE_BANDS_MIN` to `_MAX` bands, overlooking a spine lane, two climb lanes), `DRAFT_ASSAULT_PRIZES` pair(s) of significant resources either side of the road at equal route distance, one expansion site per side in its near district; (4) sides mode (R-112-08): `mirror` reflects side A's ground across the map's mid line to make side B's, `rotate` rotates it half a turn about the centre, `separate` grows side B's ground from its own stream with a meander in `DRAFT_MEANDER_MIN` 1.0 to `DRAFT_MEANDER_MAX` 1.6 tuned (a deterministic bisection, `DRAFT_MEANDER_STEPS` iterations) until the route distances match within `DRAFT_EQUAL_TOL` 0.10; (5) names a landform per piece (crossing: ford, pass, gate or canyon; heights: ridge, hill or mesa; home ground: basin, plateau or bend; others none) and builds `requests[]`: one `pad` request per place (mode `room`, name `base_a`, `base_b`, `objective`, `site_0`..), one `choke` per choke (mode `keep_open`, w, len, span, frac, axis_k), one `vantage` per vantage (mode `height`, height_bands, side), one `route` request per lane of kind route/objective_route/way_round (mode `number`, r = lane width), one `landform` request per named landform (mode `keep_open`); (6) `om_lk_run_checks`.

**Canvas**: `DRAFT_CANVAS_ASSAULT` 24,000 wu is what the CLI uses when `--canvas` is absent (S-073: Assault is large; R-116-01 large is 20,000 to 28,000). `om_lk_generate` accepts any canvas in `DRAFT_CANVAS_MIN` 8,000 to `DRAFT_CANVAS_MAX` 64,000 and scales every length by canvas / `DRAFT_CANVAS_ASSAULT`, widths excluded (a choke stays 300 to 700 wu on any canvas).

**Checks** (`om_lk_run_checks`, defined once, used by the generator and by `--check`; the graph is rebuilt from `lanes`, node `i` joined by every lane `a`/`b`):
1. `connected`: every node is reachable from side A's base node.
2. `fairness`: route distances (Dijkstra over lane polyline lengths) from each base to each significant resource: for both resources `abs(dA - dB) <= DRAFT_EQUAL_TOL * max(dA, dB)`; and to the objective too when the archetype has no slant (Assault slants the objective to the defender, so `dist_*_objective` are recorded and not checked for Assault). A distance of -1 fails the check.
3. `bypass`: for every choke on lane L (nodes u, v): length of the shortest u-to-v path avoiding L is at least `DRAFT_BYPASS_MIN` times L's length.
4. `approaches`: the objective node has at least `DRAFT_APPROACHES_MIN` 2 incident lanes, and removing any single one of them leaves the objective reachable from side A's base.
5. `chokes`: every choke width lies in `DRAFT_CHOKE_W_MIN`..`DRAFT_CHOKE_W_MAX`.
6. `bounds`: every place, node, lane point, choke and vantage lies on the canvas (0 to canvas on both axes, a pad or vantage circle wholly inside).

**Determinism**: own splitmix64 `lk_rng` (as `csrc/chronicle.c:702-712`), one stream per concern (districts, side A, side B, pieces, meander), stream seeds derived from the seed by mixing, draws never inside argument lists; angles from the Q16 tables `om_tn_sin_q16`/`om_tn_cos_q16` (`csrc/terrain_noise.c:122-131`: the argument is a turn where 65536 is a full turn, the result is Q16 where 65536 is 1.0; a 15-degree step k is turn `(k * 65536) / DRAFT_AXIS_STEPS` in integer arithmetic with `DRAFT_AXIS_STEPS` 24), no `atan2`; shortest paths by O(n squared) Dijkstra with strict `<` and lowest-index ties; insertion sort (no `qsort`); only `sqrt fabs floor fmin fmax`; coordinates stay doubles internally, quantised only when printed.

**Caps are drafts**: if a candidate needs more than a cap it is discarded (counts as zero passes); a layout that fits no cap makes `om_lk_generate` return -1 (documented, tested by nothing but the determinism sweep needing every seed 1 to 12 green).

### The request list (the B3 seam, fixed now)

`requests[]` follows `om_lk_request` (modelled on `origin/push/proto-terrain-obeys-2` `scenes/mockups/landscape/obey_layer.gd` `build_requests`: pads {name, pos, r}, choke {pos, w, len, frac, span}, vantage {pos, side}, route_count). B3's port reads this array instead of building its own. A request the landscape breaks is the landscape's fault; the layout is never bent (research README section 3).

## Acceptance criteria

Leaf 1, the C engine: `csrc/layout_drafts.h`, `csrc/layout_kit.c`, `csrc/layout_kit_pieces.c`, `csrc/layout_kit_graph.c` (about 1,400 lines across four files, each under 1,500)
1. `om_lk_generate` and `om_lk_run_checks` as the header says and "Design" above: for seeds 1 to 12, Assault, in each of the three sides modes, `checks == OM_LK_CHECKS_ALL` (the kit must not need luck); return codes -1/-2/-3 as the header says; the layout contains exactly one objective, one `base_home` (side B), one `base_forward` (side A), two `resource`, two `expansion` (one per side), `DRAFT_ASSAULT_CROSSINGS` choke(s), `DRAFT_ASSAULT_HEIGHTS` vantage(s), at least `DRAFT_APPROACHES_MIN` approach lanes to the objective, and a `requests[]` list as "Design" step 5.
2. Determinism: two calls with the same inputs fill byte-identical structs (`memcmp` over the whole struct, with the struct zeroed first); the O0 and O2 builds print byte-identical JSON over the 36 layouts (12 seeds by 3 modes).
3. `om_lk_draft_count/name/value` list the `LK_DRAFT_TABLE` entries in order, count at least the drafts named under "Named drafts"; `om_lk_name` returns the strings of the JSON section for ids in range and NULL otherwise.
4. Every numeric literal in `csrc/layout_kit*.c` other than 0, 1, 2 and array sizes is a `DRAFT_` macro (or an `LK_RNG_` constant defined in `layout_drafts.h` beside the table); `scripts/specfactory/libm_lint.py` passes on the new files.

Leaf 2, the CLI: `csrc/tools/layout_dump.c` (about 600 lines)
5. `layout_dump --seed N --archetype assault [--canvas W] [--sides mirror|rotate|separate] [--out file.json]` prints the JSON of "JSON" to stdout, or to the file with `--out` (stdout empty then); defaults: canvas `DRAFT_CANVAS_ASSAULT`, sides separate. `--seeds A..B` (with `--out-dir D`) writes `D/layout_assault_s<N>_<sides>.json` for every seed in A..B and prints one `seed N sides S checks 6/6` line each. Exit 0 on success, 2 on a usage error (stderr names it), 1 when `om_lk_generate` fails (stderr prints the return code). An unknown archetype name exits 2; `--archetype` other than `assault` exits 2 with "not built" (round A).
6. `--break <check>` generates the layout, applies the deterministic edit below, calls `om_lk_run_checks`, and prints the JSON (its `checks` then show the edit): `connected` removes every lane touching the objective node; `fairness` moves resource 0 (the first resource place) 40 percent of the way toward side A's base along the straight line, moving its node and the matching endpoint of every incident lane polyline; `bypass` removes the way-round lane of the first choke; `approaches` removes the lane of kind `objective_route` that is not the spine's (or, if none, any one lane touching the objective); `chokes` sets the first choke's width to `DRAFT_CHOKE_W_MAX` + 100 wu; `bounds` sets the first place's x to canvas + 100 wu (its node too). Positive control: for each name, the named check is false after `--break` and true without it.
7. `--check file.json` reads a JSON written by this tool (fixed key order, so a small hand parser reading numbers, strings and arrays is enough), rebuilds the `om_lk_layout` from `places`, `nodes`, `lanes`, `chokes`, `vantages`, calls `om_lk_run_checks` and prints the six check results as `connected true` ... one per line; exit 0 when all true, 1 when any false.

Leaf 3, the renderer: `scripts/layout/render.py` (about 500 lines, Python 3 with Pillow, no other import)
8. `render.py map <layout.json> <out.png>` draws the map at `DRAFT_PX_WU` 20 wu per pixel (24,000 wu is 1,200 px), drawn at 2x then reduced with LANCZOS, with a sidebar on the right: districts as faint tints by role; lanes as strips with width to scale (a polygon per segment, round joints), `way_round` dashed; chokes as the gap with hatched wall rectangles of `wall_span` either side; each vantage as a triangle, its radius circle and a dashed line to the overlooked lane; places as shapes (base square, objective star, resource diamond, expansion hollow circle), side A in one colour, side B in another, neutral grey; labels of at most two words (`forward camp`, `keep`, `prize`, `expansion`, `choke`, `height`); the sidebar lists seed, archetype, sides mode, both sides' route distances to the objective and to each resource, each check green or red, and every `drafts` value from the JSON. Output names are chosen by the caller.
9. `render.py sheet <dir> <out.png>` draws the 12 layouts `layout_assault_s1_<sides>.json`.. `s12` found in the directory in a 4 by 3 grid (each tile a map without the sidebar, seed number and `6/6` or `n/6` under it); a missing file leaves a labelled empty tile and exit status 1. Fixture-driven tests need no C: `tests/layout/fixtures/layout_hand.json` is a hand-written JSON of the schema.
10. `render.py` exits 2 with a usage message on bad arguments and never opens a window.

Docs and landing (parent-owned, written by the overlord, not a leaf)
11. Makefile targets `layout_dump` (output `build/layout_dump`), `build/O0/layout_dump`, `build/O2/layout_dump` (each compiles `csrc/tools/layout_dump.c` with `csrc/layout_kit*.c` and `csrc/terrain_noise.c`, the `CFLAGS_COMMON` and determinism flags, `-lm`); the ROADMAP layout-engine row (landed sha; S-247 awaiting his approval); `docs/method/harness.md` row if the cascade adds one; `docs/stories/S-247.md` Tests and Scene lines final; `.claude-swarm.toml` placeholders restored; `docs/northstar/story_reviews/westley/README.md` "Waiting on you" gains the round A1 row; the round A1 folder (below).

### Named drafts (new, named for his veto; every number below is a draft until the lab reports)

`DRAFT_CANVAS_MIN` 8000, `DRAFT_CANVAS_MAX` 64000, `DRAFT_CANVAS_ASSAULT` 24000, `DRAFT_CHOKE_W_MIN` 300, `DRAFT_CHOKE_W_MAX` 700, `DRAFT_BYPASS_MIN` 1.5, `DRAFT_BYPASS_MAX` 2.4, `DRAFT_ASSAULT_CROSSINGS` 1, `DRAFT_ASSAULT_HEIGHTS` 1, `DRAFT_ASSAULT_PRIZES` 1, `DRAFT_VANTAGE_BANDS_MIN` 1, `DRAFT_VANTAGE_BANDS_MAX` 3, `DRAFT_MEANDER_MIN` 1.0, `DRAFT_MEANDER_MAX` 1.6, `DRAFT_MEANDER_STEPS` 12, `DRAFT_EQUAL_TOL` 0.10, `DRAFT_CANDIDATES` 5, `DRAFT_APPROACHES_MIN` 2, `DRAFT_JSON_QUANT` 0.01, `DRAFT_PX_WU` 20. Leaf 1 adds the rest it needs (pad radii, lane widths, home-ground sizes, spacings, vantage radius, wall span) as `DRAFT_` macros with a stated reason in its report; Westley owns every threshold and tolerance.

## Tests (parent-owned `tests/**`; the shard-test-writer writes them from this section, red, in the wave base commit; builders never edit tests)

Each names the `S-247`/`R-###-##` it proves. Build helper: compile `csrc/tools/layout_dump.c` + `csrc/layout_kit*.c` + `csrc/terrain_noise.c` into a tmpdir with the flags of `tests/csim/test_VG_P_p1_layout.py:118-121`, `-I csrc`, `-lm`, once per module. Python is `$PY`.
- `tests/csim/test_layout_kit.py` (umbrella, already written): seed 1, Assault, separate: all six checks true and the place kinds present.
- Per check, a file with the positive control through `--break` and a negative control without it: `test_layout_kit_connected.py` (R-112-05), `_fairness.py` (R-112-05: route distance, `DRAFT_EQUAL_TOL`), `_bypass.py` (R-112-05), `_approaches.py` (R-112-05), `_chokes.py` (R-112-05, R-113-03), `_bounds.py` (R-112-05). Also: `--check` on a written JSON agrees with the JSON's own `checks`; `--check` on a hand-edited JSON (a lane deleted) exits 1.
- `test_layout_kit_determinism.py` (R-112-01): two runs of the same inputs byte-identical; O0 and O2 binaries byte-identical JSON over 12 seeds by 3 modes; every seed 1 to 12 green in every mode; different seeds give different `district` grids or places in at least 10 of the 12 (the kit makes different maps); `canvas 8000` and `64000` give a layout inside the canvas with choke widths still 300 to 700.
- `test_layout_kit_header.py` (R-112-06, DRAFT rule): every numeric literal in `csrc/layout_kit*.c` other than 0, 1, 2 and array sizes is a `DRAFT_` macro; `libm_lint.py` clean on the new files; the JSON `drafts` block names every `DRAFT_` macro of the X-macro table; `csrc/layout_kit*` does not include `layout_internal.h` and `simulation/layout_library/` is not read.
- `test_layout_kit_places.py` (R-113-01, R-113-02, R-113-04, R-112-07, R-112-03, R-112-04): counts of places, chokes, vantages as in criterion 1; the objective is nearer side B's base than side A's by route distance (Assault slant); two approaches; each vantage has two distinct climb lanes and an overlooked lane; every place has a pad request, every choke a choke request, every vantage a vantage request, every named landform in `om_lk_name` domain 2; the drafts and checks never read a world.
- `tests/layout/test_render.py` (R-112-04 picture): fixture `tests/layout/fixtures/layout_hand.json` hand-written; `render.py map` writes a PNG of the expected size; a known place pixel has the place colour; the sidebar differs when a `drafts` value in the fixture changes; the sheet has 12 tiles for 12 fixtures (copies of the fixture with different seeds) and a missing one exits 1; bad arguments exit 2.

## Decomposition

Three file-disjoint leaves, one wave: leaf-01 = criteria 1 to 4 (C engine, four files), leaf-02 = criteria 5 to 7 (CLI, depends on the header only), leaf-03 = criteria 8 to 10 (renderer, depends on the JSON schema only; its tests use a hand fixture). Consolidation: leaf 1 stays one leaf (one responsibility, one set of drafts; four files by size). Leaves never run git (the skill's `worktree_ops.py` does). Admission by the skill's gates; the umbrella runs before and after each admit. Criterion 11 is the overlord's.

## Verification (after admission, Linux box; the overlord runs these, then reports once)

1. `make OPT=-O2 WERROR=1`; `make layout_dump build/O0/layout_dump build/O2/layout_dump`; `$PY -m pytest tests/csim/test_layout_kit*.py tests/layout -q -p no:cacheprovider`; `python3 scripts/specfactory/libm_lint.py` clean; `make test` still green except the stale S-112/S-113 tests named in the pre-flight (list them in the report; the existing `tests/csim/test_VG_P_p1_layout.py` untouched and green).
2. Dump 12 seeds by 3 sides modes for Assault with both binaries (`build/O0/layout_dump`, `build/O2/layout_dump --seeds 1..12 --out-dir`); `cmp` every pair byte for byte; running the whole set again gives identical files.
3. Render the three maps (seed 1; mirror, rotate, separate) and three sheets (seeds 1 to 12, one per sides mode) into `docs/northstar/story_reviews/westley/layout_engine/round-A1/` and write its `README.md`: one row per picture with "What to expect / Approve means / Deny means" and a table of every draft (name, value); no agent opens a picture (DEC-no-look-pass-2026-11-05); exact checks are the tests above, run on the JSON, not by eye.
4. The game is untouched (no `csrc/ouroboros_sim.h`, pipe or scene change): the play step of `story_loop.md` step 6 is `scripts/play.sh` opening main to the menu and a mission, unchanged, before the landing merge. Landing is NOT part of this cascade's first run: the overlord stops after step 3 and reports; the Architect merges the pictures folder to main (docs only) for Westley's round; the engine lands on his word "approve" (plan 1.7).

## Scale & Boundary Profile

- **N typical / N peak:** places 8 typical, 32 peak (cap); nodes 40 typical, 96 peak; lanes 40 typical, 96 peak; 12 layouts a sheet.
- **Growth claim per hot path:** Dijkstra is `quadratic` in nodes (96 squared, about 9,000 steps) and runs once per resource per side per candidate (5 candidates, 6 runs, plus the meander bisection, 12 iterations): under 1 M operations per layout; the bypass check runs one Dijkstra per choke; the approaches check one traversal per objective lane; `linear-ish` in everything else.
- **Memory posture:** fixed-size: the layout struct is a few hundred KB at most with no heap; the CLI holds one layout at a time.
- **External call budget:** none; no network, no model, no file read in the engine; the CLI reads/writes only the named files.

## Bible Compliance

- **Bible path:** `docs/bible/game_bible.md`
- **Sections referenced:** `docs/bible/epics/E-17-map-generation.md` S-112 R-112-01 to R-112-08, S-113 R-113-01 to R-113-05, S-247, S-191 R-191-04/R-191-10 (layout first, landscape obeys), Q-191-11 (objective beside the defender), Q-191-13 (sides modes), Q-191-15 and Q-247-01 (closed 2026-11-05), E-10 S-073 and S-210 (Assault, base kinds), R-116-01 (canvas sizes).
- **Deliberate divergences:** one: Assault's objective is not equal-distance (Q-191-11, ruled; the slant is deliberate), so the fairness check covers the significant resources only on this kind.

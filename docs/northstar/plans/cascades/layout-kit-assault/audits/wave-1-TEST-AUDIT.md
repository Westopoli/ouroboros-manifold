# TEST-AUDIT, shard default, wave 1 (S-247 layout kit: leaf-01 engine, leaf-03 renderer)

Fresh-context audit. Read in full: brief, spec, leaf-01, leaf-03, `csrc/layout_kit.h`, sentinel `csrc/layout_kit.c`, probe, fixture, the four test files, umbrella, BOUNDARIES, Q1-Q8, overlord answers. Also run: `libm_lint.py csrc` (OK), `nm` on `terrain_noise.c` (no undefined symbols), assert counts (engine 28 + header 9 = 37 <= 40; render 15). Under the sentinel every test is red for the stated reason (rc -1, NULL names, 0 drafts, missing files, missing render.py); none passes by accident. No sleeps anywhere. Format: severity, quote, file:line, fix.

Counts: red 1, yellow 15, green 12.

## 1. Goal fidelity and umbrella alignment

**RED R1 - the umbrella cannot go green with a spec-conforming engine.**
Quote: `srcs = sorted(CSRC.glob("layout_kit*.c"))` then `cc ... str(cli), *map(str, srcs), "-lm"` (no `terrain_noise.c`). Spec Determinism: "angles from the Q16 tables `om_tn_sin_q16`/`om_tn_cos_q16`"; criterion 4: "`csrc/terrain_noise.c` has no undefined symbols ... so the CLI links it alone"; criterion 11 Makefile targets compile "`csrc/layout_kit*.c` and `csrc/terrain_noise.c`". The engine test links it (`test_layout_kit_engine.py:76`); the umbrella does not.
File: tests/csim/test_layout_kit.py:24-26.
Fix: add `CSRC / "terrain_noise.c"` to the cc line (as the engine test does). Otherwise wave 2 ends with an undefined-reference link failure and the umbrella stays red after leaf 2 is admitted, which the "goes green when leaf 2 is admitted" gate expects.

**YELLOW Y12 - overlord rulings Q1-Q3 are now spec and have zero assertions.**
Quote (answers): "a domain out of range is NULL too; draft accessors return NULL / 0.0 out of range" and "the order of the header comment applies (NULL out, then archetype, then canvas and sides)". Header: "-1 for a NULL out; -2 ... archetype; -3 ... canvas ... or sides_mode". Tests only cover ids -1/n (`:411`), indexes in range (`:419`), one fault at a time (`:177-182`).
Fix: (a) the combination `(arch 9, canvas 0)` -> -2 and `(arch 9, sides 3)` -> -2 and `(arch 3, canvas 0, sides 3)` -> -3 need no probe change, add them to the parametrize list at :177; (b) extend the parent-owned probe `names` to domains -1 and 6 and `drafts` to index -1 and count, then assert NULL / NULL / 0.0; (c) a NULL out with a bad archetype needs a probe mode (`null` takes fixed valid args, probe:115-118).

**YELLOW Y13 - "zeroed first" and cross-call state are invisible to the tests.**
Quote: header "fills *out (zeroed first)"; test `:332` "same seed ... byte-identical layout on a second run". Probe `cmd_gen` does `memset(&l, 0, sizeof l)` before the call (probe:84) and runs one layout per process, so an engine that forgets to zero, or keeps a `static` counter/stream between calls, passes every determinism test.
File: tests/csim/layout_kit_probe.c:78-90; test_layout_kit_engine.py:328-338.
Fix: probe mode that fills the struct with 0xA5, generates seed A, then seed B, then seed A again in one process and prints all three dumps; assert dump1 == dump3 and each equals the single-run dump.

## 2. Engine tests (tests/csim/test_layout_kit_engine.py)

**YELLOW Y8 - checks 1 (connected) and 4 (approaches) have no independent oracle.**
Quote: "Every expectation is computed here ... never from the engine's own check bits alone" (:7-9). Only fairness (:222-238), bypass (:241-263), chokes and bounds (:349-365) are recomputed. `connected` ("every node is reachable from side A's base") is only the bit in `0x3F`; fairness only checks resources and objective finite, not expansion/vantage/choke nodes. `approaches` is `sum(... lane touches obj_node) >= APPROACHES_MIN` (:215), which counts a lane from side B's own base and a way_round twin; the spec check is "removing any single one of them leaves the objective reachable from side A's base".
Fix: in the fairness test assert `all(math.isfinite(x) for x in da)` over all nodes; in the counts test, for each lane `i` incident to the objective assert `dijkstra(d, na, skip_lane=i)[obj]` is finite.

**YELLOW Y9 - spec-pinned relations of choke and vantage pieces are not asserted.**
Quote (spec Design 3): "a choke ... on the spine", "`DRAFT_ASSAULT_HEIGHTS` vantage(s) ... overlooking a spine lane, two climb lanes"; R-113-04 "overlooks one lane and is reached by two climb lanes". Tests: `d["lane"][ov]["kind"] != L_CLIMB` (:277) accepts a hidden or way_round lane as the overlooked lane; the choke's lane kind is never checked; choke `(x, y)` lying at `frac` of its lane polyline is never checked; climb lanes are not required to touch the vantage (`overlooks`/`climb` can be any two climb lanes); `ck["length"] > 0` (:250) pins no length rule; `wall_span` has no assertion at all though the renderer draws it.
Fix: `kind in (L_ROUTE, L_OBJROUTE)` for the choke lane and the overlooked lane; interpolate the lane at `frac` and compare to `(x, y)` within 0.05 wu; require each climb lane to have an endpoint within `radius` of the vantage; `wall_span > 0`.

**YELLOW Y10 - the canvas extremes are tried on one seed.**
Quote (spec Tests): "canvas 8000 and 64000 stay inside the canvas with choke widths 300 to 700"; code `d = gen(probes, 3, sides, canvas=canvas)` (:355). Seed 3 x 3 sides x 3 canvases = 9 layouts; 1 of 12 seeds at the two canvases that stress the 300-700 wu fixed widths (8,000 is a third of the default).
Fix: parametrize seeds 1..12 at `CANVAS_MIN` and `CANVAS_MAX` (24 more probe calls).

**YELLOW Y11 - sides modes and districts: weak or presence-only.**
Quotes: R-112-08 "mirror gives side B the mirror image of side A's ground, rotate a rotated copy"; test pins the expansion pair only (Q4, accepted by overlord). `separate` holds when `sum(...) < len(SEEDS)` (:399), i.e. one differing seed of twelve. District test (:368-376): one layout (seed 7, rotate, canvas 30000), `{1..6} <= roles` presence only. Zero assertions: that bases/resources follow the transform, that the bases/objective/expansions sit in HOME_A/HOME_B/OBJECTIVE/NEAR_A/NEAR_B cells, that a division pattern (band, ring, two patches) exists, that `candidate` is the first with 6/6 (only `0 <= candidate < 5`).
Fix: separate -> require at least 10 of 12 seeds to be neither rotate nor mirror (matches the "different seeds" threshold); district test over all 36 with each role present and the grid not constant across seeds; mirror/rotate -> also assert the two resources (they are an unordered pair, compare as sets) follow the transform; ask the Architect whether the bases follow (Q4 (a)/(b)/(c) was closed without a ruling on them).

**YELLOW Y14 - draft table order is spec, not tested.**
Quote: criterion 3 "`om_lk_draft_count/name/value` list the `LK_DRAFT_TABLE` entries in order". Test builds `table = {r[2]: ...}` (:420), a dict, so order is lost; `:423` compares values only.
Fix: assert the probe's name sequence equals the `X(DRAFT_...,` order parsed from `csrc/layout_drafts.h` with a regex.

**YELLOW Y15 - small spec details with zero assertions.**
Quotes: Design 3 "pair(s) of significant resources either side of the road"; R-112-07 "side B holds the objective beside it"; request field `piece` (`om_lk_request.piece`) never compared in :295-324; request `name` -> place mapping checked only for `base_a`/`base_b` (:309), so `objective` or `site_N` may sit on any place; resource/objective `side` (neutral, -1) never asserted (:216 covers only bases and expansions).
Fix: check `names["objective"]` equals the objective place xy; resources on opposite sides of the A-B straight line (cross-product sign); neutral places have side -1; pad request `piece` equals the place's `piece`.

**GREEN (engine).** Return-code table incl. both inclusive canvas ends (:177-188) is one fault at a time and each row is red under the sentinel. 36-layout sweep (:197-202) asserts rc, the integer and the six bits, not only the integer. Fairness (:222-238) uses an independent Dijkstra and also compares the engine's reported distances (so a lying `fairness` struct fails). Chokes (:241-263) rebuild the bypass from dumped lanes (slack 0.002 on the ratio, 1 wu on path length, both defensible). Requests (:295-324) compare the whole list against the dumped places/chokes/vantages, route count equals `route_count`. O0 vs O2 (:335-338) compares 36 full-text dumps. Different seeds (:341-346) is per mode, threshold 10/12 from the spec. Names (:404-411) cover all six domains with -1 and n. Drafts (:414-423) check 21 values in hundredths (checked: 0.1, 1.6, 2.4, 0.01 round identically in Python and in the probe's `floor(v*100+0.5)`). Choke/vantage tests are vacuous on empty lists (:248, :273) but the counts test (:217-219) pins exactly 1 each. Mirror axis may be x or y mid line per seed (:396): a diagonal division axis would fail it (Q4 raised, overlord accepted).

## 3. Header tests (tests/csim/test_layout_kit_header.py)

**YELLOW Y6 - the test does not prove that every literal is a DRAFT_ macro, only that no literal is in the .c files.**
Quote: criterion 4 "Every numeric literal ... other than 0, 1, 2 and array sizes is a `DRAFT_` macro (or an `LK_RNG_` constant defined in `layout_drafts.h`)". Test docstring: ":47 ... is a DRAFT_ (or LK_RNG_) macro". The check scans `.c` only; `#define LK_MAGIC 37` or an `inline` helper full of literals in `layout_drafts.h` passes. `assert "LK_DRAFT_TABLE" in drafts and "LK_RNG_" in drafts and "DRAFT_EQUAL_TOL" in drafts` (:62) is satisfied by a comment. `_ARRAY_SIZE = \[\s*\d+\s*\]` (:19) also strips every subscript, so `tab[37]` and `x[5]` in code are never flagged.
Fix: in `layout_drafts.h` require `#\s*define\s+LK_DRAFT_TABLE\s*\(\s*X\s*\)`, at least one `X\(\s*DRAFT_\w+\s*,`, and that every `#define NAME <number>` outside the table has `NAME` starting `LK_RNG_` or `DRAFT_`; restrict the array-size strip to declarations (`\b(int|double|char|...)\s+\w+\s*\[...\]`) or accept the subscript loophole in writing.

**YELLOW Y7 - "no heap, no clock, no file" is a six-name regex.**
Quote: ":65 ... never allocates or reads a clock or file" vs `\b(malloc|calloc|realloc|free|fopen|getenv)\s*\(` (:73). `time`/`clock`/`rand` are covered by libm_lint, but `fread`, `fgets`, `fscanf`, `open`, `popen`, `system`, `strdup`, `alloca`, `gettimeofday`, `clock_gettime` are not (not in `BANNED`).
Fix: widen the alternation; or assert the kit `.c` files include only `<stdint.h>`, `<stddef.h>`, `<math.h>`, `layout_kit.h`, `layout_drafts.h` (leaf-01 brief: "Include `<stdint.h>` and `layout_kit.h` only").

**GREEN (header).** Detector control with flagged and spared samples (:51-55) runs before the real scan, so a broken regex is caught. Hex, float, suffix, `#define` bodies, comments, strings are handled. R-112-06 test (:76-81) reads all `layout_kit*` plus the drafts header and requires the header to exist. Mis-cited ids: the file-set and literal tests cite R-112-02 (districts on a grid) for a file/literal rule, and the lint test cites R-112-01; the rule is criterion 4 / CLAUDE.md "every figure a DRAFT_ macro". Harmless, but a traceability tool would mark R-112-02 covered by the wrong thing.

## 4. Renderer tests (tests/layout/test_render.py)

**YELLOW Y1 - side colour cannot be told from kind colour; "neutral grey" passes vacuously.**
Quote: criterion 8 "side A in one colour, side B in another, neutral grey". Test compares the base_forward (A) and base_home (B) centres, `ca != cb` (:123); they differ in kind too (forward camp vs home), so a renderer colouring by kind passes. Grey is only `max(c) - min(c) <= GREY_SPREAD` at two resource centres (:122-124), with no comparison to the ground under them and no check that grey differs from A and B (a low-saturation A colour, or the plain background if the resource were not drawn, passes).
File: :115-124.
Fix: compare the two expansions (same kind, side A vs B: `places[5]`, `places[6]`) and a variant that swaps `side` on both bases; add `grey != ca`, `grey != cb`, and `grey != mode_colour(moved-away variant)` for the resource.

**YELLOW Y2 - "dashed" is measured as lower coverage, not as gaps.**
Quote: criterion 8 "`way_round` dashed". Test: `0 < dashed[side] < solid[side]` (:154), pixels that change when the lane is parked. A thinner, fainter-but-solid, or half-width way_round line has fewer changed pixels and passes.
File: :137-154.
Fix: sample the 1 px centre row along the middle segment (x 150..190) in the `way_round` render versus its parked variant and assert at least two separate runs of changed pixels with an unchanged pixel between them, while the `route` render has one unbroken run.

**YELLOW Y3 - sidebar contents are 5 of the spec's 9 items.**
Quote: criterion 8 "the sidebar lists seed, archetype, sides mode, both sides' route distances to the objective and to each resource, each check green or red, and every `drafts` value". Edits tried (:165-177): one drafts value, one new draft, seed, `checks.bounds`, `fairness.dist_a_objective`. Zero assertions: archetype, sides mode, `dist_b_objective`, `dist_a_res`, `dist_b_res`, the other five checks, and green vs red as colour (a flip from "ok" to "fail" in the same ink passes).
File: :165-188.
Fix: add kinds `archetype`, `sides`, `dist_b_objective`, `dist_a_res`, `dist_b_res`; for `check`, assert the changed sidebar pixels move from green-dominant to red-dominant (`g > r` before, `r > g` after).

**YELLOW Y4 - drawing details pinned by the spec with zero assertions.**
Quote: criterion 8: "districts as faint tints by role", "round joints", "chokes as the gap with hatched wall rectangles of `wall_span` either side", "each vantage as a triangle, its radius circle and a dashed line to the overlooked lane", "places as shapes (base square, objective star, resource diamond, expansion hollow circle)", labels of at most two words, "drawn at 2x then reduced with LANCZOS". Tests only prove that something changes near a choke or vantage when its list is emptied (:157-162), a place moves (:105-112), a lane widens (:127-134).
Fix (pixel-checkable ones): edit `district[r][c]` role and assert a change inside the map; set `wall_span` 400 -> 1200 and assert changes 40 px but not 70 px from the choke; set `radius` 400 -> 1200 and assert the same; swap the objective `piece`/kind and assert only that place's shape changes; assert a lane edge has an intermediate-tone pixel (anti-alias evidence of 2x + LANCZOS), or AST-check `Image.LANCZOS`. Labels cannot be asserted without OCR: list as a Westley-eye item.

**YELLOW Y5 - sheet: tile content, empty-tile label, filenames and an over-tight split.**
Quote: criterion 9 "each tile a map without the sidebar, seed number and `6/6` or `n/6` under it; a missing file leaves a labelled empty tile". Tests: 12 cells distinct and multi-colour (:221-224) would hold for 12 tiles of seed number text only; nothing shows a map is inside a tile. The missing test needs the empty cell to differ from the drawn one (:232), not to carry a label (a blank cell passes). Only `layout_assault_s{N}_separate.json` is used (:202), the spec names `<sides>`. `_cells` splits the image into equal 4 x 3 cells and trims 8 px (:208-211); a legitimate sheet with an outer margin, a title strip or gutters wider than 8 px makes the missing-seed test see two differing cells (false red; Q6 (iv) says tile order is free but not geometry).
Fix: mutate seed 3 by `moved(0)` and assert exactly cell 3's upper area changes (proves a map per tile); assert the missing-seed cell has more than one colour (label ink); run one sheet with `_mirror` names; locate the tiles by clustering the non-background bounding boxes rather than by an equal split, or have the Architect rule the layout (no margins) into the spec.

**GREEN (renderer).** Map size (:96-102) accepts any width > 400 (sidebar) and height >= 400, and the 20 wu/px scale is proven by place positions inside the pad radius (:105-112, y-up and y-down both handled, FAR parking is real). Lane width to scale (:127-134) has a near pair that must change and a far pair that must not (window of about 0.67x to 1.67x of the right width). Sidebar edits assert both that the sidebar changes and the map region does not (:188). Failed-check and missing-seed tiles are different and each touches exactly one cell (:227-242). Bad-argument cases (:246-252) pin exit 2 and "usage". Static test (:255-270) checks stdlib or PIL, no tkinter/webbrowser, no `.show`, constant 20. Not tested and silent in the spec: `sheet` with 3 args, a directory with 0 or more than 12 files, `map` on a missing or malformed file (Q6 (vi)).

## 5. Boundary and scale fidelity

Boundary table is accurate except one line: BOUNDARIES says place colours "compares with the place moved away; grey = channel spread <= 16" - the grey half does not compare with the moved-away variant (Y1). Scale: caps, no scale assertions (litigated). Not covered by the table and not a finding on their own: `om_lk_run_checks` is untouched by wave 1, so admitting leaf 1 with a no-op `om_lk_run_checks` passes every wave-1 test (the generator sets `checks` itself); wave 2 `--break` and `--check` are the only gate. The overlord should hold the leaf-02 admission to that, since criterion 1 also lists `om_lk_run_checks`.

## Summary table

| id | sev | where |
|---|---|---|
| R1 | red | test_layout_kit.py:24-26 umbrella lacks terrain_noise.c |
| Y1 | yellow | test_render.py:115-124 side vs kind colour, grey vacuous |
| Y2 | yellow | test_render.py:137-154 dashed measured as coverage |
| Y3 | yellow | test_render.py:165-188 sidebar 5 of 9 items |
| Y4 | yellow | test_render.py (many) shapes, wall_span, radius, tints, AA |
| Y5 | yellow | test_render.py:208-242 sheet tile content, label, names, split |
| Y6 | yellow | test_layout_kit_header.py:19,47-62 macro-name rule unproven |
| Y7 | yellow | test_layout_kit_header.py:73 heap/clock/file regex |
| Y8 | yellow | test_layout_kit_engine.py:205-238 connected/approaches no oracle |
| Y9 | yellow | test_layout_kit_engine.py:241-280 spine, climb, frac, wall_span |
| Y10 | yellow | test_layout_kit_engine.py:349-365 extremes one seed |
| Y11 | yellow | test_layout_kit_engine.py:368-400 sides/districts weak |
| Y12 | yellow | test_layout_kit_engine.py:177-182,404-423 Q1-Q3 rulings untested |
| Y13 | yellow | layout_kit_probe.c:78-90 zero-first and cross-call state hidden |
| Y14 | yellow | test_layout_kit_engine.py:414-423 draft order |
| Y15 | yellow | test_layout_kit_engine.py:295-324 small unasserted details |

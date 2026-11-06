# TEST-AUDIT-R2, shard default, wave 1 (S-247 layout kit)

Fresh-context round 2. Read in full: R2 brief, round 1 report, overlord answers and waivers, Q4 and Q6, spec, `csrc/layout_kit.h`, sentinel, probe (new `chain`, `null`, `names`, `drafts` modes), the umbrella, the three test files, fixture, leaf-03 brief. Ran the suite under the sentinel: 486 failed, 0 passed (nothing green by accident). I also ran a throwaway PIL experiment (2x draw, LANCZOS reduce, same as the spec's renderer) to test the dashed-lane assertion; the scratch script is at `/tmp/claude-1000/-home-westopoli-Projects-ouroboros-manifold/db98320a-0522-401b-91ae-f1f3583f73a5/scratchpad/dash.py`.

Counts (new and residual findings only): red 2, yellow 7, green 14 (closures and confirmed new assertions).

## 1. Status of R1 and Y1..Y15

| id | status | new assertion (quote) |
|---|---|---|
| R1 | closed | umbrella `srcs = sorted(CSRC.glob("layout_kit*.c")) + [CSRC / "terrain_noise.c"]` (test_layout_kit.py:24) |
| Y1 | closed | `gap(a_full, b_swap) < gap(a_full, b_full)` on the two expansions, and `g != ca and g != cb and g != ground` for the resources (test_render.py:149-165) |
| Y2 | replaced, new RED (N1) | `route_runs == 1 and all(route_flags) and dashed_runs >= 2` (:194) |
| Y3 | closed | `_sidebar_edit` kinds `archetype`, `sides`, `dist_b_objective`, `dist_a_res`, `dist_b_res` (:246-259); `ok_green > ok_red and bad_red > bad_green` (:287) |
| Y4 | partly closed | wall_span and radius `REACH_MIN <= reach(...) <= REACH_MAX` (:211); district tint (:224); AA tones and `"LANCZOS" in names` (:235). Open: see N7 |
| Y5 | partly closed | `test_S_247_each_tile_holds_its_own_map` (:337), `_sheet(..., sides="mirror")` (:330), `len(cell.getcolors(...)) > 1` (:356). Open: see N4 |
| Y6 | closed (residual written down) | `re.search(r"#[ \t]*define[ \t]+LK_DRAFT_TABLE...` and `stray == []` (header:72-73); `y * tab[37]` loophole documented in the docstring (:8-9) |
| Y7 | closed | widened alternation `alloca|strdup|fopen|fread|fgets|fscanf|open|popen|system|getenv|gettimeofday|clock_gettime` plus `ALLOWED_INCLUDES` (header:87-89) |
| Y8 | closed | `all(math.isfinite(x) for x in da)` (engine:264) and `cut_ok = all(math.isfinite(dijkstra(d, na, skip_lane=i)[obj_node]) ...)` (:246) |
| Y9 | closed | `lane["kind"] in (L_ROUTE, L_OBJROUTE) and dist <= ON_LANE and abs(at - ck["frac"] / 100.0) <= FRAC_TOL` (:287); `ck["wall_span"] > 0` (:282); climbs end within `radius` of the vantage (:314) |
| Y10 | closed (but see N3) | `CANVAS_CASES = [(CANVAS, 3)] + [(c, s) for c in (CANVAS_MIN, CANVAS_MAX) for s in SEEDS]` (:405) |
| Y11 | partly closed | separate `>= SEPARATE_MIN` (:467); district roles over all 36 (:437). Open: N2 (red) and N8 |
| Y12 | closed | return-code combinations `(9, 0, 0, -2) ... (3, 64001, -1, -3)` (:203); `null` mode `(0, -1, -1, -1)` (:218); `domain` `[-1] + ... + [6]` (:472); `oob == [["oob", "-1", "NULL", "0"], ["oob", str(count), "NULL", "0"]]` (:498) |
| Y13 | closed | `chain` mode, 0xA5 fill, seeds 5, 9, 5, `"tail_clean 1 1 1"` (:381-386); probe `tail_clean` is field by field |
| Y14 | closed | `[r[2] for r in rows] == order` with `order` parsed from `X(DRAFT_...,` in `layout_drafts.h` (:494-497) |
| Y15 | partly closed | pad `(x, y, r, piece)` equals place `(x, y, pad_r, piece)` (:346); `names["objective"]` equals the objective's xy (:349); resource sides `[-1, -1]` (:249). Waived by overlord: objective side, "either side of the road". Remaining: N9 |

## 2. New findings

**RED N1 - the dashed-lane test fails a legitimately dashed lane.**
Quote: `flags = [[changed_pixels(on, off, (x, r, x + 1, r + 1)) > 0 for x in range(*RUN_X)] ...` then `route_runs == 1 and all(route_flags) and dashed_runs >= 2` (test_render.py:190-194). Spec criterion 8: "`way_round` dashed", "drawn at 2x then reduced with LANCZOS".
Why: `> 0` counts any change, and a LANCZOS reduction from 2x leaks ringing up to about 3 output px past a dash, so a gap pixel is "unchanged" only when the gap is about 7 px or more. Experiment (4.5 px wide lane, 2x draw, `Image.LANCZOS`, centre row, x 180..370): dash/gap 6/3, 8/4, 8/6 and 10/6 px give `runs 1` (read as solid, test red); 10/8, 12/8 and 16/8 give 9 to 11 runs. A conforming renderer with an ordinary 8 on / 6 off dash is rejected, and the builder cannot tell why.
Fix: count a pixel as changed only above a tone threshold (e.g. `> 16` on the `L` difference); same experiment with thresholds 8, 16 and 40 gives 10 to 19 runs for all five dash shapes above and an unbroken run for the solid lane. Put the threshold in a named constant.

**RED N2 - mirror and rotate now require the two resources to follow the transform; the spec and the overlord's ruling do not.**
Quote: `close(b, rot(a)) and pair(res, [rot(r) for r in res])` and `any(close(b, f(a)) and pair(res, [f(r) for r in res]) for f in mirrors)` (test_layout_kit_engine.py:464-465); docstring "in both the two resources, as an unordered pair, map onto each other by the same transform". Spec Design 3: the prizes are grown in "the contested district" ("`DRAFT_ASSAULT_PRIZES` pair(s) of significant resources either side of the road at equal route distance"); Design 4: mirror "reflects side A's ground across the map's mid line to make side B's". Test-writer Q4 asked whether "(a) bases, expansions and resources all follow ... (b) only expansions ... (c) bases too but resources stay on the road"; overlord answer: "the tests check the expansion pair only. Accepted as written."
Why: this reverses the ruling and tests candidate (a). Fairness is by route distance within `DRAFT_EQUAL_TOL` 0.10, not by geometry, so a conforming engine can place the prize pair anywhere equidistant by route (contested ground is neither side's), and then `pair(res, f(res))` fails to 0.02 wu on all 24 mirror and rotate seeds. The builder would be forced to build to the test, not the spec.
Fix: remove the two `pair(...)` conjuncts (back to the expansion pair), or have the Architect add "the prize pair is symmetric under the sides transform" to Design 4 first.

**YELLOW N3 - extreme canvases assert all six checks, which the spec asks of the default canvas only.**
Quote: `assert d["kv"]["rc"] == 0 and d["kv"]["checks"] == 0x3F and wu(d["kv"]["canvas"]) == canvas` (engine:415), now over 12 seeds x 3 modes at 8,000 and at 64,000. Spec Tests: "canvas 8000 and 64000 stay inside the canvas with choke widths 300 to 700"; criterion 1 pins `checks == OM_LK_CHECKS_ALL` for seeds 1 to 12 at the Assault canvas.
Why: a conforming engine may return rc 0 with a failing fairness or bypass bit at a canvas where fixed 300 to 700 wu widths dominate; the test then fails it on a claim the spec does not make (24 more layouts than before).
Fix: at the extremes assert `checks & (OM_LK_CHECK_BOUNDS | OM_LK_CHECK_CHOKES) == 0x30` plus the dump-side geometry already there; or ask the Architect to put "all six at any accepted canvas" in the spec.

**YELLOW N4 - sheet tests locate tiles by an equal split of the whole image (Y5 residual), and the label of the empty tile is still unproven.**
Quote: `_cells`: "The 4 x 3 equal split of the whole image, no trim (the spec fixes the grid, not margins or gutters)" (render:308-311), used by `len(one) == 1`, `len(gone) == 1`, `one != other` (:345, :355, :366). Spec criterion 9: "in a 4 by 3 grid (each tile a map without the sidebar, seed number and `6/6` or `n/6` under it); a missing file leaves a labelled empty tile".
Why: the R1 trim of 8 px was dropped, so the tests are stricter. Any sheet whose tiles do not sit exactly inside the equal-split cells (an uneven margin, a title strip, tiles separated by unequal gutters) lets one changed tile touch two cells and fails `len(...) == 1` although it is a correct 4 by 3 grid. Separately `len(cell.getcolors(...)) > 1` (:356) holds for an empty bordered box with no text.
Fix: find tiles by the connected non-background boxes of the full sheet (12 boxes, sorted row-major) and compare per box; or the Architect rules "no outer margin, equal tiles" into criterion 9. Label stays a Westley-eye item; say so in the docstring.

**YELLOW N5 - sidebar edits compare only the shared height, so a renderer that grows taller hides the new row.**
Quote: `h = min(a.height, b.height)` ... `side = changed_pixels(a, b, (MAP, 0, min(a.width, b.width), h))` (render:270-271); `drafts_new` appends `DRAFT_BRAND_NEW_ONE`. Test-writer Q6 (i): the spec is silent on "whether the image grows taller than canvas/20 px".
Why: the hand fixture is 400 px tall with about 25 sidebar lines (seed, archetype, sides, six distances, six checks, eight drafts); at 16 px a line the sidebar is already at the limit. A renderer that extends the image for the ninth draft puts the new line below `h`, the only change is in the region not compared, and `side > 0` fails for a correct renderer (same for `tones` in the green/red test, :280).
Fix: pad the shorter image to the taller one's height with its own background before diffing, or compare `max` height.

**YELLOW N6 - the old-library test reads comments.**
Quote: `hits = [n for n, t in texts.items() if "layout_library" in t or re.search(r'#\s*include\s*[<"]layout_internal\.h', t)]` (header:96). Spec R-112-06 / criterion 4: the kit "reads" neither `simulation/layout_library/` nor `layout_internal.h`.
Why: the substring is matched over raw text, comments included. CLAUDE.md asks for traceability comments ("reference only: simulation/layout_library"); one such comment, or the spec's own "reference only (R-112-06)" note copied into a header, fails a kit that reads nothing. The include half already ignores prose.
Fix: strip comments with `_STRIP` before the substring test, or match `fopen`/`#include` with the path.

**YELLOW N7 - renderer drawing details still unproven or proven weakly (Y4 residual).**
Quote: criterion 8 "round joints", "hatched wall rectangles", "a dashed line to the overlooked lane", "places as shapes (base square, objective star, resource diamond, expansion hollow circle)". `test_S_247_district_roles_are_faint_tints_and_each_kind_has_its_own_shape` (:214-224): changing the objective's kind to `resource` changes pixels at the objective and at no other place.
Why: that proves "kind affects the drawing" (a different label or colour alone passes), not that the shapes differ. Joints, hatching and the overlook line have no assertion (the docstring lists them as Westley-eye, lines 14-15, which is accepted).
Fix: keep as Westley-eye items; for the shape claim compare the two kinds' pixel bounding boxes or silhouettes with colour removed (mask nonzero difference to ground), or rename the test to "kind changes the drawing".

**YELLOW N8 - sides modes and districts: placement in cells and candidate are still open (Y11 residual).**
Quote: R-112-02 "district grid" and Design 3 "place home A ... in the objective district"; `0 <= k["candidate"] < CANDIDATES` (engine:440). Not asserted: bases, objective and expansions lie in their HOME_A, HOME_B, OBJECTIVE, NEAR_A or NEAR_B cells; a division pattern; `candidate` is the first with 6 of 6.
Why: the district grid can be filled with a valid role set and ignored by the places; the overlord waived the base/transform question only.
Fix: add a test that maps each place to its cell (`int(x * 8 / canvas)`, row/col order per the probe dump, accept either axis order) and requires base_forward in HOME_A, base_home in HOME_B, objective in OBJECTIVE, expansions in NEAR_A or NEAR_B by side. Ask the Architect whether row or column comes first before writing it.

**YELLOW N9 - small unpinned assertions and brittle static checks.**
Quotes: `(0, 1, [0, 1], [-1, -1])` (resource sides, engine:249): the header says "-1 = neutral" and the renderer draws "neutral grey" but no spec line says the resources are neutral (the overlord waived the objective's side for this reason); `sorted((r["x"], r["y"], r["r"], r["piece"]) ...` (:346): "a pad request carries its place's piece" appears in no spec line; render:393 `consts = {t.id: n.value.value for n in ast.walk(tree) if isinstance(n, ast.Assign) ...}` misses `DRAFT_PX_WU: float = 20.0` (an `AnnAssign`).
Fix: have the Architect state "resources are neutral" and "pad requests carry the place's piece" in Design (cheap and probably intended), or drop the clauses; accept `ast.AnnAssign` too.

## 3. Green (checked, no action)

- R1: the umbrella now links `terrain_noise.c` exactly as the engine test does (criterion 4 and Makefile text agree).
- Y1: side colour is separated from kind colour (two expansions of the same kind; both bases swap); the grey assertions compare with the moved-away ground. Expansions sit at integer pixel centres, so equal shapes blend equally; `ink()` takes the highest-contrast pixel of both images.
- Y3: all nine sidebar items of criterion 8 now have an edit; green/red is measured as channel dominance on the changed pixels only (`TONE` 40). Mapped region stays unchanged (`mapped == 0`, Q6 (vii) accepted).
- Y6 and Y7: detector control strings still run first (flagged and spared samples); `stray` rejects `#define LK_MAGIC 37`; widened banned-call list and include allowlist (overlord waiver for the allowlist stands; note for the builder: the allowlist excludes `<string.h>`, so the "zeroed first" fill must be a loop or `__builtin_memset`, and `om_internal.h` is not allowed although the spec's criterion 4 would permit it).
- Y8 and Y9: oracle Dijkstra now covers connectedness and the per-lane cut; choke lane kind, position at `frac`, vantage overlook kind and climb endpoints are asserted with quantisation-sized tolerances (ON_LANE 0.05, FRAC_TOL 0.006, GEO_SLACK 0.02) that a correct engine meets.
- Y12: probe `names` now asks domains -1 and 6 and ids -1..count; `drafts` prints the two `oob` rows; the `null` mode takes bad archetype, canvas and sides; each row is red under the sentinel (it returns -1 for everything, NULL, 0).
- Y13: `chain` fills 0xA5 once, never clears, runs seed A, B, A; run 3 equals run 1 and each equals the one-shot `gen`; `tail_clean` is field-by-field (padding ignored) and range-checks the counts first. Under the header text ("fills *out (zeroed first)") a correct engine passes.
- Y14: `order` regex tolerates whitespace and line breaks inside `X(`; sentinel count 0 fails `count >= len(NAMED_DRAFTS)`.
- Y10 (as a geometry test): inside-canvas and choke-width checks use the dump with a 0.02 wu slack; circle margins for pads and vantages are right.
- Request tests: choke and vantage numbers compare whole records; the vantage `height_bands` is compared as `bands * 100` (the probe prints hundredths); the route multiset `(r, mode)` equals the lane widths; `route_count` equals both. A tie in `side_of` is computed on quantised integers; it differs from the engine's double compare only when the two distances are equal within 0.005 wu, so a conforming engine passes in practice.
- Return-code table (:197-204) is one fault at a time plus combinations in the header's order; inclusive ends 8000 and 64000; every row distinct.
- Determinism: O0 versus O2 over 36 full-text dumps; `chain` adds cross-call state; different seeds per mode at the spec's 10 of 12.
- Lane width, place position, chokes and vantages drawn, wall_span and radius to scale (`REACH_MIN..REACH_MAX` accommodates the 10 px half gap plus 60 px wall and a few px of ringing), sidebar changes, failed-check tile and bad-argument cases are all sound as written; assertion budget (engine + header) was 37 in round 1 and stays within the stated 40 by the file's own count rule.

## Summary table

| id | sev | where |
|---|---|---|
| N1 | red | test_render.py:187-194 dashed measured with a zero-tolerance diff; 8 on / 6 off dashes read as solid |
| N2 | red | test_layout_kit_engine.py:464-465 resources must follow mirror/rotate; reverses overlord Q4 ruling |
| N3 | yellow | test_layout_kit_engine.py:405,415 all six checks at canvas extremes |
| N4 | yellow | test_render.py:308-311,345,355-366 equal split, no trim; empty-tile label unproven |
| N5 | yellow | test_render.py:270-273,280 compare min height only |
| N6 | yellow | test_layout_kit_header.py:96 "layout_library" matched in comments |
| N7 | yellow | test_render.py:214-224 shape claim passes on a label-only change; joints/hatch/overlook line unproven |
| N8 | yellow | test_layout_kit_engine.py:427-440 places not tied to district cells; candidate unpinned |
| N9 | yellow | engine:249,346; render:393 unpinned resource side, pad piece; AnnAssign |

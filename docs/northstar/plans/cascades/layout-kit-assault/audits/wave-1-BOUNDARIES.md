# BOUNDARIES, wave 1 (S-247 layout kit: leaf-01 engine, leaf-03 renderer)

Spec = `docs/northstar/plans/cascades/layout-kit-assault/spec.md`; header = `csrc/layout_kit.h`. Axes: CORRECT (test-design.md).

| symbol | axis | boundary | spec says | disposition |
|---|---|---|---|---|
| `om_lk_generate` | Existence | `out == NULL` | header: -1 | test written (`null_out_returns_minus_one`) |
| `om_lk_generate` | Range | archetype -1, 0, 2, 4, 9, 10 (3 is the only built one) | header: -2 outside 0..9 or not built | test written, 6 cases |
| `om_lk_generate` | Range | canvas 7999 / 8000 / 64000 / 64001 / 0 / negative | spec Design: `DRAFT_CANVAS_MIN` 8,000 to `_MAX` 64,000 accepted; header: -3 outside | test written; both ends inclusive ("accepts any canvas in MIN to MAX") |
| `om_lk_generate` | Range | sides mode -1 / 0 / 1 / 2 / 3 | header: -3 outside 0..2 | test written |
| `om_lk_generate` | Conformance | two faults at once | silent | question test-writer-Q3 |
| `om_lk_generate` | Range | choke width 300 / 700 inclusive, any canvas | Design: `DRAFT_CHOKE_W_MIN` 300 to `_MAX` 700; check 5 | test written (inclusive, 0.02 wu slack for the hundredth quantisation); also at canvas 8,000 and 64,000 |
| `om_lk_generate` | Range | bypass ratio 1.5 / 2.4 | Design step 3: way round is 1.5 to 2.4 times the way through; check 3: at least 1.5 | test written (0.002 slack on the ratio; 1 wu slack on the avoid-path length) |
| `om_lk_generate` | Range | fairness `abs(dA-dB) <= 0.10*max` | check 2: `<=` (equal passes) | test written with an independent Dijkstra over the dumped lanes, 1 wu slack |
| `om_lk_generate` | Range | approaches `>= 2` | check 4: at least `DRAFT_APPROACHES_MIN` | test written (`>=`, exactly 2 passes) |
| `om_lk_generate` | Range | vantage bands 1..3; climb lanes 2 distinct | Design step 3, R-113-04 | test written |
| `om_lk_generate` | Range | candidate index 0..4 | Design step 2, `DRAFT_CANDIDATES` 5 | test written |
| `om_lk_generate` | Range | all geometry inside 0..canvas incl. pad/vantage circle | check 6 | test written at canvas 8,000 / 24,000 / 64,000, 3 sides modes, checked on the dump (not only the engine's bit) |
| `om_lk_generate` | Cardinality | exactly 1 objective, 1 + 1 bases, 2 resources, 2 expansions, 1 choke, 1 vantage; 12 seeds x 3 modes | criterion 1, `DRAFT_ASSAULT_*` | test written (36 layouts) |
| `om_lk_generate` | Cardinality | request counts: pad per place, choke per choke, vantage per vantage, route per route lane | Design step 5 | test written; landform requests: every landform on a choke/vantage has one, count not pinned (home-ground landforms have no field to carry them) |
| `om_lk_generate` | Ordering | pad names `base_a`, `base_b`, `objective`, `site_0..site_3` | Design step 5 | test written (set equality; numbering contiguous from 0) |
| `om_lk_generate` | Ordering | resource i of the pair = i-th resource place in `places[]` | spec `--break fairness`: "resource 0 (the first resource place)" | used by the fairness-number comparison |
| `om_lk_generate` | Reference | vantage request `side`: +1 nearer A, -1 nearer B, 0 equal | Design step 5 | test written; the tie (0) is computed on quantised integers, a tie on doubles that quantises unequal is not reachable in 36 layouts |
| `om_lk_generate` | Conformance | district grid holds roles 1..6 | Design step 3 | test written (presence only; row/column to x/y mapping is silent, not tested) |
| `om_lk_generate` | Conformance | piece per place kind | R-112-03 / Design step 5 | objective, resources, chokes, vantages tested; bases and expansions: question test-writer-Q7 |
| `om_lk_generate` | Conformance | sides modes mirror / rotate / separate | R-112-08, Design step 4 | rotate exact, mirror about x or y mid line, separate not all equal; bases and mid-line axis: question test-writer-Q4 |
| `om_lk_generate` | Time | O0 vs O2, run twice | criterion 2, R-112-01 | test written, 36 layouts each (no sleeps) |
| `om_lk_generate` | Cardinality | different seeds give different layouts | Tests: at least 10 of 12 | test written per sides mode (the dump minus its seed line, since the seed line differs by construction) |
| `om_lk_generate` | Range | scale of lengths with canvas | Design: scales by canvas / 24,000, widths excluded | not tested: question test-writer-Q5 |
| `om_lk_run_checks` | all | edited layouts (a lane removed etc.) | Design: "judged on what it now is" | not testable through the wave-1 probe (it has no run_checks mode); wave 2 tests it via `layout_dump --break` / `--check` |
| `om_lk_run_checks` | Existence | NULL ignored | header | not tested (no probe mode; crash-only boundary); noted for wave 2 |
| `om_lk_name` | Range | ids -1, 0..n-1, n for domains 0..5 | header + JSON section strings | test written, all six domains |
| `om_lk_name` | Range | domain -1 or 6 | silent | question test-writer-Q1 |
| `om_lk_draft_*` | Cardinality | count, unique names, `DRAFT_` prefix, 21 named values | Named drafts (+ `DRAFT_AXIS_STEPS` 24 from Determinism) | test written (values in hundredths) |
| `om_lk_draft_*` | Range | index -1 / count | silent | question test-writer-Q2 |
| `csrc/layout_kit*.c` | Conformance | numeric literals other than 0, 1, 2, array sizes | criterion 4 | test written with a detector control; strictness: question test-writer-Q8 |
| `csrc/layout_kit*` | Existence | the four named files exist | criterion 1 files | test written |
| `csrc/layout_kit*` | Reference | no `layout_internal.h`, no `layout_library`, no heap/clock/file calls, libm_lint clean | R-112-06, criterion 4 | test written |
| `render.py map` | Range | image size from canvas / 20 | criterion 8 | test written as >= 400 px square map plus wider (sidebar); place positions prove the 20 wu/px scale; sidebar width and y direction: question test-writer-Q6 |
| `render.py map` | Conformance | place colours: A vs B differ, neutral grey | criterion 8 | test written (compares with the place moved away; grey = channel spread <= 16, my number: Q6) |
| `render.py map` | Conformance | lane width to scale, way_round dashed, chokes, vantages drawn | criterion 8 | test written by variant diffs (width 120 -> 600 wu; kind route vs way_round; list emptied) |
| `render.py map` | Existence | sidebar shows seed, checks, distances, every drafts value (incl. a new key) | criterion 8 | test written (5 edits), and the map area stays unchanged |
| `render.py map` | Existence | missing or malformed input file | silent | question test-writer-Q6 (vi) |
| `render.py sheet` | Cardinality | 12 of 12 present; 11 of 12 present (missing s5) | criterion 9 | test written: 12 distinct cells; missing -> exit 1, image written, only that cell differs |
| `render.py sheet` | Cardinality | 0 present, > 12 present | silent | not tested (a directory with no seeds): noted, same family as Q6 |
| `render.py sheet` | Conformance | a failed check shows `n/6` | criterion 9 | test written: only that tile changes; exit status for it: Q6 (v) |
| `render.py` | Conformance | bad arguments: none, unknown subcommand, 0/1 args to map or sheet, too many | criterion 10 | test written (7 cases): exit 2 and "usage" on stderr |
| `render.py` | Reference | Pillow + stdlib only, no window, `DRAFT_PX_WU = 20` | criteria 8, 10 | static test written (AST) |

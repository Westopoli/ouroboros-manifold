# TEST-AUDIT, shard default, wave 2 (S-247 CLI, leaf-02)

Fresh context. Read in full: brief, BOUNDARIES, spec (amended), leaf-02 brief, questions Q1 to Q5, answers (wave 2 rulings), header, probe, engine graph/summary, wave 1 audits, the umbrella, the seven test files, determinism, helper (571 lines).
Ran (scratchpad `audit2/`, nothing in the repo touched):
- all 675 tests against the test-writer's `layout_dump.c` (literal 40 percent fairness edit): 637 pass, 38 fail = 36 fairness positive controls + `check_on_a_broken_layout[fairness]` + the lint test (artifact: the throwaway dir holds `layout_dump_bugs.c` with `rand()`).
- variant `am.c` = same CLI with the AMENDED fairness edit (append a straight `route` lane, base A node to resource 0 node, width of first route lane): 639 pass, 36 fail, all `test_S_247_fairness_break_is_exactly_the_spec_edit`.
- `am_norenum.c` (amended edit, lane indices not renumbered, Q3 ruling): same 639/36.
- `am_hb.c` (amended edit, vantage `height_bands` printed `2.00`): 636/39, three extra fails in `numbers_are_quantised...`.
- `--check` vs the file's own `checks` for connected/bypass/approaches breaks, 36 layouts, renumbering and not: 0 mismatches.

Counts: red 2, yellow 6, green 12.

## RED

**R1. The fairness edit in the tests is the superseded edit; a CLI that follows the amended spec fails 36 tests.**
Spec criterion 6 (amended 2026-11-05): "`fairness` appends one lane of kind `route` (two points, width the width of the first route lane) from side A's base node straight to resource 0's node ... (amended: moving a prize along its spur shifts both sides' distances equally, test-writer2-Q1)"; answers: "Q1 fairness break: amended in spec criterion 6 ... The two fairness test groups then go green on a correct CLI." Tests still say, helper `apply_break` (layout_kit_cli_helpers.py:280-290): `nx = r["x"] + Decimal("0.4") * (a["x"] - r["x"])` ... `ln["pts"][0] = [nx, ny]`; `edit_problems` (:313-327) special-cases "moved points"; test_layout_kit_fairness.py:4 "the first resource moved 40 percent of the way to side A's base" and :41 "`--break fairness` moves resource 0 ... 40 percent".
Why red: with the literal edit the positive control is unsatisfiable (36 `fairness_false_after_break_true_without` + `check_on_a_broken_layout[fairness]` fail on the throwaway); with the amended edit `fairness_break_is_exactly_the_spec_edit` x36 fails (`lanes differ`, `route_count`-independent). A builder cannot satisfy both groups. Q1 asked for exactly this fix ("the tests need the same edit in `apply_break`") and it was not applied.
Fix (`Test-defect:` commit): in `apply_break` replace the fairness branch with: `r = first resource place; a = base_forward place; w = width of first lane of kind "route"; lay["lanes"].append({"kind": "route", "a": a["node"], "b": r["node"], "width": w, "pts": [[nodes[a.node].x, .y], [nodes[r.node].x, .y]]})`; delete the "moved points" block of `edit_problems` (fairness then compares like the rest, lanes appended last, `refs` False); rewrite the docstrings in test_layout_kit_fairness.py:4 and :41 and the helper docstring. The positive control and `check_on_a_broken_layout[fairness]` need no change.

**R2. Vantage `height_bands` is pinned to a bare integer; the spec does not pin it and the ruling reads the other way.**
Test: `"vantages": {... "height_bands": INTEGER, ...}` (layout_kit_cli_helpers.py:382), used by `test_S_247_numbers_are_quantised_hundredths_with_integer_text`. Spec "Numbers": "coordinates, widths, radii and distances are quantised ... printed `[-]<int>.<two digits>`"; the vantage line lists `height_bands` with no type; answer Q4: "canvas, frac, height_bands print quantised like every number". The test accepts either form for `request.height_bands` (:385 `EITHER`) but not for the vantage's, although the key is the same name in the same JSON.
Why red: variant `am_hb.c` (vantage `height_bands` as `2.00`, an honest reading of the ruling) fails all three sides-mode cases. The header types it int32 (`om_lk_vantage.height_bands`, "1..3"), so a bare integer is probable but not stated.
Fix: `EITHER` for `vantages.height_bands` (same line as the request one), or the Architect writes "vantage height_bands is a bare integer" into the JSON section and the ruling.

## YELLOW

**Y1. The drafts and number-format tests are weaker than the amended spec (mutation survives).**
Spec (amended): "a magnitude above 9,000,000,000,000,000 wu clamps to that value ... so `DRAFT_INF` 1e30 in the `drafts` block prints as `9000000000000000.00`", "Rounding is half away from zero", answer Q4 "canvas, frac, height_bands print quantised like every number". Tests: `if k == "DRAFT_INF": if v <= 0:` (test_layout_kit_cli.py:106-108, docstring :98 still "1e30 does not fit"), and `EITHER` for canvas, frac, request height_bands and every drafts value (helper :336, :373-375). The throwaway prints `DRAFT_INF` as `92233720368547758.07` and the whole suite is green on it; a CLI printing canvas as `24000` also passes. Not over-strict, so not red, but it leaves criterion 5's number rules unproven for the ruled cases.
Fix: assert the raw text of `DRAFT_INF` equals `9000000000000000.00`; use `QUANT` for canvas, frac (choke and request), request height_bands and drafts; one half-away case from the drafts (e.g. a draft whose third decimal is 5) or from a negative coordinate if the engine yields one.

**Y2. "not built" is required of one archetype out of nine.**
Spec: "`--archetype` other than `assault` exits 2 with 'not built'"; answer Q2 "every one except assault exits 2 with 'not built' on stderr". Test: `any("not built" in r.stderr for r in rs)` (test_layout_kit_cli.py:158). A CLI that says "not built" for one name only passes.
Fix: `all(...)`.

**Y3. Usage cases the spec leaves to "usage error" are pinned to exit 2.**
Quotes: `["--seed", "one", ...]`, `["--seed", "1", "--archetype", "assault", "--canvas", "wide"]`, `["--check"]`, `["--seed", "1", "--archetype", "assault", "--break", "nonsense"]` (USAGE, test_layout_kit_cli.py:136-145). Spec criterion 5: "2 on a usage error (stderr names it)"; it names unknown archetype, nothing else; BOUNDARIES marks the break name as "derived". A CLI that reads a non-numeric canvas as 0 and exits 1 (`om_lk_generate` -3) is spec-literal. Likely intent, but unwritten.
Fix: the Architect adds one line to criterion 5 ("a value that is not a number, an unknown option, sides or break name, a missing value or file are usage errors"), or the four cases are dropped.

**Y4. Other count and index fields are pinned to bare integers.**
`INTEGER` for place `node`, nodes `place`, lane `a`/`b`, choke `axis_k` and `lane`, vantage `overlooks`/`climb`, request `axis_k`/`side` (helper :376-385). Spec quantises "coordinates, widths, radii and distances" and types `seed`, `candidate`, `route_count`, `district` as int; the rest are silent. Reasonable, same family as R2 but with no ruling contradicting it, so left yellow.
Fix: state in the JSON section that every index/count is a bare integer, or accept `EITHER`.

**Y5. `--check` on a text-deleted lane leaves dangling lane indices.**
`_edit_approaches` deletes lane 4 of 15; the vantage `climb` lane 14 then points past the end (checked: 36 of 36 layouts). Spec Tests: "`--check` ... exits 1 on a hand-edited JSON (a lane deleted)". A `--check` that validates index ranges and exits 2 would fail `check_reads_the_file_not_the_seed[approaches]` though the spec asks for this very edit.
Fix: say in criterion 7 that index fields are not validated, or delete the last-but-one lane instead (no dangling `climb`); weakest of the yellows.

**Y6. Citation and hook housekeeping.**
`test_S_247_libm_lint_is_clean_with_the_cli_present` cites R-112-06 (the old-library rule); the libm ban is criterion 4. `LAYOUT_DUMP_SRC` (helper `cli_source`) is a test-only redirect not in the spec; harmless unset, but a stale env var would build another file and the umbrella does not honour it. No fix needed beyond a comment.

## GREEN (checked, no action)

1. Goal fidelity: criteria 5 (flags, defaults, exit 0/1/2, `--out`, `--seeds`+`--out-dir`, summary line), 6 (five of six edits exact, all six positive controls with a negative control, judged by the JSON and by a Python Dijkstra), 7 (`--check` six lines, exit codes, file-not-seed edits) all have a test; wave 2 "Tests" list covered one for one.
2. Umbrella alignment: seed 1 separate, six checks true, counts 1/1/1/2/2, >=1 choke and vantage; the CLI tests cover the same ground by `dump(...)`; no contradiction; the umbrella needs the real source (does not honour `LAYOUT_DUMP_SRC`), by design.
3. Non-tautology: output judged against the wave 1 probe (engine called directly, 36 layouts, +-1 hundredth), against a Python oracle, and against the spec's edit; `seed` is compared to the probe's `seed` line (key present), not defaulted.
4. Over-strictness probes passed: rounding tolerance +-1 hundredth, `-0.00` refused only; lane renumbering not required (`am_norenum` green, lane indices ignored via `_strip`); lane removal by compaction (ruling Q3); `--check` canvas from the file (needed for `bounds`, Tests says "agrees with the JSON's own checks"); `candidate`, `route_count` and distances follow the engine (header: `om_lk_run_checks` sets them); drafts names/order from the header; `[0, 1]` vs `[0,1]` not pinned; drafts block layout not pinned.
5. Text layout: two-space indent, one element per line, district rows, one final newline; `drafts`/`fairness`/`checks` layout free.
6. Seeds above 2^32 and canvas ends (8000, 64000) assert exit 0: the spec pins only seeds 1..12, but the engine is fixed and passes, and the CLI has no latitude there.
7. Uses spec numbers only: 300/700, +100, 24000, 8000/64000, 1.5, 0.10, 2 approaches; every figure traced.
8. Determinism: fresh process per run, bytes, `len > 1000` guard; O0 vs O2 over 36 layouts and each break; no sleeps, no clock.
9. Boundary table matches the tests (7999/8000/64000/64001, uint64 trio, 8 usage cases, 1..12 / 3..5 / 7..7, bounds at three canvases).
10. Assertion count 37 (`grep "assert "`: 16+3+2+2+3+3+3+4+1) within the budget of 40.
11. Lint: `libm_lint.py csrc` is clean now (OK), and the test lints the CLI's directory when `LAYOUT_DUMP_SRC` is set.
12. Red for the right reason: without `csrc/tools/layout_dump.c` every module's fixture asserts the file; no test passes by accident.

## Summary table

| id | sev | where |
|---|---|---|
| R1 | red | helper :280-290, :313-327; test_layout_kit_fairness.py:4,:41 literal 40 percent edit vs amended spec |
| R2 | red | helper :382 vantage height_bands INTEGER vs ruling Q4 |
| Y1 | yellow | test_layout_kit_cli.py:98,106; helper :336,:373-375 DRAFT_INF/rounding/quantised unproven |
| Y2 | yellow | test_layout_kit_cli.py:158 `any` "not built" |
| Y3 | yellow | test_layout_kit_cli.py:136-145 unspecified usage cases |
| Y4 | yellow | helper :376-385 other index fields bare integers |
| Y5 | yellow | test_layout_kit_cli.py:_edit_approaches dangling climb index |
| Y6 | yellow | determinism lint citation, `LAYOUT_DUMP_SRC` |

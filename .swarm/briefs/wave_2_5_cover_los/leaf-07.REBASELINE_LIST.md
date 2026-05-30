# Leaf-07 rebaseline scan — candidate tests touching cover-mult removal

Scope: tests whose combat-outcome assertions could shift when `(1.0 - cover)` mult removed from `damage.py` (L5). Read-only enumeration. NO test edits per `feedback_no_test_modification.md` — Westley signs off before any changes.

Methodology: cross-ref simulation/test_*.py for (a) `cover_density` / `cover_polygons` references, (b) `resolve_damage` / FIELD_HP / kill-assertions, (c) TacticalMap fixtures via `test_maps.cover_heavy()` / `large_operational()` / `evacuation()` / `map_generator.generate_map`.

## Tests with combat assertions AND cover-bearing fixtures

None confirmed. Combat-assertion tests (`test_checkpoint_6e.py`, `test_formation_baseline.py`, `test_checkpoint_6k.py`, `test_checkpoint_formation_perf.py`, `test_cover_damage_gate.py`, `test_cover_integration.py`) use `open_field` / `open_field_large` / `chokepoint` (no cover sources) or build hand-rolled maps without `cover_polygons`. Cover-bearing fixture users below.

## Tests using cover-bearing test_maps fixtures — diagnostic only, no assertions to rebaseline

- `simulation/test_checkpoint_6f.py` — imports `cover_heavy`, runs visualization sweeps, NO `assert` statements. Diagnostic; not rebaseline candidate but flag for visual sanity check post-merge.
- `simulation/test_6j_matrix.py` — fn `_build_scenario("cover_strike_10v10")` uses `cover_heavy()`, NO `assert` statements. Diagnostic sweep.
- `simulation/test_checkpoint_6i.py` — uses `large_operational()` (has cover_density sources), NO `assert` statements. Recording / debug harness.

## Tests asserting cover_density gradient values (NOT combat outcomes — out of scope)

These should still pass since `cover_density()` sample API preserved per L3:
- `simulation/test_stage7_checkpoint_e.py::test_stage7_checkpoint_e` — asserts flank_route nodes have `cover_density > 0.05`. Gradient-source presence, unrelated to damage.
- `simulation/test_stage7_checkpoint_g.py::test_stage7_checkpoint_g` — asserts region-state→`cover_density` direction (instability/tension → positive). Region-state code path, unrelated to damage.
- `simulation/test_stage7_checkpoint_i.py` — visualization only, `cov = tm.cover_density(...)` used for pixel render.
- `simulation/test_checkpoint_a.py` — `tmap.cover_density(*pos)` print-only diagnostic.

## Tests using map_generator.generate_map (now emits cover polygons per L3) — NO combat assertions

- `simulation/test_stage7_checkpoint_i.py` — generation correctness, no combat.
- `simulation/test_stage7_5_checkpoint_i.py` — ownership baseline math, no combat.
- `simulation/test_stage7_checkpoint_m.py` — debrief data, no combat.

## Conclusion

Rebaseline list: **EMPTY** for combat-outcome assertions. No `simulation/test_*.py` file asserts a damage/kill outcome that depends on the now-removed `(1.0 - cover)` multiplier. Diagnostic / visualization tests using cover-bearing fixtures (6f, 6j_matrix, 6i) have no assertions and are not gates.

Risk areas for Westley to spot-check post-merge (not required test rebaseline, but worth visual confirmation):
- Diagnostic sweep `test_checkpoint_6f.py` output on `cover_heavy` — visual k/d ratios should swing since cover no longer reduces damage.
- `test_6j_matrix.py::cover_strike_10v10` — printed Strike vs Line outcomes will shift.

Under 20 files — no parent triage needed.

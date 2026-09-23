# Test defects fixed (2026-09-22)

Source: `docs/northstar/proving_ground/evidence/push_2026-09-22/freeze_F1b.md`,
"Freeze control" (17 forbidden -> corrections landed -> 4 remaining) and
"Test defects for the design lane" sections. Rule applied: CLAUDE.md test-edit
rule -- a repair may not weaken any assertion, every original assertion
survives, the test stays red against the STUB for the right reason (an
assertion or a STUB result, never a Python error).

Verification method: for each file, `git stash` isolated the edit to get the
committed (before) version back on disk, pytest ran with `--junit-xml`,
failures were classified by exception name (or `AssertionError` when the
junit failure has no named exception, i.e. a bare `assert`); `git stash pop`
restored the fix, same run repeated. Assertion counts: `grep -c "assert "
<file>` via `git show HEAD:<file>` (before) vs the working tree (after).

## Class 1: missing `import ctypes` / `import math` (16 occurrences, 7 files)

Fix: added the missing import line only, before `import pytest`. Nothing else
changed.

| File | Import added | Assertions before/after | Failures before | Failures after |
|---|---|---|---|---|
| `tests/csim/test_E10_S076_the_clock.py` | `ctypes` | 8 / 8 | NameError 2, AssertionError 1 | AssertionError 3 |
| `tests/csim/test_E13_S095_a_force_moves_as_one.py` | `ctypes` | 28 / 28 | NameError 6, AssertionError 1 | AssertionError 7 |
| `tests/csim/test_E13_S096_four_commands.py` | `ctypes` | 24 / 24 | NameError 1, AssertionError 6 | AssertionError 7 |
| `tests/csim/test_E13_S097_around_not_through.py` | `math` (+ loop-bound fix, see below) | 30 / 30 | NameError 3, AssertionError 7 | AssertionError 9, PASSED 1 |
| `tests/csim/test_E13_S099_speed_is_position.py` | `math` | 5 / 5 | NameError 2 | AssertionError 2 |
| `tests/csim/test_E13_S100_facing.py` | `math` | 7 / 7 | NameError 1, AssertionError 1, PASSED 1 | AssertionError 2, PASSED 1 |
| `tests/csim/test_E13_S101_movement_that_reads.py` | `ctypes` and `math` (test uses both) | 7 / 7 | NameError 1, PASSED 1 | AssertionError 1, PASSED 1 |

16 NameError occurrences before (2+6+1+3+2+1+1), 0 after. Assertion counts
identical before/after in every file (grep -c "assert " matches).

Dependency fix, not a separate class (Scope discipline: the asked-for import
fix can't work without it): `test_E13_S097_around_not_through.py`,
`test_R_097_04_it_keeps_that_heading_for` (lines 111-124) had `while
dist_covered < 55.0: lib.om_world_step(w); ...; dist_covered = math.hypot(...)`.
Against the committed (pre-fix) file the missing `math` import kills the test
on the first loop iteration (fast NameError, confirmed: 0.15s for the whole
9-file "before" run). Once `import math` is added, that NameError no longer
fires and the STUB's `om_world_step` never advances the unit, so
`dist_covered` never reaches 55.0 and the `while` spins forever (this is
exactly what freeze_F1b.md flagged: "the scratch copy hung >300s"). Fixed by
bounding it to `for _ in range(100): if dist_covered >= 55.0: break; <same
body>` -- identical check-then-body order as the original `while`, same
assertion, same cadence, just capped. Cap picked from this epic's own numbers
(R-099-02, same file family): a Raider covers 55 wu in ~8 real ticks at 7.5
wu/tick, so 100 ticks is >10x headroom for a working sim and still finite
against the STUB. Confirmed after: file runs in 0.34s (whole 9-file suite),
no hang; the test now passes vacuously against the STUB (`curr_heading ==
deflected_heading` both come from the STUB's constant `om_unit_get_facing`),
same pre-existing vacuous-STUB-pass category as the other ~66-70 documented
in freeze_F1b.md, not a new defect introduced by this repair. Assertion count
for this file unaffected (30/30; the loop's `assert` line is untouched, only
wrapped in a bounded loop instead of an unbounded one).

## Class 2: conftest helper called with wrong arity (4 sites, 2 files)

Helper signatures read from `tests/csim/conftest.py`:
- `read_drift(lib, w, idx)` (line 376) -> `(rc, OmDriftRow)`, a struct of
  drift *legs* (military_decay, d_military, ...), not a field's stored value.
- `set_region(lib, w, idx, *, tier=..., military=..., ...)` (line 366) ->
  sets fields by keyword, returns None (asserts rc==0 internally).

`tests/csim/test_E10_S078_a_battle_becomes_history.py` (3 sites: `R_078_02`,
`R_078_03`, `R_078_07`) called `read_drift(lib, w, idx, OMField.MILITARY)` (4
positional args -- `read_drift` takes 3) and compared the result directly to
a scalar (`== pytest.approx(32.0, ...)`), which only makes sense against a
field's stored value, not a drift-leg struct. freeze_F1b.md names the
intended symbol: `om_region_field(w, idx, field) -> c_double`, already bound
in conftest (`csrc/ouroboros_sim.h:136`). Fix: replaced all 7 call sites
across the 3 affected tests with `lib.om_region_field(w, idx, OMField.X)`.
Assertions: 17 / 17, unchanged.

Left untouched, out of scope (same bug, currently masked by an earlier
assertion so it never reaches the TypeError and isn't in freeze_F1b.md's
forbidden list): `test_R_078_05_band_refusal_no_force_deployed`, line 102,
still calls `read_drift(lib, w, 0, OMField.TENSION)`. It fails first at line
97 (`assert band == OMMissionBand.REFUSAL`, STUB returns 0) so the broken
read_drift call is latent, exactly like `test_E12_S092`'s duplicate below.

`tests/csim/test_E12_S093_fog_is_for_the_player_not_the_engine.py` (1 site,
`R_093_03`): called `set_region(w, 1, OMField.MILITARY, 0.42)` (missing
`lib`, and `OMField.MILITARY, 0.42` positional where the signature takes
keyword-only field args). Intent is clear from the surrounding code (line
102 reads `om_strategic_agent_read_region_field(w, 0, 1, OMField.MILITARY)`
and expects 0.42): fixed to `set_region(lib, w, 1, military=0.42)`.
Assertions: 9 / 9, unchanged.

Left untouched, out of scope (latent duplicate, not in freeze_F1b.md's
forbidden list): `test_E12_S092_recon_then_fog.py:121`,
`set_region(w2, 0, OMField.MILITARY, 0.95)`, fails first at line 117 on the
STUB `om_recon_get_terrain_visibility_ratio`.

| File | Assertions before/after | Failures before | Failures after |
|---|---|---|---|
| `tests/csim/test_E10_S078_a_battle_becomes_history.py` | 17 / 17 | AssertionError 4, TypeError 3 | AssertionError 7 |
| `tests/csim/test_E12_S093_fog_is_for_the_player_not_the_engine.py` | 9 / 9 | PASSED 1, AssertionError 1, TypeError 1 | PASSED 1, AssertionError 2 |

## Class 3: `om_tick_read_ability_events` records wrapper

No edit. `tests/csim/conftest.py:2081` already binds `wrapper = "records"`
(`_wrap_records`, line 1266) for this symbol, landed in the freeze
corrections. `len(lib.om_tick_read_ability_events(w))` in
`test_E11_S086_one_ability_each.py::test_R_086_09` and
`test_E11_S088_reading_units_on_screen.py::test_R_088_02` now calls the
wrapped adapter, which returns a Python list -- `len()` and indexing both
work as written. Confirmed neither test appears in the class-4 sweep below.

## Class 4: full sweep, `test_E0[6-9]*.py` / `test_E1*.py`

```
scripts/specfactory/red_check.py --forbid TypeError,ArgumentError,AttributeError,NameError \
  --placeholder-list docs/northstar/spec_factory/placeholder_controls.txt \
  tests/csim/test_E0[6-9]*.py tests/csim/test_E1*.py
```
Result: `passed=70 failed=331 errors=0 skipped=0 crashes=0
placeholders_excluded=0 forbidden=0`.

**Table-defect list: none.** Zero TypeError/AttributeError/NameError remain
in this glob after classes 1-3; every failure is `AssertionError` (red for
the right reason) or a pre-existing vacuous STUB pass (documented in
freeze_F1b.md, not part of this repair's scope). `passed` rose from the
freeze doc's 69 to 70 -- the one new pass is
`test_E13_S097_around_not_through.py::test_R_097_04`, the vacuous STUB pass
that the class-1 loop-bound dependency fix (above) exposed; it is the same
class as the other ~66-69 pre-existing vacuous passes, not a new one this
repair introduced.

`scripts/specfactory/fixture_defects.py` does not apply to any of the 9
edited files: its `sweep()` (the only entry point; `__main__` takes no CLI
argument) is hardcoded to `tests/csim/controls/test_control_e05_*.py` and
`tests/csim/test_E05_*.py` only. All 9 edited files are E-10/E-12/E-13.

## Files touched

- `tests/csim/test_E10_S076_the_clock.py`
- `tests/csim/test_E10_S078_a_battle_becomes_history.py`
- `tests/csim/test_E12_S093_fog_is_for_the_player_not_the_engine.py`
- `tests/csim/test_E13_S095_a_force_moves_as_one.py`
- `tests/csim/test_E13_S096_four_commands.py`
- `tests/csim/test_E13_S097_around_not_through.py`
- `tests/csim/test_E13_S099_speed_is_position.py`
- `tests/csim/test_E13_S100_facing.py`
- `tests/csim/test_E13_S101_movement_that_reads.py`

No file outside `tests/csim/` touched. No assertion added, removed, or
changed in value; only imports, one bug-for-bug call-site correction
(`read_drift`/`set_region` -> the function/arguments the surrounding lines
already clearly intend), and one loop-bound cap needed to keep the file
runnable at all.

## R-083-03 aura test: category multiplier confound (M2/B10-2 finding)

File: `tests/csim/test_E11_S083_stats_traits_ability.py::test_R_083_03_that_unit_takes_10_percent`.

Bug: enemy attacker spawned RAIDER (Strike). Target VANGUARD (Line). R-081-01
+ ALG-60 say Strike->Line carries a 0.75 category multiplier, unconditional,
same file family (`test_E11_S081_three_categories_a_soft_triangle.py`)
confirms 0.75 in the M matrix. Old fixture ignored it, asserted flat
`base_hit * 0.90` (45.0) and `base_hit` (50.0) -- only true if multiplier is
1.0. Confound: aura-reduction rule tangled with the category-triangle rule.

Fix: changed enemy attacker from RAIDER to VANGUARD (same Line category as
both friendly targets). Line->Line multiplier is 1.0, so aura isolation
holds and old/new numbers match:

| Value | Old (RAIDER attacker, wrong) | New (VANGUARD attacker, isolated) |
|---|---|---|
| friendly_in dmg (10% reduced) | 45.0 (asserted, should've been 33.75 with the confound) | 45.0 (correct, multiplier 1.0 x 0.90) |
| friendly_out dmg (no reduction) | 50.0 (asserted, should've been 37.5 with the confound) | 50.0 (correct, multiplier 1.0) |

Rule id, docstring, 10% assertion, and friendly control unchanged. One line
changed: enemy unit type RAIDER -> VANGUARD.

Verification:
1. Red at stub, main (`b4d6391`): `pytest tests/csim/test_E11_S083_stats_traits_ability.py::test_R_083_03_that_unit_takes_10_percent -q` fails at line 86, `assert lib.om_unit_hp(w, friendly_in) == pytest.approx(400.075, ...)`, obtained 0.0 (unit.c stub).
2. Green, `origin/push/B10-2` (worktree `/tmp/b10fix`, detached `10ce7e5`): fixed test file copied over, built `libouroboros.so`, ran whole S083 file: `3 passed in 0.03s` (file has 3 tests total, not 13 -- brief's "13/13" expectation didn't match file size; all 3 pass, full green).
3. Rest of E-11 unaffected on main: `pytest tests/csim/ -k E11 -q` before and after this edit both give `52 failed, 5 passed` (only fixture content in one already-failing test changed, stub result identical).

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

## R-024-05: missing `generate`/`region_neighbors` import (B4 leaf finding)

File: `tests/csim/test_E03_S024_politics_redraws_the_routes.py::test_R_024_05_no_edge_type_changed`.

Bug: file's `from conftest import (...)` block omitted `generate` and
`region_neighbors`, both used only by this one test (lines 168, 174) --
every other E-03 file (`test_E03_S021_*`, `test_E03_S023_*`,
`test_E03_S025_*`) imports both already. `NameError: name 'generate' is not
defined` at line 168 on main (`54b5abe`). Fix: added `generate` and
`region_neighbors` to the import list, alphabetical order preserved. No
assertion touched.

Verification:
1. Before (`git stash` isolates the fix): `pytest
   tests/csim/test_E03_S024_politics_redraws_the_routes.py -q` ->
   `NameError: name 'generate' is not defined` at line 168, 3 failed (R-024-01,
   -02, -05), 2 passed (R-024-03, -04).
2. After (fix applied): same run -> 3 failed, 2 passed, same test ids.
   R-024-05 no longer raises `NameError`; it now fails at line 170
   (`rc = generate(lib, w)`) with `AttributeError:
   .../libouroboros.so: undefined symbol: om_gen_set_extra_edge_ratio`,
   raised inside `conftest.py`'s `_bind_e03`/`generate` helper, not in the
   test body. R-024-01 and R-024-02 fail the same way before and after (both
   already red on main, unrelated to this import: R-024-02 hits a real
   assertion, `expected BORDER after betrayal between (0, 2), got 2`; R-024-01
   hits the same missing-symbol `AttributeError` as R-024-05, since it also
   uses `set_edge`/generation-adjacent bindings loaded by `_bind_e03`).
   R-024-03 and R-024-04 pass, unchanged.
3. Root cause of the `AttributeError`, confirmed out of scope for this fix:
   `csrc/ouroboros_sim.h:700` declares `om_gen_set_extra_edge_ratio`, but no
   `.c` file implements it -- `csrc/worldgen.c` on `HEAD` (`1eeb0a5`, "freeze
   generated from signatures.toml") is an 111-line stub (3 functions), while
   the full implementation with this setter shipped in `b8c9566` ("feat(B4):
   E-03 world generation") is not present in `HEAD`'s `worldgen.c`. Confirmed
   pre-existing and not caused by this import fix: `test_E03_S021_*.py`,
   `test_E03_S022_*.py`, `test_E03_S025_*.py` (already-correct imports, no
   edit) fail with the identical `undefined symbol: om_gen_set_extra_edge_ratio`
   `AttributeError` when run on unmodified `HEAD`. Not fixed here --
   `worldgen.c` is out of scope for an import-only repair and is a protected
   engine file.

## S-043: three fixtures never reach the branch they claim to test (B5 leaf finding)

File: `tests/csim/test_E06_S043_peace_grows_out_of_quiet.py`. All three
claims checked against `docs/bible/epics/E-06-diplomacy-and-technology.md`
(S-043 rules R-043-01/-04/-06), `docs/bible/algorithms.md` ALG-09 (stability)
and ALG-38/ALG-39 (non-aggression counter, peace formation), and
`csrc/om_constants.h` (`OM_ARCHETYPE_PEACE_DISPOSITION_*`). All three held up
against the bible; no claim was rejected.

**Red at stub** (main, stub `csrc/diplomacy.c` returns 0/NEUTRAL for
everything): 6 of 7 tests in the file fail before the fix, same 6 after
(`test_R_043_02` is the only pre-existing pass — a static counter check that
never touches diplomacy.c). First failing line, before fix:

| Test | Line | Failure |
|---|---|---|
| `test_R_043_01_their_non_aggression_counter_increments` | 52 | `assert lib.om_faction_stance_counter(w, 0, 1) == 1` — `AssertionError: assert 0 == 1` (stub never increments) |
| `test_R_043_04_p_min_1_0_5` | 147 | `assert lib.om_faction_stance(w_success, 0, 1) == OMStance.COOPERATIVE` — `AssertionError: assert 1 == 2` (stub stays NEUTRAL) |
| `test_R_043_06_pair_stays_neutral_counter_resets` | 214 | `assert lib.om_faction_stance_counter(w, 0, 1) == 80` — `AssertionError: assert 0 == 80` (stub setter is a no-op) |

Same 6/7 fail after the fix, same first failing lines and reasons — the fix
only changes fixture numbers, not what the stub does.

### 1. `test_R_043_01`: budget rejects the injected attack

Claim: fixture sets faction 0 `budget=0.0` then injects an attack with
`commit=10.0` via `inject_intent`, which asserts `om_intent_inject`'s return
code is 0. `csrc/resolve.c:80-84`: `if (commit > w->faction_budget[faction_id])
return -1;` — confirmed, this is unconditional, no bible rule exempts a
forced/injected intent from the budget check. Verified true: the injection
itself raises `AssertionError: om_intent_inject failed for faction 0: rc=-1`
before the "attack resets the counter" step is ever reached.

Fix: `set_faction(lib, w, 0, OMArchetype.DEFAULT, budget=20.0, tech=0.0)` (was
`budget=0.0`), giving headroom over the `commit=10.0` attack. Faction 1's
budget is untouched (0.0; it's the defender, not the injector).

Second, related defect found while turning this fix green (not in the
original three claims, same fixture): with the injection now succeeding, the
counter still didn't reset (`assert 3 == 0` on tick 3) — `om_step_resolve`
(3f, the function that turns a decision into a `w->attacks[]` record, which
`om__pair_attacked_this_tick` in `csrc/diplomacy.c:323-330` reads) is gated
on `OM_FEAT_FACTIONS` (`csrc/sim.c:228`), and this test module's default
feature set is `["DIPLOMACY", "TECHNOLOGY"]` only
(`docs/northstar/spec_factory/mvp_features.toml` E-06 row) — `FACTIONS` was
never on, so the injected attack decision was preserved in `w->decisions[]`
(confirmed live, `csrc/agent.c:248-267`'s injected-decision preservation) but
never resolved into `w->attacks[]`, so the counter-reset check never saw it
and just incremented instead. Fix: added
`lib.om_world_set_feature(w, OMFeature.FACTIONS, 1)` alongside the existing
`DIPLOMACY` feature flag. Assertions unchanged.

### 2. `test_R_043_04`: stability comment doesn't match ALG-09 on the fixture's own fields

Claim: fixture comment assumes stability 50.0 for `tension=42.86` (mil 50,
pop 50), but ALG-09 (`s = m*0.4 + (100-t)*0.35 + p*0.25`) gives `50*0.4 +
(100-42.86)*0.35 + 50*0.25 = 20 + 20.0 + 12.5 = 52.5`, not 50.0. Confirmed by
hand and against `csrc/diplomacy.c`'s formula. With `|avg_e_A - avg_e_B| =
|60-40| = 20` and dispositions 2.0 (Fortifier) / 1.5 (Player) per ALG-39 /
`OM_ARCHETYPE_PEACE_DISPOSITION_FORTIFIER` / `_PLAYER_CIVILIZATION`: real `p =
clamp(0.5 * 0.8 * 0.525 * 2.0 * 1.5, 0, 1) = 0.63`, not the intended 0.60 —
both forced draws (0.59, 0.61) land below 0.63, so the intended failure case
(draw 0.61 >= p) never fails.

Fix: changed `tension=42.86` to `tension=50.0` in both regions of both
sub-cases (`w_success`, `w_fail`). ALG-09 with mil=50, tension=50.0, pop=50:
`s = 20 + (100-50)*0.35 + 12.5 = 50.0` exactly, `stab/100 = 0.5`, so `p =
0.5 * 0.8 * 0.5 * 2.0 * 1.5 = 0.60` exactly, matching the rule's own worked
number. Draw 0.59 (< 0.60) still succeeds, draw 0.61 (>= 0.60) still fails —
same two draws, same two assertions, now testing the branch they claim to.

### 3. `test_R_043_06`: two Fortifiers give p = 1.0, failure branch unreachable

Claim: two Fortifiers (disposition 2.0 each) with equal economies (`|diff| =
0`) and stability 67.5 (mil 50, tension 0, pop 50: `s = 20 + 35 + 12.5 =
67.5`) give `p = clamp(0.5 * 1 * 0.675 * 2.0 * 2.0, 0, 1) = clamp(1.35, 0, 1)
= 1.0`. Confirmed by hand against ALG-39. With `p = 1.0` and draws in `[0,
1)`, no draw can be `>= p`, so the forced failing draw (0.99) always lands
in the success branch instead — the failure branch this test claims to
prove is unreachable.

Fix: changed faction 1's archetype from `FORTIFIER` (disp 2.0) to
`OPPORTUNIST` (disp 1.0), and `tension=0.0` to `tension=50.0` in both
regions (mil 50, pop 50 unchanged). ALG-09: `s = 20 + (100-50)*0.35 + 12.5 =
50.0`, `stab/100 = 0.5`. `p = clamp(0.5 * 1 * 0.5 * 2.0 * 1.0, 0, 1) = 0.5`.
Forced draw 0.99 (>= 0.5) now lands in the failure branch as intended; the
existing round-trip check (`stance_counter == 80` immediately after the
setter, before the draw) and both post-failure assertions
(`OMStance.NEUTRAL`, `stance_counter == 0`) are unchanged.

**Green on the leaf** (`git fetch origin push/B5`, worktree at detached
`999b640`, this file copied over verbatim): `test_E06_S043_peace_grows_out_of_quiet.py`
— **7 passed** (was 6 failed / 1 passed before the fix, on the same leaf
commit, same file pre-fix). The other six E-06 files on the same leaf,
unchanged by this commit:

| File | Result |
|---|---|
| `test_E06_S042_three_ways_to_feel_about_a_neighbor.py` | 5 passed, 1 failed (`test_R_042_05_their_stance_hostile_if_their`) |
| `test_E06_S044_peace_is_never_safe.py` | 7 passed |
| `test_E06_S045_a_faction_s_technology_is_one_number.py` | 6 passed, 3 failed (`test_R_045_05`, `test_R_045_07`, `test_R_045_09`) |
| `test_E06_S046_archetypes_spend_tech_differently.py` | 4 passed, 1 failed (`test_R_046_04_effective_attack_multiplied_by_it`) |
| `test_E06_S047_friends_share_knowledge.py` | 4 passed |
| `test_E06_S048_three_tiers_of_technology.py` | 0 passed, 4 failed (all) |

None of these six files were touched by this commit; their failures are
pre-existing on the leaf and out of scope for this brief (S-043 fixtures
only).

## R-032-03 / R-037-07: test-defect fixes under the test-fix gate

Both classified `test-defect` by the core doer with evidence; fixed under
the test-fix gate (`assertions_preserved`, `red_at_stub` not applicable --
E-05 is built, so "before/after on main's current tree" substitutes --
`two_agent_confound` n/a, single file each).

### `test_E05_S032_every_faction_is_a_person.py::test_R_032_03_it_uses_attack_weight_0`

Bug: `om_faction_candidates` reads live region state on every call, not a
step-3d snapshot (DECISIONS.md R8a, same shape). The fixture read candidates
*after* `om_world_step`. In that step the player's own decision (colonize
region 3, `colonize_score` 0.342 > `attack_score` 0.2775, both per the
test's own commented math) resolves in 3f and region 3 becomes owned by the
player, so a post-step candidate read for region 1's ATTACK candidate
computes `position` from only one remaining non-self neighbor (region 2,
score 0.44) instead of the mean over two (region 2 at 0.44, region 3 at the
unowned-neighbor constant 0.15) -- `mean(0.44, 0.15) = 0.295` collapses to
`0.44`.

Fix: moved the `read_candidates` call (and the `cand_1`/`cand_3` assertions
that depend on it) to *before* `force_draws`/`om_world_step`, rewrote the
inline comment to say why. Step 3d computes this same faction's decision
scores from this identical pre-resolution region state (the resolution that
mutates region 3 happens after, in 3f), so `read_decisions` after the step
still yields the unchanged `attack_score`/`colonize_score` (0.2775, 0.342 --
both assertions untouched). No assertion value changed; the `0.295` and
`0.74425` assertions are preserved verbatim, only their read is moved
earlier in the same test body.

Derivation of the kept 0.295 (unchanged from the original fixture):
`position = mean( (region2: 40*0.60+50*0.40)/100, (region3, unowned: 0.15) ) = mean(0.44, 0.15) = 0.295`.

### `test_E05_S037_battles_have_a_shape.py::test_R_037_07_attacker_s_committed_budget_spent`

Bug: fixture asserted final attacker budget 9.0 on the premise that the
same-tick breakthrough (crushing region 1's military to 0 in step 3c) causes
the Conqueror's step-3d decision loop to immediately re-declare a second
telegraph against the same, now-defenseless target in the same tick (spending
a further 21.0 of the remaining 30.0). That premise is the interim reading
from DECISIONS.md's Seventh round (R8e/R8f investigation), superseded by
Westley's final C3 ruling in the same round: "at most one resolved attack per
attacker-target pair [per tick]... step 3d does not re-declare against a
target whose attack this faction already resolved this tick" (a follow-up
against the same target waits for the next tick). The comment in the fixture
narrated the superseded interim reading, not the final rule.

Fix: recomputed the expected value under the final rule and rewrote the
stale comment. With no same-tick re-declaration, the only spend this tick is
the one already-proven committed budget (`att_tele.budget_spent == 70.0`,
untouched assertion): `100.0 - 70.0 = 30.0`. Region 0's economy is pinned at
the maintenance baseline (8.0) throughout, so zero passive ALG-17 budget
growth applies in any of the four ticks -- 30.0 is exact, not rounded.
Assertion recomputed: `9.0` -> `30.0`. The "committed budget is spent in
full" assertion two lines above (`att_tele.budget_spent == pytest.approx(70.0, ...)`)
is untouched.

### Verification (both tests)

1. Before, main (`a742857`): via a throwaway detached worktree
   (`git worktree add --detach /tmp/e05t HEAD`, `git stash` forbidden) both
   fail exactly as on the live tree --
   `test_R_032_03_it_uses_attack_weight_0`: `assert 0.44 == 0.295 +/- 1e-06`
   at the `cand_1.position` line; `test_R_037_07_...`: `assert 30.0 == 9.0
   +/- 1e-06` at the final `om_faction_budget` line. Confirmed identical on
   the live main tree before editing.
2. After: copied both edited files into the same worktree, reran --
   `tests/csim/test_E05_S032_every_faction_is_a_person.py
   tests/csim/test_E05_S037_battles_have_a_shape.py`: `12 passed` (4 + 8, the
   full contents of both files). `rm -rf /tmp/e05t && git worktree prune`.
3. Rest of both files unchanged: `test_R_032_01`, `test_R_032_02`,
   `test_R_032_04` (S032) and the other seven S037 tests
   (`test_R_037_01`..`test_R_037_06`, `test_R_037_08`) pass before and after
   in every run above -- same 4/4 and 8/8 split, no new failure and no
   assertion in any of those tests touched.

Files touched: `tests/csim/test_E05_S032_every_faction_is_a_person.py`,
`tests/csim/test_E05_S037_battles_have_a_shape.py`. No file outside
`tests/csim/` touched.

## R-044-07: expected commit follows budget growth before betrayal (B5 leaf finding)

Classified `test-defect` (fixture's own numbers never reach the value the
rule produces once an upstream core fix landed). Fixed under the test-fix
gate: `assertions_preserved` (the "commits the entire budget" assertion
stays, only the expected value changes to match what that budget is at fire
time), `red_at_stub` (confirmed below), `two_agent_confound` n/a (one file).

### `test_E06_S044_peace_is_never_safe.py::test_R_044_07_q_045_01_decides_commit`

Bug: core fix `d61bd52` (tech multipliers start at the formula value, 1.0 at
tech 0 instead of an uninitialized 0.0) changed `om_faction_step_budget`'s
`delta *= w->faction_tech_economy[f]` term from a no-op (0.0 multiplier) to
its intended value. The fixture's faction 0 (conqueror, budget 42.5, tech
0.0) owns region 0 (economy 50.0). Tick sequence step 3b (ALG-17, budget
accumulation) runs before step 3.5 (ALG-40, betrayal) on the same tick:
`Δbudget = (economy 50.0 - REGION_MAINTENANCE_COST 8.0) * BUDGET_GROWTH_RATE
0.025 * tech_economy 1.0 = 1.05` (`OM_BUDGET_GROWTH_RATE` and
`OM_REGION_MAINTENANCE_COST` in `csrc/om_constants.h`; `faction_tech_economy`
at tech 0.0 is `1.0 + (0/100) * axis = 1.0` per ALG-26, `csrc/faction.c:46`).
Budget at betrayal fire time is `42.5 + 1.05 = 43.55`, not the fixture's
pinned `42.5`. Confirmed the accumulation order and formula directly against
`csrc/faction.c::om_faction_step_budget` (`delta += (economy - 8.0) * 0.025`
per owned region, then `delta *= faction_tech_economy[f]`) rather than
inferring it from the docs alone.

Not a rule-text conflict: R-044-07 (docs/bible/epics/E-06-diplomacy-and-technology.md)
and ALG-40 (docs/bible/algorithms.md) both say the betrayer commits its
entire budget at fire time; Q-045-01 (docs/northstar/ambiguity_register.md,
closed 2026-09-16) settled the commit/mode question as "full budget
committed, at surprise efficiency" -- unrelated to this fixture's bug, which
is purely that "entire budget" was pinned to the pre-tick value instead of
the value after step 3b's legitimate growth.

Fix: `assert betrayal_attack[0].commit == pytest.approx(42.5, ...)` ->
`pytest.approx(43.55, ...)`, with the derivation above added as a comment.
The "commits the entire budget" assertion and the rule id are unchanged.

### Verification

1. Red at stub, main (`3dd2d8a`): `test_R_044_07_q_045_01_decides_commit`
   fails at `assert len(betrayal_attack) == 1` (`assert 0 == 1`) --
   `diplomacy.c` is the stub on main, no betrayal ever fires. Same failure,
   same line, for all 7 tests in the file (the whole file is red on main).
2. Green on `origin/push/B5` (`c734601`, built diplomacy.c): copied the
   edited file into a throwaway detached worktree (`git worktree add
   --detach /tmp/b5r origin/push/B5`, `make libouroboros.so`), ran
   `tests/csim/test_E06_S044_peace_is_never_safe.py`: `7 passed`.
   `rm -rf /tmp/b5r && git worktree prune`.
3. Rest of the file unchanged: `test_R_044_01` through `test_R_044_06` fail
   identically before and after (same stub-driven failure on main, same
   pass on push/B5) -- no assertion in any other test touched.

Files touched: `tests/csim/test_E06_S044_peace_is_never_safe.py`. No file
outside `tests/csim/` touched.

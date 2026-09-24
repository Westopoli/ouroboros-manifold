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

## R-052-01 and R-052-02: E-07 S-052 no-plot-armor sweep reds

Both `test-defect`. No csrc file touched, no assertion touched. Fixed under
test-fix gate: `assertions_preserved` yes both, `red_at_stub` n/a (no core
edit, main csrc untouched before/after so `E-02`..`E-08` failing-id sets and
`checksum_trace.py` output are byte-identical by construction), `two_agent_confound`
n/a (one file).

### `test_R_052_01_it_has_zero_regions_its`

Scorecard said "assert budget == 0.0, got 1.05." Repro (`/tmp` scratch ctypes
script, deleted after): tick order 3b (`ALG-17` budget accrual) runs before
3f (`ALG-19`..`ALG-24` intent resolve) same tick, per
`docs/bible/algorithms.md` tick sequence and `csrc/sim.c:232-260` (matches
byte for byte, no `OM_BUG_*` injection flag exists for this order — checked
`csrc/ouroboros_sim.h` bug enum, none named budget/conquest order). Fixture
region 0 econ 50.0: tick1 accrues `Δbudget = (50-8)*0.025 = 1.05` at 3b
*before* 3f's conquest fires same tick and takes the region. Tick2 accrues 0
(zero owned regions) but stock stays 1.05 forever. Rule text ("budget still
accumulates as 0") is about the *increment* going to 0 once regions hit 0 —
fixture's own econ=50.0 makes that increment nonzero on the very tick of
loss, so the strict `== 0.0` assert can never land on the branch it claims
to test. Not core: order matches docs, matches the injected-fault catalog
(no such fault modeled), moving 3b after 3f would change what budget agents
see at 3d (decide) system-wide — way past a targeted S-052 fix, blows the
byte-identical requirement.

Fix: region 0 economy `50.0` -> `8.0` (== `REGION_MAINTENANCE_COST`, so
`Δbudget = (8-8)*0.025 = 0` regardless of same-tick ownership timing).
Confirmed via scratch repro: econ=50.0 -> budget 1.05/1.05 (tick1/tick2);
econ=8.0 -> budget 0.0/0.0, `om_player_faction_collapsed == 1` both cases.
Conquest outcome (military-based, econ-independent) unaffected: owner=1,
territory0=0 same both cases.

### `test_R_052_02_no_rule_anywhere_checks_whether`

Scorecard said "assert damage_player == damage_npc, got 8.0 vs 8.02."
Repro: each attack (commit 30, surprise, target military 10) nets
`effective_attack=15, effective_defense=11, net=4.0` (contested band,
`d_military=-2.0` -> military 8.0), never crosses `CONQUEST_THRESHOLD=5.0`,
so `ALG-22`'s conquest-unrest draw (`csrc/resolve.c` `om_step_resolve`,
`u_draw = om_rng_draw(w)` after the conquest branch) never fires — only ONE
`om_rng_draw` call happens per attack (the net-stochastic draw), not two.
Fixture pushed `force_draws(lib, w, [1.0, 0.99])` before *each* attack.
`om_rng_force` is FIFO-append (`csrc/faction.c:233-241`), not
replace-on-push. First attack consumes only the `1.0` (net draw); the `0.99`
sits unconsumed in the queue (`om_rng_forced_remaining` confirmed: 1
remaining after step 1). Second attack's `force_draws` call appends its own
`[1.0, 0.99]` onto that leftover, so the queue reads `[0.99(stale), 1.0,
0.99]` FIFO — second attack's net draw pulls the *stale* 0.99 instead of the
intended 1.0: `net = 4*0.99 = 3.96`, `d_military=-1.98` -> military 8.02.
Exactly the scorecard's 8.0-vs-8.02. This is the fixture, not the sim: FIFO
append-not-replace is `om_rng_force`'s documented contract and every other
E-05/E-07 test using it relies on that same contract; the bug is this
fixture pushing more draws per step than the scenario consumes.

Fix: `force_draws(lib, w, [1.0, 0.99])` -> `force_draws(lib, w, [1.0])` at
both call sites (only the draw actually consumed). Confirmed via scratch
repro with `om_rng_forced_remaining()` printed each side: single-draw run
shows 0 remaining after each step, `damage_player == damage_npc == 8.0` both
attacks.

### Verification (both tests)

1. Before: main tree as-is (no csrc diff exists or was made — see status
   below), both fail exactly per scorecard (`test_R_052_01`: `assert
   1.05 == 0.0 +/- 1e-06`; `test_R_052_02`: `assert 8.0 ==
   8.02 +/- 1e-06`). No throwaway worktree needed for a before/after csrc
   diff since csrc is untouched by this fix (`git status --short csrc/`
   empty).
2. After: `pytest -q tests/csim/test_E07_S052_no_plot_armor.py` -> `2
   passed`.
3. `pytest -q tests/csim/ -k E07` (3 repeats) -> stable at `31 passed, 6
   failed`, all 6 the `tests/csim/controls/test_control_e07_*` files —
   pre-existing, unrelated to S-052 (sweep scorecard's separate B6 line:
   "not tag-ready: R-049-06, R-052-01, R-052-02"). `R-049-06` itself passes
   standalone (`test_E07_S049_a_revolt_can_birth_a_nation.py`: `7 passed`)
   and in every repeat of the batched `-k E07` run above; one earlier
   one-off run (mid-investigation, with unrelated scratch repro files still
   in `tests/csim/`) showed it failing alongside the 6 controls — collection
   pollution from those now-deleted scratch files, not a real regression.
   R-049-06 untouched either way, out of this task's scope.
4. csrc unchanged -> `E-02`..`E-08` failing-id sets and
   `checksum_trace.py --lib build/O2/libouroboros.so --seed 1 --regions 60
   --ticks 500 --features 6` output identical before/after by construction
   (same binary). Ran once post-fix for the record: checksum trace
   completes clean, no crash, no NaN.

Files touched: `tests/csim/test_E07_S052_no_plot_armor.py`. No file outside
`tests/csim/` touched.

## R-072-02 / R-072-06: E-10 S-072 urgency composite stability + unreachable ceiling (M0 design-lane ruling, 2026-09-22)

### `test_E10_S072_orders_come_from_where_the_world_hurts.py::test_R_072_02_urgency_clamp_0_4_deficit`

"stability" in ALG-55's deficit term (`docs/bible/algorithms.md`) is the
ALG-09 composite stability (`m*0.40 + (100-t)*0.35 + p*0.25`, with the two
threshold penalties), the bible's only definition of stability — the E-10
window control `tests/csim/controls/test_control_e10_window_urgency_deficit_divisor_wrong.py`
already reads it that way. The test's `expected_deficit = 0.60` used raw
tension (40) as a stand-in for stability instead of computing the composite:
test defect, per CLAUDE.md's `test-defect` class (a fixture whose own
numbers never reach the branch it claims to test).

Fixture: region 0 military=40.0, economy=40.0, tension=40.0, population=50.0.
`alg09_stability = 40*0.40 + (100-40)*0.35 + 50*0.25 = 16.0 + 21.0 + 12.5 =
49.5` (no penalty: m=40 >= 10, p=50 >= 20). `expected_deficit = ((100-40) +
(100-40) + (100-49.5))/300 = 170.5/300 = 0.5683333...`. With
`expected_conflict = 1.0` and `expected_chain = 0.60` unchanged,
`expected_urgency = clamp(0.4*0.568333... + 0.4*1.0 + 0.2*0.60, 0, 1) =
0.227333... + 0.40 + 0.12 = 0.747333...`.

Fix: replaced the hardcoded `expected_deficit = 0.60` with the ALG-09
computation from the fixture's own fields, inline in the test, plus a
derivation comment; `expected_conflict`, `expected_chain`, and the clamp
line are untouched. No other assertion in the file changed for this rule.

Verified red at stub on main both before and after: `assert urgency ==
pytest.approx(expected_urgency, abs=1e-6)` fails both times because
`om_mission_compute_urgency` is a stub returning `0.0` (`Obtained: 0.0`
against `Expected: 0.76` before, `Expected: 0.7473333333333334` after) —
same failure, corrected expected value. B9-2 (the branch that lands
ALG-55's composite stability) is expected to turn this green; B9-1 does not
(it used raw tension), confirmed by reading that branch's mission.c diff,
not by running it.

### `test_R_072_06_urgency_0_8_it_beats`

R-072-06 ("stability 15 under attack by a neighbor at military 80 -> urgency
>= 0.8") cannot hold under R-072-02's exact weights: `urgency = 0.4*deficit
+ 0.4*conflict + 0.2*chain`, each term capped at 1.0, so 0.8 requires
`deficit=1.0` and `conflict=1.0` simultaneously (every field at 0) with the
chain term contributing nothing extra; the fixture holds military and
economy at 20 (not 0), giving a ceiling around 0.75, not 0.8. R-072-02's
form stays as tested (see above); this is a genuine scenario/threshold
conflict between two rules in the same story, not a fixture bug.

Fix: opened `Q-072-02` in `docs/northstar/ambiguity_register.md` (the id
`Q-072-01` is already taken — closed, unrelated, answers R-072-07's
no-candidate-in-pool fallback, and `test_R_072_07_q_072_01` already depends
on that closed answer) with the arithmetic above and three candidates: (a)
an active revolt chain in the region (two revolt events, chain 0.6 -> +0.12
closes most of the gap); (b) threshold drops to >= 0.7; (c) the weights
change (e.g. conflict weight 0.5). Marked
`test_R_072_06_urgency_0_8_it_beats` with
`@pytest.mark.skip(reason="Q-072-02 open: ...")` — a skip under an open
flag, the assertion itself untouched.

### Verification (both rules)

1. Before edit: `pytest -q tests/csim/test_E10_S072_orders_come_from_where_the_world_hurts.py`
   -> `7 failed` (all seven rule tests fail on the stub; R-072-01/03/04/05/07
   fail on unimplemented `om_mission_*` symbols returning 0/defaults,
   R-072-02 on the wrong expected value, R-072-06 on `urgency_0 >= 0.8`).
2. After edit: same command -> `6 failed, 1 skipped` — R-072-06 now skipped
   under Q-072-02, every other test in the file fails for the same reason
   as before (stub), R-072-02 fails on the corrected `0.7473333333333334`
   expected value against the stub's `0.0`.
3. No file outside `tests/csim/test_E10_S072_orders_come_from_where_the_world_hurts.py`
   and `docs/northstar/ambiguity_register.md` touched for this fix.

Files touched: `tests/csim/test_E10_S072_orders_come_from_where_the_world_hurts.py`,
`docs/northstar/ambiguity_register.md`.

## E-06 (B5-3) test-fix gate, 2026-09-24

Branch `push/E06-tests-1`, worktree `~/Projects/om-push/wt/e06-tests` (main),
verify worktree `~/Projects/om-push/wt/e06-verify` (detached `origin/push/B5-3`,
build fresh via `make -j8` both sides). Three tests classed test-defect by
design lane, fixed under test-fix gate. Assertions preserved every case —
none loosened, none deleted.

### `test_R_045_07_one_uniform_draw_made_if`

Confound: Knowledge Lost now a registered external event
(`om_event_register_external` + `om_event_queue_external`, csrc/diplomacy.c,
B5-3 only). Reaches `om_tick_events`/`read_events` one tick after it fires
(due_tick = fire tick + 1), and only with `OM_FEAT_EVENTS` on. Fixture's
`isolate_agents` turns EVENTS off; world_factory only turns DIPLOMACY +
TECHNOLOGY on for E-06 module (mvp_features.toml).

Change: added `lib.om_world_set_feature(w, OMFeature.EVENTS, 1)` right after
TECHNOLOGY is turned on. After the tech-step assertions (tech value,
last-knowledge-lost tick — both read right after the first `om_world_step`,
untouched by what follows), added a second `lib.om_world_step(w)` to reach
the due tick before reading events. Cooldown (last_knowledge_lost just set
to 106) rules out a second draw firing on that extra step. Swapped the dead
`e.region_idx == 0` filter for `template_name(lib, w, e.template_id) ==
"Knowledge Lost"` (F2h binding, conftest.py's `template_name` helper), kept
a `region_idx == 0` check on the found record so the rule's "highest
population region" clause still gets checked.

Red/green: main — red both before and after (main's diplomacy.c never
registers/queues the record at all, `om_event_fire_manual` only, no
`om_tick_events` path exists for it). B5-3 — red before, green after.

Control: extra step removed -> `assert len(kl_events) >= 1` fails, `assert 0
>= 1`, same line, no setup error. Template name misspelled ("Knowledge
lost") -> same failure, same line. Both restored after.

### `test_R_045_09_mean_over_all_windows_between`

Confound 1 (directed fix): dead filter. `OmFiredEvent` has no
`is_knowledge_lost` field; `getattr(e, "is_knowledge_lost", False)` always
took the `False` default, so the filter never matched a real record no
matter what fired.

Change: `lib.om_world_set_feature(w, OMFeature.EVENTS, 1)` added right after
`generate()` (E-06 isolation never turns EVENTS on for this module either).
Filter swapped to `template_name(lib, w, e.template_id) == "Knowledge
Lost"`, same F2h binding as R-045-07. The one-tick queue lag does not need a
skipped read here — the loop already reads events every tick, so a record
queued at tick T just gets counted on the T+1 read instead of T, inside the
same or an adjacent window.

Control (isolated from confound 2 below): reused R-045-07's own eligible
fixture (forced draw 0.01, cooldown cleared, EVENTS on, stepped twice) in a
throwaway probe and read the resulting record through both filters —
`getattr(e, "is_knowledge_lost", False)` -> 0, `template_name(...) ==
"Knowledge Lost"` -> >=1, on the identical event list. Proves the new filter
is not itself vacuous; not committed (probe only, not one of the two test
files).

Red/green: main — red before and after (same reason as R-045-07: nothing to
register on main). B5-3 — **still red after the directed fix**: `expected
mean Knowledge Lost events between 1.0 and 2.0, got 0.0`.

Confound 2 (found while fixing, not in the original finding, NOT fixed —
reporting per "propose, do not fix"): under E-06 isolation
(DIPLOMACY+TECHNOLOGY only, mvp_features.toml), nothing ever touches region
economy or population — no DRIFT, no FACTIONS, no FRICTION. Measured a
freshly generated 50-faction/100-150-region world (seed 12345): starting
avg economy per faction 34.3-57.3, never dips near the eligibility floor of
20.0 over the run; population never moves at all (0.0 max drop over 2000
ticks measured). R-045-07's own eligibility clause ("avg economy < 20.0, or
avg population fallen >= 10.0 over 50 ticks") can never fire from this
fixture as constructed — Knowledge Lost is structurally unreachable, not
just poorly filtered. Confirmed by direct instrumentation (min avg economy
over 2000 ticks: 30.66 even with EVENTS+FACTIONS+FRICTION+ADMIN_REVOLTS+
DRIFT all forced on for the probe; population drop stayed exactly 0.0).

Real C gap found chasing confound 2 (propose, do not fix): turning on
FACTIONS for the probe still produced 0 attacks and budget stuck at exactly
0.0 for every one of the 50 factions after 1000 ticks, direct
`om_faction_step_budget` calls included. Root cause, isolated by comparison
against a hand-built fixture (which grows budget correctly:
`(100-8)*0.025*2 = 4.6`, confirmed empirically): `csrc/worldgen.c`'s
per-faction setup loop (~line 237-253) sets `w->faction_tech[fid] = 0.0`
directly but never calls `om_faction_tech_multipliers_recalc` (or otherwise
populates `w->faction_tech_attack/defense/economy[]`), so every
procedurally generated faction's tech-economy multiplier cache stays at its
calloc default of `0.0`. `om_faction_step_budget` (csrc/faction.c:250)
does `delta *= w->faction_tech_economy[f]`, so the whole per-tick budget
accrual is multiplied by zero for every generated faction, forever — no
faction can ever afford an attack, so combat, population loss, and any
economy dip past drift's own small amplitude never happen for a purely
generated world. Confirmed by calling `om_faction_set` on one generated
faction mid-run (which does call the recalc): that faction's budget growth
starts working immediately afterward (500.0 -> 503.999...). This would
also silently zero every generated faction's attack/defense multipliers
(ALG-26), not just economy — anything that exercises a *generated* faction
in combat without re-calling `om_faction_set`/`set_faction` on it first is
getting tech multiplier 0.0 (mult = 1.0, i.e. tech has zero effect) instead
of the real value. Not fixed here — out of scope (no C edits authorized for
this card) and a worldgen behavior change, not a test fixture.

Net: R-045-09 fixed for the directed confound (dead filter, EVENTS off) and
left red, correctly, for a second, deeper, unfixed defect that needs a
design-lane call: either "the launch config" in this rule's Given clause
means turning on a fuller feature set for this fixture specifically (which
alone still would not be enough while the worldgen tech-multiplier gap
above stands), or the C gap gets fixed first. Recommend opening a
`Q-045-0x` ambiguity register row for "what feature set does R-045-09's
'launch config' mean" plus a bug ticket for the worldgen tech-multiplier
gap.

### `test_R_046_04_effective_attack_multiplied_by_it`

Confound 1: defender (faction 1, Fortifier, budget=100.0) had a viable
attack of its own against faction 0's region under `om_faction_candidates`/
`om_step_decisions` (csrc/agent.c) — `potential_commit = budget_snapshot *
0.70 = 70.0`, comfortably beats faction 0's military-50 region. Two attacks
resolved in one step (`len(attacks) == 2`), so `assert len(attacks) == 1`
failed before the effective_attack/effective_defense assertions ever ran.

Confound 2: the fixture's own arithmetic comment did not follow ALG-20
(docs/bible/algorithms.md: `effective_attack = commit * ATTACK_EFFICIENCY *
tech_attack(attacker) * surprise` — no military term at all).
`csrc/resolve.c`'s `om_step_resolve` matches ALG-20 exactly (`effective_attack
= commit * 1.0 * tech_attack * surprise_mult`, confirmed by reading the
source). The old comment's `20.0 * 0.5 + 50.0 * 0.1 * 0.5 = 12.5` invented a
military term ALG-20 does not have, then `12.5 * 1.096 = 13.7` compounded
the error into the asserted expected value. The old defense comment also
dropped `RESISTANCE_FACTOR` entirely (`40.0 * 1.054`, no `0.55`).

Fix: `set_faction` for faction 1 changed `budget=100.0` -> `budget=0.0`
(same convention as `tests/csim/test_core_intent_inject.py`'s own R8f pin,
which also holds the non-injected hostile counterpart at budget 0.0 so only
one decision is viable). `effective_defense` never reads the defender's
budget (`csrc/resolve.c` uses `target->military` and tech only), so this
does not touch the value under test. Recomputed both expected values from
ALG-20 with the fixture's own numbers instead of the old comment:

```
effective_attack = commit * ATTACK_EFFICIENCY * tech_attack(conqueror@60) * surprise
                  = 20.0  * 1.0               * 1.096                    * 0.5
                  = 10.96

effective_defense = target.military * RESISTANCE_FACTOR * tech_defense(fortifier@60) * entrenchment
entrenchment: held_since=0, om_world_step increments tick to 1 before resolving,
              ent = 1.0 + min(1, (1-0)/100) = 1.01
                   = 40.0            * 0.55              * 1.054                     * 1.01
                   = 23.41988
```

Both values confirmed empirically by reading `att.effective_attack` /
`att.effective_defense` straight off a run of the fixed fixture (not just
hand math): `eff_atk 10.96 eff_def 23.419880000000003`.

Red/green: main — red before (2 attacks), green after. B5-3 — same (B5-3's
diplomacy.c diff does not touch csrc/resolve.c or csrc/agent.c, so this
rule's behavior is identical on both branches).

Control: attacker tech dropped to 0.0 (attack multiplier forced to 1.0) ->
`assert att.effective_attack == pytest.approx(20.0 * 1.0 * 1.096 * 0.5,
abs=1e-3)` fails, `Obtained: 10.0, Expected: 10.96 ± 0.001` — the assertion
catches an unapplied multiplier. Restored after.

### Whole-suite check (verify worktree, B5-3 + fixed test files)

`tests/csim` full run, before fix (B5-3's own two test files) vs after
(fixed test files copied in, no other change): `342 failed, 398 passed` ->
`340 failed, 400 passed`. Diffed sorted FAILED id lists
(`grep -E '^FAILED' | sed 's/ - .*//' | sort`): the only two lines removed
are `test_R_045_07_one_uniform_draw_made_if` and
`test_R_046_04_effective_attack_multiplied_by_it`; zero lines added. No new
red anywhere in the suite. `test_R_045_09_mean_over_all_windows_between`
stays on both lists (confound 2 above).

`tests/qa/t1`: `test_rts_detectors.py` fails collection
(`ModuleNotFoundError: No module named 'scripts.qa'`, its own comment says
"expected red: module does not exist yet") and
`test_control_empty_drifts_trips_empty_region_drifted` /
`test_control_osc_as_level_trips_oscillator_as_level` fail — all three
identical on unmodified main and on the verify worktree before touching
anything; unrelated to E-06, not touched.

Files touched: `tests/csim/test_E06_S045_a_faction_s_technology_is_one_number.py`,
`tests/csim/test_E06_S046_archetypes_spend_tech_differently.py`,
this evidence file.

## push/tests-fix-4 test-fix gate, 2026-09-24

Branch `push/tests-fix-4`, worktree `~/Projects/om-push/wt/tests-fix-4`,
base origin/main merged with origin/push/B9-4, origin/push/B13-2,
origin/push/B14-2 (all clean merges, ort strategy, no conflicts). 9 items
from design lane, all classed test-defect. Assertions preserved everywhere
fixed — none loosened, none deleted. One item (R-123-01) left red and
reported, module gap not a fixture bug.

### R-078-04 / R-078-07 (`test_E10_S078_a_battle_becomes_history.py`)

Confound: no faction registered as player. `om_mission_player_faction`
(csrc/mission.c:476) scans `faction_used[]`/`faction_archetype[]` for
`OM_ARCH_PLAYER`; unset slot defaults `faction_archetype==0==PLAYER` via
calloc but `faction_used==0`, so it never matches — returns -1, transfer
and adjacent_player-target code both bail early.

Fix: added `set_faction(lib, w, 1, 0)` (archetype 0 = PLAYER) before owner
setup in both tests. R-078-07 also had `om_region_set_owner` calls BEFORE
`set_region` — `set_region` resets `faction_id` to -1, wiping the ownership
set_owner had just written. Reordered: `set_region` first, `set_owner`
after.

Red before: `test_R_078_04` — `assert owner == player_faction`, `assert 2
== 1`. `test_R_078_07` — `assert lib.om_region_field(w, 1, ...) ==
approx(55.0)`, `Obtained: 50.0`.
Green after: both pass.
Control: `set_faction` player id changed to an unregistered faction (3 for
078-04, 5 for 078-07), rerun, same failures as red-before reproduced
exactly. Reverted, green restored.

### R-078-05 (`test_E10_S078_a_battle_becomes_history.py`)

Confound: `read_drift(lib, w, 0, OMField.TENSION)` — conftest's
`read_drift(lib, w, idx)` takes 3 args (returns `(rc, row)` from
`om_region_drift`), not 4; called with a 4th positional arg (`OMField.
TENSION`), TypeError.

Fix: read the field with `om_region_field(w, 0, OMField.TENSION)` (4-arg
getter) instead.

Red before: `TypeError: read_drift() takes 3 positional arguments but 4
were given`.
Green after: passes, tension == 44.8.
Control: `OM_MISSION_REFUSAL_TENSION_DEFICIT_PCT` (csrc/mission.c:265)
flipped 8.0 -> 20.0, rebuilt, rerun: `assert 52.0 == 44.8 ± 1e-4`. Reverted,
rebuilt, green restored.

### R-080-02 (`test_E10_S080_...py`) and R-125-01 (`test_E14_S125_...py`)

Confound: both pin easy-floor/hard-ceiling at 1.0. `om_mission_compute_
parity` is a public alias (csrc/mission.c:1068) of `om_mission_compute_
difficulty_parity`, which uses `OM_MISSION_PARITY_EASY_FLOOR 0.95` /
`OM_MISSION_PARITY_HARD_CEILING 0.85` (csrc/mission.c:189-190) — the same
constants the already-green `test_R_074_03` asserts. R-074-03 is the rule
both tests cite.

Fix: recomputed expected values with 0.95/0.85 instead of 1.0/1.0. Only
the hard-difficulty branch actually changes value in both tests (easy
floor 0.95 never binds against the fixture's base parities of 1.2, 0.8, or
1.0).

Red before: `test_R_080_02` — `assert 1.0 == 1.0` masked the bug at
base=1.2 (floor never binds there) but `p_easy_low` (base=0.8) asserted
1.0, `Obtained: 0.95`; `test_R_125_01` — `p_hard` asserted 1.0, `Obtained:
0.85`.
Green after: both pass.
Control: `OM_MISSION_PARITY_HARD_CEILING` flipped 0.85 -> 0.99, rebuilt,
both tests fail at their hard-difficulty assertion (`0.99 == 0.85 ± 1e-5`).
Reverted, rebuilt, green restored.

### R-120-03 (`test_E14_S120_five_behaviors_three_moods.py`)

Confound: pins cautious/aggressive speed multipliers at 0.6/1.2, the
bible's own example numbers. Q-120-01 (ambiguity register) closed (b),
2026-09-16: AI postures deferred, baseline speeds, no modifier-based speed
or spacing change. Code (`OM_MACRO_SPEED_MULT_CAUTIOUS`/`_AGGRESSIVE`,
csrc/enemy_macro.c:122-123) already implements the closed decision (both
1.0).

Fix: test expectations changed to 1.0/1.0. Also rewrote the E-14 epic
(docs/bible/epics/E-14-enemy-macro-behavior.md): R-120-03's prose dropped
the stale 0.6×/1.2× example (now "baseline speed" for both postures), and
the stale "Open flags: Q-120-01 ..." line under S-120 replaced with the
closed decision (rewrite, not append — no PIVOT marker, old text deleted).
This is the only bible file touched, per assignment.

Red before: `assert 0.6 == 1.0 ± 1e-5`.
Green after: passes.
Control: `OM_MACRO_SPEED_MULT_CAUTIOUS`/`_AGGRESSIVE` flipped back to
0.6/1.2, rebuilt, rerun: `assert 0.6 == 1.0 ± 1e-5` (same failure as
red-before). Reverted, rebuilt, green restored.

### R-123-01 and R-076-03 (getter-loop driver swap)

Both drove the tactical clock with `om_tactical_tick(w)` in a loop —
`om_tactical_tick` is a pure getter (csrc/mission.c:1562 comment confirms:
"never allocates or mutates"), so the loop did nothing every iteration.
The freeze's real drivers are `om_tactical_step`/`om_world_step`.
`om_tactical_step` is a no-op returning 0 when zero units exist
(csrc/unit.c:909-919, current_tick only increments inside `om_ability_
advance_all`, which the zero-unit guard skips entirely).

**R-076-03** (`test_E10_S076_the_clock.py`): fixed. Neither fixture spawned
a unit. Added `lib.om_unit_spawn(w, OMUnitType.VANGUARD, 0, 0.0, 0.0, 0)`
(new local `OMUnitType` class, same enum other E-1x test files define
locally) before the tick loop, swapped `om_tactical_tick` -> `om_tactical_
step` in the 1000-iteration loop. `om_mission_get_objective_score` doesn't
read tick state at all (csrc/mission.c:1497 comment: "nothing here reads a
tick or a deadline"), so only the `om_mission_is_ended` deadline check
needed the clock to actually move.

Red before: `assert lib.om_mission_is_ended(w) == 1` — `assert 0 == 1`
(clock frozen at baseline the whole loop).
Green after: passes, both halves.
Control: loop range dropped 1000 -> 999 (one tick short of the 1000-tick
deadline), rerun: `assert lib.om_mission_is_ended(w) == 1` fails, `assert 0
== 1` (same assertion line as red-before, now correctly catching "not
there yet" instead of "never moved"). Reverted, green restored.

**R-123-01** (`test_E14_S123_the_enemy_replays_like_i_do.py`): NOT fixed,
left red, reported. Swapping the driver alone is not enough — probed
empirically (unit spawned in both worlds, `om_tactical_tick` -> `om_
tactical_step` in the 200-tick loop, ran under pytest): `om_replay_
command_count(w1) == 0` still. Traced why: nothing in the C source calls
`om_replay_log_command` except tests themselves (`grep -rn
om_replay_log_command csrc/*.c` — only the definition site, csrc/enemy_
macro.c:672). `om_macro_tick` (csrc/enemy_macro.c:488) is never called by
`om_tactical_step`, `om_world_step`, or any other tick driver — it's a
free-standing function only ever invoked directly by tests (see test_
R_120_04's own `lib.om_macro_tick(w, 39)` calls). So even with the clock
correctly advancing, no code path exists that turns enemy macro decisions
into replay-log entries automatically. This is a module gap — enemy macro
output is not wired to the replay stream at all yet — not a test driver
bug. Per leaf-mechanics.md ("A behavior another module must provide is
reported as a closure leftover naming the symbol and the owning module,
never stubbed across files"), reporting instead of forcing: closure
leftover, symbol `om_replay_log_command`, owning module enemy_macro.c (or
wherever the eventual auto-log call site lands), needs a call site inside
the macro evaluation path (`om_macro_tick` or whatever finally drives it
per-tick) before R-123-01 can pass without the test manually faking log
entries. Probe edit reverted, file left untouched (0-line diff).

### R-126-04 (`test_E15_S126_most_of_my_force_is_out_there.py`)

Confound: `assert ctypes.c_double(reinforcement_cap).value >= pytest.
approx(80.0, abs=1e-5)` — `>=` is not defined between `float` and pytest's
`ApproxScalar`, `TypeError`.

Fix: `>= 80.0 - 1e-5` (same tolerance, plain float compare, no `pytest.
approx`).

Red before: `TypeError: '>=' not supported between instances of 'float'
and 'ApproxScalar'`.
Green after: passes.
Control: `OM_SUP_STARTING_FORCE_FRACTION` (csrc/tactical_support.c:185)
inlined as 0.5 at both call sites (`om_mission_compute_starting_force`,
`om_mission_compute_reinforcement_capacity`), rebuilt, rerun: `assert
ctypes.c_double(starting_force).value == approx(20.0)` fails first,
`Obtained: 50.0` (this line runs before the fixed `>=` line, so it's the
one that catches the flip — confirms the whole test still bites on a real
regression, not just the TypeError). Reverted, rebuilt, green restored.

### R-092-04 (`test_E12_S092_recon_then_fog.py`)

Confound: `set_region(w2, 0, OMField.MILITARY, 0.95)` — conftest's
`set_region(lib, w, idx, *, tier=..., military=..., ...)` is keyword-only
past `idx` and takes `lib` as first arg; called with 4 positional args (no
`lib`, and `OMField.MILITARY`/`0.95` positional instead of `military=
0.95`), `TypeError: takes 3 positional arguments but 4 were given`.

Fix: `set_region(lib, w2, 0, military=0.95)`.

Red before: `TypeError: set_region() takes 3 positional arguments but 4
were given`.
Green after: passes.
Control: `om_recon_get_terrain_visibility_ratio` (csrc/fog.c:415-418,
already a hardcoded `return 1.0` by design — "regardless of world state")
flipped to `return 0.5`, rebuilt, rerun: `assert approx(0.5) == 1.0` fails,
`Obtained: 1.0` (comparison order from `pytest.approx` on the left makes
the message read backwards but the failure is real). Reverted, rebuilt,
green restored.

### R-065-05 vs R-065-06 (`test_E09_S065_five_to_ten_entries_in_the_right_order.py`)

Read both rules (docs/bible/epics/E-09-chronicle.md:36-37). R-065-05:
standard fill takes clusters in descending score, capped at 2 per
category, until 10 entries. R-065-06: "Given fewer than 5 entries after
ranking ... skipped clusters are added in score order until 5" — no cap
caveat on the fallback add, it just says skipped clusters go back in by
score until 5. `test_R_065_06` (single category, 5 clusters, cap would
give 2) already passes on unfixed code with `entry_count == 5` — code
already implements "fallback overrides the cap for the minimum". Probed
`test_R_065_05`'s actual scenario (5 clusters cat 10 + 3 clusters cat 11):
cap-fill gives 4 (2+2), which is < 5, so the R-065-06 fallback fires and
adds the next-highest skipped cluster (cat 10's 7.0 score) to reach 5 —
`cat10_count` ends at 3, `entry_count` at 5. R-065-05's pinned total of 4
(and its `cat10_count <= 2` assertion) is the defect: the epic's own
composition of both rules (065-05's cap plus 065-06's fallback) puts this
fixture's real answer at 5, not 4.

Fix: `cat10_count == 3` (was `<= 2`), `cat11_count == 2` (was `<= 2`),
`entry_count == 5` (was `== 4`). `R-065-04` (same file) and `R-078-06`,
`R-092-02` (other files) also failed on this branch but are not part of
this assignment — left untouched, unrelated confounds (not investigated
further, out of scope).

Red before: `assert cat10_count <= 2` — `assert 3 <= 2`.
Green after: passes.
Control: `OM_CHRONICLE_MIN_ENTRIES` (csrc/om_constants.h:345) flipped 5 ->
4, rebuilt, rerun: `assert cat10_count == 3` fails, `assert 2 == 3` (with
the fallback target lowered to 4, cap-fill's 4 entries already satisfy the
floor, so no fallback add happens, cat10 stays capped at 2). Reverted,
rebuilt, green restored.

### Whole-suite check (`tests/csim`, before vs after)

`git stash` (all 9 test-file edits + epic doc), rebuilt (no-op, C
untouched), ran `tests/csim` full: `187 failed, 562 passed, 7 skipped, 1
xfailed`. `git stash pop`, rebuilt (no-op again — confirms no leftover
flipped constant from any control run), ran again: `177 failed, 572
passed, 7 skipped, 1 xfailed`. Diffed sorted FAILED-id lists (`LC_ALL=C
sort`): 10 lines removed (exactly the 10 fixed assertions above across 8
files — note R-078-04/05/07 are 3 ids from one file), 0 lines added. No
new red anywhere in the suite. `test_R_123_01`, `test_R_065_04`, `test_
R_078_06`, `test_R_092_02` all present on both lists, confirmed unchanged
(the first left red and reported per above; the other three untouched,
out of assignment).

Both lints (`scripts/specfactory/libm_lint.py csrc`,
`scripts/specfactory/alg_constants.py --lint csrc`) clean. `make -j8`
clean from a from-scratch build (`.so` files removed first), zero
warnings.

Files touched: `tests/csim/test_E09_S065_five_to_ten_entries_in_the_right_order.py`,
`tests/csim/test_E10_S076_the_clock.py`,
`tests/csim/test_E10_S078_a_battle_becomes_history.py`,
`tests/csim/test_E10_S080_difficulty_is_scarcity_not_stronger_enemies.py`,
`tests/csim/test_E12_S092_recon_then_fog.py`,
`tests/csim/test_E14_S120_five_behaviors_three_moods.py`,
`tests/csim/test_E14_S125_how_hard_the_enemy_tries.py`,
`tests/csim/test_E15_S126_most_of_my_force_is_out_there.py`,
`docs/bible/epics/E-14-enemy-macro-behavior.md`,
this evidence file.

## push/tests-fix-5 (2026-09-24)

Branch `push/tests-fix-5`, worktree off origin/main, merged in
`origin/push/B10c` (one mechanical conflict in `csrc/unit.c`: HEAD had
`/* STUB: B10c implements */` stubs for `om_unit_brace_phase`,
`om_unit_count`, `om_unit_get_faction`, `om_unit_get_layer`,
`om_unit_get_unit_type`, `om_unit_id_at`; B10c side had the real bodies.
Took B10c side whole, no hand-edit), `origin/push/B11-3`, `origin/push/B12-4`
(both clean merges). 5 items from the design lane, all classed test-defect.
Method same as above sections: git-stash isolate before/after, quote first
assertion line, one positive control per item, whole-`tests/csim` failing-id
diff before/after on the merged build.

### `test_E13_S098_firing_through_friends.py::test_R_098_01_shot_lands_friendly_units_never`

Confound: fixture assumed Bombard flat damage 110.0 vs a Raider target —
no roster entry has 110. Real numbers: `OM_ROSTER_BOMBARD_DAMAGE` 17.5
(csrc/unit.c), Bombard category Siege, Raider category Strike,
`OM_CATEGORY_MULTIPLIER_SIEGE_STRIKE` 0.20 (csrc/om_constants.h, ALG-60) —
`17.5 * 0.20 = 3.5`. Fix: comment + expected value 110.0 -> 3.5. Friendly-
never-blocks-fire claim untouched.

Red before: `assert 3.5 ± 1.0e-04 == 110.0` (Obtained 110.0, Expected
3.5 ± 1.0e-4 — pytest's approx prints LHS/RHS reversed from the usual
"got/want" order; the sim's own hit was 3.5 both times). Green after: 2
passed. Control: flipped expected to 4.5, `assert 3.5 ± 1.0e-04 == 4.5`
failed, reverted.

### `test_E13_S100_facing.py::test_R_100_01_it_faces_target_moving_with`

Confound: step 3 assumed the Raider still sits at (0, 0) when it commands
attack-target; the 5 move ticks in step 1 already put it at x = 37.5
(150 wu/s / 20 tps = 7.5 wu/tick). Fix: read the unit's actual position
back (`om_unit_position_x/y`) right before spawning the enemy, compute the
expected facing as `atan2(target_y - uy, target_x - ux)` instead of the
hardcoded `pi/2`.

Red before: `assert 1.9285857182272876 ± 0.01 == 1.5707963267948966`
(sim's real facing 1.9285857182272876, old fixture wanted pi/2). Green
after: 3 passed. Control: added `+ 0.5` to the computed expected value,
`assert 1.9285857182272876 ± 0.01 == 2.429566978569376` failed, reverted.

### `test_E11_S087_every_unit_thinks_the_same_way.py::test_R_087_01_it_moves_200_wu_directly`

Confound: run length 80 ticks outlives the stealthed Bombard's own attack
interval (`OM_ROSTER_BOMBARD_INTERVAL` 3.0s = 60 ticks). Debug trace
(position/in_flinch/target per tick) showed the victim's flinch completes
exactly at tick 51 (200 wu at Vanguard 80 wu/s = 4 wu/tick), holds flat at
x = -200 through tick 60, then at tick 61 the Bombard's real auto-fire
lands, restarts a second flinch from the already-fled position, and by
tick 80 the victim has over-shot to x = -276 (two flinches, not one).
Fix: shortened the run to 56 ticks — past arrival (tick 51) but under the
Bombard's own re-fire (tick 60~61) — and picked 56 (not just any value in
[51,59]) so the single extra `om_tactical_step` after the visibility flip
lands on the victim's own targeting-cohort tick (`unit_id % 4 == tick % 4`;
victim id 1, tick 57 % 4 == 1), matching the original test's structure of
one run + one extra step.

Red before: `assert -276.0 == -200.0 ± 5` (first assertion; a first attempt
at 50 ticks passed this line but then failed the second assertion,
`AssertionError: assert -1 == 2`, because the flinch had not yet fully
arrived and the extra step landed off-cohort — both diagnosed with the
debug trace before picking 56). Green after: 8 passed. Control: reverted
the run length to 80, `assert -276.0 == -200.0 ± 5` failed again
(reproduces the original confound exactly), reverted back to 56.

### `test_E11_S084_flat_damage.py::test_R_084_01_one_attack_lands_for_base`

Confound: the attacker Raider is idle with no order in step 1, so
`om_ability_autotrigger_scan` (csrc/unit.c) fires Surge on it the instant
the target is in range (`OM_UT_RAIDER` case: `if
(om_tac_enemy_within_range(...)) om_ability_start_surge(...)`), doubling
its output (`OM_ABILITY_SURGE_OUTPUT_MULT` 2.0) for the whole 16-tick
window before the fixture's one deliberate attack ever lands: 1.35 * 2 =
2.7. Fix: added one line, `lib.om_command_attack_target(w, attacker,
target)`, before the wait loop — an explicit order sets
`u->order != OM_ORDER_NONE`, which `om_tac_unit_ai` uses to suppress the
auto-trigger scan for that unit (`u->suppress_auto = 1`), same mechanism
B10c's brace-suppression rule uses for Vanguard. Attack timing and target
acquisition unaffected (same 16-tick interval, same in-range fire). Did
not touch `test_R_081_04` (symmetric Strike-vs-Line case, different file,
still 4/4 green after).

Red before: `assert 2.6999999999999886 == 1.35 ± 1.0e-06`. Green after: 7
passed. Control: flipped expected to 1.50, `assert 1.3500000000000227 ==
1.5 ± 1.0e-06` failed, reverted.

### `test_E12_S091_standing_high.py::test_R_091_03_it_affects_sensors_only_never`

Confound: fixture assumed Raider flat damage 40.0 and base sensor radius
300.0; roster is `OM_ROSTER_RAIDER_DAMAGE` 9.0, `OM_ROSTER_RAIDER_SENSOR`
800.0 (csrc/unit.c). Fix: 40.0 -> 9.0 (Strike-vs-Strike matchup 1.0, no
elevation damage bonus in Settled Reach — rule's own claim), and the
sensor-radius base in the elevation-multiplier assertion 300.0 -> 800.0
(`800 * 1.30 = 1040.0`).

Red before: `assert 9.0 ± 1.0e-04 == 40.0`. Green after: 3 passed.
Control: flipped expected damage to 10.0, `assert 9.0 ± 1.0e-04 == 10.0`
failed, reverted.

### `test_E12_S092_recon_then_fog.py::test_R_092_03_fog_applies_per_s_089`

Confound: fixture put the enemy at distance 500 assuming a 300 sensor
radius; real Raider sensor is 800, so 500 wu is inside range and
`om_unit_can_see` correctly returned 1, not the 0 the test wanted. Fix:
moved the enemy to distance 900 (outside 800) instead of 500. Terrain-
stays-visible claim untouched. `test_R_092_04` in the same file is a
distinct, pre-existing confound (`set_region(w2, 0, OMField.MILITARY,
0.95)` — `set_region()` takes 3 positional args, this call passes 4) —
not part of this item, not touched, still red before and after.

Red before: `AssertionError: assert 1 == 0` on
`lib.om_unit_can_see(w, friendly, enemy)`. Green after (this one id):
`test_R_092_03` passes; `test_R_092_04` stays red, unrelated and
unassigned. Control: reverted the enemy distance to 500, same
`assert 1 == 0` failure reproduced, reverted back to 900.

### `test_E12_S093_fog_is_for_the_player_not_the_engine.py::test_R_093_02_it_uses_its_own_visible`

Confound as assigned: fixture assumed Raider sensor 300 (in-range target
at 200, out-of-range at 500); real sensor 800, so the out-of-range target
was actually visible. Fixed the assigned part: in-range target moved to
700, out-of-range to 900, cover node moved from x=100 to x=350 (kept
roughly at the midpoint between observer and the in-range target so it
still sits on the line of sight). `can_see` assertions and the "acquire
target 1, not target 2" assertion all pass after this fix, confirmed with
a control (temporarily set the out-of-range target to 750, `assert
lib.om_unit_can_see(...) == 0` failed as expected — obtained 1 — reverted).

Left red, not fixed, reported instead of guessed: the test's last
assertion (`assert lib.om_unit_get_target(w, enemy) == 0` after cover
blocks line of sight to the previously-acquired target) still fails —
`om_unit_get_target` still returns the old target id. Traced with a
throwaway debug script (ctypes, direct calls, not committed): once
`om_unit_acquire_target` (csrc/fog.c) finds a target it calls
`om_command_attack_target`, which sets `u->order = OM_ORDER_ATTACK_TARGET`.
`om_tac_unit_ai`'s (csrc/unit.c) target-drop-on-lost-visibility check is
gated `if (!drop && u->order != OM_ORDER_ATTACK_TARGET)` — it explicitly
skips the visibility check once the unit is under an ATTACK_TARGET order,
so the stale target is never dropped, by a re-call of
`om_unit_acquire_target` or by `om_tactical_step`(both tried, same
result: target stays 2). This looks like a real gap (an enemy that
already "acquired" a target 1-shot ignores its own visible set from then
on, contradicting "same rules as the player's units" once cover moves in)
rather than a test-authoring mistake, and fixing it means touching
`csrc/unit.c` or `csrc/fog.c`, both out of a test-fix leaf's file list.
Not classed by the design lane as part of this item's confound either.
Leaving it red and naming it here rather than guessing at the C fix or
loosening the assertion.

### Whole-`tests/csim` check (merged build, before vs after this leaf's edits)

Before (5 test files at origin/main + B10c + B11-3 + B12-4, before any
edit): 161 failed, 588 passed, 7 skipped, 1 xfailed. After (7 edits across
the 5 named files): 155 failed, 594 passed, 7 skipped, 1 xfailed. Diffed
sorted `FAILED` id lists: exactly 6 lines removed
(`test_R_084_01_one_attack_lands_for_base`,
`test_R_087_01_it_moves_200_wu_directly`,
`test_R_091_03_it_affects_sensors_only_never`,
`test_R_092_03_fog_applies_per_s_089`,
`test_R_098_01_shot_lands_friendly_units_never`,
`test_R_100_01_it_faces_target_moving_with`), zero lines added. No new red
anywhere in the suite. `make -j8` clean on the merged build (both
`libouroboros.so` and `libouroboros_dbg.so`).
`scripts/specfactory/libm_lint.py csrc` -> `LIBM LINT OK`.
`scripts/specfactory/alg_constants.py --lint csrc` -> `CONSTANTS LINT OK`.

Files touched: `tests/csim/test_E13_S098_firing_through_friends.py`,
`tests/csim/test_E13_S100_facing.py`,
`tests/csim/test_E11_S087_every_unit_thinks_the_same_way.py`,
`tests/csim/test_E11_S084_flat_damage.py`,
`tests/csim/test_E12_S091_standing_high.py`,
`tests/csim/test_E12_S092_recon_then_fog.py`,
`tests/csim/test_E12_S093_fog_is_for_the_player_not_the_engine.py`,
this evidence file.

# F5 — window positive controls, one per module

Task F5 (decision 7, `docs/northstar/plans/briefs/2026-09-22-two-day-push.md`): one
live control per module for the window, design lane authored, planted in C by the
leaf later. Scope: `csrc/ouroboros_sim.h` (`om_bug` enum blocks under
`OM_DEBUG_INJECT` only), `tests/csim/conftest.py` (`OMBug*` mirrors only), twelve
new files under `tests/csim/controls/`.

Delivered **eleven** of the twelve assigned modules. `enemy_macro.c` (E-14) has no
id and no file — see "Module with no rule" below; not guessed.

## Table

| Module | Epic | File | Id | Rule (algorithms.md) | Planted fault | Liveness verdict |
|---|---|---|---|---|---|---|
| `worldgen.c` | E-03 | `test_control_e03_window_starting_ratio_swapped.py` | `OM_BUG_STARTING_RATIO_SWAPPED` = 312 | ALG-30 general formula: `economy = population*1.1 + jitter`, `military = population*0.7 + jitter` | economy/military ratio constants swapped | **ERROR** (unbuilt stub — `om_gen_set_extra_edges_enabled` undefined symbol in the current `worldgen.c`/`region.c` build; confirmed with `nm -D`, only `om_gen_set_faction_count`/`om_gen_set_region_range` are exported today) |
| `diplomacy.c` | E-06 | `test_control_e06_window_tech_growth_terms_swapped.py` | `OM_BUG_TECH_GROWTH_TERMS_SWAPPED` = 402 | ALG-27: `growth = 0.35*(avg_e/100)*max(0.3, avg_p/100)` | avg_e and avg_p swapped between the ratio term and the floor-clamped term | **DEAD** ("both runs failed" — `om_tech_step` is a no-op stub, returns unchanged tech regardless of injection) |
| `lifecycle.c` | E-07 | `test_control_e07_window_zombie_ge_not_gt.py` | `OM_BUG_ZOMBIE_PASS1_GE_NOT_GT` = 501 | ALG-42 pass 1: a zero-region breakaway is removed when `tick - created_tick >= 5` | `>` used instead of `>=` at the exact-5-ticks boundary | **DEAD** (stub never removes any faction, injected or not) |
| `generational.c` | E-08 | `test_control_e08_window_time_jump_clamp_skipped.py` | `OM_BUG_TIME_JUMP_CLAMP_SKIPPED` = 600 | ALG-45: `n = clamp(requested, 20, 100)` | clamp skipped entirely, returns `requested` verbatim | **DEAD** (stub returns something stub-fixed regardless of injection) |
| `chronicle.c` | E-09 | `test_control_e09_window_significance_cap_skipped.py` | `OM_BUG_SIGNIFICANCE_CAP_SKIPPED` = 700 | ALG-50: `base = tier + min(|delta|/50, 3.0)` | the 3.0 cap skipped, raw ratio used | **DEAD** |
| `mission.c` | E-10 | `test_control_e10_window_urgency_deficit_divisor_wrong.py` | `OM_BUG_URGENCY_DEFICIT_DIVISOR_WRONG` = 800 | ALG-55: `deficit = ((100-m)+(100-e)+(100-stability))/300` | divisor 300 replaced with 200 | **DEAD** |
| `unit.c` | E-11 | `test_control_e11_window_brace_reduction_wrong_constant.py` | `OM_BUG_BRACE_REDUCTION_WRONG_CONSTANT` = 901 | ALG-60: Brace reduction 0.50 | Fortify's 0.20 used instead of Brace's 0.50 | **DEAD** |
| `fog.c` | E-12 | `test_control_e12_window_interference_ignores_intensity.py` | `OM_BUG_INTERFERENCE_IGNORES_INTENSITY` = 1000 | ALG-65: `effective = sensor_radius*(1-interference(pos))`; a zone samples its own configured intensity at its center | intensity ignored, constant 1.0 reported inside any zone | **DEAD** |
| `tactical_move.c` | E-13 | `test_control_e13_window_navmesh_cell_size_wrong_constant.py` | `OM_BUG_NAVMESH_CELL_SIZE_WRONG_CONSTANT` = 1101 (1100 = `OM_BUG_MOVE_RUBBERBAND`, already Q2's) | ALG-67: `NAVMESH_CELL_SIZE = 100` | reports `NAVMESH_CELL_SIZE * NAVMESH_OBSTACLE_THRESHOLD` (70.0) instead of 100.0 | **DEAD** |
| `enemy_macro.c` | E-14 | — | — (1200s range reserved, no id assigned) | — | — | not attempted; see below |
| `tactical_support.c` | E-15 | `test_control_e15_window_structure_max_hp_wrong_constant.py` | `OM_BUG_STRUCTURE_MAX_HP_WRONG_CONSTANT` = 1300 | ALG-75: `REINFORCEMENT_STRUCTURE_HP = 3000` | `om_structure_get_hud_data`'s `max_hp` reads `REINFORCEMENT_CAPTURE_RADIUS` (300.0) instead | **DEAD** |
| `save.c` | E-16 (per this task's own numbering; the epic file is E-16 client/camera/hud) | `test_control_e16_window_save_skips_tick.py` | `OM_BUG_SAVE_SKIPS_TICK` = 1601 (1600 = `OM_BUG_SAVE_SKIPS_RNG_STATE`, already T2c's) | R-111-02: load restores the world such that the next jump is deterministic; tick counter leg | the tick counter is never written into (or restored from) the save buffer | **DEAD** ("both runs passed" — a fresh loaded world already starts at tick 0, indistinguishable from "tick never restored" until save.c is real) |

Two ids were added by name because other in-flight work already references them by
number, per the brief's own instruction: `OM_BUG_MOVE_RUBBERBAND = 1100` (E-13,
`tests/qa/t1/test_rts_detectors.py`'s local enum) and `OM_BUG_SAVE_SKIPS_RNG_STATE =
1600` (save, `tests/csim/test_E16_S111_saving.py`'s own control, already live and
already passing today).

## Module with no rule: `enemy_macro.c` (E-14)

Checked every function `csrc/ouroboros_sim.h` declares for `enemy_macro.c`. ALG-74's
one crisp numeric constant, `SCRIPT_EVAL_INTERVAL_TICKS = 40`, is exposed only by
`om_macro_evaluation_interval_ticks(void)` — no `om_world*` parameter at all. Every
`OM_BUG_*` this codebase's `om_debug_inject(om_world *w, om_bug bug)` sets is stored
on a specific world (`w->inject = (int)bug`, `csrc/sim.c:552`); a function with no
world pointer has no way to read that flag, in a correct build or a buggy one. A
control built on it could not fail on any build — the exact defect class CLAUDE.md
names ("A test that cannot fail is a defect"). Verified this generalizes: every
other candidate with a matching number either also takes no `om_world*`
(`om_macro_get_eval_interval`, `om_macro_get_speed_multiplier`,
`om_macro_eval_timer_transition`, and others) or is not grounded in algorithms.md at
all (bus flags, hook/transition plumbing — booleans, not formulas). The two
`om_world*`-taking candidates with numbers in the neighborhood
(`om_macro_get_threshold_noise` / `om_macro_get_timer_noise`, ALG-74's ±0.15 /
±0.20 noise) need a trigger point ("at mission start") and a `p1` indexing scheme
(hook id? transition id? force id?) that `signatures.toml`'s own transcription left
unresolved — the same kind of ambiguity decision 1 already flags as the design
lane's job to resolve, not something to guess inside a positive control. No id
assigned, no file written. The 1200s range stays reserved in the header comment for
whoever resolves that ambiguity.

Caught the identical problem before committing on two other picks and fixed them:
`om_mission_compute_time_limit(uint64_t B, double u)` (no `om_world*`) was swapped
for `om_mission_compute_urgency(w, region_idx, archetype)` (E-10, still ALG-55, a
different term); `om_structure_get_base_max_hp(void)` (no `om_world*`) was swapped
for reading the same constant through `om_structure_get_hud_data(w, structure,
out)->max_hp` (E-15, same fault, same numbers, a real path).

## Liveness, run for real

`scripts/specfactory/control_liveness.py`'s own scratch tree
(`ensure_scratch_tree`) mirrors only `tests/csim/{conftest.py,controls/*.py}` plus
the two `.so` files — it does not mirror
`docs/northstar/spec_factory/mvp_features.toml`, which every `world_factory` /
`dbg_world_factory` call has needed since D1 (freeze/F2, decision 4). Run exactly
as instructed, every one of these eleven controls comes back `DEAD` with
`FileNotFoundError: ... mvp_features.toml` on both sides — a pre-existing
scratch-tree gap, not a defect in these controls or these modules: the identical
run against `test_control_e05_garrison_before_damage.py` (documented live today)
gives the same `FileNotFoundError` `DEAD`. Not fixed here — `scripts/specfactory/**`
is outside this task's scope (only the `om_bug` enum block and the `OMBug` mirror
are), and touching it was never asked for. Flagged for whoever owns that file next.

With a one-off, non-committed copy of `mvp_features.toml` into the scratch tree
(diagnostic only, to confirm these eleven controls' own logic beneath that gap —
never part of the deliverable), the per-control verdicts are exactly the table
above: one `ERROR` (E-03, a real missing symbol in today's `worldgen.c` build) and
ten `DEAD` (the target function is an unconditional stub that returns the same
value whether or not `om_debug_inject` was called — expected pre-attach: nothing in
these ten modules reads `w->inject` yet). None report `LIVE`, matching the brief's
"never LIVE" requirement, though for the true reason (stub ignores injection),
not the `PENDING`/`ERROR` framing decision 7 anticipated for most of them. Recorded
as pending per decision 7's own language ("ERROR on a module not yet attached is
recorded as pending, never counted") for the one genuine `ERROR`; the ten `DEAD`
verdicts are the same kind of pending, just surfaced as "both sides agree" instead
of "collection error" because these particular stub bodies happen to compile and
link (skeleton_gen gave every declared symbol a body), unlike E-03's still-partial
config API.

## Gates run

- `scripts/specfactory/fixture_defects.py`'s three checks
  (`tick_order_reachability`, `branch_coverage_of_control`, `two_agent_confound`)
  run directly (its own CLI/`sweep()` only globs `test_control_e05_*.py` and
  `test_E05_*.py`, so it never reaches E-06 and later on its own) over all eleven
  files: **clean, zero findings** on every one.
- `scripts/specfactory/control_liveness.py`, unique `--scratch-root` per run: see
  above.
- `make -s OPT=-O2 WERROR=1 libouroboros.so libouroboros_dbg.so`: clean, no
  warnings, both libraries link, after every one of the enum edits (checked after
  each of the four extended blocks and after all eight new blocks).
- E-02 baseline (`tests/csim/test_E02_*.py`): confirmed **72 passed / 4 skipped**
  with and without this task's `csrc/ouroboros_sim.h` / `tests/csim/conftest.py`
  edits (isolated with `git stash push -- <those two files>`), proving this task
  did not move it. Not 64/4 as the brief states — this is a live, shared checkout
  (per this task's own brief: "other agents share this checkout"); commit
  `01fe6fc` ("seed the world RNG and route every draw through om_rng_draw") landed
  mid-session and added `tests/csim/test_E02_S020_rng_seeding.py` (8 more tests),
  moving the honest baseline to 72/4 before this task touched anything. A later
  pull (after this task's second commit, before push) brought in a further
  concurrent change that regresses `tests/csim/test_E02_S015_adjacency.py` (2
  failing, `assert 0.0 == pytest.approx(0.02)`) — reconfirmed with the same
  stash-isolation technique that this task's own changes are not the cause. Not
  this task's to fix (out of scope, and someone else's file mid-edit); flagged
  here so it isn't mistaken for something F5 broke.

## Naming note

None of these eleven declare a `MIRRORS` constant (docs/northstar/research/
harness_defects_2026-09-17/DECISIONS.md decision 1, "a control that mirrors a
test's detector declares that link machine-readably"). `MIRRORS` applies when a
control copies an existing test's own detector logic; none of these do — each is
an original scenario built straight from its own module's algorithms.md rule,
matching how the two live E-05 examples this task read for shape
(`test_control_e05_garrison_before_damage.py`,
`test_control_e05_agent_reads_live.py`) are themselves both undeclared originals,
not copies.

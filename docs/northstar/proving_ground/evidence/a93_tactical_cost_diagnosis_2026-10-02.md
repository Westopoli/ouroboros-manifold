# A93 part 2: why the tactical step is super-linear, what the every-20th spike is, and a proposed fix, 2026-10-02

Read and profile only on main. The prototype diff is `a93_tactical_cost_prototype.patch` (next to this file, applies to origin/main 34d04336 with `git apply`); no csrc change is committed on any branch. Scratch worktree `/home/westopoli/Projects/om-a93-diag` (not Westley's checkout). I rule on nothing; this is the proposal Addendum 32 asks for.

## Result

1. **The spike is one function, and it is quadratic by construction.** The step that crosses a 40-base-tick boundary runs `om_macro_tick`, which runs `om_macro_issue_group_orders`, whose contact check calls `om_unit_can_see` for every (enemy unit, player unit) pair until one is visible. With no contact yet it never exits early. Both id lists are capped at `OM_MACRO_ORDER_CAP` (2048), so at 4,996 units it is exactly 2048 x 2048 = 4,194,304 `om_unit_can_see` calls, 245 of the 277 ms of that step (89 percent). At 990 units it is 14.2 of 16.8 ms; at 2,501, 91.5 of 103 ms.
2. **The steady-state super-linearity is a candidate-count effect, not a call-count bug.** Every grid query visits every unit in its disc (around 200 to 2,000 rows each), and in the opening almost all of them are the querying unit's own faction, so they are scanned and rejected. Queries double with units (each ability scan runs once per unit of that type) and candidates per query grow 1.2 to 1.6 times per doubling until the disc is full, so calls grow 2.3 to 2.6 times.
3. **A faction-aware grid removes most of both.** Prototype (4 files, +161/-46 lines): the 20-step spike is gone (worst step 16 ms at 4,996 units against 346 to 490 before), the median falls 5x at 4,996 and 5x at 10,098 units, and the measured median exponent from 990 to 10,098 units is 1.15 (was about 1.55).
4. **The trace stays byte-identical.** Per-step state hash over thousands of steps, with and without combat, identical to main at every size tried; `checksum_trace` O0 == O2 with final 12966767929705903382 unchanged; tactical per-tick hash O0 == O2. No tie order changes, so no behaviour change is needed.
5. **One test pins the quadratic loop and fails by design:** `test_F3_probe_positive_control_counts_calls_while_contact_unset` asserts exactly `2 * n * n` `om_unit_can_see` calls. Any sub-quadratic fix breaks it (it is a test-defect candidate for the ledger; Westley owns the call). All other csim results are identical to main (128 red on main, the same 128 plus this one).

## Method and tools

- `perf`: still blocked (`kernel.perf_event_paranoid` is 2 here, kernel profiling disallowed); I did not touch system settings. `valgrind` is not installed. If you want perf next time, the user would have to run `sudo sysctl kernel.perf_event_paranoid=1` (or lower); I did not need it.
- Used instead: (a) `gprof` on a `-O2 -fno-inline -pg` build of all of csrc plus the harness (call arcs are reliable with inlining off; sample time is 10 ms resolution, so I used it for call counts and callers, and subtracted runs of N and N+1 steps to isolate one step); (b) a scratch-instrumented copy of csrc (not committed) with event counters and `clock_gettime` phase timers around each phase of `om_tactical_step`, around each ability type in the autotrigger scan, and around the pieces of `om_macro_issue_group_orders`. Timings from (b) are real wall time per phase, not sampled.
- Harness: the A91 harness (branch push/A91-tactical-measure, ddcc5f4f, same scenario: seed 121, 80 regions, features 0 to 7, Siege Breaking at region 0, `om_region_set` military 8.6 / 17 / 42.8 / 85 / 170 for 502 / 990 / 2,501 / 4,996 / 10,098 units), extended in scratch with a per-step state hash and an optional "fight" mode. The hash is FNV-1a over, for every unit, alive flag, x, y, target id and hp, plus `om_world_checksum`, folded per step. Fight mode teleports the player block with `om_unit_set_pos` to a chosen gap in front of the enemy block (the opening has the armies 22,000 to 23,000 wu apart, so nothing ever fights in the first thousands of steps) and gives every player unit `om_command_attack_move` at the enemy centroid.
- Build flags as the Makefile: `-O2 -fno-fast-math -ffp-contract=off -fexcess-precision=standard -msse2 -mfpmath=sse -fno-math-errno`, gcc 15.2.0, Ryzen 7 3700X. Absolute times on this box drift 10 to 25 percent between sessions (the same main build gave median 40.7 ms in A91 and 50.8 ms here at 4,996); every before/after pair below was run in the same session, back to back.

## 1. Why the grid iterator and nearest-scan call counts grow 2.3 to 2.6x per doubling

Battlefield geometry (counters from the instrumented build): the grid is 2 x 60, 3 x 60, 4 x 60 cells of 400 wu for 990, 2,501, 4,996 units; 8, 18, 32 cells are non-empty and the fullest holds 182 to 196 units. So units sit at a fixed density of about one per 816 sq wu (spacing about 29 wu) in a square block whose side grows with the square root of n (630 wu at 990 units, 1,470 wu at 4,996).

Per-step `om_grid_iter_next` calls in the opening (idle, steady state): 112,384 (502 units), 327,637 (990), 1,254,598 (2,501), 3,229,333 (4,996). Of the list nodes the iterator walks, 87, 66, 53 and 51 percent (at 502, 990, 2,501, 4,996 units) pass the distance test and are returned to the caller; the callers then reject every one of them (own faction, or nothing damaged) because the enemy block is 22,000 wu away. The calls are therefore all useful-looking, all wasted.

Who makes the calls (gprof call arcs, per step at 4,996 units; the number of queries is the count of units of that type, since each runs one scan per step):

| caller (ability, radius) | queries per step (990 / 2,501 / 4,996) | iterator calls per query (990 / 2,501 / 4,996) | share of the 4,996 step |
|---|---|---|---|
| `om_tac_nearest_enemy_within_range` (Bombard autotrigger, 1,200 wu) | 149 / 376 / 749 | 496 / 1,245 / 2,043 | 47 percent of calls, 7.3 ms |
| `om_tac_badly_damaged_friendly_within` (Warden Rally scan, 400 wu) | 347 / 874 / 1,746 | 357 / 455 / 492 | 27 percent of calls, 8.7 ms |
| `om_tactical_apply_aura_regen` (per Warden, 300 wu) | 347 / 874 / 1,746 | 247 / 279 / 291 | 16 percent of calls, 6.8 ms |
| `om_tac_enemy_category_within` (Interceptor, 350 wu) | 178 / 449 / 896 | 248 / 324 / 371 | 10 percent of calls, 3.4 ms |

Phase timers at 4,996 units, steady step: ability autotrigger 21.3 ms, aura regen 6.8, unit AI 3.4, position refresh 0.4, total 32 ms. By unit type inside the autotrigger: Warden 8.7, Bombard 7.3, Interceptor 3.4, Vanguard 1.3, Raider 0.5 ms.

The growth is the product of two things:

- **Queries double with n** (every unit of an ability type scans once a step). That alone is 2.0x.
- **Candidates per query grow with n until the query disc is full.** A disc of radius R holds min(whole army block, density x pi R^2). At the density above a full disc holds about 346 units at R=300, 471 at 350, 616 at 400 and 5,540 at 1,200. The small-radius scans are nearly saturated by 990 units (Warden Rally 357 to 492, up 1.38x over a 5x range) and the Bombard scan, at 1,200 wu, is not saturated until about 5,500 units (496 to 2,043, up 4.1x). Weighted by cost the product is 2.3 to 2.6x per doubling, matching A91.

The nearest-hostile scan (`om_tac_nearest_scan_cell`, unit AI) is the same mechanism: 4,129 cell scans per step at 990, 56,709 at 4,996 after the enemy's first orders (about 18 cells per query, each walking its whole 60 to 190 unit list), and every unit in a friendly-only cell is rejected on the faction test.

Consequence: this is output-sensitive. It only turns linear once every disc is full (about 5,500 units for the 1,200 wu scan, higher in a looser formation), and then with a large constant (hundreds of candidate rows per unit per step). That is why the fit exponent falls from 1.67 to 1.48 over the range and why 10,000 units costs about 2.3x the 5,000-unit step, not 4x, but still 114 ms on main.

## 2. The every-20th-step spike, profiled alone

Per-step timing at 4,996 units (instrumented build, ms): steady steps 31 to 32; step 19 (the first one after crossing 40 base ticks; period is 2 above 1,000 units, so one step in 20; one in 40 at or below 1,000 units) 277 ms, 294 ms on the next at step 39, 270 at step 59. Phase split of the spike step:

| phase (ms) | steady step | spike step |
|---|---|---|
| refresh positions | 0.4 | 0.4 |
| unit AI | 3.4 | 3.4 |
| aura regen | 6.8 | 6.8 |
| ability autotrigger | 20.9 | 20.8 |
| `om_macro_tick` | 0.0 | **245.4** |
| support, mission tick | 0.0 | 0.0 |

Inside `om_macro_tick`, the all-pairs `om_unit_can_see` loop in `om_macro_issue_group_orders` (csrc/enemy_macro.c, "contact now" block) is 99 percent of it; collecting the two faction lists and the hp sum are 0.05 ms. `om_macro_tick` returns early unless `has_evaluated`, which is true exactly when a 40-tick slot boundary (`OM_SCRIPT_EVAL_INTERVAL_TICKS`) is crossed, so the spike cadence is the macro's evaluation cadence and nothing else. gprof confirms the count: 4,194,304 `om_unit_can_see` calls over a 20-step run with one spike, all from this loop (2048^2: both lists hit the 2,048 cap).

Cost per call is about 58 ns at 4,996 units (get faction x2, alive, two position lookups, layer, cross-layer factor, effective radius, cover test, all before the distance compare that fails). At 2,501 units the loop is 1,276 x 1,225 = 1.56M calls, 91 ms; at 990, 507 x 483 = 245K calls, 14 ms. Above the cap the spike stops growing with n in call count (it is 2048^2 at 5,000 and at 10,000 units), but measured 440 to 510 ms at 10,098 units on main this session, so it is above 100 ms (the 10 ticks/s frame) at every size from about 2,000 units up.

The loop exits at the first visible pair, and `has_contact` is sticky and already skips the loop; so this cost exists only until the first contact (and while no enemy force unit has a player unit within its sensor radius, which in a real siege is the whole approach). The spike is therefore the approach-phase cost, not a combat cost.

## 3. Proposed change

Prototype `a93_tactical_cost_prototype.patch`, `csrc/unit.c` +182/-46, `csrc/enemy_macro.c`, `csrc/fog.c`, `csrc/om_internal.h` (internal header only; `ouroboros_sim.h` and `signatures.toml` untouched). Three parts, each exact by construction:

**A. Per-cell faction counts in the grid (data structure).** Add `fcnt[cell][4]` to `om_grid`, maintained in `om_grid_link` / `om_grid_unlink` (so it is correct through spawns, deaths and moves, the same paths that maintain `head`) and cleared in `om_grid_rebuild`. Buckets: faction -1, 0, 1, and one shared bucket for any higher id. Two uses:

- Scans that look for "a unit of another faction" skip a cell whose count of other-faction units is zero, via `om_grid_cell_has_other_faction`. Applied to `om_tac_nearest_enemy_within_range`, `om_tac_enemy_category_within`, `om_tac_hostile_within` and `om_tac_nearest_hostile`. The last already walks cells; the first three move from the iterator to the same cell walk with the same exact distance test the iterator applies, plus the cell gap prune `om_tac_nearest_hostile` already uses.
- The faction-filtered iterator (`om_grid_iter_begin_faction`) skips a cell whose count for the filter faction is zero. This is what fixes the contact check below and `om_fog_faction_sees`.

A querying unit whose faction is in the shared bucket never skips (conservative). Skipping removes only cells that cannot contain a returned or accepted unit, so every any-of, count and (distance, id) minimum is unchanged, and none of these queries depends on visit order.

**B. Damaged-unit prepass for the Warden Rally scan.** Once at the top of `om_ability_autotrigger_scan` (only when a Warden has ever spawned), count per cell the living units under the Rally hp threshold, by walking the same cell lists the iterator would. `om_tac_badly_damaged_friendly_within` then walks only cells with a non-zero count. Nothing in that scan moves a unit or lowers hp (Rally only heals), so a cell counted zero stays zero for the whole scan; the count is cleared at the end of the scan so no other caller can use a stale one.

**C. Contact check by grid instead of all pairs (the spike).** In `om_macro_issue_group_orders`, replace the nested loop with, for each force unit, a faction-filtered grid query for player units within that unit's own sensor bound (new `om_fog_observer_sensor_bound` in fog.c, a one-line export of the static bound `om_unit_acquire_target` already sizes its query with), testing `om_unit_can_see` on those candidates only. To reproduce the old pair set exactly (the old loop saw only the lowest 2,048 living ids of each side, a silent cap), the candidate must have id at most `player_ids[n_player - 1]`, and the observers are still the same truncated `force_ids`. No contact in range means no `om_unit_can_see` calls at all. The call to `om_unit_can_see` stays in enemy_macro.c, so the F3 probe's `--wrap` still counts it.

### Measured effect (same session, back to back, ms per `om_tactical_step`, 200 steps after 5 warm-up, release build)

| units | main median | main mean | main worst | prototype median | prototype mean | prototype worst |
|---|---|---|---|---|---|---|
| 502 | 1.32 | 1.41 | 8.0 | 0.45 | 0.43 | 0.7 |
| 990 | 4.2 | 4.4 | 31.7 | 1.24 | 1.22 | 1.7 |
| 2,501 | 17.4 | 23.4 | 178 | 4.4 | 4.5 | 7.1 |
| 4,996 | 50.8 | 68.3 | 493 | 10.3 | 10.2 | 16.0 |
| 10,098 | 114 | 128 | 586 | 21.4 | 21.2 | 25.8 |

Prototype rows: three repetitions each, spread under 3 percent on the median except 2,501 (4.3 to 4.4). Main rows from two repetitions earlier in the session. Spike cadence in the prototype is invisible: the worst step is 1.4 to 1.6 times the median, not 3 to 9 times.

Scaling exponent of the median (log ratio of time over log ratio of units): main 1.69, 1.55, 1.55 over the doublings 502 to 4,996; prototype 1.49, 1.36, 1.24, then 1.05 from 4,996 to 10,098 units. Overall 990 to 10,098 units: prototype 1.15. Where it is going: the residual steady cost at 4,996 units is 10.3 ms, of which aura regen is 7.5 ms (73 percent). That is the one scan the change does not touch: a Warden's aura counts own-faction units within 300 wu, and those are the units in the cell, so it is inherently (Wardens) x (units in a 300 wu disc), linear in n once discs are full, with a high constant (about 290 rows per Warden). Against E-13: 1,000 units at 1.24 to 1.6 ms is under 3 ms; 10,098 units at 21 ms is under 30 ms (both whole-step numbers, not the movement and collision subset the budget names; I still have not timed that subset).

With combat (fight mode, armies placed 300 to 900 wu apart then closing, same-session pairs): 990 units median 4.2 to 2.3 ms; 2,501 units median 16.3 to 7.0 ms; 4,996 units median 47.1 to 11.7 ms, worst step 293 to 21 ms. A different spike survives in combat at 990 units (runs of consecutive slow steps of 10 to 20 ms in unit AI, seen in the prototype at steps 59 to 62 and 119 to 125 of the 300 wu run; main shows spikes up to 22 ms there too, not profiled): gprof over those steps puts the cost in `om_unit_damage_reduction` / `om_warden_aura_reduction_for` (every shot scans every unit in 300 and 350 wu discs around the target to count Wardens and Bastions) and `om_tac_hostile_within`/`om_tac_nearest_hostile` over mixed cells. It is the same mechanism with a different caller and the same remedy class (a per-cell warden/bastion count, so a cell with none is skipped); I did not prototype it.

## 4. Does the trace stay byte-identical

Yes, as tested. Evidence (main source from `git archive HEAD`, built with the same flags, against the prototype; per-step hash of every unit's alive/x/y/target/hp plus `om_world_checksum`, compared line by line with `cmp`):

- Idle opening, no orders: 502 units 1,500 steps, 990 units 1,500, 2,501 units 600, 4,996 units 400. Identical.
- Combat (player block teleported to a gap in front of the enemy, attack-move): 502 units gap 100 for 1,200 steps; 990 units gaps 300, 1,500, 3,000 for 1,500, 1,500, 1,200 steps (gaps beyond sensor range exercise first contact appearing mid-run); 2,501 units gaps 600 and 2,000; 4,996 units gap 900 for 500 steps (321 units killed, both lists above the 2,048 cap, so the truncation rule in C is exercised). Identical, 11 cases, tens of thousands of step hashes.
- `checksum_trace` O0 vs O2 gate (`--seed 1 --regions 60 --ticks 500 --features 6`) on the prototype: `MATCH IDENTICAL (50 cadence rows, final=12966767929705903382)`. That gate runs a strategic world with no tactical units, so by itself it proves only that the strategic path is untouched; the tactical evidence is the hash runs above plus a tactical O0 build against the O2 build, per-step hash identical over 400 steps (990 units, combat).
- csim suite (tests/csim, about 1,350 tests; skip counts differed by three between the two runs, 60 against 57, not investigated): main 128 failed; prototype 129 failed, the same 128 plus `test_F3_probe_positive_control_counts_calls_while_contact_unset`, which asserts the all-pairs call count `2 * n * n` and so cannot pass any sub-quadratic contact check. The rest of that file (equivalence against a Python reference of the old computation in clash and spread scenes at 12 / 60 / 240 units, the pinned unit-state golden, and "zero calls once has_contact is set") passes. The 128 pre-existing reds include E17, E06 control and others unrelated to this change; I did not examine them.

Where exactness depends on an argument rather than a test: (1) the iterator gap prune assumes a unit's cached grid cell matches its cached position, which `om_tac_unit_sync_position` maintains and `om_tac_nearest_hostile` already relies on; (2) `om_unit_can_see` reads the live position through `om_unit_get_pos` while the grid holds the cached one, the same split `om_unit_acquire_target` lives with, and the contact check inherits it (the combat runs would diverge at first contact if it mattered; they did not. The combat timing pairs in section 3 were taken with an intermediate prototype whose contact check lived in fog.c; the final one (calls kept in enemy_macro.c) does the same work, but its timings were measured only on the idle opening); (3) factions 2 and above share a bucket, never skipped; not exercised by a test, only by reading.

If a future change did need a different trace (it does not here): the nearest-hostile tie path (`OM_TIE_SCAN_WINDOW`, falling back to `om_tac_nearest_hostile_ordered`) is the only place visit order could matter, and the prototype leaves its candidate set and order untouched.

## 5. What I could not measure, and what is rough

- **A real battle.** My combat runs are a teleported block pressing into a static enemy block: a few hundred casualties over a thousand steps, no reinforcements doing anything interesting, no player commands beyond the one attack-move. Sustained melee with thousands of moving and dying units, and the cost of kiting and fire-and-retreat orders, are not measured. The combat spike above (damage reduction scans) is real and unfixed.
- **Movement and collision alone.** Still not timed separately from the whole step (the E-13 budget names that subset). My phase timers do not separate it; it falls inside the unit AI and `om_move_sync` and `om_move_collision_once`, and in these runs unit AI is 0.4 to 3.4 ms at 4,996 units, so it is well inside budget at that size, but I did not isolate it.
- **perf and callgrind.** Neither available (perf blocked by `perf_event_paranoid`, no valgrind); gprof plus wall-clock phase timers instead. gprof's self-time column has 10 ms resolution and its caller attribution for static functions is unreliable in one place (it showed `om_tac_reserve` called 26 M times from the nearest scan, which is nonsense); I used only its call arcs for the five iterator callers, which sum to the total, and the wall-clock timers for time.
- **Pipe and JSON.** Still excluded.
- **Units above the 2,048 list cap.** The contact check's cap behaviour is preserved (for exactness) but the cap itself is a latent bug: units past 2,048 per side are invisible to contact detection. Not touched.
- **Machine noise.** One box, background load not controlled; absolute figures drift 10 to 25 percent between sessions, so only the same-session pairs should be compared.
- **Ownership.** The patch touches csrc/unit.c, fog.c, enemy_macro.c and om_internal.h; I did not check `pieces.toml` owners.
- **Not built:** the Warden/Bastion per-cell count for the combat-time damage scans, and any speed-up of aura regen (7.5 ms at 4,996 units after the fix; options are a hand-inlined cell loop without the iterator state machine, which would change cost but not results, or a per-cell Warden count that would not help it since the cost is Warden x neighbours).

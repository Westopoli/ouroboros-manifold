# Simulation lane report (2026-10-13)

Mandate: ROADMAP 2b step 1, verify the C simulation against the bible's stochastic rules and find regressions in mission choice and in the source of the chronicle. Context: `docs/northstar/plans/2026-10-12-sim-lane-context.md`. Westley's standing word: find and show first, change only what he has seen. Nothing below is fixed; every row is a proposal until he reads it.

## Status

| Part | State | Evidence |
|---|---|---|
| Sim viewer SV-0 to SV-3 | landed | SV-0 `ad4665c3` (debug-only `retention` on `mission_end`, set through `om_unit_set_hp`, Architect audit PASS); SV-1 to SV-3 earlier; `tests/simviewer` 67 pass, the total-failure pick XPASSes |
| Mission choice, 10 seeds x 6 missions | done, 13 findings | `findings/mission_choice.md` (SL-A) |
| Chronicle source, 10 seeds x 24 jumps | done, 15 findings | `findings/chronicle_source.md` (SL-B) |
| Equation tests for the 33 ALG rows no test named | done, 33 rows, 405 new tests (353 green, 52 red), 33 findings | `findings/alg_c1.md`, `alg_c2.md`, `alg_c3.md` (SL-C1, SL-C2, SL-C3) |
| Register Q- rows, F1 to F13, audit findings against the code | done (read, not run) | `findings/register_status.md` |
| ALG rows whose test only mentions the id (45 named rows) | not audited | next pass if Westley wants it |
| Fixes | none; each is a piece after Westley reads the row | |

The new `tests/csim/test_alg_*.py` files are on branches, not on main, because 52 of them are red on purpose (a real finding is never skipped or loosened): `push/simlane-c1` (186 pass, 11 red), `push/simlane-c2` (61 pass, 9 red), `push/simlane-c3` (106 pass, 32 red, 29 of them the E-17 stubs). Landing them needs the red ones listed in `lane_plays_known_red.txt`-style rows or fixed first; Westley decides.

Totals: 61 finding rows (SL-A 13, SL-B 15, SL-C1 9, SL-C2 14, SL-C3 10), plus the register status table.

## What matters most (cross-lane themes)

1. **Rulings Westley made in September that the code does not follow** (register_status.md): Q-042-01 diplomacy never initialised (`om_diplomacy_init` has no caller; all pairs hostile); Q-056-01 jump length fixed 50, clamp unused; Q-035-01 opportunist boost always x1.0 (writer `om_region_add_damage` never called); Q-057-01 home-region delta hardcoded 0.0 so rotation chance is always 0.8 (SL-C2-01 shows the same); Q-067-01 library 380 fragments, 20 pools, not 399 and 21.
2. **Inputs the rules read that nothing feeds**: mission archetype-fit `times_run` (SL-A-09), preference (SL-A-10), revolt events and recent-history windows (SL-A-07, SL-A-11), the faction event window (SL-C1-07), chronicle score terms (SL-B-08), ALG-74 noise (SL-C3-08), the jump report counters (SL-A-12).
3. **The pipe changes the sim's mission without saying so** (SL-A-01): 12 of 60 missions were not the generator's draw; Defensive Stand fires with no attack (SL-A-02); Interception can never enter the pool (SL-A-03).
4. **Chronicle source**: category matching is case-sensitive against Title Case names so three categories never occur (SL-B-01); admin revolts never fire (SL-B-07); only 33.8% of event regions reach a chronicle entry (SL-B-12, needs a ruling); lineage rotates every jump after about tick 850 (SL-B-03, cause unproven).
5. **Events engine order and chain tags**: exclusion after conditions, rolls across all regions (SL-C1-03, 04); admin and conquest chain starts write tag 0 (SL-C1-08), likely feeding the chronicle chain merge.
6. **Stubs and stale bible text**: ALG-70/71/72 are stubs in `csrc/tactical_mapgen.c` (SL-C3-05, Westley: keep or retire); ALG-62, 66, 70 text is stale against later rulings (SL-C3-02, 03, 04).

## Waiting on Westley (rulings, not fixes)

- Register: F1, F3, F4, F5, F6, F8, F10, F11, F12, F13 (structures and units leaving the map) from `register_status.md`.
- Proposed Q rows (candidates in the lane files): SL-B 7 rows (Q-SL-B-01 to 07, incl. the 2-per-category cap losing two thirds of event regions, ripple flags, chain tag semantics); SL-A Q-A1 to Q-A4; SL-C1-05 and SL-C1-07 (faction event window); SL-C2-02 (floor at exact products), -04 (supreme successor region), -06 (natural deaths per tick or per jump: Q-060-01 closed against R-060-04/ALG-45/49 and the code), -12, -14; SL-C3-01 (cooldown start), -06 (ALG-72 numbers), -10 (selector commander-pool decay).
- Keep or retire ALG-70/71/72 (stubs).
- Two tolerances chosen by a test writer, to overrule if wrong: ALG-56 half a tick; ALG-47 0.05 on a share measured over 800 seeds (`alg_c2.md`).
- Test-defect rows if the lane's findings are accepted: `test_R_130_01` encodes the loop-mode sawtooth (SL-C3-07), `test_R_087_04` is vacuous (SL-C3-02).

## Limits of the evidence

- `n_regions 60` fails `set_seed` for every seed (below the feasible minimum); all runs used 80, the client's default. The failure shows only on the next verb.
- The candidate pool is not on the wire; lane A read it through the same C symbols over ctypes (matched the pipe in 60 of 60 missions).
- Lane A campaigns were 6 missions with an inactive player, ended by tick 300: Reconquest, Suppression and long campaigns are unverified. The quiet-world fallback was never reached.
- Lane B: collisions were 0 across 113235 attacks, mission-internal events and the opening-jump scroll are unchecked, text content beyond "no digit" is unchecked.
- Lane D read the code, ran nothing.

## Reproduce

`make && make pipe/ouroboros_pipe_dbg`, then `.venv/bin/python scripts/simlane/mission_choice.py` and `scripts/simlane/chronicle_source.py` (arguments in each script header). Raw data: `findings/mission_choice_raw.json`.

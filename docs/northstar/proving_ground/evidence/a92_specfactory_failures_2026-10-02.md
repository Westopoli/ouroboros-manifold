# A92: classing the standing tests/specfactory failures (2026-10-02)

Run: `.venv/bin/python -m pytest tests/specfactory -q` on origin/main 81e0c833 in a scratch worktree (`make` done). Result: 522 passed, 1 skipped, 13 failed. Ten are the A92 list. Three more (`test_prefetch_measure.py`, 3 tests) fail only with `ModuleNotFoundError: yaml`: the borrowed `.venv` has no PyYAML. That is class (c), outside A92's ten, and probably an artefact of the borrowed venv; check where Westley normally runs the suite.

"Since" comes from `git bisect run` of the single test, or `git log -S`.

## Table

| # | Test | Class | Root cause | Since | Narrowest fix | Owner (pieces.toml) | Could the gate have caught it? |
|---|---|---|---|---|---|---|---|
| 1 | test_alg_constants::test_gen_allowlist_unaffected_by_constants_table_support | (b) stale generated artifact | `constants_allowlist.txt` still lists `csrc/sim.c:6.28318530717958647692528676655900577:1`. CONST-1 moved `OM_TWO_PI` to `om_constants.h`, so `--gen-allowlist` no longer emits it. Checked-in file is one line longer. | 48a3a0d7 (CONST-1, 2026-09-26) | `python scripts/specfactory/alg_constants.py --gen-allowlist csrc` and commit (one line removed); check `git diff`. | `docs/northstar/spec_factory/constants_allowlist.txt`, `scripts/specfactory/alg_constants.py`, the test: no piece owns them. | No. Gate step 3 runs `alg_constants --lint`, which tolerates extra stale allowlist lines. The exact-equality check lives only in `tests/specfactory`, which the gate never runs. |
| 2 | test_alg_constants::test_gen_allowlist_entries_new_format_matches_checked_in_file | (b) | Same one stale line, same assertion as #1. | 48a3a0d7 | Same regeneration fixes both. | same | same |
| 3 | test_card_lint::test_fuel_report_real_register_holds_r_039_05_not_205a | (c) environment dependency | Reads `~/Projects/agora/queue/205a-e05-collision-lottery.md`. Agora has parked it: it is now `agora/queue/parked/205a-e05-collision-lottery.md.hold` (mtime 2026-09-21 23:03; `agora-push/queue/` has an identical copy). Passes only while the card sits in a live Agora queue. | Card parked 2026-09-21, the day the test was written (eaf748d9). | Make it hermetic: copy the card (identical to the parked file) to `tests/specfactory/fixtures/205a-e05-collision-lottery.md` and point the test at it. Assertions stay as they are. | `tests/specfactory/test_card_lint.py`: unowned | No: suite not in the gate, and the result depends on another project's live checkout. |
| 4 | test_conftest_bindings::test_every_mappable_table_row_has_one_declaration_and_one_binding | (b) stale generated artifact | `om_mission_last_region` and `om_mission_refresh_context` have 0 bindings in conftest. The A2 contract piece added the declarations and table rows but did not run `--emit`. | c5ff2085 (A2 contract, 2026-09-30) | Re-run `sig_table.py --emit` after the table fixes in the A68 note below (adds both bindings). | `tests/csim/conftest.py`: unowned (generated region mirrors the table). Header and `signatures.toml`: piece `A2-contract` (also `core` owns the header). | No. Gate 5a checks only BLOCKED rows; no gate step runs `sig_table.py --check`; the contract piece has `acceptance = []`. |
| 5 | test_conftest_bindings::test_regeneration_reproduces_committed_files_and_leaves_legacy_blocks_untouched | (b) compounded with (e) | Header and conftest are not byte-equal to what `--emit` regenerates from the table. See "Why the header and conftest are stale". | e597ec3f (W-1c, 2026-09-26), widened since | Table fix then `--emit`, as in the note. | same as #4 | No (as #4). |
| 6 | test_reach_lint::test_real_repo_head_lists_om_mission_eval_commander_fate | (a) stale test | The test is a live-repo positive control: it asserts reach_lint flags `om_mission_eval_commander_fate` as unreachable. The gap is closed: `om_mission_end` now calls it (`csrc/mission.c:1579`), so the lint correctly stops flagging it. The detector works; the control was consumed by the fix. | 6518a6a5 (B7, 2026-10-01) | Replace the live-HEAD assertion with the synthetic-repo fixture pattern already in the file (a defined, tested, never-called symbol in a temp repo). Keep the name-based read-exemption point on the synthetic symbol. | `tests/specfactory/test_reach_lint.py`: unowned | N/A: closing the gap is the wanted outcome. The flaw was tying a positive control to repo state. |
| 7 | test_signatures_internal::test_every_om_internal_prototype_is_found | (a) stale test, with (e) | `EXPECTED_MODULE` lists the 2026-09-22 `om_internal.h` prototypes. The header now has 15 more: `om_events_install_save_hooks`, `om_faction_tech_multipliers_recalc`, `om_fog_faction_sees`, `om_generational_install_save_hooks`, `om_grid_iter_begin`, `om_grid_iter_begin_faction`, `om_grid_iter_next`, `om_grid_query_circle`, `om_grid_query_circle_faction`, `om_mission_on_begin`, `om_mission_reset_started`, `om_mission_tactical_tick`, `om_support_tick`, `om_tac_unit_sync_position`, `om_unit_clear_target`. Each was added by a build piece with no table row and no test update. | 16c1174a (2026-09-24) bisect; the rest added through 2026-09-28 | Add 15 `[[symbols]]` rows with `internal = true`, module = defining .c file, and extend `EXPECTED_MODULE` (the test's own message says this). | `csrc/om_internal.h`: `core` (M0). `signatures.toml`: `A2-contract` lane. Test: unowned. | No. Header-only additions pass every gate step, and the exact-set check is in the unrun suite. (Not verified: whether the symbol-ownership lint reads `om_internal.h` prototypes at all.) |
| 8 | test_signatures_internal::test_every_om_internal_function_has_an_internal_ownership_row | (a)/(e) same root | The same 15 names have no `[[symbols]]` row. | same | Same 15 rows as #7. | same | same |
| 9 | test_signatures_internal::test_real_project_sig_table_check_is_clean | (b) | `sig_table.py --check` exits 1 because header and conftest are stale (cause as #5). The 5 RENAMED lines are informational and do not set the exit code. | e597ec3f | Same table fix plus `--emit` as #5. | same as #4 | No. |
| 10 | test_snapshot_fixture::test_checked_in_fixture_matches_current_generator_output | (b) stale generated artifact | Fixture `snapshot_seed1_tick10.json` (seed 1, 80 regions, 10 ticks) was last rewritten 2026-09-24. Sim behaviour has moved: checksum 9459460945690250679 now regenerates as 3249135613753059850; 37 of 80 regions differ (e.g. `economy 37.05 -> 37.07`). Generation is deterministic (two runs byte-identical), so this is drift, not nondeterminism. | c50ac4c9 (2026-09-24) bisect: a test-only commit that rewrote the fixture; it has drifted again since. It was also regenerated on 09-22 (9dd790bf). | `python scripts/specfactory/snapshot_fixture.py --seed 1 --regions 80 --ticks 10 --generate --out tests/transport/fixtures/snapshot_seed1_tick10.json`. Regeneration changes owned regions from 51 to 65 (edges 88, factions 15 unchanged). Consumers `tests/test_c_bridge.gd`, `test_galaxy_view.gd`, `test_chronicle_scroll.gd`, `tests/transport/test_pipe_shapes.py` load it; `tests/test_era_library_live.gd`, `tests/qa/desktop/test_galaxy_pixels.py`, `tests/transport/test_pipe_chronicle_replay_fields.py` mention 51. Check each for a hard-coded 51 first. Durable fix (a policy call for Westley): compare structure rather than bytes, or regenerate in the same commit as any sim change. | Fixture dir covered only as `transport` acceptance (no owns row); `snapshot_fixture.py` and the test: unowned. | Partly. Gate step 9 runs `tests/transport` (the consumers), but the byte-equality check is only in `tests/specfactory`, so every economy-shifting sim change turns it red silently. |

## Note: why the header and conftest are stale (the A68 finding)

`sig_table.py --check` reports:

```
stale: csrc/ouroboros_sim.h, tests/csim/conftest.py
RENAMED params (5; fix the table):
  om_enemy_production_adapt_target: param 1 'byref' -> p1, param 2 'byref' -> p2
  om_enemy_production_select_category: param 1 'byref' -> p1
  om_map_instantiate_zone_pos: param 3 'int' -> p3
  om_mission_setup_extraction_point: param 3 'c_double' -> p3
```

**RENAMED (5).** These rows have been in the table since the F1 freeze (6c0233fd, 2026-09-22). Their param names were inferred from test call sites (`byref`, `int`, `c_double`) instead of being real names. C rejects a repeated name in one declaration, and `int` is a keyword, so `sanitize_param_names` renames them to `p<index>` on emit and reports it. The header already carries the renamed form. It is cosmetic and does not set the exit code. Fix: give those five params real names in `signatures.toml` (positional-only rows, no kwargs); the header follows on `--emit`.

**Stale header.** The committed header differs from the emitted one in four ways, all inside `generated from signatures.toml` blocks that are meant to be machine-owned.

1. Hand-written doc comments inside generated blocks (A53, B6, G-C3, B9-N, HDR4, A3 and others). Emit regenerates comments from table `note` fields, so it drops them.
2. `om_macro_set_force_fallback_point` (B13-8) and `om_mission_has_ended` (B9-N) are declared in the header with no table row.
3. `#define OM_CHRON_MENTION_FACTION/REGION` (A53) sit inside the `structs` generated block.
4. `om_chronicle_has_mission_consequence_flag` sits in a different module block than the table's `module = "generational.c"` would emit.

**Stale conftest.** The two A2 bindings are missing (#4). Several bindings were hand-placed in a different `_bind_eNN` group than `--emit` picks (it uses the lowest epic naming the symbol): `om_mission_get_enemy_faction` (W-1c, e597ec3f, the first commit after which `--check` was never clean again), `om_time_jump_*ownership*`, `om_chronicle_mention_*`, `om_chronicle_get_keyframe`, and others. Dry-run `--emit` in a scratch copy also types `om_chronicle_get_keyframe` `tick_out` as `P(c_uint64)` where the hand edit used `V`.

Root cause for the cluster is class (e), a harness gap, not (d). Contract pieces edit the generated regions by hand, the table does not follow, and nothing re-runs `--check`. The header is the real contract and compiles; the artifacts are out of step with their generator.

**Narrowest fix.** One contract-owner piece, in this order:

1. Add table rows for `om_macro_set_force_fallback_point` and `om_mission_has_ended`.
2. Move the doc comments into the rows' `note` fields.
3. Move the two `OM_CHRON_MENTION_*` defines out of the generated block.
4. Add the 15 internal rows from #7.
5. Rename the five params.
6. Run `sig_table.py --emit`, confirm `--check` is clean, and review the header diff (should be comments and ordering only).

Per CLAUDE.md a change to `ouroboros_sim.h` is its own contract piece with a pieces.toml row. `A2-contract` and `core` both own the header; ordering is by `depends_on`, so a new row is needed. `tests/csim/conftest.py` is unowned and purely generated, so the new piece should own it.

## Class totals

(a) stale test or test-defect: #6, plus #7 and #8 in part. (b) stale generated artifact: #1, #2, #4, #5, #9, #10. (c) environment dependency: #3 (plus `yaml` for prefetch_measure). (d) real defect in code or contract: none found. (e) harness or lint gap: part of #4, #5, #7, #8, #9, and the reason none of the ten was caught.

## Why the gate saw none of it

`merge_gate.sh` runs csim and qa/t1 through `suite_regression`, piece acceptance ids, and `tests/transport`. It never runs `tests/specfactory`, and it has no `sig_table.py --check` step (5a checks BLOCKED rows only). No piece owns the specfactory test directory, so no piece's acceptance includes it. A policy call to close this: add `pytest tests/specfactory` (excluding `test_prefetch_measure.py` until PyYAML is present) and `sig_table.py --check` as gate steps once the suite is green; otherwise it goes red again at the next sim change.

## Not done

No code, test or generated artifact was edited and nothing was regenerated in the repo. The fixes are predicted from reading the generators, plus dry-run `--emit` and `--gen-allowlist` and snapshot generation in scratch space to see the differences.

# Code quality page (SHOWCASE-quality-audit, step 4)

Measured on the worktree branch from origin/main at `0d7868f2`, 2026-10-23. Read-only audit: nothing was fixed. Every number below came from a command run on this tree; where a count is a heuristic, the section says so.

**Discount the legacy paths.** The legacy moves (SHOWCASE-junk, SHOWCASE-legacy-toys, SHOWCASE-legacy-scenes, SHOWCASE-docs-legacy) have not landed. These paths are still in the tree and will move or go: `build/_pyi_dist`, `.swarm/backups`, `tuning_output/*.jsonl`, `graphify-out/` (junk, deleted); `simulation/` (legacy Python sim, to `legacy/simulation/`); `toys/`; `scenes/debug/` and the unreferenced `scenes/mockups/*` (to `legacy/`); `docs/legacy/claude_exchange`, `docs/legacy/random`, `docs/legacy/blender_stuff`, `docs/legacy/design_questions`, `docs/stage_specs`, `docs/test_specs`, the loose `docs/design_lane*.md` / `research_lane*.md` files and part of `docs/research` (to `docs/legacy/`). This page audits `csrc/`, `autoload/`, `scenes/`, `scripts/specfactory/`, `scripts/skilllab/` and `tests/`, none of which move, except `scenes/debug/` and `scenes/mockups/` (flagged where they matter) and `docs/stage_specs` (one comment points into it, see 2.4).

## 1. `csrc/` (the C sim)

| Measure | Value |
|---|---|
| Files | 50 (`*.c` and `*.h`, including 5 files under `csrc/pipe/`) |
| Lines | 39,821 (largest: `mission.c` 3,509, `tactical_move.c` 3,865, `unit.c` 3,428, `chronicle.c` 2,499) |
| Functions with a body | about 1,750 (approximate: a regex brace-matcher, no C parser; `ctags` and `cloc` are not installed) |
| Functions over 150 lines | 16 |
| TODO / FIXME / XXX | 0 |
| `__attribute__((weak))` stubs | 9, all in `csrc/region.c` |
| Public symbols tested but not reachable from the game (`reach_lint.py`) | 250 of 779 tested public symbols |

**Dead or unreachable (reach_lint).** `python3 scripts/specfactory/reach_lint.py` run bare exits 1: "REACH LINT FAILED (250 unreachable of 779 tested public symbols)". It checks public `csrc/ouroboros_sim.h` symbols that a test calls against a static call graph from `om_world_step`, `om_tactical_step`, the time-jump entry and the pipe dispatch loop. None of the 250 is in `reach_allowlist.toml`. By prefix: chronicle 33, map 28, unit 27, mission 22, macro 17, faction 10, tactical 9, structure 9. The full list with header line, definition file:line and first test is the appendix at the end. Caveats: the lint's own text says it is a regression-mode lint when given `--base-ref`; the bare run counts the whole baseline. Many of these are getters and setters for tests (`om_unit_hp`, `om_trace_read`, `om_world_set_seed`), so the finding is "tested API the running game never calls", not 250 proven-dead bodies. Some are real gaps of the kind the lint exists for, for example `om_unit_attack` (`csrc/unit.c`) and `om_time_jump_start_tick` (`csrc/generational.c`); each needs a per-symbol look.

**Weak stubs (listed as stubs).** `csrc/region.c:250` `om_world_generate`; `:354` `om_world_step`; `:355` `om_world_run`; `:356` `om_region_drift`; `:357` `om_world_checksum`; `:358` `om_trace_enable`; `:359` `om_trace_len`; `:360` `om_trace_read`; `:362` `om_debug_inject` (under `#ifdef OM_DEBUG_INJECT`). Every one has a strong definition today (`csrc/sim.c` for eight, `csrc/worldgen.c` for `om_world_generate`), so the stubs are shadowed. The comments say "delete this stub after attach/B4" (`region.c:249`) and "when sim.c lands (card 201), its strong definitions override these" (`region.c:351-353`); both pieces are long attached. These are dead code that looks live, with stale comments.

**Functions over 150 lines** (file:line, name, lines): `csrc/pipe/pipe_tactical.c:299` write_tactical 365; `csrc/sim.c:194` om_world_step 359; `csrc/save.c:474` sv_parse_body 327; `csrc/worldgen.c:181` om_world_generate 272; `csrc/resolve.c:328` om_step_resolve 256; `csrc/pipe/om_pipe.c:521` write_delta 241; `csrc/unit.c:2035` om_tac_unit_ai 223; `csrc/space_plates.c:338` sp_layer 209; `csrc/generational.c:1948` gen_time_jump 209; `csrc/agent.c:248` om_step_decisions 209; `csrc/save.c:277` sv_write_body 186; `csrc/agent.c:47` om_faction_candidates 179; `csrc/region.c:13` om_world_new 169; `csrc/events.c:670` evt_resolve_queue 162; `csrc/pipe/om_pipe.c:359` write_snapshot 157; `csrc/pipe/om_pipe.c:1210` handle_mission_start 155. Several of these are the stochastic equations kept verbatim from the legacy algorithms by design (`docs/bible/algorithms.md`); the serializers (`write_*`, `sv_*`) are long because they are field lists.

**Other.** `csrc/unit.c:997` cites `simulation/movement.py` (the legacy Python sim, which will move to `legacy/simulation/`); the comment will need the new path. `csrc/ouroboros_sim.h` is 2,167 lines, the frozen contract.

## 2. `autoload/` and `scenes/` (GDScript)

| Measure | `autoload/` | `scenes/` |
|---|---|---|
| `.gd` files | 32 | 189 (86 under `scenes/mockups/`) |
| `.gd` lines | 4,732 | 42,591 (22,586 under `scenes/mockups/`) |
| `.tscn` files | 0 | 51 |
| Files over 600 lines | 1 | 11 |
| TODO / FIXME / XXX | 0 | 0 |
| Unreferenced files | 0 | 1 script, 9 scenes (+9 scripts only their own scene uses) |

**2.1 Unreferenced.** Method: for each `.gd`, grep its basename (and its `class_name`) over `scenes`, `autoload`, `project.godot` and `tests`, excluding itself. This is generous: any mention counts, so it under-reports. Result: one script, `scenes/mockups/objectives/tools/dump_nodes.gd` (21 lines). Stricter, by `.tscn`: nine scenes under `scenes/debug/` have no referrer in `scenes`, `autoload`, `project.godot`, `tests` or `scripts`: `debug_ws_test`, `test_chronicle_scroll`, `test_faction_info_panel`, `test_faction_palette`, `test_info_panel_host`, `test_region_info_panel`, `test_time_jump`, `test_world_view`, `wave2_visual_check` (the nine `.tscn`, each with its own `.gd`, 1,328 script lines, which only that scene loads). They are named `test_*` but are not tests (the suites live under `tests/`), so they read as live. They are in the legacy-scenes move. `scripts/specfactory/gd_reach_lint.py` (regression mode, reads git refs) is the gate's version of this check; this page did not run it.

**2.2 Over 600 lines** (`wc -l`): `scenes/mockups/landscape/field_map_space.gd` 1,520; `scenes/tactical_c/tactical_view.gd` 1,356; `scenes/mockups/landscape/placer.gd` 1,020; `scenes/mockups/landscape/field_map.gd` 961; `scenes/mockups/landscape/hud.gd` 920; `scenes/mission_briefing/mission_briefing.gd` 911; `scenes/shared/world_view/main_menu_galaxy.gd` 824; `scenes/mockups/landscape/pass4_terrain.gd` 798; `autoload/c_bridge.gd` 784; `scenes/world/time_jump_sequencer.gd` 707; `scenes/galaxy/galaxy_view.gd` 663; `scenes/mockups/settlement/settlement_sim.gd` 633. Six of twelve are prototypes under `scenes/mockups/`. Shipping-code outliers: `tactical_view.gd` and `c_bridge.gd` (the pipe client).

**2.3 TODO / FIXME.** None in `autoload/` or `scenes/`.

**2.4 Comments that name something gone.** 43 `See also` comments in GDScript; all path-like targets were tested for existence. Stale:
- `autoload/debug_overlay.gd:5` points at `docs/stage_specs/stage_13_spec.md`; the file is now `docs/stage_specs/_deferred/stage_13_spec.md`, and the whole folder is queued for `docs/legacy/`. High (stale claim in a live comment).
- `scenes/galaxy/shell_renderer.gd:6` says "See also: scenes/galaxy/legacy_shell_renderer.gd (superseded one box per faction)"; that file does not exist. High.
- Not stale, noted: `scenes/tactical_c/loading_overlay.gd:2` names a deleted legacy file but gives the `git show` ref that recovers it; `tests/test_legacy_tactical_deleted.gd:93` is a deliberate positive control.
Ruling and piece ids in comments (`R-`, `TD-`, `FINDING-`, `DRAFT-`) were not checked against `pieces.toml` one by one; only path targets were. Approximate.

## 3. `scripts/specfactory/` and `scripts/skilllab/` (Python)

| Measure | `specfactory/` | `skilllab/` |
|---|---|---|
| `.py` files | 47 (one in a fixtures subfolder) | 44 |
| Lines | 14,980 | 8,101 |
| Files over 800 lines | 3 | 0 |
| TODO / FIXME | 9 matches, all in template text | 0 |
| Modules nothing imports | 21 by strict import grep, 6 by any mention | 0 (the package is imported through `__main__`) |

**3.1 Over 800 lines:** `scripts/specfactory/merge_gate_support.py` 1,174; `escalator_fix_probe.py` 1,099; `alg_constants.py` 971.

**3.2 Modules nothing imports.** Strict method (`import <name>` or `from <name>` in `scripts/` or `tests/`): 21 under `scripts/specfactory/`. Nearly all are command-line tools run by path (each has a `__main__` guard and is cited in docs, the gate or a script), so "not imported" is expected: `libm_lint`, `size_lint`, `method_check`, `rule_pins`, `rule_pins_tests`, `gd_reach_lint`, `card_slice`, `tactical_trace`, `chain_graph`, `snapshot_fixture`, `gen_controls`, `gen_test_skeleton`, `gen_card`, `card_regen`, and `escalator_fix_fixtures/test_px17_scratch_r7d.py` (a scratch test under a fixtures dir, cited once). The weaker finding: six modules have no mention at all in `scripts`, `tests`, `Makefile`, `.claude` or `pieces.toml`, only in docs: `gen_all_cards.py` (217 lines, cited in 2 docs), `dor_check.py` (134), `fill_tests.py` (103), `draft_card.py` (126), `draft_e2e.py` (78), `fold_answers.py` (149). They belong to the retired card factory (Agora era) and are likely dead; each needs a look before it is called so. Medium.

**3.3 TODO.** The 9 matches are strings that generators write into card and test templates (`gen_card.py:78`, `gen_controls.py:58`, `draft_card.py:71`), not open work.

**3.4 Duplicated helper names** (same top-level `def` in two or more files; excludes `main`, `__init__`, `test_*`): 57 names. 16 of them involve `scripts/skilllab/contract.py`, which is by design a stub file of cross-module signatures (its docstring says so), so they are not duplication. The rest are real in the sense of copied helpers: `_page` in four files (`skilllab/depth.py:210`, `charts.py:63`, `batches.py:391`, `search_batch.py:343`); `grid` in four (`sample.py:47`, `search_batch.py:45`, `sweep.py:110`, `contract.py`); `_check` three (`sample.py:9`, `asym.py:77`, `positions.py:15`); `_run` three; `_play` three; `run_pytest` three (`specfactory/escalator_fix_probe.py:399`, `suite_regression.py:147`, `red_check.py:93`); `python_bin` two (`undertest_check.py:45`, `red_check.py:51`); `parse_junit` two (`control_liveness.py:253`, `red_check.py:107`); `find_function_span` two (`reach_lint.py:194`, `card_lint.py:68`); `load_allowlist` two (`reach_lint.py:330`, `alg_constants.py:862`); `build_owner_map` two (`chain_sim.py:84`, `tick_closure.py:158`); `load_cards` two (`parent_patch_fence.py:159`, `chain_sim.py:415`); `parse_card` two (`green_check.py:35`, `prefetch_measure.py:229`). The full list was produced by an `ast` scan of top-level functions. Many `skilllab` one-letter-ish private helpers (`_mean`, `_num`, `_cell`) are small. Medium.

**3.5 Portability.** `scripts/specfactory/merge_gate.sh` (the `PYTHON=` default) hard-codes `/home/westopoli/Projects/agora/.venv/bin/python`; ten files under `scripts/`, `csrc/`, `autoload/` and `scenes/` contain `/home/westopoli`. A reader cloning the repo cannot run the gate without editing it. Medium.

## 4. `tests/`

| Suite | Test files (`test_*.py` / `*.gd`) | Lines (py + gd, all files) |
|---|---|---|
| `tests/csim/` (C sim through ctypes, incl. `controls/` and `scale/`) | 471 | 72,885 |
| `tests/skilllab/` | 179 | 38,971 |
| `tests/specfactory/` | 60 | 18,575 |
| `tests/transport/` | 56 | 9,494 |
| `tests/qa/` (desktop-driver plays) | 31 | 7,795 |
| `tests/simviewer/` | 4 | 1,314 |
| `tests/net/` | 4 | 478 |
| `tests/long/`, `tests/push/` | 1 + 1 | 256 + 20 |
| `tests/*.gd` (Godot, flat in `tests/`) | 150 `test_*` files (includes 2 `.py`) | not counted |
| `tests/galaxy_field/`, `tests/support/`, `tests/fixtures/` | helpers and fixtures | 255, 253, 0 |

1,121 files in all. About 6,479 `def test_*` in Python and 123 `func test_*` / `_test_*` in GDScript (regex count, approximate; the Godot tests run many checks per function).

**Files with no `S-`/`R-` id.** Heuristic: no `S-###`, `R-###-##` (or the `S###` filename form) in the first 40 lines or the filename. Of 957 test files checked, 412 name none. By suite: `csim` 156 of 471; flat `tests/*.gd` 40 of 150; `qa` 6 of 31; `transport` 15 of 56; `specfactory` 46 of 60; `skilllab` 145 of 179; `simviewer` 3 of 4; `push` 1 of 1. The tooling suites (`specfactory`, `skilllab`, `transport`) test scripts, not stories, so no id is expected there. The `csim` and `tests/*.gd` rows are the ones that matter against "each names the S-/R- id it proves"; many of those key on piece ids instead (`test_VG_W_w1_perf_control.py`, `test_E07_wiring.py`, `test_PP_*`, `test_core_*`), so the rule is met by another id, not by an `S-`/`R-` id. 130 of the 412 are under `controls/` or `scale/` (`csim`) names.

**Files over 400 assertion lines.** None. The most assertion-dense: `tests/skilllab/test_report.py` 293, `test_sweep.py` 288, `test_diagram.py` 170, `tests/specfactory/test_spec_provenance.py` 150. By total length, 92 test files exceed 400 lines (the largest are `tests/skilllab/test_report.py` 1,773 and `test_sweep.py` 1,272). Assertion lines were counted by regex (`assert`, `_assert(`, `expect`); approximate. TODO-word matches in tests: 185, not classified (many are generator output).

## 5. The method machinery as a reader sees it

- **`scripts/specfactory/merge_gate.sh`** (695 lines): one `GATE <step> OK|REJECT|WARN|HARNESS` line per step, base first (candidate must contain current origin/main), then build, lint and regression stages. Step names in the script include `base`, `venv`, `make`, `libm_lint`, `alg_constants`, `footprint`, `owner_lint`, `reach_lint`, `gd_reach`, `gd_class_names`, `size_lint`, `rule_pins`, `sig_check`, `symbol_ownership`, `control_liveness`, `acceptance`, `regression_csim`, `regression_qa_t1`, `playthrough`, `look`, `checksum_trace`, `tactical_trace`, `transport`, `lane_plays`. Order not verified step by step.
- **`pre_gate.sh`** (181 lines): five steps before any push: noise (`.uid`/`.import` hygiene), gate in `--revert` mode, named tests, rule pins, spec provenance.
- **`status_check.py`** (323 lines): diffs the programme lane table, `pieces.toml` and the review queue against git; run after every landing.
- **`owner_lint.py`** (98 lines): fails when two in-flight pieces own the same file, per `pieces.toml`.
- **`method_check.py`** (271 lines): reads a chat's transcript and prints per rule how many turns broke it (DRIFT lines).
- **Known-red lists:** `gd_tests_known_red.txt` 25 lines, `lane_plays_known_red.txt` 4, `playthrough_known_red.txt` 5 (34 in all, line counts include comments).
- **`docs/northstar/plans/push/pieces.toml`:** 296 `[[piece]]` tables. `state =` counts: 151 attached, 97 queued, 3 superseded, 2 in_flight, 1 landed, 1 pending (255 rows carry a state; the other 41 were not classified by this page).
- **Ledger** `docs/northstar/plans/push_ledger_2026-09-22.md`: 1,531 lines, about 1,500 table rows (counted by leading `|`, which includes header and separator lines).
- **Decisions page** `docs/northstar/story_reviews/westley/decisions.md`: 38 `DEC-` rows (2026-10-22 onward).

## 6. Closing table

Severity: high = dead code that looks live or a stale claim in a live comment; medium = size, duplication, tested-only API; low = TODOs. Counts are findings (a finding can name many files), not lines.

| Directory | Lines | Files | High | Medium | Low | Takeaway |
|---|---|---|---|---|---|---|
| `csrc/` | 39,821 | 50 | 1 (9 shadowed weak stubs with stale comments) | 2 (16 functions over 150 lines; 250 tested-only public symbols) | 0 | A clean, TODO-free sim whose main debts are leftover bootstrap stubs and a long list of test-only API that needs a per-symbol wired-or-removed call. |
| `autoload/` | 4,732 | 32 | 1 (`debug_overlay.gd:5` stale path) | 1 (`c_bridge.gd` 784 lines) | 0 | Small and referenced; one stale comment. |
| `scenes/` | 42,591 | 189 | 3 (9 unreferenced debug scenes; `dump_nodes.gd`; `shell_renderer.gd:6` stale target) | 1 (11 files over 600 lines, six of them prototypes) | 0 | The shipped scenes are referenced and TODO-free; the mockups and debug scenes are where the dead weight sits, and they are moving to `legacy/`. |
| `scripts/specfactory/` | 14,980 | 47 | 0 | 4 (3 files over 800; 6 likely-dead card-factory tools; duplicated helpers; hard-coded venv path) | 0 open (9 template strings) | A working gate and lint toolkit with some retired factory tools still sitting beside it. |
| `scripts/skilllab/` | 8,101 | 44 | 0 | 1 (copied private helpers across modules) | 0 | Cohesive lab package; duplication is small helpers, and `contract.py` duplicates by design. |
| `tests/` | 1,121 files, about 150,000 lines of py and gd (flat `tests/*.gd` not counted) | 1,121 | 0 | 2 (412 files with no S-/R- id by heuristic, mostly tooling suites; 92 files over 400 lines) | 185 TODO-word matches, unclassified | The tests are the spec in volume (about 6,600 test functions); id traceability holds for story tests and is looser for tooling suites. |

## Appendix: the 250 tested-but-unreachable public symbols

Source: `python3 scripts/specfactory/reach_lint.py` output on this tree, none allowlisted. Header line is the declaration in `csrc/ouroboros_sim.h`; definition is file:line of the body (grep-resolved).

| symbol | header line | definition | first test that calls it |
|---|---|---|---|
| `om_abi_layout_check` | ouroboros_sim.h:126 | csrc/sim.c:630 | csim/test_E02_S020_abi.py |
| `om_abi_version` | ouroboros_sim.h:28 | csrc/region.c:347 | csim/conftest.py |
| `om_campaign_needs_onboarding` | ouroboros_sim.h:1631 | csrc/generational.c:1021 | csim/test_E08_S063_my_two_choices_at_the_start.py |
| `om_character_create` | ouroboros_sim.h:1647 | csrc/generational.c:1095 | csim/scale/test_scale_E08.py |
| `om_character_create_child` | ouroboros_sim.h:1648 | csrc/generational.c:1109 | csim/test_E08_S058_previous_pool_chapter_ago.py |
| `om_character_create_random` | ouroboros_sim.h:1649 | csrc/generational.c:1130 | csim/test_E08_S060_named_leaders_live_and_die.py |
| `om_character_create_with_rank` | ouroboros_sim.h:1650 | csrc/generational.c:1145 | csim/test_E08_S060_named_leaders_live_and_die.py |
| `om_character_faction` | ouroboros_sim.h:1651 | csrc/generational.c:1165 | csim/test_E08_S058_who_i_come_back_as.py |
| `om_character_lineage_id` | ouroboros_sim.h:1658 | csrc/generational.c:1217 | csim/test_E08_S058_previous_pool_chapter_ago.py |
| `om_character_name_reuse_cooldown` | ouroboros_sim.h:1659 | csrc/generational.c:1222 | csim/test_E08_S058_who_i_come_back_as.py |
| `om_character_set_faction` | ouroboros_sim.h:1666 | csrc/generational.c:1365 | csim/scale/test_scale_E08.py |
| `om_character_set_generation` | ouroboros_sim.h:1667 | csrc/generational.c:1370 | csim/test_E08_S059_the_family_grows_while_i_am_away.py |
| `om_chronicle_add_cluster_direct` | ouroboros_sim.h:1396 | csrc/chronicle.c:1967 | csim/test_E09_S065_five_to_ten_entries_in_the_right_order.py |
| `om_chronicle_add_mock_entry` | ouroboros_sim.h:1400 | csrc/chronicle.c:1993 | csim/test_E09_S069_jump_replay_ownership.py |
| `om_chronicle_add_raw_entry` | ouroboros_sim.h:1402 | csrc/chronicle.c:2014 | csim/test_E09_S068_written_from_fragments_never_the_same_twice.py |
| `om_chronicle_apply_slot_echo_anaphora` | ouroboros_sim.h:1404 | csrc/chronicle.c:2025 | csim/test_E09_S068_written_from_fragments_never_the_same_twice.py |
| `om_chronicle_apply_word_echo_synonym` | ouroboros_sim.h:1405 | csrc/chronicle.c:2036 | csim/test_E09_S068_written_from_fragments_never_the_same_twice.py |
| `om_chronicle_assemble_cluster_entry` | ouroboros_sim.h:1406 | csrc/chronicle.c:2044 | csim/test_E09_S068_written_from_fragments_never_the_same_twice.py |
| `om_chronicle_calculate_score` | ouroboros_sim.h:1410 | csrc/chronicle.c:2096 | csim/test_E09_S066_what_counts_as_notable.py |
| `om_chronicle_category_name` | ouroboros_sim.h:1414 | csrc/chronicle.c:2121 | csim/test_E09_B5_consequence_entry.py |
| `om_chronicle_context_multiplier` | ouroboros_sim.h:1416 | csrc/chronicle.c:2130 | csim/test_E09_S066_what_counts_as_notable.py |
| `om_chronicle_count_by_type` | ouroboros_sim.h:1417 | csrc/chronicle.c:2136 | csim/test_E09_S065_five_to_ten_entries_in_the_right_order.py |
| `om_chronicle_dedup_content_words` | ouroboros_sim.h:1418 | csrc/chronicle.c:2146 | csim/test_E09_S068_written_from_fragments_never_the_same_twice.py |
| `om_chronicle_dismiss_expanded` | ouroboros_sim.h:1419 | csrc/chronicle.c:2172 | csim/test_E09_S069_watching_history_happen.py |
| `om_chronicle_distill_and_assemble` | ouroboros_sim.h:1420 | csrc/chronicle.c:2177 | csim/scale/test_scale_E08.py |
| `om_chronicle_fragment_batch_exceeds_rejection_limit` | ouroboros_sim.h:1424 | csrc/chronicle.c:2197 | csim/test_E09_S071_the_fragment_library_contract.py |
| `om_chronicle_fragment_check_near_duplicate` | ouroboros_sim.h:1426 | csrc/chronicle.c:2208 | csim/test_E09_S071_the_fragment_library_contract.py |
| `om_chronicle_fragment_inject_invalid_slot` | ouroboros_sim.h:1427 | csrc/chronicle.c:2214 | csim/test_E09_S071_the_fragment_library_contract.py |
| `om_chronicle_fragment_library_load_launch` | ouroboros_sim.h:1428 | csrc/chronicle.c:2222 | csim/test_E09_S071_the_fragment_library_contract.py |
| `om_chronicle_fragment_library_validate` | ouroboros_sim.h:1429 | csrc/chronicle.c:2227 | csim/test_E09_S071_the_fragment_library_contract.py |
| `om_chronicle_fragment_pool_counts` | ouroboros_sim.h:1430 | csrc/chronicle.c:2235 | csim/test_E09_S071_the_fragment_library_contract.py |
| `om_chronicle_handle_click` | ouroboros_sim.h:1434 | csrc/chronicle.c:2290 | csim/test_E09_S069_watching_history_happen.py |
| `om_chronicle_mock_populate_events` | ouroboros_sim.h:1445 | csrc/chronicle.c:2344 | csim/test_E09_S065_five_to_ten_entries_in_the_right_order.py |
| `om_chronicle_presentation_entry_hold_sec` | ouroboros_sim.h:1446 | csrc/chronicle.c:2359 | csim/test_E09_S069_watching_history_happen.py |
| `om_chronicle_presentation_map_width_ratio` | ouroboros_sim.h:1447 | csrc/chronicle.c:2364 | csim/test_E09_S069_watching_history_happen.py |
| `om_chronicle_presentation_slide_in_sec` | ouroboros_sim.h:1448 | csrc/chronicle.c:2369 | csim/test_E09_S069_watching_history_happen.py |
| `om_chronicle_presentation_slide_out_sec` | ouroboros_sim.h:1449 | csrc/chronicle.c:2374 | csim/test_E09_S069_watching_history_happen.py |
| `om_chronicle_presentation_word_cadence_sec` | ouroboros_sim.h:1450 | csrc/chronicle.c:2379 | csim/test_E09_S069_watching_history_happen.py |
| `om_chronicle_presentation_word_fade_sec` | ouroboros_sim.h:1451 | csrc/chronicle.c:2384 | csim/test_E09_S069_watching_history_happen.py |
| `om_chronicle_render_character_rank` | ouroboros_sim.h:1453 | csrc/chronicle.c:2394 | csim/test_E09_S070_my_family_is_always_in_the_story.py |
| `om_chronicle_render_region_mention` | ouroboros_sim.h:1454 | csrc/chronicle.c:2400 | csim/test_E09_GC2_mentions.py |
| `om_chronicle_score_base` | ouroboros_sim.h:1456 | csrc/chronicle.c:2411 | csim/controls/test_control_e09_window_significance_cap_skipped.py |
| `om_chronicle_select_clusters` | ouroboros_sim.h:1458 | csrc/chronicle.c:2424 | csim/test_E09_S065_five_to_ten_entries_in_the_right_order.py |
| `om_chronicle_set_entry_state` | ouroboros_sim.h:1460 | csrc/chronicle.c:2439 | csim/test_E09_S069_watching_history_happen.py |
| `om_chronicle_validate_event_template_prose` | ouroboros_sim.h:1461 | csrc/chronicle.c:2445 | csim/test_E09_S071_the_fragment_library_contract.py |
| `om_client_snapshot_read` | ouroboros_sim.h:1587 | csrc/fog.c:840 | csim/test_E12_S089_i_see_what_my_units_see.py |
| `om_collision_pass` | ouroboros_sim.h:1952 | csrc/tactical_move.c:2689 | csim/test_E13_S097_around_not_through.py |
| `om_command_direct_move` | ouroboros_sim.h:1955 | csrc/tactical_move.c:2781 | csim/test_E13_S097_around_not_through.py |
| `om_command_issue_named` | ouroboros_sim.h:1957 | csrc/tactical_move.c:2870 | csim/test_E13_S096_four_commands.py |
| `om_command_queue_attack_move` | ouroboros_sim.h:1960 | csrc/tactical_move.c:2904 | csim/test_E13_S096_four_commands.py |
| `om_command_queue_move` | ouroboros_sim.h:1961 | csrc/tactical_move.c:2913 | csim/scale/test_PP_tables.py |
| `om_diplomacy_init` | ouroboros_sim.h:1480 | csrc/diplomacy.c:408 | csim/test_E06_S042_three_ways_to_feel_about_a_neighbor.py |
| `om_enemy_production_adapt_target` | ouroboros_sim.h:2005 | csrc/tactical_support.c:440 | csim/test_E15_S128_what_the_enemy_builds.py |
| `om_enemy_production_select_category` | ouroboros_sim.h:2006 | csrc/tactical_support.c:411 | csim/test_E15_S128_what_the_enemy_builds.py |
| `om_era_elevation_damage_bonus_enabled` | ouroboros_sim.h:2092 | csrc/unit.c:2428 | csim/test_E11_S084_flat_damage.py |
| `om_event_noise` | ouroboros_sim.h:643 | csrc/events.c:422 | csim/controls/test_control_e04_noise_rerolled.py |
| `om_event_roll_noise` | ouroboros_sim.h:641 | csrc/events.c:409 | csim/controls/test_control_e04_noise_rerolled.py |
| `om_event_set_noise` | ouroboros_sim.h:642 | csrc/events.c:416 | csim/conftest.py |
| `om_event_template_chronicle_prose` | ouroboros_sim.h:1462 | csrc/chronicle.c:2454 | csim/test_E09_S071_the_fragment_library_contract.py |
| `om_event_template_get` | ouroboros_sim.h:634 | csrc/events.c:383 | csim/conftest.py |
| `om_events_load` | ouroboros_sim.h:632 | csrc/events.c:183 | csim/conftest.py |
| `om_faction_confidence` | ouroboros_sim.h:319 | csrc/faction.c:173 | csim/test_E02_S020_rng_seeding.py |
| `om_faction_cooperative_since` | ouroboros_sim.h:1484 | csrc/diplomacy.c:474 | csim/test_E06_S043_peace_grows_out_of_quiet.py |
| `om_faction_create_named` | ouroboros_sim.h:1674 | csrc/generational.c:1418 | csim/test_E08_S060_named_leaders_live_and_die.py |
| `om_faction_mark_conquered_this_tick` | ouroboros_sim.h:1742 | csrc/lifecycle.c:352 | csim/test_E07_S051_nations_that_never_were.py |
| `om_faction_next_mission_unit_tier` | ouroboros_sim.h:1487 | csrc/diplomacy.c:757 | csim/test_E06_S048_three_tiers_of_technology.py |
| `om_faction_phase` | ouroboros_sim.h:1743 | csrc/lifecycle.c:461 | csim/test_E07_S053_every_faction_has_an_age.py |
| `om_faction_set_event_window_counts` | ouroboros_sim.h:1746 | csrc/lifecycle.c:384 | csim/test_E07_S053_every_faction_has_an_age.py |
| `om_faction_tech_economy` | ouroboros_sim.h:1493 | csrc/diplomacy.c:559 | csim/test_E06_S046_archetypes_spend_tech_differently.py |
| `om_faction_template` | ouroboros_sim.h:813 | csrc/worldgen.c:525 | csim/conftest.py |
| `om_faction_tier_transition_candidate` | ouroboros_sim.h:1496 | csrc/diplomacy.c:820 | csim/test_E06_S048_three_tiers_of_technology.py |
| `om_fairness_evaluate` | ouroboros_sim.h:1880 | csrc/tactical_mapgen.c:289 | csim/test_E17_S117_fair_enough.py |
| `om_fairness_force_score` | ouroboros_sim.h:1881 | csrc/tactical_mapgen.c:294 | csim/test_E17_S117_fair_enough.py |
| `om_fairness_run_post_generation_check` | ouroboros_sim.h:1883 | csrc/tactical_mapgen.c:305 | csim/test_E17_S117_fair_enough.py |
| `om_force_set_surviving_units` | ouroboros_sim.h:1678 | csrc/generational.c:1451 | csim/test_E08_S064_what_carries_over.py |
| `om_gen_set_extra_edge_ratio` | ouroboros_sim.h:777 | csrc/worldgen.c:467 | csim/conftest.py |
| `om_gen_set_extra_edges_enabled` | ouroboros_sim.h:794 | csrc/worldgen.c:490 | csim/conftest.py |
| `om_gen_set_home_range` | ouroboros_sim.h:800 | csrc/worldgen.c:496 | csim/conftest.py |
| `om_gen_set_player_preference` | ouroboros_sim.h:781 | csrc/worldgen.c:473 | csim/conftest.py |
| `om_gen_set_preference_weight` | ouroboros_sim.h:787 | csrc/worldgen.c:484 | csim/conftest.py |
| `om_gen_set_region_range` | ouroboros_sim.h:775 | csrc/worldgen.c:454 | csim/conftest.py |
| `om_gradient_add_moving_source` | ouroboros_sim.h:1884 | csrc/tactical_mapgen.c:310 | csim/test_E17_S118_the_battlefield_moves.py |
| `om_gradient_combine_overlap` | ouroboros_sim.h:1885 | csrc/tactical_mapgen.c:315 | csim/test_E17_S114_texture_from_gradients.py |
| `om_gradient_sample_single` | ouroboros_sim.h:1888 | csrc/tactical_mapgen.c:333 | csim/test_E17_S114_texture_from_gradients.py |
| `om_hazard_sample_interference` | ouroboros_sim.h:2010 | csrc/tactical_support.c:975 | csim/test_E15_S130_the_battlefield_moves.py |
| `om_hazard_spawn_moving_interference` | ouroboros_sim.h:2011 | csrc/tactical_support.c:956 | csim/test_E15_S130_the_battlefield_moves.py |
| `om_ledger_commander_death_outcome_band` | ouroboros_sim.h:1679 | csrc/generational.c:1457 | csim/test_E08_S061_when_my_commander_dies.py |
| `om_ledger_commander_death_region` | ouroboros_sim.h:1680 | csrc/generational.c:1465 | csim/test_E08_S061_when_my_commander_dies.py |
| `om_lineage_create` | ouroboros_sim.h:1683 | csrc/generational.c:1473 | csim/scale/test_scale_E08.py |
| `om_lineage_record_history_region` | ouroboros_sim.h:1690 | csrc/generational.c:1511 | csim/test_E08_S057_stay_with_the_family_or_move_on.py |
| `om_lineage_spawn_descendant_at_tick` | ouroboros_sim.h:1692 | csrc/generational.c:1522 | csim/test_E08_S059_the_family_grows_while_i_am_away.py |
| `om_lineage_spawn_single_descendant` | ouroboros_sim.h:1693 | csrc/generational.c:1527 | csim/test_E08_S059_the_family_grows_while_i_am_away.py |
| `om_macro_bind_hook_flag` | ouroboros_sim.h:1521 | csrc/enemy_macro.c:293 | csim/test_E14_S122_forces_that_notice_each_other.py |
| `om_macro_bus_register_vocab` | ouroboros_sim.h:1524 | csrc/enemy_macro.c:322 | csim/test_E14_S122_forces_that_notice_each_other.py |
| `om_macro_eval_hook_flag` | ouroboros_sim.h:1527 | csrc/enemy_macro.c:346 | csim/test_E14_S122_forces_that_notice_each_other.py |
| `om_macro_eval_timer_transition` | ouroboros_sim.h:1528 | csrc/enemy_macro.c:357 | csim/test_E14_S121_timers_and_thresholds_with_noise.py |
| `om_macro_evaluation_interval_ticks` | ouroboros_sim.h:959 | csrc/enemy_macro.c:371 | csim/scale/test_scale_E14.py |
| `om_macro_issues_illegal_command` | ouroboros_sim.h:1543 | csrc/enemy_macro.c:650 | csim/test_E14_S123_the_enemy_replays_like_i_do.py |
| `om_macro_mutates_unit_stats` | ouroboros_sim.h:1544 | csrc/enemy_macro.c:657 | csim/test_E14_S123_the_enemy_replays_like_i_do.py |
| `om_macro_reads_player_visibility_set` | ouroboros_sim.h:1546 | csrc/enemy_macro.c:668 | csim/test_E14_S123_the_enemy_replays_like_i_do.py |
| `om_macro_resolve_conflict` | ouroboros_sim.h:1547 | csrc/enemy_macro.c:674 | csim/test_E14_S121_timers_and_thresholds_with_noise.py |
| `om_macro_resolve_conflict_types` | ouroboros_sim.h:1548 | csrc/enemy_macro.c:680 | csim/test_E14_S121_timers_and_thresholds_with_noise.py |
| `om_macro_set_base_transition_true` | ouroboros_sim.h:1549 | csrc/enemy_macro.c:686 | csim/test_E14_S120_B1_1_tick_runs_transitions.py |
| `om_macro_set_force_hp_pct` | ouroboros_sim.h:1551 | csrc/enemy_macro.c:701 | csim/test_E14_S122_forces_that_notice_each_other.py |
| `om_macro_set_hook_true` | ouroboros_sim.h:1552 | csrc/enemy_macro.c:707 | csim/test_E14_S120_B1_1_tick_runs_transitions.py |
| `om_macro_set_state` | ouroboros_sim.h:1553 | csrc/enemy_macro.c:713 | csim/test_E14_S120_B1_1_tick_runs_transitions.py |
| `om_macro_validate_bus_flag` | ouroboros_sim.h:1557 | csrc/enemy_macro.c:826 | csim/test_E14_S122_forces_that_notice_each_other.py |
| `om_macro_validate_condition_name` | ouroboros_sim.h:1558 | csrc/enemy_macro.c:835 | csim/test_E14_S121_timers_and_thresholds_with_noise.py |
| `om_macro_validate_state` | ouroboros_sim.h:1559 | csrc/enemy_macro.c:849 | csim/test_E14_S120_five_behaviors_three_moods.py |
| `om_map_add_hazard_zone` | ouroboros_sim.h:1590 | csrc/fog.c:526 | csim/test_E12_S092_recon_then_fog.py |
| `om_map_add_interference_zone` | ouroboros_sim.h:1591 | csrc/fog.c:532 | csim/controls/test_control_e12_window_interference_ignores_intensity.py |
| `om_map_add_layer_restriction_zone` | ouroboros_sim.h:1890 | csrc/tactical_mapgen.c:352 | csim/test_E17_S114_texture_from_gradients.py |
| `om_map_add_moving_interference_zone` | ouroboros_sim.h:1592 | csrc/fog.c:541 | csim/test_E12_S090_hiding_in_the_storm.py |
| `om_map_add_obstacle` | ouroboros_sim.h:1891 | csrc/tactical_mapgen.c:387 | csim/parity/baseline/baseline_fights.py |
| `om_map_add_structure` | ouroboros_sim.h:1894 | csrc/tactical_mapgen.c:378 | csim/controls/test_control_e15_window_structure_max_hp_wrong_constant.py |
| `om_map_add_vantage_node` | ouroboros_sim.h:1593 | csrc/fog.c:553 | csim/scale/test_PP_tables.py |
| `om_map_check_boundary_gradient_discontinuity` | ouroboros_sim.h:1896 | csrc/tactical_mapgen.c:406 | csim/test_E17_S119_terrain_that_reads_like_a_place.py |
| `om_map_clamp_flavoring_delta` | ouroboros_sim.h:1897 | csrc/tactical_mapgen.c:412 | csim/test_E17_S115_the_region_shapes_the_terrain.py |
| `om_map_compute_chokepoint_width` | ouroboros_sim.h:1899 | csrc/tactical_mapgen.c:418 | csim/test_E17_S113_nine_kinds_of_place.py |
| `om_map_compute_economy_obstacle_delta` | ouroboros_sim.h:1900 | csrc/tactical_mapgen.c:424 | csim/test_E17_S115_the_region_shapes_the_terrain.py |
| `om_map_compute_modified_canvas` | ouroboros_sim.h:1901 | csrc/tactical_mapgen.c:435 | csim/test_E17_S116_canvas.py |
| `om_map_compute_tension_cover_delta` | ouroboros_sim.h:1902 | csrc/tactical_mapgen.c:451 | csim/test_E17_S115_the_region_shapes_the_terrain.py |
| `om_map_count_distinct_routes_staging_to_objective` | ouroboros_sim.h:1903 | csrc/tactical_mapgen.c:457 | csim/test_E17_S112_bones_from_the_library.py |
| `om_map_flavoring_stability_multiplier` | ouroboros_sim.h:1907 | csrc/tactical_mapgen.c:489 | csim/test_E17_S115_the_region_shapes_the_terrain.py |
| `om_map_generate` | ouroboros_sim.h:1908 | csrc/tactical_mapgen.c:495 | csim/scale/test_scale_E17.py |
| `om_map_generate_gradients` | ouroboros_sim.h:1909 | csrc/tactical_mapgen.c:500 | csim/test_E17_S114_texture_from_gradients.py |
| `om_map_generate_spine` | ouroboros_sim.h:1910 | csrc/tactical_mapgen.c:505 | csim/test_E17_S112_bones_from_the_library.py |
| `om_map_instantiate_zone_pos` | ouroboros_sim.h:1921 | csrc/tactical_mapgen.c:585 | csim/test_E17_S112_bones_from_the_library.py |
| `om_map_layout_check_hazard_approaches` | ouroboros_sim.h:1925 | csrc/tactical_mapgen.c:608 | csim/test_E17_S117_fair_enough.py |
| `om_map_layout_check_vantage_reachability` | ouroboros_sim.h:1926 | csrc/tactical_mapgen.c:614 | csim/test_E17_S117_fair_enough.py |
| `om_map_layout_matches_archetype_filter` | ouroboros_sim.h:1929 | csrc/tactical_mapgen.c:632 | csim/test_E17_S112_bones_from_the_library.py |
| `om_map_library_total_layouts` | ouroboros_sim.h:1930 | csrc/tactical_mapgen.c:638 | csim/test_E17_S112_bones_from_the_library.py |
| `om_map_sample_layer_accessibility` | ouroboros_sim.h:1933 | csrc/tactical_mapgen.c:678 | csim/scale/test_scale_E01.py |
| `om_map_select_layout_uniform` | ouroboros_sim.h:1935 | csrc/tactical_mapgen.c:774 | csim/test_E17_S112_bones_from_the_library.py |
| `om_map_set_simulation_coupling` | ouroboros_sim.h:1936 | csrc/tactical_mapgen.c:780 | csim/test_E17_S115_the_region_shapes_the_terrain.py |
| `om_map_setup_drifting_node` | ouroboros_sim.h:1937 | csrc/tactical_mapgen.c:785 | csim/test_E17_S118_the_battlefield_moves.py |
| `om_map_verify_flank_connections` | ouroboros_sim.h:1938 | csrc/tactical_mapgen.c:790 | csim/test_E17_S112_bones_from_the_library.py |
| `om_mission_apply_target_adjacent_player` | ouroboros_sim.h:1764 | csrc/mission.c:1018 | csim/test_E10_S078_a_battle_becomes_history.py |
| `om_mission_can_edit_loadout` | ouroboros_sim.h:1769 | csrc/mission.c:1174 | csim/test_E10_S079_orders_not_menus.py |
| `om_mission_check_extraction_objectives` | ouroboros_sim.h:2012 | csrc/tactical_support.c:1114 | csim/test_E15_S129_units_that_cannot_fight.py |
| `om_mission_compute_parity` | ouroboros_sim.h:1778 | csrc/mission.c:1392 | csim/test_E10_S080_difficulty_is_scarcity_not_stronger_enemies.py |
| `om_mission_compute_reinforcement_capacity` | ouroboros_sim.h:2013 | csrc/tactical_support.c:487 | csim/test_VG_E_e7.py |
| `om_mission_eval_destroy_targets` | ouroboros_sim.h:1786 | csrc/mission.c:1562 | csim/test_E10_S075_hold_destroy_escort_survive_eliminate.py |
| `om_mission_eval_escort` | ouroboros_sim.h:1788 | csrc/mission.c:1582 | csim/test_E10_S075_hold_destroy_escort_survive_eliminate.py |
| `om_mission_eval_survive` | ouroboros_sim.h:1790 | csrc/mission.c:1606 | csim/test_E10_S075_hold_destroy_escort_survive_eliminate.py |
| `om_mission_fallback_archetype` | ouroboros_sim.h:1791 | csrc/mission.c:1618 | csim/test_E10_S072_orders_come_from_where_the_world_hurts.py |
| `om_mission_init_seed` | ouroboros_sim.h:1565 | csrc/enemy_macro.c:1010 | csim/test_E14_S123_the_enemy_replays_like_i_do.py |
| `om_mission_inject_candidate` | ouroboros_sim.h:1820 | csrc/mission.c:1976 | csim/test_E10_S072_orders_come_from_where_the_world_hurts.py |
| `om_mission_select_layout` | ouroboros_sim.h:1829 | csrc/mission.c:2127 | csim/test_E10_S073_ten_kinds_of_trouble.py |
| `om_mission_set_archetype_profile` | ouroboros_sim.h:1830 | csrc/mission.c:2135 | csim/test_E10_S073_ten_kinds_of_trouble.py |
| `om_mission_set_external_reinforcement` | ouroboros_sim.h:1568 | csrc/enemy_macro.c:1038 | csim/test_E14_S124_rare_surprises.py |
| `om_mission_set_player_units` | ouroboros_sim.h:1835 | csrc/mission.c:2176 | csim/test_E10_S074_you_get_what_the_civilization_can_spare.py |
| `om_mission_set_preference` | ouroboros_sim.h:1836 | csrc/mission.c:2184 | csim/test_E10_S072_orders_come_from_where_the_world_hurts.py |
| `om_mission_set_revolt_events` | ouroboros_sim.h:1837 | csrc/mission.c:2191 | csim/controls/test_control_e10_window_urgency_deficit_divisor_wrong.py |
| `om_mission_setup_destroy_targets` | ouroboros_sim.h:1839 | csrc/mission.c:2884 | csim/test_E10_S075_hold_destroy_escort_survive_eliminate.py |
| `om_mission_setup_escort` | ouroboros_sim.h:1841 | csrc/mission.c:2902 | csim/test_E10_S075_hold_destroy_escort_survive_eliminate.py |
| `om_mission_setup_extraction_point` | ouroboros_sim.h:2017 | csrc/tactical_support.c:1102 | csim/test_E15_S129_units_that_cannot_fight.py |
| `om_mission_setup_survive` | ouroboros_sim.h:1844 | csrc/mission.c:2921 | csim/test_E10_S075_hold_destroy_escort_survive_eliminate.py |
| `om_mission_unit_tier` | ouroboros_sim.h:1499 | csrc/diplomacy.c:773 | csim/test_E06_S048_three_tiers_of_technology.py |
| `om_navmesh_find_path` | ouroboros_sim.h:1964 | csrc/tactical_move.c:2949 | csim/scale/test_PP_budgets.py |
| `om_objective_setup_drifting` | ouroboros_sim.h:2018 | csrc/tactical_support.c:824 | csim/test_E15_S130_the_battlefield_moves.py |
| `om_onboarding_load_from_slot` | ouroboros_sim.h:1698 | csrc/generational.c:1606 | csim/test_E08_S063_my_two_choices_at_the_start.py |
| `om_onboarding_save_to_slot` | ouroboros_sim.h:1699 | csrc/generational.c:1613 | csim/test_E08_S063_my_two_choices_at_the_start.py |
| `om_onboarding_update_choices` | ouroboros_sim.h:1700 | csrc/generational.c:1620 | csim/test_E08_S063_my_two_choices_at_the_start.py |
| `om_onboarding_validate` | ouroboros_sim.h:1701 | csrc/generational.c:1626 | csim/test_E08_S063_my_two_choices_at_the_start.py |
| `om_player_can_see` | ouroboros_sim.h:1599 | csrc/fog.c:601 | csim/test_E01_S162_ping_refused_on_ground.py |
| `om_player_can_see_friendly` | ouroboros_sim.h:1600 | csrc/fog.c:605 | csim/test_E12_S089_i_see_what_my_units_see.py |
| `om_player_faction_collapsed` | ouroboros_sim.h:1747 | csrc/lifecycle.c:393 | csim/test_E07_S052_no_plot_armor.py |
| `om_player_faction_record_reassignment` | ouroboros_sim.h:1706 | csrc/generational.c:1716 | csim/test_E08_S062_when_my_civilization_falls.py |
| `om_proc_arch_resolve_section_piece` | ouroboros_sim.h:1939 | csrc/tactical_mapgen.c:796 | csim/test_E17_S119_terrain_that_reads_like_a_place.py |
| `om_progression_supports_era_unlocks` | ouroboros_sim.h:1710 | csrc/generational.c:1755 | csim/test_E08_S064_what_carries_over.py |
| `om_region_assign_regional_commander` | ouroboros_sim.h:1711 | csrc/generational.c:1760 | csim/test_E08_S060_named_leaders_live_and_die.py |
| `om_region_drift` | ouroboros_sim.h:180 | csrc/sim.c:562 | csim/conftest.py |
| `om_render_detect_repeated_tile_boundary` | ouroboros_sim.h:1941 | csrc/tactical_mapgen.c:808 | csim/test_E17_S119_terrain_that_reads_like_a_place.py |
| `om_renderer_interpolate_facing` | ouroboros_sim.h:1969 | csrc/tactical_move.c:2987 | csim/test_E13_S101_movement_that_reads.py |
| `om_renderer_interpolate_position` | ouroboros_sim.h:1970 | csrc/tactical_move.c:2999 | csim/test_E13_S101_movement_that_reads.py |
| `om_roster_register_custom_unit` | ouroboros_sim.h:2093 | csrc/unit.c:2434 | csim/parity/parity_c.py |
| `om_selector_clear_pools` | ouroboros_sim.h:1716 | csrc/generational.c:1788 | csim/test_E08_S058_who_i_come_back_as.py |
| `om_selector_resolve_fallback_pool` | ouroboros_sim.h:1721 | csrc/generational.c:1847 | csim/test_E08_S058_who_i_come_back_as.py |
| `om_session_capture_enable` | ouroboros_sim.h:1572 | csrc/enemy_macro.c:1079 | csim/test_E14_S125_how_hard_the_enemy_tries.py |
| `om_session_capture_read` | ouroboros_sim.h:1575 | csrc/enemy_macro.c:1094 | csim/test_E14_S125_how_hard_the_enemy_tries.py |
| `om_set_era_flag` | ouroboros_sim.h:1607 | csrc/fog.c:647 | csim/test_E12_S091_standing_high.py |
| `om_set_era_name` | ouroboros_sim.h:1608 | csrc/fog.c:661 | csim/test_E12_S091_standing_high.py |
| `om_set_neighbors` | ouroboros_sim.h:1853 | csrc/mission.c:3054 | csim/test_E09_B5_consequence_entry.py |
| `om_strategic_agent_read_region_field` | ouroboros_sim.h:1609 | csrc/fog.c:680 | csim/test_E12_S093_fog_is_for_the_player_not_the_engine.py |
| `om_structure_apply_damage` | ouroboros_sim.h:2023 | csrc/tactical_support.c:691 | csim/test_E15_S127_taking_a_garrison.py |
| `om_structure_init_drifting` | ouroboros_sim.h:2037 | csrc/tactical_support.c:792 | csim/test_E15_S130_the_battlefield_moves.py |
| `om_structure_set_capture_progress` | ouroboros_sim.h:2043 | csrc/tactical_support.c:639 | csim/test_E15_S127_taking_a_garrison.py |
| `om_structure_set_capturing_faction` | ouroboros_sim.h:2044 | csrc/tactical_support.c:631 | csim/scale/test_scale_E15.py |
| `om_structure_set_contested` | ouroboros_sim.h:2045 | csrc/tactical_support.c:635 | csim/test_E15_S127_taking_a_garrison.py |
| `om_structure_set_timer` | ouroboros_sim.h:2048 | csrc/tactical_support.c:527 | csim/test_E15_S126_most_of_my_force_is_out_there.py |
| `om_structure_switch_unit_type` | ouroboros_sim.h:2049 | csrc/tactical_support.c:515 | csim/test_E15_S126_most_of_my_force_is_out_there.py |
| `om_structure_tick_capture` | ouroboros_sim.h:2050 | csrc/tactical_support.c:687 | csim/scale/test_scale_E15.py |
| `om_structure_unit_cost` | ouroboros_sim.h:2052 | csrc/tactical_support.c:588 | csim/test_E15_S126_most_of_my_force_is_out_there.py |
| `om_tactical_disable_abilities` | ouroboros_sim.h:2095 | csrc/unit.c:2478 | csim/parity/baseline/baseline_fights.py |
| `om_tactical_run` | ouroboros_sim.h:2097 | csrc/unit.c:2516 | csim/test_E11_S081_three_categories_a_soft_triangle.py |
| `om_tactical_run_until_eliminated` | ouroboros_sim.h:2098 | csrc/unit.c:2528 | csim/test_E11_S081_three_categories_a_soft_triangle.py |
| `om_tactical_run_until_engagement_ends` | ouroboros_sim.h:2099 | csrc/unit.c:2545 | csim/test_E11_S086_one_ability_each.py |
| `om_tactical_spawn_force_composition` | ouroboros_sim.h:2100 | csrc/unit.c:2572 | csim/test_E11_S085_long_enough_to_think.py |
| `om_tactical_target_validation_runs_every_tick` | ouroboros_sim.h:2101 | csrc/unit.c:2607 | csim/test_E11_S087_every_unit_thinks_the_same_way.py |
| `om_tactical_telegraph_active` | ouroboros_sim.h:2102 | csrc/unit.c:2612 | csim/test_E11_S086_one_ability_each.py |
| `om_tactical_tick_to` | ouroboros_sim.h:2106 | csrc/unit.c:2628 | csim/test_E14_S120_B1_2_patrol_waypoint_loop.py |
| `om_tactical_zone_visible_to_enemy` | ouroboros_sim.h:2107 | csrc/unit.c:2644 | csim/test_E11_S086_one_ability_each.py |
| `om_tick_absorptions` | ouroboros_sim.h:1750 | csrc/lifecycle.c:401 | csim/test_E07_S051_nations_that_never_were.py |
| `om_tick_reversions` | ouroboros_sim.h:1751 | csrc/lifecycle.c:409 | csim/test_E07_S050_old_loyalties.py |
| `om_tick_revolts` | ouroboros_sim.h:1752 | csrc/lifecycle.c:417 | csim/test_E07_S049_a_revolt_can_birth_a_nation.py |
| `om_ticker_pop_message` | ouroboros_sim.h:2053 | csrc/tactical_support.c:736 | csim/test_E15_S127_taking_a_garrison.py |
| `om_tier_transition_candidate_exists` | ouroboros_sim.h:1502 | csrc/diplomacy.c:824 | csim/test_E06_S048_three_tiers_of_technology.py |
| `om_time_jump_choose_length` | ouroboros_sim.h:1724 | csrc/generational.c:1874 | csim/controls/test_control_e08_window_time_jump_clamp_skipped.py |
| `om_time_jump_death_processing_tick` | ouroboros_sim.h:1727 | csrc/generational.c:1898 | csim/test_E08_S056_decades_pass_while_i_am_gone.py |
| `om_time_jump_interrupt` | ouroboros_sim.h:1729 | csrc/generational.c:1903 | csim/test_E08_S056_decades_pass_while_i_am_gone.py |
| `om_time_jump_lineage_generation_tick` | ouroboros_sim.h:1730 | csrc/generational.c:1908 | csim/test_E08_S056_decades_pass_while_i_am_gone.py |
| `om_time_jump_run_tracked` | ouroboros_sim.h:1734 | csrc/generational.c:2174 | csim/test_E08_S060_named_leaders_live_and_die.py |
| `om_time_jump_start_tick` | ouroboros_sim.h:1735 | csrc/generational.c:2179 | csim/test_E08_S055_one_commander_one_mission_then_the_world_moves.py |
| `om_trace_enable` | ouroboros_sim.h:202 | csrc/sim.c:572 | csim/controls/test_control_osc_as_level.py |
| `om_trace_len` | ouroboros_sim.h:203 | csrc/sim.c:577 | csim/controls/test_control_osc_as_level.py |
| `om_trace_read` | ouroboros_sim.h:205 | csrc/sim.c:581 | csim/controls/test_control_osc_as_level.py |
| `om_unit_ability_active` | ouroboros_sim.h:2109 | csrc/unit.c:2649 | csim/test_E11_S086_one_ability_each.py |
| `om_unit_acquire_target` | ouroboros_sim.h:1610 | csrc/fog.c:687 | csim/test_E12_S093_fog_is_for_the_player_not_the_engine.py |
| `om_unit_apply_trait_modifier` | ouroboros_sim.h:2112 | csrc/unit.c:2664 | csim/test_E11_S083_stats_traits_ability.py |
| `om_unit_attack` | ouroboros_sim.h:2113 | csrc/unit.c:2673 | csim/test_E12_S091_standing_high.py |
| `om_unit_can_return_fire` | ouroboros_sim.h:2054 | csrc/tactical_support.c:1057 | csim/test_E15_S129_units_that_cannot_fight.py |
| `om_unit_compute_terrain_speed` | ouroboros_sim.h:1976 | csrc/tactical_move.c:3082 | csim/test_E13_S097_around_not_through.py |
| `om_unit_deal_damage` | ouroboros_sim.h:2117 | csrc/unit.c:2726 | csim/test_E11_S081_three_categories_a_soft_triangle.py |
| `om_unit_hp` | ouroboros_sim.h:2126 | csrc/unit.c:2839 | csim/test_E11_S081_three_categories_a_soft_triangle.py |
| `om_unit_in_backswing` | ouroboros_sim.h:2128 | csrc/unit.c:2843 | csim/test_E11_S084_flat_damage.py |
| `om_unit_in_flinch` | ouroboros_sim.h:2129 | csrc/unit.c:2848 | csim/test_E11_S087_every_unit_thinks_the_same_way.py |
| `om_unit_order_hold_node` | ouroboros_sim.h:1944 | csrc/tactical_mapgen.c:820 | csim/test_E17_S118_the_battlefield_moves.py |
| `om_unit_profile_dps` | ouroboros_sim.h:2139 | csrc/unit.c:2911 | csim/test_E11_S084_flat_damage.py |
| `om_unit_render_silhouette_size` | ouroboros_sim.h:2146 | csrc/unit.c:2954 | csim/test_E11_S088_reading_units_on_screen.py |
| `om_unit_set_ability_cooldown` | ouroboros_sim.h:2147 | csrc/unit.c:2964 | csim/test_E11_S086_one_ability_each.py |
| `om_unit_set_brace_active` | ouroboros_sim.h:2148 | csrc/unit.c:2969 | csim/controls/test_control_e11_window_brace_reduction_wrong_constant.py |
| `om_unit_set_facing` | ouroboros_sim.h:1985 | csrc/tactical_move.c:3191 | csim/test_E13_S100_facing.py |
| `om_unit_set_fortify_active` | ouroboros_sim.h:2150 | csrc/unit.c:2979 | csim/test_E11_S084_flat_damage.py |
| `om_unit_set_stealth` | ouroboros_sim.h:2152 | csrc/unit.c:2992 | csim/test_E11_S087_every_unit_thinks_the_same_way.py |
| `om_unit_set_visible_to_faction` | ouroboros_sim.h:1987 | csrc/tactical_move.c:3220 | csim/test_E13_S096_four_commands.py |
| `om_unit_set_warden_aura_active` | ouroboros_sim.h:2153 | csrc/unit.c:2997 | csim/test_E11_S084_flat_damage.py |
| `om_unit_spawn_combat` | ouroboros_sim.h:2155 | csrc/unit.c:3006 | csim/test_E15_S129_units_that_cannot_fight.py |
| `om_unit_spawn_for_category` | ouroboros_sim.h:2156 | csrc/unit.c:3010 | csim/test_E11_S081_three_categories_a_soft_triangle.py |
| `om_unit_spawn_non_combat` | ouroboros_sim.h:2060 | csrc/tactical_support.c:1041 | csim/test_E15_S129_units_that_cannot_fight.py |
| `om_unit_spawn_with_elevation` | ouroboros_sim.h:1614 | csrc/fog.c:800 | csim/scale/test_PP_tables.py |
| `om_unit_targeting_cohort` | ouroboros_sim.h:2158 | csrc/unit.c:3026 | csim/test_E11_S087_every_unit_thinks_the_same_way.py |
| `om_unit_teleport` | ouroboros_sim.h:1988 | csrc/tactical_move.c:3231 | csim/test_E11_S083_stats_traits_ability.py |
| `om_unit_tick_decision_loop` | ouroboros_sim.h:2061 | csrc/tactical_support.c:1091 | csim/test_E15_S129_units_that_cannot_fight.py |
| `om_visibility_compute` | ouroboros_sim.h:1615 | csrc/fog.c:812 | csim/test_E12_S089_i_see_what_my_units_see.py |
| `om_visibility_set_player_fog` | ouroboros_sim.h:1616 | csrc/fog.c:823 | csim/test_E12_S093_fog_is_for_the_player_not_the_engine.py |
| `om_world_run` | ouroboros_sim.h:169 | csrc/sim.c:554 | csim/controls/test_control_osc_as_level.py |
| `om_world_set_seed` | ouroboros_sim.h:142 | csrc/region.c:243 | csim/test_E02_S020_rng_seeding.py |
| `om_world_set_strategic_tick` | ouroboros_sim.h:1736 | csrc/generational.c:2183 | csim/test_E08_S060_named_leaders_live_and_die.py |
| `om_zone_sample_interference` | ouroboros_sim.h:1617 | csrc/fog.c:829 | csim/controls/test_control_e12_window_interference_ignores_intensity.py |

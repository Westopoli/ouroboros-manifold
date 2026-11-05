<!-- Read-only audit for Westley's question of 2026-10-20 "every piece of code written had a parent test, is that not the case?"; measured by a Sonnet engineer on origin/main 2beff79c (sim, gcov) and the same tree (client and tooling, reference map); copied byte for byte by a records clerk, Architect 2026-10-20. Interpretation is in the Architect's report to Westley, not here. -->

# Coverage audit, non-C parts (origin/main in worktree ~/Projects/om-push/wt/audit-cov-rest)

Method: reference map (grep/ast), not line coverage. pytest and pytest-cov are not installed; `coverage` is absent. Godot cannot be run for coverage. CSVs: client.csv, python.csv in the same directory.

## 1. Godot client (autoload/ and scenes/, .gd, addons excluded)

Totals: 221 files, 47,323 lines.

| class | files | lines | share of lines |
|---|---|---|---|
| play (a qa play, tests/qa, tests/transport .py, names the script, class, autoload name, basename, or its scene) | 30 | 11,866 | 25% |
| unit (a tests/**/*.gd names it; no play) | 121 | 22,061 | 47% |
| none (no test or play reference) | 70 | 13,396 | 28% |

Note: 20 of the 70 `none` files (2,251 lines) have a bare-stem word hit in some test (generic names such as camera_rig, flow, title, ground); they are counted `none` because no path, class_name, autoload name, `x.gd` basename or scene name matched.

### `none` files grouped by directory (files, lines)
- autoload: 3 files, 267 (era_theme_resolver 174, input_sanitizer 83, scanline_overlay 10)
- autoload/bridge: 1, 146 (frame_decode.gd)
- scenes/debug: 7, 1,119 (manual test harness scenes: test_*.gd, wave2_visual_check)
- scenes/era_library: 2, 76 (era_card, era_roster)
- scenes/galaxy: 2, 83 (galaxy_view_driven, unknown_label)
- scenes/ground3d: 1, 14 (projection)
- scenes/harness: 1, 20 (harness)
- scenes/main_menu: 1, 263 (menu_title_heartbeat)
- scenes/tactical_c: 1, 43 (loading_overlay)
- scenes/shared/world_view: 2, 845 (main_menu_galaxy 824, era_world_view_config 21)
- scenes/shared/world_view/cameras: 1, 464 (orbital_camera_3d)
- scenes/shared/world_view/renderers: 2, 806 (settled_reach_renderer 582, constellation_renderer 224)
- scenes/mockups (all subdirs): 46 files, 9,250 lines
  - _shared 2/44, chronicle 4/829, fog 5/929, hud 5/745, landscape 8/3,436, layers 2/409,
    menus 5/421, menus/screens 5/548, objectives 4/734, objectives/tools 1/21, units 5/1,134

Split of the 13,396 `none` lines: mockups 9,250 (46 files); scenes/debug 1,119 (7); everything else 3,027 (17 files).

### Scenes (.tscn, 51 in autoload/ + scenes/) with no play that loads them
Direct reference only (scene name or res:// path in a qa play or tests/transport .py).
- 11 scenes are named by a play: debrief, error_screen, galaxy_view, load_game, lobby, main_menu, mission_briefing, privacy_modal, settings, tactical_view, world/chronicle_scroll_panel.
- 40 scenes have no play. Of these, 21 are named by neither a play nor any .gd test:
  scenes/debug (9: debug_ws_test, test_chronicle_scroll, test_faction_info_panel, test_faction_palette, test_info_panel_host, test_region_info_panel, test_time_jump, test_world_view, wave2_visual_check),
  scenes/harness/harness, 8 mockups (chronicle, fog, hud, landscape, layers, menus, objectives, units),
  shared/world_view/cameras/orbital_camera_3d, shared/world_view/main_menu_galaxy, shared/world_view/renderers/settled_reach_renderer.
- The other 19 no-play scenes are named by a .gd test only: bug_report_popup, debrief/ribbon_graph, era_library/era_detail, era_library/era_library, loading_screen, mockups/galaxy_mockup, mockups/settlement_mockup, new_game, onboarding, shared/error_panel, shared/world_view/world_view_shell, space3d/space_view, tutorial_overlay, world/chronicle_entry, world/chronicle_entry_expansion, world/faction_info_panel, world/info_panel_host, world/region_info_panel, world/time_jump_sequencer.

## 2. Python tooling (import map; "covered percent" is NOT available)

Result classes: `imported` = a test file under tests/ imports the module by AST (dotted, or flat via sys.path insert); `named-only` = no import, but a test file names the file (subprocess run, path string, marker text); `transitive-only` = imported only by an imported module; `none` = no reference in tests/. Statements = AST statement nodes.

| package | modules | statements | imported | named-only | transitive-only | none |
|---|---|---|---|---|---|---|
| scripts/specfactory (+escalator_fix_fixtures) | 45 | 8,344 | 19 mod / 5,427 st (65%) | 16 / 2,323 | 1 / 31 | 9 / 563 |
| scripts/skilllab (+ground) | 43 | 4,321 | 42 / 4,274 (99%) | 0 | 1 / 47 | 0 |
| scripts/simviewer (+probes) | 8 | 1,429 | 3 / 691 (48%) + __init__ implicit (0 st) | 3 / 738 | 0 | 1 / 0 (probes/__init__.py) |
| all | 96 | 14,094 | 64 / 10,392 + 1 implicit | 19 / 3,061 | 2 / 78 | 10 / 563 |

### Modules never imported by a test (the "under 50 percent" list stands in as "not imported")
named-only, specfactory (tests run them as subprocess/CLI or mention them):
card_regen 416, card_slice 193, chain_graph 208, gd_reach_lint 93, green_check 99, libm_lint 80, method_check 203, red_check 188, rule_pins 82, rule_pins_tests 89, size_lint 88, snapshot_fixture 147, status_check 174, tactical_trace 137 statements.
- gen_controls (60) and gen_test_skeleton (66) are `named-only` only because generated test files carry a "Generated by scripts/specfactory/gen_controls.py" marker (95 and 100 files); no test runs them.
named-only, simviewer: __main__ 90, probes/chronicle_twin 295, probes/mission_choice 353 (tests/simviewer/test_probes_smoke.py names the two probes).
transitive-only: specfactory/agy_json 31 (named in test_escalator_fix_probe.py via the probe it feeds), skilllab/summary 47.
none (no reference anywhere in tests/): specfactory budget_gate 11, dor_check 77, draft_card 65, draft_e2e 52, fill_tests 70, fold_answers 94, gen_all_cards 120, gen_card 46, escalator_fix_fixtures/test_px17_scratch_r7d 28; simviewer/probes/__init__ 0. (563 statements.)

## 3. Method caveats
1. Reference means a name appears in a test file, not that a line ran or an assertion constrains it: a `unit` or `imported` file may be touched by one test, and a mention in a comment or doc string would count; no per-line or per-function coverage exists here.
2. Scene and script links are direct only: a script or scene reached only through another scene or `load()` chain, or through the main-menu flow a play drives, is not credited unless its own name appears, so `none` and "no play" overstate the untested set, while the generic autoload/class names counted as references may overstate `play` and `unit`.
3. Godot .gd tests were not executed (about 9 specfactory tests are known red, and no pytest was available), so nothing here says whether the referencing tests pass; the C sim (csrc/) is excluded and measured by the other auditor.

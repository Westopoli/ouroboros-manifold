<!-- Read-only pre-flight for the Architect's Lane U, Lane M and HARNESS-coverage specs; measured by a Sonnet engineer on origin/main 2026-10-20; copied byte for byte by a records clerk. -->

# Client lane assignment of untested files and unplayed scenes (origin/main, audit 2026-10-20)

Sources: test-coverage-client.csv (70 `none` rows), client-tooling.md (40 unplayed scenes), visible-game programme lane table, pieces.toml (218 pieces).
Method: owner = pieces.toml `owns` (exact file) or `owns_glob`; lane letter from VG-<letter> piece ids; where only legacy ids (C1..C8, T2g) or G-* ids own a file, the lane is by directory and the legacy id is stated. A glob that several pieces claim (scenes/galaxy/** is claimed by C2, C8, VG-B; scenes/tactical_c/** by C5, C8, VG-A) lists all.
Excluded as asked: 46 `none` files under scenes/mockups/ (9,250 lines) and 7 under scenes/debug/ (1,119 lines). Remaining `none` rows: 17 files, 3,027 lines (matches the audit's "everything else").
No `none` file belongs to lane D, E, F, P, V or W.

## Part 1. The 17 `none` files by lane

### Lane A battle screen (1 file, 43 lines)
| file | lines | owner | does |
|---|---|---|---|
| scenes/tactical_c/loading_overlay.gd | 43 | VG-A glob (also C5, C8) | covers the tactical view with "DEPLOYING FORCES" until the first frame arrives (S-138) |

### Lane B galaxy (2 files, 83 lines)
| file | lines | owner | does |
|---|---|---|---|
| scenes/galaxy/galaxy_view_driven.gd | 66 | VG-B glob (also C2, C8) | model behind galaxy_view's driven mode; maps time-jump region/faction names onto the snapshot shape (S-069, S-106) |
| scenes/galaxy/unknown_label.gd | 17 | VG-B glob (also C2, C8) | class UnknownLabel: "Unknown" or "Faction N" text for an owner id not in the known list |

### Lane C ground 3D (1 file, 14 lines)
| file | lines | owner | does |
|---|---|---|---|
| scenes/ground3d/projection.gd | 14 | VG-C glob | world (x, y) wu to screen px through a Camera3D over the height field (S-236, R-207-06); audit note: stem-only hit |

### Lane D, E, F: 0 files

### Autoload shared (4 files, 413 lines)
| file | lines | owner | does |
|---|---|---|---|
| autoload/bridge/frame_decode.gd | 146 | VG-CONTRACT (exact row; contract lane K) | wire-level helpers of c_bridge.gd: frame encode and decode, exact uint64 checksums |
| autoload/era_theme_resolver.gd | 174 | no owner row | autoload EraThemeResolver: reads the era manifest, returns unit, structure and environment scenes with a fallback |
| autoload/input_sanitizer.gd | 83 | no owner row (G-wsinputsanitizer owns ws_input_sanitizer.gd, a different file) | autoload InputSanitizer: sanitize(raw, rule) for "save_name" and "key_code" |
| autoload/scanline_overlay.gd | 10 | no owner row | autoload CanvasLayer 100 drawing a scanline shader ColorRect over the screen |

### Shared/menus (8 files, 2,454 lines)
| file | lines | owner | does |
|---|---|---|---|
| scenes/main_menu/menu_title_heartbeat.gd | 263 | C1 glob (scenes/main_menu/**) | main-menu title positioning fix (waits on ThemeConstants font load before placing the title) |
| scenes/era_library/era_card.gd | 47 | G-eralib glob | one Era Library card built from a pack manifest; click opens the viewing-only detail |
| scenes/era_library/era_roster.gd | 29 | G-eralib glob | unit roster column of the era detail (type id title, then category) |
| scenes/shared/world_view/main_menu_galaxy.gd | 824 | no owner row | Node3D galaxy backdrop; loaded by main_menu.gd:144 and loading_screen.gd:128 |
| scenes/shared/world_view/cameras/orbital_camera_3d.gd | 464 | no owner row | orbital camera with moods and click signals (stage 11g); named by EraWorldViewConfig |
| scenes/shared/world_view/renderers/settled_reach_renderer.gd | 582 | no owner row | Settled Reach galaxy renderer: region visuals, shell, ambient tweens (stage 11g); named by EraWorldViewConfig |
| scenes/shared/world_view/renderers/constellation_renderer.gd | 224 | no owner row | filament tubes between regions; lane B copied it into scenes/galaxy/legacy_constellation_renderer.gd (B23 header says so) |
| scenes/shared/world_view/era_world_view_config.gd | 21 | no owner row | Resource EraWorldViewConfig: era id to renderer and camera scene paths |

### Harness (not a lettered lane) (1 file, 20 lines)
| file | lines | owner | does |
|---|---|---|---|
| scenes/harness/harness.gd | 20 | C7 glob (scenes/harness/**) | thin QA-harness wrapper scene launched by scripts/qa_harness.sh; audit note: stem-only hit |

### Lane totals, `none` files (excluding mockups and debug)
| lane | files | lines |
|---|---|---|
| A battle screen | 1 | 43 |
| B galaxy | 2 | 83 |
| C ground 3D | 1 | 14 |
| D, E, F | 0 | 0 |
| autoload shared | 4 | 413 |
| shared/menus | 8 | 2,454 |
| harness | 1 | 20 |
| total | 17 | 3,027 |

## Part 2. The 40 unplayed scenes by lane
Lane by owner row first, else directory; scene .gd lines in brackets. S-ids are those literally in the scene's script (S-### or R-###-## whose story number is ###); "none" = no S-id or R-id in the script or .tscn, and the programme file names the scene nowhere. Mockup scenes are outside the brief's directory rules; their lane is by the mockup's name and, where marked, the pieces row.

### A battle screen (5, mockups only)
- scenes/mockups/fog/fog_mockup (227): no owner row; S-ids none
- scenes/mockups/hud/hud_mockup (292): no owner row (G-mockupqa owns hud/qa/**); none
- scenes/mockups/layers/layers_mockup (356): MK-layers; none
- scenes/mockups/objectives/objectives_mockup (198): no owner row; none
- scenes/mockups/units/units_mockup (64): no owner row; none
(No unplayed scene under scenes/tactical_c: tactical_view is played.)

### B galaxy (8)
- scenes/world/chronicle_entry (295): C3 glob + C8 glob (legacy ids); none
- scenes/world/chronicle_entry_expansion (110): C3 + C8; none
- scenes/world/time_jump_sequencer (707): gd owned by VG-B (exact row) and VG-B26-chronicle-serial; R-069-03 (S-069); programme row B26 ties the chronicle to S-108
- scenes/world/faction_info_panel (250): G-infopanel (exact gd row); none
- scenes/world/info_panel_host (136): G-infopanel; none
- scenes/world/region_info_panel (294): G-infopanel; none
- scenes/mockups/chronicle/chronicle_mockup (319): MK-chronicle; none
- scenes/mockups/galaxy/galaxy_mockup (93): no owner row (G-mockupqa owns galaxy/qa/**); none

### C ground 3D: 0 unplayed scenes

### D space (2)
- scenes/space3d/space_view (279): VG-D-VIEW (exact); S-246 (R-246-01 to R-246-04); programme: S-246 row pending Westley
- scenes/mockups/landscape/landscape_mockup (262): PROTO-space-density owns landscape/hud.gd and field_map_space.gd; none in scene script

### E settlement and economy (1)
- scenes/mockups/settlement/settlement_mockup (466): no owner row; programme names scenes/mockups/settlement for PROTO-settlement-banding (S-237 context), no S-id in the scene script

### F lobby and net: 0 unplayed (lobby is played)

### Shared/menus (14)
- scenes/loading_screen/loading_screen (193): C8 glob; none
- scenes/new_game/new_game (217): no owner row; none
- scenes/onboarding/onboarding (397): no owner row; none
- scenes/tutorial/tutorial_overlay (268): no owner row; none
- scenes/bug_report/bug_report_popup (125): G-bugreport; none
- scenes/era_library/era_library (121): G-eralib; none
- scenes/era_library/era_detail (105): G-eralib; none
- scenes/debrief/ribbon_graph (197): C4 + C8 globs; none (debrief itself is played; its script cites R-077, R-078)
- scenes/shared/error_panel (21): G-errorpanel (exact), VG-F also lists the gd; none
- scenes/shared/world_view/world_view_shell (181): no owner row; none
- scenes/shared/world_view/main_menu_galaxy (824): no owner row; none
- scenes/shared/world_view/cameras/orbital_camera_3d (464): no owner row; none
- scenes/shared/world_view/renderers/settled_reach_renderer (582): no owner row; none
- scenes/mockups/menus/menus_mockup (209): no owner row (G-mockupqa owns menus/qa/**); none

### Debug and harness (10, no lane)
- scenes/debug (9: debug_ws_test 63, test_chronicle_scroll 146, test_faction_info_panel 149, test_faction_palette 182, test_info_panel_host 172, test_region_info_panel 130, test_time_jump 171, test_world_view 147, wave2_visual_check 168): all G-debug glob; none
- scenes/harness/harness (20): C7 glob; none

### Counts
| lane | unplayed scenes |
|---|---|
| A | 5 (all mockups) |
| B | 8 |
| C | 0 |
| D | 2 |
| E | 1 |
| F | 0 |
| shared/menus | 14 |
| debug and harness | 10 |
| total | 40 |

## Notes
- Programme-file S-ids on unplayed scenes: only S-246 (space_view) and S-108/S-069 (chronicle, via B26 and time_jump_sequencer). No other unplayed scene has an S-id in script or .tscn.
- pieces.toml has no row for scenes/shared/world_view/** and none for autoload/era_theme_resolver.gd, input_sanitizer.gd, scanline_overlay.gd, or the mockup dirs fog, hud, objectives, units, galaxy, landscape (except two files), menus, settlement.
- Legacy piece ids (C1 to C8, T2g) are pre-programme client pieces; their letters do not mean programme lanes (C5 is the tactical view, VG lane A).

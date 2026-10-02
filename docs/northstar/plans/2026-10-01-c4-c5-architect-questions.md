# Architect questions from the C4 and C5 tests-first pass (2026-10-01)

Source: Engineer reports on branches push/C4-E2-tests (66ea6d0), push/C4-E3-tests (144da60), push/C5-G1-tests (0187769), push/C5-G2-tests (cd3982f), push/C5-G3-tests (2e82ec2), push/C5-C1-tests (759d99a). Notes: docs/northstar/proving_ground/evidence/push_2026-10-01/c4_e2_tests_note.md and c4_e3_tests_note.md. Each question lists candidates; answers go in the rulings file.

## C4 E1 Era Library (no tests written: no rule exists)
E-16 and E-20 have no R-id for the Era Library screen and the register has no screen rows. Owed before tests: screen rules, plus register rows for mastery and tier progress showing "not yet tracked". Owner piece G-eralib (scenes/era_library/**).
- Q-C4-E1-01 entitlement source: (a) local ownership file, all installed eras owned in dev; (b) Steam stub; (c) always owned.
- Q-C4-E1-02 mastery and tier progress: (a) "not yet tracked" text; (b) hidden; (c) derived from campaign saves.
- Q-C4-E1-03 card and detail content: (a) identity, tiers and roster from the pack manifest; (b) the same plus sample chronicle text.

## C4 E2 bug report
- Q-C4-E2-01 tactical pause menu "Report a bug" entry: (a) E2 adds a minimal Esc menu with Resume and Report a bug; (b) HUD button; (c) F12 only.
- Q-C4-E2-02 four files name TacticalBridge with no owning unit: mission_metrics_recorder.gd, ws_input_sanitizer.gd, qa_daemon.gd, scripts/tactical/visibility.gd (scenes/debug/* is owned by G-debug). G6 cannot reach zero without an owner and a plan. Also whether mission_metrics.json belongs in the ZIP.
- Q-C4-E2-03 ZIP name has a one-second timestamp so two captures in one second overwrite: fix, or accept.

## C4 E3 legacy tactical deletion
- Q-C4-E3-01 ordering: autoload/tactical_bridge.gd line 57 preloads scenes/tactical/perf_logger.gd, so deleting the directory breaks boot. (a) E3 includes a one-line edit dropping the logger; (b) G6 goes first.
- Q-C4-E3-02 does the Visibility autoload (scripts/tactical/visibility.gd) go with E3.
- Q-C4-E3-03 scenes/debug/test_squad_impact_origins preloads legacy renderers: delete or rewire (G-debug owns it).
- Q-C4-E3-04 are cover and control groups rebuilt in tactical_c (the removed tests leave that behaviour untested).
- Removed-test classification table is in the E3 note; the ratchet list edit needs a ledger row.

## C5 galaxy and chronicle
1. Idle mood cycle: R-107-02 says the camera is fully the player's outside a jump; R-110-01 wants an autonomous six-mood camera behind the main menu. Trigger: (a) method called only by jump replay; (b) only the main-menu backdrop; (c) both with an auto flag. How does the view learn a jump is running.
2. Galaxy pan: keys and edge-scroll (a) or drag-only with R-103-09 inapplicable (b); settings slider scales drag (a) or not (b); vertical drag grab-style (a) or prototype inverted (b).
3. Band thresholds: R-106-03 says Overview >=75, Regional 40-65, Local <25; code uses 70 and 32.5; prototype focus distance 28. (a) rule wins, code moves; (b) rule text edited to the code values.
4. Edges between different or neutral owners: draw all with dim colour (prototype), or only same-faction (R-106-02 text).
5. Region size: map tier to size, or add significance to the wire.
6. Faction names: name_tables has 8 names for 15+ factions, modulo wrap shares names. Acceptable as placeholder? Is "[faction]" allowed for an unknown id?
7. Faction-list and data panels R-107-03/04: part of G-G3 or a new unit; observable qa_state keys hover_faction and pin_faction.
8. G-G4 frame-time fallback: key name (candidate quality_tier), tier values (0 raymarch, 1 stand-in, 2 fewer particles), step-down trigger (frame ms above 16.7 over N frames), recovery, slow-frame force (plant slow-frames or qa_frame_time(ms) verb). Numbers are Westley's.
9. Panel slide-out: R-069-01 slides out at end of scroll; R-108-05/06 put Proceed and Exit in the panel footer after the last entry and slide out on Proceed. Conflict. Also the embedded galaxy MISSION button: hide in the composite? R-108-01/05/06/07 have no C5 unit.
10. Replay clock: mockup uses 20 ticks/s, R-099-03 says 10. R-069-03 map is master clock, entry hold at least 3.0 s, shell tween 2.0 s (R-108-03).
11. Mentions (G-C2): which words are mentions, where spans come from (wire has only refs), faction mention focus distance. Live load_frame queues entries with "mentions": [] so nothing is clickable. E-09 and E-16 have no rule.
12. Names pinned by tests (change if you disagree): OrbitCamera.focus_region(int), OrbitCamera.get_hovered(), adapter string ids str(i), node name ChronicleScrollPanel in the composite, route name chronicle.
13. G-C3 jump replay needs a contract piece first. Proposed chronicle frame field: "ownership":{"stride":2,"from_tick":N,"n_regions":R,"snapshots":[[owners...],...]} (-1 unowned, count jump_ticks/2+1, about 40 KB JSON at 400 regions, 26 snapshots) plus a header accessor such as om_time_jump_get_ownership_snapshot(w,k,owners_out,cap) and a count. Lands after B5 and B6 then T1 (pipe) then client. Keyframes (R-069-05) derived client side; om_chronicle_generate_map_keyframes then unwired or deleted.

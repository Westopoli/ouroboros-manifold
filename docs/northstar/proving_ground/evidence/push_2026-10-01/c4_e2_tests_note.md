# C4-E2 tests note (bug report off TacticalBridge, reachable everywhere)

Test: `tests/test_bug_report_live.gd`. Source: gap-fix plan E2. No E-16 rule exists for bug report (Architect story still owed), tests cite the plan text.

Run: E2-1 headless ok. E2-2..E2-5 need display: `xvfb-run -a godot --path . -s tests/test_bug_report_live.gd` (frame_post_draw never fires headless; headless run prints NOTE and checks E2-1 only).

Red on main (xvfb): E2-1, E2-2, E2-3, E2-4. E2-5 (F12 every screen, 11 screens) green today: regression guard. Green with temp patch (manager reads SimSession.bridge().tactical_frame(), auto buffering, view.send_command logs), patch reverted.

Not tested, open:
- Q-C4-E2-01: "Report a bug" in tactical pause menu. tactical_c has no pause menu, no rule defines one.
- Q-C4-E2-02: mission_metrics.json in ZIP. MissionMetricsRecorder reads TacticalBridge; plan E2/E3 name no owner. Also ws_input_sanitizer, qa_daemon, scripts/tactical/visibility, scenes/debug/*: all name TacticalBridge, no unit assigned.
- Q-C4-E2-03: ZIP name has 1 s timestamp, two captures inside one second overwrite. Fix or accept.
- Ratchet: when E2 lands, `autoload/bug_report_manager.gd` leaves KNOWN_REFERENCERS (Engineer ledger row).

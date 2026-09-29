# Client scene graph

Reachable-scene list from the main menu, copied from the "Scene reachability
graph" section of `~/Projects/om-push/logs/sweep-client-2026-09-28.md`
(client sweep, 2026-09-28).

`new_game`, `onboarding` and `time_jump_sequencer` are parked and unreachable
until Q-063-01/02 are answered.

```
privacy_modal (run/main_scene)
  → (accept, or flag already set) → loading_screen → main_menu

main_menu
  ├─ NEW GAME        → SimSession.reset(); go_to("galaxy")           [galaxy, live]
  ├─ CONTINUE         → go_to("load_game")                            [load_game, live]
  │     └─ LOAD (bridge row)        → go_to("galaxy")                 [galaxy]
  │     └─ legacy card click (dead, Finding 7) → go_to("loading_screen", {target:"time_jump"})
  │           → (Python sim restart) → time_jump_sequencer            [orphaned dead-end, gap 5]
  ├─ ERA LIBRARY      → go_to("era_library")                          [era_library, live — Finding 1]
  │     └─ era card click → go_to("era_detail", {era_id})             [era_detail, live — Finding 1]
  ├─ SETTINGS         → go_to("settings")                             [settings, live — Finding 9]
  ├─ QUIT             → get_tree().quit()
  └─ Replay Tutorial (dead, Finding 5) → TutorialStateMachine.reset_for_replay()

galaxy_view
  └─ Mission button → go_to("mission_briefing")                      [mission_briefing, live]

mission_briefing
  └─ Deploy/Begin → go_to("tactical_c")                                [tactical_c, live]

tactical_c
  └─ End Mission → go_to("debrief")                                   [debrief, live]

debrief
  ├─ → go_to("chronicle")                                             [chronicle_scroll_panel, live]
  └─ → go_to("main_menu")

chronicle_scroll_panel
  └─ Return → go_to("galaxy")

error_screen (only reachable via the legacy SimBridge's own _route_to_error_screen,
  never from the C path — see Finding 2) → Continue → go_to("loading_screen")
```

Unreachable from any of the above (confirmed no `go_to()` call site anywhere in `scenes/`
targets them): `new_game`, `onboarding`, `time_jump_sequencer` via the normal NEW GAME
path (known gap 5 — the only route to `time_jump_sequencer` at all is the dead legacy
Continue-card click, Finding 7, which is itself functionally unreachable), the entire
`scenes/tactical/` stack (gap 9), `scenes/mockups/**`, `scenes/harness/`, `scenes/debug/**`,
`scenes/bug_report/bug_report_popup.tscn` (Finding 8), `scenes/tutorial/tutorial_overlay.gd`
(Finding 5).

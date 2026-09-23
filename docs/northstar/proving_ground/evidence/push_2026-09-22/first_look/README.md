# C8 flow spine -- first look, 2026-09-22

Human-eye walk, real game, real Xvfb, real QADaemon TCP protocol. Not a test.
Res 1920x1080 (review res, not the fenced suite's 1280x720). Seed 1.
Driver script: scratch tooling, written and deleted same session, not in repo.

## Flow walk

| step | scene (from `state()`) | screenshot | notes |
|---|---|---|---|
| 1. main menu | `res://scenes/main_menu/main_menu.tscn` | `01_main_menu.png` (immediate) + `01b_main_menu_settled.png` (+3s) | see "Main menu findings" below |
| 2. galaxy | `res://scenes/galaxy/galaxy_view.tscn` | `02_galaxy.png` | 60 unowned points, no factions/edges, flat grey bg -- expected, world gen (B4) not landed yet |
| 3. mission briefing | `res://scenes/mission_briefing/mission_briefing.tscn` | `03_mission_briefing.png` | fixture data (Ridge Point/Forward Camp/Hollow Crossing objectives, Tick 380, Generation 1). "Enemy Assessment"/"Your Force"/"Region State" panels render headers + empty underlines, no body text -- expected placeholder-quality, not live sim output, until B8/B9 attach |
| 4. tactical | `res://scenes/tactical_c/tactical_view.tscn` | `04_tactical.png` | flat grey bg, 6 blue squares (own units) vs 4 red squares (enemy), "END MISSION" button top-right -- stub sprites, expected until B9 attaches real tactical rendering |
| 5. debrief | `res://scenes/debrief/debrief.tscn` | `05_debrief.png` | fixture outcome (Partial Success, Score 80%, Force Retained 60%, Commander Survived, Military -4.0/Tension -3.0/Economy +2.0) -- well laid out, clean, no visible defects |
| 6. chronicle | `res://scenes/world/chronicle_scroll_panel.tscn` | `06_chronicle.png` | "CHRONICLE" header + "RETURN" button in a small top-left panel, rest of screen flat grey, empty -- no chronicle entries/text rendered at all. Expected fixture-quality per B10 not attached yet, but flagging: panel is *completely* empty, not even placeholder/stub text -- worth Westley's eye when B10 lands to confirm this is fixture-empty and not a render fail |
| 7. return to galaxy | `res://scenes/galaxy/galaxy_view.tscn` | `07_return_galaxy.png` | pixel-identical to step 2 (same 60 unowned dots, same layout) -- no conquest/recolour after mission, expected (matches conquest-no-recolour plant's purpose: nothing recolours today either way, plant or no plant) |

All 7 steps reached target scene inside their step timeout. No hangs, no crashes, no dropped transitions. `SceneRouter` handled all 6 real transitions cleanly in this run.

## Main menu findings (needs a second look)

Two menu-related observations, distinct from each other:

1. **Entrance-animation timing, not a bug.** `01_main_menu.png` (screenshot taken the instant `state()` reports `main_menu.tscn`) shows only "A WESTOPOLI GAME" -- no NEW GAME/CONTINUE/ERA LIBRARY/SETTINGS/QUIT labels, no title. `main_menu.gd::_animate_entrance()` staggers every content child's fade-in (`modulate.a` 0->1 with increasing delay per child); menu items are last in the stagger chain so they legitimately have not faded in yet at the moment the scene swap is first detected. `01b_main_menu_settled.png` (same launch, +3s wait before screenshot) shows all 5 menu items and the subtitle fully rendered and correctly laid out. Not filing this as broken -- it is a real player would see the same brief fade if they blinked at exactly the wrong instant, resolves in ~1-2s, and the controls are clickable via their `rect_px` even before the fade completes (confirmed: NewGame click worked from the tree() rect despite modulate.a still ramping).

2. **"OUROBOROS MANIFOLD" title text does not render at 1920x1080 -- possibly real bug, not investigated further (no code changes this pass).** `menu_title_heartbeat.gd` builds and positions a big pulsing serif title ("OUROBOROS MANIFOLD") as its own overlay Control, independent of the `_animate_entrance()` stagger (added directly, no `modulate.a=0` startup, so it should be visible from `_ready()` with just its normal 0.92-1.0 breathing pulse). In BOTH of our 1920x1080 captures -- immediate (`01_main_menu.png`) and settled +3s (`01b_main_menu_settled.png`) -- the title never appears anywhere on screen. A pre-existing screenshot from the fenced pytest suite's own 1280x720 run (`~/.local/share/data/qa/flow_01_main_menu.png`, not ours, left in place, predates this session) shows the title rendering fine and immediately at that resolution. We did not chase root cause (`_title_origin` positioning depends on a one-shot deferred `process_frame` callback finding `TitlePlaceholder`'s `global_position` -- could be a real resolution-dependent layout race, or could be timing-flaky independent of resolution; two samples at 1920x1080 both missing it, one sample at 1280x720 present, is suggestive but not proof). Flagging plainly per instructions rather than working around it: **at 1920x1080, the main menu's title text is missing.** Worth a deliberate repro check before/at next C8-adjacent touch.

## Plant screenshots -- could not take them, here's why

Task asked for 6 plant-triggered galaxy screenshots (`seed-ignored`, `owner-colour-flat`, `edges-2d-overlay`, `pick-radius-zero`, `bands-frozen`, `conquest-no-recolour`). Checked before assuming possible, per instructions.

`scenes/galaxy/galaxy_view.gd:130` has a real `qa_plant(id: String) -> bool` method (matches the mockup-scene convention used elsewhere: `galaxy_mockup.gd`, `objectives_mockup.gd`, etc. all have the same contract). But that method lives on the scene root; nothing outside the process can call it directly.

Checked `autoload/qa_daemon.gd`'s `_dispatch()` (its full verb switch, line 178) for every verb the daemon exposes over `--qa-port`:

```
state | tree | seed | fixture | pause | step | inject | screenshot | input
```

None of these reach `qa_plant`:
- `_do_fixture(path)` (line 247) -- just stores `_fixture_path = path` as a string. Does not call anything on the current scene. Not wired to `qa_plant` at all.
- `_do_inject(bug_id)` (line 264) -- checks `bug_id` against `KNOWN_BUG_IDS := ["stub-null-ref", "stub-stuck-ai", "stub-desync"]` and records it in `_injected_bugs`. This is the E-15/csim debug-bug injection system (comment at top of file confirms: reuses `qa_driver.gd`'s verbs, no mockup root contract in `--qa-port` mode). Unrelated to galaxy_view.gd's plants.
- `input` sub-verbs (move/click/click_node/drag/wheel/key/wait_frames) only synthesize OS-level input events through `qa_driver.gd` -- no path to calling an arbitrary GDScript method on the scene root.
- `state`/`tree`/`pause`/`step`/`screenshot` are exactly what they say, nothing more.

So: real gap, confirmed by reading the actual dispatch code, not assumed. The daemon's `--qa-port` mode has no verb that reaches a live scene's `qa_plant(id)`. (The mockup scenes' own `verify.gd` harnesses call `qa_plant` directly in-process under `--qa-script` mode, which is a different launch mode that cannot run at the same time as `--qa-port` -- see the file-header comment: instantiating `qa_driver.gd` while `--qa-script` is also set crashes the process.)

Took `08_galaxy_plants_gap_clean.png` instead -- clean galaxy view, no plants triggered, for completeness. It is identical to `02_galaxy.png`/`07_return_galaxy.png` (same launch, same seed, nothing changed between them).

**This is a real capability gap for future desktop QA/first-look passes on galaxy_view's plant states**, not a game bug. If plant-level QA screenshots are wanted going forward, `qa_daemon.gd` needs a verb (e.g. extend `fixture` or add a `call`/`plant` verb) that reaches `get_tree().current_scene.qa_plant(id)` when present. Did not add it -- out of scope, docs-only pass, no code changes.

## Liveness check

`scripts/qa_harness.sh liveness` (C7's precheck, drives `scenes/harness/harness.tscn` under the same Xvfb pattern):

```
LIVENESS OK os_inputs=3 scene=res://scenes/harness/harness.tscn
```

Passed clean.

## Files in this directory

- `01_main_menu.png` -- main menu, screenshot taken the instant scene swap detected (pre-fade)
- `01b_main_menu_settled.png` -- main menu, same launch, +3s later (post-fade, title still missing -- see findings)
- `02_galaxy.png` -- galaxy view after New Game
- `03_mission_briefing.png` -- mission briefing after clicking a system's Mission
- `04_tactical.png` -- tactical view after Deploy
- `05_debrief.png` -- debrief after End Mission
- `06_chronicle.png` -- chronicle after Continue
- `07_return_galaxy.png` -- galaxy view again after Return
- `08_galaxy_plants_gap_clean.png` -- galaxy view, no plants (see plant-screenshot section for why)

Driver script(s) used to produce this run were scratch tooling under `/tmp`, deleted after the run -- not in this worktree, not in this evidence dir.

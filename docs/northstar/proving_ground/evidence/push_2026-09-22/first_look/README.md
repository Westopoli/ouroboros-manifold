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

## Plant screenshots -- gap closed, take 2

Second pass, same day. `autoload/qa_daemon.gd` now has a real `"plant"` verb
(`_dispatch`'s match hits `_do_plant(id)`, which calls
`current_scene.qa_plant(id)` when the scene has it -- `_do_plant` at line 272,
`"plant"` case at line 194). Gap from the section above is closed, no more
"could not take them."

Ran the same boot -> New Game -> galaxy flow, then called `plant` for all six
ids in order, checked `ok: true` + `result.activated: true` on every one,
screenshotted after each. All six calls came back clean, none silently
skipped:

| plant id | ok | activated |
|---|---|---|
| `seed-ignored` | true | true |
| `owner-colour-flat` | true | true |
| `edges-2d-overlay` | true | true |
| `pick-radius-zero` | true | true |
| `bands-frozen` | true | true |
| `conquest-no-recolour` | true | true |

Screenshots: `09_plant_seed-ignored.png` through `14_plant_conquest-no-recolour.png`.

Checked pixels, not just the daemon's `ok`/`activated` flags: all six are
byte-identical to `02_galaxy.png` (md5 `f14cbfff5c4f999417881aacadf45d68` on
all seven files, clean shot included). Eyeballed `02_galaxy.png` next to
`10_plant_owner-colour-flat.png` side by side too, confirms what the hash
says -- same 60 black dots, same layout, same flat grey bg, same MISSION
button. Not a screenshot-pipeline bug, real reason each one lands the same:

- `seed-ignored` -- flips a flag `qa_seed()` checks before re-laying-out
  points on the next seed call. Nobody called `qa_seed()` after planting, so
  layout never got a chance to run (or not-run) differently. Behavioral, not
  visual, on this pass.
- `owner-colour-flat` -- does call `_recompute_region_colours()` right away
  (only one of the six that repaints immediately). But every region's
  `owner` is `-1` today (world gen / B4 not landed, per the "expected"
  notes on `02_galaxy.png` above) -- so the "flat" branch and the normal
  per-owner branch both land on the exact same single colour for every dot,
  because every dot already shares the one owner id. Flat-vs-not-flat is a
  distinction with no visible difference until factions exist.
- `edges-2d-overlay` -- does call `_render_filaments()` right away too, but
  there are zero edges in `_edges` (same empty-world reason -- no
  factions/borders yet), so the "draw nothing, 2D overlay mode" branch and
  the normal "draw real filament tubes" branch both draw nothing. Matches
  the README's earlier note up top that `02_galaxy.png` has "no
  factions/edges."
- `pick-radius-zero` -- only changes `pick_radius_px` in `state()`'s output
  (0.0 instead of 14.0), never touches rendering. Confirmed behavioral not
  visual by reading `galaxy_view.gd` line 124 -- did not screenshot-hunt for
  something that was never going to be there.
- `bands-frozen` -- freezes the camera-distance band ("Overview" /
  "Regional" / "Local") at whatever it was when planted; only shows up if
  the camera moves afterward and the band would otherwise have changed. We
  never moved the camera, so nothing to see.
- `conquest-no-recolour` -- suppresses a recolour call that only fires on a
  conquest event; no conquest happened in this run, so the suppressed call
  and the normal call are both no-ops either way.

Bottom line: the daemon-level gap (no way to call `qa_plant` at all) is
fixed and confirmed working -- all six ids activate cleanly. The
*visual*-difference gap most of these plants were built to expose is still
blocked on the same B4 empty-world caveat this README already flagged for
the plain galaxy screenshots. Worth a re-run once B4 world gen lands real
owners/edges/factions -- `owner-colour-flat` and `edges-2d-overlay` should
actually diverge from clean at that point; the other four are
behavior-only by design and will keep looking the same as clean even then.

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
- `09_plant_seed-ignored.png` -- galaxy view, `seed-ignored` planted; byte-identical to `02_galaxy.png` (see "gap closed" section)
- `10_plant_owner-colour-flat.png` -- galaxy view, `owner-colour-flat` planted; byte-identical to `02_galaxy.png` (empty-world caveat, see "gap closed" section)
- `11_plant_edges-2d-overlay.png` -- galaxy view, `edges-2d-overlay` planted; byte-identical to `02_galaxy.png` (empty-world caveat, see "gap closed" section)
- `12_plant_pick-radius-zero.png` -- galaxy view, `pick-radius-zero` planted; byte-identical to `02_galaxy.png` (behavioral not visual, see "gap closed" section)
- `13_plant_bands-frozen.png` -- galaxy view, `bands-frozen` planted; byte-identical to `02_galaxy.png` (behavioral not visual, see "gap closed" section)
- `14_plant_conquest-no-recolour.png` -- galaxy view, `conquest-no-recolour` planted; byte-identical to `02_galaxy.png` (behavioral not visual, see "gap closed" section)

Driver script(s) used to produce this run were scratch tooling under `/tmp`, deleted after the run -- not in this worktree, not in this evidence dir.

## Look 3 (live world), 2026-09-24

Same real-flow walk, redone after T1-1 landed on main (`set_seed` generates
world). Seed 1, res 1280x720 (fenced-suite res, not look-1/2's 1920x1080).
Real boot -> NewGame -> galaxy, same daemon protocol. Driver script scratch
tooling under `/tmp`, deleted, not in this dir.

**Held claim, not a pass: screenshots below show what the daemon rendered
in one run under Xvfb/software GL. Not a green test result.**

### Bottom line up front: galaxy view still empty in real play. Root cause found and pinned to one line.

Look 2 said "no factions/edges -- expected, world gen (B4) not landed yet."
World gen (T1-1) is landed now and works -- confirmed independently, pipe
alone: `set_seed(seed=1, n_regions=80, features=[6])` + `step(n=10)` +
`snapshot` gives 80 regions, 51 owned, 88 edges (exact numbers below,
reproduced twice via a bare `pipe/ouroboros_pipe` subprocess, no Godot).
But `scenes/galaxy/galaxy_view.gd:69`'s live-load call is
`bridge.load_snapshot_live(seed, 60, [6])` -- hardcoded `60`, not `80`.
`tests/transport/test_pipe_shapes.py`'s own comment says why that number is
wrong: "60 is below the feasible minimum for the default 15-faction
generator on every seed ... confirmed empirically, 0/5000 seeds generate at
n_regions=60." Proved this exact failure mode standalone (bare pipe
subprocess, `set_seed` script, no Godot):

```
set_seed(seed=1, n_regions=60, features=[6]) -> {"type":"error","name":"set_seed","reason":"generation failed"}
... step/snapshot still answered, but on the ungenerated world: 0 regions, 0 edges, 0 factions
```

`autoload/c_bridge.gd`'s `load_snapshot_live` sends `set_seed`, `step n:10`,
`snapshot`, `quit` as one fixed script regardless of whether `set_seed`
succeeded, so it does get a `"snapshot"` frame back -- just one with empty
`regions`/`edges`. `galaxy_view.gd`'s `_load_live_snapshot()` only calls
`set_snapshot()` when `load_snapshot_live()` returns `true`; it returns
`true` here (a snapshot frame did arrive), so `set_snapshot({"regions":[],
"edges":[]})` runs and the scene renders nothing. Net effect: the galaxy
scene silently renders an empty galaxy every real launch, with no error
surfaced to the player or the log -- looks exactly like "world gen not
landed," which is what fooled look 2's "expected" call.

Confirmed live, in Godot, under Xvfb: `galaxy_live.png` (below) and every
one of the six plant shots are byte-identical (md5
`1215ac7d90ff7ac2cde9d21e3574d34a`, same hash `flow_02_galaxy.png` and
`flow_06_return.png` from this same run's fenced-test screenshots got) --
same empty flat-grey view as look 2's `02_galaxy.png`, not the populated
80-region galaxy T1-1 actually produces when asked for the right count.

**Fix is a one-line change, not investigated further here (docs-only QA
pass, no code touched):** `scenes/galaxy/galaxy_view.gd:69`,
`bridge.load_snapshot_live(seed, 60, [6])` -> some `n_regions` at or above
the feasible floor (80 is proven to work at seed 1; whether 80 is the right
number for every seed or the call should ask the C side for the floor is a
design call, not this QA pass's to make).

### `["state"]` dump

Daemon's generic `state` verb only ever returns `{"scene", "tick"}` --
confirmed again this pass, same gap look 2 flagged for `qa_plant`: no verb
forwards to `galaxy_view.gd`'s own `qa_state()` (system_count/owners/
edge_counts/region_colours/etc.), so region count / owned count / edge
count / colour-equals-owner cannot be read from the live daemon at all
today, only inferred by driving the pipe directly (which is what "bottom
line" above does). Real `state()` result from this run:

```
{"ok": true, "result": {"scene": "res://scenes/galaxy/galaxy_view.tscn", "tick": 0}}
```

Counts asked for (region 80 / owned 51 / edge 88) are the true numbers
`pipe/ouroboros_pipe` produces for seed 1 at the CORRECT n_regions=80 --
verified twice, standalone, no Godot in the loop (command script above).
They are not what the live scene shows today (it shows 0/0/0, per the bug
above) and could not be read off the daemon even if they were, per the gap
just described. Region-colour-equals-owner rule from
`tests/test_galaxy_view.gd::_check_owner_colour_S106_R106_01_02` is a
GDScript-level unit-test rule against a fixture snapshot -- confirmed green
there (44/44 pass, see test run section below) but not independently
checkable from the live daemon for the same reason.

### Screenshots

- `galaxy_live.png` -- galaxy view after real NewGame click, live pipe
  world, seed 1. Flat grey, no dots, no edges -- empty, per the bug above.
  Pixel-identical to look 2's `02_galaxy.png`/`07_return_galaxy.png` and to
  this run's own fenced-suite `flow_02_galaxy.png`/`flow_06_return.png`
  (all md5 `1215ac7d90ff7ac2cde9d21e3574d34a`).
- `galaxy_plant_seed_ignored.png`, `galaxy_plant_owner_colour_flat.png`,
  `galaxy_plant_edges_2d_overlay.png`, `galaxy_plant_pick_radius_zero.png`,
  `galaxy_plant_bands_frozen.png`, `galaxy_plant_conquest_no_recolour.png`
  -- one per plant id, taken right after `["plant", id]` each returned
  `ok: true, activated: true` (all six did, no silent skips). Every one is
  byte-identical to `galaxy_live.png` (md5 matches, pixel diff 0/921600 via
  PIL for every plant, table below) -- same root cause as look 2's "gap
  closed, take 2" section (owner-colour-flat and edges-2d-overlay were the
  two plants expected to finally show a visible difference once world gen
  landed; they still show nothing, because the live world the plants act on
  is empty per the bug above, not because world gen never landed).

Pixel-difference table (`PIL`, `Image.getdata()`, RGBA, 1280x720 =
921600 px, exact equality per pixel):

| plant id | diff pixels | note |
|---|---|---|
| `seed-ignored` | 0 / 921600 | behavior-only plant either way (per look 2) |
| `owner-colour-flat` | 0 / 921600 | expected to diverge once world gen landed; still 0 because the live world is empty (bug above), not because world gen is missing |
| `edges-2d-overlay` | 0 / 921600 | same as owner-colour-flat -- expected to diverge, still 0, same root cause |
| `pick-radius-zero` | 0 / 921600 | behavior-only plant either way |
| `bands-frozen` | 0 / 921600 | behavior-only plant either way |
| `conquest-no-recolour` | 0 / 921600 | behavior-only plant either way |

Held claim: none of the six plants show a visible difference from clean in
this run. For the two that were expected to (`owner-colour-flat`,
`edges-2d-overlay`) this is the bug above, not a plant defect -- rerun this
same check once `galaxy_view.gd:69`'s region count is fixed, expect those
two to diverge and the other four to keep matching clean (by design, per
look 2's per-plant breakdown, unchanged reasoning).

### Test/build numbers from this same worktree, same session (for cross-reference)

- `make -j8 && make pipe/ouroboros_pipe`: clean, no warnings.
- `~/Projects/agora/.venv/bin/python -m pytest tests/transport -q`: 4
  passed. `test_pipe_hello_snapshot_and_checksum_match_ctypes` (n_regions=80,
  the one that actually drives the pipe) is green -- pipe checksum ==
  ctypes checksum == `9459460945690250679` for seed 1, n_regions=80,
  feature 6 (DRIFT), tick 10. That number does NOT match the checked-in
  fixture's stored checksum (`tests/transport/fixtures/snapshot_seed1_tick10.json`,
  `8319589330152745038`) -- the fenced test never actually asserts pipe-vs-
  fixture equality (only pipe-vs-ctypes, both computed fresh, both agree),
  so this is not a red test, just a heads up that the checked-in fixture
  file looks stale relative to current `csrc/worldgen.c`, worth a look
  separately.
- Godot suite (`scripts/run_godot_tests.sh tests/test_galaxy_view.gd
  tests/test_c_bridge.gd tests/test_qa_daemon.gd`): 44/0, 18/0, 9/0, all
  green.
- `scripts/qa_harness.sh liveness`: failed twice cold (`logs/` didn't
  exist in the fresh worktree, so `SimBridge`'s cmd-file `FileAccess.open`
  failed silently, sim never reached ready, boot fell through to
  `error_screen.tscn`; separately, no `.venv/` in the worktree so
  `sim_bridge.gd` fell back to system `python3`, which doesn't have the
  packages the sim needs -- "reader got null after 0 msgs"). Fixed by
  `mkdir logs` and symlinking `.venv` to `~/Projects/agora/.venv` (same
  target `~/Projects/om-push/m3`'s own `.venv` symlink already points at) --
  infra-only, no test/code/doc edits. Third run: `LIVENESS OK os_inputs=3
  scene=res://scenes/harness/harness.tscn`. Real gap for future fresh
  worktrees: nothing in the repo creates `logs/` or a `.venv` symlink on
  its own; every QA doer hitting a brand new worktree will hit this twice
  before finding it.
- `tests/qa/desktop/test_flow_spine.py`: 7/7 passed (S-C8-07's boot race
  did not reproduce this run).

### What a player would notice

Boots fine, main menu fine, New Game click works, lands on the galaxy
screen -- and it is empty. No systems, no borders, no factions, no error,
no loading spinner stuck, nothing to click on except the Mission button
(which per C8's own fixture-vs-live notes still routes off a fixture, not
this empty live snapshot). A player would read this as "the game has no
content" on the very first screen after starting a new game, not as a
minor cosmetic gap. This is the single highest-value bug this look found:
the whole point of T1-1 (the pipe generates a real world now) is invisible
in actual play because of one wrong number three lines away.

## Look 4 (galaxy live over the C2-3 / C7-2 fixes), 2026-09-24

Base: `origin/main` (`dd11142`, C2-3 on main) plus `origin/push/C7-2` merged (daemon `state` carries the scene's `qa_state()`). C7-2 is not on main yet (last merge attempt rejected at the godot_import gate). Seed 1, 1280x720, real boot -> NewGame -> galaxy under Xvfb, real daemon protocol, one fresh game per plant so plants do not stack (`qa_plant` has no unplant). Driver is scratch tooling, not in repo. Screenshots in `look4/`, numbers in `look4/look4.json`.

**Held claims, not passes: what one Xvfb/software-GL run rendered.**

### Bottom line

Galaxy data is live and correct. Galaxy pixels are not: every dot and edge draws black, so owners are not visible on screen.

- `state["qa"]`: `system_count` 80, 51 owned regions, 15 distinct owners, 16 distinct region colours, edge counts 52 at strength 0 and 36 at strength 2. Matches the pipe (80 / 51 / 88). Fenced flow spine 8/8 on this tree (S-C8-08 included).
- `galaxy_live_clean.png`: 80 black dots and a black edge tangle on flat grey, centre of screen, MISSION button bottom-right. No owner colours anywhere in the pixels although `region_colours` holds 16 different values. Brief expected owners coloured: not met on screen.

### Plants vs clean (pixel diff, 921600 px)

| plant | diff px | qa_state change | read |
|---|---|---|---|
| `seed-ignored` | 0 | none | behaviour-only, matches look 2 reasoning |
| `owner-colour-flat` | 0 | `region_colours` changed | colours change in state, no pixel change: because owner colours never reach the pixels in the clean shot either |
| `edges-2d-overlay` | 28599 | `edges_3d` true -> false | differs, real visual |
| `pick-radius-zero` | 0 | `pick_radius_px` changed | behaviour-only (click radius) |
| `bands-frozen` | 0 | none | behaviour-only (zoom band) |
| `conquest-no-recolour` | 0 | none | needs a conquest to show, see C2-4 |

Brief expected all six plants to differ by pixels. Only `edges-2d-overlay` does. `owner-colour-flat` is the one that should and does not: that is the same root cause as the black dots. Cause not investigated (docs-only pass): suspect the dot and edge materials do not apply `region_colours` (unshaded/emission missing) or the software-GL path drops it; check `scenes/galaxy/galaxy_view.gd` material setup against the colour dict.

### Follow-up owed

Galaxy render fix as a test-first story: screenshot-level assertion that the drawn pixels of an owned region differ from an unowned one (a colour-in-pixels detector), then the material fix. C2-4 conquest recolour stays blocked behind it.

## Look 5 (the live client, 2026-09-24)

Base: a scratch merge of the whole client stack (C2-6 shared session, C4-4 Begin, C1-2 Continue, C1-3 save dir, C2-5 galaxy materials, T1-5 real tactical frame on B10c and B9-6). Seed 1, 1280x720, real boot -> menu -> NewGame -> galaxy -> Mission -> Deploy -> End Mission -> Continue, real daemon protocol, real clicks on named controls, per-run `OM_SAVE_DIR`. Driver is scratch tooling, not in repo. Screenshots and the numbers below are in `look5/` (`look5.json`).

**Held claims, not passes: what one Xvfb/software-GL run rendered.**

### What works end to end (state read from `qa_state()`, not pixels)

- Main menu: `continue_enabled` false with no saves; true with a seed-3 100-tick campaign written into the save dir first (`06_menu_continue_enabled.png`).
- Galaxy: 80 systems, 51 owned, 16 distinct region colours, and the dots are coloured on screen (`01_galaxy.png`). One shared pipe session from here on.
- Briefing after stepping the galaxy 10 ticks (`step` verb): archetype 3, deadline 300, one objective (`02_briefing.png`); text panels are empty headers and zeros (force, enemy, region state come from sim fields that are 0 or absent).
- Deploy sends `mission_begin`, then the tactical view loads the live frame in 2.9 s: tick 1, canvas 24000, **572 units** (276 faction 0, 296 faction 1).
- Debrief reads the live frame: band `partial_failure`, achieved 0 %, brought home 100 %, region deltas all 0 (`04_debrief.png`).
- Chronicle after the 50-tick jump: 0 entries (`05_chronicle.png`).
- Continue: Continue -> load screen (one row, `07_load_game.png`) -> LOAD -> galaxy at tick 100 with 80 systems (`08_galaxy_loaded.png`): the saved world, not a fresh one.
- Autosaves after the flow: `campaign_1.omsave` in `OM_SAVE_DIR`; the real save dir is untouched.

### Findings

1. **The tactical view draws nothing on a real mission.** `03_tactical.png` is flat grey plus the END MISSION button, although `qa_state()` reports 276 drawn units. The view's fixed `WORLD_SCALE` (0.25) with the camera at the canvas centre shows a 7680 x 4320 world-unit window; the real canvas is 24000, and the sim puts the forces on opposite edges (faction 0 at y = 15, faction 1 at y = 23985, x 11745..12255). All 276 drawn units sit at screen y -2456..-2336, off screen. Fix belongs to C5: scale the view to the canvas (or pan/zoom to the local force); `tests/test_tactical_view.gd` pins fixture positions, so this is a test-first change M0 has to rule on.
2. **Without a pre-step the flow has no forces.** A fresh galaxy at tick 0 selects archetype 0 (seed 1); the tactical frame then has canvas 16000 and 0 units (sim side: archetype 0 spawns nothing, seed 2 and 4 the same). The look above steps the galaxy 10 ticks first to reach the archetype-3 mission with 572 units.
3. **Galaxy plants, pixel diff against the clean shot (921600 px):** `edges-2d-overlay` 31029 (differs, real); `seed-ignored`, `pick-radius-zero`, `bands-frozen`, `conquest-no-recolour` 0 (behaviour-only, as before); `owner-colour-flat` **0, and it should not be**: the plant recomputes `region_colours` (state changes) but `qa_plant` never re-renders the points, so the screen keeps the real owner colours. C2-5b fixes it, test first.
4. The load screen row reads only "Chapter 0": no slot name, tick or seed.
5. Briefing and debrief panels show empty text and zero bars: the frames carry no force composition, objective node names or region deltas yet (sim side, listed in the T1-2 gaps).
6. The sim never generates cover in a mission (all seeds tried): `map.cover` is empty by data, not by a pipe gap.

# HANDOFF BRIEF — P4 units mockup, pass 2: it must run when Westley clicks

Self-contained. Continues `scenes/mockups/units/` (pass 1 plus the fix pass merged 2026-09-22). That brief's rules still apply. Read `docs/northstar/research/mockups/units/README.md` ("Mockup review 1") first.

- If you are an Opus or Fable chat: plan and review, Sonnet sub-agents build. If you are a Sonnet chat: do the work yourself, spawn no sub-agents.

## What Westley reported, verbatim

"Units prototype: waypoints stay forever (never fade), there's no visible box that indicates the size I'm clicking and dragging over units to select (though it does work, when I click and drag and right click the units I selected output the command). Units do not move or do anything. Moving my mouse to the top left to select the drop down moves the screen that way because it's close enough to the edge of the screen to move the view."

His seat: 4480 x 1440 desktop, fullscreen window, Forward+. QA windows are 1280x720.

## Investigate, then fix, evidence first

1. Units do not move and pings never fade: one root cause. `hud.gd` starts with `_playing = false` and the toy sim ticks only while playing; command pings expire by tick (`unit_view.gd` `PING_LIFETIME_TICKS`), so with the sim stopped nothing moves and pings never expire. Prove it with a state dump (`tick` unchanged across seconds). Fix: the sim runs by default when launched interactively (`_playing = true`), issuing any command starts it if paused, and the HUD shows "PAUSED" large when it is not running. Keep `qa_tick` exact for QA: the driver's runs must still be deterministic, so under `--qa-script` the sim starts paused as before (read `OS.get_cmdline_user_args()` for `--qa-script`, or add a `qa_set("playing", false)` the smoke script calls first). Pings also expire on wall time when the sim is paused (a `Timer`-free 1.5 s fade using `_process` delta) so a paused scene never accumulates them.
2. No visible box while dragging: `hud.gd` or `input_router` never draws the drag rectangle. Add a full-rect `Control` with `mouse_filter = IGNORE` that draws the rectangle (fill `(0.3, 0.8, 1.0, 0.08)`, edge `(0.3, 0.8, 1.0, 0.75)`, width 1.5, the legacy values) from press to release, in the same coordinate space as the selection test, and clears on release (the hud mockup had a lingering-overlay bug; write the headless check that the overlay is invisible after a release).
3. Edge scroll: `camera_rig.gd` lines 39 to 46 compare a canvas-space mouse position against `get_viewport().get_visible_rect().size`, which under the project's `canvas_items` stretch is neither the canvas nor the window, so on a 4480x1440 window the right and bottom zones are unreachable. Fix as the objectives pass-2 brief does: compare in one coordinate space (canvas against canvas, or window pixels against window pixels through `get_viewport().get_final_transform()`), prove at `--res 2560x1440` with an oracle that a `move` to each of the four edges pans the camera in that direction.
4. Edge scroll over the HUD: no edge scrolling while the mouse is over any HUD control (`get_viewport().gui_get_hovered_control() != null`) or inside the HUD panel's rect; prove with a `move` onto the scenario dropdown for 30 frames leaving `camera` unchanged.

## Verification

- `scripts/mockup_verify.sh units` green, every plant `LIVE`, clean smoke at 1280x720 twice (add `qa_set playing false` or rely on the `--qa-script` detection so hashes stay identical), a new `qa/edges.json` at `--res 2560x1440` (four edges plus the HUD-hover no-pan case), one plant run each, and the 1920x1080 batch re-shot into `pass1/` where anything changed (add `drag_mid.png` showing the box: split the drag into `move`, a press via `click`-style events is atomic in the driver, so if a mid-drag frame cannot be captured, screenshot immediately after a `drag` whose release is on the same frame and say so).
- README: a "Mockup review 1 fixes" paragraph with the root causes and evidence; update the hotkeys line (sim runs by default, Space pauses).

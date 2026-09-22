# HANDOFF BRIEF — P3 objectives mockup, pass 2: edge scroll and regenerate

Self-contained. Continues `scenes/mockups/objectives/` built under `2026-09-22-p3-objectives-mockup.md`. That brief's rules still apply. Read `docs/northstar/research/mockups/objectives/README.md` ("Mockup review 1") first.

- If you are an Opus or Fable chat: plan and review, Sonnet sub-agents build. If you are a Sonnet chat: do the work yourself, spawn no sub-agents.

## What Westley reported, verbatim

"On objectives, only up/left side of screen move the view, bottom/right doesn't do anything so I can't move the view those directions. Regenerate also does nothing."

His seat: a 4480 x 1440 desktop, the window fullscreen (project `window/size/mode = 3`), Forward+. The QA runs are 1280x720 windows, which is why neither defect showed there.

## Investigate, then fix, evidence first

1. Edge scroll. `camera_rig.gd` lines 39 to 46 compare the mouse position against `DisplayServer.window_get_size()`. Under the project's `canvas_items` stretch the mouse position from the viewport is in the 1920x1080 base canvas while the window size is real pixels, so on any window larger than 1920x1080 the right and bottom thresholds sit outside the canvas and are never reached; on a 1280x720 QA window they sit inside it and work. Prove it: print the two sizes and the mouse position at the right edge in a QA run at `--res 2560x1440`, then fix by comparing the mouse against `get_viewport().get_visible_rect().size` (the canvas), or by converting the mouse to window pixels through `get_viewport().get_final_transform()`, consistently with the pixel scaling `objectives_mockup.gd` already does at lines 193 to 194. Add a headless check that the edge-scroll test uses the same coordinate space as the mouse position, and an Xvfb oracle at `--res 2560x1440`: a `move` to (2540, 720) for 30 frames changes `camera.x` positively and a `move` to (1280, 1420) changes `camera.z` positively.
2. Regenerate. `hud.gd` line 70 regenerates with the current dropdown and spinbox values, so pressing R or the button with the same seed and archetype rebuilds the identical mission and nothing visibly changes; the landscape mockup had the same complaint in its first review. Prove it with two states around a `key R` (identical `hash`), then fix: R and the button advance the seed spinbox by one before regenerating (Westley's expectation: "regenerate" produces a different map); keep `qa_seed(n)` exact. Update the smoke script's `after_r` expectation and the `regen_count` and `hash` oracles accordingly, and make the HUD's seed spinbox visibly show the new seed.
3. While there, apply the same coordinate check to every other mouse use in this mockup (click to select, minimap), and confirm the landscape, units, fog, layers and hud mockups do not share the edge-scroll defect: read their camera rigs and list, in the README, which ones compare mouse position against window size; do not edit them (each gets its own pass if needed).

## Verification

- `scripts/mockup_verify.sh objectives` green, every plant `LIVE`, clean smoke at 1280x720 twice, one plant run each, a new `qa/edges.json` run at `--res 2560x1440` proving all four edges pan, and the 1920x1080 batch re-shot into `pass1/` if any screenshot changed.
- README: a "Mockup review 1 fixes" paragraph with the two root causes and the evidence, and the list from step 3.

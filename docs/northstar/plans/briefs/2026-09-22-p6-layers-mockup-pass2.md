# HANDOFF BRIEF — P6 layers mockup, pass 2: it must demonstrate itself when Westley launches it

Self-contained. Continues `scenes/mockups/layers/` (pass 1 plus the review fixes merged 2026-09-22). That brief's rules still apply. Read `docs/northstar/research/mockups/layers/README.md` ("Mockup review 1") first.

- If you are an Opus or Fable chat: plan and review, Sonnet sub-agents build. If you are a Sonnet chat: do the work yourself, spawn no sub-agents.

## What Westley reported, verbatim

"The layers one doesn't appear to work at all. The buttons do not move the units when I click them, changing the seed doesn't do anything, reset doesn't do anything, step doesn't appear to do anything other than tick forward."

His seat: 4480 x 1440 desktop, fullscreen window, Forward+. QA windows are 1280x720, where the driver calls `qa_select`, `qa_transfer` and `qa_tick` directly, which is why none of this showed.

## Investigate, then fix, evidence first

1. Nothing moves: `layers_mockup.gd` starts with `_playing = false` and the sim advances only on Step or Play, so a transfer ordered by the buttons never progresses until the user knows to press Space, and Step advances one batch of ticks with nothing pending. Prove it with a state dump (`tick` unchanged, `transition` null). Fix: the sim runs on launch when interactive (paused only under `--qa-script`), a large PAUSED label when stopped, and ordering a transfer starts the sim if it is paused.
2. The buttons act on the selection, and selection by click likely fails on his screen: the pick compares a canvas-space mouse position against `unproject_position` pixels in another space (the same coordinate defect as the edge scroll: `camera_rig.gd` line 41 compares the mouse against `get_viewport().get_visible_rect().size`). Prove it with a `click` at a unit's projected pixel at `--res 2560x1440` leaving `selected` empty. Fix the pick and the edge scroll in one coordinate space (see the objectives pass-2 brief), prove all four edges pan and a click selects at 2560x1440. When nothing is selected, the transfer buttons apply to every friendly and the HUD says so; the selected unit is highlighted in the HUD's unit list as well as by its ring.
3. Seed and Reset do nothing visible: the map fixture is static and `generate(seed)` reseeds only what the RNG touches. Make the seed perturb the map deterministically (blocked cells around the obstacle in a seeded pattern, unit start positions, enemy positions) so seed 11 and 12 differ in at least half the blocked cells and every unit position, regenerate on the spinbox's `value_changed` as well as on R, and make Reset visibly return every unit to its start position and layer with the tick at 0 (prove with a state before and after). Every existing check stays green on both seeds; add the pixel oracle `diff before_seed11.png before_seed12.png >= 0.05`, `< 0.01` under `seed-ignored`.
4. Self-demonstration: on an interactive launch (not under `--qa-script`) the mockup runs the epic's paragraph by itself once: after two seconds the fast unit is ordered to layer 2, then the slow unit, the HUD narrates each step ("fast unit rising, 1 s", "slow unit rising, 5 s", "layer-1 enemy hidden, layer-2 enemy in half range"), then the fast unit is walked onto the blocked patch and ordered back down and waits, then walked clear and completes; the demo ends with "your turn" and the controls listed. A `D` key replays it. The demo is data (a list of timed commands in `fixtures/demo.json`), not code branches.

## Verification

- `scripts/mockup_verify.sh layers` green, every plant `LIVE`, clean smoke at 1280x720 twice (QA starts paused, hashes unchanged from pass 1 except where the seeded map changed them), a new `qa/edges.json` at `--res 2560x1440` (four edges, HUD hover no-pan, click selects), a `qa/demo.json` that drives the demo through `qa_tick` and screenshots its five beats, one plant run each, and the 1920x1080 batch re-shot into `pass1/` with the demo beats added.
- README: a "Mockup review 1 fixes" paragraph with root causes and evidence; the hotkeys line updated (runs on launch, D replays the demo).

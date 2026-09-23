# HANDOFF BRIEF — P5 fog mockup, pass 2: edge scroll and a seed that changes the map

Self-contained. Continues `scenes/mockups/fog/` (pass 1 plus the review fixes merged 2026-09-22). That brief's rules still apply. Read `docs/northstar/research/mockups/fog/README.md` ("Mockup review 1") first.

- If you are an Opus or Fable chat: plan and review, Sonnet sub-agents build. If you are a Sonnet chat: do the work yourself, spawn no sub-agents.

## What Westley reported, verbatim

"Can't move down/right on fog prototype either, bug is consistent across multiple prototypes. Changing seed doesn't do anything, otherwise it works well."

His seat: 4480 x 1440 desktop, fullscreen window, Forward+. QA windows are 1280x720.

## Investigate, then fix, evidence first

1. Edge scroll: `camera_rig.gd` lines 41 to 48 compare a canvas-space mouse position against `DisplayServer.window_get_size()` (real pixels), so on a window larger than 1920x1080 the right and bottom zones are unreachable. Fix in one coordinate space, as the objectives pass-2 brief does, and prove at `--res 2560x1440` with an oracle that a `move` to each of the four edges pans the camera in that direction. Also suppress edge scrolling while the mouse is over a HUD control (`gui_get_hovered_control() != null`).
2. Seed: `truth.generate(seed)` seeds an RNG that only jitters the enemy patrol phases; the map (obstacles, zones, interference, nodes, structures) comes verbatim from `fixtures/map_seed11.json` and the friendlies' loops from `scenarios/patrol.json`, and the seed spinbox only takes effect on R. Prove it: hashes for seeds 11 and 12 differ by the loop phases only and the screenshots are near-identical (`diff` under 0.02). Fix: keep the fixture as the base and let the seed perturb it visibly and deterministically: jitter every obstacle, zone and structure position by up to 400 wu, rotate the interference zone's centre around the canvas centre, pick the enemies' loop shapes and directions and the friendlies' waypoint order from the seed, and re-derive the fog grid. Regenerate on the spinbox's `value_changed` as well as on R. Add a headless check that seeds 11 and 12 place at least half the obstacles more than 200 wu apart, and the Xvfb oracle `diff recon_seed11.png recon_seed12.png >= 0.10` clean and `< 0.02` under `seed-ignored`. Every existing check (visibility, LOS, memory, recon) must stay green on both seeds.

## Verification

- `scripts/mockup_verify.sh fog` green, every plant `LIVE`, clean smoke at 1280x720 twice, a new `qa/edges.json` at `--res 2560x1440`, one plant run each, the 1920x1080 batch re-shot into `pass1/` with `recon_seed12.png` added.
- README: a "Mockup review 1 fixes" paragraph with root causes and evidence.

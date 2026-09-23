# HANDOFF BRIEF — P1 galaxy mockup, pass 2: the legacy look on the new generator

Self-contained. Continues `scenes/mockups/galaxy/` built under `2026-09-22-p1-galaxy-mockup.md`. That brief's rules still apply (placeholders, GDScript only, no autoload or cross-scene dependency at runtime, deterministic seed, commit per step, touch only `scenes/mockups/galaxy/**` and `docs/northstar/research/mockups/galaxy/**`, never set `DISPLAY`, QA through `scripts/mockup_qa.sh`), with one relaxation stated below. Read `docs/northstar/research/mockups/galaxy/README.md` ("Mockup review 1") first.

- If you are an Opus or Fable chat: plan and review, Sonnet sub-agents build. If you are a Sonnet chat: do the work yourself, spawn no sub-agents.

## What Westley approved and what he asked for

Approved: the seeded generator ("the generation system is awesome and worked great, let's keep that; the old one was always the same layout"), the bands, the faction list, click to focus.

Asked for, verbatim: "it looks like it didn't pull from the existing galaxy mockup. Really the galaxy from the original game was truly the foundation/prototype I wanted in terms of looks, it just needed polish/speed increases. Let's redo that prototype to be almost a copy of what already exists." And: "'Play' also only lasts a few seconds and then stops and doesn't do anything if I keep clicking (don't know if that's expected behavior or not)."

## The change: legacy renderer, new data

Replace `galaxy_view.gd`'s look with the legacy in-game galaxy view, fed by `galaxy_gen.gd`'s output. Copy, do not load: the legacy files stay untouched and the mockup keeps zero runtime dependency on them. Sources, all under `scenes/shared/world_view/`:

- `renderers/settled_reach_renderer.gd` (582 lines): the ambient rig (12 concentric particle rings with the per-ring table, radial inflow streams, ambient dust, starfield, grid plane, central glow and pulse), region node meshes, `_setup_constellation`, `_setup_shell`, `region_id_to_world_position`. `main_menu_galaxy.gd` is the same rig without the region layer; prefer the renderer.
- `renderers/constellation_renderer.gd` (224 lines) with `constellation_filament.gdshader`: the bezier tube filaments, border versus trade widths and the band alphas.
- `renderers/shell_renderer.gd` (339 lines) with `shell_metaball.gdshader`: the translucent faction territory shells with the bright seam where rivals nearly meet (R-106-02). Pass 1 deferred shells; pass 2 includes them.
- The four particle shaders beside them (`ring_particles`, `stream_particles`, `dust_particles`, `starfield_particles`).
- `cameras/orbital_camera_3d.gd` (464 lines): the six-mood auto-orbit for idle, the pan, orbit, zoom and click-focus input, the 1.5 s focus tween; keep pass 1's `qa_camera` and band API on top of it.
- `zoom_disclosure_controller.gd`: the distance-to-band blend the legacy used; reconcile with pass 1's band thresholds and keep the state names Overview, Regional, Local.

Data binding: the legacy renderer consumed `world_view_data.gd` dictionaries (`regions {id: {position, size, color, faction_id}}`, `connections`, `territories`). Write a thin adapter from `galaxy_gen.gd`'s systems, factions and edges into that shape so the copied renderer code changes as little as possible; the seed still drives everything and `hash()` is unchanged.

**Relaxation of the renderer-parity rule for this pass:** the legacy look depends on its shaders, so they are allowed. First step, before any porting: run one shader (`ring_particles`) under `scripts/mockup_qa.sh run` and check the screenshot renders; if a shader does not work under the Compatibility renderer on llvmpipe, keep it for Westley's seat (Forward+) and build a static-quad stand-in that the QA run uses instead, switched by `RenderingServer.get_current_rendering_method()`, and say so in the README. The look Westley judges is his seat; the QA screenshots must still prove structure (systems, filaments, shells present, bands, focus).

**Speed:** he wants "polish/speed increases". Measure `fps_ms` on the QA run for pass 1 and pass 2 and report both; keep MultiMesh for the points; cap particle counts so the pass-2 QA frame is not more than twice pass 1's.

**Play:** the replay runs 12 fixture events at two per second and then stops; a second press does nothing. Make Play restart the replay from the fixture's start (recolours reset to the seed's ownership first), and show a "replay 7/12" counter and "done, press J to replay" in the HUD. Take the flash proof shot pass 1 never got: `qa_replay_step` once, screenshot within the same frame window, so `mid_replay.png` shows the flash ring.

**Local band:** widen the plateau or cap the point scale so a Local focus keeps neighbouring systems and some filaments in frame (pass-1 review: "reads as flying into a planet").

## Verification

- `verify.gd` keeps every pass-1 check green; add: shells exist (one shell node per faction with systems), the adapter's dictionaries match the generator (system count, owner per id), replay resets `owners` to the seed's on restart, and the replay counter equals the fixture length at done.
- `qa/smoke.json` as pass 1 plus `screenshot flash` right after a single `qa_replay_step`, and a `play_restart` state after `call qa_replay_restart`.
- Screenshots at 1920x1080 for seeds 11 and 12 at the three bands, the hover, the flash and the replay end, into `docs/northstar/research/mockups/galaxy/pass2/`; keep `pass1/`.
- Report: does the pass-2 render read as the legacy capture `docs/bible/references/E-09/time_jump_galaxy_and_scroll.png` (shells glowing where factions touch, lanes as lit threads, nebula field, polar grid); which shaders rendered under the QA renderer; `fps_ms` pass 1 versus pass 2; the replay fix; under-defined points with candidates.

## What is not in scope

The chronicle mockup's mini galaxy (it stays its own thing), the real snapshot feed, the data panel (R-107-04), any change under `scenes/shared/`.

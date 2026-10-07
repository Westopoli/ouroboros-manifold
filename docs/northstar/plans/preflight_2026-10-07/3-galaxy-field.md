# Pre-flight scout 3-galaxy-field (2026-10-07, Sonnet, read-only)

Scout 3 report, lane B. The worktree is removed. I measured the Vulkan GPU numbers on the RTX 3060 under Xvfb. The main caveats are an unlanded earlier port, two failing checks on the branch, and a shell cost that fits budget.

**Headline findings**
- **Earlier port, unlanded:** a stack from 2026-10-01 already ports the mockup's old shell, constellation arcs, camera input and labels into `scenes/galaxy/`. Its tips are `origin/push/A54-ambient-tests` (a8c44458), `A54-quality-tests2` (182e5cbf) and `A55-names` (3d687eb2), all 12 to 14 commits ahead of main and not in the programme plan. Only the 6 `scenes/galaxy` commits (8a1d52a5 to 4302f0ad) matter here. The field is a drop-in for the stack's `legacy_shell_renderer.gd`.
- **Two checks fail on the branch itself.**
  - REFILL measured 35.6 ms median against the 12 ms budget. The committed `gpu_new.json` shows 35.5 ms.
  - FIELD-EQ on seed 12 gives 2.10% different first surfaces against the 2% limit.
  - Westley owns both thresholds.
- **A second galaxy renderer:** the chronicle and time jump (`scenes/world/time_jump_sequencer.gd:175`) use `scenes/shared/world_view/`, with the slow old shell. `scenes/galaxy` is not that path. Which one gets the field is a decision for you.

**(1) What the branch contains**
- **Where:** everything is under `scenes/mockups/galaxy/` (`push/galaxy-field` is 99f35887, based on 9404a62b, 4 commits). It draws only bubbles; the points, filaments, labels, camera and HUD are the older mockup files.
- **`territory_field.gd`, 229 lines:**
  - It holds the 96-cell, 128-unit grid, filled on the GPU. Systems are bucketed by z and uploaded as textures, one pass bakes the sheet, and the sheet is read back into an RGH 3D field texture and an R8 id texture.
  - It refills once per frame when dirty (`:122`).
  - Its API is `set_systems`, `add_system`, `update_system`, `set_system_owner`, `set_palette_color` and `is_dirty`.
- **`shaders/field_bake.gdshader`, 97 lines:** the per-cell field maths for all factions (16 max, 1024 systems max, gap 0.5).
- **`shaders/shell_field.gdshader`, 209 lines:**
  - It is one full-screen pass with at most 100 fetches per pixel.
  - It draws the first surface per faction, up to 4 layers, ISO 0.6, with a seam term.
- **`shell_renderer.gd`, 373 lines:**
  - It runs a half-resolution SubViewport and overlay, with opacity set by zoom band (0.50 / 0.12 / 0.05).
  - It also holds the faction `Label3D`s and a flat-billboard stand-in for the Compatibility renderer.
  - `res_divisor` (default 2) is the quality hook.
- **Input:** it is not fed from `c_bridge` and reads no region data. It reads a `world_view_data` node's `territory_set/updated/removed` signals and `get_territory()` (`{center, radius = significance, color}`). `galaxy_adapter.gd` fills those from `galaxy_gen.gd`, the mockup's fake seeded galaxy (180 to 220 systems, ball radius 50). Real data would come through the adapter the 10-01 stack already wrote.
- **Tests:** `tests/` holds about 1,700 lines, with the runners `run_fast.sh` and `scripts/galaxy_perf.sh`.
- **Shaders require Forward+ (Vulkan).** Under `opengl3` (Compatibility) the field is skipped and flat billboards stand in.

**(2) What the game scene must keep (`scenes/galaxy/galaxy_view.gd` and `.tscn` on main)**
- **Picking:** `PICK_RADIUS_PX` 14 appears only in `qa_state` (`:198`). Main has no click or hover code and no camera input, because `orbit_camera.gd` is a trimmed 70-line rig.
- **Mission button and fade:**
  - The MISSION button (`UI/Mission`, `:73`) calls `SceneRouter.go_to("mission_briefing")`.
  - Every `go_to` is a fade through `ThemeConstants.BASE` (`scene_router.gd:49`), so there is no "no cut".
- **Plants and qa_state:** the 6 plants and `qa_state` keys are fenced by `tests/test_galaxy_view.gd`, `tests/test_qa_state_scenes.gd:104` and the desktop tests. The desktop tests that pin them are `test_galaxy_pixels.py`, `test_galaxy_conquest.py`, `test_flow_spine.py` and `test_continue_flow.py`.
- **Pixel test:** `test_galaxy_pixels.py` reads the screen pixel at each projected owned system and needs at least 60% within tolerance 40 of the region colour. A shell overlay tints those pixels, so the test must be rechecked.
- **Self-loading and callers:**
  - The scene self-loads: `SimSession.bridge().ensure_world(seed, 80, features)` (`:107`), then `snapshot_changed` drives `set_snapshot`.
  - The callers are `main_menu.gd:71`, `load_game.gd:148` and `chronicle_scroll_panel.gd:91`. `SceneRouter` loads the scene through `autoload/scene_router.gd:16`.
  - Callers only route to "galaxy". Nothing else calls into `galaxy_view`; `qa_step` and `qa_camera` are reached through the daemon.
- **Positions and significance:**
  - Positions come from `scenes/galaxy/galaxy_gen.gd` (disc radius 40, spacing 3). The branch constants (ball 50, influence 14, grid 128) fit different geometry, so they need retuning.
  - The wire carries `tier` and no significance. The old stack maps tier to 0.3/0.6/1.0.

**(3) Merge shape**
Replacing the system and link drawing would break the fenced tests and drop plants. The smaller change is to keep `galaxy_view.gd` and add the field as a child node (`ShellRenderer`), fed by the 10-01 adapter. That is about 4 lines in `galaxy_view`, plus copying 4 files (about 910 lines, of which 306 are shader and 604 GDScript) and retuning the constants.

If the 10-01 stack is not landed, the child-node route has to bring its adapter and camera along. Sizing for that is open.

**(4) Performance, RTX 3060, Xvfb, Forward+, `scripts/galaxy_perf.sh`, 400 systems / 15 factions**

| Setting | d120 | d25 | d7.5 | inside | Budget |
|---|---|---|---|---|---|
| 1080p, ms median | 1.69 | 1.88 | 1.79 | 1.78 | 2.0 |
| Half resolution (the shipped quality switch, `res_divisor`), ms median | 0.46 | 0.50 | 0.48 | 0.49 | 0.7 |

- The GPU ran at about 1930 MHz. SHELL-SCALE (400/15 against 219/4) passes at 8.6% worst against a 15% limit.
- 300 presented frames of the mockup scene took 81 ms each under Vulkan and 58 ms each under `opengl3`. Those numbers are Xvfb present cost, not usable (the script warns of about 15 times slower). The window was also 100x100, not 1080p, because `--script` ignored `--resolution`.
- The GPU timestamp method above is the valid one.
- The spec budget is 2.0 ms at 1080p, 0.7 ms at half resolution, refill 12 ms and field memory 5 MB. Measured field memory is 4.22 MiB and passes.
- I did not measure an integrated GPU.
- The static checks, FIELD-VALUES, FIELD-ORDER and FIELD-CONQUEST pass. The headless check needs `godot --headless --import` in a fresh worktree first.

**(5) Stories**
- **S-106, shell and seam:**
  - R-106-02 is partly met: seam and gap are in the shader, and the mockup has same-faction filaments.
  - R-106-03 is mostly met: opacities are 0.50 / 0.12 / 0.05 against the rule's 40 to 60% / 8 to 15% (local "ground fog" is 0.05), and names are shown in Overview.
- **S-106, not met:**
  - R-106-04 war flashes. The mockup has `flash()` (0.6 s ring plus size boost), fired only from a fixture replay, so the game needs sim events from the pipe (`events` and `revolts` are in the delta frame).
  - R-106-05 ambient field. The branch has the old rig; the spec's vast-space step is not built.
  - R-106-01 point sizes and brightest core are mockup-only.
  - The headline says "borders touch" while R-106-02 says rivals keep a gap; the shader implements the gap (GAP_STRENGTH 0.5). That tension is for you.
- **S-107, not in the branch:** the mockup has pan, zoom, orbit, click-focus, auto-camera, faction hover/pin and tooltip. R-107-04 (data panel) has no code.
- **S-108:** none are built on the branch, and none are on main either.
  - There is no pull-back or push-in camera move, and `SceneRouter` fades.
  - There is no 2.0 s shell tween (the field snaps on refill).
  - The scroll panel already slides in over 0.40 s, but on the other renderer.

**(6) `pieces.toml`**
- `scenes/galaxy/**` is owned by C2 (`:362`, "attached") and C8 (`:515`, "attached").
- `scene_router.gd` is C8's and `time_jump_sequencer.gd` is G-timejump's (`:718`).
- Nothing lists the 10-01 stack.
- Lane B needs new rows that take the specific files from C2 and C8.

**Lane B piece list** (these are my suggestions; I made no decisions)
- **B0:** decide the 10-01 stack (land, rebase or rebuild) and the time-jump renderer. Tests: none.
- **B1:** `scenes/galaxy/territory_field.gd` plus `shaders/field_bake.gdshader`, about 230 lines with game-layout constants. Tests: port `test_field.gd` FIELD-EQ, VALUES, ORDER, CONQUEST and MEM on an 80-region fixture.
- **B2:** `shaders/shell_field.gdshader`, 209 lines of copy. Tests: COST-SHAPE and the shader-compiles check, each with its positive control.
- **B3a:** `shell_renderer.gd`, viewport and overlay, about 130 lines. Tests: ONE-DRAW, `res_divisor`, SHELL-GPU.
- **B3b:** faction labels and stand-in, about 120 lines. Tests: faction count and a band-opacity table.
- **B4:** `galaxy_view.gd` wiring, a few lines, with retuned grid and influence and the tier-to-significance map. Tests: the existing `test_galaxy_view.gd`, `test_galaxy_pixels.py` and `test_galaxy_conquest.py`, plus a `qa_state` element-inventory assertion and a look screenshot.
- **B5:** refill under 12 ms (a perf piece). Tests: REFILL. Westley owns any widening.
- **B6:** `galaxy_flash.gd` plus a pipe-events accessor, about 80 lines. Tests: R-106-04 per event kind. The `c_bridge` event contract needs checking first.
- **B7:** territory tween over 2.0 s (R-108-03, design needed). Tests: R-108-03 timing.
- **B8:** mission-to-galaxy pull-back and push-in without the `SceneRouter` fade (needs Westley's call; shared with lane A). Tests: R-108-01 and R-108-06 screenshot-based.

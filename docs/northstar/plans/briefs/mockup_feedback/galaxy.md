# Context: `galaxy` mockup

Read `README.md` in this folder first (the role brief), then `scenes/mockups/_shared/README.md`, then the record file below.

- Scene: `scenes/mockups/galaxy/galaxy_mockup.tscn`. Run: `~/.local/bin/godot --scene scenes/mockups/galaxy/galaxy_mockup.tscn` from the repo root.
- Scripts: galaxy.gd galaxy_adapter.gd galaxy_gen.gd galaxy_mockup.gd galaxy_view.gd hud.gd legacy_ambient_rig.gd legacy_constellation_renderer.gd legacy_shell_renderer.gd legacy_world_view_data.gd legacy_zoom_disclosure_controller.gd orbit_camera.gd verify.gd 
- Root script (the QA contract lives here): `scenes/mockups/galaxy/verify.gd`
- Plants (positive controls): "seed-ignored", "owner-colour-flat", "edges-2d-overlay", "pick-radius-zero", "bands-frozen", "conquest-no-recolour"
- QA scripts: checklist.md focus.json review11.json review12.json smoke.json 
- Record with Westley's verbatim reviews and the controls list: `docs/northstar/research/mockups/galaxy/README.md`
- Briefs (what it is meant to show, in order): 2026-09-22-p1-galaxy-mockup-pass2.md 2026-09-22-p1-galaxy-mockup.md 
- Next branch name: `mockup/galaxy-pass3` (check `git branch -r | grep mockup/galaxy` for the next free number)
- Controls: `~/.local/bin/godot --scene scenes/mockups/galaxy/galaxy_mockup.tscn` from the repo root. Hotkeys: `R` regenerate (from the seed spinbox), `J` toggle the jump-log replay. Left-drag pans, wheel zooms, right-drag orbits, left-click a system to focus it (tweens into the Local band over 1.5s). Hover a faction row in the left list to brighten it and dim the rest; click a row to pin that until it's clicked again or empty space is clicked. Hover a system for a name/owner tooltip.

## Westley's feedback for this pass

(paste verbatim here, then follow the procedure in README.md)

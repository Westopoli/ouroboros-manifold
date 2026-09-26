# Context: `objectives` mockup

Read `README.md` in this folder first (the role brief), then `scenes/mockups/_shared/README.md`, then the record file below.

- Scene: `scenes/mockups/objectives/objectives_mockup.tscn`. Run: `~/.local/bin/godot --scene scenes/mockups/objectives/objectives_mockup.tscn` from the repo root.
- Scripts: camera_rig.gd hud.gd markers.gd mission_gen.gd objectives_mockup.gd places.gd verify.gd 
- Root script (the QA contract lives here): `scenes/mockups/objectives/objectives_mockup.gd`
- Plants (positive controls):  "objective-on-spawn", "marker-unnamed", "progress-static", "kind-mapping-random", "seed-ignored", "route-ignored", 
- QA scripts: checklist.md edges.json plant_check.json smoke.json 
- Record with Westley's verbatim reviews and the controls list: `docs/northstar/research/mockups/objectives/README.md`
- Briefs (what it is meant to show, in order): 2026-09-22-p3-objectives-mockup-pass2.md 2026-09-22-p3-objectives-mockup.md 
- Next branch name: `mockup/objectives-pass3` (check `git branch -r | grep mockup/objectives` for the next free number)
- Controls: Hotkeys: archetype dropdown and seed spinbox in the top-left panel; **R** regenerates with the current dropdown/spinbox values; **T** advances 50 toy ticks; **P** toggles autoplay at 20 ticks/second until the mission completes. Mouse wheel zooms (height 800-20,000wu), WASD pans, edge-scroll pans. The 200x200 minimap bottom-right shows every fixture node as a dot, the player spawn as a blue square, and the current objective as a kind-specific glyph.

## Westley's feedback for this pass

(paste verbatim here, then follow the procedure in README.md)

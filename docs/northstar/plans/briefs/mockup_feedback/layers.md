# Context: `layers` mockup

Read `README.md` in this folder first (the role brief), then `scenes/mockups/_shared/README.md`, then the record file below.

- Scene: `scenes/mockups/layers/layers_mockup.tscn`. Run: `~/.local/bin/godot --scene scenes/mockups/layers/layers_mockup.tscn` from the repo root.
- Scripts: camera_rig.gd hud.gd layer_view.gd layers_mockup.gd toy_sim.gd verify.gd 
- Root script (the QA contract lives here): `scenes/mockups/layers/layers_mockup.gd`
- Plants (positive controls):  "instant-transfer", "blocked-ignored", "cross-layer-full-range", "ring-colour-same", "no-dimming", "wrong-height", "seed-ignored", 
- QA scripts: checklist.md demo.json edges.json seed_oracle.json smoke.json 
- Record with Westley's verbatim reviews and the controls list: `docs/northstar/research/mockups/layers/README.md`
- Briefs (what it is meant to show, in order): 2026-09-22-p6-layers-mockup-pass2.md 2026-09-22-p6-layers-mockup.md 
- Next branch name: `mockup/layers-pass3` (check `git branch -r | grep mockup/layers` for the next free number)
- Controls: Hotkeys: **Tab** cycles the focused layer, **1**/**2** set it directly, **Q**/**E**

## Westley's feedback for this pass

(paste verbatim here, then follow the procedure in README.md)

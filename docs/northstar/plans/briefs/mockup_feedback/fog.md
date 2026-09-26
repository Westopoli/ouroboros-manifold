# Context: `fog` mockup

Read `README.md` in this folder first (the role brief), then `scenes/mockups/_shared/README.md`, then the record file below.

- Scene: `scenes/mockups/fog/fog_mockup.tscn`. Run: `~/.local/bin/godot --scene scenes/mockups/fog/fog_mockup.tscn` from the repo root.
- Scripts: camera_rig.gd fog_grid.gd fog_mockup.gd fog_view.gd hud.gd truth.gd verify.gd 
- Root script (the QA contract lives here): `scenes/mockups/fog/fog_mockup.gd`
- Plants (positive controls):  "fog-leak", "no-memory", "recon-shows-enemy", "radius-ignored", "los-ignored", "seed-ignored", 
- QA scripts: checklist.md edges.json seed_diff.json smoke.json 
- Record with Westley's verbatim reviews and the controls list: `docs/northstar/research/mockups/fog/README.md`
- Briefs (what it is meant to show, in order): 2026-09-22-p5-fog-mockup-pass2.md 2026-09-22-p5-fog-mockup.md 
- Next branch name: `mockup/fog-pass3` (check `git branch -r | grep mockup/fog` for the next free number)
- Controls: `scenes/mockups/fog/fog_mockup.tscn` is the entry point: `~/.local/bin/godot --scene scenes/mockups/fog/fog_mockup.tscn`. Hotkeys: **B** Begin Mission, **M** toggle fog memory, **R** Reset (reseed from the spinbox), **T** step 20 ticks, **Space** play/pause continuous ticking. Left-click a friendly to select it (bolds its sensor ring); right-click issues a straight-line move to the selected friendly.

## Westley's feedback for this pass

(paste verbatim here, then follow the procedure in README.md)

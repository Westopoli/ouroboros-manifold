# Context: `units` mockup

Read `README.md` in this folder first (the role brief), then `scenes/mockups/_shared/README.md`, then the record file below.

- Scene: `scenes/mockups/units/units_mockup.tscn`. Run: `~/.local/bin/godot --scene scenes/mockups/units/units_mockup.tscn` from the repo root.
- Scripts: camera_rig.gd drag_box.gd hud.gd roster.gd toy_sim.gd unit_view.gd units_mockup.gd verify.gd 
- Root script (the QA contract lives here): `scenes/mockups/units/units_mockup.gd`
- Plants (positive controls):  "pass-through", "facing-fixed", "instant-fight", "silhouettes-same", "seed-ignored", "no-death-visual", 
- QA scripts: checklist.md edges.json review.json smoke.json 
- Record with Westley's verbatim reviews and the controls list: `docs/northstar/research/mockups/units/README.md`
- Briefs (what it is meant to show, in order): 2026-09-22-p4-units-mockup-pass2.md 2026-09-22-p4-units-mockup.md 
- Next branch name: `mockup/units-pass3` (check `git branch -r | grep mockup/units` for the next free number)
- Controls: Hotkeys: the sim runs by default on launch (paused only under `--qa-script` or `--headless`, for determinism), `Space` pauses/resumes, `T` step one tick, `R` reset the current scenario, `Tab` toggle kit, `F12` screenshot, left-click select, left-drag box-select (draws a live selection rectangle), right-click move (also resumes a paused sim), `Shift`+right-click attack-move, right-click on an enemy attack-target. A "PAUSED" banner shows top-centre whenever the sim isn't running. Scenario dropdown and kit button are also clickable in the HUD.

## Westley's feedback for this pass

(paste verbatim here, then follow the procedure in README.md)

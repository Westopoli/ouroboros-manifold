# Context: `chronicle` mockup

Read `README.md` in this folder first (the role brief), then `scenes/mockups/_shared/README.md`, then the record file below.

- Scene: `scenes/mockups/chronicle/chronicle_mockup.tscn`. Run: `~/.local/bin/godot --scene scenes/mockups/chronicle/chronicle_mockup.tscn` from the repo root.
- Scripts: chronicle_mockup.gd entry_view.gd hud.gd jump.gd scroll_panel.gd verify.gd 
- Root script (the QA contract lives here): `scenes/mockups/chronicle/verify.gd`
- Plants (positive controls): "order-shuffled", "expand-noop", "no-pause", "entries-duplicate", "morph-instant", "cadence-wallclock"
- QA scripts: checklist.md smoke.json 
- Record with Westley's verbatim reviews and the controls list: `docs/northstar/research/mockups/chronicle/README.md`
- Briefs (what it is meant to show, in order): 2026-09-22-p7-chronicle-mockup-pass2.md 2026-09-22-p7-chronicle-mockup.md 
- Next branch name: `mockup/chronicle-pass3` (check `git branch -r | grep mockup/chronicle` for the next free number)
- Controls: Hotkeys: `S` skip, `Enter` proceed (enabled once the phase reaches `done`), `R` reset the current seed. Right-drag over the galaxy pans the auto-orbit. A wrapper run without `--qa-script` leaves `QADriver` inert (no `--qa-script` in the launch args means `_ready()` returns immediately without wiring the script; no `_run.json` is ever written).

## Westley's feedback for this pass

(paste verbatim here, then follow the procedure in README.md)

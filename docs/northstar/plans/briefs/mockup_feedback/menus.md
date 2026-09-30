# Context: `menus` mockup

Read `README.md` in this folder first (the role brief), then `scenes/mockups/_shared/README.md`, then the record file below.

- Scene: `scenes/mockups/menus/menus_mockup.tscn`. Run: `~/.local/bin/godot --scene scenes/mockups/menus/menus_mockup.tscn` from the repo root.
- Scripts: backdrop.gd flow.gd menus_mockup.gd resolve.gd theme.gd verify.gd 
- Root script (the QA contract lives here): `scenes/mockups/menus/menus_mockup.gd`
- Plants (positive controls):  "band-random", "briefing-two-sections", "difficulty-dropped", "flow-skips-setup", "four-bands", "digits-in-prose", 
- QA scripts: checklist.md smoke.json 
- Record with Westley's verbatim reviews and the controls list: `docs/northstar/research/mockups/menus/README.md`
- Briefs (what it is meant to show, in order): 2026-09-22-p9-menus-mockup.md 
- Next branch name: `mockup/menus-pass3` (check `git branch -r | grep mockup/menus` for the next free number)
- Controls: `~/.local/bin/godot --scene scenes/mockups/menus/menus_mockup.tscn` from the repo root. No hotkeys are bound in this mockup (the smoke script's `key R` is a deliberate no-op — nothing in `menus_mockup.gd` or any screen handles keyboard input; the flow is mouse-only). Mouse: click a menu item, a difficulty card, or Accept/Refuse/Continue/Proceed/Resume/Back to move through the flow. Confirmed a `--qa-script`-less launch leaves the QA driver fully inert (no `QA_CALL`/`QA_WARN` output, no `_run.json` written anywhere under `user://`).

## Westley's feedback for this pass

(paste verbatim here, then follow the procedure in README.md)

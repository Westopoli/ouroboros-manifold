# Transition mockup, pass 1: one unbroken shot (spec, 2026-10-15)

**Status: specced 2026-10-15 (Architect) from Westley's ruling the same day; Doer builds on `push/proto-transition`; Westley approves before any game piece (Prototype gate, `agile.md`).**

## Why

E-16 S-108 says the mission pulls back into the galaxy and the galaxy pushes into the next mission without a cut. Westley, 2026-10-15: "This deserves a prototype before it actually gets built. We're going for a No Mans Sky sort of transition, so players really get the sense of scale. We can run things in the background while the transition happens (like pre-loading the simulation and map), but for the visual part of it I think it'd be more efficient to do a prototype first." The reference is the No Man's Sky planet-to-orbit transition (`docs/bible/references/E-16/notes.md`). A mockup is plain Godot, no C sim, runnable on the Mac.

## What the mockup shows

A single scene, `scenes/mockups/transition/transition_mockup.tscn` with `transition_mockup.gd`, new files only. Four moments, one continuous camera, no cut and no fade to black at any point:

1. **Battlefield.** A flat ground plane (land era look: a few height steps, the mockup's own simple mesh, no terrain engine) with about 40 unit markers in two colours at the game's unit scale (body radius 11.5 wu, `VG-C-unitscale`), the camera at the tactical view's normal height. A "mission complete" label; Space starts the move.
2. **Pull-back.** The camera rises and pulls back on an eased curve (R-108-01) until the battlefield is one point of light: the ground plane shrinks to a dot, atmosphere or haze thickens then clears, stars appear, the dot joins a field of system dots. Duration a named draft, DRAFT-pullback-s = 6.0 s, with keys to halve and double it. The galaxy fades in around the dot; it may reuse `scenes/mockups/galaxy/galaxy_gen.gd` for the dot field and shells, or draw its own simple field; it must not edit any file under `scenes/mockups/galaxy/`.
3. **Galaxy.** The scroll panel slides in from the right over 0.40 s and the galaxy resizes to 62 percent width (R-108-02); the panel prints three placeholder chronicle lines one at a time (R-069-03); a "Proceed" button appears when the last has printed (R-108-05). A small progress bar labelled "preloading next mission" fills during the pull-back and the print, to show that the sim jump and the next map load behind the move (Westley, 2026-10-15); it is cosmetic in the mockup.
4. **Push-in.** On Proceed the panel slides out, the next system brightens, the camera pushes in on the same eased curve in reverse until a new battlefield materialises from the point of light (R-108-06): the stars thin, haze thickens then clears, the ground plane grows from the dot, unit markers appear at their scale. Ends at the tactical height with a "briefing" label. R resets to moment 1.

Scale is the point: the move must read as the same space at different scales, the dot the battlefield becomes is the dot the camera pushes into, and nothing snaps (R-108-03). The camera path, the haze and the easing are what Westley judges.

## Controls

Space start or proceed; R reset; `[` and `]` halve and double DRAFT-pullback-s; V toggles a wireframe helper that draws the camera path; F1 to F3 pick three seeds for the galaxy field. Printed in a corner label.

## Shots

The script takes `--shot <dir>` on the command line (`OS.get_cmdline_user_args()`): it runs the whole move at normal speed with no input and saves `01_battlefield.png`, `02_pullback_mid.png`, `03_galaxy.png`, `04_pushin_mid.png`, `05_next_battlefield.png` from the viewport at those moments, then quits. The Doer attaches the five shots to its report; the landing clerk copies them to `docs/northstar/story_reviews/westley/` with a README row (S-108, mockup pass 1).

## Tests

`tests/test_mockup_transition.gd` (test writer, before the Doer builds): the scene instances without the C pipe (as `tests/test_mockup_without_pipe.gd` does for the other mockups, if that file exists on main; else the same pattern); after `--shot` to a temp dir, five PNGs exist and none is near-uniform (the gate's `look` histogram rule); the camera's distance to the battlefield origin is monotone during the pull-back and during the push-in; the panel's width is 38 percent of the viewport while printing. No timing threshold beyond DRAFT-pullback-s.

## Out of scope

The real chronicle, the real galaxy scene (`scenes/galaxy/`), the real tactical scene, saves, the sim. Nothing here lands in the game; an approved pass becomes an integration lane row in ROADMAP section 1 (guard 4, approved means scheduled).

## Run

```
GODOT=/Applications/Godot.app/Contents/MacOS/Godot
git fetch origin && git checkout push/proto-transition
$GODOT --path . res://scenes/mockups/transition/transition_mockup.tscn
```

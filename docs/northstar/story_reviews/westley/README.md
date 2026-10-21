# Shots waiting on Westley

How to answer: one word per picture, approve, reject, or a note. Where answers go: a message to the chat, or `answers.md` in the Batch A form; the clerk that records a verdict deletes the picture and its block in the same commit.

## B-S106-regional-galaxy-b24-layout.png

**What you see:** The galaxy map close up: coloured discs for regions, soft glows for territory, thin curved links between neighbours, a haze of yellow dust. Linked regions now sit next to each other and same-owner regions cluster.
**Judge:** Does this layout read as one connected galaxy of neighbours, as the prototype you approved did?
**Beta status of what is shown:**
- Star map with glowing territory (S-106): Seen (approved 2026-10-13 on the earlier dot-colour frame); this new layout is built and awaiting your verdict.
- Faction names on the map: built but not yet shown (the labels exist, none is readable at this distance).
- War flash: built but not yet shown (none fired in this frame).

## B-S110-galaxy-quality-choice-in-settings.png

**What you see:** The Settings screen. The Display card has a fourth row, Galaxy Quality, set to Full, lined up under Resolution, Fullscreen and VSync; Camera, Audio and Keybinds cards sit below.
**Judge:** Is the Galaxy Quality row where and how you want it?
**Beta status of what is shown:**
- Galaxy Quality choice (Full, Stand-in, Fewer particles): built and awaiting your verdict.
- Rest of the Settings screen (display, camera pan speed, audio sliders, keybind list): built and awaiting your verdict (S-110 is not yet Seen).

## D-S246-space-sheets-rings-tube.png

**What you see:** A dark 3D space battlefield seen from above at a slant: flat slabs of rock scattered across layered sheets, your fleet as a small cluster of blue and pink blobs in the middle, and a pale see-through disc around the cursor where the upper sheets fade.
**Judge:** Do the five sheets read as separate layers, with a ring on each unit and a see-through tube around the cursor, or is it still a dark blur?
**Beta status of what is shown:**
- Five layer sheets with asteroid slabs, unit rings, vision tube (S-246): built and awaiting your verdict (opt-in with OM_SPACE_VIEW=1, not yet the default view; the switch to default is planned, no piece scheduled).
- To-layer buttons on the right edge: stub, being replaced by the Alt plus number keybind (queued, not built).

## E-S126-starting-force-smaller-at-tick-0.png

**What you see:** The opening frame of a ground mission in 3D: a rocky ridge under a grey sky, three tinted discs each holding a stack of your units, and one lone blue blob top left.
**Judge:** Does the battle open with most of your force still to come, as your S-126 words say? The count (176 of 330) cannot be read by eye.
**Beta status of what is shown:**
- Smaller starting force (S-126): approved but not integrated (the sim gives 176 of 330; the unit count in the HUD and briefing still reads 330).
- Ground-era 3D opening view: built but not yet shown (your last word on it was "too zoomed out to judge"; a zoomed-in re-shot is owed).

## F-S143-S241-host-lobby-common-eras-and-team-size.png

**What you see:** The multiplayer host lobby on a plain grey screen: an Eras line naming the one era both players share, a Team size drop-down showing 2, a member list of two, the lobby number, and Host, Join, Doctrine, Start and Back buttons.
**Judge:** Does the Eras line tell two players with different packs which era they will play, and is the Team size choice where you expect it?
**Beta status of what is shown:**
- Common era line (S-143): built and awaiting your verdict.
- Team size 2 or 4 (S-241): stub (the choice is offered but does nothing to map or enemy size until the scaling rule is built).
- Lobby with member list and lobby number (S-141): Seen (approved 2026-10-13), placeholder look.

## P-S191-terrain-obeys-pass2-carved-routes.png

**What you see:** A top-down prototype of a land map with flat base circles, an objective, a choke bar in the middle, and orange and blue route lines; pink dots mark the cells the generator carved to make routes. Every point now has its narrow and wide routes.
**Judge:** The carved routes run as parallel lanes side by side, like a rail yard; is carving the right direction with a better path rule, or should routes come from the landforms?
**Beta status of what is shown:**
- Land that fits a requested layout, with routes (S-191, S-189): built as a prototype only, awaiting your verdict; in the game it is queued (not built), not scheduled (you said the layout engine comes first).
- The layout engine that asks for those places: stub (built, not yet called by the game).

## P-S191-terrain-obeys-pass2-small-canvas.png

**What you see:** The same prototype on a small map: base circles kept apart by scaling the pads down, steep ring slopes under the walking limit, and the same carved lanes in yellow and pink.
**Judge:** Do the pads and routes still read on the small map, or does the carving swamp it?
**Beta status of what is shown:**
- Small-map pads and routes (S-191, S-189): built as a prototype only, awaiting your verdict; in the game queued (not built), not scheduled.

## Removed today

| File | Verdict | Cite |
|---|---|---|
| `P-S108-mid-pullback-star-blobs.png` | Not approved: "the battlefield is still too large compared to the galaxy" (Westley, Batch A 1 and 2) | `plans/drift_audits/2026-10-19-decision-consistency.md` rows 1 and 11; `P.md` row 1 |
| `P-S191-terrain-obeys-seed1-no-routes.png` | Not approved, context asked (Westley, Batch A 3); also replaced by the pass 2 shot of the same case | audit rows 5 and 12; `P.md` row 3 |
| `A-S103-start-view-ground-era.png` | Rejected: no home base in sight, camera angle too low (Westley, Batch A 5) | audit rows 13 and 26 |
| `C-S001-S004-S005-S010-S132-ground-opening-frame.png` | Not accepted as an assessment: far too zoomed out, units cover the vision, a scaling issue (Westley, Batch A 11); re-shot zoomed in asked | audit row 20 |
| `C-S207-ground-units-after-move-order.png`, `C-S236-ground-zoomed-in-map-band.png` | Same run and same view as Batch A 11, taken before the unit scale fix (VG-C-unitscale 53ede72); superseded, re-shot owed | audit row 20; programme lane table, C ground 3D unit scale row |
| `A-S005-S091-ground-sight-after-20-ticks.png`, `A-S007-S075-S088-ground-plain-opening-frame.png`, `A-S075-ground-objectives-after-200-ticks.png`, `A-S095-S101-S105-ground-opening-frame-nothing-selected.png`, `A-S096-ground-move-ordered-empty-panel.png`, `A-S104-ground-first-frame-hud.png`, `A-S134-ground-camera-off-map-no-shots.png`, `A-S135-ground-ability-slot-missing.png`, `A-S136-ground-no-wreck-camera-off-map.png` | Same run (20261009-0228-5026db3) and view as Batch A 11, before the C fixes; superseded, re-shot owed | audit row 20 |

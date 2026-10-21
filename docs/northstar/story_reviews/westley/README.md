# Shots waiting on Westley

How to answer: one word per picture, approve, reject, or a note. Where answers go: a message to the chat, or `answers.md` in the Batch A form; the clerk that records a verdict deletes the picture and its block in the same commit.

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
| `E-S126-starting-force-smaller-at-tick-0.png` | Not approved: starting force still too large (about 25% fewer, not enough), units in a line, vision circle drawn parallel to the screen not the ground (Westley, 2026-10-21, new rulings 4) | `E.md` S-126 row; ledger day37 FINDING-s126-* |
| `F-S143-S241-host-lobby-common-eras-and-team-size.png` | Approved: "Looks good" (Westley, 2026-10-21, new rulings 5) | `F.md` S-143 and S-241 rows, run run-20261020T144745Z |
| `B-S106-regional-galaxy-b24-layout.png` (and `.state.json`) | Approved: "Looks good, approved." (Westley, 2026-10-21, new rulings 1) | `B.md` S-106 row, run 20261013-1406-59a24b4 |
| `B-S110-galaxy-quality-choice-in-settings.png` | Approved: "Approved" (Westley, 2026-10-21, new rulings 2) | `B.md` S-110 row, run 20261014-0538-356c339 |
| `D-S246-space-sheets-rings-tube.png` | Not approved: scale off, obstacles too sparse, scale prototype asked (Westley, 2026-10-21, new rulings 3) | `D.md` S-246 row; ledger day37 FINDING-s246-* and REQ-PROTO-scale |
| `P-S108-mid-pullback-star-blobs.png` | Not approved: "the battlefield is still too large compared to the galaxy" (Westley, Batch A 1 and 2) | `plans/drift_audits/2026-10-19-decision-consistency.md` rows 1 and 11; `P.md` row 1 |
| `P-S191-terrain-obeys-seed1-no-routes.png` | Not approved, context asked (Westley, Batch A 3); also replaced by the pass 2 shot of the same case | audit rows 5 and 12; `P.md` row 3 |
| `A-S103-start-view-ground-era.png` | Rejected: no home base in sight, camera angle too low (Westley, Batch A 5) | audit rows 13 and 26 |
| `C-S001-S004-S005-S010-S132-ground-opening-frame.png` | Not accepted as an assessment: far too zoomed out, units cover the vision, a scaling issue (Westley, Batch A 11); re-shot zoomed in asked | audit row 20 |
| `C-S207-ground-units-after-move-order.png`, `C-S236-ground-zoomed-in-map-band.png` | Same run and same view as Batch A 11, taken before the unit scale fix (VG-C-unitscale 53ede72); superseded, re-shot owed | audit row 20; programme lane table, C ground 3D unit scale row |
| `A-S005-S091-ground-sight-after-20-ticks.png`, `A-S007-S075-S088-ground-plain-opening-frame.png`, `A-S075-ground-objectives-after-200-ticks.png`, `A-S095-S101-S105-ground-opening-frame-nothing-selected.png`, `A-S096-ground-move-ordered-empty-panel.png`, `A-S104-ground-first-frame-hud.png`, `A-S134-ground-camera-off-map-no-shots.png`, `A-S135-ground-ability-slot-missing.png`, `A-S136-ground-no-wreck-camera-off-map.png` | Same run (20261009-0228-5026db3) and view as Batch A 11, before the C fixes; superseded, re-shot owed | audit row 20 |

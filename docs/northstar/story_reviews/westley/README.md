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

## C-S132-ground-units-close.png

**What you see:** Your force from 300 wu up, standing on an orange ridge under a pink steep wall: darts and arrowheads on the left, kites and wide hexagons on the right, each flat blue body 45 to 80 px across with a small dark icon and a yellow layer ring on top. Rows of loose blue arrowheads float above and below the force, away from any unit (the squad markers of the dart and arrowhead types, drawn in a flat map projection, so they do not sit on the 3D ground).
**Judge:** Can you tell the unit types apart by shape at a glance, at this size (S-132: "Every unit type has a shape I can read at a glance in any era")?
**Camera:** height 300 wu (the nearest wheel step to the ground; 1.80 px per wu at the centre), 1920x1080, seed 1, tick 2399. Body size measured on 71 blue shapes in the frame: median 55 px wide, 20 to 80 px, median 27 px tall (flat shapes seen at 50 degrees); the dark icon on top is 24 px. Your scaling question (FINDING-s246-unit-scale, land view) is still open: at the old height 3000 the same body is 4 px.
**Beta status of what is shown:**
- Unit shapes on the 3D ground (S-132): built and wired (lane C ground 3D, C6; scale fix VG-C-unitscale at 53ede72), the lane C plays pass; not Seen (your verdict pending).
- Squad markers for the dart and arrowhead types: built, but drawn in the flat map projection so they float off the units in the ground view (finding, no piece yet).

## C-S001-ground-slope-and-blocked-band-close.png

**What you see:** A steep pink wall (ground that blocks the layer) rising behind your force, a flat orange band your units stand on, green terraces dropping away at the left, and two long white bars across the ground where a slope joining two layers is marked at its midline; the bar disappears where the ground rises in front of it. Your units stand at the foot of the wall as small round icons, because their flat blue bodies lie nearly edge-on and half buried in the steep ground.
**Judge:** Can you see where terrain blocks a layer and where a slope joins two layers, so you can choose to go over, go around or hide (S-001)?
**Camera:** height 300 wu (1.80 px per wu at the centre), 1920x1080, seed 1, tick 3006. Unit bodies are not readable here (edge-on on the steep face); only the 24 px icons read. Body size on level ground is in the S-132 frame (median 55 px wide).
**Beta status of what is shown:**
- Slopes drawn with a midline and blocked ground tinted pink (S-001, R-001-06): built and wired (lane C ground 3D, C7), the S-001 play passes; not Seen (your verdict pending).
- Flat unit bodies on steep ground: built, they lie edge-on and half buried there (finding, no piece yet).

## C-S005-ground-sight-close.png

**What you see:** Nineteen selected bombards and bastions (white rings) standing on open green ground beside the settlement's white blocks, with a bright lit area around them and a dimmed, darker region beyond a curved edge at the right of the frame, where the white slope bars show through grey. The edge is a circle on the screen centred on the group, not an ellipse on the ground, and the 24 px icons sit on top of the flat bodies.
**Judge:** Do you see less outside your units' sight, with a clear edge between what they see and what they do not (S-005: "I see less on other layers than on my own, and nothing three layers away, unless I hold a vantage")?
**Camera:** height 300 wu (1.80 px per wu at the centre), 1920x1080, seed 1, tick 9774; the lit edge is about 720 px from the group centre. Unit bodies are hidden under the 24 px icons and white selection rings. At this height the dim vanishes whenever an own unit stands far south of the camera (the sight circle of a unit near or behind the camera comes out huge), so the group was first sent south of every other unit to get this edge (finding, no piece yet). No separate darker band for a neighbouring layer is drawn: the dim is one overlay outside the sight circles (R-089-03), so this frame shows the edge but not the layer rule.
**Beta status of what is shown:**
- Sight circles and the dim outside them (S-005, R-089-03): built and wired (lane A fog layer, A1 to A21), the lane A plays pass; not Seen (your verdict pending).
- The dim at close zoom: built, missing in most close positions (finding, no piece yet).

## C-S004-ground-layer-crossing-close.png

**What you see:** All 176 units selected (white rings) walking up a ridge in a long column, from the orange band at lower left to the brown band at upper right; the small ring under each unit changes from yellow to purple as it passes onto the upper layer, and the white midline bars of other slopes lie across the ground at the left. The column is thin and the units are single icons on the 3D ground, so the halfway line itself is not marked for the crossing.
**Judge:** Is a layer change on a slope visible, with the halfway line a place you can see and hold (S-004)?
**Camera:** height 300 wu (1.80 px per wu at the centre), 1920x1080, seed 1, tick 751 (the play's own order: every own unit sent to the top edge of the nearest slope, stepped in 25-tick chunks; these units crossed a ridge slope on the way, not the slope the play aimed at). No unit is in the timed transfer state, because walkers cross by position (R-004-06). Unit bodies are under the 24 px icons; body size in the S-132 frame.
**Beta status of what is shown:**
- Layer change on a slope (S-004, R-004-06): built and wired (lane C ground 3D, C7; S-004 play fix at bfd7f1c), the S-004 play passes; not Seen (your verdict pending).
- The halfway line as a marked place for one crossing: stub in this view (only the long midline bars are drawn, none picked out for the crossing).

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

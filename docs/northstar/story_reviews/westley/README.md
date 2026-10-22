# Shots waiting on Westley

How to answer: one word per picture, approve, reject, or a note. Where answers go: a message to the chat, or `answers.md` in the Batch A form; the clerk that records a verdict deletes the picture and its block in the same commit.

Each picture has one block under its file name, in this form: `**What you see:**`, `**Legend:**` (one line, what each colour and mark in the picture means), `**Judge:**` (a `**Camera:**` line may follow), `**Beta status of what is shown:**` with one line per feature.

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

## F-S140-click-move-order-obeyed.png

**What you see:** The player drags a box on the left of the match, clicks to the right, and 69 of the units move there in both peers (order tick 68; the host reads the common tick 1273, the guest reads tick 1401). The right side had blockers, so the play used the left corridor. The frame is the host's at tick 1297: 99 own units on screen, the 69 selected ones ringed in white in a loose cluster at the left, a tidy grid of unselected units at the middle right, and "69 selected" in the HUD at lower left. The drawn route line you asked for on 2026-10-13 is not built, so no path is drawn.
**Legend:** White ring: a selected unit (the HUD counts 69 selected). The other marks (green arcs, orange rings, blue arrowheads): none stated.
**Judge:** Does the move read as an order obeyed, with units leaving the box and heading for the click (S-140: "My orders reach every peer with no server in the middle")?
**Camera:** x 11950, y 250, scale 1.44, 1920x1080, tick 1297 (order given at tick 68, common read tick 1273). Last command: move, ok true, 69 units, to x 11470, y 250.
**Beta status of what is shown:**
- Move order reaching both peers (S-140, R-140-02): built and wired (lane F lockstep and lobby, VG-F-S140-CLICK); the S-140 play passes, host and guest read the same positions; not Seen (your verdict pending).
- Route line to the clicked spot (your 2026-10-13 note): not built, queued as VG-A-routeline.

## Removed today

| File | Verdict | Cite |
|---|---|---|
| `C-S001-ground-slope-and-blocked-band-close.png` | Rejected: "very mangled" (Westley, 2026-10-22); white lines are the slope midline bars, the group in the land is units behind the ridge whose 2D marks draw through the terrain, the steep face does not read as a wall; facing arrows asked, layer rings off in the land era (DEC-S001-facing-arrow, DEC-S001-no-layer-ring-land; FINDING-s001-marks-through-terrain, FINDING-s001-steep-face-flat) | C.md S-001 row |
| `C-S132-ground-units-close.png` | Approved: "Yes I can tell them apart" (Westley, 2026-10-22); clipping into the ground noted, fix for beta (FINDING-s132-body-clip, piece VG-C-unit-ground-fit) | C.md S-132 row |
| `P-S191-terrain-obeys-pass2-carved-routes.png` | Approved as a prototype: "Approved" (Westley, 2026-10-21, new rulings 6); S-191 and S-189 stay as they are | `P.md` row 3 (shot `shots/proto-terrain-obeys-2/obey_16000_1.png`); programme lane table, P layout engine and places row |
| `P-S191-terrain-obeys-pass2-small-canvas.png` | Approved as a prototype: "We won't have a map this small in reality, but approved." (Westley, 2026-10-21, new rulings 7); S-191 and S-189 stay as they are | `P.md` row 3 (shot `shots/proto-terrain-obeys-2/obey_8000_1.png`); programme lane table, P layout engine and places row |
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

# Shots waiting on Westley

How to answer: one word per picture, approve, reject, or a note. Where answers go: a message to the chat, or `answers.md` in the Batch A form; the clerk that records a verdict deletes the picture and its block in the same commit.

Each picture has one block under its file name, in this form: `**What you see:**`, `**Legend:**` (one line, what each colour and mark in the picture means), `**Judge:**` (a `**Camera:**` line may follow), `**Beta status of what is shown:**` with one line per feature.


## F-S140-click-move-order-obeyed.png

**What you see:** The player drags a box on the left of the match, clicks to the right, and 69 of the units move there in both peers (order tick 68; the host reads the common tick 1273, the guest reads tick 1401). The right side had blockers, so the play used the left corridor. The frame is the host's at tick 1297: 99 own units on screen, the 69 selected ones ringed in white in a loose cluster at the left, a tidy grid of unselected units at the middle right, and "69 selected" in the HUD at lower left. The drawn route line you asked for on 2026-10-13 is not built, so no path is drawn.
**Legend:** White ring: a selected unit (the HUD counts 69 selected). Blue outlines (dart, arrowhead, kite, hexagon, bar, square): your own units, one outline shape per unit type, in the space era's 2D view (`scenes/tactical_c/unit_visuals.gd` SHAPES, own colour (0.2, 0.6, 1.0)); the "blue diamonds" are the kite-shaped type. Small coloured ring under a unit: its layer (space era keeps layer rings). Green bar: hit points. Red-orange marks: the other faction's units. Light-blue glyphs: objective markers.
**Judge:** Does the move read as an order obeyed, with units leaving the box and heading for the click (S-140: "My orders reach every peer with no server in the middle")?
**Camera:** x 11950, y 250, scale 1.44, 1920x1080, tick 1297 (order given at tick 68, common read tick 1273). Last command: move, ok true, 69 units, to x 11470, y 250.
**Why this frame looks the way it does:** lane F's plays run the lobby match, which starts in the space era; the space battle view is 2D and top-down by design, so there is no landscape and no pitch. The land era is a launch flag (below).
**See it live (Westley 2026-10-22: motion is judged in the running game, DEC-S140-live-look):** in your checkout:
```
cd ~/Projects/ouroboros-manifold && git pull --no-rebase && make && make pipe/ouroboros_pipe
OM_GODOT_GUI=1 godot --path . -- --era greek_placeholder --seed 1
```
Menu to the mission, drag a box over some units, right-click the ground: the box's units walk there. For the two-peer version open two terminals: the same command (keep the `OM_GODOT_GUI=1` prefix; the `godot` on PATH is a wrapper that adds `--headless` without it) with `--net-local --net-local-lobby-port 7777 --net-local-udp-base 7800 --net-local-id 1` in the first and `--net-local-id 2` (same ports) in the second, type the host's lobby id into the guest's lobby, press start on the host, then order units in either window. One word back ("approved" or "rejected") on this row.
**Beta status of what is shown:**
- Move order reaching both peers (S-140, R-140-02): built and wired (lane F lockstep and lobby, VG-F-S140-CLICK); the S-140 play passes, host and guest read the same positions; not Seen (your verdict pending).
- Route line to the clicked spot (your 2026-10-13 note): not built, queued as VG-A-routeline.

## Removed today

| File | Verdict | Cite |
|---|---|---|
| `C-S004-ground-layer-crossing-close.png` | Rejected by rule: "We don't need to indicate layer changes with landscape color, layer changes will be clear based on vision distance" (Westley, 2026-10-22; DEC-S004-vision-not-colour); re-shot owed after VG-C-ground-one-colour and the VG-A-sightdisc amendment land, same camera (height 300, run-20261021T221300Z-zoomed tick 751) | C.md S-004 row |
| `C-S005-ground-sight-close.png` | Rejected: "Reject it, I'd like to see an improved version based on my feedback" (Westley, 2026-10-22; earlier "the screenshot looks good" with two findings); re-shot owed after VG-A-sightdisc and the E1k yaw amendment land, same camera (height 300, run-20261021T221300Z-zoomed tick 9774) | C.md S-005 row |
| `C-S001-ground-slope-and-blocked-band-close.png` | Rejected: "very mangled" (Westley, 2026-10-22); white lines are the slope midline bars, the group in the land is units behind the ridge whose 2D marks draw through the terrain, the steep face does not read as a wall; facing arrows asked, layer rings off in the land era (DEC-S001-facing-arrow, DEC-S001-no-layer-ring-land; FINDING-s001-marks-through-terrain, FINDING-s001-steep-face-flat); slope markers removed by his rule (DEC-S001-no-slope-markers) | C.md S-001 row |
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

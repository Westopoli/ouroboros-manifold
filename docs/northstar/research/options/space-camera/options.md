# The camera among five stacked sheets: options (T3, 2026-10-18)

Options, not decisions. The space landscape is five open-or-blocked sheets stacked 1,400 wu apart (E-17 S-246, R-246-01 to R-246-04, pass 6 approved 2026-10-06). The chosen camera is the Angle Rack with the Layer Peel and a flip key (E-16 S-103, Q-103-04 closed). The tactical band sits inside the stack, so from any pitch below top-down the sheets above the focus layer cover the units below (`research/space_landscape/README.md` line 104: "a design question in its own right"). Ruled already: a simple vision tube around the cursor or selection, built in lane D's first shot (Q-S3-01 (a), R-246-04), and layer indicators on every unit in that same shot (Westley, 2026-10-13). What is open is how the camera and the five sheets live together beyond the tube, and how a group's layers read from the map view (Q-103-06). Each option says what it adds to the ruled tube, what it costs, and what the lane D shot would show.

## Option A — Peel to the focus layer

The Layer Peel already lifts layers off one at a time. Here the peel is bound to the layer strip's focus: every sheet above the focus layer is drawn as a thin outline (its plate edges only, no body) across the whole view, and the tube is the local window where even the outline goes. Focus on 3 and sheets 4 and 5 become line drawings; focus on 5 and the stack is solid.
Adds: the whole view reads at once; the strip does the work the player already does. Costs: a player who keeps focus on 5 (the usual "see everything" habit) sees nothing of 1 to 4 but through the tube; outlines of two upper sheets over a busy lower sheet can read as noise. Shot: focus 3 with a fight on 2 under a heavy 4.

## Option B — Camera stays above the stack

The camera never enters the stack: its height floor is sheet 5 plus a margin, and pitch below 45 degrees tilts the whole stack instead (the sheets rotate as one body under the camera, the "snow globe"). Occluders between camera and focus layer are ghosted at a fixed low alpha everywhere, solid only at the tube's rim.
Adds: no camera-inside-geometry clipping, ever; the stack always reads as five sheets. Costs: the horizontal and shoulder vantages of the Angle Rack lose their meaning in space (they become stack tilts); ghosting at 20 to 30 percent alpha over three sheets stacks to a haze.
Shot: 45-degree tilt, focus 2, ghosted 3 to 5.

## Option C — Gap grows with pitch (exploded view)

Top-down, the sheets sit at their true 1,400 wu spacing. As the camera pitches toward horizontal, the gap between sheets grows (draft: up to 3x at the lowest pitch), so the stack opens like a drawer and every sheet shows a face. The tube still cuts the sheets above the focus layer around the cursor.
Adds: the Angle Rack's low angles become the way to read five layers at once, which is what the layer system wants to be read; nothing is hidden by design. Costs: unit positions on screen stop being true positions at low pitch (a unit on 5 draws higher than its ground truth), so picking and box-select need the inverse transform; the "one space at different scales" promise of S-108 and S-234 strains at the seam between tilted and top-down.
Shot: the same fight at top-down, 45 and 15 degrees.

## Option D — Cut-away cone (Q-S3-01 (c), for the record)

Everything above the focus layer is hidden inside the camera's view cone except a ring at the screen's edge. Named in Q-S3-01 as (c) and set aside for the simple tube; listed so the comparison is complete. Costs: the upper sheets stop existing for the player while focused low, the opposite of the layer system's point.

## Layer read from the map view (Q-103-06)

Independent of A to C: how a group's layers read when the camera is at the map band (S-234) and units are dots.
- (a) **Pins**: a rod per group, tall for 5, sunk for 1, one bead per occupied layer (the Sand Table option as drawn).
- (b) **Stacked slices**: the group's icon is a short stack of up to five slices, lit for occupied layers, so a group split across 2 and 4 reads as two lit slices with a gap.
- (c) **Colour bands**: the icon's rim takes the layer strip's colour for its single layer; a split group alternates two rims and shows a small "split" mark.
- (d) **Sheet silhouettes**: at the map band the five sheets draw as faint parallel planes in perspective and each group's dot sits on its sheet, so layer is read by position, the same way as in play. Pairs naturally with C.
Westley asked for more than pins (Q-103-06); (b) and (d) are the two the Architect would prototype beside (a). Each is a one-day mockup in `scenes/mockups/layers/` (pass 2 exists) with the three cases: one group on 3; a group split 2 and 4; two groups on 1 and 5 at the same spot.

## What is asked

T3-1: which of A, B, C the lane D shot should show first (one; the tube is in all three). T3-2: which two of (a) to (d) to mock up beside pins for Q-103-06. T3-3: whether C's exploded gap is worth its picking cost at all (a yes keeps it in the running; a no retires it before any mockup). Candidates sit in the decision pack (B20).

# What Westley decides, 2026-10-21

Answer in answers.md, one line per key: `<key>: <approve | reject | a | b | c | note>`. Anything not listed here is already decided or is the Architect's.

## 1. Pictures

### P6 Land that fits a layout: carved routes (S-191, S-189)

![](../../story_reviews/westley/P-S191-terrain-obeys-pass2-carved-routes.png)

**What you see:** A top-down prototype of a land map with flat base circles, an objective, a choke bar in the middle, and orange and blue route lines; pink dots mark the cells the generator carved to make routes. Every point now has its narrow and wide routes.
**Judge:** The carved routes run as parallel lanes side by side, like a rail yard; is carving the right direction with a better path rule, or should routes come from the landforms?
**Beta status of what is shown:**
- Land that fits a requested layout, with routes (S-191, S-189): built as a prototype only, awaiting your verdict; in the game it is queued (not built), not scheduled (you said the layout engine comes first).
- The layout engine that asks for those places: stub (built, not yet called by the game).

### P7 Land that fits a layout: small map (S-191, S-189)

![](../../story_reviews/westley/P-S191-terrain-obeys-pass2-small-canvas.png)

**What you see:** The same prototype on a small map: base circles kept apart by scaling the pads down, steep ring slopes under the walking limit, and the same carved lanes in yellow and pink.
**Judge:** Do the pads and routes still read on the small map, or does the carving swamp it?
**Beta status of what is shown:**
- Small-map pads and routes (S-191, S-189): built as a prototype only, awaiting your verdict; in the game queued (not built), not scheduled.

### P8 Units close on the ground (S-132)

![](../../story_reviews/westley/C-S132-ground-units-close.png)

**What you see:** Your force from 300 wu up, standing on an orange ridge under a pink steep wall: darts and arrowheads on the left, kites and wide hexagons on the right, each flat blue body 45 to 80 px across with a small dark icon and a yellow layer ring on top. Rows of loose blue arrowheads float above and below the force, away from any unit (the squad markers of the dart and arrowhead types, drawn in a flat map projection, so they do not sit on the 3D ground).
**Judge:** Can you tell the unit types apart by shape at a glance, at this size (S-132: "Every unit type has a shape I can read at a glance in any era")?
**Camera:** height 300 wu (the nearest wheel step to the ground; 1.80 px per wu at the centre), 1920x1080, seed 1, tick 2399. Body size measured on 71 blue shapes in the frame: median 55 px wide, 20 to 80 px, median 27 px tall (flat shapes seen at 50 degrees); the dark icon on top is 24 px. Your scaling question (FINDING-s246-unit-scale, land view) is still open: at the old height 3000 the same body is 4 px.
**Beta status of what is shown:**
- Unit shapes on the 3D ground (S-132): built and wired (lane C ground 3D, C6; scale fix VG-C-unitscale at 53ede72), the lane C plays pass; not Seen (your verdict pending).
- Squad markers for the dart and arrowhead types: built, but drawn in the flat map projection so they float off the units in the ground view (finding, no piece yet).

### P9 Slope with midline and blocked ground (S-001)

![](../../story_reviews/westley/C-S001-ground-slope-and-blocked-band-close.png)

**What you see:** A steep pink wall (ground that blocks the layer) rising behind your force, a flat orange band your units stand on, green terraces dropping away at the left, and two long white bars across the ground where a slope joining two layers is marked at its midline; the bar disappears where the ground rises in front of it. Your units stand at the foot of the wall as small round icons, because their flat blue bodies lie nearly edge-on and half buried in the steep ground.
**Judge:** Can you see where terrain blocks a layer and where a slope joins two layers, so you can choose to go over, go around or hide (S-001)?
**Camera:** height 300 wu (1.80 px per wu at the centre), 1920x1080, seed 1, tick 3006. Unit bodies are not readable here (edge-on on the steep face); only the 24 px icons read. Body size on level ground is in the S-132 frame (median 55 px wide).
**Beta status of what is shown:**
- Slopes drawn with a midline and blocked ground tinted pink (S-001, R-001-06): built and wired (lane C ground 3D, C7), the S-001 play passes; not Seen (your verdict pending).
- Flat unit bodies on steep ground: built, they lie edge-on and half buried there (finding, no piece yet).

### P10 Sight and the dimmed outside (S-005)

![](../../story_reviews/westley/C-S005-ground-sight-close.png)

**What you see:** Nineteen selected bombards and bastions (white rings) standing on open green ground beside the settlement's white blocks, with a bright lit area around them and a dimmed, darker region beyond a curved edge at the right of the frame, where the white slope bars show through grey. The edge is a circle on the screen centred on the group, not an ellipse on the ground, and the 24 px icons sit on top of the flat bodies.
**Judge:** Do you see less outside your units' sight, with a clear edge between what they see and what they do not (S-005: "I see less on other layers than on my own, and nothing three layers away, unless I hold a vantage")?
**Camera:** height 300 wu (1.80 px per wu at the centre), 1920x1080, seed 1, tick 9774; the lit edge is about 720 px from the group centre. Unit bodies are hidden under the 24 px icons and white selection rings. At this height the dim vanishes whenever an own unit stands far south of the camera (the sight circle of a unit near or behind the camera comes out huge), so the group was first sent south of every other unit to get this edge (finding, no piece yet). No separate darker band for a neighbouring layer is drawn: the dim is one overlay outside the sight circles (R-089-03), so this frame shows the edge but not the layer rule.
**Beta status of what is shown:**
- Sight circles and the dim outside them (S-005, R-089-03): built and wired (lane A fog layer, A1 to A21), the lane A plays pass; not Seen (your verdict pending).
- The dim at close zoom: built, missing in most close positions (finding, no piece yet).

### P11 Crossing toward another layer (S-004)

![](../../story_reviews/westley/C-S004-ground-layer-crossing-close.png)

**What you see:** All 176 units selected (white rings) walking up a ridge in a long column, from the orange band at lower left to the brown band at upper right; the small ring under each unit changes from yellow to purple as it passes onto the upper layer, and the white midline bars of other slopes lie across the ground at the left. The column is thin and the units are single icons on the 3D ground, so the halfway line itself is not marked for the crossing.
**Judge:** Is a layer change on a slope visible, with the halfway line a place you can see and hold (S-004)?
**Camera:** height 300 wu (1.80 px per wu at the centre), 1920x1080, seed 1, tick 751 (the play's own order: every own unit sent to the top edge of the nearest slope, stepped in 25-tick chunks; these units crossed a ridge slope on the way, not the slope the play aimed at). No unit is in the timed transfer state, because walkers cross by position (R-004-06). Unit bodies are under the 24 px icons; body size in the S-132 frame.
**Beta status of what is shown:**
- Layer change on a slope (S-004, R-004-06): built and wired (lane C ground 3D, C7; S-004 play fix at bfd7f1c), the S-004 play passes; not Seen (your verdict pending).
- The halfway line as a marked place for one crossing: stub in this view (only the long midline bars are drawn, none picked out for the crossing).

## 2. Questions

### Q-B23b-01 Which renderer is the look?

Under the richer lighting the 3D ground wants, the see-through faction shells wash out the system dots (our pixel check reads 6 of 18); under the simpler lighting the checks use, the dots read fine. (picture ruled 2026-10-21; see the lane row).

(a) Ship the richer lighting, and the pixel check gains a run on it.  
(b) The wash is the approved look.  
(c) A small fix makes the shells fainter over the dots (the Architect's lean, shipping the richer path).

unblocks: the galaxy pixel test and fix piece.

### Q-C2-5-01 Owner colour at the dot

In the galaxy frame (P1), 14 of the 38 owned systems do not show their owner's colour at the dot: a neighbouring region's glow covers them or the additive light whitens the hue.

(a) That is the look you want; the colour test samples the wrong thing for those dots.  
(b) A glow must not cover a neighbour's dot.  
(c) The dot's core keeps its hue under the light.

unblocks: the galaxy pixel test's margin (it passes by one dot today).

### Q-156-02 Lab pass marks

The lab's ten draft pass marks (mirror tolerance, skill beating the noise, rank agreement, stacking, dominance, dead skills, counters) are unconfirmed.

(a) The draft marks as written.  
(b) You set each of the ten (opens ten per-mark questions).  
(c) Report only, no pass or fail, until you confirm them.

unblocks: lab rev 2 runs with real marks instead of drafts.

### Q-246-02 Who sets asteroid density?

A space mission needs an asteroid-field density; the mockup uses one value (35). You asked on 2026-10-13 to see a prototype of the options first. (picture ruled 2026-10-21; see the lane row) (the prototype shot is the one owed for this).

(a) One default for every mission.  
(b) The region decides, tight in some and open in others, within a range.  
(c) The mission type decides.

unblocks: the asteroid density work.

### Q-082-03 How does a big roster keep its shape?

With 20 to 40 unit types per era, how do the three categories and six roles stretch?

(a) Every unit belongs to one of the three categories and one of the six roles; the orderings hold within each category (recommended).  
(b) Categories only, roles free.  
(c) A free roster, balanced by the scoring check alone.

unblocks: the spec for the 20-to-40 type roster.

### Q-147-01 Name the land era and the roster

The land era is "The Marble Reach" as a placeholder; its name, setting, tone and scale, and the order of eras after the first two, are unwritten. Give your words, or ask the Architect to draft candidates; also write the roster in order and mark each era earnable or purchase-only.

unblocks: the era pack form, the land era's identity and the roster the store sells.

### Q-100-01 Firing arc

You ruled on 2026-10-13 that a unit fires only inside an arc about its facing. Width, and whether it varies by type, are yours after the lab shows the effect (so this one comes after the lab chart).

(a) One arc for every type, 120 degrees as a draft the lab sweeps.  
(b) Width per category: Strike wide, Line medium, Siege narrow.  
(c) An arc for Siege only; the others fire all round.

unblocks: the final arc rule.

### Q-208-01 Can a force hold fire?

A guard steps up to engage and returns to its post. Nothing lets you order a force to wait unseen and not shoot.

(a) A hold-fire setting on the guard stance.  
(b) A separate hold-fire order.  
(c) No hold fire; an ambush is made by going silent alone.

unblocks: the movement lane, after the lab data.

### Q-228-01 Who gets a ledger character in a team?

A chapter has one commander today; how the economy seat of a pair and each sub-commander enter the chapter record and the ledger is unsettled.

(a) Only the commanding seat has a ledger character; the economy seat has none.  
(b) Every player has a ledger character and a lineage.  
(c) Other: your words.

unblocks: pairs reaching the chronicle.

### Q-149-01 How is an era earned?

Eras can be earned by play as well as bought; the condition is not set.

(a) Complete a 10-chapter campaign in the preceding era.  
(b) Reach Tier 3 in any campaign.  
(c) Other: your words.

unblocks: store work, after the beta.

### Q-149-02 Which eras are purchase-only?

Which eras are exclusive to purchase and which earnable, and the naming of the base three on the store. Give your words.

unblocks: store work, after the beta.

### B22 part 1 Show the internal figures on the website?

The website refresh draft (built, not deployed) has a page on how the game is made. Does it publish the programme's internal figures?

(a) Yes: publish the real figures.  
(b) No: keep them out.

unblocks: nothing in the queue; decide with the next three.

### B22 part 2 Your name and quotes on the site?

May the same draft name you and quote you?

(a) Yes: name and quotes appear.  
(b) No: the site speaks anonymously.

unblocks: nothing in the queue.

### B22 publish Publish the site at all?

The draft shows the galaxy view, both landscape engines, the walking prototype and the method page. Nothing deploys until you say.

(a) Yes: publish after your read.  
(b) No: hold it.

unblocks: nothing in the queue.

### doc branch method ask 1 Is the method page the public face?

A branch holds an outsider-readable page on how the game is built (tests first, prototypes approved before planning, a fight-measuring lab, ten draft pass marks). The branch verdict is "land after named edits".

(a) Yes, it stays an outsider page.  
(b) It becomes an internal page.  
(c) Not wanted.

unblocks: how openly the project explains itself; nothing in the queue waits on it. Decide with the three site questions.

## 3. Asked in chat, still open

### C1 Lab fight length
The lab's "attackers break a held line" fight runs 229 s against your 150 to 200 s window.
(a) widen the window to 230 s; (b) keep the window, the lab landing waits for a faster fight; (c) replace the fight.
unblocks: the whole lab rev 2 landing.

### C2 Lab speed
The rev 2 lab runs about 82 s per run in its Python against your 30 s mark (3.9 times slower than rev 1).
(a) accept 82 s now and speed it up after; (b) hold the landing until under 30 s; (c) a new mark.
unblocks: the same landing.

### C3 Known-red list for the gate
Let the merge gate carry a short list of tests known red for a named, recorded reason, so a landing is not rejected by a red that is already on record. yes / no.
unblocks: two Lane T landings and the lab landing.

### C4 Lab positive control
The lab's "a planted bad fight trips the detector" control reads green on main when it should trip.
(a) no lab landing until it trips; (b) land with it listed red and fix it next.
unblocks: the lab landing order.

### C5 Strongpoint damage (register Q-218-08)
A strongpoint is captured or destroyed, but nothing says units shoot it and take away its hp. Do units damage strongpoints?
(a) yes, by fire; rubble at zero hp; capture works as it does now; (b) capture only, never shot, and the unused damage code is deleted; (c) only the Siege category damages them.
unblocks: the strongpoint-damage piece.

### C6 Onboarding weights (register Q-074-05)
Your onboarding answers carry a weight for each mission kind and a mark for rare kinds, but mission selection does not read them yet (preference and difficulty are being wired regardless). How should they weigh the pool of candidate missions?
(a) the weights multiply each mission kind's score and the rare marks add the rare kinds to the pool; (b) they only feed the briefing's foreshadowing; (c) dropped from the design.
unblocks: the weights part of the onboarding work.

### C7 Housekeeping
Three yes/no, answer each as `C7i`, `C7ii`, `C7iii`:
(i) the clerks' scratch space: raise the /tmp quota, or keep all scratch under ~/Projects/om-push/tmp-*;
(ii) discard the dirty lab diagnostic worktree labdiag (29 files of uncommitted edits on an old lab base, believed throwaway, unreviewed), or have an engineer read its diff first;
(iii) widen the worktree-removal rule to treat Godot .import sidecars and dist/ as build outputs and to remove unmarked worktrees that are clean, on origin and older than three days.

### C8 Failed-play frames
Four ground-era story plays the reviewer judged "no", still pending with you, with no picture in your folder (all lane C, one run):
- S-236 (fully zoomed-in ground map): the zoom never reached the close-up band, so the shot shows the whole island from far away as colour-banded patches with tiny hexagon units; no up-close land detail.
- S-001 (slopes and blocked ground): no slope or blocked-ground marking exists; the opening frame shows coloured terrain bands but nothing marking blocked layers.
- S-004 (crossing layers): no unit entered a layer transit within 1000 ticks of a cross-map move, so no transit or halfway line was ever shown.
- S-132 (unit types readable): the force is collapsed or partly undrawn; four clusters of stacked identical hexagons with big cyan rings, types not distinguishable by shape.

## 4. Drafts in force unless you veto

- DRAFT-b25-star-ref: 1080 px, 45 degree fov (Architect, 2026-10-21)
- DRAFT-startforce-pocket 400 wu, DRAFT-startforce-clamp 0.15, DRAFT-startforce-offset 200 wu (Architect, 2026-10-20)
- DRAFT-c25-patch-radius: 3 (Architect, 2026-10-21)
- Places lane drafts of rev 6a: DRAFT-shape-harm 0.5, DRAFT-first-ring-spread 2, DRAFT-field-cost-share 15 to 55 percent (Architect, 2026-10-21)
- Age-10 lots scope narrowing (Architect, 2026-10-21)

Parked by you (8): see batch_closed.md.

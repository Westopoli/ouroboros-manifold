# The batch, closed rows (moved out of batch.md on 2026-10-21)

Westley, 2026-10-21: "the doc was absurdly long, and many of them I've already answered." `batch.md` now holds only what is his: the open design questions and the parked ones. Everything else from the 2026-10-18 batch is here, verbatim, grouped by who took it (classes from `triage_2026-10-19.md`). Nothing is deleted from the record; it moved. Each section carries a comment naming where it stood in the old `batch.md`.

Classes below: Answered (the shots and Q-069-03), Implementation, Already decided, Duplicate, Moot, Parked (full text), and the old front matter and section intros.

---

## Answered 2026-10-18, applied 2026-10-20 (Batch A, the shots), and Q-069-03 answered 2026-10-19

Taken by: Westley. Shots 1 to 11 were answered in his `answers.md` and applied by commit 7587994b (2026-10-20). Shots not yet judged stay in the page table `docs/northstar/story_reviews/westley/README.md`; they are listed here only as the record of the first batch. Q-069-03 was answered by Westley on 2026-10-19 ("Chroncile: accepted, time varying is ok it is like a book") and closed in the register as (a), the map holds until the entry has printed.

<!-- batch.md: Batch A, whole part -->

# Batch A: 22 shots to judge offline

A "layer" is a height band units sit in; "ground era" is the land-map look.

### 1. Galaxy after the pull-back — `P-S108-galaxy-moment-after-pullback.png`
**Story.** "Mission pulls back into the galaxy and pushes into the next mission without a cut." [S-108]
**What you are looking at.** The prototype of the transition, at the moment the camera has left the battlefield and the galaxy is on screen: a spiral of star dots on the left, the chronicle scroll with three lines on the right, a Proceed button. Since you saw it, the battlefield's point of light is about 13 times smaller, below one star dot (you asked 10 to 20).
**What approved means here.** Yes sends the transition on to be built into the game; no says how much smaller.
<sub>key: P-S108-galaxy-moment-after-pullback.png | stories S-108</sub>

### 2. Mid pull-back, star field — `P-S108-mid-pullback-star-blobs.png`
**Story.** "Mission pulls back into the galaxy and pushes into the next mission without a cut." [S-108]
**What you are looking at.** Mid pull-back. The battlefield is the tiny brownish speck near the middle, among dim round stars (the last version drew blobs). Does it read as stars and distance?
**What approved means here.** Yes keeps the star field; no sends back star size or density.
<sub>key: P-S108-mid-pullback-star-blobs.png | stories S-108</sub>

### 3. Terrain obeys the layout, failing map — `P-S191-terrain-obeys-seed1-no-routes.png`
**Story.** "Bases, objectives and resources sit where the land puts them." [S-191] "Some ground is too steep to walk, and slopes are the ways between layers." [S-189]
**What you are looking at.** Top-down prototype of a map about 700 units wide, where the generator shapes land to fit a requested layout: flat pads (circles), a choke (the bar in the middle, asked about 20 units wide, got about 18) and a lookout. All came out. Walkable routes did not: red circles mark points no wide road reaches.
**What approved means here.** Yes means the generator must carve routes itself, not only check for them, and that gets built; no sends back how pads, choke and wall look.
<sub>key: P-S191-terrain-obeys-seed1-no-routes.png | stories S-191, S-189</sub>

### 4. Terrain obeys the layout, passing map — `P-S191-terrain-obeys-seed3-pass.png`
**Story.** "Bases, objectives and resources sit where the land puts them." [S-191] "Some ground is too steep to walk, and slopes are the ways between layers." [S-189]
**What you are looking at.** Another seed, the one that passed: every point has narrow routes (orange) and a wide one (blue); the choke is about 8 units wide, about 11 asked.
**What approved means here.** Yes accepts this as the target look for land maps; no says what about the choke or routes does not read.
<sub>key: P-S191-terrain-obeys-seed3-pass.png | stories S-191, S-189</sub>

### 5. Ground opening view, four groups — `A-S103-start-view-ground-era.png`
**Story.** "A free camera I manage myself, with the Angle Rack, the Layer Peel, and a flip key." [S-103]
**What you are looking at.** The first frame of a ground mission in 3D: a ridge under a grey sky, four groups in tinted discs, layer buttons on the right. Does this start view fit the four groups in? The bottom-right disc runs off the bottom edge.
**What approved means here.** Yes keeps this opening camera; no sends it back to be reframed.
<sub>key: A-S103-start-view-ground-era.png | stories S-103</sub>

### 6. Regional galaxy, new layout — `B-S106-regional-galaxy-b24-layout.png`
**Story.** "A 3D star map where territory glows, borders touch, and war flashes." [S-106]
**What you are looking at.** The galaxy map close up: discs for regions, soft glows for territory, curved links. Since last time, linked regions sit next to each other and same-owner regions cluster. No faction name or war flash yet.
**What approved means here.** Yes adds names and flashes; no sends the clustering back.
<sub>key: B-S106-regional-galaxy-b24-layout.png | stories S-106</sub>

### 7. Local focus on a system — `B-S107-local-focus-b24-layout.png`
**Story.** "Pan, zoom, orbit, focus a system, pick out a faction." [S-107]
**What you are looking at.** The camera close on three regions, two red and one blue, on a flat red-brown ground. Neighbours are at a readable distance. No faction list, panel or label yet.
**What approved means here.** Yes adds labels and panels on this; no sends back range or ground.
<sub>key: B-S107-local-focus-b24-layout.png | stories S-107</sub>

### 8. Settlement rising — `E-S237-settlement-look-after-E1k.png`
**Story.** "A base starts as ground under construction and rises stage by stage, spreading and thickening." [S-237]
**What you are looking at.** A settlement: buildings at different levels, laid out irregularly along the contours. Units are still stacked, and only the bottom third of the settlement is in view. Your earlier rejection checklist applies.
**What approved means here.** Yes moves on to spacing units; no sends the building look back.
<sub>key: E-S237-settlement-look-after-E1k.png | stories S-237</sub>

### 9. Sim viewer, tick mode — `V-SV3-sim-viewer-tick-mode.png`
**Story.** No story: a developer tool for watching the simulation run on its own.
**What you are looking at.** At tick 50: factions as coloured shapes over a region graph, one region's value bars, a faction list, an event log.
**What approved means here.** Yes keeps this as the tool's tick view; no says what is unreadable.
<sub>key: V-SV3-sim-viewer-tick-mode.png | stories SV-3</sub>

### 10. Sim viewer, mission mode — `V-SV3-sim-viewer-mission-mode.png`
**Story.** No story: the same developer tool.
**What you are looking at.** The same map at tick 100 after a mission: your picked result beside the simulation's (both partial success), the region's changes, a mission log.
**What approved means here.** Yes keeps this mission view; no says what to change.
<sub>key: V-SV3-sim-viewer-mission-mode.png | stories SV-3</sub>

### 11. Ground opening frame, five stories — `C-S001-S004-S005-S010-S132-ground-opening-frame.png`
**Story.** "Terrain blocks some layers in some places, so I choose to go over, go around, or hide in the blocked layers." [S-001] "Changing layers takes time and exposes the unit; on a slope the halfway line is a place I can see and hold." [S-004] "I see less on other layers than on my own, and nothing three layers away, unless I hold a vantage." [S-005] "A unit on a higher layer sits visibly higher on screen, and rises or drops when it changes layer." [S-010] "Every unit type has a shape I can read at a glance in any era." [S-132]
**What you are looking at.** The ground opening frame: four groups on a ridge. No slope marking, layer change, rise or drop is drawn, and unit types do not differ by shape. Is this ground look wanted at all?
**What approved means here.** Yes builds the missing drawings; no sends the look back.
**Known flaws, not for judging.** The plays for S-001 and S-004 failed to draw their parts, for reasons since fixed.
<sub>key: C-S001-S004-S005-S010-S132-ground-opening-frame.png | stories S-001, S-004, S-005, S-010, S-132</sub>

### 12. Zoomed all the way in — `C-S236-ground-zoomed-in-map-band.png`
**Story.** "The ground is drawn in deep detail up close and as the shape of the land far away, with no pop between." [S-236]
**What you are looking at.** The camera pushed in as far as it goes, yet the ground still looks far away: colour-banded contours, units as tiny hexagons.
**What approved means here.** A no sends it back to draw close-up detail.
**Known flaws, not for judging.** The play failed on the detail level; judge the contours.
<sub>key: C-S236-ground-zoomed-in-map-band.png | stories S-236</sub>

### 13. Units after a move order — `C-S207-ground-units-after-move-order.png`
**Story.** "Routes follow the buildings that rise and fall, the slopes and the steep ground, and no unit is stuck in terrain or walks off the map." [S-207]
**What you are looking at.** After a move order, units sit in four overlapping clumps on the slope. Do they look like they follow the ground?
**What approved means here.** A no sends back the clumping.
<sub>key: C-S207-ground-units-after-move-order.png | stories S-207</sub>

### 14. Sight after a few seconds — `A-S005-S091-ground-sight-after-20-ticks.png`
**Story.** "I see less on other layers than on my own, and nothing three layers away, unless I hold a vantage." [S-005] "An elevated position sees farther." [S-091]
**What you are looking at.** The opening frame a few seconds in. Is any fog edge or layer dimming visible? The model reviewer saw none.
**What approved means here.** Yes keeps sight as drawn; no sends back fog and dimming.
<sub>key: A-S005-S091-ground-sight-after-20-ticks.png | stories S-005, S-091</sub>

### 15. Plain opening frame, three stories — `A-S007-S075-S088-ground-plain-opening-frame.png`
**Story.** "A tall obstacle hides units on more layers than a short one; cover hides but never protects or blocks." [S-007] "One primary objective I can see progressing, up to three secondary ones." [S-075] "A Strike squad reads as a small group, a Siege unit as a heavy asset, every ability has a cue." [S-088]
**What you are looking at.** The same opening frame. No cover drawn; squads do not read as small, siege not as heavy.
**What approved means here.** Yes builds the cues on this; no sends back the baseline.
<sub>key: A-S007-S075-S088-ground-plain-opening-frame.png | stories S-007, S-075, S-088</sub>

### 16. Objectives after a while — `A-S075-ground-objectives-after-200-ticks.png`
**Story.** "One primary objective I can see progressing, up to three secondary ones." [S-075]
**What you are looking at.** Eleven seconds in, the top-left box says only "Primary objective 0%": no secondaries, no progress.
**What approved means here.** A no sends it back to show secondaries and progress.
<sub>key: A-S075-ground-objectives-after-200-ticks.png | stories S-075</sub>

### 17. Opening frame, nothing selected — `A-S095-S101-S105-ground-opening-frame-nothing-selected.png`
**Story.** "A selection moves at its slowest member's pace and arrives in its shape; I split off a faster group when I choose." [S-095] "I see units turn, slow behind blockers, and settle into their slots." [S-101] "Click, box-select, bind groups, and never an all-army button." [S-105]
**What you are looking at.** The opening frame, nothing selected or moving, so no group move, turn or box selection shows.
**What approved means here.** Yes keeps this start.
**Known flaws, not for judging.** All three plays failed to start the action; judge only the resting frame.
<sub>key: A-S095-S101-S105-ground-opening-frame-nothing-selected.png | stories S-095, S-101, S-105</sub>

### 18. Move ordered, empty panel — `A-S096-ground-move-ordered-empty-panel.png`
**Story.** "Move is movement, attack-move fights along the way, attack-target commits, ability is a button." [S-096]
**What you are looking at.** Seconds after a move order. The groups look as before and the selection panel is empty.
**What approved means here.** A no sends back the panel.
**Known flaws, not for judging.** The play failed before the order registered.
<sub>key: A-S096-ground-move-ordered-empty-panel.png | stories S-096</sub>

### 19. First frame, HUD — `A-S104-ground-first-frame-hud.png`
**Story.** "A lean HUD that shows what I need and stays out of the way." [S-104]
**What you are looking at.** The first frame, judged on screen furniture only: objective box, timer, End Mission, layer buttons, a health bar. Is it lean?
**What approved means here.** Yes keeps this HUD as the base; no says what to cut or move.
<sub>key: A-S104-ground-first-frame-hud.png | stories S-104</sub>

### 20. Camera off the map, no shots — `A-S134-ground-camera-off-map-no-shots.png`
**Story.** "Shots travel, hits bloom, nothing twitches." [S-134]
**What you are looking at.** Green ground, grey sky, no shot drawn: the camera is past the map edge.
**What approved means here.** Nothing to approve on the look.
**Known flaws, not for judging.** The camera wandered off the map; this shot shows nothing of the story.
<sub>key: A-S134-ground-camera-off-map-no-shots.png | stories S-134</sub>

### 21. No ability slot — `A-S135-ground-ability-slot-missing.png`
**Story.** "Every ability reads at a glance as an ability in progress." [S-135]
**What you are looking at.** The opening scene, where the selection panel should show an ability slot. It does not.
**What approved means here.** A no sends back the slot to be drawn.
**Known flaws, not for judging.** The play did not reach an ability in use.
<sub>key: A-S135-ground-ability-slot-missing.png | stories S-135</sub>

### 22. No dying ship seen — `A-S136-ground-no-wreck-camera-off-map.png`
**Story.** "A dying ship flares, burns, drifts, and darkens." [S-136]
**What you are looking at.** The same off-map view as shot 20, no ship dying.
**What approved means here.** Nothing to approve on the look.
**Known flaws, not for judging.** The camera was off the map, so the wreck was never seen.
<sub>key: A-S136-ground-no-wreck-camera-off-map.png | stories S-136</sub>


### 23. Terrain obeys the layout, pass 2, carved routes — `P-S191-terrain-obeys-pass2-carved-routes.png`
**Story.** "Bases, objectives and resources sit where the land puts them." [S-191] "Some ground is too steep to walk, and slopes are the ways between layers." [S-189]
**What you are looking at.** The same map as picture 3, after the generator was taught to carve routes instead of only checking for them. Every point now has its four narrow routes (orange) and a wide one (blue); the magenta dots are the cells it cut. All six test maps pass with no number loosened. The flaw to judge: the carved routes run as parallel lanes side by side, a rail yard, not roads that follow the land.
**What approved means here.** Yes means carving is the right direction and the next pass makes the lanes diverge and use valleys; no means routes should come from the landforms themselves and carving only fills the last gap, or a direction of yours.
<sub>key: P-S191-terrain-obeys-pass2-carved-routes.png | stories S-191, S-189</sub>

### 24. Terrain obeys the layout, pass 2, the small map — `P-S191-terrain-obeys-pass2-small-canvas.png`
**Story.** As above.
**What you are looking at.** The small map (about 350 units wide) that failed in pass 1 because pads and walls overlapped: pads are now kept apart, slopes around them stay walkable, the same carved lanes.
**What approved means here.** Yes accepts the small-map scaling; no says what is wrong at this size.
<sub>key: P-S191-terrain-obeys-pass2-small-canvas.png | stories S-191, S-189</sub>

<!-- batch.md: Batch B item 1 -->
### 1. Does the map wait?
**Story.** "I watch the map change on the left while the scroll writes itself on the right, and I can stop and read." [S-069]
**Today.** Chronicle entries print one at a time. Sometimes the galaxy replay reaches the next change on the map while an entry is still printing. What the player sees in that moment is unsettled.
**The choice.**
(a) The map holds still until the entry finishes, like a book with pictures.
(b) The map runs on at 2 ticks per second and the scroll catches up, so an entry may describe a change the map already showed.
**Lean.** (a). Text and picture stay in step, which is what the story promises.
<sub>key: Q-069-03 (B9)</sub>

---

## Implementation (the Architect's)

Taken by: the Architect, recorded "Architect, 2026-10-19 (implementation; Westley may veto)"; veto in one line. The triage names each default; none of these has yet been written into the register or the ledger row by row.

<!-- batch.md: Batch B item 5 -->
### 5. Which camera view first
**Story.** "A free camera I manage myself, with the Angle Rack, the Layer Peel, and a flip key." [S-103] (Angle Rack: the camera's preset viewing angles. Layer Peel: lifting layers away one at a time.)
**Today.** In space the battlefield is five flat sheets stacked about 60 unit-widths apart. From any angle below straight-down, the sheets above the one you are looking at cover the units beneath. A simple see-through tube around the cursor is already decided; the question is what else helps. The next camera shot shows one option.
**The choice.**
(A) Peel to the focus layer: sheets above your focus draw as thin outlines across the whole view, and the tube clears even those. A player focused on the top sheet sees little below.
(B) The camera stays above the stack and tilts the whole stack like a snow globe; blockers are ghosted. No clipping ever, but the low angles lose their meaning and the ghosting can haze.
(C) The gap between sheets grows as the camera tilts, like a drawer opening, so every sheet shows a face. Best for reading five layers, but on-screen positions stop being true positions at low tilt, so picking units needs extra care.
**Lean.** A. It uses the layer strip the player already knows.
<sub>key: T3-1 (B20)</sub>

<!-- batch.md: Batch B item 6 -->
### 6. Layers seen from the map view
**Story.** "I zoom from a single unit to the battlefield's map view in one smooth drawing, and the zoom stops there." [S-234]
**Today.** Zoomed out to the Sand Table (the tabletop view of the battlefield), units are dots, so which layer a group is on is hard to read. You asked for more than pins on rods. Each mockup is about a day's work.
**The choice.** Pick two.
(a) Pins: a rod per group, tall for the top layer, sunk for the bottom, a bead per occupied layer.
(b) Stacked slices: a short stack of up to five slices, lit for occupied layers; a split group shows a gap.
(c) Colour bands: the icon's rim takes the layer's colour; a split group alternates two rims with a small split mark.
(d) Sheet silhouettes: the five sheets draw as faint parallel planes and each dot sits on its own sheet.
**Lean.** (b) and (d), built beside the pins.
<sub>key: T3-2 / Q-103-06 (B20)</sub>

<!-- batch.md: Batch B item 7 -->
### 7. Is the opening drawer worth it?
**Story.** No story yet.
**Today.** Camera option C spreads the sheets apart when you tilt, up to about three times the spacing as a first guess. It reads layers best, but picking units would need a correction for the false positions.
**The choice.**
Yes: keep option C in the running for a mockup.
No: retire it now, before any mockup.
**Lean.** Yes.
<sub>key: T3-3 (B20)</sub>

<!-- batch.md: Batch B item 10 -->
### 10. Missions with no matching layout
**Story.** "Every mission is a recognizable military situation with its own trigger, shape, and map." [S-073]
**Today.** Four of ten mission types (Suppression, Counterinsurgency, Interception, Evacuation) fit none of the surviving layouts.
**The choice.**
(a) Draw new layouts for them now.
(b) Compose them later from kit situations.
(c) They use places found in the terrain only, with no layout.
**Lean.** None stated.
<sub>key: B21 third question (library audit item 4)</sub>

<!-- batch.md: Batch B item 14 -->
### 14. Who takes over a supreme commander?
**Story.** "A fallen commander's place is taken by a relative nearby if one exists." [S-061]
**Today.** When a faction's supreme commander dies, a successor appears. The written rule says in the faction's first region, which may be nowhere near the death.
**The choice.**
(a) In the dead commander's region; the rule is rewritten to say so.
(b) In the faction's lowest-numbered region, as the rule reads now.
(c) In the faction's home region.
**Lean.** (a). A successor near the fallen fits the story.
<sub>key: ALG-49 (B23)</sub>

<!-- batch.md: Batch B item 17 -->
### 17. Where does the method page live?
**Story.** No story yet.
**Today.** The page ends with a rule that the method directory wins over other docs. In the directory where it would land, that would make it outrank the project's own README and plan.
**The choice.**
(a) Land it in the northstar directory.
(b) Land it elsewhere so it does not outrank them.
**Lean.** None stated.
<sub>key: doc branch method ask 2</sub>

<!-- batch.md: Batch B item 19 -->
### 19. Test line against column?
**Story.** No story yet.
**Today.** Groups move at the slowest member's pace, which may change how a line fares against a column.
**The choice.**
(a) Queue a lab run.
(b) No.
**Lean.** None stated.
<sub>key: doc branch doctrine ask 2</sub>

<!-- batch.md: Batch B item 20 -->
### 20. The ranking of principles
**Story.** No story yet.
**Today.** The note ranks its ten: chokes and frontage, formation, matchup, height, recon, vertical, counter-cases, force ratio. The author chose this order, not the source.
**The choice.**
Accept, amend, or leave unranked.
**Lean.** None stated.
<sub>key: doc branch doctrine ask 3</sub>

<!-- batch.md: Batch B item 21 -->
### 21. Is the era form the right shape?
**Story.** "A checklist of exactly what an era pack contains." [S-146]
**Today.** A form lists every field a designer of a new era supplies and who decides it. Most of it is rule only. Some rows are stale (the era-kind row, the doctrine and building lists) and it omits that the Climate of War (an era's fog and reinforcement settings) comes from the lab's measurements.
**The choice.**
(a) Yes, the form is the shape of an era pack.
(b) Amend the field list.
**Lean.** The branch verdict is: land after the named edits.
<sub>key: doc branch era-pack ask 1</sub>

<!-- batch.md: Batch B item 26 -->
### 26. Rush distances per mission type?
**Story.** No story yet.
**Today.** How far apart the sides start decides whether a rush works. Whether that distance is fixed, and who sets it, is unsettled.
**The choice.**
(a) One band for all.
(b) A band per mission type; the lab proposes numbers from group pace and you confirm.
(c) Bands only for types where a rush is a real play.
**Lean.** None stated.
<sub>key: Q-MAP-04</sub>

<!-- batch.md: Batch B item 27 -->
### 27. Shelter and exposure in the layout?
**Story.** No story yet.
**Today.** Good maps alternate open and sheltered ground. Whether a layout is checked for that is unsettled.
**The choice.**
(a) No; leave it to the landscape engine's judgement.
(b) A check on routes.
(c) A check on key sites only.
**Lean.** None stated.
<sub>key: Q-MAP-05</sub>

<!-- batch.md: Batch C §1 item 4 -->
### 4. Who hosts the next sitting?
**Story.** "Find a match, invite friends, get into the game." [S-144]
**Today.** A locked universe is a multiplayer campaign, a session is one sitting of it, and every peer holds an identical save. You answered a different question (which era comes next) and that rule is now in the bible; this one is who may host the next sitting. Your earlier words: "6: if not all players own the next universe, than that universe is skipped. We while loop down the line of eras checking if all players own each one. The one that every player owns is the one chosen for the next *transition* of time forward. If no players ever own one, than the time jump is cancelled and they proceed in the existing universe forever. Unless you mean something else by \"session\"."
**The choice.** (a) Any peer of the locked group may host. (b) Only the creator hosts. (c) Other: your words.
**Recommended.** (a).
<sub>key: Q-144-03</sub>

<!-- batch.md: Batch C §1 item 7 -->
### 7. When has an age been outgrown?
**Story.** "A campaign moves chronologically through the eras I own." [S-148]
**Today.** The Long Horizon (the chronicle noticing an age being outgrown) needs a measure of how far a civilization has outgrown its age, and a ceiling per age that makes the next time jump cross into the next era. The measure is not chosen.
**The choice.** (a) Technology reaches the era's top tier and holds there for two chapters. (b) A blend of technology, number of regions and economy, against a ceiling per age set in the era pack. (c) Other: your words.
**Recommended.** (a).
<sub>key: Q-148-05</sub>

<!-- batch.md: Batch C §1 item 9 -->
### 9. How is "you have the means" guaranteed?
**Story.** "The resources on the map fit the situation, tilted toward the better position, and I always have the means to do the job." [S-211]
**Today.** The mission generator shaves your force by up to 20 percent for a weak civilization and keeps a parity floor of 0.75, yet promises you can always win. You said: "#6: I want to explore what A would look like with more context without locking in the decision right now, architect weigh in." The Architect owes an options page on (a).
**The choice.** (a) The generator checks that the starting force plus reachable resources can reach the objective. (b) A floor on your share of the map's resources. (c) The parity floor alone.
<sub>key: Q-211-02</sub>

<!-- batch.md: Batch C §1 item 10 -->
### 10. Building onto a building?
**Story.** "I place buildings where I choose and the city reshapes around them." [S-168]
**Today.** Placing a building over natural lots clears them and never refuses. Placing one that overlaps another placed building is refused today.
**The choice.** (a) Refuse the placement, as now. (b) The new building replaces the old one. (c) The two may overlap.
<sub>key: Q-168-06</sub>

<!-- batch.md: Batch C §1 item 11 -->
### 11. How even must a city grow?
**Story.** "Cities rise from scaffolds in waves, climb cliffs and reshape around what I place, and dense districts slow units and give cover but always leave natural paths through." [S-193]
**Today.** On a flat open canvas the city's growth field should be mirror-symmetric about the core. Only the flip across the diagonal is exact in the port; mirrors and quarter turns differ by 1 to 3 fixed-point units. The test carries a draft of 4 units; this does not block anything.
**The choice.** (a) 4 fixed-point units (the draft). (b) Exact only, dropping the seven other symmetries. (c) 8 fixed-point units.
<sub>key: Q-193-08</sub>

<!-- batch.md: Batch C §1 item 13 -->
### 13. Which key sets layer preference?
**Story.** "I give units a standing layer preference and they keep to it without me re-ordering at every obstacle." [S-003]
**Today.** Holding a modifier and pressing 1 to 5 should make a group prefer that layer when it moves on its own, but no modifier is named. Alt already means transfer to a layer and Ctrl means control groups. You said on 2026-10-13: "shift is still free."
**The choice.** (a) Shift plus the number sets the preference. (b) Drop the preference assignment from the beta and retire the rule.
<sub>key: Q-003-02</sub>

<!-- batch.md: Batch C §2 item 2 -->
### 2. What says a roster is balanced?
**Story.** "A roster of 20 to 40 unit types per era, each with a job I can learn." [S-082]
**Today.** The per-unit power rating was deferred; an interim one scores health times damage over attack interval, set so a Vanguard (the basic line unit) is 100. Nothing yet says what scores a whole roster as balanced or who runs the check.
**The choice.** (a) The interim power formula plus headless matchup simulations, with a tolerance band per category. (b) The old bible's full rating, including traits and ability impact. (c) Other: your words.
**Recommended.** (a).
<sub>key: Q-082-04</sub>

<!-- batch.md: Batch C §2 item 4 -->
### 4. Fights run too long
**Story.** "Fights last long enough to read, reposition, and retreat." [S-085]
**Today.** A balanced 50-against-50 fight reliably runs 216 seconds, about 8 percent over the 150 to 200 second window, on every seed. The question is which lever brings it inside.
**The choice.** (a) Raise every unit's base damage by 20 percent. (b) Relax the upper bound to 225 seconds as a revised spec. (c) Cut every unit's health by 15 percent.
<sub>key: Q-085-01</sub>

<!-- batch.md: Batch C §2 item 5 -->
### 5. Strike mirror fights drag
**Story.** "Fights last long enough to read, reposition, and retreat." [S-085]
**Today.** The rule wants Strike fights shorter than Line, shorter than Siege. Strike against Strike takes 124 seconds while Line against Line takes 30, because ranged Strike units keep their minimum distance and fire slowly.
**The choice.** (a) Give Strike a melee fallback when all enemies are inside minimum range: they close and hit for 1.5 times. (b) Halve Strike health so pure fights end faster. (c) The ordering applies to mixed forces only, not same-type mirrors.
<sub>key: Q-085-02</sub>

<!-- batch.md: Batch C §2 item 6 -->
### 6. Where do fight-time targets come from?
**Story.** "Fights last long enough to read, reposition, and retreat." [S-085]
**Today.** The tests pin a 200-second cap (measured 204, with an invented force and layout) and Line-against-Line at 124 seconds against Siege-against-Siege at about 30. No bible text gave those numbers.
**The choice.** (a) Keep the tests' numbers and tune unit stats to them. (b) Retarget the tests to the measured values. (c) Drop the timing checks and keep the ordering claims.
<sub>key: Q-085-03</sub>

<!-- batch.md: Batch C §2 item 7 -->
### 7. The default test army is invented
**Story.** "Fights last long enough to read, reposition, and retreat." [S-085]
**Today.** The standard balanced force (15, 10, 15, 5, 3 and 2 per 50) and the two-grid layout used by the combat runner were invented by the builder. Two non-combat unit types have no speed or health in the roster.
**The choice.** (a) Write that force and layout into the combat epic as the beta default. (b) Make the force a mission setting and leave layout to the map generator.
<sub>key: Q-085-04</sub>

<!-- batch.md: Batch C §2 item 9 -->
### 9. Two units on one spot
**Story.** "Units route around terrain and flow around each other; nothing walks through anything." [S-097]
**Today.** You said on 2026-10-02 the Python's collision "was perfect" and should migrate. The Python shoves the lower-numbered unit the other way (minus x) by a thousand times the normal push, flinging it; the C version nudges it plus x by the normal push.
**The choice.** (a) Port the Python's collision but keep the normal-sized push, direction as the Python (minus x). (b) Port it exactly, fling included. (c) Keep the C rule as written (plus x).
**Recommended.** (a).
<sub>key: Q-097-02</sub>

<!-- batch.md: Batch C §2 item 10 -->
### 10. Do obstacles push units away?
**Story.** "Units route around terrain and flow around each other; nothing walks through anything." [S-097]
**Today.** The rule says units are pushed away from obstacles but gives no strength or range, and the Python's version turns out to do nothing. Blocked cells already keep units out, and a unit found inside one is moved to the nearest open cell; nothing is built beyond that.
**The choice.** (a) Leave repulsion unbuilt; blocked cells alone keep units out. (b) A push proportional to density within a stated range, both numbers yours. (c) The Python's do-nothing version, documented.
<sub>key: Q-097-03</sub>

<!-- batch.md: Batch C §3 item 8 -->
### 8. When the naming pool runs dry
**Story.** "People, places, units, and factions have names that sound like they belong together." [S-154]
**Today.** Names come from pools. What happens when a pool is exhausted is undecided.
**The choice.** (a) Reuse the oldest historical name. (b) Fall back to a numbered name. (c) Refuse and log the failure.
<sub>key: Q-155-01</sub>

<!-- batch.md: Batch C §3 item 9 -->
### 9. How many pieces build a settlement?
**Story.** "A faction's technology tier shows in how its ships look, and shows loss when it falls." [S-133]
**Today.** Each era pack must supply building pieces for settlements, and the 3 to 6 structures named in the rules may be points of interest only. How many pieces per era is open, and the number is yours.
**The choice.** (a) A fixed small set per era. (b) A count range, like the polygon budgets. (c) Set together with the settlement generator.
<sub>key: Q-133-01</sub>

<!-- batch.md: Batch C §3 item 10 -->
### 10. Polygon budget for workers and pieces
**Story.** "Every unit type has a shape I can read at a glance in any era." [S-132]
**Today.** Structures carry a polygon budget of 200 to 800, but workers and the many small pieces of a settlement have none. The numbers are yours.
**The choice.** (a) The same 200 to 800 as structures. (b) A lower range per piece. (c) You set them.
<sub>key: Q-236-02</sub>

<!-- batch.md: Batch C §5 item 3 -->
### 3. How does a trouble travel?
**Story.** "My region's trouble travels across the map where both sides see it and shuts down what it passes over." [S-219]
**Today.** You said on 2026-10-06: "7: mark to be designed, I think it'd be cool if the player didn't see it coming." So its path is not shown ahead; its route, speed and whether fog hides it are still open.
**The choice.** (a) It ping-pongs or loops on a drift setting. (b) A one-way front across the map. (c) Other: your words.
<sub>key: Q-219-02</sub>

<!-- batch.md: Batch C §5 item 4 -->
### 4. Which maps grow, which shrink?
**Story.** "Mission maps sized to the situation." [S-116]
**Today.** Map size is already set by the situation, within 30 percent either way of a base size. Which kinds of map lean toward the larger or smaller end is not.
**The choice.** (a) Open, aggressive layouts (Siege Field, Open Plains) lean large; defensive ones (Fortified Ridge, Narrow Pass) lean small; neutral ones draw from the middle. (b) All draw evenly across the band. (c) Each layout has an explicit bias setting.
<sub>key: Q-118-02</sub>

<!-- batch.md: Batch C §5 item 5 -->
### 5. Urgency arithmetic does not reach 0.8
**Story.** "My missions come from real trouble in the galaxy, weighted toward where I belong and what I do best." [S-072]
**Today.** A rule says a region at stability 15, attacked by a neighbour at military 80, must score urgency at least 0.8. The weights as written reach 0.8 only if every field sits at zero; with the test's values the ceiling is about 0.75.
**The choice.** (a) The scenario includes an active revolt chain in the region (two revolt events add 0.12). (b) The threshold becomes 0.7. (c) The weights change, for example conflict weighted 0.5.
<sub>key: Q-072-02</sub>

<!-- batch.md: Batch C §6 item 3 -->
### 3. Does an occupied base get recorded?
**Story.** "What I did in a mission shows in the region when I come back." [S-220]
**Today.** A mission changes a region only through four field changes and, for a transfer band, ownership. When a base is occupied or the original main base is lost, nothing says whether the simulation records it.
**The choice.** (a) Nothing beyond the field changes and ownership already there. (b) The region record gains base state, a contract change counted against its 2,048-byte budget. (c) Recorded in the ledger and chronicle only.
<sub>key: Q-220-01</sub>

<!-- batch.md: Batch C §6 item 4 -->
### 4. Where does a contested populace end up?
**Story.** "What I did in a mission shows in the region when I come back." [S-220]
**Today.** A populace contested during a mission has no defined landing in the simulation.
**The choice.** (a) It moves the region's population or tension. (b) It changes the region's ownership. (c) Nowhere; it is mission-only.
<sub>key: Q-220-02</sub>

<!-- batch.md: Batch C §6 item 6 -->
### 6. Does weather touch the strategic sim?
**Story.** "The history I read agrees with the ground I fight on." [S-225]
**Today.** A region's environmental trouble exists in missions. Whether it also drives events in the strategic simulation is open; the launch library is closed at 26 event templates.
**The choice.** (a) Tactical only. (b) A new template family that reads the trouble. (c) Decided with the map generator and weather design.
<sub>key: Q-225-01</sub>

<!-- batch.md: Batch C §6 item 7 -->
### 7. What are the city "events"?
**Story.** "The history I read agrees with the ground I fight on." [S-225]
**Today.** Settlement growth is timed in waves by "events". It is unclear whether those are the strategic events (one chain per region-year) or in-mission events such as a shipment arriving or a season turning.
**The choice.** (a) In-mission events only. (b) Strategic events only. (c) Both.
<sub>key: Q-225-02</sub>

<!-- batch.md: Batch C §6 item 8 -->
### 8. Does mission technology flow back?
**Story.** "A mission starts from the faction's technology, only slightly." [S-227]
**Today.** It is open whether anything a pair reaches in a mission feeds back into the faction's technology number, and whether Knowledge Lost (a collapse destroying technology) touches a mission's technology.
**The choice.** (a) Nothing flows back; the two are independent. (b) The mission's result nudges the faction's number. (c) Decided together with what technology does.
<sub>key: Q-227-02</sub>

<!-- batch.md: Batch C §6 item 9 -->
### 9. Tiers versus levels
**Story.** "A mission starts from the faction's technology, only slightly." [S-227]
**Today.** The simulation reads technology in three tiers, while an era has a finer range of levels, for example 1 to 5. Their relationship is not settled.
**The choice.** (a) Tiers stay the sim's coarse reading and levels are the mission's finer scale. (b) The tiers become the levels. (c) Decided together with what technology does.
<sub>key: Q-227-03</sub>

<!-- batch.md: Batch C §6 item 11 -->
### 11. A pair in a one-faction world
**Story.** "My pair is part of the chapter, the ledger and the world." [S-228]
**Today.** A pair is a sub-civilization inside the over-arching civilization, but the simulation has one faction per civilization.
**The choice.** (a) The pair maps onto the chapter only; the simulation keeps one faction. (b) Onto a set of the faction's regions. (c) Onto its own faction.
<sub>key: Q-228-02</sub>

<!-- batch.md: Batch C §6 item 12 -->
### 12. Do mission events reach the jump log?
**Story.** "Each entry reads like a passage from a real history, different every campaign." [S-068]
**Today.** In-mission happenings (base occupied, retaken, fall back, expansion made) may or may not reach the time-jump log and so shape the chronicle's consequence text and chain expansion. It depends on a companion question about what missions report.
**The choice.** (a) No, only the outcome reaches the log. (b) Yes, as content for the consequence slots. (c) Decided with that companion question.
<sub>key: Q-068-03</sub>

<!-- batch.md: Batch C §8 item 1 -->
### 1. Cross-layer numbers
**Story.** "I know whether my unit can shoot an enemy one layer up." [S-008]
**Today.** The ranges and damage multipliers by layer offset (up differs from down), area damage by offset, and the halfway rule during a transition are to be decided by the skill lab, not by argument. Whether firing needs vision is settled.
**The choice.** (a) The lab sweeps the parameter families: range and damage by signed offset, area by offset, a fire-needs-vision flag, and the halfway rule (both always targetable, per rule, or untargetable). (b) Fewer knobs, fixed by analysis alone.
<sub>key: Q-008-03</sub>

<!-- batch.md: Batch C §8 item 3 -->
### 3. Checking that refusal works
**Story.** "I know whether my unit can shoot an enemy one layer up." [S-008]
**Today.** You said refusing a fight counts as a counter, but in the lab the larger side is made to attack, so refusal cannot be played.
**The choice.** (a) A stand-off, with no unit in reach for the stalemate window, is recorded as a refusal and reported beside the counters check. (b) The larger side gets a scripted choice to decline when its scouting shows the play. (c) Not checked; the counters check covers the other counters only.
<sub>key: Q-008-06</sub>

<!-- batch.md: Batch C §8 item 6 -->
### 6. When does Rally trigger?
**Story.** "Each unit has exactly one ability that amplifies its role and costs something." [S-086]
**Today.** Rally fires on "a damaged friendly in radius" with no threshold. Two fixtures need it to ignore a friendly at 400 of 500 health and fire at one at 200 of 500, so the builder used under half health for now.
**The choice.** (a) Chosen for now: under 0.5 of maximum health, named as a constant. (b) Any damage, moving the other fixture out of Rally's radius. (c) A threshold per unit type.
<sub>key: Q-086-02</sub>

<!-- batch.md: Batch C §9 item 1 -->
### 1. Noise on event thresholds
**Story.** "Every crisis has a cause I can point to; history reads as consequence, not dice." [S-026]
**Today.** Event thresholds are meant to be noised at the start of each jump, but live noise is always 0. Wiring it changes every campaign's history and every recorded golden run, by well over 5 percent, and balance items are held for you.
**The choice.** Wire it now, or wire it together with the balance simulation. Or: your words.
<sub>key: F1</sub>

<!-- batch.md: Batch C §9 item 3 -->
### 3. Chronicle words for a fall and a death
**Story.** "When my civilization is gone I keep playing in a surviving one." [S-062]
**Today.** The chronicle should record a fallen faction and a dead commander ("the chronicle frames it"). Its category and wording are new chronicle content nobody has written.
**The choice.** Open: your words.
<sub>key: F3</sub>

<!-- batch.md: Batch C §9 item 4 -->
### 4. Telling the client the campaign ended
**Story.** "When my civilization is gone I keep playing in a surviving one." [S-062]
**Today.** When no faction survives, the campaign ends, but nothing tells the client. A fix adds a new field to the pipe between sim and client.
**The choice.** Open: your words.
<sub>key: F4</sub>

<!-- batch.md: Batch C §9 item 5 -->
### 5. A second enemy force
**Story.** "A second enemy force reacts when I rout the first." [S-122]
**Today.** No mission registers a second force and no hook scripts exist. The choice is whether setup gets a default hook now or waits for the script pipeline.
**The choice.** A default hook at mission setup now, or wait for the script pipeline. Or: your words.
<sub>key: F5</sub>

<!-- batch.md: Batch C §9 item 6 -->
### 6. How long a timed transition takes
**Story.** "The enemy escalates on a schedule and reacts to me, with the moment shifting each time." [S-121]
**Today.** Enemy forces switch behaviour on timed transitions, and the duration per force is a number nobody has given.
**The choice.** Open: your words (a duration).
<sub>key: F6</sub>

<!-- batch.md: Batch C §9 item 10 -->
### 10. Regional commander on conquest
**Story.** "The people the chronicle names are born, serve, age, and die, and someone takes their place." [S-060]
**Today.** A regional commander should appear when a region is conquered, but never does in play, and where it hooks in is unclear. It needs a scout of the code first.
**The choice.** Open: your words.
<sub>key: F10</sub>

<!-- batch.md: Batch C §9 item 11 -->
### 11. Two helpers that disagree with the rules
**Story.** "When my civilization is gone I keep playing in a surviving one." [S-062]
**Today.** The player-faction-collapsed check and the fallback-pool selector disagree with their rules or the live path. The tests are the spec.
**The choice.** Fix them to match the rules, or remove them with their tests. Or: your words.
<sub>key: F11</sub>

<!-- batch.md: Batch C §9 item 12 -->
### 12. What objectives are made of
**Story.** "One primary objective I can see progressing, up to three secondary ones." [S-075]
**Today.** Unsettled: what a designated target is and how many there are, who is escorted and how many, where the extraction point is, and where an interception's enemy force comes from.
**The choice.** Open: your words.
<sub>key: F12</sub>

<!-- batch.md: Batch C §10 item Lab 4 -->
### Lab 4. Depth score rule
**Story.** "the skill lab as a whole"
**Today.** The layout search scores depth from skills that give a gain of at least a threshold G (draft 2 units). The first chart decides.
**The choice.** (a) G is 2 units, and a skill scores if its gain is at least G and it has no counter or its counter works. (b) Another G. (c) Another rule.
<sub>key: Q-LS-01</sub>

<!-- batch.md: Batch C §10 item Lab 5 -->
### Lab 5. Sweeping the enemy mix
**Story.** "the skill lab as a whole"
**Today.** Whether the enemy's mix of unit types is swept for each layout in the second run; a 3 by 3 grid triples the cost.
**The choice.** (a) Fixed per layout. (b) Swept.
<sub>key: Q-LS-02</sub>

<!-- batch.md: Batch C §10 item Lab 6 -->
### Lab 6. Likely-places ping in the layout search
**Story.** "the skill lab as a whole"
**Today.** Whether the "likely places" ping policy joins the layout search once chokes exist.
**The choice.** (a) Yes, in the second run. (b) No.
<sub>key: Q-LS-03</sub>

<!-- batch.md: Batch C §10 item Lab 7 -->
### Lab 7. Scoring the ping
**Story.** "I ping a layer I choose at a place I choose and see it for a moment; whoever I ping learns roughly where I am." [S-162]
**Today.** The ping changes nothing in a fight by itself, so it cannot be scored like the other skills. You said on 2026-10-05: "Maybe we could look at the ratio that a specific player detected the enemy against the enemy's ratio that they detected the player, and then look at the outcome. I don't know, this is an area of investigation." Parked as lab work, not beta.
**The choice.** (a) The five readings of the proposal: policy spread, counter cost, value of knowing, warning time against set-up time, and give-away; pass values set by you after the first chart. (b) Detection ratio against outcome only. (c) Another measure.
<sub>key: Q-162-05</sub>

---

## Already decided (the record answers it)

Taken by: the record the triage names (`triage_2026-10-19.md`, `note` column). On 2026-10-21 a records clerk closed in `ambiguity_register.md` every one of these that has a register row and whose cite held. Left open because the cite did not settle them: Q-148-04, Q-151-02, Q-193-09, Q-194-01, Q-224-01. Not register rows: B3, B4, B8 (closed 2026-10-04), B9, B15, B22, B23, B24 (Q-MAP-01 and -02 have no register row yet), F2, F7, F8, F9, F13.

<!-- batch.md: Batch B item 3 -->
### 3. The transition shots
**Story.** "Mission pulls back into the galaxy and pushes into the next mission without a cut." [S-108]
**Today.** A mockup of that pull-back exists; you have its scale-and-path shots. A further pass fixing the star blobs is being built. What is yours is whether the pull-back is right.
**The choice.**
(a) Approved: the transition gets its place in the build schedule.
(b) Another pass, with your notes.
(c) Rejected, with a note.
**Lean.** None stated.
<sub>key: B14 (shots P-S108-*)</sub>

<!-- batch.md: Batch B item 4 -->
### 4. Does the land read as places?
**Story.** "Bases, objectives and resources sit where the land puts them." [S-191]
**Today.** A mockup shows a pad, a choke bar and a wall on shaped ground. A second pass is being built that carves routes through it. Unsettled: do they read as places, and should routes be carved or come from the landforms?
**The choice.** Two parts, answer both.
(a) Pad, choke bar and wall read as places on the land: yes or no.
(b) Carved routes are acceptable (judge them in the next batch of shots), or routes should come from the landforms themselves, which is a design direction, not a fix.
**Lean.** None stated.
<sub>key: B15 (shots P-S191-*)</sub>

<!-- batch.md: Batch B item 8 -->
### 8. What shape is the map engine?
**Story.** "Maps built on hand-authored strategic layouts." [S-112]
**Today.** The eight stock layouts all need rewriting before use. How the engine uses them is unsettled.
**The choice.**
(A) Authored layouts, each rewritten whole with intent.
(B) Numbers solved afresh for every map; the old layouts become reference only.
(C) A kit of small situations (a choke with two summits, a ford) assembled into maps; the old layouts are recipes for the kit.
**Lean.** C (the audit assumes it).
<sub>key: Q-191-06 (B21)</sub>

<!-- batch.md: Batch B item 9 -->
### 9. May a layout demand a landform?
**Story.** "Ways up and down I can hold, narrow places to fight over, high ground to take." [S-192]
**Today.** One stock layout needs a coast, another needs a summit to start on. The ground comes from the seed and may have neither. Whether the layout can insist is unsettled.
**The choice.**
(a) Yes: the ground must produce it, or that layout is not offered.
(b) No: drop the coast; only chokes and vantages survive.
(c) Yes for a short list of landforms the seed can steer toward.
**Lean.** None stated.
<sub>key: B21 second question (library audit item 3)</sub>

<!-- batch.md: Batch B item 15 -->
### 15. A second review of the logs spec?
**Story.** No story yet.
**Today.** The sim's logging spec has a contract paragraph that other work will build on. A second review by another model would catch a flaw before the work stacks on it. It costs you opening one chat for one brief; waiving it saves that, but a flaw found later costs a rework.
**The choice.**
(a) You open the Dispatcher chat for that one review.
(b) Waive it for this spec.
**Lean.** (a). A contract flaw is cheapest to catch before building.
<sub>key: B5 (process)</sub>

<!-- batch.md: Batch B item 22 -->
### 22. Who owns the open era fields?
**Story.** "An era in space and an era on land to play, all one game." [S-147]
**Today.** The form marks as yours the names of the three resources, per-era constants and the strategic view definition, with no values proposed.
**The choice.**
Confirm these stay yours, or name another owner.
**Lean.** None stated.
<sub>key: doc branch era-pack ask 2</sub>

<!-- batch.md: Batch B item 23 -->
### 23. What does high ground do beyond sight?
**Story.** "Ways up and down I can hold, narrow places to fight over, high ground to take." [S-192]
**Today.** On the ground, height gives vision. Anything more would reopen a call you made on 2026-10-05, to retire the elevation bonus for ground eras.
**The choice.**
(a) Nothing but vision, as StarCraft 2.
(b) A miss chance for attackers on low ground, as Brood War.
(c) Damage scaled by slope, as Total War (up to 30 percent more downhill).
(d) An aim bonus for the high side, with no defence bonus, as XCOM.
**Lean.** None stated; (a) agrees with your earlier call.
<sub>key: Q-MAP-01</sub>

<!-- batch.md: Batch B item 24 -->
### 24. Does cover protect by direction?
**Story.** No story yet.
**Today.** Cover is whatever blocks sight, with no direction.
**The choice.**
(a) Cover is whatever blocks sight, with no direction.
(b) Directional: protects only from the front arc, void when flanked or at close range, as Company of Heroes.
(c) Directional only at chosen strongpoints.
**Lean.** None stated.
<sub>key: Q-MAP-02</sub>

<!-- batch.md: Batch C §1 item 6 -->
### 6. What happens when history loops?
**Story.** "A campaign moves chronologically through the eras I own." [S-148]
**Today.** The campaign walks through the eras in order, and at the end of the list it loops. Nothing says whether technology rescales again, whether characters and the ledger continue, whether the galaxy keeps its ownership, or how this relates to the deferred Ouroboros restart (a rebirth after ruins and amnesia).
**The choice.** (a) The loop works like any era boundary: the same rescale, characters continue, ledger and galaxy carry over unchanged. (b) The loop is the Ouroboros restart: ruins, amnesia, and that story designed here. (c) Other: your words.
**Recommended.** (a).
<sub>key: Q-148-04</sub>

<!-- batch.md: Batch C §1 item 8 -->
### 8. Does the target marker show the enemy?
**Story.** "One primary objective I can see progressing, up to three secondary ones." [S-075]
**Today.** An eliminate-the-force objective needs a marker on the map, but fog hides the enemy. You said on 2026-10-07: "#3: C but remember we're not doing "match types" that don't involve a home base for both enemy and player, let's shelve this one for post-beta." The direction is a vague area.
**The choice.** (a) The marker shows the enemy's true centre. (b) It appears only once the enemy has been seen. (c) It shows a vague area.
<sub>key: Q-210-08</sub>

<!-- batch.md: Batch C §1 item 12 -->
### 12. Which region feeds a city's growth?
**Story.** "Cities rise from scaffolds in waves, climb cliffs and reshape around what I place, and dense districts slow units and give cover but always leave natural paths through." [S-193]
**Today.** At mission start the growth field reads an economy density from one region. An experiment found it read your first home-tier region (region 0, tier 2) rather than the region the mission is in (76, tier 1). Not blocking; nothing applies a fix yet.
**The choice.** (a) The mission's region. (b) Your home region. (c) The region holding the objective.
<sub>key: Q-193-09</sub>

<!-- batch.md: Batch C §2 item 3 -->
### 3. How many units per launch era?
**Story.** "A roster of 20 to 40 unit types per era, each with a job I can learn." [S-082]
**Today.** The Settled Reach ships six types. It is open how many each launch era carries, and whether an era built around a named conflict gives each side its own roster, which would override the rule that unit profiles are the same in every era.
**The choice.** (a) Launch eras carry the six plus a shared set growing toward 20, identical across eras. (b) Each launch era carries its own 20 to 40, and profiles are no longer identical across eras. (c) Other: your words.
**Recommended.** (b).
<sub>key: Q-082-05</sub>

<!-- batch.md: Batch C §2 item 12 -->
### 12. What is a scout?
**Story.** "I ping a layer I choose at a place I choose and see it for a moment; whoever I ping learns roughly where I am." [S-162]
**Today.** Scouts stay, "less aggressively than the pinging, we'll play around with what we do based on what players like" (you, 2026-10-05). What a scout is, what it reveals, for how long, and in which eras is open.
**The choice.** (a) A free, slow, killable unit that sees normally. (b) A cast like the ping, with a longer cooldown and a smaller radius. (c) Decided after players try both.
<sub>key: Q-162-06</sub>

<!-- batch.md: Batch C §2 item 13 -->
### 13. The land era's eyes
**Story.** "The land era has units that walk, so slopes and strongpoints at slopes decide where an army can go." [S-201]
**Today.** The land era needs a vision unit. You said on 2026-10-01: "the pinging should replace the seer, or make the seer really expensive", and on 2026-10-05: "a simple placeholder unit that's a scout is sufficient for now".
**The choice.** (a) A placeholder scout now (a Raider re-skin with longer sight and no weapon), with the seer designed alongside the land roster. (b) The seer now, expensive, as the 2026-10-01 words say. (c) Another: your words.
<sub>key: Q-201-02</sub>

<!-- batch.md: Batch C §2 item 14 -->
### 14. Does higher ground still add sight?
**Story.** "An elevated position sees farther." [S-091]
**Today.** The elevation sensor bonus has tiers in steps of 0.25, but on land maps the height field now gives both elevation and the five layers (terraces of the land). The sign of the tier difference is unstated, and cross-layer vision is symmetric by layer distance.
**The choice.** (a) Drop the tiers; layers are the only elevation and the bonus goes. (b) Keep them, derived from the height field, with the bonus for the higher observer only (asymmetric vision, which you allowed only with a counter). (c) Keep them, with the bonus symmetric by tier difference.
<sub>key: Q-091-01</sub>

<!-- batch.md: Batch C §3 item 2 -->
### 2. Same map seeds in every era?
**Story.** "An era in space and an era on land to play, all one game." [S-147]
**Today.** One campaign seed makes one galaxy. It is open whether each era draws the same layouts from it or may weight layouts its own way.
**The choice.** (a) Identical seeds and layouts. (b) Eras may weight layouts.
<sub>key: Q-147-02</sub>

<!-- batch.md: Batch C §3 item 3 -->
### 3. Names versus mechanics
**Story.** "A checklist of exactly what an era pack contains." [S-146]
**Today.** The bible says eras differ in names but share mechanics. Resource names, doctrine names and environmental troubles (weather and other hazards) sit on the line between the two.
**The choice.** (a) Names and troubles differ, mechanics identical. (b) All identical for the two launch eras. (c) You decide item by item.
<sub>key: Q-146-02</sub>

<!-- batch.md: Batch C §3 item 6 -->
### 6. What carries between eras?
**Story.** "Maps, civilizations, and era systems transfer between eras like skins." [S-150]
**Today.** Archetype weights and naming subsets transfer. What else counts as civilization content that moves is unsettled.
**The choice.** (a) Archetypes, names, colours. (b) Also unit skins per civilization. (c) Other: your words.
<sub>key: Q-150-01</sub>

<!-- batch.md: Batch C §3 item 7 -->
### 7. What may an era change in production?
**Story.** "Eras that feel different." [S-151]
**Today.** The Climate of War (each era's own fog, pace and production rate) has a reinforcement rate that now means pace of production plus strongpoint reinforcement. Which economy values an era may set is open.
**The choice.** (a) Production pace only. (b) Pace and resource yields. (c) None until the economy is built.
<sub>key: Q-151-02</sub>

<!-- batch.md: Batch C §4 item 1 -->
### 1. The sand table
**Story.** "I pull the camera back until the battle reads as a map and give groups move orders from there." [S-161]
**Today.** You said on 2026-09-23 you like the Dune-style sand table but want a prototype first: low resolution with large blocks for height, a grain-size dial from coarse to fine, and a 45-degree view with layers pulled apart so unit sets read. Also open is whether an always-visible corner glance survives once the minimap is replaced.
**The choice.** (a) Prototype it: block-resolution table, grain dial, and the 45-degree layered view; commit on your approval. (b) Ship the flat War Table first and the sand table later. (c) Other: your words.
**Recommended.** (a).
<sub>key: Q-103-05</sub>

<!-- batch.md: Batch C §4 item 3 -->
### 3. Player-bound cameras
**Story.** "A free camera I manage myself, with the Angle Rack, the Layer Peel, and a flip key." [S-103]
**Today.** You asked for an idea to be recorded, not decided: the player binds keys to camera angles relative to a unit's forward direction, with a view that tracks it as it moves and a default non-following mode on a key. Everything about it would be adjustable. It is not a blocker.
**The choice.** (a) Keep the chosen camera (Angle Rack for preset angles, Layer Peel, flip key). (b) Replace the Angle Rack with player-bound tracking views. (c) Offer both.
<sub>key: Q-103-07</sub>

<!-- batch.md: Batch C §4 item 4 -->
### 4. What loading screens show
**Story.** "A main menu that sets the tone and settings that cover the basics." [S-110]
**Today.** Loading screens will carry information the player would not otherwise see, in the chronicle's voice, with the content chosen before launch. There is no loading screen between a mission and the galaxy.
**The choice.** (a) Chronicle entries you have not read yet. (b) The Long Horizon's foreshadowing of the age being outgrown. (c) Lineage and legend fragments. (d) Decide before launch, after a mockup.
**Recommended.** (d).
<sub>key: Q-110-03</sub>

<!-- batch.md: Batch C §5 item 1 -->
### 1. When does the enemy rout?
**Story.** "Enemy forces advance, hold, patrol, ambush, or retreat, cautiously, aggressively, or in echelons." [S-120]
**Today.** The enemy script has "routed" and "retreating" conditions, but nothing says what moves a force from advancing or holding into a rout.
**The choice.** (a) Enemy health falls under 25 percent of its starting total. (b) Fewer than 30 percent of its starting units survive. (c) Each enemy unit routs on its own once its own health drops under 20 percent.
<sub>key: Q-120-02</sub>

<!-- batch.md: Batch C §6 item 5 -->
### 5. Generation time at 400 regions
**Story.** "A 400-region galaxy starts within a time Westley has confirmed." [S-224]
**Today.** 5 milliseconds was confirmed at 110 regions; the region range is now 250 to 400. Separately, a 150-step jump at 400 regions must finish under 2 seconds.
**The choice.** (a) Scale linearly, about 18 milliseconds. (b) Keep 5 milliseconds at 400. (c) Drop the small budget and fold generation under the 2-second figure.
<sub>key: Q-224-01</sub>

<!-- batch.md: Batch C §8 item 2 -->
### 2. Does concentration of fire count?
**Story.** "I know whether my unit can shoot an enemy one layer up." [S-008]
**Today.** In the lab's first run every unit on both sides fired, yet the side whose fire fell on a few enemies won (11 alive against 15 at equal total health). Your ruling of 2026-10-02: nearest target stays the game's rule, and one lab-only focus-fire batch measures the effect.
**The choice.** (a) It joins the principle: what counts is units firing and how their fire is concentrated. (b) It is tuned out, so the result follows the firing count alone. (c) Decide from the focus-fire batch.
<sub>key: Q-008-05</sub>

<!-- batch.md: Batch C §8 item 4 -->
### 4. Judging unit-type matchups
**Story.** "I know whether my unit can shoot an enemy one layer up." [S-008]
**Today.** The matchup skill acts through damage per hit, not through who can fire, while two of the lab's conditions judge every skill by firing count.
**The choice.** (a) For this skill the firing count is weighted by the category multiplier against the target's type, as the README says (you, 2026-09-30: "not just unit values but their type as well"). (b) Judge it on break-even alone. (c) Other: your words.
<sub>key: Q-008-07</sub>

<!-- batch.md: Batch C §8 item 5 -->
### 5. A galaxy count that comes up short
**Story.** "A galaxy small enough to learn, large enough to feel vast, different every campaign." [S-021]
**Today.** With equal template weights about one seed in five drew a region count 8 or more under the feasible minimum, and would have failed to generate. The design lane chose the first option on 2026-09-22 and the builder implemented it; confirm or change.
**The choice.** (a) Chosen: lift the drawn count to the feasible minimum after the template roll, with no extra draw, so every seed generates; a pinned count below the minimum still fails cleanly. (b) Re-roll the templates until feasible, which changes the draw-order contract. (c) Keep the failure and have the client retry with the next seed, a visible hitch that breaks "same seed, same world".
<sub>key: Q-021-07</sub>

<!-- batch.md: Batch C §8 item 7 -->
### 7. Refusing a mismatched save
**Story.** "Saved at every chapter boundary without asking." [S-111]
**Today.** Loading a save of another version is refused with a message naming both versions, but no code accessor returns the versions.
**The choice.** (a) The load call returns a status, and the client reads the two versions through separate accessors. (b) The load call gives the two versions as extra outputs. (c) A separate last-error accessor.
<sub>key: Q-111-02</sub>

<!-- batch.md: Batch C §8 item 8 -->
### 8. Fine detail against the grid
**Story.** "One continuous world from a single unit to the whole battlefield." [S-194]
**Today.** The fine terrain formula and the sim's coarse grid can disagree. You said on 2026-10-06: "2: This question requires deeper investigation, mark in the repo that when it comes time to design this part we'll need to do some research on how we can keep the backend (what's happening in the game) *true* to what's really happening (b) while still maintaining the quality of the player experience (we don't want too much snapping that comes with b)." The agreement tolerance is yours; research is queued.
**The choice.** (a) Fine detail is a ripple that cannot move ground across a band edge. (b) The sim's grid wins and the client snaps ground contact to it. (c) Play follows the grid and visuals may differ.
**Recommended.** None marked; you leaned to (b) with research to avoid heavy snapping.
<sub>key: Q-194-01</sub>

<!-- batch.md: Batch C §11 item 1 -->
### 1. A ground flyer's sight
**Story.** "I see less on other layers than on my own, and nothing three layers away, unless I hold a vantage." [S-005]
**Today.** A ground-era flyer sees down and "is visible from farther away than it can see" (you, 2026-10-05). Parked for the beta ("#5: Not for beta, skip"); the two distances and what else it borrows from the space model are open.
**The choice.** (a) Seen-from distance is its sensor radius times a multiplier above 1, and it sees down with the ground model. (b) Numbers from the skill lab. (c) Another: your words.
<sub>key: Q-005-06</sub>

<!-- batch.md: Batch C §11 item 2 -->
### 2. Space sight beyond two layers
**Story.** "I see less on other layers than on my own, and nothing three layers away, unless I hold a vantage." [S-005]
**Today.** Passive cross-layer sight in space is "very limited" (you) and the ping reaches past it. The factors 0.50, 0.20 and 0 beyond two layers were never yours; you answered "#4: A, architect decision. Should be close to what it was for the python version of the game".
**The choice.** (a) Keep 0.50, 0.20 and 0 as provisional and let the space lab sweep them. (b) Smaller, such as 0.25, 0.10 and 0. (c) A fixed short radius rather than a factor.
<sub>key: Q-005-07</sub>

<!-- batch.md: Batch C §11 item 5 -->
### 5. Where the solo controls sit
**Story.** "Alone, I have a dial, a doctrine switch, unit-mix switches and I ask by pointing, even from the map view." [S-231]
**Today.** The right sidebar holds only the layer strip, so the commander's dial and switches need a home. You said: "#6: architect choice, I provide feedback post-product."
**The choice.** (a) The right sidebar. (b) A bar at bottom centre beside the ability slots. (c) A panel opened by a key.
<sub>key: Q-231-01</sub>

<!-- batch.md: Batch C §11 item 6 -->
### 6. Overriding the mix and acknowledging
**Story.** "Alone, I have a dial, a doctrine switch, unit-mix switches and I ask by pointing, even from the map view." [S-231]
**Today.** How the commander overrides the mix the rules pick, and whether the screen confirms a request made by pointing or says when the rules cannot carry it out, is open. You said: "#7: architect choice".
**The choice.** (a) A mix panel and a short acknowledgement on the ticker. (b) A marker on the map where the request stands. (c) No acknowledgement.
<sub>key: Q-231-02</sub>

<!-- batch.md: Batch C §11 item 7 -->
### 7. The economy player's portrait
**Story.** "As the economy player of a pair, my screen shows resources, workers, the yield of a lot before I place, my schedule, technology and defenses, and no list of what the commander needs." [S-230]
**Today.** The commander's portrait place shows the commander, but the economy player is not the commander. Parked for the beta ("#4: skip for beta").
**The choice.** (a) The same commander portrait. (b) The economy player's own identity. (c) Nothing.
<sub>key: Q-230-02</sub>

<!-- batch.md: Batch C §11 item 9 -->
### 9. How difficulty scales a smarter enemy
**Story.** "A difficulty knob changes how much the enemy has, not how well its units fight." [S-125]
**Today.** How difficulty scales the enemy's prosperity and its multi-layer intelligence, and what hard mode strives for (positional awareness, informed surrounds on chosen layers), is open. You answered "#8: C", read as leaving numbers to the skill lab; the rules keep only that both scale.
**The choice.** (a) Prosperity through reinforcement structures and rate, intelligence through which layer-aware behaviours the enemy's macro layer may use per difficulty. (b) Other, decided with the lab.
**Recommended.** (a).
<sub>key: Q-125-03</sub>

<!-- batch.md: Batch C §11 item 10 -->
### 10. Does archetype pick economy doctrine?
**Story.** "A faction's standing in the galaxy carries into the economy it fights with." [S-226]
**Today.** Whether a faction's archetype, weights or confidence link to the doctrine running its economy, for the enemy and for your civilization, is open. Parked ("#2: skip characters (individual playstyles of enemies) for the beta").
**The choice.** (a) No link; doctrine is chosen apart from archetype. (b) Archetype sets the enemy's default doctrine. (c) Other, with the doctrine design.
<sub>key: Q-226-02</sub>

<!-- batch.md: Batch C §9 item 2 -->
### 2. Successor after a collapse
**Story.** "When my civilization is gone I keep playing in a surviving one." [S-062]
**Today.** The register records your answer as normal pools restricted to surviving factions, falling back to the faction with the most regions. The code and an Architect ruling use "most regions" only and call the question open. Two records disagree on your answer.
**The choice.** Which is right: pools restricted to survivors with fallback, or most regions only? Or: your words.
<sub>key: F2</sub>

<!-- batch.md: Batch C §9 item 7 -->
### 7. The cautious break-off threshold
**Story.** "Enemy forces advance, hold, patrol, ambush, or retreat, cautiously, aggressively, or in echelons." [S-120]
**Today.** A cautious enemy breaks off contact at some "contact threshold" that has no value.
**The choice.** Open: your words (a number).
<sub>key: F7</sub>

<!-- batch.md: Batch C §9 item 8 -->
### 8. Who reads a faction's phase?
**Story.** "The sim knows whether my civilization is expanding, at war, overextended, fragmenting, or settled." [S-053]
**Today.** The sim computes each faction's lifecycle phase, but it is unsettled whether the chronicle or the mission generator consumes it.
**The choice.** Open: your words (chronicle, mission generator, or both).
<sub>key: F8</sub>

<!-- batch.md: Batch C §9 item 9 -->
### 9. Clamping the jump length
**Story.** "Decades pass while I am gone, and the world decides how many." [S-056]
**Today.** The client sends the raw step count for a time jump with no clamp to the intended 20 to 100 steps of the strategic clock (50 of them pass in a time jump).
**The choice.** Open: your words.
<sub>key: F9</sub>

<!-- batch.md: Batch C §9 item 13 -->
### 13. What counts as brought home
**Story.** "The result is a spectrum weighing what I achieved and who I brought home." [S-077]
**Today.** Retention counts who you brought home. Open: whether the commander's unit, units made mid-mission and structures count, and whether a unit that leaves the map counts as alive.
**The choice.** Open: your words.
<sub>key: F13</sub>

<!-- batch.md: Batch C §10 item Lab 3 -->
### Lab 3. Constants nobody set
**Story.** "the skill lab as a whole"
**Today.** The lab runs on draft constants: win margin 5 percent, stalemate window of 20 seconds, a starting gap of about 30 unit-widths, play counts and factors, layout grid values, corridor width of about 26 unit-widths, the ping search set, and others. "Rough sizes only, not pass marks" applies until you set them. You ruled fights end by elimination only, with both sides attack-moving to one point, so the hold timer, hold radius, blind window and draw band are retired; a capped fight is a defect to trace, never a result.
**The choice.** (a) They stay drafts until the first chart, then you set what the chart shows matters. (b) Set them now.
<sub>key: Q-LAB-03</sub>

---

## Duplicate (nothing asked)

Taken by: nothing asked: each repeats another row. C §1.1 and §1.2 repeat B1 and B2; Q-103-06 repeats B6; Q-070-02 repeats Q-228-01; B25 repeats Q-165-01; C0 to C9 are children of Q-156-02 and are asked only if Westley picks (b) there.

<!-- batch.md: Batch B item 25 -->
### 25. Pacing tools in the layout kit?
**Story.** "Someday, perhaps: lanes where my troops move faster and strategic ground where they move slower." [S-165]
**Today.** Layouts shape the fight only by distance. The kit could also set the pace of crossing.
**The choice.**
(a) No, distance only.
(b) Slow and speed zones.
(c) Blockers on route openings that can be destroyed.
(d) Both (b) and (c).
**Lean.** None stated.
<sub>key: Q-MAP-03</sub>

<!-- batch.md: Batch C §1 item 1 -->
### 1. Map and scroll in step?
**Story.** "I watch the map change on the left while the scroll writes itself on the right, and I can stop and read." [S-069]
**Today.** Chronicle entries now print one at a time, as you ruled on 2026-10-13. If the map replay reaches the next entry's picture while the last entry is still printing, nothing says whether the map waits.
**The choice.** (a) The map holds until the entry has finished printing, so scroll and map stay in step like a book with pictures. (b) The map runs on at two steps a second and the scroll catches up, so an entry may describe a change the map already showed.
**Recommended.** None marked. The smaller change is (b); (a) would be a second piece of work.
<sub>key: Q-069-03</sub>

<!-- batch.md: Batch C §1 item 2 -->
### 2. Which renderer is the look?
**Story.** "A 3D star map where territory glows, borders touch, and war flashes." [S-106]
**Today.** Under the shipped graphics renderer the translucent faction shells wash over the system dots, so the dot-visibility test sees 6 of 18 dots. Under the other renderer the test and the merge gate use, it passes.
**The choice.** (a) The shipped renderer is the look, and the test gains a run under it (its pass mark is yours). (b) The shell-over-dot wash is the approved look and the finding closes as accepted. (c) A lane B piece lowers shell opacity over the dots.
<sub>key: Q-B23b-01</sub>

<!-- batch.md: Batch C §4 item 2 -->
### 2. How the map shows a group's layer
**Story.** "I pull the camera back until the battle reads as a map and give groups move orders from there." [S-161]
**Today.** From the map view you need to read which layer a group is on. You said: "I'd like to brainstorm additional options for indicating which layer specific units and unit groups are one, because the pin option is a good option but I don't think it has to be the only one. Mark further research needed." A group wholly on layer 3 is also open.
**The choice.** (a) Pins, tall, sunk or full rod, as in the sand table option. (b) Stacked icon slices, one per occupied layer. (c) Colour-banded icons keyed to the layer strip. (d) A research pass first.
**Recommended.** (d).
<sub>key: Q-103-06</sub>

<!-- batch.md: Batch C §6 item 13 -->
### 13. Where is the economy player in the chronicle?
**Story.** "Events near my family bubble up into the scroll, as the deeds of a military family." [S-070]
**Today.** Lineage members are framed as military. Who the economy player is in the chronicle, and who the others are in a team of up to six, is unsettled.
**The choice.** (a) The economy player is not in the lineage. (b) A lineage member in a support role, framed as military. (c) Other: your words.
<sub>key: Q-070-02</sub>

<!-- batch.md: Batch C §10 item C0 -->
### C0. What the lab must show before we trust it: a fair mirror
**Today.** Two identical, mirrored forces fight. This is the control that proves the lab itself is sound.
**The choice.** Draft mark: the larger force wins and the break-even sits at equal numbers. The tolerance is yours.
<sub>key: C0</sub>

<!-- batch.md: Batch C §10 item C1 -->
### C1. What the lab must show before we trust it: skill wins the firing count
**Today.** A skilled play should get more units shooting than a naive one on the same map.
**The choice.** Draft mark: the skilled side's firing advantage is above the mirror control's noise, on at least four maps in five that offer the play. How large it must be is not a fixed ratio and is yours.
<sub>key: C1</sub>

<!-- batch.md: Batch C §10 item C2 -->
### C2. What the lab must show before we trust it: the result follows the firing count
**Today.** More units firing should mean a better result, so the firing count really is what decides the fight.
**The choice.** Draft mark: results rise with firing advantage (rank agreement at least 0.8), and no more than one fight in five lies over 25 percent off the trend.
<sub>key: C2</sub>

<!-- batch.md: Batch C §10 item C3 -->
### C3. What the lab must show before we trust it: skills stack
**Today.** Using several skills together should be worth more than the best one alone.
**The choice.** Draft mark: a combination beats its best single part by at least 5 percent.
<sub>key: C3</sub>

<!-- batch.md: Batch C §10 item C4 -->
### C4. What the lab must show before we trust it: no dominant skill
**Today.** No one trick should carry the game.
**The choice.** Draft mark: no single skill gives more than 60 percent of the full set's advantage.
<sub>key: C4</sub>

<!-- batch.md: Batch C §10 item C5 -->
### C5. What the lab must show before we trust it: no dead skill
**Today.** Every skill must matter.
**The choice.** Draft mark: removing any one skill from the full set costs at least 10 percent.
<sub>key: C5</sub>

<!-- batch.md: Batch C §10 item C6 -->
### C6. What the lab must show before we trust it: counters exist
**Today.** Every skilled play needs an answer on most maps (some situations, like a full surround, are unbeatable).
**The choice.** Draft mark: the counter takes back at least half the advantage, on at least three maps in five.
<sub>key: C6</sub>

<!-- batch.md: Batch C §10 item C7 -->
### C7. What the lab must show before we trust it: the ceiling is high
**Today.** A great player should beat a much larger force; you gave rough sizes only, about 2 times for all skills at first, then singles near 30 percent and full mastery 3 times or more.
**The choice.** Reported, not pass or fail: the best situations against the rough sizes of 2 times and 3 times. Do you want a pass mark on it?
<sub>key: C7</sub>

<!-- batch.md: Batch C §10 item C8 -->
### C8. What the lab must show before we trust it: it holds across maps
**Today.** The results should not depend on one lucky map. Space maps must pass; land maps are reported and do not block.
**The choice.** Draft mark: conditions C1 to C6 hold on four space maps in five.
<sub>key: C8</sub>

<!-- batch.md: Batch C §10 item C9 -->
### C9. What the lab must show before we trust it: fights stay readable
**Today.** Skill should not make fights too short or too long to follow.
**The choice.** Reported, not pass or fail: fight length against the fights-last-long-enough story.
<sub>key: C9</sub>

---

## Moot (nothing asked)

Taken by: nothing asked: optional reads, deferred rows or rows already closed.

<!-- batch.md: Batch B item 18 -->
### 18. Read the historians' numbers first?
**Story.** No story yet.
**Today.** A research note tests ten military principles (chokes, high ground, envelopment, reserves) against history and maps them to the game's eight map pillars. Its numbers are prior art, not game numbers. One set is Dupuy's published terrain and posture multipliers (terrain about 1.3 to 1.5, hasty defence about 1.5 to 1.6, surprise up to 2.0).
**The choice.**
(a) Yes, read them as prior art when you answer the height and cover questions below.
(b) No, ignore them.
**Lean.** None stated; the branch verdict is land as is.
<sub>key: doc branch doctrine ask 1</sub>

<!-- batch.md: Batch C §2 item 8 -->
### 8. Leash before or after damage?
**Story.** "Every unit on both sides flinches, obeys, then shoots the nearest thing in range." [S-087]
**Today.** An attack-moving unit stays within about 9 unit-widths (200 world units) of its anchor. Tested before damage, a unit with longer reach never shoots a target beyond that; tested after, it does. The plan is a switch the lab runs both ways, and you pick.
**The choice.** (a) Before damage, as the old Python. (b) After damage. (c) Decided from the lab's chart.
<sub>key: Q-087-01</sub>

<!-- batch.md: Batch C §5 item 2 -->
### 2. How hard is each difficulty?
**Story.** "Hard mode gives me less to work with, never gives the enemy better units." [S-080]
**Today.** Difficulty compression (time width, resource generosity, odds of complications around 1 percent, and the ramp across generations) is a no-op until its values exist. You deferred it past the MVP on 2026-09-30.
**The choice.** (a) Easy gets 1.2 times the time and hard 0.85; generosity through parity only; complication odds 0.5, 1 and 1.5 percent; the ramp a fixed step per generation. (b) Other: your words.
**Recommended.** (a).
<sub>key: Q-080-03</sub>

<!-- batch.md: Batch C §6 item 1 -->
### 1. What does technology do?
**Story.** "the economy and bases as a whole"
**Today.** You decided a mission's starting technology is derived, only slightly, from the simulation's technology level, with an era spanning a range such as 1 to 5 and a timed match rising one or two. You said: "what tech will do exactly is undecided, mark that as something that needs designing."
**The choice.** Open: to be designed.
<sub>key: Q-159-12</sub>

<!-- batch.md: Batch C §6 item 2 -->
### 2. Does base damage survive a jump?
**Story.** "the economy and bases as a whole" (also the region fields and drift epic)
**Today.** Whether damage to a base persists across a time jump, and how fast it is rebuilt, depends on the situation. You said: "Depends on the situation, this is simulation work that is tbd".
**The choice.** Open: to be designed with the simulation.
<sub>key: Q-159-13</sub>

<!-- batch.md: Batch C §10 item Lab 2 -->
### Lab 2. Fights that end as ties
**Story.** "the skill lab as a whole"
**Today.** Fights were flagged as ties when units simply stood waiting and nothing came (you, 2026-10-06). The cap on fight length is raised (provisionally to ten minutes), and later a rule was ruled that a fight ends only by elimination. Parked, lab only ("#7 doesn't pertain to beta"), and superseded by the newer layout-search spec.
**The choice.** (a) A side that sees nothing is sent toward the last known or expected enemy position. (b) In the space lab the ping policies find the enemy and the rule fires on a reveal. (c) A fight where a side never engaged is reported as "never engaged", not a tie.
<sub>key: Q-LAB-01</sub>

---

## Parked by Westley (full text of the sections the new batch.md only lists)

Taken by: Westley parked each; not asked until its trigger arrives.

<!-- batch.md: Batch C §6 item 14 -->
### 14. How are trait cards earned?
**Story.** "I unlock trait cards and build a force that plays my way, and cards never beat positioning." [S-083]
**Today.** Unlocking, persistence, whether the enemy fields cards, and how "positioning outweighs any card" is checked in tuning are all undecided. This is post-launch work.
**The choice.** (a) Cards earned by play milestones, account-wide, the enemy draws from the same pool, and the headless matchup check rejects any card that lets a worse-positioned force win. (b) Per-campaign unlocks. (c) Other: your words.
**Recommended.** (a).
<sub>key: Q-083-03</sub>

<!-- batch.md: Batch C §6 item 15 -->
### 15. Travel lanes as a mode?
**Story.** "Someday, perhaps: lanes where my troops move faster and strategic ground where they move slower." [S-165]
**Today.** Your idea of 2026-10-01, marked as an idea only: the map generator makes tree-like lanes of travel giving troops 1.3 times speed, slowdowns at key high ground and layers, and normal speed elsewhere.
**The choice.** (a) A separate game mode. (b) Part of the standard map generator. (c) Dropped.
<sub>key: Q-165-01</sub>

<!-- batch.md: Batch C §11 item 3 -->
### 3. One silhouette per type?
**Story.** "Every unit type has a shape I can read at a glance in any era." [S-132]
**Today.** With 20 to 40 types per era, silhouette carries the information. Parked for the beta ("#5: TBD, beta doesn't need to answer questions like this").
**The choice.** (a) One persistent silhouette per type across every era. (b) Silhouette families per category, with variants read by size and detail. (c) Other: your words.
**Recommended.** (b).
<sub>key: Q-132-02</sub>

<!-- batch.md: Batch C §11 item 8 -->
### 8. Drawing a disguised building
**Story.** "I see workers walk and gather, weather cross the map, and disguised buildings look like what they pretend to be." [S-238]
**Today.** How a disguised or hidden building looks, to its owner and to the enemy, follows how disguise works at all. Parked ("#4: skipped for now").
**The choice.** (a) The enemy sees a decoy look and the owner sees the true building. (b) Both see the true building, with a cover mark for the owner. (c) Decided with the disguise design.
<sub>key: Q-238-01</sub>

<!-- batch.md: Batch C §11 item 11 -->
### 11. Disguising a building
**Story.** "A real economy: run by a partner, or running itself." [S-159]
**Today.** You said on 2026-10-01: "we should also give players a way to disguise/hide their buildings." How, and at what cost, is open. Parked ("#3: skip this for now").
**The choice.** (a) Buildings are unidentified from a distance until scouted, with cheap decoys. (b) A paid cover that hides one building's schedule. (c) Both.
<sub>key: Q-159-09</sub>

<!-- batch.md: Batch C §11 item 12 -->
### 12. How mission tech is derived
**Story.** "I choose the technology my side goes for, and a normal match has time to go up one or two levels." [S-173]
**Today.** The formula taking the simulation's technology level to a mission's starting technology, and what "only slightly" means, is open. Parked as post-beta.
**The choice.** (a) At most one step up or down. (b) A band around the level. (c) Set in the lab.
<sub>key: Q-173-01</sub>

<!-- batch.md: Batch C §11 item 13 -->
### 13. Technology levels per era
**Story.** "I choose the technology my side goes for, and a normal match has time to go up one or two levels." [S-173]
**Today.** The number of levels per era, and the cost and time per level so a timed match fits one or two, are open. Parked as post-beta.
**The choice.** (a) 5 levels per era, your example. (b) Set per era pack. (c) Set by playtest.
<sub>key: Q-173-02</sub>

---

## Old front matter and section intros (verbatim)

<!-- batch.md: lines 1 to 14 -->
# The batch (2026-10-18): what Westley decides offline

You are offline for two hours with no way to ask. Everything in this file is a decision only you can make or a picture only you can judge. Each item gives the story in your own words, what the game does today, and the choice as what a player would see or feel. Internal ids sit only in the small `key` line under each item, so your answers can be folded back without you touching them.

**How to answer.** One file, `answers.md` beside this one, or a message. One line per item:
- a picture: `<file name>: approved` or `rejected — <what is wrong>`
- a question: `<key>: <letter>` or `<key>: <letter> — <your words>`; `<key>: open — <your words>` when none fits; skip anything you don't want to rule yet.

**What your answers set in motion on the Linux box this week:** the pictures decide which screens get their next fix and which prototypes move into the game; the questions in part B decide the chronicle's pacing, the galaxy's look, the camera in space, the land era's identity and the era roster, and the shape of generated maps; the flags in part C decide the roster of units, how missions and the chronicle read the simulation, the difficulty knobs and the lab's pass marks. Everything that was only an implementation choice has already been taken by the Architect and is listed in `README.md` section C for your veto.

Three parts: **A** 24 pictures (the files are beside this folder in `docs/northstar/story_reviews/westley/`); **B** 27 design questions; **C** 111 open flags from the register, grouped. The economy numbers are not asked (you tune those by feel). Part C is long; the first three sections unblock the most.

<!-- batch.md: intro of # Batch B: the questions, in plain words -->
# Batch B: the questions, in plain words

Answer each as `<key>: <letter> - <words if any>`, using the key line under the question. Where a question has no letters, answer yes or no. A lean is the Architect's opinion, not a ruling.

<!-- batch.md: intro of # Batch C: the open design flags, in plain words -->
# Batch C: the open design flags, in plain words

Answer by key and letter, one per line, for example `Q-082-03: a` or `Q-082-03: c, plus your words`. The economy numbers (which you tune by feel), the flags the Architect already took, and the parked ones are not here; they are listed in the register extract. Fights are timed in seconds here (twenty steps of the fight clock make a second). A unit is about 23 world units across, so "a unit" below is a width, and a map canvas of 16,000 world units is about 700 units wide.

<!-- batch.md: intro of ## 1. Beta blockers and the Now table -->
## 1. Beta blockers and the Now table

<!-- batch.md: intro of ## 2. Combat framework -->
## 2. Combat framework

<!-- batch.md: intro of ## 3. Era roster and packs -->
## 3. Era roster and packs

<!-- batch.md: intro of ## 4. Client HUD and screens -->
## 4. Client HUD and screens

<!-- batch.md: intro of ## 5. Enemy, difficulty, missions -->
## 5. Enemy, difficulty, missions

<!-- batch.md: intro of ## 6. Sim and chronicle bridge -->
## 6. Sim and chronicle bridge

<!-- batch.md: intro of ## 8. Everything else open, alphabetical by id -->
## 8. Everything else open, alphabetical by id

<!-- batch.md: intro of ## 11. Dropped by the lab filter, asked anyway -->
## 11. Dropped by the lab filter, asked anyway

<!-- batch.md: intro of ## 9. Finish-the-loop items (parked, now reachable by the si -->
## 9. Finish-the-loop items (parked, now reachable by the sim lane)

<!-- batch.md: intro of ## 10. Skill lab pass marks (you set each) -->
## 10. Skill lab pass marks (you set each)

The skill lab is where tactical combat is measured on the real sim, to prove your sentence: "players with better understanding of the landscape, unit formation, layer awareness/intentionality, and the other players current position can defeat a much larger force." It judges rule sets with ten conditions. The marks below are drafts; none is confirmed. A "play" is a scripted skilled or naive way of fighting, and "the firing count" is how many units can get shots off, which your principle says decides a fight. The five skills are landscape, formation, layers, enemy position and unit-type matchup.

## Moved 2026-10-21 (batch.md rewrite)

Old batch.md header, kept for the record:

> # The batch (2026-10-18, slimmed 2026-10-21): what only Westley decides
>
> Fourteen open design questions, in the order they unblock work, and eight you have parked. The implementation choices the Architect took, the rows the record already answers, the duplicates, the moot rows and the 2026-10-18 shots are in `batch_closed.md` (veto any of them in one line).
> Answer in `answers.md` beside this file, one line each: `<key>: <letter>` or `<key>: <letter> - <your words>`; `<key>: open - <your words>` when none fits. Skip anything you do not want to rule yet.
> Shots still waiting for your eye are in the page table `../../story_reviews/westley/README.md`. Q-069-03 is answered (2026-10-19) and moved out.

## Parked by you

| id | topic | your parking words |
|---|---|---|
| Q-083-03 | How trait cards are earned | Post-launch work. |
| Q-132-02 | One silhouette per type | "Beta doesn't need to answer questions like this" (2026-10-07). |
| Q-159-09 | Disguising a building | "Skip this for now" (2026-10-07). |
| Q-238-01 | Drawing a disguised building | Follows the disguise design ("skipped for now", 2026-10-07). |
| Q-173-01 | How mission tech is derived | "Post-beta". |
| Q-173-02 | Tech levels per era | "Post-beta". |
| Q-165-01 | Travel lanes as a mode (also covers pacing tools in the layout kit) | "Only an idea, not a decision." |
| Q-180-01 | Form of the solo dial: three positions, a slider or a triangle | Asked with a shot when the economy lane reaches it. |

The 14 open design questions of the old page are kept, trimmed, in the new batch.md section 2.

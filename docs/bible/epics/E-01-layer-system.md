# E-01 — Layer System

## Definition-completeness gate (run 2026-09-10)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Yes, 15 stories, 82 rules. Rules that depend on an open flag cite it inline. |
| Every input listed with range and rejection behavior | Yes, see Inputs. Every rejection behavior is settled. |
| Every output listed with where it is observable | Yes, see Outputs. On-screen elevation follows the map's fitted height bands on land maps (S-010, S-200); per-step numbers scale with the height of the step, and how is Q-166-04, which the skill lab measures. |
| Implied-but-unstated behavior turned into flags | Yes; the 12 flags still open are listed at the foot of this file. |
| Every visible-surface story has a reference | **No — by design a Godot design phase, not a screenshot pull.** `references/E-01/notes.md` records the plan: basic single-layer movement ships first, then Claude builds several interactive layer-system options in Godot for Westley to choose between; the choice fills the references. Blocks S-009 and S-010 until then. |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed for S-008, S-009, S-010 and S-200; the rest are buildable, except the part of S-163 that carries a new open flag (none remains).** S-008 is blocked on Q-008-02, Q-008-03, Q-008-05, Q-008-06 and Q-008-07 (the skill lab decides the cross-layer numbers), S-009 on Q-009-02, S-009 and S-010 on references, and S-200 on Q-166-04 and Q-189-02 (its design is decided and not scheduled for building). S-001 to S-004 and S-162 to S-164 carry provisional numbers held as runtime settings and are built by the engine cascade in `docs/northstar/plans/2026-10-02-skill-lab-cascade.md`.

## Purpose

The layer system is the game's strategic defining characteristic. The battlefield is not a flat plane. It is a stack of five vertical layers, and a unit is always on exactly one of them. The layers are numbered 1 to 5 from the bottom; the engine and its tests count the same layers 0 to 4, so layer n here is engine layer n - 1. Terrain blocks layers at specific places, so a force can go over an obstacle on a high layer or around it on a low one. Vision across layers is worse than vision on your own layer, so a force on a layer you cannot see is a threat you do not know about. Changing layers costs time and leaves the unit briefly vulnerable.

The promise this keeps for the player (vision_v2 Q6): a smaller force that understands surrounds, high ground, and layers beats a larger force that does not. Layers are one of five understandings (landscape, formation, layers, the enemy's position, unit-type matchup) that together let a smaller force beat a larger one (hub principle 4; `docs/northstar/research/layer_dynamics/README.md` section 3). Every rule below exists to make that promise testable.

Era-agnostic: the engine knows "layers 1 and 2 are blocked here." The era pack decides whether that is an asteroid, a mountain, or a reef. Every era has an era kind, space or ground, a formal property of the pack (Westley, 2026-10-05: "space/ground is a formal property, though eras with flying units in ground eras like WW2 may pull from pieces of the space property to model airplane movements/vision. That's the only exception, otherwise it's a clean separation"). The kind decides the vision model (S-005), whether the ping exists (S-162), and whether the ground is the layers (S-200). Launch ships two simple eras, one in space (the Settled Reach) and one on land, with the same units and rules within a kind and different landscape and visuals (Westley, 2026-10-02 and 2026-10-05), and with no per-unit-type layer restriction mask. The space landscape is not designed (Q-166-02), so this epic writes no landscape rules for it.

## Obviously working in 60 seconds

Spawn a Raider and a Bastion on layer 3 next to a tall obstacle. Order both to layer 5. The Raider rises visibly within a second, the Bastion takes several seconds, and each unit's ring changes color when its layer changes. Place an enemy on layer 1 under the obstacle: neither unit sees it. Move an enemy onto layer 4 within half the Raider's sensor range: the Raider sees it, the Bastion does not until it is closer. Ping layer 1 at the obstacle from a unit that can ping: the layer-1 enemy appears for a moment (provisional 2 seconds, Q-005-04), then vanishes, and the pinged side sees an alert pointing about 60 degrees toward the pinger. Put the Raider on layer 1 on one side of the obstacle and order it to a point on the far side where layers 1 and 2 are blocked and layer 3 is open: it walks to the obstacle's edge, rises to layer 3 on its own, crosses, and arrives; with no open layer at the destination it stops as close as it can get on layer 1.

## Stories

### S-001 — The map decides where each layer is open
As a commander, I want terrain to block specific layers at specific places, so that going over, going around, and hiding in the blocked layers are real choices.

Rules
- R-001-01  Given a map position where layers 1 and 2 are blocked and layers 3 to 5 are open, When any unit on layer 1 or 2 is ordered to move through that position, Then the unit never occupies the blocked position on layers 1 or 2; its path detours around the blocked area on its current layer or changes layer, whichever route is shortest (R-001-05).
- R-001-02  Given the same position, When a unit on layer 3 moves through it, Then the unit passes straight through with no detour.
- R-001-03  Given a position where every layer is open, When any unit moves through it, Then no layer restriction applies.
- R-001-04  Given any map generated for any era pack, When the map is queried for layer accessibility at every sampled position and layer, Then the answer is a binary open or blocked per layer, and the count of layers is the same for every position on that map.
- R-001-05  Given a unit ordered to move to a destination, When its route is planned, Then it takes the route with the shortest travel time to the goal, counting each transfer, across every layer it may use, changing layer along the way wherever that shortens the route (a flying or swimming unit by a timed transfer, a walking unit by a slope, R-001-07), with S-004's time and exposure applying to each change; so a unit on layer 1 ordered to a place on layer 1 crosses layer 2 when layer 2 lies on the shortest route; and Given a destination blocked on every layer the unit may occupy, When the order is issued, Then the unit paths as close as it can and stops; a flying unit ends on the layer it was ordered on, a pending hard transfer stays pending, and a preferred layer is returned to where it is open (provisional, held as runtime settings).
- R-001-06  Given a map with a slope, When the slope is queried, Then it is a band of ground that joins two layers, adjacent or not (a slope may climb several layers), with a bottom edge on the lower layer, a top edge on the upper layer, a length between them, and a midline halfway along that length; a slope that spans more than two layers has a cross-over at each layer boundary, evenly spaced along its length, and a unit on it counts as on each layer in turn; a unit moving along it passes from one layer to the other (S-004). A map with no slopes, such as open space, has only timed transfers.
- R-001-07  Given a unit type, When its movement kind is read, Then it is walking, or flying or swimming, set per unit type in the era pack, every Settled Reach type flies and the land era has walking types (E-11 S-201); and Given a flying or swimming unit at a position where the target layer is open and nothing blocks it, When it is ordered or routed (R-001-05) to change layer, Then it makes a timed transfer there (S-004); and Given a walking unit, When it moves, Then it occupies only a layer that has land at its position (the map carries a ground flag per layer per position beside the open or blocked mask), it changes layer only by walking a slope that joins the two layers, and it never changes layer in place or skips layers without ground under it; and Given a walking unit, When a layer order of any kind reaches it, Then nothing happens: a walker has no layer selector, because at any point there is only the one layer that has ground there (Westley, 2026-10-06: "for walking units, there's only 1 layer they can ever go on. Walking units do not need a layer selector, they cannot be commanded to go on another layer other than the only layer that exists at that specific point"; caves, if ever, are a later question).

Inputs: map layer accessibility mask (binary per layer per position); ground flag per layer per position on land maps (S-200); unit position; unit current layer.
Outputs: unit path; unit position over time; layer accessibility query result.
Open flags: none. The route-change readings in R-001-05 are provisional, held as runtime settings.

### S-002 — Hard layer transfer
As a commander, I want to order selected units to a specific layer, so that I can commit a force to a height when timing matters.

Rules
- R-002-01  Given a selected unit on layer 3 at a position where layer 5 is open, When the player issues a hard transfer to layer 5, Then the unit begins its transition on the same tick and finishes on layer 5 after its transition duration (S-004).
- R-002-02  Given a selected unit at a position where layer 5 is blocked, When the player issues a hard transfer to layer 5, Then the unit keeps executing its current orders on its current layer, and begins the transition on the first tick it occupies a position where layer 5 is open; and if the unit's route (R-001-05) changes its layer first, the transfer stays pending.
- R-002-03  Given a unit with a pending hard transfer, When the player issues a second hard transfer to a different layer, Then the first transfer is discarded and only the second is pending.
- R-002-04  Given a unit with a pending hard transfer, When the player issues a move order, Then the transfer stays pending; a move order never clears a transfer.
- R-002-05  Given a hard transfer to the unit's current layer, When it is issued, Then it is accepted and completes immediately with no transition and no vulnerability window.
- R-002-06  Given a hard transfer to a layer outside the map's layer range, When it is issued, Then it is rejected and the unit's state does not change.
- R-002-07  Given a hard transfer order for a mixed selection, When it is issued, Then every unit in the selection gets its own pending transfer and each resolves independently by its own position and duration.
- R-002-08  Given one or more selected units, When the player presses Alt plus a layer number (Cmd on macOS) and then clicks the map, Then the whole selection receives a hard transfer (R-002-01) to that layer, the clicked spot being where the change is made; Alt plus the number arms the order and the click completes it (Westley 2026-10-13: "Alt + number queues up alt + number + click for the entire selection to be clicked somewhere."); no on-screen "To layer" button is the control; Ctrl plus a digit is control groups (Westley 2026-10-13: "Alt is for layers, control is for groups, shift is still free"); R-003-07's modifier is open (Q-003-02).

Inputs: layer command (target layer, integer in map range, from Alt (Cmd on macOS) plus a layer key, armed for the whole selection, then a map click, R-002-08); selection (1 to N units); unit position; accessibility mask.
Outputs: per-unit pending transfer; per-unit layer field in the tick delta; transition start and end events.
Open flags: none. The route-change readings it relies on (R-001-05) are provisional, held as runtime settings.

### S-003 — Layer preference
As a commander, I want to give units a standing preference for a layer, so that a scouting group stays high and a siege group stays low without me re-ordering them at every obstacle.

Rules
- R-003-01  Given a selected unit with no preference, When the player sets preference to layer 2, Then the unit's preference is 2 and it begins a transition to layer 2 on the first tick it is at a position where layer 2 is open and it is not already on layer 2.
- R-003-02  Given a unit with preference 2 currently on layer 4 because layer 2 is blocked here, When the unit moves to a position where layer 2 is open, Then it begins its transition to layer 2 on that tick without a new order.
- R-003-03  Given a unit with preference 2 at a position where layer 2 is blocked, When any number of ticks pass, Then the unit continues its current orders on its current layer and never stalls or stops to wait; a preferred layer is returned to where it is open (R-001-05).
- R-003-04  Given a unit with preference 2, When the player issues a hard transfer to layer 4, Then the preference is cleared and the hard transfer proceeds.
- R-003-05  Given a unit with preference 2, When the player issues the clear-preference action, Then the preference is cleared and the unit stays on its current layer.
- R-003-06  Given a unit with preference 2, When the player sets preference 3, Then the preference is 3 and any pending transition toward 2 is replaced.
- R-003-07  Given the modifier key held, When the player presses 1 through 5, Then that is a preference assignment, not a control-group recall; and Given the modifier key released, When the player presses 1 through 5, Then that is the standard control-group recall.
- R-003-08  Given a saved mission, When it is loaded, Then every unit's preference is restored exactly.

Inputs: preference command (layer integer or clear); modifier key state; selection.
Outputs: per-unit preferred layer in the tick delta; preference indicator on screen (S-009); save file.
Open flags: none. The route-change readings it relies on (R-001-05) are provisional, held as runtime settings.

### S-004 — Changing layers takes time and leaves you exposed
As a commander, I want a layer change to cost time, set by the unit type for a transfer in the open and by the slope's length and my unit's speed on a slope, so that changing layers always exposes the unit and the halfway point of a slope is a line on the map I can read and hold.

Rules
- R-004-01  Given a Raider that flies or swims (R-001-07) ordered from layer 3 to layer 4 at an open position away from any slope, When the transition starts, Then the unit is on layer 4 exactly one transition duration later, with the duration taken from the unit type's transition time (Raider 1.0 s, Interceptor 1.2 s, Vanguard 2.5 s, Warden 2.0 s, Bombard 4.0 s, Bastion 5.0 s, confirmed as design values); in the space eras a timed transfer takes the same time down as up.
- R-004-02  Given a unit mid-transition, When a unit on its old layer would attack it, Then the attack may target it until the transition is halfway completed (half the duration for a timed transfer; the midline for a slope, R-004-06) and not after; and When a unit on its new layer would attack it, Then the attack may target it from the halfway point on and not before; whether either attacker sees it follows the normal cross-layer sensor rules (S-005); and the transitioning unit itself attacks, in a timed transfer or on a slope, as a unit of the layer it is leaving until it reaches the cross-over point (halfway through a timed transfer, the midline of a slope) and as a unit of the layer it is moving to from then on; it attacks only a target its side can see (S-005, R-008-04), and stops attacking a target the moment its side loses sight of it.
- R-004-03  Given two units of different types ordered to the same layer at the same tick, When the faster type completes, Then the slower type is still mid-transition, and completion order always matches transition-time order.
- R-004-04  Given a unit mid-transition, When a new hard transfer to another layer is issued, Then the unit completes the current transition first and the new transfer becomes pending.
- R-004-05  Given the same seed and the same command stream, When the mission runs twice, Then every transition starts and ends on the same tick both times.
- R-004-06  Given a unit on a slope that joins layers L and L+1, When it is at any point along the slope's length, Then its transition progress is its position along the slope, not a timer: below the midline, units on layer L may attack it and units on layer L+1 may not; at or above the midline, units on layer L+1 may attack it and units on layer L may not; the same holds going up or down; on a slope that spans more than two layers the same holds at each cross-over (R-001-06).
- R-004-07  Given a slope 600 world units long, When a Raider (speed 150) and a Bastion (speed 40) each move along it without stopping, Then going up the Raider takes 4.4 seconds and the Bastion 16.5 seconds (speed divided by 1.1), and going down 3.6 and 13.6 seconds (speed times 1.1); on a slope 150 long, up 1.1 and 4.1, down 0.9 and 3.4 (Westley, 2026-10-06: "1.1x slowing uphill, 1.1x speed on downhill"; the 1.1 is a provisional setting); the unit type's transition time (R-004-01) plays no part on a slope.
- R-004-08  Given a unit part-way along a slope, When the player orders it to stop or to move back the way it came, Then it stops or turns back; R-004-04's rule that a transition completes first applies only to timed transfers; while on the slope the unit counts as being on the layer on its side of the midline, for its own sensing and for what may attack it, so a unit that turns back before the midline has not changed layer and one that crosses the midline and comes back has changed twice.

Inputs: unit type transition time (per type, config); transition start tick; slope position, length and the two layers it joins (map); unit speed and position.
Outputs: unit layer field; transitioning flag and progress in the tick delta; attack eligibility.
Open flags: Q-166-04 (the transition times, set per unit type, scale with the height of the layer step now that height bands are fitted per map, and how is to be measured by the skill lab; a slope's crossing time already follows its length). A strongpoint at a slope holds the way up or down: its rules are E-15 S-126 and E-17 S-192.

### S-005 — Seeing across layers is worse than seeing on your own
As a commander, I want cross-layer vision to shrink with layer distance, so that a force on a layer I am not watching is a real threat.

Rules
- R-005-01  Given an observer with sensor radius 1,000 on layer 3 and an enemy on layer 3 at distance 900, When one tick passes, Then the enemy is in the observer's visible set.
- R-005-02  Given the same observer and an enemy on layer 4 at distance 400, When one tick passes, Then the enemy is visible (adjacent layer factor 0.50, effective radius 500).
- R-005-03  Given the same observer and an enemy on layer 4 at distance 600, When one tick passes, Then the enemy is not visible.
- R-005-04  Given the same observer and an enemy on layer 5 at distance 150, When one tick passes, Then the enemy is visible (two-layer factor 0.20, effective radius 200); at distance 250 it is not.
- R-005-05  Given the same observer and an enemy on layer 1 (two layers below) at distance 150, When one tick passes, Then the enemy is visible exactly as the enemy two layers above is (R-005-04): vision is symmetric by layer distance; and Given an observer on layer 1 and an enemy on layer 4 or 5, or any pair three or more layers apart in either direction, When one tick passes, Then the enemy is never visible by passive detection at any distance.
- R-005-06  Given a space era and an observer standing at a vantage node (retired for ground eras, Westley, 2026-10-05: "retire them yes"; high ground sees down there, R-005-09), When the same enemies are placed, Then the adjacent factor is 1.00, the two-layer factor is 0.40, and a three-layer enemy is visible at factor 0.20.
- R-005-07  Given an observer inside a sensor interference zone of intensity 0.5, When an enemy is on an adjacent layer, Then the effective cross-layer radius is sensor radius × 0.50 × 0.50.
- R-005-08  Given fog on, When an enemy on another layer is outside the effective cross-layer radius, Then it is hidden from the player exactly as a same-layer enemy outside sensor radius is hidden: no silhouette, no marker, no special treatment.

Inputs: observer layer, position, sensor radius; target layer, position; vantage membership; interference intensity at observer position.
Outputs: per-unit visible set in the tick delta; player-visible unit list; fog reveal on screen.
Open flags: Q-005-05, Q-005-06 (parked for the beta); Q-166-04 (the vision factors scale with the height of the layer step on a map with fitted height bands, and how is to be measured by the skill lab).
Which model applies is the era kind (Westley, 2026-10-05, verbatim): "Space eras and Ground eras are different in terms of vision. Ground eras are just like Starcraft 2, high ground can see down, low ground can't see up. Space eras relies on the pinging system because there's no limit on up/down viewing like there is on land." R-005-01 to R-005-08 are the space model: symmetric by layer distance, and very limited ("passive cross-layer sight is very limited, to induce strategic depth, ping reaches past it in every layer/direction"); the factors 0.50 and 0.20 are provisional and not his [Q-005-07]. The ground model is R-005-09 to R-005-11. Q-005-02's condition on asymmetric vision (2026-10-01: "going asymmetic could be a good idea if there's a \"counter\" to the highest layer being hte \"best\", say a unit that works particularly well at destroying units from above it to counter") still stands for the space model; the ground model is not asymmetry inside one model but the other kind's model (Westley, 2026-10-05: "Q-005-02 this is still true, it's just that we're not seperating space from ground eras").

Ground model (land eras; every number provisional):
- R-005-09  Given a ground era, an observer and an enemy within the observer's sensor radius, When the enemy is on a lower layer than the observer, Then the enemy is visible (high ground sees down); and When the enemy is on a higher layer, Then it is never visible by passive detection at any distance (Westley, 2026-10-05: "zero, like starcraft 2") (a unit on a slope counts as the band on its side of the midline, R-004-06; Westley, 2026-10-06; the eye height of the sight line is a provisional lab setting).
- R-005-10  Given a ground era, When ground stands between an observer and an enemy on the same or a lower layer, Then the ground blocks sight (Westley, 2026-10-05: "blocks site"), as cover of sufficient height does (S-007; a line across layers follows R-007-07).
- R-005-11  Given a flying unit in a ground era, When it is above the ground's layer, Then it sees down onto lower layers as high ground does, and it is visible to units below from farther away than it can see them (Westley, 2026-10-05: "yes it sees down, but it's visible from farther away than it can see") (the seen-from distance is a provisional lab setting, always longer than the flyer's own sight: Westley, 2026-10-06, "lab draft, so long as it's longer than the flyer's own vision") [Q-005-06: which other pieces of the space model a ground-era flyer borrows].
- R-005-12  Given a ground era, When vision beyond passive sight is wanted, Then it comes from units, not from the ping: seer-type units (E-11 S-201; Westley, 2026-10-05: "ground eras will get seer type units yes"; "a simple placeholder unit that's a scout is sufficient for now") and, less aggressively than the ping, scouts (R-162-04).

### S-006 — Sensor pulse
As a commander, I want to spend a pulse to see every layer around a unit for a moment, so that scouting before a commitment is a decision with a cost.

Rules
- R-006-01  Given a pulse-capable unit with its pulse ready, When the player triggers the pulse, Then every enemy on every layer within the pulse radius is in the player's visible set for the next 2.0 seconds of sim time (40 ticks at 20 ticks per second).
- R-006-02  Given a pulse that started 2.0 seconds ago, When the next tick runs, Then enemies revealed only by the pulse leave the visible set.
- R-006-03  Given a pulse fired on tick T, When the player tries again before tick T plus 20.0 seconds (400 ticks), Then the command is rejected and the cooldown is unchanged.
- R-006-04  Given the pulse-capable unit is inside an interference zone of intensity 0.5, When it pulses, Then the pulse radius is halved.
- R-006-05  Given a pulse reveals an enemy on layer 1 while the observer is on layer 5, When the pulse expires and no passive detection applies, Then the enemy is hidden again.

Inputs: pulse command; pulse-capable unit; pulse radius (config); cooldown state.
Outputs: pulse active flag and remaining cooldown in the tick delta; revealed set; cooldown ring on the HUD; visible pulse effect on screen.
Open flags: none. The pulse is not built: the targeted ping of S-162 takes its place.

### S-007 — Cover blocks sight by height
As a commander, I want a tall obstacle to hide units on more layers than a short one, so that where I put a force relative to terrain changes what the enemy can see.

Rules
- R-007-01  Given an obstacle whose height reaches layer 2 between an observer and a target both on layer 1, When one tick passes, Then the target is not visible.
- R-007-02  Given the same obstacle and both units on layer 3, When one tick passes, Then the target is visible (the obstacle does not reach layer 3).
- R-007-03  Given a target hidden behind cover, When it attacks an observer that cannot see it, Then the attack lands and the target stays hidden; firing never reveals.
- R-007-04  Given a target visible despite nearby cover, When it takes damage, Then damage is unmodified; cover is never a damage reduction.
- R-007-05  Given cover in a unit's path, When it moves, Then movement is unaffected; cover never blocks movement.
- R-007-06  Given a unit standing inside a cover obstacle's footprint, When sight and fire are computed, Then it is seen and fired at as any unit in the open: an obstacle blocks only a line that passes through it between two units that are both outside it, and only on the layers its height reaches (R-007-01, R-007-02; Westley, 2026-10-02).
- R-007-07  Given an observer and a target on different layers, When a cover obstacle or the ground lies between them, Then the same rule applies as on one layer, with the line's height interpolated between the two layers: cover or ground the line passes through blocks the sight line and the line of fire (Westley, 2026-10-07: "#1: A"). A unit whose line of fire is blocked seeks a firing spot (E-11 R-087-09).

Inputs: obstacle position, radius, height; observer and target positions and layers; the ground on land maps (S-200).
Outputs: visible set; damage applied; unit path.
Open flags: none.

### S-008 — Combat across layers
As a commander, I want to know whether a unit can shoot at an enemy one layer above it, so that layer position is a positional decision and not a guess. The cross-layer rules are decided by measurement: the skill lab (`docs/northstar/research/layer_dynamics/README.md`, `scripts/skilllab/`) runs small engagements on the real simulation, varies range, damage, vision and terrain, and maps where the skilled side wins because of the engagement's conditions. Its numbers may become the rules below.

Rules
- R-008-01  Given an attacker on layer 3 and a visible enemy on layer 3 in range, When the attacker is idle or attack-moving, Then it engages.
- R-008-02  Given an attacker on layer 3 and a visible enemy on layer 4 in range, When the attacker is idle or attack-moving, Then it engages only if its unit type's reach includes one layer up (S-164); the range and damage at that offset are Q-008-03.
- R-008-03  Given a Bombard's area attack centered on layer 3, When enemies stand on layers 2 and 4 inside the radius, Then they take damage only at the layer offsets the Bombard's reach includes (S-164), at the multiplier Q-008-03 sets.
- R-008-04  Given an attacker whose side cannot see a target (S-005, E-12 R-093-02), When it would attack that target, Then it does not: a unit never fires at a target its side cannot see, on its own layer or another; a target seen by any friendly unit or revealed by a ping may be fired at.

End-state (the acceptance bar): the hub's definition of strategic depth (principle 4) holds in the skill lab before any cross-layer number is fixed. The mechanisms are built with provisional numbers held as runtime settings, so that the lab can move them. In the lab's terms (`docs/northstar/research/layer_dynamics/README.md` section 4): across the space maps, each skilled play wins the count of units able to fire, the result follows that count, the five skills (landscape, formation, layers, enemy position, unit-type matchup) stack with none dominant and none dead, each has an answer on most maps, and the best situations let a side beat a much larger force. Abilities are left out of this bar for now (Westley, 2026-09-30: "let's leave specific abilities out of this calculation for now, we're tuning base unit properties").

Inputs: attacker layer, target layer, range, visibility; the cross-layer rule table (range, damage and area multipliers by signed layer offset, fire-requires-vision, halfway rule) once Q-008-03 closes.
Outputs: attack events; HP changes in the tick delta.
Open flags: Q-008-02 (the research program that decides the cross-layer design, now the skill lab on the real simulation), Q-008-03 (the cross-layer numbers), Q-008-05 (concentration of fire: whether it joins the principle; the nearest enemy stays the game's target rule and a lab-only setting measures focus fire), Q-008-06 (how refusing a fight, which counts as a counter, is checked), Q-008-07 (whether unit-type matchup is judged by the firing count weighted by category).
The prototype is same-layer only until the lab reports.

### S-009 — I can see what layer every unit is on
As a commander, I want to see at a glance which layer each unit is on and which layer I am focused on, so that I never have to guess who can see whom.

Rules
- R-009-01  Given any unit on screen, When the player looks at it, Then a ring under the unit shows one color per layer, and the color changes on the tick the unit's layer changes.
- R-009-02  Given a unit toggled toward another layer, When the player looks at it, Then the target disc on its spindle (R-009-05) gains an outline and a chevron, a waypoint-like mark of where it is going, distinct from the lit current-layer disc.
- R-009-05  Given any unit on screen, When drawn, Then a thin rod beside it carries five small discs, one per layer, the unit's own disc lit at about 50 percent, adjacent discs at 10 to 20 percent, discs two away at 5 percent (the Floor Spindle); and its grid tiers are flat discs that tilt to the ground's slope at each layer's height (Terrace Reading). Both are subdued, never loud, and never block the view of the battlefield behind them.
- R-009-06  Given units hidden from the player by the current perspective (behind terrain or another layer's ground), When the player looks at the scene, Then for the beta the vision tube (E-17 S-246) lets the player see them and no occlusion mark is drawn; a small mark on the occluding units is post-beta (Westley, 2026-10-07).
- R-009-03  Given the layer strip on the HUD, When the player clicks a layer or presses Tab, Then the focused layer changes and the strip highlights the new one.
- R-009-04  Given the same selection and camera, When a T2 screenshot is taken, Then the ring colors match the sim's per-unit layer field for every unit in view.

Inputs: unit layer, preferred layer; focus click or Tab.
Outputs: ring color per unit; spindle and terrace discs; target mark; focused layer on the strip.
Open flags: none.
Focus is purely visual: other layers dim slightly. The look was chosen through the options pass, `docs/northstar/research/options/layer-system/`; Godot renders of it fill `references/E-01/notes.md`.

### S-010 — Layers read as height on screen
As a commander, I want a unit on a higher layer to sit visibly higher than one on a lower layer, so that the layer stack reads as a stack and not as a color code.

Rules
- R-010-01  Given a unit on layer L at position (x, y), When it is drawn, Then its world-space height is the elevation of layer L from that map's height bands, which are fitted to the map and not fixed globally (S-200, E-17 S-188); the code's three z-bands (0 to 30, 30 to 100, 100 to 300 world units) for a five-layer count are a defect against this. On a space map the mapping is open (Q-166-02).
- R-010-02  Given a unit transitioning from layer 3 to 4, When frames render during the transition, Then its drawn height moves from layer 3's elevation to layer 4's over the transition duration, not as a snap.
- R-010-03  Given a fixed camera on a map whose bands are fitted (R-010-01) and a unit ordered up one layer, When a T2 screenshot is taken before and after, Then the unit's screen position differs vertically by more than 5 percent of the viewport height; a layer step on a fitted map is a real height difference (E-17 S-188).

Inputs: the map's fitted height bands (layer to elevation); camera.
Outputs: unit world position on screen.
Open flags: none. Reference required: `references/E-01/notes.md`, missing.

### S-011 — Era packs may restrict unit types to layers
As an era designer, I want an era pack to say which layers a unit type may occupy, so that a submarine era or a ground-only era works on the same engine without code changes.

Rules
- R-011-01  Given the Settled Reach era pack (no restriction mask), When any unit type is ordered to any open layer, Then it is accepted.
- R-011-02  Given an era pack whose mask permits type X on layers 4 and 5 only, When a type-X unit is ordered to layer 2, Then the order is rejected and the unit stays on its layer.
- R-011-03  Given the same pack, When a type-X unit spawns, Then it spawns on a permitted layer.
- R-011-04  Given the same pack, When a type-X unit has preference 2, Then the preference is rejected at assignment time.

Inputs: era pack restriction mask (per unit type, set of layers; absent means unrestricted).
Outputs: command acceptance; spawn layer.
Open flags: none. Launch scope: capability present, mask absent (A-294, A-321).

### S-162 — Targeted ping
As a commander, I want to ping a layer I choose at a place I choose and see it for a moment, so that looking across layers is something I do on purpose and at a distance.

Rules
- R-162-01  Given a space era (ground eras have no ping for now: Westley, 2026-10-05, "Not as of right now, we'll give them vision options in the form of units"; R-005-12) and selected units, When the player chooses the ping, presses a layer number and clicks a place, Then every enemy unit on that layer around that place at that moment becomes visible to the player and stays visible for a short time wherever it moves, at a reach much longer than passive cross-layer vision (S-005) and well short of the whole map: radius 500, reveal 5 s, reach 2,000. Every unit can ping for now (Westley, 2026-10-05: "every unit for now"; "reveal follows units caught for a short time, starting with 5 seconds is probably good") Cover and ground between the caster and the place do not stop the ping: it sees behind them (Westley, 2026-10-07: "#2: A").
- R-162-02  Given a ping, When it is cast, Then it costs the player no resource, and the casting unit has a cooldown of 20 s.
- R-162-03  Given a player whose units are pinged, When the ping lands, Then that player is told nothing. The alert, a sector of about 60 degrees pointing toward the caster, is switched off for now (Westley, 2026-10-05: "Let's skip the alert actually, I'm realizing that enemies will just ping back, switch that off for now").
- R-162-04  Given a ground era, or a space era without the technology for a ping, When the player wants to look where passive sight does not reach, Then small scouts that cost nothing may carry a look, used less aggressively than the ping (Westley, 2026-10-01: "we could have them send out little scouts that cost nothing"; 2026-10-05: "we can still keep scouts, but less aggressively than the pinging, we'll play around with what we do based on what players like") [Q-162-06: what a scout is and what it reveals].
- R-162-05  Given a ping that has ended, When no passive detection applies, Then the units it revealed are hidden again.

Inputs: ping command (selection, layer, place); era kind (space: ping; ground: units and scouts).
Outputs: the revealed units for the reveal time; the cooldown of 20 s per unit.
Open flags: none.
The numbers are provisional runtime settings, tuned by the skill lab.

### S-163 — Going dark
As a commander, I want to choose which of my forces look and which stay quiet, so that seeing further is paid for by being seen, and a quiet force can wait unseen.
Space eras only, for now (Westley, 2026-10-05: "going dark and reach by type are only space for now").

Rules
- R-163-01  Given a force set to emit, When it is on the field, Then it sees other layers further than passive vision allows, and units on every layer, its own included, see it from further away than they otherwise would; emitting widens how far it can be seen by more than it widens how far it sees (Westley, 2026-10-07: "emitting should extend the area that you can be seen beyond what you can see"). Provisional: cross-layer sight doubles, and the seen-from distance grows by more than that, held as runtime settings.
- R-163-02  Given a force set to silent, When it is on the field, Then it is harder to see from other layers and gives up the extra sight that emitting gives [Q-005-04: by how much, and whether its passive cross-layer sight shrinks too].
- R-163-03  Given a force, When the player switches it between emitting and silent, Then it is a toggle on a unit or on a group (Westley, 2026-10-07: "a toggle the player can toggle through per unit or group"), and the switch costs no resource. Emitting's only drawback is the wider radius from which opponents detect the force (R-163-01; Westley, 2026-10-07: "The \"cost\" is increased detectability radius from opponents, that's it.") [Q-005-04: whether the switch takes time].

Inputs: emit or silent command; selection.
Outputs: the force's state in the tick delta; its sight and its visibility to others; a mark on screen showing which forces are emitting.
Open flags: none.
Silent is the default. The numbers are provisional runtime settings, tuned by the skill lab.

### S-164 — Reach by unit type
As a commander, I want each unit type to reach only certain layers with its fire, so that where I put each type, and which type I put under or over the enemy, decides who gets shots off.
Space eras only, for now (Westley, 2026-10-05: "going dark and reach by type are only space for now"); a ground era fights by the ground model (S-005 R-005-09 to R-005-12).

Rules
- R-164-01  Given a unit type, When its reach is read, Then it names the layer offsets it can fire at: its own layer, and how many layers up and how many down: Line its own layer, Raider one layer either way, Interceptor two up and one down, Siege two down [Q-008-03: the range and damage at each offset].
- R-164-02  Given a target at a layer offset outside the attacker's reach, When the attacker would fire, Then it does not, whatever the distance.
- R-164-03  Given the roster, When reach is assigned, Then a type that reaches further is weaker to something another type does, so its advantage is temporary (Westley, 2026-10-01: "units with higher range will hypothetically have an advantage but they should be weaker to certain things, thus making the advantage temporary") [Q-005-04: the weaknesses, and whether one type must fire upward well, which he raised as an example of a counter to the top layer].

Inputs: unit type reach table (roster, per era).
Outputs: attack eligibility by layer offset.
Open flags: Q-166-04 (the reach table scales with the height of the layer step on a map with fitted height bands, and how is to be measured by the skill lab).
The reach table is provisional. The range and damage at each offset are S-008's question (Q-008-03).

### S-200 — On land, the ground is the layers
As a commander on a land map, I want the height of the ground to decide which layers are ground and which are air, so that a mountainside, a valley and a cliff are real places that walking and flying units use differently.

Design decided 2026-10-02, not scheduled for building. These rules apply to land maps. The space-era landscape is a sister system that is not designed yet (Q-166-02), and no rule here is written for it. E-17 S-188 to S-190 generate what these rules read.

Rules
- R-200-01  Given a land map, When its layers are set, Then the five layers are five height bands fitted to that map between its lowest and highest ground, so that every layer has ground on it and no elevation mapping is fixed globally; a piece of ground belongs to the layer of the band its height falls in (E-17 S-188), and the numbers written for one standard layer step scale with the height of the step [Q-166-04: how each number scales, which the skill lab measures].
- R-200-02  Given a position whose ground falls in band k, When the map is queried there, Then the ground fills layers 1 to k - 1, which are blocked there (R-001-01); layer k and the layers above it are open unless something else blocks them (S-001), so a flying unit may be on the ground's layer or above it and never below; and the ground flag is set on layer k and on no other layer there, except along a slope, where a unit counts as on each layer it passes in turn (R-001-06, R-001-07; E-17 S-190).
- R-200-03  Given ground too steep to cross, When a walking unit is ordered across it, Then the unit cannot cross it, and the ground is not a slope: a slope is ground that joins two layers and can be climbed (R-001-06), and steep ground joins none (E-17 S-189) (about 30 to 35 degrees, Westley, 2026-10-03) [Q-189-02: the exact figure inside that range].
- R-200-04  Given two layers at a place that are joined only by ground too steep to cross, When a walking unit is ordered from one to the other, Then it takes another way if one exists and otherwise paths as close as it can and stops (R-001-05); a flying or swimming unit is not stopped by it (R-001-07).

Inputs: the band heights, the ground flag per layer, the slopes and the sections too steep to cross, all from the map generator (E-17 S-188 to S-190).
Outputs: the accessibility mask and the ground flag per layer per position; the slopes, with their edges and lengths.
Open flags: Q-166-04 (numbers that assume a standard layer step scale with the step's height, as the skill lab measures), Q-189-02 (how steep is too steep, held by E-17), Q-166-02 (space maps).

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Layer accessibility mask | Map generator | Binary per layer per sampled position | Not player-issued |
| Layer count | Engine | 5, fixed | Not player-issued |
| Height bands | Map generator | Five bands fitted to each land map between its lowest and highest ground (S-200; E-17 S-188) | Not player-issued |
| Hard transfer | Player | Target layer in map range, selection 1 to N | Out of range: rejected, no state change. Era mask forbids: rejected |
| Preference set | Player | Layer in map range or clear | Same as hard transfer |
| Modifier key | Player | Held or released | None |
| Ping | Player | Selection of units that can ping, a layer, a place within reach (S-162) | Not capable, out of reach or on cooldown: rejected |
| Emit or silent | Player | Selection (S-163) | None |
| Pulse (not built) | Player | Pulse-capable selected unit, cooldown ready | On cooldown or not capable: rejected |
| Unit type transition time | Config | 1.0 to 5.0 s | Not player-issued |
| Slopes | Map generator | Position, length, and the layers joined, adjacent or not | Not player-issued |
| Land per layer | Map generator | A ground flag per layer per position: where a walking unit can stand, on land maps (S-200) | Not player-issued |
| Ground too steep to cross | Map generator | Sections of ground, land maps (S-200; E-17 S-189) | Not player-issued |
| Unit movement kind | Era pack, per unit type | Walking, or flying or swimming; every Settled Reach type flies and the land era has walking types | Not player-issued |
| Sensor radius, vantage membership, interference intensity | Sim | Per unit, per position | Not player-issued |
| Era restriction mask | Era pack | Per unit type, subset of layers, or absent | Malformed pack fails to load |

## Outputs

| Output | Observable where |
|---|---|
| Unit layer | Tick delta unit entry; ring color on screen; save file |
| Preferred layer | Tick delta unit entry; preference indicator; save file |
| Transitioning flag and remaining time | Tick delta unit entry; drawn height mid-tween |
| Visible set per unit; player-visible list | Tick delta; fog reveal on screen |
| Ping revealed set; the alert and its sector for the pinged side | Tick delta; screen |
| Emit or silent state per force | Tick delta; mark on screen |
| Pulse active, cooldown remaining (not built) | Tick delta; HUD cooldown ring; pulse effect on screen |
| Command rejections | Command acknowledgement in the tick delta with a reason code |
| Focused layer | HUD strip highlight |

## Invariants

- A unit is on exactly one layer at every tick, including mid-transition: on a slope, the layer on its side of the midline; in a timed transfer, its old layer until the cross-over point halfway through, then its new layer.
- A walking unit never occupies a layer and position without land, never changes layer except along a slope, and never crosses ground too steep to cross.
- On a land map the ground fills every layer below its surface, and no unit occupies a filled layer.
- No unit ever occupies a position and layer the mask marks blocked.
- Visible set is symmetric in rule, not in outcome: A sees B does not imply B sees A.
- Same seed and command stream produce identical layer, visibility, and transition traces.
- Cover never changes damage or movement.

## Scale requirements

Numbers to be confirmed by Westley in Stage 3. Proposed: 1,000 units computing cross-layer visibility against 1,000 units in under 2 ms per tick; 10,000 units in under 20 ms per tick; accessibility queries at 10,000 per tick in under 1 ms.

## Look and behavior references

`references/E-01/notes.md`. Stub; needs 2 to 5 screenshots or clips with one sentence each on what is wanted and what is not, for: how a layer stack reads on screen, how a unit changing height looks, how the layer ring and strip look, how a ping looks.

## Ways this could be wrong

- Layer changes are instant in code today; a build that keeps the snap and ignores transition time passes a naive "layer changed" test.
- Visibility set changes but the fog render does not, or the render changes and the set does not.
- Cross-layer factors applied to the wrong axis (target's layer vs observer's).
- Vantage doubling applied to same-layer radius instead of cross-layer only.
- Ping reveal persists after expiry, or cooldown resets on save and load.
- Preference and hard transfer both set but the wrong one wins.
- A unit takes a longer route to stay on its layer when a shorter one crosses another layer, or changes layer when that is not on the shortest route.
- A unit fires at a target it cannot see.
- Ring colors read from the render's last-known layer instead of the delta.
- Cover blocks movement, or reduces damage, because a physics layer was reused.
- A transitioning unit keeps firing at a target its side no longer sees, or is barred from firing at one its side still sees.
- A walking unit rises in place at a cliff edge like a flying one.
- A unit on a slope runs its type's transition timer instead of reading its position, so the cross-over is a moment and not the midline; or a unit that turns back on a slope finishes the change anyway.
- Elevation taken from a fixed global mapping, so a map's five layers do not span its own relief and layers 4 and 5 draw at layer 3's height.
- A flying unit enters a layer the ground fills, or a walking unit crosses ground too steep to cross.

## Open ambiguity flags

Q-008-02, Q-008-03, Q-008-05, Q-008-06, Q-008-07, Q-166-02, Q-166-04, Q-189-02. Details in `docs/northstar/ambiguity_register.md`.

## Depends on

- E-11 Units (unit types, sensor radius, transition time per type; walking unit types, S-201).
- E-12 Fog and sensors (sensor radius, interference zones, elevation sensor bonus).
- E-13 Movement and pathing (routing around blocked layers).
- E-17 Map generation (height bands, steep ground and the ground's layers, S-188 to S-190; accessibility mask, vantage nodes, cover placement).
- E-16 Camera and HUD (layer strip, rings, elevation on screen).

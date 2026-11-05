# Map view zoom band: perception brief

## 1. Feature and status

A third zoom band above the tactical view, raised during the landscape design phase on 2026-09-21. Flag Q-103-02, open (`docs/northstar/ambiguity_register.md:161`): "Which orders, and does it replace the minimap?" No story exists yet in E-16; the landscape README lists "Map view and group commands are new client behavior not in E-16; needs a story and reference" (`docs/northstar/research/landscape_design/README.md:42`). The concept (three zoom bands, the map-view overlay) was approved in mockup review 2 (`landscape_design/README.md:65`).

## 2. Player-facing goal as documented

"The battlefield is 20 to 30 screens at the classic RTS zoom, with three zoom bands: micro (individual units), tactical (today's RTS view), and map view (World of Warships style: unit groups as icons, basic movement commands to groups from that level)." (`landscape_design/README.md:34`)

Reference row 08 in `docs/bible/references/E-17/notes.md:24`: "The map view: grid, terrain as simple shapes, unit groups as icons, drawn movement arrows, objective circles; basic group movement orders are given from here." Not wanted: "Naval UI, the grid letters."

## 3. Westley's own words

Landscape question 3, 2026-09-21 (`landscape_design/README.md:13`): "3: B but more like 20-30x, but zoomability is a big factor, you can zoom way down to the micro level to micro units, but the whole battle happens on a much larger scale, and players should be able to give basic movement commands from that level to groups of units. Think "map" view, like from World of Warships."

Mockup review 1 (`landscape_design/README.md:49`): "Camera did pan correctly but the "map" lines just pop up on screen withuot moving as you zoom out, and given it's representing things on the map, not moving with the map looks very broken."

Mockup review 2 (`landscape_design/README.md:63`): "Protoptye has my go ahead (though, the elevation changes leave much to be desired, I imagined that the maps would be significantly larger, mountains would be huge and zoomability would have a "floor" that you can follow elevation changes with..."

## 4. Fixed constraints any option must honor

- Q-103-02 is open; its candidates are (a) move and attack-move only, minimap stays; (b) full command set, minimap replaced; (c) move only at launch, the rest later (`ambiguity_register.md:161`). Options may go outside these.
- The overlay moves with the terrain; it is drawn in world space on the ground, not pinned to the screen (`landscape_design/README.md:54`).
- Camera floor: bands are defined by height above ground (`landscape_design/README.md:71`).
- The camera is canvas-bounded at every zoom (E-16 R-103-02).
- The minimap exists today as its own surface: friendly units bright, visible enemies dim, terrain contours, objectives, structures by owner (R-104-05, `docs/bible/epics/E-16-client-camera-hud-and-world-view.md:49`). The right sidebar is empty except the layer strip (R-104-09, `:53`).
- Principle 6: "Any feature that lets the player issue an order without thinking about where their units are is excluded, at every difficulty. There is no all-army command." (`docs/bible/game_bible.md:78`)
- Hub: "Not Total War: there is no campaign map and battle map split. One continuous world at two zoom levels." (`game_bible.md:49`)
- Control groups have exclusive membership; a drag box selects every layer (R-105-01, R-105-02).
- Fog: the map view shows only what the player's units can see; there is no enemy composition readout anywhere (E-16 invariants).
- Always 5 layers; the map view must not erase the layer stack from the player's reading.
- Canvas 24,000 wu default after pass 3; a mockup band table exists (`docs/northstar/plans/briefs/2026-09-21-p2-landscape-mockup.md:114`): micro 300 to 1,200, tactical 1,200 to 6,000, map 6,000 to 40,000, pitch easing to top-down, pieces fading, chevron group icons, objective circles, click group then click point draws an order arrow.

## 5. Prior art already named

- World of Warships map view, image `docs/bible/references/E-17/E-17-8-wows-map-view.png`.
- StarCraft 2 minimap viewport box (`docs/legacy/stage_specs/stage_11d_mid_mission_hud_spec.md:15`).
- Age of Empires Online for the tactical band register.
- Anti-reference: Total War's campaign and battle map split.

## 6. Contradictions, as questions for Westley

1. "Basic movement commands to groups" from map altitude sits on Principle 6. Where is the line: orders from the map view are fine because the player still chooses a place, or only some orders (move, attack-move) are safe, or the map view is read-only?
2. Does the map view replace the minimap, sit beside it, or become what the minimap turns into when you zoom out?
3. The hub says "one continuous world at two zoom levels" (strategic galaxy, tactical mission). With micro, tactical, and map bands inside the mission, is the map view a third tactical band, or the top of a single continuous zoom?
4. Are layers visible from the map view (five stacked icons, one icon with a layer badge, or the stack collapsed)?

## 7. Proposed option width

Three options, one wild. Each option names which orders exist at map altitude, how a group is picked there, what the minimap becomes, and how the five layers read from above.

## 8. Westley confirms

Batch 1, 2026-09-22, verbatim: "map view replaces minimap just like World of Warships. Galaxy view is different from when the chronicle is being shown before the mission starts, the player doens't need to see the galaxy view when they're actively in a mission, don't conflate the two different views. Map view: in game mission, Galaxy view: whole simulation view exterior to missions. Only move and attack move. For layers, we'll collapse them but the unit "group" will indicate to the user with some UI that the group is Upper layers (4-5), Lower layers (1-2), or expansive (1-5)."

Folded into the brief:

- Orders (question 1): move and attack-move only from the map view.
- Minimap (question 2): the map view replaces the minimap, as in World of Warships.
- Zoom levels (question 3): the hub's "two zoom levels" are the galaxy view (outside missions, whole simulation) and the mission. The map view is a band inside the mission and never shows the galaxy. Options do not conflate the two.
- Layers (question 4): layers collapse in the map view; each unit group carries a UI mark for Upper (layers 4 and 5), Lower (layers 1 and 2), or Expansive (layers 1 to 5). A group entirely on layer 3 was not named; options say how a mid-layer group reads.
- Q-103-02's candidates are superseded by this combination: move and attack-move only, and the minimap replaced.

## 9. Sub-agent brief

Follow the common template in `../README.md` ("Sub-agent template"). Sections 4 and 8 of this file are the constraints; where they disagree, section 8 wins.

- Options: 3, of which 1 wild.
- Move and attack-move are the only orders from map altitude. The map view replaces the minimap. It lives inside the mission and never shows the galaxy.
- How the player picks a group from above and gives the order; what the order looks like on the map and on the ground when they zoom back in.
- Groups carry a mark for Upper (layers 4 and 5), Lower (1 and 2), or Expansive (1 to 5); propose how a group entirely on layer 3 reads.
- What the transition between the tactical band and the map band looks and feels like, and how fog reads from above.

## 10. Decision (2026-09-23)

Westley, verbatim: "For the zoom band, I really like the sand table idea, but I'd like to see a prototype before I commit to it. This is the sort of thing that's really hard to pull off, but I'd really like to see something like the sand table from Dune, the execution would have to be really good on this, we'd need to make a prototype that's low resolution (large blocks to represent height), and design it such that the resolution (size of the grains of sand, and hence detail) could be turned up and down. Obviously once it gets really fine grained, the detail will be immense but so will the graphics load. It'd also be nice if the users had a 45 degree angle option of the same map, with layers seperated enough for specific sets of units to be visible. This is worth significant protytping and tuning, this is a complex mechanism. I'd like to brainstorm additional options for indicating which layer specific units and unit groups are one, because the pin option is a good option but I don't think it has to be the only one. Mark further research needed."

Recorded as: Sand Table is the candidate, prototype before commitment (block-resolution table with a grain-size dial, plus a 45° view with layers separated); more layer-mark ideas beyond pins wanted (Q-103-05, Q-103-06; E-16 S-161).

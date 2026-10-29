# E-18 — Visual Style, Combat Visuals, and Animation

## Definition-completeness gate (run 2026-09-10)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Yes, 12 stories, 49 rules; numbers from the bible's combat visuals and animation sections and the Stage 1 A-368, A-369, A-372 rewrites; the world, settlement, economy, layer-action and scale stories (S-236 to S-240) leave numbers and looks to flags. |
| Every input listed with range and rejection behavior | Yes, see Inputs. |
| Every output listed with where it is observable | Yes; every output is a screen, T2-checkable. |
| Implied-but-unstated behavior turned into flags | 4 open flags: Q-132-02 (S-132), and Q-237-01, Q-238-01, Q-239-01 on S-236 to S-240; Q-133-01 and Q-236-02 closed 2026-10-21 (register). |
| Every visible-surface story has a reference | **No.** This entire epic is a visible surface. Art of Rally (look), the opening battle of Revenge of the Sith (combat weight), Halo CE (world-building), and Claude Code's spinner (glyph animation) are the bible's named references; none is attached as a screenshot yet. |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed.** Blocked on open flags and references. S-236 to S-240 are design decided and not scheduled for building. This epic is the T2 ground truth for everything else; it cannot be Ready before Westley's reference set exists.

## Purpose

Low-poly, Art of Rally: flat shading, clean silhouettes, the shape is the information. Unit silhouettes that persist across every era so a Raider reads as a Raider whether it is a dart of a ship or a longboat; how that rule reaches across a 20 to 40 type roster is open (Q-132-02). Three tiers that read at tactical zoom in three words each: boxy, seamed, matte; smooth, integrated, polished; flowing, luminous, abstract. Combat that conveys mass: nothing snaps or pops, hits bloom slowly, dead ships drift. Four attack visual categories and three ability overlays that every era skins from a manifest without new rendering code. Menus and transitions animated from simple elements composed with precise timing. A world drawn at detail that changes with distance, settlements that rise under construction, workers, shipments and weather, and a screen that holds up as the count of units, workers and buildings grows toward thousands.

The era-agnostic rule holds here as everywhere: the engine emits abstract events and state; the era manifest maps them to look.

## Obviously working in 60 seconds

Put the six Settled Reach baseline units on screen at Tier 2: six silhouettes distinguishable at tactical zoom, Strike smallest and Siege largest, Bastion wider than long, Bombard longest. Fire a Raider at a Vanguard: a projectile with a trail travels, an impact burst drifts out over half a second, the Vanguard blooms warm for a third of a second, no shake. Kill it: a death flare, fire and sparks, a slow drift along its last heading, darkening over 3 to 5 seconds. Pop Barrage: a warm ring telegraph, then a heavy volley. Swap to a Tier 1 manifest: the same units, boxy and painted.

## Stories

### S-132 — Silhouette is the information
As a commander, I want every unit type to have a shape I can read at a glance in any era, so that I never squint to know what I am fighting.

Rules
- R-132-01  Given the six Settled Reach baseline types, When drawn in any era, Then Raider is narrow, elongated, swept back and the smallest; Interceptor wider and flatter than Raider; Vanguard a front-heavy wedge or slab; Warden vertical or radial with a central projection; Bombard the longest, dominated by one linear axis; Bastion the widest and most compact, wider than long.
- R-132-02  Given a T2 screenshot at tactical zoom with the six baseline types, When inspected, Then each type is identifiable from silhouette alone.
- R-132-05  Given an era roster of 20 to 40 types, When drawn at tactical zoom, Then each type is identifiable [Q-132-02: one persistent silhouette per type, or silhouette families per category; parked for the beta, Westley, 2026-10-07].
- R-132-03  Given a Strike unit, When drawn, Then it is 3 to 5 small models moving as one (E-11 R-088-01).
- R-132-04  Given any model, When counted, Then it is 150 to 300 polygons for Strike squad members, 300 to 500 for Line, 400 to 600 for Siege, 200 to 800 for structures, 100 to 300 for environment.
- R-132-06  Given a worker or a building piece of a self-built settlement, When counted, Then it is within [Q-236-02: the polygon budget for workers and for the many pieces of a settlement; Westley's numbers].

Inputs: era manifest models.
Outputs: screen.
Open flags: Q-132-02. Q-236-02 closed 2026-10-21 (register: a named draft). The readability check is manual review plus the playtest silhouette-naming question (Track L hypothesis H12); no automated classifier at launch.

### S-133 — Three tiers you can read
As a commander, I want a faction's technology tier to show in how its ships look, and to show loss when it falls, so that history is visible on the battlefield.

Rules
- R-133-01  Given Tier 1, When drawn, Then boxy, seamed, matte: angular silhouettes, visible paneling, bolted-on components, muted metallics, faction color as painted livery.
- R-133-02  Given Tier 2, When drawn, Then smooth, integrated, polished: deliberate curves, flush weapons, bilateral symmetry, cleaner metallics, faction color as plating, subtle seam glow.
- R-133-03  Given Tier 3, When drawn, Then flowing, luminous, abstract: organic-geometric forms, minimal surface detail, emissive materials, faction color as a property of the material.
- R-133-04  Given a faction that fell from Tier 3 to Tier 1, When its forces are drawn next to a Tier 3 neighbor, Then the contrast is immediate at tactical zoom.
- R-133-06  Given a unit in a mission, When it is drawn, Then the tier it is drawn at is given by the simulation per unit, from the roster (ruling A30; Westley, 2026-10-07).
- R-133-05  Given an era pack, When authored, Then it defines every type in its roster at all three tiers (one model per type per tier), 3 to 6 tiered point-of-interest structures, 5 to 10 universal environment objects, and the building pieces that settlements are built from, with their stages of construction [Q-133-01: how many building pieces; the 3 to 6 structures are points of interest, and the pieces of S-237 are not counted among them].

Inputs: tier; era manifest.
Outputs: screen.
Open flags: none. Q-133-01 closed 2026-10-21 (register: a content budget, a named draft).

### S-134 — Attacks read as mass
As a commander, I want shots to travel, hits to bloom, and nothing to twitch, so that combat feels heavy and slow enough to read.

Rules
- R-134-01  Given a unit attack, When rendered, Then it is one of four categories from the manifest: projectile (one object travels), volley (N objects staggered by a per-type offset), beam (an instant line for a brief duration), area pulse (an expanding ring or sphere, no travel).
- R-134-02  Given a projectile, When rendered, Then it has a mesh head and a particle trail, and an impact burst at the target on arrival; visual travel time never affects damage timing.
- R-134-03  Given a hit, When rendered, Then an impact burst of small debris drifts out over 0.5 to 1.0 s with gentle deceleration, scaled by damage, colored by the attacker's trail; and the target blooms with a slow additive emission rise of 0.3 to 0.5 s and fade of 0.3 s. No position jitter, no white-frame flash.
- R-134-04  Given 200 v 200, When the renderer is under budget pressure, Then projectiles degrade by LOD: full mesh and trail near, billboard and trail far, billboard only very far, culled beyond a count threshold; damage is unaffected.
- R-134-05  Given the Settled Reach manifest, When read, Then the mesh head is a small glowing sphere, the trail a warm energy ribbon, the impact a small radial flash; the six units use these categories: Raider a rapid kinetic projectile, Interceptor a missile volley, Vanguard a heavy plasma projectile, Warden a continuous defense beam, Bombard an arcing artillery volley, Bastion a dual kinetic cannon.

Inputs: attack events; manifest fields (projectile mesh, trail material, impact scene, visual travel speed, scale, volley count and stagger).
Outputs: screen.
Open flags: none.

### S-135 — Abilities have a signature
As a commander, I want every ability to read at a glance as an ability in progress, mine or theirs, so that I can react to a telegraph and trust my own.

Rules
- R-135-01  Given an ability event (E-11 R-086-09), When rendered, Then the unit's normal attack category plays with enhanced parameters plus overlays: Surge and Intercept add a unit glow; Brace glow only; Rally area pulse, ring, and brief distortion; Barrage heavy volley, ring, and distortion; Fortify a persistent ring for its duration.
- R-135-02  Given a ring telegraph, When drawn, Then hostile abilities use warm tones and friendly ones cool tones, and the ring persists for the ability's duration then fades.
- R-135-03  Given a screen-space distortion, When played, Then it lasts 0.3 to 0.5 s and is tunable to atmospheric, not nauseating.
- R-135-04  Given a Barrage, When its telegraph ring appears, Then it appears at the target position exactly 1.5 s before impact (E-11 R-086-05), visible to both sides.

Inputs: ability events.
Outputs: screen.
Open flags: none.

### S-136 — Death is unmistakable
As a commander, I want a dying ship to flare, burn, drift, and darken, so that I never wonder whether I lost it.

Rules
- R-136-01  Given a unit reaches 0 HP, When the renderer plays destruction, Then: a death bloom brighter than any hit (0.5 s); persistent damage emitters activate (fire, sparks, venting, era-specific); the wreck drifts along its last heading, decelerating; its material darkens toward a desaturated faction color over 3 to 5 s.
- R-136-02  Given a wreck, When units path, Then it has no collision and no gameplay effect; it is renderer-only.
- R-136-03  Given many wrecks, When the frame budget is pressed, Then wrecks degrade by LOD and are culled by distance and age: wrecks fade out after 30 s, with a cap of 150 wrecks.

Inputs: death events.
Outputs: screen.
Open flags: none.

### S-137 — Menus and transitions that breathe
As a player, I want the menus, unlock screens, and era celebrations to feel alive from simple elements composed with precise timing, so that the interface has the same craft as the game.

Rules
- R-137-01  Given any menu or celebration animation, When built, Then it is two layers: a dimmed background atmosphere (a full-screen shader at 20 to 30 percent opacity, or the 3D particle galaxy at 70 percent) and a foreground of monospace Unicode glyphs animated with tweens in the era's accent color.
- R-137-02  Given an atmosphere layer, When authored, Then it uses only the era accent color (or tint), moves slowly and continuously, never snaps or flashes, and exposes color, speed, density, and opacity as parameters.
- R-137-03  Given a glyph set, When authored, Then it has 6 to 10 glyphs of progressively increasing complexity, and no glyph is ever static on screen.
- R-137-04  Given a foreground animation, When it plays, Then it has three phases (enter, hold, exit), staggered element timing, opacity depth layers, and a total duration budget stated per animation.
- R-137-05  Given a printed chronicle entry, When idle, Then its end cursor blinks (the heartbeat vocabulary).

Inputs: era accent color; glyph sets; timing.
Outputs: screen.
Open flags: none beyond references.

### S-138 — The look
As a player, I want the whole game to look like one thing, low-poly and stylized, so that a screenshot is recognizable from across a room.

Rules
- R-138-01  Given any scene, When rendered, Then models are flat or minimally shaded low-poly with clean geometric forms; no photoreal textures; no PBR detail passes.
- R-138-02  Given a T2 screenshot from any screen, When compared against the reference set, Then it passes a manual review against the reference set; there is no automated register check at launch.
- R-138-03  Given the Settled Reach, When rendered, Then the tactical space reads as a lived-in frontier: asteroids, derelicts, cargo, nebula volumes, beacons (the landforms of S-236 do not appear in space, R-236-03; the space landscape is Q-166-02).

Inputs: era manifests; reference set.
Outputs: screen.
Open flags: none. Reference required: `references/E-18/notes.md`, missing.

### S-236 — One world, drawn at the distance you look from
As a player, I want the ground and everything on it drawn in deep detail up close and as the shape of the land far away, with smooth change between, so that the scale of the world is something I feel.

Design decided 2026-10-02, not scheduled for building (E-17 S-166). These rules apply to land maps; the space-era landscape is not designed (Q-166-02) and has no rule here.

Rules
- R-236-01  Given the camera at any zoom between a single unit and the battlefield's map view, When the world is drawn, Then it is one world drawn at continuous detail: deep detail fully zoomed in, the shape of the land zoomed out, with smooth transitions between very different zoom levels and no pop from one level of detail to the next (E-17 R-166-05, E-16 S-234).
- R-236-02  Given ground fitted to five height bands (E-17 R-166-04, R-166-06), When it is drawn, Then a step between bands is drawn as the real difference in height it is, benched and natural ground are both drawn, and cliffs, waterfalls and mountainsides read as the landforms they are; the land ground is one colour; a band is told by its height step and by sight, never by a colour (Westley 2026-10-22, DEC-S004-vision-not-colour).
- R-236-03  Given the Settled Reach, When a landform such as a cliff or a waterfall would appear, Then it does not appear: cliffs and waterfalls do not exist in space, and the space and ground eras are kept separate (E-17 R-188-05; Westley, 2026-10-06). What the space landscape draws is Q-166-02.

Inputs: the map's fields and height bands; era manifest.
Outputs: screen.
Open flags: none.

### S-237 — Settlements that rise
As a player, I want a base to start as ground under construction and rise stage by stage, spreading and thickening as it grows, so that the base I fight over is a spectacle to watch being built.

Design decided 2026-10-02, not scheduled for building (E-17 S-166, E-22). The base is a spectacle in every mode, whether rules run the economy or a second player does.

Rules
- R-237-01  Given a self-built building, When it first appears, Then it is drawn under construction and rises to complete over time, and nothing about it snaps into place (E-17 R-166-01).
- R-237-02  Given a lot whose population density passes a threshold, When it is drawn, Then it shows its next stage, from under construction upward (five stages: empty, staked, scaffold, small, large; E-17 Q-193-02, Westley, 2026-10-06).
- R-237-03  Given a wave of growth tied to an event (E-17 R-166-03), When it arrives, Then new buildings appear a little at a time across the settlement, and an expansion that is made appears as a new settlement growing in the same way.
- R-237-04  Given the player places a building, When it is drawn, Then the self-built pieces on its footprint are cleared and the settlement fills in around it.
- R-237-05  Given a settlement on a cliff, beside a waterfall or on a steep mountainside (E-17 R-166-03), When it is drawn, Then its buildings sit in those places and the settlement does not stop at difficult ground.

Inputs: growth and density events; the player's placed buildings; era pack building pieces (E-20 S-243).
Outputs: screen.
Open flags: none.

### S-238 — Work on the map: workers, shipments, weather and disguise
As a player, I want to see workers walk to a source and gather, weather cross the map, and disguised buildings look like what they pretend to be, so that the economy is something I watch happen.

Design decided 2026-10-02, not scheduled for building (E-22).

Rules
- R-238-01  Given literal workers (E-22 S-167), When they work, Then each is drawn walking to a source, gathering there, and walking to a drop-off; a worker is a unit and counts in the unit budgets (S-240).
- R-238-02  Given a shipment on its way to a base (E-22 S-176), When the receiving side's screen is drawn, Then the shipment is not shown, because that side has no vision of it at all, and nothing on screen tells the side that a shipment was killed.
- R-238-03  Given an environmental trouble travelling across the map (E-15), When it is drawn, Then it is seen moving by both sides, and what it passes over is drawn shut down.
- R-238-04  Given a disguised or hidden building (E-22 S-172), When it is drawn, Then [Q-238-01: how it looks to its owner and to the enemy; how disguise works is Q-159-09].

Inputs: worker, shipment, weather and disguise state from the tick delta.
Outputs: screen.
Open flags: Q-238-01.

### S-239 — Pings and going dark, seen
As a commander, I want a ping, an emitting force and a ping alert to read at a glance, so that the three layer actions are visible things.

Rules
- R-239-01  Given a ping (E-01 R-162-01), When it lands, Then a burst is drawn at the place for as long as the layer is revealed there, and the units it revealed are drawn hidden again when it ends (E-01 R-162-05); the burst slows into place and never snaps; every unit caught in the ping shows a small circle for about 5 seconds that shows the unit itself, its features and where it is moving, and is not vision of its surroundings (Westley, 2026-10-07).
- R-239-02  Given a force set to emit (E-01 S-163), When it is drawn, Then it reads as emitting from a silent force at tactical zoom, using the mark of E-16 S-232.
- R-239-03  Given a side is pinged (E-01 R-162-03), When the ping lands, Then nothing is drawn for the pinged side: the alert is switched off for now (Westley, 2026-10-05); if it returns, a sector of about 60 degrees toward the caster and nothing more precise (E-16 S-232).

Inputs: ping, emit and alert events (tick delta); manifest fields for the looks.
Outputs: screen.
Open flags: none.

### S-240 — Thousands on one screen
As a player, I want a screen of thousands of units, workers and buildings to stay smooth, so that a busy world is a feature and not a cost.

Design decided in part 2026-10-01: the long-term goal is thousands of units and workers on one map (hub "Reference Hardware"). The budgets in Scale requirements are Westley's numbers and are unchanged; the budgets for thousands are open.

Rules
- R-240-01  Given units, workers, buildings and settlement pieces under budget pressure, When they are drawn, Then each degrades by distance and by count: full detail near, simpler far, culled beyond a count threshold; what happens in the sim is unaffected (as R-134-04 and R-136-03 for projectiles and wrecks).
- R-240-02  Given any new visual, When it is designed, Then it is built so that it does not stand in the way of the long-term goal of thousands.
- R-240-03  Given the client budgets, When the long-term goal is read against them, Then the client's budgets for thousands of units, workers and buildings are a direction, with no frame-rate number, until the simulation's budgets (10,000) are reached (Westley, 2026-10-06).

Inputs: frame budget; counts on screen.
Outputs: screen.
Open flags: none.

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Tick delta events (attack, ability, death, ping, emit and silent changes, workers, shipments, weather, growth) | Sim | | unknown event type ignored and logged |
| Map fields and height bands | Sim | | |
| Era manifest | Era pack | per-type categories, assets, timings, colors | missing entry uses the placeholder asset |
| Tier | E-06 | 1 to 3 | |
| Frame budget | Client | | |

## Outputs

| Output | Observable where |
|---|---|
| Everything | Screen; T2 screenshots and clips |

## Invariants

- Visuals never change gameplay: damage, timing, and collisions are the sim's.
- No hit, death, or ability effect snaps.
- Adding an era never adds rendering code.
- Level of detail never changes what happens in the sim.

## Scale requirements

Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is escalated): 60 fps at 200 v 200 with full effects at medium zoom; 30 fps floor at 1,000 units with LOD; both on the minimum-spec machine (`game_bible.md` "Reference Hardware": about 110 and 55 fps on the forge's RTX 3060). E-16 states 60 fps at 1,000 units where this epic states a 30 fps floor, and neither covers the long-term goal of thousands of units and workers, which stays a direction until the simulation's budgets (10,000) are reached (Westley, 2026-10-06).

## Look and behavior references

`references/E-18/notes.md`, missing. Named by the bible: Art of Rally (look), Revenge of the Sith opening battle (combat weight), Halo CE (world-building), Claude Code spinner (glyph animation), No Man's Sky (transitions).

## Ways this could be wrong

- Damage applied on projectile arrival instead of on the sim tick.
- Hit bloom implemented as a white flash.
- Wrecks collide.
- Tier decided by the renderer from stats instead of from the faction's tier.
- A silhouette that reads as a different category at tactical zoom.
- An atmosphere shader with a second color.

## Open ambiguity flags

Q-132-02, Q-238-01. Details in `docs/northstar/ambiguity_register.md`.

## Depends on

- E-06 (tiers), E-11 (events), E-16 (screens), E-20 (era packs and manifests), E-21 (asset pipeline).
- E-17 S-166 (the landscape and settlements that S-236 and S-237 draw), E-22 (workers, shipments, disguise), E-15 (weather), E-01 S-162 and S-163 (ping and emit events), E-19 S-159.

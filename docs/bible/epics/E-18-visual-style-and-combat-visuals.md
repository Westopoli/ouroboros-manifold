# E-18 — Visual Style, Combat Visuals, and Animation

## Definition-completeness gate (run 2026-09-10)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Yes, 7 stories, 34 rules; numbers from the bible's combat visuals and animation sections and the Stage 1 A-368, A-369, A-372 rewrites. |
| Every input listed with range and rejection behavior | Yes, see Inputs. |
| Every output listed with where it is observable | Yes; every output is a screen, T2-checkable. |
| Implied-but-unstated behavior turned into flags | 4 new flags, Q-132-01, Q-134-01, Q-136-01, Q-138-01. |
| Every visible-surface story has a reference | **No.** This entire epic is a visible surface. Art of Rally (look), the opening battle of Revenge of the Sith (combat weight), Halo CE (world-building), and Claude Code's spinner (glyph animation) are the bible's named references; none is attached as a screenshot yet. |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed.** Blocked on 4 open flags and references. This epic is the T2 ground truth for everything else; it cannot be Ready before Westley's reference set exists.

## Purpose

Low-poly, Art of Rally: flat shading, clean silhouettes, the shape is the information. Six unit silhouettes that persist across every era so a Raider reads as a Raider whether it is a dart of a ship or a longboat. Three tiers that read at tactical zoom in three words each: boxy, seamed, matte; smooth, integrated, polished; flowing, luminous, abstract. Combat that conveys mass: nothing snaps or pops, hits bloom slowly, dead ships drift. Four attack visual categories and three ability overlays that every era skins from a manifest without new rendering code. Menus and transitions animated from simple elements composed with precise timing.

The era-agnostic rule holds here as everywhere: the engine emits abstract events and state; the era manifest maps them to look.

## Obviously working in 60 seconds

Put one of each unit on screen at Tier 2: six silhouettes distinguishable at tactical zoom, Strike smallest and Siege largest, Bastion wider than long, Bombard longest. Fire a Raider at a Vanguard: a projectile with a trail travels, an impact burst drifts out over half a second, the Vanguard blooms warm for a third of a second, no shake. Kill it: a death flare, fire and sparks, a slow drift along its last heading, darkening over 3 to 5 seconds. Pop Barrage: a warm ring telegraph, then a heavy volley. Swap to a Tier 1 manifest: the same units, boxy and painted.

## Stories

### S-132 — Silhouette is the information
As a commander, I want every unit type to have a shape I can read at a glance in any era, so that I never squint to know what I am fighting.

Rules
- R-132-01  Given the six types, When drawn in any era, Then Raider is narrow, elongated, swept back and the smallest; Interceptor wider and flatter than Raider; Vanguard a front-heavy wedge or slab; Warden vertical or radial with a central projection; Bombard the longest, dominated by one linear axis; Bastion the widest and most compact, wider than long.
- R-132-02  Given a T2 screenshot at tactical zoom with all six types, When inspected, Then each type is identifiable from silhouette alone.
- R-132-03  Given a Strike unit, When drawn, Then it is 3 to 5 small models moving as one (E-11 R-088-01).
- R-132-04  Given any model, When counted, Then it is 150 to 300 polygons for Strike squad members, 300 to 500 for Line, 400 to 600 for Siege, 200 to 800 for structures, 100 to 300 for environment.

Inputs: era manifest models.
Outputs: screen.
Open flags: none. The readability check is manual review plus the playtest silhouette-naming question (Track L hypothesis H12); no automated classifier at launch.

### S-133 — Three tiers you can read
As a commander, I want a faction's technology tier to show in how its ships look, and to show loss when it falls, so that history is visible on the battlefield.

Rules
- R-133-01  Given Tier 1, When drawn, Then boxy, seamed, matte: angular silhouettes, visible paneling, bolted-on components, muted metallics, faction color as painted livery.
- R-133-02  Given Tier 2, When drawn, Then smooth, integrated, polished: deliberate curves, flush weapons, bilateral symmetry, cleaner metallics, faction color as plating, subtle seam glow.
- R-133-03  Given Tier 3, When drawn, Then flowing, luminous, abstract: organic-geometric forms, minimal surface detail, emissive materials, faction color as a property of the material.
- R-133-04  Given a faction that fell from Tier 3 to Tier 1, When its forces are drawn next to a Tier 3 neighbor, Then the contrast is immediate at tactical zoom.
- R-133-05  Given an era pack, When authored, Then it defines all six types at all three tiers (18 unit models), 3 to 6 tiered point-of-interest structures, and 5 to 10 universal environment objects.

Inputs: tier; era manifest.
Outputs: screen.
Open flags: none beyond references.

### S-134 — Attacks read as mass
As a commander, I want shots to travel, hits to bloom, and nothing to twitch, so that combat feels heavy and slow enough to read.

Rules
- R-134-01  Given a unit attack, When rendered, Then it is one of four categories from the manifest: projectile (one object travels), volley (N objects staggered by a per-type offset), beam (an instant line for a brief duration), area pulse (an expanding ring or sphere, no travel).
- R-134-02  Given a projectile, When rendered, Then it has a mesh head and a particle trail, and an impact burst at the target on arrival; visual travel time never affects damage timing.
- R-134-03  Given a hit, When rendered, Then an impact burst of small debris drifts out over 0.5 to 1.0 s with gentle deceleration, scaled by damage, colored by the attacker's trail; and the target blooms with a slow additive emission rise of 0.3 to 0.5 s and fade of 0.3 s. No position jitter, no white-frame flash.
- R-134-04  Given 200 v 200, When the renderer is under budget pressure, Then projectiles degrade by LOD: full mesh and trail near, billboard and trail far, billboard only very far, culled beyond a count threshold; damage is unaffected.
- R-134-05  Given the Settled Reach manifest, When read, Then the mesh head is a small glowing sphere, the trail a warm energy ribbon, the impact a small radial flash [Q-134-01: per-type category mapping for the six units is not in the bible].

Inputs: attack events; manifest fields (projectile mesh, trail material, impact scene, visual travel speed, scale, volley count and stagger).
Outputs: screen.
Open flags: Q-134-01.

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
- R-136-03  Given many wrecks, When the frame budget is pressed, Then wrecks degrade by LOD and are culled by distance and age [Q-136-01: age and count caps].

Inputs: death events.
Outputs: screen.
Open flags: Q-136-01.

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
- R-138-03  Given the Settled Reach, When rendered, Then the tactical space reads as a lived-in frontier: asteroids, derelicts, cargo, nebula volumes, beacons.

Inputs: era manifests; reference set.
Outputs: screen.
Open flags: none. Reference required: `references/E-18/notes.md`, missing.

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Tick delta events (attack, ability, death) | Sim | | unknown event type ignored and logged |
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

## Scale requirements

Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is escalated): 60 fps at 200 v 200 with full effects at medium zoom; 30 fps floor at 1,000 units with LOD.

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

Q-134-01, Q-136-01. Details in `docs/northstar/ambiguity_register.md`.

## Depends on

- E-06 (tiers), E-11 (events), E-16 (screens), E-20 (era packs and manifests), E-21 (asset pipeline).

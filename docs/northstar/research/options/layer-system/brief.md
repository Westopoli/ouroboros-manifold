# Layer system look and feel: perception brief

## 1. Feature and status

E-01 "Layer system", the game's defining mechanic (`docs/bible/epics/E-01-layer-system.md`). The mechanics are largely decided (Q-E01-01 to Q-E01-07, Q-001 to Q-009 closed). What is open is how it reads on screen: Q-E01-08 (references missing, `docs/northstar/ambiguity_register.md:32`) and A-299 (the layer-preference indicator visual, deferred to research, `docs/legacy/agora_era/stage1_audit.md:471`). `docs/bible/references/E-01/notes.md` records the plan: "Westley does not yet know exactly what it should look like; he will decide by interacting with real options." A two-layer P6 mockup exists (`docs/northstar/plans/briefs/2026-09-22-p6-layers-mockup.md`). This brief covers the look and feel: how the stack, a height change, the ring and strip, the pulse, and the preference indicator read to the player. It does not reopen closed mechanics unless Westley says so in section 8.

## 2. Player-facing goal as documented

"The layer system is the game's strategic defining characteristic. The battlefield is not a flat plane. It is a stack of three to five vertical layers, and a unit is always on exactly one of them. Terrain blocks layers at specific places, so a force can go over an obstacle on a high layer or around it on a low one. Vision across layers is worse than vision on your own layer, so a force on a layer you cannot see is a threat you do not know about. Changing layers costs time and leaves the unit briefly vulnerable." (`E-01:18`)

"As a commander, I want to see at a glance which layer each unit is on and which layer I am focused on, so that I never have to guess who can see whom." (S-009, `E-01:148`) "As a commander, I want a unit on a higher layer to sit visibly higher than one on a lower layer, so that the layer stack reads as a stack and not as a color code." (S-010, `E-01:161`)

## 3. Westley's own words

Vision v2 Q6, 2026-09-10 (`docs/legacy/agora_era/vision_v2.md:65`): "A player with an inferior force but understanding of positional tactics (surround, high ground, game theory positioning) can overcome the opposition, the goal is to construct a situation with enough variables that creates a really high skill ceiling, and significantly favors players with an understanding of the layer system, specific units, and such. (we're really heavily basing based off of Starcraft 2 here, surrounds and high ground were really important in that game, we're trying to turn it up to 11 in our game)."

Q-E01-01, 2026-09-12 (`ambiguity_register.md:9`): "There should always be 5 layers, regardless of era. Only 3 may have been an idea from when we were just implementing a toy version, but we're not doing that anymore, so every era should be a 5 layer system."

A-299, Stage 1 (`stage1_audit.md:471`): "Westley's initial (non-final) idea: a mostly translucent grid around the unit, fading with distance, brightest on the unit's current layer and faded on adjacent layers, so layer membership reads visually at a glance." Same row: "good visualization tools exist for this kind of 3D-layer cueing and deserve a look."

Q-001-02 (`:20`): "The bottom layer is layer 1 (lowest in terms of height)." Q-001-03 (`:21`): "Units shoudl route around obstacles, just like classic starcraft 2 RTS." Q-002-01 (`:22`): "it should be 'reasonable' how quickly a unit traverses from one layer to another, between 1 and 2 seconds is a good starting point, to be tuned if needed." Q-004-02 (`:26`): "It should still be attackable by those units until the transition is halfway completed. New layer can attack it after it's halfway completed." Q-006-01 (`:28`): "Give the interceptor the pulse, mark it as a 'for now' ability, we'll modify units a lot when we have playtesters." Q-009-01, 2026-09-16 (`:31`): "(a), purely visual presentation (non-focused layers dim slightly; commands and box-select still function normally across all layers)." Q-008-01 (`:30`): "(a), prototype attacks are same-layer only. Cross-layer strikes deferred to dedicated layer tuning research."

E-17 references, 2026-09-13 (`docs/bible/references/E-17/notes.md:42`): "Dramatic elevation differences. Real earth-era height changes; the player should physically feel the height and get a real sense of scale. This ties to the E-01 layer system — vertical space must read."

Mockup review 2, 2026-09-21 (`docs/northstar/research/landscape_design/README.md:63`): "Though Halo Wars had small changes, I want this game to have big changes for vastly different heights."

## 4. Fixed constraints any option must honor

- Always 5 layers, layer 1 at the bottom; the generator never varies the count (Q-E01-01, Q-001-01, Q-001-02).
- A ring under every unit, one color per layer, changing on the tick the layer changes (R-009-01, `E-01:151`). A second, smaller preference indicator, distinct from the ring; exact visual open (R-009-02, `:152`).
- A layer strip on the HUD; click or Tab changes focus and the strip highlights (R-009-03, `:153`); vertical five-slot strip on the right edge (`docs/bible_history/bible_2_00_combat.md:199`); focus is purely visual, non-focused layers dim (Q-009-01).
- Height reads: a unit's drawn height is the layer's elevation; a transition tweens, never snaps; one layer step moves the unit by more than 5 percent of viewport height at a fixed camera (R-010-01 to 03, `E-01:164-166`).
- Transition: one tween of 1 to 2 seconds regardless of distance, per-type durations (Raider 1.0 s to Bastion 5.0 s); the old layer can hit until halfway, the new layer from halfway (Q-002-01, Q-004-01, Q-004-02, A-354).
- No automatic layer change ever; the player owns the layer (Q-001-03).
- Cross-layer vision: adjacent layer at half range, two away at a fifth, three or more none (Q-E01-03); the pulse is the Interceptor's ability, reveals all layers briefly, leaves a ghost marker for 10 s (Q-006-01, Q-006-02).
- Fog is binary hidden or revealed; no special silhouette for another layer (Q-E01-06).
- Combat is same-layer only for the prototype; layers change pathing and vision, not damage (Q-008-01, Q-E01-04).
- Alt plus 1 to 5 sets preference, Alt plus 0 clears (Q-003-01).
- Visually quiet: "the world, not the interface, stays the thing the player is actually looking at" (A-313, `stage1_audit.md:492`).
- Era-agnostic: the engine says which layers are blocked; the pack says whether that is an asteroid, a mountain, or a reef (`E-01:22`).
- The camera is never bound to a layer (E-16 R-103-04).

## 5. Prior art already named

By design, none external for the look: "Not external screenshots — a design phase." (`references/E-01/notes.md:3`). Mechanic bar: StarCraft 2 high ground and surrounds (vision Q6). Terrain scale: the Roblox biome and island generators (`references/E-17/notes.md:28-36`). Camera height floor: Halo Wars. HUD register for the strip's host bar: Immortal: Gates of Pyre. Readable-toy register: Age of Empires Online, Art of Rally.

## 6. Contradictions, as questions for Westley

1. Vertical scale. Q-E01-01 records three elevation bands (0 to 30, 30 to 100, 100 to 300 wu) for five layers; R-010-01 calls that a defect; the P6 mockup uses 600 wu between layers; pass 3 terrain peaks are 3,000 to 5,000 wu. Should the five layers be tied to terrain height (a layer is a terrace of the mountain) or float above it (a layer is an altitude band the terrain pokes through)? What should one layer step look like next to a cliff?
2. Cross-layer combat. `references/E-01/notes.md:15` records it as "an intended strategic tuning lever (range/damage vary by layer offset), still under research"; Q-008-01 closes the prototype as same-layer only. May the options explore how cross-layer strikes would read, or must they assume same-layer only?
3. "Non-focused layers dim slightly" versus the spec's 60 percent dim (`docs/legacy/stage_specs/stage_11c_layer_visuals_and_fog_spec.md:59`). How much should the other four layers fall back when one has focus?
4. A-299's translucent grid around each unit versus the P6 mockup's translucent plane for a whole layer. One idea or two? Is a whole-layer plane wanted at all?
5. The E-01 purpose still says "three to five" layers. Confirm the options assume exactly five everywhere.

## 7. Proposed option width

Four options, two wild. Each option describes, from the player's chair: the stack at normal camera distance, a unit changing height, the per-unit ring and the preference indicator, the HUD strip and what focus does to the picture, and the pulse reveal and fade.

## 8. Westley confirms

Batch 1, 2026-09-22, verbatim: "no specific scale numbers, that's for the agents to decide based on their specific option, layer differences will also change per-era: in space layer differences can be quite large, but on land layer differences are a lot smaller in small-scale combat (pre-high altitude planes or deep sea submarines). For the dimming, layer it's on should be around 50%, adjacent layers 10-20%, layers 2 away are 5%. The idea behind it is visible but not in the way. - When the player toggles to a different layer we should show them a little icon or something to indicate which layer the unit would be moving too, like a waypoint or something. Grid around each unit, not whole layer, players need to be able to see the battlefield and the background and things behind the grid view (think Autocad, Unreal engine, tools that visualize 3D objects well and clear to the user and user friendly). Exactly 5 for each, for eras that don't have units that can literal "fly" (roman/greek), the escelation will still be land, it'll just be mountains or something reasonable to get that high/low."

Folded into the brief:

- Vertical scale (question 1): no numbers from Westley; each option sets its own scale and says why. The spacing is a per-era value: large in a space era, small in a land era before high-altitude flight or deep submarines. Exactly five layers in every era; in a land era without flying units the upper layers are still land (mountains or something reasonable).
- Dimming (question 3): confirmed 2026-09-22, verbatim "Layer dimming: grid visibility per layer". The per-unit grid shows at about 50 percent on the unit's own layer, 10 to 20 percent on adjacent layers, 5 percent two layers away: "visible but not in the way". How far non-focused layers fall back under strip focus stays "slightly" (Q-009-01) and is each option's call.
- Cross-layer combat (question 2): not answered in batch 1. Options assume same-layer combat (Q-008-01) and may note where a cross-layer variant would change the picture.
- Layer-change indicator: when the player toggles a unit toward another layer, a small icon shows which layer it is moving to, like a waypoint. This is the R-009-02 preference indicator, now given a direction.
- Grid (question 4): a grid around each unit, never a whole-layer plane. The battlefield, the background, and anything behind the grid must stay visible. Reference register: AutoCAD, Unreal Engine, and other 3D visualization tools that read clearly.
- Five layers (question 5): confirmed.

## 9. Sub-agent brief

Follow the common template in `../README.md` ("Sub-agent template"). Sections 4 and 8 of this file are the constraints; where they disagree, section 8 wins.

- Options: 4, of which 2 wild.
- A grid around each unit, never a whole-layer plane; the battlefield and everything behind the grid stays visible. Register: AutoCAD, Unreal Engine, and other 3D visualization tools that read clearly.
- A waypoint-like icon that shows which layer a unit is moving to when the player toggles it.
- The per-unit grid's visibility is about 50 percent on the unit's own layer, 10 to 20 percent on adjacent layers, 5 percent two away. Strip focus dims non-focused layers "slightly"; each option shows how much.
- No fixed spacing: each option sets its own vertical scale and says why; spacing is per era (large in space, small on land). Five layers in every era, including land eras without flying units.
- Assume same-layer combat; note where a cross-layer variant would change the picture.

## 10. Decision (2026-09-23)

Westley, verbatim: "For layer system I'd like to combine Terrace Reading with Floor Spindle and have both display, but the neither should be visually loud, just a subdued indicator (not blocking the view). We'll need to come up with a method to indicate to the player that there are units blocked by their current perspective, like a little exlamation point on the blocking units, this is to be determined and open, but I think it'd be good game design for us to indiciate to the user that they're not seeing the whole picture in some fashion."

Recorded as: Terrace Reading combined with Floor Spindle, both subdued; an occlusion indicator for hidden units is open (Q-E01-08 closed, Q-009-02).

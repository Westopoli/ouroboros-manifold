# Multi-perspective camera: perception brief

## 1. Feature and status

E-16 S-103 "The tactical camera", rules R-103-01 to R-103-04 (`docs/bible/epics/E-16-client-camera-hud-and-world-view.md:29-38`). Stage 1 rows A-145 to A-148 and A-155 (`docs/legacy/agora_era/stage1_audit.md:246-249,256`), A-302 (`:474`). Flag Q-103-01 closed (a) on 2026-09-14 (`docs/northstar/ambiguity_register.md:99`). Research item RL-Q75 (`docs/legacy/research_lane_queue.md:93`) requested 2026-09-14, never run. The E-16 gate calls this "the biggest open design item in the whole bible" (`E-16:14`). A fixed-angle interim camera ships in every playtest round; the full system is committed scope waiting on this design. The map view zoom band (Q-103-02) has its own brief in `../map-view/`.

## 2. Player-facing goal as documented

"As a commander, I want a free camera I manage myself, so that attention is my skill and the camera is never the enemy." (`E-16:29`)

The old bible's endgame target: "a multi-perspective camera system that lets the player read the battle from whichever angle reveals the situation best." Presets: "top-down, 45° overhead, horizontal, 45° upward, and individual unit POV. Switchable via hotkey, with rapid transitions so the player can re-orient quickly mid-engagement." The camera is "layer-independent. It can focus on or emphasize a specific layer in view, but it is not bound to any layer. The player chooses what to view; the layer system is spatial state the camera observes... coupling the camera to a layer would conflate viewing and being, and would break the 'commander observing' stance the game requires." And: "the control scheme for layer-independent multi-angle cameras is genuinely hard." (`docs/bible_history/bible_2_00_design_vision.md:77-83`)

Hub framing: "Not a god game: you do not hover above the world pressing buttons. You are in it." (`docs/bible/game_bible.md:50`)

## 3. Westley's own words

A-145 verdict, Stage 1 audit, 2026-09-10 (`stage1_audit.md:246`): "Westley: this is not aspirational — the multi-perspective camera system ships from launch, not as a deferred post-launch target. Promote out of Endgame Targets into committed launch scope. Mechanism TBD, needs dedicated research before design: modern/advanced interfaces for viewing a complex 3D-layered system beyond flat top-down (survey game and non-game precedent; augmented-reality research on perception/legibility rules for viewing layered spatial data is an explicit lead). Westley is willing to spend significant time on this system — perception matters, and the camera must read to the player as both intelligent and genuinely useful, not a gimmick. Current fixed top-down camera (hub Stage 8, built) is the interim state pending this research and redesign."

A-148 (`:249`): "the deferred control-scheme problem for a layer-independent multi-angle camera is the same open research question as A-145's mechanism-TBD note, not a separately-scheduled future problem. Fold into the same research task."

Q-103-01 answer, 2026-09-14 (`ambiguity_register.md:99`): "(a), Track R research task now (RL-Q75 covers camera and control-group depth together); the fixed top-down interim ships in every round regardless."

Landscape design phase, question 5, 2026-09-21 (`docs/northstar/research/landscape_design/README.md:15`): "5: we're going for age of empires online, playful bright animations, class RTS camera angle for now (camera system to be designed)."

Mockup review 2, 2026-09-21 (`landscape_design/README.md:63`): "zoomability would have a "floor" that you can follow elevation changes with (halo wars had a mechanic like this), you stayed at your zoom "height" even when elevation changed, so scrolling to a higher elevation didn't require you to adjust your zoom level. Though Halo Wars had small changes, I want this game to have big changes for vastly different heights."

Mockup review 1, 2026-09-21 (`landscape_design/README.md:49`): "Camera did pan correctly but the "map" lines just pop up on screen withuot moving as you zoom out, and given it's representing things on the map, not moving with the map looks very broken."

## 4. Fixed constraints any option must honor

- R-103-01: free pan, zoom, edge-scroll; "no auto-anchoring, no forced follow, and no camera modes" (`E-16:32`). See question 2 below.
- R-103-02: the mission canvas edges bound the camera at any zoom (`E-16:33`).
- R-103-04: the camera is never bound to a layer; the layer strip changes focus, not the camera (`E-16:35`). Focus is purely visual (Q-009-01, `ambiguity_register.md:31`).
- The preset set as recorded: top-down, 45° overhead, horizontal, 45° upward, individual unit POV; hotkey-switchable; rapid transitions (A-146, `stage1_audit.md:247`).
- "Commander observing" stance: viewing is not being (A-147, `:248`).
- Camera floor: the camera keeps its height above the ground under it, bands defined by height above ground; recorded as an E-16 S-103 rule (`landscape_design/README.md:71`).
- Always 5 layers (Q-E01-01, `ambiguity_register.md:9`); layers read as height on screen, a one-layer step moves a unit by more than 5 percent of viewport height (R-010-03, `docs/bible/epics/E-01-layer-system.md:166`).
- Principle 6: no feature lets the player issue an order without thinking about where their units are (`game_bible.md:78`).
- Performance gate: 60 fps with 1,000 units on screen and the HUD live (`E-16:180`).
- Battlefield scale: 20 to 30 tactical screens, three zoom bands (`landscape_design/README.md:34`).
- Era-agnostic: nothing in the camera may depend on an era.

## 5. Prior art already named

- Ender's Game, the Battle School observation deck: "Ender reading the battle from many angles" (`bible_2_00_design_vision.md:85`).
- Age of Empires 3 and StarCraft 2: the player manages their own viewport (`docs/bible_history/bible_2_00_combat.md:172`; A-302).
- Augmented-reality perception and legibility research for layered spatial data (A-145, A-155).
- Halo Wars: zoom height follows terrain (review 2).
- Age of Empires Online: the "class RTS camera angle for now" register (`landscape_design/README.md:15`).
- Immortal: Gates of Pyre control scheme, StarCraft 2, Halo Wars, Supreme Commander (RL-Q75, `research_lane_queue.md:93`).

Prior research the sub-agent must read: `docs/legacy/topics/delegated_command_precedents.md` (the Ender's Game decomposition; its verdict that a literal Battle Room arena is a "bad fit, small ceiling" for this game, `:83`).

## 6. Contradictions, as questions for Westley

1. Scope. A-145 says the camera "ships from launch"; R-103-03 says it is "committed later scope"; Q-103-01 says the interim ships every round regardless. Which target should the options assume: the full system as the launch camera, or the full system as the thing the interim grows into?
2. R-103-01 forbids "camera modes", yet the presets are hotkey-switchable views. Is "no modes" about auto-follow, anchoring, and lock-on only, leaving presets allowed? Or should presets be one continuous camera the player steers rather than discrete modes?
3. E-16 calls the interim "fixed top-down" but the P2 and P6 mockups run a 60 to 65 degree pitch (`docs/northstar/plans/briefs/2026-09-21-p2-landscape-mockup.md:26`, `2026-09-22-p6-layers-mockup.md:62`), and the P6 brief notes top-down hides the height S-010 requires. Which is the interim?
4. Zoom bands are defined by absolute height in the P2 brief (`:108-116`) and by height above ground after review 2 (`landscape_design/README.md:71`). Is the height-above-ground floor now the standard for every band?
5. Unit POV is in the preset list. In a game where "you are in it" but never a single unit, what is the player doing in unit POV: reading, or commanding?

## 7. Proposed option width

Four options, of which two wild (no shipped game has the shape). Each option must include a control table: what the hands do to switch views, steer, and return, and what the player sees while the view changes. The control scheme is half the deliverable.

## 8. Westley confirms

Batch 1, 2026-09-22, verbatim: "present is classic RTS, I'm not sure if that's 45 degrees. We will have an auto-anchor to that view, but we'll allow users to have a different "mode" and that's the mode we're designing. Ships from launch. For the camera height, I described this in a prior chat recently, grepping "halo wars" might show what I answered, basically Halo Wars camera stayed at the height the user was at even during elevation changes, so the user wasn't fighting to zoom and move at the same time when changing elevation."

Folded into the brief:

- Scope (question 1): the multi-perspective system ships from launch. It is a "mode" the player enters; the default view is the classic RTS camera with an auto-anchor back to it. The options design the mode, and each must say how the player enters it, leaves it, and snaps home.
- Modes (question 2): a designed mode is allowed. R-103-01's "no auto-anchoring, no camera modes" is superseded for the default view (auto-anchor to classic) and for the designed mode; that rule is rewritten by the Design Lane when a pick lands, not in this pass.
- Interim (question 3): classic RTS angle; the pitch number is not a decision ("I'm not sure if that's 45 degrees").
- Height (question 4): the Halo Wars floor is the standard. The camera keeps the player's height above the ground under it through elevation changes, so the player never zooms and moves at once to follow terrain (also `docs/northstar/research/landscape_design/README.md:63,71`; `docs/northstar/plans/briefs/2026-09-21-p2-landscape-mockup-pass3.md:34`).
- Unit POV (question 5): not answered in batch 1. Options may include or omit a unit POV preset; if included, the option must say what the player does there.

## 9. Sub-agent brief

Follow the common template in `../README.md` ("Sub-agent template"). Sections 4 and 8 of this file are the constraints; where they disagree, section 8 wins.

- Options: 4, of which 2 wild.
- The designed mode, entered from the classic RTS default view that has an auto-anchor home. Each option says how the player enters the mode, switches views inside it, steers, and returns home, and what they see while the view changes.
- A control table per option: keys, mouse, and gestures for every action above.
- How the five layers read from each view in the option; the Halo Wars height floor holds in every view.
- Augmented-reality perception and legibility research is an explicit lead for wild options. Read `docs/legacy/topics/delegated_command_precedents.md` first; a literal Battle Room arena was already judged a bad fit.
- Unit POV: optional; if an option includes it, say what the player does there.

## 10. Decision (2026-09-23)

Westley, verbatim: "For the camera, I'd like to implement both the layer peel and the angle rack and give the player the option to use the layer peel if they want. I'd also like the users to be able to have a key that "flips" their current perspective 180 degrees, so if they're at 45 pointing south, they can click a key combination and point 45 north (maintaining angle, but swapping perspective relative to some center tbd) Record the decsion with a marker that now that the choice is made that we'll need to dive into control specifics later."

Recorded as: Angle Rack and Layer Peel both, Layer Peel as a player option, plus a 180-degree flip key; control specifics later (Q-103-03, Q-103-04).

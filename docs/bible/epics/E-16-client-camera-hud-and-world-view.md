# E-16 — Client: Camera, HUD, World View, and Screens

## Definition-completeness gate (run 2026-09-10)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Yes, 9 stories, 52 rules. Numbers come from the bible's HUD, world view, and transition sections and from config timing values. |
| Every input listed with range and rejection behavior | Yes, see Inputs. |
| Every output listed with where it is observable | Yes, see Outputs; every output here is a screen region, observable by T2. |
| Implied-but-unstated behavior turned into flags | 7 new flags, Q-103-01, Q-104-01, Q-105-01, Q-106-01, Q-108-01, Q-110-01, Q-111-01. |
| Every visible-surface story has a reference | **No.** Every story in this epic is a visible surface; `references/E-16/notes.md` is a stub. The IGoP HUD screenshots the bible cites (`docs/design_questions/igop_hud_reference_alpha.png`, `_beta.png`) are the first entries once Westley confirms them. |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed.** Blocked on open flags and references. The camera is chosen (Q-103-03, the Angle Rack and the Layer Peel with a flip key); its control specifics (Q-103-04) and the map view prototype (Q-103-05) are the load-bearing open items. This epic is client-ladder work and is built only after the sim ladders are green (Stage 4 roadmap).

## Purpose

Everything the player sees and touches that is not the units themselves. In a mission: a standard RTS camera, a lean bottom-bar HUD in the register of Immortal: Gates of Pyre with the economy chrome removed, a layer strip, control groups, a minimap, the commander's face. Between missions: a 3D star map the player orbits like a tabletop, faction territory as glowing filaments and translucent shells, conflict as flashes of light, and the chronicle printing beside it. Around the loop: onboarding, briefing, debrief, a clean exit at every chapter boundary, and one unbroken camera move from battle to galaxy to the next battle.

The design rule for every panel here is the player-perception rule adopted in Stage 1: state what the player can see and what it tells them, not where the pixels go.

## Obviously working in 60 seconds

Start a mission. The HUD shows objectives top-left, clock top-right, portraits and cooldown rings bottom-center, no minimap (the map view of S-161 replaces it), control-group tabs, the commander bottom-right, and a five-slot layer strip on the right edge. Pan, zoom, box-select, bind a control group to 1, press 1: the group is selected and the tab highlights. End the mission: the camera pulls back until the battlefield is a point of light, the galaxy fades in, the scroll panel slides in and prints, a border visibly morphs over two seconds, Proceed pushes the camera into the next system and the briefing appears. No loading screen anywhere.

## Stories

### S-103 — The tactical camera
As a commander, I want a free camera I manage myself, so that attention is my skill and the camera is never the enemy.

Rules
- R-103-01  Given a mission, When the player pans, zooms, or edge-scrolls, Then the camera moves freely with no forced follow; the classic view has one auto-anchor home the player returns to by key, and the designed views of R-103-05 and R-103-06 are the only camera modes.
- R-103-02  Given any zoom level, When the viewport is read, Then the mission canvas edges bound the camera; it never leaves the map.
- R-103-03  Given the launch build, When the camera is read, Then the default is the classic RTS view with an auto-anchor home, the camera keeps its height above the ground under it through elevation changes (the Halo Wars floor), and the multi-perspective camera of R-103-05 and R-103-06 ships from launch; the classic view ships in every playtest round regardless of the designed views' state.
- R-103-05  Given the Angle Rack, When the player enters it, Then five fixed vantage angles (top-down, 45° overhead, horizontal, 45° upward, unit POV) are hopped between by hotkey with a short tween, pan, zoom, and edge-scroll work inside each, and a home key returns to the classic view [Q-103-04: the keys].
- R-103-06  Given the Layer Peel, When the player enables it (an option, off by default), Then the five layers fan apart around the focus point into translucent planes, scrolling walks focus between planes, the fan pans and zooms as one, and releasing closes the planes to true height; fog and cross-layer vision are untouched. The peel is a player option [Q-103-04: its default state, and whether the peel's plane focus and the layer strip's focus are one control].
- R-103-07  Given any view, When the player presses the flip key, Then the camera turns 180 degrees about a center, keeping its pitch and distance, so a 45° view facing south becomes a 45° view facing north [Q-103-04: the key and the center it turns about].
- R-103-08  Given a selection in the tactical view, When the player presses A and then left-clicks a point or a visible enemy, Then the selection attack-moves there; right-click alone is move (Westley 2026-10-01; the rest of the control scheme stays under Q-103-04).
- R-103-04  Given the camera, When it moves, Then it is never bound to a layer; the layer strip changes focus, not the camera.

Inputs: mouse, keyboard, edge scroll.
Outputs: viewport transform.
Open flags: Q-103-04 (control specifics for the chosen camera: keys, the flip center, height floor per view, peel focus versus strip focus). Chosen through the options pass, `docs/northstar/research/options/camera/`, Q-103-03.

### S-161 — The map view
As a commander, I want to pull the camera back until the battle reads as a map, give groups basic orders from there, and zoom back in, so that a 20 to 30 screen battlefield is one continuous space.

Rules
- R-161-01  Given the camera pulled back past the tactical band, When the map view opens, Then it replaces the minimap; there is no corner minimap [Q-103-05: whether an always-visible glance survives].
- R-161-02  Given the map view, When the player selects a group and clicks a point or a visible enemy, Then the only orders are move and attack-move; every other command needs the tactical band.
- R-161-03  Given the map view, When groups are drawn, Then layers collapse into one icon per group carrying a mark for Upper (layers 4 and 5), Lower (1 and 2), or Expansive (1 to 5) [Q-103-06: a group entirely on layer 3, and indicators beyond pins].
- R-161-04  Given the map view, When it is read, Then it shows the mission only, never the galaxy; the galaxy view lives outside missions.
- R-161-05  Given the map view, When it is drawn, Then the overlay moves with the terrain and fog applies as everywhere; the look is the Sand Table candidate, a shrunken three-dimensional model of the ground with groups as pins, with a 45° view of the same table in which the layers sit far enough apart that specific sets of units read; committed only after a prototype [Q-103-05].

Inputs: mouse, keyboard.
Outputs: viewport transform; orders.
Open flags: Q-103-05 (Sand Table prototype before commitment), Q-103-06 (layer marks for groups beyond pins). Chosen direction through the options pass, `docs/northstar/research/options/map-view/`.

### S-104 — The HUD tells me what I need and nothing else
As a commander, I want a lean HUD that shows objectives, my selection, my groups, my structures, the clock, and my commander, and stays out of the way, so that the world is what I look at.

Rules
- R-104-01  Given a mission, When the HUD is drawn, Then the player can always see the objective list with progress (top-left) and a quiet ticker of notable beats beneath it; the ticker recognizes structure captured, structure lost, force routed, and objective threshold crossed, and nothing else at launch.
- R-104-02  Given nothing mission-significant has happened, When the top-center is read, Then it is empty; Given a structure falls or an objective band threshold is crossed, Then a banner appears there and clears within 5 s.
- R-104-03  Given a mission, When the top-right is read, Then it shows elapsed mission time and a pause or menu button [Q-104-01: pause in a real-time multiplayer match].
- R-104-04  Given a selection, When the bottom-center is read, Then it shows the selected units' portraits, summed HP, and one ability slot per unit type with a cooldown ring, and no contextual prompt or "ready" notification.
- R-104-05  Given the map view (S-161) in place of a minimap, When the player pulls the camera back, Then friendly groups are bright, visible enemies dim, terrain reads as ground, objectives are marked, and reinforcement structures are colored by owner.
- R-104-06  Given player-owned reinforcement structures, When the structure panel is read, Then one row per owned structure shows the production timer bar, next unit icon, and structure HP; neutral and enemy structures do not appear.
- R-104-07  Given control groups 1 through 0, When the tabs are read, Then each bound group shows its unit-type icon and count.
- R-104-08  Given a mission, When the bottom-right is read, Then it shows the commander's portrait, name, and lineage marker.
- R-104-09  Given the right sidebar, When read, Then it is empty at launch except the layer strip.
- R-104-10  Given the in-world chrome, When read, Then every unit has a thin HP bar above it and a layer-color ring beneath it, and selected units have a selection ring; there is no enemy composition readout anywhere.

Inputs: tick delta; selection; control groups.
Outputs: HUD panels, T2-checkable.
Open flags: Q-104-01. Reference: IGoP HUD screenshots, pending confirmation.

### S-105 — Selection and control groups
As a commander, I want to click, box-select, and bind groups, and never to have an all-army button, so that positional thinking is the whole game.

Rules
- R-105-01  Given the player clicks a friendly unit, When released, Then it is the selection; Given a drag box, Then every friendly unit inside it on every layer is the selection.
- R-105-06  Given a selection that spans layers, When the player presses the hotkey for layer N, Then the selection narrows to its units on layer N; the layer strip's focus is unchanged by this.
- R-105-02  Given a selection and Ctrl plus a digit, When pressed, Then the group is bound to that digit and the units leave any other group (exclusive membership); pressing the digit recalls the group; pressing it twice centers the camera on it.
- R-105-03  Given the player presses Tab, When the layer strip has focus, Then focus cycles to the next layer.
- R-105-04  Given the client, When any input is checked, Then no select-all, select-all-army, or select-all-of-type command exists (Principle 4; A-300 killed the hotkey).
- R-105-05  Given Shift plus click, When pressed, Then the unit is added to or removed from the current selection.
- R-105-07  Given a bound group that spans layers, When the player holds its digit, Then the layer strip blooms into one bar per layer the group occupies, sized by unit count; dragging across one or more bars and releasing makes those layers the selection, and releasing the digit collapses the strip (the Comb). Tap-to-recall and narrowing by layer hotkey (R-105-02, R-105-06) stay the default for control groups and multi-layer movement; the comb is how individual layers inside a group are moved.
- R-105-08  Given a selection and a right-click move, When issued, Then every unit stays on its own layer; a layer change is a deliberate act on a manual selection.

Inputs: mouse, keyboard.
Outputs: selection set; control group state.
Open flags: none. Q-106-01 is closed: no replacement affordance; the control-group hotkeys stand. Chosen through the options pass, `docs/northstar/research/options/control-groups/`, Q-105-02.

### S-106 — The galaxy between missions
As a player, I want to orbit a 3D star map where territory glows, borders touch, and war flashes, so that the world reads at a glance.

Rules
- R-106-01  Given the world view, When drawn, Then each system is a luminous point sized by significance, brightest for the player's core, dim neutral for uncolonized.
- R-106-02  Given faction territory, When drawn, Then adjacent same-faction systems are joined by faction-colored luminous filament arcs in 3D (border and both edges solid and bright, trade edges thinner and dimmer), and each faction's systems share one translucent shell; rival shells keep a visible gap with a bright seam where they nearly meet.
- R-106-03  Given camera distance d, When d ≥ 75 (Overview), Then shells render at 40 to 60 percent opacity, filaments dim, nodes shrink, faction names float at shell centers; When 40 ≤ d < 65 (Regional, default), Then filaments dominate, shells at 8 to 15 percent, border seams are the accent; When d < 25 (Local), Then the focused system brightens, its filaments thicken, shells fade to ground fog, distant systems desaturate; between bands properties interpolate continuously, inside a band they are locked.
- R-106-04  Given attack, conquest, and revolt events in the jump log, When the map animates, Then a flash pulses at the involved systems (attack and conquest between attacker and defender, revolt at the region) for each event; the sim supplies occurrence and position, the renderer owns look.
- R-106-05  Given the world view, When idle, Then an ambient particle field (rings, inflow streams, dust, starfield, central glow) fills the space behind the territory at low opacity.

Inputs: strategic snapshot; ownership timeline; event log.
Outputs: screen; T2 screenshots.
Open flags: none beyond references. Reference required.

### S-107 — Reading the galaxy
As a player, I want to pan, zoom, orbit, focus a system, and pick out a faction, so that I can find what I am looking for.

Rules
- R-107-01  Given the world view, When the player left-drags, Then the camera pans; scroll zooms along the forward axis; right-drag orbits; clicking a system centers on it and zooms to Local.
- R-107-02  Given a time jump, When the camera auto-orbits, Then any player input overrides it; outside a jump the camera is fully the player's.
- R-107-03  Given the faction list panel (always visible), When a faction is hovered, Then its territory brightens and others dim; When clicked, Then all other territory fades to near-invisible until clicked again or elsewhere.
- R-107-04  Given the faction data panel (opposite side), When a faction is hovered or selected or a system is focused, Then it shows the faction name, system count, and aggregate stats; no per-region detail at launch.
- R-107-05  Given a system hover, When shown, Then a tooltip gives name and owner, band-sensitive, and only the system's own filaments brighten; filaments and shells have no hover.

Inputs: mouse.
Outputs: camera; panels; tooltip.
Open flags: Q-108-01 (what "aggregate stats" the data panel shows, given the no-raw-numbers rule for the chronicle: numbers here, or bands).

### S-108 — One unbroken shot
As a player, I want the mission to pull back into the galaxy and the galaxy to push into the next mission without a cut, so that the world is one space at different scales.

Rules
- R-108-01  Given the mission ends, When the player confirms, Then the camera pulls back and up until the battlefield is one point of light and the galaxy fades in around it, full screen.
- R-108-02  Given the galaxy is visible, When narration begins, Then the scroll panel slides in from the right over 0.40 s and the galaxy resizes to 62 percent width (E-09 R-069-01).
- R-108-03  Given a territory change in a keyframe, When animated, Then the shell tweens from old to new over 2.0 s; nothing snaps; all events in a keyframe animate together.
- R-108-04  Given the entry currently printing names a system, When drawn, Then that system's emission brightens subtly and the entry text is tinted in its primary faction's color.
- R-108-05  Given the last entry has printed, When the galaxy settles, Then the scroll footer shows Proceed and Exit to Main Menu with no countdown.
- R-108-06  Given Proceed, When pressed, Then the panel slides out, the next mission's system highlights, and the camera pushes in until the tactical space materializes and the briefing appears.
- R-108-07  Given Exit, When pressed at this boundary or at the post-mission moment before pull-back, Then the screen fades to black and the main menu loads, with no camera choreography.

Inputs: time jump report; chronicle entries; player buttons.
Outputs: screen; menu.
Open flags: none beyond references. Reference required (No Man's Sky planetary transition is the named model).

### S-109 — Briefing, debrief, onboarding
As a player, I want the screens around a mission to read as orders and after-action reports from my civilization, so that the chain of command is felt.

Rules
- R-109-01  Given a mission is generated, When the briefing shows, Then it is E-10 S-079 (three sections, Accept and Refuse only).
- R-109-02  Given a mission ends, When the debrief shows, Then it is E-10 R-079-03 and offers Continue and Exit.
- R-109-03  Given a new campaign, When it starts, Then the onboarding screen is E-08 S-063.
- R-109-04  Given any of these screens, When rendered, Then no raw field numbers appear.

Inputs: mission setup, result, onboarding.
Outputs: screens.
Open flags: none new; references shared with E-08 and E-10.

### S-110 — Main menu and settings
As a player, I want a main menu that sets the tone and a settings screen that covers the basics, so that the first thing I see is the game and the second is control.

Rules
- R-110-01  Given launch, When the main menu shows, Then the galaxy particle structure runs behind it at 70 percent opacity with an autonomous camera cycling six moods with 5 s transitions, and the menu offers New Campaign, Continue, Settings, and Quit.
- R-110-02  Given Settings, When opened, Then it offers resolution, fullscreen, master and music volume, key rebinding for the layer modifier and control groups, and edge-scroll on or off; accessibility options (colorblind palette, UI scale) are a later story, not in the first playtest rounds.
- R-110-03  Given Continue, When pressed with a save at a chapter boundary, Then the campaign resumes at that boundary.
- R-110-04  Given any loading screen the game shows (campaign load, era switch), When displayed, Then it carries information the player would otherwise never see, in the register of the chronicle (what the Long Horizon foreshadows), never wallpaper art or a bare spinner [Q-110-03: what is shown]. No loading screen exists between mission and galaxy (S-108).

Inputs: menu input.
Outputs: screens.
Open flags: Q-110-03 (loading screen content; decided before launch).

### S-111 — Saving
As a player, I want the game saved at every chapter boundary without asking, and to be able to leave at those boundaries, so that I never lose an evening.

Rules
- R-111-01  Given a mission start, a mission end, or a time jump end, When reached, Then an autosave is written before the player can continue.
- R-111-02  Given a load, When the campaign resumes, Then the world, ledger, chapter, onboarding, RNG state, and chain counter are restored such that the next jump is deterministic (E-08 R-064-04).
- R-111-03  Given a save from a different game version, When loaded, Then it is refused with a message naming the versions.
- R-111-04  Given the campaign list, When the player starts a new campaign, Then a new campaign slot is created with no fixed limit on the number of campaigns; there is no save of any kind during a mission, and quitting mid-mission returns the campaign to its last chapter-boundary autosave.

Inputs: game state.
Outputs: save files; menu.
Open flags: none.

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Tick delta, snapshot, jump report, chronicle entries | Sim | | malformed delta drops the frame and logs |
| Mouse, keyboard | Player | | unknown keys ignored |
| Rebinding | Settings | | conflicts refused |

## Outputs

| Output | Observable where |
|---|---|
| Every panel and screen | Screen; T2 screenshots and click tests |
| Selection, control groups, camera | Tick delta commands; screen |
| Save files | Disk |

## Invariants

- The HUD never shows an enemy composition readout.
- No select-all command exists.
- No loading screen between mission and galaxy and mission.
- Every screen text is free of raw field numbers.

## Scale requirements

Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is escalated): 60 fps with 1,000 units on screen and the HUD live; galaxy view at 60 fps with 250 to 400 systems, shells, and particles, with automatic quality fallback allowed (Q-106-02 closed 2026-09-28); transition never drops below 30 fps. Measured on the minimum-spec machine (GTX 1070 class, `game_bible.md` "Reference Hardware"); on the forge's RTX 3060 the same scenes must hold about 110 fps and the transition floor about 55 fps.

## Look and behavior references

`references/E-16/notes.md`, missing: IGoP HUD screenshots (cited by the bible, to be confirmed), galaxy map references, seamless transition clip references, main menu tone.

## Ways this could be wrong

- Control-group depth. Westley's target (2026-09-14): a talented player runs three armies with two or three layers inside each. RL-Q75 answered it with the Comb (R-105-07). The risk is that the held-digit bloom reads too slowly in a fight and players ask for the all-army button we refuse.

- Camera anchors to the selection.
- Box-select ignores layer focus (or honors it) contrary to Q-105-01's answer.
- A select-all binding survives from Stage 8.
- Shell opacity does not lock inside a band, so zooming shimmers.
- Territory snaps at keyframes.
- Proceed has a countdown.
- Exit runs the camera choreography.
- Autosave written after the player continues, so a crash loses the boundary.

## Open ambiguity flags

Q-104-01, Q-106-01, Q-108-01. Details in `docs/northstar/ambiguity_register.md`.

## Depends on

- E-01, E-11, E-12, E-13 (what the HUD and camera show).
- E-08, E-09, E-10 (onboarding, chronicle, briefing, debrief).
- E-15 (reinforcement structure panel).
- E-18 (visual style and animation for menus and transitions).
- E-19 (pause and exit in multiplayer).

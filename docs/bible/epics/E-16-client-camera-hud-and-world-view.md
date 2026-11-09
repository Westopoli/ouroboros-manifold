# E-16 — Client: Camera, HUD, World View, and Screens

## Definition-completeness gate (run 2026-09-10)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Yes, 16 stories, 91 rules. Numbers come from the bible's HUD, world view, and transition sections and from config timing values; the economy and layer-action stories (S-230 to S-235) state what must be shown and leave numbers and layout to flags. |
| Every input listed with range and rejection behavior | Yes, see Inputs. |
| Every output listed with where it is observable | Yes, see Outputs; every output here is a screen region, observable by T2. |
| Implied-but-unstated behavior turned into flags | 9 open flags: 3 on the first stories, Q-103-04, Q-103-06, Q-111-01, and 6 on S-230 to S-235, Q-230-01, Q-230-03, Q-231-03, Q-232-01, Q-232-02, Q-233-01 (Q-235-01 closed 2026-10-12; Q-103-05, Q-110-03, Q-230-02, Q-231-01 and Q-231-02 closed 2026-10-21, register). |
| Every visible-surface story has a reference | **No.** Every story in this epic is a visible surface; `references/E-16/notes.md` is a stub. The IGoP HUD screenshots the bible cites (`docs/legacy/design_questions/igop_hud_reference_alpha.png`, `_beta.png`) are the first entries once Westley confirms them. |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed.** Blocked on open flags and references. S-230 to S-234 are design decided and not scheduled for building; the ticker beats of S-235 are queued (VG-E1M, VG-E1W). The camera is chosen (the Angle Rack and the Layer Peel with a flip key); its control specifics (Q-103-04) are the load-bearing open item (the map view prototype, Q-103-05, closed 2026-10-21: prototype first, then commit). This epic is client-ladder work and is built only after the sim ladders are green (Stage 4 roadmap).

## Purpose

Everything the player sees and touches that is not the units themselves. In a mission: a standard RTS camera, a lean bottom-bar HUD for the commander in the register of Immortal: Gates of Pyre with the economy chrome removed, a layer strip, control groups, the map view in place of a minimap, the commander's face, and one continuous zoom from a single unit to the battlefield's map view. A second player who runs the economy has a screen of their own (S-230); a commander playing alone has a dial, a doctrine switch and a way to ask by pointing (S-231); the three layer actions and the economy's news have their places (S-232, S-235). Between missions: a 3D star map the player orbits like a tabletop, faction territory as glowing filaments and translucent shells, conflict as flashes of light, and the chronicle printing beside it. Around the loop: onboarding, briefing, debrief, a clean exit at every chapter boundary, and one unbroken camera move from battle to galaxy to the next battle.

The design rule for every panel here is the player-perception rule adopted in Stage 1: state what the player can see and what it tells them, not where the pixels go.

## Obviously working in 60 seconds

Start a mission. The HUD shows objectives top-left, clock top-right, portraits and cooldown rings bottom-center, no minimap (the map view of S-161 replaces it), control-group tabs, the commander bottom-right, and a five-slot layer strip on the right edge. Pan, zoom, box-select, bind a control group to 1, press 1: the group is selected and the tab highlights. End the mission: the camera pulls back until the battlefield is a point of light, the galaxy fades in, the scroll panel slides in and prints, a border visibly morphs over two seconds, Proceed pushes the camera into the next system and the briefing appears. No loading screen anywhere.

## Stories

### S-103 — The tactical camera
As a commander, I want a free camera I manage myself, so that attention is my skill and the camera is never the enemy.

Rules
- R-103-01  Given a mission, When the player pans, zooms, or edge-scrolls, Then the camera moves freely with no forced follow; the classic view has one auto-anchor home the player returns to by key, and the designed views of R-103-05 and R-103-06 are the only camera modes.
- R-103-02  Given any zoom level, When the viewport is read, Then the mission canvas edges bound the camera; it never leaves the map.
- R-103-03  Given the launch build, When any battle scene is drawn, Then it is 3D, land and space alike, and 2D is for UI screens only (Q-STAGE3-01; Westley, 2026-10-07); and When the camera is read, Then the default is the classic RTS view with an auto-anchor home, the camera keeps its height above the ground under it through elevation changes (the Halo Wars floor), and the multi-perspective camera of R-103-05 and R-103-06 ships from launch; the classic view ships in every playtest round regardless of the designed views' state.
- R-103-05  Given the Angle Rack, When the player enters it, Then five fixed vantage angles (top-down, 45° overhead, horizontal, 45° upward, unit POV) are hopped between by hotkey with a short tween, pan, zoom, and edge-scroll work inside each, and a home key returns to the classic view; the Angle Rack is entered on a held key plus 1 to 5 (Westley, 2026-10-07).
- R-103-06  Given the Layer Peel, When the player enables it (an option, off by default), Then the five layers fan apart around the focus point into translucent planes, scrolling walks focus between planes, the fan pans and zooms as one, and releasing closes the planes to true height; fog and cross-layer vision are untouched. The peel is a player option on a toggle, and its plane focus and the layer strip's focus are one control (Westley, 2026-10-07).
- R-103-07  Given any view, When the player presses the flip key, Then the camera turns 180 degrees about a center, keeping its pitch and distance, so a 45° view facing south becomes a 45° view facing north; the flip is a modifier plus the anchor key and turns about the camera's ground target, and the height floor is shared across views (Westley, 2026-10-07).
- R-103-08  Given a selection in the tactical view, When the player presses A and then left-clicks a point or a visible enemy, Then the selection attack-moves there; right-click alone is move (Westley 2026-10-01; the rest of the control scheme stays under Q-103-04).
- R-103-09  Given the player pans by keys or by edge-scroll, When the zoom changes, Then the pan speed stays the same on screen, so the ground covered per second grows in proportion as the camera zooms out; the Settings pan-speed slider (R-110-02) scales that speed.
- R-103-04  Given the camera, When it moves, Then it is never bound to a layer; the layer strip changes focus, not the camera.
- R-103-10  Idea only, not a decision (Q-103-07; Westley, 2026-10-07). Instead of the Angle Rack and Layer Peel above, the player could bind keys to camera angles of their own: each key puts the camera at an angle relative to the current forward direction of a unit, in a view that tracks the unit as it moves; a default mode that does not follow, reached by its own key, is the one the player switches back to; and the player may change as much about each view as we can give: its angle, whether it follows, its zoom distance. Nothing here is specified or scheduled.
- R-103-11  Given a ground-era mission, When the battle screen draws it, Then every own unit and every seen enemy (R-089-04) has a 3D body on the terrain, and slope midlines are not marked on the land view: the midline is a sim position (R-004-06), told by sight and height (Westley 2026-10-22, DEC-S001-no-slope-markers); flyers stand above their layer floor once the terrain frame carries the floors (K-c6) (Architect, 2026-10-09; built by C6, C7 and VG-C-wire).

Inputs: mouse, keyboard, edge scroll.
Outputs: viewport transform.
Open flags: Q-103-07 (the player-bound camera, an idea only, not a blocker).
Chosen through the options pass, `docs/northstar/research/options/camera/`.

### S-161 — The map view
As a commander, I want to pull the camera back until the battle reads as a map, give groups basic orders from there, and zoom back in, so that a 20 to 30 screen battlefield is one continuous space.

Rules
- R-161-01  Given the camera pulled back past the tactical band, When the map view opens, Then it replaces the minimap; there is no corner minimap [Q-103-05: whether an always-visible glance survives].
- R-161-02  Given the map view, When the player selects a group and clicks a point or a visible enemy, Then the orders are move and attack-move; a commander playing alone may also ask for things by pointing at the map from here (expand here, fortify this pass, siege at this gate; E-22 S-180, S-231), allowed and subject to change (Westley, 2026-10-02); every other command needs the tactical band.
- R-161-03  Given the map view, When groups are drawn, Then layers collapse into one icon per group carrying a mark for Upper (layers 4 and 5), Lower (1 and 2), or Expansive (1 to 5) [Q-103-06: a group entirely on layer 3, and indicators beyond pins].
- R-161-04  Given the map view, When it is read, Then it shows the mission only, never the galaxy; the galaxy view lives outside missions.
- R-161-05  Given the map view, When it is drawn, Then the overlay moves with the terrain and fog applies as everywhere; the look is the Sand Table candidate, a shrunken three-dimensional model of the ground with groups as pins, with a 45° view of the same table in which the layers sit far enough apart that specific sets of units read; committed only after a prototype [Q-103-05: the prototype decides it, and with it whether this look is the zoomed-out end of the one continuous drawing of S-234 or a separate drawing (Westley, 2026-10-06)].

Inputs: mouse, keyboard.
Outputs: viewport transform; orders.
Open flags: Q-103-06 (layer marks for groups beyond pins). What the map view shows of the economy is S-235. Chosen direction through the options pass, `docs/northstar/research/options/map-view/`.

### S-104 — The HUD tells me what I need and nothing else
Flag closed, rule text pending: Q-104-01, single-player pause is allowed (Escape or Pause halts the simulation and opens the menu) and multiplayer never pauses. The rule below is what the tests read today.
As a commander, I want a lean HUD that shows objectives, my selection, my groups, my structures, the clock, and my commander, and stays out of the way, so that the world is what I look at.

Direction changed 2026-10-02, rewrite pending: the ticker also carries economy events (S-235), and the structure panel's production timers belong to the economy seat's schedule (S-230, E-22 S-170) with the structures themselves strongpoints (E-15). The rules below are what the game does today.

Rules
- R-104-01  Given a mission, When the HUD is drawn, Then the player can always see the objective list with progress (top-left) and a quiet ticker of notable beats beneath it; the ticker names six beats: structure captured, structure lost, force routed, objective threshold crossed, the economy beat (base occupied, a side falling back to an expansion, an expansion founded, or a weather trouble arriving, R-235-03), and a strongpoint taken or lost (R-235-03).
- R-104-02  Given nothing mission-significant has happened, When the top-center is read, Then it is empty; Given a structure falls or an objective band threshold is crossed, Then a banner appears there and clears within 5 s.
- R-104-03  Given a mission, When the top-right is read, Then it shows elapsed mission time and a pause or menu button [Q-104-01: pause in a real-time multiplayer match].
- R-104-04  Given a selection, When the bottom-center is read, Then it shows the selected units' portraits, summed HP, and one ability slot per unit type with a cooldown ring, and no contextual prompt or "ready" notification.
- R-104-05  Given the map view (S-161) in place of a minimap, When the player pulls the camera back, Then friendly groups are bright, visible enemies dim, terrain reads as ground, objectives are marked, and reinforcement structures are colored by owner; the economy's places and the weather are drawn there too (S-235).
- R-104-06  Given player-owned reinforcement structures, When the structure panel is read, Then one row per owned structure shows the production timer bar, next unit icon, and structure HP; neutral and enemy structures do not appear.
- R-104-07  Given control groups 1 through 0, When the tabs are read, Then each bound group shows its unit-type icon and count.
- R-104-08  Given a mission, When the bottom-right is read, Then it shows the commander's portrait, name, and lineage marker; the economy player's screen skips this place in the beta (Westley, 2026-10-07) [Q-230-02: parked].
- R-104-09  Given the right sidebar, When read, Then it holds the layer strip and nothing else at launch; where the solo commander's dial, doctrine switch and unit-mix switches sit is the Architect's choice, with Westley's feedback after the beta (Q-231-01).
- R-104-10  Given the in-world chrome, When read, Then every unit has a thin HP bar above it and a layer-color ring beneath it in the space era only (on land there is no ring; the height step and sight tell the layer, Westley 2026-10-22, DEC-S001-no-layer-ring-land), and selected units have a selection ring, and every force set to emit carries the emit mark of S-232; there is no enemy composition readout anywhere [Q-230-03: where the line falls between that and what a player infers from the world, such as heavy gathering of one resource showing which role a side is making more of, E-22 S-171].

Inputs: tick delta; selection; control groups.
Outputs: HUD panels, T2-checkable.
Open flags: none. Q-230-02 and Q-231-01 closed 2026-10-21 (register: the economy player's screen skips this place; the Architect's choice). Reference: IGoP HUD screenshots, pending confirmation.

### S-105 — Selection and control groups
As a commander, I want to click, box-select, and bind groups, and never to have an all-army button, so that positional thinking is the whole game.

Rules
- R-105-01  Given the player clicks a friendly unit, When released, Then it is the selection; Given a drag box, Then every friendly unit inside it on every layer is the selection.
- R-105-06  Given a selection, When the player presses Alt plus a layer number (Cmd on macOS), Then a layer transfer to that layer is armed for the whole selection and the next map click places it (E-01 R-002-08); plain digits stay with control groups, and the layer strip's focus is unchanged by this. Narrowing a selection to one layer is not in the beta (Westley 2026-10-13, overturning 2026-10-07: "Alt + number remove this ruling, I'm overturning it now. Alt + number queues up alt + number + click for the entire selection to be clicked somewhere. Skip narrowing selection for now, we'll get into that after beta."); it comes after the beta.
- R-105-02  Given a selection and Ctrl plus a digit, When pressed, Then the group is bound to that digit and the units leave any other group (exclusive membership); pressing the digit recalls the group; pressing it twice centers the camera on it.
- R-105-03  Given the player presses Tab, When the layer strip has focus, Then focus cycles to the next layer.
- R-105-04  Given the client, When any input is checked, Then no select-all, select-all-army, or select-all-of-type command exists (Principle 4; A-300 killed the hotkey).
- R-105-05  Given Shift plus click, When pressed, Then the unit is added to or removed from the current selection.
- R-105-07  Given a bound group that spans layers, When the player holds its digit, Then the layer strip blooms into one bar per layer the group occupies, sized by unit count; dragging across one or more bars and releasing makes those layers the selection, and releasing the digit collapses the strip (the Comb). Tap-to-recall stays the default for control groups and multi-layer movement; narrowing by layer hotkey is after the beta (R-105-06); the comb is how individual layers inside a group are moved.
- R-105-08  Given a selection and a right-click move, When issued, Then every unit stays on its own layer; a layer change is a deliberate act on a manual selection.

Inputs: mouse, keyboard.
Outputs: selection set; control group state.
Open flags: none here. The ping of S-232 also takes a layer number key; the keys are Q-232-03 and R-103-05.
The control-group hotkeys stand, with no replacement affordance. Chosen through the options pass, `docs/northstar/research/options/control-groups/`.

### S-106 — The galaxy between missions
As a player, I want to orbit a 3D star map where territory glows, borders touch, and war flashes, so that the world reads at a glance.

Rules
- R-106-01  Given the world view, When drawn, Then each system is a luminous point sized by significance, brightest for the player's core, dim neutral for uncolonized.
- R-106-02  Given faction territory, When drawn, Then adjacent same-faction systems are joined by faction-colored luminous filament arcs in 3D (border and both edges solid and bright, trade edges thinner and dimmer), and each faction's systems share one translucent shell; rival shells keep a visible gap with a bright seam where they nearly meet.
- R-106-03  Given camera distance d, When d ≥ 37.5 (Overview), Then shells render at 40 to 60 percent opacity, filaments dim, nodes shrink, faction names float at shell centers; When 20 ≤ d < 32.5 (Regional, default), Then filaments dominate, shells at 8 to 15 percent, border seams are the accent; When d < 12.5 (Local), Then the focused system brightens, its filaments thicken, shells fade to ground fog, distant systems desaturate; between bands properties interpolate continuously, inside a band they are locked.
- R-106-04  Given attack, conquest, and revolt events in the jump log, When the map animates, Then a flash pulses at the involved systems (attack and conquest between attacker and defender, revolt at the region) for each event; the sim supplies occurrence and position, the renderer owns look.
- R-106-05  Given the world view, When idle, Then an ambient particle field (rings, inflow streams, dust, starfield, central glow) fills the space behind the territory at low opacity.
- R-106-06  Given a time jump, When the galaxy animates, Then it plays on its own as the chronicle's master clock (E-09 R-069-03, 2 ticks per second), the player sets no speed, and only expanding a chronicle entry pauses it (E-09 R-069-04; Westley, 2026-10-07: decided in the old version of the game).

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
Open flags: none. The faction data panel shows its aggregate stats as bands; raw numbers are forbidden in the chronicle, not in the simulation view.

### S-108 — One unbroken shot
As a player, I want the mission to pull back into the galaxy and the galaxy to push into the next mission without a cut, so that the world is one space at different scales.

Rules
- R-108-01  Given the mission ends, When the player confirms, Then the camera pulls back and up until the battlefield is one point of light and the galaxy fades in around it, full screen; this is a scripted move and not the player's zoom, which stops at the battlefield's map view (S-234).
- R-108-02  Given the galaxy is visible, When narration begins, Then the scroll panel slides in from the right over 0.40 s and the galaxy resizes to 62 percent width (E-09 R-069-01).
- R-108-03  Given a territory change in a keyframe, When animated, Then the shell tweens from old to new over 2.0 s; nothing snaps; all events in a keyframe animate together.
- R-108-04  Given the entry currently printing names a system, When drawn, Then that system's emission brightens subtly and the entry text is tinted in its primary faction's color.
- R-108-05  Given the last entry has printed, When the galaxy settles, Then the scroll footer shows Proceed and Exit to Main Menu with no countdown.
- R-108-06  Given Proceed, When pressed, Then the panel slides out, the next mission's system highlights, and the camera pushes in until the tactical space materializes and the briefing appears.
- R-108-07  Given Exit, When pressed at this boundary or at the post-mission moment before pull-back, Then the screen fades to black and the main menu loads, with no camera choreography.

Inputs: time jump report; chronicle entries; player buttons.
Outputs: screen; menu.
Open flags: none beyond references. Reference required (No Man's Sky planetary transition is the named model). Prototype gate (Westley, 2026-10-15): the visual move is prototyped as a mockup and approved before it is built in the game ("we're going for a No Man's Sky sort of transition, so players really get the sense of scale"); the simulation jump and the next map are pre-loaded behind the move, so the move never waits on them. Spec: `docs/northstar/plans/archive/specs/2026-10-15-transition-mockup-spec.md`.

### S-109 — Briefing, debrief, onboarding
As a player, I want the screens around a mission to read as orders and after-action reports from my civilization, so that the chain of command is felt.

Rules
- R-109-01  Given a mission is generated, When the briefing shows, Then it is E-10 S-079 (three sections, Accept and Refuse only).
- R-109-02  Given a mission ends, When the debrief shows, Then it is E-10 R-079-03 and offers Continue and Exit.
- R-109-03  Given a new campaign, When it starts, Then the onboarding screen is E-08 S-063.
- R-109-04  Given any of these screens, When rendered, Then no raw field numbers appear.
- R-109-05  Given a live mission load the simulation refuses, When the player is on the briefing, Then an error panel names the reason and offers Retry; when the refusal cannot be retried (a desync, a missing peer) the Retry button is hidden (Architect, 2026-10-09, from the lane F landing).

Inputs: mission setup, result, onboarding.
Outputs: screens.
Open flags: none new; references shared with E-08 and E-10.

### S-110 — Main menu and settings
As a player, I want a main menu that sets the tone and a settings screen that covers the basics, so that the first thing I see is the game and the second is control.

Rules
- R-110-01  Given launch, When the main menu shows, Then the galaxy particle structure runs behind it at 70 percent opacity with an autonomous camera cycling six moods with 5 s transitions, and the menu offers New Campaign, Continue, Era Library, Settings, and Quit, and nothing else.
- R-110-02  Given Settings, When opened, Then it offers resolution, fullscreen, master and music volume, a camera pan-speed slider, and a galaxy quality choice (full, stand-in, fewer particles) that the player sets by hand and the game never changes on its own, except that under the Compatibility renderer the stand-in replaces the raymarch shell at every tier (Architect, 2026-10-08), and the automatic quality fallback Q-106-02 allows (line 310) is decided once at launch from the renderer and the first galaxy frame's measured rate, never mid-session, and the Settings row shows the value chosen (Architect 2026-10-21, implementation; Westley may veto); key rebinding for the layer modifier and control groups joins it once the layer controls (Q-005-03) and the camera controls (Q-103-04) are designed (Q-110-04); accessibility options (colorblind palette, UI scale) are a later story, not in the first playtest rounds.
- R-110-03  Given Continue, When pressed with a save at a chapter boundary, Then the campaign resumes at that boundary.
- R-110-04  Given any loading screen the game shows (campaign load, era switch), When displayed, Then it carries information the player would otherwise never see, in the register of the chronicle (what the Long Horizon foreshadows), never wallpaper art or a bare spinner [Q-110-03: what is shown]. No loading screen exists between mission and galaxy (S-108).
- R-110-05  Given the Era Library, When opened from the main menu, Then the player sees one card per installed era pack that passes validation (E-20 R-146-03), in chronological order, each with the pack's name, spatial scale and tone and whether the player owns it, telling them which ages they can play; a pack that fails validation is not listed.
- R-110-06  Given an era card, When selected, Then the detail shows that pack's identity, its three tiers and its unit roster, all read from the pack manifest; nothing on the screen is hard-coded.
- R-110-07  Given ownership, When the Era Library reads it, Then it comes from a local ownership store, and in development builds every installed era is owned. The screen shows no mastery or tier progress; they return when that part of the game is defined (Q-110-05).

Inputs: menu input.
Outputs: screens.
Open flags: none. Q-110-03 closed 2026-10-21 (register: decided before launch, after a mockup).

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

### S-230 — The economy seat's screen
As an economy player in a pair, I want a screen that shows my resources, my workers, what a building would yield before I place it, my production schedule, my technology and my defenses, so that I can hold the whole economy in mind and nothing on screen does the remembering for me.

Design decided 2026-10-02, not scheduled for building (E-19 S-159, E-22). The rules say what must be shown; where it sits on screen is built from the IGoP HUD screenshots in the references, with Westley's feedback after the first beta build (Westley, 2026-10-07).

Rules
- R-230-01  Given the economy seat of a pair, When the screen is read, Then the player can see how much of each of the three resources is held (E-22 S-167), the workers and what each is doing, and the population against its one cap (E-22 S-169) [Q-230-01: the layout of the screen].
- R-230-02  Given a building the player is about to place, When it is held over a lot, Then the screen shows what that lot would yield with what stands beside it, before the building is placed (E-22 S-168).
- R-230-03  Given the production buildings, When the schedule is read, Then it shows what each is set to make and what is planned ahead on the timeline, and how long a change of focus would take (E-22 S-170).
- R-230-04  Given technology, When the player reads the technology choices, Then the screen shows what can be chosen and what is in progress (E-22 S-173) [Q-159-12: what technology does].
- R-230-05  Given walls, gates and towers, When the screen is read, Then the player can see each defense placed and where the raid lanes run (E-22 S-174).
- R-230-06  Given the economy seat, When the screen is read, Then no list of what the commander needs appears, and no alert that the pair is falling behind on the population cap, worker production, the next technology or production; the player holds those in mind and the pair talks (E-19 R-159-01).

Inputs: economy state from the tick delta; the player's building, queue, schedule and technology commands.
Outputs: the economy panels, T2-checkable.
Open flags: none. Q-230-02 closed 2026-10-21 (register: the economy player's screen skips this place). The economy player infers the enemy's composition from the world only and nothing is totalled (Westley, 2026-10-07).

### S-231 — The solo commander's hand
As a commander playing alone, I want one dial, a doctrine switch, switches for the unit mix, and a way to ask by pointing at the map, so that I steer the economy without running it.

Design decided 2026-10-02, not scheduled for building (E-22 S-179, S-180). The controls exist for a commander with nobody in the economy seat, and in a pair whose economy player has dropped out (E-19 R-140-04).

Rules
- R-231-01  Given a commander with nobody in the economy seat, When the player turns the dial, Then it sets the balance of spending between economy, technology and army (E-22 S-180).
- R-231-02  Given a mission in progress, When the player changes the doctrine, Then the rules follow the new doctrine from then on, at any time in the mission (E-22 S-179).
- R-231-03  Given the rules that pick the unit mix and the rules that shift production toward what counters the enemy units the player's forces have seen, When the player reads the unit-mix controls, Then there is one switch for each, each can be turned off, and the commander can override the mix the rules pick (E-22 S-180) [Q-231-02: how the override is made].
- R-231-04  Given the tactical view or the map view (S-161), When the player points at a place and asks for something (expand here, fortify this pass, siege at this gate), Then the request is given and the rules carry it out; the commander never places or queues anything himself. Allowed from the map view, subject to change (Westley, 2026-10-02).
- R-231-05  Given a request, When it has been given, Then how the screen shows that the request was taken, and what it shows when the rules cannot carry it out, is the Architect's choice (Westley, 2026-10-07; Q-231-02).

Inputs: dial setting; doctrine choice; switch states; a place and a request.
Outputs: the controls and their state, T2-checkable; commands carried to the rules.
Open flags: none. Q-231-01 and Q-231-02 closed 2026-10-21 (register: the Architect's choice). The dial, the doctrine switch and the unit-mix switches are outside hub principle 6 (Westley, 2026-10-07).

### S-232 — Pinging, going dark, and reach, on screen
As a commander, I want to see my ping and my emitting forces, to be told when I am pinged and from which way, and to be told when a unit type cannot reach a layer, so that the three layer actions are things I can read and use on purpose.

Rules
- R-232-01  Given selected units that can ping (E-01 S-162), When the player chooses the ping, presses a layer number and clicks a place, Then the ping is given there, and the screen shows the cooldown of the ping if the sim gives one; the ping is an ability on the one command card all selected units share, on the same keystroke for every unit, in a sub-group or the whole group (the style of Immortal: Gates of Pyre; Westley, 2026-10-07), and with a group selected the unit closest to the clicked place casts it, unless it is out of range, in which case the player moves the cursor closer until it is in range [Q-232-03: how the layer is chosen].
- R-232-02  Given a force, When the player switches it between emitting and silent (E-01 R-163-03), Then the command is given from the HUD and the force's state changes on the next tick [Q-232-03: its key].
- R-232-03  Given forces on the field, When the in-world chrome is read, Then every force set to emit carries a mark showing that it is emitting, and a silent force carries none.
- R-232-04  Given the player's units are pinged (E-01 R-162-03), When the ping lands, Then nothing is drawn: the alert is switched off for now (Westley, 2026-10-05). If it returns, it is a sector of about 60 degrees toward the caster and nothing more precise [the display of a returning alert is not decided].
- R-232-05  Given selected units whose type cannot fire at a layer offset (E-01 S-164), When the player points at an enemy at that offset, Then the cursor shows a red X while it is out of reach and returns to the regular cursor when it is back in reach (Westley, 2026-10-07), whatever the distance.

Inputs: ping and emit commands; the alert and the unit reach tables from the tick delta.
Outputs: the ping control and its cooldown; the emit mark; the alert and sector; the reach cue, T2-checkable.
Open flags: Q-232-03.

### S-233 — Choosing how the economy runs
As a commander, I want to choose how the rules run my economy and whether the enemy's economy is clever, so that the game is as hard as I want it.

Design decided 2026-10-02, not scheduled for building.

Rules
- R-233-01  Given a commander who will play alone, When the player makes the choices for a mission, Then the player can set which doctrine the rules begin with and whether each of the two unit-mix behaviours (R-231-03) is on; the starting doctrine is the player's pick and has no default, so until the player sets it nothing is produced (Westley, 2026-10-07), and it is set in the lobby (E-22 R-179-03).
- R-233-02  Given the enemy's economy, When the player makes the choices for a mission, Then the difficulty decides whether it also scouts, counters and disguises (E-22 S-181, R-181-03; E-14 R-215-06) and the player makes no pick (Westley, 2026-10-07, Q-181-01; this rule said "as a pick" until 2026-11-08).
- R-233-03  Given a multiplayer universe, When these choices are made, Then they are locked with the rest of the universe's configuration (E-19 R-144-03).

Inputs: the player's choices.
Outputs: the choice screen, T2-checkable; the settings carried into the mission.
Open flags: none.

### S-234 — One zoom, from a single unit to the battlefield
As a commander, I want to zoom smoothly from a single unit to the battlefield's map view and no further, so that the scale of the world is something I feel.

Rules
- R-234-01  Given the camera at any zoom between the closest and the battlefield's map view, When it moves, Then the world is drawn as one world at continuous detail, with smooth transitions between very different zoom levels (E-17 R-166-05, E-18 S-236).
- R-234-02  Given the closest zoom, When it is read, Then it shows a single unit in deep detail; Given the farthest zoom, Then it is the battlefield's map view of S-161.
- R-234-03  Given the camera at the map view, When the player zooms out further, Then the zoom stops; the galaxy is not reached by the player's zoom, and the pull-back of S-108 is the only move from battlefield to galaxy.
- R-234-04  Given any zoom, When the viewport is read, Then the mission canvas edges still bound the camera (R-103-02), whatever the canvas size.

Inputs: scroll or zoom input.
Outputs: viewport transform.
Open flags: none here. Whether the Sand Table of S-161 is the zoomed-out end of this one drawing or a separate drawing is decided by the prototype (Q-103-05, closed 2026-10-21).

### S-235 — The map shows the economy and its news
As a commander, I want the map to show where the economy is and the ticker to tell me what happened to it, so that I can read the war's other half at a glance.

Design decided 2026-10-02; the ticker beats are queued (VG-E1M, wired by VG-E1W) and not on main yet; four of the five beats lack a sim source. Strongpoints and slopes apply to land maps; the space-era landscape is not designed (Q-166-02).

Rules
- R-235-01  Given the map view (S-161) and the tactical view, When the economy's places are drawn, Then the economic locations, the neutral settlements, the objective, the side's base of operations, its expansions and forward works, and on land maps the strongpoints are marked (E-22 S-175, S-177; E-15).
- R-235-02  Given an environmental trouble travelling across the map, When it is drawn, Then both sides see where it is as it moves (E-15 holds what it does).
- R-235-03  Given the ticker (R-104-01), When a base is occupied, a side falls back to an expansion, an expansion is founded, a weather trouble arrives, or a strongpoint is taken or lost, Then the ticker names it; no other economy beat reaches the ticker (Westley, 2026-10-12).
- R-235-04  Given a shipment that does not arrive (E-22 S-176), When the ticker, the banners and the map are read, Then nothing on them explains why.

Inputs: economy and weather events from the tick delta.
Outputs: marks on the map view; ticker lines, T2-checkable.
Q-235-01 closed 2026-10-12, R-235-03. Q-104-02 closed 2026-10-23, R-104-01.

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Tick delta, snapshot, jump report, chronicle entries | Sim | | malformed delta drops the frame and logs |
| Live map content (obstacle, cover and interference gradients, spine, vantage and drifting nodes) | Sim, over the pipe (frames in `docs/architecture.md`) | | malformed frame drops and logs |
| Economy state, weather and ping alerts | Sim, in the tick delta | | unknown event ignored and logged |
| Mouse, keyboard | Player | | unknown keys ignored |
| Economy, doctrine, dial, request, ping and emit commands | Player | by seat and role (E-19 S-242) | a command the seat may not give is dropped and logged |
| Rebinding | Settings | | conflicts refused |

## Outputs

| Output | Observable where |
|---|---|
| Every panel and screen | Screen; T2 screenshots and click tests |
| Selection, control groups, camera | Tick delta commands; screen |
| Save files | Disk |

## Invariants

- The HUD never shows an enemy composition readout; the player infers from the world only (Westley, 2026-10-07).
- Nothing on screen lists what the commander needs, and nothing explains a shipment that did not arrive.
- The player's zoom never goes past the battlefield's map view.
- No select-all command exists.
- No loading screen between mission and galaxy and mission.
- Every screen text is free of raw field numbers.

## Scale requirements

Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is escalated): 60 fps with 1,000 units on screen and the HUD live; galaxy view at 60 fps with 250 to 400 systems, shells, and particles, with automatic quality fallback allowed (Q-106-02 closed 2026-09-28); transition never drops below 30 fps. The long-term goal of thousands of units and workers on one map (hub "Reference Hardware") is not yet a client budget; E-18 S-240 states 30 fps at 1,000 units where this epic states 60 fps [Q-240-02], and whether workers, buildings and settlement pieces count as units on screen is decided with the budgets for thousands, which stay a direction until the simulation's budgets (10,000) are reached (Westley, 2026-10-06). Measured on the minimum-spec machine (GTX 1070 class, `game_bible.md` "Reference Hardware"); on the forge's RTX 3060 the same scenes must hold about 110 fps and the transition floor about 55 fps.

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

Q-230-02, Q-231-01, Q-231-02, Q-232-03. Details in `docs/northstar/ambiguity_register.md`.

## Depends on

- E-01, E-11, E-12, E-13 (what the HUD and camera show).
- E-08, E-09, E-10 (onboarding, chronicle, briefing, debrief).
- E-15 (reinforcement structure panel).
- E-18 (visual style and animation for menus and transitions).
- E-19 (pause and exit in multiplayer; the pair's roles, S-159, S-241, S-242).
- E-22 (the economy the seat's screen and the commander's controls show: S-167 to S-181).
- E-17 (S-166, the settlements and landscape that the zoom and the map view draw).
- E-01 (the ping, going dark and reach that S-232 shows).

### S-245 — Feedback and bug reports that reach us by themselves
As a player, I want to tell the makers what I think and report a bug from inside the game or the website, so that what I hit is seen and fixed without my chasing anyone.

Design direction 2026-10-06, not scheduled. Westley, verbatim: "I want to make getting feedback a priority, I want players to be able to provide feedback on the website and have that be brought to our attention automatically (queue), I also want them to be able to put in bug/ticket reports. We already did something like this with the last version, where players were directed to a log file when a crash happened or they could press F12 to report one. The game would capture the last 5-10 seconds of the state exactly as it was happening so we could re-create the bug ourselves and see exactly what they were seeing and investigate deeper ourselves. The long term goal is to have a classification system that classifies betwee legitemate bugs and regular player complaints, slots that bug into a queue, and have a 30B model investigate/fix autonomously. The idea is to autonomize maintenence so I don't have to be present and can focus on other things."

Rules
- R-245-01  Given a player in any scene, When they press the report key (F12; the last version's `BugReportManager` autoload, zip layout, dual write to `user://logs/reports` and Downloads, clipboard copy and "where it went" popup are kept as-is), Then the game writes a report: the player's words, the scene, and a capture of the last 5 to 10 seconds of the simulation exactly as it ran, and tells the player where it went.
- R-245-02  Given the lockstep backend (E-19 S-139, S-140), When a capture is made, Then it is the save state from 5 to 10 seconds before the press plus the command log since, so the sim replays those seconds byte-identically on our machine; the window is 10 s, and the screenshot, mission metrics, crash log, client log tail, scene name and camera ride beside it (Q-245-02 closed). The last version's zip had no seed and no words field; both are added.
- R-245-03  Given a crash, When the game dies, Then the player is pointed at the log and the capture, as the last version did.
- R-245-04  Given the website, When a player leaves feedback or a report there, Then it enters the same queue as the in-game reports, and nobody has to be present for it to be received.
- R-245-05  Given the queue, When a report arrives, Then it is read by a person for the beta: a bug goes into the maintenance queue, a complaint is summarised. The later shape, a classifier and the local model of the Agora harness investigating and proposing fixes, is a post-launch idea (Westley, 2026-10-06: "a long way down the road post launch, we can just stub that idea"); Q-245-03 is deferred until then.

Inputs: the report key; the player's words; the lockstep save and command log; the website form.
Outputs: a report file with the capture; a queue entry; a classification; for bugs, an Agora task.
Open flags: Q-245-01 (the key and whether the report asks for words first), Q-245-02 (the capture window and what else it holds), Q-245-03 (what the model may land unattended).
Depends on E-19 S-139/S-140 (the lockstep backend landed 2026-10-06 gives the state and the command log), the website (`ouroboros-site`), and the Agora harness.

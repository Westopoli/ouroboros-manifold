# Multi-perspective camera: options

This document presents four options for E-16 S-103, the multi-perspective camera, against the brief in `docs/northstar/research/options/camera/brief.md`. Each is a designed mode entered from the classic RTS default view, which keeps its own auto-anchor home; two options are grounded and two are wild.

## Option A — The Angle Rack

Five fixed vantage angles — top-down, 45° overhead, horizontal, 45° upward, a single unit's shoulder — hopped between at will. Pan, zoom, and edge-scroll work as in classic view; only the angle is chosen from a memorized set, like a keyboard shortcut.

**Vignette.** At 45° overhead you spot a red cluster on the minimap. Tap 3 for horizontal: the enemy force stops being a shape and becomes a wall with visible gaps. You commit a wedge, then tap 1 to snap back to top-down and watch it land.

| Action | Input | What you see |
|---|---|---|
| Enter mode | Hold a dedicated key (e.g. V) | Camera eases to the nearest preset over about half a second |
| Switch views | Press 1–5, or Tab to cycle | A quick tween; a label names the new view |
| Steer | Classic pan, zoom, edge-scroll | Zoom clamped to the angle's range and the height floor |
| Return home | Tap V again, or Backspace | Eases back to classic pitch, framing, and anchor |

**Layers.** Top-down and 45° overhead keep the height read on the layer-color ring; horizontal shows the clearest gap. At 45° upward and unit POV, far layers can sit behind near ones, so ring color carries more of the read.

Honors: section 8's mode override; R-103-02; R-103-04; the height floor in every angle; the observing stance. Strains: R-103-01's literal "no camera modes"; R-010's height-read promise at the two occluding angles.

Prior art: Total War's unit-cam toggle, VERIFIED — [Better Battle Camera guide](https://steamcommunity.com/sharedfiles/filedetails/?id=2756001869). StarCraft II's observer first-person camera, VERIFIED — [Liquipedia](https://liquipedia.net/starcraft2/Replay_Features).

Tradeoffs: memorable, but an angle between horizontal and 45° upward has none. Unit POV sharpens one engagement while blinding you to the rest of the field.

Diagram: diagrams/option-a.svg

## Option B — The Anchor Ring

One continuous crane in place of fixed angles: hold a key and drag anywhere from overhead to eye level, at any distance the height floor allows, and drop personal bookmarks worth returning to.

**Vignette.** Scouting before the push, you crane low along the river, then swing up behind your siege line and save the spot with Ctrl+Shift+2. The gate comes under fire; Ctrl+2 glides you straight back.

| Action | Input | What you see |
|---|---|---|
| Enter mode | Hold a modifier, or a dedicated toggle | Camera unlocks and free-cranes from its current framing |
| Switch views | Ctrl+number recalls a saved anchor; brackets step the list | A third-second glide to the anchor's framing |
| Steer | Right-drag orbits; scroll changes distance; left-drag pans | Continuous motion, no snapping |
| Set an anchor | Ctrl+Shift+number, at any framing | A brief flash and a numbered flag |
| Return home | Double-tap the mode key, or Home | Glides to classic pitch and default anchor |

**Layers.** Continuous pitch dials exactly how much vertical separation to see; height reads as height at any pitch but true top-down, where ring color carries it.

Honors: R-103-01's free-steering spirit, carried into the mode; R-103-02; R-103-04; the height floor as a continuous limit. Strains: bookmarks are the player's to set — a fresh mission has none saved, so the payoff arrives only after investment.

Prior art: Planetary Annihilation's camera anchors, REPORTED — [PA guide](https://planetaryannihilation.com/guides/controls-and-the-user-interface/). Company of Heroes' double-tap camera recall, REPORTED — [CoH2 discussion](https://steamcommunity.com/app/231430/discussions/0/3057364785116261931/). Supreme Commander's continuous strategic zoom, VERIFIED — [Wikipedia](https://en.wikipedia.org/wiki/Supreme_Commander_(video_game)).

Tradeoffs: exactly the angle you want, every time, but a player who never bookmarks gets a free camera and nothing more.

Diagram: diagrams/option-b.svg

## Option C — Layer Peel (wild)

The five layers separate like a fanned hand of cards around your focus point. A threat two layers from where you're looking is no longer hidden behind height — it sits on its own card, beside you.

**Vignette.** Suspecting a raid above your siege line, you hold L: the stack peels into five translucent fanned planes. One scroll brings the plane above into focus, brightening as the rest dim — a raiding party sits there, visible where fog already allows it. Release L; the cards close to true height, and you commit a spoiling attack upward.

| Action | Input | What you see |
|---|---|---|
| Enter mode | Hold or toggle a key (e.g. L) | The five layers fan open around your focus over about half a second |
| Switch views | Scroll or arrow keys walk focus between planes | The focused plane brightens and enlarges; others dim but stay visible |
| Steer | Pan and zoom move the whole fan together | The fan holds its shape; no independent per-plane orbit |
| Return home | Release or tap the key again | Planes slide to true stacked height, then the prior angle returns |

**Layers.** All five are visible at once, nothing occluding anything, with a thin ghost line marking each plane's true height. Fog and cross-layer vision are untouched — a hidden layer stays hidden on its own plane; the peel changes only how you're looking, not what you're allowed to see.

Honors: R-103-04, by showing every layer without moving to one; the observing stance; the height floor, applied to the fan's overall height; R-103-02. Strains: leans on section 8's mode override, since fanning the layers apart is itself a designed camera mode; with no pause, holding the peel open costs a compact read of the whole fight.

Prior art (mechanic origin, not a game): interactive exploded-view diagrams, a graphics/HCI technique, REPORTED — [Li et al., ACM SIGGRAPH 2008](https://dl.acm.org/doi/10.1145/1360612.1360700). Among shipped RTS or tactics games: none found.

Tradeoffs: a complete layer read costs a compact one — attention splits five ways, and a shot at the wrong plane while fanned is a shot at nothing.

Diagram: diagrams/option-c.svg

## Option D — Ghost Walk (wild)

An intangible eye released into the fight at human height. It has no body, cannot act or be targeted, and cannot ride or become a unit — it only watches — but climbs or drops between layers exactly as a transitioning unit would, so the layer gap you order units to cross is one you can feel.

**Vignette.** Your center is holding but you don't trust it. You hold G and the camera falls into the crowd at your selection — shoulder height, closer than any readout. Holding the layer-up gesture, the view climbs with a transitioning unit's own slow rise, until you're level with a second force massing one layer up. Releasing G sends the eye back through the layers into the classic frame.

| Action | Input | What you see |
|---|---|---|
| Enter mode | Hold a dedicated key (e.g. G) | Camera falls from the classic frame into the crowd at screen-center |
| Switch views | Hold a modifier and scroll, or Page Up/Down, one layer per step | The same climb-or-drop animation a transitioning unit plays |
| Steer | Mouse-look and free movement, no collision | Nothing blocks motion; you pass through what a unit could not |
| Return home | Release G, or Esc | Rises through the intervening layers, then reassembles into classic pitch |

**Layers.** Only the layer you stand on is visible at full detail — the sharpest version of the promise that an unwatched layer is a real threat, since the other four stay invisible except through the same fog and vision rules any observer already has.

Honors: "you are in it, not a god game"; the observing stance's letter, since the eye cannot act, be targeted, or possess a unit; the height floor, held per layer; positional thinking, since "where" is unavoidable. Strains: R-103-02's canvas bound holds, but a large battlefield at human height is impractical to cross without the return-home glide; passing through terrain a unit could not breaks, here alone, the rule that blocked terrain reads the same for everyone.

Prior art: none found for the mechanic as a whole. Thematic precedent only: the Battle School observation deck framing, REPORTED — `docs/legacy/topics/delegated_command_precedents.md` ("3D volumetric tactical space," non-load-bearing), and "Ender reading the battle from many angles" (`docs/bible_history/bible_2_00_design_vision.md:85`).

Tradeoffs: a visceral sense of scale and threat, at the cost of the overview — down in it you cannot see the rest of the fight, and getting back costs a real trip, not a tap.

Diagram: diagrams/option-d.svg

## Findings

- R-103-01's literal text ("no camera modes") cannot be honored by any option — every option here is a mode. Section 8 supersedes this for the classic view and the designed mode, but the rule's own wording still needs the rewrite section 8 promises once a pick lands.
- Whether Layer Peel's fanned focus and the HUD layer strip's focus are the same control is undecided. Q-009-01 settles that focus is purely visual (other layers dim slightly, commands and box-select unaffected), but not whether the peel's plane-focus and the strip's layer-focus are one control or two.
- Unit POV (brief section 6) was left unanswered. Only Option A carries it, and this document can only note that orders keep working since camera and selection are decoupled by R-103-04 — whether it is for commanding or only for reading one engagement is not settled here.
- The height floor is described as "the height the player was at," but nothing says whether it is remembered per view or shared across the camera. Every control table above assumes it is shared, since the brief does not distinguish; this is a finding, not a decision.

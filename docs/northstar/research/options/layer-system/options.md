# Layer system look and feel: options

These four options show how the five-layer stack, a unit's own layer marker, the HUD strip, and the sensor pulse could read on a commander's screen, at a vertical scale each option sets for its own stated reason. None ranks or recommends.

## Option A — Drafting Table

Every unit carries a small boxed lattice standing on end around its footprint, one thin tier per layer, brightest on the tier matching its own height. You read a unit's layer by which tier of its lattice glows, and the terrain behind it stays fully visible through the sparse lines.

*You scan a line of units on a ridge; each one's lattice glows on a different rung, so you can tell at a glance who shares a layer before clicking anything. You box three, tap down; a hollow diamond appears low in each lattice, then fills as the descent starts. The bodies ease downward, rings swapping color only the instant each one lands. You tap the strip one layer up; everything off that layer dims just enough to let the units that matter jump back out.*

**Stack at normal distance.** No floor plane anywhere — only the small lattices standing on each unit. A slope full of units reads as short lattices at different heights, like survey stakes.

**A unit changing height.** The unit's own tier brightens first, the body eases upward over its transition time, and the ring swaps color only the instant the unit is actually standing on the new layer.

**Grid, ring, waypoint.** The own tier holds near 50 percent strength, neighbors 10 to 20 percent, the far two 5 percent. A hollow diamond marks the target tier and fills in once the transfer starts.

**HUD strip and focus.** A vertical five-slot strip, one swatch per layer; the focused slot is full strength, the rest — and every unit's off-focus tiers — dim to about 80 percent.

**Pulse reveal and fade.** Every revealed unit's full lattice lights at full brightness for the pulse, then eases back to its normal falloff over about half a second rather than cutting off.

**Vertical scale.** In the Settled Reach the tiers sit far apart, since open space needs the spacing itself to carry scale; on a land era before flight the tiers compress into hillside terraces a few meters apart.

**Honors:** five layers; grid on the unit, never a plane; the falloff percentages; a waypoint icon; no fixed spacing; strip focus dims slightly. **Strains:** none beyond the shared tensions in Findings.

**Prior art:** Unreal Engine's and AutoCAD's local translation gizmos and 3D navigation frames, which read an object's position without a full ground plane (VERIFIED — [Unreal](https://dev.epicgames.com/documentation/unreal-engine/transforming-actors-in-unreal-engine), [AutoCAD](https://www.autodesk.com/blogs/autocad/autocad-3d-navigation-and-visualization-tuesday-tips-with-frank/)); StarCraft 2's high-ground vision block (VERIFIED — [Liquipedia](https://liquipedia.net/starcraft2/High_Ground_and_Low_Ground)); the existing two-layer prototype's ring and smooth-not-snapped rise (VERIFIED, internal — `docs/northstar/research/mockups/layers/pass1/`).

**Tradeoffs.** Legible and conventional; near a cluster the many small lattices can compete with each other for attention.

Diagram: diagrams/option-a.svg

## Option B — Terrace Reading

Each unit's grid tiers are flat discs that tilt to match the real slope under that tier's height, so the unit's own disc sits flush with the ground and the other four rake in parallel above and below it. Same falloff idea as Option A, but the shape reports what the terrain is doing.

*You walk a group up a switchback cut into a cliff. Each unit's disc-stack tilts more with every terrace crossed — you read the climb through the changing rake before the bodies even finish moving. Near the top you tap the strip; the lower notches fade toward the color of the stone itself rather than going flatly transparent, and the ground stays legible under everything you're not focused on.*

**Stack at normal distance.** The tilted discs echo the terrace lines already cut into the terrain art instead of adding a second geometry on top of it.

**A unit changing height.** The body climbs its own disc stack as in Option A; the disc's lean also visibly changes as it crosses from one terrace's slope to the next.

**Grid, ring, waypoint.** Same 50/10–20/5 percent falloff. The waypoint is a small flag planted flat on the target disc, angled to that disc's own slope.

**HUD strip and focus.** The strip is a small terrain cross-section with five notches, the focused one lit; focus fades the other discs toward the ground's own color, not to gray.

**Pulse reveal and fade.** The pulse lights each unit's disc stack bottom to top in a quick sweep, then fades back down the same way, tier by tier.

**Vertical scale.** Without real slope to hug, the Settled Reach's discs flatten toward a level lattice, spaced by deck; on land the tilt is the whole point, so spacing follows the mountain's own terrace height.

**Honors:** the same core list as A; spacing here is read directly off the terrain. **Strains:** on flat ground or in space the tilt cue disappears and the option quietly degrades toward Option A.

**Prior art:** the landscape phase's own terraced cliffs and elevation-first generator, which this option assumes (VERIFIED, internal — `docs/northstar/research/landscape_design/mockup/pass3/`); Halo Wars's camera holding constant height above sloped ground, per Westley's own account and general community description (REPORTED); Baldur's Gate 3's floor-peeling for multi-story buildings (REPORTED — [Steam discussion](https://steamcommunity.com/app/1086940/discussions/0/3819669231700210838/), no confirmed implementation detail found).

**Tradeoffs.** Reads clearly where terrain has drama; on flat ground or in space the tilt cue vanishes, and two nearby units on uneven ground can show slightly different disc angles.

Diagram: diagrams/option-b.svg

## Option C — Sonar Bloom (wild)

No static shape. Each layer height near a unit carries a soft ring that breathes outward on a slow rhythm, strongest and fastest at the unit's own height, fainter and slower at the layers nearby. You read a layer by which height's ring is brightest and quickest, not by comparing a fixed shape — no shipped strategy game reads layer membership this way.

*You pan the front line and the whole picture seems to breathe — soft rings pulsing at different heights. You order a unit up a layer; a new ring starts weak at the target height while the old one slows and fades, the two ripples crossing as the body climbs between them. You trigger a pulse; for two seconds the hidden height wakes up bright and fast, then settles back to a slow quiet glow as the effect drains away.*

**Stack at normal distance.** Dozens of soft, breathing rings at different heights read as a rhythm of light rather than a blueprint.

**A unit changing height.** A new ring forms at the target height and grows stronger as the body climbs to meet it, while the old ring fades over the same span.

**Grid, ring, waypoint.** The "grid" is brightness and rhythm: a fast full pulse at 50 percent on the own layer, a slow faint echo at 10 to 20 percent one layer off, a bare shimmer at 5 percent two off. The waypoint is a single ring frozen at the target height until the transfer starts, then it joins the rhythm.

**HUD strip and focus.** Five small ring icons stacked vertically, each animating at its own tier's rhythm; the focused slot beats faster and brighter, the rest slow and soften slightly.

**Pulse reveal and fade.** Every hidden layer's rings flash bright and fast for the pulse's duration, then the rhythm slows and brightness bleeds away over the fade window rather than cutting off.

**Vertical scale.** Scale is how far a ring travels before fading. In the Settled Reach the rings travel far, matching huge deck gaps; on land they travel a short, tight distance between hillside terraces.

**Honors:** grid-around-the-unit as a ring, never a plane; the falloff percentages as brightness and rhythm; the waypoint icon; per-era scale; slight dimming on focus. **Strains:** the brief's named register (AutoCAD, Unreal Engine, 3D visualization tools) is static lattices; a breathing ring keeps the falloff information but trades away the literal lattice look — the option's honest departure and the reason it is wild.

**Prior art:** none shipped for layer legibility in this ring-and-rhythm form (none / AMBIGUOUS per the brief's own framing); the general sensor-sweep register appears in naval instrument displays and in strategy games rendering detection rings, such as Nebulous: Fleet Command (REPORTED, general genre knowledge, not independently verified this pass).

**Tradeoffs.** Visually distinctive and close to the bible's "elegiac, alive" tone; constant animation across fifty units risks working against "visually quiet," and reads harder for a player who parses color faster than rhythm.

Diagram: diagrams/option-c.svg

## Option D — Floor Spindle (wild)

Every unit plants a thin rod beside itself, threaded with five small discs stacked bottom to top like the five layers of the world. The disc at the unit's own height glows and sits slightly proud of the rod; the rest sit small and dim — a literal floor indicator, read the way a lift's call panel is read. No RTS attaches a persistent physical dial to every unit like this.

*A line of units on a ridge looks like a row of tiny five-rung ladders, each with one lit rung at a different height — you read the pattern across the group before resolving any single unit. You toggle one down a layer; its target rung gets an outline and a chevron before anything moves, then the lit disc slides down the rod as the body descends beside it, locked together. You pulse a suspected position; a whole spindle blinks into being, then fades from its top rung down, last light landing on the true home disc.*

**Stack at normal distance.** A ridge full of units looks like small five-rung ladders; the spindle is a thin line and five small discs, nothing more, so the terrain stays clear.

**A unit changing height.** The lit disc slides up or down the rod to its new rung over the transition time while the body rises alongside it in lockstep.

**Grid, ring, waypoint.** The "grid" is the discs' brightness ladder: home disc near 50 percent, neighbors 10 to 20 percent, far discs 5 percent. The waypoint is the target disc gaining an outline and a chevron the moment it's toggled, before it moves — grown out of the existing dial rather than added on top.

**HUD strip and focus.** The same five-rung ladder drawn large at the screen edge, shared by the whole army; the focused rung is bright, the rest dim slightly, and clicking a rung is the same gesture as reading one on a unit.

**Pulse reveal and fade.** Every hidden unit's spindle appears for the reveal window, then fades from the top rung down, last light landing on the home disc right before it disappears — the fade hints which layer the unit was on.

**Vertical scale.** The rod's real height is the whole lever: tall in the Settled Reach so five discs read like an elevator shaft across a huge reach; knee-height on a land era with discs almost touching, since a tall rod on a hillside would read as a mistake.

**Honors:** grid-around-the-unit as a literal instrument, never a plane; the waypoint icon grown from the same object; falloff as disc brightness; per-era scale via rod height; slight dimming on the strip. **Strains:** the brief's grid register implies a lattice or plane; a rod with five discs is far sparser than a "grid" — the option's honest departure and the reason it is wild.

**Prior art:** no shipped RTS uses a per-unit physical floor indicator like this (none, per the brief's framing); the floor/elevator-panel convention is universal real-world signage, not a game citation (VERIFIED as a real-world convention).

**Tradeoffs.** A single-glance read of "what layer, which way," borrowing a convention every player already knows; the extra geometry beside every unit adds real on-screen clutter in a large battle.

Diagram: diagrams/option-d.svg

## Findings

Every fixed constraint in sections 4 and 8 of the brief is honorable by at least one option above; two tensions stay open rather than solved.

First, S-010's demand that height "reads as height" assumes a camera oblique enough to show vertical offset, but E-16 R-103-03 fixes the launch camera as the top-down interim. The two-layer prototype already departed from strict top-down (a 60-degree pitch) to clear R-010-03's five-percent bar, and every diagram here assumes a similarly oblique view for the same reason. None of the four options resolves this; each assumes whatever pitch its height rule needs, and the actual answer belongs to the camera options pass (`../camera/`), not this one.

Second, the brief's freedom on vertical scale ("large in space, small on land") pulls against "a grid around each unit, never a whole-layer plane." At a space era's largest candidate spacings a tier-to-tier gap can run into the thousands of world units, and a per-unit marker tall enough to visibly bridge that gap starts to look less like a personal instrument and more like a floor plane by sheer size. All four options answer this by sizing each marker to the unit itself rather than stretching it to fill the gap, so it states "here is my layer" without ever drawing the layer — a design choice, not a fully solved constraint: at very large spacing a lone marker can still read as an isolated mark with no visual link to its neighbors.

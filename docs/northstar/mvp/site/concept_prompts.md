# Concept-art and animation prompts for the site narrative

One prompt per *concept moment* in `narrative.md`, in the order the home page tells the story. This is the hand-off for the art pass: Westley generates by hand in the Gemini app (images with Nano Banana Pro, video with the app's video model), attaching the reference images named per prompt. Outputs land in `ouroboros-site/public/art/<beat-slug>/`. The site overlays any labels or captions itself — nothing textual is ever baked into an image.

The choices fixed on 2026-09-15, which every prompt below obeys:

- **Medium.** Static images as the baseline, plus five animations (beats 1, 3a-B, 4, 5, 6).
- **Register.** *Looks like the game* — the low-poly Art of Rally register in the style block below. These are mockups of the game at its best, not cinematic key art in a different style.
- **World-only.** No HUD, no command screens, no UI chrome in any image. Where a beat is about an idea the UI would show (an objective, a deadline, two commanders), the image carries it in the world instead.
- **No forced cast.** The six unit types appear where a scene needs ships; they are not a required recurring motif.
- **No text in any image.** Diagrams use shapes, wedges, and arrows only; the site adds the words.

## Shared style block — paste at the top of every prompt

> Low-poly, blocky, toy-like register — more blocky than Age of Empires Online, flatter and warmer than photoreal (Art of Rally's flat low-detail look). Clean, readable silhouettes, one per unit type, no fussy detail. Cinematic sense of scale behind the action when a scene calls for background (huge distant objects, busy but readable). Combat reads as mass and weight, not sparse skirmishers, when a scene shows combat. No text anywhere in the image. No existing-IP names, logos, insignia, or ship/character designs — thematic inspiration only, never copied content.

## Shared negative list — paste at the bottom of every prompt

> No text, labels, numbers, or UI chrome baked into the image. No photoreal detail or realistic lighting. No existing-franchise ships, uniforms, insignia, or characters (Star Wars, Halo, etc. — inspiration only). No human faces as the focal subject. No price tags, store badges, or review-quote overlays. No HUD, no command screens, no menus.

## Reference images

Attach per prompt as listed (up to 14 per generation). Paths are in the `ouroboros-manifold` repo unless noted.

- **Register:** `docs/bible/references/E-18/E-18-1.png`, `E-18-2.png` — the two Age of Empires Online shots the register is built from.
- **The game's own galaxy view (real):** `docs/bible/references/E-09/time_jump_galaxy_and_scroll.png` — captured from the legacy client: faction territory shells around system nodes, gold lane lines, a polar grid, a nebula star field, the chronicle scroll on the right.
- **Unit renders:** screenshot the Raider, Interceptor, and Vanguard from the live demo at `https://ouroboros-site.fly.dev/layers/` (orbit and capture each). Warden, Bombard, and Bastion have GLBs under `assets/eras/settled_reach/units/` — capture in Godot or from `docs/blender_stuff/the-settled-reach/` if a scene needs them.
- **Scale and battles:** `docs/bible/references/E-13/E-13.png` (Halo Wars grouping), `docs/bible/references/E-17/E-17-1.png` (AoE Online).

---

## Beat 1 — Hero: the task force dwarfed by scale

**Output:** `public/art/hero/` · **Medium:** video, ~8–12 s, loopable · **References:** E-18-1, E-18-2, one or two unit renders.

> [style block]
> A single continuous camera push-in, no cuts. Open on a galaxy-scale strategic map: dozens of small star systems as glowing nodes joined by thin lit route lines against a deep nebula star field, some nodes bright and thriving, others dim. The camera pushes steadily toward one node; the map resolves into a region, then a planet's surface, then a low-poly landscape, and finally settles low and close behind a handful of blocky low-poly ships in tight formation — a task force of six or fewer — with an enormous, indifferent distant object filling the sky behind them. The scale contrast is the point: the force is small; the world is vast. Warm, flat lighting; slow, weighty camera; nothing moves faster than the camera. End held on the formation.
> [negative list]

*Static fallback:* the final frame alone — the formation, small, against the huge distant object.

## Beat 2 — Commander, not king: a force, an objective, a deadline

**Output:** `public/art/commander/` · **Medium:** image · **References:** E-18-1, E-18-2, unit renders, E-13.

> [style block]
> A low-poly task force of a handful of blocky ships holding position in the foreground on open terrain — this is everything the commander has. In the middle distance, clearly visible and clearly the objective, a single lit structure or held position on high ground that the force must reach. The deadline is in the light: a low sun near the horizon, long shadows, the sky closing toward dusk — time running out, told by the world and nothing else. No base, no buildings of the player's own, no economy, no interface. Warm, flat, readable; the eye goes force → objective → falling light.
> [negative list]

*Variant:* the same composition at night with a narrowing band of light on the horizon, for a tenser read.

## Beat 3a — The landscape engine and the sense of scale (three pieces)

### 3a-A · Wide generated map (image)

**Output:** `public/art/landscape/` · **References:** E-18-1, E-18-2, E-17-1, E-13.

> [style block]
> A wide, high top-down-oblique view of a large procedurally generated low-poly battlefield, readable at a glance: a narrow chokepoint between two rock masses, a ridge of high ground commanding a low approach, open flats, and a winding route through. Two small groups of blocky units are visible only as tiny clusters, purely to show scale — the terrain is the subject. Elevation reads by shape and by flat color steps, not by detail. The map should feel designed by an intelligence, not scattered: every feature offers or denies a position.
> [negative list]

### 3a-B · The terrain settling into a map (video)

**Output:** `public/art/landscape/` · **Medium:** video, ~8 s · **References:** E-18-1, E-18-2.

> [style block]
> A time-lapse of a battlefield being generated. Start on a flat, featureless low-poly plane. Blocky terrain rises and settles into place in clean stages — rock masses lift, a ridge forms, a chokepoint narrows between two masses, a low approach cuts through, flats level out — each feature snapping into a deliberate strategic position as if placed by a mind. Flat color steps mark elevation as it appears. End on the finished map from a high oblique view, still and readable. Motion is crisp and geometric, not organic or erosive; no particles, no dust.
> [negative list]

### 3a-C · Cinematic vista, huge background object (image)

**Output:** `public/art/landscape/` · **References:** E-18-1, E-18-2, E-13, unit renders.

> [style block]
> A low, wide vista across a low-poly landscape toward a single enormous distant object — a shattered planetary ring, a derelict megastructure, or a moon far too close — dominating the sky and dwarfing everything. In the foreground, a few blocky ships cross the terrain, tiny against it. The landscape has the same designed, readable strategic shape as a battlefield: a ridge, a pass, an approach. Cinematic scale, flat warm lighting, busy but readable.
> [negative list]

## Beat 3b — Layers and vision

**No art.** The live demo at `/layers/` already shows this better than a still could. Skip.

## Beat 4 — How the units balance: geometry of position (diagram set)

Rock-paper-scissors shown as *positional geometry*, never as a literal fight, and expanded past balance into strategic depth — the chess of it. No unit models; low-poly wedges, blocks, and arrows stand in for forces. No labels (the site adds them). Three pieces: a legend, an asymmetric diagram, and the showpiece animation.

### 4-A · The three relationships (image, legend)

**Output:** `public/art/balance/` · **References:** none needed; E-18-1 for palette.

> [style block]
> A clean geometric diagram on a flat ground plane, three panels side by side, each showing one relationship between two low-poly shapes: a small fast wedge sweeping AROUND a large slow block (a flank); a large heavy block driving THROUGH a thin line of shapes (a crush); a firm wall of blocks that a small wedge strikes and cannot pass, its motion absorbed and turned (a hold). Motion shown by clean arrows only. Three shape-languages: small and fast, large and heavy, solid and firm. Flat warm colors, no text, no labels.
> [negative list]

### 4-B · One side reads the ground, one does not (image)

**Output:** `public/art/balance/` · **References:** 3a-A output as the terrain, E-18-1.

> [style block]
> A top-down geometric diagram on a low-poly battlefield with a chokepoint and a ridge of high ground. On one side, a force drawn as an undifferentiated blob of blocks parked in the open low approach. On the other, a force arranged with intent: heavy blocks holding the ridge above, a fast wedge already sweeping wide around the blob's flank, a firm wall sealing the chokepoint behind it. Clean arrows show the sweep and the seal closing. The geometry alone makes the outcome obvious — the blob is surrounded before anything happens. No units, no text; shapes and arrows only.
> [negative list]

### 4-C · Both sides read the ground — the chess of it (video, showpiece)

**Output:** `public/art/balance/` · **Medium:** video, ~15–20 s · **References:** 3a-A output, E-18-1.

> [style block]
> A top-down geometric animation on a low-poly battlefield shown as a stack of stepped elevation levels, both forces drawn as clean blocks and wedges, both positioned with intent. The animation plays a sequence of moves and answers like a chess game, each move drawn with a clean arrow before the shapes execute it: the heavy blocks on the high upper level begin to pull back; as the opposing heavy blocks advance to follow, fast wedges that were waiting on the lowest level sweep in underneath and around their flank. Then a second exchange: a group of wedges feints a charge at a firm wall, breaks off, and retreats — and the pursuing blocks run into a second force that had been sitting hidden behind terrain. At each decision point, briefly ghost two or three alternative arrows the moving side could have chosen, then commit to one and let the others fade, so the viewer sees options, not just events. No contact is ever shown; the shapes never touch — the geometry of who is where, and who could have gone where, is the whole story. Slow, deliberate pacing; flat warm colors; no text.
> [negative list]

*Why no units and no contact:* the beat is about the strategic depth of positioning, not damage. Shapes keep it readable as thinking.

## Beat 5 — The galaxy is alive (real capture + mockups + time-lapse)

Three sources, in this order.

### 5-A · The real prototype screenshot (no generation)

Use `docs/bible/references/E-09/time_jump_galaxy_and_scroll.png` — captured from the game's own client. Crop to the galaxy view (the left two-thirds; drop the chronicle scroll and the SKIP button). This is the one image on the site that *is* the game today; the narrative's "targets, not a finished game" framing covers the mockups beside it.

### 5-B · Polished mockups of the same view (image, 2–3 variants)

**Output:** `public/art/galaxy/` · **References:** **the real screenshot above (attach it first)**, E-18-1, E-18-2.

> [style block]
> An evolved, polished version of the attached galaxy map, keeping its structure exactly: system nodes joined by thin gold lane lines on a polar grid over a nebula star field, faction territories as translucent colored shells around their systems that overlap and glow where two factions touch. Push the look: nodes bright and thriving in some regions, dim and contested in others; the shells reading as living pressure, not flat fills; depth and atmosphere in the nebula; the whole thing composed as a beautiful living network rather than a chart. Same layout as the reference — this is the same view, finished. No text, no UI, no scroll panel.
> [negative list]

### 5-C · Time-lapse — the galaxy moves without you (video)

**Output:** `public/art/galaxy/` · **Medium:** video, ~10–15 s, loopable · **References:** the real screenshot, one 5-B output.

> [style block]
> A time-lapse of the attached galaxy map over decades, camera fixed. Faction territory shells breathe and shift: one faction's color spreads across neighboring systems, brightens, then thins and recedes as another color pushes in; lane lines light up and go dark as routes open and close; a few systems flare and dim. No single event is the focus — it is the slow tide of many factions rising and falling on their own, with no player's hand visible anywhere. Smooth, continuous, unhurried; ends on a map noticeably different from where it began.
> [negative list]

*Alternative to generating 5-C:* the client's galaxy view already animates territory change — a real screen capture of that (the open slot in the E-09 reference notes) can stand in for, or sit beside, the generated version.

## Beat 6 — You return as someone new (image + animation)

### 6-A · The same region, decades apart (image)

**Output:** `public/art/generations/` · **References:** E-18-1, E-18-2, one 3a-A output for terrain language.

> [style block]
> Two views of the same low-poly region side by side, the terrain identical in both. Left: fresh construction, clean new structures, a strong garrison of blocky ships, one faction's color on everything, morning light. Right, decades later: battle scars in the ground, structures rebuilt in a different style over the old footprints, a different faction's color on the walls and ships, some of the old garrison's wreckage still there, evening light. Same place, changed by time — the viewer should recognize it instantly and feel the years.
> [negative list]

### 6-B · The region morphs as history is written (video)

**Output:** `public/art/generations/` · **Medium:** video, ~10 s · **References:** the 6-A output, the real E-09 screenshot for the scroll's shape.

> [style block]
> A slow crossfade-morph of one low-poly region across decades: structures rise, take scars, fall, are rebuilt in a new style; the faction color on the walls and ships changes twice; the light moves from morning to evening. Beside the region, a tall parchment-like chronicle scroll advances in step with the changes — but its entries are rendered only as abstract, illegible serif-like strokes and small flat icons (a battle, a treaty, a founding), never real letters or words, each new entry appearing as the region changes. The pairing is the point: the world changes, and the record grows. Warm, elegiac, unhurried.
> [negative list]

*The site overlays the real chronicle text on top of this; the strokes in the video are placeholders for it.*

## Beat 7 — The crescendo: many eras, one campaign, with your friends (image)

**Output:** `public/art/eras/` · **References:** E-18-1, E-18-2, unit renders, E-13.

> [style block]
> One shared low-poly map with a single, readable strategic layout — a ridge, a pass, an approach. On it, two task forces from two different eras meeting, each read entirely from the dress of its ships and structures: one near-future spacefaring force, blocky sleek hulls and clean lit lines; the other from a distinctly different era of the same world, a different silhouette language and material feel, unmistakably another age. Same terrain, same strategic shape, two eras sharing it — two friends' forces on one field. Composed so the eye reads "same map, two times" at once. No interface, no text.
> [negative list]

*Variant:* the same map rendered twice side by side, each fully in one era's dress, for a cleaner "same structure, different age" read (the `narrative.md` alternate).

## Beat 8 — Join the playtest

No art.

---

## Discipline

Generated images are concept art for a target the game is being built toward, not screenshots — the only image on the site that is the game today is beat 5-A, and it is labeled as a prototype. Never caption a generated image as a capture. The one hard rule applies to every generation: no existing-IP ships, insignia, characters, or logos. Read `narrative.md` for the sequence these serve and `../distinctiveness.md` for the bets behind them; `prompt_kit.md`'s per-offer lines cover the `/offers/` pages, which this file does not.

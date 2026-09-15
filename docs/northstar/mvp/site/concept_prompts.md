# Concept-art and animation prompts for the site narrative

One prompt per *concept moment* in `narrative.md`, in the order the home page tells the story. The five animation prompts each carry their own **Context** block inside the paste, because Westley runs them in parallel across fresh chats that have no other background — paste context, style block, prompt, and negative list together as one message. This is the hand-off for the art pass: Westley generates by hand in the Gemini app (images with Nano Banana Pro, video with the app's video model), attaching the reference images named per prompt. Outputs land in `ouroboros-site/public/art/<beat-slug>/`. The site overlays any labels or captions itself — nothing textual is ever baked into an image.

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

> **Context (this chat has no other background):** This is for the website of *Ouroboros Manifold*, a real-time strategy game in which you play a commander — not a king or an emperor — given one small task force inside a vast galaxy that keeps moving on its own. This animation is the site's opening hero. Its one job is to make the viewer feel the scale gap: the galaxy is enormous and indifferent, and the force you command is tiny. It should end on the task force, so the viewer's attention lands on the player's actual place in this world.
>
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

> **Context (this chat has no other background):** *Ouroboros Manifold* is a real-time strategy game whose battlefields are generated by an intelligent landscaping system: terrain is designed to create strategic depth — chokepoints, high ground, approaches — and reading the ground is what wins fights. This animation shows a map being generated. The goal is to make the viewer feel the terrain is placed with intent, like a puzzle designer laying out a board rather than scattered at random: every feature that appears should look like it offers or denies a position.
>
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

### 4-C · Both sides read the ground — the trap and the counter-flank (video, showpiece)

**Output:** `public/art/balance/` · **Medium:** video, ~24 s · **References:** the existing *Beat 4-C Blueprint* PDF, 3a-A output, E-18-1.

**Status.** Claude Design has produced a phase-1 blueprint (*Beat 4C Blueprint.pdf*, site repo): a flat top-down plan with a fixed shape language (flank / crush / hold), a notation (committed move, dropped option, hidden force, three elevation levels), a board at rest, six moves in 19 s, and phase-2 rules. **Keep all of that scaffolding.** What changes is the *play*: the current move order is not what two competent players would do, and it ignores unit type. Below is the modification brief, then the phase-2 prompt.

#### Modification brief for Claude Design — change the play, keep the plan

**Keep verbatim:** the shape language panels; the notation; the board's four features (top step, chokepoint, south-east rock mass, west low ramp); three elevation levels; the arrow rules (options ghost together, two fade as one draws solid, shapes move only after the arrow finishes); overhead still camera with slow drift; no shape ever touches; no damage drawn as contact; no text in frame; the closing hold.

**Add to the shape language — role and counter.** The three shapes are unit *roles*, and each beats one of the others. Make this explicit in the legend and let it drive every move:
- **Wedge = Strike** (fast). Flanks Siege.
- **Heavy block = Siege** (slow, hits hard). Crushes Line.
- **Wall = Line** (firm). Absorbs Strike.
So: wedge beats heavy block, heavy block beats wall, wall beats wedge. A player moves a shape toward the shape it beats and away from the shape that beats it; every committed arrow in the sequence should be explainable by that rule.

**Add a vision rule.** A force sees one elevation level below it at about half its normal reach, and two levels below it almost not at all. Draw a force *hollow* whenever the opposing side cannot see it. Gold on the top step can see ink on the middle step; ink on the middle step can see only what gold puts at the crest lip, not what gold holds set back or behind the rock; anything on the lowest level is invisible to gold on top.

**Fix the two things that break the current sequence.**
1. *Gold gives up the height for nothing.* A competent player never cedes high ground unless it is bait. In the new play gold never leaves the height; it *shows* the height, with the wrong units, on purpose.
2. *Forces walk past each other unengaged* (moves 1→2). That does not happen at a high level. In the new play the two main bodies are engaged at range across the ramp from move 3 on, and every flank arrives on a target it counters.

**Re-cast the pieces.** The hidden force behind the south-east rock is now **gold's** (its wedges — the trap), not ink's reserve. Ink's wedges start on the **lowest level, west, by the low ramp** — ink's flank. Gold's wall now stands at the crest lip; gold's heavy blocks sit set back from the lip, angled to cover the ramp (gold's fire base). Ink's heavy blocks are its main body on the middle step, facing the ramp. The chokepoint stays sealed and is the "blocker" ink's wedges go *around*, on the bottom of the frame.

**Replace the six moves with these seven panels (~24 s).**

- **Rest · 0.0–3.0 — the board.** Gold on the top step: a wall (Line) at the crest lip, two heavy blocks (Siege) set back covering the ramp, wedges (Strike) hollow behind the south-east rock, one move from the crest's flank. Ink on the middle step: heavy blocks (Siege) as the main body facing the ramp; wedges (Strike) hollow on the lowest level, west. Hold so the viewer reads who can see what.
- **1 · 3.0–6.0 — the bait.** Gold's wall steps forward to the lip and makes itself obvious. Ghost gold's alternatives — keep everything out of sight; bring the heavy blocks forward instead — then commit the wall. From below, ink now sees a Line force exposed on high ground, and Siege crushes Line: the push up the ramp looks correct. That is the point.
- **2 · 6.0–9.5 — ink reads it, and splits.** Ink's heavy blocks begin the climb (ghost the alternatives: shell from below; decline). *At the same moment*, the competent move: ink's wedges peel west along the lowest level and around the chokepoint blockers — two levels below gold, drawn hollow, unseen. Two intentions from one player, drawn as two arrows committing together.
- **3 · 9.5–13.0 — the climb under fire.** Ink's heavy blocks climb the ramp, slow and exposed on the step. Gold's set-back heavy blocks fire down the ramp — drawn as arcs, never contact — and gold's wall holds the lip just long enough. Ink's wedges keep to the low route under the rock's shadow, still hollow. Nobody passes anybody: the main bodies are engaged at range.
- **4 · 13.0–17.0 — the trap springs.** Ink's heavy blocks crest onto the top step. Gold's wall withdraws — a controlled step back, not a rout — opening the ground. Gold's wedges surge out from behind the south-east rock and sweep around ink's heavy blocks: the shape that beats them, arriving from the side they could not see. Ink's Siege is the wrong unit on the wrong ground and begins to fall back down the ramp. Ghost, briefly, the future ink declined: not taking the bait.
- **5 · 17.0–20.5 — the counter-hit.** As ink's heavy blocks fall back, ink's wedges emerge from the low route behind gold's fire base and sweep around gold's set-back heavy blocks — the mirror of move 4. Gold's wall turns to hold them (Line absorbs Strike) but is a step late. Two flanks, two Siege groups hurt, in the same window.
- **6 · 20.5–24.0 — scathed, and the hold.** Both sides disengage. Gold keeps the height but its fire base is thinned; ink keeps its wedges and the low ground but its main body is thinned. Damage reads as shapes dimmed and drawn back, never as contact. Ghost each side's one alternative at its decisive moment — ink not climbing, gold springing later — then hold on a board that reads differently than it did.

**Retime** the timing strip to those seven blocks. Redraw the six move panels to match. Keep the 4-image progression device, extended to the new count — it is the reading aid the diehards will study.

#### Phase-2 prompt (for the animation chat)

> **Context (this chat has no other background):** *Ouroboros Manifold* is a real-time strategy game where fights are won by positioning, not unit stats. Units balance in a soft rock-paper-scissors — fast units flank heavy ones, heavy ones crush lines, lines absorb fast units — and maps are stacked in elevation levels, where a force sees one level below it at half reach and two levels below almost not at all. This animation is for the section aimed at experienced RTS players. Its goal is to show what an intelligent engagement between two competent players looks like: a deliberate bait on high ground, a trap sprung with the counter unit, and a simultaneous counter-flank from below — both sides leaving scathed. It must never look like a battle or show damage as contact; it should read as thinking. It animates the attached phase-1 blueprint exactly.
>
> [style block]
> A top-down geometric animation on a low-poly battlefield of three stepped elevation levels (lightest highest), two sides drawn in gold and ink using three shapes: fast wedges, heavy blocks, and firm walls. Wedges beat heavy blocks, heavy blocks beat walls, walls beat wedges, and every move obeys that. A force the other side cannot see is drawn hollow. Play the attached seven-panel sequence: gold shows a wall at the crest lip as bait; ink commits its heavy blocks up the ramp while its wedges split off along the lowest level around the sealed chokepoint, hollow and unseen; the heavy blocks climb under arcing fire from gold's set-back blocks; at the crest gold's wall steps back and gold's hidden wedges surge from behind the rock to sweep around ink's heavy blocks; as those fall back, ink's wedges emerge behind gold's fire base and sweep around gold's heavy blocks; both sides disengage, thinned. At each decision point, ghost two or three alternative arrows, hold a beat, then commit one and let the others fade — options first, event second. Shapes move only after their arrow finishes drawing. No shape ever touches another; damage reads as shapes dimmed and drawn back. Camera overhead and still except for a slow drift. Slow, deliberate pacing; flat warm colors; no text.
> [negative list]

*Why this play:* both players do the correct thing on the information they have, and both are punished by what they could not see. That is the tragedy-of-understanding pitch in miniature, and it is what a diehard will pause and re-watch.

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

> **Context (this chat has no other background):** *Ouroboros Manifold* is a strategy game set in a galaxy that runs its own simulation: factions rise, expand, and collapse whether or not the player does anything. This animation is a time-lapse of that galaxy map over decades, for the section explaining that the world is alive. The goal is slow, tidal change with no author — many factions breathing and shifting on their own — so the viewer understands the world does not wait for them.
>
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

> **Context (this chat has no other background):** In *Ouroboros Manifold*, each mission is a chapter; between chapters decades pass, the world changes, and you return as a different person into a place that remembers what happened. A written chronicle records that history. This animation shows one region changing across decades while a chronicle scroll grows beside it. The goal is an elegiac feeling of time passing and consequences persisting: the world moves on, and the record of it keeps being written.
>
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

# Map view zoom band: options

Three ways to give the commander a zoomed-out view of the battle, reached by pulling the same camera back, not by opening a separate screen. None show the galaxy; none grant an order beyond move and attack-move.

## Option A — The War Table

**How it works.** Past the tactical band the ground flattens into plain colored shapes — water, forest, city core — and each visible group becomes a small colored wedge. No grid letters, no naval chrome; this is what the old corner minimap becomes, filling the whole screen. A click selects one wedge; a drag box catches every unit under it, any layer. Open ground draws a cool line ending in a flag (move); a visible enemy wedge draws a hot line ending in a crossed marker (attack-move). A bar across a wedge's base marks its group: raised for Upper (4–5), lowered for Lower (1–2), full-height for Expansive (1–5); layer 3 alone carries no bar, the neutral middle.

**Vignette.** A second enemy column appears; you roll the wheel back and the battlefield flattens into wedges. You box your reserve by the river — every unit lights up, any layer — and click near a red wedge past the bridge; a hot line draws itself, an attack-move. Zoomed back in, your reserve is crossing the bridge, the line glowing at their feet before it fades.

**Transition and fog.** Pitch eases from the tactical angle to straight-down as terrain and units fade into flat shapes and wedges together. Terrain is always drawn; enemy wedges appear and vanish on the instant of current vision, nothing shown beyond color and layer bar.

**Honors:** move/attack-move only; minimap replacement; overlay on terrain; camera floor and canvas bound; drag box touches every layer; no naval grid. **Strains:** the snap from real terrain to flat shapes sits uneasily against "one continuous world."

**Prior art:** World of Warships map view — VERIFIED (`docs/bible/references/E-17/E-17-8-wows-map-view.png`). SC2 minimap viewport — REPORTED (`docs/legacy/stage_specs/stage_11d_mid_mission_hud_spec.md`).

**Tradeoffs.** A quick, legible overview with little to learn, at the cost of a visible style break at the crossing.

Diagram: diagrams/option-a.svg

## Option B — Waypoint Chorus

**How it works.** The same flattening as Option A, but the ground points at what matters first: gates, bridges, vantages, and objective circles brighten a beat before groups shrink into icons. Selection and the order line work as in Option A, except near a named feature: the line settles onto it and captions it ("through the eastern pass"). Layer marks are the same bar, except layer 3 alone carries a plain center dot — the quietest of the four.

**Vignette.** You need to know if your reserve can make the eastern pass first. You pull back; the pass glows before your units resolve into icons. You box the reserve — every unit lights up, any layer — and drag toward the pass; the line snaps onto its ring, captioning itself. You release; the move order locks in. Zoomed back in, a pennant marks the pass mouth, your units filing toward it.

**Transition and fog.** As Option A, staggered: terrain features surface first, groups a beat later.

**Honors:** move/attack-move only; minimap replacement; overlay on terrain; camera floor and canvas bound; drag box touches every layer; no naval grid; a reading of "one continuous world" since orders are named in the terrain's own language. **Strains:** the snap-to-feature behavior, though never mandatory, edges toward an auto-pathing assist worth watching against Principle 6's spirit.

**Prior art:** World of Warships map view — VERIFIED (as above). Age of Empires Online's labeled terrain register — REPORTED (`docs/bible/references/E-17/notes.md` row 01).

**Tradeoffs.** Orders read back in plain terrain language, catching a hasty click, at the cost of a temptation to let the snap aim for you.

Diagram: diagrams/option-b.svg

## Option C — The Sand Table (wild)

**How it works.** Nothing turns flat. Pulling back shrinks the world like a tilt-shift photograph shrinks a model: terrain stays three-dimensional, but scale falls away, edges soften, light warms as if looking down at a table. Groups become small standing pins; a click selects one, a drag box catches every pin under it, and every unit inside. A thread to open ground and released is cool, ending in a flag (move); onto a visible enemy's ground, hot, ending in crossed flags (attack-move) — a snapshot of where the enemy could be seen at release, not a leash that follows after. Pin height carries the layer mark: tall and spiked for Upper, short and sunk for Lower, a full rod for Expansive; layer 3 alone stands at ordinary resting height, what a pin would be with no layers at all.

**Vignette.** The fight has sprawled across a valley and you've lost its shape. You zoom out; the ground shrinks rather than flattening, haze pooling where you can't see. You box across the table — every unit inside, every layer, lifts free as pins. You take the tallest pin, spiked for a ridge-top group, and pull a cool thread into the valley, releasing it on open ground. Zoomed back in, the pin dissolves into your squad, moving downslope, the glow fading at their boots.

**Transition and fog.** No pitch-to-flat moment; the world shrinks and softens, groups condensing into pins that drop into place with a small bounce. Fog is physical: haze pools in valleys and behind ridgelines wherever no friendly unit can see, thinning the instant vision reaches it; enemy pins appear and vanish with that haze, nothing shown beyond color and height.

**Honors:** move/attack-move only; minimap replacement; never shows the galaxy; a reading of "overlay moves with the terrain," since terrain is never swapped for abstraction; camera floor and canvas bound; no naval grid; drag box catches every layer. **Strains:** legibility at map-band distances — a pin behind a tall peak can be harder to find than "pick a group from above" implies.

**Prior art:** none found for a command band built as a shrinking, still-three-dimensional model; tilt-shift/diorama photography exists as an unconnected real-world technique — ESTIMATED as a reference for the look only.

**Tradeoffs.** You never lose the feeling of looking at your battle rather than a chart of it, at the cost of legibility work where terrain that used to help you can now hide a group.

Diagram: diagrams/option-c.svg

## Findings

Two brief constraints could not be fully honored by any option, because the brief leaves them open, not because an option failed to try.

First, "the map view replaces the minimap" collides with the minimap's old job as an always-visible corner glance. World of Warships keeps a permanent corner map and swaps to full-screen on a keypress; here, the map view is reached only by pulling the camera back, and the brief says it *replaces* the minimap, so none of the three options restores an always-on corner readout. All three trade the old glance-without-zooming for a short camera pull.

Second, R-104-09 fixes the right sidebar as empty except the layer strip, but the brief never says what that strip does once the band collapses per-unit layer rings into the per-group marks described here. None of the three options changes, dims, or repurposes it — the confirmed answer speaks only to how a group is marked, not to that element's fate.

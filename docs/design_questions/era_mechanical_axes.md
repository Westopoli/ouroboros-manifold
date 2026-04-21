# Era Mechanical Axes — Mix-and-Match Identity Matrix

> **Transient working doc.** Drafted to resolve "how do we design hallmark
> and work eras without inventing a new system per era." The deliverable
> is a small set of orthogonal mechanical dials, a matrix positioning the
> 3 launch eras on every dial, and an annotation of which dial positions
> are **Branch DNA** (shared by all eras in a branch) vs. **hallmark-exclusive**
> (reserved for the branch's apex era). Once the matrix stabilizes, its
> content lands in `bible_monetization.md` (Branch System extension) and
> feeds work-era design + Sloyd prompts. This file is deleted when captured.
>
> **Capture targets:** `bible_monetization.md` (Branch System subsection),
> `bible_combat.md` (per-era parameterization re-opens from Session 6),
> `bible_world.md` (map generation gradient consequences).
>
> **Non-goals.** This doc does not invent new engine systems. Every axis
> proposed here must be expressible as per-era config the engine consumes
> uniformly (Sacred Principle #3). Axes that would require engine branching
> on era identity are rejected on sight.

---

## Production Constraints — Apply To Every Axis

These constraints filter which axes survive the pruning pass. Any axis
that violates one of these is cut or rewritten.

- **Solo developer, 20-era catalog.** An axis that costs 20 hours of
  authoring per era per position does not scale. Dial settings must be
  cheap to set — config values, not bespoke systems.
- **Sacred Principle #3.** No engine code branches on era. Dial positions
  must live in per-era config. If a dial requires `if era == "..."` in
  engine code, it's rejected.
- **Must produce noticeably different missions.** An axis whose different
  positions feel like "slightly different stats" is not an axis, it's a
  tuning parameter. Each dial must pass the test: can a player describe
  the difference without looking at numbers?
- **Must be teachable.** The axis vocabulary should be small enough that
  a player learns it once and recognizes it across all eras. Aim for
  5–7 axes total.

---

## Proposed Axis List (first pass)

Seven candidate axes. First three are already locked in `bible_monetization.md`
Branch System. Axes 4–7 are new proposals drafted in this session.

1. **Tempo** *(locked — Branch System)* — engagement duration, movement speed,
   action density per unit time. Fast / medium / slow.

2. **Information warfare** *(locked — Branch System)* — fog density, sensor
   range, cross-layer sight, scout-dependency vs. sensor-dominance.
   Near-total awareness / partial asymmetry / heavy fog.

3. **Attrition / economy** *(locked — Branch System)* — reinforcement rate,
   production density, force preservation value. Rapid recovery / industrial
   replacement / slow reinforcement.

4. **Layer access** *(new — Westley-introduced)* — which unit types can
   physically occupy which layers. Free traversal (SR) / strict lock
   (1980s subs-surface-air) / ground-only (Roman). This is about *where
   units can be*, not about *what units can see* (which is axis 2).

5. **Force scale** *(new — proposed)* — how many units on the field at
   mission peak. Squad (10–20) / company (30–50) / legion (60+). This
   axis controls mission feel in a way nothing else captures — a 15-unit
   skirmish and an 80-unit campaign are different *games*, not different
   missions of the same game.

6. **Terrain expressiveness** *(new — proposed)* — how much map geography
   shapes tactics. Minimum (open space) / mixed (naval archipelago + land
   corridors) / maximum (passes, rivers, defiles dominate). This is the
   axis that lets Roman earn a mechanical identity Branch 1 can't touch
   without contradicting its own branch DNA.

7. **Environmental threat** *(new — proposed, most speculative)* — does
   the environment itself damage or kill units over time, independent of
   enemy action? Vacuum breach, radiation, sonar conditions, heat, cold.
   Low / medium / high. The newest axis and the one I'd most expect you
   to challenge — it's where SR's "magnum opus" status could genuinely
   shine, since environmental hazards in space combat are underused in
   the genre.

---

## Batch Roadmap

- **Batch 1** *(done)* — governance, production constraints, axis list.
- **Batch 2a** *(this batch)* — detail for axes 1–4 (locked trio + layer access).
- **Batch 2b** — detail for axes 5–7 (force scale, terrain expressiveness,
  environmental threat — my new structural proposals).
- **Batch 3** — the 7-axis × 3-era matrix with one-line rationale per cell.
- **Batch 4** — Branch DNA vs. hallmark-exclusive annotations.
- **Batch 5** — rejected axes + experimental stretch axes (maximum creativity
  bay: temporal distortion, supply-line tactics, civilian presence,
  reinforcement topology, and a few others).

---

## Axis Detail — Batch 2a

Each axis below is specified by: definition, the three canonical positions,
cross-axis risk (where it overlaps with another axis and how to keep the
two distinct), implementation cost, and any open sub-questions. Positions
are canonical stanzas — actual per-era config lives on a continuum, but
the stanzas are what the player learns to recognize.

### Axis 1: Tempo *(locked)*

**Definition.** The rate at which tactical events happen. Engagement
duration, unit movement speed, and the density of decisions the player
makes per minute of play.

**Positions.**
- **Fast** (Branch 1 DNA) — 30–45s decisive engagements, rapid maneuver,
  high burst damage. The player issues many orders per minute; missions
  are short and decisive.
- **Medium** (Branch 2 DNA) — 1–2 min engagements, combined-arms
  coordination time. Orders arrive in bursts with planning gaps between.
- **Slow** (Roman, Branch 3 DNA) — 2 min+ engagements, attritional.
  Orders less frequent; missions are about positioning and commitment,
  not micro.

**Cross-axis risk.** Tempo visibly overlaps with **force scale** (a larger
force mechanically slows mission pace). Kept distinct by specifying:
tempo is *per-engagement rhythm*; scale is *how many engagements happen
simultaneously*. A fast-tempo 80-unit mission and a slow-tempo 15-unit
mission feel noticeably different — tempo is about how fast a single
fight resolves, not how many units are present.

**Implementation cost.** **Low.** HP / damage / speed multipliers already
live as per-era config in `bible_combat.md`. Session 6 flagged the Settled
Reach stat rebalance as the first consumer.

**Open sub-questions.** None — this is the most well-grounded axis.

### Axis 2: Information warfare *(locked)*

**Definition.** How much of the battlefield state the player knows at any
moment, and the tactical cost of acquiring information.

**Positions.**
- **Near-total awareness** (Branch 1 DNA) — sensor dominance, free
  cross-layer sight, counter-stealth is the active cost. The fight is
  about what to do with perfect information, not about acquiring it.
- **Partial sensor asymmetry** (Branch 2 DNA) — radar, intel, reconnaissance
  all partial. Some things seen, some things hidden. ECM and scouts matter.
  The fight is about managing the gaps in your picture.
- **Heavy fog** (Roman, Branch 3 DNA) — scout-dependent, ambush is a real
  threat, sensor systems largely absent. The fight is about *finding* the
  enemy before they find you.

**Cross-axis risk.** Information visibly overlaps with **terrain expressiveness**
(terrain hides units) and with **environmental threat** (nebulae blind).
Kept distinct by specifying: information is about *sensor capability
configuration*; terrain is about *movement and engagement geometry*;
environment is about *hostile-to-all-agents damage fields*. A nebula that
blocks sensors (info), channels movement through gaps (terrain), and
irradiates anything caught inside (environment) is one map feature
positioned on three independent dials.

**Implementation cost.** **Low.** Fog density, sensor range, cross-layer
sight multipliers, and pulse cooldown already live as tuning parameters.

**Open sub-questions.** None — this is well-grounded.

### Axis 3: Attrition / economy *(locked)*

**Definition.** How replaceable units are within and across missions, and
how much force preservation matters strategically.

**Positions.**
- **Rapid recovery** (Branch 1 DNA) — few units, fast replacement. Losses
  are recoverable; plan quality matters more than preservation. The fight
  is about executing strikes and reconstituting.
- **Industrial replacement** (Branch 2 DNA) — moderate quantities, moderate
  replacement pace. Doctrine and logistics decide campaigns. The fight is
  about outproducing or outmaneuvering.
- **Slow reinforcement** (Roman, Branch 3 DNA) — casualties hurt, force
  preservation matters, reinforcement is rare. The fight is about *not*
  committing your force when you don't have to.

**Cross-axis risk.** Attrition visibly overlaps with **force scale** (more
units = more to lose = different preservation psychology). Kept distinct
by specifying: attrition is about *replacement rate*; scale is about
*concurrent quantity*. A rapid-recovery 80-unit mission (Branch 1 at
large scale, hypothetical) and a slow-reinforcement 15-unit mission
(Roman at small scale, hypothetical) feel different in a way neither
dial captures alone.

**Implementation cost.** **Low.** Reinforcement structure density,
production time scaling, and retention currency all already exist as
config.

**Open sub-questions.** None — this is well-grounded.

### Axis 4: Layer access *(new — Westley-introduced)*

**Definition.** Which unit types can physically occupy which of the 3–5
vertical layers, and how costly layer transitions are for a unit that can
make them. This is about *where units can be*, not about *what they can
see* (which is axis 2).

**Positions.**
- **Free traversal** (Settled Reach, hallmark-exclusive) — all 6 unit
  types can occupy all layers. Layer transitions are cheap. The fight
  spans all vertical space simultaneously because there is no atmospheric
  or medium difference between layers.
- **Strict layer lock** (1980s, hallmark-exclusive) — hard per-unit-type
  layer restrictions. Submarines are below-surface-only; surface vessels
  are surface-only; aircraft are above-surface-only. Transitions are
  impossible (a submarine does not become a plane). The fight is about
  how each layer supports or threatens the others.
- **Terrain-elevation pseudo-layers** (Roman, Branch 3 DNA) — one nominal
  layer. All units operate on "the ground." But height-varying terrain
  creates functional elevation differences within that layer — a unit
  on a ridge sees over a unit in a valley, ranged fire gains elevation
  bonus, defiles funnel movement. The 2.5D system expresses as map
  geometry rather than as discrete layer assignment.

**Cross-axis risk.** Layer access visibly overlaps with **force scale**
(more unit types = more ways to layer-lock) and with **tempo** (cross-layer
engagements may be slower to resolve than same-layer). Kept distinct by
specifying: layer access is about *which (unit type, layer) pairs are
legal*; scale is about *how many units total*; tempo is about *per-engagement
rhythm*.

**Implementation cost.** **Low.** `layer_accessibility_mask` already lives
in the map generation gradient vocabulary (Q4 resolution, `bible_world.md`).
Per-unit layer restriction config exists in the 1980s era spec. Settled
Reach's free-traversal position is the *absence* of restrictions — it
ships by default if no mask is applied.

**Open sub-questions.** One important one: **does this axis also carry
the cross-layer engagement rules** (who can shoot at whom across layers,
and with what range/damage modifiers), or is cross-layer engagement a
separate dial? My lean is that it's a sub-parameter of this axis (the
config that says "air units can strike surface at X range, surface can
strike air at Y range, surface cannot strike submerged at all" sits
naturally alongside the access mask). Worth confirming.

---

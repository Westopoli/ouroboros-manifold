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

Eight candidate axes. First three are already locked in `bible_monetization.md`
Branch System. Axes 4–8 are new proposals drafted in this session.

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
   (1980s subs-surface-air) / terrain-elevation pseudo-layers (Roman).
   This is about *where units can be*, not about *what they can shoot*
   (which is axis 8).

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

8. **Cross-layer engagement** *(new — resolved from Batch 2a sub-question)* —
   which (attacker-layer, target-layer) pairs are valid for weapon
   engagements, and with what modifiers. Fully reciprocal (SR, any pair
   valid) / asymmetric matrix (1980s, some pairs mechanically impossible
   like sub→air) / ground-bound (Roman, engagement is effectively single-layer
   with elevation bonus). Split from axis 4 because where a unit *can be*
   is mechanically independent of what it *can shoot* — a 1980s submarine
   can exist underwater (access) and cannot target aircraft (engagement),
   and those two facts sit on different config knobs.

---

## Batch Roadmap

- **Batch 1** *(done)* — governance, production constraints, axis list.
- **Batch 2a** *(done)* — detail for axes 1–4 (locked trio + layer access).
- **Batch 2b** *(this batch)* — detail for axes 5–8 (force scale, terrain
  expressiveness, environmental threat, cross-layer engagement).
- **Batch 3** — the 8-axis × 3-era matrix with one-line rationale per cell.
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

**Open sub-questions.** *Resolved Session 7 (this doc):* cross-layer
engagement was split out as axis 8. The sub→air case (a submarine can
exist underwater but cannot target aircraft) is the clean evidence that
the two dials are mechanically independent. Axis 4 is now *only* about
where units can be; what they can shoot is axis 8.

### Axis 5: Force scale *(new — proposed)*

**Definition.** How many units are on the field at mission peak. The
quantity dial, independent of how fast they fight (tempo) or how quickly
they replace (attrition).

**Positions.**
- **Squad / taskforce** (Settled Reach, Branch 1 DNA) — 10–20 units. Every
  unit has a readable identity on-screen. The player makes per-unit
  tactical decisions. The mission feels like commanding a strike team.
- **Company / battlegroup** (1980s, Branch 2 DNA) — 30–50 units. Mixed
  formations across layers. Unit-type roles matter more than individual
  unit identities. The mission feels like commanding a combined-arms
  operation.
- **Legion / cohort** (Roman, Branch 3 DNA) — 60+ units. Force is massed.
  Commands issued at group level; individual units blur into formations.
  The mission feels like commanding an army.

**Cross-axis risk.** Visibly overlaps with **tempo** (more units = slower
decision rhythm per unit) and **attrition** (more units = more to lose).
Kept distinct by specifying: scale is *concurrent quantity*; tempo is
*per-engagement rhythm*; attrition is *replacement rate*. A rapid-tempo
80-unit hypothetical and a slow-tempo 15-unit hypothetical both exist on
independent dial settings.

**Implementation cost.** **Medium.** Force allocator already exists; current
parity targets are uniform. Per-era scale requires the allocator to read
era-scale config and generate larger/smaller forces at the same power
rating. Mission generator consumes it. UI consequence: selecting 80 units
vs. 15 units is a different command experience — hotkey group layouts
and selection paradigms may need per-era polish passes, though the
4-command vocabulary from `bible_combat.md` works at all scales.

**Open sub-questions.** At legion scale, do missions need group-level
command primitives (waypoint chains, formation orders) beyond the current
4-command set? Not in scope for this matrix, but flagged for the combat
bible session as a potential Roman-specific consideration.

### Axis 6: Terrain expressiveness *(new — proposed)*

**Definition.** How much map geography shapes tactical decisions. The
"how much does where you are matter" dial. Measured by how often terrain
features choose where fights happen vs. the player choosing.

**Positions.**
- **Minimum** (Settled Reach, Branch 1 DNA) — open space is the default.
  Obstacles are sparse: debris fields, asteroid belts, station structures.
  Tactics flow around a few localized hazards. Most of the map is
  tactically neutral.
- **Mixed** (1980s, Branch 2 DNA) — land missions get strong terrain
  (forests, urban, ridges, defiles); naval missions are archipelago-open
  (islands as waypoints, sea itself is tactically flat). Different mission
  archetypes sit at different points on the sub-dial.
- **Maximum** (Roman, Branch 3 DNA) — mountains, rivers, defiles, passes,
  forests dominate tactics. Geography chooses where fights happen, not
  the player. The map is the second enemy.

**Cross-axis risk.** Overlaps with **layer access** (Roman's pseudo-layers
are terrain) and with **information** (terrain hides units from sensors).
Kept distinct by specifying: terrain is about *movement and engagement
geometry*; access is about *which (unit, layer) pairs are legal*; info
is about *sensor capability*. A mountain pass is a terrain feature
(movement funnel), a sensor shadow (info consequence), and, for eras with
layer access, a layer geometry feature. Same map feature, three independent
dials picking up three different properties.

**Implementation cost.** **Medium.** Gradient vocabulary already exists
(5 gradients including obstacle_density and cover_density). Strategic
layout pool already exists (Q4 resolution, 10–20 hand-authored blueprints).
Setting per-era terrain intensity is config. But *authoring* dense-terrain
maps vs. open-space maps requires different spine/layout libraries — may
need more variety at the minimum and maximum ends of the dial.

**Open sub-questions.** Should the authored-layout pool split into
terrain-intensity variants, or do archetype filters already handle this
via layout-to-archetype compatibility? My lean: filter-based split, layout
pool stays unified. But this is a map generation concern that should be
confirmed with the Stage 7 work before it's locked.

### Axis 7: Environmental threat *(new — most speculative)*

**Definition.** Does the environment itself damage or kill units over time,
independent of enemy action? "Hostile to all agents" rather than "hostile
to one side." This is the axis that's not in the bible yet at all.

**Positions.**
- **Low** (Roman, Branch 3 DNA) — weather and seasons flavor missions but
  rarely kill units. Desert crossings and winter campaigns are edge cases
  in mission generation, not per-mission mechanical dials. Environmental
  damage is narrative dressing.
- **Medium** (1980s, Branch 2 DNA) — sonar conditions, sea state,
  atmospheric conditions affect detection and mobility. Not usually lethal
  but they shape decisions. Submarine depth limits are the closest thing
  to direct environmental damage. Environment is a tactical consideration.
- **High** (Settled Reach, candidate hallmark-exclusive) — radiation belts,
  vacuum breach, gravity wells, nebula damage. The environment actively
  kills. Map geography includes "you can't go there without HP loss" zones.
  Tactics must respect the environment as a first-class opponent.

**Cross-axis risk.** Overlaps with **terrain** (some environmental hazards
are terrain: nebulae block movement AND damage) and with **information**
(nebulae blind sensors AND harm units). Kept distinct by specifying:
environment is specifically *damage-over-time to all agents*. A nebula is
a terrain feature (blocks movement), an info feature (blocks sensors),
and an environmental feature (ionizing radiation). Each dial picks up
its own slice of the same map object.

**Implementation cost.** **Medium-high.** This is the most expensive axis
on the list because the engine doesn't currently have a
"damage-over-time-in-region" system beyond what combat damage does.
Implementing it requires:
- A damage-field representation in the tick engine (which map zones apply
  periodic damage, at what rate, to which unit categories)
- Per-unit vulnerability / resistance config (some units are vacuum-rated,
  some aren't — this is per-unit-type × per-era config)
- Visual representation for renderer (nebula shader, radiation warning
  indicators, damage-zone overlays)
- Chronicle hooks (units lost to environmental damage get different
  template treatment than units lost in combat)

Flag for design review: this is the one axis where "cheap to implement"
is not obviously true. If the cost is wrong, this axis drops out and
Settled Reach's hallmark-exclusive position shifts to another axis.

**Open sub-questions.** Should environmental damage be *uniform* (everyone
in the zone takes damage equally) or *asymmetric* (some units are
environmentally hardened)? My lean: asymmetric, because it creates
tactical expression (sending environment-hardened units into zones others
can't go creates positional puzzles no other axis generates). But uniform
is simpler to ship and may be the right v1. Revisit at Stage 7 or a
dedicated environmental-systems session.

### Axis 8: Cross-layer engagement *(new — split from axis 4)*

**Definition.** Which (attacker-layer, target-layer) pairs are valid for
weapon engagements, and with what range/damage modifiers. Where axis 4
says "a 1980s submarine can exist at layer 4," axis 8 says "a 1980s
submarine cannot target a unit at layer 1." Two separate config knobs.

**Positions.**
- **Fully reciprocal** (Settled Reach, candidate hallmark-exclusive) — any
  unit can engage any other unit regardless of layer pair. Range/damage
  may be modified across layers but no (attacker, target) pair is mechanically
  impossible. Every unit is a threat to every other unit, conditional on
  range and sensor coverage.
- **Asymmetric matrix** (1980s, hallmark-exclusive) — specific layer pairs
  are mechanically impossible. Submarines cannot engage aircraft (no
  underwater-to-air weapon). Aircraft can engage submarines via specialized
  units (ASW helicopters with depth charges) but not via fighter-aircraft.
  Surface engages air (anti-air) and engages submarines (ASW) but as
  distinct capabilities. The engagement matrix is a tactical puzzle in
  its own right — who can kill whom, and with what escort?
- **Ground-bound** (Roman, Branch 3 DNA) — engagement is effectively
  single-layer because all units are on the nominal ground layer.
  Elevation (from axis 4's pseudo-layer mechanic) grants ranged-fire
  bonus without creating mechanically-impossible pairs. A bow on a ridge
  can still shoot a bow in a valley; the elevation just modifies damage
  and range.

**Cross-axis risk.** Obviously overlaps with **layer access** (axis 4)
since both describe layer-related mechanics. Kept distinct by specifying:
access is about *where units can physically be*; engagement is about
*what units can shoot*. A submarine and a fighter jet can both exist
(access permits them at their respective layers) yet cannot exchange fire
(engagement forbids the pair). Also overlaps weakly with **information**
(you can't shoot what you can't see, but that's sensor-gating, not
engagement-matrix-gating).

**Implementation cost.** **Low.** Per-era engagement matrix is
(attacker_layer × target_layer) → (range_mult, damage_mult, valid_flag)
lookup. Already implicit in per-unit-type weapon config; making it explicit
per era is a config refactor, not a new engine system.

**Open sub-questions.** Does the engagement matrix need per-unit-type
granularity, or is per-layer-pair sufficient? 1980s probably needs
per-unit-type (ASW helicopter engages submarines, transport helicopter
does not — both are surface-layer aircraft). Per-layer-pair would be
simpler but underspecified for at least one launch era. Lean: start
per-layer-pair as the matrix default, allow per-unit-type override
entries as exceptions.

---

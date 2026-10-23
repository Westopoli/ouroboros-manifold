# Era Mechanical Axes — Mix-and-Match Identity Matrix

> **LEGACY MONETIZATION CONTEXT — 2026-05-09**
>
> This doc references the prior subscription/access-tier framing (e.g., "hallmark
> exclusivity" tied to purchase tiers). The subscription model has been **scrapped**;
> the current model is buy-once base game + paid Steam DLC expansions, no subscription.
> See `docs/bible_history/game_bible_1_23.md (formerly bible_monetization.md, folded into the hub 2026-05-31)` "Current Monetization Model" section.
> The orthogonal mechanical-axis matrix in this document remains useful as design
> context; only the access-tier annotations are obsolete.

> **Transient working doc.** Drafted to resolve "how do we design hallmark
> and work eras without inventing a new system per era." The deliverable
> is a small set of orthogonal mechanical dials, a matrix positioning the
> 3 launch eras on every dial, and an annotation of which dial positions
> are **Branch DNA** (shared by all eras in a branch) vs. **hallmark-exclusive**
> (reserved for the branch's apex era). Once the matrix stabilizes, its
> content lands in `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/) (Branch System extension) and
> feeds work-era design + Sloyd prompts. This file is deleted when captured.
>
> **Capture targets:** `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/) (Branch System subsection),
> `docs/bible_history/bible_2_00_combat.md` (per-era parameterization re-opens from Session 6),
> `docs/bible_history/bible_2_00_world.md` (map generation gradient consequences).
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

Eight candidate axes. First three are already locked in `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/)
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

5. **Force scale** *(new — proposed, refined in Batch 2c)* — how many
   units on the field at mission peak. Squad (20–60) / company (100–300) /
   legion (600–1000). The 1000 cap is a long-term target — current engine
   ceiling is `MAX_UNITS = 400` and the ORCA LP / RVO neighbor pass is
   the scaling bottleneck. A 15-unit skirmish, a 200-unit operation, and
   a 1000-unit campaign are different *games*, not different missions of
   the same game. This axis names a lever the bible has implied but never
   articulated.

6. **Terrain expressiveness** *(new — proposed, refined in Batch 2c)* —
   how much map geography shapes tactics, expressed as a **(midpoint,
   spread)** pair. Midpoint = average terrain intensity across the era's
   mission pool. Spread = how far individual missions swing from that
   midpoint. Some eras are terrain-*predictable* (tight spread — you know
   what kind of map to expect); others are terrain-*surprising* (wide
   spread — the mission pool spans very different operational theaters).
   Both dimensions must be narratively grounded. This is the axis that
   lets Roman earn a mechanical identity Branch 1 can't touch without
   contradicting its own branch DNA.

7. **Environmental threat** *(new — refined Batch 2c from persistent state
   to event-based)* — how often does the environment fire damage-dealing
   events during a mission? Meteor storms, hurricanes, solar flares,
   sonar conditions, thermal extremes — discrete events that trigger
   mid-mission, deal damage-over-time for a bounded window, and revert.
   Rare / occasional / common. Reframed from a persistent world-state
   property (my original v1 proposal) to an event-triggered property
   because the event reframe is cheaper to implement, dramatically more
   memorable as a player experience, and dovetails with `events.py`.

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
- **Batch 2b** *(done)* — detail for axes 5–8 (force scale, terrain
  expressiveness, environmental threat, cross-layer engagement).
- **Batch 2c** *(done)* — refinements to axes 5, 6, 7.
- **Batch 3** *(this batch)* — the 8-axis × 3-era matrix with one-line
  rationale per cell, plus "what the matrix reveals" commentary.
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
live as per-era config in `docs/bible_history/bible_2_00_combat.md`. Session 6 flagged the Settled
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
in the map generation gradient vocabulary (Q4 resolution, `docs/bible_history/bible_2_00_world.md`).
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
- **Squad / taskforce** (Settled Reach, Branch 1 DNA) — 20–60 units. Every
  unit has a readable identity on-screen. The player makes per-unit
  tactical decisions. The mission feels like commanding a strike team.
- **Company / battlegroup** (1980s, Branch 2 DNA) — 100–300 units. Mixed
  formations across layers. Unit-type roles matter more than individual
  unit identities. The mission feels like commanding a combined-arms
  operation.
- **Legion / cohort** (Roman, Branch 3 DNA) — 600–1000 units. Force is
  massed. Commands issued at group level; individual units blur into
  formations. The mission feels like commanding an army. The 1000 top-end
  is a long-term target, not a current-engine number.

**Cross-axis risk.** Visibly overlaps with **tempo** (more units = slower
decision rhythm per unit) and **attrition** (more units = more to lose).
Kept distinct by specifying: scale is *concurrent quantity*; tempo is
*per-engagement rhythm*; attrition is *replacement rate*. A rapid-tempo
800-unit hypothetical and a slow-tempo 40-unit hypothetical both exist on
independent dial settings.

**Implementation cost.** **Medium** (config) + **high** (engine, for the
1000 top-end). Force allocator already exists; current parity targets are
uniform. Per-era scale is a config change the allocator reads — cheap.
UI polish per scale is medium. But the 1000-unit legion position depends
on the engine performance work flagged below.

**Performance dependency — 1000-unit target.** Engine currently hardcodes
`MAX_UNITS = 400` in `unit.py`. `profile_6k_single_tick.py` already exists
in the codebase and indicates the ORCA LP solver + RVO neighbor pass is
the scaling bottleneck (O(n²) in neighbor queries, LP solve dominates
frame time). Per the language-migration analysis: the bounded-scope path
is a **native extension** (C via ctypes or Rust via pyo3) implementing
only the RVO neighbor pass and the ORCA LP solve — roughly 500–1000 lines,
keeps the rest of the engine in Python, plausibly unlocks 2000+ units.
Authoring Roman as a 1000-unit legion era is not gated on this work
(per-era config can be written now); *playing* it at scale is. Cheapest
interim win while the extension is pending: try PyPy on `sim_tuner.py`
for headless tuning runs — zero code changes, typically 3–10× on
dict-heavy code.

**Open sub-questions.** At legion scale, do missions need group-level
command primitives (waypoint chains, formation orders) beyond the current
4-command set? Not in scope for this matrix, but flagged for the combat
bible session as a potential Roman-specific consideration. Also: what is
the rendering cost of 1000 on-screen units in Godot, and does the
sim/renderer WebSocket protocol deliver tick deltas fast enough at that
scale? Out of scope for this doc but a real dependency.

### Axis 6: Terrain expressiveness *(new — proposed, refined Batch 2c)*

**Definition.** How much map geography shapes tactical decisions, expressed
as a **(midpoint, spread)** pair. Midpoint is the average terrain intensity
across the era's mission pool on a normalized 0–100 scale (0 = open void,
100 = terrain dominates every decision). Spread is how far individual
missions swing from that midpoint. Terrain is the one axis in this matrix
where per-mission variance is itself era identity — playing an era where
every mission feels like a different kind of map is a different experience
from playing an era where every mission feels the same.

**Positions.**
- **High midpoint, tight spread** (Roman, Branch 3 DNA) — roughly midpoint
  80 with spread 10–15. Most missions are terrain-rich. Mountains, rivers,
  defiles, passes dominate. Spread is narrow because Roman's operational
  theater is a coherent civic world with predictable topology types.
  Players settle into "this era is *about* terrain." Narrative grounding:
  Rome's operational theater is the Mediterranean and its hinterlands — a
  real, finite, topologically coherent landscape.
- **Mixed midpoint, wide spread** (1980s, Branch 2 DNA) — roughly midpoint
  50 with spread 30–40. Mission pool spans naval archipelago (terrain-light
  ocean with island waypoints) to land urban/forest (terrain-heavy). Wide
  variance is grounded in narrative: the Cold War proxy-war era naturally
  produces submarine campaigns *and* Eastern European land operations
  *and* desert intervention *and* jungle counterinsurgency. Players learn
  to expect the unexpected *mission type*, not to expect the unexpected
  *within a mission type*.
- **Low midpoint, moderate spread** (Settled Reach, Branch 1 DNA) —
  roughly midpoint 25 with spread 15–25. Most missions default to open
  space. Occasional swings into asteroid fields, nebula-dense regions,
  station interiors, planetside operations. Moderate rather than tight
  spread because SR's setting (a civilization across 20–30 solar systems)
  naturally produces terrain variety without being defined by it.

**Narrative-grounding requirement.** Any era authored with wide terrain
spread must have a narrative reason for the variance. 1980s has naval +
land + air + desert + jungle as genuinely distinct operational theaters
the Cold War world-builds into. A hypothetical era with wide spread but
no narrative logic ("sometimes the mission is in a desert, sometimes in
a swamp, for no reason") reads to players as random mission generation,
not era identity. Spread must be authored, not random. Each spread
position is answering the question: *why does this era produce this
range of mission types?*

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
Setting per-era (midpoint, spread) is config. Authoring enough layout
variety to express wide-spread eras (1980s especially) requires more
strategic blueprints than tight-spread eras do — each "mission theater"
within a wide-spread era is its own authored layout set.

**Open sub-questions.** Should the authored-layout pool tag blueprints
with a terrain-intensity score so the mission generator can draw from
within-spread ranges per era? My lean: yes, small per-blueprint metadata
field (terrain_intensity: 0–100) plus per-era (midpoint, spread) config,
generator samples layouts whose scores fall within the era's range. This
is small work and directly expresses the refined axis. Confirmation from
the Stage 7 map-gen work before lock.

### Axis 7: Environmental threat *(new — refined Batch 2c, event-based)*

**Definition.** How often does the environment itself fire damage-dealing
events during a mission? Discrete stochastic events that trigger mid-mission,
deal damage-over-time for a bounded window, and revert. Meteor storms,
solar flares, hurricanes, tsunamis, thermal extremes, sonar conditions
degrading catastrophically. The axis measures *event frequency*, not
persistent world state. "Hostile to all agents" rather than "hostile to
one side" — when an event fires, it threatens both sides of the engagement.

**Positions.**
- **Rare** (Roman, Branch 3 DNA) — roughly once per 10+ missions. Narrative
  texture. Players remember the one storm that broke the siege or the
  eclipse that coincided with the ambush. The event is a chronicle-grade
  moment when it fires.
- **Occasional** (1980s, Branch 2 DNA) — roughly 1-in-3 to 1-in-5 missions.
  Tactical consideration players plan around (check sonar conditions,
  watch for storm fronts, factor weather into briefing). The event is
  expected but not guaranteed.
- **Common** (Settled Reach, candidate hallmark-exclusive) — roughly
  1-in-2 missions, capped. Environment is an expected co-antagonist.
  Players develop doctrine for handling environmental events (which units
  to hold in reserve for environment-hardened duties, which zones to
  retreat into during flares). **Cap at every-other-mission maximum** —
  past that frequency, events stop being dramatic and become wallpaper.

**Why the event reframe improves this axis.** Original v1 proposal was
persistent environmental damage fields (nebulae always present, always
damaging). Reframed here as stochastic events firing mid-mission. The
reframe gains:
- **Alignment with existing engine.** `events.py` already handles
  stochastic event firing with threshold triggers, noise, chain spawns,
  and pending queues. Environmental events are a new event type, not a
  new subsystem.
- **Dramatic memorability.** A meteor storm hitting mid-mission is a
  chronicle moment. A persistent radiation zone is a map color. Players
  remember events, not backgrounds.
- **Sacred Principle #1 alignment.** Environmental threat as stochastic
  event is more authentic to the "genuine stochasticity" principle than
  environmental threat as static property.
- **Cost reduction.** Persistent damage fields would have required a new
  tick-engine subsystem (damage-field representation, zone-to-unit
  application per tick). Event-based environmental threat is a new event
  type in an existing event system — much cheaper.

**Cross-axis risk.** After the reframe, overlap with axes 2 and 6 is
minimal. Environmental events are *temporary state during firing*; axes
2 (information) and 6 (terrain) are *baseline state per mission*. A
mission's fog level is its baseline sensor configuration; a solar flare
firing mid-mission temporarily swings sensor range even lower for the
flare's duration, then reverts. Two separate dials picking up different
temporal slices of the same mission — the reframe makes this distinction
cleaner than the persistent-state version had.

**Implementation cost.** **Low-medium.** Down from medium-high in v1.
Required engine work:
- **New event type** in `events.py` — environmental event category with
  trigger (per-era probability roll at mission start, or tick-rate during
  mission), duration, affected zone (spatial or global), damage profile.
  Straightforward addition to an existing system.
- **Per-unit vulnerability / resistance config** per-era — vacuum-rated
  units take less damage from vacuum-breach events. Still needed but small.
- **Renderer visualization** — event-specific overlays when firing (meteor
  streak, storm clouds, radiation warning, nebula shader). Per-event-type
  visual authoring cost is real but bounded.
- **Chronicle hooks** — units lost to environmental events get distinct
  template treatment ("the storm took the Third Cohort before the battle
  was joined"). Chronicle framework already supports this.

No new tick-engine subsystem required. Main new work is the damage-during-event
mechanic and the per-event-type visualizations.

**Open sub-questions.**
1. **Uniform or asymmetric damage?** When an event fires, does everyone in
   the zone take equal damage (uniform) or do environmentally-hardened
   units shrug it off (asymmetric)? Asymmetric creates tactical expression
   (sending hardened units into zones others can't go creates positional
   puzzles no other axis generates). Uniform is simpler to ship. Lean:
   asymmetric, but uniform is an acceptable v1.
2. **Spatial or global events?** Does an event affect a specific zone on
   the map (meteor storm hits a quadrant) or the whole map (tsunami
   floods everywhere)? Lean: mostly spatial (spatial events create
   tactical expression — retreat to the unaffected zone), with occasional
   global events reserved for era-specific dramatic moments (SR solar
   flare = whole map).
3. **Can environmental events chain?** `events.py` already supports chain
   spawns with delays and conditions. Should an environmental event be
   able to spawn a follow-up (meteor storm → ongoing radiation leak →
   eventual dissipation)? Lean: yes, use existing chain mechanics.

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

## The Matrix — Batch 3

Eight axes × three launch eras. One position and a one-line rationale
per cell. Each row is a single axis with three era columns. Positions
marked *(candidate hallmark-exclusive)* are the ones we'll formally
lock in Batch 4's DNA-vs-hallmark pass. The rest are either Branch DNA
(cascades to work eras along the branch) or Roman-specific (standalone,
no cascade).

### Axis 1 — Tempo

| Era | Position | One-line rationale |
|---|---|---|
| **Roman** | Slow (2min+ engagements) | Legion combat is positional and commitment-based; the mission decides who wins over minutes, not seconds. Branch 3 DNA. |
| **1980s** | Medium (1–2min) | Cold War operations reward doctrine execution with coordination windows — the engagement has room for combined-arms cadence. Branch 2 DNA. |
| **Settled Reach** | Fast (30–45s) | Space combat with sensor dominance is decisive when engaged — the fight is about *whether to commit*, not whether to survive. Branch 1 DNA. |

### Axis 2 — Information warfare

| Era | Position | One-line rationale |
|---|---|---|
| **Roman** | Heavy fog | Information travels on horseback. Scouts and runners carry intel days late. Ambush is a first-class threat. Branch 3 DNA. |
| **1980s** | Partial sensor asymmetry | Radar, sonar, intel, ECM all exist but all partial — the Cold War sensor-vs-countersensor arms race is the era's tactical signature. Branch 2 DNA. |
| **Settled Reach** | Near-total awareness | Sensor dominance is technology's default in a post-scarcity sensor regime. Counter-stealth is the cost; the fight is about what to *do* with perfect information. Branch 1 DNA. |

### Axis 3 — Attrition / economy

| Era | Position | One-line rationale |
|---|---|---|
| **Roman** | Slow reinforcement | Legionnaires take years to train. Losses hurt strategically and reinforcements arrive by road, when they arrive. Force preservation is a mission-level objective implicit in every fight. Branch 3 DNA. |
| **1980s** | Industrial replacement | Military-industrial complex produces units at moderate pace. Doctrine and logistics decide campaigns; tactical losses are replaceable over operational timescales. Branch 2 DNA. |
| **Settled Reach** | Rapid recovery | Shipyards and fabricators produce quickly; small forces reconstitute between strikes. Plan quality matters more than preservation. Branch 1 DNA. |

### Axis 4 — Layer access

| Era | Position | One-line rationale |
|---|---|---|
| **Roman** | Terrain-elevation pseudo-layers | No discrete vertical layers. Every unit on "the ground." But mountains, ridges, valleys, defiles create functional elevation differences within the ground plane. 2.5D expresses as terrain, not as layer assignment. Branch 3 DNA. |
| **1980s** | Strict layer lock *(candidate hallmark-exclusive)* | Submarines can exist only underwater; surface vessels only at water level; aircraft only airborne. Transitions are impossible — a sub does not become a plane. The era's tactical puzzle IS cross-layer coordination. |
| **Settled Reach** | Free traversal *(candidate hallmark-exclusive)* | All six unit types can occupy any of the 3–5 layers. Layer transitions are cheap. Vacuum is mechanically neutral — there's no medium to be wrong for. The SR magnum-opus distinctive. |

### Axis 5 — Force scale

| Era | Position | One-line rationale |
|---|---|---|
| **Roman** | Legion/cohort (600–1000) | Classical warfare is mass warfare. Cohorts, centuries, maniples — the spectacle of a Roman legion in the field is the era's visual identity. 1000 top-end gated on the RVO native-extension engine work. Branch 3 DNA. |
| **1980s** | Company/battlegroup (100–300) | Cold War operations are combined-arms mixed formations — a carrier group with escorts, a brigade with armor + infantry + aviation support. Platoon/squadron scale. Branch 2 DNA. |
| **Settled Reach** | Squad/taskforce (20–60) | Post-scarcity sensor dominance + rapid recovery naturally produces precision strike forces over mass fleets. Each unit is a readable high-capability platform. Branch 1 DNA. |

### Axis 6 — Terrain expressiveness (midpoint, spread)

| Era | Position | One-line rationale |
|---|---|---|
| **Roman** | (80, 10–15) — high midpoint, tight spread | Mediterranean operational theater is topologically coherent and finite. Most missions are terrain-rich; variance is narrow. Players settle into "Rome is terrain." Branch 3 DNA. |
| **1980s** | (50, 30–40) — mixed midpoint, wide spread | Cold War proxy-war theater naturally produces naval + land + desert + jungle + urban as genuinely distinct operational environments. The wide spread is narratively grounded in the era's global scope. Branch 2 DNA. |
| **Settled Reach** | (25, 15–25) — low midpoint, moderate spread | Most missions default to open space. Occasional swings into asteroid fields, nebula-dense regions, station interiors, planetary operations. Spread is moderate rather than tight because 20–30 solar systems produce natural terrain variety. Branch 1 DNA. |

### Axis 7 — Environmental threat

| Era | Position | One-line rationale |
|---|---|---|
| **Roman** | Rare (~1 in 10+ missions) | Storms, eclipses, plagues fire rarely but the ones that fire become chronicle-grade moments. "The year the frost came." Branch 3 DNA. |
| **1980s** | Occasional (1-in-3 to 1-in-5) | Sonar conditions, hurricanes, monsoon, sandstorms, sea state degradation. Tactical consideration players check in briefing and plan around. Branch 2 DNA. |
| **Settled Reach** | Common (capped at 1-in-2) *(candidate hallmark-exclusive)* | Solar flares, meteor storms, radiation surges, gravity-well disruption. Environment is an expected co-antagonist. Cap at every-other-mission max — past that frequency events stop being dramatic. |

### Axis 8 — Cross-layer engagement

| Era | Position | One-line rationale |
|---|---|---|
| **Roman** | Ground-bound | Single-layer engagement; elevation grants ranged-fire bonus but no (attacker, target) pair is mechanically impossible — a ballista on a ridge can still shoot a ballista in a valley. Branch 3 DNA. |
| **1980s** | Asymmetric matrix *(candidate hallmark-exclusive)* | Submarines cannot engage aircraft. Specialized pairings (ASW helicopter → submarine; anti-air battery → aircraft) handle specific layer-crossings. The engagement matrix is itself a tactical puzzle. |
| **Settled Reach** | Fully reciprocal *(candidate hallmark-exclusive)* | Any unit can engage any other unit; range and damage may modify but no pair is mechanically impossible. Vacuum is a uniform medium — weapons work across layers by default. |

---

## What The Matrix Reveals

Five observations worth calling out before Batch 4.

### 1. The three launch eras are mechanically distinct on every axis

No two eras share a position on any axis. That's the strongest possible
signal that the axis selection is load-bearing — if two eras had identical
positions on (say) 5 of 8 axes, the axes wouldn't actually be
differentiating eras and the matrix would be overfit. The fact that every
row produces three distinct answers means each axis is doing work. Keep
all 8.

### 2. Settled Reach carries three hallmark-exclusive candidates

Axes 4 (free layer traversal), 7 (common environmental events), and 8
(fully reciprocal engagement) all land at positions no other era occupies
and where Branch 1 work eras should *not* cascade — if work sci-fi eras
also had free layer traversal + common environmental events + fully
reciprocal engagement, Settled Reach would have no distinctive left. Three
hallmark-exclusive axes is the right order of magnitude for a magnum-opus
era. Fewer would dilute its identity; more would leave the work eras
with nothing.

### 3. 1980s carries two hallmark-exclusive candidates

Axes 4 (strict layer lock) and 8 (asymmetric engagement matrix) are 1980s
distinctives. Branch 2 work eras (to be named) should sit at different
positions on these axes — maybe "partial layer lock" (helicopters can
deploy as ground forces, amphibious units cross surface/shallow) or
"mostly-reciprocal engagement with a few exceptions." The 1980s gets its
identity from the *full strictness* of both layer systems simultaneously.
Any work era that is equally strict on both is competing with the hallmark.

### 4. Roman has zero hallmark-exclusive cells — and that's correct

Roman is standalone, outside the branch structure. It has no sibling
work eras to cascade DNA to, so the DNA-vs-hallmark distinction doesn't
apply. Every Roman cell is just "Roman." When Branch 3 ships post-launch,
the Branch 3 work eras will cascade from Roman's positions (with their
own hallmark picking one or two distinctive cells). But that's a future
concern.

### 5. Two cells I'd flag as least certain

- **1980s axis 6 (terrain spread 30–40).** The "wide spread" framing
  works narratively, but 30–40 on a 0–100 scale may be too wide. A mission
  at midpoint 50 with spread 40 ranges from 10 (terrain-light) to 90
  (terrain-heavy), which is nearly the full range of the dial. That risks
  1980s missions feeling like "this mission could be anything," which is
  the random-generation failure mode the axis warned against. **Might
  need to narrow to 20–25 during tuning.**
- **SR axis 7 (common environmental events).** "1-in-2 missions capped"
  is a real design commitment — players will expect an environmental
  event every other mission. If the authoring budget can't produce enough
  event variety, "common" starts to feel like "the same storm every time."
  **Flag for Stage 7 (map gen / event authoring) review — does the
  environmental event type pool have enough variety to sustain 1-in-2
  frequency without repetition fatigue?**

---

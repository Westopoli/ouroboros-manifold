# Combat Visual Polish — Design Questions

> **Transient working doc.** Per `design_rules.md`, this file bridges chats
> during the combat visual polish brainstorming effort. Once all questions
> are CAPTURED into the bible and/or a stage spec, this file is deleted.
>
> **Capture targets:** `docs/bible_history/bible_2_00_combat.md` (unit facing, attack visuals,
> destruction), `game_bible.md` hub (stage roadmap entry), future stage
> spec (Stage 12.5 or equivalent).
>
> **Session:** April 16, 2026

---

## Scope

Pre-Stage 13 polish stage covering three areas:

1. **Unit firing animations** — visual representation of attacks (projectiles,
   beams, volleys, ability effects).
2. **Unit facing** — units rotate to face targets/movement direction.
3. **Combat visual density** — ambient visual elements that make battles feel
   massive without gameplay cost.
4. **Unit destruction** — death sequences with drifting wreckage.
5. **General game polish** — catch-all for remaining visual improvements
   before the friends-ZIP build.

All systems must be **era-agnostic** per Sacred Design Principle #3. The
engine provides abstract events; the era manifest maps them to visual
configs. Every decision below must scale to 20+ eras.

---

## Resolved Decisions

### Q1 — Attack Event Architecture [CAPTURED]

**Decision: Hybrid (Option C).**

Normal auto-attacks are **renderer-inferred**. The Godot renderer tracks
each unit's attack interval and target from the state it already receives.
When the interpolated time crosses an attack boundary, the renderer spawns
the appropriate visual. No engine changes needed for normal attacks.

Ability activations get **explicit engine events** in the delta stream.
New event type: `{"type": "ability", "unit_id": ..., "ability_id": ...,
"target_pos": [...], ...}`. The renderer receives these and plays the
corresponding ability visual with perfect sync.

**Rationale:** Normal attacks happen at regular intervals where inference
is indistinguishable from perfect sync (<50ms error). Abilities are
one-shot dramatic moments where timing precision matters (Barrage landing
exactly when damage hits). The hybrid keeps the delta stream lean (no
hundreds of attack events per tick in large battles) while ensuring the
flashy moments are perfectly synced.

**Bible capture:** New subsection in `docs/bible_history/bible_2_00_combat.md` under Tactical
Simulation Architecture — "Attack Event Protocol."

---

### Q2 — Unit Facing [CAPTURED]

**Decision: Target Priority (Option A).**

The engine sets `facing_rad` per unit per tick using a priority rule:

1. **If the unit has an active target and is attacking:** `facing_rad`
   points at the target.
2. **If the unit is moving with no target** (plain `move` command, or
   `attack_move` with no enemy in range): `facing_rad` points in the
   movement direction.
3. **If the unit is stationary with no target:** `facing_rad` holds its
   last value.

**Rotation speed cap:** Transitions between facing directions use a
rotation speed limit (config value per unit type — Strike rotates fastest,
Siege slowest) so units visually turn rather than snapping. The renderer
interpolates `facing_rad` between ticks using the same linear interpolation
it uses for position.

**Rationale:** Standard RTS model. Units face what they're shooting, face
where they're going otherwise. Retreating units face their pursuer (firing
while backing away), which reads correctly. The rotation speed cap is the
key detail that makes it feel smooth rather than mechanical.

**Bible capture:** New subsection in `docs/bible_history/bible_2_00_combat.md` under Unit Behavior
AI — "Unit Facing."

---

### Q3 — Attack Visual Categories [CAPTURED]

**Decision: Four categories (Option B).**

Every unit attack visual falls into one of four rendering categories.
The era manifest maps each unit type to a category and provides
era-specific visual assets for it.

1. **Projectile** — single object travels from attacker to target. Mesh
   head + GPU particle trail (see Q4). Impact flash on arrival. The
   workhorse for most unit types.

2. **Volley** — multiple projectiles fired in a staggered burst. Same
   rendering as projectile but N objects launched with slight timing and
   angle offsets. Creates visual density for heavy-hitter and sustained-
   fire units.

3. **Beam** — instant line connecting attacker to target for a brief
   duration. Glow, shimmer, thickness variation. Suited for continuous-
   fire or support/healing visual registers.

4. **Area pulse** — expanding ring or sphere centered on a position. No
   travel — blooms outward from the source. Natural fit for Rally (heal
   pulse), Fortify (defensive zone), and AoE ability impacts.

**Settled Reach rough mapping:** Raiders (projectile — fast, small),
Interceptors (projectile — medium), Vanguards (volley — steady stream),
Wardens (beam for auto-attack, area pulse for Rally), Bombards (volley —
heavy, slow), Bastions (projectile — heavy single shots). Final mapping
is per-era config.

**Rationale:** Four categories cover every attack type and ability in the
current roster. Volley is the key differentiator — it makes Bombard
barrages and Vanguard sustained fire visually distinct from Raider
pot-shots. Area pulse handles all support/defensive abilities naturally.
The combinatorial space (4 categories × 6 unit types) produces real visual
variety without per-unit custom work.

**Bible capture:** New subsection in `docs/bible_history/bible_2_00_combat.md` — "Attack Visual
Categories." Era-agnostic category definitions only; per-era mappings live
in the era manifest JSON.

---

### Q4 — Projectile Construction [CAPTURED]

**Decision: Hybrid mesh head + GPU particle trail (Option C).**

Each projectile consists of:

- **Mesh head** — a small 3D mesh (era-specific shape from the manifest:
  glowing sphere for Settled Reach, arrow for Roman, tracer round for
  1980s). Provides shape identity visible at close zoom.
- **GPU particle trail** — a `GPUParticles3D` emitter attached to the
  mesh head, emitting particles along the travel path. Provides atmosphere,
  trailing glow, and the visual continuity with the main menu's particle
  aesthetic.
- **Impact burst** — brief GPU particle burst at the target position on
  arrival.

**LOD tiers for performance at scale (200v200):**

1. **Close/medium zoom:** full mesh + particle trail.
2. **Far zoom:** mesh replaced by billboard sprite, particle trail
   continues.
3. **Very far zoom / frame budget pressure:** billboard only, no trail
   particles.
4. **Extreme density:** projectiles beyond a count threshold are culled
   entirely (damage still applies — this is renderer-only).

**Era manifest fields per unit type:** `projectile_mesh_scene`,
`trail_particle_material`, `impact_particle_scene`, `visual_travel_speed`,
`projectile_scale`, `volley_count` (for volley category), `volley_stagger_sec`.

**Settled Reach identity:** The mesh head is a tiny glowing sphere similar
to the main menu's `world_view_structure.tscn` particles. Trail is a
warm-toned energy ribbon. Impact is a small radial flash. This creates
visual continuity between the menu atmosphere and tactical combat.

**Rationale:** The mesh head is what makes eras visually distinct (arrow vs.
energy bolt vs. tracer). The GPU particle trail is what makes projectiles
feel alive and connected to the game's visual language. LOD tiers are the
performance safety valve — the common case in dense battles degrades
gracefully rather than dropping frames.

**Bible capture:** New subsection in `docs/bible_history/bible_2_00_combat.md` — "Projectile
Rendering." Category-level rendering spec only; LOD thresholds and particle
budgets are tuning values in engine config.

---

### Q5 — Ability Visual Treatment [CAPTURED]

**Decision: Same category with enhanced parameters + shared overlay
library (Option B).**

Abilities use their unit's normal attack visual category as a base but
with enhanced parameters (more projectiles, bigger trails, brighter
emission). On top of the enhanced base, a shared library of **overlay
effects** creates the visual step-up that says "ability in progress":

1. **Ring telegraph** — expanding ground ring showing the affected area.
   Used for Barrage (danger zone), Fortify (defensive zone), Rally (heal
   radius). Color-coded: hostile/offensive abilities use warm/red tones,
   friendly/defensive abilities use cool/blue tones. Ring persists for
   the ability's duration, then fades.

2. **Unit glow/aura** — the casting unit gets a brief full-body emission
   boost via a shader uniform toggle. Used for Surge (speed burst glow),
   Brace (defensive stance glow). Color matches the ability's
   hostile/friendly register. Duration matches the ability's active
   window.

3. **Screen-space distortion** — subtle post-process ripple centered on
   the ability's effect point. Reserved for the most dramatic moments
   only (Barrage impact, large-scale Rally). Brief duration (0.3–0.5s).
   Tunable intensity — should be atmospheric, not nauseating.

**Ability → overlay mapping:**

| Ability | Base category | Overlays |
|---------|--------------|----------|
| Raider — Surge | Projectile (enhanced) | Unit glow |
| Interceptor — Intercept | Projectile (enhanced) | Unit glow (on trigger) |
| Vanguard — Brace | — (no attack change) | Unit glow |
| Warden — Rally | Area pulse | Ring telegraph + distortion |
| Bombard — Barrage | Volley (heavy enhanced) | Ring telegraph + distortion |
| Bastion — Fortify | — (no attack change) | Ring telegraph (persistent) |

**Era-agnostic design:** The three overlay types (ring, glow, distortion)
are engine-level rendering behaviors, not era-specific assets. Ring color,
glow intensity, and distortion strength are config values. Eras do not need
to author custom overlay assets — the overlays are abstract visual
communication tools.

**Rationale:** The overlay library is small (3 effect types) and reusable
across all abilities and all eras. Ring telegraphs alone do enormous
communication work — they tell the player where an ability is active and
whether it's hostile or friendly. Combined with enhanced-parameter base
attacks, abilities feel like distinct events without requiring per-ability
custom visual sequences that would scale to 120+ assets across 20+ eras.

**Bible capture:** New subsection in `docs/bible_history/bible_2_00_combat.md` — "Ability Visual
Treatment."

---

### Q6 — Impact Feedback [CAPTURED]

**Decision: Impact flash + hit reaction, cinematic register (Option B,
refined).**

When an attack hits a target, two layers of visual feedback play:

1. **Impact particle burst** — GPU particles spawn at the target's
   position and drift outward slowly over 0.5–1.0s with gentle
   deceleration. Small debris-like particles that tumble and fade. Energy
   dissipation, not explosion. Color matches the attacker's projectile
   trail color. Burst scale varies with damage dealt (Bombard hits produce
   larger bursts than Raider hits).

2. **Hit reaction (slow emission bloom)** — the target unit's material
   receives a slow additive emission spike: 0.3–0.5s rise, 0.3s fade.
   A warm glow that spreads across the model's surface and dissipates.
   NOT a snappy white-frame flash — the cinematic register demands
   everything feel massive and deliberate.

**Explicitly excluded:**

- **Micro-jitter / position displacement.** At the cinematic scale and
  pacing, jitter reads as a rendering bug, not impact. Units absorb hits
  stoically. The bloom is the feedback.
- **Progressive damage state visuals** (scorch marks, hull breaches at HP
  thresholds). Deferred to per-era polish passes post-friends-ZIP. The
  system can be added later as an additional shader overlay layer without
  changing the impact feedback architecture.

**Timing philosophy:** All impact timing values are tuning parameters in
the era manifest. The Settled Reach uses the cinematic register (slow
blooms, drifting particles). Faster-paced eras (1980s tank combat) can
tighten these timings. The system is the same; the feel varies per era.

**Aesthetic reference:** Star Wars: Revenge of the Sith opening battle.
Turbolaser bolts connecting with capital ships — the glow that spreads
across the hull, debris drifting away slowly, everything conveying mass
and scale. Not twitchy arcade impacts.

**Bible capture:** New subsection in `docs/bible_history/bible_2_00_combat.md` — "Impact Feedback."

---

### Q7 — Unit Destruction [CAPTURED]

**Decision: Bloom + drift wreckage with LOD demotion (Option B variant,
no fragment breakup).**

When a unit reaches 0 HP, the engine removes it from gameplay state. The
renderer plays a destruction sequence and manages the resulting wreckage
as a renderer-only visual artifact:

**Destruction sequence (2–3 seconds):**

1. **Death bloom** (0.5s) — the unit flares with a slow emission burst,
   brighter than any hit flash. The unmistakable "moment of death."
2. **Damage onset** — persistent damage particle emitters activate on
   the model: fire, sparks, venting atmosphere (era-specific particle
   materials from the manifest). These were not present during combat —
   they signal the unit is now dead.
3. **Drift begins** — the unit begins drifting in a random-ish direction
   biased by its last movement heading (so the drift feels physical, not
   arbitrary). Slow, decelerating. The unit no longer responds to any
   commands or collision.
4. **Darkening** — the unit's material gradually shifts toward a dark,
   desaturated version of its faction color over 3–5 seconds, signaling
   its transition from active unit to battlefield debris.

**Wreckage lifecycle and LOD demotion:**

| Phase | Duration | Visual state | Cost |
|-------|----------|-------------|------|
| Fresh wreck | 0–5s | Full 3D model, damage particles (fire/sparks), slow drift | Moderate |
| Cooling wreck | 5–15s | Particles reduced to single faint emitter (smoke). Material fully darkened. | Low |
| Cold wreck | 15s+ | Particles off. Dark, drifting mesh only. | Near-zero |

Cold wrecks persist as dark debris drifting through the battlefield until
they leave the visible area + a buffer distance, then despawn.

**Performance safety — hybrid cull:**

When the frame budget is tight, cold wrecks are despawned **farthest from
camera center first**. Camera-center distance (not battle-center distance)
is the metric — if the player is zoomed into one flank, cold wrecks on the
opposite flank are culled first since no one is looking at them. Fresh and
cooling wrecks are never culled (their destruction sequences are active
visual events the player may be watching).

**Strike squads:** Individual squad members play abbreviated destruction
sequences (bloom + fade over 1.0s, staggered across members). No drift
phase — small ships simply flare and go dark. A squad wipe reads as a
cascade of small fades, not a series of capital-ship death events.

**No fragment breakup** at this stage. Fragment meshes (model splitting
into 2–4 tumbling pieces) are deferred as a future per-era polish option.
The destruction system architecture supports adding a fragment phase
between bloom and drift without redesign.

**Bible capture:** New subsection in `docs/bible_history/bible_2_00_combat.md` — "Unit Destruction
Visuals."

---

## Open Questions

### Q8 — Ambient Battle Density [CAPTURED]

**Decision: Two-layer hybrid — GPU particle haze base + battle-biased
Bézier flyby ships (Option C from initial options, refined to sub-option B
for flyby behavior).**

The battlefield uses two renderer-only visual layers to create a
massive-engagement atmosphere:

1. **Particle haze (always-on base)** — a large-area `GPUParticles3D`
   emitter covering the engagement zone, spawning small glowing dots,
   streaks, and debris particles. Era-manifest-driven material, density
   config slider. Near-zero rendering cost.

2. **Flyby ships (battle-biased accents)** — 10–20 very-low-poly meshes
   (8–20 triangles) on randomized Bézier curve paths through the
   engagement area, each with a GPU particle trail. Spawn points and
   curve control points are **biased toward active engagement clusters**
   via a lightweight combat heatmap — denser ambient activity near
   fighting, sparser near quiet flanks. Floor density ensures quiet areas
   still get occasional traffic. Ships spawn at boundary, fly curve,
   despawn on exit. No collision, no gameplay interaction.

**Performance degradation:** Flyby ships cut first under frame pressure;
particle haze carries alone. Particle density further reducible via config.

**Era manifest fields:** `flyby_mesh_scene`, `flyby_trail_material`,
`ambient_particle_material`.

**Bible capture:** New subsection in `docs/bible_history/bible_2_00_combat.md` — "Ambient Battle
Density."

---

### Q9 — Additional Polish Scope [CAPTURED]

**Decision: Three items in scope, two deferred.**

**In Stage 12.5 scope:**

1. **Selection circle recolor** — dim the selection circle and match it
   to the player's faction color. No other selection system changes; the
   existing implementation is otherwise fine.

2. **HUD animation refinement** — smooth fade/slide transitions on panel
   appear/disappear, cooldown sweep animations on ability icons,
   consistent timing across HUD state changes. Implements the Stage 9
   "Terminal Meets Glass" aesthetic spec.

3. **Edge-scroll speed setting** — player-configurable scroll speed for
   edge-of-screen mouse panning. Exposed in the settings screen. This is
   a functional feature (player control over camera behavior), not
   cosmetic tuning.

**Deferred to post-Stage 13:**

- **Minimap visual polish** — current minimap is functional and readable.
- **Sound placeholder hooks** — event architecture from Q1 already emits
  the signals sound would consume; explicit stubs are unnecessary
  scaffolding at this stage.

**Bible capture:** No spoke edits needed — these are implementation-scope
items captured in the Stage 12.5 hub roadmap entry and stage spec.

---

## Pending Bible Edits

All bible captures complete. The following subsections were added to
`docs/bible_history/bible_2_00_combat.md`:

1. ✅ **"Attack Event Protocol"** — hybrid model.
2. ✅ **"Unit Facing"** — target-priority rule.
3. ✅ **"Attack Visual Categories"** — four categories.
4. ✅ **"Projectile Rendering"** — mesh head + GPU particle trail.
5. ✅ **"Ability Visual Treatment"** — enhanced params + overlay library.
6. ✅ **"Impact Feedback"** — slow emission bloom + drifting particles.
7. ✅ **"Unit Destruction Visuals"** — bloom + drift + LOD demotion.
8. ✅ **"Ambient Battle Density"** — particle haze + battle-biased flybys.

Hub edit: `game_bible.md` Stage 12.5 roadmap entry updated (v2.13) with
ambient density resolution and Q9 polish scope.

---

## Handoff Note

**Session 1 (April 16, 2026):**

Resolved Q1–Q7 covering the full attack visual pipeline from event
architecture through destruction. Cinematic register established (Star
Wars: Revenge of the Sith opening as reference — slow, massive, weighty).
Key architectural decisions: hybrid attack events (renderer-inferred
normal + engine-emitted abilities), four visual categories, mesh+particle
projectiles with LOD, overlay library for abilities, slow-bloom impact
feedback, drifting wreckage with LOD demotion cull.

**Session 2 (April 17, 2026):**

Resolved Q8 (ambient battle density) and Q9 (remaining polish scope).
Ambient density: two-layer hybrid — GPU particle haze as always-on base,
10–20 low-poly flyby ships on battle-biased Bézier paths as accent layer.
Polish scope: selection circle recolor (dimmer, faction-colored), HUD
animation refinement (Stage 9 aesthetic), edge-scroll speed setting
(player-configurable). Minimap and sound hooks deferred to post-Stage 13.

All bible captures complete. `docs/bible_history/bible_2_00_combat.md` updated with "Ambient
Battle Density" subsection. `game_bible.md` updated to v2.13 with
finalized Stage 12.5 roadmap entry.

**All design questions resolved. This design doc can be archived once
the Stage 12.5 spec is written.**

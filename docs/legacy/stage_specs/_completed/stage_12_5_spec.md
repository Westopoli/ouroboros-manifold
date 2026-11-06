# Stage 12.5 — Combat Visual Polish

## Goal

Make tactical combat visually alive for the friends-ZIP build: units face their targets, attacks are visible, impacts read clearly, destroyed units leave drifting wreckage, and the battlefield feels massive through ambient visual density. Three additional polish items bring the tactical experience up to first-impression quality: dimmer faction-colored selection circles, smooth HUD transitions, and player-configurable edge-scroll speed.

## Bible References

Read the hub (`game_bible.md`) plus these spokes:

- `docs/bible_history/bible_2_00_combat.md` → "Combat Visuals" section (attack visual categories, projectile rendering, ability visual treatment, impact feedback, unit destruction visuals, ambient battle density). Also "Unit Combat Categories" (Strike/Line/Siege), "Unit Roster" (6 base types), "Abilities — One Per Unit" (ability definitions), "Unit Behavior AI" (unit facing, attack event protocol), "Tactical Simulation Architecture" (tick loop, delta stream).
- `animation_strategy.md` → HUD animation design language (two-layer shader+glyph hybrid, choreography principles). Referenced for HUD animation refinement.

Do not read `docs/bible_history/bible_2_00_simulation.md`, `docs/bible_history/bible_2_00_missions.md`, `docs/bible_history/bible_2_00_chronicle.md`, `docs/bible_history/bible_2_00_world.md`, `docs/bible_history/bible_2_00_antagonist.md`, `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/), or `docs/bible_history/bible_2_00_ai_pipeline.md` — not relevant to Stage 12.5. Stage 8 spec is consulted for the tactical bridge WebSocket protocol and renderer architecture. Stage 8.5 spec is consulted for `EraThemeResolver` and era manifest structure. Stage 9 spec is consulted for UIDataBus, settings screen, and HUD layout.

## Context

### What exists

- **Stage 6** — headless tactical engine with deterministic tick loop, unit state (position, HP, target, movement heading), attack resolution, ability activation. Units have stats, targets, and attack intervals. The engine resolves damage per tick. No visual representation of attacks — damage "just happens" in the engine state.
- **Stage 7 / 7.5** — map generation, enemy macro behavior scripts. Reinforcement structures with production.
- **Stage 8** — Godot renderer connected via WebSocket bridge. Units render as 3D meshes at interpolated positions. Selection system with selection circles. Camera with zoom, pan, edge-scroll. The renderer receives periodic full snapshots and per-tick delta updates from the engine. `TacticalBridge` manages the WebSocket connection. `UnitManager` tracks Godot node instances per unit ID.
- **Stage 8.5** — `EraThemeResolver` autoload resolving era-specific assets. Per-era JSON manifests defining mesh scenes, materials, colors. 3D tactical rendering with era-themed unit meshes.
- **Stage 9** — UI shell with `UIDataBus` singleton, `SceneRouter`, settings screen, HUD with unit info panels and ability cooldown indicators.
- **Stages 10–12** — live sim data, world view, chronicle scroll, seamless transitions, debrief, autosave, bug report. All complete and stable.

### What Stage 12.5 adds

Stage 12.5 adds visual systems to the existing tactical renderer. No new scenes. No changes to the engine's gameplay logic. All additions are renderer-side visual layers that consume existing engine state.

**Engine-side (Python) — two additions:**
1. `facing_rad` field added to per-unit state, updated per tick by the engine's behavior AI.
2. Ability activation events added to the delta stream.

**Renderer-side (Godot) — everything else:**
1. Unit facing interpolation (rotate unit meshes to match `facing_rad`).
2. Attack visual spawning (infer normal attacks from state, receive ability events from delta stream).
3. Four visual category renderers (projectile, volley, beam, area pulse).
4. Ability overlay effects (ring telegraph, unit glow, screen-space distortion).
5. Impact feedback (emission bloom on target, drifting impact particles).
6. Unit destruction sequences (bloom → damage particles → drift → darkening → wreckage lifecycle).
7. Ambient battle density (particle haze emitter + battle-biased flyby ship pool).
8. Selection circle recolor (dimmer, faction-colored).
9. HUD animation refinement (smooth transitions, cooldown sweeps).
10. Edge-scroll speed setting (player-configurable, exposed in settings).

### Aesthetic register

All visual timing in the Settled Reach era uses a **cinematic register**. The reference is the opening battle of Star Wars: Revenge of the Sith — turbolaser bolts connecting with capital ships, glow spreading across hulls, debris drifting slowly. Everything conveys mass and scale. Nothing snaps or pops. Other eras may tighten timings through their manifest configs, but the rendering systems are identical.

## What to Build

### New files — Godot

```
scenes/tactical/visuals/
├── attack_visual_manager.gd            - Spawns and manages all attack visuals. Infers normal
│                                         attacks from unit state. Receives ability events from
│                                         delta stream. Delegates to category renderers.
├── projectile_renderer.gd              - Projectile category: mesh head + GPU particle trail +
│                                         impact burst. Handles single projectile and volley
│                                         (volley = N projectiles with stagger). LOD tiers.
├── beam_renderer.gd                    - Beam category: line connecting attacker to target,
│                                         glow/shimmer, thickness variation, timed fade.
├── area_pulse_renderer.gd              - Area pulse category: expanding ring/sphere from source
│                                         position, fade on completion.
├── ability_overlay_manager.gd          - Overlay library: ring telegraph, unit glow, screen-space
│                                         distortion. Maps ability activations to overlay combos.
├── impact_feedback_manager.gd          - Impact particle bursts + hit reaction emission bloom.
│                                         Consumes damage events from unit state changes.
├── destruction_manager.gd              - Death sequences: bloom → damage particles → drift →
│                                         darkening. Wreckage lifecycle (fresh/cooling/cold).
│                                         LOD demotion. Camera-distance hybrid cull.
├── ambient_density_manager.gd          - Two-layer ambient system: particle haze emitter +
│                                         battle-biased flyby ship pool. Bézier path generation.
│                                         Combat heatmap for spawn biasing.
├── flyby_ship_pool.gd                  - Object pool for flyby ship instances. Spawn, path
│                                         evaluation, despawn, trail management.
└── combat_heatmap.gd                   - Lightweight spatial heatmap tracking where combat is
                                          active. Consumed by ambient_density_manager for
                                          flyby spawn biasing.
```

### New files — Python

```
sim/
└── facing.py                           - facing_rad update logic. Target-priority rule:
                                          (1) attacking → face target, (2) moving → face heading,
                                          (3) stationary → hold last value. Rotation speed cap
                                          per unit type.
```

### Modified files — Godot

**`autoload/era_theme_resolver.gd`** — additive. New manifest field accessors:
- `get_attack_visual_config(unit_type: String) → Dictionary` — returns category, mesh scene, trail material, impact scene, visual travel speed, scale, volley count/stagger.
- `get_flyby_config() → Dictionary` — returns flyby mesh scene, trail material, ambient particle material.

**`scenes/tactical/unit_manager.gd`** — additive. Per-unit changes:
- Apply `facing_rad` interpolation to unit mesh rotation each frame.
- On unit HP reaching 0, hand off to `destruction_manager` instead of immediately freeing the node.
- Emit damage-taken signal consumed by `impact_feedback_manager`.

**`scenes/tactical/tactical_bridge.gd`** — additive. Parse new `ability` event type from delta stream. Forward to `attack_visual_manager`.

**`scenes/tactical/hud.gd`** — modification. Add smooth fade/slide transitions on panel show/hide. Add cooldown sweep animation on ability icons. Consistent transition timing across all state changes.

**`scenes/tactical/selection_manager.gd`** (or equivalent) — modification. Change selection circle color from current bright color to a dimmer version of the player's faction color.

**`scenes/settings/settings.gd`** — additive. Add "Edge Scroll Speed" slider in camera settings subsection. Bind to config value.

**`scenes/tactical/camera_controller.gd`** (or equivalent) — modification. Read edge-scroll speed from config instead of hardcoded value.

### Modified files — Python

**`sim/engine.py`** (or equivalent tick loop) — additive. Call `facing.update_facing()` per unit per tick. Include `facing_rad` in per-unit state output.

**`sim/config.py`** — new constants:

```python
# Unit facing
FACING_ROTATION_SPEED_STRIKE = 6.0     # rad/s — fastest
FACING_ROTATION_SPEED_LINE = 4.0       # rad/s
FACING_ROTATION_SPEED_SIEGE = 2.5      # rad/s — slowest

# Ability events
ABILITY_EVENT_TYPE = "ability"

# Edge scroll (default, player-configurable)
EDGE_SCROLL_SPEED_DEFAULT = 800.0      # px/s
EDGE_SCROLL_SPEED_MIN = 200.0
EDGE_SCROLL_SPEED_MAX = 2000.0
```

**`sim/delta_encoder.py`** (or equivalent) — additive. Encode ability activation events into the delta stream as `{"type": "ability", "unit_id": ..., "ability_id": ..., "target_pos": [...]}`.

## Input/Output Shapes

### facing_rad in unit state (Python → Godot via delta stream)

```json
{
  "unit_id": "u_042",
  "facing_rad": 1.57,
  "...": "existing unit fields unchanged"
}
```

`facing_rad` is a float in radians [0, 2π). Included in every per-unit state update. The renderer interpolates between ticks using the same linear interpolation used for position.

### Ability event in delta stream (Python → Godot)

```json
{
  "type": "ability",
  "unit_id": "u_042",
  "ability_id": "surge",
  "target_pos": [1200.0, 800.0],
  "target_unit_id": null,
  "duration_ticks": 100
}
```

Emitted once when an ability activates. The renderer uses this to trigger the appropriate visual category enhancement + overlay combo. `target_pos` is always present. `target_unit_id` is present for targeted abilities (Intercept), null for positional/self abilities.

### Attack visual config from era manifest (via EraThemeResolver)

```json
{
  "raider": {
    "category": "projectile",
    "projectile_mesh_scene": "res://assets/settled_reach/projectiles/raider_bolt.tscn",
    "trail_particle_material": "res://assets/settled_reach/particles/energy_trail_warm.tres",
    "impact_particle_scene": "res://assets/settled_reach/particles/impact_flash_small.tscn",
    "visual_travel_speed": 1200.0,
    "projectile_scale": 0.3,
    "volley_count": 1,
    "volley_stagger_sec": 0.0
  },
  "bombard": {
    "category": "volley",
    "projectile_mesh_scene": "res://assets/settled_reach/projectiles/bombard_bolt.tscn",
    "trail_particle_material": "res://assets/settled_reach/particles/energy_trail_heavy.tres",
    "impact_particle_scene": "res://assets/settled_reach/particles/impact_flash_large.tscn",
    "visual_travel_speed": 600.0,
    "projectile_scale": 0.6,
    "volley_count": 5,
    "volley_stagger_sec": 0.08
  }
}
```

Six entries (one per unit type). All values visual-only — damage is resolved by the engine independently.

### Flyby and ambient config from era manifest

```json
{
  "ambient": {
    "flyby_mesh_scene": "res://assets/settled_reach/ambient/flyby_fighter.tscn",
    "flyby_trail_material": "res://assets/settled_reach/particles/flyby_trail.tres",
    "ambient_particle_material": "res://assets/settled_reach/particles/battle_haze.tres"
  }
}
```

### Ability-to-overlay mapping (hardcoded in ability_overlay_manager.gd)

```gdscript
const ABILITY_OVERLAYS = {
    "surge":     { "base_enhance": true,  "overlays": ["unit_glow"] },
    "intercept": { "base_enhance": true,  "overlays": ["unit_glow"] },
    "brace":     { "base_enhance": false, "overlays": ["unit_glow"] },
    "rally":     { "base_enhance": true,  "overlays": ["ring_telegraph", "distortion"] },
    "barrage":   { "base_enhance": true,  "overlays": ["ring_telegraph", "distortion"] },
    "fortify":   { "base_enhance": false, "overlays": ["ring_telegraph"] },
}
```

Ring telegraph color: warm/red for hostile abilities (barrage), cool/blue for friendly (rally, fortify). Defined as config constants.

### Combat heatmap (internal to ambient_density_manager)

```gdscript
# Spatial grid tracking combat intensity.
# Each cell accumulates a score when units in that cell are attacking.
# Decays over time. Consumed by flyby spawn weighting.
# Cell size, decay rate, and bias strength are tuning values.
```

Not exposed outside the ambient density system. Engineering decision — implementation detail.

## Integration Points

- **Stage 8 tactical bridge.** The delta stream gains `facing_rad` on existing unit updates and a new `ability` event type. The bridge parser is extended to handle the new event. Existing delta fields are unchanged.
- **Stage 8 unit manager.** Units gain facing rotation and destruction handoff. Existing unit lifecycle (spawn, update position, free) is unchanged — destruction adds a post-free visual phase.
- **Stage 8.5 era manifest.** New fields added to the per-era JSON manifest for attack visuals, flyby config, and ambient particles. Existing manifest fields unchanged. `EraThemeResolver` gains new accessor methods.
- **Stage 9 HUD.** Existing panel logic unchanged — transitions are added around existing show/hide calls. Cooldown indicators gain sweep animation. No new HUD elements.
- **Stage 9 settings.** One new slider in the settings screen for edge-scroll speed.
- **Kill switches:**
  - `ENABLE_STAGE12_5_ATTACK_VISUALS = true` — if false, attacks resolve silently as before. No projectiles, beams, pulses, or impact feedback rendered.
  - `ENABLE_STAGE12_5_DESTRUCTION = true` — if false, units disappear instantly on death (Stage 8 behavior).
  - `ENABLE_STAGE12_5_AMBIENT = true` — if false, no particle haze or flyby ships. Battlefield is gameplay units only.
  - `ENABLE_STAGE12_5_HUD_ANIM = true` — if false, HUD panels pop in/out without transitions (Stage 9 behavior).

## Implementation Checkpoints

### Checkpoint A — Unit Facing (Engine + Renderer)

**Build:** `sim/facing.py` + engine integration. Add `facing_rad` to per-unit state. Target-priority rule: (1) attacking → face target, (2) moving → face heading, (3) stationary → hold last value. Rotation speed cap per unit type from config. Renderer-side: interpolate `facing_rad` in `unit_manager.gd`, apply to mesh rotation each frame.

**Test:** 50v50 scripted engagement. Units attack-moving toward enemies. Verify: attacking units face their targets, moving units face movement direction, stationary units hold last facing. Verify rotation is smooth (no snapping) — print max angular velocity per unit type and confirm it respects the config cap.

**Print:** 10-unit sample: unit_id, category, state (attacking/moving/idle), facing_rad, target_pos or heading. Max angular velocity per category across all units.

**Verify:** Facing matches priority rule. No snapping — max angular velocity ≤ config cap. Visual rotation smooth at 60fps.

⛔ STOP.

### Checkpoint B — Attack Visual Manager + Projectile Renderer

**Build:** `attack_visual_manager.gd` and `projectile_renderer.gd`. The manager tracks each unit's attack interval and target from existing state. When interpolated time crosses an attack boundary, it spawns a projectile visual via the projectile renderer. Mesh head from era manifest, GPU particle trail, impact burst on arrival. Volley support (N projectiles with stagger timing).

**Test:** 20v20 engagement. Raiders (single projectile) and Bombards (volley) attacking. Verify: projectiles travel from attacker to target, trails render, impact bursts play on arrival. Volley fires N projectiles with visible stagger. Count active projectile instances.

**Print:** Active projectile count (peak and mean over 30s), volley stagger timing samples, frame time p50/p95.

**Verify:** Projectiles originate from attacker, arrive at target. Trails visible. Volleys stagger correctly. Frame time < 16ms p95 at 20v20.

⛔ STOP.

### Checkpoint C — Beam + Area Pulse Renderers

**Build:** `beam_renderer.gd` and `area_pulse_renderer.gd`. Beam: line from attacker to target with glow, shimmer, thickness variation, timed fade. Area pulse: expanding ring from source position, fade on completion. Wire both into `attack_visual_manager`.

**Test:** Scripted scenario with Warden (beam auto-attack) and Rally (area pulse). Verify: beam connects attacker to target, persists for configured duration, fades. Area pulse expands from source, fades. Test with multiple simultaneous beams and pulses.

**Print:** Active beam/pulse count, duration samples, frame time p50/p95.

**Verify:** Beams connect correct units. Pulses expand from correct positions. Both fade cleanly. No visual artifacts on despawn.

⛔ STOP.

### Checkpoint D — Ability Events + Overlay Library

**Build:** Engine-side: add ability event emission to delta stream in `delta_encoder.py`. Renderer-side: `ability_overlay_manager.gd` — ring telegraph, unit glow, screen-space distortion. Parse ability events in `tactical_bridge.gd`. Wire attack visual manager to use enhanced parameters on ability activation.

**Test:** Trigger each of the 6 abilities in a scripted scenario. Verify: each ability produces the correct overlay combo per the mapping table. Ring telegraphs show correct area and color (warm for hostile, cool for friendly). Unit glow activates on the casting unit. Screen-space distortion plays for Barrage and Rally. Enhanced projectile/volley parameters visible (bigger trails, brighter emission).

**Print:** Per-ability: ability_id, overlays triggered, ring color, glow duration, distortion intensity. Frame time p50/p95 during simultaneous abilities.

**Verify:** All 6 abilities match the mapping table. Ring colors correct. Glow durations match ability windows. Distortion brief and atmospheric. No frame drops during multi-ability moments.

⛔ STOP.

### Checkpoint E — Impact Feedback

**Build:** `impact_feedback_manager.gd`. Two layers: (1) impact particle burst at target position — drifting debris particles, 0.5–1.0s, color matches attacker's trail. (2) Hit reaction emission bloom on target unit — slow additive emission spike, 0.3–0.5s rise, 0.3s fade. Burst scale varies with damage dealt.

**Test:** 50v50 engagement. Verify: every hit produces a visible impact burst and bloom on the target. Bombard hits produce larger bursts than Raider hits. Bloom is slow and warm, not snappy. No micro-jitter on target units.

**Print:** Impact count over 30s, burst scale range (min/max), bloom timing samples, frame time p50/p95.

**Verify:** Impacts visible on all hits. Scale varies with damage. Bloom reads as cinematic (slow rise, slow fade). No position displacement on targets. Frame budget holds at 50v50.

⛔ STOP.

### Checkpoint F — Unit Destruction

**Build:** `destruction_manager.gd`. Sequence: death bloom (0.5s) → damage particle onset → drift (biased by last heading) → darkening (3–5s to desaturated faction color). Wreckage lifecycle: fresh (0–5s, full model + particles) → cooling (5–15s, single faint emitter, darkened) → cold (15s+, no particles, dark mesh). Cold wrecks despawn on leaving visible area + buffer. Strike squads: abbreviated bloom + fade (1.0s), no drift. Camera-distance hybrid cull for cold wrecks under frame pressure.

**Test:** 50v50 engagement run to completion (one side eliminated). Verify: every death triggers the full sequence. Wrecks transition through all three lifecycle phases. Cold wrecks drift and eventually despawn. Strike squad deaths are abbreviated. Spawn a 200v200, eliminate one side, verify cull behavior — cold wrecks farthest from camera despawn first.

**Print:** Active wreck count over time (fresh/cooling/cold breakdown), cull events (count, distance threshold), peak wreck count, frame time p50/p95 at peak wreckage.

**Verify:** Lifecycle phases timed correctly. Darkening visible. Drift direction correlates with last heading. Strike deaths abbreviated. Cull fires farthest-first. Frame time < 16ms p95 at peak.

⛔ STOP.

### Checkpoint G — Ambient Battle Density

**Build:** `ambient_density_manager.gd`, `flyby_ship_pool.gd`, `combat_heatmap.gd`. Particle haze: large-area `GPUParticles3D` emitter covering engagement zone, era-manifest material, density config. Flyby ships: pool of 10–20 low-poly meshes on Bézier paths with GPU particle trails. Spawn points biased toward combat heatmap hotspots. Floor density for quiet areas.

**Test:** 50v50 engagement with fighting concentrated on one flank. Verify: particle haze visible across battlefield. Flyby ships present — more near the fighting, fewer (but nonzero) on the quiet flank. Ships follow smooth curved paths, not straight lines. Trails visible. Ships despawn on exit. Test frame budget: disable ambient layer, measure baseline. Re-enable, measure overhead.

**Print:** Active flyby count (mean/peak), heatmap hotspot positions vs flyby spawn positions (correlation check), particle emitter count, frame time delta (ambient on vs off), overall p50/p95.

**Verify:** Flyby density correlates with combat activity. Floor density present on quiet areas. Paths smooth (no sharp angles). Ambient overhead < 2ms at 50v50. Kill switch off → no ambient elements, no crash.

⛔ STOP.

### Checkpoint H — Selection + HUD + Settings Polish

**Build:** Three items:
1. Selection circle recolor — dim the circle, match player faction color. Modify `selection_manager.gd`.
2. HUD animation — smooth fade/slide transitions on panel show/hide, cooldown sweep on ability icons. Modify `hud.gd`.
3. Edge-scroll speed setting — add slider to settings screen, bind to config, read in camera controller.

**Test:** (1) Select units — verify circle is dimmer and matches faction color. (2) Open/close unit info panels, trigger ability cooldowns — verify smooth transitions, no pop-in. (3) Change edge-scroll speed in settings — verify camera pans at the configured speed. Test min and max values.

**Print:** Selection circle color values (RGB + alpha). HUD transition durations. Edge-scroll speed at min/default/max settings.

**Verify:** Circle visually dimmer than before, correct faction color. HUD transitions smooth, no pop/flash. Edge-scroll speed responds to setting across full range. Settings persist across scene changes.

⛔ STOP.

### Checkpoint I — LOD + Performance Scaling (200v200)

**Build:** No new systems. Implement LOD tiers for projectiles (close: mesh+trail → far: billboard+trail → very far: billboard only → extreme density: cull). Tune particle budgets, flyby count, wreckage cull thresholds. All values in config.

**Test:** 200v200 engagement, full duration. All visual systems active simultaneously: projectiles, volleys, beams, pulses, impacts, destruction, wreckage, ambient density, abilities triggering. Measure frame time at three zoom levels (close, medium, far). Measure with ambient on vs off.

**Print:** Frame time p50/p95/p99 at each zoom level. Active visual element counts at peak: projectiles, beams, pulses, wrecks (by phase), flybys, particles. LOD tier distribution (how many projectiles at each tier). Memory footprint.

**Verify:** 60fps (p95 < 16ms) at medium and far zoom with all systems. Close zoom < 20ms p95 (acceptable dip during peak action). LOD transitions not visually jarring. Memory stable (no growth over 5-minute engagement).

⛔ STOP.

### Checkpoint J — Full Integration + Visual Review

**Build:** No new code. Full loop test with all Stage 12.5 systems active alongside Stages 8–12.

**Test:** Complete session: onboarding → first mission (verify all combat visuals, destruction, ambient density, HUD transitions, selection circles, edge-scroll setting) → debrief → narration → second mission → mid-mission quit → resume → complete. Verify all kill switches: each independently false produces graceful degradation with no crashes.

**Print:** Session log noting each visual system observed working. Kill switch test results (4 switches × on/off). Frame time summary across both missions.

**Verify:** All visual systems active and visually correct. No regressions to Stage 12 systems. Kill switches all degrade gracefully. Edge-scroll setting persists across missions. Full loop clean.

⛔ STOP.

### Checkpoint K — Performance + Stability (Final)

**Build:** No new code. Performance tuning + bug fixes from Checkpoint J findings.

**Test:** Three full sessions (different seeds), 2+ chapters each, 200v200 engagements. Measure: frame time at each zoom level, peak visual element counts, memory footprint, LOD behavior.

**Print:** Perf table: frame time p50/p95/p99 per zoom level, peak projectile/wreck/flyby counts, memory at start/peak/end, LOD tier distribution.

**Verify:** 60fps (p95 < 16ms) at medium/far zoom in 200v200. Close zoom < 20ms p95. Memory stable across sessions. No visual artifacts. No crashes across 3 sessions.

⛔ STOP.

## Invariants

- **I1 — Facing accuracy.** `facing_rad` matches the target-priority rule every tick: attacking → face target, moving → face heading, stationary → hold.
- **I2 — Facing rotation cap.** Angular velocity per tick never exceeds the configured rotation speed for the unit's category.
- **I3 — Attack visual sync.** Renderer-inferred normal attack visuals fire within 50ms of the engine's attack resolution (one tick tolerance).
- **I4 — Ability event delivery.** Every engine-emitted ability event produces the correct overlay combo per the mapping table. No missed events, no phantom events.
- **I5 — Impact completeness.** Every damage event produces a visible impact burst and emission bloom on the target. No silent hits.
- **I6 — Destruction sequence completeness.** Every unit death triggers the full destruction sequence (bloom → particles → drift → darkening). No units vanish without a death visual.
- **I7 — Wreckage lifecycle.** Every wreck transitions fresh → cooling → cold on schedule. No stuck wrecks. Cold wrecks eventually despawn.
- **I8 — Wreckage cull ordering.** Under frame pressure, cold wrecks cull farthest-from-camera first. Fresh and cooling wrecks never cull.
- **I9 — Ambient floor density.** Quiet areas of the battlefield receive at least one flyby ship per 10-second window (tuning value). Flyby count never drops to zero while combat is active anywhere.
- **I10 — Era-agnostic rendering.** All visual systems consume only era manifest config values. No hardcoded era-specific logic in any renderer file. `git grep` for "settled_reach" or era-specific strings in `scenes/tactical/visuals/` returns zero.
- **I11 — Kill switch isolation.** Each of four kill switches independently false → no crash, graceful degradation to pre-Stage-12.5 behavior for that system.
- **I12 — Engine determinism preserved.** `facing_rad` computation is deterministic. Ability event emission is deterministic. All renderer-only systems (attack visuals, destruction, ambient) have zero effect on engine state. A headless run with Stage 12.5 engine changes produces identical tick checksums to the same run without visual systems connected.
- **I13 — Selection circle faction color.** Selection circle color matches the player's current faction color and is visually dimmer than the pre-Stage-12.5 color.
- **I14 — Edge-scroll speed range.** Edge-scroll speed respects min/max bounds from config. Setting persists across scene transitions within a session.

## Done Condition

- All 11 checkpoints (A–K) approved.
- All 14 invariants pass.
- 200v200 engagement at 60fps (p95 < 16ms) at medium/far zoom with all visual systems active.
- Full game loop (onboarding → 2+ chapters with combat → debrief → narration → quit/resume) runs cleanly with all visual systems.
- All four kill switches tested independently.
- `tuning_output/stage12_5/` contains Checkpoint K measurements.
- No Stage 8 engine logic modified beyond `facing_rad` addition and ability event emission.
- No Stage 9 HUD logic modified beyond transition animation additions.
- No Stage 12 files modified.
- Era manifest extended (new fields), not restructured (existing fields unchanged).

## Files Created

(Filled in after implementation.)

## Notes for the Implementing Session

- **The renderer infers normal attacks — it does not receive them.** The attack visual manager watches each unit's attack interval and target from the state it already has. When interpolated time crosses an attack boundary, it spawns the visual. Do not add per-attack events to the delta stream for normal attacks — the stream would explode at 200v200. Only abilities get explicit events.
- **All visual timing is in the era manifest, not hardcoded.** Bloom durations, particle lifetimes, drift speeds, trail lengths — all config values. The Settled Reach values produce the cinematic register. Other eras will adjust these without code changes.
- **Destruction is renderer-only.** The engine removes the unit from gameplay state at 0 HP. The renderer keeps the visual alive through the destruction sequence. The wreck has no unit ID, no HP, no collision — it's a visual artifact managed entirely by `destruction_manager`. Do not keep dead units in engine state.
- **The combat heatmap is simple.** A spatial grid where cells gain score when units in them are attacking, decaying over time. It does not need to be precise — it's biasing random spawn positions, not pathfinding. A 10×10 grid over the engagement area is probably sufficient. This is an engineering decision — tune the resolution for performance.
- **Flyby Bézier paths are generated at spawn.** Each flyby gets a random start point on the boundary, 2–3 control points (biased toward heatmap hotspots), and an end point on the opposite boundary. The path is evaluated parametrically each frame. No physics, no steering, no collision avoidance between flybys.
- **HUD transitions are additive to existing logic.** The panels already show and hide. Wrap the existing visibility changes in tween calls. Do not restructure the HUD scene tree.
- **Edge-scroll speed is a single float in config.** The camera controller reads it each frame. The settings slider writes it. No complex binding system needed.
- **LOD tier thresholds are tuning values.** Start with reasonable defaults (billboard at 2x zoom-out, cull at 4x), tune in Checkpoint I based on actual frame measurements. Don't over-engineer the LOD system — the tiers are simple conditional branches, not a framework.

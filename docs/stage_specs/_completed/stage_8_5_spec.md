# Stage 8.5 — Era Theme Resolution and 3D Asset Integration

## Goal

Prove that the tactical renderer consumes 3D assets through an era-agnostic resolution layer — not through hardcoded paths, not through Settled-Reach-specific code, not through any mechanism that would require engine changes to support a second era. Stage 8.5 replaces Stage 8's placeholder 2D primitives (colored circles for units, colored dots for structures, heatmap overlays for gradients) with production 3D models loaded through a JSON manifest, with faction colors applied at runtime to designated face groups, tier-appropriate materials applied per the bible's material specs, and squad rendering (Strike units as 3–5 instances in formation).

Stage 8.5 is the stage where Sacred Design Principle #3 becomes visually real. After this stage, swapping from the Settled Reach to a different era means pointing the resolver at a different manifest and a different asset directory. Zero code changes, zero renderer modifications, zero engine awareness of which era is active.

**Not in scope:** Roman or 1980s era asset integration (Roman GLBs exist in the Blender directory but integration is a future stage — the resolver architecture supports them, this stage ships only Settled Reach), galaxy view era-swapping (Stage 11 — the galaxy view's spatial representation varies by era per the bible's Era Creation Template Layer 5), animation/VFX for abilities (post-8.5 polish), sound design, UI era-skinning beyond what Stage 9 already handles (accent colors, unit display names).

**Architecture.** A new `EraThemeResolver` autoload reads a per-era JSON manifest that maps abstract engine types (unit types × tiers, structure tiers, environment categories) to asset paths, material configs, and display metadata. The tactical renderers (`unit_renderer.gd`, `terrain_renderer.gd`) are retrofitted to query the resolver instead of drawing 2D primitives. The resolver is the single point where era identity enters the rendering pipeline — everything upstream (engine, bridge, snapshots) and everything downstream (the renderer's scene-tree construction) is era-blind.

## Bible References

- **`docs/bible_history/bible_2_00_ai_pipeline.md`** — §"3D Asset Pipeline" (per-era production workflow, polygon budgets, faction color face groups, tier material specifications with exact hex/metallic/roughness/emission values), §"Sci-Fi Era Production Spec" (asset manifest, Blender workflow, faction color regions).
- **`docs/bible_history/bible_2_00_world.md`** — §"Three-Tier Visual Progression" (tier visual language: Frontier/Establishment/Zenith), §"Sci-Fi Unit Designs — All 6 Types Across 3 Tiers" (per-unit visual descriptions driving model selection), §"Tactical Map Structures" (structure visual categories), §"Cross-Era Unit Silhouette Archetypes" (hard constraint: silhouette shapes persist across all eras).
- **`docs/bible_history/bible_2_00_combat.md`** — §"Unit Roster — 6 Base Types" (abstract type names the resolver maps from), §"Squad Mechanics — Visual Only" (Strike units render as 3–5 models per entity), §"Tactical Reinforcement System" (one interactive structure type on the tactical map).
- **`bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/)** — §"Branch System Implementation Notes" (production structure types, per-era configurability), §"Era Pack Delivery" (era packs as JSON + 3D assets downloaded to local content directory).
- **`game_bible.md` (hub)** — Sacred Design Principle #3 (era-agnostic architecture — the revenue principle), §"Era Creation Template" (Layer 4: tactical map structures, Layer 6: asset production spec).
- **`sloyd_prompt_strategy.md`** — full prompt sheet for Settled Reach units and environment assets. Settlement structure prompts are new deliverables for this stage.

Do NOT read `docs/bible_history/bible_2_00_chronicle.md`, `docs/bible_history/bible_2_00_simulation.md`, `docs/bible_history/bible_2_00_antagonist.md`, `docs/bible_history/bible_2_00_missions.md` — not relevant to Stage 8.5.

## Cross-Stage References

- **Stage 6** — the tactical engine emits abstract unit type strings (`"vanguard"`, `"raider"`, etc.), faction IDs (integers), and tier values in its state snapshots. Stage 8.5 does not modify the engine — it consumes these abstract identifiers through the resolver.
- **Stage 7** — the map generator places `reinforcement_structure` spine nodes. Stage 8.5 replaces their 2D colored-dot rendering with 3D settlement models. The generator's output is unchanged.
- **Stage 8** — `unit_renderer.gd` and `terrain_renderer.gd` are retrofitted. `TacticalBridge` snapshot/delta shapes are unchanged — the renderer reads the same `units`, `structures`, `map_data` dictionaries as before.
- **Stage 9** — `UIDataBus` already provides era accent colors and unit display names via `ThemeConstants.get_era_accent()` and `get_era_detail()`. Stage 8.5's resolver provides the 3D asset side of era resolution. The two systems are complementary — UI screens use the data bus, the tactical renderer uses the resolver.
- **Stage 10** — the era config (which era is active) will eventually come from the backend. In Stage 8.5, the active era is a config constant.

## Existing Asset Inventory

GLB files in `blender/the-settled-reach/` (confirmed from directory listing):

**Units — complete (18 models, all tiers):**

| Unit | T1 | T2 | T3 |
|------|----|----|-----|
| Vanguard | `SetReachVanT1.glb` | `SetReachVanT2V1.glb` | `SetReachVanT3.glb` |
| Bombard | `SetReachBombardT1.glb` | `SetReachBombardT2.glb` | `SetReachBombardT3.glb` |
| Bastion | `SetReachBastionT1.glb` | `SetReachBastionT2.glb` | `SetReachBastionT3.glb` |
| Raider | `SetReachRaiderT1.glb` | `SetReachRaiderT2.glb` | `SetReachRaiderT3.glb` |
| Interceptor | `SetReachInterceptorT1.glb` | `SetReachInterceptorT2.glb` | `SetReachInterceptorT3.glb` |
| Warden | `SetReachWardenT1.glb` | `SetReachWardenT2.glb` | `SetReachWardenT3.glb` |

Note: Some models have V2 variants (e.g., `SetReachBombardT2V2.glb`, `SetReachBastionT2V2.glb`). Westley selects the final version for each before Checkpoint A.

**Environment — partial (confirmed GLBs):**
`SetReachAstroidSmall.glb`, `SetReachAstroidMedium.glb`, `SetReachAstroidLarge.glb`

**Environment — Blender files exist, GLB export needed:**
`SetReachCargoContainer.blend`, `SetReachDerelictHull.blend`

**Structures — NOT YET CREATED.** Settlement models (3 tiers) are a new deliverable of this stage. See "Settlement Structure — Sloyd Prompts" section below.

**Roman era units — exist but out of scope:**
`RomanLegionaryT1–T3` (.blend, .fbx), `RomanVelitesT2` (.blend, .fbx). These validate that the resolver architecture works for multiple eras but are not imported into Godot in Stage 8.5.

## What to Build

### Architecture Overview

```
godot/
├── autoload/
│   ├── era_theme_resolver.gd         ← NEW: singleton, reads manifest, resolves types
│   └── era_config.gd                 ← NEW: active era ID constant
├── assets/
│   └── eras/
│       ├── settled_reach/
│       │   ├── manifest.json          ← NEW: abstract type → asset path + material config
│       │   ├── units/
│       │   │   ├── vanguard_t1.glb
│       │   │   ├── vanguard_t2.glb
│       │   │   ├── vanguard_t3.glb
│       │   │   └── ... (18 unit GLBs total)
│       │   ├── structures/
│       │   │   ├── settlement_t1.glb  ← NEW: Sloyd generation required
│       │   │   ├── settlement_t2.glb
│       │   │   └── settlement_t3.glb
│       │   └── environment/
│       │       ├── asteroid_small.glb
│       │       ├── asteroid_medium.glb
│       │       ├── asteroid_large.glb
│       │       ├── cargo_container.glb
│       │       ├── derelict_hull.glb
│       │       └── ... (remaining env assets)
│       └── test_era/
│           ├── manifest.json          ← NEW: test manifest with colored primitives
│           └── ... (generated placeholder scenes)
├── scenes/tactical/
│   ├── unit_renderer.gd              ← RETROFIT: 2D circles → 3D models via resolver
│   └── terrain_renderer.gd           ← RETROFIT: 2D dots → 3D models via resolver
```

### Files to create

**`autoload/era_config.gd`** — Active era constant. The single place in the codebase where the active era is specified.

```gdscript
extends Node
const ACTIVE_ERA_ID: String = "settled_reach"
```

Registered as autoload. Stage 10 or later replaces this constant with a value from the backend or save file. Stage 8.5 ships with it hardcoded.

**`autoload/era_theme_resolver.gd`** — Singleton that reads the per-era JSON manifest and resolves abstract engine types to concrete asset paths, material configurations, and display metadata. This is the **only file in the project that knows which era is active** beyond `era_config.gd`. Every other file asks the resolver "what does this abstract type look like?" and gets back a scene and a config.

Public API:
- `get_unit_scene(unit_type: String, tier: int) -> PackedScene` — returns the loaded scene for a unit type + tier.
- `get_structure_scene(tier: int) -> PackedScene` — returns the settlement model at a tier.
- `get_environment_scene(category: String) -> PackedScene` — returns an environment object scene by abstract category.
- `get_material_config(tier: int) -> Dictionary` — returns the full material config dict for a tier (hull colors, metallic/roughness values, emission values, faction color treatment).
- `get_faction_color_mode(tier: int) -> String` — returns `"matte"` (T1), `"metallic"` (T2), or `"emissive"` (T3).
- `get_squad_count(unit_type: String) -> int` — returns squad visual count from manifest (3–5 for Strike, 1 for Line/Siege).
- `get_era_display() -> Dictionary` — returns era display metadata (name, accent color).
- `get_active_era() -> String` — returns the active era ID string.

Behavior:
- On `_ready()`, reads `EraConfig.ACTIVE_ERA_ID`, loads `res://assets/eras/{era_id}/manifest.json`, parses it, preloads all referenced PackedScenes into a cache.
- Missing manifest or missing asset file → logs a warning (gated behind `IS_RELEASE_BUILD`), returns a fallback placeholder scene (colored primitive). **The game never crashes due to a missing asset.**
- All scene preloading happens in `_ready()`. No runtime era switching in this stage.

**`assets/eras/settled_reach/manifest.json`** — The per-era data file mapping abstract types to assets and materials. Structure:

```json
{
  "era_id": "settled_reach",
  "era_display_name": "The Settled Reach",
  "era_accent_color": "#4a9eb8",

  "units": {
    "raider":      { "category": "strike", "squad_count": 4, "tiers": {
      "1": { "scene": "units/raider_t1.glb" },
      "2": { "scene": "units/raider_t2.glb" },
      "3": { "scene": "units/raider_t3.glb" }
    }},
    "interceptor": { "category": "strike", "squad_count": 4, "tiers": { "1": {}, "2": {}, "3": {} }},
    "vanguard":    { "category": "line",   "squad_count": 1, "tiers": { "1": {}, "2": {}, "3": {} }},
    "warden":      { "category": "line",   "squad_count": 1, "tiers": { "1": {}, "2": {}, "3": {} }},
    "bombard":     { "category": "siege",  "squad_count": 1, "tiers": { "1": {}, "2": {}, "3": {} }},
    "bastion":     { "category": "siege",  "squad_count": 1, "tiers": { "1": {}, "2": {}, "3": {} }}
  },

  "structures": {
    "settlement": { "tiers": {
      "1": { "scene": "structures/settlement_t1.glb" },
      "2": { "scene": "structures/settlement_t2.glb" },
      "3": { "scene": "structures/settlement_t3.glb" }
    }}
  },

  "environment": {
    "obstacle_small":  { "scene": "environment/asteroid_small.glb" },
    "obstacle_medium": { "scene": "environment/asteroid_medium.glb" },
    "obstacle_large":  { "scene": "environment/asteroid_large.glb" },
    "cargo":           { "scene": "environment/cargo_container.glb" },
    "derelict":        { "scene": "environment/derelict_hull.glb" },
    "cover_pylon":     { "scene": "environment/shield_pylon.glb" },
    "nav_beacon":      { "scene": "environment/nav_beacon.glb" },
    "hazard_volume":   { "scene": "environment/nebula_volume.glb" }
  },

  "materials": {
    "1": {
      "hull_primary":   { "color": "#6B6B6B", "metallic": 0.7, "roughness": 0.7 },
      "hull_secondary": { "color": "#4A4A4A", "metallic": 0.6, "roughness": 0.8 },
      "accent":         { "color": "#D4A017", "metallic": 0.0, "roughness": 0.9 },
      "engine_glow":    { "color": "#FF8844", "emission": 2.0 },
      "sensor":         { "color": "#88CCFF", "emission": 0.5 },
      "faction_color_treatment": "matte",
      "faction_color_metallic": 0.0,
      "faction_color_roughness": 0.8
    },
    "2": {
      "hull_primary":   { "color": "#C0C0C8", "metallic": 0.9, "roughness": 0.3 },
      "hull_secondary": { "color": "#E8E8F0", "metallic": 0.8, "roughness": 0.35 },
      "accent_line":    { "color": "#AAAAAA", "emission": 0.3 },
      "engine_glow":    { "color": "#66AAFF", "emission": 3.0 },
      "weapon":         { "color": "#808088", "metallic": 0.9, "roughness": 0.2 },
      "faction_color_treatment": "metallic",
      "faction_color_metallic": 0.7,
      "faction_color_roughness": 0.35
    },
    "3": {
      "hull_primary":   { "color": "#1A1A2E", "metallic": 1.0, "roughness": 0.1 },
      "hull_secondary": { "color": "#2A2A3E", "metallic": 0.9, "roughness": 0.15 },
      "engine_glow_whitened": true,
      "engine_glow_emission": 4.0,
      "faction_color_treatment": "emissive",
      "faction_color_emission": 2.0,
      "faction_edge_emission": 0.8
    }
  },

  "faction_colors": {
    "0": "#4099FF",
    "1": "#FF4738",
    "2": "#40E566",
    "3": "#FFCC33"
  }
}
```

All scene paths are relative to the manifest's directory. The resolver prepends `res://assets/eras/{era_id}/` when loading.

**`assets/eras/test_era/manifest.json`** — Test manifest mapping all abstract types to colored primitives (cubes, spheres, cylinders). Used exclusively in Checkpoint G to prove era-agnostic architecture. Contains the same schema as the Settled Reach manifest but points to generated placeholder `.tscn` scenes with simple MeshInstance3D nodes using bright primary-colored materials.

### Files to modify

**`unit_renderer.gd`** — Full retrofit from 2D `_draw()` circles to 3D model instancing.

Current: extends Node2D, draws colored circles per unit via `_draw()`. Reads `faction`, `layer`, `hp` from `TacticalBridge.units`. Does not read `type` or `tier`.

Retrofit:
1. On snapshot, for each unit in `TacticalBridge.units`: read `type`, `tier`, `faction`. Call `EraThemeResolver.get_unit_scene(type, tier)` for the PackedScene. Call `EraThemeResolver.get_squad_count(type)` — if >1, instance that many copies in a V-formation pattern.
2. Apply faction color to the `faction_color` surface group using the tier's faction color treatment from `EraThemeResolver.get_material_config(tier)`.
3. Apply tier materials to non-faction surfaces per the manifest's material config.
4. On tick delta, update positions via interpolation (same buffer as Stage 8).
5. On unit removal, free instanced scenes.
6. HP feedback: material darkening or damage overlay.
7. Selection halo and layer indicator ring persist as overlay elements.

The renderer **never references era-specific strings**. It calls `EraThemeResolver.get_unit_scene("vanguard", 2)` — it does not know whether the result is a spaceship, a legionary, or a tank.

Squad formation for Strike units: instances arranged in a V/chevron centered on the engine's single-entity position. Formation spacing is a config value. Squad count comes from the manifest so different eras can specify different squad sizes.

**`terrain_renderer.gd`** — Full retrofit from 2D `_draw()` circles to 3D model instancing.

Current: extends Node2D, draws colored circles for gradient sources and spine node markers. Reads `spine_nodes` and `gradient_sources` from `TacticalBridge.map_data`.

Retrofit:
1. **Structures.** For `reinforcement_structure` spine nodes: read region `tier`, call `EraThemeResolver.get_structure_scene(tier)`, instance the settlement model. Apply faction color based on `owner`. Overlay capture zone ring + HP bar + production timer.
2. **Environment objects.** For gradient sources: `obstacle_density` → instance obstacle models via `EraThemeResolver.get_environment_scene("obstacle_small"|"medium"|"large")` based on intensity/radius. `cover_density` → cover models. `sensor_interference` → hazard volumes. Placement uses deterministic seeded scatter within each source's radius (seed derived from map seed).
3. **Non-interactive spine nodes** (objectives, chokepoints, staging) retain existing colored markers. Optional: environment model overlay if manifest defines them. Stretch goal.

The terrain renderer **never references era-specific strings**.

**`config.py` (Python side)** — No changes. The tactical engine's snapshot format already emits abstract type strings. Stage 8.5 is purely a Godot-side retrofit.

### Files NOT to modify

- All protected engine files per `CLAUDE.md`.
- `socket_server.py` — protected, no changes.
- `tactical_engine.py` — no changes. The engine already emits abstract types.
- `TacticalBridge` (`autoload/tactical_bridge.gd`) — no changes to the bridge protocol. The renderer reads the same snapshot/delta shapes.
- Stage 9 UI scenes and autoloads — no changes. UI era resolution (accent colors, display names) is a separate system that already works.

### Settlement Structure — Sloyd Prompts (NEW ASSETS)

The settlement is the tactical map's one interactive structure type. It represents a population center — the source of the region's military production capacity. The player captures settlements to produce reinforcements. The visual reads as "people live and work here" across all three tiers.

**Silhouette archetype (hard constraint for all eras):** Compact, roughly symmetric, clearly inhabited. Reads as "a place" not "a weapon" or "a machine." Distinct from all six unit silhouettes (which are vehicle/vessel shapes). At tactical zoom, the player instantly distinguishes "that's a settlement I can capture" from "that's a unit I can command."

| # | Asset | Prompt | Look For |
|---|-------|--------|----------|
| S1 | Settlement T1 | Low-poly small space outpost, modular hab modules connected by walkways, a few docking cradles, antenna cluster, scrappy and improvised, clearly inhabited, flat-shaded geometric | Reads as "frontier town" — small, scrappy, people live here. Distinct from units (not a vehicle shape) |
| S2 | Settlement T2 | Low-poly space colony station, ring habitat with docking bays, central hub with manufacturing arms, organized and designed, clearly a working settlement, flat-shaded geometric | Reads as "established colony" — proper infrastructure, planned layout, industrial capacity visible |
| S3 | Settlement T3 | Low-poly advanced space habitat, smooth monolithic form with luminous inhabitation indicators, elegant and large, minimal visible detail but clearly a major population center, flat-shaded geometric | Reads as "metropolis" — large, advanced, the civilization's crown jewels. Monolithic per T3 language |

**Poly budget:** 400–600 per tier.

**Blender post-export:** Same workflow as units. Create `faction_color` face group on hull surfaces showing ownership. Apply tier materials from `docs/bible_history/bible_2_00_ai_pipeline.md`. Silhouette check at tactical zoom distance.

## Implementation Checkpoints

Each checkpoint is a hard stop per `dev_rules.md`. Run test, show output, wait for Westley approval. Do not batch.

### Checkpoint A — Resolver + Manifest + One Unit

**Build:** `era_theme_resolver.gd`, `era_config.gd`, `manifest.json` (Settled Reach). Copy one unit GLB into Godot (Vanguard T2). Register resolver as autoload.

**Test:** Call `EraThemeResolver.get_unit_scene("vanguard", 2)` from a test script. Verify valid PackedScene returned. Call with `"nonexistent_unit"` — verify fallback (no crash, placeholder). Call with `tier=4` — verify fallback.

**Print:** Manifest load status, scene cache size, fallback trigger count.

**Verify:** Resolver loads manifest, caches scene, returns it. Fallback works for every invalid input. No era-specific strings in the test script.

⛔ STOP.

### Checkpoint B — Unit Renderer Retrofit (Single Unit, No Squad)

**Build:** Retrofit `unit_renderer.gd` to instance 3D models from the resolver for one unit type (Vanguard). Other unit types fall back to 2D circles. No squad rendering yet.

**Test:** Run a tactical mission with Vanguards. Verify 3D models render, others show circles. Verify faction color applies to `faction_color` face group. Verify position tracking via interpolation buffer.

**Print:** Per-unit: type, tier, resolver hit or fallback, faction color applied.

**Verify:** Vanguard 3D model visible, positioned correctly, faction-colored. Others gracefully fall back. No hardcoded Settled Reach references in `unit_renderer.gd`.

⛔ STOP.

### Checkpoint C — Full Unit Roster (6 Types × 3 Tiers)

**Build:** Copy all 18 unit GLBs into asset directory. Extend renderer for all unit types. Add tier material application per manifest.

**Test:** Mission with all 6 unit types. Verify each renders correctly. Verify tier materials differ visually (T1 matte vs T2 polished vs T3 emissive). Cross-tier scenario (player T2, enemy T1) — verify immediate readability.

**Print:** Per unit type × tier: model loaded, material applied, tier readable at zoom.

**Verify:** All 18 models render. Tier visually distinct. Faction color treatment matches tier. No hardcoded paths.

⛔ STOP.

### Checkpoint D — Squad Rendering (Strike Units)

**Build:** Squad instancing for Raider and Interceptor. `squad_count` from manifest (4). V-formation centered on engine position. Spacing as config value.

**Test:** Mission with Raiders and Interceptors. Verify 4-model formations. Verify formation moves as unit. Verify cleanup on entity destruction.

**Print:** Per squad: member count, formation pattern, offsets.

**Verify:** Strike = 4-ship formations. Line/Siege = single models. Formation cohesive during movement. No per-member simulation state.

⛔ STOP.

### Checkpoint E — Settlement Structure Models

**Prerequisite:** Settlement T1–T3 GLBs produced via Sloyd, cleaned in Blender, exported.

**Build:** Add settlement to manifest. Retrofit `terrain_renderer.gd` to instance 3D settlement models for `reinforcement_structure` spine nodes. Faction color by ownership. Capture zone + HP bar + production timer overlays.

**Test:** Mission with reinforcement structures. Verify 3D settlements at correct positions. Verify faction color updates on capture. Verify overlay readability.

**Print:** Per structure: tier, model loaded, owner, capture progress, production state.

**Verify:** Settlements visually distinct from units. Faction color changes on capture. Overlays readable. Reads as "a place" at tactical zoom.

⛔ STOP.

### Checkpoint F — Environment Objects

**Build:** Copy environment GLBs into asset directory. Implement deterministic scatter in `terrain_renderer.gd` — gradient sources spawn environment models within their radius based on intensity. Scatter seed from map seed.

**Test:** Mission on Stage 7 generated map. Verify obstacles = asteroids, cover = pylons/cargo, hazards = nebula volumes. Regenerate same seed — verify identical placement.

**Print:** Per gradient source: property, category resolved, model count, positions.

**Verify:** Environment populates map. Density scales with intensity. Deterministic. No era-specific strings.

⛔ STOP.

### Checkpoint G — Era-Agnostic Verification (THE CRITICAL CHECKPOINT)

**Build:** No new code. Create `test_era/manifest.json` mapping the same abstract types to colored primitives (cubes for units, spheres for structures, cylinders for environment). Different material configs (bright primary colors, no emission).

**Test:** Change `EraConfig.ACTIVE_ERA_ID` to `"test_era"`. Run the same mission from Checkpoint F. Verify:

1. All units render as colored cubes (not spaceships).
2. All structures render as colored spheres (not settlements).
3. All environment objects render as colored cylinders (not asteroids).
4. Faction colors still apply correctly.
5. Squad rendering still works (4 cubes in V-formation for Strike).
6. HP bars, capture zones, production timers all overlay correctly.
7. **Zero code was changed** — only the config constant.

**Print:** Active era ID, manifest path, all resolver cache entries showing test_era paths, screenshot comparison.

**Verify:** Changing one string in one config file swaps the entire visual presentation. No renderer code, no engine code, no bridge code modified. This proves Sacred Principle #3 holds in the rendering pipeline.

⛔ STOP.

### Checkpoint H — Performance (Final)

**Build:** MultiMesh batched rendering. Rewrite `unit_renderer.gd` from individual `MeshInstance3D` nodes per unit to `MultiMeshInstance3D` batching. This is required — individual nodes cause a Metal driver deadlock at 200v200 scale (~10 seconds to freeze). See docs/bible_history/bible_2_00_combat.md "Unit Rendering — MultiMesh Batching" for the resolved architectural decision.

**Architecture:**
```
UnitRenderer
├── MultiMeshInstance3D per (type, tier, faction)   — one draw call per batch
├── MultiMeshInstance3D per layer ring color        — 4 max
└── Individual MeshInstance3D for selected units    — selection rings only
```

**Batch key:** `"type_tier_faction"` (e.g. `"vanguard_1_0"`). Each batch holds one MultiMesh using the mesh from `EraThemeResolver.get_unit_scene()`. Squad units (squad_count > 1) contribute N instances per unit with formation offsets baked into transforms.

**Per-frame update:** Write instance transforms from `TacticalBridge.display_x/display_y` flat arrays. One `multimesh.set_instance_transform()` call per instance — C++ method, no scene tree overhead.

**Escape hatch for VFX:** Units needing per-instance effects (death animation, ability glow) temporarily leave their batch into an individual node, then return when the effect completes. Budget: <20 individual nodes at any moment.

**Draw call target:** ~30 (vs ~1200 with individual nodes). Scales to 1000 units.

**Test:** 200v200 on Metal renderer (macOS). Must survive indefinitely (>5 minutes) without visual freeze. Measure: frame time, draw calls, instance count, memory. Compare against Stage 8 Checkpoint M baseline.

**Print:** Perf table: frame time p50/p95/p99, draw calls, instances, memory, batch count. Stage 8 baseline comparison.

**Verify:** 60fps at 200v200 (p95 < 16ms). No Metal driver deadlock. Draw calls < 100. Regression vs Stage 8 must not exceed 25%.

⛔ STOP.

## Invariants

- **I1 — Era-agnostic renderer.** `git grep` for era-specific strings (`"settled_reach"`, `"SetReach"`, `"roman"`, any era name) in `unit_renderer.gd` and `terrain_renderer.gd` returns zero hits. The only files containing era identity are `era_config.gd` and manifest JSONs.
- **I2 — Era-agnostic resolver API.** Every public method on `EraThemeResolver` accepts abstract type strings (`"vanguard"`, `"settlement"`, `"obstacle_medium"`) — never era-specific asset names.
- **I3 — Manifest-only asset paths.** No GLB file path appears in any `.gd` file. All asset paths are read from the manifest JSON at runtime.
- **I4 — Graceful fallback.** Requesting any type/tier/category not in the manifest returns a visible placeholder without crashing. Proven by Checkpoint G's test_era and by deliberate invalid-input tests in Checkpoint A.
- **I5 — Squad count from manifest.** Models instanced per entity comes from the manifest's `squad_count` field, not from a hardcoded constant. Different eras can specify different squad sizes.
- **I6 — Faction color at runtime.** No GLB ships with faction colors baked in. Faction color is applied at runtime to the `faction_color` surface group. Verified by running the same model with different faction IDs.
- **I7 — Tier material from manifest.** Material properties (metallic, roughness, emission) come from the manifest's `materials` section, not from Blender-baked materials. The GLB ships with neutral placeholders; the renderer overrides them.
- **I8 — Config-only era swap.** Changing `EraConfig.ACTIVE_ERA_ID` and providing a valid manifest + assets swaps the entire tactical visual presentation. Proven by Checkpoint G.
- **I9 — Deterministic environment scatter.** Same map seed + same manifest → identical environment placement across runs.
- **I10 — Performance budget.** 200v200 on large map with full 3D: renderer p95 < 16ms.

Per `dev_rules.md`: if an invariant fails, you may not widen thresholds or weaken tests. Escalate real bugs, or narrow scope.

## Done Condition

- All 8 checkpoints (A–H) run, shown, approved by Westley.
- All 10 invariants (I1–I10) pass.
- Full tactical mission renders with 3D models for all units (6 types × 3 tiers), squad formations for Strike, settlement structures with faction color and production overlays, and scattered environment objects.
- Checkpoint G test-era swap proves era-agnostic architecture — one config change, zero code changes, different visuals.
- Settlement T1–T3 models produced, cleaned, and integrated.
- `godot/assets/eras/settled_reach/` contains all GLBs with standardized names.
- `manifest.json` complete and validated.
- No era-specific strings in any renderer or engine file.
- Performance holds 60fps at 200v200.

## Bible Capture Pending

These bible edits should land alongside or shortly after this stage:

1. **`docs/bible_history/bible_2_00_world.md` "Tactical Map Structures" section** — update to reflect the settlement as the single interactive structure type, replacing the Station/Military Installation/Resource Node breakdown for interactive structures. The three visual categories may persist as non-interactive point-of-interest skins but should be clearly distinguished from the capturable settlement.
2. **`bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/) line 249** — update "barracks-equivalent, factory-equivalent, resource-equivalent" to reflect the single settlement structure type. Per-era configurability (amount, placement, production rate) preserved.
3. **`docs/bible_history/bible_2_00_ai_pipeline.md` "Asset Manifest" section** — update structure count from "3 types × 3 tiers = 9" to "1 type × 3 tiers = 3 settlement models" per era.
4. **`docs/bible_history/bible_2_00_world.md` "Recon Phase" section** — correct "enemy positions based on intelligence quality" to "enemy positions hidden" per Stage 8's Bible Capture Pending item #7.
5. **`game_bible.md` hub** — add Stage 8.5 to the implementation roadmap between Stage 8 and Stage 9.
6. **`sloyd_prompt_strategy.md`** — replace Station / Military Installation / Resource Node structure prompts with the three settlement prompts from this spec.

## Implementation Notes (Post-Completion)

### Checkpoint H — Root Cause and Resolution

The 200v200 Metal freeze was **not** caused by draw call count. MultiMesh batching reduced draw calls from ~1200 to ~30 but the freeze persisted at identical timing (~10-12 seconds). Binary-search isolation identified the actual cause: `queue_free()` accumulation in `hud.gd`'s `_append_event()` handler. Every `unit_destroyed` event created a Label and `queue_free()`'d the oldest — deferred frees accumulated until Godot's main loop hung.

**Fix:** All UI cleanup now uses `remove_child()` + `free()` for immediate cleanup instead of `queue_free()`. Applied to `hud.gd` (event ticker, objective list, structure list) and `terrain_renderer.gd` (rebuild).

MultiMesh batching was retained as the correct architecture regardless — it reduces draw calls by 40×, scales cleanly to 1000+ units, and is documented in `docs/bible_history/bible_2_00_combat.md` "Unit Rendering — MultiMesh Batching".

### Checkpoint F — Asteroid Scatter

Environment scatter uses `MultiMeshInstance3D` per category. Gradient sources with `obstacle_density` property seed asteroid placement (deterministic via map_seed + source position). Only categories with real GLB assets are scattered — categories pointing at `placeholder.glb` are skipped until real assets exist.

**Tuning values:** `BASE_DENSITY = 0.00015` objects/unit² at intensity 1.0, scale range `[4.0, 12.0]`. Initial values (0.004 density, [80, 200] scale) produced solid masses of overlapping giant asteroids.

### Flat-Array Interpolation Buffer

Replaced per-tick Dictionary-based buffer with `PackedFloat32Array` indexed by `uid*2`. Consumers read `TacticalBridge.display_x[uid]` / `display_y[uid]` / `display_alive[uid]` directly — no per-frame dict allocation. `ws_client.gd` rate-limited to 2 messages per frame to prevent frame-drop feedback loops.

## Files Created

(Filled in after implementation.)

## Notes for the Implementing Session

- **GLB renaming.** The Blender directory uses `SetReachVanT2V1.glb` naming. The Godot asset directory uses `vanguard_t2.glb` naming. The manifest maps abstract types to Godot names. Copy-and-rename is part of Checkpoint A setup.
- **V1/V2 variants.** Westley picks the final version for each model before Checkpoint A. Non-selected variants stay in the Blender directory.
- **Faction color face group.** Every model must have a vertex/surface group named `faction_color` from the Blender cleanup pass. If any GLB is missing this group, it's a Blender rework item — not a code workaround.
- **3D in a 2D scene tree.** Stage 8's tactical scene uses Node2D and `_draw()`. The retrofit to 3D models likely requires converting to a 3D scene tree (Node3D, Camera3D) or SubViewport rendering. The bible specifies a "fixed-angle top-down RTS camera" — naturally a 3D camera looking down. The scene tree architecture is an engineering decision for CC. The constraint: the result must look like a top-down RTS with 3D models matching the "Art of Rally" low-poly aesthetic.
- **Settlement prompts are blocking.** Checkpoint E depends on settlement GLBs existing. Plan the Sloyd session to happen between Checkpoints D and E.
- **The hud.gd in the uploads is from the old iteration** (god-game UI — fate space, manifold chart, declarations). It is not the Stage 8 tactical HUD. Do not modify it.

# Stage 7 — Map Generation and Tactical Reinforcement

## Goal

Prove that procedurally generated tactical maps — produced by the spine + gradient pipeline from authored strategic layouts, flavored by region simulation state, and validated by a fairness evaluator — are gameplay-valid maps that the Stage 6 tactical engine runs on without modification. Prove that tactical reinforcement structures (a new spine node type) handle capture, production, destruction, and enemy composition reactivity correctly during missions. Stage 7 is the bridge that lets the tactical engine consume any mission the simulation can generate, instead of only the hand-authored test maps from Stage 6.

**Not in scope:** enemy macro behavior scripts (Stage 7.5), Godot renderer or command UI (Stage 8), moving gradient sources (deferred post-Stage 7 per S7-3), save scope / rewind persistence (Stage 8), mission complications (deferred per Stage 7 design session — implemented in a later stage after core missions are playable).

**Architecture.** The map generator is a pure function: `(archetype, region_state, canvas_size, seed) → TacticalMap`. It sits between mission generation (Stage 5.5) and the tactical engine (Stage 6). Reinforcement structures are a runtime extension of the engine: a new spine node type with per-tick behavior (capture state machine, production timer, destruction) wired into the existing tick loop.

**Visualization deliverables.** Per the design session, this stage ships with two debug tools (retired when Stage 8's Godot renderer lands): `map_viewer.py` (interactive pygame viewer for deep inspection) and `map_batch_png.py` (batch PNG dumper writing grids of generated maps to `tuning_output/stage7/` for async review). These are first-class deliverables — every checkpoint produces visual output, not just terminal metrics.

## Bible Capture Pending

These bible edits were deferred from the design session; they do not block implementation but must land before this stage is marked done:

1. **Hub roadmap entry for Stage 7** currently describes the pre-split scope ("Map Generation, Enemy Macro Behavior, and Tactical Reinforcement"). Needs update to reflect the Stage 7 / 7.5 / 8 split.
2. **Hub §15** (Simulation State Journaling and Rollback — OPEN) partially resolved by S8-1: rewind-with-re-seed is Stage 8 scope; crash recovery and multi-branch trees remain deferred.

## Bible References

- **`docs/bible_history/bible_2_00_world.md`** (full file) — spine + gradient pipeline, gradient property vocabulary, spine node types (objective, staging, transit, chokepoint, flank route, vantage, hazard zone anchor, spawn point, extraction, **reinforcement structure** per S7 resolution), Strategic Layout Authoring Framework, canvas sizing, 5 vertical layers, `layer_accessibility_mask` mechanism, drifting spine nodes (§"Moving Battlefields S7-3").
- **`docs/bible_history/bible_2_00_combat.md`** — Tactical Reinforcement System (structure mechanics, capture/production/destruction, enemy composition reactivity with 70/15 skew response).
- **`game_bible.md` (hub)** — Sacred Design Principles (era-agnostic architecture: all map features and node types must be abstract).

Do NOT read `docs/bible_history/bible_2_00_missions.md`, `docs/bible_history/bible_2_00_antagonist.md`, or `docs/bible_history/bible_2_00_chronicle.md` — not relevant to Stage 7.

## Cross-Stage References

- **Stages 1–4** — region state (stability, capacity, economy, tension, military, population) drives simulation flavoring. Generator reads `Region` fields; never mutates them.
- **Stage 5.5** — calls the map generator with `(archetype, region_id, canvas_size, seed)`. `MissionSetup.map_params` is extended so it carries the generator seed.
- **Stage 6** — consumes the `TacticalMap` returned by the generator. Contract: `TacticalMap.width/height/layers/spine_nodes/gradient_sources` sufficient to initialize. No engine changes for static maps; drifting spine nodes add a per-tick position update wired into the existing tick loop.
- **Stage 7.5** — behavior scripts consume spine node structure via existing `TacticalMap.spine_nodes` / `get_spine_nodes_by_type()`. Stage 7 adds no new API for this. Stage 7 ships with enemy units using Stage 6 command primitives only (attack-move) — composition reactivity decides *what unit type* to produce, not *what the unit does after spawning*.
- **Stage 8** — Godot renderer consumes `TacticalMap` + per-tick drift deltas. Stage 7 ensures the drift contract is renderer-friendly.

## What to Build

### Files to create

**`map_gen_contracts.py`** — Shared data structures.
- `LayoutSpec`: layout_id, name, canvas_class, zones (list of `ZoneSpec`), edges (list of `EdgeSpec`), tags, drift_paths.
- `ZoneSpec`: zone_id, position_ratio (x, y as 0.0–1.0 of canvas), node_type, properties dict.
- `EdgeSpec`: from_zone, to_zone, edge_type (`path` / `restricted` / `flank`).
- `DriftPathSpec`: zone_id, waypoints (position_ratio tuples), period_ticks, mode (`ping_pong` / `loop`).
- `RegionState`: frozen dataclass, the generator's view of a region. **Six numeric driver fields** (these shape the generated map): `stability`, `capacity`, `economy`, `tension`, `military`, `population`. **Two debug/label fields** (not read by generation logic, carried for `map_batch_png.py` filenames, `generation_metadata` entries, and log lines): `region_id: str`, `tier: int`. Stage 5.5 constructs a `RegionState` from the live `Region` immediately before calling `generate_map()` — the generator never imports or touches `region.py`.
- `GeneratorInput`: archetype, region_state (`RegionState`), canvas_size, seed.
- `MapGenerationResult`: tactical_map, chosen_layout_id, fairness_score, generation_metadata.

**`layout_library/`** — 8 authored layouts as JSON (`layout_01_*.json` through `layout_08_*.json`). Each covers at least one prototype archetype. Working titles: Fortress Ridge, Open Plains Assault, Three-Front Valley, Dense Urban Grid, Coastal Wedge, Flanking Pass, Scattered Outposts, Elevated Strongpoint.

**`layout_library.py`** — Loader + registry. `load_all_layouts()`, `get_layout(layout_id)`, `layouts_for_archetype(archetype)`. Validates on load: edges reference valid zones, drift_path zones exist, no duplicate zone IDs, position_ratios in [0,1].

**`archetype_filters.py`** — Boolean filter language.
- Primitives: `count(node_type) >= N`, `count(edge_type) >= N`, `has_zone_with_property(...)`, `layer_accessibility_variety >= N`; composite operators (`all_of`, `any_of`, `not`).
- Full filter definitions for 4 prototype archetypes (Defensive Stand, Assault, Multi-Front Defense, Counterinsurgency) from `docs/bible_history/bible_2_00_missions.md` map character prose. Stubs for other 6 archetypes (refined in 7.5).
- `evaluate_filter(filter_spec, layout_spec) → bool`, `matching_layouts(archetype, layout_library)`.
- **Implementation note (Checkpoint B/C audit):** `flank_route` is a spine **node type** (per `docs/bible_history/bible_2_00_world.md` — one of the 10 vocabulary types), not only an edge type. Layout nodes exclusively on flank approaches must be typed `flank_route`, not `transit`. The `defensive_stand` and `assault` filters both require `count_zone_type("flank_route") >= 1` — enforcing the bible rule "generation rules require at least one flank route per chokepoint to prevent pure-grind maps." Multi-Front Defense is exempt: interior lines between corridors serve the flanking function. `layout_08_elevated_strongpoint` carries only the `multi_front_defense` tag for the same reason.
- **Per-archetype fairness target profiles** (see "Archetype-Aware Fairness" subsection below). Stored as a `FairnessTargetProfile` per archetype alongside its compatibility filter. Same authoring surface: 4 prototype archetypes get intentional profiles in Stage 7; other 6 use a symmetric default (`1.0 ± 0.15` on every metric) until their 7.5 scripts pin their actual intent.

**`layout_instantiator.py`** — `LayoutSpec` + canvas size + seed → concrete spine (list of `SpineNode` with absolute positions + edges with node IDs).
- Canvas sizes (config): small 4000×4000, medium 8000×8000, large 12000×12000.
- Position ratios scaled to canvas; deterministic positional jitter (±LAYOUT_JITTER_PERCENT of canvas dim, default 3%), clamped so chokepoint width constraints hold.

**`gradient_placer.py`** — Deterministic gradient sources tied to spine node types.
- Per-node-type rules: `chokepoint` → `obstacle_density`, `staging` → `cover_density`, `vantage` → `elevation`, `hazard zone anchor` → `sensor_interference`, etc.
- Output: `list[GradientSource]` per property type. Config-tunable intensities and radii.
- **Gradient property count reconciliation:** `docs/bible_history/bible_2_00_world.md` refers to "5 gradient properties." The engine decomposes this as **4 continuous properties** placed here (`obstacle_density`, `cover_density`, `sensor_interference`, `elevation`) plus the **layer accessibility mask**, which is one conceptual property with 5 per-layer channels implemented in `layer_masks.py`. Total matches the bible's 5.

**`layer_masks.py`** — 5-layer `layer_block_N` accessibility gradients.
- Takes layout + canvas dims, emits 5 mask sources. Layout zones may specify layer restrictions (e.g., `staging` accessible on layers 1–3 only). Default all-accessible where unspecified.

**`sim_flavoring.py`** — Region state → gradient intensity modifiers.
- Composite axis baselines: low stability → higher sensor_interference / cover_density / hazard anchor count; high capacity → lower obstacle_density.
- Individual field deltas (bounded, additive): economy → obstacle_density reduction along paths; tension → cover_density boost; military → obstacle_density boost near defensive positions; population → feature density scale.
- All coefficients in `config.py`.

**`fairness_evaluator.py`** — Algorithmic seed scoring.
- Metrics: path count balance (player-staging → objectives vs enemy-spawn → objectives), travel time balance, vantage accessibility balance, hazard distribution symmetry. Each metric returns a ratio (not a symmetry score): `player_value / enemy_value` clamped to (0, ∞).
- `FairnessScore` dataclass with per-metric ratios + per-metric pass/fail + aggregate pass/fail.
- `is_acceptable(score, archetype) → bool` — each metric's ratio is checked against the archetype's authored `FairnessTargetProfile` (target ± tolerance). Aggregate passes when **all four** metrics fall within their per-archetype tolerances. Generator regenerates (up to `FAIRNESS_MAX_RETRIES`) on failure.

**`map_generator.py`** — Top-level pipeline.
```python
def generate_map(generator_input: GeneratorInput, layout_library: dict) -> MapGenerationResult:
    # 1. Filter layouts for archetype compatibility
    # 2. Seeded selection among compatible set
    # 3. Instantiate spine (canvas scaling + jitter)
    # 4. Place reinforcement structures per S7-5 baseline + sim delta
    # 5. Place gradients
    # 6. Generate layer masks
    # 7. Apply simulation flavoring
    # 8. Fairness evaluate; retry with new seed if below threshold
    # 9. Construct TacticalMap, return MapGenerationResult
```

**`reinforcement.py`** — Tactical reinforcement runtime.

- `ReinforcementStructure` dataclass: structure_uid, position, layer, hp, max_hp, owner_faction, capture_progress (0–1), production_timer_sec, production_target_unit_type, capture_radius.
- `step_reinforcement(engine, dt)` — per tick: evaluate capture zone occupancy per faction, advance/reset capture_progress, flip ownership on completion; if owned, advance production_timer; on production complete, spawn unit at structure position.
- Production time is power-rating-scaled: `production_time_sec = BASE_PRODUCTION_TIME_SEC × (unit_power_rating / POWER_NORMALIZATION)`. More powerful units take proportionally longer. Both constants are tuning values from `config.py`.
- `select_enemy_unit_type(target_ratio, current_composition, player_composition)` — applies 70/15 skew rule: player category > 70% → shift 15% of enemy target ratio toward counter category.
- Damage routed through existing damage resolution system (structure as immobile damage target). On HP ≤ 0, removed from active list.
**`spine_drift.py`** (avoid name collision with protected `simulation/drift.py`) — per-tick drifting node positions.

- Only `objective` and `reinforcement_structure` node types may drift (S7-3).
- `update_drifting_nodes(engine, tick)` — walks drift paths, interpolates by `tick % period_ticks`.
- Navmesh not regenerated: drifting nodes carry their own position-at-tick function; engine samples on demand.
**`map_viewer.py`** — Interactive pygame viewer.

- CLI: `python -m simulation.map_viewer <map_json> [--tick N]`.
- Renders: canvas bounds, spine nodes (color-coded), edges (style by edge_type), gradient heatmaps (toggle per property), layer masks (toggle per layer), fairness overlay, reinforcement markers + capture zones + ownership colors, drift path overlays with tick slider.
- Hover shows gradient samples at cursor; click shows spine node metadata.
**`map_batch_png.py`** — Batch PNG generator.

- CLI: `python -m simulation.map_batch_png --archetype <name> --count N --out <dir>`.
- Generates N maps (varied region states), writes per-map PNG + contact sheet to `tuning_output/stage7/<run_name>/`.
- Per-map PNG shows spine, edges, 2 key gradients (obstacle_density + cover_density), layer 1 accessibility, reinforcement positions + ownership.

**Test files** (alongside each system): `test_layout_library.py`, `test_archetype_filters.py`, `test_layout_instantiator.py`, `test_gradient_placer.py`, `test_layer_masks.py`, `test_sim_flavoring.py`, `test_fairness_evaluator.py`, `test_map_generator.py`, `test_reinforcement.py`, `test_spine_drift.py`, `test_stage7_integration.py`.
### Files to modify

**`mission_contracts.py`** — Extend `MissionSetup.map_params` dict schema: `archetype`, `region_id`, `canvas_size`, `seed`, `generated` (bool). Possibly extend `ReinforcementSpec` for S7-5 ownership baseline parameters. Document the schema change in `docs/architecture.md` before code lands (per CLAUDE.md rule; `MissionSetup` is the mission-shape contract).

**`tactical_map.py`** — Add `drifting_nodes` list + `current_spine_node_positions(tick) → dict[node_id, (x, y)]`. Static-only maps unaffected. Engine code reading positions uses tick-dependent accessor only where drift matters (objectives and capture points).

**`tactical_engine.py`** — Tick loop extended:

- `update_drifting_nodes(self, self.tick)` + `step_reinforcement(self, self.dt)` after unit decision loop, before objective evaluation.
- `self.reinforcement_structures: list[ReinforcementStructure]` initialized from `MissionSetup.reinforcements` + `TacticalMap.spine_nodes` of type `reinforcement_structure`.
- `get_reinforcement_structures()` exposed for future UI consumption.
**`config.py`** — New constants (all tuning defaults, expect playtest adjustment):

```python
CANVAS_SIZES = {"small": (4000, 4000), "medium": (8000, 8000), "large": (12000, 12000)}
STRUCTURE_COUNT_RANGES = {"small": (2, 4), "medium": (3, 6), "large": (4, 8)}  # S7-4 tuning; updated to match docs/bible_history/bible_2_00_combat.md guidance
LAYOUT_JITTER_PERCENT = 0.03
REINFORCEMENT_CAPTURE_RADIUS = 300
REINFORCEMENT_CAPTURE_DURATION_SEC = 10.0
REINFORCEMENT_STRUCTURE_HP = 3000
BASE_PRODUCTION_TIME_SEC = 30.0
POWER_NORMALIZATION = <baseline unit power>  # tune from Stage 6
COMPOSITION_SKEW_THRESHOLD = 0.70
COMPOSITION_SHIFT_MAGNITUDE = 0.15
OWNERSHIP_MILITARY_COEFF = 0.15   # S7-5 delta: military → player/enemy axis
OWNERSHIP_TENSION_COEFF = 0.15    # S7-5 delta: tension → neutral share
FAIRNESS_MAX_RETRIES = 5
# FAIRNESS_ACCEPTABLE_SCORE removed — replaced by per-archetype FairnessTargetProfile
# authored in archetype_filters.py. See "Archetype-Aware Fairness."
# Per-node-type gradient intensity and radius constants (one per node type, documented inline)
```

### Files NOT to modify

- Protected engine files (CLAUDE.md): `tick.py`, `drift.py` (→ use `spine_drift.py`), `faction.py`, `region.py`, `events.py`, `event_engine.py`, `intent_resolver.py`, `border_friction.py`, `technology.py`, `diplomacy.py`, `world.py`, `templates.py`, `theme_scifi.py`. None touched in Stage 7.
- `socket_server.py` — requires explicit user confirmation.
- `test_maps.py` — Stage 6 hand-authored maps. Keep for regression tests. Do not delete / deprecate.
### Input/Output Shapes

Generator input:

```python
GeneratorInput(
    archetype="defensive_stand",
    region_state=RegionState(
        stability=0.7, capacity=0.6,
        economy=45.0, tension=62.0, military=58.0, population=72.0,
        region_id="region_07", tier=2,  # debug/label only
    ),
    canvas_size="medium",
    seed=0x4a7f2c,
)
```

Generator output:

```python
MapGenerationResult(
    tactical_map=TacticalMap(...),  # ready for TacticalEngine
    chosen_layout_id="layout_03_three_front_valley",
    fairness_score=FairnessScore(
        # direction-preserving ratios (player_value / enemy_value)
        path_balance_ratio=0.63,  target=(0.60, 0.15),  within_tolerance=True,
        travel_time_ratio=1.04,   target=(1.00, 0.15),  within_tolerance=True,
        vantage_ratio=1.12,       target=(1.15, 0.15),  within_tolerance=True,
        hazard_ratio=0.78,        target=(0.75, 0.15),  within_tolerance=True,
        archetype_profile="defensive_stand",
        all_metrics_pass=True,
    ),
    generation_metadata={
        "candidate_layouts": ["layout_01", "layout_03", "layout_07"],
        "fairness_retries": 0,
        "gradient_source_count": 14,
        "reinforcement_structure_count": 4,
        "reinforcement_ownership": {"player": 2, "neutral": 1, "enemy": 1},
    },
)
```

Reinforcement structure in engine state:

```python
ReinforcementStructure(
    structure_uid=103,
    position=(4200.0, 3100.0), layer=1,
    hp=3000, max_hp=3000,
    owner_faction=PLAYER_FACTION,
    capture_progress=0.0,
    production_timer_sec=0.0,
    production_target_unit_type="vanguard",
    capture_radius=300.0,
)
```

Drifting node position at tick:

```python
tactical_map.current_spine_node_positions(tick=1200)
# {
#   "obj_alpha": (4500.0, 3100.0),
#   "reinforcement_2": (5200.0, 4100.0),
# }
```

### Spawn Point vs Reinforcement Structure Placement

Two distinct mechanisms put enemy units onto generated maps. They are not interchangeable:

- **`spawn_point` spine nodes** — authored into strategic layouts. Stage 5.5 / the tactical engine uses these as the location(s) where the **initial enemy force** is placed at mission start. Pre-placed units, before the first tick.
- **Reinforcement structures** — a separate spine node type (S7 resolution). During the mission, each captured-and-owned structure produces **additional units at its own structure position** per the production timer. These are distinct from the spawn_point-seeded initial force.

The generator outputs both node types in the `TacticalMap`; which one drives a given unit's origin depends on whether it's an initial-placement unit or a mid-mission reinforcement. `gradient_placer.py` does not place gradient sources on `spawn_point` nodes (they are pure placement markers, not terrain features).

### S7-5 Ownership Rule

Reinforcement structure initial ownership = **archetype-authored baseline + bounded simulation-state delta**, per S7-5.

**Baseline (Stage 7 scope).** All 10 archetypes use the uniform fallback `{player: 0.33, neutral: 0.34, enemy: 0.33}` in Stage 7. The 4 prototype archetypes (Defensive Stand, Assault, Multi-Front Defense, Counterinsurgency) receive authored baselines in Stage 7.5 per S75-2; they plug into the same resolver and the other 6 keep the fallback until their scripts land.

**Delta (Stage 7 scope).** The mission region's simulation state produces a smooth signed shift on top of the baseline:

```python
player_shift  = OWNERSHIP_MILITARY_COEFF * (region.military - 50) / 50
neutral_shift = OWNERSHIP_TENSION_COEFF  * (region.tension  - 50) / 50

player  = baseline.player  + player_shift  - neutral_shift / 2
enemy   = baseline.enemy   - player_shift  - neutral_shift / 2
neutral = baseline.neutral + neutral_shift

# clamp each to [0, 1], then renormalize so the three sum to 1
```

- Military drives the player↔enemy axis: `military=100` maximally favors player-owned, `military=0` maximally favors enemy-owned, `military=50` produces zero shift.
- Tension drives the neutral share: `tension=100` pulls weight into neutral, `tension=0` pulls it out (distributing equally between player and enemy).
- **Economy and population do NOT influence ownership.**
- The per-field coefficients `OWNERSHIP_MILITARY_COEFF` and `OWNERSHIP_TENSION_COEFF` are the full tuning surface; both are tuning values. Proposed defaults: `0.15` each (max ±15% shift per field at its extremes, yielding ≤~30% total deviation from baseline). Clamp + renormalize ensures the result is always a valid distribution regardless of coefficient choice.

This mirrors the `sim_flavoring.py` pattern (linear, continuous) S7-5 explicitly cited as its model — the same simulation state that flavors gradient intensities also flavors starting ownership, by analogous math.

### Archetype-Aware Fairness

The fairness evaluator's job is to verify that a generated map **delivers the archetype's intended experience** — not to enforce symmetry. Some archetypes are intentionally asymmetric (Defensive Stand favors the defender, Counterinsurgency has dispersed/hidden enemy positioning), and a symmetric-only evaluator would reject them outright.

Each archetype authors a `FairnessTargetProfile` alongside its compatibility filter in `archetype_filters.py`:

```python
@dataclass(frozen=True)
class FairnessTargetProfile:
    path_balance: tuple[float, float]        # (target_ratio, tolerance)
    travel_time_balance: tuple[float, float]
    vantage_balance: tuple[float, float]
    hazard_balance: tuple[float, float]
```

Each metric computes a ratio `player_value / enemy_value`. A profile of `(1.0, 0.15)` means "target is symmetric ±15%." A profile of `(0.60, 0.15)` means "I want the player side to have ~60% of what the enemy has — fewer paths in, for instance — within a 15% window." Evaluator passes the metric iff `abs(measured_ratio - target) ≤ tolerance`.

**Prototype archetype profiles (authored in Stage 7):**

| Archetype | path_balance | travel_time_balance | vantage_balance | hazard_balance |
|---|---|---|---|---|
| **Defensive Stand** | `(0.60, 0.15)` — fewer enemy ingress routes | `(1.00, 0.15)` | `(1.15, 0.15)` — defender slight vantage edge | `(0.75, 0.15)` — hazards along enemy approach |
| **Assault** | `(1.70, 0.20)` — inverse of Defensive Stand; attacker paths matter | `(1.00, 0.15)` | `(0.85, 0.15)` | `(1.30, 0.20)` — hazards in defender zone |
| **Multi-Front Defense** | `(1.00, 0.15)` — symmetric | `(1.00, 0.15)` | `(1.00, 0.15)` | `(1.00, 0.15)` |
| **Counterinsurgency** | `(1.00, 0.25)` — wide tolerance (dispersed enemy) | `(1.00, 0.20)` | `(1.20, 0.20)` — player has sensor/vantage edge | `(0.60, 0.20)` — interference clusters around enemy |

All target values and tolerances above are tuning defaults. Exact numbers calibrate during Checkpoint H and Checkpoint I playtesting.

**Non-prototype archetypes (all 6):** use a safe symmetric default of `(1.0, 0.15)` on every metric until their Stage 7.5 behavior scripts ship. This preserves today's behavior for them — they're just slightly more permissive than the old single-aggregate threshold, because each metric is now checked independently.

**Why ratios instead of 0–1 scores:** the old formulation ("each metric is a 0–1 symmetry score") threw away direction. A map that's wrong-direction-asymmetric for Defensive Stand (enemy dug in, player attacking) would score the same as a correctly-asymmetric one. Ratios preserve direction, so a Defensive Stand map with `path_balance=1.67` (inverted) fails because it's nowhere near its `0.60` target, even though its "symmetry distance" is the same as the correct `0.60` map. This is the whole point of archetype-aware fairness.

## Implementation Checkpoints

Each checkpoint is a hard stop. Run test, show output (terminal + PNG paths + viewer launch command), wait for Westley approval. Do not batch. Do not continue without explicit approval.

### Checkpoint A — Contracts + Sample Layout + Viewer Scaffolding

**Build:** `map_gen_contracts.py`, `layout_library.py`, one sample layout JSON (`layout_01_fortress_ridge.json`), `map_viewer.py` scaffolding (zones + edges, no gradients yet).

**Test:** `test_layout_library.py` — load sample, validate, print zone/edge breakdown.

**Print:** Layout ID, name, canvas_class, zone count by node type, edge count by edge type, validation status, viewer launch command.

**Verify:** Sample loads clean. Viewer shows zones in correct relative positions, edges correct, types color-coded. Visually Fortress Ridge looks like a fortress ridge.

⛔ STOP. Show output. Wait for Westley.

### Checkpoint B — Archetype Compatibility Filter Language

**Build:** `archetype_filters.py` — primitives, operators, `evaluate_filter()`, full filters for 4 prototype archetypes, stubs for other 6.

**Test:** `test_archetype_filters.py` — evaluate each prototype filter against sample layout; pathological test layouts (no chokepoints / no flank / no vantage) verified rejected by correct filters.

**Print:** Human-readable filter rules per archetype; evaluation results on sample; pathological rejection table.

**Verify:** Filter language expresses bible's map-character prose. False-positive / false-negative behavior matches intent.

⛔ STOP.

### Checkpoint C — Full 8-Layout Library + Compatibility Matrix

**Build:** Author remaining 7 layouts. At least one layout per prototype archetype; ≥3 layouts with 2+ archetype compatibility.

**Test:** Load all 8, validate, run all 10 archetype filters → 8×10 compatibility matrix.

**Print:** Compatibility matrix, per-archetype coverage, cross-pollination count. PNG contact sheet of all 8 layouts → `tuning_output/stage7/checkpoint_c/`.

**Verify:** Each prototype archetype has ≥1 compatible layout. Contact sheet shows 8 visually distinct layouts (not variations of same shape).

⛔ STOP.

### Checkpoint D — Layout Instantiation

**Build:** `layout_instantiator.py` — canvas scaling, seeded jitter, `SpineNode` construction.

**Test:** Instantiate one layout at each canvas size; 5-seed determinism + variety check.

**Print:** Per canvas size: zone positions, min/max edge lengths. Determinism hash comparison. Jitter variety stats.

**Visual:** PNGs — 3 canvas sizes + 5 jitter seeds → `tuning_output/stage7/checkpoint_d/`.

**Verify:** Canvas scaling preserves topology. Jitter visible but bounded. Determinism holds.

⛔ STOP.

### Checkpoint E — Gradient Placer

**Build:** `gradient_placer.py` — per-node-type placement for 4 continuous properties.

**Test:** For each layout, place gradients; sample at each spine node; assert expected magnitudes.

**Print:** Per-layout gradient source counts by property; sampled values at node positions; anomalies.

**Visual:** PNGs — each layout × 4 heatmap overlays → `tuning_output/stage7/checkpoint_e/`.

**Verify:** Chokepoints → high `obstacle_density`; staging → `cover_density`; vantage → `elevation`; hazard anchor → `sensor_interference`. Heatmaps match spine intent.

⛔ STOP.

### Checkpoint F — Layer Accessibility Masks

**Build:** `layer_masks.py` — 5-layer `layer_block_N` sources; per-zone restrictions honored.

**Test:** Sample `layer_accessibility(x, y, layer)` grid for each layout × 5 layers; verify restrictions + default.

**Print:** Per-layout layer restriction summary; accessibility pass rate per layer.

**Visual:** PNGs — each layout × 5 layer overlays → `tuning_output/stage7/checkpoint_f/`.

**Verify:** All maps support 5 layers. Restrictions at intended zones. Default accessible.

⛔ STOP.

### Checkpoint G — Simulation Flavoring

**Build:** `sim_flavoring.py` — composite axis mappings + individual field deltas.

**Test:** Pick one layout; flavor with "prosperous core" / "war-torn frontier" / "mid-tier baseline" region states.

**Print:** Modifier bundles per flavoring; delta tables across region states per property.

**Visual:** PNG triptych — same layout × 3 region states → `tuning_output/stage7/checkpoint_g/`.

**Verify:** Visible qualitative differences. Prosperous → smoother, less interference. War-torn → more cover, more hazards. No state produces unplayable map.

⛔ STOP.

### Checkpoint H — Fairness Evaluator

**Build:** `fairness_evaluator.py` — 4 ratio metrics + archetype-aware `is_acceptable(score, archetype)`. Author `FairnessTargetProfile` for all 4 prototype archetypes in `archetype_filters.py` per the table in "Archetype-Aware Fairness."

**Test:** Score all 8 library layouts against each prototype archetype's profile. Construct **3 classes** of deliberately-unfair test layouts and verify correct per-archetype rejection:
- Symmetric-broken (e.g., all paths on one side) — must fail under *every* archetype profile.
- Wrong-direction-asymmetric (e.g., a Defensive-Stand-shaped map but with `path_balance=1.67` instead of `0.60`) — must fail under Defensive Stand specifically, even though the *magnitude* of asymmetry is correct.
- Right-direction-asymmetric (Defensive-Stand-shaped as intended) — must pass under Defensive Stand, may fail under symmetric archetypes (expected).

**Print:** Per archetype × per library layout: per-metric ratio + target + within-tolerance flag + aggregate pass/fail. For unfair constructions: which archetype rejected it and which metric(s) fired.

**Visual:** PNGs — each library layout annotated with its per-archetype pass/fail grid → `tuning_output/stage7/checkpoint_h/`.

**Verify:** All library layouts pass under at least one prototype archetype's profile. Wrong-direction-asymmetric maps fail under their target archetype (direction matters, not just magnitude). Symmetric-broken maps fail universally. Tolerances are neither so tight that correctly-asymmetric generations get rejected, nor so loose that egregious imbalance passes.

⛔ STOP.

### Checkpoint I — End-to-End Map Generator

**Build:** `map_generator.py` — full pipeline wiring A–H.

**Test:** 100 maps × 4 prototype archetypes (400 total), varied region states. Measure fairness pass rate, retry distribution, generation time, cache behavior, filter pass rate.

**Print:** Per-archetype: 100-map summary. Pipeline timing breakdown per stage. 10-rerun determinism check.

**Visual:** 4 × 100-up contact sheets + 10 detail PNGs per archetype → `tuning_output/stage7/checkpoint_i/`.

**Verify:** Fairness pass rate ≥90% first-try. p95 generation time <250ms small / <500ms large. Determinism holds. Contact sheets show variety + expected per-archetype character.

⛔ STOP.

### Checkpoint J — Reinforcement Structure Mechanics (capture + HP)

**Build:** `reinforcement.py` capture state machine + HP/destruction. Wire into `tactical_engine.py` tick loop (structures only, NOT production yet).

**Test:** Capture scenarios (uncontested / contested / abandoned / flipped). HP scenarios (damage to zero → removal).

**Print:** Per-tick progress for each capture scenario; capture time; ownership flip tick. HP over time; destruction tick; removal verification.

**Visual:** Pygame demo recording (GIF or PNG sequence) of capture + destruction → `tuning_output/stage7/checkpoint_j/`.

**Verify:** Capture completes in `REINFORCEMENT_CAPTURE_DURATION_SEC`. Contested stalls. Abandoned resets. HP destruction removes cleanly. Ownership transitions clean.

⛔ STOP.

### Checkpoint K — Production + Composition Reactivity

**Build:** Production timer + unit spawning + `select_enemy_unit_type()` with 70/15 skew.

**Test:** Production timing across unit tiers (verify power-rating scaling). Composition scenarios: 40/30/20/10 (no trigger), 70/15/10/5 (trigger), 75/15/5/5 (stronger skew).

**Print:** Per-unit-type spawn time vs expected. Per-scenario: player composition → pre-skew ratio → post-skew ratio → shift magnitude.

**Verify:** Timing matches formula. 70% threshold fires. 15% shift applied. <70% no trigger. Shift direction is toward counter category.

⛔ STOP.

### Checkpoint L — Drifting Spine Nodes

**Build:** `spine_drift.py` — `update_drifting_nodes()`, ping_pong + loop modes. Extend `tactical_map.py` with `current_spine_node_positions(tick)`. Wire update into engine tick loop.

**Test:** Test layout with 2 drifting objectives (ping_pong, different periods) + 1 drifting capture point (loop). 1000 ticks, sample every 10 ticks.

**Print:** Per drifting node: waypoints, period, sampled positions (first 200 ticks). Navmesh generation count (must equal 1).

**Visual:** Pygame tick slider; PNG sequence → `tuning_output/stage7/checkpoint_l/`.

**Verify:** Drift follows authored paths. Ping_pong reverses. Loop cycles. Period matches config. Navmesh static.

**Known gap:** `update_drifting_nodes` mutates `SpineNode.position` each tick, but `objectives.py _update_hold_zone` reads static `zone_x/zone_y` from params and never consults the spine node. Drifting objectives currently have no gameplay effect — they move visually but capture/hold evaluation stays anchored to the original position. Wiring objectives to read live spine node positions is deferred; it must land before drifting objectives are used in shipped missions.

⛔ STOP.

### Checkpoint M — Engine Integration + Performance (Final)

**Build:** Final wiring.

**Test:** Full mission pipeline: Stage 5.5 calls map generator → Stage 6 engine runs mission → reinforcements capture/produce/destroy → drifting objective moves → `MissionResult`. Performance: 200v200 on large generated map vs Stage 6 hand-authored baseline.

**Print:** Mission run: generation time, tick count, reinforcement events, drift distance, outcome band. Performance breakdown per subsystem. Regression check vs Stage 6 baseline (>15% fails per dev_rules performance regression discipline).

**Visual:** PNG sequence of mission at sampled ticks → `tuning_output/stage7/checkpoint_m/`.

**Verify:** Full pipeline works end-to-end. Performance parity within 15%. No protected-file edits (check git diff).

⛔ STOP.

## Invariants

- **I1** — Fairness pass rate: ≥90% first-try across 400-map batch.
- **I2** — Generation time p95: <250ms small, <500ms large.
- **I3** — Determinism: Same `GeneratorInput` → byte-identical `MapGenerationResult` across 10 re-runs.
- **I4** — Layer count: All generated maps have exactly 5 layers (S7-2).
- **I5** — Minimum structure: No generated map has zero reinforcement structures (generator guarantees ≥1).
- **I6** — Capture duration: Uncontested completes in `REINFORCEMENT_CAPTURE_DURATION_SEC` ± 1 tick.
- **I7** — Composition reactivity: 70% skew triggers; 50% skew does not.
- **I8** — Navmesh stability: Exactly one navmesh generation per mission, no regeneration on drift. **Measurement:** the navmesh module exposes a monotonic `generation_count` counter incremented on every build; Checkpoint L and Checkpoint M assert `generation_count == 1` after the mission completes (regardless of tick count or drift activity).
- **I9** — Engine performance parity: Generated-map per-tick time within 15% of Stage 6 hand-authored baseline.
- **I10** — Protected files untouched: `git diff` shows no protected-file modifications across the stage.

Per CLAUDE.md: if an invariant fails, you may not widen thresholds or weaken tests to make the implementation pass. Escalate real bugs, or narrow scope (skip-cases never meant to be caught). No other changes without Westley's approval.

## Integration Points

- **Stage 5.5 → 7:** Mission generator calls `generate_map(GeneratorInput(...), layout_library)` in `MissionSetup` construction. Behind `ENABLE_STAGE7_MAP_GEN` flag — default OFF until Checkpoint I passes, then ON.
- **Stage 6 → 7:** Engine reads `TacticalMap` from `MissionSetup` as before. Engine change is tick-loop extension for reinforcement + drift. Kill switch: `enable_reinforcement=False` in `MissionSetup` skips reinforcement step (clean pure-Stage-6 fallback). Drift automatic via `drifting_nodes`; empty list = zero cost.
- **Stage 7.5 forward:** Behavior scripts use existing `TacticalMap.spine_nodes` / `get_spine_nodes_by_type()`. No new API.
- **Stage 8 forward:** Godot renderer consumes `TacticalMap` + `current_spine_node_positions(tick)`. Contract is renderer-friendly.
## Done Condition

- All 13 checkpoints (A–M) run, shown, approved by Westley.
- All 10 invariants (I1–I10) pass.
- A full mission generated by Stage 7 pipeline runs to completion in Stage 6 engine with a classified `MissionResult`.
- Pygame viewer and PNG batch tool functional against any generated map.
- `tuning_output/stage7/` contains PNG artifacts from Checkpoints C, D, E, F, G, H, I, J, L, M.
- Bible capture items (hub roadmap entry + hub §15) presented to Westley as proposed diff and applied on approval.
- No protected engine file modified.
- `docs/architecture.md` reflects `MissionSetup.map_params` schema change.

## Files Created

(Filled in after implementation.)

## Notes for the Implementing Session

- Stage 6 Checkpoint J is still in progress. Stage 7 does not depend on J completing — map generator is independent of Strike/Line/Siege tuning. If a Stage 6 stat change breaks a Stage 7 test, the Stage 7 test is the wrong side to adjust — flag to Westley and defer.
- Checkpoint order is tight. A → B → C → D/E/F → G → H → I → J → K. L independent of J/K but depends on D. M is last.
- Pygame viewer and PNG batch tool are throwaway for Stage 8. Do not over-engineer. If Godot ships before Stage 7 wraps, retire them.
- Behavior script runner is Stage 7.5, not Stage 7. Enemy units in Stage 7 integration use Stage 6 command primitives (attack-move). Scripted behaviors arrive in 7.5.
# Stage 1 — World Generation and Multi-Region Drift (Prove Regions Interact)

## Goal

Prove that a world of connected regions drifts differently based on starting values and connections, using the SD model proven in Stage 0 on a single region.

## Context

**Read in game_bible.md:**
- "World Generation — Tiered Templates" — defines the isolated start template, region tiers, and field value ranges
- "Inter-Region Topology — Typed Adjacency Graph" — defines edge types (border, trade, both), but this stage uses untyped "both" per the bible's implementation approach
- "Per-Tick Update Model" — the drift formulas proven in Stage 0, now applied across multiple regions
- "Region State Model — Layered Architecture" — the four granular fields and two composite axes

**Builds on:** Stage 0 (single-region passive drift, config values, field clamping, composite axis computation). Stage 0's `region.py` and `config.py` are the foundation. This stage adds the world graph and multi-region tick loop around the existing single-region logic.

**Era-agnostic principle:** All code in this stage uses abstract mechanical terms. Region display names come from the theme file (`theme_scifi.py`), not from engine code. See `era_agnostic_refactor.md` for the full policy.

## What to Build

### 1. `world.py` — World graph and generation

A World class that holds multiple Region instances connected by an adjacency graph. Responsible for:
- Storing regions as a dict (region_id → Region)
- Storing edges as an adjacency list with edge type tags
- Generating a world from a template definition
- Providing neighbor queries: "give me all neighbors of region X" (optionally filtered by edge type, but all edges are "both" for this stage)

### 2. `templates.py` — World starting templates

Defines the isolated start template as a data structure. Each template specifies:
- How many regions of each tier (home, frontier, empty)
- The adjacency connections between them
- Field value ranges per tier (randomized within range at generation)

Only the **isolated start** template for this stage: 1 home region, 2 frontier regions, 4–6 empty regions. Empty regions have zeroed-out fields and are inactive (skipped during drift).

### 3. `simulation.py` — Multi-region tick loop

A tick function that iterates all active regions and applies passive drift. This is the Stage 0 single-region drift logic called in a loop across the world. No events, no factions, no inter-region effects yet — each region drifts independently based on its own field values.

### 4. `test_stage_1.py` — Test and verification script

A runnable script that generates a world from the isolated start template, runs N ticks (configurable, default 200), and prints per-region field summaries at checkpoints. This is the prove-it script Westley uses to verify the stage.

### 5. Updates to `config.py`

Add template field value ranges (home military range, frontier economy range, etc.) as config values. All new tuning parameters go here.

## Input/Output Shapes

### Template definition (in `templates.py`)

```python
ISOLATED_START = {
    "name": "isolated_start",
    "regions": [
        {"id": "home_1", "tier": "home", "fields": {
            "military": (55, 70),      # (min, max) — randomized at generation
            "economy": (60, 75),
            "tension": (10, 25),
            "population": (50, 65)
        }},
        {"id": "frontier_1", "tier": "frontier", "fields": {
            "military": (20, 35),
            "economy": (25, 40),
            "tension": (5, 15),
            "population": (15, 30)
        }},
        {"id": "frontier_2", "tier": "frontier", "fields": {
            "military": (20, 35),
            "economy": (25, 40),
            "tension": (5, 15),
            "population": (15, 30)
        }},
        {"id": "empty_1", "tier": "empty", "fields": None},
        {"id": "empty_2", "tier": "empty", "fields": None},
        {"id": "empty_3", "tier": "empty", "fields": None},
        {"id": "empty_4", "tier": "empty", "fields": None},
    ],
    "edges": [
        ("home_1", "frontier_1", "both"),
        ("home_1", "frontier_2", "both"),
        ("frontier_1", "empty_1", "both"),
        ("frontier_1", "empty_2", "both"),
        ("frontier_2", "empty_3", "both"),
        ("frontier_2", "empty_4", "both"),
    ]
}
```

### World state (output of `world.generate()`)

```python
{
    "regions": {
        "home_1": {
            "tier": "home",
            "active": True,
            "fields": {"military": 63, "economy": 68, "tension": 18, "population": 57},
            "composites": {"stability": 72.4, "capacity": 65.1}
        },
        "frontier_1": {
            "tier": "frontier",
            "active": True,
            "fields": {"military": 28, "economy": 33, "tension": 11, "population": 22},
            "composites": {"stability": 41.2, "capacity": 30.8}
        },
        # ... etc
        "empty_1": {
            "tier": "empty",
            "active": False,
            "fields": {"military": 0, "economy": 0, "tension": 0, "population": 0},
            "composites": {"stability": 0, "capacity": 0}
        }
    },
    "edges": [
        {"from": "home_1", "to": "frontier_1", "type": "both"},
        # ...
    ]
}
```

### Tick output (per tick, for logging)

```python
{
    "tick": 42,
    "regions": {
        "home_1": {
            "fields": {"military": 61.3, "economy": 69.1, "tension": 20.4, "population": 57.8},
            "composites": {"stability": 70.1, "capacity": 64.3},
            "deltas": {"military": -0.2, "economy": +0.3, "tension": +0.1, "population": +0.1}
        },
        # ... only active regions
    }
}
```

## Integration Points

- **Imports Stage 0's Region class** (or equivalent) for per-region state and drift logic. Does not modify Stage 0 code — wraps it.
- **Imports Stage 0's config** and extends it with template-specific values.
- **Region display names** come from the theme file (`theme_scifi.py`), not from engine code.
- **No config flags needed** — this stage is the foundation, not an optional system.

## Checkpoints

Claude Code should stop and wait for Westley's verification at each checkpoint before proceeding to the next. Each checkpoint has specific things to look for in the output.

### Checkpoint 1: World generation from template

**Run:** Generate a world from the isolated start template. Print the full initial state of all regions.

**Verify:**
- 7 regions exist (1 home, 2 frontier, 4 empty)
- Home region fields are within the config ranges (military 55–70, economy 60–75, etc.)
- Frontier regions are weaker than home across all fields
- Empty regions have zeroed fields and are marked inactive
- Adjacency graph is correct: home connects to both frontiers, each frontier connects to 2 empty regions
- Running generation twice produces different field values (randomization works)

### Checkpoint 2: Home region drift matches Stage 0 behavior

**Run:** Generate a world. Run 50 ticks. Print home region fields every 10 ticks.

**Verify:**
- Home region drift behavior matches what was proven in Stage 0 for a region with similar starting values
- Military drift follows the maintenance cost / recruitment formula
- Economy grows based on population, dragged by tension
- Tension rises from prosperity pressure (home has high pop + high economy)
- Population grows logistically
- Fields stay clamped 0–100
- Composites update correctly each tick

### Checkpoint 3: Frontier regions drift differently from home

**Run:** Same 50-tick run. Print all active regions' fields every 10 ticks side by side.

**Verify:**
- Frontier regions drift differently from home because they start with different field values
- Low-economy frontiers should see military decay faster (can't afford maintenance)
- Low-population frontiers should see slower economic growth
- Frontier tension behavior differs from home (less prosperity pressure due to lower pop × economy)
- The two frontier regions may diverge from each other despite similar starting ranges (different random initial values)

### Checkpoint 4: Long-run behavior is coherent

**Run:** Generate a world. Run 500 ticks. Print all active regions' fields at ticks 0, 100, 200, 300, 400, 500.

**Verify:**
- No fields have gone to degenerate states (stuck at 0 or 100 for hundreds of ticks with no recovery path)
- Home region hasn't collapsed if starting values were healthy — the drift should produce slow change, not immediate crisis
- Frontier regions show more volatility than home (weaker starting position makes them more sensitive to drift interactions)
- The overall trajectory is coherent — not random noise and not a flatline
- Empty regions remain unchanged (inactive, skipped during drift)

### Checkpoint 5: Multiple generations produce variety

**Run:** Generate 5 worlds from the same template. Run each for 100 ticks. Print the final state of the home region for each.

**Verify:**
- Different random starting values within the template ranges lead to meaningfully different 100-tick outcomes
- No two runs produce identical trajectories
- All runs produce plausible states (no run immediately collapses, no run produces absurd values)

## Done Condition

All five checkpoints pass. Westley has reviewed the output at each checkpoint and confirmed:
1. World generation from template works correctly with proper randomization
2. Multi-region drift produces the same behavior as Stage 0 for equivalent starting values
3. Different starting values produce meaningfully different drift trajectories
4. Long-run behavior is coherent and plausible
5. Multiple generations produce variety

Westley signs off before Stage 2 begins.

## Files Created

*(Filled in after implementation)*

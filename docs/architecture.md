# Architecture — Cross-Stage Contracts

## MissionSetup.map_params

`MissionSetup.map_params` uses the `MapParams` TypedDict defined in `simulation/mission_contracts.py`.

```python
class MapParams(TypedDict, total=False):
    seed: int
    archetype: str
    region_id: str
    canvas_size: int
    generated: bool
```

### `seed` field lifecycle

- **Produced by:** `simulation/mission_generator.py` — generates `rng.randint(0, 2**31 - 1)` at mission creation time, stored in `map_params["seed"]`.
- **Consumed by:** `simulation/pipe_transport.py` — reads `setup.map_params.get("seed", current_tick)` when building `GeneratorInput` for the map generator.
- **Persisted by:** Stage 8's save/load system — `MissionSetup` is part of the tactical save blob; `map_params` round-trips through JSON transparently.
- **Fallback:** `current_tick` is used only for pre-Stage-11b saves that have empty `map_params`. This is temporary compatibility debt; once old saves are no longer supported, a missing seed should raise.

### Design authority

`bible_world.md:178` — *"…and a random seed (ensures reproducibility for replays and bug reports)."*
`bible_world.md:196` — *"the map is regenerated with a new random seed"* on fairness failure.

Added in Stage 11b (`stage_11b_map_variety_spec.md`).

## FairnessScore — metric skip semantics (Stage 11e)

`FairnessScore` in `simulation/fairness_evaluator.py` carries a `*_skipped` bool per metric (`path_balance_skipped`, `travel_time_skipped`, `vantage_skipped`, `hazard_skipped`).

When a layout has zero of a fairness-relevant node type on **both sides** (e.g., zero vantage nodes total), the corresponding metric is **skipped** — not counted toward the aggregate pass/fail. `is_acceptable()` passes when all non-skipped metrics fall within their tolerances.

This is a scope-narrowing fix per CLAUDE.md: balance of an absent node type is undefined, not "balanced." One-side-zero (e.g., player has 0 vantage, enemy has 3) is a real imbalance and still fails.

Added in Stage 11e (`stage_11e_fairness_reconciliation_spec.md`).

## Map Generation — Simple Picker (Stage 11e pivot)

`simulation/map_generator.py:generate_map()` uses a single-pass random picker:

1. Run archetype compatibility filter → candidate pool.
2. Pick one layout uniformly at random (seeded by `GeneratorInput.seed`).
3. Instantiate, assign reinforcement ownership, place gradients.
4. Evaluate fairness (score logged to `tuning_output/fairness_log/<date>.jsonl`, **not used for rejection**).
5. Return result.

No retry loop. `generation_metadata["fairness_retries"]` is always 0. The evaluator infrastructure (`FairnessScore`, `FairnessTargetProfile`, all four metrics) is preserved intact for the future redesign (`stage_11f_fairness_redesign_spec.md`).

## Objective Snapshot Extension (Stage 11d)

Each objective entry in the `objectives` array of a full snapshot now carries two additional fields:

### `is_primary` (bool)
Whether this is a primary objective. Always present.

### `location` (optional object)
Present only for objective types with a meaningful geographic center:
- `hold_zone`, `clear_zone` → `{"x": <zone_x>, "y": <zone_y>}`
- `escort_to_extraction` → `{"x": <extraction_x>, "y": <extraction_y>}`
- `eliminate_force` → centroid of living target unit positions; omitted if all targets are dead.
- `survive_duration`, `destroy_targets` → omitted (no location).

Shape when present: `{"x": float, "y": float}`

Renderer must tolerate missing `location`. Delta objective updates may carry `location` if it has changed since the last update; static-location objective types (`hold_zone`, `escort_to_extraction`) carry it only on full snapshots.

See also: `scenes/tactical/hud.gd` — consumes `objective.location` for marker rendering.

## World View Inspection Payloads (Stage 11g)

Stage 11g extends keyframe and chronicle-entry shapes to support per-region inspection panels, per-faction inspection panels, faction-color vivacity scaling, and clickable in-text mentions in the chronicle.

All extensions are **flag-gated** on the producer side. With the relevant flag off, payloads are bit-identical to pre-11g. Renderers must tolerate missing fields and degrade to current behavior.

### `regions_snapshot[]` per-region extension

`regions_snapshot` (in each keyframe, produced by `simulation/world_view/keyframe_selector.py`) gains four optional fields per entry. Existing fields (`region_id`, `owner_faction_id`, `significance`, `x`, `y`, `z`) are unchanged.

```python
{
    "region_id": "r_001",
    "owner_faction_id": "f_dominion",
    "significance": 0.84,
    "x": 12.4, "y": -3.1, "z": 7.8,

    # NEW (Stage 11g, gated on ENABLE_FACTION_PALETTE / inspection panels)
    "name": "Valen Reach",                    # Display name from theme_scifi
    "tier": "frontier",                       # "home" | "frontier" | "empty"
    "fields": {                               # 0..100 each, mirrors simulation Region fields
        "military": 42.7,
        "economy": 71.0,
        "tension": 18.4,
        "population": 53.2,
    },
}
```

- **Produced by:** `keyframe_selector.py::select_keyframes` — reads from `world.regions[rid]`. No engine modification.
- **Consumed by:** `scenes/shared/world_view/world_view_data.gd::set_region_metadata` and downstream `region_info_panel.gd`.
- **Fallback:** missing `name` → fall back to `region_id`. Missing `tier` → "frontier". Missing `fields` → panel shows "—" for each bar.

Composite axes (`stability`, `capacity`) are computed Godot-side from the four base fields and are **not transmitted**. This keeps the payload minimal and lets the formula evolve in one place.

### `factions_snapshot[]` (new top-level keyframe field)

Each keyframe gains an optional `factions_snapshot` array — one entry per living faction at that keyframe's tick.

```python
"factions_snapshot": [
    {
        "faction_id": "f_dominion",
        "name": "The Dominion",
        "archetype": "Conqueror",
        "tech_tier": 47,             # 0..100; bible_simulation.md:473
    },
    ...
]
```

- **Produced by:** `keyframe_selector.py` reading `world.factions[fid]`. Entries omit factions with zero owned regions at that tick (defeated factions appear in `ownership_history.previous_owners` instead).
- **Consumed by:** `WorldViewData.set_faction_metadata` → `faction_info_panel.gd`.
- **Aggregates** (military/economy/tension/population) are computed Godot-side as the mean of the faction's owned-region `fields`. Not transmitted.
- **Stability across keyframes:** `name`/`archetype`/`tech_tier` rarely change within a jump. The renderer caches per-jump and updates only on diff.

### `chronicle_entry.mentions[]` (chronicle entry message extension)

`scroll_entries_to_messages` (in `keyframe_message.py`) adds an optional `mentions` field per chronicle entry. The same array applies to both `base_form` and `expanded_form`; entries with form-specific spans use the `form` discriminator.

```python
{
    "type": "chronicle_entry",
    "time_jump_id": "tj_0003",
    "entry_id": "ce_0007",
    "tick_range_start": 1820,
    "tick_range_end": 1855,
    "base_form": "Valen Reach, held by The Dominion, fell silent.",
    "expanded_form": "...",

    # NEW (Stage 11g, gated on ENABLE_CHRONICLE_MENTIONS)
    "mentions": [
        {"kind": "region",  "id": "r_001",      "form": "base", "span_start": 0,  "span_end": 11},
        {"kind": "faction", "id": "f_dominion", "form": "base", "span_start": 22, "span_end": 34},
        {"kind": "region",  "id": "r_001",      "form": "expanded", "span_start": 0, "span_end": 11},
    ],
}
```

- **Produced by:** `simulation/chronicle_assembler.py`. Spans are character offsets into the final assembled text **after** `_apply_first_mention` enrichment runs (the enricher must update spans when it appends ", held by [Faction]").
- **Overlap rule:** longest-match wins. The assembler resolves overlaps before emitting the array.
- **Consumed by:** `scenes/world/chronicle_entry.gd::_rebuild_bbcode` — wraps word-runs whose char-range falls inside a mention with `[url=region:rid]…[/url]` or `[url=faction:fid]…[/url]`. Color tags nest inside the url tag preserving per-word vivacity.
- **Fallback:** missing or empty `mentions` → entry renders with no clickable spans (today's behavior).

### `ownership_history` (new field on `time_jump_start`)

`time_jump_lifecycle_messages::start_msg` gains an optional `ownership_history` field, produced by the new side-car `simulation/world_view/ownership_history.py`. Two parallel maps:

```python
"ownership_history": {
    "factions": {
        "f_dominion": {
            "region_count_history": [12, 11, 11, 9, 7],   # last 5 jumps, oldest first
            "status": "waning",                            # "rising" | "stable" | "waning" | "defeated"
        },
        ...
    },
    "regions": {
        "r_001": {
            "previous_owners": ["f_kestrel", "f_dominion"],   # most recent last; current owner not included
            "held_since_tick": 1820,
        },
        ...
    },
}
```

- **Produced by:** `ownership_history.py` — observes the keyframe sequence as it's built; reads `world.regions` and `world.factions` snapshots only. No engine modification.
- **Consumed by:** `region_info_panel.gd` (history one-liner), `faction_info_panel.gd` (status badge).
- **Fallback:** missing `ownership_history` → status badge defaults to "Stable", region panel shows "—" for previous-owners line.

### Producer/consumer summary

| Field | Producer file | Consumer file (Godot) | Flag |
|---|---|---|---|
| `regions_snapshot[].name/tier/fields` | `keyframe_selector.py` | `world_view_data.gd`, `region_info_panel.gd` | `ENABLE_INSPECTION_PANELS` |
| `factions_snapshot[]` | `keyframe_selector.py` | `world_view_data.gd`, `faction_info_panel.gd`, `faction_palette.gd` | `ENABLE_INSPECTION_PANELS` ‖ `ENABLE_FACTION_PALETTE` |
| `chronicle_entry.mentions[]` | `chronicle_assembler.py` → `keyframe_message.py` | `chronicle_entry.gd`, `chronicle_entry_expansion.gd` | `ENABLE_CHRONICLE_MENTIONS` |
| `time_jump_start.ownership_history` | `ownership_history.py` → `keyframe_message.py` | panels (history line, status badge) | `ENABLE_OWNERSHIP_HISTORY` |

### Design authority

- `bible_monetization.md:540–542` — region briefing card and enemy assessment card field lists.
- `bible_world.md:466` — faction data panel with "name, total systems, aggregate stats."
- `bible_world.md:481` — chronicle text tinted in entry's primary subject's faction color.
- Faction color vivacity scaling, sim-pause-on-inspect, and clickable in-text mentions are stage-11g inventions; bible amendments are part of this stage's deliverables.

Added in Stage 11g (`stage_11g_world_view_inspection_spec.md`).

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

`docs/bible_history/bible_2_00_world.md:178` — *"…and a random seed (ensures reproducibility for replays and bug reports)."*
`docs/bible_history/bible_2_00_world.md:196` — *"the map is regenerated with a new random seed"* on fairness failure.

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
        "tech_tier": 47,             # 0..100; docs/bible_history/bible_2_00_simulation.md:473
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

- `docs/bible/epics/E-16-client-camera-hud-and-world-view.md` S-107 (faction data panel) and E-10 S-079 (briefing) — the region briefing card and enemy assessment card field lists were in `bible_monetization.md`, deleted 2026-05-31; the current design is the player-perception rules in those stories.
- `docs/bible_history/bible_2_00_world.md:466` — faction data panel with "name, total systems, aggregate stats."
- `docs/bible_history/bible_2_00_world.md:481` — chronicle text tinted in entry's primary subject's faction color.
- Faction color vivacity scaling, sim-pause-on-inspect, and clickable in-text mentions are stage-11g inventions; bible amendments are part of this stage's deliverables.

Added in Stage 11g (`stage_11g_world_view_inspection_spec.md`).

## Map Manifest — `cover_asteroids` field (Wave 2.5R)

`cover_asteroids` is emitted once at map manifest write (i.e., in the first full snapshot for a mission). It is **NOT** in the per-tick delta — asteroids are non-destructible in Phase 1 and static for the lifetime of the mission.

### Shape

```python
"cover_asteroids": [
    {
        "id":      a.asteroid_id,   # int — unique across the whole map
        "cluster": a.cluster_id,    # int — which spine-node cluster this belongs to
        "x":       a.x,             # float — world units
        "y":       a.y,             # float — world units
        "r":       a.radius_xy,     # float — footprint radius (world units)
        "h":       a.height,        # float — vertical extent; drives layer-block threshold
        "class":   a.scale_class,   # str  — "tiny" | "small" | "medium" | "huge"
    }
    for a in tactical_map.asteroid_field.asteroids
]
```

### Semantics

- Produced by `simulation/snapshot_serializer.py::serialize_cover_asteroids(tactical_map)`.
- Consumed by `scenes/tactical/terrain_renderer.gd::_scatter_cover_asteroids` at mission load.
- Layer-block rule: asteroid blocks layer `i` iff `asteroid.height >= LAYER_Z_FLOORS[i]` (see `config.LAYER_Z_FLOORS`).
- `delta()` never includes this field. Clients must not expect it in tick-delta payloads.

Added in Wave 2.5R (`cover_asteroid_los_spec.md`).

## C transport v1 (2026-09-22, the tick-delta rule: shapes first, then T1 builds them)

The C pipe server (`pipe/ouroboros_pipe`, source `csrc/pipe/om_pipe.c`, piece T1) speaks to Godot over stdio with the same framing the old Python pipe used, so `autoload/sim_bridge.gd`'s reader is reused: **4-byte big-endian length prefix, then UTF-8 JSON**, both directions (the C server reads commands from stdin with the same framing; the temp-file command channel is retired). Every message has `"type"`. The server carries **no names, no positions, no prose** (decision C5): the client layout pass owns positions and the offline library owns names and prose; the server sends indices, ids, enum ints and numbers only. Keys are stable; a client ignores keys it does not know; a removed key fails `tests/transport/test_pipe_shapes.py`.

Enums are sent as the header's integer values (`om_tier`, `om_archetype`, `om_stance`, `om_edge_type`, `om_feature`, `om_bug`); the client maps them through `EraThemeResolver` or a table, never by name.

### hello (server to client, once)
```json
{"type":"hello","abi":2,"layout_ok":true,"seed":1,"n_regions":60,"features":[1,2,3,6],"checksum_cadence":10}
```
`abi` is `om_abi_version()`; `layout_ok` is `om_abi_layout_check(sizeof rows)`; `features` lists the enabled `om_feature` ids.

### snapshot (server to client, on request and after `load`)
```json
{"type":"snapshot","tick":10,"checksum":1234567890,
 "regions":[{"i":0,"owner":-1,"tier":1,"military":12.5,"economy":30.0,"tension":8.0,"population":20.0,"stability":61.2,"capacity":44.0}],
 "factions":[{"id":0,"archetype":2,"budget":100.0,"tech":1.5,"stance":[3,1,2]}],
 "edges":[{"a":0,"b":1,"t":2}],
 "telegraphs":[{"attacker":0,"target":7,"commit":40.0,"declared_tick":8}]}
```
`regions[i]` is by index; `owner` is `om_region_owner` (-1 unowned); the six numbers are the four fields and two composites, post-clamp, two decimals. `checksum` (here and on every tenth `delta`) is `om_world_get_state_checksum`, a uint64 written as a JSON number: a client whose JSON parser rounds integers through a double (Godot's `JSON.parse` does) must read the digits off the wire, as `autoload/c_bridge.gd` does; sending it as a string is a v2 shape question. `set_seed` generates the world (`om_world_new` then `om_world_generate`; a pinned `n_regions` below the feasible minimum makes generation fail and `set_seed` answers `error` instead of a frame), so the snapshot below reflects the generated owners, edges and tiers; the fixture is produced the same way, through `scripts/specfactory/snapshot_fixture.py --generate`. `factions[].stance[k]` is `om_faction_stance(id, k)` for every faction k. `edges` is the full undirected edge list once (`a < b`). `telegraphs` is `om_pending_telegraphs`.

### delta (server to client, every tick after a `step` or during `run_to`)
```json
{"type":"delta","tick":11,"checksum":0,
 "regions":[{"i":3,"owner":0,"military":11.0,"economy":30.4,"tension":7.5,"population":20.1,"stability":62.0,"capacity":44.2}],
 "events":[{"tick":11,"region":3,"template":5,"chain":-1,"source":0,"delta":[0,-2.0,3.0,0],"creates_faction":0}],
 "attacks":[{"attacker":0,"target":7,"band":2,"conquest":1,"d_military":-13.6,"d_economy":-5.4,"d_tension":10.9,"collision":0}],
 "collisions":[{"target":7,"factions":[0,1],"winner":0,"margin":0.741,"refund":6.2}],
 "revolts":[{"region":9,"faction":1,"roll":0.02}],
 "factions":[{"id":0,"budget":60.0,"tech":1.5}]}
```
Only regions whose stored values changed appear; `checksum` is the world checksum on cadence ticks, else 0; the lists come from `om_tick_events`, `om_tick_attacks`, `om_tick_collisions`, `om_tick_admin_rolls` and are empty arrays when nothing fired. A client that misses a delta requests a snapshot.

### command (client to server)
```json
{"type":"cmd","name":"step","n":1}
{"type":"cmd","name":"run_to","tick":500}
{"type":"cmd","name":"snapshot"}
{"type":"cmd","name":"set_seed","seed":7,"n_regions":60,"features":[1,2,3,6]}
{"type":"cmd","name":"set_feature","feature":4,"on":true}
{"type":"cmd","name":"inject","bug":6}
{"type":"cmd","name":"save","path":"saves/slot1.omsave"}
{"type":"cmd","name":"load","path":"saves/slot1.omsave"}
{"type":"cmd","name":"quit"}
```
`set_seed` creates the world with `om_world_new(N, S)` (`N` = 0 means the count is drawn and lifted to the feasible minimum, Q-021-07; a pinned `N` below the feasible minimum makes generation fail), sets the listed features, then calls `om_world_generate(w)`. On success it is silent (no ack, no snapshot): `tests/transport/test_pipe_shapes.py` requires the first frame after `hello` to be the first `step` delta, so a client that wants the fresh world sends `snapshot`. If `om_world_generated(w)` is 0, the server answers `{"type":"error","name":"set_seed","reason":"generation failed"}` instead — the one case where `set_seed` emits a frame. Every other command is answered by `{"type":"ack","name":"...","tick":N}` or `{"type":"error","name":"...","reason":"..."}`; `run_to` streams deltas then one ack. `inject` exists only in the debug build (`error` otherwise). `save`/`load` use T2's `om_save_state_*`; `load` replies with the post-load `snapshot` or an `error` (see session commands).

### tactical snapshot (v1 tactical, once B10/B12 attach; sent on `snapshot` when a tactical map is loaded)
```json
{"type":"tactical","tick":120,"map":{"canvas":16000,"nodes":[{"i":0,"kind":0,"x":8000.0,"y":9200.0}],"cover":[{"x":1.0,"y":2.0,"r":120.0,"h":40.0}],"obstacles":[{"x":1.0,"y":2.0,"r":200.0}]},
 "units":[{"id":4,"faction":0,"type":1,"tier":2,"x":100.0,"y":200.0,"hp":80.0,"layer":1,"facing":1.57,"target":-1,"state":0}],
 "visible":{"0":[4,5,9]}}
```
Tactical positions are sim state (units move in the sim), so they are sent; strategic region positions are not. `visible[faction]` is `om_visibility_compute`'s set for that faction.

### chronicle frame, mission frame, debrief frame (on `snapshot` after a jump, mission start, mission end)
```json
{"type":"chronicle","jump":{"from_tick":100,"to_tick":150},"entries":[{"id":12,"start_tick":103,"end_tick":110,"category":3,"cluster_type":1,"refs":{"regions":[3,4],"factions":[0]},"fragment":417,"significance":0.8}]}
{"type":"mission","archetype":2,"region":7,"deadline_ticks":900,"objectives":[{"i":0,"kind":1,"node":3,"primary":true,"radius":300.0,"progress":0.0}],"force":{"types":[2,2,1,0,0,0],"tiers":[2,2,1,0,0,0]}}
{"type":"debrief","band":2,"achieved":0.8,"brought_home":0.6,"region_delta":{"military":-4.0,"economy":2.0,"tension":-3.0,"population":0.0}}
```
`fragment` is a library id; the client renders prose from `library/chronicle/fragments.json`. Objective `kind` and `node` are E-10/E-17 enums and node indices; names come from the client's layout pass.

### session commands (v1.1, 2026-09-24; T1-2 builds them test-first)
The frames above already say what a mission, a jump and a tactical stream look like; these are the commands that produce them. The pipe session is persistent: the client keeps the process open for the whole run and consumes `delta` frames as they stream (the one-shot set_seed/step/snapshot/quit script in `autoload/c_bridge.gd` is the v1 stopgap and goes with C2-4). The client requests the launch strategic feature set (`features` = every strategic `om_feature` id, defined once as `DEFAULT_FEATURES` beside `DEFAULT_N_REGIONS` in `c_bridge.gd`); with `[6]` alone nothing ever changes owner.
```json
{"type":"cmd","name":"mission_start","faction":0}
{"type":"cmd","name":"mission_end"}
{"type":"cmd","name":"jump","ticks":50}
{"type":"cmd","name":"tactical_step","n":1}
{"type":"cmd","name":"command","verb":"move","units":[4,5],"x":100.0,"y":200.0}
{"type":"cmd","name":"command","verb":"attack_move","units":[4],"x":100.0,"y":200.0}
{"type":"cmd","name":"command","verb":"attack_target","units":[4],"target":9}
{"type":"cmd","name":"command","verb":"hold","units":[4]}
{"type":"cmd","name":"list_saves","dir":"saves"}
```
`mission_start` calls `om_mission_start(w, faction)` and answers the `mission` frame (fields from `om_mission_get_objectives` and the force allocation; `archetype`, `region`, `deadline_ticks` from the mission accessors); while the mission phase holds, `step` and `run_to` are refused with `error` (R-055-02: the strategic sim is stopped) and `tactical_step` drives `om_tactical_step` and answers a `tactical` frame per call. `mission_end` calls `om_mission_end`, answers the `debrief` frame (`om_mission_get_debrief`) and then a `snapshot`. `jump` calls `om_time_jump_run(w, ticks, &report)`; a nonzero return (a mission is running) answers `error`; success answers the `chronicle` frame (`om_chronicle_entry_count` entries, retained only) and then a `snapshot`. `command` maps `verb` onto `om_command_move`, `om_command_attack_move`, `om_command_attack_target`, `om_command_hold` and answers `ack`; an unknown unit id or verb answers `error`. Every `error` carries `name` and `reason`, and the client surfaces it (`last_error()`), never a silent empty frame.

Save slots (T2g-2 rulings): `save` writes the state bytes to `path` and a sidecar `path + ".json"` with `{"tick","chapter","phase","seed","n_regions","format_version"}` so the client can list slots without parsing the binary; `list_saves` answers `{"type":"saves","slots":[{"path":"saves/slot1.omsave","tick":120,"chapter":2,"phase":0,"seed":1,"format_version":1}]}` from the sidecars in `dir`; the slot directory is the client's `user://saves` path passed absolute; `load` needs a world whose region count equals the save's (the client sends `set_seed` with the sidecar's `seed` and `n_regions` first; a fresh pipe process has a 1-region world and refuses); it answers `error` with `reason` `"version mismatch"` or `"corrupt"` (until save.c distinguishes them, T2c-3, the pipe says `corrupt` for both) when `om_load_state_read` returns nonzero (R-111-03) and the world is left untouched, else the post-load `snapshot`; autosave (R-111-01) is client-side, a `save` sent after the `mission` frame, after the `debrief` frame and after the `chronicle` frame, never mid-mission (R-111-04).

### persistent client session (v1.1, 2026-09-24; C2-4 builds it)
`autoload/c_bridge.gd` keeps one `pipe/ouroboros_pipe` process open for the whole run (`OS.execute_with_pipe`, Godot 4.6), instead of a script-up-front one-shot per scene. Reads block on Godot's pipe `FileAccess`, so the bridge owns one reader `Thread` that decodes frames (4-byte length prefix, JSON) and pushes them onto a mutex-guarded queue; the main thread drains the queue in `_process`, applies each frame in order, and emits `frame_received(frame)`. Writes happen on the main thread only. The bridge holds the current snapshot; a `delta` frame is applied to it in place (region rows by index, faction rows by id, `tick`, and `checksum` on cadence ticks, checked against the digits off the wire); `snapshot_changed(tick)` fires after every applied frame, and scenes redraw from the bridge's snapshot (galaxy recolours on owner change: R-106-02, plant `conquest-no-recolour`). `step n` and `run_to` therefore animate without a reload. A scene that needs a whole frame type (mission, chronicle, debrief, tactical, saves) awaits `frame_received` for that type after sending its command; `last_error()` is set from any `error` frame and the awaiting scene gets it instead of a frame. Ordering guarantee: the server answers commands strictly in the order sent, so the bridge keeps a FIFO of pending command names and matches replies to it. Scene tests inject a bridge as today (`qa_set_bridge`); the live tests drive the real one against the built pipe.

### Schemas and fixture
`docs/northstar/spec_factory/transport/{snapshot,delta,command}.schema.json` (JSON Schema, draft 2020-12, `additionalProperties: true`, required keys as above); `tests/transport/fixtures/snapshot_seed1_tick10.json` is produced through ctypes by `scripts/specfactory/snapshot_fixture.py --seed 1 --regions 80 --ticks 10 --generate` (80, not `set_seed`'s doc-example 60: 60 sits below `om_world_generate`'s feasibility floor for the default 15-faction generator on every seed, `csrc/worldgen.c`) and is the client pieces' stand-in until T1 attaches; `tests/transport/test_pipe_shapes.py` validates the fixture against the schema and, once `pipe/ouroboros_pipe` exists, drives it with a 10-step script and asserts the streamed checksum equals `om_world_get_state_checksum` through ctypes.

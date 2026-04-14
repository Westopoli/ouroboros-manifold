# Strategic Viewer — Build Plan

> **Type:** Debug tool, not a stage. Follows `dev_rules.md` (isolation, prove-before-integrate, thin interfaces, kill switch, STOP-after-each-step). Read this file plus `CLAUDE.md` before starting.
>
> **Status:** Complete. All 8 checkpoints done. Additional features added beyond original spec — see "Additions" section below.

## Goal

A pygame app that replays a recorded strategic-simulation run so Westley can watch regions and factions evolve over time and confirm with his own eyes that economic / military / tension / population / tech changes are happening the way the tests claim they are.

The viewer is for **debugging / sanity-checking the live engine**. It is not part of gameplay, not part of the chronicle pipeline, and not on any stage's critical path.

## Non-goals

- Not the tactical viewer. `simulation/sim_viewer.py` already exists for Stage 6 unit-level combat replay. Leave it alone.
- Not a live debugger. Record-then-replay only.
- Not a production UI. Pygame, local only, no browser export, no packaging.
- Not an editor. Read-only on the dump.

## Bible References

None required. This is a tooling buildout that reads existing engine state via public attributes and `to_dict()`. No design decisions live here.

## Context

The strategic engine (`tick.py` + `region.py` + `faction.py` + `world.py` + `events.py` + `border_friction.py` + `drift.py` + `technology.py` + `diplomacy.py`) is stable through Stage 5.5. Tests pass. `sim_tuner.py` already runs scenarios end-to-end and renders static matplotlib PNGs via `sim_graph.py`. The visual gap is interactive — Westley wants to scrub a tick at a time, click a region, and see what's happening.

The tactical viewer (`sim_viewer.py`) is the architectural reference: JSONL dump produced by `sim_logger.py`, replayed by a pygame app with scrubber, play/pause, pan, zoom, and click-to-pick. We mirror that pattern.

## What to Build

Three new files. No edits to engine files. No edits to `sim_tuner.py`, `sim_viewer.py`, or `sim_logger.py`.

### 1. `simulation/strategic_logger.py`

JSONL writer modeled on `sim_logger.py`. One header line, one line per tick.

Public API:
```python
class StrategicLogger:
    def __init__(self, path, scenario_name, world): ...
    def log_tick(self, tick, world, factions, events_this_tick, friction_by_edge): ...
    def close(self): ...
```

Header line shape:
```python
{
  "type": "header",
  "version": 1,
  "scenario": "04_four_way",
  "factions": {fid: {"name": str, "color": "#rrggbb"}},
  "regions": [{"id": str, "name": str, "tier": str, "layout": [x, y] | null}],
  "adjacency": [[a_id, b_id, edge_type], ...],
  "tick_count": null  # filled in on close()
}
```

Tick line shape:
```python
{
  "type": "tick",
  "tick": int,
  "regions": {rid: {"faction_id": str|null,
                    "fields": {"military":..., "economy":..., "tension":..., "population":...},
                    "composites": {"stability":..., "capacity":...}}},
  "factions": {fid: {"region_count": int,
                     "tech_level": float,
                     "budget": float,
                     "totals": {"military":..., "economy":..., "population":...},
                     "stances": {other_fid: "hostile"|"neutral"|"cooperative"}}},
  "events": [{"region_id": str, "type": str, "chain_tag": str|null}],
  "friction": {[a_id, b_id]: float}  # only edges with non-zero friction
}
```

Layout coords (Fork 2, option B): default `null`. Hand-authored coords come later as an opt-in upgrade — viewer must work without them via auto-layout.

Logger reads via existing public surface:
- `world.regions[rid].to_dict()` for region state
- `faction.tech_level`, `faction.budget`, `faction.id`, `faction.color`, `faction.name`, `faction.stances` (or whatever the live attr is — discover, don't guess)
- `border_friction` module's per-edge values
- Events fired this tick: caller passes them in (don't reach into `events.PendingQueue` internals)

If a piece of state isn't available via a public attr, **stop and ask**. Do not add accessors to engine files.

### 2. `simulation/run_strategic_viewer.py`

Separate entry point — does NOT modify `sim_tuner.py`.

```
python3 run_strategic_viewer.py [scenario_name] [--ticks N] [--seed S] [--no-launch]
```

Behavior:
1. Default scenario: `04_four_way` (or whichever is most informative — confirm with Westley before picking).
2. Build world + factions exactly the way `sim_tuner.py` does (import its scenario config; do not duplicate scenario definitions).
3. Run `tick.run_tick` for N ticks with a `StrategicLogger` attached.
4. Write dump to `simulation/viewer_dumps/{scenario}_{timestamp}.jsonl` (gitignore this dir).
5. Unless `--no-launch`, exec `strategic_viewer.py` on the dump.

Kill switch: this entry point is opt-in. Nothing in the live engine knows the logger or viewer exists.

### 3. `simulation/strategic_viewer.py`

Pygame app. Loads a JSONL dump and replays it.

Reuse patterns from `sim_viewer.py`:
- Scrubber, play/pause (Space), step (←/→), Home/End, speed [/]
- Mouse pan, scroll-wheel zoom, click-to-pick
- ESC to quit, R to reset camera, V to toggle radar overlay

New behavior:

**Map render** (per region):
- Position: `layout` from header if present, else NetworkX `spring_layout` computed once at load. Cache the result.
- Outline color: owning faction color (gray for unowned)
- Fill brightness: scales with `composites.stability`
- Radius: scales with `composites.capacity` (clamped min/max)
- Inner ring: red, thickness scales with `fields.tension`
- Pulse: brief flash on ticks where `events` includes this region
- Edges: drawn between adjacent regions; width and color modulated by `friction` value (thin gray = none; thick red = high)
- **Radar overlay** (toggle `V`): draws a 4-arm star polygon over each node, one arm per field (military/economy/tension/population), arm length proportional to field value. Lets you scan the map for field anomalies without clicking. Built in Checkpoint 5 alongside the other visual richness passes.

**Sidebar (right)**:
- Default: prompt "click a region or press F to track a faction"
- On region click: show region name, tier, owning faction, raw mil/eco/tension/pop (number + bar), composites stability/capacity (number + bar), owning faction's tech_level, and 60-tick sparklines for each field
- On faction track (F to enter, click faction color swatch or cycle with Tab): show faction totals, region count, tech_level sparkline, diplomatic stances, recent events

**Bottom event log**:
- Last ~10 events with tick number, region name, type / chain tag
- Click an event → scrubber jumps to that tick and camera centers on the affected region

**Controls strip** (top or bottom — pick one, match `sim_viewer.py` placement):
- Mirrors tactical viewer: tick N / total, play state, speed, key hints

Implementation discipline:
- One file. No splitting until it's >500 lines AND has clearly separable concerns.
- Pure functions for all rendering helpers (region color, sparkline draw, edge style). No render-state classes unless genuinely needed.
- Sparkline data computed lazily from the loaded ticks list, not pre-aggregated into a separate structure.

## Integration Points

None. The viewer is a closed loop: logger writes a file, viewer reads a file. The engine doesn't know either exists.

The only "integration" is that `run_strategic_viewer.py` constructs a world the same way `sim_tuner.py` does. We do this by importing `sim_tuner`'s scenario dict directly — not by duplicating it.

Kill switch: delete the three new files and `simulation/viewer_dumps/`. Nothing else changes.

## Build Order — Checkpoints

> **Every checkpoint is a STOP gate.** Run the test, show Westley the output, wait for approval, do not proceed.

### Checkpoint 1 — Logger writes a valid dump

1. Create `strategic_logger.py`.
2. Create a minimal version of `run_strategic_viewer.py` that runs `01_solo_drift` for 50 ticks and writes a dump (no `--launch`, no viewer yet).
3. Print: dump path, file size, first header line pretty-printed, last tick's region+faction state pretty-printed.

**STOP.** Westley reads the printed JSON and confirms the shape captures what he wants to see. If not, fix the logger before touching the viewer.

### Checkpoint 2 — Viewer loads the dump and renders the static graph

1. Create `strategic_viewer.py`. Load dump, lay out regions (auto-layout — no hand-authored coords yet), draw nodes colored by faction, draw adjacency edges, draw region names.
2. Wire the scrubber so dragging it changes the displayed tick.
3. NO sparklines, NO event log, NO sidebar, NO friction overlay yet.

**STOP.** Westley scrubs through a 50-tick `01_solo_drift` dump and confirms regions/factions/adjacency look right.

### Checkpoint 3 — Region click + raw values sidebar

1. Implement click-to-pick on regions.
2. Sidebar shows raw mil/eco/tension/pop, composites, owning faction, owning faction's tech.
3. Numbers + bars only — no sparklines yet.

**STOP.** Westley clicks a region, scrubs, watches the numbers change. Confirms field values match expectations vs. what `sim_tuner.py`'s PNG would show for the same scenario.

### Checkpoint 4 — Sparklines

1. Add 60-tick sparklines for each field on the selected region.

**STOP.** Westley confirms sparklines show the same trend as `sim_graph.py`'s line plots.

### Checkpoint 5 — Visual richness on the map

1. Stability → fill brightness, capacity → radius, tension → inner red ring, friction → edge width/color.
2. Run on `03_contested` and `04_four_way`.

**STOP.** Westley confirms he can see economic / tension / military / population changes "at a glance" without clicking.

### Checkpoint 6 — Event log + jump-to-event

1. Bottom event log (last ~10).
2. Click event → jump scrubber + center camera.
3. Pulse flash on regions with events this tick.

**STOP.** Westley confirms events are visible and navigable.

### Checkpoint 7 — Faction track mode

1. F toggles between region-focus and faction-focus sidebar.
2. Faction sidebar: totals, region count over time, tech_level sparkline, diplomacy snapshot.

**STOP.** Westley confirms faction-level view tells the story he wants.

### Checkpoint 8 — Hand-authored layout coords ✓

1. Added `TEMPLATE_LAYOUTS` dict to `strategic_logger.py` with hand-authored [x, y] coordinates for `s1_isolated`, `contested_border`, and `four_way` templates.
2. Logger passes template name through and embeds coords in the header's `regions[].layout` field.
3. Viewer's existing `compute_layout()` already handled the `if all(r.get("layout"))` branch — no viewer changes needed.

## Additions (beyond original spec)

These were built during the session after all 8 checkpoints passed.

### Faction territory overlay

A convex hull polygon is drawn behind edges and nodes for each faction, showing its territorial extent at the current tick:
- Semi-transparent fill (alpha 35) in the faction's color
- Bright border line (alpha 210) in the faction's color
- Single region → circle; two regions → rectangle; three or more → convex hull expanded outward from centroid
- Redrawn every tick as the scrubber moves
- Implemented as `draw_faction_territories()` in `strategic_viewer.py`, called first in `draw_map()` so nodes and edges render on top

### Revolt faction unique colors

Previously, every breakaway/revolt faction rendered gray (unknown archetype fallback) or shared the same `#cc88ff` purple. Fixed in two parts:

**Simulation-level:** `Faction.__init__` now accepts `avoid_colors: set | None`. When provided along with an `rng`, `_unique_revolt_color()` picks a random HSV hue with saturation=0.75 / value=0.90, retrying up to 30 times to find a hue with at least 29° of angular separation from every living faction's color. `tick.py` passes `avoid_colors={f.color for f in registry.values()}` at revolt creation time.

**Archetype completeness:** `warlord` (`#ff8c4a`) and `schism` (`#ff4adc`) were missing from `_ARCHETYPE_COLORS` in `faction.py` and fell back to gray. Both added.

### Transient revolt faction capture in logger

The original `close(registry=registry)` patch only captured factions alive at end-of-run. Factions that were born and absorbed mid-sim were missing from the header, causing "Unclaimed" in the viewer for those ticks. Fixed by initializing `self._all_factions` in `StrategicLogger.__init__` and accumulating new entries in every `log_tick()` call. `close()` now patches the header from this running set instead of the final registry state.

## Done Condition ✓

Verified on `07_full_game_50` at 1000 ticks. All systems confirmed working: scrubber, click-to-pick, sparklines, event log jump, faction track mode, territory overlay, revolt faction colors, transient faction capture.

## Files Created

Filled in after implementation.

- [x] `simulation/strategic_logger.py`
- [x] `simulation/run_strategic_viewer.py`
- [x] `simulation/strategic_viewer.py`
- [x] `simulation/viewer_dumps/` added to root `.gitignore`

## Rules Recap (Don't Skip)

- **No edits to protected engine files** (`tick.py`, `drift.py`, `faction.py`, `region.py`, `events.py`, `event_engine.py`, `intent_resolver.py`, `border_friction.py`, `technology.py`, `diplomacy.py`, `world.py`, `templates.py`, `theme_scifi.py`). If the logger needs state that isn't exposed publicly, STOP and ask Westley how to expose it — do not add accessors yourself.
- **No edits to `sim_tuner.py` or the tactical `sim_viewer.py`** without explicit permission. The viewer is additive.
- **No new dependencies** beyond pygame (already used) and NetworkX (only if auto-layout is needed — confirm with Westley before adding to requirements).
- **No dead code, no docstrings except on public functions, no header comment blocks.** See `CLAUDE.md` "No stink".
- **STOP after each checkpoint.** Show output. Wait. Do not self-verify and proceed.
- **One fix at a time** when debugging. No shotgun fixes.
- **If a checkpoint feels like it needs >200 lines or touches >2 files, break it down and confirm first.**
- **Update this file** as checkpoints land. Tick the boxes in "Files Created". If a design decision changes mid-build, update the spec before changing the code.

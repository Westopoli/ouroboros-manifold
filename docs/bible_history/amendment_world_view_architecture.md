# Amendment — World View Architecture Refactor

> **Type:** Cross-cutting architectural amendment
> **Affects:** Stage 9 (rename only — already implemented), Stage 10 (no changes needed), Stage 11 (spec rewrite for world view sections), Stage 12 (ribbon graph galaxy reference update)
> **Priority:** Must be completed before Stage 11 implementation begins.
> **Status:** COMPLETED (2026-04-16)
>
> **Implementation variations:**
> - `loading_screen.gd` was updated alongside `main_menu.gd` (not listed in the amendment but required — it also loaded `galaxy_structure.tscn`).
> - `mission_briefing.gd:573` retains the user-facing hint text "ESC to return to galaxy view" — this is era-specific display text, not implementation code. Deferred to a future era-agnosticism pass.
> - Part 4 (stage spec amendments to Stage 11/12 docs) was not performed in this pass — those docs still reference the old paths and will be updated when those stages are worked on.
> - Shader migration to `shaders/` subdirectory was not performed (amendment explicitly marked this as out of scope for this pass).

---

## Problem Statement

Two issues were identified during an era-agnosticism audit of Stages 9–12:

1. **Terminology.** The world view scene uses sci-fi vocabulary (`galaxy_structure`, `system_node`, `highlight_system`) in implementation-facing code. The bible's Sacred Design Principle #3 requires abstract vocabulary in all engine and implementation code. A Roman era's world view is not a galaxy — it's a map of provinces. These names must be era-neutral before Stage 11 builds on top of them.

2. **Era-locked renderer.** The current `galaxy_structure.gd` hardcodes a 3D particle galaxy (rings, streams, dust, starfield) in its `_ready()` function. The world view between missions must support fundamentally different visual paradigms per era — 3D particle galaxy (Settled Reach), 2D top-down auto-generated landmass map (Roman), 3D globe with satellite rendering (1980s), underwater environments (future eras). These are not skin swaps; they require different rendering strategies, different camera types, and different node hierarchies. With 20+ planned eras, the architecture must support swappable renderers without touching the sequencer or data bus.

The main menu galaxy is unaffected. It is a fixed brand asset that always displays the particle galaxy regardless of the active era. It continues to instance its own standalone scene directly.

---

## Solution: Component Composition Architecture

The world view is split into four parts:

1. **WorldViewShell** — the orchestrator. The `time_jump_sequencer` talks to this and only this. It owns the data component, instances the per-era renderer and camera, and delegates all calls.
2. **WorldViewData** — shared across all eras. Pure data store (regions, connections, territories, highlights). Emits signals on every mutation. No visuals.
3. **WorldViewRenderer** — per-era, swappable. Connects to WorldViewData signals and translates data changes into era-appropriate visuals. Does not own a camera.
4. **WorldViewCamera** — per-era, swappable. Handles all camera motion (ambient orbit, move-to-region, overview pullback). Multiple eras can share a camera type (e.g., several top-down-map eras sharing a `PanCamera2D`).

**Signal-based propagation.** The data component emits signals on state changes. The renderer listens. The shell just writes to the data component — no manual routing required. This also allows future components (audio atmosphere, accessibility overlays) to listen to the same signals without touching the shell.

**Era config lookup.** The shell reads a config resource that maps era IDs to renderer and camera scene paths:

```
"settled_reach": {
    "renderer": "res://scenes/world_view/renderers/settled_reach_renderer.tscn",
    "camera": "res://scenes/world_view/cameras/orbital_camera_3d.tscn"
}
"roman": {
    "renderer": "res://scenes/world_view/renderers/roman_renderer.tscn",
    "camera": "res://scenes/world_view/cameras/pan_camera_2d.tscn"
}
"1980s": {
    "renderer": "res://scenes/world_view/renderers/globe_renderer.tscn",
    "camera": "res://scenes/world_view/cameras/orbital_camera_3d.tscn"
}
```

---

## Part 1 — Terminology Rename

### Directory rename

`scenes/shared/galaxy/` → `scenes/shared/world_view/`

All files in the directory move with it. The four particle shaders (`ring_particles.gdshader`, `stream_particles.gdshader`, `dust_particles.gdshader`, `starfield_particles.gdshader`) keep their names — they are specific to the Settled Reach renderer and will eventually move to the renderer subdirectory, but for now they stay at `scenes/shared/world_view/` to avoid breaking the main menu's standalone galaxy scene which also loads them.

### File renames

| Old path | New path |
|----------|----------|
| `scenes/shared/galaxy/galaxy_structure.gd` | `scenes/shared/world_view/world_view_structure.gd` |
| `scenes/shared/galaxy/galaxy_structure.tscn` | `scenes/shared/world_view/world_view_structure.tscn` |

### Reference updates in `world_view_structure.gd` (formerly `galaxy_structure.gd`)

Stubbed world-view API methods — rename only, signatures otherwise unchanged:

| Old method | New method |
|-----------|------------|
| `add_system_node(node_id, pos, size, color)` | `add_region_node(node_id, pos, size, color)` |
| `remove_system_node(node_id)` | `remove_region_node(node_id)` |
| `update_system_node(node_id, size, color)` | `update_region_node(node_id, size, color)` |
| `clear_system_nodes()` | `clear_region_nodes()` |
| `highlight_system(node_id)` | `highlight_region(node_id)` |

Shader load paths — update all four:

| Old | New |
|-----|-----|
| `res://scenes/shared/galaxy/ring_particles.gdshader` | `res://scenes/shared/world_view/ring_particles.gdshader` |
| `res://scenes/shared/galaxy/stream_particles.gdshader` | `res://scenes/shared/world_view/stream_particles.gdshader` |
| `res://scenes/shared/galaxy/dust_particles.gdshader` | `res://scenes/shared/world_view/dust_particles.gdshader` |
| `res://scenes/shared/galaxy/starfield_particles.gdshader` | `res://scenes/shared/world_view/starfield_particles.gdshader` |

### Reference updates in `world_view_structure.tscn` (formerly `galaxy_structure.tscn`)

| Field | Old | New |
|-------|-----|-----|
| Script path | `res://scenes/shared/galaxy/galaxy_structure.gd` | `res://scenes/shared/world_view/world_view_structure.gd` |
| Root node name | `GalaxyStructure` | `WorldViewStructure` |

### Reference updates in `main_menu.gd`

| Old | New |
|-----|-----|
| `var _galaxy: Node` | `var _world_view: Node` |
| `_setup_galaxy_viewport()` | `_setup_world_view_viewport()` |
| `func _setup_galaxy_viewport()` | `func _setup_world_view_viewport()` |
| `load("res://scenes/shared/galaxy/galaxy_structure.tscn")` | `load("res://scenes/shared/world_view/world_view_structure.tscn")` |
| `var galaxy_scene` | `var world_view_scene` |
| `var galaxy: Node3D = galaxy_scene.instantiate()` | `var world_view: Node3D = world_view_scene.instantiate()` |
| `viewport.add_child(galaxy)` | `viewport.add_child(world_view)` |
| `galaxy.start_auto_camera()` | `world_view.start_auto_camera()` |
| `_galaxy = galaxy` | `_world_view = world_view` |
| `if _galaxy and _galaxy.has_signal(...)` | `if _world_view and _world_view.has_signal(...)` |
| `_galaxy.structure_revealed.connect(...)` | `_world_view.structure_revealed.connect(...)` |

### Files confirmed clean (no changes needed)

- `autoload/ui_data_bus.gd` — zero galaxy/system references.

### Verification (Part 1)

1. Launch game. Main menu renders identically — particle galaxy visible, camera moods cycle, title heartbeat fires on structure reveal.
2. `grep -r "galaxy" scenes/` returns zero hits outside of comments.
3. `grep -r "system_node\|highlight_system" scenes/` returns zero hits outside of comments.

---

## Part 2 — Component Architecture

### New file tree

```
scenes/shared/world_view/
├── world_view_shell.tscn + .gd           ← Orchestrator. Sequencer talks to this.
├── world_view_data.gd                    ← Shared data component. All eras.
├── world_view_structure.tscn + .gd       ← Main menu standalone galaxy (Part 1 rename).
│                                            NOT used by the shell. Main menu instances
│                                            this directly. Untouched by Part 2.
├── renderers/
│   └── settled_reach_renderer.tscn + .gd ← First era renderer. Visual code migrated
│                                            from world_view_structure.gd's _build_*
│                                            methods, plus world-view signal handlers.
├── cameras/
│   └── orbital_camera_3d.tscn + .gd      ← First camera component. Camera mood system
│                                            migrated from world_view_structure.gd.
├── era_world_view_config.tres             ← Resource mapping era IDs to renderer + camera.
└── shaders/
    ├── ring_particles.gdshader            ← Moved from parent dir. Update load paths in
    ├── stream_particles.gdshader             world_view_structure.gd (main menu) and
    ├── dust_particles.gdshader               settled_reach_renderer.gd.
    └── starfield_particles.gdshader
```

### WorldViewData — shared data component

**File:** `scenes/shared/world_view/world_view_data.gd`
**Extends:** `Node`

Pure data store. No visuals. One implementation shared across all eras. The shell creates this as a child node.

#### Stored state

```gdscript
var regions: Dictionary = {}
# Key: String (region_id)
# Value: {position: Vector3, size: float, color: Color, faction_id: String}

var connections: Dictionary = {}
# Key: String ("from_id::to_id", canonically ordered so from_id < to_id)
# Value: {from_id: String, to_id: String, connection_type: String, color: Color}

var territories: Dictionary = {}
# Key: String (region_id)
# Value: {center: Vector3, radius: float, color: Color}

var highlight_id: String = ""
```

#### Signals

```gdscript
signal region_added(region_id: String)
signal region_updated(region_id: String)
signal region_removed(region_id: String)
signal regions_cleared()

signal territory_set(region_id: String)
signal territory_updated(region_id: String)
signal territory_removed(region_id: String)

signal connection_added(from_id: String, to_id: String)
signal connection_removed(from_id: String, to_id: String)

signal flash_region_requested(region_id: String, intensity: float)
signal flash_conflict_requested(from_id: String, to_id: String, intensity: float)

signal highlight_changed(region_id: String)
```

#### Public methods

```gdscript
func add_region(id: String, position: Vector3, size: float, color: Color, faction_id: String) -> void
func update_region(id: String, size: float, color: Color) -> void
func remove_region(id: String) -> void
func clear_regions() -> void

func set_territory(region_id: String, center: Vector3, radius: float, color: Color) -> void
func update_territory(region_id: String, radius: float, color: Color) -> void
func remove_territory(region_id: String) -> void

func add_connection(from_id: String, to_id: String, connection_type: String, color: Color) -> void
func remove_connection(from_id: String, to_id: String) -> void

func request_flash_region(region_id: String, intensity: float) -> void
func request_flash_conflict(from_id: String, to_id: String, intensity: float) -> void

func set_highlight(region_id: String) -> void  # Empty string to clear.

func get_region(id: String) -> Dictionary
func get_all_regions() -> Dictionary
func get_connection(from_id: String, to_id: String) -> Dictionary
func get_territory(region_id: String) -> Dictionary
```

Each mutating method updates the stored state, then emits the corresponding signal. Flash methods emit their signal immediately with no stored state (flashes are one-shot visual events). `set_highlight` updates `highlight_id` and emits `highlight_changed`.

---

### WorldViewRenderer — per-era interface

**File:** Each era provides its own script extending this interface.
**Extends:** `Node`

The renderer connects to `WorldViewData` signals during `setup()` and translates state changes into visuals. It adds its visual nodes as children of the container node it receives. It reads data from the `WorldViewData` reference to get positions, colors, and sizes — the signal says *what* changed, the data says *to what*.

#### Required interface

```gdscript
# Called once by the shell after instancing. The renderer connects to data
# signals here and adds its visual nodes as children of container.
func setup(data: WorldViewData, container: Node) -> void

# Disconnect signals, free visual nodes. Called on era switch or cleanup.
func teardown() -> void

# Returns the 2D bounding box of the rendered world. For 3D renderers,
# this is the XZ-plane projection. Used by the camera for framing.
func get_world_bounds() -> Rect2

# Translates a region ID to a world-space position the camera can target.
func region_id_to_world_position(region_id: String) -> Vector3
```

#### Signal handlers the renderer must connect during `setup()`

The renderer connects to these WorldViewData signals and provides handler methods. Naming convention is `_on_<signal_name>` but not enforced — the renderer connects however it chooses. What matters is that every signal has a handler.

| WorldViewData signal | Purpose |
|----------------------|---------|
| `region_added(region_id)` | Create visual representation of a new region. |
| `region_updated(region_id)` | Update size/color of existing region visual. |
| `region_removed(region_id)` | Remove region visual. |
| `regions_cleared()` | Remove all region visuals. |
| `territory_set(region_id)` | Create territory visual (bubble, border, shaded area). |
| `territory_updated(region_id)` | Update territory extent/color. |
| `territory_removed(region_id)` | Remove territory visual. |
| `connection_added(from_id, to_id)` | Draw connection line/arc between regions. |
| `connection_removed(from_id, to_id)` | Remove connection visual. |
| `flash_region_requested(region_id, intensity)` | Play a one-shot flash effect at the region. |
| `flash_conflict_requested(from_id, to_id, intensity)` | Play a one-shot flash between two regions. |
| `highlight_changed(region_id)` | Apply or clear the pulsing highlight on a region. Empty string = clear. |

The renderer reads the data component (passed in `setup()`) to get the actual values. Example: on `region_added("r_042")`, the handler calls `data.get_region("r_042")` to get position, size, color, faction_id, then creates the visual node.

---

### WorldViewCamera — per-era interface

**File:** Each camera type provides its own script.
**Extends:** `Node`

The camera is instanced as a child of the shell. It creates and owns the actual Godot Camera2D or Camera3D node inside the viewport it receives. It has a reference to the renderer for world-bounds and position lookups.

#### Required interface

```gdscript
# Called once by the shell. The camera creates its Godot camera node inside
# the viewport and stores the renderer reference for bounds/position queries.
func setup(renderer: WorldViewRenderer, viewport: SubViewport) -> void

# Free camera nodes, disconnect anything.
func teardown() -> void

# Animate the camera to frame the given region.
# Calls renderer.region_id_to_world_position() internally.
# Emits camera_move_completed when the animation finishes.
func move_to_region(region_id: String, duration: float) -> void

# Pull the camera back to frame the entire world.
# Calls renderer.get_world_bounds() for framing.
# Emits camera_move_completed when done.
func move_to_overview(duration: float) -> void

# Begin era-appropriate idle animation (slow orbit, gentle pan, etc.).
func start_ambient_motion() -> void

# Stop idle animation, hold current position.
func stop_ambient_motion() -> void

func get_current_position() -> Vector3
func get_current_target() -> Vector3
```

#### Signals

```gdscript
signal camera_move_completed()
signal ambient_motion_started()
```

#### Expected camera implementations (initial)

**`orbital_camera_3d.gd`** — Used by Settled Reach, 1980s, and any 3D-rendered era. Migrates the camera mood system (WIDE_ORBIT, RING_FOLLOW, APPROACH, DRIFT, PULLBACK, UNDERSIDE) from the current `world_view_structure.gd`. The mood system drives `start_ambient_motion()`. `move_to_region()` stops ambient motion, tweens to the target position, emits `camera_move_completed`. `move_to_overview()` tweens to a wide framing position derived from `get_world_bounds()`.

**`pan_camera_2d.gd`** — Used by Roman and other flat-map eras. Implements pan/zoom over a 2D world. `start_ambient_motion()` does a slow drift across the map. `move_to_region()` pans and zooms to center the target region. `move_to_overview()` zooms out to fit the full map.

These are authored when their first era is implemented. `orbital_camera_3d.gd` is authored in this amendment (needed for Settled Reach in Stage 11). `pan_camera_2d.gd` is authored when the Roman era world view is built.

---

### WorldViewShell — the orchestrator

**File:** `scenes/shared/world_view/world_view_shell.tscn + .gd`
**Extends:** `Node`

The shell is what the `time_jump_sequencer` talks to. It owns the `WorldViewData` instance, instances the per-era renderer and camera from config, and delegates all calls. Its public API is what Stage 11's sequencer calls.

#### Setup flow

```
shell.setup_era(era_id)
  → reads era_world_view_config.tres for era_id
  → creates WorldViewData as child node
  → instances renderer scene, calls renderer.setup(data, visual_container)
  → instances camera scene, calls camera.setup(renderer, viewport)
```

#### Public API

```gdscript
# --- Lifecycle ---
func setup_era(era_id: String) -> void
func cleanup() -> void  # Tears down renderer and camera, clears data.

# --- Region data (delegates to WorldViewData) ---
func add_region_node(id: String, position: Vector3, size: float, color: Color, faction_id: String) -> void
func remove_region_node(id: String) -> void
func update_region_node(id: String, size: float, color: Color) -> void
func clear_region_nodes() -> void

# --- Territory (delegates to WorldViewData) ---
func set_territory(region_id: String, center: Vector3, radius: float, color: Color) -> void
func update_territory(region_id: String, radius: float, color: Color) -> void
func remove_territory(region_id: String) -> void

# --- Connections (delegates to WorldViewData) ---
func add_connection(from_id: String, to_id: String, connection_type: String, color: Color) -> void
func remove_connection(from_id: String, to_id: String) -> void

# --- Flashes (delegates to WorldViewData) ---
func flash_military_activity(region_id: String, intensity: float) -> void
func flash_conflict(from_id: String, to_id: String, intensity: float) -> void

# --- Highlight (delegates to WorldViewData) ---
func highlight_region(region_id: String) -> void
func clear_highlight() -> void

# --- Camera (delegates to WorldViewCamera) ---
func move_camera_to_region(region_id: String, duration: float) -> void
func move_camera_to_overview(duration: float) -> void
func start_auto_camera() -> void
func stop_auto_camera() -> void
func get_camera_position() -> Vector3
func get_camera_target() -> Vector3

# --- Display (handled by shell directly) ---
func set_opacity(alpha: float) -> void  # Sets modulate on viewport container.
```

#### Signals (re-emitted from camera)

```gdscript
signal camera_move_completed()
```

The shell connects to the camera's `camera_move_completed` signal and re-emits it so the sequencer doesn't need to know about the camera component.

#### Era config resource

**File:** `scenes/shared/world_view/era_world_view_config.tres`

A Godot Resource containing a dictionary mapping era IDs to renderer and camera scene paths. The shell loads this resource and looks up the era ID passed to `setup_era()`.

```gdscript
# era_world_view_config.gd (custom Resource script)
extends Resource
class_name EraWorldViewConfig

@export var era_configs: Dictionary = {
    "settled_reach": {
        "renderer": "res://scenes/world_view/renderers/settled_reach_renderer.tscn",
        "camera": "res://scenes/world_view/cameras/orbital_camera_3d.tscn"
    },
    "roman": {
        "renderer": "res://scenes/world_view/renderers/roman_renderer.tscn",
        "camera": "res://scenes/world_view/cameras/pan_camera_2d.tscn"
    },
    "1980s": {
        "renderer": "res://scenes/world_view/renderers/globe_renderer.tscn",
        "camera": "res://scenes/world_view/cameras/orbital_camera_3d.tscn"
    }
}

func get_renderer_path(era_id: String) -> String:
    if era_id in era_configs:
        return era_configs[era_id]["renderer"]
    push_error("No world view config for era: " + era_id)
    return ""

func get_camera_path(era_id: String) -> String:
    if era_id in era_configs:
        return era_configs[era_id]["camera"]
    push_error("No world view config for era: " + era_id)
    return ""
```

Initially only the `settled_reach` entry has real scene paths. Other entries are added when their eras are built.

---

## Part 3 — Migration of Existing Code

The current `world_view_structure.gd` contains two things mixed together:

1. **The main menu particle galaxy** — all the `_build_*()` methods, camera mood system, `_ready()`.
2. **Stubbed world-view API** — the `add_region_node()`, `set_territory()`, etc. stubs at the bottom.

After this amendment:

- **`world_view_structure.gd` keeps the main menu particle galaxy code intact.** The `_build_*()` methods, camera mood system, central pulse, stream rotation — all of it stays. The main menu continues to instance this scene directly. The stubbed world-view API methods are removed from this file (they now live on the shell).

- **`settled_reach_renderer.gd` receives the visual building code** needed for the Settled Reach *world view* (not the main menu). This is NOT a copy of the main menu galaxy — the world view renderer for Settled Reach builds a simpler visualization optimized for displaying region data, territory bubbles, and connections. The main menu galaxy is a decorative brand asset with 12 tilted rings and radial streams; the world view renderer is a functional data display. Stage 11 authors the Settled Reach renderer's visual content from scratch, guided by the bible's galaxy view spec.

- **`orbital_camera_3d.gd` receives a camera system.** For the world view, the camera needs `move_to_region`, `move_to_overview`, and `start_ambient_motion` — which is a simpler system than the main menu's 6-mood camera. The main menu keeps its own camera code. The orbital camera component is authored fresh for the world view use case.

**Key point:** The main menu galaxy and the world view are NOT the same scene. The main menu galaxy is a cinematic brand piece. The world view is a functional data visualization. They happen to both involve particles in 3D space for the Settled Reach era, but they serve different purposes and have different requirements. The main menu doesn't need region nodes, territory, or connections. The world view doesn't need 12 tilted rings and radial streams. Trying to share the scene between them would compromise both.

---

## Part 4 — Stage Spec Amendments

### Stage 11 spec changes

The following sections of `stage_11_spec.md` must be updated:

1. **All references to `galaxy_structure`** → `world_view_shell` (for the sequencer's interface) or `world_view_structure` (for the main menu only).

2. **File tree** — replace `scenes/shared/galaxy/` entries with the new `scenes/shared/world_view/` tree from this amendment.

3. **"Galaxy structure public API" section** — replace with a reference to this amendment's shell API. Method names use `region_node` not `system_node`. The sequencer calls `shell.setup_era(era_id)` before any data methods.

4. **"Galaxy scene architecture" section** — rewrite to describe the shell + component architecture. The main menu and the world view are no longer the same scene. The main menu instances `world_view_structure.tscn` directly. The sequencer instances `world_view_shell.tscn` and calls `setup_era()`.

5. **Checkpoint C** — retitled from "Galaxy structure world-view API fill-in" to "World view shell and Settled Reach renderer." The checkpoint now covers: instantiating the shell, setting up the Settled Reach renderer via config, and proving that the renderer responds to data signals by adding mock regions/connections/territory and visually displaying the result.

6. **Config section** — rename all `GALAXY_*` config keys to `WORLD_VIEW_*`.

7. **Walkthrough** — replace "galaxy view" with "world view" throughout. Replace "the Settled Reach rendered: system nodes visible" with "the Settled Reach world view rendered: region nodes visible."

### Stage 12 spec changes

1. **Ribbon graph section** — the reference to "reusing galaxy camera infrastructure from `scenes/shared/galaxy/galaxy_structure.tscn`" updates to reference `scenes/shared/world_view/cameras/orbital_camera_3d.tscn`.

2. **Sequencer modification note** — the `time_jump_sequencer.gd` modification description should reference `world_view_shell` not `galaxy_structure`.

---

## Checkpoints

### Checkpoint A — Terminology rename

Rename directory, files, and all references per Part 1.

**Verify:**
1. Game launches. Main menu renders identically.
2. `grep -rn "galaxy" scenes/` returns zero hits outside of comments and the `world_view_structure.gd` internal variable names (which are private implementation details of the main menu scene and acceptable).
3. `grep -rn "system_node\|highlight_system" scenes/` returns zero hits.

### Checkpoint B — WorldViewData component

Create `world_view_data.gd` per the spec above.

**Verify:** A test script creates a WorldViewData instance, connects to all signals, calls every mutating method, and asserts that the correct signal fired with the correct arguments, and that the stored state matches. Pure unit test, no visuals.

### Checkpoint C — WorldViewShell, config resource, and wiring

Create `world_view_shell.tscn + .gd`, `era_world_view_config.gd + .tres`. The shell instances WorldViewData, reads config, and delegates. For this checkpoint, the Settled Reach renderer and camera entries in the config can point to placeholder scenes that implement the interface with no-op visuals (just print statements confirming signal receipt).

**Verify:** A test harness instances the shell, calls `setup_era("settled_reach")`, then calls shell methods (`add_region_node`, `set_territory`, `flash_military_activity`, `highlight_region`, `move_camera_to_region`). Console output from the placeholder renderer/camera confirms each signal was received and each delegation worked. No visual output required.

### Checkpoint D — Settled Reach renderer and orbital camera

Author `settled_reach_renderer.gd` and `orbital_camera_3d.gd` as real implementations. The renderer builds the Settled Reach world view visualization (region nodes, territory bubbles with contoured borders, connections, military flashes). The camera provides orbital motion with `move_to_region`, `move_to_overview`, and `start_ambient_motion`.

**Verify:** The same test harness from Checkpoint C, but now with real visuals. Add 3 factions with territories, draw connections, fire flashes, move camera to a region, pull back to overview, start ambient motion. Westley reviews by running the harness and eyeballing.

**Note:** Checkpoint D overlaps with Stage 11 Checkpoint C's scope. If this amendment is implemented as a precursor to Stage 11, Checkpoints B–D here replace Stage 11 Checkpoint C. If Stage 11 is already in progress, coordinate to avoid duplicate work.

### Checkpoint E — Main menu still works

After all changes, the main menu still renders its particle galaxy identically to before the amendment. The main menu instances `world_view_structure.tscn` directly and never touches the shell.

**Verify:** Visual comparison. Launch game, observe main menu for 60 seconds. Camera moods cycle, title heartbeat fires, particle galaxy renders at 0.7 opacity. No regressions.

---

## What This Amendment Does NOT Cover

- **Roman era renderer** — authored when Roman era world view is built.
- **Pan camera 2D** — authored when the first flat-map era is built.
- **Globe renderer / 1980s** — authored when that era's world view is built.
- **Shader migration** — the particle shaders currently sit in `scenes/shared/world_view/`. When the Settled Reach renderer is built (Checkpoint D), they can be moved to `scenes/shared/world_view/shaders/` and load paths updated in both `world_view_structure.gd` (main menu) and `settled_reach_renderer.gd`. This is a minor file-move task, not a design decision.
- **Stage 9 celebration scripts** — flagged as tech debt (per-era hardcoded files rather than data-driven). Not addressed here; lower priority.
- **Stage 9 ThemeConstants era accent colors** — flagged as tech debt (hardcoded in code rather than config resource). Not addressed here; lower priority.

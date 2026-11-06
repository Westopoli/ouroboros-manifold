# Stage 11 C3/C4 — Territory Visualization Redesign

> **CC implementation spec.** This replaces the original C3 (territory bubbles) and C4 (border contour) sub-checkpoints from `stage_11_spec_amended.md`. Read this document as the authoritative spec for territory visualization. The original C3/C4 descriptions in the stage spec are superseded.

---

## What Changed and Why

The original C3/C4 built spherical influence bubbles + gold convex-hull border contours. Both failed visually: bubbles were too opaque (obscured the galaxy particles), hull borders were angular wireframe lines that clashed with the organic galaxy, and convex hulls claimed empty space between scattered systems. Both are replaced by a single **projected Voronoi influence field** rendered on the galactic plane.

Reference visual: see the uploaded screenshot showing organic rounded territory shapes with translucent fills, luminous faction-colored border outlines, and unclaimed space left empty. That is the target.

---

## Architecture Overview

A **SubViewport** renders a 2D territory texture. A **MeshInstance3D** quad on the galactic plane displays that texture in the 3D scene. The shader computes per-pixel Voronoi cell ownership, outputs faction-colored translucent fill, and draws soft luminous borders where different-faction cells meet.

```
WorldViewData signals
        │
        ▼
SettledReachRenderer
   ├── _rebuild_territory_data()     ← rebuilds 1D data textures from current territory state
   ├── SubViewport (territory_viewport)
   │     └── ColorRect + territory_voronoi.gdshader   ← computes Voronoi field
   └── MeshInstance3D (territory_plane)
         └── StandardMaterial3D (albedo = ViewportTexture from territory_viewport)
```

---

## Files

### New files

```
scenes/shared/world_view/renderers/
├── territory_voronoi.gdshader      - Canvas-item shader: Voronoi field computation
└── territory_plane_material.tres   - Material for the galactic plane quad (optional; can be created in code)
```

### Deleted files

```
scenes/shared/world_view/renderers/
└── territory_bubbles.gdshader      - DELETED (replaced by territory_voronoi.gdshader)

scenes/world/
└── territory_contour.gdshader      - DELETED (borders emerge from Voronoi field; no separate contour pass)
```

### Modified files

```
scenes/shared/world_view/renderers/
└── settled_reach_renderer.gd       - Territory signal handlers rewritten for Voronoi system.
                                       Remove all bubble/contour code. Add SubViewport + plane setup,
                                       data texture management, transition animation.

config/
└── world_view_config.py            - Replace bubble/contour tuning values with Voronoi tuning values.
```

---

## Shader Spec: `territory_voronoi.gdshader`

**Type:** `canvas_item` (runs on the ColorRect inside the SubViewport).

### Uniforms

```glsl
uniform sampler2D system_data;        // 1D data texture (MAX_SYSTEMS x 1)
                                       // R = x position (normalized 0–1 within map bounds)
                                       // G = z position (normalized 0–1 within map bounds)
                                       // B = faction index (0.0 = unowned, 1/8..8/8 = factions 1–8)
                                       // A = significance (0–1, scales influence radius)

uniform sampler2D faction_colors;     // 1D data texture (8 x 1)
                                       // RGB = faction color

uniform int system_count;             // number of active systems (read this many pixels from system_data)

uniform float fill_opacity;           // max opacity of territory fill interior (start: 0.12)
uniform float fill_falloff;           // distance (in UV space) beyond which fill fades to 0 (start: 0.15)
uniform float border_width;           // UV-space width of the faction-boundary glow band (start: 0.012)
uniform float border_brightness;      // brightness multiplier for border glow (start: 1.4)
uniform float edge_softness;          // smoothstep width at territory outer edge (start: 0.03)
```

### Fragment Logic (pseudocode)

```
for each fragment at UV:

    nearest_dist = INF
    nearest_faction = 0.0
    second_dist = INF
    second_faction = 0.0

    for i in 0..system_count-1:
        sample system_data at (i / MAX_SYSTEMS, 0.5)
        sys_pos = vec2(R, G)
        sys_faction = B
        sys_significance = A

        dist = distance(UV, sys_pos)

        if dist < nearest_dist:
            second_dist = nearest_dist
            second_faction = nearest_faction
            nearest_dist = dist
            nearest_faction = sys_faction
        elif dist < second_dist:
            second_dist = dist
            second_faction = sys_faction

    // Skip unowned cells
    if nearest_faction == 0.0:
        output transparent
        return

    // Look up faction color
    faction_idx = round(nearest_faction * 8.0) - 1
    color = sample faction_colors at (faction_idx / 8.0, 0.5)

    // Territory fill with edge falloff
    // fill_falloff is scaled per-system by significance (larger systems claim more space)
    effective_falloff = fill_falloff * (0.5 + nearest_significance * 0.5)
    alpha = fill_opacity * (1.0 - smoothstep(effective_falloff - edge_softness, effective_falloff, nearest_dist))

    // Faction border detection
    // Where two different factions' cells meet, draw a luminous edge
    if nearest_faction != second_faction AND second_faction != 0.0:
        border_factor = second_dist - nearest_dist
        if border_factor < border_width:
            border_intensity = (1.0 - border_factor / border_width)
            border_intensity = border_intensity * border_intensity  // quadratic falloff for soft glow
            // Boost alpha and brighten color at border
            alpha = max(alpha, border_intensity * 0.6)
            color = mix(color, color * border_brightness, border_intensity)

    // Same-faction internal Voronoi edges: suppress. Do NOT draw lines between
    // systems of the same faction. The fill is continuous across same-faction territory.

    output vec4(color.rgb, alpha)
```

### Performance Note

At 30 systems and 512×512 SubViewport: 30 iterations × 262K pixels = ~7.8M distance ops. Trivially under 1ms on any GPU made this decade. At 100 systems on 512×512: ~26M ops, still well under the 4ms SubViewport budget. The SubViewport only needs to re-render when territory state changes (ownership change, system add/remove), not every frame.

**Upgrade path for 200+ systems (post-Stage 13):** Replace the brute-force per-pixel loop with a Jump Flood Algorithm (JFA) multi-pass pipeline inside the same SubViewport. Same output texture, same plane quad, same visual contract. The JFA approach is O(log₂ n) passes and is what Paradox ships in Imperator: Rome. The brute-force approach is simpler to implement and debug; swap to JFA only if profiling shows the brute-force exceeds the 4ms budget at higher system counts.

---

## Renderer Integration: `settled_reach_renderer.gd`

### Setup (in `_ready()` or `_setup_territory_system()`)

1. **Create the SubViewport.**
   - Size: `WORLD_VIEW_TERRITORY_VORONOI_RESOLUTION` × `WORLD_VIEW_TERRITORY_VORONOI_RESOLUTION` (default 512).
   - `transparent_bg = true`.
   - `render_target_update_mode = SubViewport.UPDATE_ONCE` (only re-render on demand).
   - Add as child of the renderer node.

2. **Create a ColorRect inside the SubViewport.**
   - Anchor: full rect (fills the viewport).
   - Material: `ShaderMaterial` with `territory_voronoi.gdshader`.
   - Set initial uniform values from config.

3. **Create the galactic plane quad.**
   - `MeshInstance3D` with a `PlaneMesh`.
   - Size: computed from the bounding box of all system positions + margin. The plane must be large enough to cover the full system spread. Pad each axis by `fill_falloff` worth of world units so territory at the edges doesn't get clipped.
   - Position: at the galaxy's median Y coordinate (most systems sit roughly on or near a plane).
   - Rotation: oriented to face the camera's primary view direction (the galactic plane is roughly XZ; the PlaneMesh default is XZ, which is correct).
   - Material: `StandardMaterial3D`.
     - `albedo_texture` = `ViewportTexture` from the SubViewport.
     - `transparency` = `ALPHA`.
     - `shading_mode` = `UNSHADED` (no lighting on the territory plane).
     - `render_priority` = -1 (draw behind system nodes and connection lines, in front of deep galaxy particles).
     - `no_depth_test` = false (respect depth so it layers correctly with the 3D galaxy).
   - Add as child of the renderer node.

4. **Create the data textures.**
   - `system_data`: `ImageTexture` from an `Image` of format `FORMAT_RGBAF`, size `MAX_SYSTEMS × 1`. Initialize all pixels to (0, 0, 0, 0).
   - `faction_colors`: `ImageTexture` from an `Image` of format `FORMAT_RGBAF`, size `8 × 1`. Populated from faction color config.
   - Both assigned as shader uniforms on the ColorRect's material.

### Constants

```gdscript
const MAX_SYSTEMS: int = 128  # max systems supported in data texture; increase if needed
```

### Signal Handlers

**`_on_territory_set(region_id, center, radius, color)`**

```
Store in territory_registry: { region_id: { center, radius, color, faction_id } }
Call _rebuild_territory_data()
Trigger SubViewport re-render (render_target_update_mode = UPDATE_ONCE, then queue_redraw or set UPDATE_ONCE again)
```

**`_on_territory_updated(region_id, radius, color)`**

```
Update territory_registry entry
Call _rebuild_territory_data()
Trigger SubViewport re-render
```

**`_on_territory_removed(region_id)`**

```
Remove from territory_registry
Call _rebuild_territory_data()
Trigger SubViewport re-render
```

### `_rebuild_territory_data()`

```
var img = Image.create(MAX_SYSTEMS, 1, false, Image.FORMAT_RGBAF)
var idx = 0
var min_pos = Vector2(INF, INF)
var max_pos = Vector2(-INF, -INF)

for entry in territory_registry.values():
    var pos_2d = Vector2(entry.center.x, entry.center.z)  # project to XZ plane
    min_pos = min_pos.min(pos_2d)
    max_pos = max_pos.max(pos_2d)

# Add margin
var margin = fill_falloff_world_units
min_pos -= Vector2(margin, margin)
max_pos += Vector2(margin, margin)

# Store map bounds for UV-to-world mapping
# (the shader works in UV space 0–1; we normalize system positions into that range)
_map_bounds = Rect2(min_pos, max_pos - min_pos)

idx = 0
for entry in territory_registry.values():
    var pos_2d = Vector2(entry.center.x, entry.center.z)
    var norm_x = (pos_2d.x - min_pos.x) / (max_pos.x - min_pos.x)
    var norm_y = (pos_2d.y - min_pos.y) / (max_pos.y - min_pos.y)
    var faction_idx_norm = entry.faction_index / 8.0   # faction index 1–8, normalized
    var significance = clamp(entry.radius / max_radius, 0.0, 1.0)

    img.set_pixel(idx, 0, Color(norm_x, norm_y, faction_idx_norm, significance))
    idx += 1

# Update texture
system_data_texture.update(img)

# Update shader uniforms
shader_material.set_shader_parameter("system_count", idx)

# Update plane mesh size and position to match map bounds
territory_plane.mesh.size = Vector2(_map_bounds.size.x, _map_bounds.size.y)
territory_plane.position = Vector3(
    _map_bounds.position.x + _map_bounds.size.x * 0.5,
    _galaxy_median_y,
    _map_bounds.position.y + _map_bounds.size.y * 0.5
)
```

### Faction Color Setup

On `setup_era()` or when factions are first known, populate the `faction_colors` texture:

```
var img = Image.create(8, 1, false, Image.FORMAT_RGBAF)
for i in range(faction_count):
    img.set_pixel(i, 0, faction_color_array[i])
faction_colors_texture.update(img)
shader_material.set_shader_parameter("faction_colors", faction_colors_texture)
```

Faction colors come from the existing faction data in WorldViewData. The player faction, enemy factions, and neutral factions each have assigned colors already used by the system node rendering.

### Ownership Transition Animation

When a system changes ownership (territory_updated with a new color/faction), animate the transition:

```
# In _on_territory_updated(), if the faction changed:
var tween = create_tween()
tween.tween_method(
    func(t: float):
        # Interpolate the faction index in the data texture for this system
        # from old_faction_idx to new_faction_idx over the transition duration
        _update_system_faction_lerp(region_id, old_faction_idx, new_faction_idx, t)
        _trigger_viewport_rerender()
    ,
    0.0, 1.0,
    WORLD_VIEW_TERRITORY_TRANSITION_DURATION_SEC
)
```

The `_update_system_faction_lerp` method writes an intermediate faction color into the data texture, blending between old and new faction colors. This produces a smooth color flow as territory changes hands.

**Alternative simpler approach:** Skip per-system faction lerp. Instead, on ownership change, immediately update the data texture and trigger a re-render. The visual snap is masked by the flash VFX that accompanies conquest events (C5). If the snap looks acceptable during playtesting, this is less code. Try the simple approach first; add the tween if the snap is jarring.

---

## Tuning Values

Replace the existing bubble/contour values in `config/world_view_config.py`:

```python
# Territory visualization — Voronoi field (replaces bubble + contour values)
WORLD_VIEW_TERRITORY_VORONOI_RESOLUTION = 512     # SubViewport size (square, px)
WORLD_VIEW_TERRITORY_FILL_OPACITY = 0.12          # base alpha of faction fill interior
WORLD_VIEW_TERRITORY_FILL_FALLOFF = 0.15          # UV-space distance at which fill fades to 0
WORLD_VIEW_TERRITORY_EDGE_SOFTNESS = 0.03         # smoothstep width at territory outer boundary
WORLD_VIEW_TERRITORY_BORDER_WIDTH = 0.012         # UV-space width of faction-boundary glow band
WORLD_VIEW_TERRITORY_BORDER_BRIGHTNESS = 1.4      # brightness multiplier at faction borders
WORLD_VIEW_TERRITORY_TRANSITION_DURATION_SEC = 1.0 # unchanged from original spec
```

**Remove these values** (they belonged to the deleted bubble/contour system):

```python
# DELETE:
# WORLD_VIEW_TERRITORY_BUBBLE_OPACITY = 0.25
# WORLD_VIEW_TERRITORY_BUBBLE_RADIUS_SCALE = 1.6
# WORLD_VIEW_CONTOUR_THRESHOLD = 0.08
# WORLD_VIEW_CONTOUR_BRIGHTNESS = 1.4
# WORLD_VIEW_CONTOUR_LINE_THICKNESS_PX = 1.5
```

---

## Shell API Compatibility

The existing shell API shape is unchanged:

- `set_territory(region_id, center, radius, color)` — maps to adding an entry to the territory registry and rebuilding data textures.
- `update_territory(region_id, radius, color)` — maps to updating an entry.
- `remove_territory(region_id)` — maps to removing an entry.

The sequencer continues to call these methods exactly as before. The renderer's internal implementation of the signal handlers changes, but the public interface does not.

**One addition needed:** The renderer needs to know the faction index for each territory entry, not just the color. Currently `set_territory` passes `color` but not `faction_id`. Two options:

1. **Derive faction index from color** — maintain a `color → faction_index` lookup in the renderer, populated when faction colors are first set. Simple, no API change.
2. **Add faction_id to set_territory** — cleaner, but requires a shell API change. Acceptable since the sequencer is the only consumer and is being built in the same stage.

**Recommendation:** Option 1 for now (no API change). The renderer already has faction colors from the region node rendering. A `Dictionary` mapping `Color → int` is trivial.

---

## Visual Contract

These are the visual guarantees CC must achieve. Westley will eyeball these in the test harness.

1. **Faction territory reads at a glance.** Each faction's territory is a distinct colored region. A new player understands "blue controls this area, red controls that area" without explanation.

2. **Borders between factions are visible.** Where two factions' territory meets, a luminous brighter edge appears — not a hard geometric line, but a soft glow that feels organic.

3. **Galaxy particles remain visible.** The territory tints the space; it does not replace it. The ~5,200-particle galaxy structure (orbital rings, inflow streams, ambient dust) shows through the territory coloration. Territory fill opacity never exceeds `fill_opacity` (default 0.12).

4. **Unclaimed space is empty.** Systems with no faction ownership produce no territory fill. The void between factions and beyond the frontier is dark — only the galaxy particles are visible.

5. **Same-faction territory is continuous.** No internal Voronoi cell boundaries are drawn between systems of the same faction. The fill is one smooth colored region per faction.

6. **Territory shape is organic.** No angular wireframe lines, no convex hull artifacts. The territory edges are soft, rounded by the `edge_softness` smoothstep. Concave territory shapes (a faction wrapping around another) are handled correctly by the Voronoi computation.

7. **Ownership transitions are smooth.** When a system changes hands, the territory color shifts over ~1 second (or snaps if masked by flash VFX — see transition animation section).

---

## Checkpoint Verification

This replaces the original C3 and C4 prove-it criteria. Tested in the existing test harness (`tests/test_world_view.tscn`) with the 3-faction, 8-region, 9-connection mock world state.

### C3 — Territory Voronoi field

**Build:**
- `territory_voronoi.gdshader`
- SubViewport + ColorRect setup in `settled_reach_renderer.gd`
- Galactic plane quad with ViewportTexture
- Data texture creation and `_rebuild_territory_data()`
- Signal handlers: `_on_territory_set()`, `_on_territory_updated()`, `_on_territory_removed()`

**Prove-it:**
1. Test harness shows 3 factions with distinct colored territory regions.
2. Territory edges fade softly — no hard geometric boundaries.
3. Galaxy particles are visible through territory fill.
4. The "Conquer r_07" test button changes territory color (snap or smooth).
5. The "Remove territory r_04" test button removes that region's territory contribution.
6. No internal cell edges between same-faction systems.

### C4 — Border glow at faction boundaries

**Build:**
- Border detection logic in the shader (nearest vs. second-nearest faction comparison).
- Luminous edge rendering at faction boundaries.

**Prove-it:**
1. Where two different factions' territory meets, a brighter luminous edge is visible.
2. The edge is soft/organic, not a hard pixel line.
3. No border glow between same-faction systems (suppressed).
4. Border glow is visible at the test harness's default camera distance.

**STOP after C4.** Proceed to C5 (flashes) only after Westley signs off on the territory visual.

---

## Cleanup Checklist

After C3/C4 are verified, remove all dead code from the bubble/contour system:

- [ ] Delete `territory_bubbles.gdshader`
- [ ] Delete `territory_contour.gdshader`
- [ ] Remove any SubViewport contour pass setup code from `settled_reach_renderer.gd`
- [ ] Remove any per-system sphere/bubble mesh creation from `settled_reach_renderer.gd`
- [ ] Remove deleted tuning values from `world_view_config.py`
- [ ] Verify no references to deleted files remain in `.tscn` or `.tres` resources

---

## Bible Update

Add to `docs/bible_history/bible_2_00_world.md` in the "Faction territory" paragraph (lines 399–403), replacing the influence-bubbles-plus-border-contours description:

> Territory visualization uses a Voronoi influence field projected on the galactic plane — each system claims the space nearest to it, cells are unioned by faction ownership, and the result renders as translucent faction-colored regions with soft luminous borders emerging where rival factions' territory meets. Fill opacity fades with distance from owned systems so territory does not aggressively claim empty space. The galaxy particle structure remains visible through all territory coloration.

This replaces the "spherical influence bubble" and "derived border contour" paragraphs. The design intent ("colored regions with clearly defined borders") is preserved; the implementation technique changes.

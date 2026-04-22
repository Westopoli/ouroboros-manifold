# CC Paste — Territory Metaball Shader (replaces Voronoi approach)

## Context

The territory visualization is changing from Voronoi cells to metaball fields.
Each system emits a smooth radial influence field. Same-faction fields are summed
(metaball merge), producing organic blob shapes. The outline draws at the field
threshold isoline. Fill fades from bright at the outline to transparent at the center.
Factions cannot overlap — a margin-of-victory gap separates rival territories.

The uploaded `territory_metaball.gdshader` is the complete, tested shader.
Do NOT modify the shader logic or uniform values — they were tuned visually
in an interactive playground and are frozen.

## Step 1: Replace the shader file

Delete `scenes/shared/world_view/renderers/territory_voronoi.gdshader`.
Place the uploaded `territory_metaball.gdshader` at:
`scenes/shared/world_view/renderers/territory_metaball.gdshader`

## Step 2: Add a third data texture for border colors

The shader needs THREE data textures:
- `system_data` — already exists (positions, faction index, significance)
- `faction_colors` — already exists (fill colors, darker/muted)
- `faction_borders` — NEW (bright border colors per faction)

In `_setup_territory_voronoi()` (rename to `_setup_territory_metaball()`):

```gdscript
# Add alongside existing texture setup:
_faction_borders_image = Image.create(8, 1, false, Image.FORMAT_RGBAF)
_faction_borders_texture = ImageTexture.create_from_image(_faction_borders_image)
```

In `_register_faction_color()`, populate BOTH textures:

```gdscript
# Fill color: the faction color darkened for interior fill
_faction_colors_image.set_pixel(idx - 1, 0, Color(color.r * 0.4, color.g * 0.4, color.b * 0.4, 1.0))
_faction_colors_texture.update(_faction_colors_image)

# Border color: the faction color brightened for the outline
_faction_borders_image.set_pixel(idx - 1, 0, Color(
    min(color.r * 1.3, 1.0),
    min(color.g * 1.3, 1.0),
    min(color.b * 1.3, 1.0),
    1.0
))
_faction_borders_texture.update(_faction_borders_image)
```

## Step 3: Update shader uniform setup

In the setup function, replace ALL shader parameter calls with:

```gdscript
shader_mat.set_shader_parameter("system_data", _system_data_texture)
shader_mat.set_shader_parameter("faction_colors", _faction_colors_texture)
shader_mat.set_shader_parameter("faction_borders", _faction_borders_texture)
shader_mat.set_shader_parameter("system_count", 0)
shader_mat.set_shader_parameter("influence_radius", 0.17)
shader_mat.set_shader_parameter("threshold", 0.66)
shader_mat.set_shader_parameter("outline_band", 0.025)
shader_mat.set_shader_parameter("outline_alpha", 0.95)
shader_mat.set_shader_parameter("glow_band", 0.05)
shader_mat.set_shader_parameter("glow_alpha", 0.25)
shader_mat.set_shader_parameter("fill_opacity", 0.16)
shader_mat.set_shader_parameter("fill_fade_depth", 0.8)
shader_mat.set_shader_parameter("gap_margin", 0.30)
```

Remove ANY references to old uniforms: `fill_falloff`, `edge_softness`,
`border_width`, `border_brightness`, `border_alpha`, `outline_width`,
`fill_alpha`, etc. The shader has completely different uniforms now.

## Step 4: Update shader load path

Change the shader load path from:
```gdscript
shader_mat.shader = load("res://scenes/shared/world_view/renderers/territory_voronoi.gdshader")
```
to:
```gdscript
shader_mat.shader = load("res://scenes/shared/world_view/renderers/territory_metaball.gdshader")
```

## Step 5: Plane material

Verify the plane material uses:
```gdscript
plane_mat.blend_mode = BaseMaterial3D.BLEND_MODE_MIX
plane_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
plane_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
plane_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
plane_mat.no_depth_test = true
plane_mat.render_priority = -1
```

## Step 6: Delete old files

- Delete `territory_voronoi.gdshader`
- Delete `territory_bubbles.gdshader` if it still exists
- Delete `territory_contour.gdshader` if it still exists

## How the shader works (DO NOT MODIFY)

1. Each system emits influence: `R² / (d² + R²)` where R scales with significance
2. Same-faction influences are summed (metaball merge → smooth organic blobs)
3. Best and second-best faction fields are found per pixel
4. Gap test: pixel is "inside" only if `bestField - secondField >= gap_margin`
5. Outline draws where field is just above threshold (within `outline_band`)
6. Fill draws deeper inside, fading to transparent toward center
7. Glow draws just below threshold on the outside
8. All boundaries are mathematically smooth (no angular artifacts)

## Verification

- [ ] Smooth organic territory blobs around each faction's systems
- [ ] Bright colored outline at territory boundary (no jagged edges)
- [ ] Fill fades from visible near outline to transparent at center
- [ ] Dark gap between rival factions' territories (both outlines visible)
- [ ] Galaxy particles visible through territory fill
- [ ] No old bubble/contour/Voronoi artifacts
- [ ] Soft glow halo just outside territory boundary

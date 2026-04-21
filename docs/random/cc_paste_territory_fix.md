# CC Paste — Territory Voronoi Fix

## Problem
Shader draws per-system outline rings + thin border lines instead of filled territory regions. The `outline_width`/`outline_alpha` uniforms and the ring-drawing code (lines 54-58 in current shader) are wrong. Fill alpha is set to 0.04 — nearly invisible.

## Fix 1: Replace the shader

Replace `scenes/shared/world_view/renderers/territory_voronoi.gdshader` entirely with the uploaded file `territory_voronoi.gdshader`. The new shader:
- Removes all outline/ring code
- Fills each faction's Voronoi cells with translucent faction color
- Fades fill with distance from nearest system (no fill beyond falloff radius)
- Draws soft luminous glow at faction boundaries only (not between same-faction systems)
- No per-system circles, no wireframe, just smooth filled regions

## Fix 2: Update uniform values in `_setup_territory_voronoi()`

The shader uniforms changed. Replace the `set_shader_parameter` block with:

```gdscript
shader_mat.set_shader_parameter("system_data", _system_data_texture)
shader_mat.set_shader_parameter("faction_colors", _faction_colors_texture)
shader_mat.set_shader_parameter("system_count", 0)
shader_mat.set_shader_parameter("fill_opacity", 0.15)
shader_mat.set_shader_parameter("fill_falloff", 0.18)
shader_mat.set_shader_parameter("edge_softness", 0.04)
shader_mat.set_shader_parameter("border_width", 0.02)
shader_mat.set_shader_parameter("border_brightness", 1.6)
shader_mat.set_shader_parameter("border_alpha", 0.7)
```

Remove any references to `fill_alpha`, `outline_width`, `outline_alpha` — those uniforms no longer exist.

## Fix 3: Plane material blend mode

In `_setup_territory_voronoi()`, the plane material currently uses `BLEND_MODE_ADD`. Change to `BLEND_MODE_MIX` so faction colors render correctly against the dark galaxy background without washing out to white:

```gdscript
plane_mat.blend_mode = BaseMaterial3D.BLEND_MODE_MIX
```

## Verification

After applying all three fixes:
1. Each faction's territory should appear as a soft colored translucent region
2. Galaxy particles must be visible through the territory fill
3. Where two factions' territory meets, a brighter glowing edge should appear
4. No per-system circles or rings should be visible
5. Unclaimed space (no nearby owned systems) should be fully transparent

# CC Paste — Territory Visual Fix Round 3

## What's wrong

Three problems visible in the screenshot:

1. **Thick colored outline rings** at each faction's territory perimeter (the bold green/blue/red loops). The reference image has NO outlines — territory fades smoothly to nothing.
2. **Fill too opaque in the center, too sharp at the edge.** Reference shows soft, gradual fade. Current has a tight smoothstep creating a distinct boundary.
3. **No faction border glow.** Where blue meets green meets red, the reference shows a bright luminous edge. Current shader has no faction-boundary code.

## Fix 1: Replace shader file

Replace `scenes/shared/world_view/renderers/territory_voronoi.gdshader` with the uploaded `territory_voronoi.gdshader`.

Key changes from the current shader:
- **Deleted** lines 12-13 (`outline_width`, `outline_alpha` uniforms) — gone entirely
- **Deleted** lines 57-61 (outline ring calculation) — gone entirely
- **Added** `border_width`, `border_brightness`, `border_alpha` uniforms for faction boundary glow
- **Added** faction border glow code (brightens color where two different factions' Voronoi cells meet)
- **Widened** the smoothstep band: `smoothstep(falloff - softness, falloff + softness, dist)` instead of `smoothstep(falloff - softness, falloff, dist)` — this doubles the fade zone so edges are gradual, not abrupt
- **Removed** the `proximity_fade` near system centers (line 53 in current) — unnecessary

## Fix 2: Update uniform values in `_setup_territory_voronoi()`

In `world_view_structure.gd`, replace the shader parameter block (around lines 703-709) with:

```gdscript
shader_mat.set_shader_parameter("system_data", _system_data_texture)
shader_mat.set_shader_parameter("faction_colors", _faction_colors_texture)
shader_mat.set_shader_parameter("system_count", 0)
shader_mat.set_shader_parameter("fill_opacity", 0.18)
shader_mat.set_shader_parameter("fill_falloff", 0.22)
shader_mat.set_shader_parameter("edge_softness", 0.07)
shader_mat.set_shader_parameter("border_width", 0.025)
shader_mat.set_shader_parameter("border_brightness", 1.8)
shader_mat.set_shader_parameter("border_alpha", 0.65)
```

Delete any lines setting `outline_width` or `outline_alpha` — those uniforms no longer exist.

## Fix 3: Plane material

Verify the plane material uses `BLEND_MODE_MIX` (not ADD):
```gdscript
plane_mat.blend_mode = BaseMaterial3D.BLEND_MODE_MIX
```

## Verification checklist

After all three fixes:
- [ ] No outline rings or perimeter loops around any faction's territory
- [ ] Territory is continuous soft-colored fill that fades gradually at the edges
- [ ] Galaxy particles visible through the fill (opacity ~18%, not solid)
- [ ] Where blue meets green (or any two factions), a brighter glowing edge is visible
- [ ] No internal Voronoi cell edges between same-faction systems
- [ ] Unclaimed space is fully transparent

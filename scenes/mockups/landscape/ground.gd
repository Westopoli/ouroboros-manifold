class_name GroundBuilder
extends RefCounted

# Matches placer.gd's constant so both files agree on world scale; 250 wu/level is a guess
# per the design brief, pending Westley's review.
const TERRACE_HEIGHT_WU := 250.0
const LEVELS := 4.0
const CLIFF_SOFTEN := 0.5
const VOID_ELEVATION_THRESHOLD := 0.125

func build(field_map: FieldMap, kit: Dictionary) -> MeshInstance3D:
	var dim: int = field_map.dim
	var spacing: float = FieldMap.SPACING
	var palette: Dictionary = kit.palette
	var zone_colors := [Color(palette.zone_a), Color(palette.zone_b), Color(palette.zone_c)]
	var cliff_color := Color(palette.cliff)
	# Water plane (surface mode) is drawn by whichever file the master spec assigns it to;
	# skipping it here unconditionally avoids a double-drawn plane if that file also draws one.
	var void_mode: bool = kit.get("water_is", "surface") == "void"

	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)

	for gy in range(dim - 1):
		for gx in range(dim - 1):
			if void_mode and _quad_is_void(field_map, gx, gy, dim):
				continue
			_emit_quad(st, field_map, gx, gy, dim, spacing, zone_colors, cliff_color)

	st.generate_normals()
	var mesh := st.commit()

	var mesh_instance := MeshInstance3D.new()
	mesh_instance.mesh = mesh
	var mat := StandardMaterial3D.new()
	mat.vertex_color_use_as_albedo = true
	mat.roughness = 0.9
	mat.metallic = 0.0
	mesh_instance.material_override = mat
	return mesh_instance

func _emit_quad(st: SurfaceTool, field_map: FieldMap, gx: int, gy: int, dim: int, spacing: float, zone_colors: Array, cliff_color: Color) -> void:
	var v00 := _vertex(field_map, gx, gy, dim, spacing, zone_colors, cliff_color)
	var v10 := _vertex(field_map, gx + 1, gy, dim, spacing, zone_colors, cliff_color)
	var v11 := _vertex(field_map, gx + 1, gy + 1, dim, spacing, zone_colors, cliff_color)
	var v01 := _vertex(field_map, gx, gy + 1, dim, spacing, zone_colors, cliff_color)

	st.set_color(v00.color)
	st.add_vertex(v00.pos)
	st.set_color(v10.color)
	st.add_vertex(v10.pos)
	st.set_color(v11.color)
	st.add_vertex(v11.pos)

	st.set_color(v00.color)
	st.add_vertex(v00.pos)
	st.set_color(v11.color)
	st.add_vertex(v11.pos)
	st.set_color(v01.color)
	st.add_vertex(v01.pos)

func _vertex(field_map: FieldMap, gx: int, gy: int, dim: int, spacing: float, zone_colors: Array, cliff_color: Color) -> Dictionary:
	var height := _height_at(field_map, gx, gy, dim)
	var pos := Vector3(gx * spacing, height, gy * spacing)
	var color := _zone_color(field_map, gx, gy, dim, zone_colors)
	var cliff_factor := _cliff_factor(field_map, gx, gy, dim, height)
	color = color.lerp(cliff_color, cliff_factor)
	return {pos = pos, color = color}

func _height_at(field_map: FieldMap, gx: int, gy: int, dim: int) -> float:
	var cell: Dictionary = field_map.grid[gy * dim + gx]
	return cell.elevation * LEVELS * TERRACE_HEIGHT_WU

func _zone_color(field_map: FieldMap, gx: int, gy: int, dim: int, zone_colors: Array) -> Color:
	# No raw per-zone noise weights survive to this file, only the winning zone id per cell,
	# so approximate a soft blend by voting the 3x3 neighborhood and weighting by vote share.
	var counts := [0.0, 0.0, 0.0]
	var total := 0.0
	for oy in range(-1, 2):
		for ox in range(-1, 2):
			var nx := gx + ox
			var ny := gy + oy
			if nx < 0 or nx >= dim or ny < 0 or ny >= dim:
				continue
			var z: int = field_map.grid[ny * dim + nx].zone
			counts[z] += 1.0
			total += 1.0
	var color := Color(0, 0, 0)
	for i in range(3):
		color += zone_colors[i] * (counts[i] / total)
	return color

func _cliff_factor(field_map: FieldMap, gx: int, gy: int, dim: int, height: float) -> float:
	# Steepness proxy: how far this vertex sits above/below its 4 orthogonal neighbors' average
	# height, scaled against half a terrace step; softened (not a hard threshold) so cliff
	# shading grades in rather than banding.
	var sum := 0.0
	var count := 0.0
	var offsets: Array[Vector2i] = [Vector2i(-1, 0), Vector2i(1, 0), Vector2i(0, -1), Vector2i(0, 1)]
	for offset in offsets:
		var nx: int = gx + offset.x
		var ny: int = gy + offset.y
		if nx < 0 or nx >= dim or ny < 0 or ny >= dim:
			continue
		sum += _height_at(field_map, nx, ny, dim)
		count += 1.0
	if count == 0.0:
		return 0.0
	var avg: float = sum / count
	var diff: float = abs(height - avg)
	return clamp(diff / (TERRACE_HEIGHT_WU * CLIFF_SOFTEN), 0.0, 1.0)

func _quad_is_void(field_map: FieldMap, gx: int, gy: int, dim: int) -> bool:
	var corners: Array[Vector2i] = [Vector2i(gx, gy), Vector2i(gx + 1, gy), Vector2i(gx, gy + 1), Vector2i(gx + 1, gy + 1)]
	var water_sum := 0.0
	var elevation_sum := 0.0
	for c in corners:
		var cell: Dictionary = field_map.grid[c.y * dim + c.x]
		water_sum += cell.water
		elevation_sum += cell.elevation
	return (water_sum / 4.0) > 0.5 or (elevation_sum / 4.0) < VOID_ELEVATION_THRESHOLD

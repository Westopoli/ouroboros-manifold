class_name GroundBuilder
extends RefCounted

const CLIFF_REFERENCE_WU := 400.0
const VOID_ELEVATION_THRESHOLD_WU := 100.0

func build(field_map: FieldMap, kit: Dictionary) -> MeshInstance3D:
	var dim: int = field_map.dim
	var spacing: float = FieldMap.SPACING
	var palette: Dictionary = kit.palette
	var zone_colors := [Color(palette.zone_a), Color(palette.zone_b), Color(palette.zone_c), Color(palette.zone_d), Color(palette.zone_e)]
	var cliff_color := Color(palette.cliff)
	# Water plane (surface mode) is drawn by whichever file the master spec assigns it to;
	# skipping it here unconditionally avoids a double-drawn plane if that file also draws one.
	var void_mode: bool = kit.get("water_is", "surface") == "void"

	# Each grid point is shared by up to 4 quads. Precomputing height/color once per point
	# and indexing into it from the quad loop (rather than recomputing per corner) is the
	# fix measured in pass 2 (ground was the dominant regenerate cost). Elevation is now
	# continuous world units (pass 3), not a normalized 0..1 pre-terraced value, so vertex
	# Y is the grid's own elevation directly.
	var heights := PackedFloat32Array()
	heights.resize(dim * dim)
	for gy in range(dim):
		for gx in range(dim):
			heights[gy * dim + gx] = field_map.grid[gy * dim + gx].elevation

	var colors: Array = []
	colors.resize(dim * dim)
	for gy in range(dim):
		for gx in range(dim):
			var idx := gy * dim + gx
			var color := _zone_color(field_map, gx, gy, dim, zone_colors)
			var cliff_factor := _cliff_factor(heights, gx, gy, dim)
			colors[idx] = color.lerp(cliff_color, cliff_factor)

	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)

	for gy in range(dim - 1):
		for gx in range(dim - 1):
			if void_mode and _quad_is_void(field_map, gx, gy, dim):
				continue
			_emit_quad(st, heights, colors, gx, gy, dim, spacing)

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

func _emit_quad(st: SurfaceTool, heights: PackedFloat32Array, colors: Array, gx: int, gy: int, dim: int, spacing: float) -> void:
	var i00 := gy * dim + gx
	var i10 := gy * dim + gx + 1
	var i11 := (gy + 1) * dim + gx + 1
	var i01 := (gy + 1) * dim + gx

	var p00 := Vector3(gx * spacing, heights[i00], gy * spacing)
	var p10 := Vector3((gx + 1) * spacing, heights[i10], gy * spacing)
	var p11 := Vector3((gx + 1) * spacing, heights[i11], (gy + 1) * spacing)
	var p01 := Vector3(gx * spacing, heights[i01], (gy + 1) * spacing)

	st.set_color(colors[i00])
	st.add_vertex(p00)
	st.set_color(colors[i10])
	st.add_vertex(p10)
	st.set_color(colors[i11])
	st.add_vertex(p11)

	st.set_color(colors[i00])
	st.add_vertex(p00)
	st.set_color(colors[i11])
	st.add_vertex(p11)
	st.set_color(colors[i01])
	st.add_vertex(p01)

func _zone_color(field_map: FieldMap, gx: int, gy: int, dim: int, zone_colors: Array) -> Color:
	# No raw per-zone noise weights survive to this file, only the winning zone id per cell,
	# so approximate a soft blend by voting the 3x3 neighborhood and weighting by vote share.
	var counts := [0.0, 0.0, 0.0, 0.0, 0.0]
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
	for i in range(5):
		color += zone_colors[i] * (counts[i] / total)
	return color

func _cliff_factor(heights: PackedFloat32Array, gx: int, gy: int, dim: int) -> float:
	# Steepness proxy: how far this vertex sits above/below its 4 orthogonal neighbors'
	# average height, scaled against a reference slope; softened (not a hard threshold) so
	# cliff shading grades in rather than banding.
	var height: float = heights[gy * dim + gx]
	var sum := 0.0
	var count := 0.0
	var offsets: Array[Vector2i] = [Vector2i(-1, 0), Vector2i(1, 0), Vector2i(0, -1), Vector2i(0, 1)]
	for offset in offsets:
		var nx: int = gx + offset.x
		var ny: int = gy + offset.y
		if nx < 0 or nx >= dim or ny < 0 or ny >= dim:
			continue
		sum += heights[ny * dim + nx]
		count += 1.0
	if count == 0.0:
		return 0.0
	var avg: float = sum / count
	var diff: float = abs(height - avg)
	return clamp(diff / CLIFF_REFERENCE_WU, 0.0, 1.0)

func _quad_is_void(field_map: FieldMap, gx: int, gy: int, dim: int) -> bool:
	var corners: Array[Vector2i] = [Vector2i(gx, gy), Vector2i(gx + 1, gy), Vector2i(gx, gy + 1), Vector2i(gx + 1, gy + 1)]
	var water_sum := 0.0
	var elevation_sum := 0.0
	for c in corners:
		var cell: Dictionary = field_map.grid[c.y * dim + c.x]
		water_sum += cell.water
		elevation_sum += cell.elevation
	return (water_sum / 4.0) > 0.5 or (elevation_sum / 4.0) < VOID_ELEVATION_THRESHOLD_WU

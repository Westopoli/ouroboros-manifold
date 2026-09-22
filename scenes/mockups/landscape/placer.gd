class_name Placer
extends RefCounted

# RefCounted, not Node3D: this is a stateless builder called once per (field_map, kit)
# and handed a world_parent to populate. It never needs to be in the scene tree itself,
# so a plain object is simpler than a node with lifecycle baggage.

const JITTER_RANGE_WU := 50.0
const BORDER_SEGMENT_SPACING_WU := 150.0
const CROSSING_GAP_WU := 300.0
const DEFAULT_BORDER_HEIGHT_WU := 300.0
const DEFAULT_NODE_SIZE: Array = [300.0, 400.0]
const DEFAULT_BACKDROP_SIZE: Array = [6000.0, 4000.0]
const WALL_THICKNESS_WU := 40.0
const FLAT_THICKNESS_WU := 20.0
const MAGENTA_COLOR := Color(1.0, 0.0, 1.0)

# Cliff border height is sampled from real terrain, not the kit's flat default.
const MIN_CLIFF_HEIGHT_WU := 40.0
const CLIFF_HEIGHT_SAMPLE_OFFSET_WU := 300.0
const CLIFF_HEIGHT_BUCKET_WU := 20.0

# Wall/hull border segments use tighter spacing plus overlap-length so the
# rampart reads as continuous instead of dashed, regardless of the other
# border kinds' spacing.
const WALL_SEGMENT_SPACING_WU := 100.0
const WALL_SEGMENT_OVERLAP_FACTOR := 1.3

const BACKDROP_INSTANCE_COUNT := 7
const BACKDROP_JITTER_WU := 800.0
const BACKDROP_SCALE_JITTER := 0.15

# Fixed mesh vocabulary from kits/README.md. is_known_mesh_name() is the testable API
# a later verify.gd step should call; build_mesh() falls back to a magenta box for any
# name not in MESH_BUILDER_METHODS (R-146-03 placeholder-miss rule).
const KNOWN_MESH_NAMES: Array = [
	"box", "box_gable", "prism", "cone_on_stick", "flat_box", "colonnade",
	"wall_segment", "gate_arch", "bridge_arches", "cliff_face", "stair_ramp",
	"acropolis", "camp_ring", "mountain_range", "hab_pod", "hab_ring", "spire",
	"hull_segment", "airlock", "docking_spine", "ore_chunk", "derelict",
	"ice_shard", "asteroid_backdrop", "none",
]

const MESH_BUILDER_METHODS: Dictionary = {
	"box": "_mesh_box",
	"box_gable": "_mesh_box_gable",
	"prism": "_mesh_prism",
	"cone_on_stick": "_mesh_cone_on_stick",
	"flat_box": "_mesh_flat_box",
	"colonnade": "_mesh_colonnade",
	"wall_segment": "_mesh_wall_segment",
	"gate_arch": "_mesh_gate_arch",
	"bridge_arches": "_mesh_bridge_arches",
	"cliff_face": "_mesh_cliff_face",
	"stair_ramp": "_mesh_stair_ramp",
	"acropolis": "_mesh_acropolis",
	"camp_ring": "_mesh_camp_ring",
	"mountain_range": "_mesh_mountain_range",
	"hab_pod": "_mesh_hab_pod",
	"hab_ring": "_mesh_hab_ring",
	"spire": "_mesh_spire",
	"hull_segment": "_mesh_hull_segment",
	"airlock": "_mesh_airlock",
	"docking_spine": "_mesh_docking_spine",
	"ore_chunk": "_mesh_ore_chunk",
	"derelict": "_mesh_derelict",
	"ice_shard": "_mesh_ice_shard",
	"asteroid_backdrop": "_mesh_asteroid_backdrop",
}


static func is_known_mesh_name(mesh_name: String) -> bool:
	return KNOWN_MESH_NAMES.has(mesh_name)


static func load_kit(path: String) -> Dictionary:
	var text := FileAccess.get_file_as_string(path)
	var parsed = JSON.parse_string(text)
	if typeof(parsed) != TYPE_DICTIONARY:
		return {}
	return parsed


func build_mesh(mesh_name: String, size: Array) -> Mesh:
	if mesh_name == "none":
		return null
	if not MESH_BUILDER_METHODS.has(mesh_name):
		return _mesh_magenta_placeholder(size)
	return call(MESH_BUILDER_METHODS[mesh_name], size)


func place(field_map: FieldMap, kit: Dictionary, world_parent: Node3D) -> Dictionary:
	# FieldMap does not expose its generation seed as a public field (only the
	# p_seed constructor arg, consumed internally). compute_hash() is deterministic
	# per generated map and stands in for it here.
	var rng := RandomNumberGenerator.new()
	rng.seed = field_map.compute_hash()

	var kit_name: String = kit.get("name", "kit")
	var groups: Dictionary = {}

	_place_cells(field_map, kit, kit_name, rng, groups)
	_place_borders(field_map, kit, kit_name, groups)
	_place_nodes(field_map, kit, kit_name, groups)
	_place_backdrop(field_map, kit, kit_name, groups)

	var total := 0
	var by_type: Dictionary = {}
	for key in groups.keys():
		var g: Dictionary = groups[key]
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.use_colors = true
		mm.mesh = g.mesh
		mm.instance_count = g.transforms.size()
		for i in range(g.transforms.size()):
			mm.set_instance_transform(i, g.transforms[i])
			mm.set_instance_color(i, g.colors[i])
		var mmi := MultiMeshInstance3D.new()
		mmi.name = key
		mmi.multimesh = mm
		var mat := StandardMaterial3D.new()
		mat.vertex_color_use_as_albedo = true
		mmi.material_override = mat
		world_parent.add_child(mmi)
		total += g.transforms.size()
		by_type[g.piece] = int(by_type.get(g.piece, 0)) + g.transforms.size()

	if kit.get("water_is", "") == "surface":
		_place_water(field_map, kit, world_parent)

	return {total = total, by_type = by_type}


func _place_cells(field_map: FieldMap, kit: Dictionary, kit_name: String, rng: RandomNumberGenerator, groups: Dictionary) -> void:
	var terrain_rules: Array = kit.get("terrain", [])
	var city_rules: Array = kit.get("city", [])
	var dim: int = field_map.dim
	var spacing: float = FieldMap.SPACING
	for gy in range(dim):
		for gx in range(dim):
			var cell: Dictionary = field_map.grid[gy * dim + gx]
			var rule := _find_matching_rule(terrain_rules, cell)
			if cell.district >= 1:
				var city_rule := _find_matching_rule(city_rules, cell)
				if not city_rule.is_empty():
					rule = city_rule
			if rule.is_empty():
				continue
			var density: float = rule.get("density", 0.0)
			if rng.randf() >= density:
				continue
			var resolved := _resolve(rule.get("mesh", "none"), rule.get("color", "#ffffff"), rule.get("size", []))
			if resolved.is_empty():
				continue
			var jx := rng.randf_range(-JITTER_RANGE_WU, JITTER_RANGE_WU)
			var jz := rng.randf_range(-JITTER_RANGE_WU, JITTER_RANGE_WU)
			var wx := gx * spacing + jx
			var wz := gy * spacing + jz
			var ground_y: float = cell.elevation
			var y: float = ground_y + _ground_offset(resolved.mesh)
			var xform := Transform3D(Basis(), Vector3(wx, y, wz))
			_group_add(groups, rule.get("piece", "piece"), kit_name, resolved.mesh, xform, resolved.color)


func _place_borders(field_map: FieldMap, kit: Dictionary, kit_name: String, groups: Dictionary) -> void:
	var borders_cfg: Dictionary = kit.get("borders", {})
	var crossings_by_border: Dictionary = {}
	for c in field_map.crossings:
		var bi: int = c.border_index
		if not crossings_by_border.has(bi):
			crossings_by_border[bi] = []
		crossings_by_border[bi].append(c)

	for bi in range(field_map.borders.size()):
		var border: Dictionary = field_map.borders[bi]
		var cfg: Dictionary = borders_cfg.get(border.kind, {})
		if cfg.is_empty():
			continue
		var height: float = cfg.get("height", 0.0)
		if height <= 0.0:
			height = DEFAULT_BORDER_HEIGHT_WU
		var mesh_name: String = cfg.get("mesh", "none")
		var color_hex: String = cfg.get("color", "#ffffff")
		var crossings_here: Array = crossings_by_border.get(bi, [])
		var is_cliff: bool = border.kind == "cliff"
		var is_wall: bool = border.kind == "wall"
		var spacing_wu: float = WALL_SEGMENT_SPACING_WU if is_wall else BORDER_SEGMENT_SPACING_WU
		var seg_length_wu: float = (WALL_SEGMENT_SPACING_WU * WALL_SEGMENT_OVERLAP_FACTOR) if is_wall else BORDER_SEGMENT_SPACING_WU

		if mesh_name != "none":
			# Cliff segments each need their own mesh (real elevation-derived height),
			# so only pre-resolve one shared mesh for the other border kinds.
			var resolved_fixed: Dictionary = {}
			if not is_cliff:
				resolved_fixed = _resolve(mesh_name, color_hex, [seg_length_wu, height])
			if is_cliff or not resolved_fixed.is_empty():
				var pts: Array = border.points
				for i in range(pts.size() - 1):
					var a: Vector2 = pts[i]
					var b: Vector2 = pts[i + 1]
					var seg_len: float = a.distance_to(b)
					var nd: Vector2 = ((b - a) / seg_len) if seg_len > 0.0001 else Vector2(1.0, 0.0)
					var basis := _border_basis(nd)
					var perp2 := Vector2(-nd.y, nd.x)
					var d := 0.0
					while d < seg_len:
						var t: float = (d / seg_len) if seg_len > 0.0 else 0.0
						var p: Vector2 = a.lerp(b, t)
						if not _in_any_gap(p, crossings_here):
							var resolved := resolved_fixed
							var group_kit_name := kit_name
							if is_cliff:
								var cliff_h := _cliff_height_wu(field_map, p, perp2)
								resolved = _resolve(mesh_name, color_hex, [seg_length_wu, cliff_h])
								var bucket := int(round(cliff_h / CLIFF_HEIGHT_BUCKET_WU))
								group_kit_name = "%s_h%d" % [kit_name, bucket]
							if not resolved.is_empty():
								var ground_y := _elevation_at(field_map, p)
								var y: float = ground_y + _ground_offset(resolved.mesh)
								var xform := Transform3D(basis, Vector3(p.x, y, p.y))
								_group_add(groups, "%s_segment" % border.kind, group_kit_name, resolved.mesh, xform, resolved.color)
						d += spacing_wu

		var crossing_cfg: Dictionary = cfg.get("crossing", {})
		for c in crossings_here:
			var ccfg: Dictionary = crossing_cfg.get(c.kind, {})
			if ccfg.is_empty():
				continue
			var cp: Vector2 = c.point
			# Crossing pieces align to the border's local direction here too (same
			# fix as the segments above): previously placed with an identity basis,
			# so a gate/airlock on a north-south border sat rotated 90 degrees off
			# from the wall it interrupts, reading as a thin edge-on sliver.
			var cdir := _border_dir_at(border, cp)
			var crossing_height := height
			if is_cliff:
				var cperp := Vector2(-cdir.y, cdir.x)
				crossing_height = _cliff_height_wu(field_map, cp, cperp)
			var cresolved := _resolve(ccfg.get("mesh", "none"), ccfg.get("color", "#ffffff"), [CROSSING_GAP_WU * 2.0, crossing_height])
			if cresolved.is_empty():
				continue
			var cground := _elevation_at(field_map, cp)
			var cy: float = cground + _ground_offset(cresolved.mesh)
			var cbasis := _border_basis(cdir)
			var cxform := Transform3D(cbasis, Vector3(cp.x, cy, cp.y))
			_group_add(groups, c.kind, kit_name, cresolved.mesh, cxform, cresolved.color)


func _place_nodes(field_map: FieldMap, kit: Dictionary, kit_name: String, groups: Dictionary) -> void:
	var nodes_cfg: Dictionary = kit.get("nodes", {})
	for n in field_map.nodes:
		var cfg: Dictionary = nodes_cfg.get(n.type, {})
		if cfg.is_empty():
			continue
		var resolved := _resolve(cfg.get("mesh", "none"), cfg.get("color", "#ffffff"), DEFAULT_NODE_SIZE)
		if resolved.is_empty():
			continue
		var pos: Vector2 = n.pos
		var ground_y := _elevation_at(field_map, pos)
		var y: float = ground_y + _ground_offset(resolved.mesh)
		var xform := Transform3D(Basis(), Vector3(pos.x, y, pos.y))
		_group_add(groups, n.type, kit_name, resolved.mesh, xform, resolved.color)


func _place_backdrop(field_map: FieldMap, kit: Dictionary, kit_name: String, groups: Dictionary) -> void:
	var cfg: Dictionary = kit.get("backdrop", {})
	if cfg.is_empty():
		return
	var resolved := _resolve(cfg.get("mesh", "none"), cfg.get("color", "#ffffff"), DEFAULT_BACKDROP_SIZE)
	if resolved.is_empty():
		return
	var distance: float = cfg.get("distance", 30000.0)
	# Same seeding pattern as place()'s rng: deterministic per field_map, offset
	# so this stream doesn't line up with the cell-placement rng's draws.
	var rng := RandomNumberGenerator.new()
	rng.seed = field_map.compute_hash() + 777
	var base_z: float = field_map.canvas + distance
	for i in range(BACKDROP_INSTANCE_COUNT):
		var t: float = (float(i) / float(BACKDROP_INSTANCE_COUNT - 1)) if BACKDROP_INSTANCE_COUNT > 1 else 0.5
		var base_x: float = lerp(-field_map.canvas * 0.25, field_map.canvas * 1.25, t)
		var jx := rng.randf_range(-BACKDROP_JITTER_WU, BACKDROP_JITTER_WU)
		var jz := rng.randf_range(-BACKDROP_JITTER_WU, BACKDROP_JITTER_WU)
		var scale_j: float = rng.randf_range(1.0 - BACKDROP_SCALE_JITTER, 1.0 + BACKDROP_SCALE_JITTER)
		var pos := Vector3(base_x + jx, distance * 0.1, base_z + jz)
		var xform := Transform3D(Basis().scaled(Vector3(scale_j, scale_j, scale_j)), pos)
		_group_add(groups, "backdrop", kit_name, resolved.mesh, xform, resolved.color)


func _place_water(field_map: FieldMap, kit: Dictionary, world_parent: Node3D) -> void:
	var palette: Dictionary = kit.get("palette", {})
	var color_hex: String = palette.get("water", "#2aa7d6")
	var plane := PlaneMesh.new()
	plane.size = Vector2(field_map.canvas, field_map.canvas)
	var mi := MeshInstance3D.new()
	mi.mesh = plane
	mi.name = "water_plane"
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(color_hex)
	mi.material_override = mat
	mi.position = Vector3(field_map.canvas * 0.5, 0.0, field_map.canvas * 0.5)
	world_parent.add_child(mi)


func _resolve(mesh_name: String, color_hex: String, size: Array) -> Dictionary:
	var mesh := build_mesh(mesh_name, size)
	if mesh == null:
		return {}
	var color: Color = MAGENTA_COLOR if not is_known_mesh_name(mesh_name) else Color(color_hex)
	return {mesh = mesh, color = color}


func _group_add(groups: Dictionary, piece: String, kit_name: String, mesh: Mesh, xform: Transform3D, color: Color) -> void:
	var key := "%s::%s" % [piece, kit_name]
	if not groups.has(key):
		groups[key] = {piece = piece, mesh = mesh, transforms = [], colors = []}
	groups[key].transforms.append(xform)
	groups[key].colors.append(color)


func _find_matching_rule(rules: Array, cell: Dictionary) -> Dictionary:
	for rule in rules:
		if _rule_matches(rule.get("when", {}), cell):
			return rule
	return {}


func _rule_matches(when: Dictionary, cell: Dictionary) -> bool:
	for key in when.keys():
		var cond = when[key]
		if key == "zone":
			var zone_names := ["zone_a", "zone_b", "zone_c", "zone_d", "zone_e"]
			if zone_names[cell.zone] != cond:
				return false
		elif key == "district":
			if int(cond) != cell.district:
				return false
		else:
			var val: float = cell.get(key, 0.0)
			if val < float(cond[0]) or val > float(cond[1]):
				return false
	return true


func _in_any_gap(p: Vector2, crossings_here: Array) -> bool:
	for c in crossings_here:
		if p.distance_to(c.point) <= CROSSING_GAP_WU:
			return true
	return false


func _elevation_at(field_map: FieldMap, p: Vector2) -> float:
	var dim: int = field_map.dim
	var spacing: float = FieldMap.SPACING
	var gx: int = clampi(int(round(p.x / spacing)), 0, dim - 1)
	var gy: int = clampi(int(round(p.y / spacing)), 0, dim - 1)
	var cell: Dictionary = field_map.grid[gy * dim + gx]
	return cell.elevation


# Real elevation step at a cliff border point: sample the grid on both sides
# (perpendicular to the border) and diff. Floored so a barely-there step doesn't
# render as a sliver.
func _cliff_height_wu(field_map: FieldMap, p: Vector2, perp2: Vector2) -> float:
	var dim: int = field_map.dim
	var spacing: float = FieldMap.SPACING
	var p_hi: Vector2 = p + perp2 * CLIFF_HEIGHT_SAMPLE_OFFSET_WU
	var p_lo: Vector2 = p - perp2 * CLIFF_HEIGHT_SAMPLE_OFFSET_WU
	var gx_hi: int = clampi(int(round(p_hi.x / spacing)), 0, dim - 1)
	var gy_hi: int = clampi(int(round(p_hi.y / spacing)), 0, dim - 1)
	var gx_lo: int = clampi(int(round(p_lo.x / spacing)), 0, dim - 1)
	var gy_lo: int = clampi(int(round(p_lo.y / spacing)), 0, dim - 1)
	var e_hi: float = field_map.grid[gy_hi * dim + gx_hi].elevation
	var e_lo: float = field_map.grid[gy_lo * dim + gx_lo].elevation
	var diff_wu: float = abs(e_hi - e_lo)
	return max(diff_wu, MIN_CLIFF_HEIGHT_WU)


# Nearest-segment direction on a border's polyline, for orienting a piece
# (segment or crossing) that doesn't already know which (a, b) pair it's on.
func _border_dir_at(border: Dictionary, p: Vector2) -> Vector2:
	var pts: Array = border.points
	var best_d := INF
	var best_dir := Vector2(1.0, 0.0)
	for i in range(pts.size() - 1):
		var a: Vector2 = pts[i]
		var b: Vector2 = pts[i + 1]
		var seg: Vector2 = b - a
		var len_sq: float = seg.length_squared()
		if len_sq < 0.0001:
			continue
		var t: float = clamp((p - a).dot(seg) / len_sq, 0.0, 1.0)
		var proj: Vector2 = a + seg * t
		var d: float = p.distance_to(proj)
		if d < best_d:
			best_d = d
			best_dir = seg.normalized()
	return best_dir


# Orients a border piece so its "long" local X axis runs along the border
# direction and its local Z (thickness) axis runs across it. Border segments
# and crossings were previously placed with an identity basis, so a piece on
# a north-south border stretch presented its thin edge along the path instead
# of its long face, which is what actually caused the dashed/hatch-mark look.
func _border_basis(dir2: Vector2) -> Basis:
	var dir3 := Vector3(dir2.x, 0.0, dir2.y)
	return Basis(dir3, Vector3.UP, Vector3(-dir3.z, 0.0, dir3.x))


func _ground_offset(mesh: Mesh) -> float:
	if mesh == null:
		return 0.0
	return -mesh.get_aabb().position.y


func _wh(size: Array, default_w: float = 100.0, default_h: float = 100.0) -> Vector2:
	var w := default_w
	var h := default_h
	if size.size() >= 1:
		w = float(size[0])
	if size.size() >= 2:
		h = float(size[1])
	return Vector2(w, h)


func _stack(parts: Array) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var y := 0.0
	for part in parts:
		var m: Mesh = part[0]
		var h: float = part[1]
		st.append_from(m, 0, Transform3D(Basis(), Vector3(0.0, y + h * 0.5, 0.0)))
		y += h
	return st.commit()


func _long_box(size: Array, default_w: float, default_h: float) -> Mesh:
	var wh := _wh(size, default_w, default_h)
	var m := BoxMesh.new()
	m.size = Vector3(wh.x, wh.y, WALL_THICKNESS_WU)
	return m


func _arch(size: Array, default_w: float, default_h: float) -> Mesh:
	var wh := _wh(size, default_w, default_h)
	var pillar_w := wh.x * 0.2
	var gap := wh.x * 0.6
	var pillar := BoxMesh.new()
	pillar.size = Vector3(pillar_w, wh.y, WALL_THICKNESS_WU)
	var lintel := BoxMesh.new()
	lintel.size = Vector3(wh.x, wh.y * 0.25, WALL_THICKNESS_WU)
	var side_x := (gap + pillar_w) * 0.5
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	st.append_from(pillar, 0, Transform3D(Basis(), Vector3(-side_x, wh.y * 0.5, 0.0)))
	st.append_from(pillar, 0, Transform3D(Basis(), Vector3(side_x, wh.y * 0.5, 0.0)))
	st.append_from(lintel, 0, Transform3D(Basis(), Vector3(0.0, wh.y * 0.875, 0.0)))
	return st.commit()


func _mesh_magenta_placeholder(size: Array) -> Mesh:
	var wh := _wh(size, 80.0, 80.0)
	var m := BoxMesh.new()
	m.size = Vector3(wh.x, wh.y, wh.x)
	return m


func _mesh_box(size: Array) -> Mesh:
	var wh := _wh(size)
	var m := BoxMesh.new()
	m.size = Vector3(wh.x, wh.y, wh.x)
	return m


func _mesh_box_gable(size: Array) -> Mesh:
	var wh := _wh(size)
	var base_h := wh.y * 0.65
	var roof_h := wh.y * 0.35
	var base := BoxMesh.new()
	base.size = Vector3(wh.x, base_h, wh.x)
	var roof := PrismMesh.new()
	roof.size = Vector3(wh.x, roof_h, wh.x)
	return _stack([[base, base_h], [roof, roof_h]])


func _mesh_prism(size: Array) -> Mesh:
	var wh := _wh(size, 120.0, 200.0)
	var m := PrismMesh.new()
	m.size = Vector3(wh.x, wh.y, wh.x)
	return m


func _mesh_cone_on_stick(size: Array) -> Mesh:
	var wh := _wh(size, 60.0, 110.0)
	var trunk_h := wh.y * 0.4
	var cone_h := wh.y * 0.6
	var trunk := CylinderMesh.new()
	trunk.top_radius = wh.x * 0.08
	trunk.bottom_radius = wh.x * 0.08
	trunk.height = trunk_h
	var cone := CylinderMesh.new()
	cone.top_radius = 0.0
	cone.bottom_radius = wh.x * 0.45
	cone.height = cone_h
	return _stack([[trunk, trunk_h], [cone, cone_h]])


func _mesh_flat_box(size: Array) -> Mesh:
	var wh := _wh(size, 200.0, 60.0)
	var m := BoxMesh.new()
	m.size = Vector3(wh.x, FLAT_THICKNESS_WU, wh.y)
	return m


func _mesh_colonnade(size: Array) -> Mesh:
	var wh := _wh(size, 240.0, 140.0)
	var base_h := wh.y * 0.08
	var col_h := wh.y * 0.8
	var lintel_h := wh.y * 0.12
	var base := BoxMesh.new()
	base.size = Vector3(wh.x, base_h, wh.x * 0.4)
	var column := CylinderMesh.new()
	column.top_radius = wh.x * 0.04
	column.bottom_radius = wh.x * 0.04
	column.height = col_h
	var lintel := BoxMesh.new()
	lintel.size = Vector3(wh.x, lintel_h, wh.x * 0.3)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	st.append_from(base, 0, Transform3D(Basis(), Vector3(0.0, base_h * 0.5, 0.0)))
	var n_columns := 5
	for i in range(n_columns):
		var x := (float(i) / float(n_columns - 1) - 0.5) * wh.x * 0.9
		st.append_from(column, 0, Transform3D(Basis(), Vector3(x, base_h + col_h * 0.5, 0.0)))
	st.append_from(lintel, 0, Transform3D(Basis(), Vector3(0.0, base_h + col_h + lintel_h * 0.5, 0.0)))
	return st.commit()


func _mesh_wall_segment(size: Array) -> Mesh:
	return _long_box(size, 150.0, 90.0)


func _mesh_gate_arch(size: Array) -> Mesh:
	return _arch(size, 90.0, 90.0)


func _mesh_bridge_arches(size: Array) -> Mesh:
	return _long_box(size, 150.0, 40.0)


func _mesh_cliff_face(size: Array) -> Mesh:
	var wh := _wh(size, 150.0, DEFAULT_BORDER_HEIGHT_WU)
	if wh.y <= 0.0:
		wh.y = DEFAULT_BORDER_HEIGHT_WU
	var m := BoxMesh.new()
	m.size = Vector3(wh.x, wh.y, WALL_THICKNESS_WU * 2.0)
	return m


func _mesh_stair_ramp(size: Array) -> Mesh:
	var wh := _wh(size, 150.0, DEFAULT_BORDER_HEIGHT_WU)
	if wh.y <= 0.0:
		wh.y = DEFAULT_BORDER_HEIGHT_WU
	var m := BoxMesh.new()
	m.size = Vector3(wh.x, wh.y, wh.x * 0.6)
	return m


func _mesh_acropolis(size: Array) -> Mesh:
	var wh := _wh(size, 240.0, 140.0)
	var tier_h := wh.y / 3.0
	var t1 := BoxMesh.new()
	t1.size = Vector3(wh.x, tier_h, wh.x)
	var t2 := BoxMesh.new()
	t2.size = Vector3(wh.x * 0.7, tier_h, wh.x * 0.7)
	var t3 := BoxMesh.new()
	t3.size = Vector3(wh.x * 0.45, tier_h, wh.x * 0.45)
	return _stack([[t1, tier_h], [t2, tier_h], [t3, tier_h]])


func _mesh_camp_ring(size: Array) -> Mesh:
	var wh := _wh(size, 300.0, 400.0)
	var m := TorusMesh.new()
	m.inner_radius = wh.x * 0.25
	m.outer_radius = wh.x * 0.4
	return m


func _mesh_mountain_range(size: Array) -> Mesh:
	var wh := _wh(size, DEFAULT_BACKDROP_SIZE[0], DEFAULT_BACKDROP_SIZE[1])
	var peak_a := PrismMesh.new()
	peak_a.size = Vector3(wh.x * 0.5, wh.y, wh.x * 0.5)
	var peak_b := PrismMesh.new()
	peak_b.size = Vector3(wh.x * 0.7, wh.y * 1.3, wh.x * 0.6)
	var peak_c := PrismMesh.new()
	peak_c.size = Vector3(wh.x * 0.5, wh.y * 0.8, wh.x * 0.5)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	st.append_from(peak_a, 0, Transform3D(Basis(), Vector3(-wh.x * 0.5, wh.y * 0.5, 0.0)))
	st.append_from(peak_b, 0, Transform3D(Basis(), Vector3(0.0, wh.y * 0.65, 0.0)))
	st.append_from(peak_c, 0, Transform3D(Basis(), Vector3(wh.x * 0.5, wh.y * 0.4, 0.0)))
	return st.commit()


func _mesh_hab_pod(size: Array) -> Mesh:
	var wh := _wh(size, 60.0, 40.0)
	var m := CapsuleMesh.new()
	m.radius = wh.x * 0.4
	m.height = max(wh.y, m.radius * 2.0 + 1.0)
	return m


func _mesh_hab_ring(size: Array) -> Mesh:
	var wh := _wh(size, 80.0, 60.0)
	var m := TorusMesh.new()
	m.inner_radius = wh.x * 0.3
	m.outer_radius = wh.x * 0.5
	return m


func _mesh_spire(size: Array) -> Mesh:
	var wh := _wh(size, 240.0, 140.0)
	var m := CylinderMesh.new()
	m.top_radius = 0.0
	m.bottom_radius = wh.x * 0.2
	m.height = wh.y
	return m


func _mesh_hull_segment(size: Array) -> Mesh:
	return _long_box(size, 150.0, 90.0)


func _mesh_airlock(size: Array) -> Mesh:
	return _arch(size, 90.0, 90.0)


func _mesh_docking_spine(size: Array) -> Mesh:
	return _long_box(size, 150.0, 40.0)


func _mesh_ore_chunk(size: Array) -> Mesh:
	var wh := _wh(size, 120.0, 200.0)
	var m := PrismMesh.new()
	m.size = Vector3(wh.x, wh.y, wh.x)
	m.left_to_right = 0.3
	return m


func _mesh_derelict(size: Array) -> Mesh:
	var wh := _wh(size, 60.0, 110.0)
	var m := BoxMesh.new()
	m.size = Vector3(wh.x * 2.0, wh.y * 0.5, wh.x * 0.6)
	return m


func _mesh_ice_shard(size: Array) -> Mesh:
	var wh := _wh(size, 60.0, 110.0)
	var m := PrismMesh.new()
	m.size = Vector3(wh.x * 0.4, wh.y, wh.x * 0.4)
	return m


func _mesh_asteroid_backdrop(size: Array) -> Mesh:
	var wh := _wh(size, DEFAULT_BACKDROP_SIZE[0], DEFAULT_BACKDROP_SIZE[1])
	var a := SphereMesh.new()
	a.radius = wh.x * 0.3
	a.height = wh.x * 0.6
	var b := SphereMesh.new()
	b.radius = wh.x * 0.2
	b.height = wh.x * 0.4
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	st.append_from(a, 0, Transform3D(Basis(), Vector3(-wh.x * 0.2, wh.x * 0.3, 0.0)))
	st.append_from(b, 0, Transform3D(Basis(), Vector3(wh.x * 0.3, wh.x * 0.2, wh.x * 0.2)))
	return st.commit()

extends Node3D

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")

const TUBE_SIDES := 8
const CURVE_SEGMENTS := 16
const ARC_HEIGHT_FRACTION := 0.15
const FILAMENT_WIDTH_BORDER := 0.075
const FILAMENT_WIDTH_TRADE := 0.035
const POINT_BASE_RADIUS := 1.4
const NEUTRAL_COLOR := Color(0.55, 0.55, 0.58, 1.0)
const TRADE_DIM := Color(0.42, 0.44, 0.5, 0.5)
const FLASH_DURATION := 0.6
const LOCAL_FAR_WU := 30.0

var _galaxy: Galaxy
var _points: MultiMeshInstance3D
var _filaments: Node3D
var _names: Node3D
var _flash_boost: Dictionary = {}
var _flash_rings: Array = []
# Mirrors each point's last-set colour outside the MultiMesh's own buffer:
# MultiMesh.get_instance_color() reads back zeroed data under the headless
# dummy renderer verify.gd runs under, so verify reads this array instead.
var _point_colors: Array = []


func _ready() -> void:
	_build_ambient()


func build(galaxy: Galaxy) -> void:
	_galaxy = galaxy
	_flash_boost.clear()
	for r in _flash_rings:
		r.node.free()
	_flash_rings.clear()
	_build_points()
	_build_filaments()
	_build_names()
	update_view(50.0, -1, -1, -1)


func get_galaxy() -> Galaxy:
	return _galaxy


func get_point_color(system_id: int) -> Color:
	if system_id < 0 or system_id >= _point_colors.size():
		return Color.BLACK
	return _point_colors[system_id]


func owner_color(owner_id: int, galaxy: Galaxy) -> Color:
	if owner_id == -1 or galaxy == null:
		return NEUTRAL_COLOR
	for f in galaxy.factions:
		if f.id == owner_id:
			var v := 0.95 if owner_id == 0 else 0.85
			return Color.from_hsv(f.hue, 0.65, v, 1.0)
	return NEUTRAL_COLOR


func _build_points() -> void:
	if _points:
		_points.free()
	_points = MultiMeshInstance3D.new()
	_points.name = "Points"
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	var sphere := SphereMesh.new()
	sphere.radius = POINT_BASE_RADIUS
	sphere.height = POINT_BASE_RADIUS * 2.0
	sphere.radial_segments = 12
	sphere.rings = 8
	mm.mesh = sphere
	mm.instance_count = _galaxy.systems.size()
	_point_colors.resize(_galaxy.systems.size())
	_point_colors.fill(Color.BLACK)
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.vertex_color_use_as_albedo = true
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_points.material_override = mat
	_points.multimesh = mm
	add_child(_points)


func _build_filaments() -> void:
	if _filaments:
		_filaments.free()
	_filaments = Node3D.new()
	_filaments.name = "Filaments"
	add_child(_filaments)

	if QaPlants.is_active("edges-2d-overlay"):
		_build_filaments_2d_fault()
		return

	for e in _galaxy.edges:
		_build_one_filament(e)


func _build_one_filament(e: Dictionary) -> void:
	var from_pos: Vector3 = _galaxy.systems[e.a].pos
	var to_pos: Vector3 = _galaxy.systems[e.b].pos
	var is_border: bool = e.kind == "border"
	var width: float = FILAMENT_WIDTH_BORDER if is_border else FILAMENT_WIDTH_TRADE
	var mi := MeshInstance3D.new()
	mi.name = "E_%d_%d" % [e.a, e.b]
	mi.mesh = _build_tube(_bezier_arc(from_pos, to_pos), width)
	mi.set_meta("edge", e)
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.albedo_color = owner_color(_galaxy.systems[e.a].owner, _galaxy) if is_border else TRADE_DIM
	mi.material_override = mat
	_filaments.add_child(mi)


# fault: edges-2d-overlay draws lanes in a full-rect Control's _draw() under HUD
# instead of Node3D tubes here; Filaments stays empty so EDGES-8 can tell them apart.
func _build_filaments_2d_fault() -> void:
	var hud := get_node("../../HUD")
	var existing := hud.get_node_or_null("FilamentOverlay2D")
	if existing:
		existing.free()
	var overlay := Control.new()
	overlay.name = "FilamentOverlay2D"
	overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud.add_child(overlay)


func _bezier_arc(from_pos: Vector3, to_pos: Vector3) -> PackedVector3Array:
	var mid := (from_pos + to_pos) * 0.5
	var dist := from_pos.distance_to(to_pos)
	var arc_height := dist * ARC_HEIGHT_FRACTION
	var dir := (to_pos - from_pos).normalized()
	var up := Vector3.UP
	if absf(dir.dot(up)) > 0.95:
		up = Vector3.RIGHT
	var perp := dir.cross(up).normalized()
	var hash_val := from_pos.x * 73.0 + from_pos.z * 137.0 + to_pos.x * 97.0 + to_pos.z * 53.0
	var perp_offset := sin(hash_val) * arc_height * 0.5
	var cp1 := from_pos.lerp(mid, 0.5) + Vector3(0, arc_height, 0) + perp * perp_offset
	var cp2 := mid.lerp(to_pos, 0.5) + Vector3(0, arc_height, 0) + perp * perp_offset
	var points := PackedVector3Array()
	for i in range(CURVE_SEGMENTS + 1):
		var t := float(i) / float(CURVE_SEGMENTS)
		var it := 1.0 - t
		points.append(it * it * it * from_pos + 3.0 * it * it * t * cp1 + 3.0 * it * t * t * cp2 + t * t * t * to_pos)
	return points


func _build_tube(curve: PackedVector3Array, radius: float) -> ArrayMesh:
	var mesh := ArrayMesh.new()
	var verts := PackedVector3Array()
	var indices := PackedInt32Array()
	if curve.size() < 2:
		return mesh
	for i in range(curve.size()):
		var pos := curve[i]
		var tangent: Vector3
		if i == 0:
			tangent = (curve[1] - curve[0]).normalized()
		elif i == curve.size() - 1:
			tangent = (curve[i] - curve[i - 1]).normalized()
		else:
			tangent = (curve[i + 1] - curve[i - 1]).normalized()
		var up := Vector3.UP
		if absf(tangent.dot(up)) > 0.95:
			up = Vector3.RIGHT
		var right := tangent.cross(up).normalized()
		var actual_up := right.cross(tangent).normalized()
		for j in range(TUBE_SIDES + 1):
			var angle := float(j) / float(TUBE_SIDES) * TAU
			verts.append(pos + right * cos(angle) * radius + actual_up * sin(angle) * radius)
	var verts_per_ring := TUBE_SIDES + 1
	for i in range(curve.size() - 1):
		for j in range(TUBE_SIDES):
			var curr := i * verts_per_ring + j
			var next := curr + verts_per_ring
			indices.append(curr)
			indices.append(next)
			indices.append(curr + 1)
			indices.append(curr + 1)
			indices.append(next)
			indices.append(next + 1)
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_INDEX] = indices
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return mesh


func _build_names() -> void:
	if _names:
		_names.free()
	_names = Node3D.new()
	_names.name = "Names"
	add_child(_names)
	for f in _galaxy.factions:
		var sum := Vector3.ZERO
		var n := 0
		for sys in _galaxy.systems:
			if sys.owner == f.id:
				sum += sys.pos
				n += 1
		if n == 0:
			continue
		var label := Label3D.new()
		label.name = "Name_%d" % f.id
		label.text = f.name
		label.position = sum / float(n) + Vector3(0, 6, 0)
		label.modulate = owner_color(f.id, _galaxy)
		label.font_size = 40
		# default pixel_size (0.01) renders 40px text ~0.4wu tall, invisible
		# against a ~100wu-radius galaxy; scale it up to read at Overview range.
		label.pixel_size = 0.05
		label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		label.no_depth_test = true
		label.modulate.a = 0.0
		_names.add_child(label)


func _build_ambient() -> void:
	# Pass 1's own dust/star/grid quads are superseded by the legacy rig below
	# (settled_reach_renderer.gd), which already carries its own ambient dust,
	# starfield, and polar grid alongside the rings and central glow.
	var ambient := Node3D.new()
	ambient.name = "Ambient"
	ambient.set_script(load("res://scenes/mockups/galaxy/legacy_ambient_rig.gd"))
	add_child(ambient)


func _band_weights(d: float) -> Dictionary:
	var w_local := 0.0
	var w_regional := 0.0
	var w_overview := 0.0
	if d <= 25.0:
		w_local = 1.0
	elif d < 40.0:
		var t := (d - 25.0) / 15.0
		w_local = 1.0 - t
		w_regional = t
	elif d <= 65.0:
		w_regional = 1.0
	elif d < 75.0:
		var t2 := (d - 65.0) / 10.0
		w_regional = 1.0 - t2
		w_overview = t2
	else:
		w_overview = 1.0
	return {"local": w_local, "regional": w_regional, "overview": w_overview}


func _faction_emphasis(owner: int, hover_faction: int, pin_faction: int) -> float:
	if pin_faction != -1:
		return 1.0 if owner == pin_faction else 0.05
	if hover_faction != -1:
		return 1.3 if owner == hover_faction else 0.25
	return 1.0


func _flash_scale(system_id: int) -> float:
	if not _flash_boost.has(system_id):
		return 1.0
	var t: float = _flash_boost[system_id] / FLASH_DURATION
	return lerpf(1.0, 3.0, sin(clampf(t, 0.0, 1.0) * PI))


func update_view(distance: float, focused_id: int, hover_faction: int, pin_faction: int) -> void:
	if _galaxy == null or _points == null:
		return
	var w := _band_weights(distance)
	var point_scale_band: float = lerpf(1.0, 0.6, w.overview)
	var filament_alpha_band: float = lerpf(1.0, 0.4, w.overview)
	var name_alpha: float = w.overview

	for i in range(_galaxy.systems.size()):
		var sys: Dictionary = _galaxy.systems[i]
		var emph := _faction_emphasis(sys.owner, hover_faction, pin_faction)
		var local_boost := 1.0
		var sat_mul := 1.0
		if focused_id != -1 and w.local > 0.0:
			if sys.id == focused_id:
				local_boost = lerpf(1.0, 1.5, w.local)
			else:
				var d: float = sys.pos.distance_to(_galaxy.systems[focused_id].pos)
				if d > LOCAL_FAR_WU:
					sat_mul = lerpf(1.0, 0.3, w.local)
		var scale: float = (0.6 + 1.4 * float(sys.significance)) * point_scale_band * local_boost * _flash_scale(sys.id)
		_points.multimesh.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * scale), sys.pos))
		var base_color: Color = Color.WHITE if QaPlants.is_active("owner-colour-flat") else owner_color(sys.owner, _galaxy)
		var c := Color(base_color.r * emph, base_color.g * emph, base_color.b * emph, base_color.a)
		if sat_mul < 1.0:
			c = c.lerp(Color(0.5, 0.5, 0.5, c.a), 1.0 - sat_mul)
		_points.multimesh.set_instance_color(i, c)
		_point_colors[i] = c

	for child in _filaments.get_children():
		if not child.has_meta("edge"):
			continue
		var e: Dictionary = child.get_meta("edge")
		var is_border: bool = e.kind == "border"
		var owner_a: int = _galaxy.systems[e.a].owner
		var emph := _faction_emphasis(owner_a if is_border else -1, hover_faction, pin_faction)
		var mat: StandardMaterial3D = child.material_override
		mat.albedo_color.a = clampf(filament_alpha_band * (1.0 if is_border else 0.7) * emph, 0.0, 1.0)

	if _names:
		for label in _names.get_children():
			label.modulate.a = name_alpha
			# Label3D's outline has its own alpha, separate from modulate; left
			# opaque it stays a fully readable dark silhouette even at alpha 0.
			label.outline_modulate.a = name_alpha


func flash(system_id: int, color: Color) -> void:
	if _galaxy == null or system_id < 0 or system_id >= _galaxy.systems.size():
		return
	_flash_boost[system_id] = 0.0
	var ring := MeshInstance3D.new()
	var quad := QuadMesh.new()
	quad.size = Vector2(3.0, 3.0)
	ring.mesh = quad
	ring.position = _galaxy.systems[system_id].pos
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_color = color
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	ring.material_override = mat
	add_child(ring)
	_flash_rings.append({"node": ring, "mat": mat, "t": 0.0})


func _process(delta: float) -> void:
	for id in _flash_boost.keys():
		var t: float = _flash_boost[id] + delta
		if t >= FLASH_DURATION:
			_flash_boost.erase(id)
		else:
			_flash_boost[id] = t
	var done: Array = []
	for r in _flash_rings:
		r.t += delta
		var t: float = r.t / FLASH_DURATION
		if t >= 1.0:
			r.node.free()
			done.append(r)
			continue
		r.node.scale = Vector3.ONE * lerpf(1.0, 8.0, t)
		r.mat.albedo_color.a = 1.0 - t
	for r in done:
		_flash_rings.erase(r)


func set_system_owner(system_id: int, faction_id: int) -> void:
	if _galaxy == null or system_id < 0 or system_id >= _galaxy.systems.size():
		return
	_galaxy.systems[system_id].owner = faction_id
	for child in _filaments.get_children():
		if not child.has_meta("edge"):
			continue
		var e: Dictionary = child.get_meta("edge")
		if e.a != system_id and e.b != system_id:
			continue
		var oa: int = _galaxy.systems[e.a].owner
		var ob: int = _galaxy.systems[e.b].owner
		e.kind = "border" if (oa == ob and oa != -1) else "trade"
		var is_border: bool = e.kind == "border"
		child.mesh = _build_tube(_bezier_arc(_galaxy.systems[e.a].pos, _galaxy.systems[e.b].pos), FILAMENT_WIDTH_BORDER if is_border else FILAMENT_WIDTH_TRADE)
		var mat: StandardMaterial3D = child.material_override
		mat.albedo_color = owner_color(oa, _galaxy) if is_border else TRADE_DIM

class_name LayerView
extends Node3D

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")

const LAYER_HEIGHT := 600.0
const LAYER_COLORS: Array[Color] = [Color(0.20, 0.90, 1.00), Color(1.00, 0.55, 0.15)]
const DIM_ALPHA := 0.4
const UNIT_HALF_EXTENT := 40.0
const RING_OUTER := 55.0
const RING_INNER := 48.0
const SELECTION_OUTER := 68.0
const SELECTION_INNER := 62.0
const SENSOR_TUBE := 6.0

var sim: ToySim
var focus_layer: int = 1
var selected_uid: int = -1

var _unit_nodes: Dictionary = {}
var _plane1: MeshInstance3D
var _plane2: MeshInstance3D
var _blocked_patch: MeshInstance3D
var _obstacle: MeshInstance3D
var _sensor_own: MeshInstance3D
var _sensor_other: MeshInstance3D
var _selection_ring: MeshInstance3D


func setup(p_sim: ToySim) -> void:
	sim = p_sim
	_build_ground()
	_build_obstacle()
	_build_blocked_patch()
	_build_sensor_rings()
	_build_selection_ring()


func set_focus_layer(n: int) -> void:
	focus_layer = n


func set_selected(uid: int) -> void:
	selected_uid = uid


func unit_height(u: Dictionary) -> float:
	if QaPlants.is_active("wrong-height"):
		return 0.0
	if u.transition != null:
		var tr: Dictionary = u.transition
		var t: float = 1.0 - float(tr.ticks_left) / float(tr.duration)
		var from_y: float = float(tr.from - 1) * LAYER_HEIGHT
		var to_y: float = float(tr.to - 1) * LAYER_HEIGHT
		return lerp(from_y, to_y, t)
	return float(u.layer - 1) * LAYER_HEIGHT


func ring_color(u: Dictionary) -> Color:
	if QaPlants.is_active("ring-colour-same"):
		return LAYER_COLORS[0]
	return LAYER_COLORS[clampi(u.layer - 1, 0, LAYER_COLORS.size() - 1)]


func layer_alpha(layer: int) -> float:
	if QaPlants.is_active("no-dimming"):
		return 1.0
	return 1.0 if layer == focus_layer else DIM_ALPHA


func get_unit_body(uid: int) -> MeshInstance3D:
	var e: Dictionary = _unit_nodes.get(uid, {})
	return e.get("body")


func get_unit_ring(uid: int) -> MeshInstance3D:
	var e: Dictionary = _unit_nodes.get(uid, {})
	return e.get("ring")


func refresh() -> void:
	if sim == null:
		return
	_update_ground_dim()
	_update_units()
	_update_sensor_rings()
	_update_selection_ring()


func _build_ground() -> void:
	var size: float = sim.canvas_wu if sim != null else 4000.0

	var mesh1 := PlaneMesh.new()
	mesh1.size = Vector2(size, size)
	_plane1 = MeshInstance3D.new()
	_plane1.name = "GroundLayer1"
	_plane1.mesh = mesh1
	_plane1.position = Vector3(size * 0.5, 0.0, size * 0.5)
	var mat1 := StandardMaterial3D.new()
	mat1.albedo_color = Color(0.16, 0.18, 0.22, 1.0)
	mat1.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_plane1.material_override = mat1
	add_child(_plane1)

	var mesh2 := PlaneMesh.new()
	mesh2.size = Vector2(size, size)
	_plane2 = MeshInstance3D.new()
	_plane2.name = "GroundLayer2"
	_plane2.mesh = mesh2
	_plane2.position = Vector3(size * 0.5, LAYER_HEIGHT, size * 0.5)
	var mat2 := StandardMaterial3D.new()
	mat2.albedo_color = Color(0.35, 0.55, 0.70, 0.25)
	mat2.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_plane2.material_override = mat2
	add_child(_plane2)


func _build_obstacle() -> void:
	var mesh := BoxMesh.new()
	mesh.size = Vector3(sim.obstacle_size.x, LAYER_HEIGHT * 1.6, sim.obstacle_size.y)
	_obstacle = MeshInstance3D.new()
	_obstacle.name = "Obstacle"
	_obstacle.mesh = mesh
	_obstacle.position = Vector3(sim.obstacle_pos.x, LAYER_HEIGHT * 0.8, sim.obstacle_pos.y)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.45, 0.40, 0.35, 1.0)
	_obstacle.material_override = mat
	add_child(_obstacle)


func _build_blocked_patch() -> void:
	var mesh := PlaneMesh.new()
	var side: float = sim.blocked_radius * 2.0
	mesh.size = Vector2(side, side)
	_blocked_patch = MeshInstance3D.new()
	_blocked_patch.name = "BlockedPatchLayer2"
	_blocked_patch.mesh = mesh
	_blocked_patch.position = Vector3(sim.blocked_center.x, LAYER_HEIGHT + 1.0, sim.blocked_center.y)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.85, 0.20, 0.20, 0.45)
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_blocked_patch.material_override = mat
	add_child(_blocked_patch)


func _build_sensor_rings() -> void:
	_sensor_own = _make_ring_node("SensorOwn", Color(0.9, 0.9, 0.9, 0.7))
	add_child(_sensor_own)
	_sensor_other = _make_ring_node("SensorOther", Color(0.9, 0.9, 0.9, 0.5))
	add_child(_sensor_other)


func _build_selection_ring() -> void:
	_selection_ring = _make_ring_node("SelectionRing", Color(1.0, 1.0, 1.0, 0.9))
	add_child(_selection_ring)


func _make_ring_node(node_name: String, color: Color) -> MeshInstance3D:
	var torus := TorusMesh.new()
	torus.inner_radius = RING_INNER
	torus.outer_radius = RING_OUTER
	var mi := MeshInstance3D.new()
	mi.name = node_name
	mi.mesh = torus
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.emission_enabled = true
	mat.emission = color
	mi.material_override = mat
	mi.visible = false
	return mi


func _update_ground_dim() -> void:
	(_plane1.material_override as StandardMaterial3D).albedo_color.a = layer_alpha(1)
	var base_a: float = 0.25
	(_plane2.material_override as StandardMaterial3D).albedo_color.a = base_a * layer_alpha(2)


func _update_units() -> void:
	if sim == null:
		return
	var visible_enemies: Array = sim.visible_enemy_uids()
	var seen_uids := {}
	for uid in sim.units.keys():
		seen_uids[uid] = true
		var u: Dictionary = sim.units[uid]
		if u.faction == 1 and not visible_enemies.has(uid):
			if _unit_nodes.has(uid):
				_unit_nodes[uid].body.visible = false
				_unit_nodes[uid].ring.visible = false
			continue
		if not _unit_nodes.has(uid):
			_spawn_unit_node(uid, u)
		var entry: Dictionary = _unit_nodes[uid]
		var body: MeshInstance3D = entry.body
		var ring: MeshInstance3D = entry.ring
		body.visible = true
		ring.visible = true
		var h := unit_height(u)
		body.position = Vector3(u.pos.x, h + UNIT_HALF_EXTENT, u.pos.y)
		ring.position = Vector3(u.pos.x, h + 2.0, u.pos.y)
		var body_mat: StandardMaterial3D = body.material_override
		var ring_mat: StandardMaterial3D = ring.material_override
		body_mat.albedo_color.a = layer_alpha(u.layer)
		ring_mat.albedo_color.a = layer_alpha(u.layer)
		var rc := ring_color(u)
		ring_mat.albedo_color = Color(rc.r, rc.g, rc.b, ring_mat.albedo_color.a)
		ring_mat.emission = rc

	for uid in _unit_nodes.keys():
		if not seen_uids.has(uid):
			_unit_nodes[uid].body.visible = false
			_unit_nodes[uid].ring.visible = false


func _spawn_unit_node(uid: int, u: Dictionary) -> void:
	var mesh := BoxMesh.new()
	mesh.size = Vector3(UNIT_HALF_EXTENT * 2.0, UNIT_HALF_EXTENT * 2.0, UNIT_HALF_EXTENT * 2.0)
	var body := MeshInstance3D.new()
	body.name = "Unit_%d" % uid
	body.mesh = mesh
	var body_mat := StandardMaterial3D.new()
	body_mat.albedo_color = Color("#4099FF") if u.faction == 0 else Color("#FF4738")
	body_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	body.material_override = body_mat
	add_child(body)

	var ring := _make_ring_node("Ring_%d" % uid, ring_color(u))
	ring.visible = true
	add_child(ring)

	_unit_nodes[uid] = {"body": body, "ring": ring}


func _update_sensor_rings() -> void:
	if selected_uid < 0 or not sim.units.has(selected_uid):
		_sensor_own.visible = false
		_sensor_other.visible = false
		return
	var u: Dictionary = sim.units[selected_uid]
	var h := unit_height(u)
	var other_layer: int = 2 if u.layer == 1 else 1
	var other_h: float = float(other_layer - 1) * LAYER_HEIGHT

	_sensor_own.visible = true
	_scale_ring(_sensor_own, u.sensor_wu)
	_sensor_own.position = Vector3(u.pos.x, h + 3.0, u.pos.y)

	_sensor_other.visible = true
	_scale_ring(_sensor_other, u.sensor_wu * 0.5)
	_sensor_other.position = Vector3(u.pos.x, other_h + 3.0, u.pos.y)


func _scale_ring(node: MeshInstance3D, radius_wu: float) -> void:
	var scale_factor: float = radius_wu / RING_OUTER
	node.scale = Vector3(scale_factor, 1.0, scale_factor)


func _update_selection_ring() -> void:
	if selected_uid < 0 or not sim.units.has(selected_uid):
		_selection_ring.visible = false
		return
	var u: Dictionary = sim.units[selected_uid]
	var h := unit_height(u)
	_selection_ring.visible = true
	_selection_ring.position = Vector3(u.pos.x, h + 4.0, u.pos.y)

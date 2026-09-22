class_name LayerView
extends Node3D

const LAYER_HEIGHT := 600.0
const LAYER_COLORS: Array[Color] = [Color(1, 1, 1), Color(1, 1, 1)]
const UNIT_HALF_EXTENT := 40.0

var sim: ToySim
var focus_layer: int = 1
var selected_uid: int = -1

var _dummy_bodies: Dictionary = {}
var _dummy_rings: Dictionary = {}


func setup(p_sim: ToySim) -> void:
	sim = p_sim


func set_focus_layer(n: int) -> void:
	focus_layer = n


func set_selected(uid: int) -> void:
	selected_uid = uid


func unit_height(u: Dictionary) -> float:
	return 0.0


func ring_color(u: Dictionary) -> Color:
	return Color(1, 1, 1)


func layer_alpha(layer: int) -> float:
	return 1.0


func _dummy_mesh_instance() -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var mat := StandardMaterial3D.new()
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mi.material_override = mat
	return mi


func get_unit_body(uid: int) -> MeshInstance3D:
	if not _dummy_bodies.has(uid):
		_dummy_bodies[uid] = _dummy_mesh_instance()
	return _dummy_bodies[uid]


func get_unit_ring(uid: int) -> MeshInstance3D:
	if not _dummy_rings.has(uid):
		_dummy_rings[uid] = _dummy_mesh_instance()
	return _dummy_rings[uid]


func refresh() -> void:
	pass

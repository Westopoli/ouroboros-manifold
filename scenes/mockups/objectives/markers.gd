class_name Marker
extends Node3D

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")

const BEAM_HEIGHT := 800.0
const BEAM_SIZE := 16.0
const ROUTE_BOX := Vector3(40, 20, 40)
const SCATTER_BOX := Vector3(70, 70, 70)
const RING_RADIUS := {"hold_zone": 600.0, "survive_duration": 400.0, "eliminate_force": 500.0}
const KIND_COLORS := {
	"hold_zone": Color(0.3, 0.85, 1.0),
	"destroy_targets": Color(1.0, 0.55, 0.2),
	"escort_to_extraction": Color(0.55, 0.95, 0.4),
	"survive_duration": Color(0.85, 0.4, 1.0),
	"eliminate_force": Color(1.0, 0.28, 0.28),
}

static var _material_cache: Dictionary = {}
static var _mesh_cache: Dictionary = {}
static var _font: FontFile = load("res://theme/fonts/JetBrainsMono-Bold.ttf")
static var _beam_mesh: BoxMesh
static var _route_mesh: BoxMesh
static var _scatter_mesh: BoxMesh

var label: Label3D
var _kind := ""
var _boxes: Array = []


static func _mat_for(col: Color, alpha_blend: bool) -> StandardMaterial3D:
	var key := "%s|%s" % [col, alpha_blend]
	if _material_cache.has(key):
		return _material_cache[key]
	var mat := StandardMaterial3D.new()
	mat.albedo_color = col
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	if alpha_blend:
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_material_cache[key] = mat
	return mat


static func _box_mesh(size: Vector3) -> BoxMesh:
	var key := "%s" % [size]
	if _mesh_cache.has(key):
		return _mesh_cache[key]
	var box := BoxMesh.new()
	box.size = size
	_mesh_cache[key] = box
	return box


static func _ring_mesh(radius: float) -> TorusMesh:
	var key := "ring%.1f" % radius
	if _mesh_cache.has(key):
		return _mesh_cache[key]
	var torus := TorusMesh.new()
	torus.inner_radius = radius - 8.0
	torus.outer_radius = radius
	torus.rings = 48
	torus.ring_segments = 48
	_mesh_cache[key] = torus
	return torus


func setup(mission: Dictionary, display_name: String) -> void:
	_kind = mission.kind
	var col: Color = KIND_COLORS.get(_kind, Color.WHITE)
	var wp := Vector3(mission.pos.x, 0.0, mission.pos.y)
	_add_beam(wp, col)
	_add_label(wp, display_name, col)
	_add_glyph(wp, col)
	if RING_RADIUS.has(_kind):
		_add_ring(wp, RING_RADIUS[_kind], col)
	if mission.extra.has("targets"):
		_add_scatter(mission.extra.targets, col)
	elif mission.extra.has("enemies"):
		_add_scatter(mission.extra.enemies, col)
	if mission.extra.has("route"):
		_add_route(mission.extra.route, col)


func refresh(mission: Dictionary) -> void:
	var items: Array = []
	if mission.extra.has("targets"):
		items = mission.extra.targets
	elif mission.extra.has("enemies"):
		items = mission.extra.enemies
	for i in range(min(items.size(), _boxes.size())):
		var b: Dictionary = _boxes[i]
		b.mat.albedo_color = Color(0.12, 0.12, 0.12) if items[i].destroyed else b.color


func _add_beam(wp: Vector3, col: Color) -> void:
	var mat := _mat_for(Color(col.r, col.g, col.b, 0.35), true)
	_place_mesh(_box_mesh(Vector3(BEAM_SIZE, BEAM_HEIGHT, BEAM_SIZE)), wp + Vector3(0, BEAM_HEIGHT * 0.5, 0), mat)


func _add_label(wp: Vector3, text: String, col: Color) -> void:
	label = Label3D.new()
	label.text = "" if QaPlants.is_active("marker-unnamed") else text
	label.font = _font
	label.font_size = 64
	label.pixel_size = 2.2
	label.modulate = col
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.no_depth_test = true
	label.position = wp + Vector3(0, 260.0, 0)
	add_child(label)


func _add_glyph(wp: Vector3, col: Color) -> void:
	var gp := wp + Vector3(0, 40.0, 0)
	var mat := _mat_for(col, false)
	match _kind:
		"hold_zone":
			_place_mesh(_box_mesh(Vector3(80, 80, 80)), gp, mat)
		"destroy_targets":
			var mi := _place_mesh(_box_mesh(Vector3(70, 70, 70)), gp, mat)
			mi.rotation_degrees = Vector3(0, 45, 45)
		"escort_to_extraction":
			_place_mesh(_cone_mesh(), gp, mat)
		"survive_duration":
			_place_mesh(_sphere_mesh(), gp, mat)
		"eliminate_force":
			var mia := _place_mesh(_box_mesh(Vector3(110, 24, 24)), gp, mat)
			mia.rotation_degrees = Vector3(0, 45, 0)
			var mib := _place_mesh(_box_mesh(Vector3(110, 24, 24)), gp, mat)
			mib.rotation_degrees = Vector3(0, -45, 0)


static func _cone_mesh() -> CylinderMesh:
	if _mesh_cache.has("cone"):
		return _mesh_cache["cone"]
	var cone := CylinderMesh.new()
	cone.top_radius = 0.0
	cone.bottom_radius = 45.0
	cone.height = 90.0
	_mesh_cache["cone"] = cone
	return cone


static func _sphere_mesh() -> SphereMesh:
	if _mesh_cache.has("sphere"):
		return _mesh_cache["sphere"]
	var sph := SphereMesh.new()
	sph.radius = 45.0
	sph.height = 90.0
	_mesh_cache["sphere"] = sph
	return sph


func _add_ring(wp: Vector3, radius: float, col: Color) -> void:
	var mat := _mat_for(Color(col.r, col.g, col.b, 0.4), true)
	_place_mesh(_ring_mesh(radius), wp + Vector3(0, 4.0, 0), mat)


func _add_scatter(items: Array, col: Color) -> void:
	var mesh := _box_mesh(SCATTER_BOX)
	for it in items:
		var mat := StandardMaterial3D.new()
		mat.albedo_color = col
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		_place_mesh(mesh, Vector3(it.pos.x, 35.0, it.pos.y), mat)
		_boxes.append({"mat": mat, "color": col})


func _add_route(path: Array, col: Color) -> void:
	var mesh := _box_mesh(ROUTE_BOX)
	var mat := _mat_for(col, false)
	var step: int = max(1, int(path.size() / 24))
	var i := 0
	while i < path.size():
		var p: Vector2 = path[i]
		_place_mesh(mesh, Vector3(p.x, 10.0, p.y), mat)
		i += step


func _place_mesh(mesh: Mesh, pos: Vector3, mat: StandardMaterial3D) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.material_override = mat
	mi.position = pos
	add_child(mi)
	return mi

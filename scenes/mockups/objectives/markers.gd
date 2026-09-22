class_name Marker
extends Node3D

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")

const BEAM_HEIGHT := 800.0
const BEAM_SIZE := 16.0
const RING_RADIUS := {"hold_zone": 600.0, "survive_duration": 400.0, "eliminate_force": 500.0}
const KIND_COLORS := {
	"hold_zone": Color(0.3, 0.85, 1.0),
	"destroy_targets": Color(1.0, 0.55, 0.2),
	"escort_to_extraction": Color(0.55, 0.95, 0.4),
	"survive_duration": Color(0.85, 0.4, 1.0),
	"eliminate_force": Color(1.0, 0.28, 0.28),
}

var label: Label3D
var _kind := ""
var _boxes: Array = []
var _font: FontFile = load("res://theme/fonts/JetBrainsMono-Bold.ttf")


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
	var box := BoxMesh.new()
	box.size = Vector3(BEAM_SIZE, BEAM_HEIGHT, BEAM_SIZE)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(col.r, col.g, col.b, 0.35)
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_place_mesh(box, wp + Vector3(0, BEAM_HEIGHT * 0.5, 0), mat)


func _add_label(wp: Vector3, text: String, col: Color) -> void:
	label = Label3D.new()
	label.text = "" if QaPlants.is_active("marker-unnamed") else text
	label.font = _font
	label.font_size = 56
	label.pixel_size = 0.5
	label.modulate = col
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.no_depth_test = true
	label.fixed_size = true
	label.position = wp + Vector3(0, 260.0, 0)
	add_child(label)


func _add_glyph(wp: Vector3, col: Color) -> void:
	var gp := wp + Vector3(0, 40.0, 0)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = col
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	match _kind:
		"hold_zone":
			var box := BoxMesh.new()
			box.size = Vector3(80, 80, 80)
			_place_mesh(box, gp, mat)
		"destroy_targets":
			var box := BoxMesh.new()
			box.size = Vector3(70, 70, 70)
			var mi := _place_mesh(box, gp, mat)
			mi.rotation_degrees = Vector3(0, 45, 45)
		"escort_to_extraction":
			var cone := CylinderMesh.new()
			cone.top_radius = 0.0
			cone.bottom_radius = 45.0
			cone.height = 90.0
			_place_mesh(cone, gp, mat)
		"survive_duration":
			var sph := SphereMesh.new()
			sph.radius = 45.0
			sph.height = 90.0
			_place_mesh(sph, gp, mat)
		"eliminate_force":
			var a := BoxMesh.new()
			a.size = Vector3(110, 24, 24)
			var mia := _place_mesh(a, gp, mat)
			mia.rotation_degrees = Vector3(0, 45, 0)
			var b := BoxMesh.new()
			b.size = Vector3(110, 24, 24)
			var mib := _place_mesh(b, gp, mat)
			mib.rotation_degrees = Vector3(0, -45, 0)


func _add_ring(wp: Vector3, radius: float, col: Color) -> void:
	var torus := TorusMesh.new()
	torus.inner_radius = radius - 8.0
	torus.outer_radius = radius
	torus.rings = 48
	torus.ring_segments = 48
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(col.r, col.g, col.b, 0.4)
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_place_mesh(torus, wp + Vector3(0, 4.0, 0), mat)


func _add_scatter(items: Array, col: Color) -> void:
	for it in items:
		var box := BoxMesh.new()
		box.size = Vector3(70, 70, 70)
		var mat := StandardMaterial3D.new()
		mat.albedo_color = col
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		_place_mesh(box, Vector3(it.pos.x, 35.0, it.pos.y), mat)
		_boxes.append({"mat": mat, "color": col})


func _add_route(path: Array, col: Color) -> void:
	var step: int = max(1, int(path.size() / 24))
	var i := 0
	while i < path.size():
		var p: Vector2 = path[i]
		var box := BoxMesh.new()
		box.size = Vector3(40, 20, 40)
		var mat := StandardMaterial3D.new()
		mat.albedo_color = col
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		_place_mesh(box, Vector3(p.x, 10.0, p.y), mat)
		i += step


func _place_mesh(mesh: Mesh, pos: Vector3, mat: StandardMaterial3D) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.material_override = mat
	mi.position = pos
	add_child(mi)
	return mi

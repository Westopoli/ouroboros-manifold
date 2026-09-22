extends Node3D

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")
const FIXTURES_DIR := "res://scenes/mockups/objectives/fixtures/"
const PLAYER_COLOR := Color("#4099ff")
const NODE_COLOR := Color(0.62, 0.66, 0.72)
const NODE_BOX := Vector3(160, 40, 160)

const PLANTS: Array[String] = [
	"objective-on-spawn", "marker-unnamed", "progress-static",
	"kind-mapping-random", "seed-ignored", "route-ignored",
]

var _camera_rig
var _hud
var _world: Node3D
var _generated: Node3D
var _marker: Marker
var _places: Places
var _mission: Dictionary = {}
var _fixture: int = 11
var _seed: int = 11
var _archetype: String = "defensive_stand"
var _timing_ms: Dictionary = {"gen": 0.0}
var _regen_count: int = 0


func _ready() -> void:
	_camera_rig = get_node("CameraRig")
	_hud = get_node("HUD")
	_world = Node3D.new()
	_world.name = "World"
	add_child(_world)
	_generated = Node3D.new()
	_generated.name = "Generated"
	_world.add_child(_generated)
	_build_ground()
	_generate()
	_hud.bind(self)


func _build_ground() -> void:
	var plane := PlaneMesh.new()
	plane.size = Vector2(200000, 200000)
	var mi := MeshInstance3D.new()
	mi.mesh = plane
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.09, 0.11, 0.09)
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mi.material_override = mat
	mi.position = Vector3(12000, -2.0, 12000)
	_world.add_child(mi)


func _generate() -> void:
	var t0 := Time.get_ticks_usec()
	var eff_fixture: int = 11 if QaPlants.is_active("seed-ignored") else _fixture
	_places = Places.new()
	_places.load_path(FIXTURES_DIR + "nodes_seed%d.json" % eff_fixture)
	_mission = MissionGen.build(_archetype, _places, _seed)
	var t1 := Time.get_ticks_usec()
	_timing_ms = {"gen": (t1 - t0) / 1000.0}

	for c in _generated.get_children():
		c.free()
	_marker = Marker.new()
	_generated.add_child(_marker)
	var display: String = MissionGen.DISPLAY_NAMES.get(_mission.kind, _mission.kind)
	_marker.setup(_mission, display)
	_add_player_spawn(_places.player_spawn().pos)
	_draw_places()
	_camera_rig.pan_to(Vector3(_pan_target().x, 0.0, _pan_target().y))
	_regen_count += 1
	if _hud != null:
		_hud.on_regenerated()


func _pan_target() -> Vector2:
	if _mission.kind == "escort_to_extraction" and _mission.extra.has("route"):
		var route: Array = _mission.extra.route
		return route[int(route.size() * 0.75)]
	return _mission.pos


func _add_player_spawn(pos: Vector2) -> void:
	var box := BoxMesh.new()
	box.size = Vector3(200, 120, 200)
	var mi := MeshInstance3D.new()
	mi.mesh = box
	var mat := StandardMaterial3D.new()
	mat.albedo_color = PLAYER_COLOR
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mi.material_override = mat
	mi.position = Vector3(pos.x, 60.0, pos.y)
	_generated.add_child(mi)


static var _node_mesh: BoxMesh
static var _node_mat: StandardMaterial3D
static var _node_font: FontFile = load("res://theme/fonts/JetBrainsMono-Regular.ttf")


func _draw_places() -> void:
	if _node_mesh == null:
		_node_mesh = BoxMesh.new()
		_node_mesh.size = NODE_BOX
	if _node_mat == null:
		_node_mat = StandardMaterial3D.new()
		_node_mat.albedo_color = NODE_COLOR
		_node_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	for n in _places.nodes:
		var mi := MeshInstance3D.new()
		mi.mesh = _node_mesh
		mi.material_override = _node_mat
		mi.position = Vector3(n.pos.x, 15.0, n.pos.y)
		_generated.add_child(mi)
		var lbl := Label3D.new()
		lbl.text = n.type
		lbl.font = _node_font
		lbl.font_size = 40
		lbl.pixel_size = 1.6
		lbl.modulate = Color(0.85, 0.86, 0.88)
		lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		lbl.no_depth_test = true
		lbl.position = Vector3(n.pos.x, 90.0, n.pos.y)
		_generated.add_child(lbl)


func qa_state() -> Dictionary:
	var display: String = MissionGen.DISPLAY_NAMES.get(_mission.kind, _mission.kind)
	var camera: Camera3D = _camera_rig.get_camera() if _camera_rig != null else null
	var wp := Vector3(_mission.pos.x, 0.0, _mission.pos.y)
	var px := camera.unproject_position(wp) * _viewport_scale() if camera != null else Vector2.ZERO
	return {
		"seed": _seed, "hash": MissionGen.mission_hash(_mission), "fixture": _fixture,
		"archetype": _archetype, "objective": _mission.objective, "satisfiable": _mission.satisfiable,
		"route_len_wu": min(_mission.route_len_wu, 999999.0), "time_limit_ticks": _mission.time_limit_ticks,
		"skipped": _mission.skipped, "marker": {"name": display, "px": [px.x, px.y]}, "tick": _mission.tick,
		"timing_ms": _timing_ms, "regen_count": _regen_count,
	}


func qa_plant(id: String) -> bool:
	if not PLANTS.has(id):
		return false
	QaPlants.activate(id)
	_generate()
	return true


func qa_seed(n: int) -> void:
	_seed = n
	_generate()


func qa_set(name: String, value) -> void:
	match name:
		"archetype":
			_archetype = String(value)
			_generate()
		"fixture":
			_fixture = int(value)
			_generate()


func qa_camera(height: float, x: float, z: float) -> void:
	_camera_rig.qa_camera(height, x, z)


func qa_camera_at_objective(height: float) -> void:
	_camera_rig.qa_camera(height, _mission.pos.x, _mission.pos.y)


func qa_tick(n: int) -> void:
	MissionGen.tick(_mission, n)
	_marker.refresh(_mission)


func get_mission() -> Dictionary:
	return _mission


func get_places() -> Places:
	return _places


func _viewport_scale() -> Vector2:
	var vp_size: Vector2 = get_viewport().get_visible_rect().size
	var win_size := Vector2(DisplayServer.window_get_size())
	if vp_size.x <= 0.0 or vp_size.y <= 0.0:
		return Vector2.ONE
	return win_size / vp_size

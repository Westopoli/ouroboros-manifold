extends Node3D

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")
const FIXTURES_DIR := "res://scenes/mockups/objectives/fixtures/"
const PLAYER_COLOR := Color("#4099ff")

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
	plane.size = Vector2(60000, 60000)
	var mi := MeshInstance3D.new()
	mi.mesh = plane
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.09, 0.11, 0.09)
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
	_regen_count += 1
	if _hud != null:
		_hud.on_regenerated()


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


func qa_state() -> Dictionary:
	var display: String = MissionGen.DISPLAY_NAMES.get(_mission.kind, _mission.kind)
	var camera: Camera3D = _camera_rig.get_camera() if _camera_rig != null else null
	var wp := Vector3(_mission.pos.x, 0.0, _mission.pos.y)
	var px := camera.unproject_position(wp) if camera != null else Vector2.ZERO
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


func qa_tick(n: int) -> void:
	MissionGen.tick(_mission, n)
	_marker.refresh(_mission)


func get_mission() -> Dictionary:
	return _mission


func get_places() -> Places:
	return _places

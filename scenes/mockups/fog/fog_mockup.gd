extends Node3D

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")

const FIXTURE_PATH := "res://scenes/mockups/fog/fixtures/map_seed11.json"
const SCENARIO_PATH := "res://scenes/mockups/fog/scenarios/patrol.json"
const CELL_SIZE := 100.0
const GRID_DIM := 64

const PLANTS: Array[String] = [
	"fog-leak", "no-memory", "recon-shows-enemy", "radius-ignored", "los-ignored", "seed-ignored",
]

var _truth: FogTruth
var _grid: FogCellGrid
@onready var _fog_view: FogView = get_node("World/FogView")
@onready var _camera_rig = get_node("CameraRig")
@onready var _hud = get_node("HUD")

var _phase: String = "recon"
var _selected_uid: int = -1
var _regen_count: int = 0
var _tick_durations_us: Array = []


func _ready() -> void:
	_truth = FogTruth.new()
	_grid = FogCellGrid.new()
	_truth.load_fixture(FIXTURE_PATH)
	_truth.load_scenario(SCENARIO_PATH)
	_grid.setup(GRID_DIM, CELL_SIZE)
	_fog_view.build_static(_truth, GRID_DIM, CELL_SIZE)
	_regenerate(11)
	_hud.bind(self)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed:
		var mb := event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_LEFT:
			var uid := _pick_friendly(mb.position)
			if uid != -1:
				_selected_uid = uid
				_sync_view()
		elif mb.button_index == MOUSE_BUTTON_RIGHT and _selected_uid != -1:
			_truth.command_move(_selected_uid, _project_to_ground(mb.position))
			_sync_view()


func _project_to_ground(screen_pos: Vector2) -> Vector2:
	var camera: Camera3D = _camera_rig.get_camera()
	var from: Vector3 = camera.project_ray_origin(screen_pos)
	var dir: Vector3 = camera.project_ray_normal(screen_pos)
	if absf(dir.y) < 0.0001:
		return Vector2(from.x, from.z)
	var t: float = -from.y / dir.y
	var hit: Vector3 = from + dir * t
	return Vector2(hit.x, hit.z)


func _pick_friendly(screen_pos: Vector2) -> int:
	var world := _project_to_ground(screen_pos)
	var best_uid := -1
	var best_d := 250.0
	for f in _truth.friendlies:
		var d: float = f.pos.distance_to(world)
		if d < best_d:
			best_d = d
			best_uid = f.uid
	return best_uid


func _regenerate(p_seed: int) -> void:
	_truth.load_scenario(SCENARIO_PATH)
	_truth.generate(p_seed)
	_grid.setup(GRID_DIM, CELL_SIZE)
	_phase = "recon"
	_selected_uid = -1
	_sync_view()
	_regen_count += 1


func begin_mission() -> void:
	if _phase == "mission":
		return
	_phase = "mission"
	_truth.phase = "mission"
	_grid.reset_never_seen()
	_sync_view()


func _sync_view() -> void:
	var vis: Dictionary = _truth.compute_visibility()
	var visible_uids: Array = vis.visible_enemy_uids
	var circles: Array = vis.circles

	if _phase == "mission":
		_grid.update(circles)

	var show_enemies: bool = _phase == "mission" or QaPlants.is_active("recon-shows-enemy")
	var leak_all: bool = QaPlants.is_active("fog-leak")
	var enemy_list: Array = []
	if show_enemies:
		for e in _truth.enemies:
			if leak_all or visible_uids.has(e.uid):
				enemy_list.append({"uid": e.uid, "pos": e.pos})

	_fog_view.update_enemies(enemy_list)
	_fog_view.update_friendlies(_truth.friendlies, _selected_uid)
	_fog_view.update_circles(circles, _selected_uid)
	_fog_view.update_fog(_grid, _phase == "recon")

	var struct_states := {}
	for s in _truth.structures:
		struct_states[s.sid] = "never_seen" if _phase == "recon" else _grid.state_name(_grid.state_at(s.pos))
	_fog_view.update_structures(struct_states)


func qa_state() -> Dictionary:
	var vis: Dictionary = _truth.compute_visibility()
	var counts: Dictionary
	if _phase == "recon":
		counts = {"never_seen": 0, "explored": 0, "visible": _grid.dim * _grid.dim}
	else:
		counts = _grid.counts()

	var circles_dict := {}
	for c in vis.circles:
		circles_dict[str(c.uid)] = c.radius_eff

	var camera: Camera3D = _camera_rig.get_camera() if _camera_rig != null else null
	var enemies_px := {}
	for e in _truth.enemies:
		if camera != null:
			var px: Vector2 = camera.unproject_position(Vector3(e.pos.x, 0.0, e.pos.y))
			enemies_px[str(e.uid)] = [px.x, px.y]
		else:
			enemies_px[str(e.uid)] = [0.0, 0.0]

	var struct_states := {}
	for s in _truth.structures:
		struct_states[str(s.sid)] = "never_seen" if _phase == "recon" else _grid.state_name(_grid.state_at(s.pos))

	var avg_us := 0.0
	if not _tick_durations_us.is_empty():
		var total := 0
		for d in _tick_durations_us:
			total += d
		avg_us = float(total) / float(_tick_durations_us.size())

	return {
		"seed": _truth.seed,
		"hash": _truth.compute_hash(),
		"phase": _phase,
		"tick": _truth.tick,
		"memory": _grid.memory,
		"visible_enemy_uids": vis.visible_enemy_uids,
		"view_enemy_uids": _fog_view.get_enemy_uids(),
		"enemy_count_total": _truth.enemies.size(),
		"cells": counts,
		"circles": circles_dict,
		"enemies_px": enemies_px,
		"structures": struct_states,
		"timing_ms": {"tick_avg": avg_us / 1000.0},
		"regen_count": _regen_count,
	}


func qa_plant(id: String) -> bool:
	if not PLANTS.has(id):
		return false
	QaPlants.activate(id)
	_regenerate(_truth.seed)
	return true


func qa_seed(n: int) -> void:
	_regenerate(n)


func qa_set(name: String, value) -> void:
	match name:
		"memory":
			_grid.memory = bool(value)
			_sync_view()
		"phase":
			if String(value) == "mission":
				begin_mission()


func qa_camera(height: float, x: float, z: float) -> void:
	_camera_rig.pan_to(Vector3(x, 0.0, z))
	_camera_rig.set_height(height)


func qa_tick(n: int) -> void:
	for i in range(n):
		var t0 := Time.get_ticks_usec()
		_truth.step()
		_sync_view()
		var dt: int = Time.get_ticks_usec() - t0
		_tick_durations_us.append(dt)
		if _tick_durations_us.size() > 200:
			_tick_durations_us.pop_front()


func qa_move(uid: int, x: float, z: float) -> void:
	_truth.command_move(uid, Vector2(x, z))
	_sync_view()

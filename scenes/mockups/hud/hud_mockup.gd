extends Node3D

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")
const SelectionScript := preload("res://scenes/mockups/hud/selection.gd")
const ToyUnitsScript := preload("res://scenes/mockups/hud/toy_units.gd")

const PLANTS: Array[String] = ["box-one-layer", "group-shared", "select-all-exists",
	"camera-unbounded", "clock-wallclock", "narrow-moves-focus"]

const DT := 1.0 / 20.0
const LAYER_Y := {1: 0.0, 2: 400.0}

var _camera_rig: Node3D
var _hud: Node
var _input_router: Node

var _toy
var _selection
var _tick: int = 0
var _seed: int = 11
var _time_acc: float = 0.0
var _regen_count: int = 0
var _tick_ms_sum: float = 0.0
var _tick_ms_n: int = 0


func _ready() -> void:
	_camera_rig = get_node_or_null("CameraRig")
	_hud = get_node_or_null("HUD")
	_input_router = get_node_or_null("Input")

	_toy = ToyUnitsScript.new()
	_selection = SelectionScript.new()
	if _input_router != null and _input_router.has_method("setup"):
		_input_router.setup(self, _toy, _selection, _camera_rig)
	if _hud != null and _hud.has_method("setup"):
		_hud.setup(self)

	qa_seed(_seed)


func _process(delta: float) -> void:
	_time_acc += delta
	while _time_acc >= DT:
		_time_acc -= DT
		_advance_tick()
	if _hud != null and _hud.has_method("sync"):
		_hud.sync(qa_state())


func _advance_tick() -> void:
	var t0 := Time.get_ticks_usec()
	_toy.step()
	_selection.prune_dead(_toy.get_alive())
	_tick += 1
	_tick_ms_sum += (Time.get_ticks_usec() - t0) / 1000.0
	_tick_ms_n += 1
	_sync_visuals()


func _sync_visuals() -> void:
	var units_node := get_node_or_null("World/Units")
	if units_node == null:
		return
	var alive: Dictionary = _toy.get_all()
	for uid in alive.keys():
		var body := units_node.get_node_or_null("Unit_%d" % uid)
		if body == null:
			continue
		var rec: Dictionary = alive[uid]
		var alive_flag: bool = rec.hp > 0.0
		body.visible = alive_flag
		if alive_flag:
			var y: float = LAYER_Y.get(rec.layer, 0.0)
			body.position = Vector3(rec.pos.x, y + 25.0, rec.pos.y)
		var ring := body.get_node_or_null("Ring")
		if ring != null:
			ring.visible = _selection.selected.has(uid)


func _clock_s() -> float:
	if QaPlants.is_active("clock-wallclock"):
		return Time.get_ticks_msec() / 1000.0
	return float(_tick) / 20.0


func _current_objective() -> Dictionary:
	var progress: float = clampf(float(_tick) / 1200.0, 0.0, 1.0)
	return {"name": "Hold The Core", "progress": progress}


func qa_state() -> Dictionary:
	var alive: Dictionary = _toy.get_all()
	var units: Dictionary = {}
	var units_px: Dictionary = {}
	var cam: Camera3D = _camera_rig.get_camera() if _camera_rig != null else null
	for uid in alive.keys():
		var rec: Dictionary = alive[uid]
		units[str(uid)] = {"faction": rec.faction, "layer": rec.layer, "pos": [rec.pos.x, rec.pos.y], "hp": rec.hp}
		var y: float = LAYER_Y.get(rec.layer, 0.0)
		var px: Vector2 = cam.unproject_position(Vector3(rec.pos.x, y, rec.pos.y)) if cam != null else Vector2.ZERO
		units_px[str(uid)] = [px.x, px.y]

	var groups: Dictionary = {}
	for digit in _selection.groups.keys():
		groups[str(digit)] = _selection.groups[digit].duplicate()

	var pan: Vector2 = _camera_rig.get_pan() if _camera_rig != null else Vector2.ZERO
	var height: float = _camera_rig.get_height() if _camera_rig != null else 0.0
	var bounds: Dictionary = _camera_rig.get_bounds() if _camera_rig != null else {"min_x": 0.0, "max_x": 0.0, "min_z": 0.0, "max_z": 0.0}
	var tick_avg: float = (_tick_ms_sum / _tick_ms_n) if _tick_ms_n > 0 else 0.0

	return {"seed": _seed, "hash": _state_hash(), "tick": _tick, "clock_s": _clock_s(),
		"selected": _selection.selected.duplicate(), "groups": groups, "focus_layer": _selection.focus_layer,
		"camera": {"height": height, "x": pan.x, "z": pan.y}, "bounds": bounds,
		"units": units, "units_px": units_px, "commands": _selection.commands(),
		"objective": _current_objective(), "timing_ms": {"tick_avg": tick_avg}, "regen_count": _regen_count}


func _state_hash() -> int:
	return hash([_toy.compute_hash(), _tick])


func qa_plant(id: String) -> bool:
	if not PLANTS.has(id):
		return false
	QaPlants.activate(id)
	return true


func qa_seed(n: int) -> void:
	_seed = n
	_toy.generate(n)
	_selection.selected.clear()
	_selection.groups.clear()
	_tick = 0
	_time_acc = 0.0
	_tick_ms_sum = 0.0
	_tick_ms_n = 0
	_regen_count += 1
	_sync_visuals()


func qa_set(name: String, value) -> void:
	if name == "focus_layer":
		_selection.focus_layer = int(value)


func qa_camera(height: float, x: float, z: float) -> void:
	if _camera_rig == null:
		return
	_camera_rig.centre_on(Vector2(x, z))
	_camera_rig.set_height(height)


func qa_tick(n: int) -> void:
	for i in range(n):
		_advance_tick()


func qa_select(uids: Array) -> void:
	var out: Array[int] = []
	var alive: Dictionary = _toy.get_alive()
	for v in uids:
		var uid := int(v)
		if alive.has(uid) and alive[uid].faction == SelectionScript.PLAYER_FACTION:
			out.append(uid)
	_selection.selected = out
	_sync_visuals()


func qa_bind(digit: int) -> void:
	_selection.bind(digit, _toy.get_alive())
	_sync_visuals()


func qa_recall(digit: int) -> void:
	var result: Dictionary = _selection.recall(digit, _toy.get_alive(), Time.get_ticks_msec())
	if result.centre_requested and _camera_rig != null:
		_camera_rig.centre_on(result.centre)
	_sync_visuals()


func qa_narrow(layer: int) -> void:
	_selection.narrow(layer, _toy.get_alive())
	_sync_visuals()

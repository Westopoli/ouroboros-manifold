class_name ToySim
extends RefCounted

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")

const TICK_HZ := 20.0
const MOVE_SPEED_WU_S := 80.0
const CELL_WU := 100.0
const ADJACENT_VISION_FACTOR := 0.5
const JITTER_RANGE_WU := 20.0

const TRANSITION_TICKS := {"fast": 20, "slow": 100}
const SENSOR_WU := {"fast": 800.0, "slow": 300.0}

var canvas_wu: float = 4000.0
var obstacle_pos: Vector2 = Vector2.ZERO
var obstacle_size: Vector2 = Vector2.ZERO
var blocked_center: Vector2 = Vector2.ZERO
var blocked_radius: float = 0.0
var vantage_pos: Vector2 = Vector2.ZERO

var tick: int = 0
var units: Dictionary = {}
var debug_use_global_rng: bool = false

var _fixture: Dictionary = {}
var _seed: int = 11
var _rng := RandomNumberGenerator.new()
var _tick_usec_total: int = 0
var _tick_count: int = 0


func load_fixture(path: String) -> void:
	var text := FileAccess.get_file_as_string(path)
	var parsed = JSON.parse_string(text)
	_fixture = parsed if typeof(parsed) == TYPE_DICTIONARY else {}


func generate(seed_n: int) -> void:
	_seed = seed_n
	_rng.seed = seed_n
	tick = 0
	units.clear()

	canvas_wu = float(_fixture.get("canvas_wu", 4000.0))
	var obs: Dictionary = _fixture.get("obstacle", {})
	var obs_pos: Array = obs.get("pos", [2000.0, 2000.0])
	var obs_size: Array = obs.get("size", [300.0, 300.0])
	obstacle_pos = Vector2(obs_pos[0], obs_pos[1])
	obstacle_size = Vector2(obs_size[0], obs_size[1])

	var br: Dictionary = _fixture.get("blocked_region", {})
	var br_center: Array = br.get("center", [2000.0, 2000.0])
	blocked_center = Vector2(br_center[0], br_center[1])
	blocked_radius = float(br.get("radius", 350.0))

	var vm: Dictionary = _fixture.get("vantage_marker", {})
	var vm_pos: Array = vm.get("pos", [3200.0, 700.0])
	vantage_pos = Vector2(vm_pos[0], vm_pos[1])

	for f in _fixture.get("friendlies", []):
		_add_unit(f, 0)
	for e in _fixture.get("enemies", []):
		_add_unit(e, 1)


func _jitter() -> Vector2:
	if debug_use_global_rng:
		return Vector2(randf_range(-JITTER_RANGE_WU, JITTER_RANGE_WU), randf_range(-JITTER_RANGE_WU, JITTER_RANGE_WU))
	return Vector2(_rng.randf_range(-JITTER_RANGE_WU, JITTER_RANGE_WU), _rng.randf_range(-JITTER_RANGE_WU, JITTER_RANGE_WU))


func _add_unit(data: Dictionary, faction: int) -> void:
	var uid := int(data.get("uid", 0))
	var raw_pos: Array = data.get("pos", [0.0, 0.0])
	var pos := Vector2(raw_pos[0], raw_pos[1]) + (_jitter() if faction == 0 else Vector2.ZERO)
	var type_name: String = data.get("type", "fast")
	units[uid] = {
		"uid": uid,
		"type": type_name,
		"faction": faction,
		"pos": pos,
		"layer": int(data.get("layer", 1)),
		"pending": false,
		"pending_target": null,
		"transition": null,
		"move_target": null,
		"sensor_wu": SENSOR_WU.get(type_name, 800.0) if faction == 0 else 0.0,
	}


func _cell_center(pos: Vector2) -> Vector2:
	var cx: float = floor(pos.x / CELL_WU) * CELL_WU + CELL_WU * 0.5
	var cz: float = floor(pos.y / CELL_WU) * CELL_WU + CELL_WU * 0.5
	return Vector2(cx, cz)


func is_blocked(layer: int, pos: Vector2) -> bool:
	if QaPlants.is_active("blocked-ignored"):
		return false
	if layer != 2:
		return false
	return _cell_center(pos).distance_to(_cell_center(blocked_center)) <= blocked_radius


func transfer(uid: int, layer: int) -> void:
	if not units.has(uid):
		return
	var u: Dictionary = units[uid]

	if QaPlants.is_active("instant-transfer"):
		u.layer = layer
		u.pending = false
		u.pending_target = null
		u.transition = null
		return

	if u.transition != null:
		u.pending = true
		u.pending_target = layer
		return

	if layer == u.layer:
		u.pending = false
		u.pending_target = null
		u.transition = null
		return

	if is_blocked(layer, u.pos):
		u.pending = true
		u.pending_target = layer
	else:
		u.pending = false
		u.pending_target = null
		_start_transition(u, layer)


func _start_transition(u: Dictionary, layer: int) -> void:
	var duration: int = TRANSITION_TICKS.get(u.type, 20)
	u.transition = {"from": u.layer, "to": layer, "ticks_left": duration, "duration": duration, "start_tick": tick}


func move(uid: int, x: float, z: float) -> void:
	if not units.has(uid):
		return
	units[uid].move_target = Vector2(x, z)


func step(n: int = 1) -> void:
	for i in range(n):
		var t0 := Time.get_ticks_usec()
		_step_once()
		_tick_usec_total += Time.get_ticks_usec() - t0
		_tick_count += 1


func tick_avg_ms() -> float:
	if _tick_count == 0:
		return 0.0
	return (float(_tick_usec_total) / float(_tick_count)) / 1000.0


func _step_once() -> void:
	tick += 1
	for uid in units.keys():
		var u: Dictionary = units[uid]
		_step_movement(u)
		_step_transition(u)


func _step_movement(u: Dictionary) -> void:
	if u.move_target == null:
		return
	var target: Vector2 = u.move_target
	var to_target: Vector2 = target - u.pos
	var dist := to_target.length()
	var step_dist := MOVE_SPEED_WU_S / TICK_HZ
	if dist <= step_dist:
		u.pos = target
		u.move_target = null
	else:
		u.pos = u.pos + to_target.normalized() * step_dist


func _step_transition(u: Dictionary) -> void:
	if u.transition != null:
		var tr: Dictionary = u.transition
		tr.ticks_left -= 1
		if tr.ticks_left <= 0:
			u.layer = tr.to
			u.transition = null
			if u.pending:
				_resolve_pending(u)
		return
	if u.pending:
		_resolve_pending(u)


func _resolve_pending(u: Dictionary) -> void:
	var target: int = int(u.pending_target)
	if target == u.layer:
		u.pending = false
		u.pending_target = null
		return
	if is_blocked(target, u.pos):
		return
	u.pending = false
	u.pending_target = null
	_start_transition(u, target)


func visible_by(uid: int) -> Array:
	var out: Array = []
	if not units.has(uid):
		return out
	var observer: Dictionary = units[uid]
	for eid in units.keys():
		var e: Dictionary = units[eid]
		if e.faction == observer.faction:
			continue
		var dist: float = observer.pos.distance_to(e.pos)
		var radius: float = observer.sensor_wu
		if e.layer != observer.layer:
			radius = observer.sensor_wu * ADJACENT_VISION_FACTOR
			if QaPlants.is_active("cross-layer-full-range"):
				radius = observer.sensor_wu
		if dist <= radius:
			out.append(eid)
	return out


func visible_enemy_uids() -> Array:
	var seen := {}
	for uid in units.keys():
		if units[uid].faction != 0:
			continue
		for eid in visible_by(uid):
			seen[eid] = true
	var out: Array = seen.keys()
	out.sort()
	return out


func compute_hash() -> int:
	var parts: Array = []
	parts.append(str(tick))
	var uids: Array = units.keys()
	uids.sort()
	for uid in uids:
		var u: Dictionary = units[uid]
		var tr_str := "null"
		if u.transition != null:
			tr_str = "%d>%d@%d" % [u.transition.from, u.transition.to, u.transition.ticks_left]
		parts.append("%d:%d:%.1f:%.1f:%s:%s" % [uid, u.layer, u.pos.x, u.pos.y, tr_str, str(u.pending)])
	return String(",".join(parts)).hash()

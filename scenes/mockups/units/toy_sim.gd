class_name UnitsToySim
extends RefCounted

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")

const TICK_DT := 1.0 / 20.0
const CELL_SIZE := 100.0
const CANVAS_WU := 8000.0
const GRID_DIM := int(CANVAS_WU / CELL_SIZE)
const COLLISION_DIST := 30.0
const ALLY_BLOCK_RADIUS := 20.0
const PROBE_DIST := 40.0
const DEFLECT_HOLD_WU := 60.0
const ARRIVE_DIST := 12.0
const ANCHOR_DROP_WU := 200.0
const RETARGET_STAGGER := 4
const BACKSWING_TICKS := 10
const TARGET_TIE_EPS := 15.0
const PRECHARGED_TIMER := 1000000
const SWEEP_LEFT: Array[float] = [20.0, -20.0, 40.0, -40.0, 60.0, -60.0, 80.0, -80.0]
const SWEEP_RIGHT: Array[float] = [-20.0, 20.0, -40.0, 40.0, -60.0, 60.0, -80.0, 80.0]

var roster: Roster
var units: Array = []
var obstacles: Array = []
var current_tick: int = 0
var seed_value: int = 11

var _by_uid: Dictionary = {}
var _blocked: Dictionary = {}
var _scheduled: Array = []
var _pending: Array = []
var _rng := RandomNumberGenerator.new()


func reset(p_roster: Roster, scenario: Dictionary, p_seed: int) -> void:
	roster = p_roster
	var s: int = 11 if QaPlants.is_active("seed-ignored") else p_seed
	seed_value = s
	_rng.seed = s
	current_tick = 0
	units.clear()
	_by_uid.clear()
	_pending.clear()
	obstacles = scenario.get("obstacles", []).duplicate(true)
	_build_grid()

	var uid := 0
	for entry in scenario.get("units", []):
		var role: String = entry.role
		var stats := roster.get_stats(role)
		var p: Array = entry.pos
		var u := {
			"uid": uid,
			"role": role,
			"faction": int(entry.faction),
			"pos": Vector2(float(p[0]), float(p[1])),
			"facing": 0.0,
			"hp": float(stats.get("hp", 1.0)),
			"max_hp": float(stats.get("hp", 1.0)),
			"order": {},
			"target": null,
			"anchor": null,
			"attack_timer": PRECHARGED_TIMER,
			"backswing": 0,
			"alive": true,
			"death_tick": -1,
			"last_hit_tick": -1000,
			"route": [],
			"route_index": 0,
			"deflect_angle": 0.0,
			"deflect_remaining": 0.0,
			"move_speed_override": null,
			"last_heading": 0.0,
			"moved_this_tick": false,
			"sweep_bias": _rng.randi() % 2,
		}
		units.append(u)
		_by_uid[uid] = u
		uid += 1

	_scheduled = scenario.get("commands", []).duplicate(true)
	_scheduled.sort_custom(func(a, b): return int(a.tick) < int(b.tick))


func queue_command(kind: String, uids: Array, point, target) -> void:
	_pending.append({"kind": kind, "uids": uids.duplicate(), "point": point, "target": target})


func step() -> void:
	var due: Array = []
	while not _scheduled.is_empty() and int(_scheduled[0].tick) <= current_tick:
		due.append(_scheduled.pop_front())
	due.append_array(_pending)
	_pending.clear()
	for cmd in due:
		_apply_command(cmd.kind, cmd.uids, cmd.get("point"), cmd.get("target"))

	_step_targeting()
	_step_movement(TICK_DT)
	_step_collision()
	_step_attacks()
	_step_facing(TICK_DT)
	_step_deaths()
	current_tick += 1


func run(scenario: Dictionary, ticks: int, p_seed: int = 11) -> int:
	reset(roster, scenario, p_seed)
	for i in range(ticks):
		step()
	return compute_hash()


func compute_hash() -> int:
	var h: int = 5381
	for u in units:
		h = _mix(h, int(round(u.pos.x * 100.0)))
		h = _mix(h, int(round(u.pos.y * 100.0)))
		h = _mix(h, int(round(u.facing * 10000.0)))
		h = _mix(h, int(round(u.hp * 100.0)))
		h = _mix(h, 1 if u.alive else 0)
	return h


func _mix(h: int, v: int) -> int:
	return ((h * 33) + v) & 0x7FFFFFFF


func get_unit(uid: int) -> Variant:
	return _by_uid.get(uid)


func alive_counts() -> Dictionary:
	var c := {0: 0, 1: 0}
	for u in units:
		if u.alive:
			c[u.faction] = c.get(u.faction, 0) + 1
	return c


# --- commands ---

func _apply_command(kind: String, uids: Array, point, target) -> void:
	var uids_i: Array = []
	for uid in uids:
		uids_i.append(int(uid))
	var target_i: int = int(target) if target != null else -1
	match kind:
		"move", "attack_move":
			var speed_override = null
			var centroid := Vector2.ZERO
			var live_count := 0
			for uid in uids_i:
				var u0 = _by_uid.get(uid)
				if u0 == null or not u0.alive:
					continue
				centroid += u0.pos
				live_count += 1
			if live_count > 0:
				centroid /= float(live_count)
			if uids_i.size() > 1:
				var min_speed := INF
				for uid in uids_i:
					var u = _by_uid.get(uid)
					if u == null or not u.alive:
						continue
					var sp := float(roster.get_stats(u.role).get("speed_wu_s", 1.0))
					min_speed = min(min_speed, sp)
				if min_speed < INF:
					speed_override = min_speed
			var anchor_point := Vector2(float(point[0]), float(point[1]))
			for uid in uids_i:
				var u = _by_uid.get(uid)
				if u == null or not u.alive:
					continue
				var dest: Vector2 = anchor_point if live_count <= 1 else anchor_point + (u.pos - centroid)
				u.order = {"kind": kind, "point": [dest.x, dest.y]}
				u.target = null
				u.anchor = null
				u.route = _compute_route(u.pos, dest)
				u.route_index = 0
				u.deflect_remaining = 0.0
				u.move_speed_override = speed_override
		"attack_target":
			for uid in uids_i:
				var u = _by_uid.get(uid)
				if u == null or not u.alive:
					continue
				u.order = {"kind": "attack_target", "target": target_i}
				u.target = target_i
				u.anchor = null
				u.route = []
				u.move_speed_override = null
		"stop":
			for uid in uids_i:
				var u = _by_uid.get(uid)
				if u == null or not u.alive:
					continue
				u.order = {}
				u.target = null
				u.anchor = null
				u.route = []
				u.move_speed_override = null
		_:
			pass


# --- targeting: R-087-03..08, R-096-01..04 ---

func _step_targeting() -> void:
	for u in units:
		if not u.alive:
			continue
		var order_kind: String = u.order.get("kind", "idle")
		if order_kind == "move":
			continue
		if order_kind == "attack_target":
			if u.target != null:
				var t = _by_uid.get(u.target)
				if t == null or not t.alive:
					u.target = null
					u.order = {}
			continue

		if u.target != null:
			var t2 = _by_uid.get(u.target)
			var drop := false
			if t2 == null or not t2.alive:
				drop = true
			elif order_kind == "attack_move" and u.anchor != null and Vector2(u.anchor[0], u.anchor[1]).distance_to(t2.pos) > ANCHOR_DROP_WU:
				drop = true
			elif not _in_range_of(u, t2):
				drop = true
			if drop:
				u.target = null
				u.anchor = null

		if u.target == null and (current_tick + int(u.uid)) % RETARGET_STAGGER == 0:
			var best := _find_nearest_enemy_in_range(u)
			if best != -1:
				u.target = best
				u.anchor = [u.pos.x, u.pos.y]


func _find_nearest_enemy_in_range(u: Dictionary) -> int:
	var range_wu := float(roster.get_stats(u.role).get("range_wu", 0.0))
	var candidates: Array = []
	var best_d := INF
	for other in units:
		if not other.alive or other.faction == u.faction:
			continue
		var d: float = u.pos.distance_to(other.pos)
		if d > range_wu:
			continue
		if d < best_d - TARGET_TIE_EPS:
			best_d = d
			candidates = [other.uid]
		elif d <= best_d + TARGET_TIE_EPS:
			candidates.append(other.uid)
			best_d = min(best_d, d)
	if candidates.is_empty():
		return -1
	if candidates.size() == 1:
		return candidates[0]
	return candidates[_rng.randi() % candidates.size()]


func _in_range_of(u: Dictionary, t: Dictionary) -> bool:
	var range_wu := float(roster.get_stats(u.role).get("range_wu", 0.0))
	return u.pos.distance_to(t.pos) <= range_wu


# --- movement: R-097-03..08 ---

func _movement_goal(u: Dictionary):
	if u.order.is_empty():
		return null
	match u.order.kind:
		"move", "attack_move":
			if u.route.is_empty() or u.route_index >= u.route.size():
				return null
			return u.route[u.route_index]
		"attack_target":
			var t = _by_uid.get(u.order.target)
			if t == null or not t.alive:
				return null
			return t.pos
	return null


func _is_engaged(u: Dictionary) -> bool:
	if u.target == null:
		return false
	var t = _by_uid.get(u.target)
	return t != null and t.alive and _in_range_of(u, t)


func _is_stationary(u: Dictionary) -> bool:
	if u.backswing > 0:
		return true
	if _is_engaged(u):
		return true
	return _movement_goal(u) == null


func _step_movement(dt: float) -> void:
	for u in units:
		if not u.alive:
			continue
		u.moved_this_tick = false
		if u.backswing > 0:
			u.backswing -= 1
			continue
		if _is_engaged(u):
			continue
		var goal = _movement_goal(u)
		if goal == null:
			continue
		var speed: float = u.move_speed_override if u.move_speed_override != null else float(roster.get_stats(u.role).get("speed_wu_s", 1.0))
		var to_goal: Vector2 = goal - u.pos
		var dist: float = to_goal.length()
		if dist < ARRIVE_DIST:
			_advance_waypoint(u)
			continue
		var desired: Vector2 = to_goal / dist
		var heading: Vector2 = desired
		if u.deflect_remaining > 0.0:
			heading = Vector2.RIGHT.rotated(u.deflect_angle)
		else:
			var probe: Vector2 = u.pos + desired * PROBE_DIST
			if not QaPlants.is_active("pass-through") and _ally_blocks(u, probe):
				var picked := false
				var order_list: Array[float] = SWEEP_LEFT if u.sweep_bias == 0 else SWEEP_RIGHT
				for deg in order_list:
					var test_dir: Vector2 = desired.rotated(deg_to_rad(deg))
					var test_probe: Vector2 = u.pos + test_dir * PROBE_DIST
					if not _ally_blocks(u, test_probe):
						heading = test_dir
						u.deflect_angle = test_dir.angle()
						u.deflect_remaining = DEFLECT_HOLD_WU
						picked = true
						break
				if not picked:
					continue
		var step_len: float = min(speed * dt, dist)
		u.pos += heading * step_len
		u.last_heading = heading.angle()
		u.moved_this_tick = true
		if u.deflect_remaining > 0.0:
			u.deflect_remaining = max(0.0, u.deflect_remaining - step_len)
		if (goal - u.pos).length() < ARRIVE_DIST:
			_advance_waypoint(u)


func _advance_waypoint(u: Dictionary) -> void:
	match u.order.get("kind", ""):
		"move":
			u.route_index += 1
			if u.route_index >= u.route.size():
				u.order = {}
				u.route = []
				u.move_speed_override = null
		"attack_move":
			u.route_index += 1


func _ally_blocks(u: Dictionary, probe_point: Vector2) -> bool:
	for other in units:
		if other.uid == u.uid or not other.alive or other.faction != u.faction:
			continue
		if other.pos.distance_to(probe_point) < ALLY_BLOCK_RADIUS:
			return true
	return false


# --- collision: R-097-05..08 ---

func _step_collision() -> void:
	if QaPlants.is_active("pass-through"):
		return
	for iter in range(3):
		var any_push := false
		for i in range(units.size()):
			var a = units[i]
			if not a.alive:
				continue
			for j in range(i + 1, units.size()):
				var b = units[j]
				if not b.alive:
					continue
				var delta: Vector2 = b.pos - a.pos
				var dist: float = delta.length()
				if dist >= COLLISION_DIST:
					continue
				if dist < 0.001:
					var lo = a if a.uid < b.uid else b
					lo.pos += Vector2(COLLISION_DIST * 0.5, 0.0)
					any_push = true
					continue
				var dir: Vector2 = delta / dist
				var overlap: float = COLLISION_DIST - dist
				var a_fixed := _is_stationary(a)
				var b_fixed := _is_stationary(b)
				if a_fixed and b_fixed:
					continue
				elif a_fixed:
					b.pos += dir * overlap
				elif b_fixed:
					a.pos -= dir * overlap
				else:
					a.pos -= dir * overlap * 0.5
					b.pos += dir * overlap * 0.5
				any_push = true
		if not any_push:
			break
	for u in units:
		if u.alive:
			_clamp_out_of_obstacles(u)


func _clamp_out_of_obstacles(u: Dictionary) -> void:
	for ob in obstacles:
		if u.pos.x > ob.x0 and u.pos.x < ob.x1 and u.pos.y > ob.z0 and u.pos.y < ob.z1:
			var dl: float = u.pos.x - ob.x0
			var dr: float = ob.x1 - u.pos.x
			var dt2: float = u.pos.y - ob.z0
			var db: float = ob.z1 - u.pos.y
			var m: float = min(dl, min(dr, min(dt2, db)))
			if m == dl:
				u.pos.x = ob.x0
			elif m == dr:
				u.pos.x = ob.x1
			elif m == dt2:
				u.pos.y = ob.z0
			else:
				u.pos.y = ob.z1


# --- attacks: R-084-01, R-084-02, R-084-04 ---

func _step_attacks() -> void:
	for u in units:
		if not u.alive or u.target == null:
			continue
		var t = _by_uid.get(u.target)
		if t == null or not t.alive or not _in_range_of(u, t):
			continue
		u.attack_timer += 1
		var interval_ticks: int = int(round(float(roster.get_stats(u.role).get("interval_s", 1.0)) * 20.0))
		if u.attack_timer >= interval_ticks:
			u.attack_timer = 0
			var dmg: float = float(roster.get_stats(u.role).get("damage", 0.0))
			if QaPlants.is_active("instant-fight"):
				dmg *= 50.0
			t.hp -= dmg
			t.last_hit_tick = current_tick
			u.backswing = BACKSWING_TICKS
			var t_order_kind: String = t.order.get("kind", "idle")
			if t.target == null and t_order_kind != "move" and t.alive:
				t.target = u.uid
				if t.anchor == null:
					t.anchor = [t.pos.x, t.pos.y]


# --- facing: R-100-01, R-100-02 ---

func _step_facing(dt: float) -> void:
	for u in units:
		if not u.alive:
			continue
		if QaPlants.is_active("facing-fixed"):
			continue
		var cap: float = float(Roster.TURN_RATE_RAD_S.get(roster.get_category(u.role), 4.0)) * dt
		var desired: float = u.facing
		var has_target := false
		if u.target != null:
			var t = _by_uid.get(u.target)
			if t != null and t.alive and _in_range_of(u, t):
				desired = (t.pos - u.pos).angle()
				has_target = true
		if not has_target and u.moved_this_tick:
			desired = u.last_heading
		u.facing = _turn_toward(u.facing, desired, cap)


func _turn_toward(cur: float, target: float, max_delta: float) -> float:
	var diff := wrapf(target - cur, -PI, PI)
	if abs(diff) <= max_delta:
		return wrapf(target, -PI, PI)
	return wrapf(cur + sign(diff) * max_delta, -PI, PI)


# --- deaths: R-136-02 ---

func _step_deaths() -> void:
	for u in units:
		if u.alive and u.hp <= 0.0:
			u.alive = false
			u.hp = 0.0
			u.death_tick = current_tick


# --- routing: R-097-01..02 ---

func _cell_of(p: Vector2) -> Vector2i:
	return Vector2i(clampi(int(p.x / CELL_SIZE), 0, GRID_DIM - 1), clampi(int(p.y / CELL_SIZE), 0, GRID_DIM - 1))


func _cell_center(c: Vector2i) -> Vector2:
	return Vector2((c.x + 0.5) * CELL_SIZE, (c.y + 0.5) * CELL_SIZE)


func _cell_blocked(c: Vector2i) -> bool:
	return _blocked.get(c, false)


func _build_grid() -> void:
	_blocked.clear()
	for ob in obstacles:
		var c0 := _cell_of(Vector2(float(ob.x0), float(ob.z0)))
		var c1 := _cell_of(Vector2(float(ob.x1), float(ob.z1)))
		for gx in range(min(c0.x, c1.x), max(c0.x, c1.x) + 1):
			for gy in range(min(c0.y, c1.y), max(c0.y, c1.y) + 1):
				_blocked[Vector2i(gx, gy)] = true


func _line_clear(a: Vector2, b: Vector2) -> bool:
	var dist := a.distance_to(b)
	var steps: int = max(1, int(dist / (CELL_SIZE * 0.5)))
	for s in range(steps + 1):
		var p: Vector2 = a.lerp(b, float(s) / float(steps))
		if _cell_blocked(_cell_of(p)):
			return false
	return true


func _compute_route(start: Vector2, dest: Vector2) -> Array:
	if QaPlants.is_active("pass-through") or obstacles.is_empty():
		return [dest]
	if _line_clear(start, dest):
		return [dest]
	var start_c := _cell_of(start)
	var dest_c := _cell_of(dest)
	var path_cells := _bfs(start_c, dest_c)
	if path_cells.is_empty():
		return [dest]
	var waypoints: Array = []
	var i := 0
	while i < path_cells.size() - 1:
		var far: int = path_cells.size() - 1
		while far > i + 1 and not _line_clear(_cell_center(path_cells[i]), _cell_center(path_cells[far])):
			far -= 1
		waypoints.append(_cell_center(path_cells[far]))
		i = far
	waypoints[waypoints.size() - 1] = dest
	return waypoints


func _bfs(start_c: Vector2i, dest_c: Vector2i) -> Array:
	if _cell_blocked(dest_c):
		return []
	var frontier: Array[Vector2i] = [start_c]
	var came_from := {start_c: start_c}
	var head := 0
	var dirs := [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1),
		Vector2i(1, 1), Vector2i(1, -1), Vector2i(-1, 1), Vector2i(-1, -1)]
	while head < frontier.size():
		var cur: Vector2i = frontier[head]
		head += 1
		if cur == dest_c:
			break
		for d in dirs:
			var nxt: Vector2i = cur + d
			if nxt.x < 0 or nxt.y < 0 or nxt.x >= GRID_DIM or nxt.y >= GRID_DIM:
				continue
			if came_from.has(nxt) or _cell_blocked(nxt):
				continue
			came_from[nxt] = cur
			frontier.append(nxt)
	if not came_from.has(dest_c):
		return []
	var path: Array = [dest_c]
	var cur2: Vector2i = dest_c
	while cur2 != start_c:
		cur2 = came_from[cur2]
		path.append(cur2)
	path.reverse()
	return path

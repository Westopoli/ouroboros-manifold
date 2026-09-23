class_name FogTruth
extends RefCounted

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")

const JITTER_MAX_WU := 400.0
const ENEMY_LOOP_RADII_WU: Array[float] = [90.0, 130.0, 170.0, 220.0]

var canvas: float = 6400.0
var seed: int = 11
var tick: int = 0
var phase: String = "recon"

var friendlies: Array = []
var enemies: Array = []
var structures: Array = []
var obstacles: Array = []
var zones: Array = []
var nodes: Array = []

var _rng := RandomNumberGenerator.new()


func load_fixture(fixture_path: String) -> void:
	var f := FileAccess.open(fixture_path, FileAccess.READ)
	var data: Dictionary = JSON.parse_string(f.get_as_text())
	canvas = float(data.get("canvas", canvas))
	obstacles = []
	for o in data.get("obstacles", []):
		obstacles.append({"pos": Vector2(o.pos[0], o.pos[1]), "half_extents": Vector2(o.half_extents[0], o.half_extents[1]), "tall": bool(o.tall)})
	zones = []
	for z in data.get("zones", []):
		zones.append({"kind": String(z.kind), "pos": Vector2(z.pos[0], z.pos[1]), "radius": float(z.radius), "intensity": float(z.get("intensity", 0.0))})
	nodes = []
	for n in data.get("nodes", []):
		nodes.append({"type": String(n.type), "pos": Vector2(n.pos[0], n.pos[1])})
	structures = []
	for s in data.get("structures", []):
		structures.append({"sid": int(s.sid), "pos": Vector2(s.pos[0], s.pos[1])})


func load_scenario(scenario_path: String) -> void:
	var f := FileAccess.open(scenario_path, FileAccess.READ)
	var data: Dictionary = JSON.parse_string(f.get_as_text())
	friendlies = []
	for u in data.get("friendlies", []):
		var wps: Array = []
		for w in u.waypoints:
			wps.append(Vector2(w[0], w[1]))
		friendlies.append({"uid": int(u.uid), "pos": Vector2(u.start[0], u.start[1]), "sensor_wu": float(u.sensor_wu),
			"layer": 0, "waypoints": wps, "wp_idx": 0, "speed": float(u.get("speed", 40.0))})
	enemies = []
	for e in data.get("enemies", []):
		enemies.append({"uid": int(e.uid), "center": Vector2(e.center[0], e.center[1]), "radius": float(e.radius),
			"angular_speed": float(e.angular_speed), "phase_offset": 0.0, "pos": Vector2(e.center[0], e.center[1])})


func generate(p_seed: int) -> void:
	seed = 11 if QaPlants.is_active("seed-ignored") else p_seed
	_rng.seed = seed

	for o in obstacles:
		o.pos += _jitter()
	for z in zones:
		z.pos += _jitter()
	_rotate_interference_zone()
	for s in structures:
		s.pos += _jitter()

	for e in enemies:
		if e.radius > 0.0:
			e.radius = ENEMY_LOOP_RADII_WU[_rng.randi() % ENEMY_LOOP_RADII_WU.size()]
			e.angular_speed = absf(e.angular_speed) * (-1.0 if _rng.randi() % 2 == 0 else 1.0)
		e.phase_offset = _rng.randf_range(0.0, TAU)
		e.pos = e.center + Vector2(e.radius, 0.0).rotated(e.phase_offset)

	for f in friendlies:
		_reorder_waypoints(f)

	tick = 0
	phase = "recon"


func _jitter() -> Vector2:
	return Vector2(_rng.randf_range(-JITTER_MAX_WU, JITTER_MAX_WU), _rng.randf_range(-JITTER_MAX_WU, JITTER_MAX_WU))


func _rotate_interference_zone() -> void:
	var center := Vector2(canvas * 0.5, canvas * 0.5)
	var angle: float = _rng.randf_range(0.0, TAU)
	for z in zones:
		if z.kind == "interference":
			z.pos = center + (z.pos - center).rotated(angle)


func _reorder_waypoints(f: Dictionary) -> void:
	if f.waypoints.size() < 2:
		return
	var n: int = f.waypoints.size()
	var offset: int = _rng.randi() % n
	var reversed: bool = _rng.randi() % 2 == 0
	var base: Array = f.waypoints.duplicate()
	if reversed:
		base.reverse()
	var reordered: Array = []
	for i in range(n):
		reordered.append(base[(i + offset) % n])
	f.waypoints = reordered
	f.wp_idx = 0


func step() -> void:
	if phase != "mission":
		return
	for f in friendlies:
		_advance_friendly(f)
	for e in enemies:
		e.phase_offset += e.angular_speed
		e.pos = e.center + Vector2(e.radius, 0.0).rotated(e.phase_offset)
	tick += 1


func _advance_friendly(f: Dictionary) -> void:
	if f.waypoints.is_empty():
		return
	var target: Vector2 = f.waypoints[f.wp_idx]
	var to_target: Vector2 = target - f.pos
	var dist: float = to_target.length()
	if dist <= f.speed:
		f.pos = target
		f.wp_idx = (f.wp_idx + 1) % f.waypoints.size()
	else:
		f.pos += to_target.normalized() * f.speed


func command_move(uid: int, target: Vector2) -> void:
	for f in friendlies:
		if f.uid == uid:
			f.waypoints = [target]
			f.wp_idx = 0
			return


func interference_at(pos: Vector2) -> float:
	var total := 0.0
	for z in zones:
		if z.kind != "interference":
			continue
		var d: float = pos.distance_to(z.pos)
		if d >= z.radius:
			continue
		total += z.intensity * (1.0 - d / z.radius)
	return clamp(total, 0.0, 1.0)


func _blocked(p0: Vector2, p1: Vector2) -> bool:
	for o in obstacles:
		if not o.tall:
			continue
		if _segment_intersects_aabb(p0, p1, o.pos, o.half_extents):
			return true
	return false


func _segment_intersects_aabb(p0: Vector2, p1: Vector2, center: Vector2, half: Vector2) -> bool:
	var d := p1 - p0
	var lo := center - half
	var hi := center + half
	var t_min := 0.0
	var t_max := 1.0
	for axis in range(2):
		var p0a: float = p0[axis]
		var da: float = d[axis]
		if abs(da) < 0.000001:
			if p0a < lo[axis] or p0a > hi[axis]:
				return false
			continue
		var t1: float = (lo[axis] - p0a) / da
		var t2: float = (hi[axis] - p0a) / da
		if t1 > t2:
			var tmp := t1
			t1 = t2
			t2 = tmp
		t_min = max(t_min, t1)
		t_max = min(t_max, t2)
		if t_min > t_max:
			return false
	return true


func can_see(observer_pos: Vector2, radius_eff: float, target_pos: Vector2) -> bool:
	if observer_pos.distance_to(target_pos) > radius_eff:
		return false
	if not QaPlants.is_active("los-ignored") and _blocked(observer_pos, target_pos):
		return false
	return true


func compute_visibility() -> Dictionary:
	var visible := {}
	var circles := []
	for f in friendlies:
		var interference: float = interference_at(f.pos)
		var radius_eff: float = f.sensor_wu
		if not QaPlants.is_active("radius-ignored"):
			radius_eff = f.sensor_wu * (1.0 - interference)
		circles.append({"uid": f.uid, "pos": f.pos, "radius_eff": radius_eff})
		for e in enemies:
			if visible.has(e.uid):
				continue
			if can_see(f.pos, radius_eff, e.pos):
				visible[e.uid] = true
	var uids: Array = visible.keys()
	uids.sort()
	return {"visible_enemy_uids": uids, "circles": circles}


func compute_hash() -> int:
	var parts: Array = [seed, tick]
	for f in friendlies:
		parts.append(int(round(f.pos.x)))
		parts.append(int(round(f.pos.y)))
	for e in enemies:
		parts.append(int(round(e.pos.x)))
		parts.append(int(round(e.pos.y)))
	for u in compute_visibility().visible_enemy_uids:
		parts.append(u)
	return str(parts).hash()

class_name MissionGen
extends RefCounted

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")

const VANGUARD_SPEED_WU_S := 80.0
const ESCORT_SPEED_WU_S := 60.0
const TICK_HZ := 20.0
const BASE_B_TICKS := 350.0
const MOCKUP_TIME_SCALE := 20.0
const URGENCY_DEFAULT := 0.5
const MIN_OBJECTIVE_DIST_WU := 2000.0
const HOLD_RADIUS_WU := 600.0
const HOLD_REQUIRED_TICKS := 900.0
const HOLD_ENTER_TICK := 200
const HOLD_EXIT_TICK := 300
const SURVIVE_REQUIRED_TICKS := 900.0
const DESTROY_TARGET_COUNT := 3
const DESTROY_TARGET_SPREAD_WU := 300.0
const DESTROY_TICK_INTERVAL := 150
const ELIMINATE_FORCE_COUNT := 8
const ELIMINATE_SPREAD_WU := 500.0
const ELIMINATE_TICK_INTERVAL := 100

const DISPLAY_NAMES := {
	"hold_zone": "Hold the core",
	"destroy_targets": "Destroy the targets",
	"escort_to_extraction": "Escort to extraction",
	"survive_duration": "Survive",
	"eliminate_force": "Destroy the enemy force",
}

const ARCHETYPES := [
	{"name": "defensive_stand", "label": "Defensive Stand", "canvas": "medium", "kind": "hold_zone"},
	{"name": "siege_breaking", "label": "Siege Breaking", "canvas": "large", "kind": "destroy_targets"},
	{"name": "reconquest", "label": "Reconquest", "canvas": "medium", "kind": "hold_zone"},
	{"name": "assault", "label": "Assault", "canvas": "large", "kind": "destroy_targets"},
	{"name": "suppression", "label": "Suppression", "canvas": "small", "kind": "eliminate_force"},
	{"name": "multi_front_defense", "label": "Multi-Front Defense", "canvas": "large", "kind": "hold_zone"},
	{"name": "interception", "label": "Interception", "canvas": "medium", "kind": "destroy_targets"},
	{"name": "rear_guard", "label": "Rear Guard / Evacuation", "canvas": "medium", "kind": "escort_to_extraction"},
	{"name": "containment", "label": "Containment", "canvas": "large", "kind": "hold_zone"},
	{"name": "counterinsurgency", "label": "Counterinsurgency", "canvas": "small", "kind": "eliminate_force"},
]


static func archetype_names() -> Array:
	var out := []
	for row in ARCHETYPES:
		out.append(row.name)
	return out


static func _row(name: String) -> Dictionary:
	for row in ARCHETYPES:
		if row.name == name:
			return row
	return ARCHETYPES[0]


static func time_limit_ticks(urgency: float = URGENCY_DEFAULT) -> float:
	var limit: float = max(BASE_B_TICKS * (1.0 - 0.2 * urgency), 0.6 * BASE_B_TICKS)
	return limit * MOCKUP_TIME_SCALE


static func _seeded_rng(seed_val: int, salt: String) -> RandomNumberGenerator:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_val ^ salt.hash()
	return rng


static func build(archetype_name: String, places: Places, mission_seed: int, kind_override: String = "") -> Dictionary:
	var row := _row(archetype_name)
	var eff_seed: int = 11 if QaPlants.is_active("seed-ignored") else mission_seed
	var kind: String = kind_override if kind_override != "" else row.kind
	if QaPlants.is_active("kind-mapping-random"):
		var kinds := DISPLAY_NAMES.keys()
		var rng := _seeded_rng(eff_seed, archetype_name + "_kindrandom")
		kind = kinds[rng.randi() % kinds.size()]
	var limit := time_limit_ticks()
	var placement := _place(kind, places, eff_seed, limit, archetype_name)
	if QaPlants.is_active("objective-on-spawn"):
		var pspawn: Vector2 = places.player_spawn().pos
		var sat := _check_sat(places, pspawn, pspawn, limit)
		placement = {"ok": sat.ok, "pos": pspawn, "skipped": [], "route_len": sat.route_len}
	var obj_id := "%s_primary" % archetype_name
	var objective := {
		"id": obj_id, "type": kind, "progress": 0.0, "status": "active", "is_primary": true,
		"location": {"x": placement.pos.x, "y": placement.pos.y},
	}
	return {
		"archetype": archetype_name, "label": row.label, "kind": kind,
		"objective": objective, "satisfiable": placement.ok,
		"route_len_wu": placement.route_len, "time_limit_ticks": limit,
		"skipped": placement.skipped, "pos": placement.pos,
		"progress": 0.0, "status": "active", "tick": 0,
		"extra": _build_extra(kind, places, placement.pos, eff_seed, archetype_name),
	}


static func _place(kind: String, places: Places, mission_seed: int, limit: float, salt: String) -> Dictionary:
	match kind:
		"hold_zone":
			return _pick(places.candidates("objective"), places, mission_seed, salt, limit)
		"destroy_targets":
			var cands: Array = places.candidates("chokepoint") + places.candidates("hazard_anchor")
			return _pick(cands, places, mission_seed, salt, limit)
		"survive_duration":
			return _pick(places.candidates("staging"), places, mission_seed, salt, limit)
		"escort_to_extraction":
			return _pick(places.candidates("extraction"), places, mission_seed, salt, limit)
		"eliminate_force":
			return _place_eliminate(places, mission_seed, limit, salt)
	return {"ok": false, "pos": Vector2.ZERO, "skipped": [], "route_len": INF}


static func _pick(cands: Array, places: Places, mission_seed: int, salt: String, limit: float) -> Dictionary:
	if cands.is_empty():
		return {"ok": false, "pos": Vector2.ZERO, "skipped": [], "route_len": INF}
	var player: Vector2 = places.player_spawn().pos
	var start := 0
	if cands.size() > 1:
		start = _seeded_rng(mission_seed, salt).randi() % cands.size()
	var skipped: Array = []
	for i in range(cands.size()):
		var c: Dictionary = cands[(start + i) % cands.size()]
		var sat := _check_sat(places, player, c.pos, limit)
		if sat.ok:
			return {"ok": true, "pos": c.pos, "skipped": skipped, "route_len": sat.route_len}
		skipped.append(c.id)
	return {"ok": false, "pos": cands[start].pos, "skipped": skipped, "route_len": INF}


static func _place_eliminate(places: Places, mission_seed: int, limit: float, salt: String) -> Dictionary:
	var enemy: Dictionary = places.enemy_spawn()
	if enemy.is_empty():
		return {"ok": false, "pos": Vector2.ZERO, "skipped": [], "route_len": INF}
	var rng := _seeded_rng(mission_seed, salt)
	var ang := rng.randf_range(0.0, TAU)
	var rad := rng.randf_range(0.0, 300.0)
	var pos: Vector2 = (enemy.pos + Vector2(cos(ang), sin(ang)) * rad).clamp(Vector2.ZERO, Vector2.ONE * places.canvas)
	var sat := _check_sat(places, places.player_spawn().pos, pos, limit)
	var skipped: Array = [] if sat.ok else [enemy.id]
	return {"ok": sat.ok, "pos": pos, "skipped": skipped, "route_len": sat.route_len}


static func _check_sat(places: Places, player: Vector2, pos: Vector2, limit: float) -> Dictionary:
	if pos.x < 0.0 or pos.x > places.canvas or pos.y < 0.0 or pos.y > places.canvas:
		return {"ok": false, "route_len": INF}
	if player.distance_to(pos) < MIN_OBJECTIVE_DIST_WU:
		return {"ok": false, "route_len": player.distance_to(pos)}
	var route_len: float
	if QaPlants.is_active("route-ignored"):
		route_len = player.distance_to(pos)
	else:
		route_len = places.route_length(player, pos)
	if route_len == INF:
		return {"ok": false, "route_len": route_len}
	var travel_ticks: float = (route_len / VANGUARD_SPEED_WU_S) * TICK_HZ
	return {"ok": travel_ticks <= limit, "route_len": route_len}


static func _build_extra(kind: String, places: Places, pos: Vector2, mission_seed: int, salt: String) -> Dictionary:
	match kind:
		"destroy_targets":
			return {"targets": _scatter(pos, mission_seed, salt + "_boxes", DESTROY_TARGET_COUNT, DESTROY_TARGET_SPREAD_WU), "destroyed": 0}
		"eliminate_force":
			return {"enemies": _scatter(pos, mission_seed, salt + "_boxes", ELIMINATE_FORCE_COUNT, ELIMINATE_SPREAD_WU), "destroyed": 0}
		"escort_to_extraction":
			var player: Vector2 = places.player_spawn().pos
			var path: Array = places.route_path(player, pos)
			if path.is_empty():
				path = [player, pos]
			path = _jitter_polyline(path, _seeded_rng(mission_seed, salt + "_jitter"))
			return {"route": path, "traveled_wu": 0.0, "route_total_wu": max(_polyline_length(path), 1.0)}
		"survive_duration":
			return {"elapsed_ticks": 0.0}
		"hold_zone":
			return {"elapsed_progress_ticks": 0.0}
	return {}


static func _scatter(center: Vector2, mission_seed: int, salt: String, n: int, spread: float) -> Array:
	var rng := _seeded_rng(mission_seed, salt)
	var out: Array = []
	for i in range(n):
		var ang := rng.randf_range(0.0, TAU)
		var rad := rng.randf_range(50.0, spread)
		out.append({"pos": center + Vector2(cos(ang), sin(ang)) * rad, "destroyed": false})
	return out


static func _jitter_polyline(path: Array, rng: RandomNumberGenerator) -> Array:
	if path.size() < 3:
		return path
	var out: Array = path.duplicate()
	for i in range(1, out.size() - 1):
		var dir: Vector2 = out[i + 1] - out[i - 1]
		var normal := Vector2(-dir.y, dir.x).normalized() if dir.length() > 0.01 else Vector2.ZERO
		out[i] = out[i] + normal * rng.randf_range(-80.0, 80.0)
	return out


static func _polyline_length(path: Array) -> float:
	var total := 0.0
	for i in range(1, path.size()):
		total += path[i - 1].distance_to(path[i])
	return total


static func tick(m: Dictionary, dt: int) -> void:
	if m.status != "complete" and not QaPlants.is_active("progress-static"):
		match m.kind:
			"hold_zone": _tick_hold(m, dt)
			"destroy_targets": _tick_destroy(m, dt)
			"escort_to_extraction": _tick_escort(m, dt)
			"survive_duration": _tick_survive(m, dt)
			"eliminate_force": _tick_eliminate(m, dt)
	m.tick += dt
	m.objective.progress = m.progress
	m.objective.status = m.status


static func _tick_hold(m: Dictionary, dt: int) -> void:
	var elapsed: float = m.extra.get("elapsed_progress_ticks", 0.0)
	for t in range(m.tick, m.tick + dt):
		if not (t >= HOLD_ENTER_TICK and t < HOLD_EXIT_TICK):
			elapsed += 1.0
	m.extra["elapsed_progress_ticks"] = elapsed
	m.progress = clampf(elapsed / HOLD_REQUIRED_TICKS, 0.0, 1.0)
	if m.progress >= 1.0:
		m.status = "complete"


static func _tick_destroy(m: Dictionary, dt: int) -> void:
	var destroyed: int = m.extra.get("destroyed", 0)
	var targets: Array = m.extra.targets
	for t in range(m.tick + 1, m.tick + dt + 1):
		if t % DESTROY_TICK_INTERVAL == 0 and destroyed < targets.size():
			targets[destroyed].destroyed = true
			destroyed += 1
	m.extra["destroyed"] = destroyed
	m.progress = clampf(float(destroyed) / float(max(targets.size(), 1)), 0.0, 1.0)
	if m.progress >= 1.0:
		m.status = "complete"


static func _tick_escort(m: Dictionary, dt: int) -> void:
	var traveled: float = m.extra.get("traveled_wu", 0.0) + (ESCORT_SPEED_WU_S / TICK_HZ) * dt
	m.extra["traveled_wu"] = traveled
	m.progress = clampf(traveled / float(m.extra.route_total_wu), 0.0, 1.0)
	if m.progress >= 1.0:
		m.status = "complete"


static func _tick_survive(m: Dictionary, dt: int) -> void:
	var elapsed: float = m.extra.get("elapsed_ticks", 0.0) + dt
	m.extra["elapsed_ticks"] = elapsed
	m.progress = clampf(elapsed / SURVIVE_REQUIRED_TICKS, 0.0, 1.0)
	if m.progress >= 1.0:
		m.status = "complete"


static func _tick_eliminate(m: Dictionary, dt: int) -> void:
	var destroyed: int = m.extra.get("destroyed", 0)
	var enemies: Array = m.extra.enemies
	for t in range(m.tick + 1, m.tick + dt + 1):
		if t % ELIMINATE_TICK_INTERVAL == 0 and destroyed < enemies.size():
			enemies[destroyed].destroyed = true
			destroyed += 1
	m.extra["destroyed"] = destroyed
	m.progress = clampf(float(destroyed) / float(max(enemies.size(), 1)), 0.0, 1.0)
	if m.progress >= 1.0:
		m.status = "complete"


static func mission_hash(m: Dictionary) -> int:
	var canon := {
		"archetype": m.archetype, "kind": m.kind, "objective": m.objective,
		"satisfiable": m.satisfiable, "route_len_wu": snappedf(min(m.route_len_wu, 999999.0), 0.01),
		"skipped": m.skipped, "extra_pos": _extra_positions(m),
	}
	return JSON.stringify(canon).hash()


static func _extra_positions(m: Dictionary) -> Array:
	var out: Array = []
	var extra: Dictionary = m.extra
	if extra.has("targets"):
		for t in extra.targets:
			out.append([snappedf(t.pos.x, 0.01), snappedf(t.pos.y, 0.01)])
	if extra.has("enemies"):
		for e in extra.enemies:
			out.append([snappedf(e.pos.x, 0.01), snappedf(e.pos.y, 0.01)])
	if extra.has("route"):
		for pt in extra.route:
			out.append([snappedf(pt.x, 0.01), snappedf(pt.y, 0.01)])
	return out

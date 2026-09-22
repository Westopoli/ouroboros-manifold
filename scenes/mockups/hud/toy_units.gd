extends RefCounted

const UNIT_COUNT := 24
const FRIENDLY_COUNT := 16
const SPEED_WU_S := 40.0
const DT := 1.0 / 20.0
const CANVAS := 6000.0
const MARGIN := 300.0
const WAYPOINTS_PER_UNIT := 4
const DECAY_UIDS := [3, 9, 15]
const DECAY_PER_TICK := 0.05

var _units: Dictionary = {}
var _order: Array[int] = []


func generate(seed_val: int) -> void:
	_units.clear()
	_order.clear()
	for i in range(UNIT_COUNT):
		var uid := i + 1
		var faction := "player" if i < FRIENDLY_COUNT else "enemy"
		var layer := 1 if i % 2 == 0 else 2
		var rng := RandomNumberGenerator.new()
		rng.seed = seed_val * 1000003 + uid
		var wps: Array = []
		for w in range(WAYPOINTS_PER_UNIT):
			wps.append(Vector2(rng.randf_range(MARGIN, CANVAS - MARGIN), rng.randf_range(MARGIN, CANVAS - MARGIN)))
		_units[uid] = {"uid": uid, "faction": faction, "layer": layer, "pos": wps[0], "hp": 100.0,
			"_wp": wps, "_wi": 1}
		_order.append(uid)


func step() -> void:
	for uid in _order:
		var r: Dictionary = _units[uid]
		if r.hp <= 0.0:
			continue
		_advance(r)
		if DECAY_UIDS.has(uid):
			r.hp = maxf(0.0, r.hp - DECAY_PER_TICK)


func _advance(r: Dictionary) -> void:
	var wps: Array = r["_wp"]
	var target: Vector2 = wps[r["_wi"]]
	var to_target: Vector2 = target - r["pos"]
	var dist := to_target.length()
	var step_dist := SPEED_WU_S * DT
	if dist <= step_dist:
		r["pos"] = target
		r["_wi"] = (r["_wi"] + 1) % wps.size()
	else:
		r["pos"] = r["pos"] + to_target.normalized() * step_dist


func command_move(uids: Array, target: Vector2) -> void:
	for uid in uids:
		if not _units.has(uid):
			continue
		var r: Dictionary = _units[uid]
		r["_wp"] = [r["pos"], target]
		r["_wi"] = 1


func get_all() -> Dictionary:
	var out: Dictionary = {}
	for uid in _order:
		var r: Dictionary = _units[uid]
		out[uid] = {"uid": uid, "faction": r.faction, "layer": r.layer, "pos": r.pos, "hp": r.hp}
	return out


func get_alive() -> Dictionary:
	var out: Dictionary = {}
	for uid in _order:
		var r: Dictionary = _units[uid]
		if r.hp > 0.0:
			out[uid] = {"uid": uid, "faction": r.faction, "layer": r.layer, "pos": r.pos, "hp": r.hp}
	return out


func compute_hash() -> int:
	var parts: Array = []
	for uid in _order:
		var r: Dictionary = _units[uid]
		parts.append([uid, r.layer, int(round(r.pos.x * 100.0)), int(round(r.pos.y * 100.0)), int(round(r.hp * 100.0))])
	return hash(parts)

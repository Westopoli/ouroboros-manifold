class_name ToySim
extends RefCounted

const TICK_HZ := 20.0
const MOVE_SPEED_WU_S := 80.0
const TRANSITION_TICKS := {"fast": 20, "slow": 100}

var canvas_wu: float = 4000.0
var obstacle_pos: Vector2 = Vector2.ZERO
var obstacle_size: Vector2 = Vector2.ZERO
var blocked_center: Vector2 = Vector2.ZERO
var blocked_radius: float = 0.0
var vantage_pos: Vector2 = Vector2.ZERO

var tick: int = 0
var units: Dictionary = {}
var debug_use_global_rng: bool = false


func load_fixture(path: String) -> void:
	pass


func generate(seed_n: int) -> void:
	tick = 0
	units = {
		1: _stub_unit(1, "fast"),
		2: _stub_unit(2, "slow"),
		101: _stub_unit(101, "enemy"),
		102: _stub_unit(102, "enemy"),
		103: _stub_unit(103, "enemy"),
	}


func _stub_unit(uid: int, type_name: String) -> Dictionary:
	return {
		"uid": uid, "type": type_name, "faction": 0 if uid < 100 else 1,
		"pos": Vector2.ZERO, "layer": 1, "pending": false, "pending_target": null,
		"transition": null, "move_target": null, "sensor_wu": 0.0,
	}


func is_blocked(layer: int, pos: Vector2) -> bool:
	return false


func transfer(uid: int, layer: int) -> void:
	if units.has(uid):
		units[uid].pending = true


func move(uid: int, x: float, z: float) -> void:
	pass


func step(n: int = 1) -> void:
	tick += n


func tick_avg_ms() -> float:
	return 0.0


func visible_by(uid: int) -> Array:
	return []


func visible_enemy_uids() -> Array:
	return []


func compute_hash() -> int:
	return 0

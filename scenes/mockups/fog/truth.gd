class_name FogTruth
extends RefCounted

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


func load_fixture(_fixture_path: String) -> void:
	pass


func load_scenario(_scenario_path: String) -> void:
	pass


func generate(_p_seed: int) -> void:
	pass


func step() -> void:
	pass


func park_friendly(_uid: int, _x: float, _z: float) -> void:
	pass


func command_move(_uid: int, _target: Vector2) -> void:
	pass


func interference_at(_pos: Vector2) -> float:
	return 0.0


func can_see(_observer_pos: Vector2, _radius_eff: float, _target_pos: Vector2) -> bool:
	return false


func compute_visibility() -> Dictionary:
	return {"visible_enemy_uids": [], "circles": []}


func compute_hash() -> int:
	return 0

extends Node3D

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")

const PLANTS: Array[String] = [
	"objective-on-spawn", "marker-unnamed", "progress-static",
	"kind-mapping-random", "seed-ignored", "route-ignored",
]


func qa_state() -> Dictionary:
	return {
		"seed": 11, "hash": 0, "fixture": 11, "archetype": "defensive_stand",
		"objective": {"id": "", "type": "", "progress": 0.0, "status": "active", "is_primary": true, "location": {"x": 0.0, "y": 0.0}},
		"satisfiable": false, "route_len_wu": 0.0, "time_limit_ticks": 0.0, "skipped": [],
		"marker": {"name": "", "px": [0.0, 0.0]}, "tick": 0,
		"timing_ms": {"gen": 0.0}, "regen_count": 0,
	}


func qa_plant(id: String) -> bool:
	if not PLANTS.has(id):
		return false
	QaPlants.activate(id)
	return true


func qa_seed(n: int) -> void:
	pass


func qa_set(name: String, value) -> void:
	pass


func qa_camera(height: float, x: float, z: float) -> void:
	pass


func qa_tick(n: int) -> void:
	pass

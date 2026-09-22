extends Node3D

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")

const PLANTS: Array[String] = ["box-one-layer", "group-shared", "select-all-exists",
	"camera-unbounded", "clock-wallclock", "narrow-moves-focus"]


func qa_state() -> Dictionary:
	return {"seed": 0, "hash": 0, "tick": 0, "clock_s": 0.0, "selected": [], "groups": {},
		"focus_layer": 1, "camera": {"height": 0.0, "x": 0.0, "z": 0.0},
		"bounds": {"min_x": 0.0, "max_x": 0.0, "min_z": 0.0, "max_z": 0.0},
		"units": {}, "units_px": {}, "commands": [], "objective": {"name": "", "progress": 0.0},
		"timing_ms": {"tick_avg": 0.0}, "regen_count": 0}


func qa_plant(id: String) -> bool:
	if not PLANTS.has(id):
		return false
	QaPlants.activate(id)
	return true


func qa_seed(_n: int) -> void:
	pass


func qa_set(_name: String, _value) -> void:
	pass


func qa_camera(_height: float, _x: float, _z: float) -> void:
	pass


func qa_tick(_n: int) -> void:
	pass


func qa_select(_uids: Array) -> void:
	pass


func qa_bind(_digit: int) -> void:
	pass


func qa_recall(_digit: int) -> void:
	pass


func qa_narrow(_layer: int) -> void:
	pass

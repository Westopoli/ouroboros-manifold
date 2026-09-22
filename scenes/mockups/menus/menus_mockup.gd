extends Control

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")

const PLANTS: Array[String] = [
	"band-random",
	"briefing-two-sections",
	"difficulty-dropped",
	"flow-skips-setup",
	"four-bands",
	"digits-in-prose",
]


func qa_state() -> Dictionary:
	return {
		"seed": 0,
		"hash": 0,
		"screen": "title",
		"difficulty": "",
		"campaigns": [],
		"briefing": {"title": "", "sections": [], "attacker_named": false, "has_digits": false},
		"resolve": null,
		"controls": [],
		"timing_ms": {"swap": 0},
		"regen_count": 0,
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


func qa_go(action: String) -> void:
	pass

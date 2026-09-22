extends RefCounted

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")


static func final_score(o: float, r: float) -> float:
	return 0.0


static func band_for(final: float, thresholds: Array) -> String:
	return ""


static func resolve(parity: float, difficulty: String, seed: int, thresholds: Array, force_size: int = 12) -> Dictionary:
	return {"score": 0.0, "band": "", "casualties": 0, "retention": 0.0}

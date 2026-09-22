extends RefCounted

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")

const DIFFICULTY_FACTORS := {"easy": 1.15, "medium": 1.0, "hard": 0.85}
const DEFAULT_FORCE_SIZE := 12

const THRESHOLDS := {
	"defensive_stand": [0.20, 0.40, 0.60, 0.80],
	"siege_breaking": [0.20, 0.40, 0.60, 0.80],
}


static func final_score(o: float, r: float) -> float:
	return 0.75 * o + 0.25 * r


static func band_for(final: float, thresholds: Array) -> String:
	if final < thresholds[0]:
		return "total_failure"
	if final < thresholds[1]:
		return "total_failure" if QaPlants.is_active("four-bands") else "partial_failure"
	if final < thresholds[2]:
		return "partial_success"
	if final < thresholds[3]:
		return "strong_success"
	return "total_success"


static func _seeded_roll(seed: int) -> float:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed
	return rng.randf_range(-0.15, 0.15)


static func resolve(parity: float, difficulty: String, seed: int, thresholds: Array, force_size: int = DEFAULT_FORCE_SIZE) -> Dictionary:
	var effective_difficulty: String = "medium" if QaPlants.is_active("difficulty-dropped") else difficulty
	var factor: float = DIFFICULTY_FACTORS.get(effective_difficulty, 1.0)
	var roll: float = randf_range(-0.15, 0.15) if QaPlants.is_active("band-random") else _seeded_roll(seed)
	var o: float = clamp(parity * factor + roll, 0.0, 1.0)
	var r: float = clamp(0.55 + 0.5 * o + roll / 2.0, 0.0, 1.0)
	var final: float = final_score(o, r)
	var band: String = band_for(final, thresholds)
	var casualties: int = int(round((1.0 - r) * float(force_size)))
	return {"score": final, "band": band, "casualties": casualties, "retention": r}

extends RefCounted

# Lays out one Vector3 per region id in a uniform ball, seeded. C5 rule
# (docs/architecture.md "C transport v1"): the server never transmits
# positions, so the client owns layout. Same region-id set + same seed
# always yields the same positions (determinism contract, CLAUDE.md).

# B23 (spec rev 12b): the prototype's values as run, origin/push/galaxy-field at 99f35887 (CIV_SCALE 0.5 at galaxy_gen.gd:7).
const CIV_SCALE := 0.5   # prototype galaxy_gen.gd:7
const R_BALL := 50.0   # prototype galaxy_gen.gd:8 BALL_RADIUS 100 x CIV_SCALE
const MIN_SPACING := 11.0   # prototype galaxy_gen.gd:11, 22 x CIV_SCALE, now in 3D
const PLACEMENT_ATTEMPTS := 250   # prototype galaxy_gen.gd:48 (250 per system)

var _fallbacks := 0


# Count of ids the last layout() placed unchecked after PLACEMENT_ATTEMPTS misses.
func last_fallbacks() -> int:
	return _fallbacks


func layout(region_ids: Array, p_seed: int) -> Dictionary:
	var rng := RandomNumberGenerator.new()
	rng.seed = p_seed
	_fallbacks = 0
	var sorted_ids: Array = region_ids.duplicate()
	sorted_ids.sort()
	var placed: Array[Vector3] = []
	var positions := {}
	for id in sorted_ids:
		var pos := _place_one(rng, placed)
		placed.append(pos)
		positions[id] = pos
	return positions


func _place_one(rng: RandomNumberGenerator, placed: Array[Vector3]) -> Vector3:
	var candidate := Vector3.ZERO
	for _attempt in range(PLACEMENT_ATTEMPTS):
		# prototype galaxy_gen.gd:50-54: uniform ball, r = R_BALL * cbrt(randf), uniform direction
		var r := R_BALL * pow(rng.randf(), 1.0 / 3.0)
		var cos_phi := rng.randf_range(-1.0, 1.0)
		var sin_phi := sqrt(1.0 - cos_phi * cos_phi)
		var theta := rng.randf() * TAU
		candidate = Vector3(cos(theta) * sin_phi, cos_phi, sin(theta) * sin_phi) * r
		var ok := true
		for p in placed:
			if p.distance_to(candidate) < MIN_SPACING:   # prototype galaxy_gen.gd:56-59
				ok = false
				break
		if ok:
			return candidate
	# Every attempt hit a neighbour: keep the last sample unchecked rather than stall (still seeded and
	# deterministic), and count it; qa_state reports it as layout_fallbacks.
	_fallbacks += 1
	return candidate

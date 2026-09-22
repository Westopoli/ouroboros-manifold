class_name GalaxyGen
extends RefCounted

# Lays out one Vector3 per region id on a jittered disc, seeded. C5 rule
# (docs/architecture.md "C transport v1"): the server never transmits
# positions, so the client owns layout. Same region-id set + same seed
# always yields the same positions (determinism contract, CLAUDE.md).

const DISC_RADIUS := 40.0
const Y_JITTER := 3.0
const MIN_SPACING := 3.0
const PLACEMENT_ATTEMPTS := 250


func layout(region_ids: Array, p_seed: int) -> Dictionary:
	var rng := RandomNumberGenerator.new()
	rng.seed = p_seed
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
	var attempts := 0
	while attempts < PLACEMENT_ATTEMPTS:
		attempts += 1
		var r := DISC_RADIUS * pow(rng.randf(), 1.6)
		var theta := rng.randf() * TAU
		var x := cos(theta) * r
		var z := sin(theta) * r
		var ok := true
		for p in placed:
			if Vector2(p.x, p.z).distance_to(Vector2(x, z)) < MIN_SPACING:
				ok = false
				break
		if ok:
			var y := rng.randf_range(-Y_JITTER, Y_JITTER)
			return Vector3(x, y, z)
	# Spacing rejection can exhaust its attempts on a dense id set; fall back
	# to an unchecked sample rather than stall placement (still seeded and
	# deterministic since it consumes the same rng stream either way).
	var theta2 := rng.randf() * TAU
	var r2 := DISC_RADIUS * rng.randf()
	return Vector3(cos(theta2) * r2, rng.randf_range(-Y_JITTER, Y_JITTER), sin(theta2) * r2)

extends "res://tests/support/vg_c_case.gd"

# VG-C piece C4 (scenes/ground3d/ground_pick.gd): projection + terrain pick against fixture heights
# (K0's `heights`, no live pipe). Proves S-236 / S-207 R-207-06 (a click lands on the ground a unit can
# stand on): height_at is bilinear between cell centres like csrc/terrain.c ts_height_q; pick marches a
# ray against that surface, not the flat plane y = 0 (scout 4: map_view.gd's flat pick is wrong on hills).
# Tolerance 1.0 wu is the test's own geometric epsilon, not a game threshold.
# CONTROL: the flat-plane intersection of the same ray misses the hill hit by more than 1 wu.

const EPS := 1.0


func _run() -> void:
	var gp := _load(SCENES + "ground_pick.gd")
	if gp == null:
		return
	var fx := _fixture()
	var t: Dictionary = fx.terrain()
	for c in [Vector2i(0, 0), Vector2i(3, 2), Vector2i(7, 5)]:
		var wx: float = (c.x + 0.5) * fx.CELL_WU
		var wy: float = (c.y + 0.5) * fx.CELL_WU
		_check(absf(gp.height_at(t, wx, wy) - fx.heights_cm(c.x, c.y) / 100.0) < 0.01, "S-236: height_at at cell centre %s is not heights[]/100" % c)
	_check(absf(gp.height_at(t, 300.0, 200.0) - fx.ground_y(300.0, 200.0)) < 0.01, "S-236: height_at between centres is not bilinear")
	_check(absf(gp.height_at(t, -50.0, -50.0) - fx.ground_y(0.0, 0.0)) < 0.01, "R-207-07: height_at off the map must clamp to the edge cell, not extrapolate")
	var p3: Vector3 = gp.world_to_3d(t, 300.0, 200.0)
	_check(p3.is_equal_approx(Vector3(300.0, fx.ground_y(300.0, 200.0), 200.0)), "S-236: world_to_3d must be Vector3(x, height, y)")
	var target := Vector3(450.0, fx.ground_y(450.0, 300.0), 300.0)
	var origin := Vector3(250.0, 900.0, 100.0)
	var dir := (target - origin).normalized()
	var hit = gp.pick(t, origin, dir)
	_check(hit is Vector2, "S-236: pick must return the world Vector2 where the ray meets the ground")
	if hit is Vector2:
		_check(hit.distance_to(Vector2(450.0, 300.0)) < EPS, "S-236: pick missed the known ground point by %.2f wu" % hit.distance_to(Vector2(450.0, 300.0)))
		var flat_t := -origin.y / dir.y
		var flat := Vector2(origin.x + dir.x * flat_t, origin.z + dir.z * flat_t)
		_check(flat.distance_to(Vector2(450.0, 300.0)) > EPS, "CONTROL: the flat-plane hit equals the hill hit, the fixture has no relief")
	_check(gp.pick(t, origin, Vector3.UP) == null, "R-207-07: a ray pointing away from the ground must return null")

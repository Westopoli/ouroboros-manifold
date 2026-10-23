extends "res://tests/support/vg_c_case.gd"
# Rule pins: R-207-06@5c987f, R-207-07@b117fc

# VG-C piece C4 (scenes/ground3d/ground_pick.gd): projection + terrain pick against fixture heights
# (K0's `heights`, no live pipe). Proves S-236 / S-207 R-207-06 (a click lands on the ground a unit can
# stand on): height_at is bilinear between cell centres like csrc/terrain.c ts_height_q; pick marches a
# ray against that surface, not the flat plane y = 0 (scout 4: map_view.gd's flat pick is wrong on hills).
# Tolerance 1.0 wu is the test's own geometric epsilon, not a game threshold.
# CONTROL: the flat-plane intersection of the same ray misses the hill hit by more than 1 wu.
# VG-C-groundpick-step (FINDING-groundpick-march-skips-crest, spec paragraph "VG-C-groundpick-step"): a crest thinner
# than the old 50 wu march step must still stop the ray, so the pick lands on the crest, nearer the camera than a unit
# behind it. Fixture is test-local (no vg_c_fixture): a ridge one cell wide on a flat map, a gently falling ray.
# CONTROL: an in-test march at the old 50 wu step skips the same crest (the fixture is thin enough to be red for the
# stated reason); the same march at 25 wu finds it. UNSTATED INTERFACE: the spec gives no crest height or ray, so
# ridge height 2000 cm at cell column 5 (peak x = 550 wu), ray z = 300, start x = 25, drop 0.001 wu per wu, unit at x = 900;
# the 20 wu-wide crest span at 90% height is derived from the 100 wu cell tent, not a game threshold.

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

	_thin_crest(gp)


# Flat map 12 x 6 cells with one ridge column (index 5, peak 20 wu); a ray falling 0.001 wu per wu runs at
# about 18 wu over the crest, where the tent is only ~20 wu wide, so 50 wu samples (525, 575) straddle it.
func _thin_crest(gp: GDScript) -> void:
	var w := 12
	var h := 6
	var hs := PackedInt32Array()
	hs.resize(w * h)
	for j in h:
		hs[j * w + 5] = 2000
	var t := {"cells_w": w, "cells_h": h, "heights": hs}
	var origin := Vector3(25.0, 18.3, 300.0)
	var dir := Vector3(1.0, -0.001, 0.0).normalized()
	var unit_x := 900.0
	_check(_march_hits(gp, t, origin, dir, 50.0) < 0.0, "CONTROL: a 50 wu march must skip this crest, the fixture is not thinner than the old step")
	_check(_march_hits(gp, t, origin, dir, 25.0) > 0.0, "CONTROL: a 25 wu march must find this crest, the fixture is not catchable")
	var hit = gp.pick(t, origin, dir)
	_check(hit is Vector2, "S-236: pick through a crest thinner than 50 wu returned no hit at all (the ray passed through the ridge)")
	if hit is Vector2:
		_check(hit.x < unit_x - 100.0, "S-236: pick hit x=%.1f, not nearer the camera than the unit at x=%.0f: the crest did not occlude it" % [hit.x, unit_x])
		_check(absf(hit.x - 550.0) < 30.0, "S-236: pick hit x=%.1f is not on the crest near x=550" % hit.x)


# x of the first below-surface sample of a march at `step` wu, -1 when the march never dips under the terrain.
func _march_hits(gp: GDScript, t: Dictionary, origin: Vector3, dir: Vector3, step: float) -> float:
	var s := 0.0
	while s < 2000.0:
		var p := origin + dir * s
		if p.y <= gp.height_at(t, p.x, p.z):
			return p.x
		s += step
	return -1.0

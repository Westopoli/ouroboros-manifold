extends "res://tests/support/vg_c_case.gd"

# VG-C piece C8, PARKED (Westley's number): the largest surface deviation between two adjacent detail levels at the
# height where the renderer switches, in wu. S-236 R-236-01 says "no pop"; how much deviation is invisible is his call
# (spec section 4: threshold checks live in their own *_park_* file). NOPOP_MAX_DEVIATION_WU is null until he sets it.
# API as test_vg_c8_ground_lod.gd plus GroundLod.switch_height(level) -> float and surface_at(level, wx, wy) -> float.
# Red today: ground_lod.gd does not exist; after it lands the file stays red until the number is set.

const NOPOP_MAX_DEVIATION_WU = null


func _run() -> void:
	var gl := _load(SCENES + "ground_lod.gd")
	if gl == null:
		return
	var tol: Variant = NOPOP_MAX_DEVIATION_WU
	_check(tol != null, "PARKED: Westley has not set NOPOP_MAX_DEVIATION_WU (R-236-01 no-pop tolerance)")
	if tol == null:
		return
	var fx := _fixture()
	var lod = gl.new()
	lod.set_terrain(fx.terrain())
	for l in range(lod.level_count() - 1):
		var worst := 0.0
		for j in fx.H:
			for i in fx.W:
				var wx: float = (i + 0.5) * fx.CELL_WU
				var wy: float = (j + 0.5) * fx.CELL_WU
				worst = maxf(worst, absf(lod.surface_at(l, wx, wy) - lod.surface_at(l + 1, wx, wy)))
		_check(worst <= float(tol), "R-236-01: levels %d and %d deviate by %.2f wu" % [l, l + 1, worst])

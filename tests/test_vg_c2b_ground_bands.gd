extends "res://tests/support/vg_c_case.gd"

# VG-C piece C2b (scenes/ground3d/ground_bands.gd). Proves S-236 R-236-02 and S-001 R-001-01: ground colour is
# the band ramp plus the steep tint plus the walkable mask (spec section 7: "ground colour band ramp +
# steep tint + walkable"; the sim has no zones or water). API: GroundBands.colour(band 1..5, walkable) -> Color.
# Positive control: an unwalkable cell must differ from a walkable one of the same band.


func _run() -> void:
	var gb := _load(SCENES + "ground_bands.gd")
	if gb == null:
		return
	var seen := {}
	for b in range(1, 6):
		var c: Color = gb.colour(b, true)
		seen[c.to_html()] = true
		var steep: Color = gb.colour(b, false)
		_check(steep != c, "R-001-01: band %d unwalkable colour equals walkable (blocked ground is not visible)" % b)
	_check(seen.size() == 5, "R-236-02: the five bands do not have five distinct colours (%d)" % seen.size())
	_check(gb.colour(0, true) == gb.colour(1, true) and gb.colour(9, true) == gb.colour(5, true),
		"R-236-02: out-of-range bands must clamp to 1..5 (terrain_layer.gd clamps the same way)")
	var fx := _fixture()
	var t: Dictionary = fx.terrain()
	var cols = gb.cell_colours(t)
	_check(cols is PackedColorArray and cols.size() == fx.W * fx.H, "S-236: cell_colours(terrain) must return one colour per cell")
	if cols is PackedColorArray and cols.size() == fx.W * fx.H:
		var blocked: int = 4 * fx.W + 5
		_check(cols[blocked] == gb.colour(int((t["bands"] as PackedByteArray)[blocked]), false), "R-001-01: the blocked cell (5,4) is not drawn with the steep tint")
		_check(cols[0] == gb.colour(int((t["bands"] as PackedByteArray)[0]), true), "S-236: a walkable cell does not use the plain band colour")

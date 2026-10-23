extends "res://tests/support/vg_c_case.gd"
# Rule pins: R-236-02@d5ddad, R-010-01@b3e461, R-005-09@dd0832, R-004-06@ebf993, R-001-01@025bc6

# VG-C piece C2b (scenes/ground3d/ground_bands.gd) rewritten by VG-C-ground-one-colour under TD-VG-C-one-colour.
# Proves S-236 R-236-02 (a step between bands is the real height difference, not a colour) and S-001 R-001-01 (blocked
# ground stays visible). Layer changes are told by height (R-010-01) and sight (R-005-09, R-004-06), not by landscape colour.
# API: GroundBands.colour(band, walkable) -> Color; GroundBands.GROUND_COLOUR (DRAFT-ground-colour, 0.40, 0.72, 0.42);
# STEEP_COLOUR and STEEP_MIX (0.5) stay; cell_colours(terrain) -> PackedColorArray.
# TD-VG-C-one-colour retires, from main's version of this file: the "five distinct colours" assertion (main line 23,
# `seen.size() == 5`) and the "walkable cell uses the plain band colour" assertion's per-band reading (main line 30) is kept
# in the form cols[0] == colour(band, true). The unwalkable-differs control (main line 20) and the clamp check (main line 24)
# are kept (clamp now trivially true). Other results as on main.
# POSITIVE CONTROL (the spec's): on main colour(1, true) != colour(5, true), so the same-colour test is red for the stated reason.
# UNSTATED INTERFACE choice: GROUND_COLOUR is read as a constant on the GroundBands script (gb.GROUND_COLOUR); on main it
# does not exist (red, reason b). "Differs" for the blocked tint is Color inequality, exactly as main.


func _run() -> void:
	var gb := _load(SCENES + "ground_bands.gd")
	if gb == null:
		return
	var first: Color = gb.colour(1, true)
	for b in range(1, 6):
		var c: Color = gb.colour(b, true)
		_check(c == first, "R-236-02: colour(%d, true) = %s differs from colour(1, true) = %s (ground is one colour)" % [b, c.to_html(), first.to_html()])
		var steep: Color = gb.colour(b, false)
		_check(steep != c, "R-001-01: band %d unwalkable colour equals walkable (blocked ground is not visible)" % b)
	var consts: Dictionary = gb.get_script_constant_map()
	_check(consts.has("GROUND_COLOUR"), "R-236-02: GroundBands has no GROUND_COLOUR constant")
	_check(not consts.has("BAND_COLOURS"), "R-236-02: BAND_COLOURS still exists beside GROUND_COLOUR")
	if consts.has("GROUND_COLOUR"):
		var g: Color = consts["GROUND_COLOUR"]
		_check(g.is_equal_approx(Color(0.40, 0.72, 0.42)), "R-236-02: GROUND_COLOUR is %s, want (0.40, 0.72, 0.42) DRAFT-ground-colour" % g)
		for b in range(1, 6):
			_check(gb.colour(b, true) == g, "R-236-02: colour(%d, true) is not GROUND_COLOUR" % b)
			_check(gb.colour(b, false) == g.lerp(consts["STEEP_COLOUR"], consts["STEEP_MIX"]), "R-001-01: colour(%d, false) is not GROUND_COLOUR lerped STEEP_MIX to STEEP_COLOUR" % b)
	_check(gb.colour(0, true) == gb.colour(1, true) and gb.colour(9, true) == gb.colour(5, true), "R-236-02: out-of-range bands must give the same ground colour")
	var fx := _fixture()
	var t: Dictionary = fx.terrain()
	var cols = gb.cell_colours(t)
	_check(cols is PackedColorArray and cols.size() == fx.W * fx.H, "S-236: cell_colours(terrain) must return one colour per cell")
	if cols is PackedColorArray and cols.size() == fx.W * fx.H:
		var blocked: int = 4 * fx.W + 5
		_check(cols[blocked] == gb.colour(int((t["bands"] as PackedByteArray)[blocked]), false), "R-001-01: the blocked cell (5,4) is not drawn with the steep tint")
		_check(cols[0] == gb.colour(int((t["bands"] as PackedByteArray)[0]), true), "S-236: a walkable cell does not use the ground colour")
		var distinct := {}
		for i in cols.size():
			if i != blocked:
				distinct[cols[i].to_html()] = true
		_check(distinct.size() == 1, "R-236-02: walkable cells of the 5-band fixture have %d colours, want 1" % distinct.size())

extends "res://tests/support/vg_c_case.gd"

# VG-C piece C7 (scenes/ground3d/slope_view.gd): slopes and layers visible. Proves S-001 R-001-06 (a slope is ground
# joining two layers, drawn with a midline), R-001-01 (blocked ground visible), S-004 R-004-01/06 (a unit mid-transition
# is visibly in transition; the midline is a place the player can see). Transit is section 2's `state` bit 4.
# API: SlopeView (Node3D): set_terrain(t), set_units(units), midline_count(), midline_world(i) -> Vector3,
# blocked_cells() -> Array of cell indexes, in_transit_ids() -> Array, qa_state() -> {slopes,midlines,blocked_cells,in_transit}.
# CONTROL: units with state 0 and state 1 (fired only) are not in transit; state 5 (fired | transit) is.


func _run() -> void:
	var sv := _load(SCENES + "slope_view.gd")
	if sv == null:
		return
	var fx := _fixture()
	var t: Dictionary = fx.terrain()
	var v = sv.new()
	root.add_child(v)
	await process_frame
	v.set_terrain(t)
	_check(v.midline_count() == (t["slopes"] as Array).size(), "R-001-06: one midline per slope record, got %d" % v.midline_count())
	if v.midline_count() > 0:
		var m: Vector3 = v.midline_world(0)
		_check(absf(m.x - 200.0) < 0.01 and absf(m.z - 100.0) < 0.01, "R-001-06: midline 0 is not at the slope's (mx,my)")
		_check(absf(m.y - fx.ground_y(200.0, 100.0)) < 0.5, "R-001-06: midline 0 does not sit on the ground")
	var blocked: Array = v.blocked_cells()
	_check(blocked == [4 * fx.W + 5], "R-001-01: blocked cells must be exactly the one walkable==0 cell, got %s" % [blocked])
	v.set_units(fx.frame()["units"])
	_check(v.in_transit_ids() == [4], "R-004-01: only unit 4 (state 5) is in transit, got %s" % [v.in_transit_ids()])
	var plain: Array = []
	for u in fx.frame()["units"]:
		var c: Dictionary = u.duplicate()
		c["state"] = 1 if int(u["id"]) == 4 else 0
		c.erase("tl")
		c.erase("ld")
		plain.append(c)
	v.set_units(plain)
	_check(v.in_transit_ids().is_empty(), "CONTROL: state 1 (fired) or 0 counts as in transit")
	v.set_units(fx.frame()["units"])
	var q: Dictionary = v.qa_state()
	_check(int(q.get("slopes", -1)) == 1 and int(q.get("midlines", -1)) == 1 and int(q.get("blocked_cells", -1)) == 1 and int(q.get("in_transit", -1)) == 1,
		"S-001: slope inventory wrong: %s" % q)

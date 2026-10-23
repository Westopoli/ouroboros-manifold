extends "res://tests/support/vg_c_case.gd"
# Rule pins: R-001-01@025bc6, R-001-06@9f9051, R-004-01@61a9b6, R-004-06@ebf993, R-236-02@5cb2dc

# VG-C piece C7 (scenes/ground3d/slope_view.gd) as rewritten by VG-C-no-slope-markers: slopes and layers visible, without
# the white midline bars. Proves S-001 R-001-06 (a slope is ground joining two layers; no bar is drawn), R-001-01 (blocked ground visible), S-004 R-004-01/06 (a unit
# mid-transition is visibly in transition, circles at :95-105). Transit is section 2's `state` bit 4.
# API: SlopeView (Node3D): set_terrain(t), set_units(units), blocked_cells() -> Array of cell indexes,
# in_transit_ids() -> Array, qa_state() -> {slopes,blocked_cells,in_transit} (no `midlines` key).
# CONTROL: units with state 0 and state 1 (fired only) are not in transit; state 5 (fired | transit) is.
# TD-VG-C-no-slope-markers (rule-changed by Westley 2026-10-22) retires, from main's version of this file: the assertion
# that midline_count() == slopes (main line 22), the midline 0 position and ground checks (lines 23-26), and the `midlines`
# == 1 term of the qa inventory (line 46-47). midline_count()/midline_world() are not asserted either way.
# POSITIVE CONTROL (the spec's): on main the no-bars assertion is red, the BoxMesh children exist (one per slope record).
# UNSTATED INTERFACE choice: "no MIDLINE mesh child" = no child of the view is a MeshInstance3D whose mesh is a BoxMesh
# (the bar is a BoxMesh, slope_view.gd:38-40; the circles are CylinderMesh and stay); the two transit circles of unit 4 are
# counted as CylinderMesh children (:95-105 draws two). The band-colour parity belongs to VG-C-ground-one-colour, which adds
# (TD-VG-C-one-colour, the kept ground-colour assertion): a slope's ground is GroundBands.GROUND_COLOUR on both sides of the
# midline. UNSTATED: the fixture slope runs x 100..300 at y 100 with midline x 200, so the cells either side are (1,1) and
# (2,1) (CELL_WU 100); their GroundBands.cell_colours entries are compared with the GROUND_COLOUR constant (red on main:
# the constant does not exist (b) and the two bands' colours differ (a)).


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
	var boxes := _box_children(v)
	_check(boxes == 0, "R-001-06 TD-VG-C-no-slope-markers: %d BoxMesh (midline bar) children after set_terrain, want 0" % boxes)
	_check(not (v.qa_state() as Dictionary).has("midlines"), "S-001: qa_state still carries a midlines key: %s" % [v.qa_state()])
	# PARITY (kept assertion, no deletion without parity): the slope is still in the view's inventory on the fixture
	var qs: Dictionary = v.qa_state()
	_check(int(qs.get("slopes", 0)) >= 1, "R-001-06 parity: qa_state().slopes is %s, want at least 1 on the fixture" % [qs.get("slopes")])
	var gb := _load(SCENES + "ground_bands.gd")
	if gb != null:
		var consts: Dictionary = gb.get_script_constant_map()
		var cols: PackedColorArray = gb.cell_colours(t)
		var lo: Color = cols[1 * fx.W + 1]
		var hi: Color = cols[1 * fx.W + 2]
		_check(consts.has("GROUND_COLOUR"), "R-236-02: GroundBands has no GROUND_COLOUR constant")
		_check(lo == hi, "R-236-02: the slope's ground differs across the midline: %s vs %s" % [lo.to_html(), hi.to_html()])
		if consts.has("GROUND_COLOUR"):
			_check(lo == consts["GROUND_COLOUR"] and hi == consts["GROUND_COLOUR"], "R-236-02: the slope's ground is not GROUND_COLOUR on both sides of the midline")
	var blocked: Array = v.blocked_cells()
	_check(blocked == [4 * fx.W + 5], "R-001-01: blocked cells must be exactly the one walkable==0 cell, got %s" % [blocked])
	v.set_units(fx.frame()["units"])
	var cyl := _cylinder_children(v)
	_check(cyl == 2, "R-004-06: unit 4 (TRANSIT_BIT) should show two transit circles, got %d" % cyl)
	_check(_box_children(v) == 0, "R-001-06: a BoxMesh child appeared after set_units")
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
	_check(_cylinder_children(v) == 0, "CONTROL: a unit not in transit still has transit circles")
	v.set_units(fx.frame()["units"])
	var q: Dictionary = v.qa_state()
	_check(int(q.get("slopes", -1)) == 1 and not q.has("midlines") and int(q.get("blocked_cells", -1)) == 1 and int(q.get("in_transit", -1)) == 1,
		"S-001: slope inventory wrong: %s" % q)


func _box_children(v: Node) -> int:
	var n := 0
	for c in v.get_children():
		if c is MeshInstance3D and (c as MeshInstance3D).mesh is BoxMesh:
			n += 1
	return n


func _cylinder_children(v: Node) -> int:
	var n := 0
	for c in v.get_children():
		if c is MeshInstance3D and (c as MeshInstance3D).mesh is CylinderMesh and not c.is_queued_for_deletion():
			n += 1
	return n

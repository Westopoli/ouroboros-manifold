extends "res://tests/support/vg_c_case.gd"

# VG-C-wire (scenes/ground3d/ground3d.gd): the C6 Units3D (ground_units.gd) and C7 SlopeView (slope_view.gd) pieces
# are built and tested alone but nothing attaches them to the Ground3D host. Proves S-001 R-001-06 and S-010/S-132.
# ground3d.gd adds both children, so its qa_state carries the "slope_view" and "units3d" keys.
# Contract pinned: after set_terrain + set_frame (fixtures as tactical_view feeds them), qa_state()["ground3d"] carries
#   "slope_view": {slopes, midlines, blocked_cells, in_transit} (the names the S-001 play reads)
#   "units3d": int, the count of drawn 3D units = own units plus seen enemies (R-089-04, E-12; TD-VG-C-3): ids 1, 2, 4
#   own and 3 seen enemy = 4; hidden enemy id 5 (not own, not in the visible list) is not counted.
# units3d counts the own units plus the enemies seen (4 expected here; R-089-04).
# CONTROL: the key finder says false for a state without the keys, and true for one with them.


func _find(qa: Dictionary, key: String) -> Variant:
	var g: Dictionary = qa.get("ground3d", {})
	return g.get(key, qa.get(key, null))


func _run() -> void:
	var hs := _load(SCENES + "ground3d.gd")
	if hs == null:
		return
	_check(_find({"ground3d": {"present": true}}, "units3d") == null, "CONTROL: finder reports a key that is absent")
	_check(_find({"ground3d": {"units3d": 3}}, "units3d") == 3, "CONTROL: finder misses a key that is present")
	var fx := _fixture()
	var host = hs.new()
	root.add_child(host)
	await process_frame
	var frame: Dictionary = fx.frame().duplicate(true)
	frame["player_faction"] = 0
	frame["visible"] = {"0": [1, 2, 3, 4]}
	(frame["units"] as Array).append({"id": 5, "faction": 1, "type": 0, "tier": 0, "x": 600.0, "y": 500.0, "hp": 100, "layer": 0, "facing": 0.0, "target": -1, "state": 0})
	host.set_terrain(fx.terrain())
	host.set_frame(frame, fx.mission())
	await process_frame
	var qa: Dictionary = host.qa_state()
	var sv = _find(qa, "slope_view")
	_check(sv is Dictionary, "R-001-06: ground3d qa_state has no slope_view block (Units3D/SlopesView not attached); keys %s" % [qa.keys()])
	if sv is Dictionary:
		for k in ["slopes", "midlines", "blocked_cells", "in_transit"]:
			_check((sv as Dictionary).has(k), "R-001-06: slope_view lacks %s" % k)
		_check(int(sv.get("slopes", -1)) == 1 and int(sv.get("midlines", -1)) == 1, "R-001-06: slope_view counts wrong: %s" % [sv])
	var n = _find(qa, "units3d")
	_check(n != null, "S-132: ground3d qa_state has no units3d count")
	if n != null:
		_check(int(n) == 4, "R-089-04: units3d %s, expected 4 (3 own + seen enemy 3; hidden enemy 5 not counted)" % [n])

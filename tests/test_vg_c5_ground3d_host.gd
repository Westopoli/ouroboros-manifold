extends "res://tests/support/vg_c_case.gd"

# VG-C piece C5 (scenes/ground3d/ground3d.gd, node `Ground3D`, the SubViewport host under the VG-VIEW chain).
# Proves S-236 R-236-01 and the QA contract of rulebook rows 7/11/31 (spec section 2 inventory keys `ground3d`,
# `units_px`, `objects_px`). API: set_terrain(t), set_frame(frame, mission), camera_rig() -> the C3 rig,
# qa_state() -> {ground3d:{present,cells_w,cells_h,vertices,band,camera:{x,y},scale}, units_px:{id: Vector2},
# objects_px:Array of Vector2 (one per mission objective)}. units_px stay screen pixels so box-select and clicks keep working.
# CONTROL: before set_terrain the state says ground3d.present == false (the detector is not always true).


func _px(v) -> Vector2:
	if v is Vector2:
		return v
	if v is Array and v.size() == 2:
		return Vector2(float(v[0]), float(v[1]))
	return Vector2(-1.0e9, -1.0e9)


func _run() -> void:
	var hs := _load(SCENES + "ground3d.gd")
	if hs == null:
		return
	var fx := _fixture()
	var host = hs.new()
	root.add_child(host)
	await process_frame
	var before: Dictionary = host.qa_state()
	_check(not bool((before.get("ground3d", {}) as Dictionary).get("present", false)), "CONTROL: ground3d.present is true with no terrain")
	host.set_terrain(fx.terrain())
	host.set_frame(fx.frame(), fx.mission())
	var qa: Dictionary = host.qa_state()
	var g: Dictionary = qa.get("ground3d", {})
	_check(bool(g.get("present", false)), "S-236: qa_state.ground3d.present is false after set_terrain; state keys %s" % [qa.keys()])
	_check(int(g.get("cells_w", 0)) == fx.W and int(g.get("cells_h", 0)) == fx.H, "S-236: ground3d cells_w/cells_h wrong: %s" % g)
	_check(int(g.get("vertices", 0)) >= fx.W * fx.H, "S-236: ground3d.vertices below the cell count")
	_check(g.has("camera") and g.has("scale") and g.has("band"), "row 31: ground3d lacks camera/scale/band")
	var rig = host.camera_rig()
	_check(rig != null, "S-236: camera_rig() is null")
	if rig == null:
		return
	var upx: Dictionary = qa.get("units_px", {})
	for u in fx.frame()["units"]:
		if int(u["type"]) == 0:
			var want: Vector2 = rig.project_to_screen(Vector2(u["x"], u["y"]))
			var got := _px(upx.get(u["id"], upx.get(str(u["id"]))))
			_check(got.distance_to(want) < 1.5, "S-236 row 7: units_px[%d] = %s, a walker on the ground projects to %s" % [u["id"], got, want])
	var opx: Array = qa.get("objects_px", [])
	_check(opx.size() == 2, "S-075: objects_px must list one pixel per mission objective, got %d" % opx.size())
	if opx.size() == 2:
		var n0: Dictionary = fx.frame()["map"]["nodes"][0]
		_check(_px(opx[0]).distance_to(rig.project_to_screen(Vector2(n0["x"], n0["y"]))) < 1.5, "S-075: objects_px[0] is not the projected objective node")

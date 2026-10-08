extends "res://tests/support/vg_c_case.gd"

# VG-C piece C3 (scenes/ground3d/camera_rig_3d.gd, a Node3D holding a Camera3D). Proves S-236 R-236-01
# (one continuous camera from one unit up to the map view) and rulebook row 3 / row 31 as ruled in spec lane C: the 3D
# rig publishes `camera {x,y}` and `scale` as the map band's equivalents. API: set_terrain(t), pan_to(Vector2 wu),
# pan(Vector2 wu), zoom_by(steps), camera_height() -> float, band() -> "micro"|"tactical"|"map",
# project_to_screen(Vector2 wu) -> Vector2 px, pick_ground(Vector2 px) -> Vector2 wu, qa_camera() -> {x,y,scale}.
# Round trips use 1.5 px / 1.5 wu epsilons (the test's own, not a game threshold).
# CONTROL: pick_ground of a pixel far from the projected target must not return the target.


func _run() -> void:
	var rs := _load(SCENES + "camera_rig_3d.gd")
	if rs == null:
		return
	var fx := _fixture()
	var rig = rs.new()
	root.add_child(rig)
	await process_frame
	rig.set_terrain(fx.terrain())
	rig.pan_to(Vector2(400.0, 300.0))
	var qa: Dictionary = rig.qa_camera()
	_check(absf(float(qa.get("x", -1.0)) - 400.0) < 0.5 and absf(float(qa.get("y", -1.0)) - 300.0) < 0.5, "row 31: qa_camera {x,y} must be the pan target, got %s" % qa)
	_check(float(qa.get("scale", 0.0)) > 0.0, "row 3: qa_camera must publish a positive scale")
	var centre := get_root().get_visible_rect().size * 0.5
	var sp: Vector2 = rig.project_to_screen(Vector2(400.0, 300.0))
	_check(sp.distance_to(centre) < 1.5, "S-236: the pan target must project to the viewport centre, got %s vs %s" % [sp, centre])
	for q in [Vector2(250.0, 250.0), Vector2(520.0, 340.0), Vector2(380.0, 150.0)]:
		var back: Vector2 = rig.pick_ground(rig.project_to_screen(q))
		_check(back.distance_to(q) < 1.5, "S-236: pick_ground(project_to_screen(%s)) = %s" % [q, back])
	_check(rig.pick_ground(sp + Vector2(200.0, 150.0)).distance_to(Vector2(400.0, 300.0)) > 1.5, "CONTROL: a far pixel picks the pan target, the pick ignores its input")
	rig.pan(Vector2(100.0, 0.0))
	_check(absf(float(rig.qa_camera()["x"]) - 500.0) < 0.5, "row 31: pan(+100 wu) did not move camera.x by 100")
	var h0: float = rig.camera_height()
	var s0 := float(rig.qa_camera()["scale"])
	for i in 400:
		rig.zoom_by(1)
	var h_far: float = rig.camera_height()
	_check(h_far > h0, "S-236: zooming out must raise the camera (%f -> %f)" % [h0, h_far])
	_check(float(rig.qa_camera()["scale"]) < s0, "row 3: scale must fall as the camera rises")
	_check(rig.band() == "map", "S-236: fully zoomed out must be the map band, got %s" % rig.band())
	for i in 800:
		rig.zoom_by(-1)
	_check(rig.band() == "micro", "S-236: fully zoomed in must be the micro band, got %s" % rig.band())
	var order := {"micro": 0, "tactical": 1, "map": 2}
	var last := -1
	var monotone := true
	for i in 400:
		rig.zoom_by(1)
		var b := int(order.get(rig.band(), -1))
		if b < last:
			monotone = false
		last = b
	_check(monotone and last == 2, "R-236-01: the band must only advance micro -> tactical -> map as the camera rises")

extends "res://tests/support/vg_c_case.gd"

# VG-C-wire zoom fix. Proves S-236 R-236-01 (one wheel notch is one zoom step). On the ground view each notch zooms twice:
# camera_rig_3d.gd _input handles WHEEL_UP (zoom_by(-1)) and tactical_view.gd _unhandled_input calls _zoom_by, which calls
# _rig().zoom_by again. One step = camera_rig_3d.gd _wheel_step(): ZOOM_STEP (300.0) while the canvas is at most ZOOM_MAX_MIN,
# else max(ZOOM_STEP, height * 0.08). FINDING: GREEN on origin/main, the claimed double zoom does not reproduce: ground3d.gd line 50 sets the rig to
# PROCESS_MODE_DISABLED, which also stops the rig's own _input, so only tactical_view's _zoom_by moves the camera. Kept as a
# regression pin: exactly one step per notch.
# CONTROL: the step is measured from a direct rig.zoom_by(-1) on the same view, so a zero-movement rig cannot pass as "once".


func _run() -> void:
	var cfg = root.get_node("EraConfig")
	cfg.set_era(cfg.GROUND_ERA_ID)
	var v: Node = (load("res://scenes/tactical_c/tactical_view.tscn") as PackedScene).instantiate()
	root.add_child(v)
	await process_frame
	v.set_process(false)
	await process_frame
	cfg.set_era(cfg.GROUND_ERA_ID)
	var fx := _fixture()
	var frame: Dictionary = fx.frame().duplicate(true)
	frame["player_faction"] = 0
	frame["map"]["canvas"] = 1000.0
	v.load_frame(frame)
	v.set_terrain(fx.terrain())
	await process_frame
	var rig = v._rig()
	_check(rig != null, "ground rig not active: set_terrain made no Ground3D host")
	if rig == null:
		return
	var h0: float = rig.camera_height()
	rig.zoom_by(-1)
	var one: float = h0 - rig.camera_height()
	_check(one > 0.0, "CONTROL: a direct zoom_by(-1) did not lower the camera (h0 %s)" % h0)
	rig.zoom_by(1)
	var h1: float = rig.camera_height()
	var ev := InputEventMouseButton.new()
	ev.button_index = MOUSE_BUTTON_WHEEL_UP
	ev.pressed = true
	ev.position = Vector2(640, 360)
	root.push_input(ev)
	await process_frame
	var moved: float = h1 - rig.camera_height()
	_check(absf(moved - one) < 0.01, "R-236-01: one wheel notch moved the camera %s, one step is %s" % [moved, one])
	cfg.set_era(cfg.SPACE_ERA_ID)

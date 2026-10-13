extends SceneTree

# Ruling A25 (docs/northstar/plans/2026-10-01-architect-rulings-2.md Addendum 10; E-16 R-103-09
# and R-110-02 as rewritten): Settings offers a camera pan-speed SLIDER, not an Edge Scroll toggle
# (this reverses A10: the C3-G5 toggle and the stored boolean [camera] edge_scroll are replaced).
# Provisional values: 0.5 to 2.0 times the A6 base PAN_SPEED_PX (600 px/s), default 1.0. The key
# name is chosen by this test, not by the rule: [camera] pan_speed, a float.
#
# Headless checks here (modes ui and stored). The same file is the child of the desktop test
# tests/qa/desktop/test_pan_speed_zoom.py in mode `pan` (a real Xvfb display, the live tactical_c
# view, held key and pointer on the edge at two zoom levels); that mode prints measurements and
# asserts nothing.
#
# One file, two roles: with the user arg --probe <mode> this script is the child and prints one
# "PROBE {json}" line. Child boots use a throwaway XDG_DATA_HOME so user://settings.cfg is a
# fixture, never the player's file. Linux/XDG only.

const SCRIPT_PATH := "res://tests/test_settings_pan_speed.gd"
const PAN_FRAMES := 5
const PAN_DELTA := 1.0 / 30.0

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var idx := args.find("--probe")
	if idx != -1 and idx + 1 < args.size():
		await _probe(args[idx + 1])
		return
	await _run_tests()
	_assert(_completed, "the pan-speed checks did not run to the end (a script error aborted them)")
	print("\n=== Settings Pan Speed Test Results ===")
	print("PASS: %d  FAIL: %d" % [_pass_count, _fail_count])
	if _fail_count > 0:
		print("Failures:")
		for msg in _fail_msgs:
			print("  - " + msg)
		print("=== RED ===\n")
		quit(1)
	else:
		print("=== GREEN ===\n")
		quit(0)


func _assert(cond: bool, msg: String) -> void:
	if cond:
		_pass_count += 1
	else:
		_fail_count += 1
		_fail_msgs.append(msg)


# ---- child ------------------------------------------------------------------

func _key(code: int, pressed: bool) -> void:
	var e := InputEventKey.new()
	e.keycode = code
	e.physical_keycode = code
	e.pressed = pressed
	Input.parse_input_event(e)


func _mouse_to(p: Vector2) -> void:
	get_root().warp_mouse(p)
	var e := InputEventMouseMotion.new()
	e.position = p
	e.global_position = p
	Input.parse_input_event(e)


func _collect(node: Node, out: Dictionary) -> void:
	if node is HSlider:
		out["sliders"].append({"min": node.min_value, "max": node.max_value, "value": node.value})
	elif node is CheckButton:
		out["toggles"] += 1
	elif node is Label:
		out["labels"].append(String(node.text))
	for child in node.get_children():
		_collect(child, out)


# One pan measurement: camera travel in world units and in screen pixels over PAN_FRAMES fixed-step
# _pan_input calls, for a held arrow key ("key") or the pointer resting on the right edge ("edge").
func _measure(view: Node, input: String) -> Dictionary:
	var canvas := float(view.get("_canvas"))
	view.qa_pan(canvas * 0.5, canvas * 0.5)
	var vp: Vector2 = view.get_viewport().get_visible_rect().size
	_mouse_to(vp * 0.5)
	await process_frame
	var before: Vector2 = view.get("_camera")
	if input == "key":
		_key(KEY_RIGHT, true)
	else:
		_mouse_to(Vector2(vp.x - 1.0, vp.y * 0.5))
		view.set("_pointer_seen", true)
	await process_frame
	for _i in PAN_FRAMES:
		view._pan_input(PAN_DELTA)
	if input == "key":
		_key(KEY_RIGHT, false)
	_mouse_to(vp * 0.5)
	await process_frame
	var after: Vector2 = view.get("_camera")
	var world := after.x - before.x
	return {"world": world, "screen": world * float(view.get("_world_scale")), "cross": absf(after.y - before.y)}


func _probe(mode: String) -> void:
	await process_frame
	await process_frame
	var out := {"mode": mode}
	var bus = get_root().get_node_or_null("UIDataBus")
	out["stored"] = bus.get_settings() if bus != null else {}
	if mode == "ui":
		var scene: Node = (load("res://scenes/settings/settings.tscn") as PackedScene).instantiate()
		get_root().add_child(scene)
		await process_frame
		var found := {"sliders": [], "toggles": 0, "labels": []}
		_collect(scene, found)
		out["ui"] = found
		var saved: Dictionary = bus.get_settings()
		saved["pan_speed"] = 1.5
		saved["edge_scroll"] = true
		bus.save_settings(saved)
		out["after_save"] = bus.get_settings()
		var cfg := ConfigFile.new()
		cfg.load("user://settings.cfg")
		out["file_camera"] = {}
		if cfg.has_section("camera"):
			for key in cfg.get_section_keys("camera"):
				out["file_camera"][key] = cfg.get_value("camera", key)
	elif mode == "pan":
		var view: Node = (load("res://scenes/tactical_c/tactical_view.tscn") as PackedScene).instantiate()
		get_root().add_child(view)
		await process_frame
		view.set_process(false)
		await process_frame
		out["canvas"] = float(view.get("_canvas"))
		# TD-VG-A-14 (amended): the opening zoom is the fit at ZOOM_MAX / ZOOM_STEP (32), so
		# zoom1 was 32 and _zoom_by(2.0) clamped to 40 (a 1.25 ratio). Halve first: zoom1 = 16,
		# zoom2 = 32 after the existing _zoom_by(2.0), unclamped.
		view._zoom_by(0.5)
		out["zoom1"] = {"scale": float(view.get("_world_scale")), "key": await _measure(view, "key"), "edge": await _measure(view, "edge")}
		view._zoom_by(2.0)
		out["zoom2"] = {"scale": float(view.get("_world_scale")), "key": await _measure(view, "key"), "edge": await _measure(view, "edge")}
	print("PROBE ", JSON.stringify(out))
	quit(0)


# ---- parent -----------------------------------------------------------------

func _boot_child(fixture: String, mode: String) -> Dictionary:
	var base := OS.get_cache_dir().path_join("om_a25_%d_%s" % [OS.get_process_id(), mode])
	var user_dir := base.path_join(str(ProjectSettings.get_setting("application/config/custom_user_dir_name", "data")))
	DirAccess.make_dir_recursive_absolute(user_dir)
	var f := FileAccess.open(user_dir.path_join("settings.cfg"), FileAccess.WRITE)
	f.store_string(fixture)
	f.close()
	var prior := OS.get_environment("XDG_DATA_HOME")
	OS.set_environment("XDG_DATA_HOME", base)
	var output: Array = []
	var code := OS.execute(OS.get_executable_path(),
		["--headless", "--path", ProjectSettings.globalize_path("res://"), "--quit-after", "3000", "--script", SCRIPT_PATH, "--", "--probe", mode],
		output, true)
	if prior == "":
		OS.unset_environment("XDG_DATA_HOME")
	else:
		OS.set_environment("XDG_DATA_HOME", prior)
	DirAccess.remove_absolute(user_dir.path_join("settings.cfg"))
	DirAccess.remove_absolute(user_dir)
	DirAccess.remove_absolute(base)
	var text := "\n".join(PackedStringArray(output))
	for line in text.split("\n"):
		if line.begins_with("PROBE "):
			var parsed = JSON.parse_string(line.substr(6))
			if parsed is Dictionary:
				return parsed
	return {"error": "no PROBE line (exit %d): %s" % [code, text.left(400)]}


func _run_tests() -> void:
	var fresh := _boot_child("[audio]\nmaster_volume=30\n", "ui")
	_assert(not fresh.has("error"), "A25 ui: the child boot failed: %s" % fresh.get("error", ""))
	if not fresh.has("error"):
		var ui: Dictionary = fresh.get("ui", {})
		# Control: the Settings scene really built (it has the audio sliders, 0..100).
		var sliders: Array = ui.get("sliders", [])
		_assert(sliders.size() >= 4, "A25 control: the Settings scene built %d sliders, expected at least the four audio ones" % sliders.size())
		var pan_sliders := sliders.filter(func(s): return is_equal_approx(float(s["min"]), 0.5) and is_equal_approx(float(s["max"]), 2.0))
		_assert(pan_sliders.size() == 1,
			"A25 R-110-02: Settings has %d pan-speed sliders (min 0.5, max 2.0), expected exactly one; sliders are %s" % [pan_sliders.size(), JSON.stringify(sliders)])
		if pan_sliders.size() == 1:
			_assert(is_equal_approx(float(pan_sliders[0]["value"]), 1.0),
				"A25: the pan-speed slider starts at %s with no stored value, expected the default 1.0" % pan_sliders[0]["value"])
		var texts := " | ".join(PackedStringArray(ui.get("labels", []))).to_lower()
		_assert(texts.find("edge scroll") == -1,
			"A25: Settings still shows an Edge Scroll label; the on/off toggle is replaced by the pan-speed slider (labels: %s)" % texts)
		_assert(int(ui.get("toggles", -1)) == 2,
			"A25: Settings has %s toggles, expected only Fullscreen and VSync (the Edge Scroll toggle is gone)" % ui.get("toggles"))
		var stored: Dictionary = fresh.get("stored", {})
		_assert(stored.has("pan_speed") and is_equal_approx(float(stored["pan_speed"]), 1.0),
			"A25: UIDataBus settings carry no default pan_speed of 1.0 (stored %s)" % JSON.stringify(stored))
		_assert(not stored.has("edge_scroll"), "A25: UIDataBus settings still carry the edge_scroll boolean")
		var after: Dictionary = fresh.get("after_save", {})
		_assert(after.has("pan_speed") and is_equal_approx(float(after["pan_speed"]), 1.5),
			"A25: save_settings dropped pan_speed 1.5 (after save: %s)" % JSON.stringify(after))
		_assert(not after.has("edge_scroll"), "A25: save_settings still keeps an edge_scroll boolean (after save: %s)" % JSON.stringify(after))
		var camera: Dictionary = fresh.get("file_camera", {})
		_assert(camera.has("pan_speed") and is_equal_approx(float(camera["pan_speed"]), 1.5),
			"A25: settings.cfg [camera] has no pan_speed 1.5 after save (section: %s)" % JSON.stringify(camera))
		_assert(not camera.has("edge_scroll"), "A25: settings.cfg [camera] still has an edge_scroll key after save (section: %s)" % JSON.stringify(camera))

	var loaded := _boot_child("[camera]\npan_speed=1.5\n", "stored")
	var low := _boot_child("[camera]\npan_speed=0.5\n", "stored")
	var plain := _boot_child("[camera]\npan_speed=1.5\n", "stored")
	var stale := _boot_child("[camera]\npan_speed=1.5\nedge_scroll=false\n", "stored")
	_assert(not loaded.has("error") and not low.has("error") and not plain.has("error") and not stale.has("error"),
		"A25 stored: a child boot failed: %s / %s / %s / %s" % [loaded.get("error", ""), low.get("error", ""), plain.get("error", ""), stale.get("error", "")])
	if not loaded.has("error") and not low.has("error") and not plain.has("error") and not stale.has("error"):
		var s: Dictionary = loaded.get("stored", {})
		_assert(s.has("pan_speed") and is_equal_approx(float(s["pan_speed"]), 1.5),
			"A25: UIDataBus did not load [camera] pan_speed=1.5 (stored %s)" % JSON.stringify(s))
		var s_low: Dictionary = low.get("stored", {})
		_assert(s_low.has("pan_speed") and is_equal_approx(float(s_low["pan_speed"]), 0.5),
			"A25: UIDataBus did not load [camera] pan_speed=0.5 (stored %s)" % JSON.stringify(s_low))
		_assert(not s.has("edge_scroll"), "A25: UIDataBus settings carry an edge_scroll key (stored %s)" % JSON.stringify(s))
		_assert(JSON.stringify(plain.get("stored", {})) == JSON.stringify(stale.get("stored", {})),
			"A25: a stale [camera] edge_scroll key changed the stored settings (%s vs %s)" % [JSON.stringify(plain.get("stored", {})), JSON.stringify(stale.get("stored", {}))])
	_completed = true

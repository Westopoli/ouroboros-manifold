extends Node

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")

var _root: Node
var _out_dir: String = "user://qa"
var _grab_mode: String = "engine"
var _script: Array = []
var _stopped := false

var _synth_pending := 0
var _os_inputs := 0
var _last_input := ""
var _mouse_pos: Vector2 = Vector2.ZERO
var _shots: Array = []


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	var args := OS.get_cmdline_user_args()
	var script_path := _arg_value(args, "--qa-script")
	if script_path == "":
		return

	var out_arg := _arg_value(args, "--qa-out")
	_out_dir = out_arg if out_arg != "" else "user://qa"
	var grab_arg := _arg_value(args, "--qa-grab")
	_grab_mode = grab_arg if grab_arg != "" else "engine"
	DirAccess.make_dir_recursive_absolute(_out_dir)

	var text := FileAccess.get_file_as_string(script_path)
	if text == "":
		print("QA_ERR cannot read qa-script %s" % script_path)
		get_tree().quit(2)
		return
	var parsed = JSON.parse_string(text)
	if typeof(parsed) != TYPE_ARRAY:
		print("QA_ERR qa-script is not a JSON array: %s" % script_path)
		get_tree().quit(2)
		return
	_script = parsed

	_root = get_tree().current_scene
	if _root == null or not (_root.has_method("qa_state") and _root.has_method("qa_plant")):
		print("QA_ERR scene root missing qa_state/qa_plant contract")
		get_tree().quit(3)
		return

	DisplayServer.window_set_title("QA:" + _root.name)
	_run()


func _input(event: InputEvent) -> void:
	if _synth_pending > 0:
		_synth_pending -= 1
	else:
		_os_inputs += 1
	_last_input = event.as_text()


func _arg_value(args: PackedStringArray, flag: String) -> String:
	var idx := args.find(flag)
	if idx == -1 or idx + 1 >= args.size():
		return ""
	return args[idx + 1]


func _run() -> void:
	await get_tree().process_frame
	await get_tree().process_frame
	var center: Vector2 = get_viewport().get_visible_rect().size * 0.5
	await _push_frame(_make_motion(center))

	for action in _script:
		if _stopped:
			break
		await _do(action)

	if _stopped:
		return
	_write_json("_run", _qa_info())
	get_tree().quit(0)


func _fail(code: int, msg: String) -> void:
	print("QA_ERR %s" % msg)
	_stopped = true
	get_tree().quit(code)


func _do(action: Array) -> void:
	var verb: String = action[0]
	match verb:
		"wait_frames":
			for i in range(int(action[1])):
				await get_tree().process_frame
		"call":
			_do_call(action)
		"screenshot":
			await _do_screenshot(action[1])
		"state":
			_do_state(action[1])
		_:
			_fail(3, "unknown verb %s" % verb)


func _do_call(action: Array) -> void:
	var method: String = action[1]
	var args: Array = action.slice(2)
	if not _root.has_method(method):
		_fail(3, "call: no method %s on scene root" % method)
		return
	var result = _root.callv(method, args)
	print("QA_CALL %s -> %s" % [method, result])


func _do_state(name: String) -> void:
	var d: Dictionary = _root.qa_state()
	d["_qa"] = _qa_info()
	_write_json(name, d)


func _do_screenshot(name: String) -> void:
	if DisplayServer.get_name() == "headless":
		print("QA_WARN headless no screenshot %s" % name)
		return
	await get_tree().process_frame
	await get_tree().process_frame
	await RenderingServer.frame_post_draw

	if _grab_mode == "external":
		await _do_screenshot_external(name)
		return

	var img := get_viewport().get_texture().get_image()
	if _is_uniform(img):
		print("QA_WARN uniform %s" % name)
	img.save_png(_out_path(name + ".png"))
	_shots.append(name)


func _do_screenshot_external(name: String) -> void:
	get_tree().paused = true
	_write_text(name + ".grab", "")
	var ok := await _wait_file(name + ".done", 3000)
	get_tree().paused = false
	if not ok:
		print("QA_WARN external grab timeout %s" % name)
	_shots.append(name)


func _wait_file(name: String, max_frames: int) -> bool:
	var path := _out_path(name)
	for i in range(max_frames):
		if FileAccess.file_exists(path):
			return true
		await get_tree().process_frame
	return false


func _is_uniform(img: Image) -> bool:
	var w := img.get_width()
	var h := img.get_height()
	if w == 0 or h == 0:
		return true
	var first: Color = img.get_pixel(0, 0)
	for gy in range(9):
		for gx in range(16):
			var x: int = clampi(int((gx + 0.5) / 16.0 * w), 0, w - 1)
			var y: int = clampi(int((gy + 0.5) / 9.0 * h), 0, h - 1)
			if img.get_pixel(x, y) != first:
				return false
	return true


func _make_motion(pos: Vector2) -> InputEventMouseMotion:
	var e := InputEventMouseMotion.new()
	e.position = pos
	e.global_position = pos
	e.relative = pos - _mouse_pos
	_mouse_pos = pos
	return e


func _push(e: InputEvent) -> void:
	_synth_pending += 1
	Input.parse_input_event(e)
	Input.flush_buffered_events()


func _push_frame(e: InputEvent) -> void:
	_push(e)
	await get_tree().process_frame


func _out_path(name: String) -> String:
	return _out_dir.path_join(name)


func _write_json(name: String, d: Dictionary) -> void:
	var full_name := name if name.ends_with(".json") else name + ".json"
	var f := FileAccess.open(_out_path(full_name), FileAccess.WRITE)
	if f == null:
		print("QA_ERR cannot write %s" % full_name)
		return
	f.store_string(JSON.stringify(d, "  "))
	f.close()


func _write_text(name: String, text: String) -> void:
	var f := FileAccess.open(_out_path(name), FileAccess.WRITE)
	if f == null:
		print("QA_ERR cannot write %s" % name)
		return
	f.store_string(text)
	f.close()


func _qa_info() -> Dictionary:
	var window_size := DisplayServer.window_get_size()
	return {
		"frame": Engine.get_process_frames(),
		"os_inputs": _os_inputs,
		"last_input": _last_input,
		"shots": _shots,
		"plants": QaPlants.active(),
		"adapter": RenderingServer.get_video_adapter_name(),
		"method": RenderingServer.get_current_rendering_method(),
		"display": DisplayServer.get_name(),
		"window_px": [window_size.x, window_size.y],
		"fps_ms": Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0,
	}

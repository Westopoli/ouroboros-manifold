extends Node

## C7 -- desktop QA daemon (docs/northstar/plans/push/specs/C7.md). Dev-only:
## does nothing beyond existing unless launched with --qa-port or --qa-script
## (mirrors scenes/mockups/_shared/qa_driver.gd's inert-by-default pattern).
## state() is called directly by tests/test_qa_daemon.gd via load()+Script.new()
## in --script SceneTree mode, i.e. with no SceneTree at all -- every method
## here guards get_tree() rather than assuming it is non-null.
##
## Reuses qa_driver.gd's input-synthesis verbs (move/click/key/wheel/drag/
## wait_frames/screenshot) by preload instead of duplicating them, in
## --qa-port mode only -- see leaf-01.ASSUMPTIONS.md: qa_driver.gd's own
## _ready() independently reads --qa-script off the same cmdline args and,
## finding no mockup qa_state()/qa_plant() root contract on the harness
## scene, calls get_tree().quit(3); verified with a throwaway probe script.
## Instantiating it while --qa-script is set crashes the process regardless
## of when/where it is added to the tree, so it is only ever added to the
## tree in --qa-port mode, where its _ready() no-ops harmlessly (script_path
## == ""). state, tree, seed, fixture, pause, step, inject are native to
## this daemon either way -- no mockup root contract here (spec_lines 44-57).

const QaDriverScript := preload("res://scenes/mockups/_shared/qa_driver.gd")

const KNOWN_BUG_IDS := ["stub-null-ref", "stub-stuck-ai", "stub-desync"]

var tick: int = 0

var _active := false
var _driver: Node = null
var _fixture_path: String = ""
var _injected_bugs: Dictionary = {}

var _server: TCPServer = null
var _conn: StreamPeerTCP = null
var _conn_buffer: String = ""

var _script_actions: Array = []


func _ready() -> void:
	set_process(false)
	var args := OS.get_cmdline_user_args()
	var port_str := _arg_value(args, "--qa-port")
	var script_path := _arg_value(args, "--qa-script")
	if port_str == "" and script_path == "":
		return

	_active = true

	if port_str != "":
		_driver = QaDriverScript.new()
		add_child(_driver)
		_start_server(int(port_str))
	if script_path != "":
		_load_script(script_path)


func state() -> Dictionary:
	var scene_name := ""
	var tick_val := tick
	var result := {"scene": scene_name, "tick": tick_val}
	var t := get_tree()
	if t != null:
		var cur := t.current_scene
		if cur != null:
			scene_name = cur.scene_file_path if cur.scene_file_path != "" else String(cur.name)
			if cur.has_method("qa_state"):
				result["qa"] = cur.qa_state()
		var tb := get_node_or_null("/root/TacticalBridge")
		if tb != null and "current_tick" in tb:
			tick_val = tb.current_tick
	result["scene"] = scene_name
	result["tick"] = tick_val
	return result


func tree() -> Dictionary:
	var t := get_tree()
	if t == null or t.current_scene == null:
		return {"controls": [], "node3ds": []}
	var controls: Array = []
	var node3ds: Array = []
	_collect_tree(t.current_scene, controls, node3ds)
	return {"controls": controls, "node3ds": node3ds}


func _start_server(port: int) -> void:
	_server = TCPServer.new()
	var err := _server.listen(port, "127.0.0.1")
	if err != OK:
		push_error("qa_daemon: cannot listen on 127.0.0.1:%d (err %d)" % [port, err])
		_server = null
		return
	set_process(true)


func _load_script(path: String) -> void:
	var text := FileAccess.get_file_as_string(path)
	if text == "":
		push_error("qa_daemon: cannot read qa-script %s" % path)
		return
	var parsed = JSON.parse_string(text)
	if typeof(parsed) != TYPE_ARRAY:
		push_error("qa_daemon: qa-script is not a JSON array: %s" % path)
		return
	_script_actions = parsed
	_run_script()


func _run_script() -> void:
	var t := get_tree()
	if t != null:
		await t.process_frame
	for action in _script_actions:
		if typeof(action) != TYPE_ARRAY or action.is_empty():
			continue
		var verb: String = String(action[0])
		var args: Array = action.slice(1)
		await _dispatch(verb, args)
	var t2 := get_tree()
	if t2 != null:
		t2.quit(0)


func _process(_delta: float) -> void:
	if not _active or _server == null:
		return
	_poll_server()


func _poll_server() -> void:
	if _conn == null and _server.is_connection_available():
		_conn = _server.take_connection()
	if _conn == null:
		return
	_conn.poll()
	if _conn.get_status() != StreamPeerTCP.STATUS_CONNECTED:
		_conn = null
		_conn_buffer = ""
		return
	var avail := _conn.get_available_bytes()
	if avail <= 0:
		return
	var data: Array = _conn.get_data(avail)
	if data[0] != OK:
		return
	var bytes: PackedByteArray = data[1]
	_conn_buffer += bytes.get_string_from_utf8()
	var nl := _conn_buffer.find("\n")
	while nl != -1:
		var line := _conn_buffer.substr(0, nl)
		_conn_buffer = _conn_buffer.substr(nl + 1)
		_handle_line(line)
		nl = _conn_buffer.find("\n")


func _handle_line(line: String) -> void:
	if line.strip_edges() == "":
		return
	var parsed = JSON.parse_string(line)
	var verb := ""
	var args: Array = []
	if typeof(parsed) == TYPE_DICTIONARY and parsed.has("verb"):
		verb = String(parsed["verb"])
		if parsed.has("args") and typeof(parsed["args"]) == TYPE_ARRAY:
			args = parsed["args"]
	elif typeof(parsed) == TYPE_ARRAY and not parsed.is_empty():
		verb = String(parsed[0])
		args = parsed.slice(1)
	else:
		_write_response({"ok": false, "error": "malformed request"})
		return
	var resp := await _dispatch(verb, args)
	_write_response(resp)


func _write_response(resp: Dictionary) -> void:
	if _conn == null:
		return
	_conn.put_data((JSON.stringify(resp) + "\n").to_utf8_buffer())


func _dispatch(verb: String, args: Array) -> Dictionary:
	match verb:
		"state":
			return {"ok": true, "result": state()}
		"tree":
			return {"ok": true, "result": tree()}
		"seed":
			return {"ok": true, "result": _do_seed(int(args[0]) if args.size() > 0 else 0)}
		"fixture":
			return {"ok": true, "result": _do_fixture(String(args[0]) if args.size() > 0 else "")}
		"pause":
			return {"ok": true, "result": _do_pause(bool(args[0]) if args.size() > 0 else true)}
		"step":
			return {"ok": true, "result": _do_step(int(args[0]) if args.size() > 0 else 1)}
		"inject":
			return {"ok": true, "result": _do_inject(String(args[0]) if args.size() > 0 else "")}
		"plant":
			return _do_plant(String(args[0]) if args.size() > 0 else "")
		"screenshot":
			var name: String = String(args[0]) if args.size() > 0 else "screenshot"
			if _driver == null:
				return {"ok": false, "error": "screenshot: only available in --qa-port mode"}
			await _driver.call("_do_screenshot", name)
			return {"ok": true, "result": name}
		"input":
			return await _dispatch_input(args)
		_:
			return {"ok": false, "error": "unknown verb %s" % verb}


func _dispatch_input(args: Array) -> Dictionary:
	if args.is_empty():
		return {"ok": false, "error": "input: missing sub-verb"}
	if _driver == null:
		return {"ok": false, "error": "input: only available in --qa-port mode"}
	var sub: String = String(args[0])
	var rest: Array = args.slice(1)
	match sub:
		"move":
			await _driver.call("_do_move", float(rest[0]), float(rest[1]))
		"click":
			var button: int = int(rest[2]) if rest.size() > 2 else MOUSE_BUTTON_LEFT
			await _driver.call("_do_click", float(rest[0]), float(rest[1]), button)
		"click_node":
			await _driver.call("_do_click_node", String(rest[0]))
		"drag":
			var steps: int = int(rest[4]) if rest.size() > 4 else 8
			await _driver.call("_do_drag", float(rest[0]), float(rest[1]), float(rest[2]), float(rest[3]), steps)
		"wheel":
			await _driver.call("_do_wheel", int(rest[0]))
		"key":
			await _driver.call("_do_key", String(rest[0]))
		"key_down":
			await _driver.call("_do_key_hold", String(rest[0]), true)
		"key_up":
			await _driver.call("_do_key_hold", String(rest[0]), false)
		"wait_frames":
			var t := get_tree()
			if t != null:
				for i in range(int(rest[0])):
					await t.process_frame
		_:
			return {"ok": false, "error": "input: unknown sub-verb %s" % sub}
	return {"ok": true, "result": sub}


func _do_seed(n: int) -> Dictionary:
	seed(n)
	return {"seed": n}


func _do_fixture(path: String) -> Dictionary:
	_fixture_path = path
	return {"fixture": path}


func _do_pause(p: bool) -> Dictionary:
	var t := get_tree()
	if t != null:
		t.paused = p
	return {"paused": p}


func _do_step(n: int) -> Dictionary:
	tick += n
	var t := get_tree()
	var scene: Node = t.current_scene if t != null else null
	if scene != null and scene.has_method("qa_step"):
		scene.qa_step(n)
	return {"tick": tick}


func _do_inject(bug_id: String) -> Dictionary:
	var known := KNOWN_BUG_IDS.has(bug_id)
	_injected_bugs[bug_id] = known
	return {"bug_id": bug_id, "known": known}


func _do_plant(id: String) -> Dictionary:
	var t := get_tree()
	var scene: Node = t.current_scene if t != null else null
	if scene == null or not scene.has_method("qa_plant"):
		return {"ok": false, "error": "plant: current scene has no qa_plant method"}
	var activated: bool = scene.call("qa_plant", id)
	return {"ok": true, "result": {"id": id, "activated": activated}}


func _collect_tree(node: Node, controls: Array, node3ds: Array) -> void:
	for child in node.get_children():
		if child is Control:
			var ctrl: Control = child
			if ctrl.visible:
				# rect_px added for C8 (docs/northstar/plans/push/specs/C8.md):
				# --qa-port callers had no way to locate a control's click
				# centre (qa_driver.gd's own _collect_tree, used only in
				# --qa-script mode, already computes this the same way).
				# _do_click_node is still --qa-script-only (needs _root,
				# which --qa-port mode never sets) -- port-mode callers click
				# by coordinate off this rect instead.
				var vp := ctrl.get_viewport()
				var origin: Vector2 = vp.get_final_transform() * ctrl.get_global_rect().position
				var far: Vector2 = vp.get_final_transform() * (ctrl.get_global_rect().position + ctrl.get_global_rect().size)
				controls.append({
					"path": String(ctrl.get_path()),
					"class": ctrl.get_class(),
					"text": ctrl.get("text"),
					"rect_px": [origin.x, origin.y, far.x - origin.x, far.y - origin.y],
				})
		elif child is Node3D:
			node3ds.append({
				"path": String(child.get_path()),
				"class": child.get_class(),
			})
		_collect_tree(child, controls, node3ds)


func _arg_value(args: PackedStringArray, flag: String) -> String:
	var idx := args.find(flag)
	if idx == -1 or idx + 1 >= args.size():
		return ""
	return args[idx + 1]

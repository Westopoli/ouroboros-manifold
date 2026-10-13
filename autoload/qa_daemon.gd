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
var _conns: Array = []  # {"peer": StreamPeerTCP, "buf": String}; the test client and, in a net match, the peer daemon
var _fog_filter_override := -1  # -1 unset; 0/1 set by set_fog_filter

var _nm = null  # net_loopback_start: own NetMatch (not in the tree, so only net_run polls it)
var _nm_transport = null
var _nm_local := 0
var _nm_remote := 0
var _nm_peer: StreamPeerTCP = null
var _nm_budget := 0  # ticks this side has been asked to reach; the peer's net_run may already have driven it past

var _script_actions: Array = []
var _pointer := Vector2.ZERO
var _pointer_set := false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
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
			var nodes_by_name := {}
			var hud_texts := {}
			_collect_tree(cur, [], [], nodes_by_name, hud_texts)
			result["inventory"] = {"nodes_by_name": nodes_by_name, "hud_texts": hud_texts}
		var tb := get_node_or_null("/root/TacticalBridge")
		if tb != null and "current_tick" in tb:
			tick_val = tb.current_tick
	result["scene"] = scene_name
	result["tick"] = tick_val
	return result


func tree() -> Dictionary:
	var t := get_tree()
	if t == null or t.current_scene == null:
		return {"controls": [], "node3ds": [], "hover": ""}
	var controls: Array = []
	var node3ds: Array = []
	_collect_tree(t.current_scene, controls, node3ds)
	return {"controls": controls, "node3ds": node3ds, "hover": _hover_path(t.current_scene)}


func _hover_path(scene: Node) -> String:
	var vp := scene.get_viewport()
	var hovered := vp.gui_get_hovered_control()
	if hovered != null:
		return String(hovered.get_path())
	# Headless viewports do not track the hovered control; fall back to the topmost visible one under the pointer.
	var pos := _pointer if _pointer_set else vp.get_mouse_position()
	var best: Control = null
	var stack: Array = [scene]
	while not stack.is_empty():
		var n: Node = stack.pop_back()
		for c in n.get_children():
			stack.push_back(c)
		if n is Control and n != scene and n.is_visible_in_tree() and n.mouse_filter != Control.MOUSE_FILTER_IGNORE \
				and n.get_global_rect().has_point(pos):
			if best == null or _later(n, best):
				best = n
	return String(best.get_path()) if best != null else ""


func _later(a: Node, b: Node) -> bool:
	return a.is_greater_than(b) or b.is_ancestor_of(a)


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
	while _server.is_connection_available():
		_conns.append({"peer": _server.take_connection(), "buf": ""})
	for c in _conns.duplicate():
		var peer: StreamPeerTCP = c["peer"]
		peer.poll()
		if peer.get_status() != StreamPeerTCP.STATUS_CONNECTED:
			_conns.erase(c)
			continue
		var avail := peer.get_available_bytes()
		if avail <= 0:
			continue
		var data: Array = peer.get_data(avail)
		if data[0] != OK:
			continue
		var bytes: PackedByteArray = data[1]
		c["buf"] += bytes.get_string_from_utf8()
		var nl: int = c["buf"].find("\n")
		while nl != -1:
			var line: String = c["buf"].substr(0, nl)
			c["buf"] = c["buf"].substr(nl + 1)
			_handle_line(line, peer)
			nl = c["buf"].find("\n")


func _handle_line(line: String, peer: StreamPeerTCP) -> void:
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
		_write_response({"ok": false, "error": "malformed request"}, peer)
		return
	var resp := await _dispatch(verb, args)
	_write_response(resp, peer)


func _write_response(resp: Dictionary, peer: StreamPeerTCP) -> void:
	if peer == null:
		return
	peer.put_data((JSON.stringify(resp) + "\n").to_utf8_buffer())


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
			if args.size() > 1 and String(args[1]) != "":
				await _driver.call("_do_screenshot", name, String(args[1]))
			else:
				await _driver.call("_do_screenshot", name)
			return {"ok": true, "result": name}
		"input":
			return await _dispatch_input(args)
		"qa_select":
			return _do_qa_select(args)
		"project":
			return _do_project(args)
		"set_fog_filter":
			_fog_filter_override = 1 if (args.size() > 0 and bool(args[0])) else 0
			return {"ok": true, "result": {"fog_filter": fog_filter()}}
		"net_loopback_start":
			return _net_loopback_start(args)
		"net_run":
			return _net_run(int(args[0]) if args.size() > 0 else 1)
		"net_frame":
			return _net_frame()
		"net_command":
			return _net_command(args[0] if args.size() > 0 and typeof(args[0]) == TYPE_DICTIONARY else {})
		"net_peer_pump":
			return _net_peer_pump(args[0] if args.size() > 0 and typeof(args[0]) == TYPE_ARRAY else [])
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
			_track_pointer(float(rest[0]), float(rest[1]))
			await _driver.call("_do_move", float(rest[0]), float(rest[1]))
		"click":
			_track_pointer(float(rest[0]), float(rest[1]))
			var button: int = int(rest[2]) if rest.size() > 2 else MOUSE_BUTTON_LEFT
			await _driver.call("_do_click", float(rest[0]), float(rest[1]), button)
		"click_node":
			await _driver.call("_do_click_node", String(rest[0]))
		"drag":
			_track_pointer(float(rest[2]), float(rest[3]))
			var steps: int = int(rest[4]) if rest.size() > 4 else 8
			await _driver.call("_do_drag", float(rest[0]), float(rest[1]), float(rest[2]), float(rest[3]), steps)
		"wheel":
			await _driver.call("_do_wheel", int(rest[0]))
		"key":
			if _has_mods(rest):
				await _key_with_mods(String(rest[0]), rest[1], [true, false])
			else:
				await _driver.call("_do_key", String(rest[0]))
		"key_down":
			if _has_mods(rest):
				await _key_with_mods(String(rest[0]), rest[1], [true])
			else:
				await _driver.call("_do_key_hold", String(rest[0]), true)
		"key_up":
			if _has_mods(rest):
				await _key_with_mods(String(rest[0]), rest[1], [false])
			else:
				await _driver.call("_do_key_hold", String(rest[0]), false)
		"wait_frames":
			var t := get_tree()
			if t != null:
				for i in range(int(rest[0])):
					await t.process_frame
		_:
			return {"ok": false, "error": "input: unknown sub-verb %s" % sub}
	return {"ok": true, "result": sub}


func _track_pointer(x: float, y: float) -> void:
	_pointer = Vector2(x, y)
	_pointer_set = true


func _has_mods(rest: Array) -> bool:
	return rest.size() > 1 and typeof(rest[1]) == TYPE_ARRAY and not rest[1].is_empty()


func _key_with_mods(key_name: String, mods: Array, phases: Array) -> void:
	var keycode := OS.find_keycode_from_string(key_name)
	if keycode == KEY_NONE:
		return
	for pressed in phases:
		var e := InputEventKey.new()
		e.keycode = keycode
		e.physical_keycode = keycode
		e.unicode = keycode
		e.pressed = pressed
		e.ctrl_pressed = mods.has("ctrl")
		e.shift_pressed = mods.has("shift")
		e.alt_pressed = mods.has("alt")
		e.meta_pressed = mods.has("meta")
		Input.parse_input_event(e)
		var t := get_tree()
		if t != null:
			await t.process_frame


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


# The fog filter the live mission load asks for: the game default (R-089-03) unless a probe turned it off.
func fog_filter() -> bool:
	return _fog_filter_override != 0


# Net verbs (tests/qa/desktop/net_match_loopback.py). Each process runs one NetMatch over an in-process loopback
# transport; the daemons carry the packets between the two transports through the peer's qa port. net_run drives
# both sessions in turn (peer first, so both end on the same tick), as lockstep needs both sides polling. net_run(steps)
# raises this side's tick target by steps, so the peer's run having driven this side there already makes it a no-op.
func _net_loopback_start(args: Array) -> Dictionary:
	if args.size() < 3:
		return {"ok": false, "error": "net_loopback_start: role peer_qa_port mission_seed"}
	var host: bool = String(args[0]) == "host"
	var bridge = load("res://autoload/sim_session.gd").bridge()
	if not bridge.load_mission_live(int(args[2]), bridge.DEFAULT_N_REGIONS, bridge.DEFAULT_FEATURES, fog_filter()) \
			or not bridge.begin_mission_live(int(args[2]), bridge.DEFAULT_N_REGIONS, bridge.DEFAULT_FEATURES) \
			or not bridge.net_reset():
		return {"ok": false, "error": "net_loopback_start: mission load failed: %s" % bridge.last_error()}
	_nm_local = 1 if host else 2
	_nm_remote = 2 if host else 1
	_nm_transport = load("res://autoload/net/loopback_transport.gd").new()
	_nm_transport.attach(_nm_local)
	_nm_transport.attach(_nm_remote)
	if _nm_peer != null:
		_nm_peer.disconnect_from_host()
	_nm_peer = StreamPeerTCP.new()
	if _nm_peer.connect_to_host("127.0.0.1", int(args[1])) != OK:
		return {"ok": false, "error": "net_loopback_start: cannot reach peer qa port"}
	var deadline := Time.get_ticks_msec() + 10000
	while _nm_peer.get_status() == StreamPeerTCP.STATUS_CONNECTING and Time.get_ticks_msec() < deadline:
		_nm_peer.poll()
		OS.delay_msec(2)
	if _nm_peer.get_status() != StreamPeerTCP.STATUS_CONNECTED:
		return {"ok": false, "error": "net_loopback_start: peer qa port did not connect"}
	_nm_budget = 0
	if _nm != null:
		_nm.free()
	_nm = load("res://autoload/net/net_match.gd").new()
	var record := {"peers": [{"peer_id": 1}, {"peer_id": 2}], "local_peer": _nm_local, "host_peer": 1}
	_nm.start(record, _nm_transport, load("res://autoload/net/pipe_sim.gd").new(bridge), func(_m): pass)
	if host:
		_nm.on_lobby_chat(2, {"t": "ready"})
	else:
		_nm.on_lobby_chat(1, {"t": "go"})
	return {"ok": true, "result": {"active": _nm.active()}}


func _net_exchange() -> bool:
	var out: Array = []
	for e in _nm_transport.poll(_nm_remote):
		out.append((e["data"] as PackedByteArray).hex_encode())
	var r := _peer_call("net_peer_pump", [out])
	if not r.get("ok", false):
		return false
	for h in r["result"]["packets"]:
		_nm_transport.send(_nm_remote, _nm_local, String(h).hex_decode())
	return true


func _net_peer_pump(packets: Array) -> Dictionary:
	if _nm == null:
		return {"ok": false, "error": "net_peer_pump: no match"}
	for h in packets:
		_nm_transport.send(_nm_remote, _nm_local, String(h).hex_decode())
	_nm.session.poll()
	var out: Array = []
	for e in _nm_transport.poll(_nm_remote):
		out.append((e["data"] as PackedByteArray).hex_encode())
	return {"ok": true, "result": {"packets": out}}


func _net_run(steps: int) -> Dictionary:
	if _nm == null or not _nm.active():
		return {"ok": false, "error": "net_run: no active match"}
	_nm_budget += steps
	var target: int = _nm_budget
	var guard := steps * 6 + 200
	if _nm.session._released >= target:
		return {"ok": true, "result": {"steps": steps}}
	while _nm.session._released < target and guard > 0:
		if not _net_exchange():
			return {"ok": false, "error": "net_run: peer exchange failed"}
		_nm.session.poll()
		guard -= 1
	if _nm.session._released < target:
		return {"ok": false, "error": "net_run: stalled at tick %d, wanted %d" % [_nm.session._released, target]}
	if _nm._guard.failed:
		return {"ok": false, "error": "net_run: sim step failed: %s" % load("res://autoload/sim_session.gd").bridge().last_error()}
	if not _net_exchange():
		return {"ok": false, "error": "net_run: peer exchange failed"}
	return {"ok": true, "result": {"steps": steps}}


func _net_frame() -> Dictionary:
	if _nm == null:
		return {"ok": false, "error": "net_frame: no match"}
	var ack: Dictionary = load("res://autoload/sim_session.gd").bridge().net_checksum()
	if ack.is_empty():
		return {"ok": false, "error": "net_frame: net_checksum failed"}
	var f: Dictionary = _nm.last_frame()
	return {"ok": true, "result": {"tick": int(ack["tick"]), "checksum": ack["checksum"], "units": (f.get("units", []) as Array).size()}}


func _net_command(cmd: Dictionary) -> Dictionary:
	if _nm == null or not _nm.active():
		return {"ok": false, "error": "net_command: no active match"}
	var c := cmd.duplicate()
	if c.has("units"):
		var ids: Array = []
		for u in c["units"]:
			ids.append(int(u))
		c["units"] = ids
	return {"ok": true, "result": {"queued_for_tick": _nm.command(c)}}


# One request to the peer daemon over _nm_peer; blocks (the peer is another process) until its reply line.
func _peer_call(verb: String, args: Array) -> Dictionary:
	if _nm_peer == null:
		return {"ok": false, "error": "no peer link"}
	_nm_peer.put_data((JSON.stringify({"verb": verb, "args": args}) + "\n").to_utf8_buffer())
	var buf := ""
	var deadline := Time.get_ticks_msec() + 15000
	while Time.get_ticks_msec() < deadline:
		_nm_peer.poll()
		var avail := _nm_peer.get_available_bytes()
		if avail > 0:
			buf += _nm_peer.get_data(avail)[1].get_string_from_utf8()
			var nl := buf.find("\n")
			if nl != -1:
				var parsed = JSON.parse_string(buf.substr(0, nl))
				return parsed if typeof(parsed) == TYPE_DICTIONARY else {"ok": false, "error": "bad peer reply"}
		else:
			OS.delay_msec(1)
	return {"ok": false, "error": "peer timed out"}


## Verb "project" x y (world): the screen pixel the open tactical view draws that world point at.
func _do_project(args: Array) -> Dictionary:
	var t := get_tree()
	var scene: Node = t.current_scene if t != null else null
	if scene == null or not scene.has_method("_to_screen"):
		return {"ok": false, "error": "project: no tactical view"}
	var p: Array = scene._to_screen(float(args[0]) if args.size() > 0 else 0.0, float(args[1]) if args.size() > 1 else 0.0)
	var px := float(p[0])
	var py := float(p[1])
	return {"ok": true, "result": {"x": px, "y": py, "on_screen": px >= 0.0 and px < scene.SCREEN_W and py >= 0.0 and py < scene.SCREEN_H}}


func _do_qa_select(args: Array) -> Dictionary:
	var t := get_tree()
	var scene: Node = t.current_scene if t != null else null
	if scene == null or not scene.has_method("qa_set_selected"):
		return {"ok": false, "error": "qa_select: scene has no qa_set_selected"}
	var ids: Array = args[0] if args.size() > 0 and typeof(args[0]) == TYPE_ARRAY else []
	scene.call("qa_set_selected", ids)
	return {"ok": true, "result": {"count": ids.size()}}


func _do_plant(id: String) -> Dictionary:
	var t := get_tree()
	var scene: Node = t.current_scene if t != null else null
	if scene == null or not scene.has_method("qa_plant"):
		return {"ok": false, "error": "plant: current scene has no qa_plant method"}
	var activated: bool = scene.call("qa_plant", id)
	return {"ok": true, "result": {"id": id, "activated": activated}}


func _collect_tree(node: Node, controls: Array, node3ds: Array, by_name: Dictionary = {}, texts: Dictionary = {}) -> void:
	for child in node.get_children():
		var nm := String(child.name)
		if by_name.has(nm):
			by_name[nm]["count"] += 1
		else:
			by_name[nm] = {"class": child.get_class(), "visible": child.visible if "visible" in child else true, "count": 1}
		if child is Control and "text" in child and not texts.has(nm):
			texts[nm] = String(child.get("text"))
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
					"text": "" if ctrl.get("text") == null else ctrl.get("text"),
					"rect_px": [origin.x, origin.y, far.x - origin.x, far.y - origin.y],
				})
		elif child is Node3D:
			node3ds.append({
				"path": String(child.get_path()),
				"class": child.get_class(),
			})
		_collect_tree(child, controls, node3ds, by_name, texts)


func _arg_value(args: PackedStringArray, flag: String) -> String:
	var idx := args.find(flag)
	if idx == -1 or idx + 1 >= args.size():
		return ""
	return args[idx + 1]

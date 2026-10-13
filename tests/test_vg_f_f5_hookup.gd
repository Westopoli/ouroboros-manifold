extends SceneTree

# Lane F piece F5 (the tactical hookup, VG-F5; the spec's name for the file is tests/test_vg_f5_hookup.gd, written under the
# brief's glob tests/test_vg_f_*.gd), docs/northstar/plans/2026-10-06-steam-multiplayer-wiring-spec.md W5 row and
# interface 5/6/7; visible-game spec lane F ("F5 the hookup right after A12").
# Stories S-142 (no pause, no rewind; the match clock is the net tick), S-140 (orders reach every peer), S-139 (desync
# is shown, never hidden). Rules R-140-02, R-140-03 (stall line), R-139-04 (desync shows tick and section), R-142-01.
# No pipe: SimSession's bridge is a fake that counts the single-player calls; NetMatch is the real autoload run on the
# loopback transport with a fake sim; the frame is the A7 fixture.
#
# The spec leaves these shapes open; this test FIXES them (flagged to the Architect):
#   NetMatch.last_frame() -> Dictionary   the sim's last_frame() ({} when no sim); the view loads it each _process.
#   In a match tactical_view.send_command maps move 0, attack_move 1, attack_target 2 (interface 5) to
#   NetMatch.command({"verb", "units", "x", "y", "arg" (target id for attack_target)}), and calls bridge.send_unit_command
#   not at all. _process calls bridge.tactical_step_n not at all.
#   Desync: the error panel (scenes/shared/error_panel.gd, show_error(reason, retry := true)) shows
#   "Desync at tick N, section NAME" with its Retry button hidden. Stall: a Label whose text contains "waiting for"
#   and the peer id, while NetMatch.state().kind == "stalled".
#   Section NAMES are the nine of tests/net/driver.py SECTIONS: regions factions rng units movement mission fog macro support_map.

const SIM_SESSION := "res://autoload/sim_session.gd"
const VIEW := "res://scenes/tactical_c/tactical_view.tscn"
const FIXTURE := "res://tests/fixtures/tactical_frame_seed11.json"
const LOOPBACK := "res://autoload/net/loopback_transport.gd"
const SECTION_NAMES := ["regions", "factions", "rng", "units", "movement", "mission", "fog", "macro", "support_map"]

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false
var _cur := ""
var _fixture := {}


class FakeBridge extends RefCounted:
	var frame := {}
	var step_calls := 0
	var unit_cmds: Array = []
	var DEFAULT_N_REGIONS := 80
	var DEFAULT_FEATURES := [0]
	func load_tactical_live(_a, _b, _c) -> bool:
		return true
	func live_seed() -> int:
		return 1
	func tactical_frame() -> Dictionary:
		return frame
	func mission_begun() -> bool:
		return true
	func tactical_step_n(_n: int) -> bool:
		step_calls += 1
		return true
	func send_unit_command(c: Dictionary) -> bool:
		unit_cmds.append(c)
		return true
	func mission() -> Dictionary:
		return {}
	func player_faction() -> int:
		return 0
	func last_error() -> String:
		return ""


class FakeSim extends RefCounted:
	var steps := 0
	var log: Array = []
	var frame := {}
	var tamper_tick := -1
	func submit(c: Dictionary) -> void:
		log.append(c.duplicate())
	func step():
		steps += 1
		var r := {"tick": steps}
		if steps % 10 == 0:
			var s := [11, 22, 33, 44, 55]
			if tamper_tick >= 0 and steps >= tamper_tick:
				s[3] = 999
			r["sections"] = s
		frame = _frame_at(steps)
		return r
	func last_frame() -> Dictionary:
		return frame
	var _base := {}
	func _frame_at(t: int) -> Dictionary:
		var f := _base.duplicate(true)
		f["tick"] = t
		return f


func _initialize() -> void:
	await _run_tests()
	_assert(_completed, "the checks did not run to the end (a script error aborted them)")
	print("\n=== VG-F F5 Hookup Test Results ===")
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
		_fail_msgs.append("[%s] %s" % [_cur, msg])


func _labels(node: Node, out: Array[String]) -> void:
	if node is Label:
		out.append((node as Label).text)
	for c in node.get_children():
		_labels(c, out)


func _view(bridge: FakeBridge) -> Node:
	load(SIM_SESSION)._bridge = bridge
	var v: Node = (load(VIEW) as PackedScene).instantiate()
	get_root().add_child(v)
	return v


func _start_match(sim: FakeSim, ids: Array, chat_peers := true) -> Node:
	var nm: Node = get_root().get_node("NetMatch")
	var net = load(LOOPBACK).new()
	for i in ids:
		net.attach(i)
	var peers: Array = []
	for i in ids:
		peers.append({"peer_id": i, "steam_id": 1000 + i, "faction": 0})
	var rec := {"local_peer": 0, "host_peer": 0, "peers": peers, "input_delay": 3, "repeat": 5, "stall_ticks": 20, "drop_ticks": 1200}
	nm.start(rec, net, sim, func(_m): pass)
	if chat_peers:
		for i in ids:
			if i != 0:
				nm.on_lobby_chat(i, {"t": "ready"})
	return nm


func _run_tests() -> void:
	var txt := FileAccess.get_file_as_string(FIXTURE)
	_fixture = JSON.parse_string(txt)
	await _t_control_single_player()
	if get_root().get_node_or_null("NetMatch") == null:
		_cur = "setup"
		_assert(false, "no NetMatch autoload at /root/NetMatch")
		_completed = true
		return
	await _t_match_no_step_and_orders()
	await _t_frames_from_netmatch()
	await _t_desync_panel()
	await _t_stall_line()
	LoadReset.reset()
	_completed = true


class LoadReset:
	static func reset() -> void:
		var s = load("res://autoload/sim_session.gd")
		s._bridge = null


func _t_control_single_player() -> void:
	_cur = "control_single_player"
	var b := FakeBridge.new()
	b.frame = _fixture
	var v := _view(b)
	await process_frame
	v._process(0.5)
	_assert(b.step_calls > 0, "CONTROL: with no match the view steps the sim itself (tactical_step_n), got %d calls" % b.step_calls)
	v.send_command({"kind": "move", "unit_ids": [1, 2], "x": 5.0, "y": 6.0})
	_assert(b.unit_cmds.size() == 1, "CONTROL: with no match an order goes to bridge.send_unit_command, got %d" % b.unit_cmds.size())
	v.queue_free()
	await process_frame


func _t_match_no_step_and_orders() -> void:
	_cur = "match_orders"
	var b := FakeBridge.new()
	b.frame = _fixture
	var sim := FakeSim.new()
	sim._base = _fixture
	var nm := _start_match(sim, [0])
	_assert(nm.active(), "CONTROL: a solo host match is active after start()")
	var v := _view(b)
	await process_frame
	v._process(1.0)
	_assert(b.step_calls == 0, "S-142/W5: in a match the view issues no tactical_step (NetMatch owns the tick), got %d calls" % b.step_calls)
	v.send_command({"kind": "move", "unit_ids": [1, 2], "x": 5.0, "y": 6.0})
	v.send_command({"kind": "attack_move", "unit_ids": [3], "x": 7.0, "y": 8.0})
	v.send_command({"kind": "attack_target", "unit_ids": [4], "target": 9})
	for i in 40:
		nm._process(0.05)
	_assert(b.unit_cmds.is_empty(), "S-140/W5: no order goes to the immediate command verb in a match, got %d" % b.unit_cmds.size())
	var verbs: Array = []
	for c in sim.log:
		verbs.append(int(c.get("verb", -1)))
	verbs.sort()
	_assert(verbs == [0, 1, 2], "S-140: the three orders reach the session as verbs 0 (move), 1 (attack_move), 2 (attack_target), got %s" % str(verbs))
	for c in sim.log:
		if int(c.get("verb", -1)) == 2:
			_assert(int(c.get("arg", -1)) == 9 and c.get("units", []) == [4], "attack_target carries the target in arg and the unit list, got %s" % str(c))
		if int(c.get("verb", -1)) == 0:
			_assert(c.get("units", []) == [1, 2] and float(c.get("x", 0)) == 5.0 and float(c.get("y", 0)) == 6.0, "move carries units and the point, got %s" % str(c))
	v.queue_free()
	await process_frame


func _t_frames_from_netmatch() -> void:
	_cur = "frames_from_netmatch"
	var b := FakeBridge.new()
	b.frame = _fixture
	var sim := FakeSim.new()
	sim._base = _fixture
	var nm := _start_match(sim, [0])
	_assert(nm.has_method("last_frame"), "NetMatch has no last_frame() for the view to read")
	var v := _view(b)
	await process_frame
	for i in 30:
		nm._process(0.05)
	v._process(0.05)
	var st: Dictionary = v.qa_state()
	_assert(int(st.get("tick", -1)) == sim.steps and sim.steps > 0, "the view shows the match tick %d from NetMatch.last_frame(), got %s" % [sim.steps, str(st.get("tick"))])
	v.queue_free()
	await process_frame


func _panel(v: Node) -> Node:
	for c in v.get_children():
		if c.has_method("show_error"):
			return c
	return null


func _t_desync_panel() -> void:
	_cur = "desync_panel"
	var b := FakeBridge.new()
	b.frame = _fixture
	var sim := FakeSim.new()
	sim._base = _fixture
	sim.tamper_tick = 20
	var peer_sim := FakeSim.new()
	peer_sim._base = _fixture
	var nm := _start_match(sim, [0, 1])
	# the second peer is an honest session on the same loopback: drive it by hand
	var other = load("res://autoload/net/lockstep_session.gd").new()
	other.setup(1, [0, 1], nm.session._net, peer_sim, {"input_delay": 3, "repeat": 5, "stall_ticks": 20, "drop_ticks": 1200})
	var v := _view(b)
	await process_frame
	for i in 90:
		nm._process(0.05)
		other.poll()
	_assert(nm.state().get("kind", "") == "desync", "CONTROL: the tampered sim makes NetMatch report desync, got %s" % str(nm.state()))
	v._process(0.05)
	var p := _panel(v)
	_assert(p != null, "a desync shows the error panel in the view")
	if p != null:
		var labels: Array[String] = []
		_labels(p, labels)
		var text := " ".join(labels)
		_assert(text.find("Desync at tick 20") != -1, "the panel says 'Desync at tick 20', got %s" % text)
		var named := false
		for n in SECTION_NAMES:
			if text.find("section " + n) != -1:
				named = true
		_assert(named or text.find("section 3") != -1, "the panel names the section (one of %s), got %s" % [str(SECTION_NAMES), text])
		var retry := p.find_child("Retry", true, false)
		_assert(retry != null and not (retry as Control).visible, "a desync shows no retry button (spec interface 7)")
		var menu := p.find_child("MainMenu", true, false)
		_assert(menu != null and (menu as Control).visible, "the main-menu button stays")
	v.queue_free()
	await process_frame


func _t_stall_line() -> void:
	_cur = "stall_line"
	var b := FakeBridge.new()
	b.frame = _fixture
	var sim := FakeSim.new()
	sim._base = _fixture
	var nm := _start_match(sim, [0, 1])
	var v := _view(b)
	await process_frame
	for i in 60:
		nm._process(0.05)
	_assert(nm.state().get("kind", "") == "stalled" and int(nm.state().get("peer", -1)) == 1, "CONTROL: a silent peer 1 stalls the match, got %s" % str(nm.state()))
	v._process(0.05)
	var labels: Array[String] = []
	_labels(v, labels)
	var found := false
	for l in labels:
		if l.to_lower().find("waiting for") != -1 and l.find("1") != -1:
			found = true
	_assert(found, "R-140-03: the HUD shows a 'waiting for' line naming peer 1, labels: %s" % str(labels))
	v.queue_free()
	await process_frame

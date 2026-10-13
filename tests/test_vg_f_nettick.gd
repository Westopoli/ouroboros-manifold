extends SceneTree

# Piece VG-F-NETTICK (pieces.toml), ruling in ledger rows FINDING-net-first-tick and DRAFT-s140-settle-ticks
# (docs/northstar/plans/push_ledger_2026-09-22.md, day31). Story S-140 ("My orders reach every peer with no server in the middle.").
#
# Rule R-140-02 (E-19, docs/bible/epics/E-19-multiplayer.md:52, word for word):
#   "Given a tactical tick, When commands are exchanged, Then each peer's commands for tick t + d are sent on a reliable
#   channel and every peer applies all peers' commands for tick t in a fixed peer order before advancing The input delay d is
#   3 tactical ticks (150 ms) (Westley, 2026-10-06)."
# Rule R-140-03 (E-19, :53) sits beside it: a peer's commands for tick t are awaited, nothing is applied early or twice.
#
# The ruling sentence of FINDING-net-first-tick (Architect, 2026-10-12), word for word:
#   "when NetMatch.active(), load from NetMatch.last_frame() instead of load_tactical_live, no extra step"
# The finding: tactical_view._load_live calls bridge.load_tactical_live(), which sends one extra tactical_step on each peer when
# the battle scene loads, so the C net tick runs one ahead of the session tick, every move command is stamped tick == st->tick
# and net_submit answers OM_CMD_ERR_LATE (csrc/cmd_stream.c:161, om_cmd_submit). The order never lands.
#
# Why a solo host (Westley's Q-F-1, 2026-10-11: "allowed, so long as the test does everything it can to emulate the reality of two
# players joining and not taking shortcuts beyond what is strictly necessary given the limitation"): the refusal is a property of
# the C tick versus the session tick of ONE peer and needs no second peer. This file never claims to prove the lobby, a join or
# the order crossing between processes: tests/qa/desktop/plays/F/S-140.py stays the two-process acceptance of S-140.
#
# Cases (T0 and the T2 control and the T3 control are green on the built tree; the rest are red until VG-F-NETTICK):
#   T0  R-140-02 controls  a real pipe match with no view: the session tick equals the C net tick, no refusal.
#   T1  R-140-02           mounting the real tactical view does not move the C net tick off the session tick; the view shows the
#                          frame the session holds.
#   T2  R-140-02           a move sent through the view's own route right after the scene loaded is accepted and moves the unit.
#                          Control: the same order with no view mounted is accepted and moves the unit.
#   T3  R-140-02           fake bridge: in a match the view makes no load_tactical_live call and no tactical_step_n call.
#                          Control: with no match the view calls load_tactical_live exactly once.
#
# The 50 ticks of T2 are the brief's window (VG-F-NETTICK test-writer brief), not a Westley threshold: the order is applied at its
# stamp and the unit is read 50 ticks later. The unit is sent 300.0 world units along x (the brief's offset).
#
# Needs the real pipe (pipe/ouroboros_pipe) and a display:
#   timeout 1800 xvfb-run -a -s '-screen 0 1920x1080x24' godot.real --path . --resolution 1920x1080 -s res://tests/test_vg_f_nettick.gd

const SIM_SESSION := "res://autoload/sim_session.gd"
const VIEW := "res://scenes/tactical_c/tactical_view.tscn"
const FIXTURE := "res://tests/fixtures/tactical_frame_seed11.json"
const LOOPBACK := "res://autoload/net/loopback_transport.gd"
const PIPE_SIM := "res://autoload/net/pipe_sim.gd"
const SEED := 1
const POLL_DT := 0.05
const ORDER_WINDOW_TICKS := 50   # the brief's window: 50 ticks after the order is applied
const MOVE_DX := 300.0           # the brief's offset
const POLL_CAP := 600            # hang guard only, not a threshold

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false
var _cur := ""
var _fixture := {}


class FakeBridge extends RefCounted:
	var frame := {}
	var load_calls := 0
	var step_calls := 0
	var DEFAULT_N_REGIONS := 80
	var DEFAULT_FEATURES := [0]
	func load_tactical_live(_a, _b, _c) -> bool:
		load_calls += 1
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
	func send_unit_command(_c: Dictionary) -> bool:
		return true
	func mission() -> Dictionary:
		return {}
	func player_faction() -> int:
		return 0
	func last_error() -> String:
		return ""


class FakeSim extends RefCounted:
	var steps := 0
	var frame := {}
	var _base := {}
	func submit(_c: Dictionary) -> void:
		pass
	func step():
		steps += 1
		var f := _base.duplicate(true)
		f["tick"] = steps
		frame = f
		return {"tick": steps}
	func last_frame() -> Dictionary:
		return frame


func _initialize() -> void:
	await _run_tests()
	_assert(_completed, "the checks did not run to the end (a script error aborted them)")
	print("\n=== VG-F-NETTICK Test Results ===")
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


func _run_tests() -> void:
	# pins the era; the live settings.cfg may hold greek_placeholder, TD-VG-F-NETTICK-2
	# (after one frame: the UIDataBus autoload applies the saved era in its first-frame _ready, which would undo an earlier pin)
	await process_frame
	get_root().get_node("EraConfig").set_era("settled_reach")
	_fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	if get_root().get_node_or_null("NetMatch") == null:
		_cur = "setup"
		_assert(false, "no NetMatch autoload at /root/NetMatch")
		_completed = true
		return
	_cur = "T3_control"
	await _t3_control_no_match()
	_cur = "T3"
	await _t3_match_no_load_no_step()
	_cur = "T0"
	await _t0_controls()
	_cur = "T2_control"
	await _t2_control_no_view()
	_cur = "T1"
	await _t1_and_t2_view()
	_end_real()
	_completed = true


# ---- the real pipe match, started as scenes/lobby/lobby.gd _launch does it, without the lobby ------------------------

func _start_real() -> Dictionary:
	load(SIM_SESSION).reset()
	var bridge = load(SIM_SESSION).bridge()
	_assert(bridge.ensure_session(SEED, bridge.DEFAULT_N_REGIONS, bridge.DEFAULT_FEATURES), "CONTROL: ensure_session opens the world, got: " + str(bridge.last_error()))
	_assert(bridge.begin_mission_live(SEED, bridge.DEFAULT_N_REGIONS, bridge.DEFAULT_FEATURES), "CONTROL: begin_mission_live begins the mission, got: " + str(bridge.last_error()))
	_assert(bridge.net_reset(), "CONTROL: net_reset answers an ack, got: " + str(bridge.last_error()))
	var net = load(LOOPBACK).new()
	net.attach(0)
	var sim = load(PIPE_SIM).new(bridge)
	var nm: Node = get_root().get_node("NetMatch")
	var rec := {"local_peer": 0, "host_peer": 0, "peers": [{"peer_id": 0, "steam_id": 1000, "faction": 0}],
		"input_delay": 3, "repeat": 5, "stall_ticks": 20, "drop_ticks": 1200}
	nm.start(rec, net, sim, func(_m): pass)
	return {"bridge": bridge, "nm": nm, "sim": sim}


func _end_real() -> void:
	var nm: Node = get_root().get_node("NetMatch")
	if nm.active():
		nm.leave()
	load(SIM_SESSION).reset()


func _poll(nm: Node, n: int) -> void:
	for i in n:
		nm._process(POLL_DT)


func _c_tick(bridge) -> int:
	return int(bridge.net_checksum().get("tick", -1))


func _own_units(frame: Dictionary, faction: int) -> Array:
	var out: Array = []
	for u in frame.get("units", []):
		if int(u.get("faction", -1)) == faction:
			out.append(u)
	return out


# The own unit with the lowest id (a fixed, replayable pick) whose x is at least MOVE_DX short of the canvas edge.
func _pick_unit(own: Array, canvas: float) -> Dictionary:
	var best := {}
	for u in own:
		if float(u["x"]) + MOVE_DX > canvas - 1.0:
			continue
		if best.is_empty() or int(u["id"]) < int(best["id"]):
			best = u
	return best


func _unit_in(frame: Dictionary, id: int) -> Dictionary:
	for u in frame.get("units", []):
		if int(u["id"]) == id:
			return u
	return {}


func _move_to_applied(nm: Node, stamp: int) -> void:
	var i := 0
	while int(nm.session._released) < stamp + ORDER_WINDOW_TICKS and i < POLL_CAP:
		nm._process(POLL_DT)
		i += 1


# ---- T0 -------------------------------------------------------------------------------------------------------------

func _t0_controls() -> void:
	var m := _start_real()
	var bridge = m["bridge"]
	var nm: Node = m["nm"]
	var sim = m["sim"]
	_assert(nm.active(), "CONTROL: a solo host match is active after start()")
	_poll(nm, 20)
	var released := int(nm.session._released)
	var ctick := _c_tick(bridge)
	print("PREMISE T0: seed=%d _released=%d C_tick=%d refusals=%s last_frame_empty=%s terrain_empty=%s" % [SEED, released, ctick, str(sim.refusals()), str(nm.last_frame().is_empty()), str(bridge.terrain().is_empty())])
	_assert(released > 0, "R-140-02 CONTROL: twenty polls release at least one tick, got _released=%d" % released)
	_assert(ctick == released, "R-140-02 CONTROL: with no view the C net tick equals the session tick, C tick %d, _released %d" % [ctick, released])
	_assert(sim.refusals().is_empty(), "R-140-02 CONTROL: no command was refused, refusals %s" % str(sim.refusals()))
	_end_real()
	await process_frame


# ---- T2 control: the same order, no view mounted --------------------------------------------------------------------

func _t2_control_no_view() -> void:
	var m := _start_real()
	var bridge = m["bridge"]
	var nm: Node = m["nm"]
	var sim = m["sim"]
	_poll(nm, 20)
	var frame: Dictionary = nm.last_frame()
	var faction := int(bridge.player_faction())
	var own := _own_units(frame, faction)
	var canvas := float(frame.get("map", {}).get("canvas", 0.0))
	var u := _pick_unit(own, canvas)
	_assert(not u.is_empty(), "R-140-02 CONTROL: an own unit with room to move exists (faction %d, %d own units, canvas %s)" % [faction, own.size(), str(canvas)])
	if u.is_empty():
		_end_real()
		return
	var id := int(u["id"])
	var x0 := float(u["x"])
	var y0 := float(u["y"])
	var before_keys: Array = nm.session._cmds[0].keys()
	# the verb 0 dictionary tactical_view._send_match_command builds (scenes/tactical_c/tactical_view.gd:713)
	var stamp: int = nm.command({"verb": 0, "units": [id], "x": x0 + MOVE_DX, "y": y0})
	_move_to_applied(nm, stamp)
	var after := _unit_in(nm.last_frame(), id)
	print("PREMISE T2-control: unit=%d start=(%s,%s) target=(%s,%s) stamp=%d _released=%d refusals=%s end=(%s,%s) keys_before=%s" % [id, str(x0), str(y0), str(x0 + MOVE_DX), str(y0), stamp, int(nm.session._released), str(sim.refusals()), str(after.get("x")), str(after.get("y")), str(before_keys)])
	_assert(sim.refusals().is_empty(), "R-140-02 CONTROL: with no view mounted the order is accepted, refusals %s" % str(sim.refusals()))
	_assert(not after.is_empty() and (float(after["x"]) != x0 or float(after["y"]) != y0), "R-140-02 CONTROL: with no view mounted the unit moves, start (%s,%s) end (%s,%s)" % [str(x0), str(y0), str(after.get("x")), str(after.get("y"))])
	_end_real()
	await process_frame


# ---- T1 and T2: the real view mounted on the real match ------------------------------------------------------------

func _t1_and_t2_view() -> void:
	var m := _start_real()
	var bridge = m["bridge"]
	var nm: Node = m["nm"]
	var sim = m["sim"]
	_poll(nm, 20)
	var released_before := int(nm.session._released)
	var ctick_before := _c_tick(bridge)
	var v: Node = (load(VIEW) as PackedScene).instantiate()
	get_root().add_child(v)
	await process_frame
	await process_frame
	v._process(POLL_DT)
	var released_after := int(nm.session._released)
	var ctick_after := _c_tick(bridge)
	var empty_at_mount: bool = nm.last_frame().is_empty()
	var qa: Dictionary = v.qa_state()
	print("PREMISE T1: before mount _released=%d C_tick=%d; after mount _released=%d C_tick=%d; last_frame_empty=%s; view tick=%s last_frame tick=%s; terrain_empty=%s; refusals=%s" % [released_before, ctick_before, released_after, ctick_after, str(empty_at_mount), str(qa.get("tick")), str(nm.last_frame().get("tick")), str(bridge.terrain().is_empty()), str(sim.refusals())])
	_assert(ctick_before == released_before, "R-140-02 CONTROL: before the view mounts the C net tick equals the session tick, C tick %d, _released %d" % [ctick_before, released_before])
	_assert(ctick_after == released_after, "R-140-02 FINDING-net-first-tick: after the view mounts the C net tick still equals the session tick (no extra tactical_step), C tick %d, _released %d" % [ctick_after, released_after])
	if not empty_at_mount:
		_assert(int(qa.get("tick", -1)) == int(nm.last_frame().get("tick", -2)), "R-140-02 FINDING-net-first-tick: the view shows the frame the session holds, view tick %s, last_frame tick %s" % [str(qa.get("tick")), str(nm.last_frame().get("tick"))])

	# T2: a move at the first tick after the scene loaded, through the view's own route
	var faction: int = int(qa.get("local_faction", -1))
	var canvas := float(qa.get("canvas", 0.0))
	var own: Array = []
	for id_s in qa["units"]:
		var q: Dictionary = qa["units"][id_s]
		if int(q["faction"]) == faction:
			own.append({"id": int(id_s), "x": float(q["x"]), "y": float(q["y"])})
	var u := _pick_unit(own, canvas)
	_assert(not u.is_empty(), "R-140-02: the view has an own unit with room to move (faction %d, %d own units, canvas %s)" % [faction, own.size(), str(canvas)])
	if u.is_empty():
		v.queue_free()
		await process_frame
		return
	var id := int(u["id"])
	var x0 := float(u["x"])
	var y0 := float(u["y"])
	var before_keys: Array = nm.session._cmds[0].keys()
	var sent: bool = v.send_command({"kind": "move", "unit_ids": [id], "x": x0 + MOVE_DX, "y": y0})
	var stamp := -1
	for k in nm.session._cmds[0].keys():
		if not before_keys.has(k):
			stamp = int(k)
	_assert(sent and stamp >= 0, "R-140-02 CONTROL: the view hands the move to the session (send_command %s, stamp %d)" % [str(sent), stamp])
	_move_to_applied(nm, stamp)
	var after := _unit_in(nm.last_frame(), id)
	print("PREMISE T2: seed=%d own_units=%d unit=%d start=(%s,%s) target=(%s,%s) canvas=%s stamp=%d _released=%d refusals=%s end=(%s,%s)" % [SEED, own.size(), id, str(x0), str(y0), str(x0 + MOVE_DX), str(y0), str(canvas), stamp, int(nm.session._released), str(sim.refusals()), str(after.get("x")), str(after.get("y"))])
	_assert(sim.refusals() == [], "R-140-02 FINDING-net-first-tick: the order is not refused (OM_CMD_ERR_LATE is code 1, csrc/cmd_stream.c:161), refusals %s" % str(sim.refusals()))
	_assert(not after.is_empty() and (float(after["x"]) != x0 or float(after["y"]) != y0), "R-140-02 FINDING-net-first-tick: the ordered unit %d moved within %d ticks of the order, start (%s,%s) end (%s,%s)" % [id, ORDER_WINDOW_TICKS, str(x0), str(y0), str(after.get("x")), str(after.get("y"))])
	v.queue_free()
	await process_frame
	_end_real()


# ---- T3: fake bridge, counting calls -------------------------------------------------------------------------------

func _fake_view(b: FakeBridge) -> Node:
	load(SIM_SESSION)._bridge = b
	var v: Node = (load(VIEW) as PackedScene).instantiate()
	get_root().add_child(v)
	return v


func _start_fake_match(sim: FakeSim) -> Node:
	var nm: Node = get_root().get_node("NetMatch")
	var net = load(LOOPBACK).new()
	net.attach(0)
	var rec := {"local_peer": 0, "host_peer": 0, "peers": [{"peer_id": 0, "steam_id": 1000, "faction": 0}],
		"input_delay": 3, "repeat": 5, "stall_ticks": 20, "drop_ticks": 1200}
	nm.start(rec, net, sim, func(_m): pass)
	return nm


func _t3_control_no_match() -> void:
	var b := FakeBridge.new()
	b.frame = _fixture
	var v := _fake_view(b)
	await process_frame
	_assert(not get_root().get_node("NetMatch").active(), "CONTROL: no match is active")
	_assert(b.load_calls == 1, "R-140-02 CONTROL: with no match the mounted view calls load_tactical_live exactly once, got %d" % b.load_calls)
	v.queue_free()
	await process_frame


func _t3_match_no_load_no_step() -> void:
	# a match whose sim has already released frames
	var b := FakeBridge.new()
	b.frame = _fixture
	var sim := FakeSim.new()
	sim._base = _fixture
	var nm := _start_fake_match(sim)
	_assert(nm.active(), "CONTROL: a solo host match is active after start()")
	_poll(nm, 5)
	_assert(not nm.last_frame().is_empty(), "CONTROL: after five polls the match holds a frame")
	var v := _fake_view(b)
	await process_frame
	v._process(POLL_DT)
	_assert(b.load_calls == 0, "R-140-02 FINDING-net-first-tick: in a match the mounted view makes zero load_tactical_live calls, got %d" % b.load_calls)
	_assert(b.step_calls == 0, "R-140-02 FINDING-net-first-tick: in a match the mounted view makes zero tactical_step_n calls, got %d" % b.step_calls)
	v.queue_free()
	await process_frame
	nm.leave()

	# a match whose sim has made no step yet: last_frame() is empty. Architect gap 1 (args.emptyFrame = wait) is not asserted:
	# only that mounting does not error and no load_tactical_live call happens.
	var b2 := FakeBridge.new()
	b2.frame = _fixture
	var sim2 := FakeSim.new()
	sim2._base = _fixture
	var nm2 := _start_fake_match(sim2)
	_assert(nm2.last_frame().is_empty(), "CONTROL: before any poll the match holds no frame")
	var v2 := _fake_view(b2)
	await process_frame
	v2._process(POLL_DT)
	_assert(is_instance_valid(v2) and v2.is_inside_tree(), "R-140-02: mounting the view on an empty-frame match leaves the view standing")
	_assert(b2.load_calls == 0, "R-140-02 FINDING-net-first-tick: an empty-frame match mounts with zero load_tactical_live calls, got %d" % b2.load_calls)
	_assert(b2.step_calls == 0, "R-140-02 FINDING-net-first-tick: an empty-frame match mounts with zero tactical_step_n calls, got %d" % b2.step_calls)
	v2.queue_free()
	await process_frame
	nm2.leave()
	load(SIM_SESSION)._bridge = null

extends SceneTree

# Lane F piece W2 (PipeSim + bridge wrappers), docs/northstar/plans/2026-10-06-steam-multiplayer-wiring-spec.md
# "Interfaces fixed" 2 and 3 and the audit tables; visible-game spec section 2 (tactical frame shapes).
# Stories S-140 (commands over the wire), S-139 (one sim every machine). Rules R-140-02, R-139-04, R-139-06.
# Frames are fixture dictionaries; no live pipe (the live side is tests/transport/test_vg_f_w2_net_step_frame.py).
#
# The spec leaves these shapes open; this test FIXES them so the builder has one reading (flagged to the Architect):
#   c_bridge.gd gains net_reset() -> bool, net_submit(cmd: Dictionary) -> int (the net_ack code, -1 on failure),
#       net_step(n: int = 1, frame: bool = true) -> Dictionary (the _request result keyed "net_ack" and "tactical";
#       {} on failure), net_checksum() -> Dictionary.
#   autoload/net/pipe_sim.gd: PipeSim.new(bridge); submit(cmd) -> int code; step() -> {"tick", "sections"?} or null;
#       last_frame() -> Dictionary (the reconstructed tactical frame of the last step); refusals() -> Array of int
#       nonzero codes in order. step() calls bridge.net_step(1, true), runs bridge._reconstruct_tactical(frame) on EVERY
#       frame, returns null on {} and when frame.tick != ack.tick (a stray tactical_step).

const PIPE_SIM := "res://autoload/net/pipe_sim.gd"
const BRIDGE := "res://autoload/c_bridge.gd"
const SESSION := "res://autoload/net/lockstep_session.gd"
const LOOPBACK := "res://autoload/net/loopback_transport.gd"
const U64_MAX := "18446744073709551615"
const U64_MAX_1 := "18446744073709551614"

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false
var _cur := ""


class FakeBridge extends RefCounted:
	var steps := 0
	var recon_calls := 0
	var step_args: Array = []
	var refuse_code := 0
	var fail_steps := false
	var skew_frame_tick := false
	var log: Array = []
	var state := 7
	func net_submit(cmd: Dictionary) -> int:
		if refuse_code != 0:
			return refuse_code
		log.append(cmd.duplicate())
		state = (state * 31 + int(cmd.get("seq", 0)) * 7 + int(cmd.get("peer", 0)) + steps) % 1000003
		return 0
	func net_step(n: int = 1, frame: bool = true) -> Dictionary:
		step_args.append([n, frame])
		if fail_steps:
			return {}
		steps += n
		var ack := {"type": "net_ack", "tick": steps, "code": 0}
		if steps % 10 == 0:
			ack["sections"] = [state, state + 1, 5]
		var fr := {"type": "tactical", "tick": steps + (1 if skew_frame_tick else 0), "full": steps == 1,
			"units": [{"id": 3, "faction": 0, "x": 1.0, "y": 2.0, "state": 0}], "units_changed": []}
		return {"net_ack": ack, "tactical": fr}
	func _reconstruct_tactical(frame: Dictionary) -> Dictionary:
		recon_calls += 1
		var v := frame.duplicate()
		v["reconstructed"] = true
		return v


func _initialize() -> void:
	_run_tests()
	_assert(_completed, "the checks did not run to the end (a script error aborted them)")
	print("\n=== VG-F W2 PipeSim Test Results ===")
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


func _have(path: String) -> bool:
	if ResourceLoader.exists(path):
		return true
	_assert(false, "%s does not exist yet (W2 not built)" % path)
	return false


func _run_tests() -> void:
	_t_control_fake_bridge()
	_t_wrappers_exist()
	_t_net_ack_precision()
	if _have(PIPE_SIM):
		_t_submit_and_refusals()
		_t_step_shapes()
		_t_every_frame_reconstructed()
		_t_failed_step_is_null()
		_t_tick_mismatch_is_null()
		_t_session_over_two_pipesims()
	_completed = true


func _t_control_fake_bridge() -> void:
	_cur = "control_fake_bridge"
	var b := FakeBridge.new()
	var r := b.net_step(1, true)
	_assert(r.has("net_ack") and r.has("tactical") and int(r["net_ack"]["tick"]) == 1, "CONTROL: the fake bridge answers an ack and a frame with equal ticks")
	b.skew_frame_tick = true
	_assert(int(b.net_step(1, true)["tactical"]["tick"]) != int(b.steps), "CONTROL: the skew switch really skews the frame tick")


func _t_wrappers_exist() -> void:
	_cur = "bridge_wrappers"
	var names := {}
	for m in load(BRIDGE).get_script_method_list():
		names[m["name"]] = true
	for w in ["net_reset", "net_submit", "net_step", "net_checksum"]:
		_assert(names.has(w), "c_bridge.gd has no %s wrapper (W2, interface 3)" % w)


# Section words and the checksum are uint64 decimals; JSON doubles lose the low bits (spec: "net_ack precision patch").
func _t_net_ack_precision() -> void:
	_cur = "net_ack_precision"
	var bridge = load(BRIDGE).new()
	var body := ('{"type":"net_ack","tick":10,"code":0,"checksum":%s,"sections":[%s,%s,1]}' % [U64_MAX, U64_MAX, U64_MAX_1]).to_utf8_buffer()
	var path := "user://vg_f_w2_ack.bin"
	var f := FileAccess.open(path, FileAccess.WRITE)
	var hdr := PackedByteArray([(body.size() >> 24) & 255, (body.size() >> 16) & 255, (body.size() >> 8) & 255, body.size() & 255])
	f.store_buffer(hdr)
	f.store_buffer(body)
	f.close()
	var rd := FileAccess.open(path, FileAccess.READ)
	var frame = bridge._read_live_frame(rd)
	rd.close()
	DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
	_assert(frame is Dictionary and frame.get("type", "") == "net_ack", "CONTROL: the framed net_ack is read back as a net_ack, got %s" % str(frame))
	if not (frame is Dictionary):
		return
	var secs: Array = frame.get("sections", [])
	_assert(secs.size() == 3, "CONTROL: three section words arrive")
	if secs.size() == 3:
		_assert(int(secs[0]) == -1, "a section of 2^64-1 reads as int64 bit pattern -1, got %s (W2: patch extended to net_ack, R-139-04)" % str(secs[0]))
		_assert(int(secs[1]) == -2, "a section differing in the LOW bit (2^64-2) reads -2, got %s: the desync would be invisible" % str(secs[1]))
	_assert(int(frame.get("checksum", 0)) == -1, "the net_ack checksum 2^64-1 reads -1, got %s" % str(frame.get("checksum")))


func _t_submit_and_refusals() -> void:
	_cur = "submit_refusals"
	var b := FakeBridge.new()
	var ps = load(PIPE_SIM).new(b)
	_assert(ps.submit({"peer": 0, "seq": 1, "verb": 0}) == 0, "submit returns the ack code (0 accepted)")
	b.refuse_code = 3
	_assert(ps.submit({"peer": 0, "seq": 2, "verb": 0}) == 3, "a net_submit refusal code reaches the caller (W2 test)")
	_assert(ps.refusals() == [3], "refusals() records the nonzero code in order, got %s" % str(ps.refusals()))


func _t_step_shapes() -> void:
	_cur = "step_shapes"
	var b := FakeBridge.new()
	var ps = load(PIPE_SIM).new(b)
	var r = ps.step()
	_assert(r != null and int(r["tick"]) == 1, "step() returns {tick} for the first step, got %s" % str(r))
	_assert(b.step_args == [[1, true]], "step() asks net_step(1, true): one tick, with the frame, got %s" % str(b.step_args))
	_assert(r != null and not r.has("sections"), "no sections off the checksum cadence")
	for i in 9:
		r = ps.step()
	_assert(r != null and int(r["tick"]) == 10 and r.has("sections") and r["sections"].size() == 3, "tick 10 carries the sections, got %s" % str(r))
	_assert(ps.last_frame().get("reconstructed", false) == true and int(ps.last_frame()["tick"]) == 10, "last_frame() is the reconstructed frame of the last step")


func _t_every_frame_reconstructed() -> void:
	_cur = "every_frame_reconstructed"
	var b := FakeBridge.new()
	var ps = load(PIPE_SIM).new(b)
	for i in 7:
		ps.step()
	_assert(b.recon_calls == 7, "_reconstruct_tactical runs on every frame, none skipped (Q-NET-03): %d of 7" % b.recon_calls)


func _t_failed_step_is_null() -> void:
	_cur = "failed_step_null"
	var b := FakeBridge.new()
	b.fail_steps = true
	var ps = load(PIPE_SIM).new(b)
	_assert(ps.step() == null, "an empty reply ({}) from net_step makes step() return null so the session stops")


func _t_tick_mismatch_is_null() -> void:
	_cur = "tick_mismatch_null"
	var b := FakeBridge.new()
	b.skew_frame_tick = true
	var ps = load(PIPE_SIM).new(b)
	_assert(ps.step() == null, "frame.tick != ack.tick means a stray tactical_step: step() returns null and the match ends")


func _t_session_over_two_pipesims() -> void:
	_cur = "session_two_pipesims"
	var net = load(LOOPBACK).new()
	var bridges := [FakeBridge.new(), FakeBridge.new()]
	var sess: Array = []
	for i in 2:
		net.attach(i)
		var s = load(SESSION).new()
		s.setup(i, [0, 1], net, load(PIPE_SIM).new(bridges[i]), {"input_delay": 3, "repeat": 5, "stall_ticks": 20, "drop_ticks": 1200})
		sess.append(s)
	for round in 400:
		if round == 10:
			sess[0].command({"verb": 0, "x": 5.0, "y": 6.0, "units": [1, 2]})
		if round == 25:
			sess[1].command({"verb": 1, "x": 9.0, "y": 1.0, "units": [3]})
		for s in sess:
			s.poll()
		if bridges[0].steps >= 200 and bridges[1].steps >= 200:
			break
	_assert(bridges[0].steps >= 200 and bridges[1].steps >= 200, "both PipeSim-backed sessions reach tick 200, got %d and %d" % [bridges[0].steps, bridges[1].steps])
	_assert(sess[0].desync().is_empty() and sess[1].desync().is_empty(), "equal command streams give no desync (R-139-04), got %s %s" % [str(sess[0].desync()), str(sess[1].desync())])
	_assert(bridges[0].state == bridges[1].state and bridges[0].log.size() == 2, "both sims saw both commands in one order (R-140-02)")

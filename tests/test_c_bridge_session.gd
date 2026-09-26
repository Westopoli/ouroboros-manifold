extends SceneTree

# Piece C2-4 (docs/architecture.md "persistent client session (v1.1)"):
# autoload/c_bridge.gd keeps ONE pipe/ouroboros_pipe process open, decodes its
# frames on a reader thread into a mutex-guarded queue, and applies them in
# order when pump() drains the queue on the main thread (scenes call pump()
# from their own _process; the bridge is a RefCounted, never an autoload).
# Deltas are applied in place to the bridge's snapshot, so a `step n` animates
# without a reload. Contract this test requires of the bridge:
#   open_session(seed, n_regions, features) -> bool   spawns the pipe, sends set_seed
#                                                     and snapshot; false if it cannot spawn
#   pump() -> int                                     drains the queue, applies frames in
#                                                     order, emits signals, returns the number applied
#   send_command(cmd: Dictionary) -> void             one framed command on the main thread
#   step(n: int) -> void                              send_command({type:cmd,name:step,n:n})
#   close_session() -> void                           kills the pipe, joins the reader thread
#   signals frame_received(frame), snapshot_changed(tick)
#   snapshot() / last_error()                         as today; snapshot() is updated in place
# A delta carries changed region rows by index, faction rows by id, tick, and
# checksum on cadence ticks; after any number of deltas the bridge's snapshot
# must equal the server's own snapshot of the same tick (compared below).

const SEED := 1
const STEPS := 200
const SNAPSHOT_TIMEOUT_MS := 8000
const RUN_TIMEOUT_MS := 30000

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false


func _initialize() -> void:
	await _run_tests()
	_assert(_completed, "the session checks did not run to the end (a script error aborted them, or c_bridge.gd lacks open_session / pump / send_command / step / close_session / frame_received / snapshot_changed / DEFAULT_FEATURES)")
	print("\n=== C Bridge Session Test Results ===")
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


func _pump_until(bridge, pred: Callable, timeout_ms: int) -> bool:
	var deadline := Time.get_ticks_msec() + timeout_ms
	while Time.get_ticks_msec() < deadline:
		bridge.pump()
		if pred.call():
			return true
		OS.delay_msec(5)
	return false


func _owners(snap: Dictionary) -> Dictionary:
	var out := {}
	for r in snap.get("regions", []):
		out[int(r.get("i", -1))] = int(r.get("owner", -1))
	return out


func _run_tests() -> void:
	var CBridge = load("res://autoload/c_bridge.gd")
	var bridge = CBridge.new()
	for m in ["open_session", "pump", "send_command", "step", "close_session", "snapshot", "last_error"]:
		_assert(bridge.has_method(m), "c_bridge.gd missing method (piece C2-4 not attached yet): " + m)
		if not bridge.has_method(m):
			return
	for sig in ["frame_received", "snapshot_changed"]:
		_assert(bridge.has_signal(sig), "c_bridge.gd missing signal (piece C2-4 not attached yet): " + sig)
		if not bridge.has_signal(sig):
			return
	if not CBridge.get_script_constant_map().has("DEFAULT_FEATURES"):
		_assert(false, "c_bridge.gd missing constant DEFAULT_FEATURES")
		return

	var frames_seen := [0]
	var last_tick := [-1]
	bridge.frame_received.connect(func(_f): frames_seen[0] += 1)
	bridge.snapshot_changed.connect(func(t): last_tick[0] = int(t))

	_assert(bridge.open_session(SEED, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES), "open_session returned false (last_error = %s)" % bridge.last_error())
	var got_snapshot := _pump_until(bridge, func(): return (bridge.snapshot().get("regions", []) as Array).size() > 0, SNAPSHOT_TIMEOUT_MS)
	_assert(got_snapshot, "no snapshot within %d ms of open_session (last_error = %s)" % [SNAPSHOT_TIMEOUT_MS, bridge.last_error()])
	if not got_snapshot:
		bridge.close_session()
		return
	var initial := _owners(bridge.snapshot())
	_assert(initial.size() == CBridge.DEFAULT_N_REGIONS, "initial snapshot has %d regions, expected %d" % [initial.size(), CBridge.DEFAULT_N_REGIONS])
	_assert(int(bridge.snapshot().get("tick", -1)) == 0, "initial snapshot tick = %s, expected 0" % bridge.snapshot().get("tick", -1))

	bridge.step(STEPS)
	var reached := _pump_until(bridge, func(): return int(bridge.snapshot().get("tick", 0)) >= STEPS, RUN_TIMEOUT_MS)
	_assert(reached, "bridge snapshot tick = %s after step %d and %d ms of pumping" % [bridge.snapshot().get("tick", -1), STEPS, RUN_TIMEOUT_MS])
	_assert(int(last_tick[0]) == STEPS, "snapshot_changed last fired with tick %s, expected %d" % [last_tick[0], STEPS])
	_assert(frames_seen[0] >= STEPS, "frame_received fired %d times for %d deltas" % [frames_seen[0], STEPS])

	var after := _owners(bridge.snapshot())
	var changed := 0
	for i in initial:
		if after.get(i, initial[i]) != initial[i]:
			changed += 1
	_assert(changed >= 1, "no region changed owner over %d live ticks with the full strategic feature set (seed %d)" % [STEPS, SEED])

	var applied: Dictionary = bridge.snapshot().duplicate(true)
	var server_snap: Array = [null]
	var grab := func(f): if f.get("type", "") == "snapshot": server_snap[0] = f
	bridge.frame_received.connect(grab)
	bridge.send_command({"type": "cmd", "name": "snapshot"})
	var got_server := _pump_until(bridge, func(): return server_snap[0] != null, SNAPSHOT_TIMEOUT_MS)
	_assert(got_server, "no snapshot frame answered the snapshot command")
	if got_server:
		var s: Dictionary = server_snap[0]
		_assert(_owners(s) == _owners(applied), "delta-applied owners differ from the server's own snapshot at tick %d" % STEPS)
		_assert(int(s.get("tick", -1)) == int(applied.get("tick", -2)), "delta-applied tick %s differs from the server's %s" % [applied.get("tick"), s.get("tick")])
		_assert(s.get("checksum", 1) == applied.get("checksum", 2), "delta-applied checksum %s differs from the server's %s" % [applied.get("checksum"), s.get("checksum")])
		var mismatched := 0
		var by_i := {}
		for r in s.get("regions", []):
			by_i[int(r.get("i", -1))] = r
		for r in applied.get("regions", []):
			var sr: Dictionary = by_i.get(int(r.get("i", -1)), {})
			for k in ["military", "economy", "tension", "population", "stability"]:
				if not is_equal_approx(float(r.get(k, 0.0)), float(sr.get(k, -1.0))):
					mismatched += 1
		_assert(mismatched == 0, "%d region values differ between the delta-applied snapshot and the server's" % mismatched)

	bridge.close_session()

	var bad = CBridge.new()
	_assert(bad.open_session(SEED, 30, CBridge.DEFAULT_FEATURES), "open_session at 30 regions should still spawn the pipe")
	var errored := _pump_until(bad, func(): return bad.last_error() != "", SNAPSHOT_TIMEOUT_MS)
	_assert(errored, "a below-floor set_seed left last_error empty (silent failure)")
	_assert(bad.last_error() == "generation failed", "last_error = '%s', expected the pipe's 'generation failed'" % bad.last_error())
	bad.close_session()

	# C2-8: c_bridge.gd stores player_faction from the snapshot frame.
	# Before any world: player_faction() == -1.
	# After the first snapshot from set_seed: player_faction() == snapshot["player_faction"].
	var pf_bridge = CBridge.new()
	_assert(pf_bridge.has_method("player_faction"), "c_bridge.gd missing method player_faction (piece C2-8 not attached yet)")
	if not pf_bridge.has_method("player_faction"):
		return
	_assert(pf_bridge.player_faction() == -1, "player_faction() should be -1 before any world exists, got %d" % pf_bridge.player_faction())

	_assert(pf_bridge.open_session(SEED, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES), "open_session for player_faction test returned false: %s" % pf_bridge.last_error())
	var got_snap_pf := _pump_until(pf_bridge, func(): return (pf_bridge.snapshot().get("regions", []) as Array).size() > 0, SNAPSHOT_TIMEOUT_MS)
	_assert(got_snap_pf, "no snapshot within %d ms for player_faction test (last_error = %s)" % [SNAPSHOT_TIMEOUT_MS, pf_bridge.last_error()])
	if got_snap_pf:
		var snap_pf: int = int(pf_bridge.snapshot().get("player_faction", -999))
		_assert(snap_pf != -999, "snapshot frame missing player_faction key (T1-14 not on this branch)")
		_assert(pf_bridge.player_faction() == snap_pf, "bridge.player_faction() = %d, snapshot['player_faction'] = %d (mismatch)" % [pf_bridge.player_faction(), snap_pf])
	pf_bridge.close_session()

	_completed = true

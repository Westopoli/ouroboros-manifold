extends SceneTree

# Piece W0 of docs/northstar/plans/2026-10-06-steam-multiplayer-wiring-spec.md (rev 5):
# lockstep session catch-up, per-destination coverage, sim failure, packet validation.
# Rules: E-19 R-140-02 to R-140-04 (the session). Written before the code: RED on origin/main.
#
# Interface this file fixes beyond the spec (the spec names behaviour, not method names;
# the builder implements these or the Architect renames them here):
#   session.state() -> String        "sim_failed" after step() returned null (else any other string)
#   session.bad_packet_count() -> int  packets dropped by _receive validation, counted
# Packet (var_to_bytes): [n:int, cmds:Array of [tick:int, cmd:Dictionary], sums:Array of
#   [tick:int, sections:Array of int], released:int]. Command keys follow architecture.md net_submit:
#   tick, peer, seq, verb, arg, layer, x, y (floats), units (Array of int, size 1..70).
# The per-tick command cap is 16 (spec: "draft"; Westley owns the number).

const SESSION := "res://autoload/net/lockstep_session.gd"
const LOOPBACK := "res://autoload/net/loopback_transport.gd"

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false
var _Session = null
var _Loop = null


class SpyNet extends RefCounted:
	var inbox := {}      # id -> Array of {"from", "data"}
	var sent: Array = [] # [from, to, decoded packet]
	func attach(id: int) -> void:
		inbox[id] = []
	func send(from: int, to: int, data: PackedByteArray) -> void:
		sent.append([from, to, bytes_to_var(data)])
	func inject(to: int, from: int, pkt) -> void:
		inbox[to].append({"from": from, "data": var_to_bytes(pkt)})
	func poll(id: int) -> Array:
		var out: Array = inbox[id]
		inbox[id] = []
		return out
	func last_to(dest: int):
		for i in range(sent.size() - 1, -1, -1):
			if int(sent[i][1]) == dest:
				return sent[i][2]
		return null


class FakeSim extends RefCounted:
	var steps := 0
	var calls := 0
	var fail_at := -1    # the call number whose step() returns null
	var log: Array = []  # [steps_before, peer, seq]
	func submit(c: Dictionary) -> void:
		log.append([steps, int(c.get("peer", -1)), int(c.get("seq", -1))])
	func step():
		calls += 1
		if calls == fail_at:
			return null
		steps += 1
		return {"tick": steps}


func _initialize() -> void:
	_run_tests()
	_assert(_completed, "the checks did not run to the end (a script error aborted them)")
	print("\n=== Lockstep Catch-up Test Results ===")
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


func _cmd(peer: int, tick: int, seq := 0, units := [4, 5]) -> Dictionary:
	return {"tick": tick, "peer": peer, "seq": seq, "verb": 0, "arg": 0, "layer": 0,
			"x": 100.0, "y": 200.0, "units": units}


# One session (local id 1) over a spy transport; peers [1, 2] or [1, 2, 3].
func _mk(peers: Array, opts := {}) -> Dictionary:
	var net := SpyNet.new()
	var sim := FakeSim.new()
	for id in peers:
		net.attach(id)
	var o := {"input_delay": 3, "repeat": 5, "stall_ticks": 1000, "drop_ticks": 2000}
	o.merge(opts, true)
	var s = _Session.new()
	s.setup(1, peers, net, sim, o)
	return {"s": s, "net": net, "sim": sim}


func _spin(s, n: int) -> void:
	for i in n:
		s.poll()


func _run_tests() -> void:
	if not ResourceLoader.exists(SESSION) or not ResourceLoader.exists(LOOPBACK):
		_assert(false, "session or loopback transport missing")
		return
	_Session = load(SESSION)
	_Loop = load(LOOPBACK)
	_test_catchup_cap()
	_test_catchup_command_order()
	_test_packet_released_field()
	_test_coverage_per_destination()
	_test_coverage_window_64()
	_test_sim_null_ends_session()
	_test_receive_control()
	_test_receive_bad_shapes()
	_test_receive_cap()
	_completed = true


# W0 / E-19 R-140-02: after a stall, one poll releases every tick whose commands are in, up to 8.
func _test_catchup_cap() -> void:
	var e := _mk([1, 2])
	_spin(e["s"], 10)  # peer 2 silent for 10 polls; nothing releases
	_assert(e["sim"].steps == 0, "setup: nothing released while peer 2 is silent")
	# peer 2 now delivers one packet covering ticks 1..10 (its released is 0)
	e["net"].inject(1, 2, [10, [], [], 0])
	e["s"].poll()
	_assert(e["sim"].steps == 8, "catch-up: one poll releases 8 ticks (catchup_max) when 10 are covered (steps %d)" % e["sim"].steps)
	e["s"].poll()
	_assert(e["sim"].steps == 10, "catch-up: the next poll releases the remaining covered ticks, no more (steps %d)" % e["sim"].steps)


# W0 / E-19 R-140-03: catch-up keeps tick order; commands apply just before their own tick's step.
func _test_catchup_command_order() -> void:
	var e := _mk([1, 2])
	_spin(e["s"], 10)
	e["net"].inject(1, 2, [10, [[2, _cmd(2, 2)], [9, _cmd(2, 9, 1)]], [], 0])
	e["s"].poll()
	e["s"].poll()  # TD-NET-catchup-cap: the first poll releases ticks 1..8 (cap), tick 9 follows
	var log: Array = e["sim"].log
	_assert(log.size() == 2 and log[0][0] == 1 and log[1][0] == 8,
			"catch-up submits each command before its own tick's step (log %s)" % str(log))


# W0 / E-19 R-140-02: every packet carries a fourth element, the sender's _released.
func _test_packet_released_field() -> void:
	var e := _mk([1, 2])
	e["s"].poll()
	var p = e["net"].last_to(2)
	_assert(typeof(p) == TYPE_ARRAY and p.size() == 4 and typeof(p[3]) == TYPE_INT and p[3] == 0,
			"a packet is [n, cmds, sums, released] with released 0 before any release (got %s)" % str(p))
	e["net"].inject(1, 2, [3, [], [], 0])
	e["s"].poll()
	e["s"].poll()
	var q = e["net"].last_to(2)
	_assert(e["sim"].steps > 0 and typeof(q) == TYPE_ARRAY and q.size() == 4 and q[3] == e["sim"].steps,
			"the fourth element tracks the sender's own released count (steps %d, packet %s)" % [e["sim"].steps, str(q)])


# W0 / E-19 R-140-02: _send carries commands for every tick from max(peer_released+1, n-63) to n,
# per destination (peer 2 reported released 7, peer 3 reported released 0).
func _test_coverage_per_destination() -> void:
	var e := _mk([1, 2, 3])
	e["s"].command({"verb": 0, "arg": 0, "layer": 0, "x": 1.0, "y": 2.0, "units": [4]})  # stamped tick 3
	e["net"].inject(1, 2, [10, [], [], 7])
	e["net"].inject(1, 3, [1, [], [], 0])
	_spin(e["s"], 12)
	var to2 = e["net"].last_to(2)
	var to3 = e["net"].last_to(3)
	var min2 := 999
	var has3 := false
	for en in to2[1]:
		min2 = mini(min2, int(en[0]))
	for en in to3[1]:
		has3 = has3 or int(en[0]) == 3
	_assert(to2[0] == 12 and min2 >= 8, "to a peer that released 7, no command older than tick 8 is sent (min %d)" % min2)  # control: passes today
	_assert(has3, "to a peer that released 0, the tick-3 command is still carried at n=12 (packet %s)" % str(to3))


# W0: the carried range never reaches back more than 64 ticks: max(peer_released+1, n-63).
func _test_coverage_window_64() -> void:
	var e := _mk([1, 2])
	e["s"].command({"verb": 0, "arg": 0, "layer": 0, "x": 1.0, "y": 2.0, "units": [4]})  # tick 3
	_spin(e["s"], 4)
	e["s"].command({"verb": 0, "arg": 0, "layer": 0, "x": 1.0, "y": 2.0, "units": [4]})  # tick 7
	e["net"].inject(1, 2, [1, [], [], 0])  # peer 2 stuck at released 0
	_spin(e["s"], 66)  # n = 70: window is ticks 7..70
	var p = e["net"].last_to(2)
	var ticks: Array = []
	for en in p[1]:
		ticks.append(int(en[0]))
	_assert(p[0] == 70 and ticks == [7], "at n=70 a lagging peer gets ticks 7..70 only: tick 7 in, tick 3 out (ticks %s)" % str(ticks))


# W0 / E-19 R-140-04: step() returning null ends the session with state "sim_failed".
func _test_sim_null_ends_session() -> void:
	var e := _mk([1, 2])
	e["sim"].fail_at = 3
	e["net"].inject(1, 2, [8, [], [], 0])
	_spin(e["s"], 10)
	var has_state: bool = e["s"].has_method("state")
	_assert(has_state, "session.state() exists")
	_assert(has_state and e["s"].state() == "sim_failed", "null from step() sets state sim_failed")
	_assert(e["sim"].calls == 3, "after a failed step the session never steps again (calls %d)" % e["sim"].calls)


func _bad_count(s) -> int:
	if not s.has_method("bad_packet_count"):
		return -1
	return int(s.bad_packet_count())


# Positive control for validation: a well-formed packet is accepted, counted as nothing, released.
func _test_receive_control() -> void:
	var e := _mk([1, 2])
	e["net"].inject(1, 2, [1, [[1, _cmd(2, 1)]], [], 0])
	e["s"].poll()
	_assert(_bad_count(e["s"]) == 0, "a well-formed 4-element packet is not counted bad (counter %d)" % _bad_count(e["s"]))
	_assert(e["sim"].steps == 1 and e["sim"].log.size() == 1, "a well-formed 4-element packet releases its tick (steps %d)" % e["sim"].steps)


# W0 / E-19 R-140-04: each hostile packet is dropped and counted; nothing reaches the sim; no script error.
func _test_receive_bad_shapes() -> void:
	var inf := INF
	var bad := {
		"not an array": 7,
		"old 3-element shape": [1, [], []],
		"5 elements": [1, [], [], 0, 0],
		"n float": [1.5, [], [], 0],
		"n zero": [0, [], [], 0],
		"n beyond released+64": [65, [], [], 0],
		"cmds not array": [1, 5, [], 0],
		"sums not array": [1, [], "x", 0],
		"released not int": [1, [], [], "0"],
		"cmd entry not pair": [1, [5], [], 0],
		"cmd not dictionary": [1, [[1, 5]], [], 0],
		"cmd inf float": [1, [[1, {"tick": 1, "peer": 2, "seq": 0, "verb": 0, "arg": 0, "layer": 0, "x": inf, "y": 2.0, "units": [4]}]], [], 0],
		"cmd nan float": [1, [[1, {"tick": 1, "peer": 2, "seq": 0, "verb": 0, "arg": 0, "layer": 0, "x": NAN, "y": 2.0, "units": [4]}]], [], 0],
		"units empty": [1, [[1, _cmd(2, 1, 0, [])]], [], 0],
		"units 71": [1, [[1, _cmd(2, 1, 0, range(71))]], [], 0],
		"peer is not sender": [1, [[1, _cmd(3, 1)]], [], 0],
		"sums tick not int": [1, [], [["x", [1, 2]]], 0],
		"sums section not int": [1, [], [[10, ["a"]]], 0],
	}
	for name in bad:
		var e := _mk([1, 2, 3])
		e["net"].inject(1, 2, bad[name])
		e["s"].poll()
		_assert(_bad_count(e["s"]) == 1, "bad packet '%s' is dropped and counted once (counter %d)" % [name, _bad_count(e["s"])])
		_assert(e["sim"].steps == 0 and e["sim"].log.is_empty(), "bad packet '%s' reaches nothing in the sim" % name)


# W0: per-tick command cap 16 (draft). 16 accepted, 17 dropped.
func _test_receive_cap() -> void:
	var ok_cmds: Array = []
	for i in 16:
		ok_cmds.append([1, _cmd(2, 1, i)])
	var e := _mk([1, 2])
	e["net"].inject(1, 2, [1, ok_cmds, [], 0])
	e["s"].poll()
	_assert(e["sim"].log.size() == 16 and _bad_count(e["s"]) == 0, "16 commands on one tick are accepted (log %d, counter %d)" % [e["sim"].log.size(), _bad_count(e["s"])])
	var over: Array = ok_cmds.duplicate()
	over.append([1, _cmd(2, 1, 16)])
	var e2 := _mk([1, 2])
	e2["net"].inject(1, 2, [1, over, [], 0])
	e2["s"].poll()
	_assert(_bad_count(e2["s"]) == 1 and e2["sim"].log.is_empty(), "17 commands on one tick: packet dropped and counted (counter %d)" % _bad_count(e2["s"]))

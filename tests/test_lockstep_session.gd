extends SceneTree

# Lockstep backend, gd lane (docs/northstar/plans/2026-10-05-lockstep-backend-spec.md;
# rules E-19 R-139-03, R-139-04, R-140-02 to R-140-04, R-242-01).
# Specifies three plain classes loaded by path (no class_name, nothing wired):
#   res://autoload/net/loopback_transport.gd  (extends res://autoload/net/transport.gd)
#       attach(id)                     register an endpoint
#       send(from, to, data)           data is a PackedByteArray
#       poll(id) -> Array              [{"from": int, "data": PackedByteArray}], in send order
#       drop_indices(from, to, idxs)   lose the packets at those 0-based send indices on that link
#       set_delay(from, to, polls)     a packet sent on that link appears after `polls` polls of the receiver
#       set_reorder(from, to, on)      packets that wait together in one poll come out reversed
#   res://autoload/net/lockstep_session.gd
#       setup(local_id, peer_ids, transport, sim, opts)   peer_ids includes local_id;
#           opts keys: input_delay (3), repeat (5), stall_ticks, drop_ticks, checksum_every (10)
#       command(cmd: Dictionary) -> int     stamps cmd.tick = now + input_delay (now = packets sent so far),
#                                           fills peer and seq; returns the stamp
#       poll()                              no real time: receive, send one packet (for tick now+1),
#                                           release at most one tick (submit its commands, then sim.step())
#       is_stalled() -> bool, live_peers() -> Array, desync() -> Dictionary ({} or {"tick","section"})
#   The sim object (replaced here by FakeSim): submit(command: Dictionary), step() -> {"tick": int,
#   "sections": Array (present only on checksum ticks)}. Tick t is produced by the t-th step.
# A packet for tick t repeats the commands stamped t-4..t, so any peer packet for tick n covers
# ticks n-4..n at the barrier.

const TRANSPORT := "res://autoload/net/transport.gd"
const LOOPBACK := "res://autoload/net/loopback_transport.gd"
const SESSION := "res://autoload/net/lockstep_session.gd"

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false
var _Loop = null
var _Session = null


class FakeSim extends RefCounted:
	var steps := 0
	var log: Array = []        # one entry per submit: [steps_before, peer, seq, arg]
	var tamper_tick := -1      # from this tick on, sections 3 and 4 differ
	func submit(c: Dictionary) -> void:
		log.append([steps, int(c.get("peer", -1)), int(c.get("seq", -1)), int(c.get("arg", -1))])
	func step() -> Dictionary:
		steps += 1
		var r := {"tick": steps}
		if steps % 10 == 0:
			var s := [11, 22, 33, 44, 55]
			if tamper_tick >= 0 and steps >= tamper_tick:
				s[3] = 999
				s[4] = 998
			r["sections"] = s
		return r


func _initialize() -> void:
	await _run_tests()
	_assert(_completed, "the checks did not run to the end (a script error aborted them)")
	print("\n=== Lockstep Session Test Results ===")
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


func _pkt(n: int) -> PackedByteArray:
	return PackedByteArray([n])


func _mk(ids: Array, opts := {}) -> Dictionary:
	var net = _Loop.new()
	var out := {"net": net, "s": {}, "sim": {}}
	for id in ids:
		net.attach(id)
	var o := {"input_delay": 3, "repeat": 5, "stall_ticks": 1000, "drop_ticks": 2000, "checksum_every": 10}
	o.merge(opts, true)
	for id in ids:
		var sim := FakeSim.new()
		var s = _Session.new()
		s.setup(id, ids, net, sim, o.duplicate())
		out["s"][id] = s
		out["sim"][id] = sim
	return out


func _spin(env: Dictionary, order: Array, n: int) -> void:
	for i in n:
		for id in order:
			env["s"][id].poll()


func _run_tests() -> void:
	for p in [TRANSPORT, LOOPBACK, SESSION]:
		if not ResourceLoader.exists(p):
			_assert(false, "%s does not exist yet (class under test not built)" % p)
	if not ResourceLoader.exists(LOOPBACK) or not ResourceLoader.exists(SESSION):
		return
	_Loop = load(LOOPBACK)
	_Session = load(SESSION)
	if _Loop == null or _Session == null:
		_assert(false, "loopback_transport.gd or lockstep_session.gd failed to load")
		return
	_test_transport()
	_test_stamp()
	_test_barrier()
	_test_repetition()
	_test_reorder_delay_session()
	_test_stall_and_drop()
	_test_checksums()
	_test_command_order()
	_completed = true


func _test_transport() -> void:
	var net = _Loop.new()
	net.attach(1)
	net.attach(2)
	for i in 5:
		net.send(1, 2, _pkt(i))
	var got: Array = net.poll(2)
	var seq: Array = []
	var froms_ok := true
	for g in got:
		seq.append(int(g["data"][0]))
		froms_ok = froms_ok and int(g["from"]) == 1
	_assert(seq == [0, 1, 2, 3, 4] and froms_ok, "loopback delivers in order with sender id (got %s)" % str(seq))
	_assert(net.poll(2).is_empty() and net.poll(1).is_empty(), "loopback delivers each packet once, only to its addressee")

	net.drop_indices(1, 2, [1, 3])
	for i in 5:
		net.send(1, 2, _pkt(10 + i))
	seq = []
	for g in net.poll(2):
		seq.append(int(g["data"][0]))
	_assert(seq == [10, 12, 14], "drop_indices loses exactly the named sends (got %s)" % str(seq))

	net.set_delay(2, 1, 2)
	net.send(2, 1, _pkt(7))
	var first: Array = net.poll(1)
	_assert(first.is_empty(), "a delayed packet is not delivered on the first poll")
	var found := false
	for i in 3:
		if net.poll(1).size() == 1:
			found = true
			break
	_assert(found, "a packet delayed by 2 polls arrives within 3 further polls")

	net.set_reorder(1, 2, true)
	for i in 3:
		net.send(1, 2, _pkt(20 + i))
	seq = []
	for g in net.poll(2):
		seq.append(int(g["data"][0]))
	_assert(seq == [22, 21, 20], "set_reorder reverses packets that wait together (got %s)" % str(seq))


func _test_stamp() -> void:
	var env := _mk([1, 2])
	var a = env["s"][1]
	_assert(a.command({"verb": 0, "arg": 1}) == 3, "input delay 3: first local command is stamped tick 0+3")
	_spin(env, [1, 2], 4)
	_assert(a.command({"verb": 0, "arg": 2}) == 7, "after 4 packets sent the stamp is 4+3")
	var env2 := _mk([1, 2], {"input_delay": 5})
	_assert(env2["s"][1].command({"verb": 0}) == 5, "the delay is the configured input_delay")
	_spin(env, [1, 2], 6)
	var sim = env["sim"][2]
	var hit := false
	for e in sim.log:
		if e[3] == 1:
			hit = e[0] == 2    # stamped 3 applies in the 3rd step: 2 steps done before it
	_assert(hit, "the remote sim got the command stamped 3 just before step 3 (log %s)" % str(sim.log))


func _test_barrier() -> void:
	var env := _mk([1, 2])
	var a = env["s"][1]
	var b = env["s"][2]
	var sa = env["sim"][1]
	var sb = env["sim"][2]
	for i in 6:
		a.poll()
	_assert(sa.steps == 0, "no tick is released while the other peer has sent nothing (steps %d)" % sa.steps)
	b.poll()
	_assert(sb.steps <= 1, "one poll releases at most one tick")
	var n := 0
	while sa.steps < 1 and n < 5:
		a.poll()
		n += 1
	_assert(sa.steps >= 1, "tick 1 is released once the peer's packet for it has arrived")
	_assert(sa.steps <= 2, "tick 2 is not released before the peer has sent for it (steps %d)" % sa.steps)
	_spin(env, [1, 2], 30)
	_assert(sa.steps > 20 and abs(sa.steps - sb.steps) <= 2, "two live peers keep stepping together (%d, %d)" % [sa.steps, sb.steps])


func _test_repetition() -> void:
	# one lost packet is covered by the next ones
	var env := _mk([1, 2])
	env["net"].drop_indices(1, 2, [2])           # the packet for tick 3
	env["s"][1].command({"verb": 0, "arg": 42})  # stamped 3
	_spin(env, [1, 2], 15)
	var log: Array = env["sim"][2].log
	var got := false
	for e in log:
		if e[3] == 42:
			got = e[0] == 2
	_assert(got, "a dropped packet is covered by repetition: command still applied at its tick (%s)" % str(log))
	_assert(env["sim"][2].steps > 10, "a dropped packet does not stop the barrier")
	# TD-NET-packet-shape: the old 5-tick repetition window is gone; each packet carries the
	# window max(peer_released+1, n-63)..n, so a 5-packet loss self-heals instead of stalling.
	var env2 := _mk([1, 2])
	env2["net"].drop_indices(1, 2, [2, 3, 4, 5, 6])
	env2["s"][1].command({"verb": 0, "arg": 42})
	_spin(env2, [1, 2], 15)
	_assert(env2["sim"][2].steps > 10, "tick 3 is recovered after 5 packets in a row are lost (steps %d)" % env2["sim"][2].steps)
	# four lost in a row: the fifth still carries it
	var env3 := _mk([1, 2])
	env3["net"].drop_indices(1, 2, [2, 3, 4, 5])
	env3["s"][1].command({"verb": 0, "arg": 42})
	_spin(env3, [1, 2], 15)
	_assert(env3["sim"][2].steps > 10, "each packet repeats the commands of the last 5 ticks (4 lost, a later packet covers)")


func _test_reorder_delay_session() -> void:
	var env := _mk([1, 2])
	env["net"].set_reorder(1, 2, true)
	env["net"].set_reorder(2, 1, true)
	env["net"].set_delay(1, 2, 3)
	env["s"][1].command({"verb": 0, "arg": 7})
	env["s"][2].command({"verb": 0, "arg": 8})
	_spin(env, [1, 2], 40)
	var l1: Array = env["sim"][1].log
	var l2: Array = env["sim"][2].log
	_assert(env["sim"][1].steps > 15 and env["sim"][2].steps > 15, "delayed and reordered links still run")
	_assert(l1 == l2 and l1.size() == 2, "delay and reordering do not change what each sim is handed (%s vs %s)" % [str(l1), str(l2)])
	_assert(env["sim"][2].steps <= env["sim"][1].steps + 4, "a delayed link holds the receiver back, not the sender")


func _test_stall_and_drop() -> void:
	var env := _mk([1, 2, 3], {"stall_ticks": 5, "drop_ticks": 20})
	var a = env["s"][1]
	var b = env["s"][2]
	for i in 3:
		a.poll()
		b.poll()
	_assert(not a.is_stalled(), "no stall while the wait is short")
	_spin(env, [1, 2], 3)
	_spin(env, [1, 2], 5)
	_assert(a.is_stalled(), "a peer silent for stall_ticks puts the session in a stalled state")
	_assert(3 in a.live_peers(), "a stalled peer is not dropped yet")
	var frozen := int(env["sim"][1].steps)
	_spin(env, [1, 2], 3)
	_assert(int(env["sim"][1].steps) == frozen, "a stalled session does not step")
	_spin(env, [1, 2], 25)
	_assert(not (3 in a.live_peers()) and not (3 in b.live_peers()), "a peer silent for drop_ticks is removed (live: %s)" % str(a.live_peers()))
	_assert(1 in a.live_peers() and 2 in a.live_peers(), "the other peers stay live")
	_assert(not a.is_stalled(), "after the drop the stall clears")
	var before := int(env["sim"][1].steps)
	_spin(env, [1, 2], 20)
	_assert(int(env["sim"][1].steps) >= before + 15 and int(env["sim"][2].steps) >= before + 15, "the others continue after a drop")


func _test_checksums() -> void:
	var env := _mk([1, 2])
	_spin(env, [1, 2], 60)
	_assert(env["sim"][1].steps >= 30, "setup: sessions ran past tick 30")
	_assert(env["s"][1].desync().is_empty() and env["s"][2].desync().is_empty(), "equal checksums on every tenth tick report no desync")
	var env2 := _mk([1, 2])
	env2["sim"][2].tamper_tick = 20
	_spin(env2, [1, 2], 60)
	var d1: Dictionary = env2["s"][1].desync()
	var d2: Dictionary = env2["s"][2].desync()
	_assert(int(d1.get("tick", -1)) == 20 and int(d1.get("section", -1)) == 3, "a mismatch names the tick and the first differing section index (peer 1: %s)" % str(d1))
	_assert(int(d2.get("tick", -1)) == 20 and int(d2.get("section", -1)) == 3, "both peers see the mismatch (peer 2: %s)" % str(d2))


func _test_command_order() -> void:
	var env := _mk([2, 1])    # attached in reverse of peer order
	var s1 = env["s"][1]
	var s2 = env["s"][2]
	s2.command({"verb": 0, "arg": 21})
	s2.command({"verb": 0, "arg": 22})
	s1.command({"verb": 0, "arg": 11})
	s1.command({"verb": 0, "arg": 12})
	_spin(env, [2, 1], 12)
	for id in [1, 2]:
		var log: Array = env["sim"][id].log
		var peers: Array = []
		var args: Array = []
		for e in log:
			peers.append(e[1])
			args.append(e[3])
		_assert(peers == [1, 1, 2, 2], "sim %d is handed commands in peer order (peers %s)" % [id, str(peers)])
		_assert(args == [11, 12, 21, 22], "sim %d is handed each peer's commands in sequence order (args %s)" % [id, str(args)])

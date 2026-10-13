extends SceneTree

# VG-F-SKEL-A, test half 1: autoload/net/udp_transport.gd (UdpTransport, extends transport.gd).
# Spec: docs/northstar/plans/2026-10-07-visible-game-spec.md rev 12 + 12b,
#   "Lane F part 1 ... F-SKEL-A" (line 262): "implements transport.gd's attach(id), send(from, to, PackedByteArray),
#   poll(id) over PacketPeerUDP on 127.0.0.1 with one port per peer id (UDP_BASE_PORT 47100 + id, DRAFT-udp-base-port),
#   same packet bytes as the Steam transport hands the session (no framing beyond the datagram)"; "two transports in
#   one process exchange ten packets in order; a packet to an unattached id is dropped; control: loopback_transport.gd
#   does the same, green today".
#   Rev 12b F-SKEL (2) (line 282): "UdpTransport.set_peers() exists as a no-op."
#   Rev 12b F-SKEL (4): plain script under autoload/net/, loaded with load(path).new(), no class_name.
#   Rev 12c F-SKEL (line 286): unit tests read OM_TEST_PORT_BASE (default 47000, UDP base +100).
# Rules proved: R-140-02 (input delay 3 ticks) and R-140-03 (drop after 30 s) ride on this transport; the transport
# itself states no rule, it only carries the session's packets (Westley, Q-F-1, 2026-10-11: "allowed, so long as the
# test does everything it can to emulate the reality of two players joining and not taking shortcuts beyond what is
# strictly necessary given the limitation": real UDP datagrams between two transport objects).
#
# Ports: the transport binds UDP base + 100 + id (base = env OM_TEST_PORT_BASE, default 47000). The test never binds a
# literal port. The 2 s deadlines below are harness waits for loopback delivery, not tolerances (liberty 2026-10-11).

const LOOPBACK := "res://autoload/net/loopback_transport.gd"
const UDP := "res://autoload/net/udp_transport.gd"
const DEADLINE_MS := 2000   # liberty 2026-10-11: harness wait, bounded

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false
var _Udp = null


func _initialize() -> void:
	_run_tests()
	_assert(_completed, "the checks did not run to the end (a script error aborted them)")
	print("\n=== UDP Transport Test Results ===")
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


func _base() -> int:
	var s := OS.get_environment("OM_TEST_PORT_BASE")
	return int(s) if s != "" else 47000


func _pkt(i: int) -> PackedByteArray:
	return PackedByteArray([i, (i * 7) % 256, 255 - i, 42])


# Poll `id` on `t` until `want` entries are collected or the 2 s harness deadline passes.
func _collect(t, id: int, want: int) -> Array:
	var got: Array = []
	var end := Time.get_ticks_msec() + DEADLINE_MS
	while got.size() < want and Time.get_ticks_msec() < end:
		got.append_array(t.poll(id))
		if got.size() < want:
			OS.delay_msec(2)
	return got


func _ten_in_order(sender, receiver, from_id: int, to_id: int, label: String) -> void:
	var sent: Array = []
	for i in 10:
		var p := _pkt(i)
		sent.append(p)
		sender.send(from_id, to_id, p)
	var got := _collect(receiver, to_id, 10)
	_assert(got.size() == 10, "%s: ten packets arrive, got %d" % [label, got.size()])
	var ok := got.size() == 10
	for i in mini(got.size(), 10):
		if int(got[i]["from"]) != from_id or got[i]["data"] != sent[i]:
			ok = false
	_assert(ok, "%s: the ten packets arrive in send order with from == %d and identical bytes" % [label, from_id])


func _run_tests() -> void:
	print("premise: OM_TEST_PORT_BASE base = %d, transport ports = base + 100 + id (%d + id)" % [_base(), _base() + 100])

	# CONTROL (green today): the same ten-packet exchange on loopback_transport.gd.
	_assert(ResourceLoader.exists(LOOPBACK), "control: %s exists" % LOOPBACK)
	if ResourceLoader.exists(LOOPBACK):
		var lo = load(LOOPBACK).new()
		lo.attach(1)
		lo.attach(2)
		for i in 10:
			lo.send(1, 2, _pkt(i))
		var got: Array = lo.poll(2)
		_assert(got.size() == 10, "control: loopback poll(2) returns ten entries, got %d" % got.size())
		var ok := got.size() == 10
		for i in mini(got.size(), 10):
			if int(got[i]["from"]) != 1 or got[i]["data"] != _pkt(i):
				ok = false
		_assert(ok, "control: loopback entries are {from: 1, data} in send order")

	# The feature: UdpTransport.
	if not ResourceLoader.exists(UDP):
		_assert(false, "%s does not exist yet (feature missing: UdpTransport not built); VG-F-SKEL-A" % UDP)
		_completed = true
		return
	_Udp = load(UDP)

	# Spec line 262: "two transports in one process exchange ten packets in order".
	var a = _Udp.new()
	var b = _Udp.new()
	a.attach(0)
	b.attach(1)
	_ten_in_order(a, b, 0, 1, "udp 0 to 1")

	# Spec line 262: "a packet to an unattached id is dropped" (sender's poll stays empty, no error), and the
	# transport still works afterwards.
	a.send(0, 90, _pkt(5))
	var back := _collect(a, 0, 1)   # waits the full harness deadline for something that must not come
	_assert(back.is_empty(), "a packet sent to an unattached id is dropped: the sender's poll(0) stays empty, got %d" % back.size())
	a.send(0, 1, _pkt(6))
	var after := _collect(b, 1, 1)
	_assert(after.size() == 1 and after[0]["data"] == _pkt(6), "after a dropped send the link 0 to 1 still delivers")

	# Spec line 262: poll(id) on a transport that never attached that id returns [].
	var c = _Udp.new()
	_assert(c.poll(3).is_empty(), "poll(3) on a transport that never attached id 3 returns []")
	_assert(c.poll(0).is_empty(), "poll(0) on a fresh transport returns []")

	# Spec line 262: "same packet bytes ... (no framing beyond the datagram)".
	var d = _Udp.new()
	var e = _Udp.new()
	d.attach(4)
	e.attach(5)
	var three := PackedByteArray([1, 2, 3])
	d.send(4, 5, three)
	var got3 := _collect(e, 5, 1)
	_assert(got3.size() == 1 and got3[0]["data"] == three and got3[0]["data"].size() == 3,
		"a 3-byte payload arrives as the same 3 bytes (no framing added)")
	# The port mapping, read from outside: a plain datagram to 127.0.0.1:(base + 100 + 5) shows up on id 5 with the
	# same bytes (one port per peer id, base + 100 + id).
	var raw := PacketPeerUDP.new()
	raw.set_dest_address("127.0.0.1", _base() + 100 + 5)
	raw.put_packet(three)
	var gotr := _collect(e, 5, 1)
	_assert(gotr.size() == 1 and gotr[0]["data"] == three,
		"a raw datagram to 127.0.0.1:%d reaches poll(5) with the same bytes (UDP_BASE_PORT + id)" % (_base() + 100 + 5))
	raw.close()

	# Rev 12b F-SKEL (2): set_peers() exists and is a no-op.
	var f = _Udp.new()
	var g = _Udp.new()
	f.attach(6)
	g.attach(7)
	_assert(f.has_method("set_peers"), "UdpTransport has set_peers(peers) (Rev 12b F-SKEL (2))")
	if f.has_method("set_peers"):
		f.set_peers([{"peer_id": 0, "steam_id": 1}])
		g.set_peers([{"peer_id": 0, "steam_id": 1}])
		_assert(f.poll(6).is_empty(), "set_peers changes nothing a later poll shows (empty)")
		var pb := PackedByteArray([9, 9])
		f.send(6, 7, pb)
		var gp := _collect(g, 7, 1)
		_assert(gp.size() == 1 and int(gp[0]["from"]) == 6 and gp[0]["data"] == pb,
			"after set_peers a send 6 to 7 still arrives with from == 6 and the same bytes")
	_completed = true

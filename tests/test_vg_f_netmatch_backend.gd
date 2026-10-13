extends SceneTree

# VG-F-SKEL-B, rulings 2026-10-12 (b), ledger row FINDING-netmatch-backend-lifetime.
# Rule proved: R-140-02 / the ready-go barrier of docs/northstar/plans/2026-10-06-steam-multiplayer-wiring-spec.md W3
# ("the host repeats [go] until that guest's first packet arrives", autoload/net/net_match.gd:_resend_go).
# NetMatch is an autoload that outlives the lobby scene. start() received only the Callable `lobby_chat`; a Callable
# on a RefCounted does not keep the object alive, so after the lobby scene freed, _resend_go failed with
# "Attempt to call function 'null::send_chat (Callable)' on a null instance" (net_match.gd:159).
#
# INTERFACE FIXED BY THIS TEST (the one line the builder wires, lobby.gd _launch):
#     net_match.start(record, transport, sim, _backend.send_chat, _backend)
# i.e. NetMatch.start gains a 5th optional parameter `backend` (the object whose send_chat is the Callable); NetMatch
# keeps it in a field `_backend` from start() until the match ends, and _resend_go calls through that field. The
# test uses only that line. While start still has four parameters the helper falls back to the four-argument call, so
# the flow still runs and fails for the real reason (the freed backend); the arity case is the second red line.

const NET_MATCH := "res://autoload/net/net_match.gd"
const LOOPBACK := "res://autoload/net/loopback_transport.gd"

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false
var _cur := ""


class FakeSim extends RefCounted:
	var steps := 0
	func submit(_c: Dictionary) -> void:
		pass
	func step():
		steps += 1
		return {"tick": steps}


# The lobby's backend: counts send_chat calls in an Array the test owns (the backend itself is freed with its creator).
class CountingBackend extends RefCounted:
	var sent: Array
	func _init(sink: Array) -> void:
		sent = sink
	func send_chat(msg: Dictionary) -> void:
		sent.append(msg)


# Stands in for the lobby scene: creates the backend, holds the only reference, hands it to NetMatch.start.
class FakeLobby extends Node:
	var backend
	func launch(nm: Node, record: Dictionary, transport, sim, sink: Array, five_args: bool) -> void:
		backend = CountingBackend.new(sink)
		if five_args:
			nm.start(record, transport, sim, backend.send_chat, backend)
		else:
			nm.start(record, transport, sim, backend.send_chat)


func _initialize() -> void:
	_run_tests()
	_assert(_completed, "the checks did not run to the end (a script error aborted them)")
	print("\n=== VG-F NetMatch backend lifetime Test Results ===")
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


func _record() -> Dictionary:
	return {"local_peer": 0, "host_peer": 0, "peers": [{"peer_id": 0, "steam_id": 1000, "faction": 0}, {"peer_id": 1, "steam_id": 1001, "faction": 0}],
		"input_delay": 3, "repeat": 5, "stall_ticks": 20, "drop_ticks": 1200}


func _start_arity(nm: Node) -> int:
	for m in nm.get_script().get_script_method_list():
		if m["name"] == "start":
			return (m["args"] as Array).size()
	return -1


# Host with a silent guest: start, the guest's "ready" releases the barrier (one "go"), then one poll leaves the guest
# silent so _resend_go repeats the go. Returns the messages the backend received.
func _run(free_creator: bool) -> Array:
	var sink: Array = []
	var nm: Node = load(NET_MATCH).new()
	var net = load(LOOPBACK).new()
	net.attach(0)  # peer 1 never attaches, so it never sends a packet
	var lobby := FakeLobby.new()
	get_root().add_child(lobby)
	lobby.launch(nm, _record(), net, FakeSim.new(), sink, _start_arity(nm) >= 5)
	nm.on_lobby_chat(1, {"t": "ready"})
	if free_creator:
		lobby.free()  # the lobby scene is freed; the backend's only other holder would be NetMatch
	nm._process(0.05)
	if not free_creator:
		lobby.free()
	return sink


func _run_tests() -> void:
	_cur = "netmatch_backend"
	var nm: Node = load(NET_MATCH).new()
	_assert(nm.has_method("start") and nm.has_method("_process"), "CONTROL: NetMatch instantiates with start and _process")
	_assert(_start_arity(nm) >= 4, "CONTROL: NetMatch.start takes the four-argument call the lobby makes today")
	_assert(_start_arity(nm) >= 5, "NetMatch.start takes a 5th optional parameter `backend` (the object whose send_chat is the Callable), kept in a field so the autoload holds it after the lobby scene frees; it has %d parameters" % _start_arity(nm))
	nm.free()
	# Positive control: with the lobby (and so the backend) still alive, the go and then the resent go reach the backend.
	var kept := _run(false)
	var gos_kept := kept.filter(func(m): return m is Dictionary and m.get("t", "") == "go").size()
	_assert(gos_kept >= 2, "CONTROL: with the lobby alive the host sends go at the barrier and repeats it for the silent guest (>= 2 go messages), got %s" % str(kept))
	# The case: the lobby scene frees before the resend.
	var freed := _run(true)
	var gos_freed := freed.filter(func(m): return m is Dictionary and m.get("t", "") == "go").size()
	_assert(gos_freed >= 2, "after the creating lobby is freed the repeated go still reaches the backend (>= 2 go messages; net_match.gd:159 calls a freed Callable target), got %s" % str(freed))
	_completed = true

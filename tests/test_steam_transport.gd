extends SceneTree

# Steam wiring, piece W1 (docs/northstar/plans/2026-10-06-steam-multiplayer-wiring-spec.md, rev 5:
# "Interfaces fixed here" 1, "What the Fable audit changed", Pieces table row W1).
# Rules: E-19 R-140-02..R-140-04 (commands exchanged per tick, stall, drop; the session's transport).
# Specifies res://autoload/net/steam_transport.gd (extends res://autoload/net/transport.gd):
#   set_steam(obj)             inject the Steam object (tests pass FakeSteam, same method names as GodotSteam)
#   set_peers(peers: Array)    the MatchRecord peers [{peer_id, steam_id, faction}]; the only peer table
#   attach(id) / send(from, to, bytes) / poll(id) -> [{from: peer_id, data: PackedByteArray}]
#   dropped_unknown: int       packets from senders not in the table
#   dropped_malformed: int     packets whose bytes_to_var value is not an Array of size 3 (int, Array, Array)
# Steam calls it must make (names are the GodotSteam ones):
#   send:  Steam.sendMessageToUser(identity, bytes, Steam.NETWORKING_SEND_UNRELIABLE_NO_DELAY, 0)
#   poll:  Steam.run_callbacks() then Steam.receiveMessagesOnChannel(0, 32)  (message: {identity, payload})
#   signal network_messages_session_request(remote_steam_id) -> acceptSessionWithUser(id) only for table members
# Open for the Architect: the exact shape of `identity` (int steam id here; GodotSteam may give a string
# reference). The fake sends and receives the int; send's identity is only checked to contain the id.

const TRANSPORT := "res://autoload/net/transport.gd"
const STEAM_T := "res://autoload/net/steam_transport.gd"
const FLAG_UNRELIABLE_NO_DELAY := 13   # GodotSteam NETWORKING_SEND_UNRELIABLE_NO_DELAY (k_nSteamNetworkingSend_UnreliableNoDelay)

# Table deliberately NOT in id order and with steam ids unrelated to peer ids,
# so lobby order or id arithmetic cannot satisfy the tests.
const PEERS := [
	{"peer_id": 2, "steam_id": 76561198000000222, "faction": 1},
	{"peer_id": 1, "steam_id": 76561198000000111, "faction": 1},
	{"peer_id": 3, "steam_id": 76561198000000333, "faction": 1},
]
const STRANGER := 76561198999999999

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false


class FakeSteam extends RefCounted:
	signal network_messages_session_request(remote_steam_id)
	const NETWORKING_SEND_UNRELIABLE_NO_DELAY := 13
	var sent: Array = []        # [identity, bytes, flags, channel]
	var accepted: Array = []
	var inbox: Array = []       # messages returned by the next receive
	var calls: Array = []       # call order log
	var recv_args: Array = []
	func sendMessageToUser(identity, data: PackedByteArray, flags: int, channel: int) -> int:
		calls.append("send")
		sent.append([identity, data, flags, channel])
		return 1
	func run_callbacks() -> void:
		calls.append("run_callbacks")
	func receiveMessagesOnChannel(channel: int, max_messages: int) -> Array:
		calls.append("receive")
		recv_args.append([channel, max_messages])
		var out := inbox
		inbox = []
		return out
	func acceptSessionWithUser(identity) -> bool:
		accepted.append(identity)
		return true
	func msg(steam_id: int, data: PackedByteArray) -> Dictionary:
		return {"identity": steam_id, "payload": data, "size": data.size(), "channel": 0}


func _initialize() -> void:
	_run_tests()
	_assert(_completed, "the checks did not run to the end (a script error aborted them)")
	print("\n=== Steam Transport Test Results ===")
	print("PASS: %d  FAIL: %d" % [_pass_count, _fail_count])
	if _fail_count > 0:
		print("Failures:")
		for m in _fail_msgs:
			print("  - " + m)
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
	return var_to_bytes([n, [], []])


func _mk(local_id: int = 1):
	# Returns {"t": transport or null, "s": FakeSteam}.
	var s := FakeSteam.new()
	if not ResourceLoader.exists(STEAM_T):
		return {"t": null, "s": s}
	var T = load(STEAM_T)
	var t = T.new()
	t.set_steam(s)
	t.set_peers(PEERS.duplicate(true))
	t.attach(local_id)
	return {"t": t, "s": s}


func _run_tests() -> void:
	# positive control (passes today): the base transport contract exists as specified.
	_assert(ResourceLoader.exists(TRANSPORT), "W1 control: autoload/net/transport.gd exists")
	_assert(not ResourceLoader.exists(STEAM_T) or load(STEAM_T).new() is RefCounted, "W1 control: steam_transport is a plain object")
	_assert(ResourceLoader.exists(STEAM_T), "W1 exists: %s does not exist yet (class under test not built)" % STEAM_T)
	if not ResourceLoader.exists(STEAM_T):
		for n in ["is_transport", "send_uses_table_and_flags", "send_unknown_peer", "poll_order_and_drain", "poll_maps_sender_to_peer_id", "unknown_sender_dropped", "malformed_dropped", "session_request_member", "session_request_stranger"]:
			_assert(false, "W1 %s: red, %s missing" % [n, STEAM_T])
		_completed = true
		return
	_test_is_transport()
	_test_send_uses_table_and_flags()
	_test_send_unknown_peer()
	_test_poll_order_and_drain()
	_test_poll_maps_sender_to_peer_id()
	_test_unknown_sender_dropped()
	_test_malformed_dropped()
	_test_session_request_member()
	_test_session_request_stranger()
	_completed = true


func _test_is_transport() -> void:
	var t = load(STEAM_T).new()
	var base = load(TRANSPORT)
	_assert(t.get_script().get_base_script() == base, "W1 is_transport: SteamTransport extends transport.gd")
	_assert(t.has_method("attach") and t.has_method("send") and t.has_method("poll"), "W1 is_transport: attach, send, poll present")


func _test_send_uses_table_and_flags() -> void:
	# R-140-02: commands go out per tick; Interfaces fixed 1: unreliable, channel 0, peer table from the record.
	var e = _mk(1)
	var t = e["t"]
	var s: FakeSteam = e["s"]
	var data := _pkt(7)
	t.send(1, 3, data)
	t.send(1, 2, data)
	_assert(s.sent.size() == 2, "W1 send: two sends reach Steam (got %d)" % s.sent.size())
	if s.sent.size() < 2:
		return
	_assert(str(s.sent[0][0]).contains("76561198000000333"), "W1 send: peer 3 maps to its table steam id, not lobby order (identity %s)" % str(s.sent[0][0]))
	_assert(str(s.sent[1][0]).contains("76561198000000222"), "W1 send: peer 2 maps to its table steam id (identity %s)" % str(s.sent[1][0]))
	_assert(s.sent[0][1] == data, "W1 send: the bytes go out unchanged")
	_assert(int(s.sent[0][2]) == FLAG_UNRELIABLE_NO_DELAY, "W1 send: flag is UNRELIABLE_NO_DELAY (got %s)" % str(s.sent[0][2]))
	_assert(int(s.sent[0][3]) == 0, "W1 send: channel 0 (got %s)" % str(s.sent[0][3]))


func _test_send_unknown_peer() -> void:
	# Peer table is the only source: a peer id not in the record sends nothing.
	var e = _mk(1)
	e["t"].send(1, 9, _pkt(1))
	_assert(e["s"].sent.is_empty(), "W1 send_unknown: a send to a peer id outside the table reaches no one")


func _test_poll_order_and_drain() -> void:
	# Interfaces fixed 1: poll runs Steam.run_callbacks() then drains receiveMessagesOnChannel(0, 32).
	var e = _mk(1)
	var s: FakeSteam = e["s"]
	s.inbox = [s.msg(76561198000000222, _pkt(5))]
	e["t"].poll(1)
	_assert(s.calls.find("run_callbacks") != -1 and s.calls.find("receive") != -1, "W1 poll_order: poll calls run_callbacks and receiveMessagesOnChannel (calls %s)" % str(s.calls))
	_assert(s.calls.find("run_callbacks") < s.calls.find("receive"), "W1 poll_order: run_callbacks comes before receive (calls %s)" % str(s.calls))
	_assert(s.recv_args == [[0, 32]], "W1 poll_order: receives on channel 0, max 32 (got %s)" % str(s.recv_args))
	# A second poll sees only what Steam hands over then (nothing buffered twice).
	_assert(e["t"].poll(1).is_empty(), "W1 poll_order: a poll with an empty Steam inbox returns []")


func _test_poll_maps_sender_to_peer_id() -> void:
	# poll returns the table peer id, in arrival order, bytes intact.
	var e = _mk(1)
	var s: FakeSteam = e["s"]
	var a := _pkt(10)
	var b := _pkt(11)
	var c := _pkt(12)
	s.inbox = [s.msg(76561198000000333, a), s.msg(76561198000000222, b), s.msg(76561198000000333, c)]
	var got: Array = e["t"].poll(1)
	_assert(got.size() == 3, "W1 poll_map: three packets returned (got %d)" % got.size())
	if got.size() != 3:
		return
	_assert([got[0]["from"], got[1]["from"], got[2]["from"]] == [3, 2, 3], "W1 poll_map: senders are peer ids from the table, arrival order (got %s)" % str([got[0]["from"], got[1]["from"], got[2]["from"]]))
	_assert(got[0]["data"] == a and got[1]["data"] == b and got[2]["data"] == c, "W1 poll_map: payload bytes intact")


func _test_unknown_sender_dropped() -> void:
	# Unknown senders are dropped and counted.
	var e = _mk(1)
	var s: FakeSteam = e["s"]
	s.inbox = [s.msg(STRANGER, _pkt(1)), s.msg(76561198000000222, _pkt(2)), s.msg(STRANGER, _pkt(3))]
	var got: Array = e["t"].poll(1)
	_assert(got.size() == 1 and got[0]["from"] == 2, "W1 unknown_sender: only the table peer's packet survives (got %s)" % str(got))
	_assert(int(e["t"].get("dropped_unknown")) == 2, "W1 unknown_sender: dropped_unknown counts 2 (got %s)" % str(e["t"].get("dropped_unknown")))


func _test_malformed_dropped() -> void:
	# Spec 'Found by the pre-flight': a packet whose decoded value is not an Array [int, Array, Array] is dropped and counted.
	var e = _mk(1)
	var s: FakeSteam = e["s"]
	var good := _pkt(4)
	s.inbox = [
		s.msg(76561198000000222, var_to_bytes("hello")),
		s.msg(76561198000000222, var_to_bytes([1, 2])),
		s.msg(76561198000000222, var_to_bytes(["x", [], []])),
		s.msg(76561198000000222, PackedByteArray([1, 2, 3])),
		s.msg(76561198000000222, good),
	]
	var got: Array = e["t"].poll(1)
	_assert(got.size() == 1 and got[0]["data"] == good, "W1 malformed: only the well-formed packet survives (got %d)" % got.size())
	_assert(int(e["t"].get("dropped_malformed")) == 4, "W1 malformed: dropped_malformed counts 4 (got %s)" % str(e["t"].get("dropped_malformed")))


func _test_session_request_member() -> void:
	# Fable audit: Networking Messages drops packets until the receiver accepts the session request.
	var e = _mk(1)
	var s: FakeSteam = e["s"]
	s.network_messages_session_request.emit(76561198000000222)
	_assert(s.accepted.size() == 1 and str(s.accepted[0]).contains("76561198000000222"), "W1 session_member: a request from a table peer is accepted (accepted %s)" % str(s.accepted))


func _test_session_request_stranger() -> void:
	var e = _mk(1)
	var s: FakeSteam = e["s"]
	s.network_messages_session_request.emit(STRANGER)
	_assert(s.accepted.is_empty(), "W1 session_stranger: a request from a non-member is refused (accepted %s)" % str(s.accepted))
	# positive pairing: the refusal must not be 'never accepts anything'.
	s.network_messages_session_request.emit(76561198000000111)
	_assert(s.accepted.size() == 1, "W1 session_stranger: a member requesting afterwards is still accepted (accepted %s)" % str(s.accepted))

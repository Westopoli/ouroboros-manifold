extends SceneTree

# VG-F-SKEL-A, test half 2: autoload/net/local_lobby_backend.gd (LocalLobbyBackend, extends RefCounted).
# Spec: docs/northstar/plans/2026-10-07-visible-game-spec.md rev 12 + 12b, "Lane F part 1 ... F-SKEL-A" (line 262):
#   "local_lobby_backend.gd implements the setup() backend seam (create_lobby, join, set_lobby_data, get_lobby_data,
#   members, send_chat, leave) over the same UDP: the host listens on LOBBY_PORT 47000 (DRAFT-lobby-port), the lobby id
#   is the string of that port, a guest join(id) sends {"t":"hello","id":<local id>} and gets the member list and lobby
#   data back, send_chat fans out to every member, members() is the host's list mirrored to guests, leave sends
#   {"t":"bye"}"; tests: "host and guest in one process: join returns two members, lobby data round-trips, chat
#   reaches both, leave removes".
#   Rev 12b F-SKEL (1) poll(); (3) RefCounted; (4) plain script, load(path).new(), no class_name.
#   Rev 12c F-SKEL (line 286): "the local backend declares Steam's four signals with the same arguments, emitted from
#   poll(), plus local_id() and a set_local_id(n) test seam; lobby ids are ints (the port); chat travels as var_to_str
#   text in the JSON frame"; unit tests read OM_TEST_PORT_BASE (default 47000).
# Bible rules reached: R-141-01 (friends-only, a lobby of up to 4; here create_lobby(1, 4)), R-140-04 (a leaving member
# is reported through lobby_chat_update so the lobby can drop the peer).
# Westley, Q-F-1, 2026-10-11, verbatim: "allowed, so long as the test does everything it can to emulate the reality of
# two players joining and not taking shortcuts beyond what is strictly necessary given the limitation": the host and the
# guest here talk over real UDP sockets (guest on an ephemeral port); the one shortcut is that both live in one process
# (told apart with set_local_id), because a unit test cannot start a second game; the two-process proof is the play.
#
# Ports: the lobby port is the env OM_TEST_PORT_BASE (default 47000); the test never binds a literal port.
# The 2 s deadlines are harness waits for loopback delivery, not tolerances (liberty 2026-10-11).

const LOCAL := "res://autoload/net/local_lobby_backend.gd"
const DEADLINE_MS := 2000   # liberty 2026-10-11: harness wait, bounded
const LEFT_STATES := [2, 4, 8, 16]   # lobby.gd CHAT_LEFT_STATES

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false


func _initialize() -> void:
	_run_tests()
	_assert(_completed, "the checks did not run to the end (a script error aborted them)")
	print("\n=== Local Lobby Backend Test Results ===")
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


# Pump every backend with poll() until cond.call() or the 2 s harness deadline; returns cond's last value.
func _pump(backends: Array, cond: Callable) -> bool:
	var end := Time.get_ticks_msec() + DEADLINE_MS
	while Time.get_ticks_msec() < end:
		for b in backends:
			b.poll()
		if cond.call():
			return true
		OS.delay_msec(2)
	return cond.call()


# Pump for a fixed short harness wait (for things that must NOT happen or have no completion signal).
func _pump_for(backends: Array, ms: int) -> void:
	var end := Time.get_ticks_msec() + ms
	while Time.get_ticks_msec() < end:
		for b in backends:
			b.poll()
		OS.delay_msec(2)


func _run_tests() -> void:
	var base := _base()
	print("premise: OM_TEST_PORT_BASE base = %d, lobby port = %d" % [base, base])

	# CONTROL (green today): a JSON frame between two plain PacketPeerUDP sockets on 127.0.0.1 in one process.
	var rx := PacketPeerUDP.new()
	var berr := rx.bind(0, "127.0.0.1")
	_assert(berr == OK, "control: a PacketPeerUDP binds an ephemeral port on 127.0.0.1 (err %d)" % berr)
	var tx := PacketPeerUDP.new()
	tx.set_dest_address("127.0.0.1", rx.get_local_port())
	var sent := {"t": "hello", "id": 5}
	tx.put_packet(JSON.stringify(sent).to_utf8_buffer())
	var end := Time.get_ticks_msec() + DEADLINE_MS
	while rx.get_available_packet_count() == 0 and Time.get_ticks_msec() < end:
		OS.delay_msec(2)
	_assert(rx.get_available_packet_count() > 0, "control: the JSON frame arrives over UDP within the harness wait")
	if rx.get_available_packet_count() > 0:
		var parsed = JSON.parse_string(rx.get_packet().get_string_from_utf8())
		_assert(parsed is Dictionary and int(parsed.get("id", -1)) == 5 and parsed.get("t", "") == "hello",
			"control: the frame parses back to {t: hello, id: 5}")
	print("premise: control bound ephemeral port %d for the harness socket" % rx.get_local_port())
	rx.close()
	tx.close()

	if not ResourceLoader.exists(LOCAL):
		_assert(false, "%s does not exist yet (feature missing: LocalLobbyBackend not built); VG-F-SKEL-A" % LOCAL)
		_completed = true
		return
	var Backend = load(LOCAL)

	var host = Backend.new()
	var guest = Backend.new()
	host.set_local_id(1)
	guest.set_local_id(2)
	_assert(host.local_id() == 1 and guest.local_id() == 2, "set_local_id(n) overrides local_id() (INTERFACE seam)")

	var h_created: Array = []
	var h_chat_update: Array = []
	var h_msgs: Array = []
	var g_joined: Array = []
	var g_chat_update: Array = []
	var g_msgs: Array = []
	host.lobby_created.connect(func(result, lobby_id): h_created.append([result, lobby_id]))
	host.lobby_chat_update.connect(func(lobby, changed, making, state): h_chat_update.append([lobby, changed, making, state]))
	host.lobby_message.connect(func(lobby, user, message, type): h_msgs.append([lobby, user, message, type]))
	guest.lobby_joined.connect(func(lobby_id, perm, locked, response): g_joined.append([lobby_id, perm, locked, response]))
	guest.lobby_chat_update.connect(func(lobby, changed, making, state): g_chat_update.append([lobby, changed, making, state]))
	guest.lobby_message.connect(func(lobby, user, message, type): g_msgs.append([lobby, user, message, type]))

	# Spec line 262 + INTERFACE: create_lobby(1, 4) emits lobby_created(1, lobby port); lobby id is the port, an int.
	host.create_lobby(1, 4)
	_assert(h_created.size() == 1 and int(h_created[0][0]) == 1 and int(h_created[0][1]) == base,
		"host.create_lobby(1, 4) emits lobby_created(1, %d), got %s" % [base, str(h_created)])
	_assert(host.lobby_id == base, "host.lobby_id == the lobby port %d, got %s" % [base, str(host.lobby_id)])
	_assert(host.members() == [1], "a fresh lobby lists only the host: [1], got %s" % str(host.members()))

	# Spec line 262: "a guest join(id) sends hello and gets the member list and lobby data back".
	guest.join(base)
	var both_in := _pump([host, guest], func(): return host.members().size() == 2 and guest.members().size() == 2)
	_assert(both_in, "after join and pumping, host and guest both report two members (host %s, guest %s)" % [str(host.members()), str(guest.members())])
	_assert(host.members() == [1, 2] and guest.members() == [1, 2], "members() is [1, 2], host first, on both")
	_assert(guest.lobby_id == base, "guest.lobby_id == the lobby port %d after joining, got %s" % [base, str(guest.lobby_id)])
	_assert(g_joined.size() >= 1 and int(g_joined[0][3]) == 1, "the guest emitted lobby_joined with response 1, got %s" % str(g_joined))
	if g_joined.size() >= 1:
		_assert(int(g_joined[0][0]) == base, "lobby_joined carries the lobby id %d, got %s" % [base, str(g_joined[0][0])])
	var h_enter := h_chat_update.filter(func(e): return int(e[3]) == 1)
	var g_enter := g_chat_update.filter(func(e): return int(e[3]) == 1)
	_assert(h_enter.size() >= 1, "the host emitted lobby_chat_update with chat_state 1 (member entered), got %s" % str(h_chat_update))
	_assert(g_enter.size() >= 1, "the guest emitted lobby_chat_update with chat_state 1 (member entered), got %s" % str(g_chat_update))

	# Spec line 262: lobby data round-trips (host writes, both read after pumping).
	host.set_lobby_data("record", "x")
	var data_ok := _pump([host, guest], func(): return guest.get_lobby_data("record") == "x")
	_assert(host.get_lobby_data("record") == "x", "the host reads its own lobby data back")
	_assert(data_ok and guest.get_lobby_data("record") == "x", "the guest reads lobby data \"record\" == \"x\" after pumping")
	_assert(guest.get_lobby_data("nokey") == "", "an unset key reads \"\"")

	# Spec line 262 + INTERFACE: chat fans out to every member, the sender included; message = var_to_str(msg);
	# ints stay ints (batch-2 ruling 13).
	var ping := {"t": "ping", "n": 1}
	guest.send_chat(ping)
	var ping_in := _pump([host, guest], func(): return h_msgs.size() >= 1 and g_msgs.size() >= 1)
	_assert(ping_in, "a chat from the guest reaches the host and the guest itself (host %d, guest %d messages)" % [h_msgs.size(), g_msgs.size()])
	for pair in [["host", h_msgs], ["guest", g_msgs]]:
		var msgs: Array = pair[1]
		if msgs.size() >= 1:
			var m = msgs[0][2]
			_assert(m == var_to_str(ping), "%s lobby_message message == var_to_str(dict), got %s" % [pair[0], str(m)])
			var back = str_to_var(String(m))
			_assert(back is Dictionary and back == ping and typeof(back.get("n")) == TYPE_INT,
				"%s str_to_var(message) equals the dictionary with n still an int" % pair[0])
	# Chat from the host reaches both.
	var h_before := h_msgs.size()
	var g_before := g_msgs.size()
	var pong := {"t": "pong", "n": 2}
	host.send_chat(pong)
	var pong_in := _pump([host, guest], func(): return h_msgs.size() > h_before and g_msgs.size() > g_before)
	_assert(pong_in, "a chat from the host reaches the guest and the host itself")
	if g_msgs.size() > g_before:
		_assert(g_msgs[g_before][2] == var_to_str(pong), "guest receives the host's chat as var_to_str(dict)")

	# Spec line 262: leave removes. The guest's leave() makes the host emit lobby_chat_update with a left state.
	var h_cu_before := h_chat_update.size()
	guest.leave()
	var left_ok := _pump([host], func(): return host.members().size() == 1)
	_assert(left_ok and host.members() == [1], "after guest.leave() the host's members() shrinks to [1], got %s" % str(host.members()))
	var h_left := h_chat_update.slice(h_cu_before).filter(func(e): return int(e[3]) in LEFT_STATES)
	_assert(h_left.size() >= 1, "the host emitted lobby_chat_update with a chat_state in [2, 4, 8, 16] on the guest's leave, got %s" % str(h_chat_update.slice(h_cu_before)))
	host.leave()
	_completed = true

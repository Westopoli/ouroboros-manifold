extends SceneTree

# Piece W3 of docs/northstar/plans/2026-10-06-steam-multiplayer-wiring-spec.md (rev 5):
# SteamInit autoload + NetMatch autoload. Session rules: E-19 R-140-02 to R-140-04.
# Determinism rule (E-19 R-139-03, the contract W7 protects): equal command streams give equal sim logs.
#
# The spec fixes the names: autoload/steam/steam_init.gd (steam_ready), autoload/net/net_match.gd
# (start, active, command, state, drop, _process, session). It leaves the following open; this test
# FIXES them so the builder has one reading (flagged to the Architect in the report):
#   SteamInit.init_steam(app_id := 480) -> void     what _ready calls; steam_ready after it
#   NetMatch.start(record, transport, sim, lobby_chat: Callable) -> void
#       record keys used here: local_peer, host_peer, peers [{peer_id, steam_id, faction}],
#       input_delay, repeat, stall_ticks, drop_ticks (the MatchRecord, spec interface 4)
#       lobby_chat.call(msg: Dictionary) sends one reliable lobby chat message to every other member
#   NetMatch.on_lobby_chat(from_peer: int, msg: Dictionary)   the lobby-chat receive hook
#       barrier messages: {"t": "ready"} from every peer to the host; {"t": "go", "tick": 0} host to all
#       the host counts itself ready at start(); a guest sends its "ready" at start()
#   NetMatch.active() -> bool    true once the barrier has released (go sent or received)
#   NetMatch.command(cmd) -> int the session's stamp; NetMatch adds no delay of its own
#   NetMatch.state() -> Dictionary  {"kind": "running"|"stalled"|"desync"|"sim_failed"|"ended",
#       stalled: "peer"; desync: "tick", "section"}
#   NetMatch.session             the held LockstepSession
#   NetMatch._process(delta)     tests call it by hand; the poll accumulator is 50 ms
# The sim object is the session's: submit(cmd), step() -> {"tick", "sections"?} or null.

const STEAM_INIT := "res://autoload/steam/steam_init.gd"
const NET_MATCH := "res://autoload/net/net_match.gd"
const LOOPBACK := "res://autoload/net/loopback_transport.gd"

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false
var _cur := ""


class FakeSim extends RefCounted:
	var steps := 0
	var log: Array = []
	var tamper_tick := -1
	var fail_at := -1
	func submit(c: Dictionary) -> void:
		log.append([steps, int(c.get("peer", -1)), int(c.get("seq", -1)), int(c.get("arg", -1))])
	func step():
		if fail_at >= 0 and steps + 1 >= fail_at:
			return null
		steps += 1
		var r := {"tick": steps}
		if steps % 10 == 0:
			var s := [11, 22, 33, 44, 55]
			if tamper_tick >= 0 and steps >= tamper_tick:
				s[3] = 999
			r["sections"] = s
		return r


class ChatLog extends RefCounted:
	var sent: Array = []
	func send(msg: Dictionary) -> void:
		sent.append(msg)


func _initialize() -> void:
	_run_tests()
	_assert(_completed, "the checks did not run to the end (a script error aborted them)")
	print("\n=== Net Match Test Results ===")
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
	_assert(false, "%s does not exist yet (W3 not built)" % path)
	return false


func _record(local: int, ids: Array, extra := {}) -> Dictionary:
	var peers: Array = []
	for i in ids:
		peers.append({"peer_id": i, "steam_id": 1000 + i, "faction": 0})
	var r := {"local_peer": local, "host_peer": ids[0], "peers": peers,
		"input_delay": 3, "repeat": 5, "stall_ticks": 20, "drop_ticks": 1200}
	r.merge(extra, true)
	return r


func _node(sim, record: Dictionary, net, chat: Callable):
	var n = load(NET_MATCH).new()
	n.start(record, net, sim, chat)
	return n


# Two (or three) NetMatch nodes on one loopback; chat messages go straight to the other members.
func _group(ids: Array, extra := {}) -> Dictionary:
	var net = load(LOOPBACK).new()
	for i in ids:
		net.attach(i)
	var g := {"net": net, "n": {}, "sim": {}, "chat": {}}
	for i in ids:
		g["sim"][i] = FakeSim.new()
		g["chat"][i] = ChatLog.new()
	for i in ids:
		var me: int = i
		var send := func(msg: Dictionary) -> void:
			g["chat"][me].send(msg)
			for j in ids:
				if j != me and g["n"].has(j):
					g["n"][j].on_lobby_chat(me, msg)
		g["n"][i] = _node(g["sim"][i], _record(i, ids, extra), net, send)
	return g


func _tick_all(g: Dictionary, frames: int, dt := 0.05) -> void:
	for f in frames:
		for i in g["n"]:
			g["n"][i]._process(dt)


func _run_tests() -> void:
	_cur = "steam_init"
	_t_steam_init_missing_singleton()
	if not _have(NET_MATCH) or not ResourceLoader.exists(LOOPBACK):
		# every NetMatch test is red for the same reason; record one row per test name
		for t in ["inactive_before_start", "guest_waits_for_go", "guest_sends_ready", "host_waits_for_all_ready",
				"poll_accumulator_50ms", "command_adds_no_delay", "state_running", "state_stalled_names_peer",
				"state_desync_names_tick_and_section", "state_sim_failed", "drop_forwarded", "equal_command_streams"]:
			_cur = t
			_assert(false, "NetMatch missing (W3 not built)")
		_completed = true
		return
	_t_inactive_before_start()
	_t_guest_waits_for_go()
	_t_guest_sends_ready()
	_t_host_waits_for_all_ready()
	_t_poll_accumulator()
	_t_command_adds_no_delay()
	_t_state_running()
	_t_state_stalled()
	_t_state_desync()
	_t_state_sim_failed()
	_t_drop_forwarded()
	_t_equal_command_streams()
	_completed = true


# W3: a missing Steam singleton (no GodotSteam in a plain checkout) or a failed init must not crash.
func _t_steam_init_missing_singleton() -> void:
	if not _have(STEAM_INIT):
		return
	var s = load(STEAM_INIT).new()
	# See also: TD-NET-steam-singleton. The fetch script unpacks addons/godotsteam/, which makes the
	# singleton exist in a worktree; with no Steam client running, init still fails cleanly.
	if Engine.has_singleton("Steam"):
		s.init_steam(480)
		_assert(s.steam_ready == false, "a Steam singleton with no Steam client running leaves steam_ready false without crashing")
	else:
		s.init_steam(480)
		_assert(s.steam_ready == false, "no Steam singleton leaves steam_ready false without crashing")


func _t_inactive_before_start() -> void:
	_cur = "inactive_before_start"
	var n = load(NET_MATCH).new()
	_assert(n.active() == false, "a fresh NetMatch is not active (W3, E-19 R-140-02)")


func _t_guest_waits_for_go() -> void:
	_cur = "guest_waits_for_go"
	var g := _group([0, 1])
	_tick_all(g, 1, 0.0)
	var guest = g["n"][1]
	var gsim: FakeSim = g["sim"][1]
	for i in 30:
		guest._process(0.05)
	_assert(not guest.active() and gsim.steps == 0, "a guest does not step before go (W3 barrier)")
	guest.on_lobby_chat(0, {"t": "go", "tick": 0})
	_assert(guest.active(), "a guest is active once go arrives")


func _t_guest_sends_ready() -> void:
	_cur = "guest_sends_ready"
	var chat := ChatLog.new()
	var net = load(LOOPBACK).new()
	net.attach(0)
	net.attach(1)
	_node(FakeSim.new(), _record(1, [0, 1]), net, chat.send)
	_assert(chat.sent.size() == 1 and chat.sent[0].get("t", "") == "ready", "a guest sends ready at start (W3 barrier)")


func _t_host_waits_for_all_ready() -> void:
	_cur = "host_waits_for_all_ready"
	var chat := ChatLog.new()
	var net = load(LOOPBACK).new()
	for i in 3:
		net.attach(i)
	var host = _node(FakeSim.new(), _record(0, [0, 1, 2]), net, chat.send)
	_assert(not host.active() and chat.sent.is_empty(), "the host sends no go before any guest is ready")
	host.on_lobby_chat(1, {"t": "ready"})
	_assert(not host.active() and chat.sent.is_empty(), "the host waits for every peer, not the first")
	host.on_lobby_chat(2, {"t": "ready"})
	var gos := chat.sent.filter(func(m): return m.get("t", "") == "go")
	_assert(gos.size() == 1 and int(gos[0].get("tick", -1)) == 0, "ready from all peers makes the host send go with tick 0")
	_assert(host.active(), "the host is active once it has sent go")


func _t_poll_accumulator() -> void:
	_cur = "poll_accumulator_50ms"
	var sim := FakeSim.new()
	var net = load(LOOPBACK).new()
	net.attach(0)
	var n = _node(sim, _record(0, [0]), net, func(_m): pass)
	_assert(n.active(), "setup: a solo host is active at once (it is the only peer to be ready)")
	for i in 10:
		n._process(0.05)
	_assert(sim.steps == 10, "ten 50 ms frames give ten session polls (got %d)" % sim.steps)
	var sim2 := FakeSim.new()
	var net2 = load(LOOPBACK).new()
	net2.attach(0)
	var n2 = _node(sim2, _record(0, [0]), net2, func(_m): pass)
	for i in 5:
		n2._process(0.02)
	_assert(sim2.steps == 2, "frames shorter than 50 ms accumulate: 100 ms in 20 ms frames is two polls (got %d)" % sim2.steps)


func _t_command_adds_no_delay() -> void:
	_cur = "command_adds_no_delay"
	var net = load(LOOPBACK).new()
	net.attach(0)
	var n = _node(FakeSim.new(), _record(0, [0]), net, func(_m): pass)
	var stamp: int = n.command({"verb": 0, "arg": 7})
	_assert(stamp == 3, "NetMatch.command stamps now + input_delay and nothing more (got %d)" % stamp)
	n._process(0.05)
	n._process(0.05)
	var stamp2: int = n.command({"verb": 0, "arg": 8})
	_assert(stamp2 == 5, "after two polls the stamp is 2 + 3 (got %d)" % stamp2)


func _t_state_running() -> void:
	_cur = "state_running"
	var g := _group([0, 1])
	_tick_all(g, 40)
	_assert(g["n"][0].state().get("kind", "") == "running" and g["n"][1].state().get("kind", "") == "running", "healthy peers report running")
	_assert(int(g["sim"][0].steps) >= 30 and int(g["sim"][1].steps) >= 30, "both peers advanced past tick 30 on the loopback")


func _t_state_stalled() -> void:
	_cur = "state_stalled_names_peer"
	var g := _group([0, 1, 2])
	for f in 60:
		g["n"][0]._process(0.05)
		g["n"][1]._process(0.05)
	var st: Dictionary = g["n"][0].state()
	_assert(st.get("kind", "") == "stalled" and int(st.get("peer", -1)) == 2, "peer 2 silent past stall_ticks: stalled(peer 2), got %s (W3, R-140-03)" % str(st))


func _t_state_desync() -> void:
	_cur = "state_desync_names_tick_and_section"
	var g := _group([0, 1])
	g["sim"][1].tamper_tick = 20
	_tick_all(g, 80)
	var st: Dictionary = g["n"][0].state()
	_assert(st.get("kind", "") == "desync" and int(st.get("tick", -1)) == 20 and int(st.get("section", -1)) == 3, "a tampered section 3 at tick 20 gives desync(20, 3), got %s (W3, R-140-04)" % str(st))


func _t_state_sim_failed() -> void:
	_cur = "state_sim_failed"
	var sim := FakeSim.new()
	sim.fail_at = 5
	var net = load(LOOPBACK).new()
	net.attach(0)
	var n = _node(sim, _record(0, [0]), net, func(_m): pass)
	for i in 20:
		n._process(0.05)
	_assert(n.state().get("kind", "") == "sim_failed", "a sim step that returns null gives sim_failed (W3 + W0 null branch), got %s" % str(n.state()))


func _t_drop_forwarded() -> void:
	_cur = "drop_forwarded"
	var g := _group([0, 1, 2])
	_tick_all(g, 5)
	g["n"][0].drop(2)
	_assert(not (2 in g["n"][0].session.live_peers()), "drop(peer) reaches the session: peer 2 leaves live_peers (W3, R-140-03)")
	_assert(1 in g["n"][0].session.live_peers(), "the other peer stays")


# Determinism: the same ordered command stream is applied at the same sim step on every peer.
func _t_equal_command_streams() -> void:
	_cur = "equal_command_streams"
	var g := _group([0, 1])
	_tick_all(g, 10)
	g["n"][0].command({"verb": 0, "arg": 1})
	g["n"][1].command({"verb": 1, "arg": 2})
	_tick_all(g, 40)
	_assert(g["sim"][0].log.size() == 2, "both commands reached peer 0's sim (got %d)" % g["sim"][0].log.size())
	_assert(g["sim"][0].log == g["sim"][1].log, "both sims saw the same commands at the same steps (W7 determinism rule)")

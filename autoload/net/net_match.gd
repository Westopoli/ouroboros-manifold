extends Node
# Match pump (W3, docs/northstar/plans/2026-10-06-steam-multiplayer-wiring-spec.md).
# Holds the lockstep session; polls it every 50 ms once the ready/go barrier has released.

const POLL_SECONDS := 0.05

var session = null
var _record := {}
var _sim = null
var _chat: Callable
var _backend = null  # the lobby's backend: this autoload outlives the lobby scene, a Callable alone does not keep a RefCounted alive (ledger row FINDING-netmatch-backend-lifetime)
var _transport = null
var _ready_from := {}
var _active := false
var _sim_failed := false
var _acc := 0.0
var _polls := 0


# Hands the session a null-safe view of the sim: a failed step is recorded here and polling stops.
class _SimGuard extends RefCounted:
	var inner = null
	var failed := false
	func submit(c: Dictionary) -> void:
		inner.submit(c)
	func step() -> Dictionary:
		var r = inner.step()
		if r == null:
			failed = true
			return {}
		return r


var _guard := _SimGuard.new()


func start(record: Dictionary, transport, sim, lobby_chat: Callable, backend = null) -> void:
	_record = record
	_backend = backend
	_sim = sim
	_transport = transport
	_chat = lobby_chat
	_guard.inner = sim
	var ids: Array = []
	for p in record["peers"]:
		ids.append(int(p["peer_id"]))
	session = load("res://autoload/net/lockstep_session.gd").new()
	session.setup(int(record["local_peer"]), ids, transport, _guard, record)
	_ready_from = {}
	_active = false
	_sim_failed = false
	_acc = 0.0
	_polls = 0
	if _is_host():
		_ready_from[_local()] = true
		_try_go()
	else:
		_chat.call({"t": "ready"})


func _local() -> int:
	return int(_record["local_peer"])


func _is_host() -> bool:
	return _local() == int(_record["host_peer"])


func on_lobby_chat(from_peer: int, msg: Dictionary) -> void:
	match msg.get("t", ""):
		"ready":
			if _is_host():
				_ready_from[from_peer] = true
				_try_go()
		"go":
			if not _is_host() and from_peer == int(_record["host_peer"]):
				_active = true


func _try_go() -> void:
	for p in _record["peers"]:
		if not _ready_from.has(int(p["peer_id"])):
			return
	if not _active:
		_active = true
		_chat.call({"t": "go", "tick": 0})


func active() -> bool:
	return _active


func command(cmd: Dictionary) -> int:
	return session.command(cmd)


func last_frame() -> Dictionary:
	if _sim == null:
		return {}
	return _sim.last_frame()


# W5: End Mission in a match. Leaves the Steam lobby, ends the session, deactivates; the view then runs mission_end locally.
func leave() -> void:
	if _transport != null and _transport.has_method("leave_lobby"):
		_transport.leave_lobby()
	elif _record.has("lobby_id") and Engine.has_singleton("Steam"):
		Engine.get_singleton("Steam").leaveLobby(int(_record["lobby_id"]))
	if session != null:
		session.end()
	_active = false
	_backend = null


func drop(peer: int) -> void:
	session.drop(peer)


func state() -> Dictionary:
	if _guard.failed:
		return {"kind": "sim_failed"}
	var d: Dictionary = session.desync()
	if not d.is_empty():
		return {"kind": "desync", "tick": int(d["tick"]), "section": int(d["section"])}
	var live: Array = session.live_peers()
	if live.size() <= 1 and _record["peers"].size() > 1:
		return {"kind": "ended"}
	if session.is_stalled():
		var worst := -1
		var worst_silent := -1
		for p in live:
			if p != _local() and int(session._silent[p]) > worst_silent:
				worst = p
				worst_silent = int(session._silent[p])
		return {"kind": "stalled", "peer": worst}
	return {"kind": "running"}


func _process(delta: float) -> void:
	var steam = Engine.get_singleton("Steam") if Engine.has_singleton("Steam") else null
	if steam != null and get_node_or_null("/root/SteamInit") != null and get_node("/root/SteamInit").steam_ready:
		steam.run_callbacks()
	if not _active or session == null or _guard.failed:
		return
	_acc += delta
	while _acc >= POLL_SECONDS - 0.000001:
		_acc -= POLL_SECONDS
		session.poll()
		_polls += 1
		if _guard.failed:
			return
		_resend_go()


# Lobby chat is reliable, but a guest that joins the chat late can miss the one go; the host repeats it
# until that guest's first packet arrives.
func _resend_go() -> void:
	if not _is_host():
		return
	for p in session.live_peers():
		if p != _local() and int(session._silent[p]) >= _polls:
			if _backend != null:
				_backend.send_chat({"t": "go", "tick": 0})
			else:
				_chat.call({"t": "go", "tick": 0})
			return

## Singleton bridge between the Python tactical engine and Godot scenes.
## Owns the TCP connection, applies snapshots/deltas, dead-reckons unit
## positions between ticks, and re-publishes state via signals.
##
## Dead-reckoning: units absent from units_updated are extrapolated using their
## last known velocity each _process() frame. Resyncs land via units_updated
## with both pos and velocity. See snapshot_serializer.py for the Python side.
##
## Stage 10 note: ws_client.gd (the TCP transport) is replaced by stdio pipes
## when Godot spawns the sim as a child process. This file's public API stays
## the same; only connect_to_engine() changes its transport call.
extends Node

signal snapshot_received(snapshot: Dictionary)
signal tick_delta_received(delta: Dictionary)
signal connection_state_changed(connected: bool)

const INTERP_BUFFER_TICKS := 3

var _client: Node  # WsClient autoload reference (set in _ready)
var _connected := false

# Current authoritative state (after applying all deltas)
var current_tick: int = 0
var units: Dictionary = {}        # uid (int) → unit dict
var structures: Dictionary = {}   # uid (int) → structure dict
var objectives: Array = []
var map_data: Dictionary = {}     # from snapshot "map" field

# Dead-reckoning: per-uid last-known velocity [vx, vy] in wu/s
var _velocities: Dictionary = {}  # uid → [vx, vy]

# Interpolated display positions (updated every frame)
var display_positions: Dictionary = {}  # uid → [x, y]

var _last_frame_time: float = 0.0


func _ready() -> void:
	_client = WsClient
	_client.connected.connect(_on_connected)
	_client.disconnected.connect(_on_disconnected)
	_client.message_received.connect(_on_message)


func connect_to_engine(host: String = "127.0.0.1", port: int = 8765) -> void:
	_client.connect_to_server(host, port)


func disconnect_from_engine() -> void:
	_client.disconnect_from_server()


func send_command(command: Dictionary) -> void:
	_client.send({"type": "command", "command": command})


func _process(delta: float) -> void:
	if not _connected:
		return
	# Dead-reckon all units by their last velocity
	for uid in display_positions:
		var vel: Array = _velocities.get(uid, [0.0, 0.0])
		if vel[0] != 0.0 or vel[1] != 0.0:
			display_positions[uid] = [
				display_positions[uid][0] + vel[0] * delta,
				display_positions[uid][1] + vel[1] * delta,
			]


func _on_connected() -> void:
	_connected = true
	connection_state_changed.emit(true)
	print("TacticalBridge: connected to engine")


func _on_disconnected() -> void:
	_connected = false
	connection_state_changed.emit(false)
	print("TacticalBridge: disconnected from engine")


func _on_message(payload: Dictionary) -> void:
	match payload.get("type", ""):
		"snapshot":
			_apply_snapshot(payload)
			snapshot_received.emit(payload)
		"delta":
			_apply_delta(payload)
			tick_delta_received.emit(payload)
		_:
			pass  # hello or unknown — ignore


func _apply_snapshot(snap: Dictionary) -> void:
	current_tick = snap.get("tick", 0)
	map_data = snap.get("map", {})
	units.clear()
	_velocities.clear()
	display_positions.clear()
	for u in snap.get("units", []):
		var uid: int = u["uid"]
		units[uid] = u.duplicate()
		var vel: Array = u.get("velocity", [0.0, 0.0])
		_velocities[uid] = vel
		display_positions[uid] = [u["pos"][0], u["pos"][1]]
	structures.clear()
	for s in snap.get("structures", []):
		structures[s["uid"]] = s.duplicate()
	objectives = snap.get("objectives", []).duplicate()


func _apply_delta(d: Dictionary) -> void:
	current_tick = d.get("tick", current_tick)

	for uid in d.get("units_removed", []):
		units.erase(uid)
		_velocities.erase(uid)
		display_positions.erase(uid)

	for u in d.get("units_added", []):
		var uid: int = u["uid"]
		units[uid] = u.duplicate()
		var vel: Array = u.get("velocity", [0.0, 0.0])
		_velocities[uid] = vel
		display_positions[uid] = [u["pos"][0], u["pos"][1]]

	for upd in d.get("units_updated", []):
		var uid: int = upd["uid"]
		if uid not in units:
			continue
		units[uid].merge(upd, true)
		if "pos" in upd:
			# Resync: snap display position and update velocity
			display_positions[uid] = [upd["pos"][0], upd["pos"][1]]
			_velocities[uid] = upd.get("velocity", [0.0, 0.0])
		if "velocity" in upd and "pos" not in upd:
			_velocities[uid] = upd["velocity"]

	for upd in d.get("structures_updated", []):
		var uid: int = upd["uid"]
		if uid in structures:
			structures[uid].merge(upd, true)

	for upd in d.get("objectives_updated", []):
		for i in range(objectives.size()):
			if objectives[i].get("id") == upd.get("id"):
				objectives[i] = upd.duplicate()
				break

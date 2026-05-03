## Singleton bridge between the Python tactical engine and Godot scenes.
## Owns the TCP connection, applies snapshots/deltas, and re-publishes state
## via signals.
##
## Flat-array interpolation buffer (Stage 8.5):
## Renders the RECENT PAST by interpolating between known-good server tick
## states stored as PackedFloat32Arrays indexed by uid*2. Display is ~150ms
## behind real-time (3 ticks at 20Hz) but shows ground-truth positions that
## never need correction.
##
## Performance: buffer entries use C++-backed flat arrays instead of GDScript
## Dictionaries. _apply_delta copies via memcpy + writes only changed indices.
## _process lerps flat arrays directly into display_x/display_y output arrays.
## No per-unit Dictionary allocation per tick or per frame.
##
## See also: scenes/tactical/perf_logger.gd, docs/architecture.md
extends Node

signal snapshot_received(snapshot: Dictionary)
signal tick_delta_received(delta: Dictionary)
signal connection_state_changed(connected: bool)
signal command_sent(command: Dictionary)
signal ability_event_received(event: Dictionary)

const BUFFER_DELAY_TICKS := 3
const BUFFER_DEPTH := 6
const TICK_DURATION := 0.05  # 1.0 / 20Hz
const MAX_UNITS := 1024

var _client: Node
var _connected := false

# Current authoritative state (non-positional, applied immediately)
var current_tick: int = 0
var units: Dictionary = {}        # uid (int) → unit dict
var structures: Dictionary = {}   # uid (int) → structure dict
var objectives: Array = []
var map_data: Dictionary = {}
# See also: scripts/tactical/visibility.gd — fog predicate reads this
var player_visible_unit_uids: Dictionary = {}  # uid(int) → true; set semantics

# Interpolation buffer: array of tick entries with flat arrays.
# Each entry: {tick: int, time: float, positions: PFA, velocities: PFA, alive: PBA}
var _tick_buffer: Array = []

# Public render output — flat arrays, written every _process frame.
# Consumers index by uid directly. Scales to MAX_UNITS without Dict overhead.
var display_x: PackedFloat32Array = PackedFloat32Array()
var display_y: PackedFloat32Array = PackedFloat32Array()
var display_facing: PackedFloat32Array = PackedFloat32Array()
var display_alive: PackedByteArray = PackedByteArray()
var unit_count: int = 0  # high-water mark: highest uid + 1

var _logger = preload("res://scenes/tactical/perf_logger.gd").new()


func _ready() -> void:
	display_x.resize(MAX_UNITS)
	display_y.resize(MAX_UNITS)
	display_facing.resize(MAX_UNITS)
	display_alive.resize(MAX_UNITS)
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
	# See also: scenes/tactical/input_router.gd:_send — emits command_sent for both sim paths


func _process(_delta: float) -> void:

	if not _connected:
		return
	if _tick_buffer.size() == 0:
		return

	if _tick_buffer.size() == 1:
		var entry: Dictionary = _tick_buffer[0]
		_write_display_from_entry(entry)
		if _logger:
			_logger.log_frame(display_x, display_y, display_alive, unit_count,
							  entry.positions, current_tick)
		return

	var latest_time: float = _tick_buffer[_tick_buffer.size() - 1].time
	var render_time: float = latest_time - BUFFER_DELAY_TICKS * TICK_DURATION

	if render_time <= _tick_buffer[0].time:
		_write_display_from_entry(_tick_buffer[0])
		if _logger:
			_logger.log_frame(display_x, display_y, display_alive, unit_count,
							  _tick_buffer[0].positions, current_tick)
		return

	# Find bracketing entries
	var entry_a: Dictionary = _tick_buffer[0]
	var entry_b: Dictionary = _tick_buffer[1]
	for i in range(_tick_buffer.size() - 1):
		if _tick_buffer[i + 1].time >= render_time:
			entry_a = _tick_buffer[i]
			entry_b = _tick_buffer[i + 1]
			break

	var span: float = entry_b.time - entry_a.time
	var t: float = 0.0
	if span > 0.0001:
		t = clamp((render_time - entry_a.time) / span, 0.0, 1.0)

	# Lerp flat arrays
	var pa: PackedFloat32Array = entry_a.positions
	var pb: PackedFloat32Array = entry_b.positions
	var fa: PackedFloat32Array = entry_a.facings
	var fb: PackedFloat32Array = entry_b.facings
	var alive_b: PackedByteArray = entry_b.alive
	for uid in range(unit_count):
		if alive_b[uid] == 0:
			display_alive[uid] = 0
			continue
		display_alive[uid] = 1
		var idx: int = uid * 2
		display_x[uid] = pa[idx] + (pb[idx] - pa[idx]) * t
		display_y[uid] = pa[idx + 1] + (pb[idx + 1] - pa[idx + 1]) * t
		display_facing[uid] = lerp_angle(fa[uid], fb[uid], t)

	if _logger:
		_logger.log_frame(display_x, display_y, display_alive, unit_count,
						  entry_b.positions, current_tick)


func _on_connected() -> void:
	_connected = true
	_tick_buffer.clear()
	connection_state_changed.emit(true)
	print("TacticalBridge: connected to engine")


func _on_disconnected() -> void:
	_connected = false
	connection_state_changed.emit(false)
	print("TacticalBridge: disconnected from engine")


func _on_message(payload: Dictionary) -> void:
	var t: String = payload.get("type", "")
	if t == "snapshot":
		print("TacticalBridge: snapshot tick=%d units=%d" % [payload.get("tick", -1), payload.get("units", []).size()])
	match payload.get("type", ""):
		"snapshot":
			_apply_snapshot(payload)
			snapshot_received.emit(payload)
		"delta":
			_apply_delta(payload)
			tick_delta_received.emit(payload)
		_:
			pass


func _apply_snapshot(snap: Dictionary) -> void:
	if _logger:
		_logger.log_snapshot(snap, display_x, display_y, display_alive, unit_count)
	current_tick = snap.get("tick", 0)
	map_data = snap.get("map", {})

	var pos := PackedFloat32Array()
	pos.resize(MAX_UNITS * 2)
	var vel := PackedFloat32Array()
	vel.resize(MAX_UNITS * 2)
	var fac := PackedFloat32Array()
	fac.resize(MAX_UNITS)
	var alive := PackedByteArray()
	alive.resize(MAX_UNITS)

	var seen: Dictionary = {}
	var max_uid: int = 0

	for u in snap.get("units", []):
		var uid: int = int(u["uid"])
		seen[uid] = true
		units[uid] = u.duplicate()
		pos[uid * 2] = float(u["pos"][0])
		pos[uid * 2 + 1] = float(u["pos"][1])
		var v: Array = u.get("velocity", [0.0, 0.0])
		vel[uid * 2] = float(v[0])
		vel[uid * 2 + 1] = float(v[1])
		fac[uid] = float(u.get("facing_rad", 0.0))
		alive[uid] = 1
		if uid >= max_uid:
			max_uid = uid + 1

	unit_count = max_uid

	# Prune units not in snapshot
	for uid in units.keys():
		if not seen.has(uid):
			units.erase(uid)

	_tick_buffer.clear()
	_tick_buffer.append({
		"tick": current_tick,
		"time": Time.get_ticks_msec() / 1000.0,
		"positions": pos,
		"velocities": vel,
		"facings": fac,
		"alive": alive,
	})

	# Initialize display
	_write_display_from_entry(_tick_buffer[0])

	# Fog of war: convert array → dict for O(1) lookup.
	# Deltas don't carry fog_of_war; this set persists until the next snapshot.
	var fog: Dictionary = snap.get("fog_of_war", {})
	var vis_array: Array = fog.get("player_visible_unit_uids", [])
	player_visible_unit_uids.clear()
	for uid in vis_array:
		player_visible_unit_uids[int(uid)] = true

	structures.clear()
	for s in snap.get("structures", []):
		structures[s["uid"]] = s.duplicate()
	objectives = snap.get("objectives", []).duplicate()


func _apply_delta(d: Dictionary) -> void:
	if _logger:
		_logger.log_delta(d, display_x, display_y, display_alive, unit_count)
	current_tick = d.get("tick", current_tick)

	var prev: Dictionary = _tick_buffer[_tick_buffer.size() - 1] if _tick_buffer.size() > 0 else {}

	# Copy previous arrays (C++-backed memcpy)
	var pos: PackedFloat32Array
	var vel: PackedFloat32Array
	var fac: PackedFloat32Array
	var alive: PackedByteArray
	if prev.is_empty():
		pos = PackedFloat32Array()
		pos.resize(MAX_UNITS * 2)
		vel = PackedFloat32Array()
		vel.resize(MAX_UNITS * 2)
		fac = PackedFloat32Array()
		fac.resize(MAX_UNITS)
		alive = PackedByteArray()
		alive.resize(MAX_UNITS)
	else:
		pos = PackedFloat32Array(prev.positions)
		vel = PackedFloat32Array(prev.velocities)
		fac = PackedFloat32Array(prev.facings)
		alive = PackedByteArray(prev.alive)

	# Advance all alive units by vel × dt
	for uid in range(unit_count):
		if alive[uid] == 0:
			continue
		var idx: int = uid * 2
		pos[idx] += vel[idx] * TICK_DURATION
		pos[idx + 1] += vel[idx + 1] * TICK_DURATION

	# Apply units_removed
	for uid in d.get("units_removed", []):
		var iuid: int = int(uid)
		alive[iuid] = 0
		pos[iuid * 2] = 0.0
		pos[iuid * 2 + 1] = 0.0
		vel[iuid * 2] = 0.0
		vel[iuid * 2 + 1] = 0.0
		fac[iuid] = 0.0
		units.erase(iuid)

	# Apply units_added
	for u in d.get("units_added", []):
		var uid: int = int(u["uid"])
		if uid >= unit_count:
			unit_count = uid + 1
		units[uid] = u.duplicate()
		alive[uid] = 1
		pos[uid * 2] = float(u["pos"][0])
		pos[uid * 2 + 1] = float(u["pos"][1])
		var v: Array = u.get("velocity", [0.0, 0.0])
		vel[uid * 2] = float(v[0])
		vel[uid * 2 + 1] = float(v[1])
		fac[uid] = float(u.get("facing_rad", 0.0))

	# Apply units_updated
	for upd in d.get("units_updated", []):
		var uid: int = int(upd["uid"])
		if uid not in units:
			continue
		units[uid].merge(upd, true)
		if "pos" in upd:
			pos[uid * 2] = float(upd["pos"][0])
			pos[uid * 2 + 1] = float(upd["pos"][1])
			var v: Array = upd.get("velocity", [0.0, 0.0])
			vel[uid * 2] = float(v[0])
			vel[uid * 2 + 1] = float(v[1])
		elif "velocity" in upd:
			vel[uid * 2] = float(upd["velocity"][0])
			vel[uid * 2 + 1] = float(upd["velocity"][1])
		if "facing_rad" in upd:
			fac[uid] = float(upd["facing_rad"])

	_tick_buffer.append({
		"tick": current_tick,
		"time": Time.get_ticks_msec() / 1000.0,
		"positions": pos,
		"velocities": vel,
		"facings": fac,
		"alive": alive,
	})

	while _tick_buffer.size() > BUFFER_DEPTH:
		_tick_buffer.pop_front()

	# Non-positional state updates
	for upd in d.get("structures_updated", []):
		var uid: int = upd["uid"]
		if uid in structures:
			structures[uid].merge(upd, true)

	for upd in d.get("objectives_updated", []):
		for i in range(objectives.size()):
			if objectives[i].get("id") == upd.get("id"):
				objectives[i] = upd.duplicate()
				break

	for evt in d.get("events", []):
		if str(evt.get("kind", "")) == "ability":
			ability_event_received.emit(evt)


func _write_display_from_entry(entry: Dictionary) -> void:
	var pos: PackedFloat32Array = entry.positions
	var fac: PackedFloat32Array = entry.facings
	var alive_arr: PackedByteArray = entry.alive
	for uid in range(unit_count):
		if alive_arr[uid] == 0:
			display_alive[uid] = 0
			continue
		display_alive[uid] = 1
		display_x[uid] = pos[uid * 2]
		display_y[uid] = pos[uid * 2 + 1]
		display_facing[uid] = fac[uid]

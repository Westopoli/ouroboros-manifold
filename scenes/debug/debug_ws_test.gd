## Checkpoint F debug scene — connects to the Python engine over raw TCP
## and displays live tick count, unit count, and structure count.
## Disconnect / reconnect via buttons to verify graceful handling.
extends Control

@onready var _label: Label = $StatusLabel
@onready var _log: Label = $LogLabel

var _log_lines: Array[String] = []
const LOG_MAX := 12


func _ready() -> void:
	TacticalBridge.snapshot_received.connect(_on_snapshot)
	TacticalBridge.tick_delta_received.connect(_on_delta)
	TacticalBridge.connection_state_changed.connect(_on_conn_state)
	_set_status("Connecting to 127.0.0.1:8765 ...")
	TacticalBridge.connect_to_engine("127.0.0.1", 8765)


func _on_conn_state(connected: bool) -> void:
	if connected:
		_log_push("CONNECTED")
	else:
		_log_push("DISCONNECTED")
		_set_status("Disconnected — waiting for server")


func _on_snapshot(snap: Dictionary) -> void:
	var unit_count: int = (snap.get("units", []) as Array).size()
	var struct_count: int = (snap.get("structures", []) as Array).size()
	_set_status("SNAPSHOT  tick=%d  units=%d  structures=%d" % [
		snap.get("tick", 0), unit_count, struct_count
	])
	_log_push("snapshot tick=%d" % snap.get("tick", 0))


func _on_delta(d: Dictionary) -> void:
	var tick: int = TacticalBridge.current_tick
	var unit_count: int = TacticalBridge.units.size()
	var struct_count: int = TacticalBridge.structures.size()
	_set_status("LIVE  tick=%d  units=%d  structures=%d" % [tick, unit_count, struct_count])


func _set_status(text: String) -> void:
	_label.text = text


func _log_push(line: String) -> void:
	_log_lines.push_back(line)
	if _log_lines.size() > LOG_MAX:
		_log_lines.pop_front()
	_log.text = "\n".join(_log_lines)


func _on_disconnect_pressed() -> void:
	TacticalBridge.disconnect_from_engine()
	_log_push("disconnect requested")


func _on_reconnect_pressed() -> void:
	TacticalBridge.connect_to_engine("127.0.0.1", 8765)
	_log_push("reconnect requested")

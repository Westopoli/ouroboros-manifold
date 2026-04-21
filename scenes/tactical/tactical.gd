## Tactical scene root: camera pan/zoom and performance metrics overlay.
## Connects to TacticalBridge and passes connection state to child renderers.
extends Node3D

const PAN_SPEED        := 1500.0
const ZOOM_STEP        := 300.0
const ZOOM_MIN         := 150.0
const ZOOM_MAX         := 6000.0
const EDGE_SCROLL_ZONE := 60.0

# Camera offset from pan target: (0, sin65, cos65) * zoom_dist
const _CAM_SIN := 0.9063  # sin(65°)
const _CAM_COS := 0.4226  # cos(65°)

var _zoom_dist: float    = 3000.0
var _pan_target: Vector3 = Vector3(2000.0, 0.0, 2000.0)

@onready var _camera: Camera3D  = $Camera3D
@onready var _perf_label: Label = $DebugLayer/PerfPanel/PerfLabel

const _PERF_WINDOW := 300
var _frame_times: Array[float] = []
var _dropped_frames: int = 0
var _frame_counter: int = 0


var _attack_visuals: Node3D


func _ready() -> void:
	_attack_visuals = preload("res://scenes/tactical/visuals/attack_visual_manager.gd").new()
	_attack_visuals.name = "AttackVisualManager"
	add_child(_attack_visuals)

	if SimBridge.USE_LIVE_SIM:
		# Stage 10: tactical data flows through SimBridge stdio pipe.
		SimBridge.state_updated.connect(TacticalBridge._on_message)
	else:
		# Development fallback: connect via WebSocket to run_debug_server.py
		TacticalBridge.connect_to_engine("127.0.0.1", 8765)
	TacticalBridge.connection_state_changed.connect(_on_conn_state)
	TacticalBridge.snapshot_received.connect(_on_first_snapshot, CONNECT_ONE_SHOT)
	_setup_environment()
	_update_camera()


func _notification(what: int) -> void:
	if what == NOTIFICATION_EXIT_TREE:
		MissionMetricsRecorder.stop_recording()
		BugReportManager.stop_buffering()


func _on_first_snapshot(_snap: Dictionary) -> void:
	MissionMetricsRecorder.start_recording()
	BugReportManager.start_buffering()
	var sum := Vector3.ZERO
	var count := 0
	for uid: int in range(TacticalBridge.unit_count):
		if TacticalBridge.display_alive[uid] == 0:
			continue
		if TacticalBridge.units.get(uid, {}).get("faction", -1) == 0:
			sum += Vector3(TacticalBridge.display_x[uid], 0.0, TacticalBridge.display_y[uid])
			count += 1
	if count > 0:
		_pan_target = sum / float(count)
	_zoom_dist = 1000.0
	_update_camera()


func _setup_environment() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.04, 0.04, 0.08)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.35, 0.35, 0.45)
	env.ambient_light_energy = 0.6
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)

	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-50.0, -30.0, 0.0)
	sun.light_energy = 0.9
	sun.shadow_enabled = false
	add_child(sun)


func _on_conn_state(is_connected: bool) -> void:
	if not is_connected:
		_perf_label.text = "Disconnected — waiting for engine..."


func _process(delta: float) -> void:
	_handle_camera(delta)
	_record_frame(delta)
	_frame_counter += 1
	if _frame_counter % 60 == 0:
		_update_perf_label()


func _handle_camera(delta: float) -> void:
	var pan_speed := PAN_SPEED * (_zoom_dist / 3000.0)
	var pan := Vector3.ZERO
	var mouse := get_viewport().get_mouse_position()
	var vp    := get_viewport().get_visible_rect().size
	if mouse.x < EDGE_SCROLL_ZONE:            pan.x -= 1.0
	if mouse.x > vp.x - EDGE_SCROLL_ZONE:    pan.x += 1.0
	if mouse.y < EDGE_SCROLL_ZONE:            pan.z -= 1.0
	if mouse.y > vp.y - EDGE_SCROLL_ZONE:    pan.z += 1.0
	if pan != Vector3.ZERO:
		_pan_target += pan.normalized() * pan_speed * delta
		_update_camera()


func _input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.pressed:
			if mb.button_index == MOUSE_BUTTON_WHEEL_UP:
				_zoom_by(ZOOM_STEP)
			elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN:
				_zoom_by(-ZOOM_STEP)
	elif event is InputEventPanGesture:
		# macOS trackpad sends PanGesture instead of MouseButton wheel events
		var pg := event as InputEventPanGesture
		_zoom_by(-pg.delta.y * 15.0)
	elif event is InputEventKey and event.pressed and event.keycode == KEY_F5:
		# Debug: jump to debrief with mock data. Remove when mission_ended signal is wired.
		_debug_debrief()


func _zoom_by(amount: float) -> void:
	_zoom_dist = clampf(_zoom_dist - amount, ZOOM_MIN, ZOOM_MAX)
	_update_camera()


func _update_camera() -> void:
	_camera.position = _pan_target + Vector3(0.0, _CAM_SIN, _CAM_COS) * _zoom_dist
	_camera.look_at(_pan_target, Vector3.UP)


func _record_frame(delta: float) -> void:
	var ms := delta * 1000.0
	_frame_times.append(ms)
	if _frame_times.size() > _PERF_WINDOW:
		_frame_times = _frame_times.slice(_frame_times.size() - _PERF_WINDOW)
	if ms > 16.67:
		_dropped_frames += 1


func _update_perf_label() -> void:
	if _frame_times.is_empty():
		return
	var sorted: Array[float] = _frame_times.duplicate()
	sorted.sort()
	var n := sorted.size()
	var p50 := sorted[n * 50 / 100]
	var p95 := sorted[n * 95 / 100]
	var p99 := sorted[n * 99 / 100]
	var mem_static_mb  := Performance.get_monitor(Performance.MEMORY_STATIC)  / 1048576.0
	var mem_dynamic_mb := Performance.get_monitor(Performance.MEMORY_MESSAGE_BUFFER_MAX) / 1048576.0
	var obj_count      := int(Performance.get_monitor(Performance.OBJECT_COUNT))
	var node_count     := int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))
	var orphan_count   := int(Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT))
	_perf_label.text = (
		"tick %d   units %d   zoom %.0f\n" % [TacticalBridge.current_tick, TacticalBridge.units.size(), _zoom_dist] +
		"frame  p50 %.1fms  p95 %.1fms  p99 %.1fms\n" % [p50, p95, p99] +
		"dropped (>16.7ms): %d\n" % _dropped_frames +
		"mem  static %.1fMB  dynamic %.1fMB\n" % [mem_static_mb, mem_dynamic_mb] +
		"objects %d   nodes %d   orphans %d" % [obj_count, node_count, orphan_count]
	)


func _debug_debrief() -> void:
	var mock_debrief := {
		"outcome_band": "strong_success",
		"outcome_band_prose": "A hard-fought defense that held the line.",
		"final_score": 0.78,
		"objective_score": 0.82,
		"force_retention": 0.68,
		"objectives": [
			{"id": "hold_zone_alpha", "type": "hold_zone", "weight": 0.6,
			 "completion": 0.95, "label": "Hold the northern approach"},
			{"id": "eliminate_force", "type": "eliminate_force", "weight": 0.4,
			 "completion": 0.62, "label": "Destroy the assault force"},
		],
		"field_deltas": {
			"military": {"raw": 6.4, "direction": "up", "magnitude": "moderate",
						 "prose": "Your defense stabilized the region's military position."},
			"tension": {"raw": -4.2, "direction": "down", "magnitude": "moderate",
						"prose": "Tensions in the region eased."},
			"economy": {"raw": -3.8, "direction": "down", "magnitude": "moderate",
						"prose": "Significant economic disruption followed the fighting."},
			"population": {"raw": 0.0, "direction": "stable", "magnitude": "none", "prose": ""},
		},
		"impact_preview": "Your defense stabilized the region's military position. Tensions eased — but the economic disruption could attract opportunists if the region doesn't recover quickly.",
		"commander_fate": "survived",
		"mission_duration_ticks": 36000,
		"mission_duration_seconds": 1800.0,
	}
	SceneRouter.go_to("debrief", {"debrief": mock_debrief, "era_id": "settled_reach"})

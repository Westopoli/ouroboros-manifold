## Tactical scene root: camera pan/zoom and performance metrics overlay.
## Connects to TacticalBridge and passes connection state to child renderers.
extends Node3D

const SimSession := preload("res://autoload/sim_session.gd")

const PAN_SPEED        := 1500.0
const ZOOM_STEP        := 300.0
const ZOOM_MIN         := 150.0
const ZOOM_MAX         := 12000.0
const EDGE_SCROLL_ZONE := 60.0

# Camera offset from pan target: (0, sin65, cos65) * zoom_dist
const _CAM_SIN := 0.9063  # sin(65°)
const _CAM_COS := 0.4226  # cos(65°)

var _zoom_dist: float    = 6000.0
var _pan_target: Vector3 = Vector3(4000.0, 0.0, 4000.0)
var _edge_scroll_speed: float = PAN_SPEED

@onready var _camera: Camera3D  = $Camera3D
@onready var _perf_label: Label = $DebugLayer/PerfPanel/PerfLabel

const _PERF_WINDOW := 300
var _frame_times: Array[float] = []
var _dropped_frames: int = 0
var _frame_counter: int = 0


var _attack_visuals: Node3D
var _ability_overlays: Node3D
var _impact_feedback: Node3D
var _destruction: Node3D
var _ambient: Node3D
var _loading_overlay: CanvasLayer
# See also: scenes/tactical/mission_marker.gd — in-world objective beacons
var _mission_markers: Node3D
var _marker_instances: Dictionary = {}  # obj_id → MissionMarker node
# See also: scenes/tactical/command_indicator.gd — transient command decals
var _command_indicators: Node3D

# See also: autoload/tutorial_state_machine.gd — listens for these triggers
# to fire TUT_002 (first_unit_visible) and TUT_003 (first_unit_selected).
var _emitted_first_unit_visible: bool = false
var _emitted_first_unit_selected: bool = false


func _ready() -> void:
	print("Tactical: scene _ready()")
	_attack_visuals = preload("res://scenes/tactical/visuals/attack_visual_manager.gd").new()
	_attack_visuals.name = "AttackVisualManager"
	add_child(_attack_visuals)

	_ability_overlays = preload("res://scenes/tactical/visuals/ability_overlay_manager.gd").new()
	_ability_overlays.name = "AbilityOverlayManager"
	add_child(_ability_overlays)
	_ability_overlays.setup($Camera3D, SimSession.bridge().player_faction(), _attack_visuals)

	_impact_feedback = preload("res://scenes/tactical/visuals/impact_feedback_manager.gd").new()
	_impact_feedback.name = "ImpactFeedbackManager"
	add_child(_impact_feedback)

	_destruction = preload("res://scenes/tactical/visuals/destruction_manager.gd").new()
	_destruction.name = "DestructionManager"
	add_child(_destruction)
	_destruction.setup($Camera3D)

	_ambient = preload("res://scenes/tactical/visuals/ambient_density_manager.gd").new()
	_ambient.name = "AmbientDensityManager"
	add_child(_ambient)

	_loading_overlay = preload("res://scenes/tactical/tactical_loading_overlay.gd").new()
	add_child(_loading_overlay)

	_mission_markers = Node3D.new()
	_mission_markers.name = "MissionMarkers"
	add_child(_mission_markers)

	_command_indicators = Node3D.new()
	_command_indicators.name = "CommandIndicators"
	add_child(_command_indicators)

	var settings := UIDataBus.get_settings()
	_edge_scroll_speed = float(settings.get("edge_scroll_speed", PAN_SPEED))

	if SimBridge.USE_LIVE_SIM:
		# Stage 10: tactical data flows through SimBridge stdio pipe.
		SimBridge.state_updated.connect(TacticalBridge._on_message)
		TacticalBridge._connected = true
		SimBridge.send_command({"type": "command", "cmd": "ready_for_tactical"})
	# See also: autoload/tactical_bridge.gd — the WebSocket dev fallback this
	# branched to (TacticalBridge.connect_to_engine) was removed with WsClient.
	TacticalBridge.connection_state_changed.connect(_on_conn_state)
	TacticalBridge.snapshot_received.connect(_on_first_snapshot, CONNECT_ONE_SHOT)
	TacticalBridge.snapshot_received.connect(_sync_mission_markers)
	TacticalBridge.tick_delta_received.connect(_on_delta_markers)
	TacticalBridge.command_sent.connect(_on_command_sent)
	_setup_environment()
	_update_camera()


func _notification(what: int) -> void:
	if what == NOTIFICATION_EXIT_TREE:
		MissionMetricsRecorder.stop_recording()
		BugReportManager.stop_buffering()


func _on_first_snapshot(_snap: Dictionary) -> void:
	if _loading_overlay and is_instance_valid(_loading_overlay):
		_loading_overlay.dismiss()
		_loading_overlay = null
	MissionMetricsRecorder.start_recording()
	BugReportManager.start_buffering()
	var sum := Vector3.ZERO
	var count := 0
	for uid: int in range(TacticalBridge.unit_count):
		if TacticalBridge.display_alive[uid] == 0:
			continue
		if TacticalBridge.units.get(uid, {}).get("faction", -1) == SimSession.bridge().player_faction():
			sum += Vector3(TacticalBridge.display_x[uid], 0.0, TacticalBridge.display_y[uid])
			count += 1
	if count > 0:
		_pan_target = sum / float(count)
	_zoom_dist = 1000.0
	_update_camera()
	# See also: autoload/tutorial_state_machine.gd — TUT_002 fires on first_unit_visible.
	if not _emitted_first_unit_visible and TacticalBridge.units.size() > 0:
		_emitted_first_unit_visible = true
		_notify_tutorial("first_unit_visible")


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
	_attack_visuals.camera_zoom = _zoom_dist
	_impact_feedback.camera_zoom = _zoom_dist
	_ambient.camera_zoom = _zoom_dist
	_record_frame(delta)
	_frame_counter += 1
	if _frame_counter % 60 == 0:
		_update_perf_label()
	_check_first_unit_selected()


func _check_first_unit_selected() -> void:
	if _emitted_first_unit_selected:
		return
	var router := get_node_or_null("InputRouter")
	if router == null:
		return
	var selected = router.get("selected_uids")
	if selected == null:
		return
	if selected.size() > 0:
		_emitted_first_unit_selected = true
		_notify_tutorial("first_unit_selected")


func _notify_tutorial(trigger_event: String) -> void:
	var tsm := get_node_or_null("/root/TutorialStateMachine")
	if tsm != null and tsm.has_method("handle_trigger"):
		tsm.call("handle_trigger", trigger_event)


func _handle_camera(delta: float) -> void:
	var pan_speed := _edge_scroll_speed * (_zoom_dist / 3000.0)
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
	var fps := Engine.get_frames_per_second()
	var atk_stats: Dictionary = _attack_visuals.get_stats()
	var amb_stats: Dictionary = _ambient.get_stats()
	var imp_stats: Dictionary = _impact_feedback.get_stats()
	_perf_label.text = (
		"FPS %d   tick %d   units %d   zoom %.0f\n" % [fps, TacticalBridge.current_tick, TacticalBridge.units.size(), _zoom_dist] +
		"frame  p50 %.1fms  p95 %.1fms  p99 %.1fms\n" % [p50, p95, p99] +
		"dropped (>16.7ms): %d\n" % _dropped_frames +
		"proj %d  beam %d  pulse %d  lod_cull %d\n" % [atk_stats.active_projectiles, atk_stats.active_beams, atk_stats.active_pulses, atk_stats.lod_culled] +
		"bursts %d  blooms %d  impacts %d\n" % [imp_stats.active_bursts, imp_stats.active_blooms, imp_stats.total_impacts] +
		"flybys %d  haze %s\n" % [amb_stats.active_flybys, "on" if amb_stats.haze_active else "off"] +
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


func _sync_mission_markers(_snap: Dictionary) -> void:
	var active_ids: Dictionary = {}
	for obj in TacticalBridge.objectives:
		var obj_id: String = obj.get("id", "")
		var status: String = obj.get("status", "in_progress")
		var loc: Dictionary = obj.get("location", {})
		if loc.is_empty() or status == "complete" or status == "failed":
			if obj_id in _marker_instances:
				_marker_instances[obj_id].queue_free()
				_marker_instances.erase(obj_id)
			continue
		active_ids[obj_id] = true
		if obj_id in _marker_instances:
			_marker_instances[obj_id].update_objective(obj)
		else:
			var marker: Node3D = preload("res://scenes/tactical/mission_marker.gd").new()
			marker.setup(obj)
			_mission_markers.add_child(marker)
			_marker_instances[obj_id] = marker
	for existing_id in _marker_instances.keys():
		if existing_id not in active_ids:
			_marker_instances[existing_id].queue_free()
			_marker_instances.erase(existing_id)


func _on_delta_markers(_d: Dictionary) -> void:
	for obj in TacticalBridge.objectives:
		var obj_id: String = obj.get("id", "")
		var status: String = obj.get("status", "in_progress")
		if status == "complete" or status == "failed":
			if obj_id in _marker_instances:
				_marker_instances[obj_id].queue_free()
				_marker_instances.erase(obj_id)
			continue
		if obj_id in _marker_instances:
			_marker_instances[obj_id].update_objective(obj)


func _on_command_sent(cmd: Dictionary) -> void:
	var kind: String = cmd.get("kind", "")
	if kind != "move" and kind != "attack_move":
		return
	var target: Dictionary = cmd.get("target", {})
	var pos: Array = target.get("pos", [])
	if pos.size() < 2:
		return
	var layer_y: float = float(target.get("layer", 0)) * EraConfig.LAYER_HEIGHT
	var world_pos := Vector3(float(pos[0]), layer_y, float(pos[1]))
	var indicator: Node3D = preload("res://scenes/tactical/command_indicator.gd").new()
	indicator.setup(world_pos, kind == "attack_move")
	_command_indicators.add_child(indicator)


func qa_state() -> Dictionary:
	return {
		"scene": "tactical",
		"tick": TacticalBridge.current_tick,
		"unit_count": TacticalBridge.unit_count,
		"plants": [],
	}

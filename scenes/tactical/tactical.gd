## Tactical scene root: camera pan/zoom and performance metrics overlay.
## Connects to TacticalBridge and passes connection state to child renderers.
extends Node2D

# Camera tuning (world units per second at zoom 1.0; scales with zoom level)
const PAN_SPEED    := 1500.0
const ZOOM_STEP    := 0.1
const ZOOM_MIN     := 0.05
const ZOOM_MAX     := 3.0

@onready var _camera: Camera2D    = $Camera2D
@onready var _perf_label: Label   = $DebugLayer/PerfLabel

# Performance ring buffer (frame times in ms, last 300 frames ≈ 5 s at 60 fps)
const _PERF_WINDOW := 300
var _frame_times: Array[float] = []
var _dropped_frames: int = 0
var _frame_counter: int = 0


func _ready() -> void:
	TacticalBridge.connect_to_engine("127.0.0.1", 8765)
	TacticalBridge.connection_state_changed.connect(_on_conn_state)


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
	# Pan — WASD or arrow keys; speed scales inversely with zoom so feel stays constant
	var pan_speed: float = PAN_SPEED / _camera.zoom.x
	var pan := Vector2.ZERO
	if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT):
		pan.x -= 1.0
	if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT):
		pan.x += 1.0
	if Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP):
		pan.y -= 1.0
	if Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN):
		pan.y += 1.0
	if pan != Vector2.ZERO:
		_camera.position += pan.normalized() * pan_speed * delta


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
		_zoom_by(-pg.delta.y * 0.005)


func _zoom_by(amount: float) -> void:
	var new_zoom: float = clampf(_camera.zoom.x + amount, ZOOM_MIN, ZOOM_MAX)
	_camera.zoom = Vector2(new_zoom, new_zoom)


func _record_frame(delta: float) -> void:
	var ms: float = delta * 1000.0
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
	var n: int = sorted.size()
	var p50: float = sorted[n * 50 / 100]
	var p95: float = sorted[n * 95 / 100]
	var p99: float = sorted[n * 99 / 100]
	var unit_count: int = TacticalBridge.units.size()
	var tick: int = TacticalBridge.current_tick

	_perf_label.text = (
		"tick %d   units %d   zoom %.2f\n" % [tick, unit_count, _camera.zoom.x] +
		"frame  p50 %.1fms  p95 %.1fms  p99 %.1fms\n" % [p50, p95, p99] +
		"dropped frames (>16.7ms): %d" % _dropped_frames
	)

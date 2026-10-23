extends Node2D

# S-138 share: drifting haze and slow flyby ships over the field. Pure decoration, reads the frame, never writes it.
# Legacy reference: ambient_density_manager.gd (haze), flyby_ship_pool.gd (flyby). Counts and timings are named drafts.

const SCREEN_CENTER := Vector2(960.0, 540.0)
const DEFAULT_CANVAS := Vector2(4000.0, 4000.0)
const HAZE_COUNT := 24
const HAZE_RADIUS_MIN := 300.0
const HAZE_RADIUS_MAX := 900.0
const HAZE_SPEED := 10.0
const HAZE_COLOR := Color(0.3, 0.35, 0.5, 0.05)
const FLYBY_MAX := 4
const FLYBY_INTERVAL := 12.0
const FLYBY_SPEED := 200.0
const FLYBY_MARGIN := 300.0
const FLYBY_SIZE := 40.0
const FLYBY_COLOR := Color(0.5, 0.6, 0.9, 0.5)
const SEED := 1138

var _canvas := DEFAULT_CANVAS
var _scale := 1.0
var _camera := Vector2.ZERO
var _haze: Array = []
var _flybys: Array = []
var _timer := 0.0
var _rng := RandomNumberGenerator.new()
var _projector := Callable()


func _ready() -> void:
	name = "Ambient"
	_rng.seed = SEED


func set_projector(projector: Callable) -> void:
	_projector = projector


func has_projector() -> bool:
	return _projector.is_valid()


func set_frame(frame: Dictionary, _local_faction: int, world_scale: float, camera: Vector2) -> void:
	_scale = world_scale
	_camera = camera
	var canvas = frame.get("map", {}).get("canvas")
	if canvas is Array and canvas.size() >= 2:
		_canvas = Vector2(float(canvas[0]), float(canvas[1]))
	if _haze.is_empty():
		_seed_haze()
	queue_redraw()


func advance(dt_s: float) -> void:
	for h in _haze:
		h["p"] += Vector2(1.0, 0.3).normalized() * HAZE_SPEED * dt_s
		h["p"].x = fposmod(h["p"].x, _canvas.x)
		h["p"].y = fposmod(h["p"].y, _canvas.y)
	_timer += dt_s
	if _timer >= FLYBY_INTERVAL:
		_timer = 0.0
		_spawn_flyby()
	var i := 0
	while i < _flybys.size():
		var s: Dictionary = _flybys[i]
		s["t"] += dt_s / s["dur"]
		if s["t"] >= 1.0:
			_flybys.remove_at(i)
		else:
			i += 1
	queue_redraw()


func haze_count() -> int:
	return _haze.size()


func flyby_count() -> int:
	return _flybys.size()


func _seed_haze() -> void:
	for i in HAZE_COUNT:
		_haze.append({"p": Vector2(_rng.randf() * _canvas.x, _rng.randf() * _canvas.y),
			"r": _rng.randf_range(HAZE_RADIUS_MIN, HAZE_RADIUS_MAX)})


func _spawn_flyby() -> void:
	if _flybys.size() >= FLYBY_MAX:
		return
	var y := _rng.randf() * _canvas.y
	var from := Vector2(-FLYBY_MARGIN, y)
	var to := Vector2(_canvas.x + FLYBY_MARGIN, _canvas.y - y)
	if _rng.randf() < 0.5:
		var tmp := from
		from = to
		to = tmp
	_flybys.append({"a": from, "b": to, "t": 0.0, "dur": from.distance_to(to) / FLYBY_SPEED})


func _scr(w: Vector2) -> Vector2:
	if _projector.is_valid():
		return _projector.call(w)
	return (w - _camera) * _scale + SCREEN_CENTER


func _draw() -> void:
	for h in _haze:
		draw_circle(_scr(h["p"]), float(h["r"]) * _scale, HAZE_COLOR)
	for s in _flybys:
		var p: Vector2 = _scr(s["a"].lerp(s["b"], s["t"]))
		var dir: Vector2 = (s["b"] - s["a"]).normalized()
		var side := Vector2(-dir.y, dir.x)
		var sz := FLYBY_SIZE * _scale
		draw_colored_polygon(PackedVector2Array([p + dir * sz, p - dir * sz * 0.6 + side * sz * 0.5, p - dir * sz * 0.6 - side * sz * 0.5]), FLYBY_COLOR)

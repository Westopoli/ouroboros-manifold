extends Node

# VG-A A11: pan, edge scroll, wheel zoom to the map band, initial framing (R-103-01/02, S-234).
# Zoom is the scale in screen px per world unit. Constants are the placeholders of tactical_view.gd
# (Q-103-04 gives the bible no numbers): see ZOOM_MAX, ZOOM_STEP, PAN_SPEED_PX, pad there.
const EDGE_ZONE_PX := 60.0
const PAN_SPEED_PX := 600.0
const ZOOM_MAX_FACTOR := 4.0
const ZOOM_STEP := 1.25
const FRAME_PAD_PX := 12.0

var _canvas := 0.0
var _viewport := Vector2(1920, 1080)
var _scale := 1.0
var _centre := Vector2.ZERO


func setup(canvas: float, viewport: Vector2) -> void:
	_canvas = canvas
	_viewport = viewport
	_scale = zoom_min()
	_centre = Vector2(canvas, canvas) * 0.5


func zoom_min() -> float:
	if _canvas <= 0.0:
		return 1.0
	return maxf(_viewport.x, _viewport.y) / _canvas


func zoom_to(z: float) -> void:
	_scale = clampf(z, zoom_min(), zoom_min() * ZOOM_MAX_FACTOR)
	_clamp()


func wheel(direction: int) -> void:
	zoom_to(_scale * (ZOOM_STEP if direction > 0 else 1.0 / ZOOM_STEP))


func pan(delta_world: Vector2) -> void:
	_centre += delta_world
	_clamp()


func pan_keys(dir: Vector2, dt_s: float) -> void:
	if dir != Vector2.ZERO:
		pan(dir.normalized() * PAN_SPEED_PX * _pan_speed() * dt_s / _scale)


func edge_scroll(mouse: Vector2, dt_s: float) -> void:
	var dir := Vector2.ZERO
	if mouse.x <= EDGE_ZONE_PX:
		dir.x -= 1.0
	elif mouse.x >= _viewport.x - EDGE_ZONE_PX:
		dir.x += 1.0
	if mouse.y <= EDGE_ZONE_PX:
		dir.y -= 1.0
	elif mouse.y >= _viewport.y - EDGE_ZONE_PX:
		dir.y += 1.0
	pan_keys(dir, dt_s)


func frame_units(world_positions: Array) -> void:
	if world_positions.is_empty():
		return
	var lo := Vector2(INF, INF)
	var hi := Vector2(-INF, -INF)
	for p in world_positions:
		lo = lo.min(p)
		hi = hi.max(p)
	var pad := FRAME_PAD_PX / _scale
	lo -= Vector2(pad, pad)
	hi += Vector2(pad, pad)
	var need := minf(_viewport.x / maxf(hi.x - lo.x, 1.0), _viewport.y / maxf(hi.y - lo.y, 1.0))
	if need < _scale:
		zoom_to(need)
	_centre = (lo + hi) * 0.5
	_clamp()


func view_rect() -> Rect2:
	var size := _viewport / _scale
	return Rect2(_centre - size * 0.5, size)


func centre() -> Vector2:
	return _centre


func _clamp() -> void:
	var half := _viewport / _scale * 0.5
	for a in 2:
		_centre[a] = clampf(_centre[a], half[a], maxf(_canvas - half[a], half[a]))


func _pan_speed() -> float:
	var bus := get_node_or_null("/root/UIDataBus")
	return 1.0 if bus == null else clampf(float(bus.get_settings().get("pan_speed", 1.0)), 0.5, 2.0)

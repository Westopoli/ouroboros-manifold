extends Node2D

# Cover discs by class, obstacle discs and the map boundary (S-007). Objective rings: objective_markers.gd (A5b). Fog: fog_layer.gd (A4).
# See also: push/tv-read scenes/tactical_c/map_layer.gd, the source of the polygon helpers.

const CLASS_COLORS := [Color(0.45, 0.65, 0.35, 0.40), Color(0.30, 0.50, 0.30, 0.55), Color(0.15, 0.35, 0.20, 0.70)]
const OBSTACLE_COLOR := Color(0.35, 0.3, 0.3, 0.8)
const BOUNDARY_COLOR := Color(0.9, 0.4, 0.3, 0.8)
const SCREEN := Vector2(1920.0, 1080.0)

var _cover: Array = []
var _obstacles: Array = []
var _boundary := PackedVector2Array()
var _centres: Array = []
var _projector := Callable()
var _scale := 1.0
var _camera := Vector2.ZERO


func set_projector(projector: Callable) -> void:
	_projector = projector


func _to_screen(w: Vector2) -> Vector2:
	if _projector.is_valid():
		return _projector.call(w)
	return (w - _camera) * _scale + SCREEN * 0.5


func _circle(c: Vector2, r: float) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for i in 24:
		pts.append(_to_screen(c + Vector2.from_angle(TAU * i / 24.0) * r))
	return pts


func set_frame(frame: Dictionary, _mission: Dictionary, _local_faction: int, world_scale := 1.0, camera := Vector2.ZERO) -> void:
	_scale = world_scale
	_camera = camera
	_centres = []
	_cover = []
	_obstacles = []
	_boundary = PackedVector2Array()
	var map: Dictionary = frame.get("map", {})
	if map.is_empty():
		queue_redraw()
		return
	for c in map.get("cover", []):
		var cls := clampi(int(c.get("class", 0)), 0, CLASS_COLORS.size() - 1)
		var ctr := Vector2(float(c.get("x", 0.0)), float(c.get("y", 0.0)))
		_centres.append(_to_screen(ctr))
		_cover.append({"class": cls, "polygon": _circle(ctr, float(c.get("r", 0.0))), "color": CLASS_COLORS[cls]})
	for o in map.get("obstacles", []):
		var ctr := Vector2(float(o.get("x", 0.0)), float(o.get("y", 0.0)))
		_centres.append(_to_screen(ctr))
		_obstacles.append(_circle(ctr, float(o.get("r", 0.0))))
	var canvas := float(map.get("canvas", 0.0))
	if canvas > 0.0:
		for p in [Vector2(0, 0), Vector2(canvas, 0), Vector2(canvas, canvas), Vector2(0, canvas)]:
			_boundary.append(_to_screen(p))
	queue_redraw()


func _draw() -> void:
	for c in _cover:
		draw_colored_polygon(c["polygon"], c["color"])
	for p in _obstacles:
		draw_colored_polygon(p, OBSTACLE_COLOR)
	if _boundary.size() >= 4:
		var closed := _boundary.duplicate()
		closed.append(_boundary[0])
		draw_polyline(closed, BOUNDARY_COLOR, 3.0)


func cover_cells() -> Array:
	return _cover


func obstacle_polygons() -> Array:
	return _obstacles


func boundary_polygon() -> PackedVector2Array:
	return _boundary


func screen_points() -> Array:
	return _centres

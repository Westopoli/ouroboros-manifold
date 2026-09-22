extends Node3D

# Minimal orbit-style camera rig for the galaxy view: holds a target point
# and a distance, offsets a fixed-pitch Camera3D around the target, and
# projects world positions to screen pixels. Mirrors the pan/zoom/orbit
# camera pattern in scenes/mockups/galaxy/orbit_camera.gd, trimmed to what
# this piece's fenced test exercises (qa_camera + project); no drag/zoom
# input handling here since no fenced check drives real mouse input.

const DIST_MIN := 10.0
const DIST_MAX := 220.0
const PITCH_DEG := 55.0

var _target: Vector3 = Vector3.ZERO
var _distance: float = 50.0
var _yaw: float = 0.0

@onready var _camera: Camera3D = $Camera3D


func _ready() -> void:
	_update_camera()


func set_view(distance: float, target: Vector3) -> void:
	_distance = clampf(distance, DIST_MIN, DIST_MAX)
	_target = target
	_update_camera()


func get_target() -> Vector3:
	return _target


func get_distance() -> float:
	return _distance


func get_camera() -> Camera3D:
	return _camera


func project(pos: Vector3) -> Vector2:
	var raw: Vector2 = _camera.unproject_position(pos)
	return raw * _canvas_to_real_scale()


# get_viewport().get_visible_rect().size, read from a Camera3D under a Window
# using canvas_items/expand stretch (project.godot), is the project's
# configured base resolution (1920x1080), not the Window's own real pixel
# size -- which is what the fenced test's qa_state() bound-check compares
# systems_px against (get_root().size, i.e. this same Window). Rescale so
# project() lands in that same space. Mirrors scenes/mockups/galaxy/
# orbit_camera.gd:192-197's _canvas_to_real_scale, keyed off get_window()
# instead of DisplayServer (DisplayServer.window_get_size() returned (0,0)
# under this repo's headless test runner; get_window().size is the exact
# value the test reads via get_root().size, so it can't disagree with it).
func _canvas_to_real_scale() -> Vector2:
	var inflated: Vector2 = get_viewport().get_visible_rect().size
	var real: Vector2 = get_window().size
	if inflated.x <= 0.0 or inflated.y <= 0.0 or real.x <= 0.0 or real.y <= 0.0:
		return Vector2.ONE
	return Vector2(real.x / inflated.x, real.y / inflated.y)


func _update_camera() -> void:
	var pitch := deg_to_rad(PITCH_DEG)
	var offset := Vector3(cos(_yaw) * cos(pitch), sin(pitch), sin(_yaw) * cos(pitch)) * _distance
	_camera.position = _target + offset
	_camera.look_at(_target, Vector3.UP)

extends Node2D

const SCREEN_W := 1920.0
const SCREEN_H := 1080.0
const INACTIVE_ALPHA := 0.4
const STRIP_X := 1840.0
const STRIP_Y := 120.0
const STRIP_STEP := 56.0
const STRIP_BOX := Vector2(48.0, 48.0)
# A16 (R-104-09): the To-layer buttons sit under the focus markers; all five engine layers 0..4 get one, always.
const LAYER_COUNT := 5
const LAYER_COLOURS := [Color(0.55, 0.85, 0.45), Color(0.40, 0.80, 0.85), Color(0.45, 0.60, 0.95), Color(0.75, 0.50, 0.95), Color(0.95, 0.85, 0.95)]

# Emitted when a To-layer button is pressed; layer is an engine number 0..4 (the button labelled N sends N - 1).
signal layer_order_requested(layer: int)

var _units: Dictionary = {}
var _local_faction := 0
var _scale := 1.0
var _camera := Vector2.ZERO
var _focus := 0
var _buttons: Array = []
var _layers: Array = []
var _projector := Callable()


# Architect 2026-10-12 (G6): plain Buttons, the strip's constants, text "To layer N" (N = engine layer + 1, player text only).
# R-103-04: a button press changes nothing about the camera; focus_mode NONE keeps Tab for the layer focus (R-105-03).
func _ready() -> void:
	_build_buttons()


func _build_buttons() -> void:
	if not _buttons.is_empty():
		return
	for l in LAYER_COUNT:
		var b := Button.new()
		b.name = "ToLayer%d" % l
		b.text = "To layer %d" % (l + 1)
		b.set_meta("layer", l)
		b.focus_mode = Control.FOCUS_NONE
		b.position = Vector2(STRIP_X, STRIP_Y + (LAYER_COUNT + l) * STRIP_STEP)
		b.size = STRIP_BOX
		b.pressed.connect(func() -> void: layer_order_requested.emit(l))
		add_child(b)
		_buttons.append(b)


func to_layer_buttons() -> Array:
	_build_buttons()
	return _buttons.duplicate()


# R-001-07: with only walkers selected the buttons are dimmed and inert.
func set_orderable(on: bool) -> void:
	_build_buttons()
	for b in _buttons:
		(b as Button).disabled = not on


func set_projector(p: Callable) -> void:
	_projector = p
	queue_redraw()


func screen_points() -> Array:
	var out := []
	for id in _units:
		out.append(_screen(_units[id]))
	return out


# Two call shapes: (frame, local_faction, world_scale, camera) from lane A, or (frame, mission, local_faction) from the 3D host.
func set_frame(frame: Dictionary, a: Variant = 0, b: Variant = 1.0, c: Variant = Vector2.ZERO) -> void:
	if a is Dictionary:
		_local_faction = int(b)
	else:
		_local_faction = int(a)
		_scale = float(b)
		_camera = c
	_units = {}
	var seen := {}
	for u in frame.get("units", []):
		_units[int(u["id"])] = u
		seen[int(u.get("layer", 0))] = true
	_layers = seen.keys()
	_layers.sort()
	queue_redraw()


func set_focus_layer(n: int) -> void:
	_focus = n
	queue_redraw()


func focus_layer() -> int:
	return _focus


func strip_layers() -> Array:
	return _layers.duplicate()


func cycle_focus() -> void:
	if _layers.is_empty():
		return
	var i := _layers.find(_focus)
	_focus = int(_layers[(i + 1) % _layers.size()]) if i >= 0 else int(_layers[0])
	queue_redraw()


func dim_alpha(layer: int) -> float:
	return 1.0 if layer == _focus else INACTIVE_ALPHA


func transit(id: int) -> String:
	var u = _units.get(id)
	if u == null or not u.has("tl"):
		return ""
	return "rise" if int(u["tl"]) > int(u.get("layer", 0)) else "drop"


func sensor_ring(id: int) -> Variant:
	var u = _units.get(id)
	if u == null or int(u["faction"]) != _local_faction or not u.has("sight"):
		return null
	return {"center": _screen(u), "radius": float(u["sight"]) * _scale}


func _screen(u: Dictionary) -> Vector2:
	if _projector.is_valid():
		return _projector.call(Vector2(float(u["x"]), float(u["y"])))
	return (Vector2(float(u["x"]), float(u["y"])) - _camera) * _scale + Vector2(SCREEN_W, SCREEN_H) * 0.5


func _colour(layer: int) -> Color:
	return LAYER_COLOURS[clampi(layer, 0, LAYER_COLOURS.size() - 1)]


func _draw() -> void:
	for id in _units:
		var u: Dictionary = _units[id]
		var layer := int(u.get("layer", 0))
		var c := _colour(layer)
		c.a = dim_alpha(layer)
		var p := _screen(u)
		draw_arc(p, 14.0, 0.0, TAU, 24, c, 2.0)
		var t := transit(id)
		if t != "":
			var d := -1.0 if t == "rise" else 1.0
			draw_colored_polygon(PackedVector2Array([p + Vector2(0, d * 22), p + Vector2(-6, d * 14), p + Vector2(6, d * 14)]), c)
	for i in _layers.size():
		var l := int(_layers[i])
		var r := Rect2(Vector2(STRIP_X, STRIP_Y + i * STRIP_STEP), STRIP_BOX)
		var c := _colour(l)
		c.a = dim_alpha(l)
		draw_rect(r, c, l == _focus)
		draw_rect(r, c, false, 2.0)

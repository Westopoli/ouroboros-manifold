extends Node2D

const SCREEN_W := 1920.0
const SCREEN_H := 1080.0
const CELL_WU := 100.0
const TICK_WU := 60.0
const BAND_COLOURS := [Color(0.40, 0.72, 0.42), Color(0.72, 0.80, 0.38), Color(0.90, 0.68, 0.30), Color(0.72, 0.48, 0.30), Color(0.92, 0.90, 0.88)]
const STEEP_COLOUR := Color(0.85, 0.10, 0.85)

var _terrain: Dictionary = {}
var _texture: ImageTexture
var _ticks: Array = []
var _scale := 1.0
var _camera := Vector2.ZERO


func set_terrain(t: Dictionary) -> void:
	_terrain = t
	_texture = null
	_ticks = []
	if not t.is_empty():
		var w := int(t["cells_w"])
		var h := int(t["cells_h"])
		var bands: PackedByteArray = t["bands"]
		var walk: PackedByteArray = t["walkable"]
		var img := Image.create(w, h, false, Image.FORMAT_RGB8)
		for i in w * h:
			var c: Color = BAND_COLOURS[clampi(bands[i], 1, 5) - 1]
			if walk[i] == 0:
				c = c.lerp(STEEP_COLOUR, 0.5)
			img.set_pixel(i % w, i / w, c)
		_texture = ImageTexture.create_from_image(img)
		for s in t.get("slopes", []):
			var d := Vector2(float(s["x1"]) - float(s["x0"]), float(s["y1"]) - float(s["y0"]))
			d = d.normalized() if d.length() > 0.0 else Vector2.RIGHT
			var m := Vector2(float(s["mx"]), float(s["my"]))
			_ticks.append([m - d * TICK_WU * 0.5, m + d * TICK_WU * 0.5])
	queue_redraw()


func ground_texture() -> Texture2D:
	return _texture


func slope_ticks() -> Array:
	return _ticks


func screen_rect(world_scale: float, camera: Vector2) -> Rect2:
	var size := Vector2(int(_terrain.get("cells_w", 0)), int(_terrain.get("cells_h", 0))) * CELL_WU * world_scale
	return Rect2((-camera) * world_scale + Vector2(SCREEN_W, SCREEN_H) * 0.5, size)


func set_view(world_scale: float, camera: Vector2) -> void:
	_scale = world_scale
	_camera = camera
	queue_redraw()


func _draw() -> void:
	if _texture == null:
		return
	draw_texture_rect(_texture, screen_rect(_scale, _camera), false)
	for t in _ticks:
		var a: Vector2 = ((t[0] as Vector2) - _camera) * _scale + Vector2(SCREEN_W, SCREEN_H) * 0.5
		var b: Vector2 = ((t[1] as Vector2) - _camera) * _scale + Vector2(SCREEN_W, SCREEN_H) * 0.5
		draw_line(a, b, Color.WHITE, 2.0)

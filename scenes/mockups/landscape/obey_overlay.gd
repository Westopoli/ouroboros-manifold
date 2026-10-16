extends Control

# Terrain-obeys overlay: requests (pads, choke bar, wall span, vantage, sites), the found routes in two
# colours, the failing clause in red, and the panel. Data comes from obey_layer.gd (layer).

const SMALL_COLOR := Color(1.0, 0.65, 0.15, 0.95)
const BIG_COLOR := Color(0.3, 0.75, 1.0, 0.95)
const FAIL_COLOR := Color(1.0, 0.1, 0.1, 1.0)
const PAD_COLOR := {"base_a": Color(0.4, 0.6, 1.0), "base_b": Color(0.4, 0.6, 1.0), "objective": Color(1.0, 0.9, 0.2), "site_0": Color(0.3, 1.0, 0.9), "site_1": Color(0.3, 1.0, 0.9)}

var layer
var _panel: PanelContainer
var _label: Label
var _drafts: Label


func _ready() -> void:
	_panel = PanelContainer.new()
	_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_panel.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	_panel.grow_vertical = Control.GROW_DIRECTION_BEGIN
	_panel.position = Vector2(12.0, -12.0)
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.03, 0.04, 0.07, 0.86)
	style.content_margin_left = 8
	style.content_margin_right = 8
	style.content_margin_top = 5
	style.content_margin_bottom = 5
	_panel.add_theme_stylebox_override("panel", style)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 24)
	_label = Label.new()
	_drafts = Label.new()
	for l in [_label, _drafts]:
		l.mouse_filter = Control.MOUSE_FILTER_IGNORE
		l.add_theme_font_size_override("font_size", 12)
		row.add_child(l)
	_panel.add_child(row)
	add_child(_panel)


func set_panel(results: String, drafts: String) -> void:
	if _label != null:
		_label.text = results
		_drafts.text = drafts


func _process(_delta: float) -> void:
	if visible:
		queue_redraw()


func _proj(p: Vector2) -> Vector2:
	var cam: Camera3D = layer._camera_rig.get_camera()
	var c: Vector2i = layer._cell_of(p)
	var h: float = layer.fm.p4.h[c.y * layer.fm.dim + c.x]
	return cam.unproject_position(Vector3(p.x, h, p.y))


func _poly(points: Array, color: Color, width: float, closed: bool) -> void:
	var pts := PackedVector2Array()
	for p in points:
		pts.append(_proj(p))
	if closed:
		pts.append(pts[0])
	draw_polyline(pts, color, width, true)


func _circle(c: Vector2, r: float, color: Color, width: float) -> void:
	var pts: Array = []
	for k in range(48):
		pts.append(c + Vector2.from_angle(TAU * k / 48.0) * r)
	_poly(pts, color, width, true)


func _box(c: Vector2, axis: Vector2, half: Vector2, color: Color, width: float) -> void:
	var perp := axis.orthogonal()
	_poly([c + axis * half.x + perp * half.y, c + axis * half.x - perp * half.y, c - axis * half.x - perp * half.y, c - axis * half.x + perp * half.y], color, width, true)


func _draw() -> void:
	if layer == null or layer.fm == null or layer.res.is_empty() or layer.fm.p4.is_empty():
		return
	var req: Dictionary = layer.req
	var res: Dictionary = layer.res
	var fails: Array = res.fails
	var font := ThemeDB.fallback_font
	for name in layer.POINTS:
		for line in res.paths_big[name]:
			var pts := PackedVector2Array()
			for p in line:
				pts.append(_proj(p))
			if pts.size() > 1:
				draw_polyline(pts, BIG_COLOR, 3.0, true)
	for name in layer.POINTS:
		for line in res.paths_small[name]:
			var pts := PackedVector2Array()
			for p in line:
				pts.append(_proj(p))
			if pts.size() > 1:
				draw_polyline(pts, SMALL_COLOR, 1.5, true)
	for p in req.pads:
		var bad: bool = res.ring[p.name] > layer.WALK_LIMIT_DEG or fails.has("routes:" + p.name)
		_circle(p.pos, p.r, FAIL_COLOR if bad else PAD_COLOR[p.name], 2.5)
		var at := _proj(p.pos)
		draw_string(font, at + Vector2(6, -6), "%s  s%d b%d" % [p.name, res.report.routes_small.get(p.name, 0), res.report.routes_big.get(p.name, 0)] if p.name != "base_a" else "base_a", HORIZONTAL_ALIGNMENT_LEFT, -1, 13, FAIL_COLOR if bad else Color.WHITE)
	var a: Vector2 = req.pads[0].pos
	var b: Vector2 = req.pads[1].pos
	_poly([a, b], Color(1, 1, 1, 0.35), 1.0, false)
	var choke_bad := fails.has("choke")
	var hw: float = req.choke_w * 0.5
	var half_len: float = req.choke_len * 0.5
	_box(req.choke, req.dir, Vector2(half_len, hw), FAIL_COLOR if choke_bad else Color(0.5, 1.0, 0.2), 3.0)
	var span: float = layer.draft["choke-wall"]
	for side in [1.0, -1.0]:
		_box(req.choke + req.perp * side * (hw + span * 0.5), req.dir, Vector2(half_len, span * 0.5), FAIL_COLOR if choke_bad else Color(1.0, 0.5, 0.1), 1.5)
	draw_string(font, _proj(req.choke) + Vector2(8, 16), "choke asked %d  measured %d" % [int(req.choke_w), int(res.report.choke_measured_wu)], HORIZONTAL_ALIGNMENT_LEFT, -1, 13, FAIL_COLOR if choke_bad else Color(0.7, 1.0, 0.4))
	var v := _proj(req.vantage)
	_circle(req.vantage, layer.draft["vantage-radius"], Color(1.0, 0.4, 0.9), 2.0)
	draw_string(font, v + Vector2(6, -6), "vantage", HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color(1.0, 0.6, 0.95))
	draw_string(font, Vector2(16, 14), "orange = small-width routes, blue = big-width routes, red = failing clause", HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color.WHITE)

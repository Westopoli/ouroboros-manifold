extends Node2D

# Prototype (disposable): walkers and flyers on generated land, top-down 2D. The land mockup is 3D, so
# the ground is drawn here from walker_grid's data (band colours, steep ground shaded), not reused.
# Optional user argument for the QA shots: -- --shot=pass|short|mixed

const Grid := preload("res://scenes/mockups/walkers/walker_grid.gd")
const Units := preload("res://scenes/mockups/walkers/walker_units.gd")
const SEEDS := {KEY_F1: 11, KEY_F2: 12, KEY_F3: 13}
const OPTION_TEXT := {
	"a": "(a) no slowing: time is distance along the ground over speed",
	"b": "(b) uphill slows by grade, half speed at the 35 degree limit",
	"c": "(c) as (b), and downhill is faster by half as much",
}
const VIEW_TEXT := ["steep ground shaded + band colours", "steep ground shaded only", "band colours only", "neither"]
const WATER_COLOUR := Color(0.10, 0.18, 0.40)
const BAND_COLOURS := [Color(0.40, 0.72, 0.42), Color(0.72, 0.80, 0.38), Color(0.90, 0.68, 0.30), Color(0.72, 0.48, 0.30), Color(0.92, 0.90, 0.88)]
const STEEP_COLOUR := Color(0.85, 0.10, 0.85)
const WALKER_COLOUR := Color(1.0, 0.72, 0.1)
const FLYER_COLOUR := Color(0.25, 0.95, 1.0)
const FONT := 24
# provisional (prototype draft, 2026-10-05)
const QA_FRAMES := 6
const HELP := [
	"HELP",
	"Left click or drag: select units",
	"Right click: send the selected units there",
	"1 to 5: set the layer of the selected flyers",
	"G: does a slope slow a walker? (a) (b) (c)",
	"C: flyer blocked by ground: go around / climb over",
	"B: walker speed 40 / 80 / 150",
	"V: ground view: shading, bands, both, neither",
	"F1 F2 F3: land seed 11 / 12 / 13",
	"Arrow keys or middle mouse drag: move view",
	"Mouse wheel: zoom",
	"Squares are walkers, triangles are flyers.",
	"Number by a unit: its layer. Short bar on a route:",
	"where the unit changes layer. Red X: target no route reaches.",
]

var grids := {}
var grid
var units
var seed_value := 11
var option := "a"
var climb := false
var speed_i := 1
var view := 0
var sel: Array = []
var cam: Camera2D
var over: Control
var tex: ImageTexture
var drag_from := Vector2.ZERO
var dragging := false
var panning := false


func _ready() -> void:
	cam = Camera2D.new()
	add_child(cam)
	var layer := CanvasLayer.new()
	add_child(layer)
	over = Control.new()
	over.set_anchors_preset(Control.PRESET_FULL_RECT)
	over.mouse_filter = Control.MOUSE_FILTER_IGNORE
	over.draw.connect(_draw_overlay)
	layer.add_child(over)
	load_seed(11)
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--shot="):
			_shot(a.substr(7))


func load_seed(s: int) -> void:
	seed_value = s
	if not grids.has(s):
		grids[s] = Grid.new(s)
	grid = grids[s]
	units = Units.new(grid)
	sel = []
	_build_texture()
	_fit(Rect2(0, 0, Grid.CANVAS_WU, Grid.CANVAS_WU))
	queue_redraw()


func _fit(r: Rect2) -> void:
	var vp := get_viewport_rect().size
	var z := minf(vp.x / (r.size.x * 1.25), vp.y / (r.size.y * 1.25))
	cam.zoom = Vector2(z, z)
	cam.position = r.get_center()


func _build_texture() -> void:
	var img := Image.create(grid.dim, grid.dim, false, Image.FORMAT_RGB8)
	for i in range(grid.dim * grid.dim):
		var c := Color(0.6, 0.6, 0.6)
		if view == 0 or view == 2:
			c = WATER_COLOUR if grid.land[i] == 0 else BAND_COLOURS[grid.band[i] - 1]
		if (view == 0 or view == 1) and grid.land[i] == 1 and grid.walkable[i] == 0:
			c = c.lerp(STEEP_COLOUR, 0.5)
		img.set_pixel(i % grid.dim, i / grid.dim, c)
	tex = ImageTexture.create_from_image(img)


func _draw() -> void:
	var px := 1.0 / cam.zoom.x
	var h: float = grid.cell * 0.5
	draw_texture_rect(tex, Rect2(-h, -h, grid.dim * grid.cell, grid.dim * grid.cell), false)
	for u in units.units:
		var col := WALKER_COLOUR if u.kind == "w" else FLYER_COLOUR
		var r: Dictionary = u.route
		if not r.is_empty():
			draw_polyline(r.points, col, 3.0 * px)
			for c in r.crossings:
				var d := _dir_at(r.points, c.pos)
				var n := Vector2(-d.y, d.x) * 9.0 * px
				draw_line(c.pos - n, c.pos + n, Color.WHITE, 3.0 * px)
			for t in r.transfers:
				draw_circle(t.pos, 6.0 * px, Color.WHITE)
			if not r.reached:
				var e: Vector2 = u.target
				draw_line(e + Vector2(-14, -14) * px, e + Vector2(14, 14) * px, Color.RED, 5.0 * px)
				draw_line(e + Vector2(-14, 14) * px, e + Vector2(14, -14) * px, Color.RED, 5.0 * px)
		var s := 10.0 * px
		if u.kind == "w":
			draw_rect(Rect2(u.pos - Vector2(s, s), Vector2(2 * s, 2 * s)), col)
			draw_rect(Rect2(u.pos - Vector2(s, s), Vector2(2 * s, 2 * s)), Color.BLACK, false, 1.5 * px)
		else:
			var tri := PackedVector2Array([u.pos + Vector2(0, -s * 1.2), u.pos + Vector2(s, s), u.pos + Vector2(-s, s)])
			draw_colored_polygon(tri, col)
			draw_polyline(PackedVector2Array([tri[0], tri[1], tri[2], tri[0]]), Color.BLACK, 1.5 * px)
	for i in sel:
		draw_arc(units.units[i].pos, 17.0 * px, 0, TAU, 20, Color.WHITE, 2.5 * px)


func _dir_at(pts: PackedVector2Array, p: Vector2) -> Vector2:
	var best := Vector2.RIGHT
	var bd := INF
	for i in range(1, pts.size()):
		var q := Geometry2D.get_closest_point_to_segment(p, pts[i - 1], pts[i])
		if q.distance_squared_to(p) < bd:
			bd = q.distance_squared_to(p)
			best = (pts[i] - pts[i - 1]).normalized()
	return best


func _draw_overlay() -> void:
	var xf := get_canvas_transform()
	for u in units.units:
		var sp: Vector2 = xf * u.pos + Vector2(14, -10)
		var t := str(units.layer_of(u))
		over.draw_string_outline(ThemeDB.fallback_font, sp, t, HORIZONTAL_ALIGNMENT_LEFT, -1, FONT - 4, 5, Color.BLACK)
		over.draw_string(ThemeDB.fallback_font, sp, t, HORIZONTAL_ALIGNMENT_LEFT, -1, FONT - 4, Color.WHITE)
	if dragging:
		over.draw_rect(Rect2(drag_from, get_viewport().get_mouse_position() - drag_from).abs(), Color(1, 1, 1, 0.9), false, 2.0)
	var vp := over.size
	_panel(Vector2(vp.x - 10, 10), HELP, true)
	var st := [
		"Seed %d    Walker speed %d    Flyers %s" % [seed_value, Units.WALKER_SPEEDS[speed_i], "climb over when blocked" if climb else "go around when blocked"],
		"Slope: " + OPTION_TEXT[option],
		"View: " + VIEW_TEXT[view],
		"Selected: %d    Flyer layers: %s" % [sel.size(), _layers_text()],
	]
	var lines := st.duplicate()
	lines.append("")
	lines.append_array(_readout_lines())
	_panel(Vector2(10, vp.y - 40 - lines.size() * (FONT + 6)), lines)


func _layers_text() -> String:
	var out := []
	for u in units.units:
		if u.kind == "f":
			out.append(str(u.layer))
	return " ".join(out)


func _readout_lines() -> Array:
	var l: Dictionary = units.last
	if l.is_empty():
		return ["LAST ORDER: none yet. Select units, then right click."]
	var r := "(arrives)" if l.reached else "(stops short)"
	var o := "arrives" if l.other_reached else "stops short"
	return [
		"LAST ORDER: %d unit(s), %s, at pace %d" % [l.count, l.kind, l.pace],
		"Route length %d wu   Time %.1f s   Bands crossed %d   %s" % [l.length, l.seconds, l.bands, r],
		"Same order as a %s (own speed): %.1f s, %d wu, %s" % [l.other_kind, l.other_seconds, l.other_length, o],
	]


func _panel(pos: Vector2, lines: Array, right := false) -> void:
	var w := 0.0
	for t in lines:
		w = maxf(w, ThemeDB.fallback_font.get_string_size(t, HORIZONTAL_ALIGNMENT_LEFT, -1, FONT).x)
	if right:
		pos.x -= w + 20
	over.draw_rect(Rect2(pos, Vector2(w + 20, lines.size() * (FONT + 6) + 14)), Color(0, 0, 0, 0.75))
	for i in range(lines.size()):
		over.draw_string(ThemeDB.fallback_font, pos + Vector2(10, 8 + (i + 1) * (FONT + 6) - 6), lines[i], HORIZONTAL_ALIGNMENT_LEFT, -1, FONT, Color.WHITE)


func _process(dt: float) -> void:
	units.step(dt)
	var pan := Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	cam.position += pan * 1200.0 * dt / cam.zoom.x * 0.1
	queue_redraw()
	over.queue_redraw()


func to_world(screen: Vector2) -> Vector2:
	return get_canvas_transform().affine_inverse() * screen


func select_box(a: Vector2, b: Vector2) -> void:
	sel = units.pick(Rect2(to_world(a), Vector2.ZERO).expand(to_world(b)))


func order_to(world: Vector2) -> void:
	units.order(sel, world, Units.WALKER_SPEEDS[speed_i], option, climb)


func key(k: int) -> void:
	if k >= KEY_1 and k <= KEY_5:
		for i in sel:
			if units.units[i].kind == "f":
				units.units[i].layer = k - KEY_0
	elif k == KEY_G:
		option = {"a": "b", "b": "c", "c": "a"}[option]
	elif k == KEY_C:
		climb = not climb
	elif k == KEY_B:
		speed_i = (speed_i + 1) % 3
	elif k == KEY_V:
		view = (view + 1) % 4
		_build_texture()
	elif SEEDS.has(k):
		load_seed(SEEDS[k])


func _unhandled_input(e: InputEvent) -> void:
	if e is InputEventKey and e.pressed and not e.echo:
		key(e.keycode)
	elif e is InputEventMouseButton:
		if e.button_index == MOUSE_BUTTON_LEFT:
			if e.pressed:
				drag_from = e.position
				dragging = true
			elif dragging:
				dragging = false
				if drag_from.distance_to(e.position) < 6.0:
					var c: Array = units.pick(Rect2(to_world(e.position) - Vector2(1, 1) * 24.0 / cam.zoom.x, Vector2(1, 1) * 48.0 / cam.zoom.x))
					sel = c.slice(0, 1)
				else:
					select_box(drag_from, e.position)
		elif e.button_index == MOUSE_BUTTON_RIGHT and e.pressed:
			order_to(to_world(e.position))
		elif e.button_index == MOUSE_BUTTON_MIDDLE:
			panning = e.pressed
		elif e.pressed and e.button_index == MOUSE_BUTTON_WHEEL_UP:
			cam.zoom *= 1.15
		elif e.pressed and e.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			cam.zoom /= 1.15
	elif e is InputEventMouseMotion and panning:
		cam.position -= e.relative / cam.zoom.x


# QA shots: scripted order through the same functions the mouse uses, then a PNG.
func _shot(name: String) -> void:
	var w: Array = []
	var f: Array = []
	for i in range(units.units.size()):
		(w if units.units[i].kind == "w" else f).append(i)
	var home: Vector2 = units.units[w[0]].pos
	var main: PackedInt32Array = grid.main_cells
	var target := home
	var frac := 1.0
	sel = w
	if name == "pass":
		var best := 0.0
		for k in range(60):
			var t: Vector2 = grid.cell_pos(main[(k * 7919 + 13) % main.size()])
			var r: Dictionary = grid.route_walker(home, t, option)
			var straight := home.distance_to(t)
			if r.bands_crossed >= 3 and straight > 4000.0 and r.length / straight > best:
				best = r.length / straight
				target = t
		frac = 0.5
	elif name == "short":
		var inmain := PackedByteArray()
		inmain.resize(grid.dim * grid.dim)
		for c in main:
			inmain[c] = 1
		var tries := 0
		for c in range(0, grid.dim * grid.dim, 37):
			if grid.walkable[c] == 1 and inmain[c] == 0 and home.distance_to(grid.cell_pos(c)) > 4000.0:
				var r: Dictionary = grid.route_walker(home, grid.cell_pos(c), option)
				tries += 1
				if not r.reached and r.end.distance_to(grid.cell_pos(c)) > 800.0:
					target = grid.cell_pos(c)
					break
				if tries > 40:
					break
	else:
		sel = range(units.units.size())
		for k in range(60):
			var t: Vector2 = grid.cell_pos(main[(k * 7919 + 13) % main.size()])
			if home.distance_to(t) > 5000.0:
				target = t
				break
		frac = 0.4
	order_to(target)
	var longest := 0.0
	var box := Rect2(home, Vector2.ZERO)
	for i in sel:
		longest = maxf(longest, units.units[i].secs)
		for p in units.units[i].route.points:
			box = box.expand(p)
	units.step(longest * frac)
	_fit(box.grow(600.0))
	await get_tree().process_frame
	for i in range(QA_FRAMES):
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var dir := ProjectSettings.globalize_path("res://scenes/mockups/walkers/qa/")
	DirAccess.make_dir_recursive_absolute(dir)
	get_viewport().get_texture().get_image().save_png(dir + "walkers_" + name + ".png")
	print("shot ", name, " ", units.last)
	get_tree().quit()

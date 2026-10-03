extends Node

# Pass 4 prototype UI (spec 2026-10-03-land-mockup-pass4-spec.md): view keys, the X cursor, the
# sliders and the numbers panel. Owns the pass-4 settings; hud.gd reads them when it generates.

const VIEWS := ["visual", "steep30", "steep35", "band", "walk"]
const MIN_RELIEF_RANGE := Vector2(0.0, 6000.0)

var landform: String = "seed"
var min_relief: float = Pass4Terrain.MIN_RELIEF_DEFAULT
var bench_override: float = -1.0
var footprint: float = 300.0
var ramps := true
var detail_scale: float = 1.0
var _fp_table: Dictionary = {}
var view: String = "visual"
var limit: float = 30.0
var unit_selected := false

var _hud
var _camera_rig: Node3D
var _fm: FieldMap
var _generated: Node3D
var _active := false
var _panel: PanelContainer
var _label: Label
var _cursor: Control
var _controls: Array = []
var _landform_button: Button
var _relief_label: Label
var _relief_slider: HSlider
var _bench_button: Button
var _bench_label: Label
var _bench_slider: HSlider
var _unit_button: Button
var _fp_label: Label
var _fp_slider: HSlider
var _ramp_button: Button
var _detail_label: Label
var _detail_slider: HSlider
var _cursor_override := Vector2(-1.0, -1.0)
var _cursor_world := Vector3.ZERO
var _cursor_world_on := false
var _x_pos := Vector2.ZERO
var _x_show := false
var _last_mouse := Vector2(-1.0, -1.0)
var _hover_steep_deg := -1.0


func setup(hud, camera_rig: Node3D, box: VBoxContainer) -> void:
	_hud = hud
	_camera_rig = camera_rig
	_landform_button = Button.new()
	_landform_button.focus_mode = Control.FOCUS_NONE
	_landform_button.pressed.connect(func(): set_landform(Pass4Terrain.LANDFORM_MODES[(Pass4Terrain.LANDFORM_MODES.find(landform) + 1) % Pass4Terrain.LANDFORM_MODES.size()]))
	_relief_label = Label.new()
	_relief_slider = _slider(MIN_RELIEF_RANGE.x, MIN_RELIEF_RANGE.y, 100.0, min_relief)
	_relief_slider.value_changed.connect(func(v): _relief_label.text = "Min relief: %d wu (candidate)" % int(v))
	_relief_slider.drag_ended.connect(func(changed): if changed: _apply_relief(_relief_slider.value))
	_bench_button = Button.new()
	_bench_button.focus_mode = Control.FOCUS_NONE
	_bench_button.pressed.connect(func(): set_bench(-1.0 if bench_override >= 0.0 else _bench_slider.value))
	_bench_label = Label.new()
	_bench_slider = _slider(0.0, 100.0, 5.0, 50.0)
	_bench_slider.value_changed.connect(func(v): _bench_label.text = "Benched share override: %d%%" % int(v))
	_bench_slider.drag_ended.connect(func(changed): if changed and bench_override >= 0.0: set_bench(_bench_slider.value))
	_unit_button = Button.new()
	_unit_button.focus_mode = Control.FOCUS_NONE
	_unit_button.pressed.connect(func(): set_unit_selected(not unit_selected))
	_fp_label = Label.new()
	_fp_slider = _slider(100.0, 600.0, 50.0, footprint)
	_fp_slider.value_changed.connect(func(v): _fp_label.text = "Slope footprint: %d wu (candidate)" % int(v))
	_fp_slider.drag_ended.connect(func(changed): if changed: set_footprint(_fp_slider.value))
	_detail_label = Label.new()
	_detail_slider = _slider(0.0, 3.0, 0.1, detail_scale)
	_detail_slider.value_changed.connect(func(v): _detail_label.text = "Terrain steepness (detail x): %.1f" % v)
	_detail_slider.drag_ended.connect(func(changed): if changed: set_detail_scale(_detail_slider.value))
	_ramp_button = Button.new()
	_ramp_button.focus_mode = Control.FOCUS_NONE
	_ramp_button.pressed.connect(func(): set_ramps(not ramps))
	_controls = [_landform_button, _relief_label, _relief_slider, _bench_button, _bench_label, _bench_slider, _fp_label, _fp_slider, _detail_label, _detail_slider, _ramp_button, _unit_button]
	for c in _controls:
		box.add_child(c)
	_relief_label.text = "Min relief: %d wu (candidate)" % int(min_relief)
	_bench_label.text = "Benched share override: 50%"
	_fp_label.text = "Slope footprint: %d wu (candidate)" % int(footprint)
	_detail_label.text = "Terrain steepness (detail x): %.1f" % detail_scale
	_refresh_buttons()

	_panel = PanelContainer.new()
	_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_panel.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	_panel.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	_panel.position = Vector2(-16.0, 16.0)
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.04, 0.05, 0.08, 0.82)
	style.content_margin_left = 10
	style.content_margin_right = 10
	style.content_margin_top = 8
	style.content_margin_bottom = 8
	_panel.add_theme_stylebox_override("panel", style)
	_label = Label.new()
	_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_label.add_theme_font_size_override("font_size", 15)
	_panel.add_child(_label)
	hud.add_child(_panel)

	_cursor = Control.new()
	_cursor.set_anchors_preset(Control.PRESET_FULL_RECT)
	_cursor.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_cursor.draw.connect(_draw_cursor)
	hud.add_child(_cursor)
	set_process(true)


func _slider(low: float, high: float, step: float, value: float) -> HSlider:
	var s := HSlider.new()
	s.custom_minimum_size = Vector2(160, 0)
	s.min_value = low
	s.max_value = high
	s.step = step
	s.value = value
	return s


func _refresh_buttons() -> void:
	_landform_button.text = "Landform: %s (M)" % landform
	_bench_button.text = "Benched share: %s" % ("override" if bench_override >= 0.0 else "from seed")
	_ramp_button.text = "Ramps: %s (P)" % ("on" if ramps else "off")
	_unit_button.text = "Unit selected: %s (U)" % ("on" if unit_selected else "off")


func _apply_relief(v: float) -> void:
	min_relief = v
	_hud.p4_regenerate()


func set_landform(mode: String) -> void:
	if not Pass4Terrain.LANDFORM_MODES.has(mode):
		return
	landform = mode
	_refresh_buttons()
	_hud.p4_regenerate()


func set_min_relief(v: float) -> void:
	min_relief = clampf(v, MIN_RELIEF_RANGE.x, MIN_RELIEF_RANGE.y)
	_relief_slider.set_value_no_signal(min_relief)
	_relief_label.text = "Min relief: %d wu (candidate)" % int(min_relief)
	_hud.p4_regenerate()


func set_bench(pct: float) -> void:
	bench_override = pct
	if pct >= 0.0:
		_bench_slider.set_value_no_signal(pct)
		_bench_label.text = "Benched share override: %d%%" % int(pct)
	_refresh_buttons()
	_hud.p4_regenerate()


func set_footprint(v: float) -> void:
	footprint = clampf(v, 100.0, 600.0)
	_fp_slider.set_value_no_signal(footprint)
	_fp_label.text = "Slope footprint: %d wu (candidate)" % int(footprint)
	_hud.p4_regenerate()


func set_detail_scale(v: float) -> void:
	detail_scale = clampf(v, 0.0, 3.0)
	_detail_slider.set_value_no_signal(detail_scale)
	_detail_label.text = "Terrain steepness (detail x): %.1f" % detail_scale
	_hud.p4_regenerate()


func set_ramps(on: bool) -> void:
	ramps = on
	_refresh_buttons()
	_hud.p4_regenerate()


func set_unit_selected(on: bool) -> void:
	unit_selected = on
	_refresh_buttons()
	_refresh_panel()


func set_limit(deg: float) -> void:
	limit = 35.0 if deg >= 32.5 else 30.0
	_apply_view()
	_refresh_panel()


func set_view(v: String) -> void:
	if not VIEWS.has(v):
		return
	view = v
	if v == "steep30":
		limit = 30.0
	elif v == "steep35":
		limit = 35.0
	_apply_view()
	_refresh_panel()


func handle_key(keycode: int) -> bool:
	if not _active:
		return false
	match keycode:
		KEY_T:
			set_view("steep30" if view != "steep30" and view != "steep35" else ("steep35" if view == "steep30" else "visual"))
		KEY_B:
			set_view("visual" if view == "band" else "band")
		KEY_G:
			set_view("visual" if view == "walk" else "walk")
		KEY_L:
			set_limit(35.0 if limit < 32.5 else 30.0)
		KEY_P:
			set_ramps(not ramps)
		KEY_U:
			set_unit_selected(not unit_selected)
		KEY_M:
			set_landform(Pass4Terrain.LANDFORM_MODES[(Pass4Terrain.LANDFORM_MODES.find(landform) + 1) % Pass4Terrain.LANDFORM_MODES.size()])
		_:
			return false
	return true


func on_regenerated(fm: FieldMap, generated: Node3D, is_space: bool) -> void:
	_fm = fm
	_generated = generated
	_active = not is_space
	for c in _controls:
		c.visible = _active
	_panel.visible = _active
	_cursor.visible = _active
	if not _active:
		return
	fm.p4 = Pass4Terrain.analyse(fm)
	_apply_view()
	_refresh_panel()


func _apply_view() -> void:
	if not _active or _generated == null or _fm == null or _fm.p4.is_empty():
		return
	var old := _generated.get_node_or_null("P4Overlay")
	if old != null:
		_generated.remove_child(old)
		old.free()
	var shown := view != "visual"
	for child in _generated.get_children():
		if child.name == "GroundMesh":
			child.visible = not shown
		elif child is Node3D:
			child.visible = not shown
	if shown:
		var colors := Pass4Terrain.cell_colors(_fm, view, limit)
		_generated.add_child(Pass4Terrain.build_overlay(_fm, colors))


func _refresh_panel() -> void:
	if not _active or _fm == null or _fm.p4.is_empty():
		return
	var m: Dictionary = _fm.p4.metrics
	var steep: Dictionary = m.steep_pct
	var w: Dictionary = m.walk[str(limit)]
	var floors: Array = m.band_floor_wu
	var shares: Array = m.layer_share_pct
	var lf: Array = m.landforms
	var floors_s := " | ".join(range(5).map(func(i): return "L%d %d" % [i + 1, int(round(floors[i]))]))
	var shares_s := " / ".join(shares.map(func(v): return "%.0f" % v))
	var view_note: String = {
		"visual": "normal ground",
		"steep30": "red = over 30: blocked, the walk flood cannot enter",
		"steep35": "red = over 35: blocked; orange = 30 to 35, open at 35 only",
		"band": "ground by layer 1 (green) to 5 (white)",
		"walk": "green reachable, gold ramp, magenta cut off, cyan/black peaks, white core",
	}[view]
	_label.text = "PASS 4   view: %s   (%s)\n" % [view, view_note] \
		+ "Relief %d wu  (lowest %d, highest %d)  minimum asked %d wu%s\n" % [int(m.relief_wu), int(m.lowest_wu), int(m.highest_wu), int(m.min_relief_wu), "  (stretched x%.2f)" % m.relief_scale if m.relief_scale > 1.0001 else ""] \
		+ "Layer floors (wu): %s   step %d wu\n" % [floors_s, int(round(m.step_wu))] \
		+ "Land on layers 1..5: %s %%\n" % shares_s \
		+ "Slope footprint %d wu   terrain steepness x%.1f\n" % [int(m.footprint_wu), m.detail_scale] \
		+ "Too steep (share of land): over 30 = %.1f%%   32.5 = %.1f%%   35 = %.1f%%\n" % [steep["30.0"], steep["32.5"], steep["35.0"]] \
		+ "Benched ground: %.0f%% (%s)   Landforms: %s\n" % [m.bench_share_pct, "from seed" if m.bench_from_seed else "override", ", ".join(lf) if not lf.is_empty() else "none"] \
		+ "Ramps %s: %d cut (%d cells, gold) for layers %s\n" % ["on" if m.ramps_on else "off", m.ramps, m.ramp_cells, str(m.ramp_bands)] \
		+ "Walk, limit %d deg: %.1f%% of land reachable, %d of 5 layers, peaks %d of %d reachable (%.0f%%)\n" % [int(limit), w.reach_pct, w.layers_reachable, w.peaks_reachable, w.peaks, w.peaks_reachable_pct] \
		+ "Variety: %.2f of %.2f bits (layer x biome spread)\n" % [m.variety_bits, m.variety_max_bits] \
		+ "Unit selected: %s   hover steep: %s\n" % ["on" if unit_selected else "off", "%d deg" % int(_hover_steep_deg) if _hover_steep_deg >= 0.0 else "-"] \
		+ "Keys: T steep 30/35/off  B bands  G walk  L limit  P ramps  U unit  M landform  R regen"


func _process(_delta: float) -> void:
	if not _active or _fm == null or _fm.p4.is_empty():
		return
	var shown_before := _x_show
	var pos_before := _x_pos
	_x_show = false
	_hover_steep_deg = -1.0
	if _cursor_world_on:
		_cursor_override = _camera_rig.get_camera().unproject_position(Vector3(_cursor_world.x, _camera_rig.position.y, _cursor_world.z))
	if unit_selected:
		var mouse: Vector2 = _cursor_override if _cursor_override.x >= 0.0 else get_viewport().get_mouse_position()
		var hit = _pick(mouse)
		if hit != null:
			var gx := clampi(int(round(hit.x / FieldMap.SPACING)), 0, _fm.dim - 1)
			var gy := clampi(int(round(hit.z / FieldMap.SPACING)), 0, _fm.dim - 1)
			var q := gy * _fm.dim + gx
			if _fm.p4.land[q] == 1:
				var tn: float = _fm.p4.tan[q]
				_hover_steep_deg = rad_to_deg(atan(tn))
				if tn > tan(deg_to_rad(limit)):
					_x_show = true
					_x_pos = mouse
	if _x_show != shown_before or _x_pos != pos_before:
		_cursor.queue_redraw()
		_refresh_panel()


func _draw_cursor() -> void:
	if not _x_show:
		return
	var r := 12.0
	for pair in [[Color.WHITE, 9.0], [Color(0.9, 0.05, 0.05), 5.0]]:
		_cursor.draw_line(_x_pos + Vector2(-r, -r), _x_pos + Vector2(r, r), pair[0], pair[1], true)
		_cursor.draw_line(_x_pos + Vector2(-r, r), _x_pos + Vector2(r, -r), pair[0], pair[1], true)


func _height_at(x: float, z: float) -> float:
	var h: PackedFloat32Array = _fm.p4.h
	var dim := _fm.dim
	var fx := clampf(x / FieldMap.SPACING, 0.0, dim - 1.001)
	var fz := clampf(z / FieldMap.SPACING, 0.0, dim - 1.001)
	var gx := int(fx)
	var gz := int(fz)
	var tx := fx - gx
	var tz := fz - gz
	var i := gz * dim + gx
	return lerpf(lerpf(h[i], h[i + 1], tx), lerpf(h[i + dim], h[i + dim + 1], tx), tz)


func _pick(screen: Vector2) -> Variant:
	var cam: Camera3D = _camera_rig.get_camera()
	var o := cam.project_ray_origin(screen)
	var d := cam.project_ray_normal(screen)
	var canvas := _fm.canvas
	var t := 0.0
	var step := 60.0
	while t < 80000.0:
		var p := o + d * t
		if p.x >= 0.0 and p.z >= 0.0 and p.x <= canvas and p.z <= canvas and p.y <= _height_at(p.x, p.z):
			var a := maxf(t - step, 0.0)
			var b := t
			for k in range(10):
				var m := (a + b) * 0.5
				var pm := o + d * m
				if pm.y <= _height_at(pm.x, pm.z):
					b = m
				else:
					a = m
			return o + d * b
		if p.y > 6500.0 and d.y >= 0.0:
			return null
		t += step
	return null


# QA: a blocked cell near the core with open ground beside it, camera aimed at it.
func qa_look_steep(height: float) -> Array:
	if _fm == null or _fm.p4.is_empty():
		return []
	var dim := _fm.dim
	var core: int = _fm.p4.metrics.core_cell
	var cx := core % dim
	var cy := core / dim
	var tl := tan(deg_to_rad(limit))
	var best := -1
	var best_d := INF
	for i in range(dim * dim):
		if _fm.p4.land[i] == 1 and _fm.p4.tan[i] > tl:
			var gx := i % dim
			var gy := i / dim
			var d := Vector2(gx - cx, gy - cy).length()
			if d > 12.0 and d < best_d and _edge_cell(gx, gy, tl):
				best = i
				best_d = d
	if best < 0:
		return []
	var wx := (best % dim) * FieldMap.SPACING
	var wz := (best / dim) * FieldMap.SPACING
	_camera_rig.pan_to(Vector3(wx, 0.0, wz))
	_camera_rig.set_height(height)
	qa_cursor_world(wx, wz)
	return [wx, wz]


# Blocked cell in a 5 by 5 block that is about half open dry ground: a real edge.
func _edge_cell(gx: int, gy: int, tl: float) -> bool:
	var dim := _fm.dim
	var open := 0
	for oy in range(-2, 3):
		for ox in range(-2, 3):
			var x := gx + ox
			var y := gy + oy
			if x < 0 or y < 0 or x >= dim or y >= dim or _fm.p4.land[y * dim + x] == 0:
				return false
			if _fm.p4.tan[y * dim + x] <= tl:
				open += 1
	return open >= 10 and open <= 16


func qa_footprint_table() -> void:
	if _fm != null and not _fm.p4.is_empty():
		_fp_table = Pass4Terrain.footprint_table(_fm, [100.0, 300.0, 500.0])


func qa_cursor_world(x: float, z: float) -> void:
	_cursor_world = Vector3(x, _height_at(x, z), z)
	_cursor_world_on = true


func qa_cursor_clear() -> void:
	_cursor_world_on = false
	_cursor_override = Vector2(-1.0, -1.0)


func get_state() -> Dictionary:
	if _fm == null or _fm.p4.is_empty():
		return {}
	var d: Dictionary = _fm.p4.metrics.duplicate(true)
	d["view"] = view
	d["limit"] = limit
	d["unit_selected"] = unit_selected
	d["landform_mode"] = landform
	d["x_cursor_shown"] = _x_show
	d["x_cursor_px"] = [_x_pos.x, _x_pos.y]
	d["footprint_table"] = _fp_table
	d["hover_steep_deg"] = _hover_steep_deg
	return d

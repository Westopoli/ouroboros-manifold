extends Node

# Pass 5 prototype UI: layout picker, reaction toggle, the changed-ground / walk / heat views, the
# 3D graph and place markers, the checks panel. Settings are read by hud.gd when it generates.

const VIEWS := ["react", "p5walk", "heat"]
const MODES := ["off", "seed", "1", "2", "3", "4", "5", "6", "7", "8"]
const TYPE_COLOR := {"staging": Color(0.25, 0.5, 1.0), "spawn_point": Color(1.0, 0.25, 0.25), "objective": Color(1.0, 0.85, 0.1), "chokepoint": Color(1.0, 0.5, 0.05), "vantage": Color(0.9, 0.9, 0.95), "flank_route": Color(0.95, 0.6, 0.9), "transit": Color(0.7, 0.7, 0.7), "hazard_zone_anchor": Color(0.7, 0.15, 0.7), "reinforcement_structure": Color(0.55, 0.85, 0.55), "extraction": Color(0.3, 0.9, 0.9)}
const EDGE_COLOR := {"path": Color(1, 1, 1), "flank": Color(1.0, 0.6, 0.1), "restricted": Color(1.0, 0.2, 0.9)}
const CAT_COLOR := {1: Color(1.0, 0.9, 0.2), 2: Color(1.0, 0.5, 0.05), 3: Color(0.1, 0.9, 1.0), 4: Color(0.5, 1.0, 0.2), 5: Color(0.65, 0.1, 0.1), 6: Color(1.0, 0.4, 0.8)}
const CAT_NAME := {1: "pad", 2: "graded route", 3: "bridge", 4: "choke corridor", 5: "choke wall", 6: "vantage ground"}
const HEAT := [Color(0.1, 0.02, 0.25), Color(0.25, 0.2, 0.6), Color(0.1, 0.6, 0.6), Color(0.55, 0.85, 0.2), Color(1.0, 0.95, 0.2)]

var mode := "seed"
var react_on := true
var show_graph := true
var show_places := true
var narrow := 300.0
var moderate := 600.0
var tol_pct := 10.0
var kind := "base"

var _hud
var _p4
var _camera_rig: Node3D
var _fm: FieldMap
var _generated: Node3D
var _active := false
var _box: VBoxContainer
var _mode_btn: Button
var _react_btn: Button
var _graph_btn: Button
var _places_btn: Button
var _heat_btn: Button
var _narrow_label: Label
var _moderate_label: Label
var _tol_label: Label
var _panel: PanelContainer
var _label: Label
var _key: Control


func setup(hud, p4, camera_rig: Node3D) -> void:
	_hud = hud
	_p4 = p4
	_camera_rig = camera_rig
	_box = VBoxContainer.new()
	_box.position = Vector2(340.0, 16.0)
	hud.add_child(_box)
	_mode_btn = _button(func(): set_mode(MODES[(MODES.find(mode) + 1) % MODES.size()]))
	_react_btn = _button(func(): set_react(not react_on))
	_graph_btn = _button(func(): set_graph(not show_graph))
	_places_btn = _button(func(): set_places(not show_places))
	_heat_btn = _button(func(): cycle_heat())
	_narrow_label = Label.new()
	var ns := _slider(100.0, 1200.0, 50.0, narrow)
	ns.value_changed.connect(func(v): _narrow_label.text = "Narrow choke: %d wu (candidate)" % int(v))
	ns.drag_ended.connect(func(c): if c: set_widths(ns.value, moderate))
	_moderate_label = Label.new()
	var ms := _slider(200.0, 2000.0, 50.0, moderate)
	ms.value_changed.connect(func(v): _moderate_label.text = "Moderate choke: %d wu (candidate)" % int(v))
	ms.drag_ended.connect(func(c): if c: set_widths(narrow, ms.value))
	_tol_label = Label.new()
	var ts := _slider(2.0, 30.0, 1.0, tol_pct)
	ts.value_changed.connect(func(v): _tol_label.text = "Equal-distance tolerance: %d%% (candidate)" % int(v))
	ts.drag_ended.connect(func(c): if c: set_tol(ts.value))
	for c in [_mode_btn, _react_btn, _graph_btn, _places_btn, _heat_btn, _narrow_label, ns, _moderate_label, ms, _tol_label, ts]:
		_box.add_child(c)
	_refresh_buttons()
	_panel = PanelContainer.new()
	_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_panel.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	_panel.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	_panel.position = Vector2(-16.0, 345.0)
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.04, 0.05, 0.08, 0.84)
	style.content_margin_left = 10
	style.content_margin_right = 10
	style.content_margin_top = 6
	style.content_margin_bottom = 6
	_panel.add_theme_stylebox_override("panel", style)
	_label = Label.new()
	_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_label.add_theme_font_size_override("font_size", 12)
	_label.custom_minimum_size = Vector2(500.0, 0.0)
	_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_panel.add_child(_label)
	hud.add_child(_panel)
	_key = Control.new()
	_key.set_anchors_preset(Control.PRESET_FULL_RECT)
	_key.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_key.draw.connect(_draw_key)
	hud.add_child(_key)


func _button(cb: Callable) -> Button:
	var b := Button.new()
	b.focus_mode = Control.FOCUS_NONE
	b.pressed.connect(cb)
	return b


func _slider(low: float, high: float, step: float, value: float) -> HSlider:
	var s := HSlider.new()
	s.custom_minimum_size = Vector2(190, 0)
	s.min_value = low
	s.max_value = high
	s.step = step
	s.value = value
	return s


func _refresh_buttons() -> void:
	_mode_btn.text = "Layout: %s (Y)" % mode
	_react_btn.text = "Terrain obeys layout: %s (O)" % ("on" if react_on else "off")
	_graph_btn.text = "Layout graph: %s (N)" % ("on" if show_graph else "off")
	_places_btn.text = "Place markers: %s (Z)" % ("on" if show_places else "off")
	_heat_btn.text = "Heat view: %s (H)" % kind
	_narrow_label.text = "Narrow choke: %d wu (candidate)" % int(narrow)
	_moderate_label.text = "Moderate choke: %d wu (candidate)" % int(moderate)
	_tol_label.text = "Equal-distance tolerance: %d%% (candidate)" % int(tol_pct)


# ---------------------------------------------------------------- settings

func layout_for(seed_value: int) -> Variant:
	var all := Pass5Layout.layouts()
	match mode:
		"off":
			return null
		"seed":
			return all[seed_value % all.size()]
		_:
			return all[int(mode) - 1]


func set_mode(m: String) -> void:
	if MODES.has(m):
		mode = m
		_refresh_buttons()
		_hud.p4_regenerate()


func set_react(on: bool) -> void:
	react_on = on
	_refresh_buttons()
	_hud.p4_regenerate()


func set_graph(on: bool) -> void:
	show_graph = on
	_refresh_buttons()
	_apply_visibility()


func set_places(on: bool) -> void:
	show_places = on
	_refresh_buttons()
	_apply_visibility()


func set_widths(n: float, m: float) -> void:
	narrow = n
	moderate = m
	_refresh_buttons()
	_hud.p4_regenerate()


func set_tol(v: float) -> void:
	tol_pct = v
	_refresh_buttons()
	_hud.p4_regenerate()


func cycle_heat() -> void:
	if _p4.view == "heat":
		kind = Pass5Places.KINDS[(Pass5Places.KINDS.find(kind) + 1) % Pass5Places.KINDS.size()]
	_refresh_buttons()
	_p4.set_view("heat")
	_key.queue_redraw()


func set_kind(k: String) -> void:
	if Pass5Places.KINDS.has(k):
		kind = k
		_refresh_buttons()
		_key.queue_redraw()
		_p4.refresh_view()


# QA: {"layout": "1", "react": true, "narrow": 300, "moderate": 600, "tol": 10, "graph": true,
# "places": true, "kind": "base", "look_choke": 3500, "regen": false}
func qa_apply(d: Dictionary) -> void:
	if d.has("layout"):
		mode = str(d.layout)
	if d.has("react"):
		react_on = bool(d.react)
	if d.has("narrow"):
		narrow = float(d.narrow)
	if d.has("moderate"):
		moderate = float(d.moderate)
	if d.has("tol"):
		tol_pct = float(d.tol)
	if d.has("graph"):
		show_graph = bool(d.graph)
	if d.has("places"):
		show_places = bool(d.places)
	if d.has("kind"):
		kind = String(d.kind)
	_refresh_buttons()
	if bool(d.get("regen", true)) and (d.has("layout") or d.has("react") or d.has("narrow") or d.has("moderate") or d.has("tol")):
		_hud.p4_regenerate()
	else:
		_apply_visibility()
		_key.queue_redraw()
		_p4.refresh_view()
	if d.has("look_choke"):
		var info: Dictionary = _fm.p5_info if _fm != null else {}
		if info.has("chokes") and not info.chokes.is_empty():
			var ck: Dictionary = info.chokes[int(d.get("choke_index", 0))]
			_camera_rig.pan_to(Vector3(ck.pos.x, 0.0, ck.pos.y))
			_camera_rig.set_height(float(d.look_choke))


func handle_key(keycode: int) -> bool:
	if not _active:
		return false
	match keycode:
		KEY_Y:
			set_mode(MODES[(MODES.find(mode) + 1) % MODES.size()])
		KEY_O:
			set_react(not react_on)
		KEY_N:
			set_graph(not show_graph)
		KEY_Z:
			set_places(not show_places)
		KEY_C:
			_p4.set_view("visual" if _p4.view == "react" else "react")
		KEY_V:
			_p4.set_view("visual" if _p4.view == "p5walk" else "p5walk")
		KEY_H:
			cycle_heat()
		_:
			return false
	return true


# ---------------------------------------------------------------- generation hook

func on_regenerated(fm: FieldMap, generated: Node3D, is_space: bool) -> void:
	_fm = fm
	_generated = generated
	_active = not is_space
	_box.visible = _active
	_panel.visible = _active
	_key.visible = _active
	if not _active:
		return
	if fm.p5_layout == null:
		fm.p5_res = {}
		_label.text = "PASS 5   layout: off   (Y picks a layout)"
		_key.queue_redraw()
		return
	fm.p5_res = Pass5Places.compute(fm, tol_pct / 100.0)
	_build_overlay()
	_refresh_panel()
	_apply_visibility()
	_key.queue_redraw()
	_p4.refresh_view()


func _apply_visibility() -> void:
	if _generated == null:
		return
	var g := _generated.get_node_or_null("P5Graph")
	if g != null:
		g.visible = show_graph
	var p := _generated.get_node_or_null("P5Places")
	if p != null:
		p.visible = show_places
	var r := _generated.get_node_or_null("P5Routes")
	if r != null:
		r.visible = _p4.view == "p5walk"


# ---------------------------------------------------------------- 3D overlay

func _build_overlay() -> void:
	var info: Dictionary = _fm.p5_info
	var res: Dictionary = _fm.p5_res
	var dim := _fm.dim
	var h: PackedFloat32Array = _fm.p4.h
	var by_id := {}
	for nd in info.nodes:
		by_id[nd.id] = nd
	var graph := Node3D.new()
	graph.name = "P5Graph"
	var verts := PackedVector3Array()
	var cols := PackedColorArray()
	for e in info.edges:
		_ribbon(verts, cols, [by_id[e.a].pos, by_id[e.b].pos], h, dim, 130.0, EDGE_COLOR[e.type], 160.0)
	graph.add_child(_mesh(verts, cols))
	for nd in info.nodes:
		var y := _h(h, dim, nd.pos) + 40.0
		graph.add_child(_disc(Vector3(nd.pos.x, y, nd.pos.y), 280.0, TYPE_COLOR.get(nd.type, Color.GRAY)))
		graph.add_child(_label3d(nd.id, Vector3(nd.pos.x, y + 250.0, nd.pos.y - 420.0), Color.WHITE, 8.0))
	_generated.add_child(graph)

	var places := Node3D.new()
	places.name = "P5Places"
	var counters := {}
	for p in res.places:
		var key: String = p.kind
		counters[key] = counters.get(key, 0) + 1
		var tag: String = {"base": "BASE", "economic": "ECO", "resource": "RES", "expansion": "EXP", "settlement": "TOWN"}[key]
		var side := "" if p.side == 2 else ("A" if p.side == 0 else "B")
		var txt := "%s %s%d" % [tag, side, counters[key]] if key != "base" else "%s %s" % [tag, side]
		if p.get("unmet", false):
			txt += " (tol not met)"
		var y := _h(h, dim, p.pos) + 220.0
		var box := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(380.0, 380.0, 380.0)
		box.mesh = bm
		box.material_override = _unshaded(Pass5Places.PLACE_COLOR[key], true)
		box.position = Vector3(p.pos.x, y, p.pos.y)
		places.add_child(box)
		places.add_child(_label3d(txt, Vector3(p.pos.x, y + 420.0, p.pos.y + 420.0), Pass5Places.PLACE_COLOR[key].lightened(0.3), 8.0))
	_generated.add_child(places)

	var routes := Node3D.new()
	routes.name = "P5Routes"
	var rv := PackedVector3Array()
	var rc := PackedColorArray()
	var m := {"walk": res.walk, "land": res.land, "h": h}
	for e in info.edges:
		var path := Pass5Layout.astar(_fm, m, info, Pass5Places._near_walk(_fm, res.walk, by_id[e.a].pos), Pass5Places._near_walk(_fm, res.walk, by_id[e.b].pos), true, false)
		if path.is_empty():
			continue
		var pts: Array = []
		for c in path:
			pts.append(Vector2(c % dim, c / dim) * FieldMap.SPACING)
		_ribbon(rv, rc, pts, h, dim, 110.0, Color(1.0, 0.9, 0.1), 120.0)
	routes.add_child(_mesh(rv, rc))
	_generated.add_child(routes)


func _h(h: PackedFloat32Array, dim: int, p: Vector2) -> float:
	var gx := clampi(int(round(p.x / FieldMap.SPACING)), 0, dim - 1)
	var gy := clampi(int(round(p.y / FieldMap.SPACING)), 0, dim - 1)
	return maxf(h[gy * dim + gx], 0.0)


# A flat strip of quads along a polyline, sampled at the terrain height plus an offset.
func _ribbon(verts: PackedVector3Array, cols: PackedColorArray, pts: Array, h: PackedFloat32Array, dim: int, width: float, color: Color, lift: float) -> void:
	var dense: Array = []
	for k in range(pts.size() - 1):
		var a: Vector2 = pts[k]
		var b: Vector2 = pts[k + 1]
		var steps := maxi(1, int(a.distance_to(b) / 200.0))
		for s in range(steps):
			dense.append(a.lerp(b, float(s) / steps))
	dense.append(pts[pts.size() - 1])
	for k in range(dense.size() - 1):
		var a: Vector2 = dense[k]
		var b: Vector2 = dense[k + 1]
		var dir := (b - a).normalized()
		var side := Vector2(-dir.y, dir.x) * width * 0.5
		var ya := _h(h, dim, a) + lift
		var yb := _h(h, dim, b) + lift
		var p0 := Vector3(a.x + side.x, ya, a.y + side.y)
		var p1 := Vector3(a.x - side.x, ya, a.y - side.y)
		var p2 := Vector3(b.x - side.x, yb, b.y - side.y)
		var p3 := Vector3(b.x + side.x, yb, b.y + side.y)
		for v in [p0, p1, p2, p0, p2, p3]:
			verts.append(v)
			cols.append(color)


func _mesh(verts: PackedVector3Array, cols: PackedColorArray) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	if verts.is_empty():
		return mi
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_COLOR] = cols
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	mi.mesh = mesh
	var mat := _unshaded(Color.WHITE, true)
	mat.vertex_color_use_as_albedo = true
	mi.material_override = mat
	return mi


func _unshaded(c: Color, no_depth: bool) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_color = c
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.no_depth_test = no_depth
	return mat


func _disc(pos: Vector3, r: float, c: Color) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = r
	cm.bottom_radius = r
	cm.height = 60.0
	mi.mesh = cm
	mi.material_override = _unshaded(c, true)
	mi.position = pos
	return mi


func _label3d(text: String, pos: Vector3, c: Color, px: float) -> Label3D:
	var l := Label3D.new()
	l.text = text
	l.font_size = 40
	l.pixel_size = px
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	l.no_depth_test = true
	l.modulate = c
	l.outline_size = 14
	l.outline_modulate = Color(0, 0, 0, 1)
	l.position = pos
	return l


# ---------------------------------------------------------------- views (called from pass4_ui)

func cell_colors(fm: FieldMap, view: String) -> PackedColorArray:
	var res: Dictionary = fm.p5_res
	var dim := fm.dim
	var n := dim * dim
	var out := PackedColorArray()
	out.resize(n)
	var walk: PackedByteArray = res.walk
	var land: PackedByteArray = res.land
	var changed: PackedByteArray = fm.p5_info.changed
	var bridge: PackedByteArray = fm.p5_info.bridge
	var comp: PackedInt32Array = res.comp
	var base_comp: int = comp[res.base_a_cell] if res.base_a_cell >= 0 else -1
	for i in range(n):
		if land[i] == 0 and bridge[i] == 0:
			out[i] = Pass4Terrain.WATER
			continue
		var c := Color(0.2, 0.42, 0.22) if walk[i] == 1 else Color(0.36, 0.2, 0.2)
		match view:
			"react":
				if changed[i] != 0:
					c = CAT_COLOR[changed[i]]
			"p5walk":
				if walk[i] == 1:
					c = Color(0.4, 0.74, 0.38) if comp[i] == base_comp else Color(0.95, 0.55, 0.15)
					if bridge[i] == 1:
						c = CAT_COLOR[3]
				else:
					c = Color(0.78, 0.25, 0.8)
			"heat":
				var s: PackedFloat32Array = res.scores.get(kind, PackedFloat32Array())
				if not s.is_empty() and s[i] > 0.0:
					c = _heat(s[i], kind, res)
				elif walk[i] == 0:
					c = Color(0.22, 0.16, 0.16)
				else:
					c = Color(0.3, 0.3, 0.34)
		out[i] = c
	if view == "heat":
		for p in res.places:
			if p.kind == kind:
				Pass4Terrain._blob(out, dim, p.cell, 2, Color.WHITE)
				Pass4Terrain._blob(out, dim, p.cell, 1, Pass5Places.PLACE_COLOR[kind])
	return out


func _heat(v: float, k: String, res: Dictionary) -> Color:
	var s: PackedFloat32Array = res.scores[k]
	var mx := 0.0001
	for x in s:
		mx = maxf(mx, x)
	var t := clampf(v / mx, 0.0, 1.0) * (HEAT.size() - 1)
	var a := int(floor(t))
	var b := mini(a + 1, HEAT.size() - 1)
	return HEAT[a].lerp(HEAT[b], t - a)


func _draw_key() -> void:
	if not _active or _p4 == null or _fm == null or _fm.p5_res.is_empty():
		return
	var v: String = _p4.view
	if not VIEWS.has(v):
		return
	var size := _key.get_viewport_rect().size
	var font := ThemeDB.fallback_font
	var x0 := 24.0
	var y0 := size.y - 200.0
	_key.draw_rect(Rect2(x0 - 10.0, y0 - 24.0, 380.0, 190.0), Color(0.04, 0.05, 0.08, 0.84))
	if v == "heat":
		_key.draw_string(font, Vector2(x0, y0), "Heat: %s score (0 low, 1 high, per cell)" % kind, HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color.WHITE)
		for i in range(300):
			var t := float(i) / 299.0 * (HEAT.size() - 1)
			var a := int(floor(t))
			var b := mini(a + 1, HEAT.size() - 1)
			_key.draw_rect(Rect2(x0 + i, y0 + 12.0, 1.0, 22.0), HEAT[a].lerp(HEAT[b], t - a))
		_key.draw_string(font, Vector2(x0, y0 + 54.0), "low", HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color.WHITE)
		_key.draw_string(font, Vector2(x0 + 270.0, y0 + 54.0), "high", HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color.WHITE)
		_key.draw_string(font, Vector2(x0, y0 + 76.0), "grey: walkable, not eligible   dark red: blocked", HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color.WHITE)
		_key.draw_string(font, Vector2(x0, y0 + 96.0), "white square with colour: winner for this kind", HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color.WHITE)
	elif v == "react":
		_key.draw_string(font, Vector2(x0, y0), "Ground the layout changed", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color.WHITE)
		var row := 0
		for cat in CAT_NAME:
			_key.draw_rect(Rect2(x0, y0 + 12.0 + row * 20.0, 16.0, 14.0), CAT_COLOR[cat])
			_key.draw_string(font, Vector2(x0 + 24.0, y0 + 24.0 + row * 20.0), CAT_NAME[cat], HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color.WHITE)
			row += 1
		_key.draw_rect(Rect2(x0 + 190.0, y0 + 12.0, 16.0, 14.0), Color(0.2, 0.42, 0.22))
		_key.draw_string(font, Vector2(x0 + 214.0, y0 + 24.0), "walkable, unchanged", HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color.WHITE)
		_key.draw_rect(Rect2(x0 + 190.0, y0 + 32.0, 16.0, 14.0), Color(0.36, 0.2, 0.2))
		_key.draw_string(font, Vector2(x0 + 214.0, y0 + 44.0), "blocked, unchanged", HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color.WHITE)
	else:
		_key.draw_string(font, Vector2(x0, y0), "Walk view (limit 30, bridges walkable)", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color.WHITE)
		var items := [[Color(0.4, 0.74, 0.38), "walkable, joined to base A"], [Color(0.95, 0.55, 0.15), "walkable, cut off from base A"], [Color(0.78, 0.25, 0.8), "blocked"], [CAT_COLOR[3], "bridge"], [Color(1.0, 0.9, 0.1), "gold line: walking route per edge"]]
		for k in range(items.size()):
			_key.draw_rect(Rect2(x0, y0 + 12.0 + k * 20.0, 16.0, 14.0), items[k][0])
			_key.draw_string(font, Vector2(x0 + 24.0, y0 + 24.0 + k * 20.0), items[k][1], HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color.WHITE)


# ---------------------------------------------------------------- panel and state

func _fmt_wu(v: float) -> String:
	return "%d" % int(round(v)) if v >= 0.0 else "none"


func _refresh_panel() -> void:
	var res: Dictionary = _fm.p5_res
	var info: Dictionary = _fm.p5_info
	var t: PackedStringArray = []
	t.append("PASS 5   layout %s %s   terrain obeys layout: %s   (react %.0f ms, checks %.0f ms)" % [res.layout.substr(7, 2), res.name, "ON" if res.react else "OFF", info.react_ms, res.places_ms])
	t.append("Edges walkable: %d of %d%s" % [res.edges_walkable, res.edges_total, "" if res.edges_broken.is_empty() else "   broken: " + ", ".join(res.edges_broken.slice(0, 2)) + (" ..." if res.edges_broken.size() > 2 else "")])
	for ck in res.chokes:
		t.append("Choke %s (%s): asked %d wu, measured %d wu, sides blocked: %s" % [ck.id, ck.hint, int(ck.target_wu), int(ck.measured_wu), "yes" if ck.sides_blocked else "NO"])
	for v in res.vantages:
		t.append("Vantage %s: reachable %s, %+d wu vs local mean ground%s" % [v.id, "yes" if v.reachable else "NO", int(v.above_local_mean_wu), " (moved)" if v.moved else ""])
	t.append("Flank routes that bypass every choke: %d of %d" % [res.flank_bypass_ok, res.flank_total])
	t.append("Base A to base B: %s   walking %s wu, straight %d wu" % ["route exists" if res.bases_route else "NO ROUTE", _fmt_wu(res.bases_walk_wu), int(res.bases_straight_wu)])
	t.append("Equal distance, tolerance %d%%: %s" % [int(tol_pct), "MET" if res.equal_distance_ok else "NOT MET"])
	for r in res.distance_rows:
		t.append("  %s: walk A %s, B %s (diff %s) | straight A %d, B %d (diff %d%%) %s" % [r.name, _fmt_wu(r.walk_a), _fmt_wu(r.walk_b), ("%d%%" % int(round(r.walk_diff * 100.0))) if r.walk_diff >= 0.0 else "n/a", int(r.straight_a), int(r.straight_b), int(round(r.straight_diff * 100.0)), "ok" if r.within_tol else "OUTSIDE"])
	if res.resources_unmet > 0:
		t.append("  %d resource(s) placed at the most balanced cell: no cell met the tolerance 4000 wu from the other (%d cells met it in all)" % [res.resources_unmet, res.fair_cells])
	var cnt := {}
	for p in res.places:
		cnt[p.kind] = cnt.get(p.kind, 0) + 1
	t.append("Places (canvas x%.2f): base %d, economic %d (%d/side), resource %d, expansion %d (%d/side), settlement %d" % [res.scale, cnt.get("base", 0), cnt.get("economic", 0), res.counts_per_side.economic, cnt.get("resource", 0), cnt.get("expansion", 0), res.counts_per_side.expansion, cnt.get("settlement", 0)])
	if res.react:
		var ch: PackedByteArray = info.changed
		var parts: Array = []
		for cat in CAT_NAME:
			parts.append("%s %d" % [CAT_NAME[cat], ch.count(cat)])
		t.append("Changed cells: " + ", ".join(parts) + "   routes cut %d" % info.cuts)
	t.append("Keys: Y layout  O terrain obeys  N graph  Z places  C changed ground  V walk  H heat kind")
	_label.text = "\n".join(t)


func get_state() -> Dictionary:
	if _fm == null or _fm.p5_res.is_empty():
		return {"layout": "off"}
	var res: Dictionary = _fm.p5_res
	var out := {}
	for k in ["layout", "name", "react", "tol", "edges_total", "edges_walkable", "edges_broken", "bases_route", "bases_walk_wu", "bases_straight_wu", "vantages", "vantages_reachable", "chokes", "flank_total", "flank_bypass_ok", "distance_rows", "equal_distance_ok", "resources_unmet", "fair_cells", "counts_per_side", "scale", "places_ms"]:
		out[k] = res[k]
	var pl: Array = []
	for p in res.places:
		pl.append({"kind": p.kind, "side": p.side, "pos": [p.pos.x, p.pos.y], "score": p.score, "unmet": p.get("unmet", false)})
	out["places"] = pl
	var ch: PackedByteArray = _fm.p5_info.changed
	var cc := {}
	for cat in CAT_NAME:
		cc[CAT_NAME[cat]] = ch.count(cat)
	out["changed_cells"] = cc
	out["react_ms"] = _fm.p5_info.react_ms
	out["routes_cut"] = _fm.p5_info.get("cuts", 0)
	out["route_iterations"] = _fm.p5_info.get("route_iterations", 0)
	out["kind"] = kind
	out["narrow_wu"] = narrow
	out["moderate_wu"] = moderate
	out["mode"] = mode
	return out

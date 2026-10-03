extends Node3D
# Settlement mockup pass 1: a base that builds itself. Placeholder boxes; never loaded by the game.
# Every number it uses is a candidate (see settlement_sim.gd and the README).

const Sim := preload("res://scenes/mockups/settlement/settlement_sim.gd")
const SEED := 11

var fm: FieldMap
var sim
var speed := 1.0
var cam: Camera3D
var cam_target := Vector3.ZERO
var cam_yaw := 0.35
var cam_pitch := -0.9
var cam_dist := 48.0
var lots: MultiMeshInstance3D
var path_view: MeshInstance3D
var players_node: Node3D
var hover_box: MeshInstance3D
var hover_cell := Vector2i(-1, -1)
var mouse_px := Vector2(960, 600)
var info: Label
var paths_on := false
var frame_ms := 0.0
var flush_ms := 0.0
var last_wave := {}
var terrain_mi: MeshInstance3D
var player_boxes := 0


func _ready() -> void:
	DisplayServer.window_set_title("Settlement mockup")
	var t0 := Time.get_ticks_msec()
	fm = FieldMap.new()
	fm.generate(SEED, 24000.0, 60.0)
	sim = Sim.new()
	sim.setup(fm)
	print("fieldmap+setup ms: ", Time.get_ticks_msec() - t0)
	print("CANDIDATES thresholds=", Sim.THRESHOLDS, " tick_s=", Sim.TICK_S, " decay=", Sim.BASE_DECAY,
		" cliff_slope=", Sim.CLIFF_SLOPE, " rise_s=", Sim.RISE_S, " wave_len=", Sim.WAVE_LEN,
		" path_dilate_cells=", Sim.PATH_DILATE, " rebuild_delay_s=", Sim.REBUILD_DELAY_S)
	_build_world()
	_build_hud()
	_place_camera()
	_flush()


func _w(c: Vector2i) -> Vector3:
	var i: int = sim.idx(c)
	return Vector3(c.x, sim.elev[i] / 100.0, c.y)


func _build_world() -> void:
	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color(0.62, 0.72, 0.82)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.8, 0.82, 0.88)
	e.ambient_light_energy = 0.55
	env.environment = e
	add_child(env)
	var sun := DirectionalLight3D.new()
	sun.rotation = Vector3(-0.9, 0.6, 0)
	sun.light_energy = 1.0
	add_child(sun)
	cam = Camera3D.new()
	cam.far = 600.0
	cam.fov = 55.0
	add_child(cam)

	terrain_mi = MeshInstance3D.new()
	terrain_mi.mesh = _terrain_mesh()
	var tm := StandardMaterial3D.new()
	tm.vertex_color_use_as_albedo = true
	tm.roughness = 1.0
	terrain_mi.material_override = tm
	add_child(terrain_mi)

	lots = MultiMeshInstance3D.new()
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	mm.mesh = BoxMesh.new()
	mm.instance_count = Sim.WIN * Sim.WIN
	lots.multimesh = mm
	var lm := StandardMaterial3D.new()
	lm.vertex_color_use_as_albedo = true
	lm.roughness = 0.9
	lots.material_override = lm
	add_child(lots)

	path_view = MeshInstance3D.new()
	var pmat := StandardMaterial3D.new()
	pmat.albedo_color = Color(1.0, 0.85, 0.1)
	pmat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	pmat.cull_mode = BaseMaterial3D.CULL_DISABLED
	path_view.material_override = pmat
	path_view.visible = false
	add_child(path_view)

	players_node = Node3D.new()
	add_child(players_node)

	hover_box = MeshInstance3D.new()
	var hb := BoxMesh.new()
	hb.size = Vector3(1, 0.12, 1)
	hover_box.mesh = hb
	var hm := StandardMaterial3D.new()
	hm.albedo_color = Color(1, 0.9, 0.2, 0.18)
	hm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	hm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	hover_box.material_override = hm
	hover_box.visible = false
	add_child(hover_box)


func _terrain_mesh() -> ArrayMesh:
	var W: int = Sim.WIN
	var verts := PackedVector3Array()
	var cols := PackedColorArray()
	var norms := PackedVector3Array()
	var idxs := PackedInt32Array()
	for gy in W:
		for gx in W:
			var i := gy * W + gx
			var h: float = sim.elev[i] / 100.0
			if sim.water[i] == 1 and h < 0.0:
				h = 0.0
			verts.append(Vector3(gx, h, gy))
			var hl: float = sim.elev[gy * W + maxi(gx - 1, 0)] / 100.0
			var hr: float = sim.elev[gy * W + mini(gx + 1, W - 1)] / 100.0
			var hu: float = sim.elev[maxi(gy - 1, 0) * W + gx] / 100.0
			var hd: float = sim.elev[mini(gy + 1, W - 1) * W + gx] / 100.0
			norms.append(Vector3(hl - hr, 2.0, hu - hd).normalized())
			var c: Color
			if sim.water[i] == 1:
				c = Color(0.18, 0.38, 0.65)
			elif sim.slope[i] > Sim.CLIFF_SLOPE:
				c = Color(0.46, 0.43, 0.4)
			else:
				var e: float = clampf(sim.elev[i] / 3000.0, 0.0, 1.0)
				c = Color(0.36, 0.52, 0.3).lerp(Color(0.62, 0.58, 0.45), e)
			cols.append(c)
	for gy in W - 1:
		for gx in W - 1:
			var a := gy * W + gx
			idxs.append_array([a, a + 1, a + W, a + 1, a + W + 1, a + W])
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = verts
	arr[Mesh.ARRAY_NORMAL] = norms
	arr[Mesh.ARRAY_COLOR] = cols
	arr[Mesh.ARRAY_INDEX] = idxs
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	return mesh


func _build_hud() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	var bar := HBoxContainer.new()
	bar.position = Vector2(8, 6)
	bar.add_theme_constant_override("separation", 6)
	layer.add_child(bar)
	for e in [["Shipment arrives", "shipment"], ["Expansion founded", "expansion"], ["Season turns", "season"]]:
		_btn(bar, e[0], func(): qa_wave(e[1]))
	_sep(bar)
	for s in [1.0, 5.0, 20.0]:
		_btn(bar, "%dx" % int(s), func(): speed = s)
	_btn(bar, "Reset", qa_reset)
	_sep(bar)
	var cb := CheckButton.new()
	cb.text = "Paths (P)"
	cb.focus_mode = Control.FOCUS_NONE
	cb.toggled.connect(func(on): qa_paths(on))
	bar.add_child(cb)
	info = Label.new()
	info.position = Vector2(8, 46)
	info.add_theme_color_override("font_color", Color.WHITE)
	info.add_theme_color_override("font_outline_color", Color.BLACK)
	info.add_theme_constant_override("outline_size", 6)
	info.add_theme_font_size_override("font_size", 18)
	layer.add_child(info)
	var help := Label.new()
	help.text = "click: place big building   D: damage under mouse   Z/X/C: waves   1/2/3: speed 1x 5x 20x   P: paths   R: reset   WASD pan, Q/E turn, wheel zoom"
	help.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT)
	help.position += Vector2(8, -30)
	help.add_theme_color_override("font_color", Color.WHITE)
	help.add_theme_color_override("font_outline_color", Color.BLACK)
	help.add_theme_constant_override("outline_size", 6)
	layer.add_child(help)


func _btn(parent: Control, text: String, cb: Callable) -> void:
	var b := Button.new()
	b.text = text
	b.focus_mode = Control.FOCUS_NONE
	b.pressed.connect(cb)
	parent.add_child(b)


func _sep(parent: Control) -> void:
	var s := VSeparator.new()
	parent.add_child(s)


func _place_camera() -> void:
	cam_target = _w(sim.core)
	_apply_cam()


func _apply_cam() -> void:
	var dir := Vector3(sin(cam_yaw) * cos(cam_pitch), -sin(cam_pitch), cos(cam_yaw) * cos(cam_pitch))
	cam.position = cam_target + dir * cam_dist
	cam.look_at(cam_target, Vector3.UP)


func _process(delta: float) -> void:
	var t0 := Time.get_ticks_usec()
	sim.update(delta * speed)
	_flush()
	_hover()
	frame_ms = lerpf(frame_ms, (Time.get_ticks_usec() - t0) / 1000.0, 0.1)
	var cnt: Dictionary = sim.counts()
	info.text = "t %s  x%d   stage1 %d  scaffold %d  built %d  dense %d  cliff %d  rubble %d  player %d   routes %d   script frame %.1f ms%s" % [
		_clock(sim.t), int(speed), cnt.stage1, cnt.stage2, cnt.stage3, cnt.stage4, cnt.cliff, cnt.rubble,
		sim.players.size(), sim.path_routes.size(), frame_ms, ("   wave: " + str(last_wave.get("kind", "")) if sim.t < sim.wave_until else "")]


func _clock(s: float) -> String:
	return "%d:%02d" % [int(s) / 60, int(s) % 60]


func _flush() -> void:
	var t0 := Time.get_ticks_usec()
	var mm: MultiMesh = lots.multimesh
	for i in sim.dirty:
		var v: Array = sim.vis(i)
		var gx: int = i % Sim.WIN
		var gy: int = i / Sim.WIN
		var h: float = v[0]
		if h <= 0.0:
			mm.set_instance_transform(i, Transform3D(Basis.from_scale(Vector3.ZERO), Vector3.ZERO))
		else:
			var fw: float = v[1]
			var jx: float = (sim._hash(i + 3) - 0.5) * 2.0 * Sim.JITTER_CELLS
			var jz: float = (sim._hash(i + 5) - 0.5) * 2.0 * Sim.JITTER_CELLS
			var yaw: float = _lot_yaw(i, gx, gy)
			var b := Basis(Vector3.UP, yaw) * Basis.from_scale(Vector3(fw, h, fw * 0.85))
			mm.set_instance_transform(i, Transform3D(b, Vector3(gx + jx, sim.elev[i] / 100.0 + h * 0.5 - 0.12, gy + jz)))
			mm.set_instance_color(i, v[2])
	sim.dirty = {}
	if sim.routes_dirty:
		_build_routes()
	while player_boxes < sim.players.size():
		var p: Dictionary = sim.players[player_boxes]
		var mi := MeshInstance3D.new()
		var bm := BoxMesh.new()
		var sz: float = Sim.PLAYER_HALF * 2 + 1
		bm.size = Vector3(sz, 3.0, sz)
		mi.mesh = bm
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(0.2, 0.7, 0.8)
		mi.material_override = mat
		mi.position = Vector3(p.cell.x, p.elev / 100.0 + 1.3, p.cell.y)
		players_node.add_child(mi)
		player_boxes += 1
	flush_ms = lerpf(flush_ms, (Time.get_ticks_usec() - t0) / 1000.0, 0.2)


func _lot_yaw(i: int, gx: int, gy: int) -> float:
	var W: int = Sim.WIN
	var dx: float = sim.elev[gy * W + mini(gx + 1, W - 1)] - sim.elev[gy * W + maxi(gx - 1, 0)]
	var dz: float = sim.elev[mini(gy + 1, W - 1) * W + gx] - sim.elev[maxi(gy - 1, 0) * W + gx]
	var jit: float = (sim._hash(i + 7) - 0.5) * 2.0 * Sim.YAW_JITTER
	if sim.slope[i] > Sim.CONTOUR_SLOPE and (absf(dx) + absf(dz)) > 0.0:
		return atan2(-dx, -dz) + jit
	return sim._hash(i + 9) * PI + jit


func _build_routes() -> void:
	var W: int = Sim.WIN
	var verts := PackedVector3Array()
	var idxs := PackedInt32Array()
	for route in sim.path_routes:
		var pts: Array = []
		for i in route:
			var cx: int = i % W
			var cy: int = i / W
			var top := -1e9
			for oy in range(-1, 2):
				for ox in range(-1, 2):
					var nx := clampi(cx + ox, 0, W - 1)
					var ny := clampi(cy + oy, 0, W - 1)
					var e: float = sim.elev[ny * W + nx]
					if sim.water[ny * W + nx] == 1:
						e = maxf(e, 0.0)
					top = maxf(top, e)
			pts.append(Vector3(cx, top / 100.0 + 0.15, cy))
		for k in pts.size() - 1:
			var a: Vector3 = pts[k]
			var b: Vector3 = pts[k + 1]
			var dir := (b - a)
			dir.y = 0
			var side := Vector3(-dir.z, 0, dir.x).normalized() * 1.0
			var base := verts.size()
			verts.append_array([a - side, a + side, b - side, b + side])
			idxs.append_array([base, base + 1, base + 2, base + 1, base + 3, base + 2])
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = verts
	arr[Mesh.ARRAY_INDEX] = idxs
	var mesh := ArrayMesh.new()
	if verts.size() > 0:
		mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	path_view.mesh = mesh
	sim.routes_dirty = false


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion:
		mouse_px = event.position
	elif event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_LEFT and event.position.y > 44:
			var c := _pick(event.position)
			if c.x >= 0:
				sim.place_building(c)
		elif event.button_index == MOUSE_BUTTON_WHEEL_UP:
			cam_dist = maxf(10.0, cam_dist * 0.9)
			_apply_cam()
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			cam_dist = minf(160.0, cam_dist * 1.1)
			_apply_cam()
	elif event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_D: if hover_cell.x >= 0: sim.damage(hover_cell)
			KEY_Z: qa_wave("shipment")
			KEY_X: qa_wave("expansion")
			KEY_C: qa_wave("season")
			KEY_1: speed = 1.0
			KEY_2: speed = 5.0
			KEY_3: speed = 20.0
			KEY_P: qa_paths(not paths_on)
			KEY_R: qa_reset()
			KEY_Q: cam_yaw -= 0.15; _apply_cam()
			KEY_E: cam_yaw += 0.15; _apply_cam()
	if event is InputEventKey and event.pressed:
		var s := cam_dist * 0.04
		var fwd := Vector3(-sin(cam_yaw), 0, -cos(cam_yaw))
		var right := Vector3(cos(cam_yaw), 0, -sin(cam_yaw))
		match event.keycode:
			KEY_W: cam_target += fwd * s * 3.0
			KEY_S: cam_target -= fwd * s * 3.0
			KEY_A: cam_target -= right * s * 3.0
			KEY_RIGHT: cam_target += right * s * 3.0
			KEY_UP: cam_target += fwd * s * 3.0
			KEY_DOWN: cam_target -= fwd * s * 3.0
			KEY_LEFT: cam_target -= right * s * 3.0
		_apply_cam()


func _pick(px: Vector2) -> Vector2i:
	var o := cam.project_ray_origin(px)
	var d := cam.project_ray_normal(px)
	var tt := 0.0
	while tt < 400.0:
		var p := o + d * tt
		var c := Vector2i(int(round(p.x)), int(round(p.z)))
		if sim.inside(c) and p.y <= sim.elev[sim.idx(c)] / 100.0:
			return c
		tt += 0.3
	return Vector2i(-1, -1)


func _hover() -> void:
	hover_cell = _pick(mouse_px) if mouse_px.y > 44 else Vector2i(-1, -1)
	hover_box.visible = hover_cell.x >= 0
	if hover_cell.x >= 0:
		var sz := float(Sim.DAMAGE_R * 2 + 1)
		(hover_box.mesh as BoxMesh).size = Vector3(sz, 0.12, sz)
		hover_box.position = _w(hover_cell) + Vector3(0, 0.3, 0)


func qa_plant(_id: String) -> bool:
	return false


func qa_state() -> Dictionary:
	var c: Dictionary = sim.counts()
	return {"seed": SEED, "t": sim.t, "speed": speed, "counts": c, "piece_total": sim.piece_total(),
		"frame_ms": frame_ms, "flush_ms": flush_ms, "tick_ms": sim.tick_ms, "path_ms": sim.path_ms,
		"paths_visible": paths_on, "path_ends": sim.path_ends.size(), "routes": sim.path_routes.size(), "lots_on_water": _lots_on_water(), "path_connected": sim.path_connected,
		"path_cells": int(sim.path.count(1)) + int(sim.path.count(2)), "players": sim.players.size(),
		"thresholds": Sim.THRESHOLDS, "wave": last_wave, "wave_active": sim.t < sim.wave_until,
		"core": [sim.core.x, sim.core.y], "player_cells_cleared": sim.path_cells_cleared,
		"cliff_cells": _cliff_cells(), "reached": sim.reached.size(), "p_over_thresh0": _p_over(), "water_cells": int(sim.water.count(1))}


func _cliff_cells() -> int:
	var n := 0
	for i in Sim.WIN * Sim.WIN:
		if sim.water[i] == 0 and sim.is_cliff(i):
			n += 1
	return n


func qa_advance(seconds: float) -> void:
	var dt := 0.25
	var n := int(seconds / dt)
	for k in n:
		sim.update(dt)
		if k % 40 == 0:
			_flush()
	_flush()


func qa_wave(kind: String) -> void:
	last_wave = sim.wave(kind)


func qa_paths(on: bool) -> void:
	paths_on = on
	path_view.visible = on


func qa_reset() -> void:
	sim.reset()
	for ch in players_node.get_children():
		ch.queue_free()
	player_boxes = 0
	last_wave = {}
	_flush()


func qa_speed(s: float) -> void:
	speed = s


func qa_cam(yaw: float, pitch: float, dist: float, dx: float, dz: float) -> void:
	cam_yaw = yaw
	cam_pitch = pitch
	cam_dist = dist
	cam_target = _w(sim.core) + Vector3(dx, 0, dz)
	_apply_cam()


func qa_damage_at(dx: int, dy: int) -> int:
	return sim.damage(sim.core + Vector2i(dx, dy))


func _p_over() -> int:
	var n := 0
	for i in Sim.WIN * Sim.WIN:
		if sim.P[i] >= Sim.THRESHOLDS[0]:
			n += 1
	return n


func _lots_on_water() -> int:
	var n := 0
	for i in Sim.WIN * Sim.WIN:
		if sim.water[i] == 1 and (sim.state[i] > 0 or sim.rubble[i] == 1):
			n += 1
	return n

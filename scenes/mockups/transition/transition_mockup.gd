extends Node
# Transition mockup, pass 1 (docs/northstar/plans/2026-10-15-transition-mockup-spec.md; E-16 S-108).
# One camera, one eased curve: battlefield -> pull-back -> galaxy + scroll panel -> push-in -> next battlefield.

enum S { IDLE, PULL, GALAXY, PUSH, DONE }

const D0 := 700.0              # tactical-view camera distance to the battlefield origin (wu)
const D1 := 1.0e7              # galaxy-view camera distance (wu)
const UNIT_R := 11.5           # VG-C-unitscale body radius (wu)
const PANEL_FRAC := 0.38
const SLIDE_S := 0.40
const CHARS_PER_S := 45.0
const LINE_PAUSE_S := 0.5
const SAMPLE_S := 0.1
const LINES := [
	"The ford was held until the water stopped being a question.",
	"Nobody wrote down who crossed first; everyone remembered it.",
	"By evening the far bank had a name, and the name had a road.",
]

var DRAFT_pullback_s := 6.0
var DRAFT_star_count := 4000
var DRAFT_star_size_frac := 0.004
var camera_path_samples: Array = []
var panel_width_fraction := 0.0

var _state := S.IDLE
var _t := 0.0
var _e := 0.0                  # eased progress, 0 battlefield .. 1 galaxy
var _slide := 0.0              # 0 panel out .. 1 panel in
var _slide_target := 0.0
var _seed := 1
var _field_seed := 1
var _sample_clock := SAMPLE_S
var _print_t := 0.0
var _shot_dir := ""
var _shots_done := {}
var _gal_t := 0.0

var _svc: SubViewportContainer
var _sv: SubViewport
var _cam: Camera3D
var _env: Environment
var _battle: Node3D
var _stars: MultiMeshInstance3D
var _star_mat: StandardMaterial3D
var _dot: MeshInstance3D
var _dot_mat: StandardMaterial3D
var _path: MeshInstance3D
var _haze: ColorRect
var _panel: Panel
var _text: Label
var _proceed: Button
var _bar: ProgressBar
var _status: Label
var _keys: Label


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	var i := args.find("--shot")
	if i >= 0 and i + 1 < args.size():
		_shot_dir = args[i + 1]
		DirAccess.make_dir_recursive_absolute(_shot_dir)
	_build_world()
	_build_ui()
	_make_battlefield()
	_make_stars()
	_apply()


func _build_world() -> void:
	_svc = SubViewportContainer.new()
	_svc.stretch = true
	_svc.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_svc)
	_sv = SubViewport.new()
	_svc.add_child(_sv)
	_env = Environment.new()
	_env.background_mode = Environment.BG_COLOR
	_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	_env.ambient_light_color = Color(0.55, 0.58, 0.65)
	var we := WorldEnvironment.new()
	we.environment = _env
	_sv.add_child(we)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-50, 35, 0)
	_sv.add_child(sun)
	_cam = Camera3D.new()
	_cam.fov = 60.0
	_cam.far = 1.0e8
	_sv.add_child(_cam)
	_battle = Node3D.new()
	_sv.add_child(_battle)
	# the point of light the battlefield becomes: a billboard whose size follows distance
	_dot = MeshInstance3D.new()
	var q := QuadMesh.new()
	_dot_mat = StandardMaterial3D.new()
	_dot_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_dot_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_dot_mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	_dot_mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	q.material = _dot_mat
	_dot.mesh = q
	_sv.add_child(_dot)
	# camera path helper (V)
	_path = MeshInstance3D.new()
	var am := ArrayMesh.new()
	var pts := PackedVector3Array()
	for k in range(65):
		pts.append(_cam_pos(k / 64.0))
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = pts
	am.add_surface_from_arrays(Mesh.PRIMITIVE_LINE_STRIP, arr)
	var pm := StandardMaterial3D.new()
	pm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	pm.albedo_color = Color(1, 0.9, 0.2)
	am.surface_set_material(0, pm)
	_path.mesh = am
	_path.visible = false
	_sv.add_child(_path)


func _build_ui() -> void:
	var haze_layer := CanvasLayer.new()
	haze_layer.layer = 1
	add_child(haze_layer)
	_haze = ColorRect.new()
	_haze.color = Color(0.62, 0.72, 0.88, 0.0)
	_haze.set_anchors_preset(Control.PRESET_FULL_RECT)
	_haze.mouse_filter = Control.MOUSE_FILTER_IGNORE
	haze_layer.add_child(_haze)
	var ui := CanvasLayer.new()
	ui.layer = 2
	add_child(ui)
	_panel = Panel.new()
	ui.add_child(_panel)
	var box := VBoxContainer.new()
	box.set_anchors_preset(Control.PRESET_FULL_RECT)
	box.offset_left = 16
	box.offset_top = 16
	box.offset_right = -16
	box.offset_bottom = -16
	_panel.add_child(box)
	var head := Label.new()
	head.text = "CHRONICLE"
	box.add_child(head)
	_text = Label.new()
	_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_text.size_flags_vertical = Control.SIZE_EXPAND_FILL
	box.add_child(_text)
	_proceed = Button.new()
	_proceed.text = "Proceed"
	_proceed.visible = false
	_proceed.pressed.connect(_on_proceed)
	box.add_child(_proceed)
	_status = Label.new()
	_status.position = Vector2(16, 12)
	_status.add_theme_font_size_override("font_size", 26)
	ui.add_child(_status)
	var bl := VBoxContainer.new()
	bl.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	bl.offset_left = 16
	bl.offset_top = -56
	bl.offset_bottom = -12
	bl.grow_vertical = Control.GROW_DIRECTION_BEGIN
	ui.add_child(bl)
	var pl := Label.new()
	pl.text = "preloading next mission"
	bl.add_child(pl)
	_bar = ProgressBar.new()
	_bar.custom_minimum_size = Vector2(220, 10)
	_bar.show_percentage = false
	bl.add_child(_bar)
	_keys = Label.new()
	_keys.set_anchors_preset(Control.PRESET_TOP_LEFT)
	_keys.position = Vector2(16, 52)
	
	
	_keys.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	_keys.modulate = Color(1, 1, 1, 0.8)
	ui.add_child(_keys)


func _make_battlefield() -> void:
	for c in _battle.get_children():
		c.queue_free()
	var rng := RandomNumberGenerator.new()
	rng.seed = _seed * 7919
	var tint := Color(0.36, 0.46, 0.24).lerp(Color(0.5, 0.4, 0.26), rng.randf())
	var cols := 6
	var rows := 5
	var cw := 150.0
	var ch := 140.0
	var heights := []
	for r in range(rows):
		for c in range(cols):
			var h := 10.0 * float(rng.randi_range(0, 3))
			heights.append(h)
			var m := MeshInstance3D.new()
			var b := BoxMesh.new()
			b.size = Vector3(cw, h + 40.0, ch)
			var mat := StandardMaterial3D.new()
			mat.albedo_color = tint.lightened(h / 80.0).darkened(0.1 * rng.randf())
			b.material = mat
			m.mesh = b
			m.position = Vector3((c - (cols - 1) * 0.5) * cw, (h - 40.0) * 0.5, (r - (rows - 1) * 0.5) * ch)
			_battle.add_child(m)
	var sm := SphereMesh.new()
	sm.radius = UNIT_R
	sm.height = UNIT_R * 2.0
	sm.radial_segments = 12
	sm.rings = 6
	var side_mats: Array = []
	for col in [Color(0.2, 0.45, 0.95), Color(0.95, 0.3, 0.2)]:
		var um := StandardMaterial3D.new()
		um.albedo_color = col
		side_mats.append(um)
	for n in range(40):
		var side := n % 2
		var x := rng.randf_range(-400.0, -60.0) if side == 0 else rng.randf_range(60.0, 400.0)
		var z := rng.randf_range(-280.0, 280.0)
		var ci := clampi(int((x / cw) + cols * 0.5), 0, cols - 1)
		var ri := clampi(int((z / ch) + rows * 0.5), 0, rows - 1)
		var u := MeshInstance3D.new()
		u.mesh = sm
		u.material_override = side_mats[side]
		u.position = Vector3(x, heights[ri * cols + ci] + UNIT_R, z)
		_battle.add_child(u)


func _make_stars() -> void:
	if _stars:
		_stars.queue_free()
	var rng := RandomNumberGenerator.new()
	rng.seed = _field_seed * 104729
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	var sm := QuadMesh.new()
	sm.size = Vector2(2.0, 2.0)
	var disc := GradientTexture2D.new()
	disc.fill = GradientTexture2D.FILL_RADIAL
	disc.fill_from = Vector2(0.5, 0.5)
	disc.fill_to = Vector2(1.0, 0.5)
	disc.gradient = Gradient.new()
	disc.gradient.offsets = PackedFloat32Array([0.0, 0.55, 1.0])
	disc.gradient.colors = PackedColorArray([Color(1, 1, 1, 1), Color(1, 1, 1, 0.8), Color(1, 1, 1, 0)])
	_star_mat = StandardMaterial3D.new()
	_star_mat.albedo_texture = disc
	_star_mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	_star_mat.billboard_keep_scale = true
	_star_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_star_mat.vertex_color_use_as_albedo = true
	_star_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	sm.material = _star_mat
	mm.mesh = sm
	mm.instance_count = DRAFT_star_count
	for k in range(mm.instance_count):
		var arm := rng.randi_range(0, 2)
		var r := 4.0e5 + 3.6e6 * pow(rng.randf(), 0.7)
		if k % 2 == 0:
			r = 6.0e4 + 9.4e5 * pow(rng.randf(), 1.5)
		var a := r * 1.2e-6 + arm * TAU / 3.0 + rng.randfn(0.0, 0.25)
		var pos := Vector3(cos(a) * r, rng.randfn(0.0, 6.0e4), sin(a) * r)
		var s := rng.randf_range(15000.0, 40000.0)
		var dim := 1.0
		if k % 2 == 0:
			s = minf(s, r * DRAFT_star_size_frac)
			dim = lerpf(1.0, 0.25, smoothstep(6.0e4, 1.0e6, r))
		mm.set_instance_transform(k, Transform3D(Basis.from_scale(Vector3(s, s, s)), pos))
		mm.set_instance_color(k, Color(1, 0.9, 0.75).lerp(Color(0.7, 0.8, 1.0), rng.randf()) * dim)
	_stars = MultiMeshInstance3D.new()
	_stars.multimesh = mm
	_sv.add_child(_stars)


func _cam_pos(e: float) -> Vector3:
	var d := D0 * pow(D1 / D0, e)
	var pitch := deg_to_rad(lerpf(48.0, 62.0, e))
	var yaw := e * 0.5
	return Vector3(sin(yaw) * cos(pitch), sin(pitch), cos(yaw) * cos(pitch)) * d


func _apply() -> void:
	var vp := get_viewport().get_visible_rect().size
	var p := _cam_pos(_e)
	var d := p.length()
	_cam.position = p
	_cam.near = maxf(1.0, d * 0.02)
	_cam.look_at_from_position(p, Vector3.ZERO, Vector3.UP)
	panel_width_fraction = PANEL_FRAC * _slide
	var w := vp.x * panel_width_fraction
	_panel.position = Vector2(vp.x - w, 0)
	_panel.size = Vector2(w, vp.y)
	_svc.size = Vector2(vp.x - w, vp.y)
	_env.background_color = Color(0.5, 0.64, 0.82).lerp(Color(0.01, 0.012, 0.03), smoothstep(0.08, 0.55, _e))
	_haze.color.a = 0.6 * pow(sin(PI * clampf(_e * 1.7, 0.0, 1.0)), 2.0)
	_star_mat.albedo_color.a = smoothstep(0.05, 0.4, _e)
	var dot_a := smoothstep(0.3, 0.7, _e)
	_dot.position = Vector3.ZERO
	_dot.scale = Vector3.ONE * d * 0.0015
	_dot_mat.albedo_color = Color(1.0, 0.85, 0.5, dot_a).lerp(Color(1.0, 1.0, 0.9, dot_a), 1.0 if _state == S.PUSH else 0.0)
	_battle.visible = d < D1 * 0.5
	_status.text = "Mission complete" if _state == S.IDLE else ("Briefing" if _state == S.DONE else "")
	_keys.text = "Space start/proceed   R reset   [ ] pull-back %.2f s   V path   F1-F3 seed" % DRAFT_pullback_s


func _process(delta: float) -> void:
	_t += delta
	_sample_clock += delta
	match _state:
		S.IDLE:
			if _shot_dir != "":
				if _t > 0.8 and not _shots_done.has("01"):
					_grab("01_battlefield.png", "01")
				elif _t > 1.2 and _shots_done.has("01"):
					_start()
		S.PULL:
			_e = smoothstep(0.0, 1.0, minf(_t / DRAFT_pullback_s, 1.0))
			_bar.value = _e * 50.0
			if _shot_dir != "" and _t >= DRAFT_pullback_s * 0.5 and not _shots_done.has("02"):
				_grab("02_pullback_mid.png", "02")
			if _t >= DRAFT_pullback_s:
				_e = 1.0
				_enter(S.GALAXY)
				_slide_target = 1.0
				_print_t = 0.0
				_text.text = ""
		S.GALAXY:
			_print_galaxy(delta)
		S.PUSH:
			_e = 1.0 - smoothstep(0.0, 1.0, minf(_t / DRAFT_pullback_s, 1.0))
			if _shot_dir != "" and _t >= DRAFT_pullback_s * 0.5 and not _shots_done.has("04"):
				_grab("04_pushin_mid.png", "04")
			if _t >= DRAFT_pullback_s:
				_e = 0.0
				_enter(S.DONE)
		S.DONE:
			if _shot_dir != "" and _t > 0.8 and not _shots_done.has("05"):
				_grab("05_next_battlefield.png", "05", true)
	_slide = move_toward(_slide, _slide_target, delta / SLIDE_S)
	while _sample_clock >= SAMPLE_S:
		_sample_clock -= SAMPLE_S
		camera_path_samples.append(_cam_pos(_e).length())
	_apply()


func _print_galaxy(delta: float) -> void:
	_gal_t += delta
	if _slide < 1.0:
		return
	_print_t += delta
	var shown := ""
	var clock := _print_t
	var done := true
	for line in LINES:
		var n := int(clock * CHARS_PER_S)
		if n >= line.length():
			shown += line + "\n\n"
			clock -= line.length() / CHARS_PER_S + LINE_PAUSE_S
		else:
			shown += line.substr(0, maxi(n, 0))
			done = false
			break
	_text.text = shown
	var total := 0.0
	for line in LINES:
		total += line.length() / CHARS_PER_S + LINE_PAUSE_S
	_bar.value = 50.0 + 50.0 * minf(_print_t / total, 1.0)
	if done and not _proceed.visible:
		_proceed.visible = true
		_gal_t = 0.0
	if done and _shot_dir != "":
		if _gal_t > 0.6 and not _shots_done.has("03"):
			_grab("03_galaxy.png", "03")
		elif _gal_t > 1.0 and _shots_done.has("03"):
			_on_proceed()


func _enter(s: S) -> void:
	_state = s
	_t = 0.0


func _start() -> void:
	_enter(S.PULL)
	_bar.value = 0.0


func _on_proceed() -> void:
	if _state != S.GALAXY:
		return
	_proceed.visible = false
	_slide_target = 0.0
	_seed += 1
	_make_battlefield()
	_enter(S.PUSH)


func _reset() -> void:
	_state = S.IDLE
	_t = 0.0
	_e = 0.0
	_slide = 0.0
	_slide_target = 0.0
	_print_t = 0.0
	_text.text = ""
	_proceed.visible = false
	_bar.value = 0.0
	camera_path_samples.clear()
	_sample_clock = SAMPLE_S
	_seed = 1
	_make_battlefield()


func _grab(file: String, key: String, quit_after := false) -> void:
	_shots_done[key] = true
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(_shot_dir.path_join(file))
	if quit_after:
		get_tree().quit(0)


func _input(ev: InputEvent) -> void:
	if not (ev is InputEventKey) or not ev.pressed or ev.echo:
		return
	match ev.keycode:
		KEY_SPACE:
			if _state == S.IDLE:
				_start()
			elif _state == S.GALAXY and _proceed.visible:
				_on_proceed()
		KEY_R:
			_reset()
		KEY_BRACKETLEFT:
			DRAFT_pullback_s = maxf(0.75, DRAFT_pullback_s * 0.5)
		KEY_BRACKETRIGHT:
			DRAFT_pullback_s = minf(48.0, DRAFT_pullback_s * 2.0)
		KEY_V:
			_path.visible = not _path.visible
		KEY_F1, KEY_F2, KEY_F3:
			_field_seed = ev.keycode - KEY_F1 + 1
			_make_stars()

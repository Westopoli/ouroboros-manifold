extends Node
# Real-GPU checks for the galaxy shell: DEVICE, SHELL-GPU, SHELL-SCALE, REFILL,
# LOOK-LAYERS, SCREENSHOTS (SHADER-COMPILES is the log scan in
# scripts/galaxy_perf.sh). Promoted from the experiment probe
# (scenes/mockups/galaxy/experiment/probe.gd on push/galaxy-field-experiment).
# Frozen after the "galaxy field: failing tests" commit; builders do not edit.
# Run it with scripts/galaxy_perf.sh, never directly.
#
# MEASUREMENT METHOD (why it looks like this):
#  - Window-free: Xvfb + Vulkan, so nothing opens on the owner's desktop.
#  - Presented frames under Xvfb take 60-130 ms each (the driver copies every
#    frame to the X server), the GPU idles ~90% between frames and drops to
#    200-900 MHz, and ordinary frame timing reads about 15x too slow. So:
#    never use frame time or Performance.TIME_PROCESS here.
#  - GPU time of the shell is RenderingServer.viewport_get_measured_render_time_gpu
#    of the shell's own SubViewport (timestamps, not wall clock).
#  - Frames are drawn back to back with RenderingServer.force_draw(false) (no
#    present), 60 warm-up then 120 recorded; median and p95 are reported, the
#    budget is judged on the median.
#  - A burner SubViewport (a heavy full-surface canvas shader, drawn every
#    frame) keeps the GPU saturated so its clocks stay at their maximum even
#    when the shell alone would take 0.1 ms. Viewport timestamps are per
#    viewport and the card runs one queue, so the burner does not enter the
#    shell's number. The SM clock is sampled with nvidia-smi after each run and
#    flagged below 1700 MHz.
#  - Every number is only valid when DEVICE names the RTX 3060 on forward_plus
#    at 1920x1080; llvmpipe, the dummy renderer or another window size
#    invalidates the run.
#
# Contract used on the product (new renderer):
#   GalaxyView child "ShellRenderer" with
#     get_shell_viewport() -> SubViewport     the half-resolution shell viewport
#     var res_divisor: int                    1 = full 1080p, 2 = shipped default
#     get_territory_field() -> Node           the TerritoryField (see test_field.gd)
#     set_debug_mode(mode: int)               mode 1: every pixel opaque, ALBEDO.r = layer count / 16
#   (the legacy renderer is measured through its private _sub_viewport; it has no
#    res_divisor, no field and no debug mode, so those checks fail on it)

const BigGalaxy := preload("res://scenes/mockups/galaxy/tests/big_galaxy.gd")
const GridSampler := preload("res://scenes/mockups/galaxy/tests/grid_sampler.gd")
const MOCKUP_SCENE := "res://scenes/mockups/galaxy/galaxy_mockup.tscn"
const RESULTS := "res://scenes/mockups/galaxy/tests/results/"
const WARMUP := 60
const RECORD := 120
const POSITIONS := ["d120", "d25", "d7.5_f0", "inside"]
const BUDGET_FULL_MS := 2.0
const BUDGET_HALF_MS := 0.7
const SCALE_TOLERANCE := 0.15
const REFILL_MAX_MS := 12.0
const MIN_CLOCK_MHZ := 1700

var _mock: Node
var _orbit: Node
var _view: Node
var _shell: Node
var _failures := 0
var _only: PackedStringArray = []
var _tag := "new"
var _results := {}
var _galaxy_key := ""
var _burner: SubViewport


func _ready() -> void:
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	Engine.max_fps = 0
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--tag="):
			_tag = a.substr(6)
		elif a.begins_with("--only="):
			_only = a.substr(7).split(",")
	await _run()
	_write_json()
	print("GPU CHECKS %s" % ("FAILED: %d" % _failures if _failures > 0 else "OK"))
	get_tree().quit(1 if _failures > 0 else 0)


func _wanted(id: String) -> bool:
	return _only.is_empty() or _only.has(id)


func _check(id: String, ok: bool, detail: String) -> void:
	if not ok:
		_failures += 1
	print("CHECK %s %s %s" % [id, "PASS" if ok else "FAIL", detail])


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _run() -> void:
	var size := get_viewport().get_visible_rect().size
	var name := RenderingServer.get_video_adapter_name()
	var ok_dev := name.contains("RTX 3060") and DisplayServer.get_name() != "headless" \
		and RenderingServer.get_current_rendering_method() == "forward_plus" \
		and RenderingServer.get_video_adapter_type() != RenderingDevice.DEVICE_TYPE_CPU \
		and size == Vector2(1920, 1080)
	_check("DEVICE", ok_dev, "adapter=%s method=%s display=%s type=%d visible_rect=%s (needs NVIDIA GeForce RTX 3060, forward_plus, x11, 1920x1080)" % [name, RenderingServer.get_current_rendering_method(), DisplayServer.get_name(), RenderingServer.get_video_adapter_type(), size])
	_results["meta"] = {"device": name, "method": RenderingServer.get_current_rendering_method(), "display": DisplayServer.get_name(), "godot": Engine.get_version_info().string, "tag": _tag}
	if not ok_dev:
		print("GPU run invalid: every number below is meaningless without the RTX 3060 at 1920x1080")

	var packed: PackedScene = load(MOCKUP_SCENE)
	_mock = packed.instantiate()
	add_child(_mock)
	await _frames(2)
	_orbit = _mock.get_node("OrbitCamera")
	_view = _mock.get_node("World/GalaxyView")
	_shell = _view.get_node_or_null("ShellRenderer")
	if _shell == null:
		_check("SHELL-GPU", false, "GalaxyView has no ShellRenderer child")
		return
	_make_burner()
	var vp: SubViewport = _shell_viewport()
	if vp == null:
		_check("SHELL-GPU", false, "cannot find the shell SubViewport (get_shell_viewport() / legacy _sub_viewport)")
		return
	RenderingServer.viewport_set_measure_render_time(vp.get_viewport_rid(), true)
	RenderingServer.viewport_set_measure_render_time(get_viewport().get_viewport_rid(), true)

	if _wanted("SHELL-GPU") or _wanted("SHELL-SCALE"):
		await _run_timing()
	if _wanted("REFILL"):
		await _check_refill()
	if _wanted("LOOK-LAYERS"):
		await _check_look_layers()
	if _wanted("SCREENSHOTS"):
		await _check_screenshots()


# ---- plumbing ------------------------------------------------------------

func _shell_viewport() -> SubViewport:
	if _shell.has_method("get_shell_viewport"):
		return _shell.get_shell_viewport()
	var legacy = _shell.get("_sub_viewport")
	return legacy if legacy is SubViewport else null


func _is_new_renderer() -> bool:
	return _shell.has_method("get_shell_viewport")


func _make_burner() -> void:
	_burner = SubViewport.new()
	_burner.size = Vector2i(2048, 2048)
	_burner.disable_3d = true
	_burner.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	var rect := ColorRect.new()
	rect.size = Vector2(2048, 2048)
	var mat := ShaderMaterial.new()
	var sh := Shader.new()
	sh.code = "shader_type canvas_item;\nvoid fragment() {\n\tfloat x = UV.x;\n\tfor (int i = 0; i < 1200; i++) { x = sin(x * 1.37 + UV.y) * 0.5 + 0.5; }\n\tCOLOR = vec4(x, x, x, 1.0);\n}\n"
	mat.shader = sh
	rect.material = mat
	_burner.add_child(rect)
	add_child(_burner)


func _set_galaxy(key: String) -> void:
	if key == _galaxy_key:
		return
	_galaxy_key = key
	if key == "big":
		_view.build(BigGalaxy.make(11, 400, 15, 9.0))
	else:
		_mock.qa_seed(11)
	await _frames(6)


func _set_pos(pos: String) -> void:
	_orbit.set_process(true)
	_orbit.set("_yaw", 0.5)
	_orbit.set("_pitch_deg", 55.0)
	var g: Galaxy = _view.get_galaxy()
	match pos:
		"d120":
			_orbit.set("_target", Vector3.ZERO)
			_mock.qa_camera(120.0, -1)
		"d25":
			_orbit.set("_target", Vector3.ZERO)
			_mock.qa_camera(25.0, -1)
		"d7.5_f0":
			_mock.qa_camera(7.5, g.factions[0].capital)
		"inside":
			_orbit.set("_target", Vector3.ZERO)
			_mock.qa_camera(25.0, -1)
			var best := -1
			var bd := -1.0
			for s in g.systems:
				if s.owner == 0 and s.pos.length() > bd:
					bd = s.pos.length()
					best = s.id
			_orbit.set_process(false)
			var cam: Camera3D = _orbit.get_camera()
			cam.global_position = g.systems[best].pos
			cam.look_at(Vector3.ZERO, Vector3.UP)
	await _frames(6)


func _gpu_clock() -> int:
	var out: Array = []
	OS.execute("nvidia-smi", ["--query-gpu=clocks.sm", "--format=csv,noheader,nounits"], out)
	return int(str(out[0]).strip_edges()) if out.size() > 0 else -1


func _median(a: Array) -> float:
	var b := a.duplicate()
	b.sort()
	return b[b.size() / 2]


func _p95(a: Array) -> float:
	var b := a.duplicate()
	b.sort()
	return b[int(b.size() * 0.95)]


func _write_json() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(RESULTS))
	var f := FileAccess.open(RESULTS + "gpu_%s.json" % _tag, FileAccess.WRITE)
	f.store_string(JSON.stringify(_results, "  "))
	f.close()


# ---- SHELL-GPU and SHELL-SCALE --------------------------------------------

func _measure(divisor: int) -> Dictionary:
	var vp := _shell_viewport()
	var rid := vp.get_viewport_rid()
	for i in WARMUP:
		RenderingServer.force_draw(false, 0.0167)
	var g: Array = []
	for i in RECORD:
		RenderingServer.force_draw(false, 0.0167)
		g.append(RenderingServer.viewport_get_measured_render_time_gpu(rid))
	return {"median_ms": _median(g), "p95_ms": _p95(g), "clock_mhz": _gpu_clock(), "viewport": [vp.size.x, vp.size.y], "divisor": divisor}


func _run_timing() -> void:
	var table := {}   # galaxy -> divisor -> pos -> stats
	for galaxy in ["big", "default"]:
		await _set_galaxy(galaxy)
		var g: Galaxy = _view.get_galaxy()
		table[galaxy] = {}
		for divisor in [2, 1]:
			table[galaxy][divisor] = {}
			if divisor != 2:
				if not "res_divisor" in _shell:
					continue
				_shell.res_divisor = divisor
				await _frames(4)
			for pos in POSITIONS:
				await _set_pos(pos)
				table[galaxy][divisor][pos] = _measure(divisor)
			if "res_divisor" in _shell:
				_shell.res_divisor = 2
		_results["timing_%s_%dsys_%dfac" % [galaxy, g.systems.size(), g.factions.size()]] = table[galaxy]
	if "res_divisor" in _shell:
		_shell.res_divisor = 2
		await _frames(4)

	if _wanted("SHELL-GPU"):
		for divisor in [1, 2]:
			var budget := BUDGET_FULL_MS if divisor == 1 else BUDGET_HALF_MS
			for pos in POSITIONS:
				var st = table["big"][divisor].get(pos)
				if st == null:
					_check("SHELL-GPU", false, "400/15 %s %s: legacy renderer has no res_divisor, cannot measure full resolution (budget %.1f ms)" % ["full" if divisor == 1 else "half", pos, budget])
					continue
				var low_clock: bool = st.clock_mhz < MIN_CLOCK_MHZ
				_check("SHELL-GPU", st.median_ms <= budget and not low_clock, "400/15 %s res %s %s: median %.3f ms p95 %.3f ms (budget %.1f ms) GPU %d MHz%s on %s" % ["full" if divisor == 1 else "half", st.viewport, pos, st.median_ms, st.p95_ms, budget, st.clock_mhz, " LOW CLOCK, run invalid" if low_clock else "", RenderingServer.get_video_adapter_name()])
	if _wanted("SHELL-SCALE"):
		for divisor in [1, 2]:
			for pos in POSITIONS:
				var a = table["big"][divisor].get(pos)
				var b = table["default"][divisor].get(pos)
				if a == null or b == null:
					_check("SHELL-SCALE", false, "%s %s: not measurable on the legacy renderer" % ["full" if divisor == 1 else "half", pos])
					continue
				var ratio: float = absf(a.median_ms - b.median_ms) / maxf(b.median_ms, 1e-6)
				_check("SHELL-SCALE", ratio <= SCALE_TOLERANCE, "%s %s: 400/15 %.3f ms vs 219/4 %.3f ms, differ %.1f%% (<= 15%%)" % ["full" if divisor == 1 else "half", pos, a.median_ms, b.median_ms, 100.0 * ratio])


# ---- REFILL --------------------------------------------------------------

func _check_refill() -> void:
	await _set_galaxy("big")
	await _set_pos("d120")
	if not _shell.has_method("get_territory_field"):
		_check("REFILL", false, "ShellRenderer has no get_territory_field() (legacy renderer)")
		return
	var field: Node = _shell.get_territory_field()
	await _frames(3)
	var g: Galaxy = _view.get_galaxy()
	var sid := -1
	for s in g.systems:
		if s.owner == 0:
			sid = s.id
			break
	var times: Array = []
	var wired := true
	for i in 14:
		var to := 1 if i % 2 == 0 else 0
		_view.set_system_owner(sid, to)
		if not field.is_dirty():
			wired = false
		var t0 := Time.get_ticks_usec()
		field.refill()
		var ms := (Time.get_ticks_usec() - t0) / 1000.0
		if i >= 2:
			times.append(ms)
		await _frames(2)
	_results["refill_ms"] = {"median": _median(times), "p95": _p95(times), "samples": times}
	_check("REFILL", wired and _median(times) <= REFILL_MAX_MS, "owner change via GalaxyView.set_system_owner marked the field dirty=%s; refill median %.2f ms p95 %.2f ms over %d (<= %.0f ms) on %s" % [wired, _median(times), _p95(times), times.size(), REFILL_MAX_MS, RenderingServer.get_video_adapter_name()])


# ---- LOOK-LAYERS ---------------------------------------------------------

func _check_look_layers() -> void:
	if not (_shell.has_method("set_debug_mode") and _shell.has_method("get_territory_field")):
		_check("LOOK-LAYERS", false, "ShellRenderer has no set_debug_mode()/get_territory_field() (legacy renderer)")
		return
	await _set_galaxy("default")
	await _set_pos("d120")
	var table := await _calibrate_layer_decode()
	if table.is_empty():
		_check("LOOK-LAYERS", false, "layer-count readout calibration failed")
		return
	_shell.set_debug_mode(1)
	await _frames(5)
	var vp := _shell_viewport()
	var img := vp.get_texture().get_image()
	_shell.set_debug_mode(0)
	var grid = GridSampler.from_field(_shell.get_territory_field())
	var cam: Camera3D = _orbit.get_camera()
	var div: int = _shell.res_divisor if "res_divisor" in _shell else 2
	var over := 0
	var over4 := 0
	var sampled := 0
	var drawn := 0
	var control_pixels := 0
	var worst := ""
	for py in range(8, img.get_height(), 24):
		for px in range(8, img.get_width(), 24):
			var layers := _decode_layers(img.get_pixel(px, py), table)
			var screen := Vector2((px + 0.5) * div, (py + 0.5) * div)
			var cpu := _cpu_layers(grid, cam.project_ray_origin(screen), cam.project_ray_normal(screen))
			sampled += 1
			if layers > 0:
				drawn += 1
			if cpu.crossings > cpu.distinct:
				control_pixels += 1
			if layers > cpu.distinct:
				over += 1
				if worst == "":
					worst = "pixel %d,%d drew %d layers, CPU counts %d distinct factions (%d crossings)" % [px, py, layers, cpu.distinct, cpu.crossings]
			if layers > 4:
				over4 += 1
	_check("LOOK-LAYERS", over == 0 and over4 == 0 and drawn > 0, "seed 11 d120: %d pixels sampled, %d with a drawn shell; layer count above the faction count on %d, above 4 on %d %s" % [sampled, drawn, over, over4, worst])
	_check("LOOK-LAYERS-control", control_pixels > 0, "%d sampled rays cross more surfaces than they have distinct factions, so a renderer that draws every crossing would fail LOOK-LAYERS" % control_pixels)


# Render known layer counts through a calibration quad in a viewport set up like
# the shell's, and read back the bytes: {count: red value 0..1}.
func _calibrate_layer_decode() -> Dictionary:
	var vp := SubViewport.new()
	vp.size = Vector2i(32, 32)
	vp.transparent_bg = true
	vp.own_world_3d = true
	vp.msaa_3d = Viewport.MSAA_DISABLED
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(vp)
	var cam := Camera3D.new()
	cam.current = true
	vp.add_child(cam)
	var quad := MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = Vector2(2, 2)
	quad.mesh = q
	quad.extra_cull_margin = 16384.0
	var mat := ShaderMaterial.new()
	var sh := Shader.new()
	sh.code = "shader_type spatial;\nrender_mode unshaded, blend_mix, depth_test_disabled, cull_disabled;\nuniform float count = 0.0;\nvoid vertex() { POSITION = vec4(VERTEX.xy, 1.0, 1.0); }\nvoid fragment() { ALBEDO = vec3(count / 16.0, 0.0, 0.0); ALPHA = 1.0; }\n"
	mat.shader = sh
	quad.material_override = mat
	vp.add_child(quad)
	var table := {}
	for c in 5:
		mat.set_shader_parameter("count", float(c))
		await _frames(4)
		var px := vp.get_texture().get_image().get_pixel(16, 16)
		table[c] = px.r
	vp.queue_free()
	print("LOOK-LAYERS calibration (count -> red): %s" % [table])
	for c in range(1, 5):
		if table[c] <= table[c - 1] + 0.01:
			return {}
	return table


func _decode_layers(px: Color, table: Dictionary) -> int:
	var best := 0
	var bd := INF
	for c in table:
		var d := absf(px.r - table[c])
		if d < bd:
			bd = d
			best = c
	return best


# Distinct factions (ids met where net >= ISO - 0.02, so a grazing sliver thinner
# than a step cannot make the card's layer look like an overcount) and number of
# surface entries (net >= ISO) along a ray through the grid, stepping 0.1 units.
func _cpu_layers(grid, o: Vector3, d: Vector3) -> Dictionary:
	var b := o.dot(d)
	var disc := b * b - (o.length_squared() - 66.0 * 66.0)
	if disc <= 0.0:
		return {"distinct": 0, "crossings": 0}
	var s := sqrt(disc)
	var t := maxf(-b - s, 0.0)
	var t1 := -b + s
	var ids := {}
	var crossings := 0
	var inside := false
	while t <= t1:
		var p := o + d * t
		var v: float = grid.net(p)
		if v >= GridSampler.ISO - 0.02:
			ids[grid.id_at(p)] = true
		var now := v >= GridSampler.ISO
		if now and not inside:
			crossings += 1
		inside = now
		t += 0.1
	return {"distinct": ids.size(), "crossings": crossings}


# ---- SCREENSHOTS ---------------------------------------------------------

func _check_screenshots() -> void:
	var dir := ProjectSettings.globalize_path(RESULTS) + "look/"
	DirAccess.make_dir_recursive_absolute(dir + "old")
	DirAccess.make_dir_recursive_absolute(dir + "new")
	if _tag == "new" and not _is_new_renderer():
		_check("SCREENSHOTS", false, "the renderer in the scene is the legacy one; refusing to save its pictures as the new ones (run with --tag old to capture the old look)")
		return
	var made: Array = []
	for galaxy in ["default", "big"]:
		await _set_galaxy(galaxy)
		for pos in POSITIONS:
			await _set_pos(pos)
			await _frames(3)
			var img := get_viewport().get_texture().get_image()
			var key := "%s_%s" % [galaxy, pos]
			img.save_jpg("%s%s/%s.jpg" % [dir, _tag, key], 0.9)
			made.append(key)
	var composites := 0
	var missing: Array = []
	for key in made:
		var old_img := Image.load_from_file("%sold/%s.jpg" % [dir, key])
		var new_img := Image.load_from_file("%snew/%s.jpg" % [dir, key])
		if old_img == null or new_img == null:
			missing.append(key)
			continue
		old_img.resize(960, 540, Image.INTERPOLATE_LANCZOS)
		new_img.resize(960, 540, Image.INTERPOLATE_LANCZOS)
		var sheet := Image.create(1924, 540, false, Image.FORMAT_RGB8)
		sheet.fill(Color.WHITE)
		old_img.convert(Image.FORMAT_RGB8)
		new_img.convert(Image.FORMAT_RGB8)
		sheet.blit_rect(old_img, Rect2i(0, 0, 960, 540), Vector2i(0, 0))
		sheet.blit_rect(new_img, Rect2i(0, 0, 960, 540), Vector2i(964, 0))
		sheet.save_jpg("%s%s.jpg" % [dir, key], 0.9)
		composites += 1
	_check("SCREENSHOTS", missing.is_empty() and composites == 8, "tag %s: %d pictures saved; %d old|new composites written to results/look/ (need 8: 2 galaxies x 4 positions); missing a side: %s" % [_tag, made.size(), composites, missing])

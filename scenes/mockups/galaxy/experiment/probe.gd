extends Node
# Throwaway experiment harness. Usage (see run_probe.sh):
#   godot ... probe.tscn -- --cfg=<cfg.json>
# cfg: {"out": "name", "runs": [{"name","galaxy":"default|big","mode":"old_on|old_off|field|bake","variant":{steps,cross,skip,refine,divisor},"grid":96}]}
const FieldBake := preload("res://scenes/mockups/galaxy/experiment/field_bake.gd")
const FieldRenderer := preload("res://scenes/mockups/galaxy/experiment/field_renderer.gd")
const WARMUP := 60
const RECORD := 120
const OUT_DIR := "res://scenes/mockups/galaxy/experiment/results/"

var _mock: Node
var _orbit: Node
var _view: Node
var _shell: Node
var _field: Node3D
var _cfg: Dictionary
var _galaxy_key := ""
var _bakes := {}    # grid -> {vol, skip, fb, wall_ms, gpu_ms}
var _results: Array = []
var _shots_dir := ""
var _dump_dir := ""

func _ready() -> void:
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	Engine.max_fps = 0
	var cfgpath := ""
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--cfg="):
			cfgpath = a.substr(6)
		if a.begins_with("--dump="):
			_dump_dir = a.substr(7)
	_cfg = JSON.parse_string(FileAccess.get_file_as_string(cfgpath))
	_shots_dir = ProjectSettings.globalize_path(OUT_DIR) + "shots/"
	DirAccess.make_dir_recursive_absolute(_shots_dir)
	var scene: PackedScene = load("res://scenes/mockups/galaxy/galaxy_mockup.tscn")
	_mock = scene.instantiate()
	add_child(_mock)
	await get_tree().process_frame
	_orbit = _mock.get_node("OrbitCamera")
	_view = _mock.get_node("World/GalaxyView")
	_shell = _view._shell
	_field = FieldRenderer.new()
	_view.add_child(_field)
	_field.setup(_orbit.get_zoom_controller())
	_field.set_enabled(false)
	var meta := {
		"device": RenderingServer.get_video_adapter_name(),
		"vendor": RenderingServer.get_video_adapter_vendor(),
		"api": RenderingServer.get_video_adapter_api_version(),
		"method": RenderingServer.get_current_rendering_method(),
		"adapter_type": RenderingServer.get_video_adapter_type(),
		"godot": Engine.get_version_info().string,
		"window": [get_window().size.x, get_window().size.y],
		"visible_rect": [get_viewport().get_visible_rect().size.x, get_viewport().get_visible_rect().size.y],
		"vsync_mode": DisplayServer.window_get_vsync_mode(),
		"display_driver": DisplayServer.get_name(),
		"headless": DisplayServer.get_name() == "headless",
	}
	print("PROBE device=", meta.device, " method=", meta.method, " display=", meta.display_driver)
	RenderingServer.viewport_set_measure_render_time(get_viewport().get_viewport_rid(), true)
	RenderingServer.viewport_set_measure_render_time(_shell._sub_viewport.get_viewport_rid(), true)
	for run in _cfg.runs:
		await _do_run(run)
	var out := {"meta": meta, "runs": _results}
	var f := FileAccess.open(OUT_DIR + str(_cfg.out) + ".json", FileAccess.WRITE)
	f.store_string(JSON.stringify(out, "  "))
	f.close()
	print("PROBE done ", _cfg.out)
	get_tree().quit()

func _set_galaxy(key: String) -> void:
	if key == _galaxy_key:
		return
	_galaxy_key = key
	if key == "big":
		GalaxyGen.exp_system_count = 400
		GalaxyGen.exp_faction_count = 15
		GalaxyGen.exp_min_spacing = 9.0
	else:
		GalaxyGen.exp_system_count = 0
		GalaxyGen.exp_faction_count = 0
		GalaxyGen.exp_min_spacing = 0.0
	_mock.qa_seed(11)
	_bakes.clear()
	for i in 5:
		await get_tree().process_frame

func _ensure_bake(grid: int) -> Dictionary:
	if _bakes.has(grid):
		return _bakes[grid]
	var g: Galaxy = _view.get_galaxy()
	var data := FieldBake.system_data(g)
	var fb := FieldBake.new()
	add_child(fb)
	fb.setup(grid)
	await get_tree().process_frame
	await get_tree().process_frame
	await fb.bake(data)
	for i in 4:
		await get_tree().process_frame
	await fb.bake(data)   # second run: shader compiled, caches warm
	for i in 4:
		await get_tree().process_frame
	var gpu := RenderingServer.viewport_get_measured_render_time_gpu(fb._vp.get_viewport_rid())
	var skip := fb.build_skip(16)
	_bakes[grid] = {"fb": fb, "vol": fb.volume, "skip": skip, "wall_ms": fb.last_wall_ms, "gpu_ms": gpu, "parts": fb.last_parts}
	if _dump_dir != "":
		var key := "%s_g%d" % [_galaxy_key, grid]
		fb.dump(_dump_dir + "/" + key)
	return _bakes[grid]

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
			var cam: Camera3D = _orbit.get_node("../Camera3D") if _orbit.has_node("../Camera3D") else _orbit.get_child(0)
			cam.global_position = g.systems[best].pos
			cam.look_at(Vector3.ZERO, Vector3.UP)

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

func _stats(a: Array) -> Dictionary:
	return {"median": _median(a), "p95": _p95(a), "mean": _mean(a)}

func _mean(a: Array) -> float:
	var s := 0.0
	for v in a:
		s += v
	return s / maxf(a.size(), 1)

func _do_run(run: Dictionary) -> void:
	await _set_galaxy(run.get("galaxy", "default"))
	var mode: String = run.mode
	if mode == "bake":
		_shell._overlay.visible = false
		_shell._sub_viewport.render_target_update_mode = SubViewport.UPDATE_DISABLED
		_field.set_enabled(false)
		await _bake_bench(run)
		return
	# mode setup
	var on_old := mode == "old_on"
	_shell._overlay.visible = on_old
	_shell._sub_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS if on_old else SubViewport.UPDATE_DISABLED
	var field_on := mode == "field"
	_field.set_enabled(field_on)
	var extra := {}
	if field_on:
		var v: Dictionary = run.variant
		var grid := int(run.get("grid", 96))
		var b := await _ensure_bake(grid)
		_field.apply_variant(v)
		var fb = b.fb
		_field.set_volume(b.vol, b.skip, fb.gmin, fb.gsize, grid, FieldBake.palette_for(_view.get_galaxy()))
	var g: Galaxy = _view.get_galaxy()
	var res := {"name": run.name, "galaxy": run.get("galaxy", "default"), "mode": mode, "variant": run.get("variant", {}), "grid": run.get("grid", 0), "systems": g.systems.size(), "factions": g.factions.size(), "positions": {}}
	var main_rid := get_viewport().get_viewport_rid()
	var old_rid: RID = _shell._sub_viewport.get_viewport_rid()
	var field_rid: RID = _field.sub_viewport.get_viewport_rid()
	for pos in run.get("positions", ["d120", "d25", "d7.5_f0", "inside"]):
		_set_pos(pos)
		# 1) normal frames: scene scripts run (camera sync, band opacity); sample CPU process time
		var pt: Array = []
		for i in 24:
			await get_tree().process_frame
			if i >= 4:
				pt.append(Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0)
		# 2) back-to-back renders without presenting: the GPU stays busy so its clocks
		# stay up (with presented frames under Xvfb the GPU idles ~90% of each frame
		# and drops to idle clocks, inflating light workloads by up to ~15x).
		for i in WARMUP:
			RenderingServer.force_draw(false, 0.0167)
		var gm: Array = []
		var go: Array = []
		var gf: Array = []
		var dc: Array = []
		var ft: Array = []
		for i in RECORD:
			var t_a := Time.get_ticks_usec()
			RenderingServer.force_draw(false, 0.0167)
			ft.append((Time.get_ticks_usec() - t_a) / 1000.0)
			gm.append(RenderingServer.viewport_get_measured_render_time_gpu(main_rid))
			go.append(RenderingServer.viewport_get_measured_render_time_gpu(old_rid) if on_old else 0.0)
			gf.append(RenderingServer.viewport_get_measured_render_time_gpu(field_rid) / float(_field.reps) if field_on else 0.0)
			dc.append(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))
		var clk := _gpu_clock()
		var reps_used: int = _field.reps
		if field_on:
			_field.set_reps(1)   # screenshot must show one pass, not the timing amplification
		for i in 3:
			await get_tree().process_frame
		var img := get_viewport().get_texture().get_image()
		img.save_png(_shots_dir + "%s__%s.png" % [run.name, pos])
		if field_on:
			_field.set_reps(reps_used)
		res.positions[pos] = {
			"gpu_main_ms": _stats(gm), "gpu_old_shell_vp_ms": _stats(go), "gpu_field_vp_ms": _stats(gf), "field_reps": reps_used,
			"draw_calls": _stats(dc), "process_ms": _stats(pt), "force_draw_call_ms": _stats(ft), "gpu_sm_clock_mhz": clk,
		}
		print("PROBE ", run.name, " ", pos, " main=", snapped(_median(gm), 0.01), " old=", snapped(_median(go), 0.01), " field=", snapped(_median(gf), 0.01), " draw_ms=", snapped(_median(ft), 0.01), " clk=", clk, " proc=", snapped(_median(pt), 0.01))
	_results.append(res)

func _bake_bench(run: Dictionary) -> void:
	var out := {"name": run.name, "mode": "bake", "galaxy": _galaxy_key, "grids": {}}
	var g: Galaxy = _view.get_galaxy()
	for grid in run.get("grids", [64, 96, 128]):
		var data := FieldBake.system_data(g)
		var fb := FieldBake.new()
		add_child(fb)
		fb.setup(grid)
		await get_tree().process_frame
		await get_tree().process_frame
		var rid: RID = fb._vp.get_viewport_rid()
		var fulls: Array = []
		var full_gpu: Array = []
		var full_parts: Array = []
		for k in 8:
			await fb.bake(data)
			RenderingServer.force_draw(false, 0.0)
			if k > 1:
				fulls.append(fb.last_wall_ms)
				full_gpu.append(RenderingServer.viewport_get_measured_render_time_gpu(rid))
				full_parts.append(fb.last_parts)
		# GPU time of the bake pass itself: steady-state difference between a back-to-back
		# force_draw loop that re-runs the bake each iteration and one that does not
		# (the canvas-only SubViewport reports no viewport GPU time, so this is derived).
		fb._upload(data)
		for i in 20:
			RenderingServer.force_draw(false, 0.0)
		var t_b0 := Time.get_ticks_usec()
		for i in 100:
			RenderingServer.force_draw(false, 0.0)
		var base_ms := (Time.get_ticks_usec() - t_b0) / 100000.0
		var t_b1 := Time.get_ticks_usec()
		for i in 100:
			fb._vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
			fb._vp.render_target_update_mode = SubViewport.UPDATE_ONCE
			RenderingServer.force_draw(false, 0.0)
		var with_ms := (Time.get_ticks_usec() - t_b1) / 100000.0
		var bake_gpu_ms := with_ms - base_ms
		var t_skip0 := Time.get_ticks_usec()
		fb.build_skip(16)
		var skip_ms := (Time.get_ticks_usec() - t_skip0) / 1000.0
		# one owner change: flip one border system of faction 0 to faction 1
		var data2 := FieldBake.system_data(g)
		var idx := -1
		for i in data2.fid.size():
			if data2.fid[i] == 0:
				idx = i
				break
		data2.fid[idx] = 1
		var refills: Array = []
		var refill_gpu: Array = []
		for k in 8:
			await fb.bake(data2 if k % 2 == 0 else data)
			RenderingServer.force_draw(false, 0.0)
			if k > 1:
				refills.append(fb.last_wall_ms)
				refill_gpu.append(RenderingServer.viewport_get_measured_render_time_gpu(rid))
		var bytes_per := 8   # RGBAH as built
		out.grids[str(grid)] = {
			"full_wall_ms": _stats(fulls), "full_gpu_ms": _stats(full_gpu), "parts_last": full_parts.back(),
			"refill_wall_ms": _stats(refills), "refill_gpu_ms": _stats(refill_gpu),
			"scene_only_draw_ms": base_ms, "scene_plus_bake_draw_ms": with_ms, "bake_pass_gpu_ms_derived": bake_gpu_ms, "skip_build_ms": skip_ms, "gpu_sm_clock_mhz": _gpu_clock(),
			"mem_bytes_rgbah": grid * grid * grid * 8, "mem_bytes_packed_rgh_r8": grid * grid * grid * 5,
		}
		print("PROBE bake ", _galaxy_key, " ", grid, " full wall ", snapped(_median(fulls), 0.01), " gpu ", snapped(_median(full_gpu), 0.001), " refill wall ", snapped(_median(refills), 0.01), " bake_gpu_derived ", snapped(bake_gpu_ms, 0.001), " (", snapped(base_ms, 0.001), " -> ", snapped(with_ms, 0.001), ")")
		fb.queue_free()
	_results.append(out)

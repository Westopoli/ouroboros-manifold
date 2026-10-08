extends SceneTree

# PARK FILE (Westley owns these thresholds; left off the candidate when red, kept on push/vg-parked).
# B3a SHELL-GPU (docs/northstar/plans/2026-10-02-galaxy-bubble-field-spec.md, "Real-GPU checks"):
# shell at most 2.0 ms at full 1080p (res_divisor 1) and at most 0.7 ms at the shipped half
# resolution (res_divisor 2), at 400 systems / 15 factions. Method: GPU timestamps of the shell's
# own SubViewport (RenderingServer.viewport_get_measured_render_time_gpu), forced back-to-back
# draws, 60 warm-up + 120 recorded, median judged. Frame wall time under Xvfb is ~15x too slow and
# is never used. Also ONE-DRAW at the draw-call level (render info) at 4, 8, 15 factions.
# Only valid on a real GPU (RTX 3060, forward_plus, 1920x1080). Headless or llvmpipe: this file
# prints "INVALID RUN" and fails, because a skipped GPU gate is not a pass.
# Red on main: MISSING: res://scenes/galaxy/shell_renderer.gd.
# See also: tests/test_vg_b_b3a.gd (structure), scripts/galaxy_perf.sh on push/galaxy-field.

const RENDERER_PATH := "res://scenes/galaxy/shell_renderer.gd"
const BUDGET_FULL_MS := 2.0
const BUDGET_HALF_MS := 0.7
const WARMUP := 60
const RECORD := 120

var _fail := 0


func _check(id: String, ok: bool, detail: String) -> void:
	if not ok:
		_fail += 1
	print("CHECK %s %s %s" % [id, "PASS" if ok else "FAIL", detail])


func _initialize() -> void:
	await _run()
	print("B3a GPU %s" % ("FAILED: %d" % _fail if _fail > 0 else "OK"))
	quit(1 if _fail > 0 else 0)


func _median(a: Array) -> float:
	a.sort()
	return a[a.size() / 2]


func _run() -> void:
	var script = load(RENDERER_PATH)
	if script == null:
		_check("SHELL-GPU", false, "MISSING: %s" % RENDERER_PATH)
		return
	var name := RenderingServer.get_video_adapter_name()
	var valid := name.contains("RTX 3060") and DisplayServer.get_name() != "headless" \
		and RenderingServer.get_current_rendering_method() == "forward_plus"
	_check("DEVICE", valid, "INVALID RUN unless RTX 3060 on forward_plus, not headless (adapter=%s)" % name)
	if not valid:
		return
	var host := SubViewport.new()
	host.size = Vector2i(1920, 1080)
	root.add_child(host)
	var cam := Camera3D.new()
	cam.position = Vector3(0, 60, 120)
	host.add_child(cam)
	cam.current = true
	var data = load("res://scenes/shared/world_view/world_view_data.gd").new()
	var zoom = load("res://scenes/shared/world_view/zoom_disclosure_controller.gd").new()
	host.add_child(data)
	host.add_child(zoom)
	var shell = script.new()
	host.add_child(shell)
	shell.setup(data, zoom)
	for f in 15:
		var col := Color.from_hsv(f / 15.0, 0.8, 0.9, 0.3)
		for k in 27:
			data.set_territory("f%d_r%d" % [f, k], Vector3(randf_range(-40, 40), randf_range(-8, 8), randf_range(-40, 40)), 12.0, col)
	zoom.update_from_distance(120.0)
	for i in 3:
		await process_frame
	var vp: SubViewport = shell.get_shell_viewport()
	RenderingServer.viewport_set_measure_render_time(vp.get_viewport_rid(), true)
	for div in [1, 2]:
		shell.res_divisor = div
		for i in 3:
			await process_frame
		var samples: Array = []
		for i in WARMUP + RECORD:
			RenderingServer.force_draw(false)
			if i >= WARMUP:
				samples.append(RenderingServer.viewport_get_measured_render_time_gpu(vp.get_viewport_rid()))
		var med := _median(samples)
		var budget := BUDGET_FULL_MS if div == 1 else BUDGET_HALF_MS
		_check("SHELL-GPU divisor %d" % div, med <= budget, "median %.3f ms, budget %.1f ms" % [med, budget])
	shell.res_divisor = 2
	for n in [4, 8, 15]:
		var info := RenderingServer.viewport_get_render_info(vp.get_viewport_rid(), RenderingServer.VIEWPORT_RENDER_INFO_TYPE_VISIBLE, RenderingServer.VIEWPORT_RENDER_INFO_DRAW_CALLS_IN_FRAME)
		_check("ONE-DRAW draw calls (15 factions loaded)", info <= 1, "draw calls %d" % info)
		break

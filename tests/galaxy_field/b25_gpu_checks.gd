extends Node
# Real-GPU checks for the vast-space backdrop of the live galaxy rig (piece VG-B25-vast-space, lane B,
# docs/northstar/plans/2026-10-07-visible-game-spec.md Rev 12d, paragraph "VG-B25-vast-space";
# Step 5 of docs/northstar/plans/2026-10-02-galaxy-bubble-field-spec.md; Architect gap 7 ruling 2026-10-12).
# NOT a tests/test_*.gd file and not run by the gate: a scene with a Node script, run by hand on the RTX 3060.
#
# LAUNCHER (the run is wrapped by this line; SHADER-COMPILES scans the Godot log of the run it wraps):
#   timeout 1800 xvfb-run -a -s '-screen 0 1920x1080x24' godot.real --path . --rendering-driver vulkan --rendering-method forward_plus --resolution 1920x1080 --disable-vsync res://tests/galaxy_field/b25_gpu_checks.tscn
#   (the SHADER-COMPILES scan reads Godot's default file log, user://logs/godot.log; to scan a log of your own add
#    --log-file "$L" before the scene path and -- --log="$L" after it.)
#   (long runs: systemd-run --user --scope -q -p MemoryMax=6G -p MemorySwapMax=0 -- nice -n 10 <the line above>;
#    run `godot.real --headless --import` once first; exit code 0 only if every check passes.)
#
# Proves (Westley 2026-10-02, quoted in the spec paragraph): "vast space gets the dim wash, real-depth star layers and
#   fading edges together", with the Step 5 budget "Real GPU: backdrop adds at most 0.5 ms at all four positions; shaders
#   compile" and the spec paragraph's "at most 6 added draws" [W 2026-10-02 budget]. Bible E-16:
#   R-106-05 (as it stands on main, to be rewritten by the piece): "Given the world view, When idle, Then ambient rings,
#   inflow streams, dust, a starfield and a central glow fill the space behind the territory at low opacity."
#   S-106 "A 3D star map where territory glows, borders touch, and war flashes."
#   S-107 "Pan, zoom, orbit, focus a system, pick out a faction."
#   Westley 2026-10-12 on the B23 S-107 frame: "still lacking the 3 things that were decided on regarding making the
#   galaxy feel less like it's an isolated ball".
#
# Checks, each printing a line  CHECK <ID> PASS|FAIL <detail>:
#   DEVICE            adapter contains RTX 3060, forward_plus, a real display, not a CPU device, visible rect 1920x1080
#                     (otherwise "GPU run invalid" is printed and the GPU rows fail)
#   BACKDROP-GPU      median GPU ms of the root viewport, backdrop nodes hidden versus shown, at d120, d25, d7.5 focused
#                     on the player's faction region, and inside a shell: the difference is at most BUDGET_MS
#   BACKDROP-DRAWS    RenderingServer total draw calls in frame, shown minus hidden, at most MAX_ADDED_DRAWS
#   BACKDROP-MESH     the rows the headless file cannot hold: each StarLayer's ArrayMesh vertex array equals
#                     ambient_rig.layer_star_positions(i, tier), PRIMITIVE_POINTS, one surface; the CameraDust MultiMesh
#                     instance count equals DUST_COUNT and its transforms equal get_dust_positions()
#   SHADER-COMPILES   the Godot log of the launcher-line run has no SHADER ERROR / SCRIPT ERROR / Parse Error
# Positive controls (each green on the tree without the backdrop, printed before the row they guard):
#   DEVICE; BACKDROP-GPU-CONTROL (a deliberate full-screen heavy canvas shader adds more than BUDGET_MS, so the method
#   can see a breach); BACKDROP-DRAWS-CONTROL (one added single-surface box adds at least one draw call);
#   SHADER-COMPILES-CONTROL (the scan flags a sample error line, passes a clean one, and the log holds the Vulkan banner).
# On a tree without the backdrop nodes the rows BACKDROP-GPU, -DRAWS and -MESH fail "absent"; the baseline lines
# (BASELINE <position> ...) print the rig-without-backdrop frame time and draws, which is the number to beat.
#
# MEASUREMENT METHOD (copied from scenes/mockups/galaxy/tests/gpu_checks.gd and scripts/galaxy_perf.sh on
# origin/push/galaxy-field 99f35887; kept here because it is easy to get wrong):
#  - Window-free: Xvfb + Vulkan, so nothing opens on the owner's desktop.
#  - Presented frames under Xvfb take 60-130 ms each (the driver copies every frame to the X server), the GPU idles ~90%
#    between frames and drops to 200-900 MHz, and ordinary frame timing reads about 15x too slow. So: never use frame
#    time or Performance.TIME_PROCESS here.
#  - GPU time is RenderingServer.viewport_get_measured_render_time_gpu of the root viewport (timestamps, not wall
#    clock); the backdrop is drawn by the root viewport's 3D scene (the galaxy shell has its own SubViewport and does
#    not enter this number).
#  - Frames are drawn back to back with RenderingServer.force_draw(false) (no present), 60 warm-up then 120 recorded;
#    median and p95 are reported, the budget is judged on the median.
#  - A burner SubViewport (a heavy full-surface canvas shader, drawn every frame) keeps the GPU saturated so its clocks
#    stay at their maximum even when the scene alone would take 0.1 ms. Viewport timestamps are per viewport and the
#    card runs one queue, so the burner does not enter the root viewport's number. The SM clock is sampled with
#    nvidia-smi after each run and flagged below MIN_CLOCK_MHZ.
#  - Every number is only valid when DEVICE names the RTX 3060 on forward_plus at 1920x1080; llvmpipe, the dummy
#    renderer or another window size invalidates the run.

const AMBIENT_RIG_PATH := "res://scenes/galaxy/ambient_rig.gd"
const VIEW_SCENE := "res://scenes/galaxy/galaxy_view.tscn"
const FIXTURE_PATH := "res://tests/transport/fixtures/snapshot_seed1_tick10.json"
const PLAYER_FACTION := 0   # galaxy_view.gd PLAYER_OWNER_VAL: faction 0 is the player's faction (the fixture has no player_faction key)
const STAR_LAYERS := 4
const BACKDROP_NODES := ["Wash", "StarLayer0", "StarLayer1", "StarLayer2", "StarLayer3", "CameraDust"]
const POSITIONS := ["d120", "d25", "d7.5_player", "inside_shell"]

# [W 2026-10-02 budget]: the backdrop adds at most 0.5 ms at all four camera positions. Written once.
const BUDGET_MS := 0.5
# Step 5 / the spec paragraph: "at most 6 added draws" (six nodes, one surface each).
const MAX_ADDED_DRAWS := 6
# scenes/mockups/galaxy/tests/gpu_checks.gd:43-44 (origin/push/galaxy-field 99f35887).
const WARMUP := 60
const RECORD := 120
# scenes/mockups/galaxy/tests/gpu_checks.gd:50 (origin/push/galaxy-field 99f35887): a run below this SM clock is invalid.
const MIN_CLOCK_MHZ := 1700
const LOG_ERROR_MARKERS := ["SHADER ERROR", "SCRIPT ERROR", "Parse Error"]

var _failures := 0
var _view: Node
var _rig: Node
var _rig_script: GDScript
var _camera: Camera3D
var _burner: SubViewport
var _device_ok := false
var _tier := 0


func _ready() -> void:
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	Engine.max_fps = 0
	await _run()
	print("GPU CHECKS %s" % ("FAILED: %d" % _failures if _failures > 0 else "OK"))
	get_tree().quit(1 if _failures > 0 else 0)


func _check(id: String, ok: bool, detail: String) -> void:
	if not ok:
		_failures += 1
	print("CHECK %s %s %s" % [id, "PASS" if ok else "FAIL", detail])


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _run() -> void:
	var size := get_viewport().get_visible_rect().size
	var adapter := RenderingServer.get_video_adapter_name()
	_device_ok = adapter.contains("RTX 3060") and DisplayServer.get_name() != "headless" \
		and RenderingServer.get_current_rendering_method() == "forward_plus" \
		and RenderingServer.get_video_adapter_type() != RenderingDevice.DEVICE_TYPE_CPU \
		and size == Vector2(1920, 1080)
	_check("DEVICE", _device_ok, "adapter=%s method=%s display=%s type=%d visible_rect=%s (needs NVIDIA GeForce RTX 3060, forward_plus, x11, 1920x1080)" % [adapter, RenderingServer.get_current_rendering_method(), DisplayServer.get_name(), RenderingServer.get_video_adapter_type(), size])
	if not _device_ok:
		print("GPU run invalid: every number below is meaningless without the RTX 3060 at 1920x1080")

	if not await _load_view():
		return
	_make_burner()
	RenderingServer.viewport_set_measure_render_time(get_viewport().get_viewport_rid(), true)

	await _check_gpu_and_draws()
	_check_mesh()
	_check_shader_compiles()


# ---- scene: the live galaxy view with the game's 80-region fixture ------------------------------

func _load_view() -> bool:
	var f := FileAccess.open(FIXTURE_PATH, FileAccess.READ)
	var snap = JSON.parse_string(f.get_as_text()) if f != null else null
	if not (snap is Dictionary):
		_check("BACKDROP-GPU", false, "fixture %s unreadable" % FIXTURE_PATH)
		return false
	_view = (load(VIEW_SCENE) as PackedScene).instantiate()
	_view.driven = true
	add_child(_view)
	await _frames(2)
	_view.set_snapshot(snap)
	await _frames(3)
	_rig = _view.get_node_or_null("AmbientRig")
	_camera = _view.get_node("OrbitCamera/Camera3D")
	if _rig == null or _camera == null:
		_check("BACKDROP-GPU", false, "galaxy_view has no AmbientRig / OrbitCamera/Camera3D (rig=%s camera=%s)" % [_rig, _camera])
		return false
	_rig_script = load(AMBIENT_RIG_PATH)
	_tier = int(_view.qa_state().get("quality_tier", 0))
	var owners: Dictionary = _view.qa_state()["owners"]
	var mine := 0
	for id in owners:
		if int(owners[id]) == PLAYER_FACTION:
			mine += 1
	# Premises dumped (rules.md section (d)): the numbers the positions rely on.
	print("PREMISES systems=%d owner%d_regions=%d tier=%d camera_far=%s adapter=%s" % [int(_view.qa_state()["system_count"]), PLAYER_FACTION, mine, _tier, _camera.far, RenderingServer.get_video_adapter_name()])
	return true


# The player's region (lowest id owned by faction 0) and the faction-0 region nearest the centroid of faction 0's systems
# (the camera goes there for "inside a shell": a shell is drawn around its faction's systems).
func _player_regions() -> Dictionary:
	var owners: Dictionary = _view.qa_state()["owners"]
	var pos: Dictionary = _view.get_positions()
	var ids: Array = []
	for id in owners:
		if int(owners[id]) == PLAYER_FACTION and pos.has(id):
			ids.append(int(id))
	ids.sort()
	if ids.is_empty():
		return {"focus": -1, "inner": -1}
	var centroid := Vector3.ZERO
	for id in ids:
		centroid += pos[id]
	centroid /= float(ids.size())
	var inner: int = ids[0]
	for id in ids:
		if (pos[id] as Vector3).distance_to(centroid) < (pos[inner] as Vector3).distance_to(centroid):
			inner = id
	return {"focus": ids[0], "inner": inner}


func _set_pos(position_id: String) -> void:
	var mine := _player_regions()
	var pos: Dictionary = _view.get_positions()
	match position_id:
		"d120":
			_view.qa_camera(120.0, -1)
		"d25":
			_view.qa_camera(25.0, -1)
		"d7.5_player":
			_view.qa_camera(7.5, int(mine["focus"]))
		"inside_shell":
			_view.qa_camera(25.0, -1)
			var at: Vector3 = pos[int(mine["inner"])]
			_camera.global_position = at
			var look: Vector3 = Vector3.ZERO if at.length() > 1.0 else Vector3(0.0, -0.5, -1.0)
			_camera.look_at(look, Vector3.UP)
	await _frames(6)


# ---- the burner keeps the GPU clocks up (see MEASUREMENT METHOD) ---------------------------------

func _make_burner() -> void:
	_burner = SubViewport.new()
	_burner.size = Vector2i(2048, 2048)
	_burner.disable_3d = true
	_burner.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	var rect := ColorRect.new()
	rect.size = Vector2(2048, 2048)
	rect.material = _heavy_material()
	_burner.add_child(rect)
	add_child(_burner)


func _heavy_material() -> ShaderMaterial:
	var mat := ShaderMaterial.new()
	var sh := Shader.new()
	sh.code = "shader_type canvas_item;\nvoid fragment() {\n\tfloat x = UV.x;\n\tfor (int i = 0; i < 1200; i++) { x = sin(x * 1.37 + UV.y) * 0.5 + 0.5; }\n\tCOLOR = vec4(x, x, x, 1.0);\n}\n"
	mat.shader = sh
	return mat


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


# ---- BACKDROP-GPU and BACKDROP-DRAWS ------------------------------------------------------------

func _backdrop_nodes() -> Array:
	var found: Array = []
	if _rig == null:
		return found
	for n in BACKDROP_NODES:
		var node := _rig.get_node_or_null(n)
		if node != null:
			found.append(node)
	return found


func _set_backdrop_visible(on: bool) -> void:
	for node in _backdrop_nodes():
		node.visible = on


# 60 warm-up and 120 recorded back-to-back force_draw(false) draws; GPU ms of the root viewport and total draw calls.
func _measure() -> Dictionary:
	var rid := get_viewport().get_viewport_rid()
	for i in WARMUP:
		RenderingServer.force_draw(false, 0.0167)
	var g: Array = []
	var draws := 0
	for i in RECORD:
		RenderingServer.force_draw(false, 0.0167)
		g.append(RenderingServer.viewport_get_measured_render_time_gpu(rid))
		draws = int(RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME))
	return {"median_ms": _median(g), "p95_ms": _p95(g), "clock_mhz": _gpu_clock(), "draws": draws}


func _check_gpu_and_draws() -> void:
	await _controls()
	var present := _backdrop_nodes().size()
	var all_present := present == BACKDROP_NODES.size()
	var worst_ms := -INF
	var worst_draws := -INT_MAX
	var gpu_ok := all_present and _device_ok
	var draws_ok := all_present
	var gpu_detail: PackedStringArray = []
	var draw_detail: PackedStringArray = []
	for position_id in POSITIONS:
		await _set_pos(position_id)
		_set_backdrop_visible(false)
		await _frames(2)
		var hidden := _measure()
		print("BASELINE %s without the backdrop: median %.3f ms p95 %.3f ms, %d draw calls, GPU %d MHz" % [position_id, hidden.median_ms, hidden.p95_ms, hidden.draws, hidden.clock_mhz])
		if not all_present:
			continue
		_set_backdrop_visible(true)
		await _frames(2)
		var shown := _measure()
		var diff_ms: float = shown.median_ms - hidden.median_ms
		var added: int = shown.draws - hidden.draws
		worst_ms = maxf(worst_ms, diff_ms)
		worst_draws = maxi(worst_draws, added)
		var low_clock: bool = hidden.clock_mhz < MIN_CLOCK_MHZ or shown.clock_mhz < MIN_CLOCK_MHZ
		if diff_ms > BUDGET_MS or low_clock:
			gpu_ok = false
		if added > MAX_ADDED_DRAWS:
			draws_ok = false
		gpu_detail.append("%s: hidden %.3f ms shown %.3f ms adds %.3f ms (p95 %.3f/%.3f) GPU %d MHz%s" % [position_id, hidden.median_ms, shown.median_ms, diff_ms, hidden.p95_ms, shown.p95_ms, shown.clock_mhz, " LOW CLOCK, run invalid" if low_clock else ""])
		draw_detail.append("%s: %d hidden, %d shown, adds %d" % [position_id, hidden.draws, shown.draws, added])
	_set_backdrop_visible(true)
	if not all_present:
		var why := "backdrop nodes absent: found %d of %d (%s) under the rig; nothing to compare, the baseline above is the rig without a backdrop" % [present, BACKDROP_NODES.size(), ", ".join(BACKDROP_NODES)]
		_check("BACKDROP-GPU", false, why)
		_check("BACKDROP-DRAWS", false, why)
		return
	_check("BACKDROP-GPU", gpu_ok, "backdrop adds at most %.1f ms [W 2026-10-02 budget] at every position, worst %.3f ms; %s on %s" % [BUDGET_MS, worst_ms, " | ".join(gpu_detail), RenderingServer.get_video_adapter_name()] + ("" if _device_ok else " (GPU run invalid)"))
	_check("BACKDROP-DRAWS", draws_ok, "backdrop adds at most %d draw calls in frame, worst %d; %s" % [MAX_ADDED_DRAWS, worst_draws, " | ".join(draw_detail)])


const INT_MAX := 9223372036854775807


# Positive controls for the two measurements, run at d25 before the real rows.
func _controls() -> void:
	await _set_pos("d25")
	# BACKDROP-GPU-CONTROL: a deliberate heavy full-screen canvas shader on the root viewport must show up as more than BUDGET_MS.
	var layer := CanvasLayer.new()
	var rect := ColorRect.new()
	rect.size = Vector2(1920, 1080)
	rect.material = _heavy_material()
	layer.add_child(rect)
	add_child(layer)
	await _frames(2)
	layer.visible = false
	await _frames(2)
	var off := _measure()
	layer.visible = true
	await _frames(2)
	var on := _measure()
	remove_child(layer)
	layer.free()
	_check("BACKDROP-GPU-CONTROL", _device_ok and on.median_ms - off.median_ms > BUDGET_MS, "a full-screen heavy canvas shader adds %.3f ms (%.3f vs %.3f ms), must exceed the %.1f ms budget so a breach is visible" % [on.median_ms - off.median_ms, on.median_ms, off.median_ms, BUDGET_MS] + ("" if _device_ok else " (GPU run invalid)"))
	# BACKDROP-DRAWS-CONTROL: one single-surface box in front of the camera adds at least one draw call.
	var box := MeshInstance3D.new()
	box.mesh = BoxMesh.new()
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	box.material_override = mat
	_camera.add_child(box)
	box.position = Vector3(0.0, 0.0, -3.0)
	box.visible = false
	await _frames(2)
	var d_off := _measure()
	box.visible = true
	await _frames(2)
	var d_on := _measure()
	_camera.remove_child(box)
	box.free()
	_check("BACKDROP-DRAWS-CONTROL", d_on.draws - d_off.draws >= 1, "one added box changes the draw-call counter from %d to %d" % [d_off.draws, d_on.draws])


# ---- BACKDROP-MESH --------------------------------------------------------------------------------

func _static_call(method: String, args: Array):
	for m in _rig_script.get_script_method_list():
		if m["name"] == method:
			return _rig_script.callv(method, args)
	return null


func _check_mesh() -> void:
	var consts := _rig_script.get_script_constant_map()
	var tolerated_missing: PackedStringArray = []
	for i in STAR_LAYERS:
		var node := _rig.get_node_or_null("StarLayer%d" % i)
		if node == null or not (node is MeshInstance3D):
			_check("BACKDROP-MESH", false, "StarLayer%d: no MeshInstance3D under the rig (backdrop absent)" % i)
			continue
		var mesh = (node as MeshInstance3D).mesh
		if not (mesh is ArrayMesh):
			_check("BACKDROP-MESH", false, "StarLayer%d: mesh is %s, want ArrayMesh" % [i, mesh])
			continue
		var am := mesh as ArrayMesh
		if am.get_surface_count() != 1:
			_check("BACKDROP-MESH", false, "StarLayer%d: %d surfaces, want one" % [i, am.get_surface_count()])
			continue
		var prim := am.surface_get_primitive_type(0)
		if prim != Mesh.PRIMITIVE_POINTS:
			_check("BACKDROP-MESH", false, "StarLayer%d: primitive type %d, want PRIMITIVE_POINTS (%d)" % [i, prim, Mesh.PRIMITIVE_POINTS])
			continue
		var want = _static_call("layer_star_positions", [i, _tier])
		if not (want is PackedVector3Array):
			_check("BACKDROP-MESH", false, "StarLayer%d: ambient_rig.gd has no layer_star_positions(i, tier) returning PackedVector3Array" % i)
			continue
		var got: PackedVector3Array = am.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
		var first_bad := -1
		for k in mini(got.size(), want.size()):
			if got[k] != want[k]:
				first_bad = k
				break
		var same: bool = got.size() == want.size() and first_bad == -1
		_check("BACKDROP-MESH", same, "StarLayer%d (tier %d): mesh has %d vertices, layer_star_positions has %d%s; one surface, PRIMITIVE_POINTS" % [i, _tier, got.size(), want.size(), "" if first_bad == -1 else ", first difference at index %d (%s vs %s)" % [first_bad, got[first_bad], want[first_bad]]])
	var dust := _rig.get_node_or_null("CameraDust")
	if dust == null or not (dust is MultiMeshInstance3D) or (dust as MultiMeshInstance3D).multimesh == null:
		_check("BACKDROP-MESH", false, "CameraDust: no MultiMeshInstance3D with a MultiMesh under the rig (backdrop absent)")
		return
	var mm := (dust as MultiMeshInstance3D).multimesh
	if not consts.has("DUST_COUNT"):
		_check("BACKDROP-MESH", false, "CameraDust: ambient_rig.gd has no DUST_COUNT constant")
		return
	var count: int = consts["DUST_COUNT"]
	_check("BACKDROP-MESH", mm.instance_count == count, "CameraDust: MultiMesh instance_count %d, DUST_COUNT %d" % [mm.instance_count, count])
	if not _rig.has_method("get_dust_positions"):
		_check("BACKDROP-MESH", false, "CameraDust: rig has no get_dust_positions()")
		return
	var cpu: PackedVector3Array = _rig.get_dust_positions()
	var bad := -1
	for k in mini(mm.instance_count, cpu.size()):
		if mm.get_instance_transform(k).origin != cpu[k]:
			bad = k
			break
	_check("BACKDROP-MESH", cpu.size() == mm.instance_count and bad == -1, "CameraDust: %d transforms against %d get_dust_positions()%s" % [mm.instance_count, cpu.size(), "" if bad == -1 else ", first difference at index %d (%s vs %s)" % [bad, mm.get_instance_transform(bad).origin, cpu[bad]]])


# ---- SHADER-COMPILES ------------------------------------------------------------------------------

static func log_errors(text: String) -> PackedStringArray:
	var out: PackedStringArray = []
	for line in text.split("\n"):
		for marker in LOG_ERROR_MARKERS:
			if line.contains(marker):
				out.append(line.strip_edges())
				break
	return out


func _check_shader_compiles() -> void:
	# SHADER-COMPILES-CONTROL: the scan flags a sample error line and passes a clean one.
	var flags_error: bool = log_errors("SHADER ERROR: sample\nclean line").size() == 1 and log_errors("clean line\nVulkan 1.3").is_empty()
	# Godot consumes --log-file, so a run that sets it passes the same path again after "--" as --log=PATH; without it the
	# default file log (project setting debug/file_logging/log_path, user://logs/godot.log, rotated at every start) is read.
	var log_path: String = str(ProjectSettings.get_setting("debug/file_logging/log_path", "user://logs/godot.log"))
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--log="):
			log_path = a.substr(6)
	if not FileAccess.file_exists(log_path):
		_check("SHADER-COMPILES-CONTROL", false, "no readable Godot log at %s (file logging off, or --log= wrong)" % log_path)
		_check("SHADER-COMPILES", false, "the Godot log cannot be scanned")
		return
	var text := FileAccess.get_file_as_string(log_path)
	_check("SHADER-COMPILES-CONTROL", flags_error and text.contains("Vulkan"), "the scan flags a sample error line and passes a clean one; the log %s (%d bytes) holds the Vulkan banner=%s" % [log_path, text.length(), text.contains("Vulkan")])
	var errors := log_errors(text)
	_check("SHADER-COMPILES", errors.is_empty(), "no SHADER ERROR / SCRIPT ERROR / Parse Error in the Godot log %s%s" % [log_path, "" if errors.is_empty() else ": " + " || ".join(errors.slice(0, 3))])

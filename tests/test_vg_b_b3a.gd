extends SceneTree

# Lane B piece B3a (docs/northstar/plans/2026-10-07-visible-game-spec.md rev 4, lane B;
# preflight_2026-10-07/3-galaxy-field.md "B3a"; S-106 / R-106-03). Tests first: every check marked
# RED fails on origin/main because scenes/galaxy/shell_renderer.gd does not exist
# ("MISSING: res://scenes/galaxy/shell_renderer.gd").
#
# Contract proved (taken from the field branch's shell_renderer.gd, push/galaxy-field):
#   setup(data, zoom_controller), teardown(), get_faction_shell_count(),
#   get_shell_viewport() -> SubViewport, var res_divisor (default 2), get_territory_field(),
#   set_debug_mode(int). data = scenes/shared/world_view/world_view_data.gd (territory_* signals),
#   zoom = scenes/shared/world_view/zoom_disclosure_controller.gd.
# Names this test chooses where the spec gives none (builder: match them):
#   - the shell opacity is the ShaderMaterial parameter "shell_opacity" on the ONE MeshInstance3D
#     (the full-screen quad) inside the shell SubViewport;
#   - the overlay is the one TextureRect (texture = the shell viewport's texture) under the renderer.
# ONE-DRAW here is structural (one quad, one material, constant as factions grow 4 -> 8 -> 15); the
# GPU draw-call and ms checks live in tests/test_vg_b_b3a_park_gpu.gd (SHELL-GPU, Westley's numbers).
# Positive controls: _legacy_fake() builds the superseded one-box-per-faction layout; the counter
# must see it as non-one-draw. A wrong-opacity and a wrong-divisor control are checked the same way.

const RENDERER_PATH := "res://scenes/galaxy/shell_renderer.gd"
const DATA_PATH := "res://scenes/shared/world_view/world_view_data.gd"
const ZOOM_PATH := "res://scenes/shared/world_view/zoom_disclosure_controller.gd"
const SCREEN := Vector2i(1920, 1080)
# R-106-03 / preflight 3-galaxy-field: 0.50 / 0.12 / 0.05 (rule: 40-60% / 8-15% / local ground fog).
const OP_OVERVIEW := 0.50
const OP_REGIONAL := 0.12
const OP_LOCAL := 0.05

var _pass := 0
var _fail := 0
var _msgs: Array[String] = []


func _check(id: String, cond: bool, msg: String) -> void:
	if cond:
		_pass += 1
		print("  PASS %s" % id)
	else:
		_fail += 1
		_msgs.append("%s: %s" % [id, msg])
		print("  FAIL %s: %s" % [id, msg])


func _initialize() -> void:
	await _run()
	print("\n=== B3a: %d passed, %d failed ===" % [_pass, _fail])
	print("PASS: %d  FAIL: %d" % [_pass, _fail])
	for m in _msgs:
		print("  FAILED " + m)
	quit(1 if _fail > 0 else 0)


func _frames(n: int) -> void:
	for i in n:
		await process_frame


# ---- helpers --------------------------------------------------------------

func _quads(root: Node) -> Array:
	var out: Array = []
	for n in root.find_children("*", "MeshInstance3D", true, false):
		out.append(n)
	return out


func _count_shell_draws(vp: SubViewport) -> int:
	# One draw = one visible MeshInstance3D in the shell viewport.
	var c := 0
	for m in _quads(vp):
		if m.visible:
			c += 1
	return c


func _legacy_fake(n: int) -> SubViewport:
	# The superseded layout: one raymarched box per faction. Positive control for ONE-DRAW.
	var vp := SubViewport.new()
	for i in n:
		vp.add_child(MeshInstance3D.new())
	return vp


func _opacity(vp: SubViewport) -> float:
	var qs := _quads(vp)
	if qs.size() != 1:
		return -1.0
	var mat := (qs[0] as MeshInstance3D).material_override as ShaderMaterial
	if mat == null:
		return -2.0
	var v = mat.get_shader_parameter("shell_opacity")
	return float(v) if v != null else -3.0


func _make_host() -> SubViewport:
	var host := SubViewport.new()
	host.size = SCREEN
	host.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(host)
	var cam := Camera3D.new()
	cam.position = Vector3(3, 40, 90)
	cam.fov = 55.0
	host.add_child(cam)
	cam.current = true
	return host


func _add_factions(data: Node, n: int) -> void:
	for f in n:
		var col := Color.from_hsv(float(f) / float(n), 0.8, 0.9, 0.3)
		for k in 2:
			var rid := "f%d_r%d" % [f, k]
			data.set_territory(rid, Vector3(f * 6.0 - 40.0, k * 4.0, 0.0), 12.0, col)


func _band_opacity(zoom: Node, vp: SubViewport, dist: float) -> float:
	zoom.update_from_distance(dist)
	await _frames(2)
	return _opacity(vp)


# ---- the run --------------------------------------------------------------

func _run() -> void:
	print("--- positive controls ---")
	var fake := _legacy_fake(8)
	_check("CTRL one-draw counter sees a legacy one-box-per-faction layout", _count_shell_draws(fake) == 8,
		"counter returned %d for 8 boxes" % _count_shell_draws(fake))
	fake.free()
	var fake_one := _legacy_fake(1)
	_check("CTRL one-draw counter reads 1 for one quad", _count_shell_draws(fake_one) == 1, "counter broken")
	fake_one.free()

	var script = load(RENDERER_PATH)
	if script == null:
		_check("RED B3a-exists", false, "MISSING: %s" % RENDERER_PATH)
		return
	var data_script = load(DATA_PATH)
	var zoom_script = load(ZOOM_PATH)
	_check("fixture scripts load", data_script != null and zoom_script != null, "world_view_data / zoom controller missing")
	if data_script == null or zoom_script == null:
		return

	var host := _make_host()
	var data: Node = data_script.new()
	var zoom: Node = zoom_script.new()
	host.add_child(data)
	host.add_child(zoom)
	var shell: Node = script.new()
	host.add_child(shell)
	shell.setup(data, zoom)
	await _frames(3)

	print("--- API surface ---")
	for m in ["setup", "teardown", "get_faction_shell_count", "get_shell_viewport", "get_territory_field", "set_debug_mode"]:
		_check("RED API %s()" % m, shell.has_method(m), "shell renderer lacks %s" % m)
	_check("RED API res_divisor default is 2", shell.get("res_divisor") == 2,
		"res_divisor = %s (want 2, the shipped half resolution)" % str(shell.get("res_divisor")))

	var vp: SubViewport = shell.get_shell_viewport() if shell.has_method("get_shell_viewport") else null
	_check("RED VIEWPORT exists", vp != null, "get_shell_viewport() returned null")
	if vp == null:
		host.queue_free()
		return

	print("--- half-resolution SubViewport and overlay ---")
	_check("RED VIEWPORT half size", vp.size == Vector2i(SCREEN.x / 2, SCREEN.y / 2),
		"shell viewport %s, want %s" % [str(vp.size), str(Vector2i(SCREEN.x / 2, SCREEN.y / 2))])
	_check("VIEWPORT transparent_bg (so the overlay shows the sky)", vp.transparent_bg, "transparent_bg is false")
	_check("VIEWPORT own_world_3d (isolated from the main world)", vp.own_world_3d, "own_world_3d is false")
	_check("VIEWPORT updates every frame", vp.render_target_update_mode == SubViewport.UPDATE_ALWAYS,
		"render_target_update_mode = %d" % vp.render_target_update_mode)
	_check("VIEWPORT msaa off", vp.msaa_3d == Viewport.MSAA_DISABLED, "msaa_3d = %d" % vp.msaa_3d)
	var overlays := shell.find_children("*", "TextureRect", true, false)
	_check("RED OVERLAY exactly one TextureRect", overlays.size() == 1, "found %d TextureRects" % overlays.size())
	if overlays.size() == 1:
		var ov: TextureRect = overlays[0]
		_check("OVERLAY shows the shell viewport", ov.texture is ViewportTexture, "overlay texture is not a ViewportTexture")
		_check("OVERLAY ignores the mouse", ov.mouse_filter == Control.MOUSE_FILTER_IGNORE, "mouse_filter = %d" % ov.mouse_filter)
		var cim := ov.material as CanvasItemMaterial
		_check("OVERLAY premultiplied-alpha blend", cim != null and cim.blend_mode == CanvasItemMaterial.BLEND_MODE_PREMULT_ALPHA,
			"overlay material is not a premult-alpha CanvasItemMaterial")
		_check("OVERLAY sits in a CanvasLayer", ov.get_parent() is CanvasLayer, "parent is %s" % str(ov.get_parent()))
		_check("OVERLAY fills the screen", ov.anchor_right == 1.0 and ov.anchor_bottom == 1.0, "anchors not full rect")
	var cams := vp.find_children("*", "Camera3D", true, false)
	_check("RED SUB-CAMERA exists", cams.size() == 1, "shell viewport has %d cameras" % cams.size())
	if cams.size() == 1:
		var main_cam := host.get_camera_3d()
		_check("SUB-CAMERA follows the main camera", main_cam != null and (cams[0] as Camera3D).global_transform.is_equal_approx(main_cam.global_transform)
			and is_equal_approx((cams[0] as Camera3D).fov, main_cam.fov), "sub-camera transform/fov differ from the main camera")

	print("--- ONE-DRAW at 4, 8, 15 factions ---")
	var draws: Array = []
	for n in [4, 8, 15]:
		data.regions_cleared.emit()
		await _frames(1)
		_add_factions(data, n)
		await _frames(3)
		var d := _count_shell_draws(vp)
		draws.append(d)
		_check("RED ONE-DRAW %d factions -> 1 shell draw" % n, d == 1, "%d visible meshes in the shell viewport" % d)
		_check("faction count %d" % n, shell.get_faction_shell_count() == n, "get_faction_shell_count() = %d" % shell.get_faction_shell_count())
	_check("ONE-DRAW constant across 4/8/15", draws[0] == draws[1] and draws[1] == draws[2], "draw counts %s" % str(draws))
	_check("RED ONE-DRAW quad has a ShaderMaterial", _opacity(vp) >= 0.0, "shell_opacity read %f (no single quad with a shell_opacity parameter)" % _opacity(vp))

	print("--- opacity by zoom band (R-106-03) ---")
	var o_over := await _band_opacity(zoom, vp, 120.0)
	var o_reg := await _band_opacity(zoom, vp, 50.0)
	var o_loc := await _band_opacity(zoom, vp, 10.0)
	_check("RED OPACITY overview d=120 is 0.50", is_equal_approx(o_over, OP_OVERVIEW), "got %f" % o_over)
	_check("RED OPACITY regional d=50 is 0.12", is_equal_approx(o_reg, OP_REGIONAL), "got %f" % o_reg)
	_check("RED OPACITY local d=10 is 0.05", is_equal_approx(o_loc, OP_LOCAL), "got %f" % o_loc)
	_check("OPACITY overview inside the rule's 40-60%", o_over >= 0.40 and o_over <= 0.60, "got %f" % o_over)
	_check("OPACITY regional inside the rule's 8-15%", o_reg >= 0.08 and o_reg <= 0.15, "got %f" % o_reg)
	# Blends (zoom_disclosure_controller.gd): overview->regional at d=70 is blend 0.5; regional->local at d=32.5 is blend 0.5.
	var o_b1 := await _band_opacity(zoom, vp, 70.0)
	_check("RED OPACITY blend overview to regional at d=70", is_equal_approx(o_b1, lerpf(OP_OVERVIEW, OP_REGIONAL, 0.5)), "got %f want %f" % [o_b1, lerpf(OP_OVERVIEW, OP_REGIONAL, 0.5)])
	var o_b2 := await _band_opacity(zoom, vp, 32.5)
	_check("RED OPACITY blend regional to local at d=32.5", is_equal_approx(o_b2, lerpf(OP_REGIONAL, OP_LOCAL, 0.5)), "got %f want %f" % [o_b2, lerpf(OP_REGIONAL, OP_LOCAL, 0.5)])
	_check("CTRL opacity reader rejects a wrong value", not is_equal_approx(o_over, OP_REGIONAL), "reader cannot tell 0.50 from 0.12")

	print("--- res_divisor quality hook ---")
	var sizes := {}
	for div in [1, 2, 4]:
		shell.set("res_divisor", div)
		await _frames(3)
		sizes[div] = vp.size
	_check("RED DIVISOR 1 is full resolution", sizes[1] == SCREEN, "size %s" % str(sizes[1]))
	_check("RED DIVISOR 2 is half", sizes[2] == Vector2i(960, 540), "size %s" % str(sizes[2]))
	_check("RED DIVISOR 4 is quarter", sizes[4] == Vector2i(480, 270), "size %s" % str(sizes[4]))
	_check("CTRL divisor sizes differ", sizes[1] != sizes[2] and sizes[2] != sizes[4], "sizes identical")
	_check("DIVISOR change keeps the same SubViewport node", shell.get_shell_viewport() == vp, "viewport was replaced")
	shell.set("res_divisor", 2)
	await _frames(2)

	print("--- teardown ---")
	var field = shell.get_territory_field() if shell.has_method("get_territory_field") else null
	shell.teardown()
	await _frames(3)
	_check("RED TEARDOWN frees the viewport", not is_instance_valid(vp) or vp.is_queued_for_deletion(), "shell viewport still alive")
	_check("TEARDOWN frees the field", field == null or not is_instance_valid(field) or field.is_queued_for_deletion(), "field still alive")
	_check("TEARDOWN disconnects territory signals", data.territory_set.get_connections().is_empty(), "territory_set still connected")
	host.queue_free()

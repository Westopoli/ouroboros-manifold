extends SceneTree
# test-timeout: 20000

# Piece B23, the prototype's numbers exactly (docs/northstar/plans/2026-10-07-visible-game-spec.md rev 12b,
# lane B, paragraph "B23, the prototype's numbers exactly", built on "B22, the prototype's geometry").
# Proves (bible E-16, docs/bible/epics/E-16-client-camera-hud-and-world-view.md):
#   S-106 "A 3D star map where territory glows, borders touch, and war flashes."
#   S-107 "Pan, zoom, orbit, focus a system, pick out a faction."
#   S-108 "Mission pulls back into the galaxy and pushes into the next mission without a cut."
#   R-106-01  Given the world view, When drawn, Then each system is a luminous point sized by significance,
#             brightest for the player's core, dim neutral for uncolonized.
#   R-106-02  ... adjacent same-faction systems are joined by faction-colored luminous filament arcs in 3D (border
#             and both edges solid and bright, trade edges thinner and dimmer), and each faction's systems share
#             one translucent shell; rival shells keep a visible gap with a bright seam where they nearly meet.
#   R-106-03  Given camera distance d, ... between bands properties interpolate continuously, inside a band they
#             are locked. (The band edges are the controller thresholds below; the bible text still carries the
#             pre-rescale 75 / 65 / 40 / 25, the docs piece of B23 rewrites it to 37.5 / 32.5 / 20 / 12.5.)
#   R-106-04  ... a flash pulses at the involved systems for each event; the renderer owns look.
#   R-107-01  Given the world view, When the player left-drags, Then the camera pans; scroll zooms along the
#             forward axis; right-drag orbits; clicking a system centers on it and zooms to Local.
# Source of every number: the approved prototype, origin/push/galaxy-field at 99f35887, scenes/mockups/galaxy/
# (Westley approved its look 2026-10-07), CIV_SCALE 0.5 at galaxy_gen.gd:7. File:line beside each row below.
# TD-VG-B-14 (superseded by B23 prototype scale) moves the older pins; this file is the parity table.
#
# The window is 64x64 under the dummy display, where Godot maps pushed mouse events by a 1/30 stretch; _motion pre-scales
# the relative motion so the camera rows read the same values headless and under xvfb.
#
# Control first (green today): rows already equal on main, plus the instantiation of the view with the 80-region
# fixture. Red until B23 is built: every other row. Headless-safe: no row reads MultiMesh transforms (the dot mesh
# and material are read as resources), so the file runs under the dummy renderer as well as under xvfb:
#   xvfb-run -a godot.real --path . --resolution 1920x1080 -s res://tests/test_vg_b_b23.gd
#
# Player faction seam (Rev 12b, ruled): the view reads snapshot["player_faction"] (the value CBridge.player_faction()
# stores, autoload/c_bridge.gd:289-290). The fixture snapshot_seed1_tick10.json has no such key, so this file adds
# it to its own copy; the control "no player_faction key" proves the 0.95 branch is unreached without it.

const SCENE_PATH := "res://scenes/galaxy/galaxy_view.tscn"
const FIXTURE_PATH := "res://tests/transport/fixtures/snapshot_seed1_tick10.json"
const GEN_PATH := "res://scenes/galaxy/galaxy_gen.gd"
const FIELD_PATH := "res://scenes/galaxy/territory_field.gd"
const VIEW_PATH := "res://scenes/galaxy/galaxy_view.gd"
const CAM_PATH := "res://scenes/galaxy/orbit_camera.gd"
const ZOOM_PATH := "res://scenes/galaxy/legacy_zoom_disclosure_controller.gd"
const FILAMENT_PATH := "res://scenes/galaxy/legacy_constellation_renderer.gd"
const LABELS_PATH := "res://scenes/galaxy/shell_labels.gd"
const FIXTURE_SEED := 1
const REGIONS := 80
const PLAYER_FACTION := 3        # a faction id in the fixture (4 regions), not 0, so id 0 stays an "other" owner
const GOLDEN_ANGLE := 0.6180339887498949   # galaxy_view.gd hue step, unchanged by B23
const EPS := 0.001               # derived float compare, not a threshold
const POS := Vector2(60.0, 60.0) # event position: clear of the view's MISSION button in a 64x64 headless window
const TOL_DEG := 0.05

var _pass := 0
var _fail := 0
var _msgs: Array[String] = []
var _ctrl_pass := 0
var _ctrl_fail := 0
var _view: Node
var _rig: Node
var _cam: Camera3D


func _initialize() -> void:
	await _run()
	print("\n=== B23 prototype numbers: PASS %d FAIL %d (controls %d green, %d red) ===" % [_pass, _fail, _ctrl_pass, _ctrl_fail])
	print("PASS: %d  FAIL: %d" % [_pass, _fail])   # the summary line scripts/run_godot_tests.sh reads
	for m in _msgs:
		print("  - " + m)
	print("=== %s ===" % ("RED" if _fail > 0 else "GREEN"))
	quit(1 if _fail > 0 else 0)


func _check(c: bool, msg: String) -> void:
	if c:
		_pass += 1
	else:
		_fail += 1
		_msgs.append(msg)


# A positive-control row: counted like any check, and its result line is printed so the report can paste it.
func _ctrl(c: bool, msg: String) -> void:
	if c:
		_ctrl_pass += 1
		print("CONTROL ok: " + msg)
	else:
		_ctrl_fail += 1
	_check(c, "control: " + msg)


func _same(a, b) -> bool:
	if a == null or b == null:
		return false
	if typeof(a) != typeof(b):
		return false
	match typeof(a):
		TYPE_FLOAT:
			return absf(float(a) - float(b)) <= 1.0e-5 * maxf(1.0, absf(float(b)))
		TYPE_VECTOR3:
			return (a as Vector3).is_equal_approx(b)
		TYPE_COLOR:
			return (a as Color).is_equal_approx(b)
		_:
			return a == b


# One parity row: name, live value, prototype value, prototype file:line.
func _row(name: String, got, want, proto: String) -> void:
	_check(_same(got, want), "B23 parity %s: live %s, want %s (prototype %s)" % [name, str(got), str(want), proto])


func _consts(path: String) -> Dictionary:
	return (load(path) as GDScript).get_script_constant_map()


func _const_row(path: String, name: String, want, proto: String) -> void:
	var m := _consts(path)
	_row("%s.%s" % [path.get_file(), name], m.get(name, null), want, proto)


func _frames(n: int) -> void:
	for _i in range(n):
		await process_frame


func _new_view(snap: Dictionary) -> Node:
	var v: Node = (load(SCENE_PATH) as PackedScene).instantiate()
	v.driven = true
	get_root().add_child(v)
	await _frames(2)
	v.set_snapshot(snap)
	await _frames(2)
	return v


# --- input, the way tests/qa/desktop/galaxy_camera_probe.gd drives the rig, through the root Window ---

func _motion(rel: Vector2, mask: int) -> void:
	var ev := InputEventMouseMotion.new()
	ev.position = POS
	ev.global_position = POS
	# the Window maps an event into canvas units by the inverse of its final transform (scale 1/30 in the 64x64 headless
	# window, 1 at 1920x1080), so the relative motion is pre-scaled to arrive as `rel` either way
	ev.relative = rel * get_root().get_final_transform().get_scale().x
	ev.button_mask = mask
	get_root().push_input(ev)
	await process_frame


func _wheel(index: int) -> void:
	for pressed in [true, false]:
		var ev := InputEventMouseButton.new()
		ev.button_index = index
		ev.pressed = pressed
		ev.position = POS
		ev.global_position = POS
		get_root().push_input(ev)
		await process_frame


# Pitch (degrees above the horizon) read off the camera's global basis: the forward vector's elevation.
func _pitch_deg() -> float:
	var fwd: Vector3 = -_cam.global_transform.basis.z
	return rad_to_deg(asin(clampf(-fwd.y, -1.0, 1.0)))


# Yaw (radians) read off the camera's position relative to the orbit target, in the rig's own convention.
func _yaw_rad() -> float:
	var off: Vector3 = _cam.global_position - _rig.get_target()
	return atan2(off.z, off.x)


func _run() -> void:
	var f := FileAccess.open(FIXTURE_PATH, FileAccess.READ)
	var snap = JSON.parse_string(f.get_as_text()) if f != null else null
	_ctrl(snap is Dictionary, "fixture snapshot_seed1_tick10.json readable")
	if not (snap is Dictionary):
		return
	var ids: Array = []
	for r in snap.get("regions", []):
		ids.append(int(r.get("i", -1)))
	ids.sort()
	_ctrl(ids.size() == REGIONS, "fixture has %d regions, want %d" % [ids.size(), REGIONS])

	# ---- positive controls: rows already equal on main (green today) ----
	_ctrl(int(_consts(FIELD_PATH).get("GRID_CELLS", -1)) == 96, "territory_field GRID_CELLS 96 (prototype territory_field.gd:18)")
	# TD-VG-B-16 (superseded by B24, spec VG-B24-layout, DRAFT-b24-relax): was `== 250, "galaxy_gen PLACEMENT_ATTEMPTS 250 (prototype galaxy_gen.gd:48)"`
	_ctrl(int(_consts(GEN_PATH).get("PLACEMENT_ATTEMPTS", -1)) == 16, "galaxy_gen PLACEMENT_ATTEMPTS 16 (VG-B24 spec: up to 16 tries per region, DRAFT-b24-relax)")
	_ctrl(_same(_consts(CAM_PATH).get("ZOOM_STEP", null), 0.9), "orbit_camera ZOOM_STEP 0.9 (prototype orbit_camera.gd:238-241 wheel up x0.9)")
	_ctrl(_same(_consts(CAM_PATH).get("DIST_MAX", null), 120.0), "orbit_camera DIST_MAX 120 (prototype orbit_camera.gd:9, not scaled)")
	_ctrl(_same(_consts(VIEW_PATH).get("PICK_RADIUS_PX", null), 14.0), "galaxy_view PICK_RADIUS_PX 14 (prototype orbit_camera.gd:19)")
	_ctrl(int(_consts(LABELS_PATH).get("LABEL_FONT_SIZE", -1)) == 40, "shell_labels LABEL_FONT_SIZE 40 (prototype galaxy_view.gd:166)")
	_ctrl(_same(_consts(VIEW_PATH).get("OWNER_SAT", null), 0.65) and _same(_consts(VIEW_PATH).get("OWNER_VAL", null), 0.85),
		"galaxy_view OWNER_SAT 0.65 and OWNER_VAL 0.85 for every non-player owner (prototype galaxy_view.gd:93-95)")
	_ctrl((load("res://scenes/galaxy/shaders/field_bake.gdshader") as Shader) != null,
		"field_bake.gdshader loads (its R default 16 is inert: territory_field.gd overrides it with INFLUENCE_RADIUS; Rev 12b)")

	# ---- the view on the 80-region fixture (instantiation control) ----
	_view = await _new_view(snap)
	var st: Dictionary = _view.qa_state()
	_ctrl(int(st.get("system_count", -1)) == REGIONS, "view instantiates and qa_state.system_count is %s, want %d" % [st.get("system_count"), REGIONS])
	_rig = _view.get_node_or_null("OrbitCamera")
	_cam = _rig.get_camera() if _rig != null else null
	_ctrl(_cam != null, "view has OrbitCamera with a Camera3D")
	if _cam == null:
		return

	# scene: Camera3D, Environment, light (galaxy_mockup.tscn:12-17, 30-32, 41-43)
	_ctrl(is_equal_approx(_cam.fov, 45.0) and is_equal_approx(_cam.far, 3000.0), "Camera3D fov %s far %s, want 45 and 3000 (DRAFT-b25-far, TD-VG-B-20: ambient_rig.gd sets far at runtime; was 800, galaxy_mockup.tscn:42-43)" % [_cam.fov, _cam.far])
	var we: WorldEnvironment = _view.get_node_or_null("WorldEnvironment")
	var env: Environment = we.environment if we != null else null
	_ctrl(env != null and env.background_mode == Environment.BG_COLOR
		and env.background_color.is_equal_approx(Color(0.0392157, 0.0509804, 0.0705882, 1.0)),
		"Environment background BG_COLOR (0.0392157, 0.0509804, 0.0705882) (galaxy_mockup.tscn:10-11)")
	# pitch default 55 (prototype orbit_camera.gd:13 PITCH_DEFAULT_DEG): green today, the fixed PITCH_DEG
	_ctrl(absf(_pitch_deg() - 55.0) <= TOL_DEG, "camera pitch %.3f degrees at the default view, want 55 (orbit_camera.gd:13 PITCH_DEFAULT_DEG)" % _pitch_deg())

	# premises dump (from this one run; the report pastes these lines)
	var pos: Dictionary = _view.get_positions()
	var min_d := INF
	var y_lo := INF
	var y_hi := -INF
	var r_max := 0.0
	for a in ids:
		y_lo = minf(y_lo, pos[a].y)
		y_hi = maxf(y_hi, pos[a].y)
		r_max = maxf(r_max, pos[a].length())
		for b in ids:
			if int(a) < int(b):
				min_d = minf(min_d, pos[a].distance_to(pos[b]))
	var vp := Vector2(get_root().size)
	var px: Dictionary = st.get("systems_px", {})
	var inside := 0
	for k in px:
		var p = px[k]
		if p[0] >= 0 and p[0] <= vp.x and p[1] >= 0 and p[1] <= vp.y:
			inside += 1
	print("PREMISES regions=%d min_pair=%.3f y_spread=%.3f r_max=%.3f default_distance=%.3f layout_fallbacks=%s systems_px=%d inside_viewport=%d window=%s" % [
		ids.size(), min_d, y_hi - y_lo, r_max, float(st.get("distance", -1.0)), st.get("layout_fallbacks"), px.size(), inside, str(get_root().size)])

	# ---- red until built: constants through the script constant maps ----
	# galaxy_gen.gd (prototype galaxy_gen.gd:7-8, 11)
	_const_row(GEN_PATH, "R_BALL", 50.0, "galaxy_gen.gd:8 BALL_RADIUS 100 x CIV_SCALE 0.5")
	_const_row(GEN_PATH, "MIN_SPACING", 11.0, "galaxy_gen.gd:11 22 x CIV_SCALE 0.5")
	# territory_field.gd (prototype galaxy_gen.gd:17, territory_field.gd:19-20)
	_const_row(FIELD_PATH, "INFLUENCE_RADIUS", 14.0, "galaxy_gen.gd:17 28 x CIV_SCALE 0.5")
	_const_row(FIELD_PATH, "GRID_SIZE", 128.0, "territory_field.gd:19 2 x (BALL_RADIUS + INFLUENCE_RADIUS)")
	_const_row(FIELD_PATH, "GRID_MIN", Vector3(-64.0, -64.0, -64.0), "territory_field.gd:20 -GRID_SIZE x 0.5")
	# galaxy_view.gd (prototype galaxy_view.gd:5-6, 93-94; orbit_camera.gd:14, 28-29)
	_const_row(VIEW_PATH, "POINT_RADIUS", 0.7, "galaxy_view.gd:5 POINT_BASE_RADIUS 1.4 x CIV_SCALE 0.5")
	_const_row(VIEW_PATH, "DEFAULT_DISTANCE", 25.0, "orbit_camera.gd:14 DIST_DEFAULT 50 x CIV_SCALE 0.5")
	_const_row(VIEW_PATH, "BAND_SPLIT_LOW", 16.25, "orbit_camera.gd:28 32.5 x CIV_SCALE 0.5")
	_const_row(VIEW_PATH, "BAND_SPLIT_HIGH", 35.0, "orbit_camera.gd:29 70 x CIV_SCALE 0.5")
	_const_row(VIEW_PATH, "NEUTRAL_COLOUR", Color(0.55, 0.55, 0.58, 1.0), "galaxy_view.gd:6 NEUTRAL_COLOR")
	_const_row(VIEW_PATH, "PLAYER_OWNER_VAL", 0.95, "galaxy_view.gd:93-94 value 0.95 for faction 0 (the player's faction, Rev 12b)")
	_const_row(VIEW_PATH, "FLASH_SIZE", 1.5, "galaxy_view.gd:283 quad Vector2(3, 3) x CIV_SCALE 0.5")
	_const_row(VIEW_PATH, "FLASH_SECONDS", 0.6, "galaxy_view.gd:8 FLASH_DURATION")
	_check(not _consts(VIEW_PATH).has("FLASH_RADIUS"), "B23 parity galaxy_view.gd.FLASH_RADIUS: still present, want it gone (prototype galaxy_view.gd:283 draws a QuadMesh, no sphere radius)")
	# orbit_camera.gd (prototype orbit_camera.gd:7, 25-26)
	_const_row(CAM_PATH, "DIST_MIN", 7.5, "orbit_camera.gd:7 15 x CIV_SCALE 0.5")
	_const_row(CAM_PATH, "LOCAL_DISTANCE", 14.0, "orbit_camera.gd:25 FOCUS_DISTANCE 28 x CIV_SCALE 0.5")
	_const_row(CAM_PATH, "FOCUS_SEC", 1.5, "orbit_camera.gd:26 FOCUS_DURATION")
	# legacy_constellation_renderer.gd, shell_labels.gd (prototype :12-13; galaxy_view.gd:164, 170)
	_const_row(FILAMENT_PATH, "FILAMENT_WIDTH_BORDER", 0.0375, "legacy_constellation_renderer.gd:12 0.075 x CIV_SCALE 0.5")
	_const_row(FILAMENT_PATH, "FILAMENT_WIDTH_TRADE", 0.0175, "legacy_constellation_renderer.gd:13 0.035 x CIV_SCALE 0.5")
	_const_row(LABELS_PATH, "LABEL_LIFT", 3.0, "galaxy_view.gd:164 6.0 x CIV_SCALE 0.5")
	_const_row(LABELS_PATH, "LABEL_PIXEL_SIZE", 0.025, "galaxy_view.gd:170 0.05 x CIV_SCALE 0.5")

	# controller thresholds through an instance (prototype legacy_zoom_disclosure_controller.gd:14-17)
	var zoom: Node = (load(ZOOM_PATH) as GDScript).new()
	_row("legacy_zoom_disclosure_controller.overview_min", zoom.get("overview_min"), 37.5, "legacy_zoom_disclosure_controller.gd:14 75 x 0.5")
	_row("legacy_zoom_disclosure_controller.overview_regional_blend", zoom.get("overview_regional_blend"), 32.5, "legacy_zoom_disclosure_controller.gd:15 65 x 0.5")
	_row("legacy_zoom_disclosure_controller.regional_min", zoom.get("regional_min"), 20.0, "legacy_zoom_disclosure_controller.gd:16 40 x 0.5")
	_row("legacy_zoom_disclosure_controller.regional_local_blend", zoom.get("regional_local_blend"), 12.5, "legacy_zoom_disclosure_controller.gd:17 25 x 0.5")
	zoom.free()

	# layout of the fixture inside the ball (derived from R_BALL: red while the ball is 71)
	_check(r_max <= 50.0 + EPS, "B23 parity layout: farthest system %.3f from the origin, want <= 50 (R_BALL 50, galaxy_gen.gd:8)" % r_max)

	# ---- red until built: the scene (galaxy_mockup.tscn:12-17, 30-32, 41-43) ----
	_row("Camera3D near", _cam.near, 0.25, "galaxy_mockup.tscn:42")
	_check(env != null, "B23 parity Environment: the view has no WorldEnvironment with an Environment")
	if env != null:
		_row("Environment ambient_light_source", int(env.ambient_light_source), 2, "galaxy_mockup.tscn:12")
		_row("Environment ambient_light_color", env.ambient_light_color, Color(0.35, 0.37, 0.42, 1.0), "galaxy_mockup.tscn:13")
		_row("Environment ambient_light_energy", env.ambient_light_energy, 0.4, "galaxy_mockup.tscn:14")
		_row("Environment fog_enabled", env.fog_enabled, true, "galaxy_mockup.tscn:15")
		_row("Environment fog_light_color", env.fog_light_color, Color(0.0392157, 0.0509804, 0.0705882, 1.0), "galaxy_mockup.tscn:16")
		_row("Environment fog_density", env.fog_density, 0.0006, "galaxy_mockup.tscn:17")
	var light: DirectionalLight3D = _view.get_node_or_null("World/DirectionalLight3D")
	_check(light != null, "B23 parity DirectionalLight3D: no DirectionalLight3D under World (galaxy_mockup.tscn:30-32)")
	if light != null:
		_row("DirectionalLight3D rotation_degrees", light.rotation_degrees, Vector3(-55.0, -35.0, 0.0), "galaxy_mockup.tscn:31")
		_row("DirectionalLight3D light_energy", light.light_energy, 0.5, "galaxy_mockup.tscn:32")

	# ---- red until built: the dot mesh and material, read as resources (galaxy_view.gd:109-118) ----
	var points: MultiMeshInstance3D = _view.get_node_or_null("World/Points")
	var mm: MultiMesh = points.multimesh if points != null else null
	_check(mm != null and mm.instance_count == REGIONS, "B23 dots: World/Points MultiMesh holds %s instances, want %d" % [str(mm.instance_count) if mm != null else "none", REGIONS])
	if mm != null and mm.mesh is SphereMesh:
		var sphere: SphereMesh = mm.mesh
		_row("dot SphereMesh radius", sphere.radius, 0.7, "galaxy_view.gd:107 radius = POINT_BASE_RADIUS (1.4 x 0.5)")
		_row("dot SphereMesh height", sphere.height, 1.4, "galaxy_view.gd:108 height = radius x 2")
		_row("dot SphereMesh radial_segments", sphere.radial_segments, 12, "galaxy_view.gd:109")
		_row("dot SphereMesh rings", sphere.rings, 8, "galaxy_view.gd:110")
	else:
		_check(false, "B23 dots: the dot mesh is not a SphereMesh (%s)" % str(mm.mesh) if mm != null else "B23 dots: no MultiMesh")
	var mat = points.material_override if points != null else null
	_check(mat is StandardMaterial3D, "B23 dots: World/Points material_override is not a StandardMaterial3D")
	if mat is StandardMaterial3D:
		# The two dot rows below pin main before B23, not the prototype (TD-VG-B-15, piece VG-B23b-dotcolour). Westley 2026-10-12:
		# "I like the coloring of the MAIN-passing better, but other than that they both look exactly the same to me. My eyes approve, pending the color change."
		# Spec :306: "the dot material and vertex-colour path as on origin/main before B23 (the srgb flag and the prototype's dot transparency are reverted on the dots only); every other B23 value stays".
		_row("dot material transparency", int(mat.transparency), int(BaseMaterial3D.TRANSPARENCY_DISABLED), "main before B23: galaxy_view.gd at 33e3bc2f^ sets no transparency (default DISABLED); spec :306 ruling")
		_row("dot material vertex_color_is_srgb", mat.vertex_color_is_srgb, true, "main before B23: galaxy_view.gd:114 at 33e3bc2f^ vertex_color_is_srgb = true; spec :306 ruling")
		_ctrl(mat.vertex_color_use_as_albedo and mat.shading_mode == BaseMaterial3D.SHADING_MODE_UNSHADED,
			"dot material vertex_color_use_as_albedo true and unshaded (galaxy_view.gd:113-114)")

	# ---- red until built: behaviour. Default camera, wheel, right-drag pitch and yaw, pan ----
	_row("default camera distance (qa_state.distance)", float(_view.qa_state().get("distance", -1.0)), 25.0, "orbit_camera.gd:14 DIST_DEFAULT 50 x 0.5")
	await _check_camera()

	# ---- red until built: colours (Rev 12b) ----
	await _check_colours(snap)

	# ---- red until built: the flash (Rev 12b) ----
	await _check_flash()

	# ---- W3: the prototype's two CIV_SCALE terms in the constellation renderer (prototype :149, :181) ----
	_check_arc_and_tube()

	# ---- W2: camera_move_completed waits FOCUS_SEC (a fixed 0.6 s would fire 0.9 s early) ----
	await _check_camera_done_timer(snap)

	_view.queue_free()


func _check_camera() -> void:
	_view.qa_camera(25.0, -1)
	_rig.set_view(25.0, Vector3.ZERO)
	await _frames(1)
	# wheel (prototype orbit_camera.gd:238-241: up x0.9, down x1.1)
	var d0: float = _rig.get_distance()
	await _wheel(MOUSE_BUTTON_WHEEL_UP)
	var d1: float = _rig.get_distance()
	_ctrl(absf(d1 - d0 * 0.9) <= EPS, "one wheel-up step: distance %.4f -> %.4f, want x0.9 = %.4f (orbit_camera.gd:240)" % [d0, d1, d0 * 0.9])
	await _wheel(MOUSE_BUTTON_WHEEL_DOWN)
	var d2: float = _rig.get_distance()
	_check(absf(d2 - d1 * 1.1) <= EPS, "B23 camera: one wheel-down step: distance %.4f -> %.4f, want x1.1 = %.4f (orbit_camera.gd:241)" % [d1, d2, d1 * 1.1])
	_rig.set_view(25.0, Vector3.ZERO)
	await _frames(1)

	# right-drag yaw: -relative.x x 0.01 (prototype orbit_camera.gd:16 ORBIT_YAW_SPEED, :279-283 _orbit_by)
	var yaw0 := _yaw_rad()
	await _motion(Vector2(100.0, 0.0), MOUSE_BUTTON_MASK_RIGHT)
	var dyaw := angle_difference(yaw0, _yaw_rad())
	_check(absf(dyaw - (-1.0)) <= EPS, "B23 camera: right-drag +100 px turned the yaw by %.4f rad, want -1.0 (ORBIT_YAW_SPEED 0.01 x 100 px; main turns 0.5)" % dyaw)
	_ctrl(absf(_pitch_deg() - 55.0) <= TOL_DEG, "a horizontal right-drag leaves the pitch at 55 (got %.3f)" % _pitch_deg())

	# right-drag pitch: +relative.y x 0.1 degrees, clamped 20..85 (prototype orbit_camera.gd:11-12, 17)
	var p0 := _pitch_deg()
	await _motion(Vector2(0.0, 100.0), MOUSE_BUTTON_MASK_RIGHT)
	var p1 := _pitch_deg()
	_check(absf((p1 - p0) - 10.0) <= TOL_DEG, "B23 camera: right-drag +100 px (y) moved the pitch %.3f -> %.3f (change %.3f), want +10 degrees (ORBIT_PITCH_SPEED 0.1; main keeps 55 fixed)" % [p0, p1, p1 - p0])
	await _motion(Vector2(0.0, -1000.0), MOUSE_BUTTON_MASK_RIGHT)
	var p2 := _pitch_deg()
	_check(absf(p2 - 20.0) <= TOL_DEG, "B23 camera: right-drag -1000 px (y) left the pitch at %.3f, want the clamp 20 (PITCH_MIN_DEG)" % p2)
	await _motion(Vector2(0.0, 1000.0), MOUSE_BUTTON_MASK_RIGHT)
	var p3 := _pitch_deg()
	_check(absf(p3 - 85.0) <= TOL_DEG, "B23 camera: right-drag +1000 px (y) left the pitch at %.3f, want the clamp 85 (PITCH_MAX_DEG)" % p3)

	# left-drag pan keeps main's constant on-screen speed and uses the pitch variable: a vertical 100 px drag at pitch 20
	# moves the target on the ground by 100 x per_px / sin(pitch), per_px = 2 x distance x tan(fov / 2) / viewport height
	# (orbit_camera.gd:_pan; main divides by sin(55) whatever the pitch).
	await _motion(Vector2(0.0, -1000.0), MOUSE_BUTTON_MASK_RIGHT)
	var pitch_before := _pitch_deg()
	var t0: Vector3 = _rig.get_target()
	var dist: float = _rig.get_distance()
	var height := maxf(_rig.get_viewport().get_visible_rect().size.y, 1.0)
	var per_px := 2.0 * dist * tan(deg_to_rad(_cam.fov) * 0.5) / height
	await _motion(Vector2(0.0, 100.0), MOUSE_BUTTON_MASK_LEFT)
	var tgt: Vector3 = _rig.get_target()
	var moved: float = (tgt - t0).length()
	var want := 100.0 * per_px / sin(deg_to_rad(pitch_before))
	_check(absf(moved - want) <= 0.005 * want, "B23 camera: left-drag 100 px (y) at pitch %.2f moved the target %.4f, want %.4f (100 x per_px %.5f / sin(pitch); main uses sin(55) always)" % [pitch_before, moved, want, per_px])
	_rig.set_view(25.0, Vector3.ZERO)
	await _frames(1)


func _owner_colour(st: Dictionary, owner: int) -> Color:
	var a = st.get("owner_colours", {}).get(owner, null)
	return Color(a[0], a[1], a[2], a[3]) if a != null else Color(-1, -1, -1, -1)


func _check_colours(snap: Dictionary) -> void:
	var owners: Array = []
	for r in snap.get("regions", []):
		var o := int(r.get("owner", -1))
		if not owners.has(o):
			owners.append(o)
	_ctrl(owners.has(-1) and owners.has(PLAYER_FACTION) and owners.has(0), "fixture holds owners -1, %d and 0" % PLAYER_FACTION)

	# control: without the key the 0.95 branch is unreached (paste this line)
	var no_key: Node = await _new_view(snap)
	var st0: Dictionary = no_key.qa_state()
	var any_player_val := false
	for o in owners:
		if o >= 0 and absf(_owner_colour(st0, o).v - 0.95) <= EPS:
			any_player_val = true
	_ctrl(not any_player_val and not snap.has("player_faction"),
		"with no player_faction key in the snapshot dict no owner colour has value 0.95 (the player branch is unreached: key absent -> player faction -1)")
	no_key.queue_free()
	await _frames(1)

	var keyed := snap.duplicate(true)
	keyed["player_faction"] = PLAYER_FACTION
	var v: Node = await _new_view(keyed)
	var st: Dictionary = v.qa_state()
	# owner -1: NEUTRAL_COLOUR (prototype galaxy_view.gd:6, :86-87)
	var neutral := _owner_colour(st, -1)
	_check(neutral.is_equal_approx(Color(0.55, 0.55, 0.58, 1.0)), "B23 colour: owner -1 colour is %s, want the neutral grey (0.55, 0.55, 0.58, 1.0) (galaxy_view.gd:6)" % str(neutral))
	# player faction: value 0.95, saturation 0.65, golden-angle hue (prototype :93-95)
	var pc := _owner_colour(st, PLAYER_FACTION)
	_check(absf(pc.v - 0.95) <= EPS and absf(pc.s - 0.65) <= EPS,
		"B23 colour: player faction %d colour has value %.4f saturation %.4f, want 0.95 and 0.65 (galaxy_view.gd:93-95; Rev 12b)" % [PLAYER_FACTION, pc.v, pc.s])
	_check(absf(pc.h - fposmod(float(PLAYER_FACTION) * GOLDEN_ANGLE, 1.0)) <= EPS,
		"B23 colour: player faction hue %.4f, want the golden-angle hue %.4f (unchanged)" % [pc.h, fposmod(float(PLAYER_FACTION) * GOLDEN_ANGLE, 1.0)])
	# every other non-neutral owner: value 0.85, saturation 0.65, hue unchanged
	var bad_val := 0
	var bad_hue := 0
	for o in owners:
		if o < 0 or o == PLAYER_FACTION:
			continue
		var c := _owner_colour(st, o)
		if absf(c.v - 0.85) > EPS or absf(c.s - 0.65) > EPS:
			bad_val += 1
		if absf(c.h - fposmod(float(o) * GOLDEN_ANGLE, 1.0)) > EPS:
			bad_hue += 1
	_ctrl(bad_val == 0 and bad_hue == 0, "every other non-neutral owner keeps value 0.85, saturation 0.65 and the golden-angle hue (%d off in value, %d off in hue)" % [bad_val, bad_hue])
	# the region colours follow the owner colours (the player's regions carry the 0.95 colour)
	var rc = st.get("region_colours", {})
	var wrong := 0
	for r in keyed.get("regions", []):
		var o := int(r.get("owner", -1))
		var got = rc.get(int(r.get("i", -1)), null)
		var want := _owner_colour(st, o)
		if got == null or not Color(got[0], got[1], got[2], got[3]).is_equal_approx(want):
			wrong += 1
	_ctrl(wrong == 0, "region_colours equal their owner's owner_colours entry for all %d regions (%d off)" % [REGIONS, wrong])
	v.queue_free()
	await _frames(1)


func _flash_nodes(v: Node) -> Array:
	var out: Array = []
	for c in v.get_children():
		if c is MeshInstance3D:
			out.append(c)
	return out


func _check_flash() -> void:
	var snap = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE_PATH))
	var v: Node = await _new_view(snap)
	var before := _flash_nodes(v).size()
	var n: int = v.flash_from_delta({"type": "delta", "tick": 11, "regions": [], "events": [],
		"attacks": [{"attacker": 0, "target": 7, "band": 2, "conquest": 0}], "collisions": [], "revolts": [], "factions": []})
	_ctrl(n == 1 and int(v.qa_state().get("flashes_active", -1)) == 1, "flash_from_delta spawns 1 flash for one attack and qa_state.flashes_active is 1 (got %d, %s)" % [n, str(v.qa_state().get("flashes_active"))])
	var fl := _flash_nodes(v)
	_check(fl.size() == before + 1, "B23 flash: the view gained %d MeshInstance3D children for one flash, want 1" % (fl.size() - before))
	if fl.size() > 0:
		var mi: MeshInstance3D = fl[fl.size() - 1]
		var quad := mi.mesh as QuadMesh
		_check(quad != null, "B23 flash: the flash mesh is %s, want a QuadMesh (prototype galaxy_view.gd:282-283)" % str(mi.mesh))
		if quad != null:
			_check(quad.size.is_equal_approx(Vector2(1.5, 1.5)), "B23 flash: QuadMesh size %s, want (1.5, 1.5) (galaxy_view.gd:283 Vector2(3, 3) x CIV_SCALE 0.5)" % str(quad.size))
		var mat = mi.material_override
		_check(mat is StandardMaterial3D and mat.billboard_mode == BaseMaterial3D.BILLBOARD_ENABLED,
			"B23 flash: material billboard_mode is %s, want BILLBOARD_ENABLED (galaxy_view.gd:289)" % (str(mat.billboard_mode) if mat is StandardMaterial3D else "no StandardMaterial3D"))
		_ctrl(mat is StandardMaterial3D and mat.transparency == BaseMaterial3D.TRANSPARENCY_ALPHA and mat.shading_mode == BaseMaterial3D.SHADING_MODE_UNSHADED
			and Color(mat.albedo_color.r, mat.albedo_color.g, mat.albedo_color.b).is_equal_approx(Color(1.0, 0.45, 0.2)),
			"flash material is unshaded, alpha-blended and carries the attack colour (1.0, 0.45, 0.2) (colours per kind unchanged)")
	# lifetime: 0.6 s of frames (prototype FLASH_DURATION galaxy_view.gd:8): alive at 0.3 s, gone by 0.75 s
	var t0 := Time.get_ticks_msec()
	while Time.get_ticks_msec() - t0 < 300:
		await process_frame
	_ctrl(int(v.qa_state().get("flashes_active", -1)) == 1, "flash still active after 0.3 s (flashes_active %s)" % str(v.qa_state().get("flashes_active")))
	while Time.get_ticks_msec() - t0 < 750:
		await process_frame
	var gone := int(v.qa_state().get("flashes_active", -1))
	_check(gone == 0, "B23 flash: flashes_active %d after %d ms, want 0 once FLASH_SECONDS 0.6 has passed (main keeps it 1.0 s)" % [gone, Time.get_ticks_msec() - t0])
	v.queue_free()
	await _frames(1)


# prototype legacy_constellation_renderer.gd:149 (hash_val divided by CIV_SCALE) and :181 (total_length < 0.001 x CIV_SCALE)
func _check_arc_and_tube() -> void:
	var civ := 0.5
	var rend: Node3D = (load(FILAMENT_PATH) as GDScript).new()
	var from_pos := Vector3(3.0, 0.0, 4.0)
	var to_pos := Vector3(9.0, 2.0, 12.0)
	var frac := 0.15   # ARC_HEIGHT_FRACTION, unchanged
	var mid := (from_pos + to_pos) * 0.5
	var arc_h := from_pos.distance_to(to_pos) * frac
	var dir := (to_pos - from_pos).normalized()
	var perp := dir.cross(Vector3.UP).normalized()
	var raw := from_pos.x * 73.0 + from_pos.z * 137.0 + to_pos.x * 97.0 + to_pos.z * 53.0
	var want_pt := _bezier_mid(from_pos, to_pos, mid, arc_h, perp, sin(raw / civ))
	var unscaled_pt := _bezier_mid(from_pos, to_pos, mid, arc_h, perp, sin(raw))
	_ctrl(want_pt.distance_to(unscaled_pt) > 0.1, "arc fixture separates the scaled and the unscaled hash by %.3f world units (fixture premise)" % want_pt.distance_to(unscaled_pt))
	var curve: PackedVector3Array = rend._compute_bezier_arc(from_pos, to_pos)
	_ctrl(curve.size() == 17 and curve[0].is_equal_approx(from_pos) and curve[16].is_equal_approx(to_pos), "arc has 17 points from the first to the second system")
	var mid_pt: Vector3 = curve[8] if curve.size() == 17 else Vector3.ZERO
	_check(mid_pt.distance_to(want_pt) <= 0.001, "B23 W3: arc midpoint %s, want %s (hash_val / CIV_SCALE 0.5, prototype :149); the unscaled hash gives %s" % [str(mid_pt), str(want_pt), str(unscaled_pt)])
	# the degenerate-curve guard: total length < 0.001 x CIV_SCALE builds nothing (prototype :181)
	var tiny := PackedVector3Array([Vector3.ZERO, Vector3(0.0003, 0.0, 0.0), Vector3(0.0007, 0.0, 0.0)])
	var mesh_tiny: ArrayMesh = rend._build_tube_mesh(tiny, 0.01)
	_check(mesh_tiny.get_surface_count() == 1, "B23 W3: a curve of total length 0.0007 builds %d surfaces, want 1 (guard is 0.001 x 0.5 = 0.0005, prototype :181; main guards at 0.001)" % mesh_tiny.get_surface_count())
	var shorter := PackedVector3Array([Vector3.ZERO, Vector3(0.0001, 0.0, 0.0), Vector3(0.0002, 0.0, 0.0)])
	var mesh_short: ArrayMesh = rend._build_tube_mesh(shorter, 0.01)
	_ctrl(mesh_short.get_surface_count() == 0, "a curve of total length 0.0002 builds no surface (below the guard under both values)")
	var normal := PackedVector3Array([Vector3.ZERO, Vector3(0.05, 0.0, 0.0), Vector3(0.1, 0.0, 0.0)])
	_ctrl((rend._build_tube_mesh(normal, 0.01) as ArrayMesh).get_surface_count() == 1, "a curve of total length 0.1 builds one surface")
	rend.free()


func _bezier_mid(p0: Vector3, p3: Vector3, mid: Vector3, arc_h: float, perp: Vector3, sin_hash: float) -> Vector3:
	var off := sin_hash * arc_h * 0.5
	var p1 := p0.lerp(mid, 0.5) + Vector3(0.0, arc_h, 0.0) + perp * off
	var p2 := mid.lerp(p3, 0.5) + Vector3(0.0, arc_h, 0.0) + perp * off
	return 0.125 * p0 + 0.375 * p1 + 0.375 * p2 + 0.125 * p3   # cubic bezier at t = 0.5


# W2: a driven move_camera_to_region emits camera_move_completed after FOCUS_SEC (orbit_camera.gd:19, 1.5 s), not 0.6 s.
func _check_camera_done_timer(snap: Dictionary) -> void:
	var v: Node = await _new_view(snap)
	var done := [false]
	v.camera_move_completed.connect(func(): done[0] = true)
	v.move_camera_to_overview(1.0)
	var t0 := Time.get_ticks_msec()
	while Time.get_ticks_msec() - t0 < 1000:
		await process_frame
	_check(not done[0], "B23 W2: camera_move_completed fired within 1.0 s of move_camera_to_overview, want it after FOCUS_SEC 1.5 s (a fixed create_timer(0.6) fires 0.9 s early)")
	while Time.get_ticks_msec() - t0 < 2000 and not done[0]:
		await process_frame
	_ctrl(done[0], "camera_move_completed fires (within 2.0 s of move_camera_to_overview)")
	v.queue_free()
	await _frames(1)

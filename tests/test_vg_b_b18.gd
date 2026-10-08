extends SceneTree

# Piece B18 (docs/northstar/plans/2026-10-07-visible-game-spec.md rev 4, lane B; bible E-16 S-106;
# review docs/northstar/story_reviews/B.md row S-106: "small dot cluster (about 40 percent of the
# screen width) on a flat grey background"): background and framing of the instanced galaxy view
# (res://scenes/galaxy/galaxy_view.tscn, driven=true, seed1 tick10 fixture).
#   Background: a WorldEnvironment (or the Camera3D's environment) under the view has
#   background_mode BG_COLOR and the approved mockup's colour, read on origin/push/galaxy-field:
#   scenes/mockups/galaxy/galaxy_mockup.tscn:10-11 (background_mode = 1,
#   background_color = Color(0.0392157, 0.0509804, 0.0705882, 1)).
#   Framing: the mockup's default distance is 50 * CIV_SCALE (orbit_camera.gd DIST_DEFAULT;
#   galaxy_gen.gd:7 CIV_SCALE 0.5) in the mockup's own world units, which the main view's layout
#   does not share (DEFAULT_DISTANCE 180), so distance equality is NOT checkable. The checkable
#   form is the projected extent: after set_snapshot the systems_px of qa_state() span between 60%
#   and 90% of the viewport width (the review reads 40% today; the 60..90 band is the brief's).
# NEEDS A DISPLAY: headless projection is not the windowed one (1.5% vs 24.6% on main), so run
# under xvfb: xvfb-run -a godot.real --path . -s res://tests/test_vg_b_b18.gd

const SCENE_PATH := "res://scenes/galaxy/galaxy_view.tscn"
const FIXTURE_PATH := "res://tests/transport/fixtures/snapshot_seed1_tick10.json"
const BG_COLOUR := Color(0.0392157, 0.0509804, 0.0705882, 1.0)   # galaxy_mockup.tscn:11
const BG_MODE_COLOR := 1                                           # galaxy_mockup.tscn:10
const WIDTH_MIN := 0.60
const WIDTH_MAX := 0.90

var _pass := 0
var _fail := 0
var _msgs: Array[String] = []


func _initialize() -> void:
	await _run()
	print("\n=== B18 background and framing: PASS %d FAIL %d ===" % [_pass, _fail])
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


func _find_env(n: Node) -> Environment:
	if n is WorldEnvironment and (n as WorldEnvironment).environment != null:
		return (n as WorldEnvironment).environment
	if n is Camera3D and (n as Camera3D).environment != null:
		return (n as Camera3D).environment
	for c in n.get_children():
		var e := _find_env(c)
		if e != null:
			return e
	return null


func _run() -> void:
	var f := FileAccess.open(FIXTURE_PATH, FileAccess.READ)
	var snap = JSON.parse_string(f.get_as_text()) if f != null else null
	_check(snap is Dictionary, "control: fixture readable")
	if not (snap is Dictionary):
		return
	var v: Node = (load(SCENE_PATH) as PackedScene).instantiate()
	v.driven = true
	get_root().add_child(v)
	await process_frame
	await process_frame
	v.set_snapshot(snap)
	await process_frame
	await process_frame

	var env := _find_env(v)
	_check(env != null, "B18: no WorldEnvironment or Camera3D environment under the galaxy view (background is the engine default grey)")
	if env != null:
		_check(env.background_mode == BG_MODE_COLOR, "B18: background_mode %d, want %d (BG_COLOR)" % [env.background_mode, BG_MODE_COLOR])
		var c := env.background_color
		_check(absf(c.r - BG_COLOUR.r) < 0.002 and absf(c.g - BG_COLOUR.g) < 0.002 and absf(c.b - BG_COLOUR.b) < 0.002,
			"B18: background_color %s, want the mockup's %s" % [str(c), str(BG_COLOUR)])

	var st: Dictionary = v.qa_state()
	var px: Dictionary = st.get("systems_px", {})
	_check(px.size() > 10, "control: qa_state.systems_px has more than 10 systems, got %d" % px.size())
	var vw := float(v.get_viewport().get_visible_rect().size.x)
	_check(vw > 0.0, "control: viewport width > 0")
	if px.size() > 10 and vw > 0.0:
		var lo := INF
		var hi := -INF
		for k in px:
			var x := float(px[k][0])
			lo = minf(lo, x)
			hi = maxf(hi, x)
		var frac := (hi - lo) / vw
		_check(frac >= WIDTH_MIN and frac <= WIDTH_MAX,
			"B18: default framing spans %.1f%% of the viewport width (x %.0f..%.0f of %.0f), want %d..%d%%" % [frac * 100.0, lo, hi, vw, int(WIDTH_MIN * 100), int(WIDTH_MAX * 100)])
	v.queue_free()

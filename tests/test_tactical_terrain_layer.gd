extends SceneTree

# Piece 3d (docs/northstar/plans/2026-10-06-terrain-stage3-spec.md rev 3, Pieces row 3d,
# "What the audit changed", "What the pre-flight changed"). The ground layer under the
# unit drawing in the ground era. RED on origin/push/t3-contract because
# res://scenes/tactical_c/terrain_layer.gd does not exist and tactical_view.gd has no
# ground layer ("A Node2D child drawn first ... no terrain adds nothing").
#
# Interface this test requires (the spec names no method names; these are the test's
# choice, to be confirmed by the Architect before the 3d card is cut):
#   terrain dict (3c's c_bridge.terrain(), the shape the pipe's terrain frame decodes to,
#     docs/architecture.md terrain_dump): {cells_w:int, cells_h:int, bands:PackedByteArray
#     (row-major, 1..5), walkable:PackedByteArray (0/1), slopes:Array of {x0,y0,x1,y1,mx,my,
#     length,lower_band,upper_band}}; empty dict = space era.
#   terrain_layer.gd (extends Node2D):
#     set_terrain(t: Dictionary) -> void
#     ground_texture() -> Texture2D          null when no terrain
#     screen_rect(world_scale: float, camera: Vector2) -> Rect2   (1920x1080 screen, the
#                                            same mapping as tactical_view _world_to_screen)
#     slope_ticks() -> Array                 [[Vector2 a, Vector2 b], ...] in world units
#   tactical_view.gd: set_terrain(t: Dictionary); qa_state()["ground_layer"] is
#     {"present": bool, "cells_w": int, "cells_h": int, "ticks": int}; absent or present=false
#     with no terrain; the layer is the first child (drawn first).
# Constants (spec pre-flight, from origin/push/proto-walkers walkers_mockup.gd):
#   BAND_COLOURS, STEEP_COLOUR lerped 0.5 on unwalkable land; slope tick length 60 wu (draft).
# Era items (3e/3f, spec "What the audit changed" / "What the pre-flight changed"): checked
# here where a Godot test can reach them.

const LAYER_PATH := "res://scenes/tactical_c/terrain_layer.gd"
const VIEW_PATH := "res://scenes/tactical_c/tactical_view.tscn"
const ERA_CONFIG_PATH := "res://autoload/era_config.gd"
const BANDS := [Color(0.40, 0.72, 0.42), Color(0.72, 0.80, 0.38), Color(0.90, 0.68, 0.30),
	Color(0.72, 0.48, 0.30), Color(0.92, 0.90, 0.88)]
const STEEP := Color(0.85, 0.10, 0.85)
const CELL_WU := 100.0
const TICK_WU := 60.0
const TOL := 1.5 / 255.0

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	await _run_tests()
	print("\n=== Tactical Terrain Layer Test Results ===")
	print("PASS: %d  FAIL: %d" % [_pass_count, _fail_count])
	if _fail_count > 0:
		print("Failures:")
		for msg in _fail_msgs:
			print("  - " + msg)
		print("=== RED ===\n")
		quit(1)
	else:
		print("=== GREEN ===\n")
		quit(0)


func _assert(cond: bool, msg: String) -> void:
	if cond:
		_pass_count += 1
	else:
		_fail_count += 1
		_fail_msgs.append(msg)


func _near(a: Color, b: Color) -> bool:
	return absf(a.r - b.r) < TOL and absf(a.g - b.g) < TOL and absf(a.b - b.b) < TOL


# A fake terrain: band = 1 + (cx*5/w); row 0 is walkable; cell (1,1) is steep (walkable 0)
# at band 2; the last cell is band 5 and walkable. One slope with a midpoint in cell (3,3).
func _fake(n: int) -> Dictionary:
	var bands := PackedByteArray()
	var walk := PackedByteArray()
	bands.resize(n * n)
	walk.resize(n * n)
	for cy in n:
		for cx in n:
			bands[cy * n + cx] = 1 + (cx * 5) / n
			walk[cy * n + cx] = 1
	bands[1 * n + 1] = 2
	walk[1 * n + 1] = 0
	bands[n * n - 1] = 5
	var slopes := [{"x0": 300.0, "y0": 350.0, "x1": 350.0, "y1": 350.0, "mx": 350.0, "my": 350.0,
		"length": 50.0, "lower_band": 1, "upper_band": 2}]
	return {"cells_w": n, "cells_h": n, "bands": bands, "walkable": walk, "slopes": slopes}


func _make_layer() -> Node:
	var s = load(LAYER_PATH)
	if s == null:
		return null
	return s.new()


func _run_tests() -> void:
	# --- terrain_layer.gd exists (red: "tactical_view.gd ... there is no _draw"; the layer is new)
	var layer := _make_layer()
	_assert(layer != null, "3d: " + LAYER_PATH + " does not exist (spec row 3d: 'scenes/tactical_c/terrain_layer.gd (new, under the C5 glob)')")
	if layer != null:
		_assert(layer is Node2D, "3d: terrain_layer must extend Node2D ('A Node2D child drawn first')")
		for m in ["set_terrain", "ground_texture", "screen_rect", "slope_ticks"]:
			_assert(layer.has_method(m), "3d: terrain_layer.gd lacks method " + m)
		if layer.has_method("set_terrain") and layer.has_method("ground_texture"):
			# texture sized cells_w x cells_h: 80 and 240 (spec: 'a fake 80^2 and 240^2 terrain each give a texture of that size')
			for n in [80, 240]:
				layer.call("set_terrain", _fake(n))
				var tex = layer.call("ground_texture")
				_assert(tex != null and tex.get_width() == n and tex.get_height() == n,
					"3d: a fake %d^2 terrain must give a %d x %d texture (not a fixed 160x160)" % [n, n, n])
			# colours (240 terrain still loaded is replaced by 80 for cheap pixel checks)
			layer.call("set_terrain", _fake(80))
			var img: Image = layer.call("ground_texture").get_image()
			_assert(_near(img.get_pixel(79, 79), BANDS[4]),
				"3d: a band-5 walkable cell is the ramp top (0.92,0.90,0.88); got " + str(img.get_pixel(79, 79)))
			_assert(_near(img.get_pixel(0, 5), BANDS[0]),
				"3d: a band-1 walkable cell is the ramp bottom (0.40,0.72,0.42); got " + str(img.get_pixel(0, 5)))
			# steep cell tinted: band-2 colour lerped 0.5 to STEEP
			_assert(_near(img.get_pixel(1, 1), BANDS[1].lerp(STEEP, 0.5)),
				"3d: an unwalkable cell is its band colour lerped 0.5 to (0.85,0.10,0.85); got " + str(img.get_pixel(1, 1)))
			# POSITIVE CONTROL: the same band, walkable, is NOT tinted -- proves the steep check can tell tint from none
			_assert(_near(img.get_pixel(1, 2), BANDS[0]) or _near(img.get_pixel(1, 2), BANDS[1]),
				"3d control: a walkable cell next to the steep one is untinted; got " + str(img.get_pixel(1, 2)))
			_assert(not _near(img.get_pixel(1, 1), BANDS[1]),
				"3d control: the steep cell must differ from the plain band-2 colour")
		if layer.has_method("slope_ticks"):
			layer.call("set_terrain", _fake(80))
			var ticks: Array = layer.call("slope_ticks")
			_assert(ticks.size() == 1, "3d: one slope in the terrain gives one tick; got %d" % ticks.size())
			if ticks.size() == 1:
				var a: Vector2 = ticks[0][0]
				var b: Vector2 = ticks[0][1]
				_assert(absf(a.distance_to(b) - TICK_WU) < 0.5, "3d: slope tick length is 60 wu (Settings); got %f" % a.distance_to(b))
				_assert(((a + b) * 0.5).distance_to(Vector2(350, 350)) < 1.0, "3d: the tick is centred on the slope midline point (mx,my)")
			layer.call("set_terrain", {})
			_assert(layer.call("slope_ticks").is_empty(), "3d: empty terrain has no ticks")
			_assert(layer.call("ground_texture") == null, "3d: empty terrain has no texture (space: nothing added)")
		if layer.has_method("screen_rect") and layer.has_method("set_terrain"):
			layer.call("set_terrain", _fake(80))
			# 80 cells x 100 wu = 8000 wu; scale 0.25, camera at the map centre (4000,4000)
			# -> rect size 2000 px, origin = (0-4000)*0.25 + 960, (0-4000)*0.25 + 540
			var r: Rect2 = layer.call("screen_rect", 0.25, Vector2(4000, 4000))
			_assert(r.position.distance_to(Vector2(-40, -460)) < 0.5 and r.size.distance_to(Vector2(2000, 2000)) < 0.5,
				"3d: screen rect follows _world_scale and _camera (1920x1080 screen); got " + str(r))
			var r2: Rect2 = layer.call("screen_rect", 0.5, Vector2(0, 0))
			_assert(r2.position.distance_to(Vector2(960, 540)) < 0.5 and r2.size.distance_to(Vector2(4000, 4000)) < 0.5,
				"3d: screen rect recomputed for another scale and camera; got " + str(r2))
		layer.free()

	# --- tactical_view.gd wiring (red: no ground layer in the view today)
	var vs = load(VIEW_PATH)
	_assert(vs != null, "3d: tactical_view.tscn missing")
	if vs != null:
		var v: Node = vs.instantiate()
		root.add_child(v)
		await process_frame
		_assert(v.has_method("set_terrain"), "3d: tactical_view.gd lacks set_terrain(t: Dictionary)")
		var gl0: Dictionary = v.qa_state().get("ground_layer", {})
		_assert(gl0.has("present") and gl0["present"] == false,
			"3d: qa_state()['ground_layer'] must exist and say present=false with no terrain ('the QA state names the ground layer'; space adds nothing)")
		var before := v.get_child_count()
		if v.has_method("set_terrain"):
			v.call("set_terrain", {})
			_assert(v.get_child_count() == before, "3d: empty terrain adds no node to the view (space screen unchanged)")
			v.call("set_terrain", _fake(240))
			var gl: Dictionary = v.qa_state().get("ground_layer", {})
			_assert(gl.get("present", false) == true and int(gl.get("cells_w", 0)) == 240 and int(gl.get("cells_h", 0)) == 240,
				"3d: after set_terrain(240^2) qa_state()['ground_layer'] reports present, 240 x 240; got " + str(gl))
			_assert(int(gl.get("ticks", 0)) == 1, "3d: qa_state ground_layer.ticks counts the slope ticks; got " + str(gl))
			var first := v.get_child(0)
			_assert(first != null and first.get_script() != null and str(first.get_script().resource_path) == LAYER_PATH,
				"3d: the ground layer is the view's first child (drawn first, under the units)")
			v.call("set_terrain", {})
			_assert(v.qa_state().get("ground_layer", {}).get("present", true) == false,
				"3d: clearing terrain (a space mission after a ground one) removes the layer")
		v.queue_free()

	# --- era items the audit/pre-flight fixed (3e/3f), reachable from Godot
	var ec := load(ERA_CONFIG_PATH)
	_assert(ec != null, "3e: era_config.gd must load")
	if ec != null:
		var consts: Dictionary = ec.get_script_constant_map()
		_assert(not consts.has("ACTIVE_ERA_ID"),
			"3e: ACTIVE_ERA_ID must become a var (spec audit row: 'EraConfig.ACTIVE_ERA_ID is a const'); it is still a const")
		_assert(consts.has("TYPE_IDS"), "3f: era_config.gd needs const TYPE_IDS (pre-flight: name-to-id table)")
		if consts.has("TYPE_IDS"):
			var t: Dictionary = consts["TYPE_IDS"]
			var want := {"raider": 0, "interceptor": 1, "vanguard": 2, "warden": 3, "bombard": 4, "bastion": 5}
			var ok := true
			for k in want:
				ok = ok and t.has(k) and int(t[k]) == want[k]
			_assert(ok and t.size() == 6, "3f: TYPE_IDS must be raider 0, interceptor 1, vanguard 2, warden 3, bombard 4, bastion 5 (csrc/unit.c:69-76); got " + str(t))
		var src := FileAccess.get_file_as_string(ERA_CONFIG_PATH)
		_assert(src.contains("\"--era\"") and not src.contains("--era="),
			"3e: era_config.gd reads the user arg in the space form '--era <id>' (pre-flight), not '--era=<id>'")
		_assert(src.contains("kind") and src.contains("movement_kinds"), "3e: era_config.gd has kind() and movement_kinds()")
	var ui := FileAccess.get_file_as_string("res://autoload/ui_data_bus.gd")
	_assert(ui.count("era_id") >= 3,
		"3e: ui_data_bus.gd must carry [game] era_id in both branches of _load_settings and in save_settings (pre-flight: unknown keys are dropped); found %d mentions" % ui.count("era_id"))
	var pipe_src := FileAccess.get_file_as_string("res://csrc/pipe/om_pipe.c")
	_assert(pipe_src.contains("terrain generate failed"),
		"3a/3b: handle_mission_start answers write_error(\"mission_start\", \"terrain generate failed\") on a -1 generate (named error, no silent flat mission)")
	_assert(pipe_src.contains("\"movement_kinds\""), "3b: handle_mission_start parses the flat movement_kinds list")

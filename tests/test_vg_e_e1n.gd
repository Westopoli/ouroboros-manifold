extends SceneTree
# NEEDS A DISPLAY (the [PROJECT], [COLOUR] and [DESTROYED] groups read rendered pixels): run under
#   timeout 1800 xvfb-run -a -s '-screen 0 1920x1080x24' godot.real --path . --resolution 1920x1080 -s tests/test_vg_e_e1n.gd
#
# VG-E1 piece E1n (scenes/economy/map_markers.gd, class MapMarkers, extends Node2D, name "MapMarkers"): the map marks the
# strongpoints and the side's base of operations. Tests written before the code; RED on origin/main because
# res://scenes/economy/map_markers.gd does not exist. Builders never edit this file.
#
# Rules this file proves (docs/bible/epics/E-16-client-camera-hud-and-world-view.md, S-235, word for word):
#   R-235-01  Given the map view (S-161) and the tactical view, When the economy's places are drawn, Then the economic
#             locations, the neutral settlements, the objective, the side's base of operations, its expansions and forward
#             works, and on land maps the strongpoints are marked (E-22 S-175, S-177; E-15).
#   R-235-02  Given an environmental trouble travelling across the map, When it is drawn, Then both sides see where it is as
#             it moves (E-15 holds what it does).                                  [stub: not asserted here, no sim source]
#   R-235-03  Given the ticker (R-104-01), When a base is occupied, a side falls back to an expansion, an expansion is
#             founded, a weather trouble arrives, or a strongpoint is taken or lost, Then the ticker names it; no other
#             economy beat reaches the ticker (Westley, 2026-10-12).              [the ticker half is in the TickerBeats test]
#   R-235-04  Given a shipment that does not arrive (E-22 S-176), When the ticker, the banners and the map are read, Then
#             nothing on them explains why.            [the map half: no marker is produced for anything outside the kinds]
#   R-104-01  Given a mission, When the HUD is drawn, Then the player can always see the objective list with progress
#             (top-left) and a quiet ticker of notable beats beneath it; the ticker recognizes structure captured, structure
#             lost, force routed, and objective threshold crossed, and nothing else at launch.   [the ticker lives in E1m]
# Spec sentence (docs/..plans/2026-10-07-visible-game-spec.md, "S-235 ticker (amends the E1m and E1n paragraphs; Q-235-01
# closed)"): "The ticker carries the four beats plus a strongpoint taken or lost; forward bases are not named. E1m, E1n and
# the S-235 play are unblocked; their drafters take the five beats as the inventory."
# Rulings used (Architect 2026-10-14): GAP 2 (b) the owner of a strongpoint is read from the structures rows joined to the
# strongpoint ids; GAP 6 MapMarkers is a 2D Node2D layer beside StructuresLayer for STRONGPOINTS and the HOME BASE (kinds
# "strongpoint", "home_base"); economic locations, neutral settlements, expansions, forward works and weather are stubs and
# produce no marker; GAP 7 (a) the marker look is DRAFT-e1n-marker (not asserted beyond what is said per case below).
#
# Interface (fixed in full): set_frame(frame, local_faction, world_scale, camera) as StructuresLayer.set_frame
# (structures_layer.gd:25); markers() -> [{kind: String, x: float, y: float, owner: int, state: int}] world wu, strongpoint
# rows ascending id, then the home base; empty before the first set_frame. The home base is the map node of kind 7 nearest
# the centroid of the local faction's units (tactical_view.gd SPAWN_NODE_KIND / _home_box). The strongpoint state (0 free,
# 1 held, 2 rubble, docs/architecture.md:403) comes from frame["strongpoints"]; a strongpoint whose structures row has left
# the frame reads state 2 (rubble, R-218-05, GAP 7 "destroyed mark").
#
# Not written (no quoted rule or interface states it; reported as gaps): the home_base marker with NO own unit in the frame;
# the home_base marker's owner and state values (only that they are ints); the exact look of any marker (DRAFT-e1n-marker).
# Groups: [CONTROL] green on the built tree; [LOAD] [STRONGPOINT] [HOME] [PROJECT] [COLOUR] [KINDS] [DESTROYED] red until E1n.

const TITLE := "VG-E1 E1n map markers"
const MARKERS_PATH := "res://scenes/economy/map_markers.gd"
const STRUCTURES_PATH := "res://scenes/tactical_c/structures_layer.gd"
const SCREEN_CENTER := Vector2(960.0, 540.0)    # structures_layer.gd:3, the projection's screen origin
const KINDS := ["strongpoint", "home_base"]      # GAP 6
const LOCAL := 0
const ENEMY := 1
# Detector allowance, not a game tolerance: pixel bounding boxes of the same fixed-size mark drawn at integer screen
# positions agree to 1 px; the positive control (StructuresLayer) is measured with the same detector in [CONTROL].
const RASTER_TOL_PX := 1.0
const COLOR_TOL := 0.02

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _red_groups: Dictionary = {}


func _initialize() -> void:
	await _run_tests()
	print("\n=== %s Results ===" % TITLE)
	print("PASS: %d  FAIL: %d" % [_pass_count, _fail_count])
	if _fail_count > 0:
		print("Failures:")
		for msg in _fail_msgs:
			print("  - " + msg)
		print("RED GROUPS: %s" % str(_red_groups.keys()))
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
		_red_groups[msg.get_slice("]", 0).trim_prefix("[")] = true


func _run_tests() -> void:
	_control_structures_layer()
	await _control_pixel_detector()
	_load()
	_strongpoint()
	_home()
	await _project()
	await _colour()
	_kinds()
	await _destroyed()


# ---------------------------------------------------------------- fixtures

func _scr(w: Vector2, s: float, c: Vector2) -> Vector2:
	return (w - c) * s + SCREEN_CENTER


func _unit(id: int, faction: int, x: float, y: float) -> Dictionary:
	return {"id": id, "faction": faction, "type": 0, "tier": 0, "x": x, "y": y, "hp": 100.0, "layer": 1, "facing": 0.0,
		"target": -1, "state": 0}


# A structures row (section 2 of the spec: {id,type,owner,x,y,hp,stage,cap,nst,next_type,period}).
func _row(id: int, owner: int, x: float, y: float, hp: float = 3000.0) -> Dictionary:
	return {"id": id, "type": 0, "owner": owner, "x": x, "y": y, "hp": hp, "stage": 0, "cap": 0, "nst": 0, "next_type": 0,
		"period": 0}


# One strongpoint entry (docs/architecture.md:415: {id,x,y,owner,state}).
func _sp(id: int, x: float, y: float, owner: int, state: int) -> Dictionary:
	return {"id": id, "x": x, "y": y, "owner": owner, "state": state}


# A full tactical view as CBridge hands it to the layers (c_bridge.gd _reconstruct_tactical).
func _frame(structures: Array, strongpoints: Array, units: Array = [], nodes: Array = [], extra: Dictionary = {}) -> Dictionary:
	var f := {"type": "tactical", "tick": 100, "full": true, "player_faction": LOCAL, "units": units, "structures": structures,
		"strongpoints": strongpoints, "map": {"nodes": nodes, "cover": [], "obstacles": []}, "events": [], "objectives": [],
		"lots": [], "profiles": []}
	f.merge(extra, true)
	return f


# Three strongpoints, ids 2, 5, 9; owners own, enemy, -1; states 1, 1, 0; rows agree with the list.
func _three_sp_frame() -> Dictionary:
	return _frame(
		[_row(2, LOCAL, 1200.0, 1500.0), _row(5, ENEMY, 2600.0, 2300.0), _row(9, -1, 3400.0, 900.0)],
		[_sp(2, 1200.0, 1500.0, LOCAL, 1), _sp(5, 2600.0, 2300.0, ENEMY, 1), _sp(9, 3400.0, 900.0, -1, 0)])


func _make_markers(tag: String) -> Node2D:
	_assert(ResourceLoader.exists(MARKERS_PATH), "[%s] %s exists (red: file missing)" % [tag, MARKERS_PATH])
	if not ResourceLoader.exists(MARKERS_PATH):
		return null
	var s: GDScript = load(MARKERS_PATH)
	var n = s.new()
	if not (n is Node2D):
		_assert(false, "[%s] MapMarkers extends Node2D" % tag)
		return null
	root.add_child(n)
	return n


func _make_structures() -> Node2D:
	var s: GDScript = load(STRUCTURES_PATH)
	var n: Node2D = s.new()
	root.add_child(n)
	return n


func _rows(mm: Node2D) -> Array:
	return mm.call("markers")


func _of_kind(rows: Array, kind: String) -> Array:
	return rows.filter(func(m): return m.get("kind", "") == kind)


# Renders `layer` (after `setup.call(layer)`) alone in a transparent 1920x1080 SubViewport and returns the image.
func _shot(layer: Node2D, setup: Callable) -> Image:
	var vp := SubViewport.new()
	vp.size = Vector2i(1920, 1080)
	vp.transparent_bg = true
	vp.disable_3d = true
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(vp)
	if layer.get_parent() != null:
		layer.get_parent().remove_child(layer)
	vp.add_child(layer)
	setup.call(layer)
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	var img := vp.get_texture().get_image()
	vp.queue_free()
	return img


func _centre(img: Image) -> Vector2:
	var r := img.get_used_rect()
	return Vector2(r.position) + Vector2(r.size) / 2.0


func _has_color(img: Image, col: Color) -> bool:
	var r := img.get_used_rect()
	for y in range(r.position.y, r.position.y + r.size.y):
		for x in range(r.position.x, r.position.x + r.size.x):
			var p := img.get_pixel(x, y)
			if p.a >= 0.99 and absf(p.r - col.r) <= COLOR_TOL and absf(p.g - col.g) <= COLOR_TOL and absf(p.b - col.b) <= COLOR_TOL:
				return true
	return false


# ---------------------------------------------------------------- [CONTROL] green on the built tree

# The projection and the colour baseline MapMarkers must agree with: StructuresLayer.set_frame with two structures.
func _control_structures_layer() -> void:
	var sl := _make_structures()
	var f := _frame([_row(3, LOCAL, 2000.0, 2000.0), _row(4, ENEMY, 2400.0, 2200.0)], [])
	sl.call("set_frame", f, LOCAL, 0.25, Vector2(2000.0, 2000.0))
	_assert(sl.get_child_count() == 2, "[CONTROL] StructuresLayer keeps one node per structure (2), got %d" % sl.get_child_count())
	_assert(sl.call("owner_color", 3) == sl.get("OWN_COLOR"), "[CONTROL] own structure reads OWN_COLOR")
	_assert(sl.call("owner_color", 4) == sl.get("ENEMY_COLOR"), "[CONTROL] enemy structure reads ENEMY_COLOR")
	var n3: Node2D = sl.call("structure_node", 3)
	var n4: Node2D = sl.call("structure_node", 4)
	_assert(n3 != null and n3.position.is_equal_approx(SCREEN_CENTER), "[CONTROL] structure at the camera projects to the screen centre")
	_assert(n4 != null and n4.position.is_equal_approx(_scr(Vector2(2400.0, 2200.0), 0.25, Vector2(2000.0, 2000.0))),
		"[CONTROL] structure projection is (world - camera) * scale + (960, 540)")
	sl.queue_free()


# The pixel detector used below, proven on StructuresLayer: the bounding-box centre of the painted pixels moves by exactly the
# projection delta between two (camera, scale) values, and the owner colour is found among the painted pixels.
func _control_pixel_detector() -> void:
	var w := Vector2(2600.0, 2300.0)
	var f := _frame([_row(5, ENEMY, w.x, w.y)], [_sp(5, w.x, w.y, ENEMY, 1)])
	var a := await _shot(_make_structures(), func(l): l.call("set_frame", f, LOCAL, 0.25, Vector2(2200.0, 2100.0)))
	var b := await _shot(_make_structures(), func(l): l.call("set_frame", f, LOCAL, 0.5, Vector2(2000.0, 2000.0)))
	_assert(a.get_used_rect().size != Vector2i.ZERO and b.get_used_rect().size != Vector2i.ZERO, "[CONTROL] StructuresLayer paints pixels (detector sees a ring)")
	var want := _scr(w, 0.5, Vector2(2000.0, 2000.0)) - _scr(w, 0.25, Vector2(2200.0, 2100.0))
	var got := _centre(b) - _centre(a)
	_assert(absf(got.x - want.x) <= RASTER_TOL_PX and absf(got.y - want.y) <= RASTER_TOL_PX,
		"[CONTROL] detector: StructuresLayer ring centre moves by the projection delta %s, got %s" % [str(want), str(got)])
	_assert(_has_color(a, load(STRUCTURES_PATH).get("ENEMY_COLOR")), "[CONTROL] detector: the ENEMY_COLOR ring is found among the painted pixels")


# ---------------------------------------------------------------- [LOAD]

func _load() -> void:
	var mm := _make_markers("LOAD")
	if mm == null:
		return
	_assert(mm.get_script().get_global_name() == &"MapMarkers", "[LOAD] script class_name is MapMarkers")
	_assert(mm.name == &"MapMarkers", "[LOAD] _ready sets name = \"MapMarkers\", got %s" % mm.name)
	_assert(mm.has_method("markers") and mm.has_method("set_frame"), "[LOAD] markers() and set_frame() exist")
	_assert(_rows(mm).is_empty(), "[LOAD] markers() is empty before the first set_frame (R-235-01: nothing marked before a frame)")
	mm.queue_free()


# ---------------------------------------------------------------- [STRONGPOINT] R-235-01 "on land maps the strongpoints are marked"

func _strongpoint() -> void:
	var mm := _make_markers("STRONGPOINT")
	if mm == null:
		return
	mm.call("set_frame", _three_sp_frame(), LOCAL, 0.25, Vector2(2000.0, 2000.0))
	var rows := _rows(mm)
	_assert(rows.size() == 3, "[STRONGPOINT] three strongpoints and no home base give three markers, got %d" % rows.size())
	if rows.size() == 3:
		var want_ids := [2, 5, 9]
		var want_x := [1200.0, 2600.0, 3400.0]
		var want_y := [1500.0, 2300.0, 900.0]
		var want_owner := [LOCAL, ENEMY, -1]
		var want_state := [1, 1, 0]
		for i in 3:
			var m: Dictionary = rows[i]
			_assert(m.get("kind", "") == "strongpoint", "[STRONGPOINT] row %d kind is strongpoint (strongpoint rows ascending id), got %s" % [i, str(m.get("kind"))])
			_assert(typeof(m.get("x")) == TYPE_FLOAT and typeof(m.get("y")) == TYPE_FLOAT, "[STRONGPOINT] row %d x and y are floats (world wu)" % i)
			_assert(is_equal_approx(float(m.get("x", -1.0)), want_x[i]) and is_equal_approx(float(m.get("y", -1.0)), want_y[i]),
				"[STRONGPOINT] row %d (strongpoint id %d) sits at world (%s, %s), got (%s, %s)" % [i, want_ids[i], want_x[i], want_y[i], str(m.get("x")), str(m.get("y"))])
			_assert(typeof(m.get("owner")) == TYPE_INT and int(m.get("owner", -9)) == want_owner[i], "[STRONGPOINT] row %d owner int %d, got %s" % [i, want_owner[i], str(m.get("owner"))])
			_assert(typeof(m.get("state")) == TYPE_INT and int(m.get("state", -9)) == want_state[i], "[STRONGPOINT] row %d state int %d, got %s" % [i, want_state[i], str(m.get("state"))])
	# NEG-CONTROL stale list: fails on a build that reads the owner from frame["strongpoints"] instead of the structures rows
	# (GAP 2 (b) / GAP 6: the live owner is the structures row's). The list says 2 -> enemy, 5 -> own; the rows say 2 -> own, 5 -> enemy.
	var stale := _frame(
		[_row(2, LOCAL, 1200.0, 1500.0), _row(5, ENEMY, 2600.0, 2300.0), _row(9, -1, 3400.0, 900.0)],
		[_sp(2, 1200.0, 1500.0, ENEMY, 1), _sp(5, 2600.0, 2300.0, LOCAL, 1), _sp(9, 3400.0, 900.0, -1, 0)])
	mm.call("set_frame", stale, LOCAL, 0.25, Vector2(2000.0, 2000.0))
	rows = _rows(mm)
	_assert(rows.size() == 3, "[STRONGPOINT] stale-list frame still gives three markers, got %d" % rows.size())
	if rows.size() == 3:
		_assert(int(rows[0].get("owner", -9)) == LOCAL, "[STRONGPOINT] NEG-CONTROL stale list: strongpoint 2 list owner enemy, row owner own, marker reads own, got %s" % str(rows[0].get("owner")))
		_assert(int(rows[1].get("owner", -9)) == ENEMY, "[STRONGPOINT] NEG-CONTROL stale list: strongpoint 5 list owner own, row owner enemy, marker reads enemy, got %s" % str(rows[1].get("owner")))
		_assert(int(rows[2].get("owner", -9)) == -1, "[STRONGPOINT] stale-list frame: strongpoint 9 stays neutral (-1), got %s" % str(rows[2].get("owner")))
	# A later frame replaces the markers (the layer holds the last frame, as StructuresLayer.set_frame does).
	mm.call("set_frame", _frame([], []), LOCAL, 0.25, Vector2(2000.0, 2000.0))
	_assert(_rows(mm).is_empty(), "[STRONGPOINT] a frame with no strongpoints and no home base leaves markers() empty")
	mm.queue_free()


# ---------------------------------------------------------------- [HOME] R-235-01 "the side's base of operations"

func _home() -> void:
	var mm := _make_markers("HOME")
	if mm == null:
		return
	# Two own units near the node at (1300, 1100); four enemy units near the node at (5200, 5200); a kind-3 node nearer to the
	# own centroid than either kind-7 node. The centroid of ALL units lies nearer the enemy kind-7 node (a build that ignores
	# the faction picks it); the nearest node of ANY kind is the kind-3 node (a build that ignores the kind picks it).
	var units := [_unit(1, LOCAL, 1000.0, 1000.0), _unit(2, LOCAL, 1100.0, 1050.0),
		_unit(10, ENEMY, 5000.0, 5000.0), _unit(11, ENEMY, 5050.0, 5000.0), _unit(12, ENEMY, 5100.0, 5000.0), _unit(13, ENEMY, 5050.0, 5000.0)]
	var nodes := [{"x": 1300.0, "y": 1100.0, "kind": 7}, {"x": 5200.0, "y": 5200.0, "kind": 7}, {"x": 1050.0, "y": 1020.0, "kind": 3}]
	mm.call("set_frame", _frame([], [], units, nodes), LOCAL, 0.25, Vector2(2000.0, 2000.0))
	var rows := _rows(mm)
	var homes := _of_kind(rows, "home_base")
	_assert(homes.size() == 1, "[HOME] exactly one home_base marker, got %d" % homes.size())
	if homes.size() == 1:
		var h: Dictionary = homes[0]
		_assert(is_equal_approx(float(h.get("x", -1.0)), 1300.0) and is_equal_approx(float(h.get("y", -1.0)), 1100.0),
			"[HOME] home_base is the kind-7 node nearest the own units' centroid (1300, 1100), got (%s, %s)" % [str(h.get("x")), str(h.get("y"))])
		_assert(typeof(h.get("owner")) == TYPE_INT and typeof(h.get("state")) == TYPE_INT, "[HOME] home_base has owner and state ints")
		_assert(typeof(h.get("x")) == TYPE_FLOAT and typeof(h.get("y")) == TYPE_FLOAT, "[HOME] home_base x and y are floats")
	_assert(rows.size() == 1, "[HOME] with no strongpoints the only marker is the home base, got %d" % rows.size())
	# Order: strongpoint rows ascending id, then the home base.
	mm.call("set_frame", _frame([_row(2, LOCAL, 1200.0, 1500.0)], [_sp(2, 1200.0, 1500.0, LOCAL, 1)], units, nodes), LOCAL, 0.25, Vector2(2000.0, 2000.0))
	rows = _rows(mm)
	_assert(rows.size() == 2 and rows[0].get("kind", "") == "strongpoint" and rows[1].get("kind", "") == "home_base",
		"[HOME] order is strongpoint rows then the home base, got %s" % str(rows.map(func(m): return m.get("kind"))))
	# Playing as the other faction reads the other node (local_faction is the argument, not a constant).
	mm.call("set_frame", _frame([], [], units, nodes), ENEMY, 0.25, Vector2(2000.0, 2000.0))
	homes = _of_kind(_rows(mm), "home_base")
	_assert(homes.size() == 1 and is_equal_approx(float(homes[0].get("x", -1.0)), 5200.0) and is_equal_approx(float(homes[0].get("y", -1.0)), 5200.0),
		"[HOME] local faction 1 reads its own units: home_base at the kind-7 node (5200, 5200), got %s" % str(homes))
	mm.queue_free()


# ---------------------------------------------------------------- [PROJECT] R-235-01 "on the map view" (drawn where the map is)

# A marker is drawn at StructuresLayer's projection of its world point: between two (camera, scale) values the painted marker
# moves by exactly the projection delta of the same point (a build that draws at world position, or ignores camera or scale,
# fails). Detector proven on StructuresLayer in [CONTROL].
func _project() -> void:
	var mm_a := _make_markers("PROJECT")
	if mm_a == null:
		return
	var w := Vector2(2600.0, 2300.0)
	var f := _frame([_row(5, ENEMY, w.x, w.y)], [_sp(5, w.x, w.y, ENEMY, 1)])
	var ca := Vector2(2200.0, 2100.0)
	var cb := Vector2(2000.0, 2000.0)
	var a := await _shot(mm_a, func(l): l.call("set_frame", f, LOCAL, 0.25, ca))
	var mm_b := _make_markers("PROJECT")
	var b := await _shot(mm_b, func(l): l.call("set_frame", f, LOCAL, 0.5, cb))
	_assert(a.get_used_rect().size != Vector2i.ZERO and b.get_used_rect().size != Vector2i.ZERO, "[PROJECT] the marker paints pixels in both views")
	var want := _scr(w, 0.5, cb) - _scr(w, 0.25, ca)
	var got := _centre(b) - _centre(a)
	_assert(absf(want.x) >= 100.0 and absf(want.y) >= 50.0, "[PROJECT] fixture sanity: the two views are far apart (%s)" % str(want))
	_assert(absf(got.x - want.x) <= RASTER_TOL_PX and absf(got.y - want.y) <= RASTER_TOL_PX,
		"[PROJECT] marker moves by the StructuresLayer projection delta %s between (scale 0.25, camera %s) and (scale 0.5, camera %s), got %s" % [str(want), str(ca), str(cb), str(got)])


# ---------------------------------------------------------------- [COLOUR] colours from StructuresLayer constants (interface, G7)

func _colour() -> void:
	var w := Vector2(2600.0, 2300.0)
	var sl: GDScript = load(STRUCTURES_PATH)
	for cs in [[LOCAL, "OWN_COLOR"], [ENEMY, "ENEMY_COLOR"]]:
		var own: int = cs[0]
		var mm := _make_markers("COLOUR")
		if mm == null:
			return
		var f := _frame([_row(5, own, w.x, w.y)], [_sp(5, w.x, w.y, own, 1)])
		var img := await _shot(mm, func(l): l.call("set_frame", f, LOCAL, 0.25, Vector2(2200.0, 2100.0)))
		_assert(_has_color(img, sl.get(cs[1])), "[COLOUR] a strongpoint of owner %d is painted in StructuresLayer.%s %s" % [own, cs[1], str(sl.get(cs[1]))])


# ---------------------------------------------------------------- [KINDS] R-235-01 stubs, R-235-04, R-235-03 "no other economy beat"

# No marker of a kind outside the GAP 6 ruling: economic locations, neutral settlements, expansions, forward works and weather
# are stubs and produce none; nothing marks a shipment (R-235-04).
func _kinds() -> void:
	var mm := _make_markers("KINDS")
	if mm == null:
		return
	var units := [_unit(1, LOCAL, 1000.0, 1000.0), _unit(2, ENEMY, 5000.0, 5000.0)]
	var nodes := []
	for k in range(8):
		nodes.append({"x": 1000.0 + 300.0 * k, "y": 1100.0, "kind": k})
	var extra := {
		"lots": [{"id": 1, "x": 1500.0, "y": 1500.0, "stage": 2, "building": 0, "owner": LOCAL}],
		"economy": {"doctrine": 3, "resources": {"a": 10}},
		"weather": [{"x": 3000.0, "y": 3000.0, "kind": 1}],
		"objectives": [{"i": 0, "progress": 10, "done": 0}],
	}
	# Structure rows that are NOT strongpoints (a forward base, a settlement, an expansion): no marker.
	var structures := [_row(2, LOCAL, 1200.0, 1500.0), _row(5, ENEMY, 2600.0, 2300.0), _row(9, -1, 3400.0, 900.0),
		_row(20, LOCAL, 1800.0, 1800.0), _row(21, ENEMY, 4800.0, 4800.0), _row(22, -1, 2500.0, 2500.0)]
	var sps := [_sp(2, 1200.0, 1500.0, LOCAL, 1), _sp(5, 2600.0, 2300.0, ENEMY, 1), _sp(9, 3400.0, 900.0, -1, 0)]
	mm.call("set_frame", _frame(structures, sps, units, nodes, extra), LOCAL, 0.25, Vector2(2000.0, 2000.0))
	var rows := _rows(mm)
	var outside := rows.filter(func(m): return not (m.get("kind", "") in KINDS))
	_assert(outside.is_empty(), "[KINDS] no marker of a kind outside %s (stubs: economic location, settlement, expansion, forward work, weather), got %s" % [str(KINDS), str(outside)])
	_assert(_of_kind(rows, "strongpoint").size() == 3, "[KINDS] exactly the three strongpoint ids are marked (structure rows 20, 21, 22 are not), got %d" % _of_kind(rows, "strongpoint").size())
	_assert(_of_kind(rows, "home_base").size() == 1, "[KINDS] exactly one home_base marker (other node kinds 0..6 are not marked), got %d" % _of_kind(rows, "home_base").size())
	_assert(rows.size() == 4, "[KINDS] four markers in all, got %d" % rows.size())
	mm.queue_free()


# ---------------------------------------------------------------- [DESTROYED] GAP 7: a destroyed strongpoint is drawn as a destroyed mark

func _destroyed() -> void:
	var mm := _make_markers("DESTROYED")
	if mm == null:
		return
	var w := Vector2(2600.0, 2300.0)
	var cam := Vector2(2200.0, 2100.0)
	var held := _frame([_row(5, ENEMY, w.x, w.y)], [_sp(5, w.x, w.y, ENEMY, 1)])
	# the same strongpoint with its structures row gone (frame["strongpoints"] still lists it as held)
	var gone := _frame([], [_sp(5, w.x, w.y, ENEMY, 1)])
	mm.call("set_frame", held, LOCAL, 0.25, cam)
	var rows := _rows(mm)
	_assert(rows.size() == 1 and int(rows[0].get("state", -9)) == 1, "[DESTROYED] held strongpoint reads state 1 before it goes, got %s" % str(rows))
	mm.call("set_frame", gone, LOCAL, 0.25, cam)
	rows = _rows(mm)
	_assert(rows.size() == 1, "[DESTROYED] a strongpoint whose structures row left the frame stays in markers(), got %d rows" % rows.size())
	if rows.size() == 1:
		_assert(int(rows[0].get("state", -9)) == 2, "[DESTROYED] and reads state 2 (rubble), got %s" % str(rows[0].get("state")))
		_assert(rows[0].get("kind", "") == "strongpoint" and is_equal_approx(float(rows[0].get("x", -1.0)), w.x) and is_equal_approx(float(rows[0].get("y", -1.0)), w.y),
			"[DESTROYED] still a strongpoint marker at its world point, got %s" % str(rows[0]))
	mm.queue_free()
	# Drawn: the destroyed mark paints pixels at the projected point and looks different from the held mark.
	var held_img := await _shot(_make_markers("DESTROYED"), func(l): l.call("set_frame", held, LOCAL, 0.25, cam))
	var gone_img := await _shot(_make_markers("DESTROYED"), func(l): l.call("set_frame", gone, LOCAL, 0.25, cam))
	_assert(gone_img.get_used_rect().size != Vector2i.ZERO, "[DESTROYED] the destroyed mark is still drawn (not erased)")
	_assert(held_img.get_data() != gone_img.get_data(), "[DESTROYED] the destroyed mark looks different from the held mark (a build that draws state 2 like state 1 fails)")

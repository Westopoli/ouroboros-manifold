extends SceneTree

# Client readability piece (Architect, 2026-10-07). E-16 S-232/S-234
# (docs/bible/epics/E-16-client-camera-hud-and-world-view.md); R-104-10 (in-world chrome: layer
# ring, selection ring); R-232-03 (emit mark, not tested: needs a sim field); R-234-01 (one world,
# continuous detail). RED because res://scenes/tactical_c/unit_visuals.gd and map_layer.gd do not
# exist and tactical_view.gd has no UnitVisuals/MapLayer child (it draws one blue square per unit).
#
# Interface this test requires (test's choice; the builder matches it). Screen mapping is the
# view's _to_screen: sx = (wx - camera.x) * scale + 960, sy = (wy - camera.y) * scale + 540.
#   unit_visuals.gd (extends Node2D; child of the view named "UnitVisuals"):
#     set_frame(frame: Dictionary, local_faction: int, world_scale: float, camera: Vector2) -> void
#         one child node per unit the local faction can see (own units + visible enemies)
#     unit_node(id: int) -> Node2D             null when no node (hidden enemy)
#     unit_polygon(id: int) -> PackedVector2Array   the unit-type flat shape, local points
#     unit_tint(id: int) -> Color               layer tint (differs per layer; same type same shape)
#     set_selected(ids: Array) -> void          adds one ring node per selected id, removes the rest
#     selection_ring(id: int) -> Node2D         null when not selected
#     set_move_marker(world: Vector2) -> void   marker at the goal, world coords
#     move_marker() -> Node2D                   null before any order; .position is screen px
#   map_layer.gd (extends Node2D; child of the view named "MapLayer"):
#     const SIGHT_RADIUS_DRAFT: float           draft sight radius in world units (marked draft)
#     const FOG_DIM_ALPHA: float                0 < a < 1, the dim outside the sight discs
#     set_frame(frame: Dictionary, mission: Dictionary, local_faction: int, world_scale: float, camera: Vector2) -> void
#         mission is the mission frame (objectives[].node indexes frame.map.nodes, .radius in wu)
#     objective_rings() -> Array                [{center: Vector2 (screen), radius: float (screen px)}]
#     cover_polygons() -> Array                 one PackedVector2Array (screen px) per map.cover entry
#     obstacle_polygons() -> Array              one PackedVector2Array (screen px) per map.obstacles entry
#     fog_node() -> Node2D                      null when there is no map
#     fog_discs() -> Array                      [{center: Vector2 (screen), radius: float (screen px)}],
#                                               one per own unit; radius = frame["sight_radius"] if the
#                                               frame has it else SIGHT_RADIUS_DRAFT, times world_scale
#   A frame with no "map" (space era): all of the above empty or null.

const UNITS_PATH := "res://scenes/tactical_c/unit_visuals.gd"
const MAP_PATH := "res://scenes/tactical_c/map_layer.gd"
const VIEW_PATH := "res://scenes/tactical_c/tactical_view.tscn"
const SCALE := 0.25
const CAM := Vector2(2000, 2000)

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	await _run_tests()
	print("\n=== Tactical Readability Test Results ===")
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


func _scr(w: Vector2) -> Vector2:
	return (w - CAM) * SCALE + Vector2(960, 540)


# Own units 1 (type 0, layer 1) and 2 (type 2, layer 3), a visible enemy 3, a hidden enemy 4.
func _frame(with_map: bool) -> Dictionary:
	var f := {"type": "tactical", "tick": 5, "player_faction": 0,
		"units": [
			{"id": 1, "faction": 0, "type": 0, "tier": 1, "x": 1500.0, "y": 1500.0, "hp": 100.0, "layer": 1, "facing": 0.0, "target": -1, "state": 0},
			{"id": 2, "faction": 0, "type": 2, "tier": 1, "x": 1800.0, "y": 1600.0, "hp": 100.0, "layer": 3, "facing": 0.0, "target": -1, "state": 0},
			{"id": 3, "faction": 1, "type": 1, "tier": 1, "x": 2400.0, "y": 2400.0, "hp": 100.0, "layer": 1, "facing": 0.0, "target": -1, "state": 0},
			{"id": 4, "faction": 1, "type": 1, "tier": 1, "x": 3000.0, "y": 3000.0, "hp": 100.0, "layer": 1, "facing": 0.0, "target": -1, "state": 0}],
		"visible": {"0": [1, 2, 3], "1": [3, 4]}}
	if with_map:
		f["map"] = {"canvas": 4000.0,
			"nodes": [{"i": 0, "kind": 0, "x": 1000.0, "y": 1000.0}],
			"cover": [{"x": 2000.0, "y": 2000.0, "r": 150.0, "h": 30.0}, {"x": 2600.0, "y": 1200.0, "r": 120.0, "h": 20.0}],
			"obstacles": [{"x": 2500.0, "y": 1500.0, "r": 100.0}]}
	return f


func _mission() -> Dictionary:
	return {"type": "mission", "objectives": [{"i": 0, "kind": 1, "node": 0, "primary": true, "radius": 300.0, "progress": 0.0}]}


func _run_tests() -> void:
	var us = load(UNITS_PATH)
	_assert(us != null, "unit_visuals: " + UNITS_PATH + " does not exist (S-234 R-104-10: units read by type and layer, not as one blue square)")
	if us != null:
		var uv: Node2D = us.new()
		get_root().add_child(uv)
		for m in ["set_frame", "unit_node", "unit_polygon", "unit_tint", "set_selected", "selection_ring", "set_move_marker", "move_marker"]:
			_assert(uv.has_method(m), "unit_visuals lacks method " + m)
		if uv.has_method("set_frame"):
			uv.call("set_frame", _frame(true), 0, SCALE, CAM)
			# R-104-10 / S-234: a shape per unit type
			_assert(uv.call("unit_node", 1) != null and uv.call("unit_node", 2) != null and uv.call("unit_node", 3) != null,
				"unit_visuals: own units and the visible enemy each get a node")
			_assert(uv.call("unit_node", 4) == null, "unit_visuals control: a hidden enemy gets no node (R-089-04)")
			var p0: PackedVector2Array = uv.call("unit_polygon", 1)
			var p2: PackedVector2Array = uv.call("unit_polygon", 2)
			var p1: PackedVector2Array = uv.call("unit_polygon", 3)
			_assert(p0.size() >= 3 and p2.size() >= 3 and p1.size() >= 3, "unit_visuals: every type shape is a polygon (>= 3 points)")
			_assert(p0.size() != p2.size() and p0.size() != p1.size() and p2.size() != p1.size(),
				"unit_visuals: types 0, 2 and 1 have distinct shapes (point counts differ); got %d, %d, %d" % [p0.size(), p2.size(), p1.size()])
			# layer tint (R-104-10: layer-color ring/tint)
			_assert(uv.call("unit_tint", 1) != uv.call("unit_tint", 2),
				"unit_visuals: layer 1 and layer 3 units carry different tints")
			var n1: Node2D = uv.call("unit_node", 1)
			if n1 != null:
				_assert(n1.position.distance_to(_scr(Vector2(1500, 1500))) < 0.5,
					"unit_visuals: the node sits at the unit's screen position; got " + str(n1.position))
			# selection ring (R-104-10)
			_assert(uv.call("selection_ring", 1) == null, "unit_visuals control: no ring before selecting")
			uv.call("set_selected", [1])
			_assert(uv.call("selection_ring", 1) != null, "unit_visuals: selecting unit 1 adds a ring node (R-104-10)")
			_assert(uv.call("selection_ring", 2) == null, "unit_visuals control: unselected unit 2 has no ring")
			uv.call("set_selected", [])
			_assert(uv.call("selection_ring", 1) == null, "unit_visuals: clearing the selection removes the ring")
			# move marker
			_assert(uv.call("move_marker") == null, "unit_visuals control: no move marker before an order")
			uv.call("set_move_marker", Vector2(2200, 1800))
			var mk: Node2D = uv.call("move_marker")
			_assert(mk != null and mk.position.distance_to(_scr(Vector2(2200, 1800))) < 0.5,
				"unit_visuals: a move order adds a marker at the goal's screen position; got " + str(mk.position if mk != null else null))
		uv.free()

	var ms = load(MAP_PATH)
	_assert(ms != null, "map_layer: " + MAP_PATH + " does not exist (S-234: the objective, cover and what is seen are drawn)")
	if ms != null:
		var ml: Node2D = ms.new()
		get_root().add_child(ml)
		for m in ["set_frame", "objective_rings", "cover_polygons", "obstacle_polygons", "fog_node", "fog_discs"]:
			_assert(ml.has_method(m), "map_layer lacks method " + m)
		_assert("SIGHT_RADIUS_DRAFT" in ms and "FOG_DIM_ALPHA" in ms, "map_layer lacks SIGHT_RADIUS_DRAFT / FOG_DIM_ALPHA constants")
		if ml.has_method("set_frame"):
			ml.call("set_frame", _frame(true), _mission(), 0, SCALE, CAM)
			var rings: Array = ml.call("objective_rings")
			_assert(rings.size() == 1, "map_layer: one objective ring for one objective; got %d" % rings.size())
			if rings.size() == 1:
				_assert(rings[0]["center"].distance_to(_scr(Vector2(1000, 1000))) < 0.5,
					"map_layer: the ring is at the node's screen position; got " + str(rings[0]["center"]))
				_assert(absf(rings[0]["radius"] - 300.0 * SCALE) < 0.5,
					"map_layer: the ring radius is 300 wu scaled to %f px; got %f" % [300.0 * SCALE, rings[0]["radius"]])
			var cov: Array = ml.call("cover_polygons")
			_assert(cov.size() == 2, "map_layer: two cover polygons; got %d" % cov.size())
			_assert(ml.call("obstacle_polygons").size() == 1, "map_layer: one obstacle polygon")
			if cov.size() == 2:
				var c: Vector2 = Vector2.ZERO
				for p in cov[0]:
					c += p
				c /= float(cov[0].size())
				_assert(cov[0].size() >= 3 and c.distance_to(_scr(Vector2(2000, 2000))) < 1.0,
					"map_layer: a cover polygon is centred on its disc's screen position; got " + str(c))
			# fog (what is seen)
			_assert(ml.call("fog_node") != null, "map_layer: a fog node exists when the frame has a map")
			var discs: Array = ml.call("fog_discs")
			_assert(discs.size() == 2, "map_layer: one sight disc per own unit (2); the enemy is not one; got %d" % discs.size())
			if discs.size() == 2 and "SIGHT_RADIUS_DRAFT" in ms:
				var want: float = float(ms.get("SIGHT_RADIUS_DRAFT")) * SCALE
				_assert(want > 0.0 and absf(discs[0]["radius"] - want) < 0.5,
					"map_layer: with no sight_radius in the frame the draft constant is used (%f px); got %f" % [want, discs[0]["radius"]])
				_assert(discs[0]["center"].distance_to(_scr(Vector2(1500, 1500))) < 0.5, "map_layer: the sight disc is centred on its unit")
			if "FOG_DIM_ALPHA" in ms:
				var a: float = float(ms.get("FOG_DIM_ALPHA"))
				_assert(a > 0.0 and a < 1.0, "map_layer: the fog dim is partial (0 < alpha < 1); got %f" % a)
			# the frame's own radius wins
			var f2 := _frame(true)
			f2["sight_radius"] = 500.0
			ml.call("set_frame", f2, _mission(), 0, SCALE, CAM)
			var d2: Array = ml.call("fog_discs")
			_assert(d2.size() == 2 and absf(d2[0]["radius"] - 500.0 * SCALE) < 0.5,
				"map_layer: a sight_radius in the frame is used over the draft constant")
			# control: space era, no map, draws nothing extra
			ml.call("set_frame", _frame(false), {}, 0, SCALE, CAM)
			_assert(ml.call("objective_rings").is_empty() and ml.call("cover_polygons").is_empty()
				and ml.call("obstacle_polygons").is_empty() and ml.call("fog_discs").is_empty() and ml.call("fog_node") == null,
				"map_layer control: a frame with no map draws no ring, cover, obstacle or fog")
		ml.free()

	# wiring: the view instantiates both and passes frames (reachable from the view, not only from tests)
	var packed = load(VIEW_PATH)
	if packed != null:
		var v: Node = (packed as PackedScene).instantiate()
		get_root().add_child(v)
		await process_frame
		v.set_process(false)
		v.call("load_frame", _frame(true))
		var uvn := v.get_node_or_null("UnitVisuals")
		var mln := v.get_node_or_null("MapLayer")
		_assert(uvn != null and uvn.get_script() != null and uvn.get_script().resource_path == UNITS_PATH,
			"tactical_view: has a child UnitVisuals running unit_visuals.gd")
		_assert(mln != null and mln.get_script() != null and mln.get_script().resource_path == MAP_PATH,
			"tactical_view: has a child MapLayer running map_layer.gd")
		if uvn != null and uvn.has_method("unit_node"):
			_assert(uvn.call("unit_node", 1) != null, "tactical_view: load_frame passes the frame to UnitVisuals")
			v.call("qa_set_selected", [1])
			_assert(uvn.call("selection_ring", 1) != null, "tactical_view: selecting a unit shows the ring")
		if mln != null and mln.has_method("fog_discs"):
			_assert(mln.call("fog_discs").size() == 2, "tactical_view: load_frame passes the frame to MapLayer (2 own units)")
		v.queue_free()

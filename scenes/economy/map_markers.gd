class_name MapMarkers
extends Node2D
# E1n (S-235, R-235-01): the map marks the strongpoints and the side's base of operations (home base). Markers are drawn
# in screen space by the projection StructuresLayer._sync uses; markers() lists them in world wu.
# REAL: kinds "strongpoint" (rows of frame["strongpoints"], owner from the joined structures row, GAP 2 (b)) and "home_base"
#   (the kind-7 map node nearest the centroid of the local faction's units, tactical_view.gd SPAWN_NODE_KIND / _home_box).
# STUB (GAP 6): economic locations, neutral settlements, expansions, forward works and weather are neither drawn nor listed;
#   no sim source marks them here. Towns are the places lane's (P6) layer.
# See also: the places lane spec (P6), the E-15 weather epic, docs/northstar/plans/2026-10-07-visible-game-spec.md (S-235).

const SL := preload("res://scenes/tactical_c/structures_layer.gd")
const SPAWN_NODE_KIND := 7
const STATE_HELD := 1
const STATE_RUBBLE := 2
# DRAFT-e1n-marker (GAP 7 (a), Architect 2026-10-14): the look, taken as written, listed in one ledger row. A strongpoint is a
# diamond outline around the structure ring, a destroyed one (state 2, rubble, R-218-05) a cross, the home base a filled
# square; colours are StructuresLayer's (own, enemy, neutral).
const MARK_RADIUS_PX := 36.0
const MARK_WIDTH := 3.0

var _local := 0
var _scale := 1.0
var _camera := Vector2.ZERO
var _rows: Array = []
var _home: Dictionary = {}


func _ready() -> void:
	name = "MapMarkers"


func set_frame(frame: Dictionary, local_faction: int, world_scale: float, camera: Vector2) -> void:
	_local = local_faction
	_scale = world_scale
	_camera = camera
	_rows = []
	var owner_of := {}
	for s in frame.get("structures", []):
		owner_of[int(s["id"])] = int(s.get("owner", -1))
	var sps: Array = frame.get("strongpoints", []).duplicate()
	sps.sort_custom(func(a, b): return int(a["id"]) < int(b["id"]))
	for sp in sps:
		var id := int(sp["id"])
		var held := owner_of.has(id)
		_rows.append({"kind": "strongpoint", "x": float(sp["x"]), "y": float(sp["y"]),
			"owner": int(owner_of[id]) if held else int(sp.get("owner", -1)),
			"state": int(sp.get("state", 0)) if held else STATE_RUBBLE})
	var home := _home_base(frame)
	if not home.is_empty():
		_rows.append(home)
	queue_redraw()


func markers() -> Array:
	return _rows.duplicate(true)


func _home_base(frame: Dictionary) -> Dictionary:
	# Remembered from the first frame with own units (per local faction) so the marker does not follow the army; pinned by tests/test_vg_e_e1w.gd [HOME].
	if not _home.is_empty() and int(_home["owner"]) == _local:
		return _home
	var sum := Vector2.ZERO
	var count := 0
	for u in frame.get("units", []):
		if int(u.get("faction", -1)) == _local:
			sum += Vector2(float(u.get("x", 0.0)), float(u.get("y", 0.0)))
			count += 1
	if count == 0:
		return {}
	var centroid := sum / float(count)
	var best := INF
	var spawn := Vector2.ZERO
	for n in frame.get("map", {}).get("nodes", []):
		if int(n.get("kind", -1)) == SPAWN_NODE_KIND:
			var np := Vector2(float(n.get("x", 0.0)), float(n.get("y", 0.0)))
			var d := np.distance_squared_to(centroid)
			if d < best:
				best = d
				spawn = np
	if best == INF:
		return {}
	_home = {"kind": "home_base", "x": spawn.x, "y": spawn.y, "owner": _local, "state": STATE_HELD}
	return _home


func _colour(owner: int) -> Color:
	if owner < 0:
		return SL.NEUTRAL_COLOR
	return SL.OWN_COLOR if owner == _local else SL.ENEMY_COLOR


func _draw() -> void:
	var r := MARK_RADIUS_PX
	for m in _rows:
		var p := (Vector2(float(m["x"]), float(m["y"])) - _camera) * _scale + SL.SCREEN_CENTER
		var col := _colour(int(m["owner"]))
		if m["kind"] == "home_base":
			draw_rect(Rect2(p - Vector2(r, r) * 0.5, Vector2(r, r)), col)
		elif int(m["state"]) == STATE_RUBBLE:
			draw_line(p + Vector2(-r, -r) * 0.7, p + Vector2(r, r) * 0.7, col, MARK_WIDTH)
			draw_line(p + Vector2(-r, r) * 0.7, p + Vector2(r, -r) * 0.7, col, MARK_WIDTH)
		else:
			draw_polyline(PackedVector2Array([p + Vector2(0, -r), p + Vector2(r, 0), p + Vector2(0, r), p + Vector2(-r, 0), p + Vector2(0, -r)]), col, MARK_WIDTH)

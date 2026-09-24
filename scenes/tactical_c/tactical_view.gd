extends Node2D

# Piece C5: minimal tactical view over a C transport v1 "tactical" snapshot
# (docs/architecture.md "C transport v1"). Fresh scene, no legacy code. See
# docs/northstar/plans/push/specs/C5.md and
# docs/northstar/proving_ground/evidence/push_2026-09-22/c5_t2g_tests_note.md
# for the contract this implements; tests/test_tactical_view.gd is the
# literal, authoritative test of it.

const SCREEN_W := 1920.0
const SCREEN_H := 1080.0
const WORLD_SCALE := 0.25
const UNIT_SIZE := 24.0
const LOCAL_FACTION := 0

var _frame: Dictionary = {}
var _canvas: float = 0.0
var _camera := Vector2.ZERO
var _camera_initialized := false
var _camera_unbounded := false
var _facing_fixed := false
var _frozen_facing: Dictionary = {}
var _selected: Array = []
var _unit_visuals: Dictionary = {}


func _ready() -> void:
	# C8 flow spine: SceneRouter._swap_scene never passes data into a
	# scene routed to via go_to() (no setup() call on this path), so this
	# view self-loads the first live tactical frame on a fresh route-in. A
	# failed live load leaves the view empty and logs the reason; it never
	# falls back to a fixture (C5-2).
	var bridge = load("res://autoload/c_bridge.gd").new()
	if bridge.load_tactical_live(bridge.live_seed(), bridge.DEFAULT_N_REGIONS, bridge.DEFAULT_FEATURES):
		load_frame(bridge.tactical_frame())
	else:
		push_error("tactical_view: live tactical frame failed: %s" % bridge.last_error())
	var end_mission_btn := get_node_or_null("CanvasLayer/EndMission")
	if end_mission_btn != null:
		end_mission_btn.pressed.connect(func():
			SceneRouter.go_to("debrief")
		)


func load_frame(frame: Dictionary) -> void:
	_frame = frame
	_canvas = float(frame.get("map", {}).get("canvas", 0.0))
	if not _camera_initialized and _canvas > 0.0:
		_camera = Vector2(_canvas * 0.5, _canvas * 0.5)
		_camera_initialized = true
	if _facing_fixed:
		for u in frame.get("units", []):
			var id := int(u.get("id"))
			if not _frozen_facing.has(id):
				_frozen_facing[id] = float(u.get("facing", 0.0))
	_prune_selected()
	_redraw()


func qa_state() -> Dictionary:
	var visible_ids := _visible_ids()
	var units := {}
	var units_px := {}
	for u in _frame.get("units", []):
		var id := int(u.get("id"))
		var facing := float(u.get("facing", 0.0))
		if _facing_fixed and _frozen_facing.has(id):
			facing = float(_frozen_facing[id])
		units[str(id)] = {
			"faction": int(u.get("faction", 0)),
			"type": int(u.get("type", 0)),
			"tier": int(u.get("tier", 0)),
			"hp": float(u.get("hp", 0.0)),
			"layer": int(u.get("layer", 0)),
			"facing": facing,
			"state": int(u.get("state", 0)),
			"x": float(u.get("x", 0.0)),
			"y": float(u.get("y", 0.0)),
		}
		if visible_ids.has(id):
			units_px[str(id)] = _to_screen(float(u.get("x", 0.0)), float(u.get("y", 0.0)))
	return {
		"tick": int(_frame.get("tick", 0)),
		"canvas": _canvas,
		"units": units,
		"units_px": units_px,
		"local_faction": LOCAL_FACTION,
		"selected": _selected.duplicate(),
		"camera": {"x": _camera.x, "y": _camera.y},
	}


func qa_plant(id: String) -> bool:
	match id:
		"facing-fixed":
			if not _facing_fixed:
				_facing_fixed = true
				for u in _frame.get("units", []):
					var uid := int(u.get("id"))
					if not _frozen_facing.has(uid):
						_frozen_facing[uid] = float(u.get("facing", 0.0))
			return true
		"camera-unbounded":
			_camera_unbounded = true
			return true
		"select-all-exists":
			# R-105-04: no select-all command may ever exist. Permanent
			# negative, never wired to a fault site -- always false, even
			# when "planted".
			return false
		_:
			return false


func issue_command(cmd: Dictionary) -> Dictionary:
	var kind := str(cmd.get("kind", ""))
	var unit_ids: Array = cmd.get("unit_ids", []).duplicate()
	match kind:
		"move":
			return {
				"type": "cmd",
				"name": "command_move",
				"unit_ids": unit_ids,
				"x": float(cmd.get("x", 0.0)),
				"y": float(cmd.get("y", 0.0)),
			}
		"attack_move":
			return {
				"type": "cmd",
				"name": "command_attack_move",
				"unit_ids": unit_ids,
				"x": float(cmd.get("x", 0.0)),
				"y": float(cmd.get("y", 0.0)),
			}
		"attack_target":
			return {
				"type": "cmd",
				"name": "command_attack_target",
				"unit_ids": unit_ids,
				"target": int(cmd.get("target", -1)),
			}
		_:
			return {"type": "cmd", "name": "", "unit_ids": unit_ids}


func qa_box_select(x0: float, y0: float, x1: float, y1: float) -> Array:
	var rx0: float = min(x0, x1)
	var ry0: float = min(y0, y1)
	var rx1: float = max(x0, x1)
	var ry1: float = max(y0, y1)
	var visible_ids := _visible_ids()
	var out: Array = []
	for u in _frame.get("units", []):
		var id := int(u.get("id"))
		if not visible_ids.has(id):
			continue
		var px: Array = _to_screen(float(u.get("x", 0.0)), float(u.get("y", 0.0)))
		var sx: float = px[0]
		var sy: float = px[1]
		if sx >= rx0 and sx <= rx1 and sy >= ry0 and sy <= ry1:
			out.append(id)
	_selected = out.duplicate()
	return out


func qa_pan(x: float, y: float) -> void:
	if _camera_unbounded:
		_camera = Vector2(x, y)
	else:
		_camera = Vector2(clampf(x, 0.0, _canvas), clampf(y, 0.0, _canvas))
	_redraw()


func _visible_ids() -> Dictionary:
	var out := {}
	for v in _frame.get("visible", {}).get(str(LOCAL_FACTION), []):
		out[int(v)] = true
	return out


func _to_screen(wx: float, wy: float) -> Array:
	var sx := (wx - _camera.x) * WORLD_SCALE + SCREEN_W * 0.5
	var sy := (wy - _camera.y) * WORLD_SCALE + SCREEN_H * 0.5
	return [sx, sy]


func _prune_selected() -> void:
	var live_ids := {}
	for u in _frame.get("units", []):
		live_ids[int(u.get("id"))] = true
	var kept: Array = []
	for s in _selected:
		if live_ids.has(int(s)):
			kept.append(int(s))
	_selected = kept


func _redraw() -> void:
	if not is_inside_tree():
		return
	var visible_ids := _visible_ids()
	var seen := {}
	for u in _frame.get("units", []):
		var id := int(u.get("id"))
		if not visible_ids.has(id):
			continue
		seen[id] = true
		var px: Array = _to_screen(float(u.get("x", 0.0)), float(u.get("y", 0.0)))
		var poly: Polygon2D
		if _unit_visuals.has(id):
			poly = _unit_visuals[id]
		else:
			poly = _make_unit_visual(int(u.get("faction", 0)))
			add_child(poly)
			_unit_visuals[id] = poly
		poly.position = Vector2(float(px[0]), float(px[1]))
	for id in _unit_visuals.keys().duplicate():
		if not seen.has(id):
			_unit_visuals[id].queue_free()
			_unit_visuals.erase(id)


func _make_unit_visual(faction: int) -> Polygon2D:
	var poly := Polygon2D.new()
	var h := UNIT_SIZE * 0.5
	poly.polygon = PackedVector2Array([
		Vector2(-h, -h), Vector2(h, -h), Vector2(h, h), Vector2(-h, h),
	])
	poly.color = Color(0.2, 0.6, 1.0) if faction == LOCAL_FACTION else Color(1.0, 0.3, 0.3)
	return poly

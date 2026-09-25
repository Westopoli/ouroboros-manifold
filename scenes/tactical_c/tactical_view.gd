extends Node2D

const SimSession := preload("res://autoload/sim_session.gd")

# Piece C5: minimal tactical view over a C transport v1 "tactical" snapshot
# (docs/architecture.md "C transport v1"). Fresh scene, no legacy code. See
# docs/northstar/plans/push/specs/C5.md and
# docs/northstar/proving_ground/evidence/push_2026-09-22/c5_t2g_tests_note.md
# for the contract this implements; tests/test_tactical_view.gd is the
# literal, authoritative test of it.

const SCREEN_W := 1920.0
const SCREEN_H := 1080.0
# Fallback scale for a zero-canvas frame; replaced dynamically once canvas > 0.
const WORLD_SCALE := 0.25
const UNIT_SIZE := 24.0
const LOCAL_FACTION := 0

var _frame: Dictionary = {}
var _canvas: float = 0.0
var _world_scale: float = WORLD_SCALE
var _camera := Vector2.ZERO
var _camera_initialized := false
var _camera_canvas: float = 0.0
var _camera_unbounded := false
var _facing_fixed := false
var _frozen_facing: Dictionary = {}
var _selected: Array = []
var _unit_visuals: Dictionary = {}
var _display_px: Dictionary = {}
var _last_command: Dictionary = {}

# Plants: stuck freezes drawn positions after first load_frame; rubber-band snaps
# back to the position from two loads ago on every third load (N%3==0).
# move-order-dropped: sends one command per unit instead of one group command.
var _stuck := false
var _rubber_band := false
var _rubber_band_count := 0
var _rubber_band_prev_px: Dictionary = {}
var _rubber_band_prev_prev_px: Dictionary = {}
var _move_order_dropped := false

# C5-4 counters: updated by send_command on every player order.
var _commands_sent_last_order: int = 0
var _units_in_last_command: int = 0

# Desktop input: left-drag start position; -1 means no drag in progress.
var _drag_start := Vector2(-1.0, -1.0)


func _ready() -> void:
	# C8 flow spine: SceneRouter._swap_scene never passes data into a
	# scene routed to via go_to() (no setup() call on this path), so this
	# view self-loads the first live tactical frame on a fresh route-in. A
	# failed live load leaves the view empty and logs the reason; it never
	# falls back to a fixture (C5-2).
	var bridge = SimSession.bridge()
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
	if _canvas > 0.0:
		_world_scale = SCREEN_H / _canvas
	if _canvas > 0.0 and (not _camera_initialized or _canvas != _camera_canvas):
		_camera = Vector2(_canvas * 0.5, _canvas * 0.5)
		_camera_initialized = true
		_camera_canvas = _canvas
	if _facing_fixed:
		for u in frame.get("units", []):
			var id := int(u.get("id"))
			if not _frozen_facing.has(id):
				_frozen_facing[id] = float(u.get("facing", 0.0))
	_prune_selected()
	_update_display_px()
	_redraw()


func qa_state() -> Dictionary:
	var units := {}
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
	return {
		"scene": "tactical_view",
		"tick": int(_frame.get("tick", 0)),
		"plants": ["facing-fixed", "camera-unbounded", "move-order-dropped"],
		"canvas": _canvas,
		"scale": _world_scale,
		"unit_count": _frame.get("units", []).size(),
		"units": units,
		"units_px": _display_px.duplicate(),
		"local_faction": LOCAL_FACTION,
		"selected": _selected.duplicate(),
		"camera": {"x": _camera.x, "y": _camera.y},
		"last_command": _last_command.duplicate(),
		"commands_sent_last_order": _commands_sent_last_order,
		"units_in_last_command": _units_in_last_command,
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
		"move-order-dropped":
			# Plant: send_command issues one pipe command per unit instead of one
			# group command. Detector: commands_sent_last_order != 1 under this plant.
			_move_order_dropped = true
			return true
		"stuck":
			# Freeze drawn positions at whatever they are when the next
			# load_frame computes them.
			_stuck = true
			_display_px = {}
			return true
		"rubber-band":
			# Every third load_frame snaps units back to where they were
			# two loads ago.
			_rubber_band = true
			_rubber_band_count = 0
			_rubber_band_prev_px = {}
			_rubber_band_prev_prev_px = {}
			_display_px = {}
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


# Sends the command over the shared session; returns true if the kind is known
# and the command was fired, false if the kind is unknown (command dropped).
# Updates qa_state().last_command, commands_sent_last_order, units_in_last_command.
# With the move-order-dropped plant active, sends one pipe command per selected
# unit instead of one group command (detector fault site).
func send_command(cmd: Dictionary) -> bool:
	var kind := str(cmd.get("kind", ""))
	var unit_ids: Array = cmd.get("unit_ids", []).duplicate()
	var bridge = SimSession.bridge()
	var ok: bool
	if _move_order_dropped:
		# Plant: one pipe command per unit (trips the one-command invariant).
		_commands_sent_last_order = unit_ids.size()
		ok = false
		for uid in unit_ids:
			var r: bool = bridge.send_unit_command({
				"kind": kind,
				"unit_ids": [uid],
				"x": float(cmd.get("x", 0.0)),
				"y": float(cmd.get("y", 0.0)),
				"target": int(cmd.get("target", -1)),
			})
			ok = ok or r
	else:
		ok = bridge.send_unit_command({
			"kind": kind,
			"unit_ids": unit_ids,
			"x": float(cmd.get("x", 0.0)),
			"y": float(cmd.get("y", 0.0)),
			"target": int(cmd.get("target", -1)),
		})
		_commands_sent_last_order = 1
	_units_in_last_command = unit_ids.size()
	_last_command = {"ok": ok, "kind": kind, "units": unit_ids.size()}
	return ok


# Advances the live mission by n tactical ticks and reloads the view.
func qa_step(n: int) -> void:
	var bridge = SimSession.bridge()
	if bridge.tactical_step_n(n):
		load_frame(bridge.tactical_frame())


func qa_box_select(x0: float, y0: float, x1: float, y1: float) -> Array:
	var rx0: float = min(x0, x1)
	var ry0: float = min(y0, y1)
	var rx1: float = max(x0, x1)
	var ry1: float = max(y0, y1)
	var out: Array = []
	for id_str in _display_px:
		var p: Array = _display_px[id_str]
		var sx: float = p[0]
		var sy: float = p[1]
		if sx >= rx0 and sx <= rx1 and sy >= ry0 and sy <= ry1:
			out.append(int(id_str))
	_selected = out.duplicate()
	return out


func qa_pan(x: float, y: float) -> void:
	if _camera_unbounded:
		_camera = Vector2(x, y)
	else:
		_camera = Vector2(clampf(x, 0.0, _canvas), clampf(y, 0.0, _canvas))
	_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_LEFT:
			if mb.pressed:
				_drag_start = mb.position
			else:
				if _drag_start.x >= 0.0:
					qa_box_select(_drag_start.x, _drag_start.y, mb.position.x, mb.position.y)
					_drag_start = Vector2(-1.0, -1.0)
		elif mb.button_index == MOUSE_BUTTON_RIGHT and mb.pressed:
			var wx: float = (mb.position.x - SCREEN_W * 0.5) / _world_scale + _camera.x
			var wy: float = (mb.position.y - SCREEN_H * 0.5) / _world_scale + _camera.y
			send_command({"kind": "move", "unit_ids": _selected.duplicate(), "x": wx, "y": wy})


func _visible_ids() -> Dictionary:
	var out := {}
	for v in _frame.get("visible", {}).get(str(LOCAL_FACTION), []):
		out[int(v)] = true
	return out


func _to_screen(wx: float, wy: float) -> Array:
	var sx := (wx - _camera.x) * _world_scale + SCREEN_W * 0.5
	var sy := (wy - _camera.y) * _world_scale + SCREEN_H * 0.5
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


func _update_display_px() -> void:
	var visible_ids := _visible_ids()
	var current_px: Dictionary = {}
	for u in _frame.get("units", []):
		var id := int(u.get("id"))
		if visible_ids.has(id):
			current_px[str(id)] = _to_screen(float(u.get("x", 0.0)), float(u.get("y", 0.0)))

	if _stuck:
		# Freeze: populate once on first load_frame after planting; never update after.
		if _display_px.is_empty():
			_display_px = current_px
	elif _rubber_band:
		_rubber_band_count += 1
		if _rubber_band_count % 3 == 0:
			# Snap back to positions from two loads ago.
			_display_px = _rubber_band_prev_prev_px.duplicate()
		else:
			_display_px = current_px
		_rubber_band_prev_prev_px = _rubber_band_prev_px.duplicate()
		_rubber_band_prev_px = current_px.duplicate()
	else:
		_display_px = current_px


func _redraw() -> void:
	if not is_inside_tree():
		return
	# Build a faction lookup for color selection.
	var faction_of: Dictionary = {}
	for u in _frame.get("units", []):
		faction_of[str(int(u.get("id")))] = int(u.get("faction", 0))

	var seen := {}
	for id_str in _display_px:
		var id := int(id_str)
		seen[id] = true
		var px: Array = _display_px[id_str]
		var faction := int(faction_of.get(id_str, 0))
		var poly: Polygon2D
		if _unit_visuals.has(id):
			poly = _unit_visuals[id]
		else:
			poly = _make_unit_visual(faction)
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

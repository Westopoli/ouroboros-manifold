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

# A6a camera. Q-103-04 leaves the bible without numbers: these are named
# placeholders. Zoom 1.0 fits the whole canvas to the screen height.
const ZOOM_MIN := 1.0
const ZOOM_MAX := 4.0
const ZOOM_STEP := 1.25
const PAN_SPEED_PX := 600.0
const EDGE_MARGIN_PX := 4.0

# Real-time stepping (B9-N, 2026-09-28 QA-run wiring brief): before this, a
# deployed mission only ever advanced through the qa_step() QA hook, so real
# play froze at tick 0. _process() accumulates real time and requests whole
# tactical ticks at the sim's own rate: 20 base ticks/sec at or below 1,000
# live units (csrc/om_constants.h OM_TACTICAL_TICK_RATE; docs/bible/epics/
# E-13-tactical-combat.md R-099-02). Above 1,000 live units each
# om_tactical_step call spans OM_TACTICAL_HIGH_LOAD_PERIOD (2, csrc/unit.c)
# base ticks instead of 1 (R-099-03), so holding the same 20 base-ticks/sec
# in real time needs only 10 tactical_step_n calls/sec -- this is the "tick
# rate drops from 20 to 10" R-099-03 describes; base_tick itself keeps
# advancing at 20/sec regardless, which is the invariant R-099-03 requires.
const TACTICAL_BASE_TICKS_PER_SECOND := 20.0
const TACTICAL_HIGH_LOAD_UNITS := 1000
const TACTICAL_HIGH_LOAD_PERIOD := 2
# Cap on tactical_step_n's n per _process call so a stalled frame (long GC
# pause, breakpoint, etc.) never floods the pipe with a huge catch-up
# request; any ticks still owed after the cap carry over to later frames.
const TACTICAL_MAX_STEPS_PER_FRAME := 10

# Player faction: read from the loaded frame when the frame carries
# "player_faction"; falls back to SimSession.bridge().player_faction()
# so live play also works when the frame does not carry the key.
# -1 means not yet set; visible["−1"] in a frame would be empty.
var _local_faction: int = -1

var _frame: Dictionary = {}
var _canvas: float = 0.0
var _world_scale: float = WORLD_SCALE
var _camera := Vector2.ZERO
var _camera_initialized := false
var _camera_canvas: float = 0.0
var _camera_unbounded := false
var _zoom := 1.0
var _last_tick := -1
var _fit_scale := WORLD_SCALE
var _pointer_seen := false
var _facing_fixed := false
var _frozen_facing: Dictionary = {}
var _selected: Array = []
var _unit_visuals: Dictionary = {}
var _display_px: Dictionary = {}
var _last_command: Dictionary = {}

# Real-time stepping state (see TACTICAL_BASE_TICKS_PER_SECOND above).
# _tactical_calls_due carries fractional tactical_step_n calls across frames
# so the average call rate matches the target over time even though each
# frame can only request a whole number of calls. _mission_over_seen latches
# once a loaded frame reports mission_over so _process never steps a mission
# that has already ended (the view still routes to debrief the moment it
# sees the flag, in load_frame() below; this only stops further stepping).
var _tactical_calls_due: float = 0.0
var _mission_over_seen := false

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


func _get_local_faction() -> int:
	if _local_faction >= 0:
		return _local_faction
	return SimSession.bridge().player_faction()


func load_frame(frame: Dictionary) -> void:
	_frame = frame
	if frame.has("player_faction"):
		_local_faction = int(frame["player_faction"])
	# docs/architecture.md "C transport v1", tactical snapshot: the sim itself
	# ended the mission (R-075-07 termination, checked live every tactical
	# tick -- not only in response to the player's own End Mission press).
	# Route to debrief the same way the End Mission button does, above, and
	# latch _mission_over_seen so _process() stops requesting more ticks.
	if bool(frame.get("mission_over", false)):
		_mission_over_seen = true
		SceneRouter.go_to("debrief")
	_canvas = float(frame.get("map", {}).get("canvas", 0.0))
	if _canvas > 0.0:
		_fit_scale = SCREEN_H / _canvas
		_world_scale = _fit_scale * _zoom
	var tick := int(frame.get("tick", 0))
	var fresh_load := tick <= _last_tick
	_last_tick = tick
	if _canvas > 0.0 and (not _camera_initialized or _canvas != _camera_canvas or fresh_load):
		_zoom = 1.0
		_world_scale = _fit_scale
		_camera = _force_camera()
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
		"local_faction": _get_local_faction(),
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


# Drives the live mission every frame once it has begun (see the constants
# block above for the rate and R-099-03 rationale). No wall-clock read: only
# `delta`, the engine's own frame time, decides how many whole tactical ticks
# are due; the client never adds randomness or timing input to the sim
# itself, only the count of ticks it requests. Does nothing while the
# mission has not begun yet or has already ended (_mission_over_seen); the
# scene has no pause/menu state to also gate on.
func _process(delta: float) -> void:
	_pan_input(delta)
	if _mission_over_seen:
		return
	var bridge = SimSession.bridge()
	if not bridge.mission_begun():
		return
	_tactical_calls_due += delta * TACTICAL_BASE_TICKS_PER_SECOND / float(_tactical_tick_period())
	var k := int(_tactical_calls_due)
	if k <= 0:
		return
	if k > TACTICAL_MAX_STEPS_PER_FRAME:
		k = TACTICAL_MAX_STEPS_PER_FRAME
	_tactical_calls_due -= float(k)
	qa_step(k)


# R-099-03: the tick period the engine is currently spanning per
# om_tactical_step call, inferred client-side from the live unit count in
# the last loaded frame (the pipe does not expose om_tactical_tick_period
# directly). Mirrors csrc/unit.c's om_tac_update_period live-unit count
# (in-use units with hp > 0).
func _tactical_tick_period() -> int:
	return TACTICAL_HIGH_LOAD_PERIOD if _live_unit_count() > TACTICAL_HIGH_LOAD_UNITS else 1


func _live_unit_count() -> int:
	var n := 0
	for u in _frame.get("units", []):
		if float(u.get("hp", 0.0)) > 0.0:
			n += 1
	return n


# Advances the live mission by n tactical ticks and reloads the view. Used
# directly by QA (unchanged) and by _process() above for real-time play.
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


func qa_set_selected(ids: Array) -> void:
	_selected = []
	for v in ids:
		_selected.append(int(v))


func qa_pan(x: float, y: float) -> void:
	if _camera_unbounded:
		_camera = Vector2(x, y)
	else:
		_camera = Vector2(clampf(x, 0.0, _canvas), clampf(y, 0.0, _canvas))
	_update_display_px()
	_redraw()


# Frames what the player sees at mission start: shifts the canvas-centred camera
# just enough to bring every visible unit's sprite on screen; if they cannot all
# fit, centres on their bounding box.
func _force_camera() -> Vector2:
	var centre := Vector2(_canvas * 0.5, _canvas * 0.5)
	var lf := _get_local_faction()
	var seen := _visible_ids()
	var lo := Vector2(INF, INF)
	var hi := Vector2(-INF, -INF)
	for u in _frame.get("units", []):
		if int(u.get("faction", -1)) == lf or seen.has(int(u.get("id"))):
			var p := Vector2(float(u.get("x", 0.0)), float(u.get("y", 0.0)))
			lo = lo.min(p)
			hi = hi.max(p)
	if lo.x == INF:
		return centre
	var pad := UNIT_SIZE * 0.5 / _world_scale
	var half := Vector2(SCREEN_W, SCREEN_H) * 0.5 / _world_scale
	var cam := centre
	for axis in 2:
		var lo_a := lo[axis] - pad
		var hi_a := hi[axis] + pad
		if hi_a - lo_a >= half[axis] * 2.0:
			cam[axis] = (lo_a + hi_a) * 0.5
		elif lo_a < centre[axis] - half[axis]:
			cam[axis] = lo_a + half[axis]
		elif hi_a > centre[axis] + half[axis]:
			cam[axis] = hi_a - half[axis]
	return cam


func _zoom_by(factor: float) -> void:
	_zoom = clampf(_zoom * factor, ZOOM_MIN, ZOOM_MAX)
	_world_scale = _fit_scale * _zoom
	qa_pan(_camera.x, _camera.y)


func _pan_input(delta: float) -> void:
	var dir := Vector2.ZERO
	if Input.is_key_pressed(KEY_LEFT):
		dir.x -= 1.0
	if Input.is_key_pressed(KEY_RIGHT):
		dir.x += 1.0
	if Input.is_key_pressed(KEY_UP):
		dir.y -= 1.0
	if Input.is_key_pressed(KEY_DOWN):
		dir.y += 1.0
	if _pointer_seen:
		var vp := get_viewport()
		var m := vp.get_mouse_position()
		var r := vp.get_visible_rect().size
		if m.x <= EDGE_MARGIN_PX:
			dir.x -= 1.0
		elif m.x >= r.x - EDGE_MARGIN_PX:
			dir.x += 1.0
		if m.y <= EDGE_MARGIN_PX:
			dir.y -= 1.0
		elif m.y >= r.y - EDGE_MARGIN_PX:
			dir.y += 1.0
	if dir != Vector2.ZERO and _world_scale > 0.0:
		var step := dir.normalized() * PAN_SPEED_PX * delta / _world_scale
		qa_pan(_camera.x + step.x, _camera.y + step.y)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion:
		_pointer_seen = true
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_WHEEL_UP and mb.pressed:
			_zoom_by(ZOOM_STEP)
		elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN and mb.pressed:
			_zoom_by(1.0 / ZOOM_STEP)
		elif mb.button_index == MOUSE_BUTTON_LEFT:
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
	for v in _frame.get("visible", {}).get(str(_get_local_faction()), []):
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
	poly.color = Color(0.2, 0.6, 1.0) if faction == _get_local_faction() else Color(1.0, 0.3, 0.3)
	return poly

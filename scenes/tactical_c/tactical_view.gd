extends Node2D

const SimSession := preload("res://autoload/sim_session.gd")
const Ground3DHost := preload("res://scenes/ground3d/ground3d.gd")
const GroundProjection := preload("res://scenes/ground3d/projection.gd")
const SettlementLayerNode := preload("res://scenes/settlement/settlement_layer.gd")

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
# Draft: raised from 4.0 so the opening frame can close in on a dense deployment (A19: 330 own units sit inside 540 wu of a
# 24000 wu canvas, one pixel at the fit scale); the framing stops one wheel notch short of this.
const ZOOM_MAX := 40.0
const ZOOM_STEP := 1.25
const PAN_SPEED_PX := 600.0

# A6b HUD. The clock reads elapsed mission time (R-104-03) from the frame tick
# at the sim's tactical rate.
const ATTACK_MOVE_FEEDBACK_SECONDS := 1.0
const ATTACK_MOVE_FEEDBACK_COLOR := Color(1.0, 0.8, 0.2)
const EDGE_MARGIN_PX := 4.0
# Named draft (nobody gave a letter, Q-232-01/03 leave the key open): the ping key. Ping = this key, then a click.
const PING_KEY := KEY_P
const PICK_RADIUS_PX := 16.0

# VG-A A12: the shell. Pieces are instantiated by their section 2 node name; a piece whose script is not on main yet
# (the Fx nodes, StructuresLayer, Reinforcements, LoadingOverlay) is a bare placeholder node of that name, replaced
# by the piece's script when it lands (docs/northstar/plans/2026-10-07-visible-game-spec.md lane A).
const PIECES := {
	"MapLayer": "res://scenes/tactical_c/map_layer.gd",
	"StructuresLayer": "res://scenes/tactical_c/structures_layer.gd",
	"ObjectiveMarkers": "res://scenes/tactical_c/objective_markers.gd",
	"FogLayer": "res://scenes/tactical_c/fog_layer.gd",
	"LayerView": "res://scenes/tactical_c/layer_view.gd",
	"UnitSquads": "res://scenes/tactical_c/unit_squads.gd",
	"UnitVisuals": "res://scenes/tactical_c/unit_visuals.gd",
	"Shots": "res://scenes/tactical_c/fx/shots.gd",
	"Deaths": "res://scenes/tactical_c/fx/deaths.gd",
	"Abilities": "res://scenes/tactical_c/fx/abilities.gd",
	"Ambient": "res://scenes/tactical_c/fx/ambient.gd",
	"Objectives": "res://scenes/tactical_c/hud/objectives_panel.gd",
	"Selection": "res://scenes/tactical_c/hud/selection_panel.gd",
	"Comb": "res://scenes/tactical_c/hud/comb.gd",
	"Events": "res://scenes/tactical_c/hud/events_feed.gd",
	"Reinforcements": "res://scenes/tactical_c/hud/reinforcements.gd",
}

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
var _attack_move_mode := false
var _clock_label: Label
var _selection_label: Label
var _hud: Control
var _fx: Node2D
var _motion: Node
var _since_load := 0.0
var _load_gap := 0.05
var _live_stepped := false
var _loading_overlay: Control # loading_overlay.gd
var _ping_armed := false
var _last_tick := -1
var _fit_scale := WORLD_SCALE
var _pointer_seen := false
var _facing_fixed := false
var _frozen_facing: Dictionary = {}
var _selected: Array = []
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

var _error_panel: Control
var _ending := false
var _ground_layer: Node2D
# Ground era (S-236): the 3D ground hosted under the 2D shell. The 2D terrain layer is demoted to the map band.
var _ground3d: Node
var _settlement: Node3D
var _terrain: Dictionary = {}


func _ready() -> void:
	# C8 flow spine: SceneRouter._swap_scene never passes data into a
	# scene routed to via go_to() (no setup() call on this path), so this
	# view self-loads the first live tactical frame on a fresh route-in. A
	# failed live load leaves the view empty and logs the reason; it never
	# falls back to a fixture (C5-2).
	_build_shell()
	_load_live()
	_update_hud()
	var end_mission_btn := get_node_or_null("CanvasLayer/EndMission")
	if end_mission_btn != null:
		end_mission_btn.pressed.connect(_end_mission)


func _build_shell() -> void:
	_motion = load("res://scenes/tactical_c/unit_motion.gd").new()
	add_child(_motion)
	for n in ["MapLayer", "StructuresLayer", "ObjectiveMarkers", "FogLayer", "LayerView", "UnitSquads", "UnitVisuals"]:
		add_child(_piece(n, false))
	_node("LayerView").layer_order_requested.connect(order_layer)  # the To-layer buttons (R-002-01, R-104-09)
	_fx = Node2D.new()
	_fx.name = "Fx"
	add_child(_fx)
	for n in ["Shots", "Deaths", "Abilities", "Ambient"]:
		_fx.add_child(_piece(n, false))
	_hud = Control.new()
	_hud.name = "Hud"
	_hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
	$CanvasLayer.add_child(_hud)
	for n in ["Objectives", "Selection", "Comb", "Events", "Reinforcements"]:
		var panel := _piece(n, true)
		_hud.add_child(panel)
		if PANEL_POSITIONS.has(n):
			panel.position = PANEL_POSITIONS[n]
		panel.draw.connect(_draw_backing.bind(panel))
	var strip := Control.new()
	strip.name = "Strip"
	strip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hud.add_child(strip)
	var clock := Control.new()
	clock.name = "Clock"
	clock.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hud.add_child(clock)
	clock.draw.connect(_draw_backing.bind(clock))
	_clock_label = _make_hud_label(Vector2(1500.0, 20.0), clock)
	_selection_label = _make_hud_label(Vector2(20.0, SCREEN_H - 60.0), _hud.get_node("Selection"))
	_loading_overlay = load("res://scenes/tactical_c/loading_overlay.gd").new()
	$CanvasLayer.add_child(_loading_overlay)
	var sel := _hud.get_node("Selection")
	if sel.has_signal("selection_changed"):
		sel.selection_changed.connect(_on_panel_selection)
		sel.centre_requested.connect(func(w: Vector2): qa_pan(w.x, w.y))


# A19: HUD panels sit at fixed corners (a bare Control sits at 0,0 with no size, so Reinforcements drew under Objectives).
const PANEL_POSITIONS := {"Events": Vector2(760.0, 70.0), "Reinforcements": Vector2(1640.0, 800.0)}
const PANEL_BACK := Color(0.05, 0.06, 0.08, 0.7)
const PANEL_PAD := 8.0


# A19: a translucent backing under whatever the panel's children show, so each reads as a panel on the field.
func _draw_backing(panel: Control) -> void:
	var box := Rect2()
	var any := false
	for c in panel.get_children():
		if not (c is Control) or not c.visible:
			continue
		var r := Rect2(c.position, c.size.max(c.get_combined_minimum_size()))
		if r.size.x < 1.0 or r.size.y < 1.0 or (c is Label and c.text == ""):
			continue
		box = r if not any else box.merge(r)
		any = true
	if any:
		panel.draw_rect(box.grow(PANEL_PAD), PANEL_BACK)


func _piece(node_name: String, control: bool) -> Node:
	var path: String = PIECES[node_name]
	var n: Node
	if ResourceLoader.exists(path):
		n = load(path).new()
	else:
		n = Control.new() if control else Node2D.new()
		if n is Control:
			n.mouse_filter = Control.MOUSE_FILTER_IGNORE
	n.name = node_name
	return n


func _on_panel_selection(ids: Array) -> void:
	_selected = ids.duplicate()
	_node("UnitVisuals").set_selected(_selected)
	_update_hud()


func _node(node_name: String) -> Node:
	return find_child(node_name, true, false)


func _sync_selection() -> void:
	var panel := _node("Selection")
	if panel != null and panel.has_method("set_selection"):
		panel.set_selection(_selected)
	_node("UnitVisuals").set_selected(_selected)


func _load_live() -> void:
	var bridge = SimSession.bridge()
	# FINDING-net-first-tick: load_tactical_live adds one tactical_step on each peer, so the C net tick runs one ahead
	# of LockstepSession._released and every order is stamped tick == st->tick and refused OM_CMD_ERR_LATE
	# (csrc/cmd_stream.c:161). The match owns the tick: load its last frame, step nothing. An empty last frame
	# loads nothing here; the first frame arrives through _match_frame.
	# See also: tests/test_vg_f_nettick.gd
	if NetMatch.active():
		if _error_panel != null:
			_error_panel.hide_error()
		if NetMatch.has_method("last_frame"):
			var mf: Dictionary = NetMatch.last_frame()
			if not mf.is_empty():
				load_frame(mf)
		set_terrain(bridge.terrain() if bridge.has_method("terrain") else {})
		return
	if bridge.load_tactical_live(bridge.live_seed(), bridge.DEFAULT_N_REGIONS, bridge.DEFAULT_FEATURES):
		if _error_panel != null:
			_error_panel.hide_error()
		load_frame(bridge.tactical_frame())
		set_terrain(bridge.terrain() if bridge.has_method("terrain") else {})
		return
	var reason: String = bridge.last_error()
	push_error("tactical_view: live tactical frame failed: %s" % reason)
	_show_error(reason if reason != "" else "tactical load failed")


func _ground_era() -> bool:
	var cfg := get_node_or_null("/root/EraConfig")
	return cfg != null and cfg.kind() == "ground"


func set_terrain(t: Dictionary) -> void:
	_terrain = t
	if t.is_empty():
		if _ground_layer != null:
			_ground_layer.queue_free()
			remove_child(_ground_layer)
			_ground_layer = null
		if _ground3d != null:
			_ground3d.queue_free()
			remove_child(_ground3d)
			_ground3d = null
			_settlement = null
		return
	if _ground_layer == null:
		_ground_layer = load("res://scenes/tactical_c/terrain_layer.gd").new()
		add_child(_ground_layer)
		move_child(_ground_layer, 0)
	_ground_layer.set_terrain(t)
	_ground_layer.set_view(_world_scale, _camera)
	var deaths := _fx.get_node_or_null("Deaths")
	if deaths != null and deaths.has_method("set_ground"):
		deaths.set_ground(t, t.get("layer_floors_wu", []), t.get("flyer_types", []))
	if _ground_era():
		if _ground3d == null:
			_ground3d = Ground3DHost.new()
			_ground3d.name = "Ground3D"
			add_child(_ground3d)
			move_child(_ground3d, 0)
		_ground3d.set_terrain(t)
		_add_ground_layers(t)
		_ground3d.set_frame(_frame, SimSession.bridge().mission())
		_camera = _force_camera()
		_ground3d.camera_rig().pan_to(_camera)
		_sync_from_rig()
		_update_display_px()
		_redraw()


# E1p-a: the 3D layers go in through Ground3D.add_layer once the host has its terrain, so the layer is primed here with
# the terrain and the frame already held (add_layer only fans later changes).
func _add_ground_layers(t: Dictionary) -> void:
	if _settlement != null:
		return
	_settlement = SettlementLayerNode.new()
	_settlement.local_faction = _get_local_faction()
	_ground3d.add_layer(_settlement)
	_settlement.set_terrain(t)
	_settlement.set_frame(_frame)


func _rig() -> Node3D:
	return _ground3d.camera_rig() if _ground3d != null else null


# The rig is the camera in a ground era: the view reads its pan target and pixels-per-wu back as the map band's
# camera {x,y} and scale, and shows the 2D terrain layer only on the map band.
func _sync_from_rig() -> void:
	var rig := _rig()
	if rig == null:
		return
	var q: Dictionary = rig.qa_camera()
	_camera = Vector2(q["x"], q["y"])
	_world_scale = q["scale"]
	if _ground_layer != null:
		_ground_layer.visible = rig.band() == "map"


func _show_error(reason: String) -> void:
	if _error_panel == null:
		_error_panel = load("res://scenes/shared/error_panel.tscn").instantiate()
		_error_panel.retry_pressed.connect(_load_live)
		add_child(_error_panel)
	_error_panel.show_error(reason)


# A43: both routing sites (End Mission, a mission_over frame) end the mission
# here: one mission_end, pump until the debrief frame is held (the debrief
# scene shows it and sends nothing), then route. No frame: error panel, no route.
func _end_mission() -> void:
	if _ending:
		return
	_ending = true
	_mission_over_seen = true
	var bridge = SimSession.bridge()
	var got := []
	var on_frame := func(frame):
		if String(frame.get("type", "")) == "debrief":
			got.append(frame)
	bridge.frame_received.connect(on_frame)
	if NetMatch.active():
		NetMatch.leave()
	bridge.send_command({"type": "cmd", "name": "mission_end"})
	var deadline: int = Time.get_ticks_msec() + bridge.LIVE_READ_TIMEOUT_MSEC
	while got.is_empty() and Time.get_ticks_msec() < deadline:
		if bridge.pump() == 0:
			OS.delay_msec(5)
	bridge.frame_received.disconnect(on_frame)
	_ending = false
	if got.is_empty():
		var reason: String = bridge.last_error() if bridge.last_error() != "" else "timed out waiting for the debrief frame"
		push_error("tactical_view: mission_end failed: %s" % reason)
		_show_error(reason)
		return
	SceneRouter.go_to("debrief")


func _make_hud_label(pos: Vector2, parent: Node) -> Label:
	var l := Label.new()
	l.position = pos
	parent.add_child(l)
	return l


func _update_hud() -> void:
	_sync_orderable()
	if _clock_label == null:
		return
	var tick := int(_frame.get("tick", 0))
	var events := _node("Events")
	if events != null and events.has_method("clock_text"):
		_clock_label.text = events.clock_text(tick)
	else:
		var secs := int(tick / int(TACTICAL_BASE_TICKS_PER_SECOND))
		_clock_label.text = "%02d:%02d" % [secs / 60, secs % 60]
	var mission_objectives: Array = []
	var objs: Array = SimSession.bridge().mission().get("objectives", [])
	for i in objs.size():
		var o: Dictionary = objs[i].duplicate()
		if not o.has("i"):
			o["i"] = i
		mission_objectives.append(o)
	_node("Objectives").set_objectives(mission_objectives, _frame.get("objectives", []))
	_selection_label.text = "%d selected" % _selected.size() if not _selected.is_empty() else ""


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
		_end_mission()
	_canvas = float(frame.get("map", {}).get("canvas", 0.0))
	if _canvas > 0.0:
		_fit_scale = SCREEN_H / _canvas
		_world_scale = _fit_scale * _zoom
	if _settlement != null:
		_settlement.local_faction = _get_local_faction()
	if _ground3d != null:
		_ground3d.set_frame(frame, SimSession.bridge().mission())
	var tick := int(frame.get("tick", 0))
	var fresh_load := tick <= _last_tick
	_last_tick = tick
	if _canvas > 0.0 and (not _camera_initialized or _canvas != _camera_canvas or fresh_load):
		_zoom = _framing_zoom()
		_world_scale = _fit_scale * _zoom
		_camera = _force_camera()
		_camera_initialized = true
		_camera_canvas = _canvas
		if _rig() != null:
			_rig().pan_to(_camera)
	if _rig() != null:
		_sync_from_rig()
	if _facing_fixed:
		for u in frame.get("units", []):
			var id := int(u.get("id"))
			if not _frozen_facing.has(id):
				_frozen_facing[id] = float(u.get("facing", 0.0))
	_prune_selected()
	_update_display_px()
	_loading_overlay.dismiss()
	_node("Selection").set_frame(frame)
	_node("Events").feed(frame, _get_local_faction())
	_redraw()
	_sync_selection()
	_update_hud()


# The read-only HUD readouts rebuild their children each frame with the default STOP filter; one at the top-left
# swallowed the press of a box drag from (0,0) before _unhandled_input saw it. Run at the end of every _redraw: a camera
# pan redraws without a load_frame and rebuilt Reinforcements with fresh STOP children under the edge-scrolling pointer.
func _ignore_mouse(n: Node) -> void:
	if n is Control:
		n.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for c in n.get_children():
		_ignore_mouse(c)


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
		# A16 (S-002's visible half, G4): the transition target and load from the frame's unit object, absent when omitted.
		if u.has("tl"):
			units[str(id)]["tl"] = int(u["tl"])
		if u.has("ld"):
			units[str(id)]["ld"] = int(u["ld"])
	return {
		"scene": "tactical_view",
		"tick": int(_frame.get("tick", 0)),
		"plants": ["facing-fixed", "camera-unbounded", "move-order-dropped"],
		"canvas": _canvas,
		"scale": _world_scale,
		"unit_count": _frame.get("units", []).size(),
		"units": units,
		"units_px": _display_px.duplicate(),
		"focus_layer": int(_node("LayerView").focus_layer()),
		"local_faction": _get_local_faction(),
		"selected": _selected.duplicate(),
		"camera": {"x": _camera.x, "y": _camera.y},
		"ground3d": _ground3d.qa_state()["ground3d"] if _ground3d != null else {"present": false},
		"objects_px": _objects_px(),
		"last_command": _last_command.duplicate(),
		"commands_sent_last_order": _commands_sent_last_order,
		"units_in_last_command": _units_in_last_command,
		"ground_layer": _ground_layer_state(),
		"error_panel": _error_panel != null and _error_panel.visible and _error_panel.get_node("ErrorPanel").visible,
		"inventory": _inventory(),
		"settlement_lots": _settlement.lots_drawn() if _settlement != null else [],
	}


func _inventory() -> Dictionary:
	var squads := 0
	var squad_node := _node("UnitSquads")
	for u in _frame.get("units", []):
		if squad_node.squad_models(int(u.get("id"))).size() > 0:
			squads += 1
	var own_structures := 0
	for st in _frame.get("structures", []):
		if int(st.get("owner", -1)) == _get_local_faction():
			own_structures += 1
	var map_layer := _node("MapLayer")
	var hud := {
		"clock": _clock_label.text,
		"objectives": _node("Objectives").rows().size(),
		"selection": _node("Selection").summary().size(),
		"events": _node("Events").lines().size(),
		"strip": _node("LayerView").strip_layers().size(),
		"comb": _node("Comb").is_open(),
		"reinforcements": own_structures,
	}
	return {
		"fog_layer": _node("FogLayer").sight_discs().size(),
		"objective_markers": _node("ObjectiveMarkers").beacons().size(),
		"cover_cells": map_layer.cover_cells().size(),
		"obstacles": map_layer.obstacle_polygons().size(),
		"structures": _frame.get("structures", []).size(),
		"shots_in_flight": _piece_count("Shots", "in_flight"),
		"wrecks": _piece_count("Deaths", "wrecks"),
		"squads": squads,
		"abilities_fx": _piece_count("Abilities", "active"),
		"ambient": _piece_count("Ambient", "active"),
		"loading_overlay": 1 if _loading_overlay.visible else 0,
		"hud": hud,
		"settlement_lots": _settlement.lots_drawn().size() if _settlement != null else 0,
	}


# A count a Fx piece reports through `method`; 0 while the piece is still a placeholder (see PIECES).
func _piece_count(node_name: String, method: String) -> int:
	var n := _node(node_name)
	return _count_of(n.call(method)) if n.has_method(method) else 0


func _count_of(v: Variant) -> int:
	return v.size() if v is Array or v is Dictionary else int(v)


func _objects_px() -> Array:
	var out: Array = []
	var nodes: Array = _frame.get("map", {}).get("nodes", [])
	for o in SimSession.bridge().mission().get("objectives", []):
		var n := int(o.get("node", -1))
		if n >= 0 and n < nodes.size():
			out.append(_to_screen(float(nodes[n]["x"]), float(nodes[n]["y"])))
	return out


func _ground_layer_state() -> Dictionary:
	if _ground_layer == null:
		return {"present": false}
	var tex: Texture2D = _ground_layer.ground_texture()
	return {"present": true, "cells_w": tex.get_width(), "cells_h": tex.get_height(), "ticks": _ground_layer.slope_ticks().size()}


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
	BugReportManager.log_command(cmd)
	var bridge = SimSession.bridge()
	var ok: bool
	# A16 (R-002-01): a layer order carries its engine layer to the bridge (c_bridge.gd:476-477 reads cmd["layer"]).
	var layer_extra := {"layer": int(cmd.get("layer", 0))} if kind == "set_layer" else {}
	if NetMatch.active():
		return _send_match_command(kind, unit_ids, cmd)
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
			}.merged(layer_extra))
			ok = ok or r
	else:
		ok = bridge.send_unit_command({
			"kind": kind,
			"unit_ids": unit_ids,
			"x": float(cmd.get("x", 0.0)),
			"y": float(cmd.get("y", 0.0)),
			"target": int(cmd.get("target", -1)),
		}.merged(layer_extra))
		_commands_sent_last_order = 1
	_units_in_last_command = unit_ids.size()
	_last_command = {"ok": ok, "kind": kind, "units": unit_ids.size(),
		"x": float(cmd.get("x", 0.0)), "y": float(cmd.get("y", 0.0))}.merged(layer_extra)
	return ok


# A16, the layer order (S-002, R-002-01 a hard transfer begins on the same tick). The view holds engine layers 0..4.
# Returns the ok of the order; a refusal never reaches the bridge. Walker source: EraConfig.movement_kinds() (G3).
func order_layer(layer: int) -> bool:
	if _selected.is_empty():
		return false
	if _selection_is_walkers():
		# R-001-07: a walker takes no layer order; the buttons are dimmed (set_orderable) and the key does nothing.
		_refuse_layer(layer, "walkers")
		return false
	if layer < 0 or layer >= _node("LayerView").LAYER_COUNT:
		_refuse_layer(layer, "range")
		return false
	return send_command({"kind": "set_layer", "unit_ids": _selected.duplicate(), "layer": layer})


# Q is dir +1 (one layer up), E is dir -1 (one layer down), from the lowest selected unit's layer.
# DRAFT-a16-qe-relative (register Q-A16-01 (a), Westley decides). See also: the layers mockup
# scenes/mockups/layers/layers_mockup.gd:94-97, where Q and E were absolute because it had two layers.
func order_layer_step(dir: int) -> bool:
	var lowest := _lowest_selected_layer()
	if lowest < 0:
		return false
	return order_layer(lowest + dir)


func _refuse_layer(layer: int, reason: String) -> void:
	_last_command = {"ok": false, "kind": "set_layer", "units": _selected.size(), "x": 0.0, "y": 0.0, "layer": layer, "reason": reason}


func _lowest_selected_layer() -> int:
	var lowest := -1
	for u in _frame.get("units", []):
		if _selected.has(int(u.get("id"))):
			var l := int(u.get("layer", 0))
			lowest = l if lowest < 0 else mini(lowest, l)
	return lowest


# True when the selection is not empty and every selected unit's type walks (EraConfig.movement_kinds(): 0 flying, 1 walking).
func _selection_is_walkers() -> bool:
	if _selected.is_empty():
		return false
	var walks := {}
	var mk: Array = EraConfig.movement_kinds()
	for i in range(0, mk.size() - 1, 2):
		walks[int(mk[i])] = int(mk[i + 1]) == 1
	var seen := 0
	for u in _frame.get("units", []):
		if _selected.has(int(u.get("id"))):
			seen += 1
			if not walks.get(int(u.get("type", 0)), false):
				return false
	return seen > 0


# R-001-07: dim the To-layer buttons while only walkers are selected; run on every selection and frame change.
func _sync_orderable() -> void:
	var lv := _node("LayerView")
	if lv != null and lv.has_method("set_orderable"):
		lv.set_orderable(not _selection_is_walkers())


# Drives the live mission every frame once it has begun (see the constants
# block above for the rate and R-099-03 rationale). No wall-clock read: only
# `delta`, the engine's own frame time, decides how many whole tactical ticks
# are due; the client never adds randomness or timing input to the sim
# itself, only the count of ticks it requests. Does nothing while the
# mission has not begun yet or has already ended (_mission_over_seen); the
# scene has no pause/menu state to also gate on.
func _process(delta: float) -> void:
	_pan_input(delta)
	for n in ["Objectives", "Selection", "Events", "Reinforcements", "Clock"]:
		_node(n).queue_redraw()
	_since_load += delta
	if NetMatch.active():
		_match_frame()
	else:
		_step_live(delta)
	_apply_motion()


# Wiring spec W5 / interface 5: in a match NetMatch owns the tick; the view only submits orders and shows frames.
const MATCH_VERBS := {"move": 0, "attack_move": 1, "attack_target": 2, "set_layer": 4}  # 4 = OM_NET_VERB_SET_LAYER (csrc/ouroboros_sim.h:292), G12


func _send_match_command(kind: String, unit_ids: Array, cmd: Dictionary) -> bool:
	var ok := MATCH_VERBS.has(kind)
	if ok:
		var c := {"verb": MATCH_VERBS[kind], "units": unit_ids, "x": float(cmd.get("x", 0.0)), "y": float(cmd.get("y", 0.0))}
		if kind == "attack_target":
			c["arg"] = int(cmd.get("target", -1))
		ok = NetMatch.command(c) >= 0
	_commands_sent_last_order = 1
	_units_in_last_command = unit_ids.size()
	_last_command = {"ok": ok, "kind": kind, "units": unit_ids.size(),
		"x": float(cmd.get("x", 0.0)), "y": float(cmd.get("y", 0.0))}
	return ok


func _match_frame() -> void:
	var st: Dictionary = NetMatch.state()
	var kind := String(st.get("kind", ""))
	if kind == "desync":
		_show_desync(int(st["tick"]), int(st["section"]))
	_show_stall(st.get("peer", -1) if kind == "stalled" else -1)
	if kind == "stalled" or not NetMatch.has_method("last_frame"):
		return
	var f: Dictionary = NetMatch.last_frame()
	if f.is_empty() or int(f.get("tick", -1)) == int(_frame.get("tick", -2)):
		return
	_load_gap = _since_load
	_since_load = 0.0
	load_frame(f)
	_live_stepped = true
	_motion.push_frame(_frame)


const SECTION_NAMES := ["regions", "factions", "rng", "units", "movement", "mission", "fog", "macro", "support_map"]


func _show_desync(tick: int, section: int) -> void:
	var name: String = SECTION_NAMES[section] if section >= 0 and section < SECTION_NAMES.size() else str(section)
	_show_error("Desync at tick %d, section %s" % [tick, name])
	var retry := _error_panel.find_child("Retry", true, false)
	if retry != null:
		retry.visible = false


var _stall_overlay: Control
var _stall_label: Label


# Q-NET-02 b: a dimmed pause overlay naming the peer the match waits for; never a rewind.
func _show_stall(peer) -> void:
	if int(peer) < 0:
		if _stall_overlay != null:
			_stall_overlay.visible = false
		return
	if _stall_overlay == null:
		_stall_overlay = Control.new()
		_stall_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
		_stall_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var dim := ColorRect.new()
		dim.color = Color(0, 0, 0, 0.5)
		dim.set_anchors_preset(Control.PRESET_FULL_RECT)
		dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_stall_overlay.add_child(dim)
		_stall_label = Label.new()
		_stall_label.set_anchors_preset(Control.PRESET_CENTER)
		_stall_overlay.add_child(_stall_label)
		$CanvasLayer.add_child(_stall_overlay)
	_stall_label.text = "Paused, waiting for peer %d" % int(peer)
	_stall_overlay.visible = true


func _step_live(delta: float) -> void:
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


# S-101: between two loaded frames the units are drawn on the path from the previous frame to the current one
# (UnitMotion), taking as long as the last gap between loads. Direct load_frame calls keep the raw positions.
func _apply_motion() -> void:
	if not _live_stepped or _mission_over_seen:
		return
	var alpha := clampf(_since_load / maxf(_load_gap, 0.001), 0.0, 1.0)
	var visible_ids := _visible_ids()
	var uv := _node("UnitVisuals")
	for u in _frame.get("units", []):
		var id := int(u.get("id"))
		if not visible_ids.has(id) or not _motion.has_unit(id):
			continue
		var w: Vector2 = _motion.position_at(id, alpha)
		var px := _to_screen(w.x, w.y)
		_display_px[str(id)] = px
		var node: Node2D = uv.unit_node(id)
		if node != null:
			node.position = Vector2(px[0], px[1])


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
		_load_gap = _since_load
		_since_load = 0.0
		load_frame(bridge.tactical_frame())
		_live_stepped = true
		_motion.push_frame(_frame)


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
	_sync_selection()
	_update_hud()
	return out


func qa_set_selected(ids: Array) -> void:
	_selected = []
	for v in ids:
		_selected.append(int(v))
	_sync_selection()
	_update_hud()


func qa_pan(x: float, y: float) -> void:
	if _camera_unbounded:
		_camera = Vector2(x, y)
	else:
		_camera = Vector2(clampf(x, 0.0, _canvas), clampf(y, 0.0, _canvas))
	if _rig() != null:
		_rig().pan_to(_camera)
		_sync_from_rig()
	_update_display_px()
	_redraw()


# A19: the zoom at which every own and visible unit fits the screen with the edge of its sight disc, so the dimming outside
# it shows too; 1.0 when they span the canvas, at most one wheel notch under ZOOM_MAX.
# Draft: the share of a sight radius kept in view around the units (nobody gave a number).
const FRAMING_SIGHT_SHARE := 1.0


func _framing_zoom() -> float:
	var lf := _get_local_faction()
	var seen := _visible_ids()
	var lo := Vector2(INF, INF)
	var hi := Vector2(-INF, -INF)
	var sight := 0.0
	for u in _frame.get("units", []):
		if int(u.get("faction", -1)) == lf or seen.has(int(u.get("id"))):
			var p := Vector2(float(u.get("x", 0.0)), float(u.get("y", 0.0)))
			lo = lo.min(p)
			hi = hi.max(p)
			sight = maxf(sight, float(u.get("sight", 0.0)))
	if lo.x == INF:
		return 1.0
	var size := hi - lo + Vector2.ONE * sight * FRAMING_SIGHT_SHARE
	var room := Vector2(SCREEN_W, SCREEN_H) - Vector2.ONE * UNIT_SIZE * 4.0
	var z := minf(room.x / maxf(size.x * _fit_scale, 1.0), room.y / maxf(size.y * _fit_scale, 1.0))
	return clampf(z, 1.0, ZOOM_MAX / ZOOM_STEP)


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
	if _rig() != null:
		return (lo + hi) * 0.5
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
	if _rig() != null:
		_rig().zoom_by(-1 if factor > 1.0 else 1)
		qa_pan(_camera.x, _camera.y)
		return
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
		var step := dir.normalized() * PAN_SPEED_PX * _pan_speed() * delta / _world_scale
		qa_pan(_camera.x + step.x, _camera.y + step.y)


func _pan_speed() -> float:
	var bus := get_node_or_null("/root/UIDataBus")
	return 1.0 if bus == null else clampf(float(bus.get_settings().get("pan_speed", 1.0)), 0.5, 2.0)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion:
		_pointer_seen = true
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_A:
			_attack_move_mode = true
		elif event.keycode == PING_KEY:
			_ping_armed = true
		elif event.keycode == KEY_TAB:
			_node("LayerView").cycle_focus()
		elif (event.keycode == KEY_Q or event.keycode == KEY_E) and not (event.alt_pressed or event.ctrl_pressed or event.shift_pressed or event.meta_pressed):
			# DRAFT-a16-qe-relative (register Q-A16-01 (a), Westley decides): Q one layer up, E one layer down from the
			# lowest selected unit's layer. See also: the layers mockup scenes/mockups/layers/layers_mockup.gd:94-97.
			# A modifier held does nothing here (Alt+N is narrowing's, R-105-06, G7). R-103-04: never moves the camera.
			order_layer_step(1 if event.keycode == KEY_Q else -1)
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_WHEEL_UP and mb.pressed:
			_zoom_by(ZOOM_STEP)
		elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN and mb.pressed:
			_zoom_by(1.0 / ZOOM_STEP)
		elif mb.button_index == MOUSE_BUTTON_LEFT:
			if mb.pressed:
				_drag_start = mb.position
				if mb.double_click:
					var hit := _unit_at(mb.position)
					if hit >= 0:
						_node("Selection").select_same_type(hit)
						_drag_start = Vector2(-1.0, -1.0)
			elif _ping_armed:
				_ping_armed = false
				_drag_start = Vector2(-1.0, -1.0)
				_send_ping(_to_world(mb.position))
			elif _attack_move_mode:
				_attack_move_mode = false
				_drag_start = Vector2(-1.0, -1.0)
				var w := _to_world(mb.position)
				send_command({"kind": "attack_move", "unit_ids": _selected.duplicate(), "x": w.x, "y": w.y})
				_show_order_feedback(mb.position)
			else:
				if _drag_start.x >= 0.0:
					qa_box_select(_drag_start.x, _drag_start.y, mb.position.x, mb.position.y)
					_drag_start = Vector2(-1.0, -1.0)
		elif mb.button_index == MOUSE_BUTTON_RIGHT and mb.pressed:
			_attack_move_mode = false
			_ping_armed = false
			var w := _to_world(mb.position)
			send_command({"kind": "move", "unit_ids": _selected.duplicate(), "x": w.x, "y": w.y})


# Q-232-01: the ping is an ability on the shared card; with a group selected the unit closest to the click casts it.
func _send_ping(w: Vector2) -> void:
	var best := -1
	var best_d := INF
	for u in _frame.get("units", []):
		var id := int(u.get("id"))
		if not _selected.has(id):
			continue
		var d := Vector2(float(u.get("x", 0.0)), float(u.get("y", 0.0))).distance_squared_to(w)
		if d < best_d:
			best_d = d
			best = id
	if best >= 0:
		send_command({"kind": "activate_ability", "unit_ids": [best], "x": w.x, "y": w.y})


func _unit_at(screen: Vector2) -> int:
	var best := -1
	var best_d := PICK_RADIUS_PX
	for id_str in _display_px:
		var p: Array = _display_px[id_str]
		var d := Vector2(float(p[0]), float(p[1])).distance_to(screen)
		if d <= best_d:
			best_d = d
			best = int(id_str)
	return best


func _to_world(screen: Vector2) -> Vector2:
	if _ground3d != null and is_inside_tree():
		var w = _ground3d.to_world(screen)
		if w != null:
			return w
	return (screen - Vector2(SCREEN_W, SCREEN_H) * 0.5) / _world_scale + _camera


func _show_order_feedback(screen: Vector2) -> void:
	var marker := _make_order_marker()
	marker.color = ATTACK_MOVE_FEEDBACK_COLOR
	marker.position = screen
	add_child(marker)
	var tw := marker.create_tween()
	tw.tween_property(marker, "modulate:a", 0.0, ATTACK_MOVE_FEEDBACK_SECONDS)
	tw.tween_callback(marker.queue_free)


func _visible_ids() -> Dictionary:
	var out := {}
	for v in _frame.get("visible", {}).get(str(_get_local_faction()), []):
		out[int(v)] = true
	return out


func _to_screen(wx: float, wy: float) -> Array:
	if _ground3d != null and is_inside_tree():
		var p: Vector2 = _ground3d.to_screen(wx, wy)
		return [p.x, p.y]
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


func _project_ground(w: Vector2) -> Vector2:
	return _ground3d.to_screen(w.x, w.y)


func _redraw() -> void:
	if not is_inside_tree():
		return
	if _ground_layer != null:
		_ground_layer.set_view(_world_scale, _camera)
	var lf := _get_local_faction()
	var mission: Dictionary = SimSession.bridge().mission()
	var ground := _ground3d != null
	if ground:
		for n in ["MapLayer", "ObjectiveMarkers", "FogLayer", "LayerView", "Shots"]:
			var piece := _node(n)
			if piece != null and piece.has_method("set_projector"):
				piece.set_projector(_project_ground)
	_node("MapLayer").set_frame(_frame, mission, lf, _world_scale, _camera)
	_node("ObjectiveMarkers").set_frame(_frame, mission, lf, _world_scale, _camera)
	if ground:
		_node("FogLayer").set_frame(_frame, mission, lf)
	else:
		_node("FogLayer").set_frame(_frame, lf, _world_scale, _camera)
	for n in ["LayerView", "UnitSquads", "UnitVisuals"]:
		_node(n).set_frame(_frame, lf, _world_scale, _camera)
	for n in ["StructuresLayer", "Shots", "Deaths", "Abilities", "Ambient"]:
		var piece := _node(n)
		if piece.has_method("set_frame"):
			if ground and n == "Shots":
				piece.set_frame(_frame, mission, lf)
			else:
				piece.set_frame(_frame, lf, _world_scale, _camera)
	var reinforcements := _node("Reinforcements")
	if reinforcements.has_method("set_frame"):
		reinforcements.set_frame(_frame, lf)
	for n in ["Objectives", "Comb", "Events", "Reinforcements"]:
		_ignore_mouse(_node(n))


# The order marker: a small square at the click, faded out; not a unit drawing.
func _make_order_marker() -> Polygon2D:
	var poly := Polygon2D.new()
	var h := UNIT_SIZE * 0.5
	poly.polygon = PackedVector2Array([Vector2(-h, -h), Vector2(h, -h), Vector2(h, h), Vector2(-h, h)])
	return poly

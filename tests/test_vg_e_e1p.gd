extends "res://tests/support/vg_c_case.gd"

# VG-E1 piece E1p (scenes/tactical_c/tactical_view.gd + scenes/ground3d/ground3d.gd add_layer hook), spec rev 8
# "Lane E1 part b". Proves S-193 R-193-03 (placement click), S-218 (strongpoints drawn), R-168-01/05 wiring.
# Pinned contract: ground3d.add_layer(node) puts the node after SlopesView and before Units3D (by script) and fans
# set_terrain(t) / set_frame(frame) to it; the view builds SettlementLayer, StrongpointLayer (via add_layer) and PlacementUi
# (under Hud); qa_state gains settlement_lots, strongpoints, placement {active, building, last_result}; the view listens to
# PlacementUi.placement_mode_changed(active, building) (the test emits it); with placement active a left click calls
# SimSession.bridge().send_place(world.x, world.y, building) with the _to_world point and starts no selection box.
# CONTROLS: the name finder misses an absent name; the stub records zero calls before any click; without placement mode the
# same click starts a selection box and calls no send_place; a probe layer that lacks the methods is not called.
# RED on main for: Ground3D has no add_layer, the view has no SettlementLayer/StrongpointLayer/PlacementUi nodes and no
# settlement_lots/strongpoints/placement keys.

const STUB_SRC := """extends "res://autoload/c_bridge.gd"
var places: Array = []
var fixture_mission: Dictionary = {}
func send_place(x, y, building) -> bool:
	places.append([x, y, building])
	return true
func mission() -> Dictionary:
	return fixture_mission
"""

const PROBE_SRC := """extends Node3D
var terrains: Array = []
var frames: Array = []
func set_terrain(t) -> void:
	terrains.append(t)
func set_frame(f) -> void:
	frames.append(f)
"""


static func mentions(v, name: String) -> bool:
	if v is Dictionary:
		for k in v:
			if mentions(k, name) or mentions(v[k], name):
				return true
		return false
	if v is Array:
		for e in v:
			if mentions(e, name):
				return true
		return false
	return str(v).contains(name)


func _idx_by_script(parent: Node, file: String) -> int:
	for i in parent.get_child_count():
		var s = parent.get_child(i).get_script()
		if s != null and (s as Script).resource_path.ends_with(file):
			return i
	return -1


func _script(src: String) -> GDScript:
	var s := GDScript.new()
	s.source_code = src
	s.reload()
	return s


func _press(pos: Vector2, pressed: bool) -> void:
	var ev := InputEventMouseButton.new()
	ev.button_index = MOUSE_BUTTON_LEFT
	ev.pressed = pressed
	ev.position = pos
	root.push_input(ev)
	await process_frame


func _view(fx: GDScript, stub) -> Node:
	var cfg = root.get_node("EraConfig")
	cfg.set_era(cfg.GROUND_ERA_ID)
	var v: Node = (load("res://scenes/tactical_c/tactical_view.tscn") as PackedScene).instantiate()
	root.add_child(v)
	await process_frame
	v.set_process(false)
	await process_frame
	cfg.set_era(cfg.GROUND_ERA_ID)
	var frame: Dictionary = fx.frame().duplicate(true)
	frame["player_faction"] = 0
	frame["map"]["canvas"] = 1000.0
	v.load_frame(frame)
	v.set_terrain(fx.terrain())
	await process_frame
	return v


func _run() -> void:
	_check(not mentions({"a": ["x"]}, "SettlementLayer"), "CONTROL: mentions() finds a name that is absent")
	_check(mentions({"a": ["SettlementLayer"]}, "SettlementLayer"), "CONTROL: mentions() misses a name that is present")
	var fx := _fixture()
	var hs := _load(SCENES + "ground3d.gd")
	if hs == null:
		return

	# add_layer hook on the bare host.
	var host = hs.new()
	root.add_child(host)
	await process_frame
	var has_add: bool = host.has_method("add_layer")
	_check(has_add, "R-193-03 wiring: Ground3D has no add_layer(node) (E1p hook not built)")
	if has_add:
		var probe = _script(PROBE_SRC).new()
		var plain := Node3D.new()
		host.add_layer(probe)
		host.add_layer(plain)
		host.set_terrain(fx.terrain())
		host.set_frame(fx.frame(), fx.mission())
		var par: Node = probe.get_parent()
		_check(par != null and par == host._viewport, "add_layer: probe not added inside the SubViewport")
		if par != null:
			var si: int = _idx_by_script(par, "slope_view.gd")
			var ui: int = _idx_by_script(par, "ground_units.gd")
			var pi: int = probe.get_index()
			_check(si >= 0 and ui >= 0, "CONTROL: SlopesView/Units3D not found by script in the viewport")
			_check(pi > si and pi < ui, "add_layer: probe index %d must be after SlopesView (%d) and before Units3D (%d)" % [pi, si, ui])
		_check(probe.terrains.size() == 1 and probe.frames.size() >= 1, "add_layer: set_terrain/set_frame not fanned (terrains %d, frames %d)" % [probe.terrains.size(), probe.frames.size()])
		_check(plain.get_parent() != null, "CONTROL: a layer without set_terrain/set_frame was not added or was crashed on")

	# The wired view.
	var stub = _script(STUB_SRC).new()
	stub.fixture_mission = fx.mission()
	var SS = load("res://autoload/sim_session.gd")
	SS._bridge = stub
	var v: Node = await _view(fx, stub)
	_check(v.find_child("SettlementLayer", true, false) != null, "E1p: view has no SettlementLayer node")
	_check(v.find_child("StrongpointLayer", true, false) != null, "E1p: view has no StrongpointLayer node")
	var hud := v.find_child("Hud", true, false)
	_check(hud != null and hud.find_child("PlacementUi", true, false) != null, "E1p: PlacementUi is not under Hud")
	var qa: Dictionary = v.qa_state()
	for k in ["settlement_lots", "strongpoints", "placement"]:
		_check(qa.has(k), "E1p: qa_state lacks top-level key %s; keys %s" % [k, qa.keys()])
	for n in ["SettlementLayer", "StrongpointLayer", "PlacementUi"]:
		_check(mentions(qa.get("inventory", {}), n), "E1p: _inventory does not name %s" % n)
	var pl = qa.get("placement", null)
	_check(pl is Dictionary and pl.has("active") and pl.has("building") and pl.has("last_result"), "E1p: placement lacks active/building/last_result: %s" % [pl])
	_check(pl is Dictionary and not bool(pl.get("active", true)), "E1p: placement.active true before any mode change")
	var pui = hud.find_child("PlacementUi", true, false) if hud != null else null
	if pui == null or not pui.has_signal("placement_mode_changed"):
		_check(false, "E1p: PlacementUi missing or lacks placement_mode_changed; click routing not testable")
		return

	# Control first: no placement mode, a click starts a selection box and sends no place.
	var pos := Vector2(900.0, 500.0)
	_check(stub.places.size() == 0, "CONTROL: stub recorded a place before any click")
	await _press(pos, true)
	_check(v._drag_start.x >= 0.0, "CONTROL: without placement mode a left press did not start a selection box")
	await _press(pos, false)
	_check(stub.places.size() == 0, "CONTROL: send_place called without placement mode")

	# Placement mode active.
	pui.placement_mode_changed.emit(true, 2)
	await process_frame
	var pl2 = v.qa_state().get("placement", {})
	_check(pl2 is Dictionary and bool(pl2.get("active", false)) and int(pl2.get("building", -1)) == 2, "E1p: qa_state.placement did not follow placement_mode_changed(true, 2): %s" % [pl2])
	var want: Vector2 = v._to_world(pos)
	await _press(pos, true)
	_check(v._drag_start.x < 0.0, "R-193-03: a click in placement mode opened a selection box")
	await _press(pos, false)
	_check(stub.places.size() == 1, "R-193-03: send_place called %d times for one placement click, expected 1" % stub.places.size())
	if stub.places.size() >= 1:
		var c: Array = stub.places[0]
		_check(Vector2(float(c[0]), float(c[1])).distance_to(want) < 0.01 and int(c[2]) == 2, "R-193-03: send_place got %s, expected (%s, %s, 2) from _to_world" % [c, want.x, want.y])
	SS._bridge = null
	var cfg = root.get_node("EraConfig")
	cfg.set_era(cfg.SPACE_ERA_ID)

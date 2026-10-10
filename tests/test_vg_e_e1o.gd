extends SceneTree

# Visible-game programme lane E1 part b, piece E1o (PlacementUi), docs/northstar/plans/2026-10-07-visible-game-spec.md rev 8.
# Fenced: builders never edit this file. Proves S-193 R-193-03 (placement) and S-218 / R-168-01 (5x5-cell footprint, 100 wu cells).
# The spec names the class, set_projector, placement_mode_changed, place_requested, place_result and last_error; it does not name
# the feeding calls. Pinned here (flagged for the builder brief):
#   * class PlacementUi extends Control, scenes/economy/placement_ui.gd; set_buildings(list: Array) takes the manifest `buildings`
#     entries (dicts with "id"); one Button descendant per entry, in order, text = the entry's "id"; the Button is created in
#     set_buildings (no scene tree entry needed beyond add_child).
#   * set_cursor_world(p: Vector2) moves the ghost; ghost_corners() -> PackedVector2Array: 4 screen points, the projector applied
#     to the world corners (x-250,y-250) (x+250,y-250) (x+250,y+250) (x-250,y+250), in that order; empty while not active.
#   * is_active() -> bool; active_building() -> int (-1 when idle).
#   * place_result(accepted: bool, x: float, y: float, building: int, error: String = "") is a method E1p connects the bridge
#     signal to; last_error() -> String returns the error of the last refusal ("" after success); ghost_is_red() -> bool;
#     ghost_flash_frames() -> int, 20 right after a refusal.
#   * a "(control)" check is a positive control for the detector next to it.

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false
var _events: Array = []

const BLDS := [{"id": "bld_workshop"}, {"id": "bld_dwelling"}, {"id": "bld_hut"}]

const STUB_SRC := """
extends Node
var sent: Array = []
func send_place(x: float, y: float, building: int) -> bool:
	sent.append([x, y, building])
	return true
"""


func _initialize() -> void:
	_run_tests()
	_assert(_completed, "the E1o checks did not run to the end (a script error aborted them)")
	print("\n=== VG E1o PlacementUi Test Results ===")
	print("Passed: %d  Failed: %d" % [_pass_count, _fail_count])
	for m in _fail_msgs:
		print("  FAIL: " + m)
	quit(1 if _fail_count > 0 else 0)


func _assert(cond: bool, msg: String) -> void:
	if cond:
		_pass_count += 1
	else:
		_fail_count += 1
		_fail_msgs.append(msg)


func _buttons(n: Node) -> Array:
	var out: Array = []
	for c in n.get_children():
		if c is Button:
			out.append(c)
		out.append_array(_buttons(c))
	return out


func _on_mode(active: bool, building: int) -> void:
	_events.append(["mode", active, building])


func _on_req(x: float, y: float, building: int) -> void:
	_events.append(["req", x, y, building])


func _run_tests() -> void:
	var stub_s := GDScript.new()
	stub_s.source_code = STUB_SRC
	stub_s.reload()
	var bridge: Node = stub_s.new()
	bridge.name = "CBridge"
	root.add_child(bridge)
	# detector control: the recording stub does record a call
	bridge.send_place(1.0, 2.0, 3)
	_assert(bridge.sent.size() == 1, "control: the stub bridge did not record a direct send_place")
	bridge.sent.clear()

	var scr: Resource = load("res://scenes/economy/placement_ui.gd")
	_assert(scr != null, "E1o: scenes/economy/placement_ui.gd does not exist (PlacementUi is missing)")
	if scr == null:
		_completed = true
		return
	var ui: Control = scr.new()
	root.add_child(ui)
	for m in ["set_buildings", "set_projector", "set_cursor_world", "ghost_corners", "is_active", "active_building", "place_result", "last_error", "ghost_is_red", "ghost_flash_frames"]:
		_assert(ui.has_method(m), "E1o: PlacementUi has no %s()" % m)
	for s in ["placement_mode_changed", "place_requested"]:
		_assert(ui.has_signal(s), "E1o: PlacementUi has no signal %s" % s)
	if not (ui.has_method("set_buildings") and ui.has_signal("placement_mode_changed") and ui.has_method("ghost_corners")):
		_completed = true
		return
	ui.placement_mode_changed.connect(_on_mode)
	ui.place_requested.connect(_on_req)

	# three entries -> three buttons, in order
	ui.set_buildings(BLDS)
	var btns := _buttons(ui)
	_assert(btns.size() == 3, "E1o: %d buttons for 3 buildings" % btns.size())
	if btns.size() != 3:
		_completed = true
		return
	for i in 3:
		_assert(String((btns[i] as Button).text) == String(BLDS[i]["id"]), "E1o: button %d text '%s', expected '%s'" % [i, (btns[i] as Button).text, BLDS[i]["id"]])
	_assert(not ui.is_active() and ui.active_building() == -1, "E1o: active before any click")
	_assert((ui.ghost_corners() as PackedVector2Array).is_empty(), "E1o: ghost drawn while idle")

	# click enters placement mode and emits
	(btns[1] as Button).pressed.emit()
	_assert(ui.is_active() and ui.active_building() == 1, "E1o: click on button 1 did not enter mode for building 1")
	_assert(_events.size() == 1 and _events[0] == ["mode", true, 1], "E1o: expected placement_mode_changed(true, 1), got %s" % [_events])

	# ghost: linear projector world -> screen = p * 0.1 + (5, 7)
	ui.set_projector(func(p: Vector2) -> Vector2: return p * 0.1 + Vector2(5.0, 7.0))
	ui.set_cursor_world(Vector2(1000.0, 2000.0))
	var gc: PackedVector2Array = ui.ghost_corners()
	_assert(gc.size() == 4, "E1o: ghost has %d corners, expected 4" % gc.size())
	if gc.size() == 4:
		var want := [Vector2(750, 1750), Vector2(1250, 1750), Vector2(1250, 2250), Vector2(750, 2250)]
		for i in 4:
			var w: Vector2 = want[i] * 0.1 + Vector2(5.0, 7.0)
			_assert(gc[i].distance_to(w) < 0.01, "E1o: ghost corner %d at %s, expected %s (5x5 cells of 100 wu around the cursor)" % [i, gc[i], w])
	ui.set_cursor_world(Vector2(0.0, 0.0))
	gc = ui.ghost_corners()
	_assert(gc.size() == 4 and gc[0].distance_to(Vector2(-250, -250) * 0.1 + Vector2(5, 7)) < 0.01, "E1o: ghost did not follow the cursor to (0,0)")

	# refusal: red flash 20 frames, last_error shown, mode stays
	_assert(not ui.ghost_is_red(), "E1o: ghost red before any refusal")
	ui.place_result(false, 0.0, 0.0, 1, "blocked")
	_assert(ui.ghost_is_red() and ui.ghost_flash_frames() == 20, "E1o: refusal did not flash red for 20 frames (red=%s frames=%s)" % [ui.ghost_is_red(), ui.ghost_flash_frames()])
	_assert(ui.last_error() == "blocked", "E1o: last_error() is '%s', expected 'blocked'" % ui.last_error())
	_assert(ui.is_active(), "E1o: a refusal ended the mode")

	# success ends the mode
	ui.place_result(true, 0.0, 0.0, 1)
	_assert(not ui.is_active(), "E1o: place_result(true) did not end the mode")
	_assert(_events.back() == ["mode", false, -1] or (_events.back()[0] == "mode" and _events.back()[1] == false), "E1o: no placement_mode_changed(false, ...) after success: %s" % [_events])

	# Escape ends the mode
	(btns[0] as Button).pressed.emit()
	_assert(ui.is_active() and ui.active_building() == 0, "control: re-entering the mode on button 0 failed")
	var esc := InputEventKey.new()
	esc.keycode = KEY_ESCAPE
	esc.pressed = true
	ui._unhandled_input(esc)
	_assert(not ui.is_active(), "E1o: Escape did not end the mode")

	# positive control: a second click on the same button leaves the mode
	(btns[2] as Button).pressed.emit()
	_assert(ui.is_active() and ui.active_building() == 2, "control: click on button 2 did not enter the mode")
	(btns[2] as Button).pressed.emit()
	_assert(not ui.is_active(), "E1o: a second click on the same button did not leave the mode")
	_assert(_events.back()[0] == "mode" and _events.back()[1] == false, "E1o: second click emitted no placement_mode_changed(false, ...)")

	# the panel never calls the bridge
	_assert(bridge.sent.is_empty(), "E1o: the panel called the bridge: %s" % [bridge.sent])
	_completed = true

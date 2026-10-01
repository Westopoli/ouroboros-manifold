extends SceneTree

# Plan item A6, unit A6c (docs/northstar/plans/2026-09-30-mission-plays-plan.md,
# Wave A): the attack-move key of res://scenes/tactical_c/tactical_view.tscn.
# Rules proved: E-13 S-096 R-096-02 (attack-move is an order the player can
# give; the sim side exists as command_attack_move), E-16 S-103 (the view is
# driven by mouse and keyboard), and the QA profile the harness already runs
# (agora projects/ouroboros/qa.toml: "attack_move <target>: presses 'a' then
# clicks there"): key A, then a left click on the ground.
#
# The view is mounted on the live mission (its _ready() self-loads it), so the
# order goes to the real pipe session and the unit ids are real. The order is
# read from qa_state().last_command {ok, kind, units} (written by
# send_command, the one function that talks to the bridge). Visible feedback is
# read as a new visible CanvasItem node in the view's tree after the click,
# never as pixels.
#
# Positive controls: A1 (a plain right-click still sends kind "move": the
# last_command detector sees orders at all), A2 (the node-set detector sees a
# node added by load_frame, so "no feedback node" is a real reading).
#
# Open (reported, not guessed): settings.gd lists the binding as "A + RMB" while
# the QA profile and this file use A then LEFT click; the qa_state last_command
# carries no destination, so the target point is only checked if the scene adds
# "x"/"y" to it; the feedback node's lifetime and colour are not specified by
# any rule here.

const SCENE_PATH := "res://scenes/tactical_c/tactical_view.tscn"

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	await _run_tests()
	print("\n=== Tactical Attack-Move Test Results ===")
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


func _run_tests() -> void:
	var packed = load(SCENE_PATH)
	_assert(packed is PackedScene, "cannot load " + SCENE_PATH)
	if not (packed is PackedScene):
		return
	# One view for all sections: remounting the scene a third time in one
	# process makes its live load fail ("command failed"), which would turn
	# these sections red for a reason that has nothing to do with attack-move.
	var v := await _mount(packed)
	await _test_a_then_click_issues_attack_move_R096_02(v)
	await _test_no_a_no_order_and_mode_is_one_shot_R096_02(v)
	await _test_feedback_node_appears_R096_02(v)


# -- helpers ---------------------------------------------------------------

func _mount(packed: PackedScene) -> Node:
	var v: Node = packed.instantiate()
	get_root().add_child(v)
	await process_frame
	v.set_process(false)  # live stepping would reload frames under the test
	await process_frame
	return v


func _own_ids(v: Node, n: int) -> Array:
	var st: Dictionary = v.qa_state()
	var lf := int(st.get("local_faction", 0))
	var ids: Array = []
	for id in st.get("units", {}):
		if int((st["units"][id] as Dictionary).get("faction", -1)) == lf:
			ids.append(int(id))
	ids.sort()
	return ids.slice(0, n)


func _win(p: Vector2) -> Vector2:
	return get_root().get_final_transform() * p


func _key(code: int, pressed: bool) -> void:
	var e := InputEventKey.new()
	e.keycode = code
	e.physical_keycode = code
	e.pressed = pressed
	Input.parse_input_event(e)


func _click(p: Vector2, button: int) -> void:
	for pressed in [true, false]:
		var e := InputEventMouseButton.new()
		e.button_index = button
		e.pressed = pressed
		e.position = _win(p)
		e.global_position = e.position
		Input.parse_input_event(e)
		await process_frame
	await process_frame


func _press_a() -> void:
	_key(KEY_A, true)
	await process_frame
	_key(KEY_A, false)
	await process_frame


func _last(v: Node) -> Dictionary:
	return v.qa_state().get("last_command", {})


func _canvas_items(n: Node, out: Dictionary = {}) -> Dictionary:
	for c in n.get_children():
		if c is CanvasItem and (c as CanvasItem).is_visible_in_tree():
			out[c.get_instance_id()] = c
		_canvas_items(c, out)
	return out


func _new_nodes(before: Dictionary, after: Dictionary) -> Array:
	var out: Array = []
	for id in after:
		if not before.has(id):
			out.append(after[id])
	return out


# -- A6c-1: A then click -> attack-move order ------------------------------

func _test_a_then_click_issues_attack_move_R096_02(v: Node) -> void:
	var ids := _own_ids(v, 3)
	_assert(ids.size() == 3, "A6c setup: fewer than three own units in the live mission")
	if ids.size() < 3:
		return
	v.qa_set_selected(ids)
	_assert(_last(v).is_empty(), "A6c setup: last_command is not empty on a fresh view: %s" % str(_last(v)))

	# A1 control: a right-click on the ground sends a plain move for the same group.
	await _click(Vector2(700, 400), MOUSE_BUTTON_RIGHT)
	var ctrl := _last(v)
	_assert(ctrl.get("kind") == "move" and int(ctrl.get("units", 0)) == 3,
		"A6c-1 control A1: right-click did not report kind=move for 3 units; last_command=%s" % str(ctrl))

	# Pressing A alone enters the mode; it is not itself an order.
	var kind_before := str(_last(v).get("kind"))
	await _press_a()
	_assert(str(_last(v).get("kind")) == kind_before,
		"A6c-1 R-096-02: pressing A alone sent an order (last_command went from kind=%s to %s)" % [kind_before, str(_last(v))])

	var click_at := Vector2(1100, 600)
	await _click(click_at, MOUSE_BUTTON_LEFT)
	var cmd := _last(v)
	_assert(cmd.get("kind") == "attack_move",
		"A6c-1 R-096-02: A then left-click should send kind=attack_move for the selected group; last_command=%s" % str(cmd))
	_assert(cmd.get("kind") == "attack_move" and cmd.get("ok") == true and int(cmd.get("units", 0)) == 3,
		"A6c-1 R-096-02: the attack-move was not accepted for all 3 selected units; last_command=%s" % str(cmd))
	_assert(int(v.qa_state().get("commands_sent_last_order", 0)) == 1,
		"A6c-1 R-096-02: one group order must be one pipe command, commands_sent_last_order=%s" % str(v.qa_state().get("commands_sent_last_order")))
	if cmd.has("x") and cmd.has("y"):
		var st: Dictionary = v.qa_state()
		var scale := float(st.get("scale", 1.0))
		var cam: Dictionary = st.get("camera", {})
		var wx := (click_at.x - 960.0) / scale + float(cam.get("x", 0.0))
		var wy := (click_at.y - 540.0) / scale + float(cam.get("y", 0.0))
		_assert(absf(float(cmd["x"]) - wx) < 1.0 and absf(float(cmd["y"]) - wy) < 1.0,
			"A6c-1 R-096-02: attack-move target (%s,%s) is not the clicked ground point (%s,%s)" % [str(cmd["x"]), str(cmd["y"]), str(wx), str(wy)])


# -- A6c-2: no A, no order; the mode is spent by the order ------------------

func _test_no_a_no_order_and_mode_is_one_shot_R096_02(v: Node) -> void:
	var ids := _own_ids(v, 3)
	if ids.size() < 3:
		_assert(false, "A6c setup: fewer than three own units in the live mission")
		return
	v.qa_set_selected(ids)

	# A left-click alone selects; it never orders. Baseline: a plain move, so any
	# order a stray click sent would change last_command.
	await _click(Vector2(500, 300), MOUSE_BUTTON_RIGHT)
	var base := _last(v)
	_assert(base.get("kind") == "move", "A6c-2 setup: baseline right-click did not report kind=move: %s" % str(base))
	v.qa_set_selected(ids)
	await _click(Vector2(1100, 600), MOUSE_BUTTON_LEFT)
	_assert(_last(v) == base, "A6c-2 R-096-02: a left-click without A sent an order: last_command went from %s to %s" % [str(base), str(_last(v))])

	# After one attack-move the mode is over: the next right-click is a plain move.
	v.qa_set_selected(ids)
	await _press_a()
	await _click(Vector2(1100, 600), MOUSE_BUTTON_LEFT)
	_assert(_last(v).get("kind") == "attack_move", "A6c-2 setup: A then left-click did not produce attack_move: %s" % str(_last(v)))
	await _click(Vector2(500, 300), MOUSE_BUTTON_RIGHT)
	_assert(_last(v).get("kind") == "move",
		"A6c-2 R-096-02: the attack-move mode stuck; the right-click after it reported %s instead of kind=move" % str(_last(v)))


# -- A6c-3: visible feedback ------------------------------------------------

func _test_feedback_node_appears_R096_02(v: Node) -> void:
	var ids := _own_ids(v, 3)
	if ids.size() < 3:
		_assert(false, "A6c setup: fewer than three own units in the live mission")
		return
	v.qa_set_selected(ids)

	# A2 control: the node-set detector sees a node that load_frame adds.
	var base := _canvas_items(v)
	var frame: Dictionary = v.get("_frame").duplicate(true)
	var extra := {"id": 999999, "faction": int(v.qa_state().get("local_faction", 0)), "type": 0, "tier": 0,
		"x": 100.0, "y": 100.0, "hp": 100.0, "layer": 0, "facing": 0.0, "target": -1, "state": 0}
	frame["units"].append(extra)
	var vis: Dictionary = frame.get("visible", {})
	var lf := str(int(v.qa_state().get("local_faction", 0)))
	vis[lf] = (vis.get(lf, []) as Array) + [999999]
	frame["visible"] = vis
	v.load_frame(frame)
	await process_frame
	_assert(_new_nodes(base, _canvas_items(v)).size() > 0,
		"A6c-3 control A2: loading a frame with one more visible unit added no visible node, so the feedback detector is blind")
	v.qa_set_selected(ids)

	var before := _canvas_items(v)
	await _press_a()
	await _click(Vector2(1100, 600), MOUSE_BUTTON_LEFT)
	_assert(_last(v).get("kind") == "attack_move", "A6c-3 setup: no attack_move was issued: %s" % str(_last(v)))
	var added := _new_nodes(before, _canvas_items(v))
	_assert(added.size() > 0,
		"A6c-3 R-096-02: the attack-move order gave no visible feedback (no new visible node in the view's tree after the click)")

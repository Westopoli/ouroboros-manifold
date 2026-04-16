## Routes keyboard and mouse input to validated command packets.
## Owns selection state, control groups, and active-layer tracking.
## Sends all commands through WsInputSanitizer before TacticalBridge.send_command().
extends Node2D

const _UNIT_PICK_RADIUS := 50.0  # world units — slightly larger than drawn unit

# W S D C E → ability slots 0–4
const _ABILITY_KEYS: Array[int] = [KEY_W, KEY_S, KEY_D, KEY_C, KEY_E]

var selected_uids: Array[int] = []
var active_layer: int = 0         # 0 = ground; cycles 0–4 with Q/Z

var _control_groups: Dictionary = {}  # group(1..10) → Array[int]
var _box_selecting: bool = false
var _box_start_screen: Vector2
var _box_start_world: Vector2

const _BOX_FILL  := Color(0.3, 0.8, 1.0, 0.08)
const _BOX_EDGE  := Color(0.3, 0.8, 1.0, 0.75)
const _BOX_WIDTH := 1.5

@onready var _camera: Camera2D = $"../Camera2D"


func _process(_delta: float) -> void:
	if _box_selecting:
		queue_redraw()


func _draw() -> void:
	if not _box_selecting:
		return
	var current := _to_world(get_viewport().get_mouse_position())
	var rect := Rect2(_box_start_world, Vector2.ZERO).expand(current)
	draw_rect(rect, _BOX_FILL, true)
	draw_rect(rect, _BOX_EDGE, false, _BOX_WIDTH)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		_on_mouse_button(event as InputEventMouseButton)
	elif event is InputEventKey:
		_on_key(event as InputEventKey)


func _on_mouse_button(mb: InputEventMouseButton) -> void:
	match mb.button_index:
		MOUSE_BUTTON_LEFT:
			if mb.pressed:
				_box_start_screen = mb.position
				_box_start_world = _to_world(mb.position)
				_box_selecting = true
			else:
				_finish_selection(mb.position)
		MOUSE_BUTTON_RIGHT:
			if mb.pressed:
				_on_right_click(_to_world(mb.position))


func _on_key(ke: InputEventKey) -> void:
	if not ke.pressed or ke.echo:
		return
	match ke.keycode:
		KEY_A:
			_cmd_attack_move()
		KEY_Q:
			_cycle_layer(1)
		KEY_Z:
			_cycle_layer(-1)
		KEY_X:
			_cmd_layer_hard_transfer()
		KEY_ASCIITILDE, KEY_QUOTELEFT:
			_select_all_army()
		_:
			_handle_digit(ke)
			_handle_ability(ke)


func _handle_digit(ke: InputEventKey) -> void:
	var digit: int = _digit(ke.keycode)
	if digit < 0:
		return
	# Accept ctrl OR meta (Cmd on macOS, Super on Win/Linux). macOS intercepts
	# Ctrl+digit for Mission Control desktop-switching; Cmd reaches us instead.
	var bind_mod: bool = ke.ctrl_pressed or ke.meta_pressed
	if bind_mod:
		_bind_group(digit)
	elif ke.shift_pressed and digit >= 1 and digit <= 5:
		_cmd_layer_preference(digit)
	elif not ke.shift_pressed:
		_recall_group(digit)


func _handle_ability(ke: InputEventKey) -> void:
	var slot: int = _ABILITY_KEYS.find(ke.keycode)
	if slot >= 0:
		_cmd_activate_ability(slot)


# ── Selection ─────────────────────────────────────────────────────────────────

func _finish_selection(release_screen: Vector2) -> void:
	_box_selecting = false
	queue_redraw()
	if release_screen.distance_to(_box_start_screen) < 6.0:
		_click_select(_to_world(release_screen))
	else:
		_box_select(_box_start_world, _to_world(release_screen))


func _click_select(world_pos: Vector2) -> void:
	var best_uid: int = -1
	var best_dist: float = _UNIT_PICK_RADIUS
	for uid: int in TacticalBridge.display_positions:
		if not _is_selectable(uid):
			continue
		var d: float = world_pos.distance_to(_unit_pos(uid))
		if d < best_dist:
			best_dist = d
			best_uid = uid
	selected_uids.clear()
	if best_uid >= 0:
		selected_uids.append(best_uid)


func _box_select(world_a: Vector2, world_b: Vector2) -> void:
	var rect := Rect2(world_a, Vector2.ZERO).expand(world_b)
	selected_uids.clear()
	for uid: int in TacticalBridge.display_positions:
		if _is_selectable(uid) and rect.has_point(_unit_pos(uid)):
			selected_uids.append(uid)


func _select_all_army() -> void:
	selected_uids.clear()
	for uid: int in TacticalBridge.units:
		if TacticalBridge.units[uid].get("selection_eligible", false):
			selected_uids.append(uid)


# ── Control groups ────────────────────────────────────────────────────────────

func _bind_group(group: int) -> void:
	if selected_uids.is_empty():
		return
	_control_groups[group] = selected_uids.duplicate()
	_send({"kind": "control_group_bind", "group": group,
		   "unit_uids": selected_uids.duplicate()})


func _recall_group(group: int) -> void:
	if not _control_groups.has(group):
		return
	var live: Array[int] = []
	for uid: int in _control_groups[group]:
		if TacticalBridge.units.has(uid):
			live.append(uid)
	_control_groups[group] = live
	selected_uids.assign(live)
	_send({"kind": "control_group_recall", "group": group})


# ── Layer ─────────────────────────────────────────────────────────────────────

func _cycle_layer(dir: int) -> void:
	active_layer = clampi(active_layer + dir, 0, 4)


func _cmd_layer_hard_transfer() -> void:
	if selected_uids.is_empty():
		return
	_send({"kind": "layer_hard_transfer", "unit_uids": selected_uids.duplicate(),
		   "target_layer": active_layer})


func _cmd_layer_preference(layer: int) -> void:
	if selected_uids.is_empty():
		return
	_send({"kind": "layer_preference_set", "unit_uids": selected_uids.duplicate(),
		   "preferred_layer": layer})


# ── Movement + combat ─────────────────────────────────────────────────────────

func _on_right_click(world_pos: Vector2) -> void:
	if selected_uids.is_empty():
		return
	_send({"kind": "move", "unit_uids": selected_uids.duplicate(),
		   "target": {"pos": [world_pos.x, world_pos.y], "layer": active_layer}})


func _cmd_attack_move() -> void:
	if selected_uids.is_empty():
		return
	var world_pos := _to_world(get_viewport().get_mouse_position())
	_send({"kind": "attack_move", "unit_uids": selected_uids.duplicate(),
		   "target": {"pos": [world_pos.x, world_pos.y], "layer": active_layer}})


# ── Abilities ─────────────────────────────────────────────────────────────────

func _cmd_activate_ability(slot: int) -> void:
	if selected_uids.is_empty():
		return
	_send({"kind": "activate_ability", "unit_uids": selected_uids.duplicate(),
		   "ability_id": "slot_%d" % slot})


# ── Helpers ───────────────────────────────────────────────────────────────────

func _to_world(screen_pos: Vector2) -> Vector2:
	return get_viewport().get_canvas_transform().affine_inverse() * screen_pos


func _unit_pos(uid: int) -> Vector2:
	var arr: Array = TacticalBridge.display_positions[uid]
	return Vector2(float(arr[0]), float(arr[1]))


func _is_selectable(uid: int) -> bool:
	return TacticalBridge.units.get(uid, {}).get("selection_eligible", false)


func _send(cmd: Dictionary) -> void:
	if WsInputSanitizer.validate(cmd):
		TacticalBridge.send_command(cmd)


func _digit(keycode: int) -> int:
	if keycode == KEY_0:
		return 10
	if keycode >= KEY_1 and keycode <= KEY_9:
		return keycode - KEY_1 + 1
	return -1

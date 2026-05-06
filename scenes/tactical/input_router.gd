## Routes keyboard and mouse input to validated command packets.
## Owns selection state, control groups, and active-layer tracking.
## Sends all commands through WsInputSanitizer before TacticalBridge.send_command().
## _to_world() intersects the mouse ray with the active layer's horizontal plane.
## Selection picking and box-select operate in screen space via Camera3D.unproject_position().
extends Node2D

# Screen-space pick radius in pixels
const _UNIT_PICK_RADIUS := 30.0

const _ABILITY_KEYS: Array[int] = [KEY_W, KEY_S, KEY_D, KEY_C, KEY_E]

const _CATEGORY_TYPES: Dictionary = {
	2: ["raider", "interceptor"],
	3: ["vanguard", "warden"],
	4: ["bombard", "bastion"],
}

var selected_uids: Array[int] = []
var active_layer: int = 0

var _control_groups: Dictionary = {}
var _box_selecting: bool = false
var _box_start_screen: Vector2

const _BOX_FILL  := Color(0.3, 0.8, 1.0, 0.08)
const _BOX_EDGE  := Color(0.3, 0.8, 1.0, 0.75)
const _BOX_WIDTH := 1.5


func _process(_delta: float) -> void:
	if _box_selecting:
		queue_redraw()


func _draw() -> void:
	if not _box_selecting:
		return
	# Draw in screen space — InputRouter sits at (0,0) so local coords = screen coords
	var current := get_viewport().get_mouse_position()
	var rect := Rect2(_box_start_screen, Vector2.ZERO).expand(current)
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
	var bind_mod: bool = ke.ctrl_pressed or ke.meta_pressed
	if bind_mod:
		_bind_group(digit)
	elif ke.shift_pressed and digit >= 1 and digit <= 5:
		_cmd_layer_preference(digit)
	elif not ke.shift_pressed:
		if digit == 1:
			_select_all_army()
		elif digit >= 2 and digit <= 4:
			_select_by_category(digit)
		else:
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
		_click_select(release_screen)
	else:
		_box_select(_box_start_screen, release_screen)


func _click_select(screen_pos: Vector2) -> void:
	var cam := get_viewport().get_camera_3d()
	if not cam:
		return
	var best_uid  := -1
	var best_dist := _UNIT_PICK_RADIUS
	for uid: int in range(TacticalBridge.unit_count):
		if TacticalBridge.display_alive[uid] == 0:
			continue
		if not _is_selectable(uid):
			continue
		var sp := cam.unproject_position(_unit_world_pos(uid))
		var d  := screen_pos.distance_to(sp)
		if d < best_dist:
			best_dist = d
			best_uid  = uid
	selected_uids.clear()
	if best_uid >= 0:
		selected_uids.append(best_uid)


func _box_select(screen_a: Vector2, screen_b: Vector2) -> void:
	var cam := get_viewport().get_camera_3d()
	if not cam:
		return
	var rect := Rect2(screen_a, Vector2.ZERO).expand(screen_b)
	selected_uids.clear()
	for uid: int in range(TacticalBridge.unit_count):
		if TacticalBridge.display_alive[uid] == 0:
			continue
		if _is_selectable(uid):
			var sp := cam.unproject_position(_unit_world_pos(uid))
			if rect.has_point(sp):
				selected_uids.append(uid)


func _select_all_army() -> void:
	selected_uids.clear()
	for uid: int in TacticalBridge.units:
		if TacticalBridge.units[uid].get("selection_eligible", false):
			selected_uids.append(uid)


func _select_by_category(digit: int) -> void:
	var types: Array = _CATEGORY_TYPES.get(digit, [])
	selected_uids.clear()
	for uid: int in TacticalBridge.units:
		var unit: Dictionary = TacticalBridge.units[uid]
		if not unit.get("selection_eligible", false):
			continue
		if unit.get("type", "").to_lower() in types:
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
	var friendly: Array[int] = _friendly_only(selected_uids)
	if friendly.is_empty():
		return
	_send({"kind": "layer_hard_transfer", "unit_uids": friendly,
		   "target_layer": active_layer})


func _cmd_layer_preference(layer: int) -> void:
	var friendly: Array[int] = _friendly_only(selected_uids)
	if friendly.is_empty():
		return
	_send({"kind": "layer_preference_set", "unit_uids": friendly,
		   "preferred_layer": layer})


# ── Movement + combat ─────────────────────────────────────────────────────────

func _on_right_click(world_pos: Vector3) -> void:
	var friendly: Array[int] = _friendly_only(selected_uids)
	if friendly.is_empty():
		return
	_send({"kind": "move", "unit_uids": friendly,
		   "target": {"pos": [world_pos.x, world_pos.z], "layer": active_layer}})


func _cmd_attack_move() -> void:
	var friendly: Array[int] = _friendly_only(selected_uids)
	if friendly.is_empty():
		return
	var world_pos := _to_world(get_viewport().get_mouse_position())
	_send({"kind": "attack_move", "unit_uids": friendly,
		   "target": {"pos": [world_pos.x, world_pos.z], "layer": active_layer}})


# ── Abilities ─────────────────────────────────────────────────────────────────

func _cmd_activate_ability(slot: int) -> void:
	var friendly: Array[int] = _friendly_only(selected_uids)
	if friendly.is_empty():
		return
	_send({"kind": "activate_ability", "unit_uids": friendly,
		   "ability_id": "slot_%d" % slot})


# ── Helpers ───────────────────────────────────────────────────────────────────

func _to_world(screen_pos: Vector2) -> Vector3:
	var cam := get_viewport().get_camera_3d()
	if not cam:
		return Vector3.ZERO
	var origin := cam.project_ray_origin(screen_pos)
	var dir    := cam.project_ray_normal(screen_pos)
	if absf(dir.y) < 0.001:
		return origin
	var layer_y := float(active_layer) * EraConfig.LAYER_HEIGHT
	var t := (layer_y - origin.y) / dir.y
	return origin + dir * t


func _friendly_only(uids: Array[int]) -> Array[int]:
	var result: Array[int] = []
	for uid: int in uids:
		if TacticalBridge.units.get(uid, {}).get("selection_eligible", false):
			result.append(uid)
	return result


func _unit_world_pos(uid: int) -> Vector3:
	var layer: int = TacticalBridge.units.get(uid, {}).get("layer", 0)
	return Vector3(TacticalBridge.display_x[uid], float(layer) * EraConfig.LAYER_HEIGHT, TacticalBridge.display_y[uid])


# See also: scripts/tactical/visibility.gd — fog gate
# Friendly-only gate lifted per stage_11d D5; fog gate remains.
# Visible enemies are selectable for inspection; commands filter to friendlies.
func _is_selectable(uid: int) -> bool:
	return Visibility.is_unit_visible_to_player(uid)


func _send(cmd: Dictionary) -> void:
	if WsInputSanitizer.validate(cmd):
		BugReportManager.log_command(cmd)
		if SimBridge.USE_LIVE_SIM:
			SimBridge.send_command({"type": "command", "command": cmd})
		else:
			TacticalBridge.send_command(cmd)
		TacticalBridge.command_sent.emit(cmd)


func _digit(keycode: int) -> int:
	if keycode == KEY_0:
		return 10
	if keycode >= KEY_1 and keycode <= KEY_9:
		return keycode - KEY_1 + 1
	return -1

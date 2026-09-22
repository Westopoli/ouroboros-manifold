extends Node

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")
const PICK_RADIUS := 30.0

var _root
var _toy
var _selection
var _camera_rig

var box_active := false
var box_start := Vector2.ZERO
var _box_additive := false


func setup(root, toy, selection, camera_rig) -> void:
	_root = root
	_toy = toy
	_selection = selection
	_camera_rig = camera_rig


func mapped_commands() -> Array[String]:
	var cmds: Array[String] = ["click", "shift_click", "box", "bind", "recall", "narrow", "tab_cycle", "move"]
	if QaPlants.is_active("select-all-exists"):
		cmds.append("select_all")
	return cmds


func _unhandled_input(event: InputEvent) -> void:
	if _root == null:
		return
	if event is InputEventMouseButton:
		_on_mouse_button(event)
	elif event is InputEventKey and event.pressed and not event.echo:
		_on_key(event)


func _on_mouse_button(mb: InputEventMouseButton) -> void:
	match mb.button_index:
		MOUSE_BUTTON_LEFT:
			if mb.pressed:
				box_start = mb.position
				box_active = true
				_box_additive = mb.shift_pressed
			else:
				if box_active:
					_finish_box(mb.position)
				box_active = false
		MOUSE_BUTTON_RIGHT:
			if mb.pressed:
				_on_right_click(mb.position)


func _finish_box(release_pos: Vector2) -> void:
	if release_pos.distance_to(box_start) < 6.0:
		_click_at(release_pos, _box_additive)
	else:
		var rect := Rect2(box_start, Vector2.ZERO).expand(release_pos)
		var cam: Camera3D = _camera_rig.get_camera()
		var project := func(uid): return cam.unproject_position(_world_pos(uid))
		_selection.box(rect, project, _toy.get_alive())
	_root._sync_visuals()


func _click_at(pos: Vector2, additive: bool) -> void:
	var uid := _pick_unit(pos)
	if uid < 0:
		if not additive:
			_selection.selected = [] as Array[int]
		return
	if additive:
		_selection.shift_click(uid, _toy.get_alive())
	else:
		_selection.click(uid, _toy.get_alive())


func _pick_unit(pos: Vector2) -> int:
	var cam: Camera3D = _camera_rig.get_camera()
	var alive: Dictionary = _toy.get_alive()
	var best := -1
	var best_d := PICK_RADIUS
	for uid in alive.keys():
		if alive[uid].faction != _selection.PLAYER_FACTION:
			continue
		var sp: Vector2 = cam.unproject_position(_world_pos(uid))
		var d := pos.distance_to(sp)
		if d < best_d:
			best_d = d
			best = uid
	return best


func _world_pos(uid: int) -> Vector3:
	var rec: Dictionary = _toy.get_alive().get(uid, {})
	var p: Vector2 = rec.get("pos", Vector2.ZERO)
	var y: float = 400.0 if rec.get("layer", 1) == 2 else 0.0
	return Vector3(p.x, y, p.y)


func _on_right_click(pos: Vector2) -> void:
	var cam: Camera3D = _camera_rig.get_camera()
	var origin: Vector3 = cam.project_ray_origin(pos)
	var dir: Vector3 = cam.project_ray_normal(pos)
	if absf(dir.y) < 0.001:
		return
	var t: float = -origin.y / dir.y
	var world: Vector3 = origin + dir * t
	_toy.command_move(_selection.selected, Vector2(world.x, world.z))


func _on_key(ke: InputEventKey) -> void:
	match ke.keycode:
		KEY_Q:
			_root.qa_narrow(1)
		KEY_E:
			_root.qa_narrow(2)
		KEY_TAB:
			var cur: int = _selection.focus_layer
			_root.qa_set("focus_layer", 2 if cur == 1 else 1)
		_:
			var digit := _digit(ke.keycode)
			if digit < 0:
				return
			if ke.ctrl_pressed or ke.meta_pressed:
				_root.qa_bind(digit)
			else:
				_root.qa_recall(digit)


func _digit(keycode: int) -> int:
	if keycode == KEY_0:
		return 10
	if keycode >= KEY_1 and keycode <= KEY_9:
		return keycode - KEY_1 + 1
	return -1

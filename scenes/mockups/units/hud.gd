extends CanvasLayer

const KITS_DIR := "res://scenes/mockups/units/kits/"
const SCENARIOS_DIR := "res://scenes/mockups/units/scenarios/"
const DEFAULT_KIT := "greek"
const DEFAULT_SCENARIO := "lineup"
const SCENARIO_NAMES := ["lineup", "mirror_10v10", "bombards_1000", "flank_4v4", "formation_move", "plain_move_under_fire"]

var _sim: ToySim
var _roster: Roster
var _kits: Dictionary = {}
var _scenarios: Dictionary = {}
var _kit_name: String = DEFAULT_KIT
var _scenario_name: String = DEFAULT_SCENARIO
var _seed: int = 11
var _regen_count: int = 0
var _last_tick_avg_ms: float = 0.0
var _playing: bool = false
var _tick_accum: float = 0.0
var _selected: Array = []
var _drag_start: Vector2 = Vector2.ZERO
var _dragging: bool = false
var _log: Array = []

var _world: Node3D
var _camera_rig: Node3D
var _view: Node3D
var _ground: MeshInstance3D

@onready var _scenario_option: OptionButton = $VBoxContainer/ScenarioOption
@onready var _kit_button: Button = $VBoxContainer/KitButton
@onready var _tick_label: Label = $VBoxContainer/TickLabel
@onready var _survivors_label: Label = $VBoxContainer/SurvivorsLabel
@onready var _selected_label: Label = $VBoxContainer/SelectedLabel
@onready var _log_label: Label = $VBoxContainer/LogLabel


func _ready() -> void:
	_world = get_node("../World")
	_camera_rig = get_node("../CameraRig")
	_view = get_node("../World/UnitView")
	_ground = get_node("../World/Ground")

	_load_kits()
	_load_scenarios()
	if not _kits.has(_kit_name) and not _kits.is_empty():
		_kit_name = _kits.keys()[0]
	_roster = _kits.get(_kit_name, Roster.new())
	_view.set_roster(_roster)

	_sim = ToySim.new()
	for name in SCENARIO_NAMES:
		_scenario_option.add_item(name)
	_scenario_option.item_selected.connect(_on_scenario_selected)
	_scenario_option.focus_mode = Control.FOCUS_NONE
	_kit_button.focus_mode = Control.FOCUS_NONE
	_kit_button.pressed.connect(_toggle_kit)

	_regenerate()


func _process(delta: float) -> void:
	if _playing:
		_tick_accum += delta
		var steps := 0
		while _tick_accum >= ToySim.TICK_DT and steps < 40:
			_tick_accum -= ToySim.TICK_DT
			_sim.step()
			steps += 1
		if steps > 0:
			_view.sync(_sim.current_tick, _sim.units)
			_refresh_labels()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_SPACE:
				_playing = not _playing
			KEY_T:
				qa_tick(1)
			KEY_R:
				_regenerate()
			KEY_TAB:
				_toggle_kit()
			KEY_F12:
				_take_screenshot()
	elif event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_LEFT:
			if mb.pressed:
				_drag_start = mb.position
				_dragging = true
			elif _dragging:
				_dragging = false
				_handle_left_release(mb.position)
		elif mb.button_index == MOUSE_BUTTON_RIGHT and mb.pressed:
			_handle_right_click(mb.position)


func _handle_left_release(pos: Vector2) -> void:
	if _drag_start.distance_to(pos) < 6.0:
		var uid := _pick_unit(pos)
		set_selection([] if uid == -1 else [uid])
	else:
		var rect := Rect2(_drag_start, Vector2.ZERO).expand(pos)
		var picked: Array = []
		var cam: Camera3D = _camera_rig.get_camera()
		for u in _sim.units:
			if not u.alive or u.faction != 0:
				continue
			var sp: Vector2 = cam.unproject_position(Vector3(u.pos.x, 0.0, u.pos.y))
			if rect.has_point(sp):
				picked.append(u.uid)
		set_selection(picked)


func _pick_unit(pos: Vector2) -> int:
	var cam: Camera3D = _camera_rig.get_camera()
	var best := -1
	var best_d := 30.0
	for u in _sim.units:
		if not u.alive:
			continue
		var sp: Vector2 = cam.unproject_position(Vector3(u.pos.x, 0.0, u.pos.y))
		var d: float = sp.distance_to(pos)
		if d < best_d:
			best_d = d
			best = u.uid
	return best


func _handle_right_click(pos: Vector2) -> void:
	if _selected.is_empty():
		return
	var enemy_uid := _pick_enemy(pos)
	if enemy_uid != -1:
		_sim.queue_command("attack_target", _selected.duplicate(), null, enemy_uid)
		_log_command("attack_target", _selected, 0.0, 0.0)
		return
	var world := _screen_to_ground(pos)
	var shift := Input.is_key_pressed(KEY_SHIFT)
	var kind := "attack_move" if shift else "move"
	_sim.queue_command(kind, _selected.duplicate(), [world.x, world.y], null)
	_view.add_ping(world, shift)
	_log_command(kind, _selected, world.x, world.y)


func _pick_enemy(pos: Vector2) -> int:
	var cam: Camera3D = _camera_rig.get_camera()
	var best := -1
	var best_d := 30.0
	for u in _sim.units:
		if not u.alive or u.faction == 0:
			continue
		var sp: Vector2 = cam.unproject_position(Vector3(u.pos.x, 0.0, u.pos.y))
		var d: float = sp.distance_to(pos)
		if d < best_d:
			best_d = d
			best = u.uid
	return best


func _screen_to_ground(pos: Vector2) -> Vector2:
	var cam: Camera3D = _camera_rig.get_camera()
	var from := cam.project_ray_origin(pos)
	var dir := cam.project_ray_normal(pos)
	if absf(dir.y) < 0.0001:
		return Vector2(from.x, from.z)
	var t := -from.y / dir.y
	var hit := from + dir * t
	return Vector2(hit.x, hit.z)


func _log_command(kind: String, uids: Array, x: float, z: float) -> void:
	var line := "%s %s -> (%.0f,%.0f)" % [kind, str(uids), x, z]
	_log.append(line)
	if _log.size() > 3:
		_log = _log.slice(_log.size() - 3)
	_refresh_labels()


func set_selection(uids: Array) -> void:
	_selected = uids
	_view.set_selected(uids)
	_refresh_labels()


func _load_kits() -> void:
	var dir := DirAccess.open(KITS_DIR)
	if dir == null:
		return
	dir.list_dir_begin()
	var f := dir.get_next()
	while f != "":
		if not dir.current_is_dir() and f.ends_with(".json"):
			var r := Roster.load_kit(KITS_DIR + f)
			if r.kit_name != "":
				_kits[r.kit_name] = r
		f = dir.get_next()
	dir.list_dir_end()


func _load_scenarios() -> void:
	var dir := DirAccess.open(SCENARIOS_DIR)
	if dir == null:
		return
	dir.list_dir_begin()
	var f := dir.get_next()
	while f != "":
		if not dir.current_is_dir() and f.ends_with(".json"):
			var text := FileAccess.get_file_as_string(SCENARIOS_DIR + f)
			var data = JSON.parse_string(text)
			if typeof(data) == TYPE_DICTIONARY:
				_scenarios[f.get_basename()] = data
		f = dir.get_next()
	dir.list_dir_end()


func _regenerate() -> void:
	if not _scenarios.has(_scenario_name):
		return
	_sim.reset(_roster, _scenarios[_scenario_name], _seed)
	_selected = []
	_view.set_selected([])
	_view.sync(_sim.current_tick, _sim.units)
	_update_ground_color()
	_regen_count += 1
	_playing = false
	_tick_accum = 0.0
	_refresh_labels()


func _toggle_kit() -> void:
	var names: Array = _kits.keys()
	if names.is_empty():
		return
	var idx: int = names.find(_kit_name)
	_set_kit(names[(idx + 1) % names.size()])


func _set_kit(name: String) -> void:
	if not _kits.has(name):
		return
	_kit_name = name
	_roster = _kits[name]
	_sim.roster = _roster
	_view.set_roster(_roster)
	_update_ground_color()
	_regen_count += 1
	_refresh_labels()


func _update_ground_color() -> void:
	if _ground == null or _ground.material_override == null:
		return
	var mat: StandardMaterial3D = _ground.material_override
	mat.albedo_color = Color(String(_roster.palette.get("ground", "#202020")))


func _on_scenario_selected(idx: int) -> void:
	_scenario_name = SCENARIO_NAMES[idx]
	_regenerate()


func _take_screenshot() -> void:
	var dir := DirAccess.open("user://")
	if dir:
		dir.make_dir_recursive("units_manual_screens")
	var img := get_viewport().get_texture().get_image()
	img.save_png("user://units_manual_screens/manual_%d.png" % Time.get_unix_time_from_system())


func _refresh_labels() -> void:
	_tick_label.text = "Tick: %d" % _sim.current_tick
	var alive := _sim.alive_counts()
	_survivors_label.text = "Blue: %d  Red: %d" % [alive.get(0, 0), alive.get(1, 0)]
	_kit_button.text = "Kit: %s" % _kit_name
	if _selected.is_empty():
		_selected_label.text = "Selected: none"
	else:
		var lines: Array = []
		for uid in _selected:
			var u = _sim.get_unit(uid)
			if u != null:
				lines.append("%s f%d hp%.0f" % [u.role, u.faction, u.hp])
		_selected_label.text = "Selected: " + ", ".join(lines)
	_log_label.text = "\n".join(_log)


# --- contract surface used by units_mockup.gd ---

func qa_tick(n: int) -> void:
	var t0 := Time.get_ticks_usec()
	for i in range(n):
		_sim.step()
	var t1 := Time.get_ticks_usec()
	_last_tick_avg_ms = (float(t1 - t0) / 1000.0) / float(max(n, 1))
	_view.sync(_sim.current_tick, _sim.units)
	_refresh_labels()


func qa_command(kind: String, uids: Array, x: float, z: float) -> void:
	match kind:
		"attack_target":
			_sim.queue_command(kind, uids, null, int(x))
		"stop":
			_sim.queue_command(kind, uids, null, null)
		_:
			_sim.queue_command(kind, uids, [x, z], null)
	_log_command(kind, uids, x, z)


func qa_seed(n: int) -> void:
	_seed = n
	_regenerate()


func qa_regenerate() -> void:
	_view.set_roster(_roster)
	_regenerate()


func qa_set(name: String, value) -> void:
	match name:
		"scenario":
			var s := String(value)
			if _scenarios.has(s):
				_scenario_name = s
				var idx: int = SCENARIO_NAMES.find(s)
				if idx != -1:
					_scenario_option.select(idx)
				_regenerate()
		"kit":
			_set_kit(String(value))


func get_sim() -> ToySim:
	return _sim


func get_roster() -> Roster:
	return _roster


func get_view() -> Node3D:
	return _view


func get_camera_rig() -> Node3D:
	return _camera_rig


func get_state_dict() -> Dictionary:
	var alive := _sim.alive_counts()
	var units_dict := {}
	var units_px := {}
	var cam: Camera3D = _camera_rig.get_camera()
	for u in _sim.units:
		units_dict[str(u.uid)] = {
			"role": u.role,
			"faction": u.faction,
			"pos": [u.pos.x, u.pos.y],
			"facing": u.facing,
			"hp": u.hp,
			"alive": u.alive,
		}
		var sp: Vector2 = cam.unproject_position(Vector3(u.pos.x, 0.0, u.pos.y))
		units_px[str(u.uid)] = [sp.x, sp.y]
	var bboxes := {}
	for role in Roster.ROLE_ORDER:
		bboxes[role] = _roster.get_silhouette(role).get("size", [0, 0, 0])
	return {
		"seed": _seed,
		"hash": _sim.compute_hash(),
		"kit": _kit_name,
		"scenario": _scenario_name,
		"tick": _sim.current_tick,
		"alive": {"0": alive.get(0, 0), "1": alive.get(1, 0)},
		"units": units_dict,
		"units_px": units_px,
		"bboxes": bboxes,
		"flashes_active": _view.flashes_active,
		"wrecks_active": _view.wrecks_active,
		"timing_ms": {"tick_avg": _last_tick_avg_ms},
		"regen_count": _regen_count,
	}

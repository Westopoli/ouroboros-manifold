extends Node3D

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")
const FIXTURE_PATH := "res://scenes/mockups/layers/fixtures/map_seed11.json"
const DEMO_PATH := "res://scenes/mockups/layers/fixtures/demo.json"
const PICK_RADIUS_WU := 150.0
const TICK_INTERVAL_S := 1.0 / 20.0

const PLANTS: Array[String] = [
	"instant-transfer",
	"blocked-ignored",
	"cross-layer-full-range",
	"ring-colour-same",
	"no-dimming",
	"wrong-height",
	"seed-ignored",
]

var _sim: ToySim
var _camera_rig: Node3D
var _hud
var _layer_view: LayerView

var _seed: int = 11
var _focus_layer: int = 1
var _selected_uid: int = -1
var _regen_count: int = 0
var _playing: bool = false
var _play_accum: float = 0.0
var _qa_scripted: bool = false
var _demo: Array = []
var _demo_idx: int = 0
var _demo_time: float = 0.0
var _demo_running: bool = false
var _demo_narration: String = ""


func _ready() -> void:
	_camera_rig = get_node("CameraRig")
	_hud = get_node("HUD")
	_layer_view = get_node("World/LayerView")

	_qa_scripted = OS.get_cmdline_user_args().has("--qa-script")

	_sim = ToySim.new()
	_sim.load_fixture(FIXTURE_PATH)
	_sim.generate(_seed)
	_regen_count += 1
	_layer_view.setup(_sim)
	_camera_rig.canvas_size = _sim.canvas_wu
	_load_demo()
	_sync_view()

	# See also: "What Westley reported, verbatim" in the pass-2 brief — the sim
	# never advanced on its own, so ordering a transfer never visibly moved a
	# unit. Interactive launches now run; a QA-scripted launch stays paused so
	# qa_tick keeps deterministic control.
	_playing = not _qa_scripted
	if not _qa_scripted:
		start_demo()


func _process(delta: float) -> void:
	if _playing:
		_play_accum += delta
		while _play_accum >= TICK_INTERVAL_S:
			_play_accum -= TICK_INTERVAL_S
			_sim.step(1)
		_sync_view()
	if _demo_running:
		_demo_time += delta
		while _demo_idx < _demo.size() and _demo_time >= float(_demo[_demo_idx].get("t", 0.0)):
			_run_demo_entry(_demo[_demo_idx])
			_demo_idx += 1
		if _demo_idx >= _demo.size():
			_demo_running = false


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_R:
				reset(_hud.get_seed_value())
			KEY_T:
				step_ticks(1)
			KEY_SPACE:
				toggle_play()
			KEY_TAB:
				cycle_focus_layer()
			KEY_1:
				set_focus_layer_direct(1)
			KEY_2:
				set_focus_layer_direct(2)
			KEY_Q:
				transfer_selected(1)
			KEY_E:
				transfer_selected(2)
			KEY_D:
				start_demo()
		return

	if event is InputEventMouseButton and event.pressed:
		var mb := event as InputEventMouseButton
		var world: Variant = _ground_point(mb.position)
		if world == null:
			return
		if mb.button_index == MOUSE_BUTTON_LEFT:
			_select_at(world)
		elif mb.button_index == MOUSE_BUTTON_RIGHT:
			if _selected_uid >= 0:
				qa_move(_selected_uid, world.x, world.z)


func _ground_point(screen_pos: Vector2) -> Variant:
	var cam: Camera3D = _camera_rig.get_camera()
	var origin: Vector3 = cam.project_ray_origin(screen_pos)
	var dir: Vector3 = cam.project_ray_normal(screen_pos)
	if absf(dir.y) < 0.0001:
		return null
	var t := -origin.y / dir.y
	if t < 0.0:
		return null
	return origin + dir * t


func _select_at(world: Vector3) -> void:
	var best_uid := -1
	var best_dist := PICK_RADIUS_WU
	for uid in _sim.units.keys():
		var u: Dictionary = _sim.units[uid]
		if u.faction != 0:
			continue
		var d: float = Vector2(u.pos.x, u.pos.y).distance_to(Vector2(world.x, world.z))
		if d < best_dist:
			best_dist = d
			best_uid = uid
	if best_uid >= 0:
		qa_select(best_uid)


func _sync_view() -> void:
	_layer_view.set_focus_layer(_focus_layer)
	_layer_view.set_selected(_selected_uid)
	_layer_view.refresh()
	if _hud != null:
		_hud.refresh()


func get_sim() -> ToySim:
	return _sim


func get_layer_view() -> LayerView:
	return _layer_view


func get_camera_rig() -> Node3D:
	return _camera_rig


func get_hud():
	return _hud


func get_focus_layer() -> int:
	return _focus_layer


func get_selected_uid() -> int:
	return _selected_uid


func get_seed() -> int:
	return _seed


func get_regen_count() -> int:
	return _regen_count


func is_playing() -> bool:
	return _playing


func cycle_focus_layer() -> void:
	set_focus_layer_direct(2 if _focus_layer == 1 else 1)


func set_focus_layer_direct(n: int) -> void:
	_focus_layer = clampi(n, 1, 2)
	_sync_view()


func reset(seed_n: int) -> void:
	_seed = seed_n
	_sim.generate(_seed)
	_regen_count += 1
	_selected_uid = -1
	_playing = false
	_play_accum = 0.0
	_layer_view.rebuild_blocked_patch()
	_sync_view()


func step_ticks(n: int) -> void:
	_sim.step(n)
	_sync_view()


func toggle_play() -> void:
	_playing = not _playing
	_play_accum = 0.0


func transfer_selected(layer: int) -> void:
	var uids: Array = _targets_for_command()
	if uids.is_empty():
		return
	if not _playing:
		toggle_play()
	for uid in uids:
		qa_transfer(uid, layer)


func _targets_for_command() -> Array:
	if _selected_uid >= 0:
		return [_selected_uid]
	var out: Array = []
	for uid in _sim.units.keys():
		if _sim.units[uid].faction == 0:
			out.append(uid)
	out.sort()
	return out


func has_selection() -> bool:
	return _selected_uid >= 0


func get_demo_narration() -> String:
	return _demo_narration


func _load_demo() -> void:
	var text := FileAccess.get_file_as_string(DEMO_PATH)
	var parsed = JSON.parse_string(text)
	_demo = parsed if typeof(parsed) == TYPE_ARRAY else []


func start_demo() -> void:
	reset(_seed)
	_playing = true
	_demo_idx = 0
	_demo_time = 0.0
	_demo_running = not _demo.is_empty()
	_demo_narration = ""


func _run_demo_entry(entry: Dictionary) -> void:
	if entry.has("narrate"):
		_demo_narration = String(entry.narrate)
	if entry.has("call"):
		var method: String = entry.call
		var args: Array = entry.get("args", [])
		callv(method, args)


func qa_state() -> Dictionary:
	var units_out := {}
	var units_px := {}
	var rings := {}
	var cam: Camera3D = _camera_rig.get_camera()
	for uid in _sim.units.keys():
		var u: Dictionary = _sim.units[uid]
		var transition_out = null
		if u.transition != null:
			transition_out = {"to": u.transition.to, "ticks_left": u.transition.ticks_left}
		units_out[str(uid)] = {
			"type": u.type,
			"layer": u.layer,
			"pos": [u.pos.x, u.pos.y],
			"transition": transition_out,
			"pending": u.pending,
		}
		var h := _layer_view.unit_height(u)
		var wp := Vector3(u.pos.x, h, u.pos.y)
		var px: Vector2 = cam.unproject_position(wp) if cam != null else Vector2.ZERO
		units_px[str(uid)] = [px.x, px.y]
		if u.faction == 0:
			rings[str(uid)] = "#" + _layer_view.ring_color(u).to_html(false)

	var pan: Vector2 = _camera_rig.get_pan()
	return {
		"seed": _seed,
		"hash": _sim.compute_hash(),
		"tick": _sim.tick,
		"focus_layer": _focus_layer,
		"layer_height_wu": LayerView.LAYER_HEIGHT,
		"units": units_out,
		"units_px": units_px,
		"visible_enemy_uids": _sim.visible_enemy_uids(),
		"rings": rings,
		"ring_px": _layer_view.sensor_ring_px(cam),
		"timing_ms": {"tick_avg": _sim.tick_avg_ms()},
		"regen_count": _regen_count,
		"selected_uid": _selected_uid,
		"camera": {"x": pan.x, "z": pan.y},
		"canvas_px": [get_viewport().get_visible_rect().size.x, get_viewport().get_visible_rect().size.y],
		"playing": _playing,
		"demo_narration": _demo_narration,
	}


func qa_plant(id: String) -> bool:
	if not PLANTS.has(id):
		return false
	QaPlants.activate(id)
	_sim.generate(_seed)
	_regen_count += 1
	_layer_view.rebuild_blocked_patch()
	_sync_view()
	return true


func qa_seed(n: int) -> void:
	reset(n)
	_hud.set_seed_value(n)


func qa_set(name: String, value) -> void:
	if name == "focus_layer":
		set_focus_layer_direct(int(value))


func qa_camera(height: float, x: float, z: float) -> void:
	_camera_rig.pan_to(Vector3(x, 0.0, z))
	_camera_rig.set_height(height)


func qa_tick(n: int) -> void:
	step_ticks(n)


func qa_transfer(uid: int, layer: int) -> void:
	_sim.transfer(uid, layer)
	_sync_view()


func qa_move(uid: int, x: float, z: float) -> void:
	_sim.move(uid, x, z)
	_sync_view()


func qa_select(uid: int) -> void:
	_selected_uid = uid
	_sync_view()

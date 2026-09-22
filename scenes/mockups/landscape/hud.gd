extends CanvasLayer

const KITS_DIR := "res://scenes/mockups/landscape/kits/"
const DEFAULT_CANVAS := 16000.0
const DEFAULT_KIT := "greek"
const SCREENSHOT_DIR := "res://docs/northstar/research/landscape_design/mockup/"
const BAND_HEIGHTS := {"micro": 1000.0, "tactical": 3000.0, "map": 20000.0}

var _world: Node3D
var _camera_rig: Node3D
var _generated: Node3D
var _field_map: FieldMap

var _kits: Dictionary = {}
var _kit_name: String = DEFAULT_KIT
var _seed: int = 11
var _canvas: float = DEFAULT_CANVAS
var _stability: float = 60.0

@onready var _seed_label: Label = $VBoxContainer/SeedLabel
@onready var _seed_spinbox: SpinBox = $VBoxContainer/SeedSpinBox
@onready var _band_label: Label = $VBoxContainer/BandLabel
@onready var _regenerate_button: Button = $VBoxContainer/RegenerateButton
@onready var _kit_toggle_button: Button = $VBoxContainer/KitToggleButton
@onready var _piece_count_label: Label = $VBoxContainer/PieceCountLabel
@onready var _skeleton_label: Label = $VBoxContainer/SkeletonLabel
@onready var _timing_label: Label = $VBoxContainer/TimingLabel
@onready var _stability_slider: HSlider = $VBoxContainer/StabilitySlider
@onready var _map_view: Control = $MapView


func _ready() -> void:
	_world = get_node("../World")
	_camera_rig = get_node("../CameraRig")

	# A container we own and wipe wholesale, instead of diffing World's children: World also
	# holds WorldEnvironment/DirectionalLight3D that must survive every regen, and matching by
	# name/type would be fragile as the placer's node vocabulary grows.
	_generated = Node3D.new()
	_generated.name = "Generated"
	_world.add_child(_generated)

	_load_kits()
	if not _kits.has(_kit_name):
		_kit_name = _kits.keys()[0] if not _kits.is_empty() else _kit_name

	_seed = int(_seed_spinbox.value)
	_stability = _stability_slider.value
	_kit_toggle_button.text = "Kit: %s" % _kit_name
	_band_label.text = "Band: %s" % _camera_rig.get_current_band()

	_camera_rig.band_changed.connect(_on_band_changed)
	_regenerate_button.pressed.connect(_on_regenerate_pressed)
	_kit_toggle_button.pressed.connect(_on_kit_toggle_pressed)
	# Regenerate on release, not on every drag tick (Westley: dragging "slows everything down
	# for a few seconds" because value_changed fired a full regenerate per pixel of drag).
	_stability_slider.drag_ended.connect(_on_stability_drag_ended)

	_regenerate()

	# Batch capture for the review screenshots (docs/northstar/research/landscape_design/
	# mockup/): run non-interactively via `... scenes/mockups/landscape/landscape_mockup.tscn
	# -- --screenshot-batch`, since headless mode has no real renderer to capture from.
	if OS.get_cmdline_user_args().has("--screenshot-batch"):
		_run_screenshot_batch()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_R:
			_on_regenerate_pressed()
		elif event.keycode == KEY_TAB:
			_on_kit_toggle_pressed()
		elif event.keycode == KEY_F12:
			_take_screenshot("manual_%d" % Time.get_unix_time_from_system())


func _load_kits() -> void:
	var dir := DirAccess.open(KITS_DIR)
	if dir == null:
		return
	dir.list_dir_begin()
	var file_name := dir.get_next()
	while file_name != "":
		if not dir.current_is_dir() and file_name.ends_with(".json"):
			var kit := Placer.load_kit(KITS_DIR + file_name)
			var kit_name: String = kit.get("name", "")
			if kit_name != "":
				_kits[kit_name] = kit
		file_name = dir.get_next()
	dir.list_dir_end()


func _regenerate() -> void:
	for child in _generated.get_children():
		child.free()

	var t0 := Time.get_ticks_usec()
	var field_map := FieldMap.new()
	field_map.generate(_seed, _canvas, _stability)
	var t1 := Time.get_ticks_usec()

	var kit: Dictionary = _kits[_kit_name]

	var ground_builder := GroundBuilder.new()
	_generated.add_child(ground_builder.build(field_map, kit))
	var t2 := Time.get_ticks_usec()

	var placer := Placer.new()
	var result := placer.place(field_map, kit, _generated)
	var t3 := Time.get_ticks_usec()

	_field_map = field_map
	_seed_label.text = "Seed: %d" % _seed
	_piece_count_label.text = "Pieces: %d" % result.total
	_skeleton_label.text = "Skeleton: %s" % field_map.skeleton_name
	var gen_ms := (t1 - t0) / 1000.0
	var ground_ms := (t2 - t1) / 1000.0
	var placer_ms := (t3 - t2) / 1000.0
	_timing_label.text = "Gen: %dms Ground: %dms Placer: %dms (total %dms)" % [gen_ms, ground_ms, placer_ms, gen_ms + ground_ms + placer_ms]
	print("regenerate timing: gen=%.1fms ground=%.1fms placer=%.1fms total=%.1fms" % [gen_ms, ground_ms, placer_ms, gen_ms + ground_ms + placer_ms])
	_map_view.set_field_map(field_map)


func _on_regenerate_pressed() -> void:
	_seed = int(_seed_spinbox.value)
	_regenerate()


func _on_kit_toggle_pressed() -> void:
	var kit_names: Array = _kits.keys()
	var idx: int = kit_names.find(_kit_name)
	_kit_name = kit_names[(idx + 1) % kit_names.size()]
	_kit_toggle_button.text = "Kit: %s" % _kit_name
	_regenerate()


func _on_stability_drag_ended(value_changed: bool) -> void:
	if not value_changed:
		return
	_stability = _stability_slider.value
	_regenerate()


func _on_band_changed(band: String) -> void:
	_band_label.text = "Band: %s" % band


func _find_objective_pos() -> Vector3:
	for n in _field_map.nodes:
		if n.type == "objective":
			return Vector3(n.pos.x, 0.0, n.pos.y)
	return Vector3(_field_map.canvas * 0.5, 0.0, _field_map.canvas * 0.5)


# Micro band sits low enough that aiming at the objective drops the camera inside the
# dense city geometry (colonnades, walls). A gate crossing puts it in open ground with a
# wall and units to read at human scale instead, matching the brief's "near a gate" framing
# -- but standing exactly ON the gate point put the camera inside the (now correctly sized)
# gate_arch mesh itself. Stand 60% of the way from the nearest staging node toward the gate
# instead, so the shot is just outside it looking in.
func _find_gate_pos() -> Vector3:
	var gate_point: Vector2 = Vector2.ZERO
	var found := false
	for c in _field_map.crossings:
		if c.kind == "gate":
			gate_point = c.point
			found = true
			break
	if not found:
		return _find_objective_pos()

	var staging_point: Vector2 = gate_point
	var best_d := INF
	for n in _field_map.nodes:
		if n.type == "staging":
			var d: float = n.pos.distance_to(gate_point)
			if d < best_d:
				best_d = d
				staging_point = n.pos
	var approach: Vector2 = staging_point.lerp(gate_point, 0.6)
	return Vector3(approach.x, 0.0, approach.y)


func _take_screenshot(file_name: String) -> void:
	var dir := DirAccess.open("res://")
	dir.make_dir_recursive("docs/northstar/research/landscape_design/mockup")
	var img := get_viewport().get_texture().get_image()
	img.save_png(SCREENSHOT_DIR + file_name + ".png")


func _run_screenshot_batch() -> void:
	for kit_name in _kits.keys():
		for shot_seed in [11, 12]:
			_kit_name = kit_name
			_seed = shot_seed
			_seed_spinbox.value = shot_seed
			_kit_toggle_button.text = "Kit: %s" % _kit_name
			_regenerate()
			var objective_pos := _find_objective_pos()
			var gate_pos := _find_gate_pos()
			for band in ["micro", "tactical", "map"]:
				_camera_rig.pan_to(gate_pos if band == "micro" else objective_pos)
				_camera_rig.set_height(BAND_HEIGHTS[band])
				await get_tree().process_frame
				await get_tree().process_frame
				await RenderingServer.frame_post_draw
				_take_screenshot("%s_%s_seed%d" % [kit_name, band, shot_seed])

	_kit_name = "greek"
	_seed = 11
	_seed_spinbox.value = 11
	_kit_toggle_button.text = "Kit: %s" % _kit_name
	for shot_stability in [20.0, 90.0]:
		_stability = shot_stability
		_regenerate()
		_camera_rig.pan_to(_find_objective_pos())
		_camera_rig.set_height(BAND_HEIGHTS["tactical"])
		await get_tree().process_frame
		await get_tree().process_frame
		await RenderingServer.frame_post_draw
		_take_screenshot("greek_tactical_seed11_stability%d" % int(shot_stability))

	get_tree().quit()

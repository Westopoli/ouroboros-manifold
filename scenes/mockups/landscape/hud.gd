extends CanvasLayer

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")
const KITS_DIR := "res://scenes/mockups/landscape/kits/"
const DEFAULT_CANVAS := 24000.0
const CANVAS_OPTIONS := [16000.0, 24000.0, 32000.0]
const DEFAULT_KIT := "greek"
const SPACE_KIT := "space"
const DEFAULT_DENSITY := 35.0
const MAX_DENSITY := 90.0
const GAP_RANGE := Vector2(200.0, 3000.0)
const SPREAD_RANGE := Vector2(0.0, 1.0)
const SWING_RANGE := Vector2(0.0, 1.2)
const PLATE_RANGE := Vector2(800.0, 3200.0)
const SCREENSHOT_DIR := "res://docs/northstar/research/landscape_design/mockup/pass3/"
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
var _density: float = DEFAULT_DENSITY
var _layer_gap: float = SpaceFieldMap.LAYER_GAP_WU
var _plate_cell: float = SpaceFieldMap.PLATE_CELL_WU
var _size_spread: float = SpaceFieldMap.SIZE_SPREAD
var _density_swing: float = SpaceFieldMap.DENSITY_SWING
var _shared_density := true
var _focus_layer: int = 0
var _show_crossings := false
var _piece_total: int = 0
var _timing_ms: Dictionary = {}
var _regen_count: int = 0

@onready var _seed_label: Label = $VBoxContainer/SeedLabel
@onready var _seed_spinbox: SpinBox = $VBoxContainer/SeedSpinBox
@onready var _band_label: Label = $VBoxContainer/BandLabel
@onready var _regenerate_button: Button = $VBoxContainer/RegenerateButton
@onready var _kit_toggle_button: Button = $VBoxContainer/KitToggleButton
@onready var _piece_count_label: Label = $VBoxContainer/PieceCountLabel
@onready var _canvas_label: Label = $VBoxContainer/CanvasLabel
@onready var _canvas_toggle_button: Button = $VBoxContainer/CanvasToggleButton
@onready var _timing_label: Label = $VBoxContainer/TimingLabel
@onready var _stability_slider: HSlider = $VBoxContainer/StabilitySlider
@onready var _stability_label: Label = $VBoxContainer/StabilityLabel
@onready var _map_view: Control = $MapView

# Space-kit controls, built here so the scene file stays as it is.
var _density_label: Label
var _density_slider: HSlider
var _gap_label: Label
var _gap_slider: HSlider
var _plate_label: Label
var _plate_slider: HSlider
var _spread_label: Label
var _spread_slider: HSlider
var _swing_label: Label
var _swing_slider: HSlider
var _shared_button: Button
var _top_down_button: Button
var _focus_label: Label
var _solo_label: Label
var _space_stats_label: Label


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
	_canvas_toggle_button.text = "Canvas: %d" % int(_canvas)
	_band_label.text = "Band: %s" % _camera_rig.get_current_band()

	_camera_rig.band_changed.connect(_on_band_changed)
	_regenerate_button.pressed.connect(_on_regenerate_pressed)
	_kit_toggle_button.pressed.connect(_on_kit_toggle_pressed)
	_canvas_toggle_button.pressed.connect(_on_canvas_toggle_pressed)
	# Regenerate on release, not on every drag tick (Westley: dragging "slows everything down
	# for a few seconds" because value_changed fired a full regenerate per pixel of drag).
	_stability_slider.drag_ended.connect(_on_stability_drag_ended)
	_build_space_controls()

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
		elif _kit_name == SPACE_KIT and event.keycode >= KEY_0 and event.keycode <= KEY_5:
			_set_focus(event.keycode - KEY_0)
		elif _kit_name == SPACE_KIT and event.keycode == KEY_C:
			_show_crossings = not _show_crossings
			_apply_view()
			_update_space_controls(_field_map)
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
	if QaPlants.is_active("regen-stall"):
		OS.delay_msec(3000)
	var is_space := _kit_name == SPACE_KIT
	var field_map: FieldMap
	if is_space:
		var space_map := SpaceFieldMap.new()
		space_map.plate_cell_wu = _plate_cell
		space_map.layer_gap_wu = _layer_gap
		space_map.size_spread = _size_spread
		space_map.density_swing = _density_swing
		space_map.shared_density = _shared_density
		field_map = space_map
	else:
		field_map = FieldMap.new()
	var gen_seed := 11 if QaPlants.is_active("seed-ignored") else _seed
	field_map.generate(gen_seed, _canvas, _density if is_space else _stability)
	var t1 := Time.get_ticks_usec()

	var kit: Dictionary = _kits[_kit_name]

	var ground_builder := GroundBuilder.new()
	var ground := ground_builder.build(field_map, kit)
	if ground != null:
		_generated.add_child(ground)
	var t2 := Time.get_ticks_usec()

	var placer := Placer.new()
	var result := placer.place(field_map, kit, _generated)
	if is_space:
		_apply_view()
	var t3 := Time.get_ticks_usec()

	_field_map = field_map
	_camera_rig.field_map = field_map
	_seed_label.text = "Seed: %d" % _seed
	_piece_count_label.text = "Pieces: %d" % result.total
	_piece_total = result.total
	_canvas_label.text = "Canvas: %d" % int(field_map.canvas)
	var gen_ms := (t1 - t0) / 1000.0
	var ground_ms := (t2 - t1) / 1000.0
	var placer_ms := (t3 - t2) / 1000.0
	_timing_ms = {"gen": gen_ms, "ground": ground_ms, "placer": placer_ms, "total": gen_ms + ground_ms + placer_ms}
	_timing_label.text = "Gen: %dms Ground: %dms Placer: %dms (total %dms)" % [gen_ms, ground_ms, placer_ms, gen_ms + ground_ms + placer_ms]
	print("regenerate timing: gen=%.1fms ground=%.1fms placer=%.1fms total=%.1fms" % [gen_ms, ground_ms, placer_ms, gen_ms + ground_ms + placer_ms])
	_map_view.set_field_map(field_map)
	_update_space_controls(field_map)
	_regen_count += 1


func _on_regenerate_pressed() -> void:
	_seed = int(_seed_spinbox.value)
	_regenerate()


func _on_kit_toggle_pressed() -> void:
	var kit_names: Array = _kits.keys()
	var idx: int = kit_names.find(_kit_name)
	_kit_name = kit_names[(idx + 1) % kit_names.size()]
	_kit_toggle_button.text = "Kit: %s" % _kit_name
	_regenerate()


func _on_canvas_toggle_pressed() -> void:
	var idx: int = CANVAS_OPTIONS.find(_canvas)
	_canvas = CANVAS_OPTIONS[(idx + 1) % CANVAS_OPTIONS.size()] if idx != -1 else CANVAS_OPTIONS[0]
	_canvas_toggle_button.text = "Canvas: %d" % int(_canvas)
	_camera_rig.canvas_size = _canvas
	_regenerate()


func _on_stability_drag_ended(value_changed: bool) -> void:
	if not value_changed:
		return
	_stability = _stability_slider.value
	_regenerate()


func _on_density_drag_ended(value_changed: bool) -> void:
	if not value_changed:
		return
	_density = _density_slider.value
	_regenerate()


func _build_space_controls() -> void:
	var box: VBoxContainer = $VBoxContainer
	_density_label = Label.new()
	_density_label.name = "DensityLabel"
	_density_slider = _make_slider("DensitySlider", 0.0, MAX_DENSITY, 1.0, _density)
	_gap_label = Label.new()
	_gap_label.name = "GapLabel"
	_gap_slider = _make_slider("GapSlider", GAP_RANGE.x, GAP_RANGE.y, 100.0, _layer_gap)
	_plate_label = Label.new()
	_plate_label.name = "PlateLabel"
	_plate_slider = _make_slider("PlateSlider", PLATE_RANGE.x, PLATE_RANGE.y, 100.0, _plate_cell)
	_spread_label = Label.new()
	_spread_label.name = "SpreadLabel"
	_spread_slider = _make_slider("SpreadSlider", SPREAD_RANGE.x, SPREAD_RANGE.y, 0.05, _size_spread)
	_swing_label = Label.new()
	_swing_label.name = "SwingLabel"
	_swing_slider = _make_slider("SwingSlider", SWING_RANGE.x, SWING_RANGE.y, 0.05, _density_swing)
	_shared_button = Button.new()
	_shared_button.name = "SharedDensityButton"
	_top_down_button = Button.new()
	_top_down_button.name = "TopDownButton"
	_focus_label = Label.new()
	_focus_label.name = "FocusLabel"
	_solo_label = Label.new()
	_solo_label.name = "SoloLabel"
	_space_stats_label = Label.new()
	_space_stats_label.name = "SpaceStatsLabel"
	for control in [_density_label, _density_slider, _gap_label, _gap_slider, _plate_label, _plate_slider, _spread_label, _spread_slider, _swing_label, _swing_slider, _shared_button, _top_down_button, _focus_label, _solo_label, _space_stats_label]:
		box.add_child(control)
	# Same debounce as stability: regenerate on release, not per drag tick.
	_density_slider.drag_ended.connect(_on_density_drag_ended)
	_density_slider.value_changed.connect(_on_density_value_changed)
	_gap_slider.drag_ended.connect(_on_gap_drag_ended)
	_gap_slider.value_changed.connect(_on_gap_value_changed)
	_plate_slider.drag_ended.connect(_on_plate_drag_ended)
	_plate_slider.value_changed.connect(_on_plate_value_changed)
	_spread_slider.drag_ended.connect(_on_spread_drag_ended)
	_spread_slider.value_changed.connect(_on_spread_value_changed)
	_swing_slider.drag_ended.connect(_on_swing_drag_ended)
	_swing_slider.value_changed.connect(_on_swing_value_changed)
	_shared_button.pressed.connect(_on_shared_pressed)
	_top_down_button.pressed.connect(_on_top_down_pressed)
	_on_density_value_changed(_density)
	_on_gap_value_changed(_layer_gap)
	_on_plate_value_changed(_plate_cell)
	_on_spread_value_changed(_size_spread)
	_on_swing_value_changed(_density_swing)
	_refresh_shared_text()
	_refresh_top_down_text()
	_set_focus(_focus_layer)


func _make_slider(slider_name: String, low: float, high: float, step: float, value: float) -> HSlider:
	var slider := HSlider.new()
	slider.name = slider_name
	slider.custom_minimum_size = Vector2(160, 0)
	slider.min_value = low
	slider.max_value = high
	slider.step = step
	slider.value = value
	return slider


func _on_density_value_changed(value: float) -> void:
	_density_label.text = "Density: %d%% blocked" % int(value)


func _on_gap_value_changed(value: float) -> void:
	_gap_label.text = "Layer gap: %d wu" % int(value)


func _on_plate_value_changed(value: float) -> void:
	_plate_label.text = "Plate size: %d wu" % int(value)


func _on_spread_value_changed(value: float) -> void:
	_spread_label.text = "Size spread: %.2f" % value


func _on_swing_value_changed(value: float) -> void:
	_swing_label.text = "Density swing: %.2f" % value


func _on_spread_drag_ended(value_changed: bool) -> void:
	if not value_changed:
		return
	_size_spread = _spread_slider.value
	_regenerate()


func _on_swing_drag_ended(value_changed: bool) -> void:
	if not value_changed:
		return
	_density_swing = _swing_slider.value
	_regenerate()


func _on_shared_pressed() -> void:
	_set_shared_density(not _shared_density)


func _set_shared_density(on: bool) -> void:
	_shared_density = on
	_refresh_shared_text()
	_regenerate()


func _refresh_shared_text() -> void:
	_shared_button.text = "Shared density: %s" % ("on" if _shared_density else "off")


func _on_gap_drag_ended(value_changed: bool) -> void:
	if not value_changed:
		return
	_layer_gap = _gap_slider.value
	_regenerate()


func _on_plate_drag_ended(value_changed: bool) -> void:
	if not value_changed:
		return
	_plate_cell = _plate_slider.value
	_regenerate()


func _on_top_down_pressed() -> void:
	_set_top_down(not _camera_rig.is_top_down())


func _set_top_down(on: bool) -> void:
	_camera_rig.set_top_down(on)
	_refresh_top_down_text()
	_apply_view()


func _refresh_top_down_text() -> void:
	_top_down_button.text = "Top-down: %s" % ("on" if _camera_rig.is_top_down() else "off")


func _set_focus(layer: int) -> void:
	_focus_layer = layer
	_focus_label.text = "Focus: all" if layer == 0 else "Focus: layer %d" % layer
	_apply_view()


func _apply_view() -> void:
	var top_down: bool = _camera_rig.is_top_down()
	Placer.apply_layer_view(_generated, _focus_layer, top_down, _show_crossings)
	_solo_label.text = "Solo: layer %d" % _focus_layer
	_solo_label.visible = _kit_name == SPACE_KIT and top_down and _focus_layer != 0


func _update_space_controls(field_map: FieldMap) -> void:
	var is_space := field_map is SpaceFieldMap
	_stability_label.visible = not is_space
	_stability_slider.visible = not is_space
	for control in [_density_label, _density_slider, _gap_label, _gap_slider, _plate_label, _plate_slider, _spread_label, _spread_slider, _swing_label, _swing_slider, _shared_button]:
		control.visible = is_space
	_focus_label.visible = is_space
	_solo_label.visible = is_space and _camera_rig.is_top_down() and _focus_layer != 0
	_space_stats_label.visible = is_space
	if not is_space:
		return
	var blocked: Array = []
	for stat in field_map.layer_stats:
		blocked.append("%d%%" % int(round(stat.blocked * 100.0)))
	var plates: Array = field_map.plates_per_layer.map(func(c): return str(c))
	_space_stats_label.text = "Blocked per layer: %s\nPlates per layer: %s\nPlates dropped: %d clearing, %d reachability  Rubble: %d%%\nPockets filled: %d  Still unreachable: %d  Crossings (8 to 50 cells): %d, marks %s (C)\nCells blocked on two neighbouring layers: %s" % [
		" ".join(blocked), " ".join(plates) if not plates.is_empty() else "-", field_map.plates_cleared, field_map.tunnels_cut,
		int(round(field_map.rubble_share * 100.0)), field_map.pockets_filled,
		field_map.regions_unreachable_after, field_map.crossings.size(), "on" if _show_crossings else "off",
		" ".join(field_map.filled_cells_per_pair.map(func(c): return str(c)))]


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
	dir.make_dir_recursive("docs/northstar/research/landscape_design/mockup/pass3")
	var img := get_viewport().get_texture().get_image()
	img.save_png(SCREENSHOT_DIR + file_name + ".png")


# A valley point close to the vantage's base: the vantage is a real local peak now (pass 3),
# so standing near its foot at micro band should put the mountain filling the frame without
# any special look-at-target logic -- camera_rig always looks back at its own origin, so
# placing that origin at the mountain's foot is enough.
func _find_valley_near_vantage_pos() -> Vector3:
	var vantage_pos := Vector2.ZERO
	for n in _field_map.nodes:
		if n.type == "vantage":
			vantage_pos = n.pos
			break
	var dim: int = _field_map.dim
	var best_e := INF
	var best := vantage_pos + Vector2(1200, 0)
	for gy in range(dim):
		for gx in range(dim):
			var wpos := Vector2(gx, gy) * FieldMap.SPACING
			var d := wpos.distance_to(vantage_pos)
			if d < 600.0 or d > 2000.0:
				continue
			var e: float = _field_map.grid[gy * dim + gx].elevation
			if e < best_e:
				best_e = e
				best = wpos
	return Vector3(best.x, 0.0, best.y)


func _run_screenshot_batch() -> void:
	for kit_name in _kits.keys():
		for shot_seed in [11, 12, 13]:
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

	for kit_name in _kits.keys():
		_kit_name = kit_name
		_seed = 11
		_seed_spinbox.value = 11
		_kit_toggle_button.text = "Kit: %s" % _kit_name
		_regenerate()
		_camera_rig.pan_to(_find_valley_near_vantage_pos())
		_camera_rig.set_height(BAND_HEIGHTS["micro"])
		await get_tree().process_frame
		await get_tree().process_frame
		await RenderingServer.frame_post_draw
		_take_screenshot("%s_valley_looking_up_seed11" % kit_name)

	get_tree().quit()


func get_seed() -> int:
	return _seed


func get_canvas_wu() -> float:
	return _canvas


func get_stability() -> float:
	return _stability


func get_density() -> float:
	return _density


func get_layer_gap() -> float:
	return _layer_gap


func get_plate_cell() -> float:
	return _plate_cell


func get_focus_layer() -> int:
	return _focus_layer


func get_show_crossings() -> bool:
	return _show_crossings


# Crossing marks actually drawn: the instances in the visible mark groups.
func get_marks_drawn() -> int:
	var drawn := 0
	for child in _generated.get_children():
		if child.get_meta("crossing_mark", false) and child.visible:
			drawn += child.multimesh.instance_count
	return drawn


func get_size_spread() -> float:
	return _size_spread


func get_density_swing() -> float:
	return _density_swing


func get_shared_density() -> bool:
	return _shared_density


func get_kit_name() -> String:
	return _kit_name


func get_field_map() -> FieldMap:
	return _field_map


func get_piece_total() -> int:
	return _piece_total


func get_timing_ms() -> Dictionary:
	return _timing_ms


func get_regen_count() -> int:
	return _regen_count


func qa_regenerate() -> void:
	_regenerate()


func qa_seed(n: int) -> void:
	_seed = n
	_seed_spinbox.value = n
	_regenerate()


func qa_set_stability(v: float) -> void:
	_stability = v
	_stability_slider.value = v
	_regenerate()


func qa_set_density(v: float) -> void:
	_density = clamp(v, 0.0, MAX_DENSITY)
	_density_slider.value = _density
	_regenerate()


func qa_set_plate_cell(v: float) -> void:
	_plate_cell = clamp(v, PLATE_RANGE.x, PLATE_RANGE.y)
	_plate_slider.value = _plate_cell
	_regenerate()


func qa_set_layer_gap(v: float) -> void:
	_layer_gap = clamp(v, GAP_RANGE.x, GAP_RANGE.y)
	_gap_slider.value = _layer_gap
	_regenerate()


func qa_set_size_spread(v: float) -> void:
	_size_spread = clamp(v, SPREAD_RANGE.x, SPREAD_RANGE.y)
	_spread_slider.value = _size_spread
	_regenerate()


func qa_set_density_swing(v: float) -> void:
	_density_swing = clamp(v, SWING_RANGE.x, SWING_RANGE.y)
	_swing_slider.value = _density_swing
	_regenerate()


func qa_set_shared_density(on: bool) -> void:
	_set_shared_density(on)


func qa_set_marks(on: bool) -> void:
	_show_crossings = on
	_apply_view()
	_update_space_controls(_field_map)


func qa_set_top_down(on: bool) -> void:
	_set_top_down(on)


func qa_set_focus(layer: int) -> void:
	_set_focus(layer)


func qa_set_kit(kit_name: String) -> void:
	if _kits.has(kit_name):
		_kit_name = kit_name
		_kit_toggle_button.text = "Kit: %s" % _kit_name
		_regenerate()

extends Control

const LOADING_TIPS_PATH := "res://data/loading_tips.json"
const BAR_WIDTH := 20

var _tips: Array = []
var _tip_idx: int = 0
var _cursor_on: bool = true
var _cursor_elapsed: float = 0.0
var _tip_elapsed: float = 0.0
var _current_step: String = "starting"
var _current_pct: float = 0.0

var _progress_label: Label
var _flavor_label: Label
var _skip_to_main: bool = false


func _ready() -> void:
	_build_ui()
	_load_tips()

	if not SimBridge.USE_LIVE_SIM:
		SceneRouter.go_to("main_menu")
		return

	if SimBridge._ready_received:
		_skip_to_main = true
		return

	SimBridge.progress_updated.connect(_on_progress_updated)
	SimBridge.sim_ready.connect(_on_sim_ready)

	_update_progress_display()
	if not _tips.is_empty():
		_flavor_label.text = _tips[0]


func _process(delta: float) -> void:
	if _skip_to_main:
		SceneRouter.go_to("main_menu")
		return

	_cursor_elapsed += delta
	if _cursor_elapsed >= ThemeConstants.CURSOR_BLINK_INTERVAL:
		_cursor_elapsed = 0.0
		_cursor_on = not _cursor_on
		_update_progress_display()

	_tip_elapsed += delta
	if _tip_elapsed >= 4.0:
		_tip_elapsed = 0.0
		_advance_tip()


func _build_ui() -> void:
	var bg := ColorRect.new()
	bg.color = ThemeConstants.BASE
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)

	_setup_galaxy_viewport()

	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(center)

	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 16)
	vbox.custom_minimum_size.x = 680
	center.add_child(vbox)

	var header := Label.new()
	header.text = "INITIALIZING SIMULATION"
	header.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	header.add_theme_font_size_override("font_size", ThemeConstants.CLASSIFICATION_LABEL_SIZE)
	header.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	header.add_theme_constant_override("letter_spacing", ThemeConstants.CLASSIFICATION_LABEL_SPACING)
	header.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	vbox.add_child(header)

	var spacer1 := Control.new()
	spacer1.custom_minimum_size.y = 8
	vbox.add_child(spacer1)

	_progress_label = Label.new()
	_progress_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	_progress_label.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
	_progress_label.add_theme_color_override("font_color", Color("#c9a84c"))
	_progress_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	vbox.add_child(_progress_label)

	var spacer2 := Control.new()
	spacer2.custom_minimum_size.y = 28
	vbox.add_child(spacer2)

	_flavor_label = Label.new()
	_flavor_label.add_theme_font_override("font", ThemeConstants.font_serif_italic)
	_flavor_label.add_theme_font_size_override("font_size", ThemeConstants.BODY_NARRATIVE_SIZE)
	_flavor_label.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	_flavor_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_flavor_label.autowrap_mode = TextServer.AUTOWRAP_WORD
	_flavor_label.custom_minimum_size.x = 680
	vbox.add_child(_flavor_label)


func _setup_galaxy_viewport() -> void:
	var container := SubViewportContainer.new()
	container.set_anchors_preset(Control.PRESET_FULL_RECT)
	container.stretch = true
	container.mouse_filter = Control.MOUSE_FILTER_IGNORE
	container.modulate = Color(1, 1, 1, 0.0)
	add_child(container)

	var viewport := SubViewport.new()
	viewport.transparent_bg = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	viewport.msaa_3d = Viewport.MSAA_DISABLED
	viewport.use_hdr_2d = false
	container.add_child(viewport)

	var galaxy_scene := load("res://scenes/shared/galaxy/galaxy_structure.tscn")
	var galaxy: Node3D = galaxy_scene.instantiate()
	viewport.add_child(galaxy)
	galaxy.start_auto_camera()

	var tw := create_tween()
	tw.tween_property(container, "modulate:a", 0.4, 2.0)


func _load_tips() -> void:
	if not FileAccess.file_exists(LOADING_TIPS_PATH):
		return
	var f := FileAccess.open(LOADING_TIPS_PATH, FileAccess.READ)
	if f == null:
		return
	var json := JSON.new()
	if json.parse(f.get_as_text()) == OK:
		var data = json.get_data()
		if data is Array:
			_tips = data
	f.close()


func _update_progress_display() -> void:
	var filled := int(_current_pct * BAR_WIDTH)
	var empty := BAR_WIDTH - filled
	var bar := "█".repeat(filled) + "░".repeat(empty)
	var pct_str := "%d%%" % int(_current_pct * 100)
	var cursor := "█" if _cursor_on else " "
	var step_display := _current_step.to_upper().replace("_", " ")
	_progress_label.text = "%s  %s %s %s" % [step_display, bar, pct_str, cursor]


func _advance_tip() -> void:
	if _tips.is_empty():
		return
	_tip_idx = (_tip_idx + 1) % _tips.size()
	var tip: String = _tips[_tip_idx]
	var tw := create_tween()
	tw.tween_property(_flavor_label, "modulate:a", 0.0, 0.3)
	tw.tween_callback(func(): _flavor_label.text = tip)
	tw.tween_property(_flavor_label, "modulate:a", 1.0, 0.3)


func _on_progress_updated(step: String, pct: float) -> void:
	var step_changed := step != _current_step
	_current_step = step
	_current_pct = pct
	_update_progress_display()
	if step_changed:
		_advance_tip()
		_tip_elapsed = 0.0


func _on_sim_ready(_metadata: Dictionary) -> void:
	SceneRouter.go_to("main_menu")

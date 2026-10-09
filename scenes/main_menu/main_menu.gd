extends Control

const SimSession := preload("res://autoload/sim_session.gd")

const HOVER_GLYPH_CAP := 12
const HOVER_GLYPHS := ["✦", "·"]
const HOVER_GLYPH_COUNTS := {
	"NEW CAMPAIGN": 4, "CONTINUE": 3, "ERA LIBRARY": 3, "MULTIPLAYER": 3, "SETTINGS": 2, "QUIT": 2,
}
const GLYPH_COLOR := Color("#FFFFFF")

var _menu_items: Array[Control] = []
var _bridge = null
var _continue_item: Control = null
var _slot_count := 0
var _world_view: Node
var _title_heartbeat: Control
var _hover_layer: Control
var _active_hover_glyphs := 0

func _ready() -> void:
	_build_ui()
	_setup_title_heartbeat()
	_animate_entrance()


func _build_ui() -> void:
	var bg := ColorRect.new()
	bg.color = ThemeConstants.BASE
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)

	_setup_world_view_viewport()

	var content := VBoxContainer.new()
	content.set_anchors_preset(Control.PRESET_CENTER_LEFT)
	content.anchor_left = 0.15
	content.anchor_right = 0.5
	content.anchor_top = 0.3
	content.anchor_bottom = 0.8
	content.offset_left = 0
	content.offset_right = 0
	content.offset_top = 0
	content.offset_bottom = 0
	content.add_theme_constant_override("separation", 0)
	add_child(content)

	var classification := Label.new()
	classification.text = "A WESTOPOLI GAME"
	classification.uppercase = true
	classification.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	classification.add_theme_font_size_override("font_size", 20)
	classification.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	classification.add_theme_constant_override("letter_spacing", 7)
	content.add_child(classification)

	var spacer1 := Control.new()
	spacer1.custom_minimum_size.y = 10
	content.add_child(spacer1)

	var title_placeholder := Control.new()
	title_placeholder.custom_minimum_size.y = int(ThemeConstants.TITLE_SIZE * 1.5) + 20
	title_placeholder.name = "TitlePlaceholder"
	content.add_child(title_placeholder)

	var spacer2 := Control.new()
	spacer2.custom_minimum_size.y = 52
	content.add_child(spacer2)

	var menu_data := [
		{"label": "NEW CAMPAIGN", "action": "galaxy"},
		{"label": "CONTINUE", "action": "load_game"},
		{"label": "ERA LIBRARY", "action": "era_library"},
		{"label": "MULTIPLAYER", "action": "lobby"},
		{"label": "SETTINGS", "action": "settings"},
		{"label": "QUIT", "action": "quit"},
	]

	for item_data in menu_data:
		var item := _create_menu_item(item_data["label"], item_data["action"])
		if item_data["action"] == "load_game":
			item.name = "Continue"
			_continue_item = item
		if item_data["action"] == "galaxy":
			item.name = "NewGame"
		content.add_child(item)
		_menu_items.append(item)
	var era_toggle := Button.new()
	era_toggle.name = "EraToggle"
	era_toggle.flat = true
	era_toggle.alignment = HORIZONTAL_ALIGNMENT_LEFT
	era_toggle.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	era_toggle.add_theme_font_size_override("font_size", 20)
	era_toggle.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	era_toggle.pressed.connect(_on_era_toggle.bind(era_toggle))
	_refresh_era_toggle(era_toggle)
	content.add_child(era_toggle)
	qa_set_bridge(SimSession.bridge())

	_hover_layer = Control.new()
	_hover_layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	_hover_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_hover_layer)

	var version := Label.new()
	version.text = "v0.9.0"
	version.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	version.add_theme_font_size_override("font_size", 20)
	version.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	version.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	version.offset_left = -80
	version.offset_top = -30
	version.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	add_child(version)


func _refresh_era_toggle(toggle: Button) -> void:
	toggle.text = "ERA: %s" % ("GROUND" if EraConfig.kind() == "ground" else "SPACE")


func _on_era_toggle(toggle: Button) -> void:
	var next := EraConfig.SPACE_ERA_ID if EraConfig.kind() == "ground" else EraConfig.GROUND_ERA_ID
	EraConfig.set_era(next)
	var settings: Dictionary = UIDataBus.get_settings()
	settings["era_id"] = next
	UIDataBus.save_settings(settings)
	_refresh_era_toggle(toggle)


func _setup_world_view_viewport() -> void:
	var container := SubViewportContainer.new()
	container.set_anchors_preset(Control.PRESET_FULL_RECT)
	container.stretch = true
	container.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(container)

	var viewport := SubViewport.new()
	viewport.transparent_bg = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	viewport.msaa_3d = Viewport.MSAA_DISABLED
	viewport.use_hdr_2d = false
	container.add_child(viewport)

	var world_view_scene := load("res://scenes/shared/world_view/main_menu_galaxy.tscn")
	var world_view: Node3D = world_view_scene.instantiate()
	viewport.add_child(world_view)

	world_view.start_auto_camera()
	_world_view = world_view

	container.modulate = Color(1, 1, 1, 0.0)
	var tw := create_tween()
	tw.tween_property(container, "modulate:a", 0.7, 2.0)


# Self-healing title-position tracking (replaces a CONNECT_ONE_SHOT
# process_frame read). Investigation for this bug found TitlePlaceholder's
# global_position is actually stable from the first frame in every
# resolution tested; the real cause of the blank title was a separate
# font-load race fixed in menu_title_heartbeat.gd's _try_build_title_labels.
# This per-frame retry is kept as defense in depth against any future
# layout timing where the placeholder's position takes a frame or more to
# settle -- see also: scenes/loading_screen/loading_screen.gd's _process
# retry (S-C8-07), the precedent for replacing a one-shot read with a
# self-correcting per-frame one.
const TITLE_POSITION_SETTLE_FRAME_CAP := 30

var _title_position_prev := Vector2.INF
var _title_position_frame := 0

func _setup_title_heartbeat() -> void:
	var heartbeat_script := load("res://scenes/main_menu/menu_title_heartbeat.gd")
	_title_heartbeat = Control.new()
	_title_heartbeat.set_script(heartbeat_script)
	add_child(_title_heartbeat)

	set_process(true)

	if _world_view and _world_view.has_signal("structure_revealed"):
		_world_view.structure_revealed.connect(_title_heartbeat._on_climax)


func _process(_delta: float) -> void:
	var placeholder: Control = find_child("TitlePlaceholder", true, false)
	if placeholder == null or _title_heartbeat == null:
		return
	var pos: Vector2 = placeholder.global_position
	_title_heartbeat.set_title_origin(pos)
	_title_position_frame += 1
	if pos == _title_position_prev or _title_position_frame >= TITLE_POSITION_SETTLE_FRAME_CAP:
		set_process(false)
	_title_position_prev = pos


func _create_menu_item(label_text: String, action: String) -> Control:
	var container := HBoxContainer.new()
	container.custom_minimum_size.y = 62
	container.add_theme_constant_override("separation", 12)

	var accent_line := ColorRect.new()
	accent_line.custom_minimum_size = Vector2(0, 2)
	accent_line.color = ThemeConstants.SECONDARY
	accent_line.modulate.a = 0.0
	container.add_child(accent_line)

	var label := Label.new()
	label.text = label_text
	label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	label.add_theme_font_size_override("font_size", 27)
	label.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
	container.add_child(label)

	container.mouse_filter = Control.MOUSE_FILTER_STOP
	container.mouse_entered.connect(func():
		label.add_theme_color_override("font_color", Color("#D4A017"))
		var tw := create_tween()
		tw.tween_property(accent_line, "custom_minimum_size:x", 16.0, 0.15)
		tw.parallel().tween_property(accent_line, "modulate:a", 1.0, 0.15)
		_spawn_hover_bloom(container, label_text)
	)
	container.mouse_exited.connect(func():
		label.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
		var tw := create_tween()
		tw.tween_property(accent_line, "custom_minimum_size:x", 0.0, 0.15)
		tw.parallel().tween_property(accent_line, "modulate:a", 0.0, 0.15)
	)
	container.gui_input.connect(func(event: InputEvent):
		if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
			if action != "quit":
				_spawn_click_burst(container)
			_on_menu_action(action)
	)
	return container


func _spawn_hover_bloom(container: Control, label_text: String) -> void:
	var count: int = HOVER_GLYPH_COUNTS.get(label_text, 2)
	if _active_hover_glyphs >= HOVER_GLYPH_CAP:
		return

	var origin := container.global_position + Vector2(0, container.size.y * 0.5)

	for i in range(count):
		if _active_hover_glyphs >= HOVER_GLYPH_CAP:
			break
		_active_hover_glyphs += 1

		var glyph_text: String = HOVER_GLYPHS[randi() % HOVER_GLYPHS.size()]
		var lbl := Label.new()
		lbl.text = glyph_text
		lbl.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		lbl.add_theme_font_size_override("font_size", 14)
		lbl.add_theme_color_override("font_color", GLYPH_COLOR)
		lbl.mouse_filter = Control.MOUSE_FILTER_IGNORE
		lbl.modulate.a = 0.0

		var y_offset := randf_range(-8.0, 8.0)
		lbl.position = origin + Vector2(0, y_offset)
		_hover_layer.add_child(lbl)

		var drift_x := randf_range(-25.0, -40.0)
		var drift_y := randf_range(-6.0, 6.0)
		var delay := randf() * 0.1

		var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_interval(delay)
		tw.tween_property(lbl, "modulate:a", 0.45, 0.1)
		tw.parallel().tween_property(lbl, "position", lbl.position + Vector2(drift_x, drift_y), 0.5)
		tw.tween_property(lbl, "modulate:a", 0.0, 0.3)
		tw.tween_callback(func():
			_active_hover_glyphs -= 1
			if is_instance_valid(lbl):
				lbl.queue_free()
		)


func _spawn_click_burst(container: Control) -> void:
	var center := container.global_position + Vector2(0, container.size.y * 0.5)

	for i in range(6):
		var angle := (float(i) / 6.0) * TAU
		var start_pos := center + Vector2(cos(angle), sin(angle)) * 30.0
		var end_pos := center + Vector2(cos(angle), sin(angle)) * 60.0

		var glyph_text: String = HOVER_GLYPHS[randi() % HOVER_GLYPHS.size()]
		var lbl := Label.new()
		lbl.text = glyph_text
		lbl.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		lbl.add_theme_font_size_override("font_size", 14)
		lbl.add_theme_color_override("font_color", GLYPH_COLOR)
		lbl.mouse_filter = Control.MOUSE_FILTER_IGNORE
		lbl.modulate.a = 0.0
		lbl.position = start_pos
		_hover_layer.add_child(lbl)

		var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_property(lbl, "modulate:a", 0.50, 0.08)
		tw.parallel().tween_property(lbl, "position", end_pos, 0.3)
		tw.tween_property(lbl, "modulate:a", 0.0, 0.15)
		tw.tween_callback(func():
			if is_instance_valid(lbl):
				lbl.queue_free()
		)


func _on_menu_action(action: String) -> void:
	match action:
		"quit":
			get_tree().quit()
		"galaxy":
			SimSession.reset()
			SceneRouter.go_to(action)
		_:
			SceneRouter.go_to(action)


# CONTINUE is enabled by the live save list (bridge.list_saves(), C1-2), not
# the legacy UIDataBus.get_save_slots(). The dim is on the item's label: the
# entrance animation tweens the item's own modulate to 1.0.
func qa_set_bridge(bridge) -> void:
	_bridge = bridge
	_slot_count = (_bridge.list_saves() as Array).size()
	if _continue_item == null:
		return
	var enabled := _slot_count > 0
	_continue_item.mouse_filter = Control.MOUSE_FILTER_STOP if enabled else Control.MOUSE_FILTER_IGNORE
	for c in _continue_item.get_children():
		if c is Label:
			(c as Label).modulate.a = 1.0 if enabled else 0.3


func qa_state() -> Dictionary:
	return {
		"scene": "main_menu",
		"tick": -1,
		"continue_enabled": _slot_count > 0,
		"slot_count": _slot_count,
		"plants": [],
	}


func _animate_entrance() -> void:
	var delay := ThemeConstants.STAGGER_BASE_DELAY
	for i in range(get_child_count()):
		var child := get_child(i)
		if child is ColorRect:
			continue
		if child is Label:
			child.modulate.a = 0.0
			child.position.y += 8.0
			var original_y: float = child.position.y - 8.0
			var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
			tw.tween_interval(delay)
			tw.tween_property(child, "modulate:a", 1.0, ThemeConstants.ELEMENT_ANIM_DURATION)
			tw.parallel().tween_property(child, "position:y", original_y, ThemeConstants.ELEMENT_ANIM_DURATION)
			delay += ThemeConstants.STAGGER_INCREMENT

	var content_node: VBoxContainer = null
	for child in get_children():
		if child is VBoxContainer:
			content_node = child
			break
	if not content_node:
		return

	for i in range(content_node.get_child_count()):
		var child := content_node.get_child(i)
		child.modulate.a = 0.0
		var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_interval(delay)
		tw.tween_property(child, "modulate:a", 1.0, ThemeConstants.ELEMENT_ANIM_DURATION)
		delay += ThemeConstants.STAGGER_INCREMENT

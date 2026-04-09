extends Control

signal animation_finished

var _accent_color: Color = Color("#c9a84c")
var _chars: Array[Dictionary] = []
var _active := false

func set_accent_color(color: Color) -> void:
	_accent_color = color


func play() -> void:
	_active = true
	_run_animation()


func _run_animation() -> void:
	pass


func _finish() -> void:
	_active = false
	animation_finished.emit()


func spawn_char(character: String, pos: Vector2, delay_time: float, duration: float, color: Color = Color.TRANSPARENT) -> void:
	var use_color := color if color.a > 0 else _accent_color
	var lbl := Label.new()
	lbl.text = character
	lbl.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	lbl.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
	lbl.add_theme_color_override("font_color", use_color)
	lbl.position = pos
	lbl.modulate.a = 0.0
	add_child(lbl)

	var tw := create_tween()
	tw.tween_interval(delay_time)
	tw.tween_property(lbl, "modulate:a", 1.0, 0.2)
	if duration > 0:
		tw.tween_interval(duration)
		tw.tween_property(lbl, "modulate:a", 0.0, 0.2)
		tw.tween_callback(lbl.queue_free)


func cascade_text(text: String, start_pos: Vector2, direction: Vector2, char_delay: float, color: Color = Color.TRANSPARENT) -> void:
	var use_color := color if color.a > 0 else _accent_color
	for i in range(text.length()):
		var ch := text[i]
		if ch == " ":
			continue
		var pos := start_pos + direction * i
		spawn_char(ch, pos, char_delay * i, 0, use_color)


func particle_burst(center: Vector2, chars: Array, count: int, radius: float, duration: float) -> void:
	for i in range(count):
		var angle := randf() * TAU
		var dist := randf() * radius
		var target := center + Vector2(cos(angle), sin(angle)) * dist
		var ch: String = chars[randi() % chars.size()]
		var lbl := Label.new()
		lbl.text = ch
		lbl.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		lbl.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
		lbl.add_theme_color_override("font_color", _accent_color)
		lbl.position = center
		lbl.modulate.a = 1.0
		add_child(lbl)

		var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_property(lbl, "position", target, duration)
		tw.parallel().tween_property(lbl, "modulate:a", 0.0, duration)
		tw.tween_callback(lbl.queue_free)


func typewriter(text: String, pos: Vector2, char_interval: float, color: Color = Color.TRANSPARENT) -> void:
	var use_color := color if color.a > 0 else ThemeConstants.SECONDARY
	var lbl := Label.new()
	lbl.text = ""
	lbl.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	lbl.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
	lbl.add_theme_color_override("font_color", use_color)
	lbl.position = pos
	add_child(lbl)

	var full := text
	var tw := create_tween()
	for i in range(full.length()):
		var partial := full.substr(0, i + 1)
		tw.tween_callback(func(): lbl.text = partial)
		tw.tween_interval(char_interval)


func _clear_children() -> void:
	for child in get_children():
		child.queue_free()

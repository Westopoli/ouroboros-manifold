extends Control

signal animation_finished

var _era_id: String = ""
var _accent: Color
var _shader_rect: ColorRect
var _glyph_layer: Control
var _glyph_pool: Array[Label] = []

func play(era_id: String) -> void:
	_era_id = era_id
	_accent = ThemeConstants.get_era_accent(era_id)
	_setup_layers()
	_run_sequence()


func _get_shader() -> Shader:
	return null


func _get_glyph_set() -> Array:
	return []


func _get_title_text() -> String:
	return ""


func _setup_layers() -> void:
	# Shader atmosphere layer
	var shader := _get_shader()
	if shader:
		_shader_rect = ColorRect.new()
		_shader_rect.set_anchors_preset(Control.PRESET_FULL_RECT)
		_shader_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var mat := ShaderMaterial.new()
		mat.shader = shader
		_shader_rect.material = mat
		_shader_rect.modulate.a = 0.0
		add_child(_shader_rect)

	# Glyph foreground layer
	_glyph_layer = Control.new()
	_glyph_layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	_glyph_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_glyph_layer)


func _run_sequence() -> void:
	pass


func _fade_shader_in(duration: float, target_alpha: float = 0.25) -> void:
	if _shader_rect:
		var tw := create_tween()
		tw.tween_property(_shader_rect, "modulate:a", target_alpha, duration)


func _fade_shader_out(duration: float = 0.3) -> void:
	if _shader_rect:
		var tw := create_tween()
		tw.tween_property(_shader_rect, "modulate:a", 0.0, duration)


func bloom_ring(center: Vector2, glyphs: Array, count: int, radius: float, delay_time: float, duration: float) -> void:
	var stagger := duration / float(count) / 3.0
	for i in range(count):
		var angle := (float(i) / float(count)) * TAU
		var pos := center + Vector2(cos(angle), sin(angle)) * radius
		var glyph_text: String = glyphs[i % glyphs.size()]

		var lbl := Label.new()
		lbl.text = glyph_text
		lbl.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		lbl.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
		lbl.add_theme_color_override("font_color", _accent)
		lbl.position = pos - Vector2(8, 10)
		lbl.modulate.a = 0.0
		lbl.scale = Vector2(0.5, 0.5)
		lbl.pivot_offset = Vector2(8, 10)
		_glyph_layer.add_child(lbl)
		_glyph_pool.append(lbl)

		var char_delay := delay_time + i * stagger
		var expand_target := pos + (pos - center).normalized() * radius * 0.12 - Vector2(8, 10)

		var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_interval(char_delay)
		tw.tween_property(lbl, "modulate:a", 1.0, duration * 0.3)
		tw.parallel().tween_property(lbl, "scale", Vector2.ONE, duration * 0.3)
		tw.parallel().tween_property(lbl, "position", expand_target, duration * 0.6)
		tw.tween_interval(duration * 0.2)
		tw.tween_property(lbl, "modulate:a", 0.0, duration * 0.3)


func bloom_scatter(center: Vector2, glyphs: Array, count: int, radius: float, delay_time: float, duration: float, alpha_override: float = 1.0) -> void:
	for i in range(count):
		var angle := randf() * TAU
		var dist := randf() * radius
		var pos := center + Vector2(cos(angle), sin(angle)) * dist
		var glyph_text: String = glyphs[i % glyphs.size()]

		var lbl := Label.new()
		lbl.text = glyph_text
		lbl.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		lbl.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
		lbl.add_theme_color_override("font_color", _accent)
		lbl.position = pos - Vector2(8, 10)
		lbl.modulate.a = 0.0
		_glyph_layer.add_child(lbl)
		_glyph_pool.append(lbl)

		var drift := (pos - center).normalized() * randf_range(10, 20)
		var char_delay := delay_time + randf() * duration * 0.2

		var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_interval(char_delay)
		tw.tween_property(lbl, "modulate:a", alpha_override, duration * 0.2)
		tw.parallel().tween_property(lbl, "position", lbl.position + drift, duration * 0.7)
		tw.tween_interval(duration * 0.3)
		tw.tween_property(lbl, "modulate:a", 0.0, duration * 0.3)


func resolve_title(text: String, center: Vector2, delay_time: float, char_interval: float, scramble_duration: float) -> void:
	var glyphs := _get_glyph_set()
	if glyphs.is_empty():
		glyphs = ["\u2726", "\u2727", "\u25c6", "\u2756"]
	var char_width := 50.0
	var total_width := text.length() * char_width
	var start_x := center.x - total_width / 2.0

	for i in range(text.length()):
		var final_char := text[i]
		if final_char == " ":
			continue

		var pos := Vector2(start_x + i * char_width, center.y - 20)

		# Scramble label (mono font)
		var scramble_lbl := Label.new()
		scramble_lbl.text = glyphs[randi() % glyphs.size()]
		scramble_lbl.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		scramble_lbl.add_theme_font_size_override("font_size", ThemeConstants.TITLE_SIZE - 6)
		scramble_lbl.add_theme_color_override("font_color", _accent)
		scramble_lbl.position = pos
		scramble_lbl.modulate.a = 0.0
		_glyph_layer.add_child(scramble_lbl)
		_glyph_pool.append(scramble_lbl)

		# Final label (serif font)
		var final_lbl := Label.new()
		final_lbl.text = final_char
		final_lbl.add_theme_font_override("font", ThemeConstants.font_serif_regular)
		final_lbl.add_theme_font_size_override("font_size", ThemeConstants.TITLE_SIZE)
		final_lbl.add_theme_color_override("font_color", _accent)
		final_lbl.position = pos
		final_lbl.modulate.a = 0.0
		_glyph_layer.add_child(final_lbl)
		_glyph_pool.append(final_lbl)

		var char_start := delay_time + i * char_interval
		var scramble_cycles := int(scramble_duration / 0.06)

		# Scramble animation
		var stw := create_tween()
		stw.tween_interval(char_start)
		stw.tween_property(scramble_lbl, "modulate:a", 1.0, 0.05)
		for c in range(scramble_cycles):
			var g: String = glyphs[randi() % glyphs.size()]
			stw.tween_callback(func(): scramble_lbl.text = g)
			stw.tween_interval(0.06)
		stw.tween_property(scramble_lbl, "modulate:a", 0.0, 0.05)

		# Final letter locks in
		var ftw := create_tween()
		ftw.tween_interval(char_start + scramble_duration)
		ftw.tween_property(final_lbl, "modulate:a", 1.0, 0.1)


func _make_glyph(text: String, pos: Vector2, font_size: int = -1, color: Color = Color.TRANSPARENT, bold: bool = false) -> Label:
	var lbl := Label.new()
	lbl.text = text
	lbl.add_theme_font_override("font", ThemeConstants.font_mono_bold if bold else ThemeConstants.font_mono_regular)
	lbl.add_theme_font_size_override("font_size", font_size if font_size > 0 else ThemeConstants.BODY_DATA_SIZE)
	lbl.add_theme_color_override("font_color", color if color.a > 0 else _accent)
	lbl.position = pos
	lbl.modulate.a = 0.0
	_glyph_layer.add_child(lbl)
	_glyph_pool.append(lbl)
	return lbl


func _cleanup_and_finish(hold_time: float = 0.4) -> void:
	var tw := create_tween()
	tw.tween_interval(hold_time)
	tw.tween_callback(func():
		for lbl in _glyph_pool:
			if is_instance_valid(lbl):
				var ftw := create_tween()
				ftw.tween_property(lbl, "modulate:a", 0.0, 0.3)
		_fade_shader_out(0.3)
	)
	tw.tween_interval(0.4)
	tw.tween_callback(func():
		animation_finished.emit()
	)

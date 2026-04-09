extends "res://assets/celebrations/celebration_base.gd"

var _persistent_stars: Array[Label] = []

func _get_shader() -> Shader:
	return load("res://assets/shaders/starfield.gdshader")


func _get_glyph_set() -> Array:
	return ["\u00b7", "\u2727", "\u2726", "\u2736", "\u2739", "\u273a", "\u273b", "\u273d"]


func _get_title_text() -> String:
	return "SETTLED REACH"


func _run_sequence() -> void:
	var center := size / 2.0
	var glyphs := _get_glyph_set()

	# Phase 1 (0-1.5s): Shader + 8 scatter waves + halo layer + persistent stars
	_fade_shader_in(0.8, 0.25)

	# 8 main scatter waves with progressive glyph complexity
	bloom_scatter(center, glyphs.slice(0, 2), 3, 40, 0.15, 0.8)
	bloom_scatter(center, glyphs.slice(0, 2), 4, 60, 0.25, 0.8)
	bloom_scatter(center, glyphs.slice(0, 3), 5, 80, 0.35, 0.9)
	bloom_scatter(center, glyphs.slice(0, 4), 7, 100, 0.45, 0.9)
	bloom_scatter(center, glyphs.slice(0, 5), 8, 120, 0.55, 1.0)
	bloom_scatter(center, glyphs.slice(0, 6), 10, 150, 0.65, 1.0)
	bloom_scatter(center, glyphs.slice(0, 7), 11, 180, 0.8, 1.0)
	bloom_scatter(center, glyphs, 12, 200, 0.95, 1.0)

	# Halo layer — faint dots at 1.5x radius
	bloom_scatter(center, ["\u00b7"], 8, 60, 0.2, 1.2, 0.15)
	bloom_scatter(center, ["\u00b7"], 12, 120, 0.4, 1.4, 0.15)
	bloom_scatter(center, ["\u00b7"], 16, 200, 0.6, 1.5, 0.15)
	bloom_scatter(center, ["\u00b7"], 20, 300, 0.8, 1.5, 0.15)

	# 6 persistent background stars
	for i in range(6):
		var pos := Vector2(
			randf_range(80, size.x - 80),
			randf_range(80, size.y - 80)
		)
		var lbl := _make_glyph("\u2727", pos)

		var fade_delay := randf_range(0.3, 1.0)
		var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_interval(fade_delay)
		tw.tween_property(lbl, "modulate:a", 0.4, 0.3)

		# Slow random drift
		var drift_dir := Vector2(randf_range(-1, 1), randf_range(-1, 1)).normalized()
		var drift_tw := create_tween().set_ease(Tween.EASE_IN_OUT).set_trans(Tween.TRANS_SINE)
		drift_tw.tween_interval(fade_delay + 0.3)
		drift_tw.tween_property(lbl, "position", pos + drift_dir * 30, 2.5)

		_persistent_stars.append(lbl)

	# Phase 2 (1.5-3.0s): Title resolve + shockwave rings on first/last letter lock
	var title := _get_title_text()
	resolve_title(title, center, 1.5, 0.08, 0.4)

	# Shockwave on first letter lock
	var first_lock_time := 1.5 + 0.4
	bloom_ring(center + Vector2(0, -40), glyphs.slice(1, 4), 5, 50, first_lock_time, 0.5)
	bloom_ring(center + Vector2(0, 40), glyphs.slice(1, 4), 5, 50, first_lock_time, 0.5)

	# Pulse persistent stars on first shockwave
	var pulse1 := create_tween()
	pulse1.tween_interval(first_lock_time)
	pulse1.tween_callback(func(): _pulse_persistent_stars())

	# Shockwave on last letter lock — count non-space chars
	var char_count := 0
	for ch in title:
		if ch != " ":
			char_count += 1
	var last_lock_time := 1.5 + (char_count - 1) * 0.08 + 0.4
	bloom_ring(center + Vector2(0, -40), glyphs.slice(2, 5), 5, 50, last_lock_time, 0.5)
	bloom_ring(center + Vector2(0, 40), glyphs.slice(2, 5), 5, 50, last_lock_time, 0.5)

	var pulse2 := create_tween()
	pulse2.tween_interval(last_lock_time)
	pulse2.tween_callback(func(): _pulse_persistent_stars())

	# Phase 3 (3.0-3.8s): Stars accelerate outward, final wink
	var finish := create_tween()
	finish.tween_interval(3.0)
	finish.tween_callback(_phase3_exit)


func _pulse_persistent_stars() -> void:
	for lbl in _persistent_stars:
		if is_instance_valid(lbl):
			var tw := create_tween()
			tw.tween_property(lbl, "modulate:a", 1.0, 0.1)
			tw.tween_property(lbl, "modulate:a", 0.4, 0.2)


func _phase3_exit() -> void:
	var center := size / 2.0

	# Persistent stars accelerate drift and fade
	for lbl in _persistent_stars:
		if not is_instance_valid(lbl):
			continue
		var dir := (lbl.position - center).normalized()
		var tw := create_tween().set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_CUBIC)
		tw.tween_property(lbl, "position", lbl.position + dir * 60, 0.5)
		tw.parallel().tween_property(lbl, "modulate:a", 0.0, 0.5)

	# Fade all other glyphs
	for lbl in _glyph_pool:
		if is_instance_valid(lbl) and not _persistent_stars.has(lbl) and lbl.modulate.a > 0:
			var ftw := create_tween()
			ftw.tween_property(lbl, "modulate:a", 0.0, 0.3)

	_fade_shader_out(0.4)

	# Final ✽ wink at center after everything else fades
	var final_star := _make_glyph("\u273d", center - Vector2(10, 12), ThemeConstants.TITLE_SIZE)
	var wink := create_tween()
	wink.tween_interval(0.5)
	wink.tween_property(final_star, "modulate:a", 1.0, 0.1)
	wink.tween_interval(0.3)
	wink.tween_property(final_star, "modulate:a", 0.0, 0.2)
	wink.tween_callback(func(): animation_finished.emit())

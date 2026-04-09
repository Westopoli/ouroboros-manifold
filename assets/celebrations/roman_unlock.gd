extends "res://assets/celebrations/celebration_base.gd"

var _cardinal_glyphs: Array[Label] = []
var _ring_glyphs_by_ring: Array[Array] = []

func _get_shader() -> Shader:
	return load("res://assets/shaders/ember_drift.gdshader")


func _get_glyph_set() -> Array:
	return ["\u2726", "\u2727", "\u25c6", "\u2756", "\u2736", "\u2b25", "\u25c8", "\u2734"]


func _get_title_text() -> String:
	return "ROMAN"


func _run_sequence() -> void:
	var center := size / 2.0
	var glyphs := _get_glyph_set()

	# Phase 1 (0-1.2s): Shader + three bloom rings + cardinal glyphs
	_fade_shader_in(0.5, 0.25)

	_spawn_tracked_ring(center, glyphs, 6, 80, 0.3, 0.8)
	_spawn_tracked_ring(center, glyphs, 10, 160, 0.6, 0.9)
	_spawn_tracked_ring(center, glyphs, 14, 240, 0.9, 1.0)

	# Cardinal ✦ glyphs at N/S/E/W, radius 120
	var cardinal_dirs: Array[Vector2] = [Vector2(0, -1), Vector2(0, 1), Vector2(1, 0), Vector2(-1, 0)]
	for dir in cardinal_dirs:
		var pos := center + dir * 120.0
		var lbl := _make_glyph("\u2726", pos - Vector2(8, 10))
		_cardinal_glyphs.append(lbl)

		var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_interval(0.5)
		tw.tween_property(lbl, "modulate:a", 1.0, 0.3)

	# Cardinal pulse loop (0.6-1.0 opacity, ~2Hz sine)
	for lbl in _cardinal_glyphs:
		var pulse := create_tween().set_loops(8)
		pulse.tween_interval(0.5)
		pulse.tween_property(lbl, "modulate:a", 0.6, 0.25)
		pulse.tween_property(lbl, "modulate:a", 1.0, 0.25)

	# Phase 2 (1.2-2.8s): Title resolve + depth layers + underline
	resolve_title(_get_title_text(), center, 1.2, 0.12, 0.5)

	# Foreground scatter
	bloom_scatter(center, glyphs, 20, 200, 1.4, 1.2, 0.4)
	# Background depth layer — dots at 20% opacity, double count, slower drift
	bloom_scatter(center, ["\u00b7"], 40, 200, 1.4, 1.6, 0.2)

	# Expanding underline beneath title
	var title_text := _get_title_text()
	var char_w := 22.0
	var title_w := title_text.length() * char_w
	var underline_y := center.y + 16
	var underline_count := int(title_w / 9.0)
	for i in range(underline_count):
		var half := underline_count / 2
		var dist_from_center: int = abs(i - half)
		var x_pos := center.x - (underline_count * 9.0) / 2.0 + i * 9.0
		var lbl := _make_glyph("\u2500", Vector2(x_pos, underline_y))

		var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_interval(1.4 + dist_from_center * 0.03)
		tw.tween_property(lbl, "modulate:a", 0.5, 0.15)

	# Phase 3 (2.8-3.5s): Cardinals shoot outward, rings collapse, title fades last
	var finish := create_tween()
	finish.tween_interval(2.8)
	finish.tween_callback(_phase3_exit)


func _phase3_exit() -> void:
	var center := size / 2.0

	# Cardinals shoot to screen edges
	var edge_targets: Array[Vector2] = [
		Vector2(center.x, -40),
		Vector2(center.x, size.y + 40),
		Vector2(size.x + 40, center.y),
		Vector2(-40, center.y),
	]
	for i in range(_cardinal_glyphs.size()):
		var lbl: Label = _cardinal_glyphs[i]
		if not is_instance_valid(lbl):
			continue
		var tw := create_tween().set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_CUBIC)
		tw.tween_property(lbl, "position", edge_targets[i], 0.4)
		tw.parallel().tween_property(lbl, "modulate:a", 0.0, 0.4)

	# Ring glyphs collapse inward
	for ring in _ring_glyphs_by_ring:
		for lbl in ring:
			if not is_instance_valid(lbl):
				continue
			var tw := create_tween().set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_CUBIC)
			tw.tween_property(lbl, "position", center - Vector2(8, 10), 0.35)
			tw.parallel().tween_property(lbl, "modulate:a", 0.0, 0.35)

	# Everything else fades, title last
	var cleanup := create_tween()
	cleanup.tween_interval(0.45)
	cleanup.tween_callback(func():
		for lbl in _glyph_pool:
			if is_instance_valid(lbl) and lbl.modulate.a > 0:
				var ftw := create_tween()
				ftw.tween_property(lbl, "modulate:a", 0.0, 0.2)
		_fade_shader_out(0.3)
	)
	cleanup.tween_interval(0.3)
	cleanup.tween_callback(func(): animation_finished.emit())


func _spawn_tracked_ring(center: Vector2, glyphs: Array, count: int, radius: float, delay_time: float, duration: float) -> void:
	var ring_labels: Array = []
	var stagger := duration / float(count) / 3.0
	for i in range(count):
		var angle := (float(i) / float(count)) * TAU
		var pos := center + Vector2(cos(angle), sin(angle)) * radius
		var glyph_text: String = glyphs[i % glyphs.size()]

		var lbl := _make_glyph(glyph_text, pos - Vector2(8, 10))
		lbl.scale = Vector2(0.5, 0.5)
		lbl.pivot_offset = Vector2(8, 10)
		ring_labels.append(lbl)

		var char_delay := delay_time + i * stagger
		var expand_target := pos + (pos - center).normalized() * radius * 0.12 - Vector2(8, 10)

		var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_interval(char_delay)
		tw.tween_property(lbl, "modulate:a", 1.0, duration * 0.3)
		tw.parallel().tween_property(lbl, "scale", Vector2.ONE, duration * 0.3)
		tw.parallel().tween_property(lbl, "position", expand_target, duration * 0.6)
		# Don't auto-fade — Phase 3 handles exit
		tw.tween_interval(duration * 0.5)
		tw.tween_property(lbl, "modulate:a", 0.6, duration * 0.2)

	_ring_glyphs_by_ring.append(ring_labels)

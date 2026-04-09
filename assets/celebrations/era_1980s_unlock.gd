extends "res://assets/celebrations/celebration_base.gd"

var _sweep_labels_1: Array[Label] = []
var _sweep_labels_2: Array[Label] = []
var _tick_marks: Array[Label] = []
var _box_frame_labels: Array[Label] = []
var _crosshair_labels: Array[Label] = []

func _get_shader() -> Shader:
	return load("res://assets/shaders/wave_surface.gdshader")


func _get_glyph_set() -> Array:
	return ["\u2500", "\u2501", "\u2550", "\u25aa", "\u25ab", "\u25fd", "\u25fe", "\u25a0"]


func _get_title_text() -> String:
	return "1980s"


func _run_sequence() -> void:
	var center := size / 2.0
	var glyphs := _get_glyph_set()

	# Phase 1 (0-1.2s): Shader + dual sweep lines + tick marks + triple bloom ping
	_fade_shader_in(0.4, 0.3)

	var sweep_count := 30
	var sweep_width := sweep_count * 9.0
	var sweep_start_x := center.x - sweep_width / 2.0

	# Sweep line 1: left to right
	for i in range(sweep_count):
		var x_pos := sweep_start_x + i * 9.0
		var lbl := _make_glyph("\u2500", Vector2(x_pos, center.y))
		_sweep_labels_1.append(lbl)

		var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_interval(0.3 + i * 0.02)
		tw.tween_property(lbl, "modulate:a", 0.6, 0.1)

		# Tick marks at every 5th position
		if i % 5 == 0:
			var tick := _make_glyph("\u2502", Vector2(x_pos, center.y - 12), ThemeConstants.BODY_DATA_SMALL_SIZE)
			_tick_marks.append(tick)
			var ttw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
			ttw.tween_interval(0.3 + i * 0.02 + 0.05)
			ttw.tween_property(tick, "modulate:a", 0.3, 0.1)

		# Fade sweep during title resolve
		var fade_tw := create_tween()
		fade_tw.tween_interval(1.5 + i * 0.01)
		fade_tw.tween_property(lbl, "modulate:a", 0.0, 0.5)

	# Sweep line 2: right to left, 4px below, 0.15s later
	for i in range(sweep_count):
		var ri := sweep_count - 1 - i
		var x_pos := sweep_start_x + ri * 9.0
		var lbl := _make_glyph("\u2500", Vector2(x_pos, center.y + 14))
		_sweep_labels_2.append(lbl)

		var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_interval(0.45 + i * 0.02)
		tw.tween_property(lbl, "modulate:a", 0.4, 0.1)

		if i % 5 == 0:
			var tick := _make_glyph("\u2502", Vector2(x_pos, center.y + 26), ThemeConstants.BODY_DATA_SMALL_SIZE)
			_tick_marks.append(tick)
			var ttw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
			ttw.tween_interval(0.45 + i * 0.02 + 0.05)
			ttw.tween_property(tick, "modulate:a", 0.3, 0.1)

		var fade_tw := create_tween()
		fade_tw.tween_interval(1.5 + ri * 0.01)
		fade_tw.tween_property(lbl, "modulate:a", 0.0, 0.5)

	# Fade tick marks
	for tick in _tick_marks:
		var ftw := create_tween()
		ftw.tween_interval(1.5)
		ftw.tween_property(tick, "modulate:a", 0.0, 0.4)

	# Triple bloom pings — center + left/right endpoints
	bloom_ring(center, glyphs.slice(3), 8, 100, 0.9, 0.8)
	bloom_ring(Vector2(sweep_start_x, center.y), ["\u25aa", "\u25ab"], 5, 40, 0.95, 0.6)
	bloom_ring(Vector2(sweep_start_x + sweep_width, center.y), ["\u25aa", "\u25ab"], 5, 40, 0.95, 0.6)

	# Phase 2 (1.2-2.6s): Title resolve + crosshairs + box frame
	var title := _get_title_text()
	resolve_title(title, center, 1.2, 0.15, 0.5)

	var char_w := 22.0
	var title_w := title.length() * char_w
	var title_start_x := center.x - title_w / 2.0

	# Crosshair tick marks above/below each scrambling position
	for i in range(title.length()):
		if title[i] == " ":
			continue
		var pos_x := title_start_x + i * char_w + 5
		var above := _make_glyph("\u2502", Vector2(pos_x, center.y - 46), ThemeConstants.BODY_DATA_SMALL_SIZE, ThemeConstants.TERTIARY)
		var below := _make_glyph("\u2502", Vector2(pos_x, center.y + 16), ThemeConstants.BODY_DATA_SMALL_SIZE, ThemeConstants.TERTIARY)
		_crosshair_labels.append(above)
		_crosshair_labels.append(below)

		var char_start := 1.2 + i * 0.15
		var char_end := char_start + 0.5

		for ch_lbl in [above, below]:
			var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
			tw.tween_interval(char_start)
			tw.tween_property(ch_lbl, "modulate:a", 0.4, 0.1)
			tw.tween_interval(0.5)
			tw.tween_property(ch_lbl, "modulate:a", 0.0, 0.15)

	# Box frame around title area — clockwise trace
	var box_left := title_start_x - 16
	var box_right := title_start_x + title_w + 8
	var box_top := center.y - 50
	var box_bottom := center.y + 24
	var frame_start := 1.3
	_draw_box_frame(box_left, box_right, box_top, box_bottom, frame_start)

	# Phase 3 (2.6-3.3s): Box frame pulse + scatter + final ping
	var phase3 := create_tween()
	phase3.tween_interval(2.6)
	phase3.tween_callback(func(): _phase3_exit(center))


func _draw_box_frame(left: float, right: float, top: float, bottom: float, start_time: float) -> void:
	var segments: Array[Dictionary] = []
	var seg_size := 9.0
	var total_time := 0.8

	# Top: left to right
	var top_count := int((right - left) / seg_size)
	for i in range(top_count):
		var ch := "\u250c" if i == 0 else ("\u2510" if i == top_count - 1 else "\u2500")
		segments.append({"ch": ch, "pos": Vector2(left + i * seg_size, top), "idx": i})
	var top_total := top_count

	# Right: top to bottom
	var right_count := int((bottom - top) / seg_size)
	for i in range(1, right_count):
		segments.append({"ch": "\u2502", "pos": Vector2(right - seg_size, top + i * seg_size), "idx": top_total + i})
	var right_total := top_total + right_count

	# Bottom: right to left
	for i in range(top_count):
		var ri := top_count - 1 - i
		var ch := "\u2518" if ri == top_count - 1 else ("\u2514" if ri == 0 else "\u2500")
		segments.append({"ch": ch, "pos": Vector2(left + ri * seg_size, bottom), "idx": right_total + i})
	var bottom_total := right_total + top_count

	# Left: bottom to top
	for i in range(1, right_count - 1):
		var ri := right_count - 1 - i
		segments.append({"ch": "\u2502", "pos": Vector2(left, top + ri * seg_size), "idx": bottom_total + i})

	var total_segs := segments.size()
	for seg in segments:
		var lbl := _make_glyph(seg["ch"], seg["pos"], ThemeConstants.BODY_DATA_SMALL_SIZE)
		_box_frame_labels.append(lbl)

		var delay_val: float = start_time + (float(seg["idx"]) / float(total_segs)) * total_time
		var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_interval(delay_val)
		tw.tween_property(lbl, "modulate:a", 0.5, 0.08)


func _phase3_exit(center: Vector2) -> void:
	# Box frame pulse
	for lbl in _box_frame_labels:
		if not is_instance_valid(lbl):
			continue
		var tw := create_tween()
		tw.tween_property(lbl, "modulate:a", 1.0, 0.1)
		tw.tween_property(lbl, "modulate:a", 0.5, 0.1)
		tw.tween_property(lbl, "modulate:a", 1.0, 0.1)

	# Box frame scatter outward after pulse
	var scatter_tw := create_tween()
	scatter_tw.tween_interval(0.35)
	scatter_tw.tween_callback(func():
		for lbl in _box_frame_labels:
			if not is_instance_valid(lbl):
				continue
			var dir := (lbl.position - center).normalized()
			var ftw := create_tween().set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_CUBIC)
			ftw.tween_property(lbl, "position", lbl.position + dir * 40, 0.3)
			ftw.parallel().tween_property(lbl, "modulate:a", 0.0, 0.3)
	)

	# Final sonar pings
	bloom_ring(center, ["\u25aa", "\u25ab"], 10, 120, 0.1, 0.4)

	# Cleanup remaining
	var finish := create_tween()
	finish.tween_interval(0.55)
	finish.tween_callback(func():
		for lbl in _glyph_pool:
			if is_instance_valid(lbl) and lbl.modulate.a > 0:
				var ftw := create_tween()
				ftw.tween_property(lbl, "modulate:a", 0.0, 0.2)
		_fade_shader_out(0.3)
	)
	finish.tween_interval(0.3)
	finish.tween_callback(func(): animation_finished.emit())

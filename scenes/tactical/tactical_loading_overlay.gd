extends CanvasLayer

# Shown while the simulation builds the navmesh and sends the first snapshot.
# Uses looping glyph bloom in the era's accent color.
# See also: simulation/movement.py — _ensure_navmesh() for the build cost.

const GLYPHS := ["\u00b7", "\u2727", "\u2726", "\u2736", "\u2739", "\u273a", "\u273b", "\u273d"]
const WAVE_INTERVAL := 2.2
const RING_COUNT := 8
const SCATTER_COUNT := 12
const RING_RADIUS := 120.0
const SCATTER_RADIUS := 180.0

var _active := true
var _accent: Color
var _glyph_layer: Control
var _bg: ColorRect
var _header: Label


func _ready() -> void:
	layer = 50
	_accent = Color("#c9a84c")

	_bg = ColorRect.new()
	_bg.color = ThemeConstants.BASE
	_bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	_bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_bg)

	_glyph_layer = Control.new()
	_glyph_layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	_glyph_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_glyph_layer)

	_header = Label.new()
	_header.text = "DEPLOYING FORCES"
	_header.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	_header.add_theme_font_size_override("font_size", ThemeConstants.CLASSIFICATION_LABEL_SIZE)
	_header.add_theme_color_override("font_color", _accent)
	_header.add_theme_constant_override("letter_spacing", ThemeConstants.CLASSIFICATION_LABEL_SPACING)
	_header.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_header.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_header.set_anchors_preset(Control.PRESET_CENTER)
	_header.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_header.custom_minimum_size.x = 600
	_header.position.y = -60
	add_child(_header)

	_fire_wave()


func dismiss() -> void:
	if not _active:
		return
	_active = false
	var tw := create_tween()
	tw.tween_property(_bg, "modulate:a", 0.0, 0.3)
	tw.parallel().tween_property(_header, "modulate:a", 0.0, 0.3)
	tw.parallel().tween_property(_glyph_layer, "modulate:a", 0.0, 0.3)
	tw.tween_callback(queue_free)


func _fire_wave() -> void:
	if not _active:
		return
	var center := _glyph_layer.get_viewport_rect().size / 2.0
	_bloom_ring(center, RING_COUNT, RING_RADIUS, 1.8)
	_bloom_scatter(center, SCATTER_COUNT, SCATTER_RADIUS, 1.8, 0.15)

	var tw := create_tween()
	tw.tween_interval(WAVE_INTERVAL)
	tw.tween_callback(_fire_wave)


func _bloom_ring(center: Vector2, count: int, radius: float, duration: float) -> void:
	var stagger := duration / float(count) / 3.0
	for i in range(count):
		var angle := (float(i) / float(count)) * TAU
		var pos := center + Vector2(cos(angle), sin(angle)) * radius
		var glyph_text: String = GLYPHS[i % GLYPHS.size()]

		var lbl := _make_glyph(glyph_text, pos - Vector2(8, 10))
		lbl.scale = Vector2(0.5, 0.5)
		lbl.pivot_offset = Vector2(8, 10)

		var char_delay := i * stagger
		var expand_target := pos + (pos - center).normalized() * radius * 0.12 - Vector2(8, 10)

		var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_interval(char_delay)
		tw.tween_property(lbl, "modulate:a", 0.6, duration * 0.3)
		tw.parallel().tween_property(lbl, "scale", Vector2.ONE, duration * 0.3)
		tw.parallel().tween_property(lbl, "position", expand_target, duration * 0.6)
		tw.tween_interval(duration * 0.2)
		tw.tween_property(lbl, "modulate:a", 0.0, duration * 0.3)
		tw.tween_callback(lbl.queue_free)


func _bloom_scatter(center: Vector2, count: int, radius: float, duration: float, delay_time: float) -> void:
	for i in range(count):
		var angle := randf() * TAU
		var dist := randf() * radius
		var pos := center + Vector2(cos(angle), sin(angle)) * dist
		var glyph_text: String = GLYPHS[i % GLYPHS.size()]

		var lbl := _make_glyph(glyph_text, pos - Vector2(8, 10))

		var drift := (pos - center).normalized() * randf_range(10, 20)
		var char_delay := delay_time + randf() * duration * 0.2

		var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_interval(char_delay)
		tw.tween_property(lbl, "modulate:a", 0.25, duration * 0.2)
		tw.parallel().tween_property(lbl, "position", lbl.position + drift, duration * 0.7)
		tw.tween_interval(duration * 0.3)
		tw.tween_property(lbl, "modulate:a", 0.0, duration * 0.3)
		tw.tween_callback(lbl.queue_free)


func _make_glyph(text: String, pos: Vector2) -> Label:
	var lbl := Label.new()
	lbl.text = text
	lbl.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	lbl.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
	lbl.add_theme_color_override("font_color", _accent)
	lbl.position = pos
	lbl.modulate.a = 0.0
	_glyph_layer.add_child(lbl)
	return lbl

extends Control

@export var value: float = 0.0:
	set(v):
		value = clampf(v, 0.0, 1.0)
		queue_redraw()

@export var max_display_value: float = 100.0
@export var bar_color: Color = Color("#5a8fbf")
@export var label_text: String = ""
@export var show_label: bool = false
@export var show_value: bool = false

var _display_value: float = 0.0
var _animated := false

func _ready() -> void:
	_update_min_size()


func _update_min_size() -> void:
	var label_height := ThemeConstants.BODY_DATA_SMALL_SIZE + 4 if show_label else 0
	custom_minimum_size.y = label_height + 14


func _draw() -> void:
	var label_height := ThemeConstants.BODY_DATA_SMALL_SIZE + 4 if show_label and label_text != "" else 0
	var bar_y: float = label_height + 4.0
	var bar_height := 4.0
	var bar_width := size.x
	if show_value:
		bar_width -= 50.0

	var bg_rect := Rect2(0, bar_y, bar_width, bar_height)
	draw_rect(bg_rect, ThemeConstants.SURFACE, true)

	var fill_width: float = bar_width * _display_value if _animated else bar_width * value
	if fill_width > 0:
		var fill_rect := Rect2(0, bar_y, fill_width, bar_height)
		draw_rect(fill_rect, bar_color, true)

	if show_label and label_text != "":
		var font := ThemeConstants.font_mono_regular
		draw_string(font, Vector2(0, label_height - 2), label_text, HORIZONTAL_ALIGNMENT_LEFT, -1, ThemeConstants.BODY_DATA_SMALL_SIZE, ThemeConstants.TERTIARY)

	if show_value:
		var font := ThemeConstants.font_mono_regular
		var display := _display_value if _animated else value
		var val_text := str(int(display * max_display_value))
		draw_string(font, Vector2(bar_width + 8, bar_y + bar_height + 2), val_text, HORIZONTAL_ALIGNMENT_LEFT, -1, ThemeConstants.BODY_DATA_SMALL_SIZE, ThemeConstants.PRIMARY)


func animate_in(delay: float) -> void:
	_animated = true
	_display_value = 0.0
	modulate.a = 0.0
	var tw := create_tween()
	tw.set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.tween_interval(delay)
	tw.tween_property(self, "modulate:a", 1.0, 0.3)
	tw.parallel().tween_method(_set_display_value, 0.0, value, ThemeConstants.STAT_BAR_DURATION)


func _set_display_value(v: float) -> void:
	_display_value = v
	queue_redraw()

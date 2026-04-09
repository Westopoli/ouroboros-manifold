extends ColorRect

@export var cursor_color: Color = Color("#c9a84c"):
	set(value):
		cursor_color = value
		color = value

var _blink_time := 0.0

func _ready() -> void:
	custom_minimum_size = Vector2(1, 14)
	size = Vector2(1, 14)
	color = cursor_color


func _process(delta: float) -> void:
	_blink_time += delta
	if fmod(_blink_time, ThemeConstants.CURSOR_BLINK_INTERVAL) < 0.5:
		modulate.a = 1.0
	else:
		modulate.a = 0.0

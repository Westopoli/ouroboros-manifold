extends ColorRect

func _ready() -> void:
	color = Color(1.0, 1.0, 1.0, 0.08)
	custom_minimum_size.y = 1
	size_flags_horizontal = Control.SIZE_EXPAND_FILL


func animate_in(delay: float) -> void:
	scale.x = 0.0
	pivot_offset.x = size.x / 2.0
	modulate.a = 0.0
	var tw := create_tween()
	tw.set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.tween_interval(delay)
	tw.tween_property(self, "modulate:a", 1.0, 0.2)
	tw.parallel().tween_property(self, "scale:x", 1.0, ThemeConstants.DIVIDER_EXPAND_DURATION)

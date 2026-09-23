extends Control

const FILL := Color(0.3, 0.8, 1.0, 0.08)
const EDGE := Color(0.3, 0.8, 1.0, 0.75)

var _rect: Rect2 = Rect2()
var active: bool = false


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func set_rect(r: Rect2, is_active: bool) -> void:
	_rect = r
	active = is_active
	visible = is_active
	queue_redraw()


func _draw() -> void:
	if not active:
		return
	draw_rect(_rect, FILL, true)
	draw_rect(_rect, EDGE, false, 1.5)

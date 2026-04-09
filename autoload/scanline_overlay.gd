extends CanvasLayer

func _ready() -> void:
	layer = 100
	var rect := ColorRect.new()
	rect.material = ShaderMaterial.new()
	rect.material.shader = load("res://theme/shaders/scanline.gdshader")
	rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(rect)

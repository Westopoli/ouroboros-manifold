@tool
extends Button

enum ButtonStyle { PRIMARY, SECONDARY }

@export var style: ButtonStyle = ButtonStyle.PRIMARY:
	set(value):
		style = value
		_apply_style()

@export var accent_color: Color = Color("#c9a84c"):
	set(value):
		accent_color = value
		_apply_style()

func _ready() -> void:
	_apply_style()
	mouse_entered.connect(_on_mouse_entered)
	mouse_exited.connect(_on_mouse_exited)
	button_down.connect(_on_button_down)
	button_up.connect(_on_button_up)


func _apply_style() -> void:
	if not Engine.is_editor_hint() and ThemeConstants:
		add_theme_font_override("font", ThemeConstants.font_mono_medium)
		add_theme_font_size_override("font_size", ThemeConstants.BUTTON_PRIMARY_SIZE)

	var normal := StyleBoxFlat.new()
	var hover := StyleBoxFlat.new()
	var pressed := StyleBoxFlat.new()

	for sb: StyleBoxFlat in [normal, hover, pressed]:
		sb.set_corner_radius_all(3)
		sb.content_margin_left = 10
		sb.content_margin_right = 10
		sb.content_margin_top = 8
		sb.content_margin_bottom = 8

	var tc := ThemeConstants if not Engine.is_editor_hint() and ThemeConstants else null

	if style == ButtonStyle.PRIMARY:
		normal.bg_color = accent_color
		hover.bg_color = accent_color.lightened(0.1)
		pressed.bg_color = accent_color.darkened(0.05)
		var dark_text := Color("#0a0a0c")
		add_theme_color_override("font_color", dark_text)
		add_theme_color_override("font_hover_color", dark_text)
		add_theme_color_override("font_pressed_color", dark_text)
		for sb: StyleBoxFlat in [normal, hover, pressed]:
			sb.border_color = Color.TRANSPARENT
	else:
		normal.bg_color = Color.TRANSPARENT
		hover.bg_color = Color.TRANSPARENT
		pressed.bg_color = Color("#111114") if not tc else tc.SURFACE
		var sec_color := Color(0.91, 0.90, 0.88, 0.55)
		var pri_color := Color("#e8e6e1")
		var border := Color(1.0, 1.0, 1.0, 0.08)
		add_theme_color_override("font_color", sec_color)
		add_theme_color_override("font_hover_color", pri_color)
		add_theme_color_override("font_pressed_color", pri_color)
		for sb: StyleBoxFlat in [normal, hover, pressed]:
			sb.set_border_width_all(1)
			sb.border_color = border
		hover.border_color = Color(1.0, 1.0, 1.0, 0.15)

	add_theme_stylebox_override("normal", normal)
	add_theme_stylebox_override("hover", hover)
	add_theme_stylebox_override("pressed", pressed)
	add_theme_stylebox_override("focus", StyleBoxEmpty.new())


func _on_mouse_entered() -> void:
	pass


func _on_mouse_exited() -> void:
	pass


func _on_button_down() -> void:
	var tw := create_tween()
	tw.tween_property(self, "scale", Vector2(0.97, 0.97), 0.05)


func _on_button_up() -> void:
	var tw := create_tween()
	tw.tween_property(self, "scale", Vector2.ONE, 0.1)

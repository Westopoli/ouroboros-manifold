@tool
extends PanelContainer

@export var card_title: String = "":
	set(value):
		card_title = value
		if _title_label:
			_title_label.text = value
			_title_label.visible = show_title and value != ""

@export var show_title: bool = true:
	set(value):
		show_title = value
		if _title_label:
			_title_label.visible = value and card_title != ""

var _title_label: Label
var _content_container: VBoxContainer
var _initial_position := Vector2.ZERO

func _ready() -> void:
	_apply_style()
	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 8)
	add_child(vbox)

	_title_label = Label.new()
	_title_label.text = card_title
	_title_label.uppercase = true
	_title_label.visible = show_title and card_title != ""
	if not Engine.is_editor_hint():
		_title_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		_title_label.add_theme_font_size_override("font_size", ThemeConstants.SECTION_LABEL_SIZE)
		_title_label.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	vbox.add_child(_title_label)

	_content_container = VBoxContainer.new()
	_content_container.add_theme_constant_override("separation", 6)
	vbox.add_child(_content_container)


func get_content_container() -> VBoxContainer:
	return _content_container


func _apply_style() -> void:
	var style := StyleBoxFlat.new()
	if not Engine.is_editor_hint():
		style.bg_color = ThemeConstants.CARD
		style.border_color = ThemeConstants.BORDER_COLOR
	else:
		style.bg_color = Color("#18181c")
		style.border_color = Color(1.0, 1.0, 1.0, 0.08)
	style.set_border_width_all(1)
	style.set_corner_radius_all(6)
	style.set_content_margin_all(0)
	style.content_margin_left = 14
	style.content_margin_right = 14
	style.content_margin_top = 16
	style.content_margin_bottom = 16
	add_theme_stylebox_override("panel", style)


func animate_in(delay: float) -> void:
	modulate.a = 0.0
	_initial_position = position
	position.y += 8.0
	var tw := create_tween()
	tw.set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.tween_interval(delay)
	tw.tween_property(self, "modulate:a", 1.0, ThemeConstants.ELEMENT_ANIM_DURATION)
	tw.parallel().tween_property(self, "position:y", _initial_position.y, ThemeConstants.ELEMENT_ANIM_DURATION)

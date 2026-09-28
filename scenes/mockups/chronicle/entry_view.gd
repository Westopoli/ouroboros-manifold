extends VBoxContainer

const SERIF_FONT := preload("res://theme/fonts/Newsreader-Light.ttf")

var entry_id: String = ""
var _root: Node
var _label: RichTextLabel
var _cursor: Label
var _mention_just_clicked: bool = false


func setup(root: Node) -> void:
	_root = root
	mouse_filter = Control.MOUSE_FILTER_STOP
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	add_theme_constant_override("separation", 2)
	_label = RichTextLabel.new()
	_label.bbcode_enabled = true
	_label.fit_content = true
	_label.scroll_active = false
	_label.mouse_filter = Control.MOUSE_FILTER_PASS
	_label.meta_clicked.connect(_on_meta_clicked)
	_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_label.add_theme_font_override("normal_font", SERIF_FONT)
	_label.add_theme_font_size_override("normal_font_size", 22)
	add_child(_label)
	_cursor = Label.new()
	_cursor.text = "_"
	_cursor.visible = false
	_cursor.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_cursor)


func render(row: Dictionary) -> void:
	entry_id = String(row.entry_id)
	var text := String(row.base_form)
	var words: PackedStringArray = text.split(" ", false)
	var ranges := word_ranges(text, words)
	var alphas: PackedFloat32Array = row.alphas
	var printed: int = int(row.printed_words)
	var mentions: Array = row.mentions
	var out := ""
	for i in range(words.size()):
		if i >= printed:
			break
		if i > 0:
			out += " "
		var a: float = alphas[i] if i < alphas.size() else 1.0
		var m := mention_for(ranges[i], mentions)
		var c := color_for(m)
		var piece := "[color=#%02x%02x%02x%02x]%s[/color]" % [int(c.r * 255), int(c.g * 255), int(c.b * 255), int(a * c.a * 255), words[i]]
		if not m.is_empty():
			piece = "[url=%s:%s]%s[/url]" % [m.get("kind", ""), m.get("id", ""), piece]
		out += piece
	_label.text = out
	_cursor.visible = printed >= int(row.total_words)


func _on_meta_clicked(meta: Variant) -> void:
	var meta_str := String(meta)
	var sep := meta_str.find(":")
	if sep < 0:
		return
	var kind := meta_str.substr(0, sep)
	var id := meta_str.substr(sep + 1)
	_mention_just_clicked = true
	if _root != null and _root.has_method("qa_click_mention"):
		_root.qa_click_mention(kind, id)


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		if _mention_just_clicked:
			_mention_just_clicked = false
			return
		if _root != null:
			_root.qa_click_entry(entry_id)


static func word_ranges(text: String, words: PackedStringArray) -> Array:
	var out: Array = []
	var cursor := 0
	for w in words:
		var s := text.find(w, cursor)
		if s < 0:
			out.append([cursor, cursor])
		else:
			out.append([s, s + w.length()])
			cursor = s + w.length()
	return out


static func mention_for(word_range: Array, mentions: Array) -> Dictionary:
	for m in mentions:
		var ms := int(m.get("span_start", -1))
		var me := int(m.get("span_end", -1))
		if ms < word_range[1] and me > word_range[0]:
			return m
	return {}


static func color_for(m: Dictionary) -> Color:
	if m.is_empty():
		return Color(0.86, 0.85, 0.82, 0.92)
	if String(m.get("kind", "")) == "faction":
		return Color.from_hsv(float(posmod(String(m.get("id", "")).hash(), 360)) / 360.0, 0.65, 0.92)
	return Color(0.75, 0.82, 0.9, 0.95)


static func build_bbcode(text: String, mentions: Array) -> String:
	var words: PackedStringArray = text.split(" ", false)
	var ranges := word_ranges(text, words)
	var out := ""
	for i in range(words.size()):
		if i > 0:
			out += " "
		var m := mention_for(ranges[i], mentions)
		var c := color_for(m)
		var piece := "[color=#%02x%02x%02x%02x]%s[/color]" % [int(c.r * 255), int(c.g * 255), int(c.b * 255), int(c.a * 255), words[i]]
		if not m.is_empty():
			piece = "[url=%s:%s]%s[/url]" % [m.get("kind", ""), m.get("id", ""), piece]
		out += piece
	return out

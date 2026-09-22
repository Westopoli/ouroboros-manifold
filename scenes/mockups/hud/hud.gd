extends CanvasLayer

const TYPE_NAMES := ["scout", "line"]
const LAYER_COLORS := {1: Color(0.3, 0.8, 1.0), 2: Color(1.0, 0.55, 0.0)}
const ACTIVE_COLOR := Color(0.3, 0.8, 1.0)
const DIM := Color(0.91, 0.90, 0.88, 0.55)
const TEXT := Color(0.91, 0.90, 0.88, 1.0)

class BoxOverlay extends Control:
	var router: Node
	var _was_active := false

	func _process(_delta: float) -> void:
		var active: bool = router != null and router.box_active
		if active or active != _was_active:
			queue_redraw()
		_was_active = active

	func _draw() -> void:
		if router == null or not router.box_active:
			return
		var current := get_viewport().get_mouse_position()
		var rect := Rect2(router.box_start, Vector2.ZERO).expand(current)
		draw_rect(rect, Color(0.3, 0.8, 1.0, 0.08), true)
		draw_rect(rect, Color(0.3, 0.8, 1.0, 0.75), false, 1.5)

var _root
var _selection

var _objective_label: Label
var _objective_bar: ColorRect
var _clock_label: Label
var _selection_header: Label
var _selection_rows: VBoxContainer
var _group_tabs: Array[Label] = []
var _layer_slots: Array[Label] = []
var _last_rows_key := ""


func setup(root) -> void:
	_root = root
	_selection = root._selection
	_build_objective()
	_build_clock()
	_build_selection_panel()
	_build_group_tabs()
	_build_layer_strip()
	_build_overlay()
	var all: Array = []
	_collect(self, all)
	for c in all:
		c.focus_mode = Control.FOCUS_NONE


func _collect(node: Node, out: Array) -> void:
	for c in node.get_children():
		if c is Control:
			out.append(c)
		_collect(c, out)


func _build_objective() -> void:
	var panel := Control.new()
	panel.anchor_left = 0; panel.anchor_top = 0
	panel.position = Vector2(16, 16)
	panel.custom_minimum_size = Vector2(360, 30)
	add_child(panel)
	_objective_label = Label.new()
	_objective_label.add_theme_color_override("font_color", TEXT)
	panel.add_child(_objective_label)
	_objective_bar = ColorRect.new()
	_objective_bar.color = ACTIVE_COLOR
	_objective_bar.position = Vector2(0, 22)
	_objective_bar.size = Vector2(0, 6)
	panel.add_child(_objective_bar)


func _build_clock() -> void:
	_clock_label = Label.new()
	_clock_label.anchor_left = 1; _clock_label.anchor_right = 1
	_clock_label.position = Vector2(-96, 16)
	_clock_label.add_theme_color_override("font_color", TEXT)
	add_child(_clock_label)


func _build_selection_panel() -> void:
	var panel := VBoxContainer.new()
	panel.anchor_left = 0.5; panel.anchor_right = 0.5
	panel.anchor_top = 1; panel.anchor_bottom = 1
	panel.position = Vector2(-180, -190)
	add_child(panel)
	_selection_header = Label.new()
	_selection_header.add_theme_color_override("font_color", DIM)
	panel.add_child(_selection_header)
	_selection_rows = VBoxContainer.new()
	panel.add_child(_selection_rows)


func _build_group_tabs() -> void:
	var hbox := HBoxContainer.new()
	hbox.anchor_left = 0.5; hbox.anchor_right = 0.5
	hbox.anchor_top = 1; hbox.anchor_bottom = 1
	hbox.position = Vector2(-135, -50)
	add_child(hbox)
	for i in range(1, 10):
		var lbl := Label.new()
		lbl.custom_minimum_size = Vector2(30, 28)
		lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		lbl.text = "%d\n-" % i
		lbl.add_theme_font_size_override("font_size", 11)
		lbl.add_theme_color_override("font_color", DIM)
		_group_tabs.append(lbl)
		hbox.add_child(lbl)


func _build_layer_strip() -> void:
	var vbox := VBoxContainer.new()
	vbox.anchor_left = 1; vbox.anchor_right = 1
	vbox.anchor_top = 0.5; vbox.anchor_bottom = 0.5
	vbox.position = Vector2(-64, -60)
	add_child(vbox)
	for i in [1, 2]:
		var lbl := Label.new()
		lbl.custom_minimum_size = Vector2(48, 40)
		lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		lbl.text = "L%d" % i
		lbl.add_theme_color_override("font_color", DIM)
		_layer_slots.append(lbl)
		vbox.add_child(lbl)
	var hint := Label.new()
	hint.text = "Q/E narrow"
	hint.add_theme_font_size_override("font_size", 11)
	hint.add_theme_color_override("font_color", DIM)
	vbox.add_child(hint)


func _build_overlay() -> void:
	var overlay := BoxOverlay.new()
	overlay.name = "BoxOverlay"
	overlay.anchor_right = 1
	overlay.anchor_bottom = 1
	overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	overlay.router = _root.get_node("Input")
	add_child(overlay)


func compute_rows(uids: Array, units: Dictionary) -> Array:
	var order: Array = []
	var rows: Dictionary = {}
	for uid in uids:
		var key := str(uid)
		if not units.has(key):
			continue
		var rec: Dictionary = units[key]
		var t: String = TYPE_NAMES[int(uid) % TYPE_NAMES.size()]
		if not rows.has(t):
			rows[t] = {"type": t, "count": 0, "hp": 0.0, "layers": []}
			order.append(t)
		rows[t].count += 1
		rows[t].hp += float(rec.hp)
		rows[t].layers.append(int(rec.layer))
	var out: Array = []
	for t in order:
		out.append(rows[t])
	return out


func sync(state: Dictionary) -> void:
	var obj: Dictionary = state.objective
	var progress: float = float(obj.progress)
	var filled := int(round(progress * 10.0))
	var bar := "▮".repeat(filled) + "▯".repeat(10 - filled)
	_objective_label.text = "HOLD  %s  %s  %d%%" % [obj.name, bar, int(round(progress * 100.0))]
	_objective_bar.size.x = 320.0 * progress

	var secs := int(state.clock_s)
	_clock_label.text = "%02d:%02d" % [secs / 60, secs % 60]

	var selected: Array = state.selected
	_selection_header.text = "SELECTION (%d)" % selected.size()
	var rows := compute_rows(selected, state.units)
	var rows_key := str(rows)
	if rows_key != _last_rows_key:
		_last_rows_key = rows_key
		for c in _selection_rows.get_children():
			c.free()
		for row in rows:
			var hb := HBoxContainer.new()
			var lbl := Label.new()
			lbl.text = "%s x%d  %d hp" % [row.type, row.count, int(row.hp)]
			lbl.add_theme_color_override("font_color", TEXT)
			hb.add_child(lbl)
			for layer in row.layers:
				var dot := ColorRect.new()
				dot.color = LAYER_COLORS.get(layer, TEXT)
				dot.custom_minimum_size = Vector2(8, 8)
				hb.add_child(dot)
			_selection_rows.add_child(hb)

	var groups: Dictionary = state.groups
	for i in range(_group_tabs.size()):
		var digit := i + 1
		var count: int = groups[str(digit)].size() if groups.has(str(digit)) else 0
		var active: bool = digit == _selection.last_recall_digit
		_group_tabs[i].text = "%d\n%s" % [digit, (str(count) if count > 0 else "-")]
		_group_tabs[i].add_theme_color_override("font_color", ACTIVE_COLOR if active else DIM)

	for i in range(_layer_slots.size()):
		var on: bool = (i + 1) == int(state.focus_layer)
		_layer_slots[i].add_theme_color_override("font_color", ACTIVE_COLOR if on else DIM)

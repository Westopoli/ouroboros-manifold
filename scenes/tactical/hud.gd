## Mid-mission HUD per docs/bible_history/bible_2_00_combat.md §"Mid-Mission HUD Layout" (IGoP-inspired).
## Layout built in code — no tscn children. Subscribes to TacticalBridge for
## tick-driven data (units/structures/objectives/events) and reads selection +
## active_layer from sibling InputRouter each frame.
extends CanvasLayer

const _PANEL_BG := Color(0.05, 0.08, 0.12, 0.82)
const _PANEL_BORDER := Color(0.35, 0.45, 0.55, 0.9)
const _TEXT := Color(0.92, 0.93, 0.95)
const _DIM  := Color(0.60, 0.62, 0.70)
const _LAYER_ACTIVE := Color(0.3, 0.85, 1.0)
const _BANNER_COLOR := Color(1.0, 0.80, 0.40)
const _FACTION_COLORS := [Color(0.30, 0.70, 1.00), Color(1.00, 0.35, 0.35)]
const _OBJ_PRIMARY_BAR := Color(0.3, 0.85, 1.0)
const _OBJ_SECONDARY_BAR := Color(0.4, 0.5, 0.6)
const _OBJ_BAR_BG := Color(0.15, 0.18, 0.22)
const _OBJ_BAR_HEIGHT := 6.0
const _OBJ_BAR_WIDTH := 320.0
# See also: simulation/snapshot_serializer.py — objective type + is_primary source
const _OBJ_DESCRIPTIONS: Dictionary = {
	"hold_zone": "Hold the zone",
	"clear_zone": "Clear the zone",
	"eliminate_force": "Destroy enemy force",
	"escort_to_extraction": "Escort to extraction",
	"survive_duration": "Survive",
	"destroy_targets": "Destroy targets",
}
const _MAX_EVENTS := 4
const _BANNER_DURATION := 4.0
const _MINIMAP_SIZE := Vector2(330, 330)  # 1.5× base; IGoP-scale presence at bottom-left
const _TICK_HZ := 20.0

var _input_router: Node

var _objectives_list: VBoxContainer
var _event_ticker_list: VBoxContainer
var _banner_label: Label
var _clock_label: Label
var _minimap: Control
var _selection_content: VBoxContainer
var _structure_list: VBoxContainer
var _control_group_labels: Array = []
var _layer_buttons: Array = []
var _layer_readout_label: Label
var _layer_markers: Array = []  # 5 ColorRect markers

var _banner_timer: float = 0.0
var _start_tick: int = -1

var _f12_label: Label
var _f12_age: float = 0.0
const _F12_FADE_TIME := 30.0
const _F12_MIN_ALPHA := 0.15
const _F12_FLASH_DURATION := 0.5
var _f12_flash_timer: float = 0.0


func _ready() -> void:
	layer = 10
	_input_router = get_node("../InputRouter")
	_build_ui()
	TacticalBridge.snapshot_received.connect(_on_snapshot)
	TacticalBridge.tick_delta_received.connect(_on_delta)


func _process(delta: float) -> void:
	_update_clock()
	_update_selection_panel()
	_update_layer_selector()
	_update_layer_readout()
	_update_control_groups()
	if _minimap:
		_minimap.queue_redraw()
	if _banner_timer > 0.0:
		_banner_timer -= delta
		if _banner_timer <= 0.0:
			var tw := create_tween()
			tw.tween_property(_banner_label, "modulate:a", 0.0, 0.4)
			tw.tween_callback(func(): _banner_label.visible = false)
	_update_f12_label(delta)


# ── Signals ──────────────────────────────────────────────────────────────────

func _on_snapshot(snap: Dictionary) -> void:
	if _start_tick < 0:
		_start_tick = snap.get("tick", 0)
	_rebuild_objectives()
	_rebuild_structure_list()


func _on_delta(d: Dictionary) -> void:
	_update_objectives()
	_update_structure_list()
	for ev in d.get("events", []):
		_handle_event(ev)


func _handle_event(ev: Dictionary) -> void:
	var kind: String = ev.get("kind", "")
	var text := ""
	var banner := false
	match kind:
		"unit_destroyed":
			text = "Unit destroyed"
		"structure_captured":
			text = "Structure captured"
			banner = true
		"structure_lost":
			text = "Structure lost"
			banner = true
		"objective_threshold":
			text = "Objective threshold crossed"
			banner = true
		_:
			return
	_append_event(text)
	if banner:
		_show_banner(text)


func _append_event(text: String) -> void:
	var lbl := Label.new()
	lbl.text = text
	lbl.add_theme_color_override("font_color", _TEXT)
	lbl.modulate.a = 0.0
	lbl.position.x = -20.0
	_event_ticker_list.add_child(lbl)
	var tw := create_tween().set_parallel(true)
	tw.tween_property(lbl, "modulate:a", 1.0, 0.3)
	tw.tween_property(lbl, "position:x", 0.0, 0.3).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_QUAD)
	while _event_ticker_list.get_child_count() > _MAX_EVENTS:
		var old := _event_ticker_list.get_child(0)
		_event_ticker_list.remove_child(old)
		old.free()


func _show_banner(text: String) -> void:
	_banner_label.text = text
	_banner_label.visible = true
	_banner_label.modulate.a = 0.0
	var tw := create_tween()
	tw.tween_property(_banner_label, "modulate:a", 1.0, 0.25)
	_banner_timer = _BANNER_DURATION


# ── Per-frame panel updates ──────────────────────────────────────────────────

func _update_clock() -> void:
	var elapsed_ticks: int = TacticalBridge.current_tick - max(0, _start_tick)
	var secs: float = max(0.0, elapsed_ticks) / _TICK_HZ
	var m: int = int(secs) / 60
	var s: int = int(secs) % 60
	_clock_label.text = "%02d:%02d" % [m, s]


func _update_selection_panel() -> void:
	var selected: Array = _input_router.selected_uids
	for child in _selection_content.get_children():
		child.queue_free()
	if selected.is_empty():
		var lbl := Label.new()
		lbl.text = "(no selection)"
		lbl.add_theme_color_override("font_color", _DIM)
		_selection_content.add_child(lbl)
		return
	var total_hp := 0
	var total_max := 0
	var types := {}
	var min_cd := INF
	for uid in selected:
		if uid not in TacticalBridge.units:
			continue
		var u: Dictionary = TacticalBridge.units[uid]
		total_hp += int(u.get("hp", 0))
		total_max += int(u.get("max_hp", 0))
		var t: String = u.get("type", "?")
		types[t] = types.get(t, 0) + 1
		var cd: float = u.get("ability_cd_sec", 0.0)
		if cd < min_cd:
			min_cd = cd
	var type_parts: Array[String] = []
	for t in types.keys():
		type_parts.append("%s ×%d" % [t, types[t]])
	var title := Label.new()
	title.text = ", ".join(type_parts)
	title.add_theme_color_override("font_color", _TEXT)
	_selection_content.add_child(title)
	var hp_lbl := Label.new()
	hp_lbl.text = "HP %d / %d" % [total_hp, total_max]
	hp_lbl.add_theme_color_override("font_color", _TEXT)
	_selection_content.add_child(hp_lbl)
	# Ability cooldown ring per docs/bible_history/bible_2_00_combat.md §Mid-Mission HUD Layout:
	# "ability slots showing cooldown rings ... no 'ready' notifications beyond the ring itself."
	var ring := _AbilityRing.new()
	ring.set_cd(min_cd if min_cd != INF else 0.0)
	_selection_content.add_child(ring)


func _update_layer_selector() -> void:
	var active: int = _input_router.active_layer
	for i in range(_layer_buttons.size()):
		var btn: Button = _layer_buttons[i]
		if i == active:
			btn.add_theme_color_override("font_color", _LAYER_ACTIVE)
			btn.modulate = Color(1, 1, 1, 1)
		else:
			btn.add_theme_color_override("font_color", _DIM)
			btn.modulate = Color(1, 1, 1, 0.6)


func _update_control_groups() -> void:
	var groups: Dictionary = _input_router._control_groups
	for i in range(10):
		var group_id: int = i + 1
		var lbl: Label = _control_group_labels[i]
		var uids: Array = groups.get(group_id, [])
		var live: Array[int] = []
		for uid in uids:
			if uid in TacticalBridge.units:
				live.append(uid)
		if live.is_empty():
			lbl.text = "%d\n—" % (group_id % 10)
			lbl.add_theme_color_override("font_color", _DIM)
		else:
			var types := {}
			for uid in live:
				var t: String = TacticalBridge.units[uid].get("type", "?")
				types[t] = types.get(t, 0) + 1
			var dominant := "?"
			var dom_n := 0
			for t in types:
				if types[t] > dom_n:
					dom_n = types[t]
					dominant = t
			lbl.text = "%d\n%s\n%d" % [group_id % 10, dominant.substr(0, 4), live.size()]
			lbl.add_theme_color_override("font_color", _TEXT)


func _rebuild_objectives() -> void:
	_clear_children(_objectives_list)
	if TacticalBridge.objectives.is_empty():
		var lbl := Label.new()
		lbl.text = "(no objectives)"
		lbl.add_theme_color_override("font_color", _DIM)
		_objectives_list.add_child(lbl)
		return
	var sorted_objs: Array = TacticalBridge.objectives.duplicate()
	sorted_objs.sort_custom(func(a, b): return a.get("is_primary", false) and not b.get("is_primary", false))
	for obj in sorted_objs:
		var is_primary: bool = obj.get("is_primary", false)
		var prog: float = obj.get("progress", 0.0)
		var obj_type: String = obj.get("type", "")
		var status: String = obj.get("status", "in_progress")
		var desc: String = _OBJ_DESCRIPTIONS.get(obj_type, obj_type)
		if status == "complete":
			desc += " — COMPLETE"
		elif status == "failed":
			desc += " — FAILED"
		var row := VBoxContainer.new()
		row.add_theme_constant_override("separation", 2)
		row.set_meta("obj_id", obj.get("id", ""))
		var lbl := Label.new()
		lbl.text = desc
		lbl.add_theme_font_size_override("font_size", 15 if is_primary else 12)
		lbl.add_theme_color_override("font_color", _TEXT if is_primary else _DIM)
		row.add_child(lbl)
		var bar_bg := ColorRect.new()
		bar_bg.custom_minimum_size = Vector2(_OBJ_BAR_WIDTH, _OBJ_BAR_HEIGHT)
		bar_bg.color = _OBJ_BAR_BG
		row.add_child(bar_bg)
		var bar_fill := ColorRect.new()
		bar_fill.custom_minimum_size = Vector2(_OBJ_BAR_WIDTH * clampf(prog, 0.0, 1.0), _OBJ_BAR_HEIGHT)
		bar_fill.color = _OBJ_PRIMARY_BAR if is_primary else _OBJ_SECONDARY_BAR
		bar_fill.position = Vector2.ZERO
		bar_bg.add_child(bar_fill)
		_objectives_list.add_child(row)


func _rebuild_structure_list() -> void:
	_clear_children(_structure_list)
	_update_structure_list()


func _update_objectives() -> void:
	var children := _objectives_list.get_children()
	if TacticalBridge.objectives.is_empty():
		if children.size() != 1:
			_rebuild_objectives()
		return
	if children.size() != TacticalBridge.objectives.size():
		_rebuild_objectives()
		return
	var obj_by_id: Dictionary = {}
	for obj in TacticalBridge.objectives:
		obj_by_id[obj.get("id", "")] = obj
	for row in children:
		if not row.has_meta("obj_id"):
			continue
		var obj_id: String = row.get_meta("obj_id")
		var obj: Dictionary = obj_by_id.get(obj_id, {})
		if obj.is_empty():
			continue
		var prog: float = obj.get("progress", 0.0)
		var status: String = obj.get("status", "in_progress")
		var obj_type: String = obj.get("type", "")
		var desc: String = _OBJ_DESCRIPTIONS.get(obj_type, obj_type)
		if status == "complete":
			desc += " — COMPLETE"
		elif status == "failed":
			desc += " — FAILED"
		var lbl: Label = row.get_child(0)
		lbl.text = desc
		var bar_bg: ColorRect = row.get_child(1)
		var bar_fill: ColorRect = bar_bg.get_child(0)
		bar_fill.custom_minimum_size.x = _OBJ_BAR_WIDTH * clampf(prog, 0.0, 1.0)


func _update_structure_list() -> void:
	var player_structs: Array = []
	for uid in TacticalBridge.structures:
		var s: Dictionary = TacticalBridge.structures[uid]
		if int(s.get("owner", -1)) != 0:
			continue
		player_structs.append({"uid": uid, "data": s})

	var children := _structure_list.get_children()

	if player_structs.is_empty():
		if children.size() != 1 or children[0].text != "(no structures held)":
			_clear_children(_structure_list)
			var lbl := Label.new()
			lbl.text = "(no structures held)"
			lbl.add_theme_color_override("font_color", _DIM)
			_structure_list.add_child(lbl)
		return

	if children.size() != player_structs.size():
		_clear_children(_structure_list)
		for ps in player_structs:
			var row := Label.new()
			row.add_theme_color_override("font_color", _TEXT)
			_structure_list.add_child(row)
		children = _structure_list.get_children()

	for i in player_structs.size():
		var uid: int = player_structs[i].uid
		var s: Dictionary = player_structs[i].data
		var hp: int = int(s.get("hp", 0))
		var max_hp: int = int(s.get("max_hp", 1))
		var prod_sec: float = s.get("production_timer_sec", 0.0)
		var prod_target: String = s.get("production_target", "—")
		children[i].text = "[%d] HP %d/%d  %s in %ds" % [uid, hp, max_hp, prod_target, int(prod_sec)]


func _clear_children(container: Container) -> void:
	for child in container.get_children():
		container.remove_child(child)
		child.free()


# ── UI construction ──────────────────────────────────────────────────────────

func _styled_panel() -> PanelContainer:
	var p := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = _PANEL_BG
	sb.border_color = _PANEL_BORDER
	sb.border_width_left = 1
	sb.border_width_top = 1
	sb.border_width_right = 1
	sb.border_width_bottom = 1
	sb.corner_radius_top_left = 4
	sb.corner_radius_top_right = 4
	sb.corner_radius_bottom_left = 4
	sb.corner_radius_bottom_right = 4
	sb.content_margin_left = 10
	sb.content_margin_right = 10
	sb.content_margin_top = 6
	sb.content_margin_bottom = 6
	p.add_theme_stylebox_override("panel", sb)
	return p


func _place_top_left(ctrl: Control, x: float, y: float, w: float, h: float) -> void:
	ctrl.anchor_left = 0; ctrl.anchor_right = 0
	ctrl.anchor_top = 0;  ctrl.anchor_bottom = 0
	ctrl.offset_left = x
	ctrl.offset_right = x + w
	ctrl.offset_top = y
	ctrl.offset_bottom = y + h


func _place_top_right(ctrl: Control, x_from_right: float, y: float, w: float, h: float) -> void:
	ctrl.anchor_left = 1; ctrl.anchor_right = 1
	ctrl.anchor_top = 0;  ctrl.anchor_bottom = 0
	ctrl.offset_left = -x_from_right - w
	ctrl.offset_right = -x_from_right
	ctrl.offset_top = y
	ctrl.offset_bottom = y + h


func _place_top_center(ctrl: Control, y: float, w: float, h: float) -> void:
	ctrl.anchor_left = 0.5; ctrl.anchor_right = 0.5
	ctrl.anchor_top = 0;    ctrl.anchor_bottom = 0
	ctrl.offset_left = -w / 2.0
	ctrl.offset_right = w / 2.0
	ctrl.offset_top = y
	ctrl.offset_bottom = y + h


func _place_bottom_left(ctrl: Control, x: float, y_from_bottom: float, w: float, h: float) -> void:
	ctrl.anchor_left = 0; ctrl.anchor_right = 0
	ctrl.anchor_top = 1;  ctrl.anchor_bottom = 1
	ctrl.offset_left = x
	ctrl.offset_right = x + w
	ctrl.offset_top = -y_from_bottom - h
	ctrl.offset_bottom = -y_from_bottom


func _place_bottom_right(ctrl: Control, x_from_right: float, y_from_bottom: float, w: float, h: float) -> void:
	ctrl.anchor_left = 1; ctrl.anchor_right = 1
	ctrl.anchor_top = 1;  ctrl.anchor_bottom = 1
	ctrl.offset_left = -x_from_right - w
	ctrl.offset_right = -x_from_right
	ctrl.offset_top = -y_from_bottom - h
	ctrl.offset_bottom = -y_from_bottom


func _build_ui() -> void:
	_build_info_column()
	_build_banner()
	_build_clock()
	_build_minimap_panel()        # bottom-left
	_build_structure_panel()      # right of minimap
	_build_selection_panel()      # bottom-center
	_build_control_group_bar()    # bottom-right, left of layer selector
	_build_layer_selector()       # right edge
	_build_layer_readout()        # above layer selector
	_build_f12_label()


func _build_info_column() -> void:
	var panel := _styled_panel()
	_place_top_left(panel, 12, 12, 360, 380)

	var vbox := VBoxContainer.new()
	panel.add_child(vbox)

	var oh := Label.new(); oh.text = "OBJECTIVES"
	oh.add_theme_color_override("font_color", _DIM)
	vbox.add_child(oh)
	_objectives_list = VBoxContainer.new()
	vbox.add_child(_objectives_list)

	var spacer := Control.new()
	spacer.custom_minimum_size = Vector2(0, 14)
	vbox.add_child(spacer)

	var eh := Label.new(); eh.text = "EVENTS"
	eh.add_theme_color_override("font_color", _DIM)
	vbox.add_child(eh)
	_event_ticker_list = VBoxContainer.new()
	vbox.add_child(_event_ticker_list)

	add_child(panel)


func _build_banner() -> void:
	_banner_label = Label.new()
	_place_top_center(_banner_label, 30, 600, 32)
	_banner_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_banner_label.add_theme_font_size_override("font_size", 22)
	_banner_label.add_theme_color_override("font_color", _BANNER_COLOR)
	_banner_label.visible = false
	add_child(_banner_label)


func _build_clock() -> void:
	var panel := _styled_panel()
	_place_top_right(panel, 12, 12, 160, 38)

	var hbox := HBoxContainer.new()
	panel.add_child(hbox)

	_clock_label = Label.new()
	_clock_label.text = "00:00"
	_clock_label.add_theme_color_override("font_color", _TEXT)
	_clock_label.add_theme_font_size_override("font_size", 18)
	hbox.add_child(_clock_label)

	var spacer := Control.new()
	spacer.custom_minimum_size = Vector2(12, 0)
	hbox.add_child(spacer)

	var menu := Button.new()
	menu.text = "☰"
	menu.custom_minimum_size = Vector2(32, 0)
	hbox.add_child(menu)

	add_child(panel)


func _build_minimap_panel() -> void:
	var panel := _styled_panel()
	var panel_h: float = _MINIMAP_SIZE.y + 24
	_place_bottom_left(panel, 12, 12, _MINIMAP_SIZE.x + 20, panel_h)
	_minimap = _Minimap.new()
	_minimap.custom_minimum_size = _MINIMAP_SIZE
	_minimap.camera = get_viewport().get_camera_3d()
	panel.add_child(_minimap)
	add_child(panel)


func _build_structure_panel() -> void:
	# Right of minimap. Stage 8 scope: text rows per player-owned structure.
	# Future: IGoP-style hotkey-labeled production tiles (TRAIN/TECH/BUILD/POWER analogue).
	var panel := _styled_panel()
	var panel_h: float = _MINIMAP_SIZE.y + 24
	var x_from_left: float = 12 + _MINIMAP_SIZE.x + 20 + 8
	_place_bottom_left(panel, x_from_left, 12, 360, panel_h)
	var vbox := VBoxContainer.new()
	panel.add_child(vbox)
	var hdr := Label.new(); hdr.text = "REINFORCEMENTS"
	hdr.add_theme_color_override("font_color", _DIM)
	vbox.add_child(hdr)
	_structure_list = VBoxContainer.new()
	vbox.add_child(_structure_list)
	add_child(panel)


func _build_selection_panel() -> void:
	var panel := _styled_panel()
	_place_bottom_center(panel, 12, 360, 180)
	var vbox := VBoxContainer.new()
	panel.add_child(vbox)
	var hdr := Label.new(); hdr.text = "SELECTION"
	hdr.add_theme_color_override("font_color", _DIM)
	vbox.add_child(hdr)
	_selection_content = VBoxContainer.new()
	vbox.add_child(_selection_content)
	add_child(panel)


func _place_bottom_center(ctrl: Control, y_from_bottom: float, w: float, h: float) -> void:
	ctrl.anchor_left = 0.5; ctrl.anchor_right = 0.5
	ctrl.anchor_top = 1;    ctrl.anchor_bottom = 1
	ctrl.offset_left = -w / 2.0
	ctrl.offset_right = w / 2.0
	ctrl.offset_top = -y_from_bottom - h
	ctrl.offset_bottom = -y_from_bottom


class _AbilityRing extends Control:
	const MAX_CD := 30.0
	var cd_sec: float = 0.0
	var _cd_label: Label

	func _init() -> void:
		custom_minimum_size = Vector2(32, 32)
		_cd_label = Label.new()
		_cd_label.anchor_left = 0; _cd_label.anchor_right = 1
		_cd_label.anchor_top = 0;  _cd_label.anchor_bottom = 1
		_cd_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		_cd_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		_cd_label.add_theme_font_size_override("font_size", 11)
		_cd_label.add_theme_color_override("font_color", Color(0.88, 0.90, 0.95))
		add_child(_cd_label)

	func set_cd(sec: float) -> void:
		cd_sec = sec
		_cd_label.text = "" if sec <= 0.0 else "%d" % ceil(sec)
		queue_redraw()

	func _draw() -> void:
		var r: float = min(size.x, size.y) / 2.0 - 2.0
		var c: Vector2 = size / 2.0
		if cd_sec <= 0.0:
			draw_arc(c, r, 0.0, TAU, 32, Color(0.35, 0.95, 0.55), 2.0, true)
		else:
			draw_circle(c, r, Color(0.10, 0.12, 0.15))
			draw_arc(c, r, 0.0, TAU, 32, Color(0.25, 0.28, 0.35), 1.5, true)
			# Sweep: filled arc from top, clockwise, proportional to cooldown elapsed
			var frac: float = clampf(cd_sec / MAX_CD, 0.0, 1.0)
			var sweep_angle: float = (1.0 - frac) * TAU
			if sweep_angle > 0.01:
				draw_arc(c, r, -PI / 2.0, -PI / 2.0 + sweep_angle, 32, Color(0.35, 0.75, 0.95, 0.8), 2.5, true)


class _Minimap extends Control:
	# See also: scripts/tactical/visibility.gd — fog gate
	var camera: Camera3D

	func _draw() -> void:
		var canvas_size := Vector2(16000, 16000)
		var md: Dictionary = TacticalBridge.map_data
		if "canvas_size" in md:
			canvas_size = Vector2(md["canvas_size"][0], md["canvas_size"][1])
		draw_rect(Rect2(Vector2.ZERO, size), Color(0.10, 0.12, 0.16), true)
		var sx: float = size.x / canvas_size.x
		var sy: float = size.y / canvas_size.y
		var faction_colors := [Color(0.30, 0.70, 1.00), Color(1.00, 0.35, 0.35)]
		for uid in range(TacticalBridge.unit_count):
			if TacticalBridge.display_alive[uid] == 0:
				continue
			if not Visibility.is_unit_visible_to_player(uid):
				continue
			var px: float = TacticalBridge.display_x[uid]
			var py: float = TacticalBridge.display_y[uid]
			var u: Dictionary = TacticalBridge.units.get(uid, {})
			var faction: int = int(u.get("faction", 0))
			var col: Color = faction_colors[faction] if faction < faction_colors.size() else Color.WHITE
			if faction != 0:
				col.a = EraConfig.MINIMAP_ENEMY_DIM_ALPHA
			draw_circle(Vector2(px * sx, py * sy), 2.0, col)
		for uid in TacticalBridge.structures:
			var s: Dictionary = TacticalBridge.structures[uid]
			var pos: Array = s.get("pos", [0, 0])
			var owner: int = int(s.get("owner", -1))  # faction int; 0=player, 1=enemy, -1=neutral
			var col: Color
			match owner:
				0:  col = Color(0.3, 0.9, 0.6)
				1:  col = Color(1.0, 0.4, 0.3)
				_:  col = Color(0.65, 0.65, 0.68)
			var rect_pos := Vector2(pos[0] * sx - 3, pos[1] * sy - 3)
			draw_rect(Rect2(rect_pos, Vector2(6, 6)), col, true)
		# Objective markers — always visible regardless of fog (briefing intel)
		for obj in TacticalBridge.objectives:
			var loc: Dictionary = obj.get("location", {})
			if loc.is_empty():
				continue
			var status: String = obj.get("status", "in_progress")
			if status == "complete" or status == "failed":
				continue
			var is_primary: bool = obj.get("is_primary", false)
			var col: Color = _OBJ_PRIMARY_BAR if is_primary else _OBJ_SECONDARY_BAR
			var mx: float = float(loc.get("x", 0.0)) * sx
			var my: float = float(loc.get("y", 0.0)) * sy
			var obj_type: String = obj.get("type", "")
			if obj_type in ["hold_zone", "clear_zone"]:
				draw_rect(Rect2(Vector2(mx - 4, my - 4), Vector2(8, 8)), col, true)
			elif obj_type == "eliminate_force":
				var pts := PackedVector2Array([
					Vector2(mx, my - 5), Vector2(mx + 5, my),
					Vector2(mx, my + 5), Vector2(mx - 5, my)])
				draw_colored_polygon(pts, col)
			elif obj_type == "escort_to_extraction":
				var pts := PackedVector2Array([
					Vector2(mx, my - 5), Vector2(mx + 4, my + 4), Vector2(mx - 4, my + 4)])
				draw_colored_polygon(pts, col)
			else:
				draw_circle(Vector2(mx, my), 3.0, col)
		# Viewport box — project camera frustum corners onto ground plane
		if not camera:
			camera = get_viewport().get_camera_3d()
		if camera and camera.is_inside_tree():
			var vp_size := camera.get_viewport().get_visible_rect().size
			var corners := [
				Vector2(0, 0), Vector2(vp_size.x, 0),
				Vector2(vp_size.x, vp_size.y), Vector2(0, vp_size.y)]
			var minimap_pts := PackedVector2Array()
			for corner in corners:
				var origin := camera.project_ray_origin(corner)
				var dir := camera.project_ray_normal(corner)
				if absf(dir.y) < 0.001:
					continue
				var t: float = -origin.y / dir.y
				var hit := origin + dir * t
				minimap_pts.append(Vector2(hit.x * sx, hit.z * sy))
			if minimap_pts.size() == 4:
				minimap_pts.append(minimap_pts[0])
				draw_polyline(minimap_pts, Color(1.0, 1.0, 1.0, 0.4), 1.5)


func _build_control_group_bar() -> void:
	# Bottom-right, left of the layer selector (64 wide + 12 gap + 12 right margin = 88).
	var panel := _styled_panel()
	_place_bottom_right(panel, 88, 12, 268, 56)

	var hbox := HBoxContainer.new()
	hbox.add_theme_constant_override("separation", 0)
	panel.add_child(hbox)
	for i in range(10):
		var lbl := Label.new()
		lbl.custom_minimum_size = Vector2(24, 44)
		lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		lbl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		lbl.autowrap_mode = TextServer.AUTOWRAP_OFF
		lbl.text = "%d\n—" % ((i + 1) % 10)
		lbl.add_theme_color_override("font_color", _DIM)
		lbl.add_theme_font_size_override("font_size", 11)
		_control_group_labels.append(lbl)
		hbox.add_child(lbl)
	add_child(panel)


func _build_layer_selector() -> void:
	var panel := _styled_panel()
	_place_bottom_right(panel, 12, 12, 64, 220)

	var vbox := VBoxContainer.new()
	panel.add_child(vbox)
	var header := Label.new(); header.text = "LYR"
	header.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	header.add_theme_color_override("font_color", _DIM)
	header.add_theme_font_size_override("font_size", 11)
	vbox.add_child(header)
	for i in range(5):
		var btn := Button.new()
		btn.text = "L%d" % i
		btn.custom_minimum_size = Vector2(44, 30)
		btn.pressed.connect(_on_layer_clicked.bind(i))
		_layer_buttons.append(btn)
		vbox.add_child(btn)
	add_child(panel)


func _on_layer_clicked(layer_idx: int) -> void:
	_input_router.active_layer = layer_idx


const _LAYER_COLORS: Array[Color] = [
	Color.TRANSPARENT,
	Color(0.00, 1.00, 1.00),
	Color(1.00, 1.00, 0.00),
	Color(1.00, 0.55, 0.00),
	Color(0.75, 0.20, 1.00),
]


func _build_layer_readout() -> void:
	var panel := _styled_panel()
	# Place above the layer selector (which is at bottom-right 12, 12, 64, 220)
	_place_bottom_right(panel, 12, 244, 64, 52)

	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 2)
	panel.add_child(vbox)

	_layer_readout_label = Label.new()
	_layer_readout_label.text = "L0 / 5"
	_layer_readout_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_layer_readout_label.add_theme_font_size_override("font_size", 13)
	_layer_readout_label.add_theme_color_override("font_color", _TEXT)
	vbox.add_child(_layer_readout_label)

	var marker_row := HBoxContainer.new()
	marker_row.add_theme_constant_override("separation", 2)
	marker_row.alignment = BoxContainer.ALIGNMENT_CENTER
	vbox.add_child(marker_row)
	for i in range(5):
		var marker := ColorRect.new()
		marker.custom_minimum_size = Vector2(8, 8)
		marker.color = _DIM
		marker_row.add_child(marker)
		_layer_markers.append(marker)

	add_child(panel)


func _update_layer_readout() -> void:
	var active: int = _input_router.active_layer
	var col: Color = _LAYER_COLORS[active] if active < _LAYER_COLORS.size() else _TEXT
	_layer_readout_label.text = "L%d / 5" % active
	_layer_readout_label.add_theme_color_override("font_color", col)
	for i in range(_layer_markers.size()):
		if i == active:
			_layer_markers[i].color = _LAYER_COLORS[i] if i < _LAYER_COLORS.size() else _TEXT
		else:
			_layer_markers[i].color = _DIM


func _build_f12_label() -> void:
	_f12_label = Label.new()
	_f12_label.text = "F12 — Report Bug"
	_f12_label.add_theme_font_size_override("font_size", 13)
	_f12_label.add_theme_color_override("font_color", _DIM)
	_f12_label.anchor_left = 0
	_f12_label.anchor_top = 1
	_f12_label.anchor_bottom = 1
	_f12_label.offset_left = 12
	_f12_label.offset_top = -30
	_f12_label.offset_bottom = -12
	add_child(_f12_label)


func _update_f12_label(delta: float) -> void:
	if not _f12_label:
		return
	if _f12_flash_timer > 0.0:
		_f12_flash_timer -= delta
		_f12_label.modulate.a = 1.0
		return
	_f12_age += delta
	var t := clampf(_f12_age / _F12_FADE_TIME, 0.0, 1.0)
	_f12_label.modulate.a = lerpf(1.0, _F12_MIN_ALPHA, t)


func flash_f12() -> void:
	_f12_flash_timer = _F12_FLASH_DURATION

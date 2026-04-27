extends Control

enum Phase { INIT, NARRATION, SETTLING, PROCEEDING, EXITING }

var _phase: int = Phase.INIT
var _shell: Node
var _scroll: Node
var _world_viewport: SubViewportContainer
var _world_sub_viewport: SubViewport
var _footer: HBoxContainer
var _fade_overlay: ColorRect
var _accent: Color

var _keyframe_queue: Array[Dictionary] = []
var _entry_queue: Array[Dictionary] = []
var _waiting_for_entry: bool = false
var _current_entry_id: String = ""
var _regions_state: Dictionary = {}
var _faction_colors: Dictionary = {}
var _faction_display_colors: Dictionary = {}
var _next_mission_region: String = ""
var _time_jump_id: String = ""
var _total_entries: int = 0
var _entries_printed: int = 0

var _flicker_timer: float = 0.0
var _flicker_interval: float = 3.0

var _ownership_timeline: Array = []
var _timeline_index: int = 0
var _timeline_timer: float = 0.0
var _timeline_interval: float = 0.6


func _ready() -> void:
	_accent = ThemeConstants.get_era_accent(EraConfig.ACTIVE_ERA_ID)
	_build_layout()
	_connect_bus_signals()
	if SimBridge.USE_LIVE_SIM:
		SimBridge.send_command({"type": "command", "cmd": "ready_for_time_jump"})


func setup(params: Dictionary) -> void:
	_next_mission_region = params.get("next_mission_region", "")
	if params.has("time_jump_id"):
		_time_jump_id = params["time_jump_id"]


func _build_layout() -> void:
	var bg := ColorRect.new()
	bg.color = ThemeConstants.BASE
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)

	_world_viewport = SubViewportContainer.new()
	_world_viewport.stretch = true
	_world_viewport.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_world_viewport)
	# Starts full-screen; resized to left 62% when scroll slides in

	_world_sub_viewport = SubViewport.new()
	_world_sub_viewport.transparent_bg = false
	_world_sub_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	_world_viewport.add_child(_world_sub_viewport)

	var env := WorldEnvironment.new()
	var sky_env := Environment.new()
	sky_env.background_mode = Environment.BG_COLOR
	sky_env.background_color = Color(0, 0, 0)
	env.environment = sky_env
	_world_sub_viewport.add_child(env)

	_shell = load("res://scenes/shared/world_view/world_view_shell.tscn").instantiate()
	_world_sub_viewport.add_child(_shell)
	_shell.set_viewport(_world_sub_viewport)
	_shell.setup_era(EraConfig.ACTIVE_ERA_ID)

	_scroll = load("res://scenes/world/chronicle_scroll_panel.tscn").instantiate()
	_scroll.anchor_left = 0.62
	_scroll.anchor_right = 1.0
	_scroll.anchor_top = 0.0
	_scroll.anchor_bottom = 1.0
	_scroll.visible = false
	_scroll.entry_finished_printing.connect(_on_entry_finished_printing)
	_scroll.all_entries_finished.connect(_on_all_entries_finished)
	_scroll.entry_expansion_opened.connect(_on_expansion_opened)
	_scroll.entry_expansion_closed.connect(_on_expansion_closed)
	add_child(_scroll)

	_fade_overlay = ColorRect.new()
	_fade_overlay.color = Color(0, 0, 0, 0)
	_fade_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fade_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_fade_overlay)

	_footer = HBoxContainer.new()
	_footer.anchor_left = 0.0
	_footer.anchor_right = 0.62
	_footer.anchor_top = 0.92
	_footer.anchor_bottom = 1.0
	_footer.alignment = BoxContainer.ALIGNMENT_CENTER
	_footer.add_theme_constant_override("separation", 40)
	_footer.visible = false
	add_child(_footer)

	var proceed_btn := Button.new()
	proceed_btn.text = "PROCEED"
	proceed_btn.add_theme_font_override("font", ThemeConstants.font_mono_medium)
	proceed_btn.add_theme_font_size_override("font_size", 16)
	proceed_btn.pressed.connect(_on_proceed)
	_footer.add_child(proceed_btn)

	var exit_btn := Button.new()
	exit_btn.text = "EXIT TO MAIN MENU"
	exit_btn.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	exit_btn.add_theme_font_size_override("font_size", 14)
	exit_btn.pressed.connect(_on_exit)
	_footer.add_child(exit_btn)


func _connect_bus_signals() -> void:
	UIDataBus.time_jump_started.connect(_on_time_jump_started)
	UIDataBus.time_jump_keyframe.connect(_on_keyframe)
	UIDataBus.chronicle_entry.connect(_on_chronicle_entry)
	UIDataBus.time_jump_ended.connect(_on_time_jump_ended)


func _disconnect_bus_signals() -> void:
	if UIDataBus.time_jump_started.is_connected(_on_time_jump_started):
		UIDataBus.time_jump_started.disconnect(_on_time_jump_started)
	if UIDataBus.time_jump_keyframe.is_connected(_on_keyframe):
		UIDataBus.time_jump_keyframe.disconnect(_on_keyframe)
	if UIDataBus.chronicle_entry.is_connected(_on_chronicle_entry):
		UIDataBus.chronicle_entry.disconnect(_on_chronicle_entry)
	if UIDataBus.time_jump_ended.is_connected(_on_time_jump_ended):
		UIDataBus.time_jump_ended.disconnect(_on_time_jump_ended)


func _exit_tree() -> void:
	_disconnect_bus_signals()


# --- Bus signal handlers ---

func _on_time_jump_started(tj_id: String, _span_years: int, _total_kf: int, total_entries: int, faction_names: Dictionary) -> void:
	_time_jump_id = tj_id
	_total_entries = total_entries
	_entries_printed = 0
	_phase = Phase.NARRATION
	# Assign evenly-spaced hues so factions are always visually distinct
	var faction_ids: Array = faction_names.keys()
	faction_ids.sort()
	for i in range(faction_ids.size()):
		var fid: String = faction_ids[i]
		var hue: float = float(i) / maxf(faction_ids.size(), 1)
		var color := Color.from_hsv(hue, 0.7, 0.9)
		_faction_colors[fid] = color
		_faction_display_colors[faction_names[fid]] = color

	_ownership_timeline = SimBridge.ownership_timeline
	_timeline_index = 0
	_timeline_timer = 0.0
	if _ownership_timeline.size() > 0 and total_entries > 0:
		# ~3.5s per chronicle entry; spread timeline evenly across full narration
		var estimated_narration_secs: float = total_entries * 3.5
		_timeline_interval = estimated_narration_secs / _ownership_timeline.size()
	else:
		_timeline_interval = 0.6
	# Init scroll BEFORE any await — chronicle entries arrive during the same
	# dispatch cycle and must not be wiped by a late begin_time_jump().
	_scroll.begin_time_jump(total_entries, _faction_display_colors)
	_scroll.visible = true
	_scroll.slide_in()

	var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.tween_property(_world_viewport, "anchor_right", 0.62, 1.2)

	_shell.move_camera_to_overview(4.0)
	# Disable orbit after the move completes
	await get_tree().create_timer(4.2).timeout
	_shell.stop_auto_camera()


func _on_keyframe(keyframe_data: Dictionary) -> void:
	_keyframe_queue.append(keyframe_data)


func _on_chronicle_entry(entry_data: Dictionary) -> void:
	_scroll.queue_entry(entry_data)
	_entry_queue.append(entry_data)


var _time_jump_ended_received: bool = false

func _on_time_jump_ended(_tj_id: String) -> void:
	_time_jump_ended_received = true
	_try_settle()


func _try_settle() -> void:
	if not _time_jump_ended_received:
		return
	if not _keyframe_queue.is_empty() or _waiting_for_entry:
		return
	if _timeline_index < _ownership_timeline.size():
		return
	_phase = Phase.SETTLING
	if _next_mission_region != "":
		_shell.highlight_region(_next_mission_region)
	_footer.visible = true
	_footer.modulate.a = 0.0
	var tw := create_tween()
	tw.tween_property(_footer, "modulate:a", 1.0, 0.4)


# --- Keyframe application ---

func _apply_keyframe(kf: Dictionary) -> void:
	var timeline_active := not _ownership_timeline.is_empty()
	var regions: Array = kf.get("regions_snapshot", [])
	for r in regions:
		var rid: String = r.get("region_id", "")
		var faction_id: String = r.get("owner_faction_id", "")
		var sig: float = r.get("significance", 0.5)
		var color: Color = _get_faction_color(faction_id)
		var pos := Vector3(r.get("x", 0.0), r.get("y", 0.0), r.get("z", 0.0))
		if rid in _regions_state:
			# Timeline drives colors when active — keyframes only flash military
			if not timeline_active:
				_shell.update_region_node(rid, sig * 1.5, color)
				_shell.update_territory(rid, sig * 6.0, color)
			var old_faction: String = _regions_state[rid].get("owner_faction_id", "")
			if old_faction != faction_id:
				_shell.flash_military_activity(rid, 0.9)
			# Preserve timeline's owner_faction_id; update other fields only
			if not timeline_active:
				_regions_state[rid] = r
			else:
				var current_owner: String = _regions_state[rid].get("owner_faction_id", "")
				_regions_state[rid] = r
				_regions_state[rid]["owner_faction_id"] = current_owner
		else:
			_shell.add_region_node(rid, pos, sig * 1.5, color, faction_id)
			_shell.set_territory(rid, pos, sig * 6.0, color)
			_regions_state[rid] = r

	var conns: Array = kf.get("connections_snapshot", [])
	for c in conns:
		var fid: String = c.get("from_id", "")
		var tid: String = c.get("to_id", "")
		var etype: String = c.get("edge_type", "border")
		var color_fid_val = c.get("color_faction_id")
		var color_fid: String = color_fid_val if color_fid_val is String else ""
		var color: Color = _get_faction_color(color_fid)
		_shell.add_connection(fid, tid, etype, color)

	var military: Array = kf.get("military_events", [])
	for evt in military:
		var kind: String = evt.get("kind", "")
		if kind == "attack" or kind == "conquest":
			var atk: String = evt.get("attacker_region_id", "")
			var dfn: String = evt.get("defender_region_id", "")
			if atk != "" and dfn != "":
				_shell.flash_conflict(atk, dfn, 0.8)


func _get_faction_color(faction_id: String) -> Color:
	if faction_id in _faction_colors:
		return _faction_colors[faction_id]
	var hash_val := faction_id.hash()
	var hue := absf(fmod(float(hash_val) / 2147483647.0, 1.0))
	var color := Color.from_hsv(hue, 0.7, 0.9)
	_faction_colors[faction_id] = color
	return color


func _entry_queue_ids() -> Array[String]:
	var ids: Array[String] = []
	for e in _entry_queue:
		ids.append(e.get("entry_id", ""))
	return ids


# --- Scroll callbacks ---

func _on_entry_finished_printing(entry_id: String) -> void:
	_entries_printed += 1
	if _waiting_for_entry and entry_id == _current_entry_id:
		_waiting_for_entry = false
		_current_entry_id = ""
	_try_settle()


func _on_all_entries_finished() -> void:
	if _phase == Phase.NARRATION:
		pass


func _on_expansion_opened(_entry_id: String) -> void:
	_shell.stop_auto_camera()


func _on_expansion_closed(_entry_id: String) -> void:
	_shell.start_auto_camera()


# --- Ambient flickers during settle ---

func _process(delta: float) -> void:
	if _phase == Phase.NARRATION:
		_advance_narration()
		_advance_timeline(delta)
	elif _phase == Phase.SETTLING:
		_flicker_timer -= delta
		if _flicker_timer <= 0.0:
			_flicker_timer = randf_range(3.0, 5.0)
			_fire_ambient_flicker()


func _advance_narration() -> void:
	if _waiting_for_entry:
		return
	if _keyframe_queue.is_empty():
		return
	var kf: Dictionary = _keyframe_queue.pop_front()
	_apply_keyframe(kf)
	var entry_id_val = kf.get("chronicle_entry_id")
	var entry_id: String = entry_id_val if entry_id_val is String else ""
	if entry_id != "" and entry_id in _entry_queue_ids():
		_waiting_for_entry = true
		_current_entry_id = entry_id
		_scroll.start_printing(entry_id)
	else:
		# No paired entry — check if we should settle
		_try_settle()


func _advance_timeline(delta: float) -> void:
	if _ownership_timeline.is_empty() or _timeline_index >= _ownership_timeline.size():
		return
	_timeline_timer += delta
	while _timeline_timer >= _timeline_interval and _timeline_index < _ownership_timeline.size():
		_timeline_timer -= _timeline_interval
		_apply_ownership_tick(_ownership_timeline[_timeline_index])
		_timeline_index += 1
	if _timeline_index >= _ownership_timeline.size():
		_try_settle()


func _apply_ownership_tick(ownership: Dictionary) -> void:
	var changed_rids: Array[String] = []
	for rid: String in ownership:
		var faction_id_val = ownership[rid]
		var faction_id: String = faction_id_val if faction_id_val is String else ""
		if rid in _regions_state:
			var old_fid: String = _regions_state[rid].get("owner_faction_id", "")
			if old_fid != faction_id:
				var color: Color = _get_faction_color(faction_id)
				var sig: float = _regions_state[rid].get("significance", 0.5)
				_shell.update_region_node(rid, sig * 1.5, color)
				_shell.update_territory(rid, sig * 6.0, color)
				_regions_state[rid]["owner_faction_id"] = faction_id
				changed_rids.append(rid)
	# Stagger flashes across the tick interval
	for i in range(changed_rids.size()):
		var flash_rid: String = changed_rids[i]
		var delay: float = randf_range(0.0, _timeline_interval * 0.8)
		get_tree().create_timer(delay).timeout.connect(func():
			_shell.flash_military_activity(flash_rid, 0.7)
		)


func _fire_ambient_flicker() -> void:
	var region_ids := _regions_state.keys()
	if region_ids.is_empty():
		return
	var rid: String = region_ids[randi() % region_ids.size()]
	_shell.flash_military_activity(rid, randf_range(0.1, 0.2))


# --- Proceed / Exit ---

func _on_proceed() -> void:
	if _phase != Phase.SETTLING:
		return
	_phase = Phase.PROCEEDING
	_footer.visible = false
	_shell.clear_highlight()
	_scroll.slide_out()
	var expand_tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	expand_tw.tween_property(_world_viewport, "anchor_right", 1.0, 0.4)

	if _next_mission_region != "":
		_shell.move_camera_to_region(_next_mission_region, 3.0)
		await _shell.camera_move_completed

	var tw := create_tween()
	tw.tween_property(_fade_overlay, "color:a", 1.0, 0.6)
	tw.tween_callback(func():
		_disconnect_bus_signals()
		if SimBridge.USE_LIVE_SIM:
			UIDataBus.proceed_to_next_mission()
		else:
			# No sim running — fall back to main menu
			UIDataBus.exit_to_main_menu()
	)


func _on_exit() -> void:
	if _phase == Phase.PROCEEDING or _phase == Phase.EXITING:
		return
	_phase = Phase.EXITING
	_footer.visible = false
	var tw := create_tween()
	tw.tween_property(_fade_overlay, "color:a", 1.0, 0.6)
	tw.tween_callback(func():
		_disconnect_bus_signals()
		UIDataBus.exit_to_main_menu()
	)

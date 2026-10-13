extends Control

const SimSession := preload("res://autoload/sim_session.gd")

enum Phase { INIT, NARRATION, SETTLING, PROCEEDING, EXITING }

# A52, R-069-03: the replay clock; the map never waits for the scroll.
const REPLAY_TICKS_PER_SECOND := 2
const ENTRY_HOLD_S := 3.0

var _phase: int = Phase.INIT
var _shell: Node
var _scroll: Node
var _world_viewport: SubViewportContainer
var _world_sub_viewport: SubViewport
var _footer: HBoxContainer
var _skip_btn: Button
var _fade_overlay: ColorRect
var _accent: Color

# Stage 11g — info panel host. Gated on FeatureFlags.ENABLE_INSPECTION_PANELS.
# See orbital_camera_3d.gd: when the flag is on the camera skips its own
# _focus_on_region so the sequencer can drive both panel and camera pan.
var _info_host: Control
var _faction_names: Dictionary = {}

var _keyframe_queue: Array[Dictionary] = []
var _entry_hold_s: float = 0.0
var _entry_queue: Array[Dictionary] = []
var _regions_state: Dictionary = {}
var _faction_colors: Dictionary = {}
var _faction_display_colors: Dictionary = {}
var _next_mission_region: String = ""
var _time_jump_id: String = ""
var _total_entries: int = 0
var _entries_printed: int = 0

var _flicker_timer: float = 0.0
var _flicker_interval: float = 3.0

# Replay of a chronicle frame's "ownership" snapshots (A48 item 13, A59).
var _rp_active: bool = false
var _rp_clock: float = 0.0
var _rp_from: int = 0
var _rp_to: int = 0
var _rp_tick: int = 0
var _rp_snaps: Array = []
var _rp_live: Array = []
var _rp_shown: Array = []
var _rp_keyframes: Array = []
var _rp_entries: Array = []
var _rp_keyframes_hit: Array[int] = []
var _rp_entries_started: Array[int] = []


func _ready() -> void:
	_accent = ThemeConstants.get_era_accent(EraConfig.ACTIVE_ERA_ID)
	_build_layout()
	_connect_bus_signals()
	# A69: opening the scene sends no command; the jump was issued by Proceed
	# from the debrief and the bridge holds its frame.
	var bridge = SimSession.bridge()
	var frame: Dictionary = bridge.chronicle_frame()
	_scroll.slide_in()
	create_tween().tween_property(_world_viewport, "anchor_right", 0.62, 0.40)
	if frame.is_empty():
		_settle()
		return
	_phase = Phase.NARRATION
	_skip_btn.visible = true
	_scroll.set_snapshot(bridge.chronicle_snapshot())
	_scroll.load_frame(frame)
	var live: Array = []
	for i in range(bridge.regions().size()):
		live.append(bridge.owner_of(i))
	load_frame(frame, live)


# live_owners: owner per region index, -1 unowned. Replaces any replay.
func load_frame(frame: Dictionary, live_owners: Array) -> void:
	var jump: Dictionary = frame.get("jump", {})
	var own = frame.get("ownership")
	var snaps: Array = own.get("snapshots", []) if own is Dictionary else []
	_rp_from = int(jump.get("from_tick", 0))
	_rp_to = int(jump.get("to_tick", 0))
	_rp_live = live_owners
	_rp_snaps = snaps
	_rp_clock = 0.0
	_rp_keyframes = frame.get("keyframes", [])
	_rp_entries = frame.get("entries", [])
	_rp_keyframes_hit = []
	_rp_entries_started = []
	_total_entries = _rp_entries.size()
	_entries_printed = 0
	_entry_hold_s = 0.0
	_rp_active = not snaps.is_empty() and _rp_to > _rp_from
	if _rp_active:
		_rp_tick = _rp_from
		_show_owners(snaps[0])
	else:
		_rp_tick = _rp_to
		_show_owners(live_owners)


func _advance_replay(delta: float) -> void:
	if FeatureFlags.ENABLE_INSPECTION_PAUSE and InspectionState.is_paused():
		return
	_rp_clock += delta * REPLAY_TICKS_PER_SECOND
	_rp_tick = _rp_from + int(_rp_clock)
	for k in _rp_keyframes:
		if int(k) <= _rp_tick and not _rp_keyframes_hit.has(int(k)):
			_rp_keyframes_hit.append(int(k))
	for e in _rp_entries:
		var id := int(e.get("id", -1))
		if int(e.get("start_tick", 0)) <= _rp_tick and not _rp_entries_started.has(id):
			_rp_entries_started.append(id)
			_scroll.start_printing(str(id))
	if _rp_tick >= _rp_to:
		_rp_tick = _rp_to
		_rp_active = false
		_show_owners(_rp_live)
		_try_settle()
	else:
		_show_owners(_rp_snaps[mini((_rp_tick - _rp_from) / 2, _rp_snaps.size() - 1)])


# Integer region and faction ids map onto the shell's "r<i>" and "f<id>"; a
# region the shell does not know yet is placed on a ring by index.
func _show_owners(owners: Array) -> void:
	if owners == _rp_shown:
		return
	_rp_shown = owners.duplicate()
	var ownership := {}
	for i in range(owners.size()):
		var rid := "r%d" % i
		if not rid in _regions_state:
			var a := TAU * i / maxi(owners.size(), 1)
			var pos := Vector3(cos(a) * 10.0, 0.0, sin(a) * 10.0)
			_regions_state[rid] = {"owner_faction_id": "", "significance": 0.5, "x": pos.x, "y": pos.y, "z": pos.z}
			_shell.add_region_node(rid, pos, 0.75, _get_faction_color(""), "")
		ownership[rid] = "f%d" % int(owners[i]) if int(owners[i]) >= 0 else ""
	_apply_ownership_tick(ownership)


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

	_shell = load("res://scenes/galaxy/galaxy_view.tscn").instantiate()
	_shell.driven = true
	_world_sub_viewport.add_child(_shell)
	if _shell.has_signal("region_clicked"):
		_shell.region_clicked.connect(_on_shell_region_clicked)
	if _shell.has_signal("empty_space_clicked"):
		_shell.empty_space_clicked.connect(_on_shell_empty_space_clicked)

	_scroll = load("res://scenes/world/chronicle_scroll_panel.tscn").instantiate()
	_scroll.anchor_left = 0.62
	_scroll.anchor_right = 1.0
	_scroll.anchor_top = 0.0
	_scroll.anchor_bottom = 1.0
	_scroll.hosted = true
	_scroll.entry_finished_printing.connect(_on_entry_finished_printing)
	_scroll.all_entries_finished.connect(_on_all_entries_finished)
	_scroll.entry_expansion_opened.connect(_on_expansion_opened)
	_scroll.entry_expansion_closed.connect(_on_expansion_closed)
	_scroll.mention_clicked.connect(_on_scroll_mention_clicked)
	add_child(_scroll)

	_info_host = load("res://scenes/world/info_panel_host.tscn").instantiate()
	# Anchored to the right side of the world viewport area (left 62% during
	# narration), so it doesn't collide with debug harness buttons (top-left)
	# or the skip button (bottom-left).
	_info_host.anchor_left = 0.30
	_info_host.anchor_right = 0.62
	_info_host.anchor_top = 0.0
	_info_host.anchor_bottom = 1.0
	_info_host.offset_left = 0
	_info_host.offset_top = 24
	_info_host.offset_right = -24
	_info_host.offset_bottom = -80
	_info_host.open_region_requested.connect(_on_host_open_region_requested)
	_info_host.open_faction_requested.connect(_on_host_open_faction_requested)
	add_child(_info_host)

	_fade_overlay = ColorRect.new()
	_fade_overlay.color = Color(0, 0, 0, 0)
	_fade_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fade_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_fade_overlay)

	_skip_btn = Button.new()
	_skip_btn.text = "SKIP ▶▶"
	_skip_btn.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	_skip_btn.add_theme_font_size_override("font_size", 14)
	_skip_btn.pressed.connect(_on_skip)
	_skip_btn.anchor_left = 0.0
	_skip_btn.anchor_right = 0.0
	_skip_btn.anchor_top = 1.0
	_skip_btn.anchor_bottom = 1.0
	_skip_btn.offset_left = 20
	_skip_btn.offset_top = -50
	_skip_btn.offset_bottom = -16
	_skip_btn.offset_right = 130
	_skip_btn.visible = false
	add_child(_skip_btn)

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
	_faction_names = faction_names
	# Assign evenly-spaced hues so factions are always visually distinct
	var faction_ids: Array = faction_names.keys()
	faction_ids.sort()
	for i in range(faction_ids.size()):
		var fid: String = faction_ids[i]
		var hue: float = float(i) / maxf(faction_ids.size(), 1)
		var color := Color.from_hsv(hue, 0.7, 0.9)
		_faction_colors[fid] = color
		_faction_display_colors[faction_names[fid]] = color

	# Init scroll BEFORE any await — chronicle entries arrive during the same
	# dispatch cycle and must not be wiped by a late begin_time_jump().
	_scroll.begin_time_jump(total_entries, _faction_display_colors)
	_scroll.visible = true
	_scroll.slide_in()
	_skip_btn.visible = true

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


func _on_time_jump_ended(_tj_id: String) -> void:
	_try_settle()


# A79, R-069-03: settle when the replay clock is at the jump's last tick and the
# last entry has printed and held ENTRY_HOLD_S; keyframes never delay it.
func _try_settle() -> void:
	if _phase != Phase.NARRATION or _rp_active:
		return
	if _total_entries > 0 and _entry_hold_s < ENTRY_HOLD_S:
		return
	_settle()


func _settle() -> void:
	_phase = Phase.SETTLING
	_skip_btn.visible = false
	if _next_mission_region != "":
		_shell.highlight_region(_next_mission_region)
	_footer.visible = true
	_footer.modulate.a = 0.0
	var tw := create_tween()
	tw.tween_property(_footer, "modulate:a", 1.0, 0.4)


# --- Keyframe application ---

func _apply_keyframe(kf: Dictionary) -> void:
	var timeline_active := _rp_active
	var regions: Array = kf.get("regions_snapshot", [])
	for r in regions:
		var rid: String = r.get("region_id", "")
		var faction_id: String = r.get("owner_faction_id", "")
		var sig: float = r.get("significance", 0.5)
		var color: Color = _get_faction_color(faction_id)
		var pos := Vector3(r.get("x", 0.0), r.get("y", 0.0), r.get("z", 0.0))
		if rid in _regions_state:
			if not timeline_active:
				_shell.update_region_node(rid, sig * 1.5, color)
				if faction_id != "":
					_shell.set_region_owner(rid, faction_id)
					_shell.update_territory(rid, sig * 6.0, color)
				else:
					_shell.remove_territory(rid)
				var old_faction: String = _regions_state[rid].get("owner_faction_id", "")
				if old_faction != faction_id:
					_shell.flash_military_activity(rid, 0.9)
				_regions_state[rid] = r
			else:
				# Timeline drives visuals — keyframes only update non-ownership fields
				var current_owner: String = _regions_state[rid].get("owner_faction_id", "")
				_regions_state[rid] = r
				_regions_state[rid]["owner_faction_id"] = current_owner
		else:
			_shell.add_region_node(rid, pos, sig * 1.5, color, faction_id)
			if faction_id != "":
				_shell.set_territory(rid, pos, sig * 6.0, color)
			_regions_state[rid] = r

	var conns: Array = kf.get("connections_snapshot", [])
	for c in conns:
		var fid: String = c.get("from_id", "")
		var tid: String = c.get("to_id", "")
		var etype: String = c.get("edge_type", "border")
		var color_fid_val = c.get("color_faction_id")
		var color_fid: String = color_fid_val if color_fid_val is String else ""
		var color: Color
		if color_fid == "":
			color = Color(1.0, 0.92, 0.6, 0.8)
		else:
			color = _get_faction_color(color_fid)
		_shell.add_connection(fid, tid, etype, color)

	if not timeline_active:
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

func _on_entry_finished_printing(_entry_id: String) -> void:
	_entries_printed += 1


func _on_all_entries_finished() -> void:
	if _phase == Phase.NARRATION:
		pass


func _on_expansion_opened(_entry_id: String) -> void:
	_shell.stop_auto_camera()


func _on_expansion_closed(_entry_id: String) -> void:
	_shell.start_auto_camera()


# --- Ambient flickers during settle ---

func _process(delta: float) -> void:
	if _rp_active:
		_advance_replay(delta)
	if _phase == Phase.NARRATION:
		_advance_narration()
		if _total_entries > 0 and _entries_printed >= _total_entries:
			_entry_hold_s += delta
		_try_settle()
	elif _phase == Phase.SETTLING:
		_flicker_timer -= delta
		if _flicker_timer <= 0.0:
			_flicker_timer = randf_range(3.0, 5.0)
			_fire_ambient_flicker()


func _advance_narration() -> void:
	# Stage 11g — pause holders block narration advance.
	# See also: scenes/world/world_view_inspection_state.gd, info_panel_host.gd
	if FeatureFlags.ENABLE_INSPECTION_PAUSE and InspectionState.is_paused():
		return
	while not _keyframe_queue.is_empty():
		var kf: Dictionary = _keyframe_queue.pop_front()
		_apply_keyframe(kf)
		var entry_id_val = kf.get("chronicle_entry_id")
		var entry_id: String = entry_id_val if entry_id_val is String else ""
		if entry_id != "" and entry_id in _entry_queue_ids():
			_scroll.start_printing(entry_id)


func _apply_ownership_tick(ownership: Dictionary) -> void:
	for rid: String in ownership:
		var faction_id_val = ownership[rid]
		var faction_id: String = faction_id_val if faction_id_val is String else ""
		if rid in _regions_state:
			var old_fid: String = _regions_state[rid].get("owner_faction_id", "")
			if old_fid != faction_id:
				var color: Color = _get_faction_color(faction_id)
				var sig: float = _regions_state[rid].get("significance", 0.5)
				_shell.update_region_node(rid, sig * 1.5, color)
				if faction_id != "":
					# set_territory handles both create (uninhabited → owned) and update
					var pos := Vector3(
						_regions_state[rid].get("x", 0.0),
						_regions_state[rid].get("y", 0.0),
						_regions_state[rid].get("z", 0.0))
					_shell.set_region_owner(rid, faction_id)
					_shell.set_territory(rid, pos, sig * 6.0, color)
				else:
					_shell.remove_territory(rid)
				_regions_state[rid]["owner_faction_id"] = faction_id


func _fire_ambient_flicker() -> void:
	var region_ids := _regions_state.keys()
	if region_ids.is_empty():
		return
	var rid: String = region_ids[randi() % region_ids.size()]
	_shell.flash_military_activity(rid, randf_range(0.1, 0.2))


# --- Skip / Proceed / Exit ---

func _on_skip() -> void:
	if _phase != Phase.NARRATION:
		return
	_skip_btn.visible = false
	while not _keyframe_queue.is_empty():
		_apply_keyframe(_keyframe_queue.pop_front())
	if _rp_active:
		_rp_active = false
		_rp_tick = _rp_to
		_show_owners(_rp_live)
	_scroll.skip_all()
	_entry_hold_s = ENTRY_HOLD_S
	_try_settle()


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
		if SimSession.bridge().has_world():
			UIDataBus.proceed_to_next_mission()
		else:
			# No C sim session — fall back to main menu
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


# --- Stage 11g — Inspection panel wiring ---

func _on_shell_region_clicked(region_id: String) -> void:
	if not FeatureFlags.ENABLE_INSPECTION_PANELS:
		return
	if not _regions_state.has(region_id):
		return
	_open_region_panel(region_id)
	_shell.move_camera_to_region(region_id, 1.5)


func _on_shell_empty_space_clicked() -> void:
	if not FeatureFlags.ENABLE_INSPECTION_PANELS:
		return
	if _info_host == null or not _info_host.is_open():
		return
	# Don't close if the click was over the panel itself.
	var hovered: Control = get_viewport().gui_get_hovered_control()
	if hovered != null and (hovered == _info_host or _info_host.is_ancestor_of(hovered)):
		return
	_info_host.close()


func _on_host_open_region_requested(region_id: String) -> void:
	if not _regions_state.has(region_id):
		return
	_open_region_panel(region_id)
	_shell.move_camera_to_region(region_id, 1.5)


func _on_host_open_faction_requested(faction_id: String) -> void:
	_open_faction_panel(faction_id)
	_pan_camera_to_faction(faction_id)


func _on_scroll_mention_clicked(kind: String, id: String) -> void:
	# Stage 11g — chronicle mention link clicked.
	# See also: scenes/world/chronicle_entry.gd, chronicle_entry_expansion.gd
	if not FeatureFlags.ENABLE_INSPECTION_PANELS:
		return
	if kind == "region":
		if not _regions_state.has(id):
			return
		_open_region_panel(id)
		_shell.move_camera_to_region(id, 1.5)
	elif kind == "faction":
		_open_faction_panel(id)
		_pan_camera_to_faction(id)


func _pan_camera_to_faction(faction_id: String) -> void:
	var rids: PackedStringArray = []
	for rid in _regions_state:
		if String(_regions_state[rid].get("owner_faction_id", "")) == faction_id:
			rids.append(rid)
	if rids.is_empty():
		return
	_shell.move_camera_to_regions(rids, 1.5)


func _open_region_panel(region_id: String) -> void:
	var r: Dictionary = _regions_state[region_id]
	var fid: String = r.get("owner_faction_id", "")
	var fname: String = String(_faction_names.get(fid, fid))
	var fcolor: Color = _get_faction_color(fid) if fid != "" else Color(0.5, 0.5, 0.5, 0.5)
	var ownership_line := ""
	if fid != "":
		ownership_line = "Held by %s." % fname
	_info_host.open_region(region_id, r.merged({"region_id": region_id}), fid, fname, fcolor, ownership_line)


func _open_faction_panel(faction_id: String) -> void:
	if faction_id == "":
		return
	var fcolor: Color = _get_faction_color(faction_id)
	var meta: Dictionary = {
		"id": faction_id,
		"archetype": "—",
		"tech_tier": 0,
		"status": "Stable",
		"aggregates": _aggregate_for_faction(faction_id),
	}
	var rows: Array = _region_rows_for_faction(faction_id)
	_info_host.open_faction(faction_id, meta, fcolor, rows)


func _aggregate_for_faction(faction_id: String) -> Dictionary:
	var sums := {"military": 0, "economy": 0, "tension": 0, "population": 0}
	for rid in _regions_state:
		var r: Dictionary = _regions_state[rid]
		if String(r.get("owner_faction_id", "")) != faction_id:
			continue
		sums["military"]   += int(r.get("military", 0))
		sums["economy"]    += int(r.get("economy", 0))
		sums["tension"]    += int(r.get("tension", 0))
		sums["population"] += int(r.get("population", 0))
	return sums


func _region_rows_for_faction(faction_id: String) -> Array:
	var rows: Array = []
	for rid in _regions_state:
		var r: Dictionary = _regions_state[rid]
		if String(r.get("owner_faction_id", "")) != faction_id:
			continue
		rows.append({
			"region_id": rid,
			"tier": String(r.get("tier", "")),
		})
	return rows


func qa_state() -> Dictionary:
	return {
		"scene": "time_jump",
		"tick": -1,
		"phase": _phase,
		"entries": _rp_entries,
		"entries_total": _total_entries,
		"entries_printed": _entries_printed,
		"plants": [],
		"replay": {
			"active": _rp_active,
			"tick": _rp_tick,
			"from_tick": _rp_from,
			"to_tick": _rp_to,
			"snapshot_count": _rp_snaps.size(),
			"shown_owners": _rp_shown.duplicate(),
			"keyframes_hit": _rp_keyframes_hit.duplicate(),
			"entries_started": _rp_entries_started.duplicate(),
		},
	}

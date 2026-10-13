extends PanelContainer

const SimSession := preload("res://autoload/sim_session.gd")

signal entry_finished_printing(entry_id: String)
signal entry_expansion_opened(entry_id: String)
signal entry_expansion_closed(entry_id: String)
signal all_entries_finished()
signal mention_clicked(kind: String, id: String)

var _entries: Dictionary = {}
var _printing_id: String = ""
# R-069-03: entries print one at a time; an entry reached while another prints waits here.
# See also: time_jump_sequencer.gd ENTRY_HOLD_S
const PRINT_HOLD_S := 3.0  # R-069-03: a printed entry holds for at least 3.0 s; liberty 2026-10-13: the hold gates only the start of the next entry
var _print_queue: Array[String] = []
var _printed_order: Array[String] = []
var _hold_left_s: float = 0.0
var _total_expected: int = 0
var _finished_count: int = 0
var _paused: bool = false
var _time_jump_active: bool = false
var _accent: Color
var _faction_colors: Dictionary = {}

var _scroll: ScrollContainer
var _entry_container: VBoxContainer
var _expansion_overlay: Control
var _error_panel: Control

# Piece C3 rebind — reads a C transport v1 "chronicle" frame (see file
# header) independent of the legacy begin_time_jump()/queue_entry() path
# above. R-069-02's bible-mandated pace: reported by qa_state() and also
# the actual source of truth for chronicle_entry.gd's print timer, wired
# in via set_pace() in queue_entry() below.
const CHRONICLE_PACE := {
	"word_interval_s": 0.08,
	"fade_s": 0.20,
}
const FRAGMENTS_LIBRARY_PATH := "res://library/chronicle/fragments.json"
const PLANTS := ["entries-dropped", "refs-unresolved"]

# Piece C8 self-load pattern (docs/northstar/plans/push/specs/C8-M3.md
# "Self-loading pattern"): this panel becomes a directly-routed top-level
# scene with no setup() call, so it self-loads the live chronicle frame and
# the snapshot after the jump in _ready() (C3-3). A failed live load leaves
# the panel empty and logs the reason; it never falls back to a fixture.

var _snapshot_data: Dictionary = {}
var _snapshot_region_ids: Dictionary = {}
var _snapshot_faction_ids: Dictionary = {}

var _fragment_library_loaded: bool = false
var _fragment_library_text_by_id: Dictionary = {}
var _chronicle_names = null  # ChronicleNames instance, lazy-loaded in _ensure_fragment_library

var _qa_entries: Array = []
var _qa_owners: Dictionary = {}
var _qa_dropped_entries: int = 0
var _qa_unresolved_refs: int = 0
var _qa_hash = 0
var _qa_load_ms: float = 0.0
var _qa_regen_count: int = 0
var _qa_expanded_id: int = -1
var _qa_tick: int = -1

# Set by the sequencer before add_child: it hands this panel the held frame itself.
var hosted: bool = false
var _plant_refs_unresolved: bool = false
var _plant_entries_dropped: bool = false


func _ready() -> void:
	_accent = ThemeConstants.get_era_accent(EraConfig.ACTIVE_ERA_ID)
	_build_ui()
	if not hosted:
		_load_held()
	# Stage 11g — listen to the world-view pause coordinator so any holder
	# (region/faction panel, expansion) halts entry printing.
	# See also: scenes/world/world_view_inspection_state.gd
	if FeatureFlags.ENABLE_INSPECTION_PAUSE:
		InspectionState.pause_changed.connect(_on_inspection_pause_changed)


# A69: opening the scene sends nothing; the frame is the one the flow leading in
# (Proceed from the debrief) left on the bridge, none after a load.
func _load_held() -> void:
	var bridge = SimSession.bridge()
	var frame: Dictionary = bridge.chronicle_frame()
	if frame.is_empty():
		return
	set_snapshot(bridge.chronicle_snapshot())
	load_frame(frame)


func _on_return_pressed() -> void:
	SceneRouter.go_to("galaxy")


func _on_inspection_pause_changed(paused: bool) -> void:
	if paused:
		pause()
	else:
		resume()


func _build_ui() -> void:
	var style := StyleBoxFlat.new()
	style.bg_color = ThemeConstants.SURFACE
	style.border_color = ThemeConstants.BORDER_COLOR
	style.border_width_left = ThemeConstants.BORDER_WIDTH
	add_theme_stylebox_override("panel", style)

	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	margin.add_theme_constant_override("margin_left", 20)
	margin.add_theme_constant_override("margin_right", 20)
	margin.add_theme_constant_override("margin_top", 24)
	margin.add_theme_constant_override("margin_bottom", 24)
	add_child(margin)

	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 12)
	margin.add_child(vbox)

	var header := Label.new()
	header.text = "CHRONICLE"
	header.uppercase = true
	header.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	header.add_theme_font_size_override("font_size", ThemeConstants.SECTION_LABEL_SIZE)
	header.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	vbox.add_child(header)

	var divider = load("res://theme/components/tm_divider.tscn").instantiate()
	vbox.add_child(divider)

	_scroll = ScrollContainer.new()
	_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	vbox.add_child(_scroll)

	_entry_container = VBoxContainer.new()
	_entry_container.add_theme_constant_override("separation", 4)
	_entry_container.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_scroll.add_child(_entry_container)

	# Piece C8: this panel becomes a directly-routed top-level scene
	# (docs/northstar/plans/push/specs/C8.md step 6), so it needs its own
	# way back to the galaxy view. tm_button matches debrief.gd's/
	# mission_briefing.gd's existing footer-button pattern.
	var return_btn = load("res://theme/components/tm_button.tscn").instantiate()
	return_btn.text = "RETURN"
	return_btn.accent_color = _accent
	return_btn.name = "Return"
	return_btn.pressed.connect(_on_return_pressed)
	vbox.add_child(return_btn)

	_expansion_overlay = Control.new()
	_expansion_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	_expansion_overlay.visible = false
	_expansion_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_expansion_overlay)


func begin_time_jump(total_entries: int, faction_colors: Dictionary = {}) -> void:
	_total_expected = total_entries
	_finished_count = 0
	_time_jump_active = true
	_paused = false
	_clear_print_state()
	_faction_colors = faction_colors
	_entries.clear()
	for child in _entry_container.get_children():
		child.queue_free()
	_close_expansion()


func queue_entry(entry_data: Dictionary) -> void:
	var entry_id: String = entry_data.get("entry_id", "")
	var entry_scene := load("res://scenes/world/chronicle_entry.tscn")
	var entry_node: Node = entry_scene.instantiate()
	entry_node.setup(entry_data, _accent, _faction_colors)
	entry_node.set_pace(CHRONICLE_PACE["word_interval_s"], CHRONICLE_PACE["fade_s"])
	entry_node.finished_printing.connect(_on_entry_finished)
	entry_node.expansion_requested.connect(_on_expansion_requested)
	entry_node.mention_clicked.connect(_on_mention_clicked)
	_entry_container.add_child(entry_node)
	_entries[entry_id] = entry_node

	entry_node.modulate.a = 0.0
	entry_node.position.x = 40
	var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.tween_property(entry_node, "modulate:a", 1.0, 0.3)
	tw.parallel().tween_property(entry_node, "position:x", 0.0, 0.3)


# liberty 2026-10-13: start_printing enqueues; an unknown, printing, queued or PRINTED id is ignored; FIFO in call order.
func start_printing(entry_id: String) -> void:
	if not _entries.has(entry_id) or entry_id == _printing_id or _print_queue.has(entry_id):
		return
	if _entries[entry_id].get_current_state() == 2:  # PRINTED
		return
	_print_queue.append(entry_id)
	_try_start_next()


func _try_start_next() -> void:
	if _printing_id != "" or _hold_left_s > 0.0:
		return
	while not _print_queue.is_empty():
		var entry_id: String = _print_queue.pop_front()
		if not _entries.has(entry_id) or not is_instance_valid(_entries[entry_id]):
			continue  # a freed node is skipped
		_printing_id = entry_id
		_entries[entry_id].start_printing()
		_auto_scroll_to_entry(entry_id)
		return


func _clear_print_state() -> void:
	_print_queue.clear()
	_printed_order.clear()
	_hold_left_s = 0.0
	_printing_id = ""


func _process(delta: float) -> void:
	if _hold_left_s > 0.0 and not _paused and not _expansion_overlay.visible \
			and not (FeatureFlags.ENABLE_INSPECTION_PAUSE and InspectionState.is_paused()):
		_hold_left_s = maxf(0.0, _hold_left_s - delta)
	_try_start_next()


func end_time_jump() -> void:
	_time_jump_active = false


func skip_all() -> void:
	_clear_print_state()
	for entry_id in _entries:
		var entry_node: Node = _entries[entry_id]
		if entry_node.get_current_state() != 2:  # not PRINTED
			entry_node.start_printing()
			entry_node._finish_printing()


func pause() -> void:
	_paused = true
	if _printing_id != "" and _entries.has(_printing_id):
		_entries[_printing_id].pause_printing()


func resume() -> void:
	_paused = false
	if _printing_id != "" and _entries.has(_printing_id) and not _expansion_overlay.visible:
		_entries[_printing_id].resume_printing()


var _rest_position_x: float = 0.0
var _rest_position_stored: bool = false


func slide_in() -> void:
	if not _rest_position_stored:
		await get_tree().process_frame
		_rest_position_x = position.x
		_rest_position_stored = true
	position.x = _rest_position_x + 200
	modulate.a = 0.0
	visible = true
	var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.tween_property(self, "position:x", _rest_position_x, 0.40)
	tw.parallel().tween_property(self, "modulate:a", 1.0, 0.40)


func slide_out() -> void:
	if not _rest_position_stored:
		_rest_position_x = position.x
		_rest_position_stored = true
	var tw := create_tween().set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_CUBIC)
	tw.tween_property(self, "position:x", _rest_position_x + 200, 0.4)
	tw.parallel().tween_property(self, "modulate:a", 0.0, 0.4)


func _on_entry_finished(entry_id: String) -> void:
	_finished_count += 1
	_printing_id = ""
	_printed_order.append(entry_id)
	_hold_left_s = PRINT_HOLD_S
	entry_finished_printing.emit(entry_id)
	if _finished_count >= _total_expected:
		all_entries_finished.emit()


func _on_expansion_requested(entry_id: String) -> void:
	if not _entries.has(entry_id):
		return
	_show_expansion(entry_id)


func _show_expansion(entry_id: String) -> void:
	_close_expansion()

	# Stage 11g — expansion now goes through InspectionState so the rest of
	# the world view (renderers, narration) pauses too. With the flag off,
	# fall back to the original ad-hoc pause path.
	if FeatureFlags.ENABLE_INSPECTION_PAUSE:
		InspectionState.acquire("expansion")
	else:
		if _printing_id != "" and _entries.has(_printing_id):
			_entries[_printing_id].pause_printing()

	var entry_data: Dictionary = _entries[entry_id].get_entry_data()
	var expansion: Node = load("res://scenes/world/chronicle_entry_expansion.tscn").instantiate()
	expansion.setup(entry_data, _accent)
	expansion.mention_clicked.connect(_on_mention_clicked)
	expansion.dismissed.connect(func():
		_close_expansion()
		if FeatureFlags.ENABLE_INSPECTION_PAUSE:
			InspectionState.release("expansion")
		else:
			if not _paused and _printing_id != "" and _entries.has(_printing_id):
				_entries[_printing_id].resume_printing()
		entry_expansion_closed.emit(entry_id)
	)
	_expansion_overlay.add_child(expansion)
	_expansion_overlay.visible = true
	_expansion_overlay.mouse_filter = Control.MOUSE_FILTER_STOP
	entry_expansion_opened.emit(entry_id)


func _on_mention_clicked(kind: String, id: String) -> void:
	mention_clicked.emit(kind, id)


func _close_expansion() -> void:
	for child in _expansion_overlay.get_children():
		child.queue_free()
	_expansion_overlay.visible = false
	_expansion_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE


func _auto_scroll_to_entry(entry_id: String) -> void:
	if not _entries.has(entry_id):
		return
	await get_tree().process_frame
	var entry_node: Control = _entries[entry_id]
	var target_scroll := maxf(0.0, entry_node.position.y - 20.0)
	var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.tween_property(_scroll, "scroll_vertical", int(target_scroll), 0.3)


# --- Piece C3: chronicle frame rebind (QA-facing data plumbing) ---------

func set_snapshot(snapshot: Dictionary) -> void:
	_snapshot_data = snapshot
	_snapshot_region_ids = {}
	for region in snapshot.get("regions", []):
		_snapshot_region_ids[int(region.get("i", -999))] = true
	_snapshot_faction_ids = {}
	for faction in snapshot.get("factions", []):
		_snapshot_faction_ids[int(faction.get("id", -999))] = true


func load_frame(frame: Dictionary) -> void:
	var start_usec := Time.get_ticks_usec()

	_qa_entries = []
	_qa_owners = {}
	_qa_dropped_entries = 0
	_qa_unresolved_refs = 0
	_qa_expanded_id = -1

	for raw_entry in frame.get("entries", []):
		var entry: Dictionary = raw_entry
		var refs: Dictionary = entry.get("refs", {})
		var region_refs: Array = refs.get("regions", [])
		var faction_refs: Array = refs.get("factions", [])
		var total_refs := region_refs.size() + faction_refs.size()

		# Real ref validity always drives the drop decision, independent of
		# the refs-unresolved plant (which only fakes the *reported*
		# unresolved_refs count) — see leaf-01.ASSUMPTIONS.md for why this
		# had to be split from the reported count.
		var real_bad_refs := 0
		for rid in region_refs:
			var r := int(rid)
			if not _qa_owners.has(r):
				_qa_owners[r] = _region_owner(r)
			if not _snapshot_region_ids.has(r):
				real_bad_refs += 1
		for fid in faction_refs:
			var fa := int(fid)
			if not _snapshot_faction_ids.has(fa):
				real_bad_refs += 1

		var reported_bad_refs := 0 if _plant_refs_unresolved else real_bad_refs
		_qa_unresolved_refs += reported_bad_refs

		var wholly_unresolved := total_refs > 0 and real_bad_refs == total_refs
		if wholly_unresolved and not _plant_entries_dropped:
			_qa_dropped_entries += 1
			continue

		var region_id: int = int(region_refs[0]) if region_refs.size() > 0 else -1
		var faction_id: int = int(faction_refs[0]) if faction_refs.size() > 0 else -1
		# Prefer fragment_ids (T1-9 shape); fall back to legacy "fragment" key for
		# frames that pre-date T1-9 (fixture frames, C3-4 test frames).
		var raw_fids = entry.get("fragment_ids", null)
		var fragment_ids_arr: Array
		if raw_fids is Array and (raw_fids as Array).size() == 3:
			fragment_ids_arr = [int((raw_fids as Array)[0]), int((raw_fids as Array)[1]), int((raw_fids as Array)[2])]
		else:
			fragment_ids_arr = [int(entry.get("fragment", -1)), -1, -1]
		var all_minus_one: bool = fragment_ids_arr[0] == -1 and fragment_ids_arr[1] == -1 and fragment_ids_arr[2] == -1
		var text: String = str(entry.get("text", ""))
		if text == "":
			if all_minus_one:
				text = _structural_line(entry, region_id)
			else:
				text = _resolve_fragment_ids(fragment_ids_arr, region_id, faction_id)
		_qa_entries.append({
			"entry_id": int(entry.get("id", -1)),
			"fragment_id": fragment_ids_arr[0],
			"fragment_ids": fragment_ids_arr,
			"text": text,
			"mentions": _conv_mentions(entry.get("mentions", [])),
			"expanded_text": str(entry.get("expanded_text", "")),
			"expanded_mentions": _conv_mentions(entry.get("expanded_mentions", [])),
		})

	for child in _entry_container.get_children():
		child.queue_free()
	_entries.clear()
	_clear_print_state()
	for qa_entry in _qa_entries:
		queue_entry({
			"entry_id": str(qa_entry["entry_id"]),
			"base_form": qa_entry["text"],
			"mentions": qa_entry["mentions"],
			"expanded_form": qa_entry["expanded_text"],
			"expanded_mentions": qa_entry["expanded_mentions"],
		})

	_qa_tick = int(frame.get("jump", {}).get("to_tick", -1))
	_qa_hash = hash(frame)
	_qa_regen_count += 1
	_qa_load_ms = float(Time.get_ticks_usec() - start_usec) / 1000.0


func _conv_mentions(arr: Array) -> Array:
	var out: Array = []
	for m in arr:
		var start := int(m.get("start", 0))
		out.append({"kind": str(m.get("kind", "")), "start": start,
			"end": start + int(m.get("len", 0)), "id": str(int(m.get("id", -1)))})
	return out


func qa_state() -> Dictionary:
	var owners_out := {}
	for rid in _qa_owners:
		owners_out[str(rid)] = _qa_owners[rid]
	return {
		"scene": "chronicle",
		"error_panel": _error_panel != null and _error_panel.visible and _error_panel.get_node("ErrorPanel").visible,
		"tick": _qa_tick,
		"plants": PLANTS.duplicate(),
		"hash": _qa_hash,
		"timing_ms": {"load": _qa_load_ms},
		"regen_count": _qa_regen_count,
		"entries": _qa_entries.duplicate(true),
		"expanded_id": _qa_expanded_id,
		"owners": owners_out,
		"pace": CHRONICLE_PACE.duplicate(true),
		"dropped_entries": _qa_dropped_entries,
		"unresolved_refs": _qa_unresolved_refs,
		"print": {
			"printing_id": int(_printing_id) if _printing_id != "" else -1,
			"queued": _print_queue.map(func(id): return int(id)),
			"printed": _printed_order.map(func(id): return int(id)),
			"hold_left_s": _hold_left_s,
		},
	}


func qa_plant(id: String) -> bool:
	match id:
		"entries-dropped":
			_plant_entries_dropped = true
			return true
		"refs-unresolved":
			_plant_refs_unresolved = true
			return true
		_:
			return false


func qa_click_entry(entry_id: int) -> void:
	_qa_expanded_id = entry_id


func qa_dismiss() -> void:
	_qa_expanded_id = -1


func _region_owner(region_id: int) -> int:
	for region in _snapshot_data.get("regions", []):
		if int(region.get("i", -999)) == region_id:
			return int(region.get("owner", -1))
	return -999


func _ensure_fragment_library() -> void:
	if _fragment_library_loaded:
		return
	_fragment_library_loaded = true
	if _chronicle_names == null:
		_chronicle_names = load("res://scenes/world/chronicle_names.gd").new()
	var f := FileAccess.open(FRAGMENTS_LIBRARY_PATH, FileAccess.READ)
	if f == null:
		return
	var text := f.get_as_text()
	f.close()
	var data = JSON.parse_string(text)
	if data is Dictionary:
		_chronicle_names.load_tables(data.get("name_tables", {}))
		for fragment in data.get("fragments", []):
			if fragment is Dictionary and fragment.has("id"):
				_fragment_library_text_by_id[str(int(fragment["id"]))] = str(fragment.get("text", ""))
	elif data is Array:
		for fragment in data:
			if fragment is Dictionary and fragment.has("id"):
				_fragment_library_text_by_id[str(fragment["id"])] = str(fragment.get("text", ""))


func _resolve_fragment_text(fragment_id: int, region_id: int = -1, faction_id: int = -1) -> String:
	_ensure_fragment_library()
	var key := str(fragment_id)
	if _fragment_library_text_by_id.has(key):
		var raw: String = _fragment_library_text_by_id[key]
		if _chronicle_names != null:
			return _chronicle_names.fill_template(raw, region_id, faction_id)
		return raw
	return "[fragment %d]" % fragment_id


# Resolve text from fragment_ids array: concatenate all non-(-1) ids with a
# space. Each id that is -1 contributes nothing. Returns "" when the array is
# all -1 (callers should check all_minus_one before calling).
func _resolve_fragment_ids(fragment_ids_arr: Array, region_id: int, faction_id: int) -> String:
	var parts: Array = []
	for raw_id in fragment_ids_arr:
		var fid := int(raw_id)
		if fid == -1:
			continue
		var resolved := _resolve_fragment_text(fid, region_id, faction_id)
		if resolved != "":
			parts.append(resolved)
	return " ".join(PackedStringArray(parts))


# Structural line for entries with no fragment text (all ids -1): category
# number, resolved region name (from name tables), and tick range. Never
# contains {, }, or [ characters.
func _structural_line(entry: Dictionary, region_id: int) -> String:
	_ensure_fragment_library()
	var category := int(entry.get("category", 0))
	var start_tick := int(entry.get("start_tick", 0))
	var end_tick := int(entry.get("end_tick", 0))
	var region_label: String
	if _chronicle_names != null and region_id >= 0:
		region_label = _chronicle_names.fill_template("{region_name}", region_id, -1)
		# fill_template returns "[region]" when tables are empty; fall back to numeric.
		if "[" in region_label:
			region_label = "region %d" % region_id
	else:
		region_label = "region %d" % region_id
	return "Cat. %d — %s — t%d–t%d" % [category, region_label, start_tick, end_tick]

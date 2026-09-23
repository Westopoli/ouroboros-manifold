extends PanelContainer

signal entry_finished_printing(entry_id: String)
signal entry_expansion_opened(entry_id: String)
signal entry_expansion_closed(entry_id: String)
signal all_entries_finished()
signal mention_clicked(kind: String, id: String)

var _entries: Dictionary = {}
var _printing_id: String = ""
var _total_expected: int = 0
var _finished_count: int = 0
var _paused: bool = false
var _time_jump_active: bool = false
var _accent: Color
var _faction_colors: Dictionary = {}

var _scroll: ScrollContainer
var _entry_container: VBoxContainer
var _expansion_overlay: Control

# Piece C3 rebind — reads a C transport v1 "chronicle" frame (see file
# header) independent of the legacy begin_time_jump()/queue_entry() path
# above. R-069-02's bible-mandated pace: reported by qa_state() and also
# the actual source of truth for chronicle_entry.gd's print timer, wired
# in via set_pace() in queue_entry() below.
const CHRONICLE_PACE := {
	"word_interval_s": 0.08,
	"fade_s": 0.20,
}
const FRAGMENTS_LIBRARY_PATH := "res://simulation/library/chronicle/fragments.json"
const PLANTS := ["entries-dropped", "refs-unresolved"]

# Piece C8 self-load pattern (docs/northstar/plans/push/specs/C8-M3.md
# "Self-loading pattern"): this panel becomes a directly-routed top-level
# scene with no setup() call, so it self-loads its own snapshot + frame
# fixtures in _ready(). Fallbacks mirror tests/test_chronicle_scroll.gd's
# own _build_minimal_snapshot()/_build_minimal_chronicle_frame() verbatim
# so a missing/unreadable fixture still degrades to the same 6-entry shape
# instead of a blank panel.
const _SNAPSHOT_FIXTURE_PATH := "res://tests/transport/fixtures/snapshot_seed1_tick10.json"
const _FRAME_FIXTURE_PATH := "res://tests/fixtures/chronicle_frame_seed11.json"

var _snapshot_data: Dictionary = {}
var _snapshot_region_ids: Dictionary = {}
var _snapshot_faction_ids: Dictionary = {}

var _fragment_library_loaded: bool = false
var _fragment_library_text_by_id: Dictionary = {}

var _qa_entries: Array = []
var _qa_owners: Dictionary = {}
var _qa_dropped_entries: int = 0
var _qa_unresolved_refs: int = 0
var _qa_hash = null
var _qa_load_ms: float = 0.0
var _qa_regen_count: int = 0
var _qa_expanded_id: int = -1

var _plant_refs_unresolved: bool = false
var _plant_entries_dropped: bool = false


func _ready() -> void:
	_accent = ThemeConstants.get_era_accent(EraConfig.ACTIVE_ERA_ID)
	_build_ui()
	set_snapshot(_load_fixture_or_fallback(_SNAPSHOT_FIXTURE_PATH, _fallback_snapshot()))
	load_frame(_load_fixture_or_fallback(_FRAME_FIXTURE_PATH, _fallback_chronicle_frame()))
	# Stage 11g — listen to the world-view pause coordinator so any holder
	# (region/faction panel, expansion) halts entry printing.
	# See also: scenes/world/world_view_inspection_state.gd
	if FeatureFlags.ENABLE_INSPECTION_PAUSE:
		InspectionState.pause_changed.connect(_on_inspection_pause_changed)


func _load_fixture_or_fallback(path: String, fallback: Dictionary) -> Dictionary:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return fallback
	var text := f.get_as_text()
	f.close()
	var data = JSON.parse_string(text)
	if data is Dictionary:
		return data
	return fallback


func _fallback_snapshot() -> Dictionary:
	var regions := []
	for i in range(60):
		regions.append({
			"i": i,
			"owner": (i % 3) - 1,
			"tier": 1,
			"military": 10.0,
			"economy": 10.0,
			"tension": 10.0,
			"population": 10.0,
			"stability": 10.0,
			"capacity": 10.0,
		})
	var edges := []
	for i in range(59):
		edges.append({"a": i, "b": i + 1, "t": i % 2})
	var factions := []
	for f in range(3):
		factions.append({"id": f, "archetype": 0, "budget": 100.0, "tech": 1.0, "stance": [1, 1, 1]})
	return {"type": "snapshot", "tick": 10, "checksum": 424242, "regions": regions, "factions": factions, "edges": edges}


func _fallback_chronicle_frame() -> Dictionary:
	return {
		"type": "chronicle",
		"jump": {"from_tick": 100, "to_tick": 150},
		"entries": [
			{"id": 201, "start_tick": 102, "end_tick": 109, "category": 0, "cluster_type": 0,
				"refs": {"regions": [3], "factions": [0]}, "fragment": 910201, "significance": 0.92},
			{"id": 202, "start_tick": 111, "end_tick": 116, "category": 5, "cluster_type": 1,
				"refs": {"regions": [4], "factions": [0]}, "fragment": 910202, "significance": 0.71},
			{"id": 203, "start_tick": 119, "end_tick": 131, "category": 10, "cluster_type": 2,
				"refs": {"regions": [12, 13], "factions": [1]}, "fragment": 910203, "significance": 0.83},
			{"id": 204, "start_tick": 133, "end_tick": 137, "category": 16, "cluster_type": 3,
				"refs": {"regions": [24], "factions": [2, 0]}, "fragment": 910204, "significance": 0.68},
			{"id": 205, "start_tick": 139, "end_tick": 143, "category": 16, "cluster_type": 3,
				"refs": {"regions": [25], "factions": [2, 0]}, "fragment": 910205, "significance": 0.62},
			{"id": 206, "start_tick": 145, "end_tick": 149, "category": 17, "cluster_type": 3,
				"refs": {"regions": [13], "factions": [1]}, "fragment": 910206, "significance": 0.51},
		],
	}


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
	_printing_id = ""
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


func start_printing(entry_id: String) -> void:
	if not _entries.has(entry_id):
		return
	_printing_id = entry_id
	_entries[entry_id].start_printing()
	_auto_scroll_to_entry(entry_id)


func end_time_jump() -> void:
	_time_jump_active = false


func skip_all() -> void:
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
	tw.tween_property(self, "position:x", _rest_position_x, 1.0)
	tw.parallel().tween_property(self, "modulate:a", 1.0, 1.0)


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

		var fragment_id := int(entry.get("fragment", -1))
		_qa_entries.append({
			"entry_id": int(entry.get("id", -1)),
			"fragment_id": fragment_id,
			"text": _resolve_fragment_text(fragment_id),
		})

	_qa_hash = hash(frame)
	_qa_regen_count += 1
	_qa_load_ms = float(Time.get_ticks_usec() - start_usec) / 1000.0


func qa_state() -> Dictionary:
	var owners_out := {}
	for rid in _qa_owners:
		owners_out[str(rid)] = _qa_owners[rid]
	return {
		"hash": _qa_hash,
		"timing_ms": {"load": _qa_load_ms},
		"regen_count": _qa_regen_count,
		"entries": _qa_entries.duplicate(true),
		"expanded_id": _qa_expanded_id,
		"owners": owners_out,
		"pace": CHRONICLE_PACE.duplicate(true),
		"dropped_entries": _qa_dropped_entries,
		"unresolved_refs": _qa_unresolved_refs,
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
	var f := FileAccess.open(FRAGMENTS_LIBRARY_PATH, FileAccess.READ)
	if f == null:
		return
	var text := f.get_as_text()
	f.close()
	var data = JSON.parse_string(text)
	if data is Array:
		for fragment in data:
			if fragment is Dictionary and fragment.has("id"):
				_fragment_library_text_by_id[str(fragment["id"])] = str(fragment.get("text", ""))


func _resolve_fragment_text(fragment_id: int) -> String:
	_ensure_fragment_library()
	var key := str(fragment_id)
	if _fragment_library_text_by_id.has(key):
		return _fragment_library_text_by_id[key]
	return "[fragment %d]" % fragment_id

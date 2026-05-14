extends Control

signal panel_opened(kind: String, id: String)
signal panel_closed()
signal open_region_requested(region_id: String)
signal open_faction_requested(faction_id: String)

const RegionInfoPanelScene := preload("res://scenes/world/region_info_panel.tscn")
const FactionInfoPanelScene := preload("res://scenes/world/faction_info_panel.tscn")

const FADE_DURATION := 0.25

var _current_kind: String = ""
var _current_id: String = ""
var _current_panel: Control = null
var _outgoing_panel: Control = null
var _tween: Tween = null


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _holder_for(kind: String) -> String:
	if kind == "region":
		return "region_panel"
	if kind == "faction":
		return "faction_panel"
	return ""


func is_open() -> bool:
	return _current_panel != null


func current_kind() -> String:
	return _current_kind


func current_id() -> String:
	return _current_id


func open_region(region_id: String, region_meta: Dictionary, faction_id: String,
				 faction_name: String, faction_color: Color, ownership_line: String) -> void:
	if _current_kind == "region" and _current_id == region_id and _current_panel != null:
		# Same panel + same id: refresh contents in place, no fade.
		_current_panel.bind(region_meta, faction_id, faction_name, faction_color, ownership_line)
		return

	var panel := RegionInfoPanelScene.instantiate()
	if panel.has_signal("open_faction_requested"):
		panel.open_faction_requested.connect(func(fid: String): open_faction_requested.emit(fid))
	_swap_to(panel, "region", region_id)
	# bind after add_child so _ready has built the UI
	panel.bind(region_meta, faction_id, faction_name, faction_color, ownership_line)


func open_faction(faction_id: String, faction_meta: Dictionary, faction_color: Color,
				  region_rows: Array) -> void:
	if _current_kind == "faction" and _current_id == faction_id and _current_panel != null:
		_current_panel.bind(faction_meta, faction_color, region_rows)
		return

	var panel := FactionInfoPanelScene.instantiate()
	if panel.has_signal("open_region_requested"):
		panel.open_region_requested.connect(func(rid: String): open_region_requested.emit(rid))
	_swap_to(panel, "faction", faction_id)
	panel.bind(faction_meta, faction_color, region_rows)


func close() -> void:
	if _current_panel == null:
		return
	if _tween != null and _tween.is_valid():
		_tween.kill()

	# Stage 11g — release the pause holder for whatever was open.
	if FeatureFlags.ENABLE_INSPECTION_PAUSE:
		var holder := _holder_for(_current_kind)
		if holder != "":
			InspectionState.release(holder)

	_outgoing_panel = _current_panel
	_current_panel = null
	_current_kind = ""
	_current_id = ""
	var outgoing := _outgoing_panel
	_tween = create_tween()
	_tween.tween_property(outgoing, "modulate:a", 0.0, FADE_DURATION)
	_tween.tween_callback(func():
		if outgoing != null and outgoing.get_parent() == self:
			remove_child(outgoing)
			outgoing.queue_free()
	)
	panel_closed.emit()


func _swap_to(new_panel: Control, kind: String, id: String) -> void:
	if _tween != null and _tween.is_valid():
		_tween.kill()

	# Stage 11g — pause refcount: only release if the kind actually changes,
	# so region→region or faction→faction swaps don't briefly unpause the world.
	# See also: scenes/world/world_view_inspection_state.gd
	if FeatureFlags.ENABLE_INSPECTION_PAUSE:
		var old_holder := _holder_for(_current_kind)
		var new_holder := _holder_for(kind)
		if old_holder != "" and old_holder != new_holder:
			InspectionState.release(old_holder)

	new_panel.modulate.a = 0.0
	add_child(new_panel)

	var outgoing := _current_panel
	_current_panel = new_panel
	_current_kind = kind
	_current_id = id

	if FeatureFlags.ENABLE_INSPECTION_PAUSE:
		var holder := _holder_for(kind)
		if holder != "":
			InspectionState.acquire(holder)

	_tween = create_tween()
	_tween.set_parallel(true)
	if outgoing != null:
		_tween.tween_property(outgoing, "modulate:a", 0.0, FADE_DURATION)
	_tween.tween_property(new_panel, "modulate:a", 1.0, FADE_DURATION)
	_tween.chain().tween_callback(func():
		if outgoing != null and outgoing.get_parent() == self:
			remove_child(outgoing)
			outgoing.queue_free()
	)

	panel_opened.emit(kind, id)

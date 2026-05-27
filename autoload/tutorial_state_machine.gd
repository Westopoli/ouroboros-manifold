extends Node

signal beat_fired(beat_id: String)
signal tutorial_completed

const FLAG_PATH := "user://tutorial_completed"
const BEATS_PATH := "res://simulation/library/tutorial/beats.json"
const OVERLAY_SCRIPT_PATH := "res://scenes/tutorial/tutorial_overlay.gd"

const TRIGGER_EVENTS: Array[String] = [
	"mission_load",
	"first_unit_visible",
	"first_unit_selected",
	"first_mission_loaded",
	"first_mission_complete",
]

var _completed: bool = false
var _beats: Dictionary = {}
var _trigger_to_beat_id: Dictionary = {}
var _overlay: Node = null
var _fired_beats: Dictionary = {}


func _ready() -> void:
	if FileAccess.file_exists(FLAG_PATH):
		_completed = true
	_load_beats()


func _load_beats() -> void:
	if not FileAccess.file_exists(BEATS_PATH):
		return
	var f := FileAccess.open(BEATS_PATH, FileAccess.READ)
	if f == null:
		return
	var raw := f.get_as_text()
	f.close()
	var parsed = JSON.parse_string(raw)
	if parsed is Dictionary:
		_beats = parsed
		for beat_id in _beats:
			var beat: Dictionary = _beats[beat_id]
			var trigger := String(beat.get("trigger_event", ""))
			if trigger != "":
				_trigger_to_beat_id[trigger] = beat_id


func handle_trigger(trigger_event: String) -> void:
	if _completed:
		return
	if not _trigger_to_beat_id.has(trigger_event):
		return
	var beat_id: String = _trigger_to_beat_id[trigger_event]
	if _fired_beats.has(beat_id):
		return
	_fired_beats[beat_id] = true
	_ensure_overlay()
	if _overlay != null and _overlay.has_method("show_beat"):
		_overlay.call("show_beat", beat_id)
	beat_fired.emit(beat_id)


func _ensure_overlay() -> void:
	if _overlay != null and is_instance_valid(_overlay):
		return
	var script: Script = load(OVERLAY_SCRIPT_PATH)
	if script == null:
		return
	_overlay = Control.new()
	_overlay.set_script(script)
	get_tree().get_root().add_child(_overlay)
	if _overlay.has_signal("beat_dismissed"):
		_overlay.connect("beat_dismissed", _on_beat_dismissed)


func _on_beat_dismissed(beat_id: String) -> void:
	if beat_id == "TUT_005":
		var f := FileAccess.open(FLAG_PATH, FileAccess.WRITE)
		if f != null:
			f.store_string("1")
			f.close()
		_completed = true
		tutorial_completed.emit()


func reset_for_replay() -> void:
	var abs_path := ProjectSettings.globalize_path(FLAG_PATH)
	if FileAccess.file_exists(FLAG_PATH):
		DirAccess.remove_absolute(abs_path)
	_completed = false
	_fired_beats.clear()
	if _overlay != null and is_instance_valid(_overlay):
		if _overlay.has_method("hide_beat"):
			_overlay.call("hide_beat")
		_overlay.queue_free()
		_overlay = null

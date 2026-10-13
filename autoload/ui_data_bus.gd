extends Node

# Subscription model removed 2026-05-09 — see docs/bible_history/game_bible_1_23.md (bible_monetization.md was folded into the hub 2026-05-31 and the hub rewritten 2026-09-10).
# initiate_purchase() now routes to the data source's open_steam_dlc_page() stub.
signal purchase_requested(era_id: String, purchase_type: String)
signal time_jump_started(time_jump_id: String, span_years: int, total_keyframes: int, total_entries: int, faction_names: Dictionary)
signal time_jump_keyframe(keyframe_data: Dictionary)
signal chronicle_entry(entry_data: Dictionary)
signal time_jump_ended(time_jump_id: String)

const SimSession := preload("res://autoload/sim_session.gd")
const SETTINGS_PATH := "user://settings.cfg"
const RESOLUTIONS := [Vector2i(1280, 720), Vector2i(1600, 900), Vector2i(1920, 1080), Vector2i(2560, 1440), Vector2i(3440, 1440), Vector2i(3840, 2160)]
const VALID_RESOLUTION_COUNT := 6

var _source: RefCounted
var _settings: Dictionary = {}


func _ready() -> void:
	_source = load("res://autoload/sim_bridge_data_source.gd").new()
	_load_settings()


func get_all_eras() -> Array[Dictionary]:
	return _source.get_all_eras()


func get_era_detail(era_id: String) -> Dictionary:
	return _source.get_era_detail(era_id)


func is_era_accessible(era_id: String) -> bool:
	return _source.is_era_accessible(era_id)


func get_save_slots() -> Array[Dictionary]:
	return _source.get_save_slots()


func create_save_slot(era_id: String, slot_name: String) -> Dictionary:
	return _source.create_save_slot(era_id, slot_name)


func delete_save_slot(slot_id: String) -> bool:
	return _source.delete_save_slot(slot_id)


func get_mission_briefing(mission_id: String) -> Dictionary:
	return _source.get_mission_briefing(mission_id)


func initiate_purchase(era_id: String, purchase_type: String) -> void:
	purchase_requested.emit(era_id, purchase_type)
	_source.open_steam_dlc_page(era_id)


func refresh_entitlements() -> void:
	if _source.has_method("refresh_entitlements"):
		_source.refresh_entitlements()


func proceed_to_next_mission() -> void:
	SceneRouter.go_to("mission_briefing")


func get_mission_metrics() -> Dictionary:
	return MissionMetricsRecorder.get_metrics()


func get_bug_report_path() -> String:
	return ProjectSettings.globalize_path(BugReportManager.REPORTS_DIR)


func trigger_autosave(loop_phase: String) -> void:
	SimSession.bridge()._autosave()


func exit_to_main_menu() -> void:
	SceneRouter.go_to("main_menu")


func _load_settings() -> void:
	var config := ConfigFile.new()
	if config.load(SETTINGS_PATH) == OK:
		_settings = {
			"master_volume": config.get_value("audio", "master_volume", 80),
			"music_volume": config.get_value("audio", "music_volume", 70),
			"sfx_volume": config.get_value("audio", "sfx_volume", 80),
			"narration_volume": config.get_value("audio", "narration_volume", 90),
			"resolution_index": config.get_value("display", "resolution_index", 2),
			"fullscreen": config.get_value("display", "fullscreen", false),
			"vsync": config.get_value("display", "vsync", true),
			"galaxy_quality": clampi(int(config.get_value("display", "galaxy_quality", 0)), 0, 2),
			"pan_speed": clampf(float(config.get_value("camera", "pan_speed", 1.0)), 0.5, 2.0),
			"era_id": str(config.get_value("game", "era_id", "settled_reach")),
		}
		EraConfig.apply_saved(_settings["era_id"])
		_apply_stored_settings()
	else:
		_settings = {
			"master_volume": 80,
			"music_volume": 70,
			"sfx_volume": 80,
			"narration_volume": 90,
			"resolution_index": 2,
			"fullscreen": false,
			"vsync": true,
			"galaxy_quality": 0,
			"pan_speed": 1.0,
			"era_id": "settled_reach",
		}


func _apply_stored_settings() -> void:
	var buses := {"Master": "master_volume", "Music": "music_volume", "SFX": "sfx_volume", "Narration": "narration_volume"}
	for bus_name in buses:
		var idx := AudioServer.get_bus_index(bus_name)
		if idx >= 0:
			AudioServer.set_bus_volume_db(idx, linear_to_db(float(_settings[buses[bus_name]]) / 100.0))
	var res_idx := clampi(int(_settings["resolution_index"]), 0, VALID_RESOLUTION_COUNT - 1)
	if bool(_settings["fullscreen"]):
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
	else:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
		DisplayServer.window_set_size(RESOLUTIONS[res_idx])
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED if bool(_settings["vsync"]) else DisplayServer.VSYNC_DISABLED)


func get_settings() -> Dictionary:
	return _settings.duplicate()


func save_settings(settings: Dictionary) -> void:
	var clamped := {
		"master_volume": clampi(int(settings.get("master_volume", 80)), 0, 100),
		"music_volume": clampi(int(settings.get("music_volume", 70)), 0, 100),
		"sfx_volume": clampi(int(settings.get("sfx_volume", 80)), 0, 100),
		"narration_volume": clampi(int(settings.get("narration_volume", 90)), 0, 100),
		"resolution_index": clampi(int(settings.get("resolution_index", 2)), 0, VALID_RESOLUTION_COUNT - 1),
		"fullscreen": bool(settings.get("fullscreen", false)),
		"vsync": bool(settings.get("vsync", true)),
		"galaxy_quality": clampi(int(settings.get("galaxy_quality", 0)), 0, 2),
		"pan_speed": clampf(float(settings.get("pan_speed", 1.0)), 0.5, 2.0),
		"era_id": str(settings.get("era_id", "settled_reach")),
	}
	_settings = clamped
	var config := ConfigFile.new()
	config.set_value("audio", "master_volume", clamped["master_volume"])
	config.set_value("audio", "music_volume", clamped["music_volume"])
	config.set_value("audio", "sfx_volume", clamped["sfx_volume"])
	config.set_value("audio", "narration_volume", clamped["narration_volume"])
	config.set_value("display", "resolution_index", clamped["resolution_index"])
	config.set_value("display", "fullscreen", clamped["fullscreen"])
	config.set_value("display", "vsync", clamped["vsync"])
	config.set_value("display", "galaxy_quality", clamped["galaxy_quality"])
	config.set_value("camera", "pan_speed", clamped["pan_speed"])
	config.set_value("game", "era_id", clamped["era_id"])
	config.save(SETTINGS_PATH)

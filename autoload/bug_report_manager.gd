extends Node

const SimSession := preload("res://autoload/sim_session.gd")

const BUFFER_SNAPSHOTS := 10
const BUFFER_CADENCE_SEC := 1.0
const COMMAND_BUFFER_SEC := 10.0
const REPORTS_DIR := "user://logs/reports"

var _active := true
var _timer := 0.0
var _snapshot_buffer: Array[Dictionary] = []
var _command_log: Array[Dictionary] = []
var _popup_scene := preload("res://scenes/bug_report/bug_report_popup.tscn")


func start_buffering() -> void:
	_active = true
	_timer = 0.0
	_snapshot_buffer.clear()
	_command_log.clear()


func stop_buffering() -> void:
	_active = false


func get_snapshot_buffer() -> Array[Dictionary]:
	return _snapshot_buffer


func get_command_log() -> Array[Dictionary]:
	return _command_log


func log_command(cmd: Dictionary) -> void:
	if not _active:
		return
	_command_log.append({
		"tick": _frame().get("tick", 0),
		"time": Time.get_ticks_msec() / 1000.0,
		"command": cmd.duplicate(true),
	})
	_trim_command_log()


func capture() -> void:
	# Wait one frame so the viewport texture is current
	await RenderingServer.frame_post_draw
	var stamp := Time.get_datetime_string_from_system().replace(":", "").replace("-", "").replace("T", "_")
	var ms := int(fmod(Time.get_unix_time_from_system(), 1.0) * 1000.0)

	var screenshot := _capture_screenshot()

	DirAccess.make_dir_recursive_absolute(REPORTS_DIR)
	# Two captures in one millisecond (same frame) must not share a name.
	while FileAccess.file_exists(REPORTS_DIR.path_join("bug_report_%s_%03d.zip" % [stamp, ms])):
		ms = (ms + 1) % 1000
	var filename := "bug_report_%s_%03d.zip" % [stamp, ms]
	var reports_path := REPORTS_DIR.path_join(filename)

	var downloads_dir := _get_downloads_dir()
	DirAccess.make_dir_recursive_absolute(downloads_dir)
	var downloads_path := downloads_dir.path_join(filename)

	var zip_data := _build_zip(screenshot)

	_write_bytes(reports_path, zip_data)
	_write_bytes(downloads_path, zip_data)

	var abs_reports := ProjectSettings.globalize_path(reports_path)
	var abs_downloads := ProjectSettings.globalize_path(downloads_path)
	_copy_to_clipboard(abs_downloads)
	_flash_hud_label()

	_show_popup(abs_downloads, abs_reports)
	print("BugReport: saved to %s" % abs_downloads)


func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_F12:
			capture()
			get_viewport().set_input_as_handled()


func _process(delta: float) -> void:
	if not _active:
		return
	_timer += delta
	if _timer >= BUFFER_CADENCE_SEC:
		_timer -= BUFFER_CADENCE_SEC
		_take_snapshot()


func _take_snapshot() -> void:
	var frame := _frame()
	if frame.get("units", []).is_empty():
		return
	var snap := {
		"tick": frame.get("tick", 0),
		"time": Time.get_ticks_msec() / 1000.0,
		"units": frame["units"].duplicate(true),
		"structures": frame.get("structures", []).duplicate(true),
		"objectives": frame.get("objectives", []).duplicate(true),
		"unit_count": frame["units"].size(),
	}
	_snapshot_buffer.append(snap)
	while _snapshot_buffer.size() > BUFFER_SNAPSHOTS:
		_snapshot_buffer.pop_front()


func _frame() -> Dictionary:
	return SimSession.bridge().tactical_frame()


func _trim_command_log() -> void:
	if _command_log.is_empty():
		return
	var cutoff: float = _command_log[_command_log.size() - 1].time - COMMAND_BUFFER_SEC
	while _command_log.size() > 0 and _command_log[0].time < cutoff:
		_command_log.pop_front()


func _capture_screenshot() -> PackedByteArray:
	var img := get_viewport().get_texture().get_image()
	if img:
		return img.save_png_to_buffer()
	return PackedByteArray()


func _build_zip(screenshot: PackedByteArray) -> PackedByteArray:
	var tmp_path := "user://tmp_bug_report.zip"
	var writer := ZIPPacker.new()
	if writer.open(tmp_path) != OK:
		return PackedByteArray()

	var metadata := {
		"schema_version": 1,
		"game_version": "0.12.0",
		"os": OS.get_name(),
		"timestamp": Time.get_datetime_string_from_system(),
		"current_tick": _frame().get("tick", 0),
		"buffer_snapshots_count": _snapshot_buffer.size(),
		"command_log_entries": _command_log.size(),
		"note": "Paste this file into Discord for Westopoli.",
	}
	var bridge = SimSession.bridge()
	if bridge != null:
		metadata["seed"] = bridge.live_seed()
	metadata["scene"] = SceneRouter._current_scene_name
	_zip_json(writer, "metadata.json", metadata)

	if not _snapshot_buffer.is_empty():
		for snap in _snapshot_buffer:
			var tick: int = snap.get("tick", 0)
			_zip_json(writer, "tactical_snapshots/snapshot_tick_%d.json" % tick, snap)

	if not _command_log.is_empty():
		_zip_json(writer, "command_log.json", _command_log)

	var metrics := MissionMetricsRecorder.get_metrics()
	if not metrics.get("samples", []).is_empty():
		_zip_json(writer, "mission_metrics.json", metrics)

	if not screenshot.is_empty():
		writer.start_file("screenshot.png")
		writer.write_file(screenshot)
		writer.close_file()

	var crash_path := "res://logs/crash_report.txt"
	if FileAccess.file_exists(crash_path):
		var crash_data := FileAccess.get_file_as_bytes(crash_path)
		writer.start_file("crash_log.txt")
		writer.write_file(crash_data)
		writer.close_file()

	writer.close()

	var zip_data := FileAccess.get_file_as_bytes(tmp_path)
	DirAccess.remove_absolute(tmp_path)
	return zip_data


func _zip_json(writer: ZIPPacker, path: String, data: Variant) -> void:
	writer.start_file(path)
	writer.write_file(JSON.stringify(data, "  ").to_utf8_buffer())
	writer.close_file()


func _write_bytes(path: String, data: PackedByteArray) -> void:
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f:
		f.store_buffer(data)
		f.close()


func _get_downloads_dir() -> String:
	if OS.get_name() == "macOS":
		return OS.get_environment("HOME").path_join("Downloads")
	elif OS.get_name() == "Windows":
		var userprofile := OS.get_environment("USERPROFILE")
		if userprofile != "":
			return userprofile.path_join("Downloads")
	return OS.get_environment("HOME").path_join("Downloads")


func _copy_to_clipboard(path: String) -> void:
	var os_name := OS.get_name()
	if os_name == "macOS":
		# Write AppleScript to temp file to avoid quoting issues with OS.execute
		var script_path := "user://tmp_clipboard.scpt"
		var f := FileAccess.open(script_path, FileAccess.WRITE)
		f.store_string('set the clipboard to (POSIX file "%s")' % path)
		f.close()
		var abs_script := ProjectSettings.globalize_path(script_path)
		var output := []
		var code := OS.execute("osascript", [abs_script], output)
		DirAccess.remove_absolute(script_path)
		if code != 0:
			print("BugReport: file clipboard failed (exit %d), falling back to path" % code)
			DisplayServer.clipboard_set(path)
	elif os_name == "Windows":
		var ps := 'Set-Clipboard -Path "%s"' % path
		OS.execute("powershell", ["-Command", ps])
	else:
		DisplayServer.clipboard_set(path)


func _flash_hud_label() -> void:
	var hud := get_tree().root.find_child("HUD", true, false)
	if hud and hud.has_method("flash_f12"):
		hud.flash_f12()


func _show_popup(downloads_path: String, reports_path: String) -> void:
	var popup := _popup_scene.instantiate()
	popup.setup(downloads_path, reports_path)
	get_tree().root.add_child(popup)

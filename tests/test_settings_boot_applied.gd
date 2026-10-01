extends SceneTree

# Piece C3-G5 (docs/northstar/plans/2026-09-28-gap-fix-and-migration-plan.md G5; E-16 R-110-02;
# Architect ruling 2026-10-01 addendum 4 A10): stored settings are applied at boot. Today
# autoload/ui_data_bus.gd only loads user://settings.cfg into memory; the audio buses and
# the tactical camera are touched only when the Settings scene is opened and a control moved.
#
# The check boots a real child Godot process on a settings.cfg fixture (the fixture
# lives in a throwaway XDG_DATA_HOME, never the player's user dir) and reads what the
# running game looks like once its autoloads are up. One file, two modes: with the
# user arg --probe <mode> this script is the child and prints one "PROBE {json}" line.
#
#   audio  Master and Music bus volume_db follow master_volume / music_volume
#          (linear_to_db(value / 100.0), the mapping scenes/settings/settings.gd uses).
#   edge   R-110-02 / Q-110-01: edge scroll is an on/off TOGGLE. Settings stores the boolean
#          [camera] edge_scroll (default true); the live tactical_c camera edge-pans, mouse at
#          the viewport edge, only when it is on. The speed slider is gone: the stored dict has
#          no edge_scroll_speed, the Settings scene offers no speed slider, and a stale
#          edge_scroll_speed key in the file does not change the pan (pan speed stays the
#          A6 constant PAN_SPEED_PX).
#   display  (desktop only) resolution and fullscreen at boot (window mode read before the first
#          frame, size after it); read by
#          tests/qa/desktop/test_settings_boot_display.py under a real Xvfb display, because
#          the headless DisplayServer is a dummy and window mode and size do not read back.
#
# The correction note: the first version of this test pinned edge_scroll_speed (a speed
# comparison); the rule wins over the stored key, so that assertion was replaced by the toggle.
# Linux/XDG only (XDG_DATA_HOME redirects user://).

const SCRIPT_PATH := "res://tests/test_settings_boot_applied.gd"

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var idx := args.find("--probe")
	if idx != -1 and idx + 1 < args.size():
		await _probe(args[idx + 1])
		return
	await _run_tests()
	_assert(_completed, "the boot-settings checks did not run to the end (a script error aborted them)")
	print("\n=== Settings Boot Applied Test Results ===")
	print("PASS: %d  FAIL: %d" % [_pass_count, _fail_count])
	if _fail_count > 0:
		print("Failures:")
		for msg in _fail_msgs:
			print("  - " + msg)
		print("=== RED ===\n")
		quit(1)
	else:
		print("=== GREEN ===\n")
		quit(0)


func _assert(cond: bool, msg: String) -> void:
	if cond:
		_pass_count += 1
	else:
		_fail_count += 1
		_fail_msgs.append(msg)


# ---- child ------------------------------------------------------------------

func _probe(mode: String) -> void:
	# Under Xvfb there is no window manager, so a fullscreen request reverts a frame after boot:
	# the window mode is read before the first frame, the size after the boot settles.
	var early_mode := DisplayServer.window_get_mode()
	await process_frame
	await process_frame
	var out := {"mode": mode}
	var bus = get_root().get_node_or_null("UIDataBus")
	out["stored"] = bus.get_settings() if bus != null else {}
	if mode == "audio":
		out["master_db"] = AudioServer.get_bus_volume_db(0)
		out["music_db"] = AudioServer.get_bus_volume_db(AudioServer.get_bus_index("Music"))
	elif mode == "edge":
		var view: Node = (load("res://scenes/tactical_c/tactical_view.tscn") as PackedScene).instantiate()
		get_root().add_child(view)
		await process_frame
		await process_frame
		var canvas := float(view.get("_canvas"))
		view.qa_pan(canvas * 0.5, canvas * 0.5)
		view.set("_pointer_seen", true)
		var before: Vector2 = view.get("_camera")
		view._pan_input(0.1)
		var after: Vector2 = view.get("_camera")
		out["moved"] = before.distance_to(after)
	elif mode == "display":
		for _i in 30:
			await process_frame
		out["window_mode"] = early_mode
		out["window_size"] = [DisplayServer.window_get_size().x, DisplayServer.window_get_size().y]
		out["screen_size"] = [DisplayServer.screen_get_size().x, DisplayServer.screen_get_size().y]
	print("PROBE ", JSON.stringify(out))
	quit(0)


# ---- parent -----------------------------------------------------------------

func _boot_child(fixture: String, mode: String) -> Dictionary:
	var base := OS.get_cache_dir().path_join("om_g5_%d_%s" % [OS.get_process_id(), mode])
	var user_dir := base.path_join(str(ProjectSettings.get_setting("application/config/custom_user_dir_name", "data")))
	DirAccess.make_dir_recursive_absolute(user_dir)
	var f := FileAccess.open(user_dir.path_join("settings.cfg"), FileAccess.WRITE)
	f.store_string(fixture)
	f.close()
	var prior := OS.get_environment("XDG_DATA_HOME")
	OS.set_environment("XDG_DATA_HOME", base)
	var output: Array = []
	var code := OS.execute(OS.get_executable_path(),
		["--headless", "--path", ProjectSettings.globalize_path("res://"), "--quit-after", "3000", "--script", SCRIPT_PATH, "--", "--probe", mode],
		output, true)
	if prior == "":
		OS.unset_environment("XDG_DATA_HOME")
	else:
		OS.set_environment("XDG_DATA_HOME", prior)
	DirAccess.remove_absolute(user_dir.path_join("settings.cfg"))
	DirAccess.remove_absolute(user_dir)
	DirAccess.remove_absolute(base)
	var text := "\n".join(PackedStringArray(output))
	for line in text.split("\n"):
		if line.begins_with("PROBE "):
			var parsed = JSON.parse_string(line.substr(6))
			if parsed is Dictionary:
				return parsed
	return {"error": "no PROBE line (exit %d): %s" % [code, text.left(400)]}


func _run_tests() -> void:
	var audio := _boot_child("[audio]\nmaster_volume=30\nmusic_volume=10\n", "audio")
	_assert(not audio.has("error"), "G5 audio: the child boot failed: %s" % audio.get("error", ""))
	if not audio.has("error"):
		var stored: Dictionary = audio.get("stored", {})
		# Positive control: the child really read the fixture, so a default-valued bus below is the bug.
		_assert(int(stored.get("master_volume", -1)) == 30 and int(stored.get("music_volume", -1)) == 10,
			"G5 control: the child did not load the settings fixture (stored %s)" % JSON.stringify(stored))
		var want_master := linear_to_db(0.30)
		var want_music := linear_to_db(0.10)
		_assert(absf(float(audio.get("master_db", 99.0)) - want_master) < 0.1,
			"G5: Master bus is %s dB at boot, expected %.2f dB for master_volume 30" % [audio.get("master_db"), want_master])
		_assert(absf(float(audio.get("music_db", 99.0)) - want_music) < 0.1,
			"G5: Music bus is %s dB at boot, expected %.2f dB for music_volume 10" % [audio.get("music_db"), want_music])

	var off := _boot_child("[camera]\nedge_scroll=false\n", "edge")
	var on := _boot_child("[camera]\nedge_scroll=true\n", "edge")
	var stale := _boot_child("[camera]\nedge_scroll=true\nedge_scroll_speed=3000\n", "edge")
	_assert(not off.has("error") and not on.has("error") and not stale.has("error"),
		"G5 edge: a child boot failed: %s / %s / %s" % [off.get("error", ""), on.get("error", ""), stale.get("error", "")])
	if not off.has("error") and not on.has("error") and not stale.has("error"):
		var s_off: Dictionary = off.get("stored", {})
		var s_on: Dictionary = on.get("stored", {})
		_assert(s_off.get("edge_scroll", null) is bool and s_off.get("edge_scroll") == false
			and s_on.get("edge_scroll", null) is bool and s_on.get("edge_scroll") == true,
			"G5 control: Settings does not store edge scroll as a boolean (off fixture -> %s, on fixture -> %s)" % [s_off.get("edge_scroll", "<absent>"), s_on.get("edge_scroll", "<absent>")])
		_assert(not s_on.has("edge_scroll_speed") and not (stale.get("stored", {}) as Dictionary).has("edge_scroll_speed"),
			"G5: Settings still stores edge_scroll_speed; the speed slider is gone (R-110-02 is on/off)")
		var m_on := float(on.get("moved", 0.0))
		var m_off := float(off.get("moved", 0.0))
		var m_stale := float(stale.get("moved", 0.0))
		_assert(m_on > 0.0, "G5 control: the camera did not edge-pan with edge scroll on (moved %s), so the off case proves nothing" % m_on)
		_assert(m_off == 0.0, "G5: the tactical camera edge-panned %s px with edge_scroll=false at boot; off must not pan" % m_off)
		_assert(absf(m_stale - m_on) < 0.001,
			"G5: a stale edge_scroll_speed changed the pan (%s px vs %s px); pan speed is the constant" % [m_stale, m_on])

	var src := FileAccess.get_file_as_string("res://scenes/settings/settings.gd")
	_assert(src != "", "cannot read scenes/settings/settings.gd")
	_assert(src.find("Edge Scroll Speed") == -1 and src.find("edge_scroll_speed") == -1,
		"G5: scenes/settings/settings.gd still offers the edge scroll speed slider")
	_assert(src.find("Edge Scroll") != -1, "G5: scenes/settings/settings.gd has no Edge Scroll toggle")
	_completed = true

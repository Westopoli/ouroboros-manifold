extends SceneTree

# Plan item C4, unit E2 (docs/northstar/plans/2026-09-30-mission-plays-plan.md C4;
# docs/northstar/plans/2026-09-28-gap-fix-and-migration-plan.md E2): the in-game bug report
# (F12) reads the live bridge and the live tactical frame, never the legacy bridge autoload, and is
# reachable from every live screen. Player-facing behaviour kept: F12 builds a ZIP with a
# screenshot, logs, state and metrics, saves it to user://logs/reports/ and the Downloads
# folder, and shows a confirmation popup.
#
# NOTE: no E-16 rule for the bug report exists, so there is no R-id to name; the tests cite the
# gap-fix plan E2 text and Architect ruling A46 (docs/northstar/plans/2026-10-01-architect-
# rulings-2.md). A46: F12 only, handled in one place so it works on every screen; no pause menu
# is added (the game has no pause), so no test expects a "Report a bug" menu entry; the ZIP name
# gains milliseconds (Q-C4-E2-01 and Q-C4-E2-03 answered).
#
# Not asserted: the ZIP's mission_metrics.json (A46: only if its recorder is live; the recorder
# check is a separate read-only report).
#
# Rules proved, by test id:
#   E2-1  bug_report_manager.gd and bug_report_popup.gd do not name the legacy bridge autoload.
#   E2-2  on a live mission, the captured ZIP (reports dir and Downloads dir) carries the
#         live tick in metadata.json, not the dead bridge's 0.
#   E2-3  the live mission fills the snapshot buffer with the live units, so the ZIP holds
#         a tactical_snapshots/ entry with units.
#   E2-4  a command sent through the live view lands in command_log.json.
#   E2-5  F12 on each live screen produces a ZIP and the "BUG REPORT CAPTURED" popup.
#   E2-6  two captures inside one second give two distinct ZIP names, and the name carries
#         milliseconds (A46, Q-C4-E2-03).
#   E2-7  F12 is handled in exactly one place (A46): one source file hooks the key to a capture,
#         and one F12 press yields exactly one ZIP and one popup.
# Positive controls: C1 (matcher), C2 (the live bridge really advanced past tick 0, so
# E2-2 cannot pass or fail on a dead frame), C3 (the ZIP reader sees metadata.json that
# any capture writes), C4 (F12 on a bare node already captures, so E2-5's finder works).

const SimSession := preload("res://autoload/sim_session.gd")
const MANAGER_PATH := "autoload/bug_report_manager.gd"
const POPUP_PATH := "scenes/bug_report/bug_report_popup.gd"
const TACTICAL_SCENE := "res://scenes/tactical_c/tactical_view.tscn"
const REPORTS_DIR := "user://logs/reports"
const SCREENS := [
	"main_menu", "load_game", "era_library", "settings", "mission_briefing",
	"debrief", "galaxy", "chronicle", "tactical_c", "error_screen", "loading_screen",
]

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _home := ""


func _initialize() -> void:
	await _run_tests()
	print("\n=== Bug Report Live Test Results ===")
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


# Needles are built by concatenation so this file never names the dead bridge itself
# (the G6 ratchet scans every .gd for the name).
func _names_it(text: String) -> bool:
	return text.find("Tactical" + "Bridge") != -1 or text.find("tactical" + "_bridge") != -1


func _reports() -> Array:
	var out: Array = []
	var d := DirAccess.open(REPORTS_DIR)
	if d == null:
		return out
	for f in d.get_files():
		if f.ends_with(".zip"):
			out.append(f)
	return out


func _new_report(before: Array) -> String:
	for f in _reports():
		if not before.has(f):
			return f
	return ""


func _wait_report(before: Array, timeout_s: float) -> String:
	var t0 := Time.get_ticks_msec()
	while Time.get_ticks_msec() - t0 < int(timeout_s * 1000.0):
		var f := _new_report(before)
		if f != "":
			await create_timer(0.2).timeout
			return f
		await process_frame
	return ""


func _read_zip(path: String) -> Dictionary:
	var out := {}
	var z := ZIPReader.new()
	if z.open(path) != OK:
		return out
	for name in z.get_files():
		out[name] = z.read_file(name)
	z.close()
	return out


func _json(files: Dictionary, name: String) -> Variant:
	if not files.has(name):
		return null
	return JSON.parse_string((files[name] as PackedByteArray).get_string_from_utf8())


# The ZIP name carries a one-second timestamp, so two captures inside one second would
# overwrite each other; every capture here starts a clean second after the last.
func _press_f12() -> void:
	await create_timer(1.2).timeout
	var ev := InputEventKey.new()
	ev.keycode = KEY_F12
	ev.pressed = true
	Input.parse_input_event(ev)


# E2-6: the name must end in a millisecond group (3 digits) after the seconds (6 digits),
# whatever separator the implementation picks.
func _has_ms_name(f: String) -> bool:
	var re := RegEx.new()
	re.compile("^bug_report_\\d{8}_\\d{6}\\D?\\d{3}\\.zip$")
	return re.search(f) != null


# E2-7: source files under the live directories whose text hooks F12 to a capture. The popup's
# F12 only dismisses it and the mockup scenes are not on the live path, so neither counts.
func _f12_capture_hooks(sources: Dictionary) -> Array:
	var out: Array = []
	for path in sources.keys():
		var t: String = sources[path]
		if t.find("KEY_F12") != -1 and (t.find("capture(") != -1 or t.find("BugReportManager") != -1):
			out.append(path)
	return out


func _live_sources() -> Dictionary:
	var out := {}
	var stack: Array = ["res://autoload", "res://scenes", "res://scripts"]
	while not stack.is_empty():
		var d: String = stack.pop_back()
		var da := DirAccess.open(d)
		if da == null:
			continue
		for sub in da.get_directories():
			if sub == "mockups" or sub == "harness":
				continue
			stack.append(d.path_join(sub))
		for f in da.get_files():
			if f.ends_with(".gd"):
				out[d.path_join(f)] = FileAccess.get_file_as_string(d.path_join(f))
	return out


func _popups() -> Array:
	var out: Array = []
	for c in get_root().get_children():
		if c is CanvasLayer and c.get_script() != null and String(c.get_script().resource_path).ends_with("bug_report_popup.gd"):
			out.append(c)
	return out


func _clear_popups() -> void:
	for p in _popups():
		p.queue_free()


func _run_tests() -> void:
	_home = ProjectSettings.globalize_path("user://c4_e2_home")
	DirAccess.make_dir_recursive_absolute(_home)
	OS.set_environment("HOME", _home)
	OS.set_environment("USERPROFILE", _home)
	var downloads := _home.path_join("Downloads")

	# E2-1 static: nothing in the bug report names the dead bridge.
	_assert(_names_it("Tactical" + "Bridge.current_tick"), "control C1: matcher misses the dead bridge class name")
	_assert(_names_it("res://autoload/tactical" + "_bridge.gd"), "control C1: matcher misses the dead bridge file name")
	_assert(not _names_it("SimSession.bridge().tactical_frame()"), "control C1: matcher false-positive on the live bridge")
	for p in [MANAGER_PATH, POPUP_PATH]:
		var src := FileAccess.get_file_as_string("res://" + p)
		_assert(src != "", "E2-1: cannot read " + p)
		_assert(not _names_it(src), "E2-1: %s still names the legacy bridge autoload (E2: read the live bridge and tactical frame)" % p)

	# E2-7 static: exactly one source file hooks F12 to a capture.
	_assert(_f12_capture_hooks({"a.gd": "if k == KEY_F12: capture()", "b.gd": "KEY_F12 BugReportManager.capture()"}).size() == 2, "control C7: hook finder misses a duplicate F12 hook")
	_assert(_f12_capture_hooks({"a.gd": "if k == KEY_F12: dismiss()"}).is_empty(), "control C7: hook finder false-positive on a dismiss-only handler")
	var hooks := _f12_capture_hooks(_live_sources())
	_assert(hooks == ["res://" + MANAGER_PATH], "E2-7: F12 must be hooked to a capture in exactly one place (" + MANAGER_PATH + "), found: " + str(hooks))

	# E2-6 control C6: the name matcher.
	_assert(_has_ms_name("bug_report_20261001_120000_123.zip"), "control C6: matcher rejects a millisecond name")
	_assert(not _has_ms_name("bug_report_20261001_120000.zip"), "control C6: matcher accepts a seconds-only name")

	if DisplayServer.get_name() == "headless":
		print("NOTE: headless run, capture tests skipped (frame_post_draw never fires without a display); only E2-1 ran. Run under xvfb-run -a for E2-2..E2-5.")
		return

	# E2-5 control C4: F12 on a bare node (no screen) already captures.
	var before := _reports()
	await _press_f12()
	var f0 := await _wait_report(before, 5.0)
	_assert(f0 != "", "control C4: F12 with no screen produced no ZIP in %s within 5 s" % REPORTS_DIR)
	if f0 != "":
		var files0 := _read_zip(REPORTS_DIR.path_join(f0))
		_assert(files0.has("metadata.json"), "control C3: ZIP reader found no metadata.json in %s (entries: %s)" % [f0, str(files0.keys())])
	_clear_popups()
	await process_frame

	# E2-6 control C5: two captures a clean second apart already give two names.
	var mgr = get_root().get_node("BugReportManager")
	before = _reports()
	await create_timer(1.2).timeout
	await mgr.capture()
	await create_timer(1.2).timeout
	await mgr.capture()
	var spaced := _reports().filter(func(n): return not before.has(n))
	_assert(spaced.size() == 2, "control C5: two captures 1.2 s apart gave %d new ZIP names, expected 2" % spaced.size())
	_clear_popups()

	# E2-6: two captures inside one second must not overwrite each other.
	before = _reports()
	await create_timer(1.2).timeout
	var done := [0]
	var run_capture := func() -> void:
		await mgr.capture()
		done[0] += 1
	run_capture.call()
	run_capture.call()
	var tw := Time.get_ticks_msec()
	while done[0] < 2 and Time.get_ticks_msec() - tw < 10000:
		await process_frame
	var burst := _reports().filter(func(n): return not before.has(n))
	_assert(burst.size() == 2, "E2-6: two captures in one second gave %d distinct ZIP names, expected 2 (names: %s)" % [burst.size(), str(burst)])
	for n in burst:
		_assert(_has_ms_name(n), "E2-6: ZIP name '%s' does not carry milliseconds" % n)
	_clear_popups()
	await process_frame

	# E2-7 dynamic: one F12 press gives exactly one ZIP and one popup (a second hook would give two).
	before = _reports()
	await _press_f12()
	await _wait_report(before, 5.0)
	await create_timer(1.0).timeout
	var once := _reports().filter(func(n): return not before.has(n))
	_assert(once.size() == 1, "E2-7: one F12 press produced %d ZIPs, expected exactly 1 (a second handler?)" % once.size())
	_assert(_popups().size() == 1, "E2-7: one F12 press showed %d popups, expected exactly 1" % _popups().size())
	_clear_popups()
	await process_frame

	# Live mission, mounted the way the player reaches it.
	var packed = load(TACTICAL_SCENE)
	_assert(packed is PackedScene, "cannot load " + TACTICAL_SCENE)
	if not (packed is PackedScene):
		return
	var v: Node = (packed as PackedScene).instantiate()
	get_root().add_child(v)
	await process_frame
	await process_frame
	var bridge = SimSession.bridge()
	var st: Dictionary = v.qa_state()
	_assert(int(st.get("unit_count", 0)) > 0, "setup: the live mission frame has no units (live load failed?)")
	if int(st.get("unit_count", 0)) == 0:
		return
	bridge.tactical_step_n(40)
	v.load_frame(bridge.tactical_frame())
	var live_tick := int(bridge.tactical_frame().get("tick", 0))
	_assert(live_tick > 0, "control C2: the live bridge tick is %d after stepping, the E2-2 reading is meaningless" % live_tick)

	# Let the buffer cadence (1 s) run at least twice over the live mission, then send a command.
	var uid := -1
	var ids: Array = st.get("units", {}).keys()
	for k in ids:
		if int(st["units"][k].get("faction", -1)) == int(st.get("local_faction", 0)):
			uid = int(k)
			break
	if uid >= 0:
		var u: Dictionary = st["units"][str(uid)] if st["units"].has(str(uid)) else st["units"][uid]
		v.send_command({"kind": "move", "unit_ids": [uid], "x": float(u.get("x", 800.0)) + 40.0, "y": float(u.get("y", 800.0)) + 40.0})
	var t0 := Time.get_ticks_msec()
	while Time.get_ticks_msec() - t0 < 2500:
		await process_frame
	var post_tick := int(bridge.tactical_frame().get("tick", 0))

	before = _reports()
	var dl_before: Array = []
	var dd := DirAccess.open(downloads)
	if dd != null:
		dl_before = Array(dd.get_files())
	await _press_f12()
	var fname := await _wait_report(before, 8.0)
	_assert(fname != "", "E2-2: F12 on the live tactical view produced no ZIP in %s" % REPORTS_DIR)
	if fname != "":
		var files := _read_zip(REPORTS_DIR.path_join(fname))
		var meta: Variant = _json(files, "metadata.json")
		_assert(meta is Dictionary, "E2-2: no readable metadata.json in %s" % fname)
		if meta is Dictionary:
			var mt := int((meta as Dictionary).get("current_tick", -1))
			_assert(mt > 0 and mt <= int(bridge.tactical_frame().get("tick", 0)),
				"E2-2: metadata current_tick is %d, the live tick was %d..%d (the dead bridge reads 0)" % [mt, live_tick, post_tick])
		var snaps := 0
		for n in files.keys():
			if String(n).begins_with("tactical_snapshots/"):
				var s: Variant = _json(files, n)
				if s is Dictionary and (s as Dictionary).get("units", {}).size() > 0:
					snaps += 1
		_assert(snaps > 0, "E2-3: ZIP has no tactical_snapshots/ entry with units (entries: %s)" % str(files.keys()))
		var cl: Variant = _json(files, "command_log.json")
		_assert(cl is Array and (cl as Array).size() > 0, "E2-4: command_log.json missing or empty after a live move command (entries: %s)" % str(files.keys()))
		if DisplayServer.get_name() != "headless":
			_assert(files.has("screenshot.png"), "E2: no screenshot.png in the ZIP on a desktop run")
		var dd2 := DirAccess.open(downloads)
		_assert(dd2 != null and Array(dd2.get_files()).has(fname) and not dl_before.has(fname), "E2: the ZIP %s was not also saved to the Downloads folder %s" % [fname, downloads])
	_clear_popups()
	v.queue_free()
	await process_frame
	await process_frame

	# E2-5: F12 on every live screen.
	var router = get_root().get_node("SceneRouter")
	for name in SCREENS:
		var path: String = router.SCENES.get(name, "")
		_assert(path != "", "E2-5 setup: SceneRouter has no screen '%s'" % name)
		if path == "":
			continue
		var res = load(path)
		if not (res is PackedScene):
			_assert(false, "E2-5: cannot load screen %s (%s)" % [name, path])
			continue
		var scr: Node = (res as PackedScene).instantiate()
		get_root().add_child(scr)
		await process_frame
		await process_frame
		var b := _reports()
		await _press_f12()
		var f := await _wait_report(b, 15.0)
		_assert(f != "", "E2-5: F12 on screen '%s' produced no ZIP" % name)
		_assert(_popups().size() > 0, "E2-5: F12 on screen '%s' showed no BUG REPORT CAPTURED popup" % name)
		_clear_popups()
		scr.queue_free()
		await process_frame
		await process_frame

extends SceneTree

# Ruling A54 (docs/northstar/plans/2026-10-01-architect-rulings-2.md Addendum 23; replaces A48 item 8
# and gap-fix G-G4; register Q-106-04 closed: "manually configure, not an auto-switch"; E-16 S-106):
# galaxy quality is a MANUAL Settings choice with three values (full 0, stand-in 1, fewer particles 2),
# default full, stored and applied at boot with the other settings.
#
# Names chosen by THIS test, not by the ruling (the Doer must match them):
#   stored key     [display] galaxy_quality, an int 0..2 in user://settings.cfg;
#                  UIDataBus.get_settings()["galaxy_quality"] (autoload/ui_data_bus.gd).
#   Settings UI    exactly one OptionButton with 3 items, in the order full, stand-in, fewer
#                  particles (item text contains "full", "stand", "particle"), next to a Label
#                  containing "quality"; written by the APPLY button like every other setting.
# This file proves the setting and its storage (headless). What each value DRAWS, and that the game
# never changes it, is tests/qa/desktop/test_galaxy_quality.py.
#
# One file, two roles: with the user arg --probe <mode> this script is the child and prints one
# "PROBE {json}" line. Child boots use a throwaway XDG_DATA_HOME so user://settings.cfg is a fixture,
# never the player's file. Linux/XDG only.
#   ui      builds Settings, reads the quality control, selects tier 2, presses APPLY, reads the file
#   boot    reports the stored value and what a NEW Settings instance shows (the "persists, applied
#           at boot" proof: a fresh process, then a fresh scene reading it)

const SCRIPT_PATH := "res://tests/test_galaxy_quality_setting.gd"

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
	_assert(_completed, "the galaxy-quality setting checks did not run to the end (a script error aborted them)")
	print("\n=== Galaxy Quality Setting Test Results ===")
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

func _quality_control(scene: Node) -> Dictionary:
	var found := {"option_buttons": [], "labels": [], "apply": null, "control": null}
	_collect(scene, found)
	var threes: Array = found["option_buttons"].filter(func(o): return o.item_count == 3)
	found["control"] = threes[0] if threes.size() == 1 else null
	found["control_count"] = threes.size()
	return found


func _collect(node: Node, out: Dictionary) -> void:
	if node is OptionButton:
		out["option_buttons"].append(node)
	elif node is Label:
		out["labels"].append(String(node.text))
	if "text" in node and String(node.get("text")) == "APPLY":
		out["apply"] = node
	for child in node.get_children():
		_collect(child, out)


func _describe(scene: Node) -> Dictionary:
	var found := _quality_control(scene)
	var d := {"control_count": found["control_count"], "labels": found["labels"], "has_apply": found["apply"] != null}
	var ctl: OptionButton = found["control"]
	if ctl != null:
		d["selected"] = ctl.selected
		d["items"] = []
		for i in ctl.item_count:
			d["items"].append(ctl.get_item_text(i))
	return d


func _probe(mode: String) -> void:
	await process_frame
	await process_frame
	var out := {"mode": mode}
	var bus = get_root().get_node_or_null("UIDataBus")
	out["stored"] = bus.get_settings() if bus != null else {}
	var scene: Node = (load("res://scenes/settings/settings.tscn") as PackedScene).instantiate()
	get_root().add_child(scene)
	await process_frame
	out["ui"] = _describe(scene)
	if mode == "ui":
		var found := _quality_control(scene)
		var ctl: OptionButton = found["control"]
		if ctl != null:
			ctl.select(2)
			ctl.item_selected.emit(2)
		if found["apply"] != null:
			found["apply"].pressed.emit()
			await process_frame
			out["after_apply"] = bus.get_settings()
			var cfg := ConfigFile.new()
			cfg.load("user://settings.cfg")
			out["file_display"] = {}
			if cfg.has_section("display"):
				for key in cfg.get_section_keys("display"):
					out["file_display"][key] = cfg.get_value("display", key)
	print("PROBE ", JSON.stringify(out))
	quit(0)


# ---- parent -----------------------------------------------------------------

func _base_dir(tag: String) -> String:
	return OS.get_cache_dir().path_join("om_a54_%d_%s" % [OS.get_process_id(), tag])


func _user_dir(base: String) -> String:
	return base.path_join(str(ProjectSettings.get_setting("application/config/custom_user_dir_name", "data")))


func _write_fixture(base: String, fixture: String) -> void:
	var user_dir := _user_dir(base)
	DirAccess.make_dir_recursive_absolute(user_dir)
	if fixture != "":
		var f := FileAccess.open(user_dir.path_join("settings.cfg"), FileAccess.WRITE)
		f.store_string(fixture)
		f.close()


func _cleanup(base: String) -> void:
	var user_dir := _user_dir(base)
	DirAccess.remove_absolute(user_dir.path_join("settings.cfg"))
	DirAccess.remove_absolute(user_dir)
	DirAccess.remove_absolute(base)


func _run_child(base: String, mode: String) -> Dictionary:
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
	var text := "\n".join(PackedStringArray(output))
	for line in text.split("\n"):
		if line.begins_with("PROBE "):
			var parsed = JSON.parse_string(line.substr(6))
			if parsed is Dictionary:
				return parsed
	return {"error": "no PROBE line (exit %d): %s" % [code, text.left(400)]}


func _boot_child(fixture: String, mode: String) -> Dictionary:
	var base := _base_dir(mode)
	_write_fixture(base, fixture)
	var res := _run_child(base, mode)
	_cleanup(base)
	return res


func _run_tests() -> void:
	# --- default, and the control exists (R-110-02 Settings; A54) ---
	var fresh := _boot_child("[audio]\nmaster_volume=30\n", "ui")
	_assert(not fresh.has("error"), "A54 ui: the child boot failed: %s" % fresh.get("error", ""))
	if not fresh.has("error"):
		var ui: Dictionary = fresh.get("ui", {})
		# Positive control: the Settings scene really built (it has the 6-item resolution dropdown and APPLY).
		_assert(bool(ui.get("has_apply", false)), "A54 control: the Settings scene built no APPLY button")
		_assert(int(ui.get("control_count", -1)) == 1,
			"A54: Settings has %s three-item OptionButtons (galaxy quality), expected exactly one" % ui.get("control_count"))
		var texts := " | ".join(PackedStringArray(ui.get("labels", []))).to_lower()
		_assert(texts.find("quality") != -1, "A54: no Settings label mentions galaxy quality (labels: %s)" % texts)
		var items: Array = ui.get("items", [])
		if items.size() == 3:
			_assert(String(items[0]).to_lower().find("full") != -1, "A54: quality item 0 is '%s', expected full" % items[0])
			_assert(String(items[1]).to_lower().find("stand") != -1, "A54: quality item 1 is '%s', expected stand-in" % items[1])
			_assert(String(items[2]).to_lower().find("particle") != -1, "A54: quality item 2 is '%s', expected fewer particles" % items[2])
		_assert(int(ui.get("selected", -1)) == 0, "A54: with nothing stored the quality control shows item %s, expected the default full (0)" % ui.get("selected"))
		var stored: Dictionary = fresh.get("stored", {})
		_assert(stored.has("galaxy_quality") and int(stored["galaxy_quality"]) == 0,
			"A54: UIDataBus settings carry no default galaxy_quality of 0 (stored %s)" % JSON.stringify(stored))
		# --- choosing a value and APPLY writes it (A54 'stored') ---
		var after: Dictionary = fresh.get("after_apply", {})
		_assert(after.has("galaxy_quality") and int(after["galaxy_quality"]) == 2,
			"A54: choosing 'fewer particles' and pressing APPLY left UIDataBus galaxy_quality at %s, expected 2" % after.get("galaxy_quality"))
		var file_display: Dictionary = fresh.get("file_display", {})
		_assert(file_display.has("galaxy_quality") and int(file_display["galaxy_quality"]) == 2,
			"A54: APPLY wrote [display] %s to user://settings.cfg, expected galaxy_quality=2" % JSON.stringify(file_display))
		# Control against a vacuous pass: the other display keys are still written (existing storage works).
		_assert(file_display.has("vsync") and file_display.has("resolution_index"),
			"A54 control: APPLY wrote no resolution_index/vsync to [display] (%s); the storage path itself broke" % JSON.stringify(file_display))

	# --- persists across boots: apply in one process, read in a fresh process and a fresh scene ---
	var base := _base_dir("persist")
	_write_fixture(base, "")
	var first := _run_child(base, "ui")
	var second := _run_child(base, "boot")
	_cleanup(base)
	_assert(not first.has("error") and not second.has("error"),
		"A54 persist: a child boot failed: %s / %s" % [first.get("error", ""), second.get("error", "")])
	if not first.has("error") and not second.has("error"):
		var s2: Dictionary = second.get("stored", {})
		_assert(s2.has("galaxy_quality") and int(s2["galaxy_quality"]) == 2,
			"A54: after APPLY in one run, a fresh boot loads galaxy_quality=%s, expected 2" % s2.get("galaxy_quality"))
		_assert(int(second.get("ui", {}).get("selected", -1)) == 2,
			"A54: a new Settings instance shows quality item %s after a fresh boot, expected 2 (fewer particles)" % second.get("ui", {}).get("selected"))

	# --- stored value at boot, every tier ---
	for tier in [0, 1, 2]:
		var r := _boot_child("[display]\ngalaxy_quality=%d\n" % tier, "boot")
		_assert(not r.has("error"), "A54 boot tier %d: child failed: %s" % [tier, r.get("error", "")])
		if r.has("error"):
			continue
		var st: Dictionary = r.get("stored", {})
		_assert(st.has("galaxy_quality") and int(st["galaxy_quality"]) == tier,
			"A54: stored galaxy_quality=%d loaded as %s at boot" % [tier, st.get("galaxy_quality")])
		_assert(int(r.get("ui", {}).get("selected", -1)) == tier,
			"A54: stored galaxy_quality=%d but a new Settings instance shows item %s" % [tier, r.get("ui", {}).get("selected")])

	# --- out-of-range or unusable stored value is clamped (A60): below 0 -> 0, above 2 -> 2,
	# non-int -> default 0. The valid-tier loop above is the control: a read path that clamps
	# everything to one end, or ignores the stored value, fails there. ---
	var clamp_cases := [
		["7", 2, "above 2 clamps to 2"],
		["-3", 0, "below 0 clamps to 0"],
		["\"x\"", 0, "a non-int string falls back to the default 0"],
		["", 0, "a settings file with no galaxy_quality key gives the default 0"],
	]
	for c in clamp_cases:
		var fixture := "[display]\nvsync=true\n" if c[0] == "" else "[display]\ngalaxy_quality=%s\n" % c[0]
		var r := _boot_child(fixture, "boot")
		_assert(not r.has("error"), "A60 clamp (%s): child failed: %s" % [c[2], r.get("error", "")])
		if r.has("error"):
			continue
		var st: Dictionary = r.get("stored", {})
		_assert(st.has("galaxy_quality") and int(st["galaxy_quality"]) == int(c[1]),
			"A60: stored galaxy_quality=%s: %s, but UIDataBus carries %s" % [c[0], c[2], st.get("galaxy_quality")])
		_assert(int(r.get("ui", {}).get("selected", -1)) == int(c[1]),
			"A60: stored galaxy_quality=%s: a new Settings instance shows item %s, expected %d" % [c[0], r.get("ui", {}).get("selected"), c[1]])
	_completed = true

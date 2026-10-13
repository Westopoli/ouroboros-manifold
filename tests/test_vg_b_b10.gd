extends SceneTree

# Piece B10 (docs/northstar/plans/workflows_2026-10-07/vg-wave2b-laneB.js; ruling A54 and A60 in
# docs/northstar/plans/2026-10-01-architect-rulings-2.md; E-16 R-110-02 / S-106): the galaxy quality
# setting is STORED ([display] galaxy_quality, int 0..2, default 0, clamped on save and on read),
# READ by scenes/galaxy/galaxy_quality.gd, and APPLIED to the shell renderer's res_divisor
# (the quality hook of the field renderer, shell_renderer.gd: 1 full, 2 half, 4 quarter).
# The Settings control and what each tier draws are the existing A54 stack tests, not repeated here.
#
# Names chosen by THIS test (the Doer must match them; the rulebook/ruling give none):
#   scenes/galaxy/galaxy_quality.gd, static funcs, no instance:
#     tier_from_settings(settings: Dictionary) -> int   missing key = 0; clamped to 0..2
#     res_divisor_for_tier(tier: int) -> int            tier clamped to 0..2
#     apply(shell: Object, settings: Dictionary) -> int sets shell.res_divisor, returns the tier
#     read_tier() -> int                                reads UIDataBus.get_settings()
# NOT GIVEN by any doc (reported to the Architect, so not pinned here): the exact divisor of each
# tier. This test pins only what the shell_renderer comment gives: divisors come from {1, 2, 4},
# never get finer as the tier rises, and tier 2 is coarser than tier 0 (positive control: a view
# that ignores the setting fails). A60: the view reads the setting when built; no live re-apply.
#
# One file, two roles: with the user arg --probe the script is the child, booted on a throwaway
# XDG_DATA_HOME so user://settings.cfg is a fixture, never the player's file. Linux/XDG only.

const SCRIPT_PATH := "res://tests/test_vg_b_b10.gd"
const QUALITY_PATH := "res://scenes/galaxy/galaxy_quality.gd"

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false


class StubShell extends Node3D:
	var res_divisor := 2


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var idx := args.find("--probe")
	if idx != -1 and idx + 1 < args.size():
		await _probe(args[idx + 1])
		return
	await _run_tests()
	_assert(_completed, "the B10 galaxy-quality checks did not run to the end (a script error aborted them)")
	print("\n=== VG B10 Galaxy Quality Test Results ===")
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
	await process_frame
	await process_frame
	var out := {"mode": mode}
	var bus = get_root().get_node_or_null("UIDataBus")
	out["has_bus"] = bus != null
	if bus != null:
		out["stored"] = bus.get_settings()
		if mode == "save":
			for v in [7, -3, 1]:
				var s: Dictionary = bus.get_settings()
				s["galaxy_quality"] = v
				bus.save_settings(s)
				out["after_%d" % v] = bus.get_settings().get("galaxy_quality", -1)
			var cfg := ConfigFile.new()
			cfg.load("user://settings.cfg")
			out["file_value"] = cfg.get_value("display", "galaxy_quality", -1)
	var gq = load(QUALITY_PATH) if ResourceLoader.exists(QUALITY_PATH) else null
	out["has_quality_script"] = gq != null
	if gq != null and bus != null:
		out["read_tier"] = gq.read_tier()
	print("PROBE ", JSON.stringify(out))
	quit(0)


# ---- parent -----------------------------------------------------------------

func _base_dir(tag: String) -> String:
	return OS.get_cache_dir().path_join("om_vgb10_%d_%s" % [OS.get_process_id(), tag])


func _user_dir(base: String) -> String:
	return base.path_join(str(ProjectSettings.get_setting("application/config/custom_user_dir_name", "data")))


func _cleanup(base: String) -> void:
	var user_dir := _user_dir(base)
	DirAccess.remove_absolute(user_dir.path_join("settings.cfg"))
	DirAccess.remove_absolute(user_dir)
	DirAccess.remove_absolute(base)


func _boot_child(fixture: String, mode: String) -> Dictionary:
	var base := _base_dir(mode)
	var user_dir := _user_dir(base)
	DirAccess.make_dir_recursive_absolute(user_dir)
	if fixture != "":
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
	_cleanup(base)
	var text := "\n".join(PackedStringArray(output))
	for line in text.split("\n"):
		if line.begins_with("PROBE "):
			var parsed = JSON.parse_string(line.substr(6))
			if parsed is Dictionary:
				return parsed
	return {"error": "no PROBE line (exit %d): %s" % [code, text.left(400)]}


func _run_tests() -> void:
	# --- pure mapping: read and apply (isolation, no file I/O) ---
	_assert(ResourceLoader.exists(QUALITY_PATH),
		"B10: %s does not exist (the galaxy quality reader/applier is not built)" % QUALITY_PATH)
	if ResourceLoader.exists(QUALITY_PATH):
		var gq = load(QUALITY_PATH)
		_assert(gq.tier_from_settings({}) == 0, "B10: with no galaxy_quality key the tier is not the default 0")
		_assert(gq.tier_from_settings({"galaxy_quality": 1}) == 1, "B10: stored 1 is not read as tier 1")
		_assert(gq.tier_from_settings({"galaxy_quality": 2}) == 2, "B10: stored 2 is not read as tier 2")
		_assert(gq.tier_from_settings({"galaxy_quality": 9}) == 2, "B10: stored 9 is not clamped to 2 (A60)")
		_assert(gq.tier_from_settings({"galaxy_quality": -4}) == 0, "B10: stored -4 is not clamped to 0 (A60)")
		var allowed := [1, 2, 4]
		var divs: Array = []
		for t in 3:
			var d: int = gq.res_divisor_for_tier(t)
			divs.append(d)
			_assert(allowed.has(d), "B10: tier %d maps to res_divisor %d, outside the documented {1, 2, 4}" % [t, d])
		_assert(divs[0] <= divs[1] and divs[1] <= divs[2], "B10: res_divisor gets finer as the tier rises: %s" % str(divs))
		_assert(divs[2] > divs[0], "B10: tier 2 and tier 0 share res_divisor %s (the setting changes nothing)" % str(divs))
		_assert(gq.res_divisor_for_tier(7) == divs[2] and gq.res_divisor_for_tier(-1) == divs[0],
			"B10: out-of-range tiers are not clamped to the end tiers")
		# apply: the stub stands in for shell_renderer.gd (its public res_divisor var).
		for t in 3:
			var shell := StubShell.new()
			shell.res_divisor = 3  # a sentinel apply must overwrite
			var got = gq.apply(shell, {"galaxy_quality": t})
			_assert(got == t, "B10 apply: returned tier %s for stored %d" % [str(got), t])
			_assert(shell.res_divisor == divs[t],
				"B10 apply: tier %d left res_divisor %d, expected %d" % [t, shell.res_divisor, divs[t]])
			shell.free()
		var shell2 := StubShell.new()
		gq.apply(shell2, {})
		_assert(shell2.res_divisor == divs[0], "B10 apply: no stored key must apply the default tier 0 divisor")
		shell2.free()

	# --- stored: default, fixture read, clamp and persistence (real UIDataBus, throwaway user dir) ---
	var fresh := _boot_child("[audio]\nmaster_volume=30\n", "default")
	_assert(not fresh.has("error"), "B10 default: the child boot failed: %s" % fresh.get("error", ""))
	if not fresh.has("error"):
		_assert(bool(fresh.get("has_bus", false)), "B10 control: the UIDataBus autoload did not boot in the child")
		var stored: Dictionary = fresh.get("stored", {})
		_assert(stored.has("galaxy_quality") and int(stored["galaxy_quality"]) == 0,
			"B10: UIDataBus settings carry no default galaxy_quality 0 (stored %s)" % JSON.stringify(stored))
		_assert(int(fresh.get("read_tier", -1)) == 0, "B10: galaxy_quality.read_tier() is %s with nothing stored, expected 0" % str(fresh.get("read_tier")))
	for tier in [1, 2]:
		var r := _boot_child("[display]\ngalaxy_quality=%d\n" % tier, "fix%d" % tier)
		_assert(not r.has("error"), "B10 fixture %d: the child boot failed: %s" % [tier, r.get("error", "")])
		if not r.has("error"):
			_assert(int(r.get("stored", {}).get("galaxy_quality", -1)) == tier,
				"B10: a stored galaxy_quality=%d loaded as %s" % [tier, str(r.get("stored", {}).get("galaxy_quality"))])
			_assert(int(r.get("read_tier", -1)) == tier, "B10: read_tier() is %s for stored %d" % [str(r.get("read_tier")), tier])
	var bad := _boot_child("[display]\ngalaxy_quality=9\n", "outofrange")
	if not bad.has("error"):
		_assert(int(bad.get("read_tier", -1)) == 2, "B10: read_tier() is %s for a stored 9, expected the clamp to 2" % str(bad.get("read_tier")))
	var sv := _boot_child("", "save")
	_assert(not sv.has("error"), "B10 save: the child boot failed: %s" % sv.get("error", ""))
	if not sv.has("error"):
		_assert(int(sv.get("after_7", -1)) == 2, "B10: save_settings with galaxy_quality 7 kept %s, expected 2" % str(sv.get("after_7")))
		_assert(int(sv.get("after_-3", -1)) == 0, "B10: save_settings with galaxy_quality -3 kept %s, expected 0" % str(sv.get("after_-3")))
		_assert(int(sv.get("after_1", -1)) == 1, "B10: save_settings with galaxy_quality 1 kept %s" % str(sv.get("after_1")))
		_assert(int(sv.get("file_value", -1)) == 1,
			"B10: [display] galaxy_quality in settings.cfg is %s after saving 1" % str(sv.get("file_value")))
	_completed = true

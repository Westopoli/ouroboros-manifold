extends SceneTree

# Rule pins: none (harness piece SHOWCASE-legacy-scenes: no S- or R- id; spec docs/northstar/plans/showcase/README.md, paragraph "SHOWCASE-legacy-scenes")
#
# SHOWCASE-legacy-scenes: eight of the nine scenes/debug/* scenes move to legacy/scenes/debug/ with their .gd and .uid
# sidecars; debug_ws_test.* stays (tests/test_tacticalbridge_ratchet.gd KNOWN_REFERENCERS names it); legacy/README.md lists each.
#
# UNSTATED INTERFACE CHOICES:
# - "not loadable at its old res:// path" is read as ResourceLoader.exists() false for the .tscn and the .gd.
# - "the new location is loadable" is read as load() returning a PackedScene for the .tscn.
# - "legacy/README.md lists each" is asserted as the scene's file stem appearing in the README text; the paragraph gives no
#   line format for "last commit and purpose", so those are NOT asserted (gap).
# - Each scene's .gd.uid sidecar is asserted to sit at the new path and be gone from the old one.
# Controls: debug_ws_test.tscn still loads at its old path (so "not loadable" is not a blanket failure of ResourceLoader on
# scenes/debug), and the live scenes/tactical_c/tactical_view.tscn loads.

const MOVED := ["test_chronicle_scroll", "test_faction_info_panel", "test_faction_palette", "test_info_panel_host",
	"test_region_info_panel", "test_time_jump", "test_world_view", "wave2_visual_check"]
const OLD_DIR := "res://scenes/debug/"
const NEW_DIR := "res://legacy/scenes/debug/"

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	_run_tests()
	print("\n=== Showcase Legacy Scenes Test Results ===")
	print("PASS: %d  FAIL: %d" % [_pass_count, _fail_count])
	if _fail_count > 0:
		print("Failures:")
		for msg in _fail_msgs:
			print("  - " + msg)
	quit(1 if _fail_count > 0 else 0)


func _assert(cond: bool, msg: String) -> void:
	if cond:
		_pass_count += 1
	else:
		_fail_count += 1
		_fail_msgs.append(msg)


func _run_tests() -> void:
	_assert(ResourceLoader.exists(OLD_DIR + "debug_ws_test.tscn"), "control C1: debug_ws_test.tscn no longer loadable at its old path (it stays)")
	_assert(load("res://scenes/tactical_c/tactical_view.tscn") is PackedScene, "control C2: the live tactical scene does not load")
	_assert(not ResourceLoader.exists(OLD_DIR + "no_such_scene.tscn"), "control C3: ResourceLoader.exists true for a path that never existed")

	var readme := FileAccess.get_file_as_string("res://legacy/README.md")
	for n in MOVED:
		for ext in [".tscn", ".gd"]:
			_assert(not ResourceLoader.exists(OLD_DIR + n + ext), "%s%s is still loadable at its old path" % [n, ext])
		_assert(not FileAccess.file_exists(OLD_DIR + n + ".gd.uid"), "%s.gd.uid sidecar still at the old path" % n)
		_assert(load(NEW_DIR + n + ".tscn") is PackedScene, "%s%s.tscn is not loadable at the new path" % [NEW_DIR, n])
		_assert(ResourceLoader.exists(NEW_DIR + n + ".gd"), "%s%s.gd is not loadable at the new path" % [NEW_DIR, n])
		_assert(FileAccess.file_exists(NEW_DIR + n + ".gd.uid"), "%s%s.gd.uid sidecar missing at the new path" % [NEW_DIR, n])
		_assert(readme.find(n) != -1, "legacy/README.md does not list %s" % n)

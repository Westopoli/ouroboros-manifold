extends SceneTree

# Plan item C4, unit E3 (docs/northstar/plans/2026-09-30-mission-plays-plan.md C4;
# docs/northstar/plans/2026-09-28-gap-fix-and-migration-plan.md E3): the legacy tactical
# scene (res://scenes/tactical/**) is deleted, and nothing still points at it. The live
# tactical view is res://scenes/tactical_c/tactical_view.tscn; scenes/tactical_c/ and
# scripts/tactical/ are different directories and must not trip the scan.
#
# Rules proved, by test id:
#   E3-1  res://scenes/tactical/ does not exist.
#   E3-2  no .gd/.tscn/.tres file (outside .swarm/, graphify-out/, dot dirs, docs/,
#         simulation/) holds a non-comment line naming "scenes/tactical/", so nothing loads
#         or preloads a deleted file, and the tests that exercised it are gone or retargeted
#         (the Engineer classifies each removal in the E3 ledger note).
#   E3-3  SceneRouter.SCENES has no "tactical" entry (the legacy route).
# Positive controls: C1 (the matcher sees "scenes/tactical/" and not "scenes/tactical_c/" or
# "scripts/tactical/"), C2 (the walk reaches tests/test_legacy_tactical_deleted.gd and
# scenes/tactical_c/tactical_view.tscn, and that live scene still loads, so "deleted" cannot
# be reached by deleting the wrong directory or breaking the walk).
#
# Excluded from E3-2: this file, and tests/test_tacticalbridge_ratchet.gd (its
# known-referencer list is data the Engineer lowers when files vanish, tracked by that test).
#
# A47: E3 also drops the perf-logger preload from the legacy bridge autoload (covered by
# E3-2, which sees the preload line), deletes the Visibility autoload (read only by
# scenes/tactical/**, verified; see c4_e3_tests_note.md) and the debug scene
# scenes/debug/test_squad_impact_origins (.gd, .tscn and its input stub):
#   E3-4  no Visibility autoload line in project.godot and scripts/tactical/visibility.gd is gone.
#   E3-5  scenes/debug/test_squad_impact_origins* .gd/.tscn is gone (stale .uid sidecars are ignored).

const THIS_TEST := "tests/test_legacy_tactical_deleted.gd"
const RATCHET := "tests/test_tacticalbridge_ratchet.gd"
const LIVE_SCENE := "scenes/tactical_c/tactical_view.tscn"
const NEEDLE := "scenes/tactical/"
const SKIP_TOP := [".swarm", "graphify-out", "docs", "simulation", "legacy"]
const EXTENSIONS := ["gd", "tscn", "tres"]

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	_run_tests()
	print("\n=== Legacy Tactical Deleted Test Results ===")
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


func _names_legacy(text: String) -> bool:
	for raw in text.split("\n"):
		var line := raw.strip_edges()
		if line.begins_with("#"):
			continue
		if line.find(NEEDLE) != -1:
			return true
	return false


func _walk(dir_path: String, out: Array[String]) -> void:
	var d := DirAccess.open("res://" + dir_path)
	if d == null:
		return
	for sub in d.get_directories():
		if sub.begins_with(".") or (dir_path == "" and sub in SKIP_TOP):
			continue
		_walk(sub if dir_path == "" else dir_path + "/" + sub, out)
	for f in d.get_files():
		if f.get_extension() in EXTENSIONS:
			out.append(f if dir_path == "" else dir_path + "/" + f)


func _run_tests() -> void:
	_assert(_names_legacy("var s = preload(\"res://scenes/tactical/hud.gd\")"), "control C1: matcher misses a scenes/tactical/ path")
	_assert(not _names_legacy("load(\"res://scenes/tactical_c/tactical_view.tscn\")"), "control C1: matcher false-positive on scenes/tactical_c/")
	_assert(not _names_legacy("preload(\"res://scripts/tactical/visibility.gd\")"), "control C1: matcher false-positive on scripts/tactical/")
	_assert(not _names_legacy("# See also: scenes/tactical/hud.gd"), "control C1: matcher counts a comment line")

	var files: Array[String] = []
	_walk("", files)
	_assert(files.has(THIS_TEST), "control C2: the walk never reached " + THIS_TEST)
	_assert(files.has(LIVE_SCENE), "control C2: the walk never reached " + LIVE_SCENE)
	_assert(load("res://" + LIVE_SCENE) is PackedScene, "control C2: the live tactical scene " + LIVE_SCENE + " no longer loads")

	_assert(not DirAccess.dir_exists_absolute(ProjectSettings.globalize_path("res://scenes/tactical")),
		"E3-1: res://scenes/tactical/ still exists")

	var holders: Array[String] = []
	for f in files:
		if f == THIS_TEST or f == RATCHET or f.begins_with("scenes/tactical/"):
			continue
		if _names_legacy(FileAccess.get_file_as_string("res://" + f)):
			holders.append(f)
	holders.sort()
	_assert(holders.is_empty(), "E3-2: %d file(s) outside scenes/tactical/ still name scenes/tactical/: %s" % [holders.size(), ", ".join(holders)])

	var router_src := FileAccess.get_file_as_string("res://autoload/scene_router.gd")
	var has_route := false
	for raw in router_src.split("\n"):
		if raw.strip_edges().begins_with("\"tactical\":"):
			has_route = true
	_assert(not has_route, "E3-3: SceneRouter.SCENES still has the legacy \"tactical\" route")

	var godot_cfg := FileAccess.get_file_as_string("res://project.godot")
	_assert(godot_cfg.find("Visibility=") == -1, "E3-4: project.godot still autoloads Visibility")
	_assert(not FileAccess.file_exists("res://scripts/tactical/visibility.gd"), "E3-4: scripts/tactical/visibility.gd still exists")

	var dbg := DirAccess.open("res://scenes/debug")
	_assert(dbg != null, "control C3: scenes/debug cannot be listed")
	if dbg != null:
		var left: Array[String] = []
		for f in dbg.get_files():
			if f.begins_with("test_squad_impact_origins") and f.get_extension() != "uid":
				left.append(f)
		_assert(left.is_empty(), "E3-5: scenes/debug still holds %s" % ", ".join(left))

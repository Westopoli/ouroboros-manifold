extends SceneTree

# Piece C3-G6 (the brief's G5b; docs/northstar/plans/2026-09-28-gap-fix-and-migration-plan.md
# G6): the TacticalBridge autoload leaves project.godot once nothing reads it (G4 debug
# overlay and E2 bug report rewired, E3 legacy tactical scene deleted).
#
# THIS IS A RATCHET, NOT THE FINAL STATE. It cannot go green-by-removal until E2 and E3
# land, so today it records the files that still name TacticalBridge (25, listed below; G4 swapped autoload/debug_overlay.gd for its own test) and
# asserts the set only shrinks:
#   - no file outside KNOWN_REFERENCERS may name TacticalBridge or tactical_bridge (a new
#     reader is a regression, reported by path);
#   - the final state is conditional: once no file names it, project.godot must carry no
#     TacticalBridge autoload line and autoload/tactical_bridge.gd must be gone.
# Whoever shrinks the set lowers KNOWN_REFERENCERS in the same change; the Engineer
# classifies that edit (ledger row), builders never edit it. The scan covers .gd, .tscn and
# .tres under res:// except .swarm/, graphify-out/ and dot-directories, and excludes
# autoload/tactical_bridge.gd and this file.
# Numbering note: the gap-fix plan calls this G6 and key rebinding G5b; the brief swapped them.

const SELF_PATH := "autoload/tactical_bridge.gd"
const THIS_TEST := "tests/test_tacticalbridge_ratchet.gd"
const SKIP_DIRS := [".swarm", "graphify-out"]
const EXTENSIONS := ["gd", "tscn", "tres"]

const KNOWN_REFERENCERS := [
	"autoload/bug_report_manager.gd",
	"autoload/mission_metrics_recorder.gd",
	"autoload/qa_daemon.gd",
	"autoload/ws_input_sanitizer.gd",
	"scenes/debug/debug_ws_test.gd",
	"scenes/debug/test_squad_impact_origins.gd",
	"scenes/tactical/hud.gd",
	"scenes/tactical/input_router.gd",
	"scenes/tactical/perf_logger.gd",
	"scenes/tactical/tactical.gd",
	"scenes/tactical/terrain_renderer.gd",
	"scenes/tactical/unit_renderer.gd",
	"scenes/tactical/visuals/ability_overlay_manager.gd",
	"scenes/tactical/visuals/ambient_density_manager.gd",
	"scenes/tactical/visuals/attack_visual_manager.gd",
	"scenes/tactical/visuals/combat_heatmap.gd",
	"scenes/tactical/visuals/destruction_manager.gd",
	"scenes/tactical/visuals/impact_feedback_manager.gd",
	"scripts/tactical/visibility.gd",
	"tests/test_boot_scripts_parse.gd",
	"tests/test_cover_render.gd",
	"tests/test_debug_overlay_gate.gd",
	"tests/test_input_router_control_groups.gd",
	"tests/test_input_router_selection.gd",
	"tests/test_qa_state_scenes.gd",
]

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	_run_tests()
	print("\n=== TacticalBridge Ratchet Test Results ===")
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


func _names_it(text: String) -> bool:
	return text.find("TacticalBridge") != -1 or text.find("tactical_bridge") != -1


func _walk(dir_path: String, out: Array[String]) -> void:
	var d := DirAccess.open("res://" + dir_path)
	if d == null:
		return
	for sub in d.get_directories():
		if sub.begins_with(".") or (dir_path == "" and sub in SKIP_DIRS):
			continue
		_walk(sub if dir_path == "" else dir_path + "/" + sub, out)
	for f in d.get_files():
		if f.get_extension() in EXTENSIONS:
			out.append(f if dir_path == "" else dir_path + "/" + f)


func _run_tests() -> void:
	# Positive controls: the matcher and the walker can see a reference at all.
	_assert(_names_it("TacticalBridge.units.size()"), "control: matcher misses 'TacticalBridge'")
	_assert(_names_it("preload(\"res://autoload/tactical_bridge.gd\")"), "control: matcher misses 'tactical_bridge'")
	_assert(not _names_it("SimBridge.units"), "control: matcher false-positive on SimBridge")
	var files: Array[String] = []
	_walk("", files)
	_assert(files.has("autoload/c_bridge.gd"), "control: the walk never reached autoload/c_bridge.gd")

	var referencers: Array[String] = []
	for f in files:
		if f == SELF_PATH or f == THIS_TEST:
			continue
		if _names_it(FileAccess.get_file_as_string("res://" + f)):
			referencers.append(f)
	referencers.sort()

	var added: Array[String] = []
	for f in referencers:
		if not KNOWN_REFERENCERS.has(f):
			added.append(f)
	_assert(added.is_empty(), "G6 ratchet: new file(s) name TacticalBridge (%d known, %d now): %s" % [KNOWN_REFERENCERS.size(), referencers.size(), ", ".join(added)])
	_assert(referencers.size() <= KNOWN_REFERENCERS.size(), "G6 ratchet: %d files name TacticalBridge, up from the recorded %d" % [referencers.size(), KNOWN_REFERENCERS.size()])

	if referencers.is_empty():
		var godot_cfg := FileAccess.get_file_as_string("res://project.godot")
		_assert(godot_cfg.find("TacticalBridge=") == -1, "G6: nothing names TacticalBridge but project.godot still autoloads it")
		_assert(not FileAccess.file_exists("res://" + SELF_PATH), "G6: nothing names TacticalBridge but " + SELF_PATH + " still exists")

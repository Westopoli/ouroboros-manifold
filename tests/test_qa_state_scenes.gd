extends SceneTree

# Piece C7-5: every player-facing scene exposes qa_state() for the QA daemon.
#
# REQUIRED: top-level screens and named overlays the player can reach.
# Source: autoload/scene_router.gd SCENES dict + named overlays.
#
# EXEMPT categories (path rule, counted in failure messages):
#   debug_scenes    scenes/debug/**, legacy/** -- debug harness and moved legacy scenes, never player-facing
#   mockup_scenes   scenes/mockups/**         -- prototype mockups
#   harness_scenes  scenes/harness/**         -- test harness
#   shared_scenes   scenes/shared/**          -- world-view building blocks
#   widget_scenes   named below individually  -- sub-scenes hosted inside another screen
#
# Widget sub-scenes exempt:
#   scenes/debrief/ribbon_graph.tscn          -- chart embedded in debrief
#   scenes/world/chronicle_entry.tscn         -- entry sub-row (C3-4 owned)
#   scenes/world/chronicle_entry_expansion.tscn -- expansion widget (C3-4 owned)
#   scenes/world/faction_info_panel.tscn      -- info panel embedded in world scenes
#   scenes/world/info_panel_host.tscn         -- info panel host, embedded in time_jump
#   scenes/world/region_info_panel.tscn       -- info panel embedded in world scenes
#
# LEFTOVER (owned by C3-4, C7-5 cannot touch):
#   scenes/world/chronicle_scroll_panel.tscn  -- routed as "chronicle"; owned by C3-4
#
# TOTAL .tscn: 47 (E3 removed scenes/tactical/** and the debug squad-impact scene)
#   REQUIRED:      18 (17 owned by C7-5, 1 leftover to C3-4)
#   debug_scenes:  9
#   mockup_scenes:  9
#   harness_scenes: 1
#   shared_scenes:  4
#   widget_scenes:  6
#   Total exempt: 29
#   18 + 29 = 47 ✓
#
# Mounting notes:
#   era_detail, onboarding: call setup({era_id: "settled_reach"}) after add_child
#   time_jump_sequencer: no setup() needed for qa_state (params set tick etc.)
#   bug_report_popup: setup(path, path) is optional; qa_state safe without it
#   privacy_modal: @onready binds from .tscn; skips if flag file exists (harmless)

const REQUIRED_SCENES: Array = [
	{
		"path": "res://scenes/loading_screen/loading_screen.tscn",
		"scene_name": "loading_screen",
		"setup": {},
	},
	{
		"path": "res://scenes/error_screen/error_screen.tscn",
		"scene_name": "error_screen",
		"setup": {},
	},
	{
		"path": "res://scenes/main_menu/main_menu.tscn",
		"scene_name": "main_menu",
		"setup": {},
	},
	{
		"path": "res://scenes/new_game/new_game.tscn",
		"scene_name": "new_game",
		"setup": {},
	},
	{
		"path": "res://scenes/load_game/load_game.tscn",
		"scene_name": "load_game",
		"setup": {},
	},
	{
		"path": "res://scenes/era_library/era_library.tscn",
		"scene_name": "era_library",
		"setup": {},
	},
	{
		"path": "res://scenes/era_library/era_detail.tscn",
		"scene_name": "era_detail",
		"setup": {"era_id": "settled_reach"},
	},
	{
		"path": "res://scenes/onboarding/onboarding.tscn",
		"scene_name": "onboarding",
		"setup": {"era_id": "settled_reach", "slot_name": "test"},
	},
	{
		"path": "res://scenes/mission_briefing/mission_briefing.tscn",
		"scene_name": "mission_briefing",
		"setup": {},
	},
	{
		"path": "res://scenes/debrief/debrief.tscn",
		"scene_name": "debrief",
		"setup": {},
	},
	{
		"path": "res://scenes/world/time_jump_sequencer.tscn",
		"scene_name": "time_jump",
		"setup": {},
	},
	{
		"path": "res://scenes/settings/settings.tscn",
		"scene_name": "settings",
		"setup": {},
	},
	{
		"path": "res://scenes/galaxy/galaxy_view.tscn",
		"scene_name": "galaxy_view",
		"setup": {},
	},
	{
		"path": "res://scenes/tactical_c/tactical_view.tscn",
		"scene_name": "tactical_view",
		"setup": {},
	},
	{
		"path": "res://scenes/privacy_modal/privacy_modal.tscn",
		"scene_name": "privacy_modal",
		"setup": {},
	},
	{
		"path": "res://scenes/tutorial/tutorial_overlay.tscn",
		"scene_name": "tutorial_overlay",
		"setup": {},
	},
	{
		"path": "res://scenes/bug_report/bug_report_popup.tscn",
		"scene_name": "bug_report_popup",
		"setup": {},
	},
]

# scenes/world/chronicle_scroll_panel.tscn is routed (as "chronicle") but owned
# by piece C3-4. C7-5 cannot touch it. Leftover: C3-4 must add scene/tick/plants
# keys matching this contract.
const CHRONICLE_PATH := "res://scenes/world/chronicle_scroll_panel.tscn"

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	await _run_tests()
	print("\n=== QA State Scenes Test Results ===")
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


func _run_tests() -> void:
	for entry in REQUIRED_SCENES:
		await _test_scene(entry)
	# C3-4b: close the leftover -- chronicle screen must match the same contract.
	await _test_scene({
		"path": CHRONICLE_PATH,
		"scene_name": "chronicle",
		"setup": {},
	})


func _test_scene(entry: Dictionary) -> void:
	var scene_path: String = entry["scene_name"]
	var res_path: String = entry["path"]
	var expected_name: String = entry["scene_name"]
	var setup_params: Dictionary = entry["setup"]

	if not ResourceLoader.exists(res_path):
		_assert(false, "%s: tscn not found: %s" % [scene_path, res_path])
		return

	var packed = load(res_path) as PackedScene
	if packed == null:
		_assert(false, "%s: failed to load PackedScene from %s" % [scene_path, res_path])
		return

	var scene: Node = packed.instantiate()
	if scene == null:
		_assert(false, "%s: PackedScene.instantiate() returned null" % scene_path)
		return

	get_root().add_child(scene)
	await process_frame
	await process_frame

	if not setup_params.is_empty() and scene.has_method("setup"):
		scene.call("setup", setup_params)
		await process_frame

	# T1: method exists
	var has_method: bool = scene.has_method("qa_state")
	_assert(has_method, "%s: missing qa_state() (C7-5 not yet implemented)" % scene_path)
	if not has_method:
		scene.queue_free()
		await process_frame
		return

	var result = scene.call("qa_state")
	_assert(result is Dictionary, "%s: qa_state() did not return Dictionary (got %s)" % [scene_path, typeof(result)])
	if not (result is Dictionary):
		scene.queue_free()
		await process_frame
		return

	var d: Dictionary = result

	# T2: required keys present
	_assert(d.has("scene"), "%s: qa_state() missing key 'scene'" % scene_path)
	_assert(d.has("tick"), "%s: qa_state() missing key 'tick'" % scene_path)
	_assert(d.has("plants"), "%s: qa_state() missing key 'plants'" % scene_path)

	# T3: correct types
	if d.has("scene"):
		_assert(d["scene"] is String, "%s: qa_state()['scene'] not a String (got %s)" % [scene_path, typeof(d["scene"])])
		_assert(d["scene"] == expected_name,
			"%s: qa_state()['scene'] == %s, expected %s" % [scene_path, d["scene"], expected_name])
	if d.has("tick"):
		_assert(d["tick"] is int or d["tick"] is float,
			"%s: qa_state()['tick'] not numeric (got type %s)" % [scene_path, typeof(d["tick"])])
		if d["tick"] is int or d["tick"] is float:
			var tv: float = float(d["tick"])
			_assert(tv == -1.0 or tv >= 0.0,
				"%s: qa_state()['tick'] must be -1 or >= 0 (got %s)" % [scene_path, d["tick"]])
	if d.has("plants"):
		_assert(d["plants"] is Array, "%s: qa_state()['plants'] not an Array (got %s)" % [scene_path, typeof(d["plants"])])
		if d["plants"] is Array:
			for p in d["plants"]:
				_assert(p is String, "%s: qa_state()['plants'] entry not a String: %s" % [scene_path, str(p)])

	# T4: JSON round-trip (all values JSON-safe; no Node, Vector2, NaN, Inf)
	var json_str: String = JSON.stringify(d)
	_assert(json_str != "", "%s: JSON.stringify(qa_state()) produced empty string" % scene_path)
	if json_str != "":
		var parsed = JSON.parse_string(json_str)
		_assert(parsed != null, "%s: JSON.parse_string failed on qa_state() output" % scene_path)
		if parsed != null:
			_assert(parsed is Dictionary,
				"%s: JSON round-trip did not yield a Dictionary (got %s)" % [scene_path, typeof(parsed)])

	scene.queue_free()
	await process_frame

extends SceneTree

# A82 (docs/northstar/plans/2026-10-01-architect-rulings-2.md, Addendum 29): the
# mission briefing marker is shown under its region's OWN name, the same name the sim
# chronicle uses (scenes/world/chronicle_names.gd, table identical to
# library/chronicle/fragments.json), not table[(region + node) % 528].
# Positive control: for each tested frame the old formula's name differs from the
# region's own name, so a briefing still on the old formula must fail here.

const NamesScript := preload("res://scenes/world/chronicle_names.gd")
const BRIEFING_SCENE_PATH := "res://scenes/mission_briefing/mission_briefing.tscn"
const FIXTURE_PATH := "res://tests/fixtures/mission_frame_seed11.json"
const LIBRARY_PATH := "res://library/chronicle/fragments.json"
# region 7 with the fixture's nodes 3/7/12; 520 + 12 wraps past 528 under the old formula.
const REGIONS := [7, 0, 100, 520]

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _assert(cond: bool, msg: String) -> void:
	if cond:
		_pass_count += 1
	else:
		_fail_count += 1
		_fail_msgs.append(msg)


func _finish(title: String) -> void:
	print("\n=== %s Test Results ===" % title)
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


func _initialize() -> void:
	await _run_tests()
	_finish("A82 Briefing Marker Name")


func _own_name(names, region: int) -> String:
	return names.fill_template("{region_name}", region, -1)


func _run_tests() -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE_PATH))
	var lib = JSON.parse_string(FileAccess.get_file_as_string(LIBRARY_PATH))
	_assert(fixture is Dictionary and lib is Dictionary, "setup: fixture or fragments.json unreadable")
	if not (fixture is Dictionary and lib is Dictionary):
		return
	var names = NamesScript.new()
	names.load_tables(lib.get("name_tables", {}))
	var table: Array = lib["name_tables"]["region_names"]
	var packed = load(BRIEFING_SCENE_PATH)
	for region in REGIONS:
		var frame: Dictionary = (fixture as Dictionary).duplicate(true)
		frame["region"] = region
		var own := _own_name(names, region)
		_assert(own != "" and own != "[region]", "setup: region %d has no own name" % region)
		var root: Node = (packed as PackedScene).instantiate()
		get_root().add_child(root)
		await process_frame
		root.load_frame(frame)
		await process_frame
		var objs: Array = root.qa_state().get("objectives", [])
		_assert(objs.size() > 0, "region %d: briefing shows no objectives" % region)
		for o in objs:
			var node := int((o as Dictionary).get("node", 0))
			var old_name := str(table[(region + node) % table.size()])
			# positive control: the old formula would give a different name for this node
			_assert(node > 0 and old_name != own,
				"control: region %d node %d: old formula name '%s' should differ from own '%s'" % [region, node, old_name, own])
			var shown := str((o as Dictionary).get("marker_name", ""))
			_assert(shown == own,
				"A82: region %d node %d marker shows '%s'; must be the region's own name '%s' (old formula gives '%s')" % [region, node, shown, own, old_name])
		root.queue_free()
		await process_frame

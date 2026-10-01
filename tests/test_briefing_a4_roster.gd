extends SceneTree

# A4 client half (docs/northstar/plans/2026-09-30-mission-plays-plan.md; E-10 S-079,
# R-079-01 Assets section, R-079-04 no raw numbers, R-074-04 player force filled):
# mission_briefing.gd renders the player's roster from a mission frame's
# force {"types","tiers"} (docs/architecture.md mission frame) and shows no mock_001 prose
# or "TICK 0" placeholder on the frame-driven path.
#
# Scope is the frame data docs/architecture.md already documents. `position_name`,
# `parity`, `objective` text and a top-level node/radius/force[] are not documented there
# (contract docs piece first), so a position-name assertion is deliberately absent; see the
# A4 test report.
#
# Part 1 drives load_frame() with tests/fixtures/mission_frame_seed11.json (needs the client
# change alone). Part 2 uses the live pipe frame (also needs the pipe piece: today
# handle_mission_start answers force {"types":[],"tiers":[]}). Part 3 is the positive
# control: the roster detector must find nothing on a frame with an empty force.

const BRIEFING_SCENE_PATH := "res://scenes/mission_briefing/mission_briefing.tscn"
const FIXTURE_PATH := "res://tests/fixtures/mission_frame_seed11.json"
# mock_001 prose that must never appear on a frame-driven briefing (mock_data_source.gd).
const MOCK_STRINGS := ["OP-2741", "Thessalonica", "Northern Confederation", "Marcus Aurelius", "Fortifier"]

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	await _run_tests()
	print("\n=== Briefing A4 Roster Test Results ===")
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


func _texts(node: Node, out: Array[String]) -> void:
	if node is Label:
		out.append((node as Label).text)
	elif node is RichTextLabel:
		out.append((node as RichTextLabel).get_parsed_text())
	for c in node.get_children():
		_texts(c, out)


# Roster rows are "<unit name> x<count>" labels (U+00D7); returns [name, count] pairs.
func _roster_rows(root: Node) -> Array:
	var texts: Array[String] = []
	_texts(root, texts)
	var rows: Array = []
	for t in texts:
		var parts := t.split("×")
		if parts.size() == 2 and parts[0].strip_edges() != "" and parts[1].strip_edges().is_valid_int():
			rows.append([parts[0].strip_edges(), int(parts[1].strip_edges())])
	return rows


func _mount(frame: Dictionary) -> Node:
	var root: Node = (load(BRIEFING_SCENE_PATH) as PackedScene).instantiate()
	get_root().add_child(root)
	await process_frame
	await process_frame
	root.load_frame(frame)
	await process_frame
	return root


func _check_roster_and_no_fallbacks(root: Node, label: String) -> void:
	var rows := _roster_rows(root)
	_assert(rows.size() > 0, "%s: briefing shows no roster row (a '<unit> ×<count>' label); YOUR FORCE card is empty" % label)
	var total := 0
	for r in rows:
		_assert(int(r[1]) > 0, "%s: roster row '%s' has count %d, expected > 0" % [label, r[0], r[1]])
		total += int(r[1])
	_assert(total > 0, "%s: roster total is %d" % [label, total])
	var texts: Array[String] = []
	_texts(root, texts)
	var joined := "\n".join(texts)
	for m in MOCK_STRINGS:
		_assert(not joined.contains(m), "%s: briefing text contains mock_001 prose '%s'" % [label, m])
	_assert(not joined.contains("TICK 0\n") and not joined.ends_with("TICK 0"), "%s: briefing shows the 'TICK 0' zero placeholder" % label)


func _run_tests() -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE_PATH))
	_assert(fixture is Dictionary and (fixture["force"]["types"] as Array).size() > 0, "fixture has no force to render (test setup)")

	# Part 1: client rendering of the documented force on the fixture frame.
	var root := await _mount((fixture as Dictionary).duplicate(true))
	_check_roster_and_no_fallbacks(root, "fixture frame")
	root.queue_free()
	await process_frame

	# Part 3 (positive control): the detector finds no roster when the force is empty.
	var empty_frame: Dictionary = (fixture as Dictionary).duplicate(true)
	empty_frame["force"] = {"types": [], "tiers": []}
	var empty_root := await _mount(empty_frame)
	_assert(_roster_rows(empty_root).size() == 0, "positive control: an empty force still produced %d roster rows" % _roster_rows(empty_root).size())
	empty_root.queue_free()
	await process_frame

	# Part 2: the live pipe frame.
	var CBridge = load("res://autoload/c_bridge.gd")
	var bridge = CBridge.new()
	var ok: bool = bridge.load_mission_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES)
	_assert(ok, "load_mission_live(1) failed: %s" % bridge.last_error())
	var live: Dictionary = bridge.mission_frame()
	var force: Dictionary = live.get("force", {})
	_assert((force.get("types", []) as Array).size() > 0,
		"live mission frame force.types is empty (pipe piece T1-N: handle_mission_start must ship the allocation)")
	var live_root := await _mount(live)
	_check_roster_and_no_fallbacks(live_root, "live frame")
	live_root.queue_free()
	await process_frame

extends SceneTree

# A4 client half (docs/northstar/plans/2026-10-01-architect-rulings.md A4; E-10 S-079,
# R-079-01, R-079-04 no raw numbers, R-074-04 player force filled): mission_briefing.gd
# renders the player's roster from a mission frame's force {"types","tiers"} (six counts in
# unit-type-id order), shows the three frame briefing texts (situation, objective, assets),
# never renders the numeric parity, derives the position name from objectives[0].node and
# region via scenes/world/chronicle_names.gd (frames carry no names), and shows no mock_001
# prose or "TICK 0" placeholder on the frame-driven path.
#
# Part 1 drives load_frame() with tests/fixtures/mission_frame_a4.json (needs the client
# change alone). Part 2 uses the live pipe frame (also needs the pipe piece). Part 3 is the
# positive control: the roster detector must find nothing on a frame with an empty force, and
# the text/parity detectors must fire on a planted bad render.

const BRIEFING_SCENE_PATH := "res://scenes/mission_briefing/mission_briefing.tscn"
const FIXTURE_PATH := "res://tests/fixtures/mission_frame_a4.json"
const UNMARKED := "Unmarked Position"
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


func _parity_strings(parity: float) -> Array[String]:
	var out: Array[String] = []
	for f in ["%.4f", "%.3f", "%.2f", "%.1f"]:
		out.append(f % parity)
	out.append(str(parity))
	out.append("%d%%" % int(round(parity * 100.0)))
	out.append("%d %%" % int(round(parity * 100.0)))
	return out


# R-079-04: the parity number is data, never text the player reads.
func _parity_leaks(joined: String, parity: float) -> Array[String]:
	var leaks: Array[String] = []
	for p in _parity_strings(parity):
		if joined.contains(p):
			leaks.append(p)
	return leaks


func _check_texts_and_parity(root: Node, frame: Dictionary, label: String) -> void:
	var texts: Array[String] = []
	_texts(root, texts)
	var joined := "\n".join(texts)  # compared case-insensitively: the objective header is shown uppercased
	var b: Dictionary = frame.get("briefing", {})
	for k in ["situation", "objective", "assets"]:
		var t: String = str(b.get(k, ""))
		_assert(t != "", "%s: frame briefing.%s is empty (test setup / pipe piece)" % [label, k])
		_assert(t != "" and joined.to_lower().contains(t.to_lower()), "%s: briefing does not show the frame's %s text '%s' (R-079-01)" % [label, k, t])
	var parity := float(frame.get("parity", 0.0))
	_assert(parity > 0.0, "%s: frame parity is %s, expected a number > 0" % [label, parity])
	var leaks := _parity_leaks(joined, parity)
	_assert(leaks.is_empty(), "%s: briefing renders the parity number %s (R-079-04)" % [label, str(leaks)])


# Position name from objectives[0].node + region via chronicle_names.gd, shown through
# qa_state().objectives[0].marker_name. Tables come from library/chronicle/fragments.json.
func _position_name(root: Node) -> String:
	var objs: Array = root.qa_state().get("objectives", [])
	return str((objs[0] as Dictionary).get("marker_name", "")) if objs.size() > 0 else ""


func _is_real_name(n: String) -> bool:
	var stripped := n.strip_edges()
	if stripped == "" or n.contains("mock_001") or n == UNMARKED or n == "[region]":
		return false
	var only_zero := true
	for c in stripped:
		if c != "0" and c != " " and c != "." and c != "_":
			only_zero = false
	return not only_zero


func _run_tests() -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE_PATH))
	_assert(fixture is Dictionary and (fixture["force"]["types"] as Array).size() > 0, "fixture has no force to render (test setup)")

	# Part 1: client rendering of the documented force on the fixture frame.
	var root := await _mount((fixture as Dictionary).duplicate(true))
	_check_roster_and_no_fallbacks(root, "fixture frame")
	var fixture_total := 0
	for c in (fixture["force"]["types"] as Array):
		fixture_total += int(c)
	var shown_total := 0
	for r in _roster_rows(root):
		shown_total += int(r[1])
	_assert(shown_total == fixture_total, "fixture frame: roster counts sum to %d, force.types sums to %d" % [shown_total, fixture_total])
	_check_texts_and_parity(root, fixture as Dictionary, "fixture frame")
	var name_a := _position_name(root)
	_assert(_is_real_name(name_a), "fixture frame: position name '%s' is empty, mock_001, a placeholder or zeros (derive from objectives[0].node and region via chronicle_names.gd)" % name_a)
	root.queue_free()
	await process_frame

	# Region matters: same node, a different region gives a different position name.
	var other: Dictionary = (fixture as Dictionary).duplicate(true)
	other["region"] = int(other["region"]) + 1
	var other_root := await _mount(other)
	var name_b := _position_name(other_root)
	_assert(_is_real_name(name_b), "region+1 frame: position name '%s' is not a real name" % name_b)
	_assert(name_a != name_b, "position name '%s' did not change with region 7 -> 8 (name must come from node and region)" % name_a)
	other_root.queue_free()
	await process_frame

	# Part 3 (positive control): the detector finds no roster when the force is empty.
	var empty_frame: Dictionary = (fixture as Dictionary).duplicate(true)
	empty_frame["force"] = {"types": [], "tiers": []}
	var empty_root := await _mount(empty_frame)
	_assert(_roster_rows(empty_root).size() == 0, "positive control: an empty force still produced %d roster rows" % _roster_rows(empty_root).size())
	_assert(not _is_real_name(UNMARKED) and not _is_real_name("mock_001") and not _is_real_name("0 0 0") and _is_real_name("Ridge Point"), "positive control: name detector is wrong")
	_assert(_parity_leaks("assets: parity 0.84 of theirs", 0.8425166666666667).size() > 0 and _parity_leaks("committed at parity", 0.8425166666666667).is_empty(), "positive control: parity-leak detector is wrong")
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
	_check_texts_and_parity(live_root, live, "live frame")
	var live_name := _position_name(live_root)
	_assert(_is_real_name(live_name), "live frame: position name '%s' is empty, mock_001, a placeholder or zeros" % live_name)
	live_root.queue_free()
	await process_frame

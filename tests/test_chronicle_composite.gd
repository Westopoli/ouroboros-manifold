extends SceneTree

# Piece C5-C1 (docs/northstar/plans/2026-09-28-gap-fix-and-migration-plan.md
# "G-C1 layout"; mission-plays plan item C5): the scene routed as "chronicle" is
# the composite, the galaxy view with the scroll panel beside it.
#   R-108-02 / R-069-01  when narration begins the scroll panel slides in from
#             the right over 0.40 s and the map view resizes to 62 percent of
#             the width (before that the map is full width).
#   E-16 S-108 "One unbroken shot": the galaxy under the narration is the
#             campaign's own galaxy, from the same pipe session the jump ran on.
#   Survives (gap-fix plan "Must survive"): the chronicle qa_state keys, the
#             ChronicleScrollPanel control (tests/qa/desktop/test_flow_spine.py
#             accepts an embedded panel by that name) and the root entry points
#             tests/test_chronicle_scroll.gd drives (the plants, click, dismiss).
# Open and NOT tested here (register questions in the C5 report): when the panel
# slides out (R-069-01 says at the end, R-108-06 says on Proceed) and the
# Proceed / Exit footer (R-108-05..07).
# The map extent is read from qa_state().systems_px of the embedded galaxy: with
# the camera on the galaxy centre the mean x of the projected systems sits at the
# map's horizontal centre (0.5 of the window at full width, 0.31 at 62 percent).
# Needs no display.

const SessionScript := preload("res://autoload/sim_session.gd")
const CHRONICLE_KEYS := ["scene", "error_panel", "tick", "plants", "hash", "timing_ms", "regen_count", "entries", "expanded_id", "owners", "pace", "dropped_entries", "unresolved_refs"]
const FULL_CENTRE := 0.5
const NARRATION_CENTRE := 0.31
const CENTRE_TOLERANCE := 0.04
const SLIDE_SEC := 0.40
const SLIDE_SLACK := 0.20
const WATCH_SEC := 2.0
const FRAME_BUDGET := 200  # the headless runner quits after 300 frames in all

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	await _run_tests()
	print("\n=== Chronicle Composite Test Results ===")
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


func _find(node: Node, pred: Callable) -> Node:
	for child in node.get_children():
		if pred.call(child):
			return child
		var deeper := _find(child, pred)
		if deeper != null:
			return deeper
	return null


func _is_galaxy(n: Node) -> bool:
	if not n.has_method("qa_state") or not n.has_method("qa_camera"):
		return false
	return String(n.call("qa_state").get("scene", "")) == "galaxy_view"


func _centre_fraction(galaxy: Node) -> float:
	var px: Dictionary = galaxy.qa_state()["systems_px"]
	var sum := 0.0
	for id in px:
		sum += float(px[id][0])
	return sum / float(px.size()) / float(get_root().size.x)


func _run_tests() -> void:
	var router := get_root().get_node_or_null("SceneRouter")
	_assert(router != null, "no SceneRouter autoload")
	if router == null:
		return
	var path: String = router.SCENES.get("chronicle", "")
	_assert(path != "", "SceneRouter has no chronicle route")
	var packed = load(path)
	_assert(packed is PackedScene, "cannot load the chronicle route " + path)
	if not (packed is PackedScene):
		return
	SessionScript.reset()
	var root: Node = (packed as PackedScene).instantiate()
	get_root().add_child(root)
	await process_frame

	var galaxy := _find(root, _is_galaxy) if not _is_galaxy(root) else root
	var panel := _find(root, func(n): return n.name == "ChronicleScrollPanel") if root.name != "ChronicleScrollPanel" else root
	_assert(galaxy != null, "R-108-02: the chronicle scene embeds no galaxy view (a node whose qa_state scene is galaxy_view)")
	_assert(panel != null and panel.has_method("load_frame"), "the chronicle scene has no ChronicleScrollPanel control")
	if galaxy == null or panel == null:
		return

	_check_qa_contract(root)
	var before := _centre_fraction(galaxy)
	_assert(absf(before - FULL_CENTRE) < CENTRE_TOLERANCE, "R-069-01: before narration the map is not full width (systems centre at %.3f of the window, expected %.2f)" % [before, FULL_CENTRE])
	await _check_slide_in_R108_02(galaxy, panel)
	_check_same_session_galaxy(galaxy)


func _check_qa_contract(root: Node) -> void:
	for m in ["qa_state", "qa_plant", "qa_click_entry", "qa_dismiss", "set_snapshot", "load_frame"]:
		_assert(root.has_method(m), "composite root lost chronicle entry point: " + m)
	if not root.has_method("qa_state"):
		return
	var state: Dictionary = root.qa_state()
	for k in CHRONICLE_KEYS:
		_assert(state.has(k), "composite root qa_state lost the chronicle key: " + k)
	_assert(state.get("scene", "") == "chronicle", "composite root qa_state scene is '%s', expected 'chronicle'" % state.get("scene", ""))
	_assert((state.get("plants", []) as Array).has("entries-dropped") and (state.get("plants", []) as Array).has("refs-unresolved"), "composite root qa_state lost the chronicle plants")


func _check_slide_in_R108_02(galaxy: Node, panel: Node) -> void:
	var t0 := Time.get_ticks_msec()
	var started := -1.0
	var settled := -1.0
	var last := 0.0
	var samples := 0
	var settled_frames := 0
	while float(Time.get_ticks_msec() - t0) / 1000.0 < WATCH_SEC and samples < FRAME_BUDGET and settled_frames < 10:
		await process_frame
		var f := _centre_fraction(galaxy)
		var t := float(Time.get_ticks_msec() - t0) / 1000.0
		samples += 1
		if started < 0.0 and f < FULL_CENTRE - 0.01:
			started = t
		if started >= 0.0 and settled < 0.0 and absf(f - NARRATION_CENTRE) < 0.006:
			settled = t
		last = f
		if settled >= 0.0:
			settled_frames += 1
	_assert(started >= 0.0, "R-108-02: the map never started resizing when narration began (centre stayed at %.3f)" % last)
	_assert(absf(last - NARRATION_CENTRE) < CENTRE_TOLERANCE, "R-108-02: with narration under way the map is not 62 percent wide (systems centre at %.3f of the window, expected %.2f)" % [last, NARRATION_CENTRE])
	if started >= 0.0 and settled >= 0.0:
		var took := settled - started
		_assert(absf(took - SLIDE_SEC) <= SLIDE_SLACK, "R-069-01: the map took %.2f s to resize, expected 0.40 s" % took)
	if panel is Control:
		var width := float(get_root().get_visible_rect().size.x)
		var rect: Rect2 = (panel as Control).get_global_rect()
		_assert(absf(rect.position.x / width - 0.62) < 0.03, "R-108-02: the scroll panel starts at %.3f of the width, expected 0.62" % (rect.position.x / width))
		_assert(absf(rect.end.x / width - 1.0) < 0.02, "R-108-02: the scroll panel ends at %.3f of the width, expected the right edge" % (rect.end.x / width))


func _check_same_session_galaxy(galaxy: Node) -> void:
	var snap: Dictionary = SessionScript.bridge().chronicle_snapshot()
	var want: int = (snap.get("regions", []) as Array).size()
	_assert(want > 0, "the chronicle session holds no snapshot")
	_assert(int(galaxy.qa_state()["system_count"]) == want, "S-108: the embedded galaxy shows %d systems, the session's post-jump snapshot has %d" % [galaxy.qa_state()["system_count"], want])

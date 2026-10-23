extends SceneTree
# Rule pins: R-104-01@1aaaa3, R-104-03@9dae08, R-104-04@6bbcd1

# Plan item A6, unit A6b (docs/northstar/plans/2026-09-30-mission-plays-plan.md,
# Wave A): the HUD of res://scenes/tactical_c/tactical_view.tscn on a live
# mission. Rules proved: E-16 S-104 R-104-01 (objective list with progress),
# R-104-03 (elapsed mission time top-right), R-104-04 (selected-group summary),
# E-10 R-076 "HUD clock" (the clock exists and runs), plan A6 "debug overlay
# stays off" (G4).
#
# The view self-loads the live mission in _ready() (the same mount
# tests/test_tactical_view.gd uses), so no frame is injected: the HUD must be
# fed by the real mission, which is the point of the item. Assertions are on
# label text patterns, never on layout pixels (the player-perception rule):
#   clock       any visible text node whose text holds mm:ss, and whose text
#               changes once the mission has run
#   objective   one text node holding a name (3+ letters) and a completion
#               percentage ("... 0%")
#   selection   after three own units are selected, a text node that was not
#               there before holds the count 3 as a standalone number
#   End Mission a visible Button whose text reads END MISSION
#   overlay     /root/DebugOverlay is not visible by default
#
# Positive controls: H1 (the text-node finder sees the End Mission button that
# exists on main today, so an empty finder cannot hide a regression), H2 (F3
# turns the debug overlay on, so "overlay off" is a real reading), H3 (the
# clock detector is only trusted while the mission tick really advanced).
#
# Open (reported, not guessed): whether the clock counts elapsed or remaining
# time (R-104-03 says elapsed, R-076 only "HUD clock"); the exact objective
# wording (names come from the client's layout pass, E-10 snapshot docs); where
# the selection summary sits. None is asserted.

const SCENE_PATH := "res://scenes/tactical_c/tactical_view.tscn"
const MIN_TICKS_FOR_CLOCK := 40
const WAIT_TICKS_TIMEOUT_S := 20.0

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	await _run_tests()
	print("\n=== Tactical HUD Test Results ===")
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
	var packed = load(SCENE_PATH)
	_assert(packed is PackedScene, "cannot load " + SCENE_PATH)
	if not (packed is PackedScene):
		return
	var v: Node = (packed as PackedScene).instantiate()
	get_root().add_child(v)
	await process_frame
	await process_frame

	var st: Dictionary = v.qa_state()
	_assert(int(st.get("unit_count", 0)) > 0, "A6b setup: the live mission frame has no units (live load failed?)")
	if int(st.get("unit_count", 0)) == 0:
		return

	_test_end_mission_and_finder_control_R104_03(v)
	await _test_debug_overlay_off_R104_01()
	_test_objective_name_and_completion_R104_01(v)
	await _test_clock_runs_R076_R104_03(v)
	await _test_selection_summary_R104_04(v)
	v.queue_free()
	await process_frame


# -- helpers ---------------------------------------------------------------

# Every visible text-bearing node under n: {text, node}.
func _texts(n: Node, out: Array = []) -> Array:
	if n is CanvasItem and not (n as CanvasItem).visible:
		return out
	if n is Label or n is RichTextLabel or n is Button:
		var t := String(n.get("text"))
		if t != "":
			out.append({"text": t, "node": n})
	for c in n.get_children():
		_texts(c, out)
	return out


func _all_text(v: Node) -> Array:
	var out: Array = []
	for e in _texts(v):
		out.append(String(e["text"]))
	return out


func _clock_re() -> RegEx:
	var re := RegEx.new()
	re.compile("\\b\\d{1,3}:\\d{2}\\b")
	return re


func _clock_texts(v: Node) -> Array:
	var re := _clock_re()
	var out: Array = []
	for t in _all_text(v):
		var m := re.search(t)
		if m != null:
			out.append(m.get_string())
	return out


# -- A6b-1: End Mission, and the finder's own control ----------------------

# H1: the finder must see the one HUD element that exists on main today.
func _test_end_mission_and_finder_control_R104_03(v: Node) -> void:
	var found := false
	for e in _texts(v):
		if e["node"] is Button and String(e["text"]).to_upper().contains("END MISSION"):
			found = true
	_assert(found, "A6b-1 control H1 / End Mission: no visible Button reading END MISSION found under the tactical view; texts seen: %s" % str(_all_text(v)))


# -- A6b-2: debug overlay off ----------------------------------------------

func _test_debug_overlay_off_R104_01() -> void:
	var ov := get_root().get_node_or_null("DebugOverlay")
	_assert(ov != null, "A6b-2 setup: DebugOverlay autoload missing")
	if ov == null:
		return
	_assert(not bool(ov.get("visible")), "A6b-2 G4: the debug overlay (FPS/Tick/Units/Sim) is visible on a fresh tactical view")
	# H2 control: with the debug flag on (plan A8, FeatureFlags.ENABLE_DEBUG_OVERLAY), F3 really toggles it on, so the reading above can be false.
	var flags := get_root().get_node_or_null("FeatureFlags")
	_assert(flags != null, "A6b-2 setup: FeatureFlags autoload missing")
	if flags == null:
		return
	flags.set("ENABLE_DEBUG_OVERLAY", true)
	var e := InputEventKey.new()
	e.keycode = KEY_F3
	e.physical_keycode = KEY_F3
	e.pressed = true
	Input.parse_input_event(e)
	await process_frame
	await process_frame
	_assert(bool(ov.get("visible")), "A6b-2 control H2: F3 did not show the debug overlay, so 'overlay off' proves nothing")
	if bool(ov.get("visible")):
		Input.parse_input_event(e)
		await process_frame
		await process_frame
		_assert(not bool(ov.get("visible")), "A6b-2 control H2: second F3 did not hide the overlay again")
	flags.set("ENABLE_DEBUG_OVERLAY", false)


# -- A6b-3: objective name and completion ----------------------------------

func _test_objective_name_and_completion_R104_01(v: Node) -> void:
	var re := RegEx.new()
	re.compile("[A-Za-z]{3,}[^\\n]*\\b\\d{1,3}\\s?%")
	var hits: Array = []
	for t in _all_text(v):
		if re.search(t) != null:
			hits.append(t)
	_assert(hits.size() >= 1,
		"A6b-3 R-104-01: no text shows an objective name with its completion percentage (pattern: letters ... N%%); texts seen: %s" % str(_all_text(v)))


# -- A6b-4: mission clock --------------------------------------------------

func _test_clock_runs_R076_R104_03(v: Node) -> void:
	var before := _clock_texts(v)
	_assert(before.size() >= 1,
		"A6b-4 R-104-03 / R-076 HUD clock: no mm:ss text on the HUD at mission start; texts seen: %s" % str(_all_text(v)))

	# H3: wait until the mission has genuinely run (real-time stepping at 20
	# ticks/s drives the view's _process), else a frozen clock proves nothing.
	var tick0 := int(v.qa_state().get("tick", 0))
	var waited := 0.0
	while int(v.qa_state().get("tick", 0)) - tick0 < MIN_TICKS_FOR_CLOCK and waited < WAIT_TICKS_TIMEOUT_S:
		await create_timer(0.25).timeout
		waited += 0.25
	var ran := int(v.qa_state().get("tick", 0)) - tick0
	_assert(ran >= MIN_TICKS_FOR_CLOCK,
		"A6b-4 control H3: the mission advanced only %d ticks in %.0f s of real time (need %d); the clock cannot be judged" % [ran, waited, MIN_TICKS_FOR_CLOCK])
	if ran < MIN_TICKS_FOR_CLOCK:
		return
	await process_frame
	await process_frame
	var after := _clock_texts(v)
	_assert(after.size() >= 1, "A6b-4 R-104-03: the mm:ss clock disappeared once the mission was running")
	_assert(after.size() >= 1 and before.size() >= 1 and after != before,
		"A6b-4 R-104-03: the clock still reads %s after %d mission ticks (was %s); a running mission needs a moving clock" % [str(after), ran, str(before)])


# -- A6b-5: selected-group summary -----------------------------------------

func _test_selection_summary_R104_04(v: Node) -> void:
	var st: Dictionary = v.qa_state()
	var lf := int(st.get("local_faction", 0))
	var ids: Array = []
	for id in st.get("units", {}):
		if int((st["units"][id] as Dictionary).get("faction", -1)) == lf:
			ids.append(int(id))
	ids.sort()
	_assert(ids.size() >= 3, "A6b-5 setup: fewer than three own units in the live mission")
	if ids.size() < 3:
		return
	v.qa_set_selected([])
	await process_frame
	await process_frame
	var before := _all_text(v)
	v.qa_set_selected(ids.slice(0, 3))
	await process_frame
	await process_frame
	var re := RegEx.new()
	re.compile("(^|[^\\d.:%])3([^\\d.:%]|$)")
	var added: Array = []
	for t in _all_text(v):
		if re.search(t) != null and not before.has(t):
			added.append(t)
	_assert(added.size() >= 1,
		"A6b-5 R-104-04: selecting 3 own units added no text holding the count 3 (texts before: %s; after: %s)" % [str(before), str(_all_text(v))])
	# Clearing the selection removes it again.
	v.qa_set_selected([])
	await process_frame
	await process_frame
	for t in added:
		_assert(not _all_text(v).has(t),
			"A6b-5 R-104-04: summary text '%s' stayed on the HUD after the selection was cleared" % t)

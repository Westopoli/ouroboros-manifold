extends SceneTree

# Piece C3-G4 (docs/northstar/plans/2026-09-28-gap-fix-and-migration-plan.md G4): the
# debug overlay (FPS / Tick / Units / Sim) is gated off by default: it appears only
# with an explicit debug flag, which is not set in normal or QA launches, and it
# reads the tactical frame of the live bridge, not the dead TacticalBridge autoload.
#
# Interface this test pins (the plan names the behaviour, not the flag): the flag is
# the boolean FeatureFlags.ENABLE_DEBUG_OVERLAY, default false, following the
# existing ENABLE_* convention in autoload/feature_flags.gd. With it false, F3 does
# nothing; with it true, F3 toggles the overlay as today. The Tick and Units lines
# keep today's "Tick: %s" / "Units: %d" format and come from
# SimSession.bridge().tactical_frame() ("tick", "units").
# Conflict to resolve outside this file: tests/test_tactical_hud.gd (A6b-2 control H2)
# expects a bare F3 to show the overlay; under G4 that control must set the flag first.

const SimSessionScript := "res://autoload/sim_session.gd"
const OVERLAY_SOURCE := "res://autoload/debug_overlay.gd"
const FLAG := "ENABLE_DEBUG_OVERLAY"

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false


class FrameBridge:
	extends "res://autoload/c_bridge.gd"

	func _init(tick: int, unit_count: int) -> void:
		var units: Array = []
		for i in unit_count:
			units.append({"id": i})
		_tactical = {"tick": tick, "units": units, "full": true}


func _initialize() -> void:
	await _run_tests()
	_assert(_completed, "the debug-overlay checks did not run to the end (a script error aborted them)")
	print("\n=== Debug Overlay Gate Test Results ===")
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


func _f3() -> InputEventKey:
	var e := InputEventKey.new()
	e.keycode = KEY_F3
	e.physical_keycode = KEY_F3
	e.pressed = true
	return e


func _label_text(ov: Node) -> String:
	var stack: Array = [ov]
	while not stack.is_empty():
		var n: Node = stack.pop_back()
		if n is Label:
			return (n as Label).text
		stack.append_array(n.get_children())
	return ""


func _run_tests() -> void:
	await process_frame
	await process_frame
	var ov := get_root().get_node_or_null("DebugOverlay")
	var flags := get_root().get_node_or_null("FeatureFlags")
	_assert(ov != null, "setup: DebugOverlay autoload missing")
	_assert(flags != null, "setup: FeatureFlags autoload missing")
	if ov == null or flags == null:
		return

	_assert(FLAG in flags, "G4: FeatureFlags has no %s flag" % FLAG)
	_assert(FLAG in flags and flags.get(FLAG) == false, "G4: %s is not false by default (normal and QA launches must not show the overlay)" % FLAG)
	_assert(not bool(ov.get("visible")), "G4: the overlay is visible at boot")

	# Gate: with the flag off, F3 does nothing.
	flags.set(FLAG, false)
	ov.set("visible", false)
	ov._unhandled_input(_f3())
	_assert(not bool(ov.get("visible")), "G4: F3 showed the overlay with %s false" % FLAG)

	# Positive control: with the flag on, F3 toggles it on and off, so the reading above can be false.
	flags.set(FLAG, true)
	ov.set("visible", false)
	ov._unhandled_input(_f3())
	_assert(bool(ov.get("visible")), "G4 control: F3 did not show the overlay with %s true" % FLAG)
	ov._unhandled_input(_f3())
	_assert(not bool(ov.get("visible")), "G4 control: a second F3 did not hide the overlay")

	# Source: no TacticalBridge (the autoload is going away).
	var src := FileAccess.get_file_as_string(OVERLAY_SOURCE)
	_assert(src != "", "cannot read " + OVERLAY_SOURCE)
	_assert(src.find("TacticalBridge") == -1, "G4: debug_overlay.gd still names TacticalBridge")

	# Reads the tactical frame of the live bridge.
	var SimSession = load(SimSessionScript)
	SimSession.reset()
	SimSession._bridge = FrameBridge.new(1234, 3)
	ov.set("visible", true)
	ov._process(0.0)
	var text := _label_text(ov)
	_assert(text.find("Tick: 1234") != -1, "G4: overlay text '%s' does not show the tactical frame's tick (Tick: 1234)" % text.replace("\n", " | "))
	_assert(text.find("Units: 3") != -1, "G4: overlay text '%s' does not show the tactical frame's unit count (Units: 3)" % text.replace("\n", " | "))

	flags.set(FLAG, false)
	ov.set("visible", false)
	SimSession.reset()
	_completed = true

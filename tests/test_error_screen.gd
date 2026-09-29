extends SceneTree

# Piece G-errorscreen-1 (docs/northstar/plans/2026-09-28-gap-fix-and-migration-plan.md,
# row G1): res://scenes/error_screen/error_screen.gd's Retry action must go
# through SimSession (res://autoload/sim_session.gd) instead of the dead
# SimBridge autoload, and must route to "main_menu" (not "loading_screen",
# whose own contract is changing under a different piece in this same wave).
#
# This file is red on the unmodified scene today: _on_restart() calls
# SimBridge.restart() then SceneRouter.go_to("loading_screen"). It is
# TESTS ONLY -- error_screen.gd is not touched by this piece.
#
# Style mirrors tests/test_briefing_deploy.gd (SimSession.bridge()/reset()
# usage) and tests/test_load_game.gd (mount/assert/queue_free pattern).
# The "no forbidden reference in source" check mirrors tests/test_qa_daemon.gd
# (FileAccess.open(...).get_as_text() scan) rather than inspecting a live
# script instance, since Script has no public source-text accessor outside
# the editor.

const SCENE_PATH := "res://scenes/error_screen/error_screen.tscn"
const SCRIPT_PATH := "res://scenes/error_screen/error_screen.gd"

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	await _run_tests()
	print("\n=== Error Screen Test Results ===")
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
	_test_no_simbridge_reference_in_source()
	await _test_qa_state_pin()
	await _test_retry_resets_sim_session_and_routes_to_main_menu()
	# R-G1: QUIT is untouched by this piece; see _test_quit_button_unchanged
	# for why it is checked by wiring inspection instead of actually quitting.
	await _test_quit_button_unchanged()


# Assertion 1: SimBridge must not be referenced anywhere in the file after
# the fix. Scanned red (must currently FAIL) against the unmodified source.
func _test_no_simbridge_reference_in_source() -> void:
	var f := FileAccess.open(SCRIPT_PATH, FileAccess.READ)
	_assert(f != null, "could not open %s to scan its source" % SCRIPT_PATH)
	if f == null:
		return
	var src := f.get_as_text()
	f.close()
	_assert(src.find("SimBridge") == -1,
		"G1: error_screen.gd source still references SimBridge (must call SimSession.reset() instead)")


# Assertion 5 (pin, non-red): qa_state() shape is untouched by this piece.
func _test_qa_state_pin() -> void:
	var packed = load(SCENE_PATH)
	_assert(packed != null, "cannot load %s" % SCENE_PATH)
	if packed == null:
		return
	var scene: Node = (packed as PackedScene).instantiate()
	get_root().add_child(scene)
	await process_frame
	await process_frame

	_assert(scene.has_method("qa_state"), "error_screen missing qa_state()")
	if scene.has_method("qa_state"):
		var state: Dictionary = scene.qa_state()
		_assert(state.get("scene", "") == "error_screen", "qa_state().scene = %s, expected 'error_screen'" % state.get("scene"))
		_assert(int(state.get("tick", -999)) == -1, "qa_state().tick = %s, expected -1" % state.get("tick"))
		_assert(int(state.get("button_count", -1)) == 2, "qa_state().button_count = %s, expected 2" % state.get("button_count"))
		_assert((state.get("plants", ["x"]) as Array).is_empty(), "qa_state().plants = %s, expected []" % [state.get("plants")])

	scene.queue_free()
	await process_frame


# Assertions 2 and 3: the retry action must call SimSession.reset() (observed
# via the SimSession.bridge() instance changing identity -- reset() closes
# the session and forgets the bridge, so the next bridge() call constructs a
# fresh instance) and must route to "main_menu", not "loading_screen".
#
# SimSession.bridge()/reset() are exercised for real (same pattern as
# tests/test_briefing_deploy.gd) -- there is no test seam to add (not
# permitted; tests only) and no fake to inject, since error_screen.gd talks
# to the SimSession/SceneRouter autoloads directly, not through an injected
# dependency.
#
# SceneRouter.go_to() sets _current_scene_name synchronously before its fade
# tween runs (autoload/scene_router.gd), so it is safe to read immediately
# after calling the handler without waiting out the tween.
func _test_retry_resets_sim_session_and_routes_to_main_menu() -> void:
	var SimSession = load("res://autoload/sim_session.gd")
	SimSession.reset()
	var bridge_before = SimSession.bridge()
	_assert(bridge_before != null, "control: SimSession.bridge() must not be null after forcing creation")

	var packed = load(SCENE_PATH)
	_assert(packed != null, "cannot load %s" % SCENE_PATH)
	if packed == null:
		SimSession.reset()
		return
	var scene: Node = (packed as PackedScene).instantiate()
	get_root().add_child(scene)
	await process_frame
	await process_frame

	# The handler may be renamed _on_retry(); today it is _on_restart(). Call
	# whichever exists so this test survives the rename half of the fix.
	var method_name := ""
	if scene.has_method("_on_retry"):
		method_name = "_on_retry"
	elif scene.has_method("_on_restart"):
		method_name = "_on_restart"
	_assert(method_name != "", "error_screen has neither _on_retry() nor _on_restart() -- cannot drive the retry action")

	if method_name != "":
		scene.call(method_name)

	# Assertion 3: routes to main_menu, not loading_screen.
	var SceneRouterScript = load("res://autoload/scene_router.gd")
	var router = Engine.get_main_loop().root.get_node_or_null("/root/SceneRouter") if Engine.get_main_loop() else null
	# SceneRouter is a project autoload; reach it the same way scripts do,
	# through the tree root, since this test script has no "SceneRouter"
	# global identifier of its own (that name only resolves inside scene
	# scripts compiled with the autoload singleton present).
	if router == null:
		router = get_root().get_node_or_null("SceneRouter")
	_assert(router != null, "could not find the SceneRouter autoload node in the tree to inspect routing")
	if router != null:
		_assert(router.get("_current_scene_name") == "main_menu",
			"G1: retry routed to '%s', expected 'main_menu' (loading_screen's contract is changing under a different piece)" % router.get("_current_scene_name"))

	# Assertion 2: SimSession.reset() was called -- bridge() now returns a
	# fresh instance, not the one forced into existence before the retry.
	var bridge_after = SimSession.bridge()
	_assert(bridge_after != bridge_before,
		"G1: SimSession.bridge() instance unchanged after retry -- SimSession.reset() was not called (still on the dead SimBridge path)")

	scene.queue_free()
	await process_frame

	# Cleanup: SimBridge.restart() (today's dead-path call) spawns a real
	# sim subprocess and reader thread as a side effect of driving the
	# handler above. Reap it so this test does not leak a process. Once the
	# fix lands and SimBridge is no longer called, this is a no-op (SimBridge
	# still exists as an autoload elsewhere until G1's sibling pieces retire
	# it; harmless either way).
	var sim_bridge = get_root().get_node_or_null("SimBridge")
	if sim_bridge != null and sim_bridge.has_method("_kill_sim"):
		sim_bridge._kill_sim()
	SimSession.reset()


# Assertion 4: QUIT must remain get_tree().quit() -- untouched by this piece.
# Actually invoking it headless would exit this very test runner before it
# can print its PASS/FAIL summary (scripts/run_godot_tests.sh treats a
# missing summary line as an aborted run), so this is checked the same way
# assertion 1 checks for SimBridge: a source-text scan, not a live call.
func _test_quit_button_unchanged() -> void:
	var f := FileAccess.open(SCRIPT_PATH, FileAccess.READ)
	if f == null:
		_assert(false, "could not open %s to scan for the QUIT handler" % SCRIPT_PATH)
		return
	var src := f.get_as_text()
	f.close()
	_assert(src.find("get_tree().quit()") != -1,
		"error_screen.gd no longer calls get_tree().quit() from its QUIT handler (out of scope for G1 -- should be unchanged)")

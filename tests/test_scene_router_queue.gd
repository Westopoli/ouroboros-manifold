extends SceneTree
# test-timeout: 6000

# T12 / E-16 (the client never loses an input the player saw land), S-C8 flow spine.
# Root cause: SceneRouter.go_to silently returned while _transitioning was true, and that
# flag stays true through the fade-out although the new scene is already live and
# clickable. A Deploy click in that window ran begin_mission() but the go_to("tactical_c")
# was dropped. Ruling: go_to never drops a request; a request made during a transition is
# queued (latest wins) and performed when the current tween finishes.
# Stub scenes: SCENES is a const, so a subclass overrides _swap_scene to put a stub scene
# in the tree and log the swap; real scene names are used only as keys.

const FADE := 0.3

# The router and stubs are built from source at run time: a SceneTree main script is
# compiled before the autoloads exist, so a compile-time subclass of the router (which
# names ThemeConstants) fails to compile.
const STUB_SRC := """extends Node
var tag := ""
var router: Node
var button: Button
var pressed_target := ""
func _ready() -> void:
	button = Button.new()
	button.pressed.connect(_on_pressed)
	add_child(button)
func _on_pressed() -> void:
	router.go_to(pressed_target)
"""
const ROUTER_SRC := """extends "res://autoload/scene_router.gd"
var swaps: Array = []
var stub_script: GDScript
func _swap_scene(scene_name: String, _params: Dictionary) -> void:
	swaps.append(scene_name)
	var tree := get_tree()
	if tree.current_scene:
		tree.current_scene.queue_free()
	var stub: Node = stub_script.new()
	stub.tag = scene_name
	stub.router = self
	tree.root.add_child(stub)
	tree.current_scene = stub
"""

var _router_script: GDScript
var _stub_script: GDScript

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	await _run_tests()
	print("\n=== SceneRouter Queue Test Results ===")
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


func _wait(seconds: float) -> void:
	var end := Time.get_ticks_msec() + int(seconds * 1000.0)
	while Time.get_ticks_msec() < end:
		await process_frame


func _make_router() -> Node:
	if _router_script == null:
		_stub_script = GDScript.new()
		_stub_script.source_code = STUB_SRC
		_stub_script.reload()
		_router_script = GDScript.new()
		_router_script.source_code = ROUTER_SRC
		_router_script.reload()
	var r: Node = _router_script.new()
	r.stub_script = _stub_script
	r.name = "TestRouter"
	root.add_child(r)
	return r


func _final_tag() -> String:
	var cs := current_scene
	return "" if cs == null or not "tag" in cs else str(cs.tag)


func _run_tests() -> void:
	await process_frame
	await _test_control_no_transition()
	await _test_request_mid_fade_out()
	await _test_two_requests_latest_wins()
	await _test_button_pressed_one_frame_after_swap()


# (3) positive control: no transition in flight behaves as today.
func _test_control_no_transition() -> void:
	var r := _make_router()
	r.go_to("settings")
	await _wait(FADE * 2 + 0.4)
	_assert(_final_tag() == "settings", "control: go_to with nothing in flight ends on settings, got '%s'" % _final_tag())
	r.go_to("galaxy")
	await _wait(FADE * 2 + 0.4)
	_assert(_final_tag() == "galaxy", "control: a second go_to after the first finished ends on galaxy, got '%s'" % _final_tag())
	_assert(r.swaps == ["settings", "galaxy"], "control: swaps are settings then galaxy, got %s" % str(r.swaps))
	r.queue_free()
	await process_frame


# (1) go_to("galaxy") issued while the transition to "settings" is in its fade-out.
func _test_request_mid_fade_out() -> void:
	var r := _make_router()
	r.go_to("settings")
	await _wait(FADE + 0.1)
	_assert(_final_tag() == "settings", "mid-fade: settings is live after the swap, got '%s'" % _final_tag())
	r.go_to("galaxy")
	await _wait(FADE * 3 + 0.5)
	_assert(_final_tag() == "galaxy", "mid-fade: a go_to made during the fade-out is performed after the tween, ended on '%s' (swaps %s)" % [_final_tag(), str(r.swaps)])
	r.queue_free()
	await process_frame


# (2) two requests during one transition: the latest wins, the earlier is discarded.
func _test_two_requests_latest_wins() -> void:
	var r := _make_router()
	r.go_to("settings")
	await _wait(FADE + 0.1)
	r.go_to("era_library")
	r.go_to("galaxy")
	await _wait(FADE * 3 + 0.5)
	_assert(_final_tag() == "galaxy", "latest-wins: ended on '%s', expected galaxy" % _final_tag())
	_assert(not r.swaps.has("era_library"), "latest-wins: the earlier queued request era_library is discarded, swaps %s" % str(r.swaps))
	r.queue_free()
	await process_frame


# (4) flow-spine shape: a scene's button handler calls go_to on press, pressed one frame
# after the swap (the Deploy click inside the fade-out window).
func _test_button_pressed_one_frame_after_swap() -> void:
	var r := _make_router()
	r.go_to("settings")
	var guard := Time.get_ticks_msec() + 3000
	while r.swaps.is_empty() and Time.get_ticks_msec() < guard:
		await process_frame
	await process_frame
	var stub = current_scene
	_assert(stub != null and "button" in stub, "spine: stub briefing scene is live after the swap")
	if stub != null and "button" in stub:
		stub.pressed_target = "galaxy"
		stub.button.emit_signal("pressed")
	await _wait(FADE * 3 + 0.5)
	_assert(_final_tag() == "galaxy", "spine: press one frame after swap still ends on galaxy, ended on '%s' (swaps %s)" % [_final_tag(), str(r.swaps)])
	r.queue_free()
	await process_frame

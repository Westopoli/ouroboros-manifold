extends SceneTree

# Piece C8-10 (docs/northstar/plans/2026-09-28-gap-fix-and-migration-plan.md
# G1): scenes/loading_screen/loading_screen.gd's _ready() branches on the
# dead SimBridge autoload (SimBridge.USE_LIVE_SIM is always false today, so
# the live path is already "route to _target_scene immediately" -- the
# SimBridge-gated branches below never execute in practice). This test pins
# the source-level removal target (no SimBridge reference inside _ready()
# specifically) and the observable routing behavior of setup()'s default
# and non-default targets, both of which must survive the SimBridge
# removal unchanged.

const SCENE_PATH := "res://scenes/loading_screen/loading_screen.gd"
const TSCN_PATH := "res://scenes/loading_screen/loading_screen.tscn"

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _scene_router: Node


func _initialize() -> void:
	# Autoload singletons are not resolvable as bare identifiers at compile
	# time when a script is run directly via `--script` in this harness
	# (verified 2026-09-28: `ThemeConstants`/`TacticalBridge`/`SceneRouter`
	# bare-identifier access all fail "Identifier not found" the same way in
	# this environment, including in tests/test_input_router_selection.gd,
	# an existing file unrelated to this piece). Route through
	# get_node_or_null("/root/SceneRouter") after a process_frame instead,
	# which resolves fine once the autoload has entered the tree.
	await process_frame
	_scene_router = get_root().get_node_or_null("/root/SceneRouter")
	await _run_tests()
	print("\n=== Loading Screen Test Results ===")
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
	_check_ready_body_has_no_simbridge()
	await _check_default_target_routes_to_main_menu()
	await _check_explicit_target_routes_to_that_target()


# (1) _ready()'s body (isolated between "func _ready" and the next "func ")
# must not mention SimBridge. Red today: SimBridge.USE_LIVE_SIM,
# SimBridge._ready_received, SimBridge.progress_updated, SimBridge.sim_ready
# all appear inside _ready() as written now.
func _check_ready_body_has_no_simbridge() -> void:
	var f := FileAccess.open(SCENE_PATH, FileAccess.READ)
	_assert(f != null, "could not open " + SCENE_PATH)
	if f == null:
		return
	var src := f.get_as_text()
	f.close()

	var start := src.find("func _ready")
	_assert(start >= 0, "no func _ready found in " + SCENE_PATH)
	if start < 0:
		return

	var next_func := src.find("\nfunc ", start + 1)
	var body: String
	if next_func >= 0:
		body = src.substr(start, next_func - start)
	else:
		body = src.substr(start)

	_assert(body.find("SimBridge") < 0,
		"_ready() body still references SimBridge (found at offset %d within the sliced body): %s" % [
			body.find("SimBridge"), body])


# (2) setup() is never called (SceneRouter.go_to("loading_screen") with no
# params dict still calls setup({}) per scene_router.gd's
# `if new_scene.has_method("setup"): new_scene.setup(params)`, and
# setup({}) leaves _target_scene at its "main_menu" default via
# params.get("target", "main_menu")). Mount the scene the same way, call
# setup({}) to mirror that real call site, and confirm it routes to
# "main_menu" without any SimBridge signal ever firing.
func _check_default_target_routes_to_main_menu() -> void:
	var packed = load(TSCN_PATH)
	_assert(packed != null, "cannot load " + TSCN_PATH)
	if packed == null:
		return

	var node = packed.instantiate()
	_assert(node != null, TSCN_PATH + " failed to instantiate")
	if node == null:
		return

	node.setup({})
	get_root().add_child(node)
	await process_frame
	await process_frame

	_assert(_scene_router._current_scene_name == "main_menu",
		"expected _scene_router._current_scene_name == 'main_menu' after default-target mount, got: %s" % _scene_router._current_scene_name)

	node.queue_free()
	await process_frame
	_reset_router_transitioning()


# (3) setup({"target": "settings"}) (a real, non-default SCENES key in
# scene_router.gd) must route to that exact target, not the "main_menu"
# default.
func _check_explicit_target_routes_to_that_target() -> void:
	var packed = load(TSCN_PATH)
	_assert(packed != null, "cannot load " + TSCN_PATH)
	if packed == null:
		return

	var node = packed.instantiate()
	_assert(node != null, TSCN_PATH + " failed to instantiate")
	if node == null:
		return

	node.setup({"target": "settings"})
	get_root().add_child(node)
	await process_frame
	await process_frame

	_assert(_scene_router._current_scene_name == "settings",
		"expected _scene_router._current_scene_name == 'settings' after explicit-target mount, got: %s" % _scene_router._current_scene_name)

	node.queue_free()
	await process_frame
	_reset_router_transitioning()


# SceneRouter.go_to() no-ops while a previous transition's fade-in/swap/
# fade-out tween (2x ThemeConstants.FADE_DURATION, a real-time tween
# unrelated to this piece) is still in flight, so a second go_to() call
# issued before that finishes would silently do nothing and
# _current_scene_name would not update. This test only needs the
# synchronous side effect go_to() has on _current_scene_name (which lands
# before the tween is even created), not the full visual transition, so
# rather than await the real-time tween (which, combined with this
# scene's own UI tweens, was observed to stall the harness rather than
# ever resolve -- an existing scene_router.gd/tween interaction, not
# something this piece touches) reset the flag directly between
# scenarios.
func _reset_router_transitioning() -> void:
	if _scene_router:
		_scene_router._transitioning = false

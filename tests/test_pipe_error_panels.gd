extends SceneTree

# Piece C3-G2 (docs/northstar/plans/2026-09-28-gap-fix-and-migration-plan.md G2,
# docs/northstar/plans/2026-09-30-mission-plays-plan.md item C3): a pipe failure is
# visible. When the live load fails, each of galaxy, briefing, debrief, chronicle and
# tactical_c shows an error panel with the reason, Retry and Main Menu instead of a
# bare push_error and an empty scene; the briefing never falls back to mock_001.
#
# Interface this test pins (the plan names the behaviour, not the node names; the
# names follow the DeployError convention of tests/test_briefing_deploy.gd):
#   - a visible Control named ErrorPanel somewhere under the scene root
#   - under it: a Label named ErrorReason whose text contains bridge.last_error()
#     verbatim, a Button named Retry and a Button named MainMenu, both enabled
#   - Retry runs the live load again (the failing bridge's attempt counter rises) and the
#     panel stays up while the pipe is still failing
#   - MainMenu routes to "main_menu" (SceneRouter)
#   - qa_state()["error_panel"] is true while the panel is showing, false otherwise
#   - ruling G2/A7: the panel is ONE shared scene, scenes/shared/error_panel.tscn, instanced
#     by each of the five scenes: the ErrorPanel node is that scene's root or lies inside an
#     instance of it (checked by scene_file_path up the parent chain)
# The failure is injected with FailBridge, a c_bridge.gd subclass whose live loads
# refuse, installed as SimSession's bridge (no seam in the scenes is needed). The debrief
# no longer loads anything (A39/A44): its failure case is NoFrameBridge, a bridge that holds
# no debrief frame (and reports REASON as its last_error, as after a failed mission_end);
# Retry re-reads the held frame (attempts counts debrief_frame() reads), and its healthy
# control is a bridge holding the frame of a mission ended through it. One
# scene (briefing) is also failed for real, by killing the pipe process. Every scene
# has a positive control on a healthy real pipe: no panel.

const CBridge := preload("res://autoload/c_bridge.gd")
const SHARED_PANEL := "res://scenes/shared/error_panel.tscn"
const REASON := "pipe exploded (test reason 7731)"
const SCENES := {
	"galaxy": "res://scenes/galaxy/galaxy_view.tscn",
	"mission_briefing": "res://scenes/mission_briefing/mission_briefing.tscn",
	"debrief": "res://scenes/debrief/debrief.tscn",
	"chronicle": "res://scenes/world/chronicle_scroll_panel.tscn",
	"tactical_c": "res://scenes/tactical_c/tactical_view.tscn",
}

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false


class FailBridge:
	extends "res://autoload/c_bridge.gd"
	var attempts := 0

	func _refuse() -> bool:
		attempts += 1
		_last_error = "pipe exploded (test reason 7731)"
		return false

	func ensure_world(_s, _n, _f) -> bool:
		return _refuse()

	func load_mission_live(_s, _n, _f, _fog_filter := false) -> bool:
		return _refuse()

	func load_debrief_live(_s, _n, _f) -> bool:
		return _refuse()

	func load_chronicle_live(_s, _n, _f) -> bool:
		return _refuse()

	func begin_mission_live(_s, _n, _f) -> bool:
		return _refuse()

	func load_tactical_live(_s, _n, _f) -> bool:
		return _refuse()


class NoFrameBridge:
	extends "res://autoload/c_bridge.gd"
	var attempts := 0

	func _init() -> void:
		_last_error = "pipe exploded (test reason 7731)"

	func debrief_frame() -> Dictionary:
		attempts += 1
		return {}


func _initialize() -> void:
	await _run_tests()
	_assert(_completed, "the error-panel checks did not run to the end (a script error aborted them)")
	print("\n=== Pipe Error Panels Test Results ===")
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


func _session():
	return load("res://autoload/sim_session.gd")


func _router():
	return get_root().get_node_or_null("SceneRouter")


func _mount(scene_name: String) -> Node:
	var scene: Node = (load(SCENES[scene_name]) as PackedScene).instantiate()
	get_root().add_child(scene)
	await process_frame
	await process_frame
	return scene


func _panel(scene: Node) -> Control:
	var p = scene.find_child("ErrorPanel", true, false)
	return p as Control


func _panel_showing(scene: Node) -> bool:
	var p := _panel(scene)
	return p != null and p.is_visible_in_tree()


func _is_shared_instance(panel: Node, scene: Node) -> bool:
	var n: Node = panel
	while n != null:
		if n.scene_file_path == SHARED_PANEL:
			return true
		if n == scene:
			break
		n = n.get_parent()
	return false


func _qa_flag(scene: Node) -> bool:
	if not scene.has_method("qa_state"):
		return false
	return bool((scene.qa_state() as Dictionary).get("error_panel", false))


func _run_tests() -> void:
	for scene_name in SCENES:
		await _test_failure_shows_panel(scene_name)
		await _test_healthy_pipe_has_no_panel(scene_name)
	await _test_briefing_has_no_mock_fallback()
	await _test_briefing_killed_pipe()
	_session().reset()
	_completed = true


func _test_failure_shows_panel(scene_name: String) -> void:
	var fb = NoFrameBridge.new() if scene_name == "debrief" else FailBridge.new()
	_session().reset()
	_session()._bridge = fb
	var scene := await _mount(scene_name)
	var tag := "G2 %s" % scene_name

	var panel := _panel(scene)
	_assert(panel != null, "%s: no ErrorPanel node after a refused live load (blank scene plus push_error)" % tag)
	_assert(_panel_showing(scene), "%s: ErrorPanel exists but is not visible" % tag)
	_assert(_qa_flag(scene), "%s: qa_state()['error_panel'] is not true while the panel shows" % tag)
	_assert(fb.attempts >= 1, "control %s: the scene never attempted the %s" % [tag, "read of the held frame" if scene_name == "debrief" else "live load"])
	_assert(ResourceLoader.exists(SHARED_PANEL), "%s: %s does not exist" % [tag, SHARED_PANEL])
	if panel != null:
		_assert(_is_shared_instance(panel, scene),
			"%s: ErrorPanel is not an instance of %s" % [tag, SHARED_PANEL])
		var reason = panel.find_child("ErrorReason", true, false)
		_assert(reason is Label and (reason as Label).text.find(REASON) != -1,
			"%s: ErrorReason label missing or does not carry the bridge's last_error() text" % tag)
		var retry = panel.find_child("Retry", true, false)
		var back = panel.find_child("MainMenu", true, false)
		_assert(retry is Button and not (retry as Button).disabled, "%s: no enabled Retry button" % tag)
		_assert(back is Button and not (back as Button).disabled, "%s: no enabled MainMenu button" % tag)
		if retry is Button:
			var before: int = fb.attempts
			(retry as Button).pressed.emit()
			await process_frame
			await process_frame
			_assert(fb.attempts > before, "%s: Retry did not run the %s again" % [tag, "read of the held frame" if scene_name == "debrief" else "live load"])
			_assert(_panel_showing(scene), "%s: panel vanished after Retry although the pipe is still failing" % tag)
		if back is Button and _router() != null:
			_router().set("_current_scene_name", "")
			_router().set("_transitioning", false)
			(back as Button).pressed.emit()
			_assert(_router().get("_current_scene_name") == "main_menu",
				"%s: MainMenu routed to '%s', expected 'main_menu'" % [tag, _router().get("_current_scene_name")])
	scene.queue_free()
	await process_frame
	_session().reset()


func _test_healthy_pipe_has_no_panel(scene_name: String) -> void:
	_session().reset()
	if scene_name == "debrief":
		var held = _session().bridge()
		_assert(held.load_mission_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES),
			"G2 control debrief setup: load_mission_live failed: %s" % held.last_error())
		held.send_command({"type": "cmd", "name": "mission_end"})
		var deadline := Time.get_ticks_msec() + 5000
		while held.debrief_frame().is_empty() and Time.get_ticks_msec() < deadline:
			if held.pump() == 0:
				OS.delay_msec(5)
		_assert(not held.debrief_frame().is_empty(), "G2 control debrief setup: mission_end was not answered with a frame in 5 s")
	var scene := await _mount(scene_name)
	var tag := "G2 control %s" % scene_name
	var bridge = _session().bridge()
	_assert(bridge.last_error() == "", "%s: healthy pipe reported last_error '%s'" % [tag, bridge.last_error()])
	_assert(not _panel_showing(scene), "%s: ErrorPanel showing although the pipe is healthy" % tag)
	_assert(not _qa_flag(scene), "%s: qa_state()['error_panel'] true although the pipe is healthy" % tag)
	scene.queue_free()
	await process_frame
	_session().reset()


func _test_briefing_has_no_mock_fallback() -> void:
	var fb := FailBridge.new()
	_session().reset()
	_session()._bridge = fb
	var scene := await _mount("mission_briefing")
	var texts: Array[String] = []
	var stack: Array = [scene]
	while not stack.is_empty():
		var n: Node = stack.pop_back()
		if n is Label:
			texts.append((n as Label).text)
		elif n is RichTextLabel:
			texts.append((n as RichTextLabel).text)
		stack.append_array(n.get_children())
	var joined := "\n".join(texts)
	_assert(joined.find("Thessalonica") == -1 and joined.find("OP-2741") == -1,
		"G2 briefing: mock_001 fixture text (Thessalonica / OP-2741) shown after a failed live load")
	scene.queue_free()
	await process_frame
	_session().reset()


func _test_briefing_killed_pipe() -> void:
	_session().reset()
	var bridge = _session().bridge()
	if not bridge.ensure_world(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES):
		_assert(false, "killed-pipe setup: ensure_world failed: %s" % bridge.last_error())
		_session().reset()
		return
	var pid := int(bridge.get("_session_pid"))
	_assert(pid > 0, "control: the real session has no pipe pid")
	OS.kill(pid)
	OS.delay_msec(200)
	var scene := await _mount("mission_briefing")
	_assert(_panel_showing(scene), "G2 briefing (pipe killed): no visible ErrorPanel after the pipe process died")
	_assert(_panel(scene) != null and _is_shared_instance(_panel(scene), scene),
		"G2 briefing (pipe killed): ErrorPanel is not an instance of %s" % SHARED_PANEL)
	var reason = _panel(scene).find_child("ErrorReason", true, false) if _panel(scene) != null else null
	_assert(reason is Label and (reason as Label).text.strip_edges() != "",
		"G2 briefing (pipe killed): ErrorReason is missing or empty")
	scene.queue_free()
	await process_frame
	_session().reset()

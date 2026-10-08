extends CanvasLayer

const SCENES := {
	"loading_screen": "res://scenes/loading_screen/loading_screen.tscn",
	"error_screen": "res://scenes/error_screen/error_screen.tscn",
	"main_menu": "res://scenes/main_menu/main_menu.tscn",
	"new_game": "res://scenes/new_game/new_game.tscn",
	"load_game": "res://scenes/load_game/load_game.tscn",
	"era_library": "res://scenes/era_library/era_library.tscn",
	"era_detail": "res://scenes/era_library/era_detail.tscn",
	"onboarding": "res://scenes/onboarding/onboarding.tscn",
	"mission_briefing": "res://scenes/mission_briefing/mission_briefing.tscn",
	"debrief": "res://scenes/debrief/debrief.tscn",
	"time_jump": "res://scenes/world/time_jump_sequencer.tscn",
	"settings": "res://scenes/settings/settings.tscn",
	"galaxy": "res://scenes/galaxy/galaxy_view.tscn",
	"tactical_c": "res://scenes/tactical_c/tactical_view.tscn",
	"lobby": "res://scenes/lobby/lobby.tscn",
	"chronicle": "res://scenes/world/chronicle_scroll_panel.tscn",
}

var _back_stack: Array[Dictionary] = []
var _overlay: ColorRect
var _current_scene_name: String = ""
var _transitioning := false
var _pending: Dictionary = {}

func _ready() -> void:
	layer = 99
	_current_scene_name = "loading_screen"
	_overlay = ColorRect.new()
	_overlay.color = ThemeConstants.BASE
	_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_overlay.modulate.a = 0.0
	add_child(_overlay)


func go_to(scene_name: String, params: Dictionary = {}) -> void:
	# See also: tests/test_scene_router_queue.gd (T12, dropped Deploy click)
	if _transitioning:
		if not _pending.is_empty():
			push_warning("SceneRouter: queued '%s' replaced by '%s'" % [_pending["name"], scene_name])
		_pending = {"name": scene_name, "params": params}
		return
	if not SCENES.has(scene_name):
		if not ThemeConstants.IS_RELEASE_BUILD:
			print("SceneRouter: unknown scene '%s'" % scene_name)
		return

	_transitioning = true

	if scene_name == "main_menu":
		_back_stack.clear()
	elif _current_scene_name != "":
		_back_stack.push_back({"name": _current_scene_name, "params": {}})

	_current_scene_name = scene_name

	var tw := create_tween()
	tw.tween_property(_overlay, "modulate:a", 1.0, ThemeConstants.FADE_DURATION)
	tw.tween_callback(_swap_scene.bind(scene_name, params))
	tw.tween_property(_overlay, "modulate:a", 0.0, ThemeConstants.FADE_DURATION)
	tw.tween_callback(_finish_transition)


func _finish_transition() -> void:
	_transitioning = false
	if not _pending.is_empty():
		var next := _pending
		_pending = {}
		go_to(next["name"], next["params"])


func go_back() -> void:
	if _back_stack.is_empty() or _transitioning:
		return
	var prev: Dictionary = _back_stack.pop_back()
	_current_scene_name = ""
	go_to(prev["name"], prev.get("params", {}))


func _swap_scene(scene_name: String, params: Dictionary) -> void:
	var tree := get_tree()
	var old_scene := tree.current_scene
	if old_scene:
		old_scene.queue_free()

	var new_scene_res = load(SCENES[scene_name])
	var new_scene = new_scene_res.instantiate()
	tree.root.add_child(new_scene)
	tree.current_scene = new_scene

	if new_scene.has_method("setup"):
		new_scene.setup(params)

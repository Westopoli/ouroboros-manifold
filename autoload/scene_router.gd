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
	"tactical": "res://scenes/tactical/tactical.tscn",
	"debrief": "res://scenes/debrief/debrief.tscn",
	"time_jump": "res://scenes/world/time_jump_sequencer.tscn",
	"settings": "res://scenes/settings/settings.tscn",
}

var _back_stack: Array[Dictionary] = []
var _overlay: ColorRect
var _current_scene_name: String = ""
var _transitioning := false

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
	if _transitioning:
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
	tw.tween_callback(func(): _transitioning = false)


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

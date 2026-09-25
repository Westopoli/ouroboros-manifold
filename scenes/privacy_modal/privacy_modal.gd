extends Control

const FLAG_PATH := "user://privacy_accepted"

var _skip_to_loading_screen: bool = false

@onready var _accept_button: Button = $CenterContainer/VBoxContainer/AcceptButton


func _ready() -> void:
	if FileAccess.file_exists(FLAG_PATH):
		_skip_to_loading_screen = true
		visible = false
		call_deferred("_route_to_loading")
		return
	if _accept_button != null:
		_accept_button.pressed.connect(_on_accept_pressed)


func _on_accept_pressed() -> void:
	var f := FileAccess.open(FLAG_PATH, FileAccess.WRITE)
	if f != null:
		f.close()
	_route_to_loading()


func _route_to_loading() -> void:
	var router := get_node_or_null("/root/SceneRouter")
	if router != null and router.has_method("go_to"):
		router.go_to("loading_screen")


func qa_state() -> Dictionary:
	return {
		"scene": "privacy_modal",
		"tick": -1,
		"accepted": _skip_to_loading_screen,
		"plants": [],
	}

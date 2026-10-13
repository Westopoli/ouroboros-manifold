extends Control

signal retry_pressed

@onready var _panel: Control = $ErrorPanel
@onready var _reason: Label = $ErrorPanel/V/ErrorReason


func _ready() -> void:
	$ErrorPanel/V/Retry.pressed.connect(func(): retry_pressed.emit())
	$ErrorPanel/V/MainMenu.pressed.connect(func(): SceneRouter.go_to("main_menu"))


func show_error(reason: String, retry: bool = true) -> void:
	_reason.text = reason
	$ErrorPanel/V/Retry.visible = retry
	_panel.visible = true


func hide_error() -> void:
	_panel.visible = false

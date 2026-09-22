extends Control

## C7 -- thin QA-harness wrapper scene (docs/northstar/plans/push/specs/C7.md).
## scripts/qa_harness.sh's run/liveness subcommands launch this scene
## directly (no --qa-port/--qa-script needed for the window to exist); the
## title is set unconditionally, matching qa_driver.gd's
## DisplayServer.window_set_title("QA:" + _root.name) convention so
## `xdotool search --name '^QA:'` finds this window regardless of whether
## the QADaemon autoload is active.


func _ready() -> void:
	DisplayServer.window_set_title("QA:" + name)


func _input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed:
		print("QA_INPUT mouse_button %d,%d" % [int(event.position.x), int(event.position.y)])
	elif event is InputEventKey and event.pressed:
		print("QA_INPUT key 0,0")

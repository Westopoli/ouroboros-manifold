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

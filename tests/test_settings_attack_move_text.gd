extends SceneTree

# A6 follow-up C5-N (docs/northstar/plans/2026-10-01-architect-rulings.md "A6 follow-ups" 4):
# attack-move is "press A, then left-click" (R-103-08, Westley); the controls text in
# scenes/settings/settings.gd no longer says "A + RMB".
const SETTINGS_SOURCE := "res://scenes/settings/settings.gd"

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	_run_tests()
	print("\n=== Settings Attack-Move Text Test Results ===")
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
	var src := FileAccess.get_file_as_string(SETTINGS_SOURCE)
	_assert(src != "", "cannot read " + SETTINGS_SOURCE)
	_assert(src.find("A, then left-click") != -1, "settings.gd does not say attack-move is 'A, then left-click'")
	_assert(src.find("A + RMB") == -1 and src.find("A+RMB") == -1, "settings.gd still says attack-move is 'A + RMB'")

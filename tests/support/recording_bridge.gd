extends "res://autoload/c_bridge.gd"

# Test double for the shared pipe session (autoload/sim_session.gd): no pipe
# process; records every command the client sends, answers a jump with a
# canned chronicle frame and snapshot. Install with
# SimSession.set("_bridge", RecordingBridge.new()) after SimSession.reset().
# Used by tests/test_chronicle_scene_open.gd and tests/test_debrief_proceed_jump.gd
# (A69: a scene's _ready sends no sim-changing command).

const SIM_CHANGING := ["jump", "step", "mission_start", "mission_end", "mission_refuse",
	"mission_begin", "tactical_step", "set_seed", "command", "load", "ready_for_time_jump"]

var sent: Array = []
var canned_chronicle: Dictionary = {}
var canned_snapshot: Dictionary = {}


func send_command(cmd: Dictionary) -> void:
	sent.append(str(cmd.get("name", cmd.get("cmd", ""))))


func _request(cmds: Array, want: Array) -> Dictionary:
	for cmd in cmds:
		sent.append(str(cmd.get("name", "")))
	var out := {}
	if want.has("chronicle"):
		out["chronicle"] = canned_chronicle
		out["snapshot"] = canned_snapshot
	return out


func _autosave() -> bool:
	return true


func ensure_world(_seed: int, _n_regions: int, _features: Array) -> bool:
	return true


func ensure_session(_seed: int, _n_regions: int, _features: Array, _new_campaign: bool = true) -> bool:
	return true


func count(name: String) -> int:
	return sent.count(name)


func sim_changing_sent() -> Array:
	var out: Array = []
	for n in sent:
		if SIM_CHANGING.has(n):
			out.append(n)
	return out


# Holds a frame as if the flow leading in (Proceed from the debrief) had jumped.
func hold_jump(frame: Dictionary, snapshot: Dictionary) -> void:
	_chronicle = frame
	_chronicle_snapshot = snapshot
	_snapshot = snapshot
	canned_chronicle = frame
	canned_snapshot = snapshot

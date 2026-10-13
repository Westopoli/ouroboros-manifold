extends RefCounted
# Sim adapter over the C pipe (W2, docs/northstar/plans/2026-10-06-steam-multiplayer-wiring-spec.md, interface 2).

var _bridge = null
var _last_frame := {}
var _refusals: Array = []


func _init(bridge = null) -> void:
	_bridge = bridge


func submit(cmd: Dictionary) -> int:
	var code: int = int(_bridge.net_submit(cmd))
	if code != 0:
		_refusals.append(code)
	return code


# Returns {tick, sections?} or null when the pipe failed or the frame is not the ack's tick (a stray tactical_step).
func step():
	var r: Dictionary = _bridge.net_step(1, true)
	if r.is_empty():
		return null
	var ack: Dictionary = r.get("net_ack", {})
	var fr: Dictionary = r.get("tactical", {})
	if ack.is_empty() or fr.is_empty():
		return null
	_last_frame = _bridge._reconstruct_tactical(fr)
	if int(fr.get("tick", -1)) != int(ack.get("tick", -2)):
		return null
	var out := {"tick": int(ack["tick"])}
	if ack.has("sections"):
		out["sections"] = ack["sections"]
	return out


func last_frame() -> Dictionary:
	return _last_frame


func refusals() -> Array:
	return _refusals

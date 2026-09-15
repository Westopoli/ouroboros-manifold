## Client-side command validator. Refuses malformed packets before they reach the server.
## Fails closed: unknown kind, dead/unknown unit UIDs, and negative positions are all rejected.
## See also: input_router.gd — calls validate() before every SimBridge.send_command()
extends Node

const _KNOWN_KINDS := [
	"move", "attack_move", "attack_target", "activate_ability",
	"layer_hard_transfer", "layer_preference_set",
	"control_group_bind", "control_group_recall",
]


func validate(cmd: Dictionary) -> bool:
	if cmd.get("kind", "") not in _KNOWN_KINDS:
		return false
	for uid in cmd.get("unit_uids", []):
		if not TacticalBridge.units.has(int(uid)):
			return false
	if cmd.has("target_uid") and not TacticalBridge.units.has(int(cmd["target_uid"])):
		return false
	if cmd.has("target"):
		var tgt: Dictionary = cmd["target"]
		if tgt.has("pos"):
			var pos: Array = tgt["pos"]
			if float(pos[0]) < 0.0 or float(pos[1]) < 0.0:
				return false
	return true

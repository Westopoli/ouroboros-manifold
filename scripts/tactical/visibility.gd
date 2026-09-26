## Visibility predicate — single source of truth for fog of war.
## See: docs/stage_specs/stage_11c_layer_visuals_and_fog_spec.md (D5)
## Consumers: unit_renderer.gd, hud.gd (_Minimap), input_router.gd
extends Node

const _SimSession := preload("res://autoload/sim_session.gd")


func is_unit_visible_to_player(uid: int) -> bool:
	var unit: Dictionary = TacticalBridge.units.get(uid, {})
	if unit.is_empty():
		return false
	var faction: int = int(unit.get("faction", -1))
	var pf: int = _SimSession.bridge().player_faction()
	if pf < 0:
		# No player faction known yet: nothing is own; use fog visibility only.
		return TacticalBridge.player_visible_unit_uids.has(uid)
	if faction == pf:
		return true
	# In a two-faction game opponent is 1 - pf; neutrals (any other id) are visible.
	var opponent: int = 1 - pf
	if faction != opponent:
		return true
	return TacticalBridge.player_visible_unit_uids.has(uid)

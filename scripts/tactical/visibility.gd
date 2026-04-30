## Visibility predicate — single source of truth for fog of war.
## See: docs/stage_specs/stage_11c_layer_visuals_and_fog_spec.md (D5)
## Consumers: unit_renderer.gd, hud.gd (_Minimap), input_router.gd
extends Node

const PLAYER_FACTION := 0


func is_unit_visible_to_player(uid: int) -> bool:
	var unit: Dictionary = TacticalBridge.units.get(uid, {})
	if unit.is_empty():
		return false
	var faction: int = int(unit.get("faction", -1))
	if faction == PLAYER_FACTION:
		return true
	if faction != 1:
		return true
	return TacticalBridge.player_visible_unit_uids.has(uid)

extends RefCounted

# S-069 (shared with S-106): the model behind galaxy_view's driven mode. The
# time-jump sequencer names regions "r<i>" and factions "f<id>"; this maps them
# onto the snapshot shape galaxy_view renders (regions {i, owner, tier}, edges
# {a, b, t}) so the chronicle map shares the S-106/S-107 renderer. Positions,
# colours and camera are the galaxy view's own.

const TIER_BY_SIGNIFICANCE := [0.45, 0.8]
const EDGE_TYPES := {"border": 0, "trade": 1, "alliance": 2}

var _index_of: Dictionary = {}
var _owner_of: Dictionary = {}
var _tier_of: Dictionary = {}
var _edges: Array = []


func index_for(region_id: String) -> int:
	if not _index_of.has(region_id):
		var tail := region_id.substr(1)
		_index_of[region_id] = int(tail) if region_id.begins_with("r") and tail.is_valid_int() else _index_of.size() + 10000
	return _index_of[region_id]


func knows(region_id: String) -> bool:
	return _index_of.has(region_id)


func set_region(region_id: String, significance: float, faction_id: String) -> void:
	var i := index_for(region_id)
	_tier_of[i] = 0 if significance < TIER_BY_SIGNIFICANCE[0] else (1 if significance < TIER_BY_SIGNIFICANCE[1] else 2)
	if faction_id != "<keep>":
		_owner_of[i] = _owner_for(faction_id)


func set_tier(region_id: String, significance: float) -> void:
	set_region(region_id, significance, "<keep>")


func set_owner(region_id: String, faction_id: String) -> void:
	var i := index_for(region_id)
	_owner_of[i] = _owner_for(faction_id)
	if not _tier_of.has(i):
		_tier_of[i] = 1


func clear_owner(region_id: String) -> void:
	_owner_of[index_for(region_id)] = -1


func add_edge(from_id: String, to_id: String, edge_type: String) -> void:
	_edges.append({"a": index_for(from_id), "b": index_for(to_id), "t": EDGE_TYPES.get(edge_type, 0)})


func snapshot() -> Dictionary:
	var regions := []
	var ids := _tier_of.keys()
	ids.sort()
	for i in ids:
		regions.append({"i": i, "owner": _owner_of.get(i, -1), "tier": _tier_of[i]})
	return {"regions": regions, "edges": _edges.duplicate()}


func _owner_for(faction_id: String) -> int:
	var tail := faction_id.substr(1)
	return int(tail) if faction_id.begins_with("f") and tail.is_valid_int() else -1

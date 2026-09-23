extends Node

# Copied and trimmed from scenes/shared/world_view/world_view_data.gd (2026-09-22)
# for the pass-2 galaxy mockup. Only the regions/connections/territories surface
# that legacy_constellation_renderer.gd and legacy_shell_renderer.gd consume is
# kept; Stage-11g inspection metadata (regions_metadata, factions, centroid
# cache) and the flash/highlight signals are dropped, unused by this mockup
# (galaxy_view.gd keeps its own flash()).

signal regions_cleared()
signal connection_added(from_id: String, to_id: String)
signal connection_removed(from_id: String, to_id: String)
signal territory_set(region_id: String)
signal territory_updated(region_id: String)
signal territory_removed(region_id: String)

var regions: Dictionary = {}
var connections: Dictionary = {}
var territories: Dictionary = {}


func _connection_key(from_id: String, to_id: String) -> String:
	if from_id < to_id:
		return from_id + "::" + to_id
	return to_id + "::" + from_id


func add_region(id: String, position: Vector3, size: float, color: Color, faction_id: String) -> void:
	regions[id] = {
		"position": position,
		"size": size,
		"color": color,
		"faction_id": faction_id,
	}


func get_region(id: String) -> Dictionary:
	if id in regions:
		return regions[id]
	return {}


func set_territory(region_id: String, center: Vector3, radius: float, color: Color) -> void:
	territories[region_id] = {
		"center": center,
		"radius": radius,
		"color": color,
	}
	territory_set.emit(region_id)


func remove_territory(region_id: String) -> void:
	if region_id not in territories:
		return
	territories.erase(region_id)
	territory_removed.emit(region_id)


func get_territory(region_id: String) -> Dictionary:
	if region_id in territories:
		return territories[region_id]
	return {}


func add_connection(from_id: String, to_id: String, connection_type: String, color: Color) -> void:
	var key := _connection_key(from_id, to_id)
	connections[key] = {
		"from_id": from_id,
		"to_id": to_id,
		"connection_type": connection_type,
		"color": color,
	}
	connection_added.emit(from_id, to_id)


func remove_connection(from_id: String, to_id: String) -> void:
	var key := _connection_key(from_id, to_id)
	if key not in connections:
		return
	connections.erase(key)
	connection_removed.emit(from_id, to_id)


func get_connection(from_id: String, to_id: String) -> Dictionary:
	var key := _connection_key(from_id, to_id)
	if key in connections:
		return connections[key]
	return {}


func clear_all() -> void:
	regions.clear()
	connections.clear()
	territories.clear()
	regions_cleared.emit()

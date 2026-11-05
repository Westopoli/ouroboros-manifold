extends Node

signal region_added(region_id: String)
signal region_updated(region_id: String)
signal region_removed(region_id: String)
signal regions_cleared()

signal territory_set(region_id: String)
signal territory_updated(region_id: String)
signal territory_removed(region_id: String)

signal connection_added(from_id: String, to_id: String)
signal connection_removed(from_id: String, to_id: String)

signal flash_region_requested(region_id: String, intensity: float)
signal flash_conflict_requested(from_id: String, to_id: String, intensity: float)

signal highlight_changed(region_id: String)

# Stage 11g — inspection metadata. See docs/legacy/stage_specs/stage_11g_world_view_inspection_spec.md
signal region_metadata_set(region_id: String)
signal faction_metadata_set(faction_id: String)
signal factions_cleared()

var regions: Dictionary = {}
var connections: Dictionary = {}
var territories: Dictionary = {}
var highlight_id: String = ""

# Stage 11g — additive metadata stores. Empty until a producer populates them.
var regions_metadata: Dictionary = {}  # rid → {region_id, tier, military, economy, tension, population, previous_owners}
var factions: Dictionary = {}          # fid → {id, archetype, tech_tier, region_ids, aggregates, history}
var _faction_centroid_cache: Dictionary = {}


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
	region_added.emit(id)


func update_region(id: String, size: float, color: Color) -> void:
	if id not in regions:
		return
	regions[id]["size"] = size
	regions[id]["color"] = color
	region_updated.emit(id)


func remove_region(id: String) -> void:
	if id not in regions:
		return
	regions.erase(id)
	region_removed.emit(id)


func clear_regions() -> void:
	regions.clear()
	regions_cleared.emit()


func set_territory(region_id: String, center: Vector3, radius: float, color: Color) -> void:
	territories[region_id] = {
		"center": center,
		"radius": radius,
		"color": color,
	}
	territory_set.emit(region_id)


func update_territory(region_id: String, radius: float, color: Color) -> void:
	if region_id not in territories:
		return
	territories[region_id]["radius"] = radius
	territories[region_id]["color"] = color
	territory_updated.emit(region_id)


func remove_territory(region_id: String) -> void:
	if region_id not in territories:
		return
	territories.erase(region_id)
	territory_removed.emit(region_id)


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


func request_flash_region(region_id: String, intensity: float) -> void:
	flash_region_requested.emit(region_id, intensity)


func request_flash_conflict(from_id: String, to_id: String, intensity: float) -> void:
	flash_conflict_requested.emit(from_id, to_id, intensity)


func set_highlight(region_id: String) -> void:
	highlight_id = region_id
	highlight_changed.emit(region_id)


func get_region(id: String) -> Dictionary:
	if id in regions:
		return regions[id]
	return {}


func get_all_regions() -> Dictionary:
	return regions


func get_connection(from_id: String, to_id: String) -> Dictionary:
	var key := _connection_key(from_id, to_id)
	if key in connections:
		return connections[key]
	return {}


func get_territory(region_id: String) -> Dictionary:
	if region_id in territories:
		return territories[region_id]
	return {}


# ── Stage 11g — inspection metadata ──────────────────────────────────────────
func set_region_metadata(region_id: String, meta: Dictionary) -> void:
	regions_metadata[region_id] = meta.duplicate(true)
	region_metadata_set.emit(region_id)


func get_region_metadata(region_id: String) -> Dictionary:
	if region_id in regions_metadata:
		return regions_metadata[region_id]
	return {}


func set_faction_metadata(faction_id: String, meta: Dictionary) -> void:
	factions[faction_id] = meta.duplicate(true)
	_faction_centroid_cache.erase(faction_id)
	faction_metadata_set.emit(faction_id)


func get_faction_metadata(faction_id: String) -> Dictionary:
	if faction_id in factions:
		return factions[faction_id]
	return {}


func clear_factions() -> void:
	factions.clear()
	_faction_centroid_cache.clear()
	factions_cleared.emit()


func get_faction_region_ids(faction_id: String) -> Array:
	var owned: Array = []
	for rid in regions:
		var r: Dictionary = regions[rid]
		if r.get("faction_id", "") == faction_id:
			owned.append(rid)
	return owned


func get_faction_centroid(faction_id: String) -> Vector3:
	if _faction_centroid_cache.has(faction_id):
		return _faction_centroid_cache[faction_id]
	var sum := Vector3.ZERO
	var count := 0
	for rid in regions:
		var r: Dictionary = regions[rid]
		if r.get("faction_id", "") == faction_id:
			sum += r.get("position", Vector3.ZERO) as Vector3
			count += 1
	var centroid := Vector3.ZERO if count == 0 else sum / float(count)
	_faction_centroid_cache[faction_id] = centroid
	return centroid


func invalidate_faction_centroids() -> void:
	_faction_centroid_cache.clear()

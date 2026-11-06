extends Node

var _manifest: Dictionary = {}
var _scene_cache: Dictionary = {}  # "units/vanguard_t2.glb" → PackedScene
var _fallback_scene: PackedScene

var _load_warnings: int = 0


func _ready() -> void:
	_fallback_scene = _make_fallback_scene()
	var era_id: String = EraConfig.ACTIVE_ERA_ID
	var manifest_path := "res://assets/eras/%s/manifest.json" % era_id
	var f := FileAccess.open(manifest_path, FileAccess.READ)
	if not f:
		push_warning("EraThemeResolver: manifest not found at %s" % manifest_path)
		return
	var parsed = JSON.parse_string(f.get_as_text())
	f.close()
	if not parsed is Dictionary:
		push_warning("EraThemeResolver: manifest parse failed")
		return
	_manifest = parsed
	_preload_scenes(era_id)
	print("EraThemeResolver: loaded era=%s  cached=%d  warnings=%d" % [
		era_id, _scene_cache.size(), _load_warnings
	])


func get_unit_scene(unit_type: String, tier: int) -> PackedScene:
	var units: Dictionary = _manifest.get("units", {})
	var entry: Dictionary = units.get(unit_type, {})
	var tiers: Dictionary = entry.get("tiers", {})
	var tier_entry: Dictionary = tiers.get(str(tier), {})
	var rel: String = tier_entry.get("scene", "")
	return _cached_or_fallback(rel)


func get_structure_scene(tier: int) -> PackedScene:
	var structs: Dictionary = _manifest.get("structures", {})
	var entry: Dictionary = structs.get("settlement", {})
	var tiers: Dictionary = entry.get("tiers", {})
	var tier_entry: Dictionary = tiers.get(str(tier), {})
	var rel: String = tier_entry.get("scene", "")
	return _cached_or_fallback(rel)


func get_environment_scene(category: String) -> PackedScene:
	var env: Dictionary = _manifest.get("environment", {})
	var entry: Dictionary = env.get(category, {})
	var rel: String = entry.get("scene", "")
	return _cached_or_fallback(rel)


func get_material_config(tier: int) -> Dictionary:
	var mats: Dictionary = _manifest.get("materials", {})
	return mats.get(str(tier), {})


func get_faction_color_mode(tier: int) -> String:
	var cfg := get_material_config(tier)
	return cfg.get("faction_color_treatment", "matte")


func get_squad_count(unit_type: String) -> int:
	var units: Dictionary = _manifest.get("units", {})
	var entry: Dictionary = units.get(unit_type, {})
	return entry.get("squad_count", 1)


func get_unit_visual_scale(unit_type: String) -> float:
	var units: Dictionary = _manifest.get("units", {})
	var entry: Dictionary = units.get(unit_type, {})
	return float(entry.get("visual_scale", EraConfig.UNIT_VISUAL_SCALE))


func get_unit_facing_offset(unit_type: String) -> float:
	var units: Dictionary = _manifest.get("units", {})
	var entry: Dictionary = units.get(unit_type, {})
	return float(entry.get("facing_offset_rad", 0.0))


func get_era_display() -> Dictionary:
	return {
		"era_id":      _manifest.get("era_id", ""),
		"name":        _manifest.get("era_display_name", ""),
		"accent_color": _manifest.get("era_accent_color", "#888888"),
	}


func get_active_era() -> String:
	return _manifest.get("era_id", EraConfig.ACTIVE_ERA_ID)


# Cover asset keys per era. Settled Reach: tiny+small → asteroid_small.glb,
# medium → asteroid_medium.glb, huge → asteroid_large.glb. Additional eras
# are research-only (see docs/legacy/method_era1/priority_queue.md "Research-only" §
# Multi-era catalog) — no per-era asset bindings until multi-era promotes.
const _COVER_ASSETS: Dictionary = {
	"settled_reach": {
		"tiny":   "res://assets/eras/settled_reach/environment/asteroid_small.glb",
		"small":  "res://assets/eras/settled_reach/environment/asteroid_small.glb",
		"medium": "res://assets/eras/settled_reach/environment/asteroid_medium.glb",
		"huge":   "res://assets/eras/settled_reach/environment/asteroid_large.glb",
	},
}


func get_cover_asset(era_id: String, scale_class: String) -> String:
	var era_map: Dictionary = _COVER_ASSETS.get(era_id, {})
	return era_map.get(scale_class, "")


func get_faction_color(faction_id: int) -> Color:
	var colors: Dictionary = _manifest.get("faction_colors", {})
	var hex: String = colors.get(str(faction_id), "#888888")
	return Color(hex)


# — internals —

func _preload_scenes(era_id: String) -> void:
	var base := "res://assets/eras/%s/" % era_id
	var paths: Array[String] = []
	_collect_scene_paths(_manifest.get("units", {}), paths, true)
	_collect_scene_paths(_manifest.get("structures", {}), paths, false)
	for entry in _manifest.get("environment", {}).values():
		var rel: String = (entry as Dictionary).get("scene", "")
		if rel != "":
			paths.append(rel)
	for rel in paths:
		var full := base + rel
		if ResourceLoader.exists(full):
			_scene_cache[rel] = load(full)
		else:
			_load_warnings += 1


func _collect_scene_paths(section: Dictionary, out: Array[String], has_tiers: bool) -> void:
	for entry in section.values():
		if not entry is Dictionary:
			continue
		if has_tiers:
			for tier_entry in (entry as Dictionary).get("tiers", {}).values():
				var rel: String = (tier_entry as Dictionary).get("scene", "")
				if rel != "":
					out.append(rel)
		else:
			for tier_entry in (entry as Dictionary).get("tiers", {}).values():
				var rel: String = (tier_entry as Dictionary).get("scene", "")
				if rel != "":
					out.append(rel)


func _cached_or_fallback(rel: String) -> PackedScene:
	if rel == "":
		return _fallback_scene
	if _scene_cache.has(rel):
		return _scene_cache[rel]
	return _fallback_scene


func _make_fallback_scene() -> PackedScene:
	var mesh := SphereMesh.new()
	mesh.radius = 1.0
	mesh.height = 2.0
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(1.0, 0.0, 1.0)
	mesh.surface_set_material(0, mat)
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	var packed := PackedScene.new()
	packed.pack(mi)
	return packed

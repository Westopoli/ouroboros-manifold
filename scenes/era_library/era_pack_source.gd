extends RefCounted

# Reads era packs for the Era Library screens. Required keys mirror
# scripts/specfactory/pack_validate.py REQUIRED_KEYS (R-146-03).
const REQUIRED_KEYS := [
	"era_id", "era_display_name", "era_accent_color",
	"era_spatial_scale", "era_tone", "era_order",
	"units", "structures", "environment", "materials", "faction_colors",
]

var _packs: Array = []


func _init(packs_root: String = "res://assets/eras") -> void:
	for id in DirAccess.get_directories_at(packs_root):
		var m := _read("%s/%s/manifest.json" % [packs_root, id])
		if m.is_empty() or bool(m.get("test_only", false)):
			continue
		var ok := true
		for k in REQUIRED_KEYS:
			ok = ok and m.has(k)
		if ok:
			_packs.append(m)
	_packs.sort_custom(func(a, b): return int(a["era_order"]) < int(b["era_order"]))


func manifests() -> Array:
	return _packs


func find(era_id: String) -> Dictionary:
	for m in _packs:
		if m["era_id"] == era_id:
			return m
	return {}


func tiers(era_id: String) -> Array:
	var seen := {}
	for u in find(era_id).get("units", {}).values():
		for t in u.get("tiers", {}).keys():
			seen[int(t)] = true
	var out := seen.keys()
	out.sort()
	return out


func roster(era_id: String) -> Array:
	var out := []
	var units: Dictionary = find(era_id).get("units", {})
	for type_id in units.keys():
		out.append({"abstract_type": type_id, "category": str(units[type_id].get("category", ""))})
	return out


func _read(path: String) -> Dictionary:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return {}
	var v = JSON.parse_string(f.get_as_text())
	return v if v is Dictionary else {}

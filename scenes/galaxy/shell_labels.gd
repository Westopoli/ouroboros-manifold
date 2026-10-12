extends RefCounted

# Faction name labels (R-106-03: names show in the overview band only) and, under the
# Compatibility renderer, a flat alpha-blended stand-in mesh per faction in place of the field shell.
# Called from shell_renderer.gd.

const ChronicleNames := preload("res://scenes/world/chronicle_names.gd")
const LABEL_LIBRARY := "res://library/chronicle/fragments.json"
const LABEL_LIFT := 3.0   # prototype scenes/mockups/galaxy/galaxy_view.gd:164, 6.0 x CIV_SCALE 0.5 (B23): above the mean of the faction's system positions
const LABEL_PIXEL_SIZE := 0.025   # prototype galaxy_view.gd:170, 0.05 x CIV_SCALE 0.5 (B23)
const LABEL_FONT_SIZE := 40   # prototype galaxy_view.gd:166
const STAND_IN_OPACITY_MULTIPLIER := 0.15   # draft: Architect ruling 2026-10-08, planes sit under the dots

var stand_in: bool
var _host: Node3D
var _names: RefCounted   # chronicle name table: the wire carries no faction names
var _labels: Dictionary = {}    # faction id -> Label3D
var _meshes: Dictionary = {}    # colour key -> MeshInstance3D (stand-in only)


func _init(host: Node3D, use_stand_in: bool) -> void:
	_host = host
	stand_in = use_stand_in
	_names = ChronicleNames.new()
	var lib = JSON.parse_string(FileAccess.get_file_as_string(LABEL_LIBRARY))
	if lib is Dictionary:
		_names.load_tables(lib.get("name_tables", {}))


# factions: colour key -> {region_id: true}. One label per faction id (R-106-03), at the mean of its
# regions; a region mid-tween sits in its old owner's colour, so the label takes the colour held by most
# of the faction's regions.
func refresh(factions: Dictionary, data: Node, known_ids: Array = []) -> void:
	var live := {}
	var parts := {}
	var keys := factions.keys()
	keys.sort()
	for key in keys:
		for rid in factions[key]:
			var t: Dictionary = data.get_territory(rid)
			if t.is_empty():
				continue
			var fid := str(data.get_region(rid).get("faction_id", ""))
			if not parts.has(fid):
				parts[fid] = {"sum": Vector3.ZERO, "n": 0, "votes": {}, "colors": {}}
			parts[fid]["sum"] += t["center"]
			parts[fid]["n"] += 1
			parts[fid]["votes"][key] = parts[fid]["votes"].get(key, 0) + 1
			parts[fid]["colors"][key] = t["color"]
	var fids := parts.keys()
	fids.sort()
	for fid in fids:
		var p: Dictionary = parts[fid]
		var best := ""
		for k in keys:
			if p["votes"].has(k) and (best == "" or p["votes"][k] > p["votes"][best]):
				best = k
		var color: Color = p["colors"][best]
		live[fid] = true
		var label: Label3D = _labels.get(fid)
		if label == null:
			label = Label3D.new()
			label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
			label.no_depth_test = true
			label.pixel_size = LABEL_PIXEL_SIZE
			label.font_size = LABEL_FONT_SIZE
			_host.add_child(label)
			_labels[fid] = label
		label.text = _text_for(fid, known_ids, _labels.size())
		label.position = p["sum"] / p["n"] + Vector3(0.0, LABEL_LIFT, 0.0)
		label.modulate = Color(color.r, color.g, color.b, label.modulate.a)
	for key in factions:
		var terr: Array = []
		var color := Color.WHITE
		for rid in factions[key]:
			var t: Dictionary = data.get_territory(rid)
			if t.is_empty():
				continue
			terr.append(t)
			color = t["color"]
		if terr.is_empty():
			continue
		var centroid := Vector3.ZERO
		for t in terr:
			centroid += t["center"]
		centroid /= terr.size()
		if stand_in:
			var reach := 0.0
			for t in terr:
				reach = maxf(reach, centroid.distance_to(t["center"]) + float(t["radius"]))
			var mesh: MeshInstance3D = _meshes.get(key)
			if mesh == null:
				mesh = _make_stand_in(color)
				_host.add_child(mesh)
				_meshes[key] = mesh
			mesh.position = centroid
			mesh.scale = Vector3(reach, 1.0, reach)
			(mesh.material_override as StandardMaterial3D).albedo_color = Color(color.r, color.g, color.b, (mesh.material_override as StandardMaterial3D).albedo_color.a)
	for lkey in _labels.keys():
		if not live.has(lkey):
			_drop(_labels, lkey)
	for key in _meshes.keys():
		if not factions.has(key):
			_drop(_meshes, key)


# A display name (non-numeric faction_id) reads as a name; a bare owner id goes through UnknownLabel.
func _text_for(fid: String, known_ids: Array, ordinal: int) -> String:
	if fid == "":
		return "Faction %d" % ordinal
	var num := fid.trim_prefix("faction_")
	if fid.is_valid_int() or (fid.begins_with("faction_") and num.is_valid_int()):
		if known_ids.has(int(num)):
			return _names.fill_template("{faction_name}", -1, int(num))
		return UnknownLabel.text_for(int(num), known_ids)
	return fid.replace("_", " ").capitalize()


func apply(shell_opacity: float, label_alpha: float) -> void:
	for label: Label3D in _labels.values():
		label.modulate.a = label_alpha
		label.outline_modulate.a = label_alpha
	for mesh: MeshInstance3D in _meshes.values():
		var m := mesh.material_override as StandardMaterial3D
		m.albedo_color.a = shell_opacity * STAND_IN_OPACITY_MULTIPLIER


func clear() -> void:
	for key in _labels.keys():
		_drop(_labels, key)
	for key in _meshes.keys():
		_drop(_meshes, key)


func _drop(from: Dictionary, key) -> void:
	var node: Node = from[key]
	from.erase(key)
	if node.get_parent():
		node.get_parent().remove_child(node)
	node.queue_free()


func _make_stand_in(color: Color) -> MeshInstance3D:
	var mesh := MeshInstance3D.new()
	mesh.mesh = SphereMesh.new()
	mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.blend_mode = BaseMaterial3D.BLEND_MODE_MIX
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.albedo_color = Color(color.r, color.g, color.b, 0.0)
	mat.render_priority = -10
	mat.no_depth_test = false
	mesh.sorting_offset = -1000.0
	mesh.material_override = mat
	return mesh

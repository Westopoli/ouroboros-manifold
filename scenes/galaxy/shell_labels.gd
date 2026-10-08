extends RefCounted

# Faction name labels (R-106-03: names show in the overview band only) and, under the
# Compatibility renderer, a flat additive stand-in mesh per faction in place of the field shell.
# Called from shell_renderer.gd. Label text is the faction id spelled out; UnknownLabel.text_for
# (scenes/galaxy/unknown_label.gd, lane B13) is not on this branch yet.

const LABEL_LIFT := 8.0   # draft: B4 retunes the label scale and offset
const LABEL_PIXEL_SIZE := 0.05
const LABEL_FONT_SIZE := 64
const STAND_IN_OPACITY_MULTIPLIER := 0.15   # draft: Architect ruling 2026-10-08, planes sit under the dots

var stand_in: bool
var _host: Node3D
var _labels: Dictionary = {}    # colour key -> Label3D
var _meshes: Dictionary = {}    # colour key -> MeshInstance3D (stand-in only)


func _init(host: Node3D, use_stand_in: bool) -> void:
	_host = host
	stand_in = use_stand_in


# factions: colour key -> {region_id: true}
func refresh(factions: Dictionary, data: Node) -> void:
	for key in _labels.keys():
		if not factions.has(key):
			_drop(_labels, key)
	for key in _meshes.keys():
		if not factions.has(key):
			_drop(_meshes, key)
	for key in factions:
		var sum := Vector3.ZERO
		var n := 0
		var color := Color.WHITE
		var name_id := ""
		var terr: Array = []
		for rid in factions[key]:
			var t: Dictionary = data.get_territory(rid)
			if t.is_empty():
				continue
			terr.append(t)
			sum += t["center"]
			n += 1
			color = t["color"]
			if name_id == "":
				name_id = str(data.get_region(rid).get("faction_id", ""))
		if n == 0:
			continue
		var centroid := sum / n
		var label: Label3D = _labels.get(key)
		if label == null:
			label = Label3D.new()
			label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
			label.no_depth_test = true
			label.pixel_size = LABEL_PIXEL_SIZE
			label.font_size = LABEL_FONT_SIZE
			_host.add_child(label)
			_labels[key] = label
		label.text = name_id.replace("_", " ").capitalize() if name_id != "" else "Faction %d" % (_labels.size())
		label.position = centroid + Vector3(0.0, LABEL_LIFT, 0.0)
		label.modulate = Color(color.r, color.g, color.b, label.modulate.a)
		label.outline_modulate = Color(color.r * 0.5, color.g * 0.5, color.b * 0.5, label.outline_modulate.a)
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
	var plane := PlaneMesh.new()
	plane.size = Vector2(2, 2)
	mesh.mesh = plane
	mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.albedo_color = Color(color.r, color.g, color.b, 0.0)
	mat.render_priority = -10
	mat.no_depth_test = false
	mesh.sorting_offset = -1000.0
	mesh.material_override = mat
	return mesh

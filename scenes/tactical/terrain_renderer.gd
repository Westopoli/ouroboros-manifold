## Draws the tactical map in 3D: boundary slabs, gradient-source discs, spine node markers.
## For reinforcement_structure nodes, instances a 3D settlement model via EraThemeResolver
## and shows a faction-colored capture ring + HP label. Rebuilds on snapshot and on any
## structures_updated delta (captures are infrequent, full rebuild is acceptable).
extends Node3D

const BOUNDARY_COLOR     := Color(0.4, 0.4, 0.4, 0.9)
const BOUNDARY_THICKNESS := 8.0
const BOUNDARY_HEIGHT    := 20.0

const GRADIENT_COLORS: Dictionary = {
	"obstacle_density":    Color(0.9, 0.2, 0.1, 0.15),
	"cover_density":       Color(0.1, 0.8, 0.2, 0.12),
	"sensor_interference": Color(0.8, 0.2, 0.9, 0.12),
}
const GRADIENT_DEFAULT_COLOR := Color(0.5, 0.5, 0.5, 0.10)

const SPINE_NODE_COLORS: Dictionary = {
	"objective":               Color(1.0, 0.9, 0.1, 0.9),
	"chokepoint":              Color(0.8, 0.4, 0.1, 0.8),
	"staging":                 Color(0.3, 0.7, 1.0, 0.8),
	"extraction":              Color(0.2, 1.0, 0.5, 0.9),
	"vantage_point":           Color(0.9, 0.5, 1.0, 0.8),
	"reinforcement_structure": Color(0.1, 0.9, 0.5, 0.9),
}
const SPINE_DEFAULT_COLOR := Color(0.8, 0.8, 0.8, 0.7)
const SPINE_OUTER_RADIUS  := 48.0
const SPINE_INNER_RADIUS  := 40.0
const SPINE_HEIGHT        := 6.0

# Capture zone ring dimensions (larger than spine ring, sits on ground plane)
const CAP_OUTER_RADIUS := 120.0
const CAP_INNER_RADIUS := 108.0
const STRUCTURE_SCALE  := 2.0


func _ready() -> void:
	TacticalBridge.snapshot_received.connect(_on_snapshot)
	TacticalBridge.tick_delta_received.connect(_on_delta)


func _on_snapshot(_snap: Dictionary) -> void:
	_rebuild()


func _on_delta(delta: Dictionary) -> void:
	if delta.get("structures_updated", []).size() > 0:
		_rebuild()


func _rebuild() -> void:
	for c in get_children():
		remove_child(c)
		c.free()
	var md: Dictionary = TacticalBridge.map_data
	var canvas: Array  = md.get("canvas_size", [4000, 4000])
	_build_boundary(float(canvas[0]), float(canvas[1]))
	_build_gradient_sources(md.get("gradient_sources", []))
	_build_spine_nodes(md.get("spine_nodes", []))
	_scatter_environment(md.get("gradient_sources", []), md.get("map_seed", 0))


func _build_boundary(w: float, h: float) -> void:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = BOUNDARY_COLOR
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	var half_h := BOUNDARY_HEIGHT * 0.5
	var edges: Array = [
		[Vector3(w * 0.5, half_h, 0.0),   Vector3(w + BOUNDARY_THICKNESS * 2.0, BOUNDARY_HEIGHT, BOUNDARY_THICKNESS)],
		[Vector3(w * 0.5, half_h, h),      Vector3(w + BOUNDARY_THICKNESS * 2.0, BOUNDARY_HEIGHT, BOUNDARY_THICKNESS)],
		[Vector3(0.0,     half_h, h * 0.5), Vector3(BOUNDARY_THICKNESS, BOUNDARY_HEIGHT, h)],
		[Vector3(w,       half_h, h * 0.5), Vector3(BOUNDARY_THICKNESS, BOUNDARY_HEIGHT, h)],
	]
	for e in edges:
		var mi := MeshInstance3D.new()
		var box := BoxMesh.new()
		box.size = e[1]
		mi.mesh = box
		mi.set_surface_override_material(0, mat)
		mi.position = e[0]
		add_child(mi)


func _build_gradient_sources(sources: Array) -> void:
	for gs in sources:
		var pos2d: Array  = gs["pos"]
		var radius: float = float(gs.get("radius", 200))
		var intensity: float = float(gs.get("intensity", 0.5))
		var prop: String  = gs.get("property", "")
		var col: Color    = GRADIENT_COLORS.get(prop, GRADIENT_DEFAULT_COLOR)
		col.a *= intensity

		var mi  := MeshInstance3D.new()
		var cyl := CylinderMesh.new()
		cyl.top_radius    = radius
		cyl.bottom_radius = radius
		cyl.height        = 2.0
		mi.mesh = cyl

		var mat := StandardMaterial3D.new()
		mat.albedo_color = col
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mat.cull_mode    = BaseMaterial3D.CULL_DISABLED
		mi.set_surface_override_material(0, mat)
		mi.position = Vector3(float(pos2d[0]), 1.0, float(pos2d[1]))
		add_child(mi)


func _build_spine_nodes(nodes: Array) -> void:
	# Build pos→structure lookup for reinforcement_structure matching
	var struct_by_pos: Dictionary = {}
	for uid in TacticalBridge.structures:
		var s: Dictionary = TacticalBridge.structures.get(uid, {})
		if s.is_empty():
			continue
		var key := "%d_%d" % [int(float(s["pos"][0])), int(float(s["pos"][1]))]
		struct_by_pos[key] = s

	for sn in nodes:
		var pos2d: Array      = sn["pos"]
		var node_type: String = sn.get("type", "")
		var col: Color        = SPINE_NODE_COLORS.get(node_type, SPINE_DEFAULT_COLOR)

		var container := Node3D.new()
		container.position = Vector3(float(pos2d[0]), 0.0, float(pos2d[1]))
		add_child(container)

		if node_type == "reinforcement_structure":
			_build_structure_node(container, pos2d, struct_by_pos)
		else:
			_build_generic_spine_node(container, col, node_type)


func _build_generic_spine_node(container: Node3D, col: Color, node_type: String) -> void:
	var mi    := MeshInstance3D.new()
	var torus := TorusMesh.new()
	torus.inner_radius = SPINE_INNER_RADIUS
	torus.outer_radius = SPINE_OUTER_RADIUS
	mi.mesh = torus

	var mat := StandardMaterial3D.new()
	mat.albedo_color          = col
	mat.transparency          = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.emission_enabled      = true
	mat.emission              = col
	mat.emission_energy_multiplier = 0.4
	mi.set_surface_override_material(0, mat)
	mi.position = Vector3(0.0, SPINE_HEIGHT * 0.5, 0.0)
	container.add_child(mi)

	var label := Label3D.new()
	label.text      = node_type.replace("_", "\n")
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.font_size = 22
	label.modulate  = col.lightened(0.3)
	label.position  = Vector3(0.0, SPINE_HEIGHT + 40.0, 0.0)
	container.add_child(label)


func _build_structure_node(container: Node3D, pos2d: Array, struct_by_pos: Dictionary) -> void:
	var key := "%d_%d" % [int(float(pos2d[0])), int(float(pos2d[1]))]
	var s: Dictionary = struct_by_pos.get(key, {})

	var faction: int  = s.get("owner", -1)
	var hp: float     = float(s.get("hp", 0.0))
	var max_hp: float = float(s.get("max_hp", 1.0))
	var cap_prog: float = float(s.get("capture_progress", 0.0))

	# 3D settlement model
	var scene: PackedScene = EraThemeResolver.get_structure_scene(1)
	var model := scene.instantiate()
	model.name = "Model"
	model.scale = Vector3.ONE * STRUCTURE_SCALE
	container.add_child(model)

	# Capture zone ring — faction color if owned, neutral white if unowned
	var ring_col: Color
	if faction >= 0:
		ring_col = EraThemeResolver.get_faction_color(faction)
	else:
		ring_col = Color(0.8, 0.8, 0.8, 0.6)

	var cap_ring := MeshInstance3D.new()
	var torus    := TorusMesh.new()
	torus.outer_radius = CAP_OUTER_RADIUS
	torus.inner_radius = CAP_INNER_RADIUS
	cap_ring.mesh = torus
	var cap_mat  := StandardMaterial3D.new()
	cap_mat.albedo_color          = ring_col
	cap_mat.transparency          = BaseMaterial3D.TRANSPARENCY_ALPHA
	cap_mat.emission_enabled      = true
	cap_mat.emission              = ring_col
	cap_mat.emission_energy_multiplier = 0.5
	cap_ring.set_surface_override_material(0, cap_mat)
	cap_ring.position = Vector3(0.0, 2.0, 0.0)
	container.add_child(cap_ring)

	# HP / capture label
	if max_hp > 0.0:
		var label := Label3D.new()
		var hp_pct := int((hp / max_hp) * 100.0)
		if cap_prog > 0.01:
			label.text = "HP %d%%\ncap %d%%" % [hp_pct, int(cap_prog * 100.0)]
		else:
			label.text = "HP %d%%" % hp_pct
		label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		label.font_size  = 20
		label.modulate   = ring_col.lightened(0.2)
		label.position   = Vector3(0.0, 120.0, 0.0)
		container.add_child(label)


# ── Environment scatter ─────────────────────────────────────────────────────
# Maps gradient source property → environment categories from manifest.
# Each category gets one MultiMeshInstance3D for all instances across all sources.

const PROPERTY_CATEGORIES: Dictionary = {
	"obstacle_density": ["obstacle_small", "obstacle_medium", "obstacle_large"],
	# cover_density and sensor_interference use placeholder assets — skip until real GLBs exist
}

const BASE_DENSITY := 0.00015  # objects per world-unit² at intensity 1.0
const ASTEROID_SCALE_RANGE := [4.0, 12.0]  # min/max scale for environment objects


func _scatter_environment(sources: Array, map_seed: int) -> void:
	# Collect all instances per category
	var category_instances: Dictionary = {}  # category_name → Array of Transform3D

	for gs in sources:
		var prop: String = gs.get("property", "")
		var categories: Array = PROPERTY_CATEGORIES.get(prop, [])
		if categories.is_empty():
			continue

		var pos: Array = gs["pos"]
		var cx: float = float(pos[0])
		var cy: float = float(pos[1])
		var radius: float = float(gs.get("radius", 200))
		var intensity: float = float(gs.get("intensity", 0.5))

		var area: float = PI * radius * radius
		var count: int = int(area * BASE_DENSITY * intensity)
		if count <= 0:
			continue

		# Deterministic seed from map_seed + source position
		var rng := RandomNumberGenerator.new()
		rng.seed = map_seed + int(cx * 1000) + int(cy * 7919)

		for i in count:
			# Random point within circle (uniform distribution)
			var angle: float = rng.randf() * TAU
			var dist: float = radius * sqrt(rng.randf())
			var wx: float = cx + cos(angle) * dist
			var wy: float = cy + sin(angle) * dist

			# Pick a category from the available ones
			var cat: String = categories[rng.randi() % categories.size()]
			if not category_instances.has(cat):
				category_instances[cat] = []

			# Random scale and rotation
			var s: float = rng.randf_range(ASTEROID_SCALE_RANGE[0], ASTEROID_SCALE_RANGE[1])
			var rot: float = rng.randf() * TAU
			var basis := Basis(Vector3.UP, rot).scaled(Vector3(s, s, s))
			category_instances[cat].append(Transform3D(basis, Vector3(wx, 0.0, wy)))

	# Build one MultiMeshInstance3D per category
	for cat in category_instances:
		var transforms: Array = category_instances[cat]
		if transforms.is_empty():
			continue

		var scene: PackedScene = EraThemeResolver.get_environment_scene(cat)
		var mesh: Mesh = _extract_env_mesh(scene)

		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.instance_count = transforms.size()
		mm.mesh = mesh

		for i in transforms.size():
			mm.set_instance_transform(i, transforms[i])

		var mmi := MultiMeshInstance3D.new()
		mmi.name = "EnvScatter_%s" % cat
		mmi.multimesh = mm
		add_child(mmi)


func _extract_env_mesh(scene: PackedScene) -> Mesh:
	var instance := scene.instantiate()
	var mesh: Mesh = null
	if instance is MeshInstance3D:
		mesh = instance.mesh
	else:
		var meshes := instance.find_children("*", "MeshInstance3D", true, false)
		if meshes.size() > 0:
			mesh = (meshes[0] as MeshInstance3D).mesh
	instance.free()
	if mesh == null:
		var s := SphereMesh.new()
		s.radius = 1.0
		s.height = 2.0
		mesh = s
	return mesh

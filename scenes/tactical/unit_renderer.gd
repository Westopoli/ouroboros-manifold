## Renders all units via MultiMeshInstance3D batching.
## Grouped by (type, tier, faction) — one draw call per batch.
## See bible_combat.md "Unit Rendering — MultiMesh Batching" for design rationale.
## See also: scripts/tactical/visibility.gd — fog gate in _update_transforms()
extends Node3D

const MAX_INSTANCES_PER_BATCH := 1024

const LAYER_COLORS: Array[Color] = [
	Color.TRANSPARENT,
	Color(0.00, 1.00, 1.00),
	Color(1.00, 1.00, 0.00),
	Color(1.00, 0.55, 0.00),
	Color(0.75, 0.20, 1.00),
]

const SEL_OUTER := 66.0
const SEL_INNER := 60.0
const RING_OUTER := 50.0
const RING_INNER := 44.0
const PREF_OUTER := 56.0
const PREF_INNER := 53.0

const _V_OFFSETS: Array[Vector2] = [
	Vector2(0.0, 0.0),
	Vector2(-60.0, 60.0),
	Vector2(60.0, 60.0),
	Vector2(0.0, 110.0),
]

# Per batch: one MultiMeshInstance3D + metadata
# Key: "type_tier_faction" e.g. "vanguard_1_0"
var _batches: Dictionary = {}

# uid → batch_key for quick lookup on removal
var _uid_to_batch_key: Dictionary = {}

# Selection ring nodes — spawned on demand for selected units only
var _sel_rings: Dictionary = {}  # uid → MeshInstance3D

# Layer ring batches — one MultiMeshInstance3D per layer color
var _layer_batches: Dictionary = {}  # layer(int) → MultiMeshInstance3D

# Preference ring batches — one per preferred layer, thinner outline style
var _pref_batches: Dictionary = {}  # layer(int) → MultiMeshInstance3D

# Shared torus mesh for layer rings (all use the same geometry, different materials)
var _layer_ring_mesh: TorusMesh
var _sel_ring_mesh: TorusMesh
var _pref_ring_mesh: TorusMesh

@onready var _input_router = $"../InputRouter"


func _ready() -> void:
	_layer_ring_mesh = TorusMesh.new()
	_layer_ring_mesh.outer_radius = RING_OUTER
	_layer_ring_mesh.inner_radius = RING_INNER

	_sel_ring_mesh = TorusMesh.new()
	_sel_ring_mesh.outer_radius = SEL_OUTER
	_sel_ring_mesh.inner_radius = SEL_INNER

	_pref_ring_mesh = TorusMesh.new()
	_pref_ring_mesh.outer_radius = PREF_OUTER
	_pref_ring_mesh.inner_radius = PREF_INNER

	TacticalBridge.snapshot_received.connect(_on_snapshot)
	TacticalBridge.tick_delta_received.connect(_on_delta)

var _facing_log_frames: int = 0

func _process(_delta: float) -> void:
	_update_transforms()
	_update_selection_rings()
	_update_layer_rings()
	_update_preference_rings()

	_facing_log_frames += 1
	if _facing_log_frames % 180 == 0:
		var sample := ""
		for uid in range(mini(TacticalBridge.unit_count, 4)):
			if TacticalBridge.display_alive[uid] == 1:
				sample += "uid=%d facing=%.3f  " % [uid, TacticalBridge.display_facing[uid]]
		if sample != "":
			print("[FACING-GD] ", sample)


func _on_snapshot(_snap: Dictionary) -> void:
	_full_rebuild()


func _on_delta(delta: Dictionary) -> void:
	var removed: Array = delta.get("units_removed", [])
	var added: Array = delta.get("units_added", [])
	if removed.is_empty() and added.is_empty():
		return
	for uid in removed:
		_remove_unit(int(uid))
	for u in added:
		_add_unit(int(u["uid"]))
	_rebuild_all_multimeshes()


func _full_rebuild() -> void:
	# Clear everything
	for key in _batches:
		_batches[key].mmi.queue_free()
	_batches.clear()
	_uid_to_batch_key.clear()
	for uid in _sel_rings:
		_sel_rings[uid].queue_free()
	_sel_rings.clear()
	for layer in _layer_batches:
		_layer_batches[layer].queue_free()
	_layer_batches.clear()
	for layer in _pref_batches:
		_pref_batches[layer].queue_free()
	_pref_batches.clear()

	# Add all living units
	for uid: int in TacticalBridge.units:
		_add_unit(uid)
	_rebuild_all_multimeshes()


func _add_unit(uid: int) -> void:
	var unit: Dictionary = TacticalBridge.units.get(uid, {})
	if unit.is_empty():
		return
	var unit_type: String = unit.get("type", "").to_lower()
	var tier: int = unit.get("tier", 1)
	var faction: int = unit.get("faction", 0)
	var batch_key := "%s_%d_%d" % [unit_type, tier, faction]

	if not _batches.has(batch_key):
		_create_batch(batch_key, unit_type, tier, faction)

	var batch: Dictionary = _batches[batch_key]
	var squad_count: int = EraThemeResolver.get_squad_count(unit_type)
	var vscale: float = EraThemeResolver.get_unit_visual_scale(unit_type)
	var foff: float = EraThemeResolver.get_unit_facing_offset(unit_type)

	for i in squad_count:
		var offset := _V_OFFSETS[i] if i < _V_OFFSETS.size() else Vector2.ZERO
		batch.entries.append({"uid": uid, "squad_idx": i, "offset": offset, "vscale": vscale, "facing_offset": foff})

	_uid_to_batch_key[uid] = batch_key


func _remove_unit(uid: int) -> void:
	var batch_key: String = _uid_to_batch_key.get(uid, "")
	if batch_key == "":
		return
	var batch: Dictionary = _batches.get(batch_key, {})
	if batch.is_empty():
		return
	# Remove all entries for this uid
	var entries: Array = batch.entries
	var i := entries.size() - 1
	while i >= 0:
		if entries[i].uid == uid:
			entries.remove_at(i)
		i -= 1
	_uid_to_batch_key.erase(uid)
	# Clean up selection ring if present
	if _sel_rings.has(uid):
		_sel_rings[uid].queue_free()
		_sel_rings.erase(uid)


func _create_batch(batch_key: String, unit_type: String, tier: int, faction: int) -> void:
	var scene: PackedScene = EraThemeResolver.get_unit_scene(unit_type, tier)
	var mesh: Mesh = _extract_mesh_with_faction(scene, faction, tier)

	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	mm.instance_count = MAX_INSTANCES_PER_BATCH
	mm.visible_instance_count = 0
	mm.mesh = mesh

	var mmi := MultiMeshInstance3D.new()
	mmi.name = "Batch_%s" % batch_key
	mmi.multimesh = mm
	add_child(mmi)

	_batches[batch_key] = {
		"mmi": mmi,
		"entries": [],
	}


func _extract_mesh_with_faction(scene: PackedScene, faction: int, tier: int) -> Mesh:
	var instance := scene.instantiate()
	var source_mi: MeshInstance3D = null
	if instance is MeshInstance3D:
		source_mi = instance
	else:
		var meshes := instance.find_children("*", "MeshInstance3D", true, false)
		if meshes.size() > 0:
			source_mi = meshes[0] as MeshInstance3D

	if source_mi == null or source_mi.mesh == null:
		instance.free()
		var s := SphereMesh.new()
		s.radius = 1.0
		s.height = 2.0
		var mat := StandardMaterial3D.new()
		mat.albedo_color = EraThemeResolver.get_faction_color(faction)
		s.surface_set_material(0, mat)
		return s

	var mesh: Mesh = source_mi.mesh
	var arr_mesh := mesh as ArrayMesh
	if arr_mesh == null:
		# Non-ArrayMesh (SphereMesh, BoxMesh, etc.) — apply faction color directly
		var faction_color := EraThemeResolver.get_faction_color(faction)
		var mat := _make_faction_mat(faction_color, tier)
		mesh = mesh.duplicate()
		mesh.surface_set_material(0, mat)
		instance.free()
		return mesh

	# ArrayMesh — duplicate and apply faction color to the "faction_color" surface,
	# preserve all other surface materials
	var dup_mesh := arr_mesh.duplicate() as ArrayMesh
	var faction_color := EraThemeResolver.get_faction_color(faction)

	for s in dup_mesh.get_surface_count():
		if dup_mesh.surface_get_name(s) == "faction_color":
			dup_mesh.surface_set_material(s, _make_faction_mat(faction_color, tier))
		elif source_mi.get_surface_override_material(s) != null:
			dup_mesh.surface_set_material(s, source_mi.get_surface_override_material(s))

	instance.free()
	return dup_mesh


func _make_faction_mat(faction_color: Color, tier: int) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = faction_color
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	var treatment := EraThemeResolver.get_faction_color_mode(tier)
	match treatment:
		"metallic":
			mat.metallic = 0.7
			mat.roughness = 0.35
		"emissive":
			mat.emission_enabled = true
			mat.emission = faction_color
			mat.emission_energy_multiplier = 2.0
		_:
			mat.metallic = 0.0
			mat.roughness = 0.8
	return mat


func _rebuild_all_multimeshes() -> void:
	for key in _batches:
		var batch: Dictionary = _batches[key]
		batch.mmi.multimesh.visible_instance_count = batch.entries.size()


func _update_transforms() -> void:
	var focus_layer: int = _input_router.active_layer
	var dim_color := Color(1.0, 1.0, 1.0, EraConfig.INACTIVE_LAYER_ALPHA)
	var full_color := Color(1.0, 1.0, 1.0, 1.0)
	var hidden_color := Color(1.0, 1.0, 1.0, 0.0)

	for key in _batches:
		var batch: Dictionary = _batches[key]
		var entries: Array = batch.entries
		var mm: MultiMesh = batch.mmi.multimesh
		var write_idx := 0

		for entry in entries:
			var uid: int = entry.uid
			if uid >= TacticalBridge.unit_count or TacticalBridge.display_alive[uid] == 0:
				mm.set_instance_transform(write_idx, Transform3D(Basis(), Vector3(0.0, -99999.0, 0.0)))
				mm.set_instance_color(write_idx, hidden_color)
				write_idx += 1
				continue
			# See also: scripts/tactical/visibility.gd — fog gate
			if not Visibility.is_unit_visible_to_player(uid):
				mm.set_instance_transform(write_idx, Transform3D(Basis(), Vector3(0.0, -99999.0, 0.0)))
				mm.set_instance_color(write_idx, hidden_color)
				write_idx += 1
				continue

			var px: float = TacticalBridge.display_x[uid]
			var py: float = TacticalBridge.display_y[uid]
			var unit: Dictionary = TacticalBridge.units.get(uid, {})
			var layer: int = unit.get("layer", 0)
			var y: float = float(layer) * EraConfig.LAYER_HEIGHT
			var offset: Vector2 = entry.offset
			var vscale: float = entry.vscale

			var facing: float = -TacticalBridge.display_facing[uid] - PI / 2.0 + entry.facing_offset
			var basis := Basis(Vector3.UP, facing).scaled(Vector3(vscale, vscale, vscale))
			var origin := Vector3(px + offset.x, y, py + offset.y)
			mm.set_instance_transform(write_idx, Transform3D(basis, origin))
			mm.set_instance_color(write_idx, full_color if layer == focus_layer else dim_color)
			write_idx += 1


func _update_selection_rings() -> void:
	var selected: Array[int] = _input_router.selected_uids

	# Remove rings for deselected units
	for uid in _sel_rings.keys():
		if uid not in selected:
			_sel_rings[uid].queue_free()
			_sel_rings.erase(uid)

	# Add rings for newly selected units
	for uid in selected:
		if _sel_rings.has(uid):
			# Update position
			var ring: MeshInstance3D = _sel_rings[uid]
			if uid < TacticalBridge.unit_count and TacticalBridge.display_alive[uid] == 1:
				var unit: Dictionary = TacticalBridge.units.get(uid, {})
				var layer: int = unit.get("layer", 0)
				ring.position = Vector3(
					TacticalBridge.display_x[uid],
					float(layer) * EraConfig.LAYER_HEIGHT + 2.0,
					TacticalBridge.display_y[uid])
				ring.visible = true
			else:
				ring.visible = false
		else:
			# Spawn new ring — dimmer, faction-colored per Stage 12.5H
			var ring := MeshInstance3D.new()
			ring.mesh = _sel_ring_mesh
			var mat := StandardMaterial3D.new()
			var unit_faction: int = TacticalBridge.units.get(uid, {}).get("faction", 0)
			var fc: Color = EraThemeResolver.get_faction_color(unit_faction)
			mat.albedo_color = Color(fc.r, fc.g, fc.b, 0.35)
			mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			mat.emission_enabled = true
			mat.emission = fc
			mat.emission_energy_multiplier = 0.3
			ring.set_surface_override_material(0, mat)
			add_child(ring)
			_sel_rings[uid] = ring
			# Set initial position
			if uid < TacticalBridge.unit_count and TacticalBridge.display_alive[uid] == 1:
				var unit: Dictionary = TacticalBridge.units.get(uid, {})
				var layer: int = unit.get("layer", 0)
				ring.position = Vector3(
					TacticalBridge.display_x[uid],
					float(layer) * EraConfig.LAYER_HEIGHT + 2.0,
					TacticalBridge.display_y[uid])


func _update_layer_rings() -> void:
	# Count units per layer
	var layer_entries: Dictionary = {}  # layer → Array of {uid, px, py, y}
	for uid in range(TacticalBridge.unit_count):
		if TacticalBridge.display_alive[uid] == 0:
			continue
		if not Visibility.is_unit_visible_to_player(uid):
			continue
		var unit: Dictionary = TacticalBridge.units.get(uid, {})
		var layer: int = unit.get("layer", 0)
		if layer <= 0 or layer >= LAYER_COLORS.size():
			continue
		if not layer_entries.has(layer):
			layer_entries[layer] = []
		layer_entries[layer].append(uid)

	# Ensure MultiMesh exists per active layer
	for layer in layer_entries:
		if not _layer_batches.has(layer):
			var mm := MultiMesh.new()
			mm.transform_format = MultiMesh.TRANSFORM_3D
			mm.instance_count = MAX_INSTANCES_PER_BATCH
			mm.visible_instance_count = 0
			mm.mesh = _layer_ring_mesh
			var mmi := MultiMeshInstance3D.new()
			mmi.name = "LayerRings_%d" % layer
			mmi.multimesh = mm
			var mat := StandardMaterial3D.new()
			mat.albedo_color = LAYER_COLORS[layer]
			mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			mat.emission_enabled = true
			mat.emission = LAYER_COLORS[layer]
			mat.emission_energy_multiplier = 0.6
			mmi.material_override = mat
			add_child(mmi)
			_layer_batches[layer] = mmi

	# Update transforms + layer-focus dimming on rings
	var focus_layer: int = _input_router.active_layer
	for layer in _layer_batches:
		var mmi: MultiMeshInstance3D = _layer_batches[layer]
		var uids: Array = layer_entries.get(layer, [])
		mmi.multimesh.visible_instance_count = uids.size()
		var ring_alpha: float = 1.0 if layer == focus_layer else EraConfig.INACTIVE_LAYER_ALPHA
		(mmi.material_override as StandardMaterial3D).albedo_color.a = ring_alpha
		for i in uids.size():
			var uid: int = uids[i]
			var unit: Dictionary = TacticalBridge.units.get(uid, {})
			var ly: float = float(layer) * EraConfig.LAYER_HEIGHT + 2.0
			var xform := Transform3D(Basis(), Vector3(TacticalBridge.display_x[uid], ly, TacticalBridge.display_y[uid]))
			mmi.multimesh.set_instance_transform(i, xform)

	# Hide layers with no units
	for layer in _layer_batches:
		if not layer_entries.has(layer):
			(_layer_batches[layer] as MultiMeshInstance3D).multimesh.visible_instance_count = 0


func _update_preference_rings() -> void:
	# Collect units whose preferred_layer differs from current layer
	var pref_entries: Dictionary = {}  # preferred_layer → Array of uid
	for uid in range(TacticalBridge.unit_count):
		if TacticalBridge.display_alive[uid] == 0:
			continue
		if not Visibility.is_unit_visible_to_player(uid):
			continue
		var unit: Dictionary = TacticalBridge.units.get(uid, {})
		var pref: int = int(unit.get("preferred_layer", -1))
		if pref < 1 or pref >= LAYER_COLORS.size():
			continue
		var cur_layer: int = unit.get("layer", 0)
		if pref == cur_layer:
			continue
		if not pref_entries.has(pref):
			pref_entries[pref] = []
		pref_entries[pref].append(uid)

	# Ensure MultiMesh exists per preferred layer
	for pref_layer in pref_entries:
		if not _pref_batches.has(pref_layer):
			var mm := MultiMesh.new()
			mm.transform_format = MultiMesh.TRANSFORM_3D
			mm.instance_count = MAX_INSTANCES_PER_BATCH
			mm.visible_instance_count = 0
			mm.mesh = _pref_ring_mesh
			var mmi := MultiMeshInstance3D.new()
			mmi.name = "PrefRings_%d" % pref_layer
			mmi.multimesh = mm
			var mat := StandardMaterial3D.new()
			var col: Color = LAYER_COLORS[pref_layer]
			mat.albedo_color = Color(col.r, col.g, col.b, 0.5)
			mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			mat.emission_enabled = true
			mat.emission = col
			mat.emission_energy_multiplier = 0.3
			mmi.material_override = mat
			add_child(mmi)
			_pref_batches[pref_layer] = mmi

	# Update transforms — preference ring sits at unit's current position
	for pref_layer in _pref_batches:
		var mmi: MultiMeshInstance3D = _pref_batches[pref_layer]
		var uids: Array = pref_entries.get(pref_layer, [])
		mmi.multimesh.visible_instance_count = uids.size()
		for i in uids.size():
			var uid: int = uids[i]
			var unit: Dictionary = TacticalBridge.units.get(uid, {})
			var cur_layer: int = unit.get("layer", 0)
			var ly: float = float(cur_layer) * EraConfig.LAYER_HEIGHT + 2.5
			var xform := Transform3D(Basis(), Vector3(TacticalBridge.display_x[uid], ly, TacticalBridge.display_y[uid]))
			mmi.multimesh.set_instance_transform(i, xform)

	# Hide unused
	for pref_layer in _pref_batches:
		if not pref_entries.has(pref_layer):
			(_pref_batches[pref_layer] as MultiMeshInstance3D).multimesh.visible_instance_count = 0

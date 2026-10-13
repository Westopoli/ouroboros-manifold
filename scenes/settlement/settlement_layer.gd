extends Node3D
class_name SettlementLayer

## The settlement layer (visible-game lane E1, S-193): one box per sim lot, sized by stage, cliff and a per-lot factor, jittered and
## yawed (contour-aligned on a slope), tinted by owner, eased by time between stages, plus a hidden route mesh.
## The skeleton's BOX_FOOTPRINT_WU and BOX_HEIGHT_WU liberty (2026-10-10) is replaced by the mockup numbers in settlement_look.gd.
## See also: settlement_look.gd, settlement_streets.gd, spec Rev 12d (docs/northstar/plans/2026-10-07-visible-game-spec.md),
## tests/test_vg_e_e1k.gd.

const GroundPick := preload("res://scenes/ground3d/ground_pick.gd")
const StructuresLayer := preload("res://scenes/tactical_c/structures_layer.gd")
const Look := preload("res://scenes/settlement/settlement_look.gd")
const Streets := preload("res://scenes/settlement/settlement_streets.gd")

var local_faction := 0
var _terrain: Dictionary = {}
var _has_terrain := false
var _lots: Array = []
var _has_frame := false
var _loaded := false # the first set_frame after set_terrain snaps (spec :298, GAP 5)
var _mmi: MultiMeshInstance3D
var _streets_mi: MeshInstance3D
var _streets_sig := PackedFloat64Array()
var _streets_sig_ok := false
var _drawn: Array = []
var _rec: Dictionary = {} # lot id -> {from: [h, fw, Color], to: [h, fw, Color], t: float seconds}
var _geo: Dictionary = {} # lot id -> {pos: Vector3 (ground point), jit: Vector2 cells, yaw: float}


func _ready() -> void:
	name = "SettlementLayer"


func set_terrain(t: Dictionary) -> void:
	_terrain = t
	_has_terrain = true
	_loaded = false
	_streets_sig_ok = false
	_sync()


func set_frame(frame: Dictionary) -> void:
	_lots = frame.get("lots", [])
	_has_frame = true
	_sync()


func lots_drawn() -> Array:
	return _drawn.duplicate(true)


func _owner_color(owner_id: int) -> Color:
	if owner_id < 0:
		return StructuresLayer.NEUTRAL_COLOR
	return StructuresLayer.OWN_COLOR if owner_id == local_faction else StructuresLayer.ENEMY_COLOR


func _process(delta: float) -> void:
	if _mmi == null or _rec.is_empty():
		return
	var moving := false
	for id in _rec:
		var r: Dictionary = _rec[id]
		if r["t"] < Look.RISE_S:
			r["t"] = float(r["t"]) + delta
			moving = true
	if moving:
		_write_all()


func _eased(r: Dictionary) -> Array:
	var e := clampf(float(r["t"]) / Look.RISE_S, 0.0, 1.0)
	var f: Array = r["from"]
	var to: Array = r["to"]
	return [lerpf(f[0], to[0], e), lerpf(f[1], to[1], e), (f[2] as Color).lerp(to[2], e)]


# Mockup vis() easing (S:320-327): lerp height, footprint and colour from the value at the moment of the change.
func _write_all() -> void:
	var mm := _mmi.multimesh
	for i in _drawn.size():
		var id: int = _drawn[i]["id"]
		_write(mm, i, _geo[id], _eased(_rec[id]))


# N8: basis = Basis(UP, yaw) * scale(footprint, height, footprint * 0.85); centre y = ground + height / 2 - 0.12 unit (M:251-252).
func _write(mm: MultiMesh, i: int, g: Dictionary, v: Array) -> void:
	var h_wu: float = float(v[0]) * Look.CELL_WU
	var fw_wu: float = float(v[1]) * Look.CELL_WU
	var basis := Basis(Vector3.UP, float(g["yaw"])) * Basis.from_scale(Vector3(fw_wu, h_wu, fw_wu * Look.DEPTH_RATIO))
	var p: Vector3 = g["pos"]
	var jit: Vector2 = g["jit"]
	var origin := Vector3(p.x + jit.x * Look.CELL_WU, p.y + h_wu * 0.5 - Look.SINK_UNITS * Look.CELL_WU, p.z + jit.y * Look.CELL_WU)
	mm.set_instance_transform(i, Transform3D(basis, origin))
	mm.set_instance_color(i, v[2])


func _sync() -> void:
	if not (_has_terrain and _has_frame):
		return
	var sorted := _lots.duplicate()
	sorted.sort_custom(func(a, b): return int(a["id"]) < int(b["id"]))
	if _mmi == null:
		_mmi = MultiMeshInstance3D.new()
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.use_colors = true
		var box := BoxMesh.new()
		box.size = Vector3.ONE
		var mat := StandardMaterial3D.new()
		mat.vertex_color_use_as_albedo = true
		box.material = mat
		mm.mesh = box
		_mmi.multimesh = mm
		add_child(_mmi)
	var mm := _mmi.multimesh
	if mm.instance_count != sorted.size():
		mm.instance_count = sorted.size()
	var snap := not _loaded
	_loaded = true
	var old_rec := _rec
	_rec = {}
	_geo = {}
	_drawn = []
	for i in sorted.size():
		var l: Dictionary = sorted[i]
		var id := int(l["id"])
		var x := float(l.get("x", 0.0))
		var y := float(l.get("y", 0.0))
		var stage := int(l.get("stage", 0))
		var gx := clampi(int(floor(x / Look.CELL_WU)), 0, int(_terrain["cells_w"]) - 1)
		var gy := clampi(int(floor(y / Look.CELL_WU)), 0, int(_terrain["cells_h"]) - 1)
		var cliff := Look.slope_at(_terrain, gx, gy) > Look.CLIFF_SLOPE
		var drawn_stage := mini(stage, Look.CLIFF_MAX_STAGE) if cliff else stage
		var key := Look.lot_key(_terrain, l)
		var row := Look.vis(drawn_stage, cliff, key)
		var owner_id := int(l.get("owner", -1))
		var col: Color = Look.RUBBLE_COLOR if drawn_stage == 0 else _owner_color(owner_id)
		var to := [float(row[0]), float(row[1]), col]
		var rec: Dictionary
		if snap:
			rec = {"from": to, "to": to, "t": Look.RISE_S}
		elif old_rec.has(id):
			rec = old_rec[id]
			if not _same(rec["to"], to):
				rec = {"from": _eased(rec), "to": to, "t": 0.0}
		else:
			# A lot that first appears after the load frame rises from a zero-scale box (the spec names no start; mockup vis() eases from the current value).
			rec = {"from": [0.0, 0.0, col], "to": to, "t": 0.0}
		_rec[id] = rec
		_geo[id] = {"pos": GroundPick.world_to_3d(_terrain, x, y), "jit": Look.jitter(key), "yaw": Look.yaw(_terrain, gx, gy, key)}
		_write(mm, i, _geo[id], _eased(rec))
		_drawn.append({"id": id, "x": x, "y": y, "stage": drawn_stage, "building": int(l.get("building", 0)), "owner": owner_id, "cliff": cliff})
	_sync_streets()


func _same(a: Array, b: Array) -> bool:
	return is_equal_approx(a[0], b[0]) and is_equal_approx(a[1], b[1]) and (a[2] as Color).is_equal_approx(b[2])


# GAP 4: the route mesh exists and is hidden by default; it is added only when it has a surface.
func _sync_streets() -> void:
	# Streets.ribbons is O(n^2) in the stage 2+ lots; rebuild only when the lots it reads changed.
	var sig := PackedFloat64Array()
	for d in _drawn:
		if int(d["stage"]) >= Streets.MIN_STAGE:
			sig.append_array([float(d["id"]), float(d["x"]), float(d["y"])])
	if _streets_sig_ok and sig == _streets_sig:
		return
	_streets_sig = sig
	_streets_sig_ok = true
	var mesh := Streets.ribbons(_drawn, _terrain)
	if mesh.get_surface_count() == 0:
		if _streets_mi != null:
			_streets_mi.mesh = null
		return
	if _streets_mi == null:
		_streets_mi = MeshInstance3D.new()
		_streets_mi.name = "SettlementStreets"
		_streets_mi.visible = false
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(1.0, 0.9, 0.2) # yellow route, as the mockup ships it (GAP 4)
		_streets_mi.material_override = mat
		add_child(_streets_mi)
	_streets_mi.mesh = mesh

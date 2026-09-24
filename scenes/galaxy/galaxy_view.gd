extends Node3D

# Piece C2 (tests/test_galaxy_view.gd, docs/northstar/plans/push/specs/C2.md):
# draws the C-snapshot galaxy from a raw snapshot dict (same shape
# autoload/c_bridge.gd parses) -- one point per region, owner colour,
# pan/zoom/click bands -- per docs/bible/epics/
# E-16-client-camera-hud-and-world-view.md S-106/S-107. Positions are never
# transmitted (C5 rule, docs/architecture.md), so this scene lays systems
# out itself from a seed (see galaxy_gen.gd). Mirrors the proven pattern at
# scenes/mockups/galaxy/{galaxy_gen,galaxy_view,orbit_camera}.gd, adapted to
# real snapshot-driven region/edge/owner data and to this piece's own
# qa_state() key names and plant ids.

const GalaxyGen := preload("res://scenes/galaxy/galaxy_gen.gd")
const CBridge := preload("res://autoload/c_bridge.gd")
const SimSession := preload("res://autoload/sim_session.gd")

const PLANTS := ["seed-ignored", "owner-colour-flat", "edges-2d-overlay",
	"pick-radius-zero", "bands-frozen", "conquest-no-recolour"]

const DEFAULT_SEED := 1
const LIVE_SNAPSHOT_TIMEOUT_MSEC := 8000
const DEFAULT_DISTANCE := 180.0
const PICK_RADIUS_PX := 14.0
const BAND_SPLIT_LOW := 32.5
const BAND_SPLIT_HIGH := 70.0
const FLAT_COLOUR := Color(1.0, 1.0, 1.0, 1.0)
const FILAMENT_RADIUS := 0.5
const POINT_RADIUS := 1.2
const OWNER_SAT := 0.65
const OWNER_VAL := 0.85
const OWNER_ALPHA := 1.0
const GOLDEN_ANGLE := 0.6180339887498949

var _regions: Array = []
var _edges: Array = []
var _positions: Dictionary = {}
var _region_colours: Dictionary = {}
var _owner_colours_cache: Dictionary = {}
var _seed: int = DEFAULT_SEED
var _hash: int = 0
var _plants: Dictionary = {}
var _frozen_band: String = ""

var _gen := GalaxyGen.new()
var _bridge = null
var _bridge_dirty := false

@onready var _world: Node3D = $World
@onready var _points: MultiMeshInstance3D = $World/Points
@onready var _filaments: Node3D = $World/Filaments
@onready var _camera_rig := $OrbitCamera


func _ready() -> void:
	_camera_rig.set_view(DEFAULT_DISTANCE, Vector3.ZERO)
	_load_live_snapshot()
	var mission_btn := get_node_or_null("UI/Mission")
	if mission_btn:
		mission_btn.pressed.connect(func(): SceneRouter.go_to("mission_briefing"))


# Self-loading pattern (docs/northstar/plans/push/specs/C8-M3.md
# "Self-loading pattern"): SceneRouter._swap_scene never passes data into a
# scene unless it has setup(), so galaxy_view joins the run's shared pipe
# session (autoload/sim_session.gd) here (docs/architecture.md "persistent client session (v1.1)"),
# waits for the first snapshot, and from then on redraws whenever the
# session applies a frame (set_snapshot re-renders, so a conquest recolours,
# R-106-02). On failure (binary missing, pipe error) the scene stays exactly
# as it is pre-set_snapshot -- qa_state() already handles empty
# _regions/_edges gracefully (proven by tests/test_galaxy_view.gd's own
# fallback-snapshot path). The session outlives this scene: the world the
# galaxy stepped is the one the other scenes read.
func _load_live_snapshot() -> void:
	var seed_str := _arg_value(OS.get_cmdline_user_args(), "--seed")
	var seed := int(seed_str) if seed_str != "" else DEFAULT_SEED
	_bridge = SimSession.bridge()
	if not _bridge.ensure_session(seed, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES):
		push_error("galaxy_view: live snapshot failed: %s" % _bridge.last_error())
		_bridge = null
		return
	_bridge.snapshot_changed.connect(_on_bridge_changed)
	set_snapshot(_bridge.snapshot())


func _on_bridge_changed(_tick) -> void:
	_bridge_dirty = true


func _process(_delta: float) -> void:
	if _bridge == null:
		return
	_bridge.pump()
	if _bridge_dirty:
		_bridge_dirty = false
		set_snapshot(_bridge.snapshot())


func _exit_tree() -> void:
	if _bridge != null and _bridge.snapshot_changed.is_connected(_on_bridge_changed):
		_bridge.snapshot_changed.disconnect(_on_bridge_changed)


# Advances the live sim n ticks; the redraw follows as the deltas arrive.
# The daemon's step verb reaches this the way its plant verb reaches qa_plant.
func qa_step(n: int) -> void:
	if _bridge != null:
		_bridge.step(n)


func _arg_value(args: PackedStringArray, flag: String) -> String:
	var idx := args.find(flag)
	if idx == -1 or idx + 1 >= args.size():
		return ""
	return args[idx + 1]


func set_snapshot(snapshot: Dictionary) -> void:
	_regions = snapshot.get("regions", [])
	_edges = snapshot.get("edges", [])
	_relayout()
	_render()


func qa_state() -> Dictionary:
	var owners := {}
	for r in _regions:
		owners[int(r.get("i", -1))] = int(r.get("owner", -1))

	var edge_counts := {}
	for e in _edges:
		var t := int(e.get("t", 0))
		edge_counts[t] = int(edge_counts.get(t, 0)) + 1

	var systems_px := {}
	for i in _positions:
		var p: Vector2 = _camera_rig.project(_positions[i])
		systems_px[i] = [p.x, p.y]

	var region_colours := {}
	for i in owners:
		var c: Color = _region_colours.get(i, FLAT_COLOUR)
		region_colours[i] = [c.r, c.g, c.b, c.a]

	var owner_colours := {}
	for owner in _owner_colours_cache:
		var c: Color = _owner_colours_cache[owner]
		owner_colours[owner] = [c.r, c.g, c.b, c.a]

	var distance: float = _camera_rig.get_distance()
	var band: String = _frozen_band if _plants.get("bands-frozen", false) else _band_for(distance)

	return {
		"system_count": _regions.size(),
		"owners": owners,
		"edge_counts": edge_counts,
		"systems_px": systems_px,
		"region_colours": region_colours,
		"owner_colours": owner_colours,
		"band": band,
		"distance": distance,
		"pick_radius_px": 0.0 if _plants.get("pick-radius-zero", false) else PICK_RADIUS_PX,
		"edges_3d": not bool(_plants.get("edges-2d-overlay", false)),
		"hash": _hash,
		"tick": int(_bridge.snapshot().get("tick", 0)) if _bridge != null else 0,
	}


func qa_plant(id: String) -> bool:
	if not PLANTS.has(id):
		return false
	_plants[id] = true
	if id == "bands-frozen":
		_frozen_band = _band_for(_camera_rig.get_distance())
	elif id == "edges-2d-overlay":
		_render_filaments()
	elif id == "owner-colour-flat":
		_recompute_region_colours()
	return true


func qa_seed(n: int) -> void:
	if _plants.get("seed-ignored", false):
		return
	_seed = n
	_relayout()


func qa_camera(distance: float, target_system_id: int) -> void:
	var target: Vector3 = _camera_rig.get_target()
	if target_system_id != -1 and _positions.has(target_system_id):
		target = _positions[target_system_id]
	_camera_rig.set_view(distance, target)


func _band_for(distance: float) -> String:
	if distance >= BAND_SPLIT_HIGH:
		return "Overview"
	elif distance >= BAND_SPLIT_LOW:
		return "Regional"
	return "Local"


func _relayout() -> void:
	var ids := []
	for r in _regions:
		ids.append(int(r.get("i", -1)))
	_positions = _gen.layout(ids, _seed)
	_hash = _compute_hash(ids)


func _compute_hash(ids: Array) -> int:
	var sorted_ids: Array = ids.duplicate()
	sorted_ids.sort()
	var h: int = 1469598103
	for id in sorted_ids:
		var p: Vector3 = _positions.get(id, Vector3.ZERO)
		h = _mix(h, id)
		h = _mix(h, int(round(p.x * 100.0)))
		h = _mix(h, int(round(p.y * 100.0)))
		h = _mix(h, int(round(p.z * 100.0)))
	h = _mix(h, _seed)
	return h


func _mix(h: int, v: int) -> int:
	return (h * 1099511628211) ^ v


func _render() -> void:
	_grow_owner_colours()
	if not _plants.get("conquest-no-recolour", false):
		_recompute_region_colours()
	_render_filaments()
	_render_points()


func _grow_owner_colours() -> void:
	for r in _regions:
		var owner := int(r.get("owner", -1))
		if not _owner_colours_cache.has(owner):
			_owner_colours_cache[owner] = _colour_for_owner(owner)


# Same hue/sat/val shape as autoload/faction_palette.gd:29-38's hue_for
# (owner id -> a hue via Color.from_hsv), but golden-angle-stepped instead
# of faction_palette's str(id).hash() % 360: owner ids here are small
# sequential ints (-1..N), and String.hash() on adjacent small-int strings
# is nearly linear (measured: "0".hash()=177621, "1".hash()=177622 -> hues
# 141/142 out of 360, well inside the test's 0.01 colour-equality
# tolerance). scenes/mockups/galaxy/galaxy_gen.gd:193-204 hit and documented
# this exact clustering for its own small sequential faction ids and fixed
# it the same way. No fixed formula is fenced here, only self-consistency
# (region_colours[i] == owner_colours[owner_of(i)]), so this satisfies the
# contract while actually giving distinct owners distinct colours.
func _colour_for_owner(owner: int) -> Color:
	var hue := fposmod(float(owner) * GOLDEN_ANGLE, 1.0)
	return Color.from_hsv(hue, OWNER_SAT, OWNER_VAL, OWNER_ALPHA)


# Clean path: region_colours[i] = owner_colours[owner_of(i)]. Fault
# owner-colour-flat mirrors a realistic "wrong variable" render bug -- every
# region reports the CURRENT FIRST region's owner colour instead of its own,
# so it still tracks real data (collapses to one colour, but that colour
# moves when the anchor region's owner changes) rather than a colour frozen
# for the rest of the process.
func _recompute_region_colours() -> void:
	_region_colours.clear()
	var flat := bool(_plants.get("owner-colour-flat", false))
	var anchor_colour := FLAT_COLOUR
	if flat and _regions.size() > 0:
		var anchor_owner := int(_regions[0].get("owner", -1))
		anchor_colour = _owner_colours_cache.get(anchor_owner, _colour_for_owner(anchor_owner))
	for r in _regions:
		var i := int(r.get("i", -1))
		if flat:
			_region_colours[i] = anchor_colour
		else:
			var owner := int(r.get("owner", -1))
			_region_colours[i] = _owner_colours_cache.get(owner, _colour_for_owner(owner))


func _render_filaments() -> void:
	for child in _filaments.get_children():
		child.free()
	if _plants.get("edges-2d-overlay", false):
		return
	for e in _edges:
		var a := int(e.get("a", -1))
		var b := int(e.get("b", -1))
		if not (_positions.has(a) and _positions.has(b)):
			continue
		_filaments.add_child(_build_tube(_positions[a], _positions[b]))


func _build_tube(from_pos: Vector3, to_pos: Vector3) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var mesh := CylinderMesh.new()
	mesh.top_radius = FILAMENT_RADIUS
	mesh.bottom_radius = FILAMENT_RADIUS
	mesh.height = maxf(from_pos.distance_to(to_pos), 0.001)
	mi.mesh = mesh
	var dir := to_pos - from_pos
	var basis := Basis()
	if dir.length_squared() > 0.0001:
		basis = Basis(Quaternion(Vector3.UP, dir.normalized()))
	mi.transform = Transform3D(basis, (from_pos + to_pos) * 0.5)
	return mi


func _render_points() -> void:
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	var sphere := SphereMesh.new()
	sphere.radius = POINT_RADIUS
	sphere.height = POINT_RADIUS * 2.0
	mm.mesh = sphere
	var ids := _positions.keys()
	mm.instance_count = ids.size()
	for idx in range(ids.size()):
		var i = ids[idx]
		mm.set_instance_transform(idx, Transform3D(Basis(), _positions[i]))
		mm.set_instance_color(idx, _region_colours.get(i, FLAT_COLOUR))
	_points.multimesh = mm

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
const GalaxyAdapter := preload("res://scenes/galaxy/galaxy_adapter.gd")
const ConstellationRenderer := preload("res://scenes/galaxy/legacy_constellation_renderer.gd")
const ShellRenderer := preload("res://scenes/galaxy/shell_renderer.gd")
const DrivenModel := preload("res://scenes/galaxy/galaxy_view_driven.gd")
const AmbientRig := preload("res://scenes/galaxy/ambient_rig.gd")
const GalaxyQuality := preload("res://scenes/galaxy/galaxy_quality.gd")
const GalaxyFlash := preload("res://scenes/galaxy/galaxy_flash.gd")
const UnknownLabel := preload("res://scenes/galaxy/unknown_label.gd")
const TerritoryTween := preload("res://scenes/galaxy/territory_tween.gd")
const ZoomController := preload("res://scenes/galaxy/legacy_zoom_disclosure_controller.gd")

const PLANTS := ["seed-ignored", "owner-colour-flat", "edges-2d-overlay",
	"pick-radius-zero", "bands-frozen", "conquest-no-recolour"]

const DEFAULT_SEED := 1
const LIVE_SNAPSHOT_TIMEOUT_MSEC := 8000
# B23 (spec rev 12b): the prototype's default camera as run (orbit_camera.gd:14 DIST_DEFAULT 50 x CIV_SCALE 0.5 on
# origin/push/galaxy-field at 99f35887); Regional, where R-106-03 puts the default. Target the origin, the centre of the ball.
const DEFAULT_DISTANCE := 25.0
const DEFAULT_TARGET := Vector3.ZERO
const PICK_RADIUS_PX := 14.0
const BAND_SPLIT_LOW := 16.25   # prototype orbit_camera.gd:28, 32.5 x CIV_SCALE 0.5 (B23)
const BAND_SPLIT_HIGH := 35.0   # prototype orbit_camera.gd:29, 70 x CIV_SCALE 0.5 (B23)
const FLAT_COLOUR := Color(1.0, 1.0, 1.0, 1.0)
const EDGE_2D_WIDTH := 1.5
const EDGE_2D_COLOUR := Color(0.6, 0.6, 0.6, 1.0)
const POINT_RADIUS := 0.7   # prototype galaxy_view.gd:5 POINT_BASE_RADIUS 1.4 x CIV_SCALE 0.5 (B23)
const OWNER_SAT := 0.65
const OWNER_VAL := 0.85
const PLAYER_OWNER_VAL := 0.95   # prototype galaxy_view.gd:93-94, faction 0 = the player's faction (Rev 12b)
const NEUTRAL_COLOUR := Color(0.55, 0.55, 0.58, 1.0)   # prototype galaxy_view.gd:6 NEUTRAL_COLOR, owner -1
const OWNER_ALPHA := 1.0
const GOLDEN_ANGLE := 0.6180339887498949
const TIER_SIGNIFICANCE := [0.3, 0.6, 1.0]
# B23 (Rev 12b): the prototype's flash, a billboard quad (galaxy_view.gd:283, Vector2(3, 3) x CIV_SCALE 0.5) living
# FLASH_DURATION 0.6 s (galaxy_view.gd:8)
const FLASH_SECONDS := 0.6
const FLASH_SIZE := 1.5
const FLASH_COLOURS := {"attack": Color(1.0, 0.45, 0.2), "conquest": Color(1.0, 0.9, 0.3), "revolt": Color(0.6, 0.8, 1.0)}

var _regions: Array = []
var _edges: Array = []
var _positions: Dictionary = {}
var _point_ids: Array = []   # region id of each dot instance, in MultiMesh order
var _region_colours: Dictionary = {}
var _significance: Dictionary = {}
var _owner_colours_cache: Dictionary = {}
var _player_faction: int = -1   # snapshot["player_faction"], -1 when the key is absent
var _seed: int = DEFAULT_SEED
var _hash: int = 0
var _plants: Dictionary = {}
var _frozen_band: String = ""

var _gen := GalaxyGen.new()
var _point_material: StandardMaterial3D
var _adapter: Node
var _zoom: Node
var _bridge = null
var _bridge_dirty := false
var _edge_canvas: Node2D = null  # Node2D in a CanvasLayer; valid only while edges-2d-overlay plant is active

var _error_panel: Control
var _quality := {"tier": 0, "res_divisor": 1}
var _unknown_factions: Array = []
var _prev_owners: Dictionary = {}
var _tween := TerritoryTween.new()
var _flashes: Array = []

signal camera_move_completed
signal region_clicked(region_id: String)
signal empty_space_clicked

# S-069: a host that feeds regions through add_region_node & co. (the time-jump
# sequencer) sets driven before add_child; the view then skips the live pipe.
var driven := false
var _driven_model := DrivenModel.new()
var _auto_camera := false

@onready var _world: Node3D = $World
@onready var _points: MultiMeshInstance3D = $World/Points
@onready var _camera_rig := $OrbitCamera


func _ready() -> void:
	_build_materials()
	_build_renderers()
	_camera_rig.set_view(DEFAULT_DISTANCE, DEFAULT_TARGET)
	if not driven:
		_load_live_snapshot()
	var mission_btn := get_node_or_null("UI/Mission")
	if mission_btn:
		mission_btn.pressed.connect(func(): SceneRouter.go_to("mission_briefing"))


# The point material is unshaded (a default lit material drew the dots black before the scene had a light,
# look 4, first_look/README.md), and the points read the per-instance owner colour as albedo.
func _build_materials() -> void:
	_point_material = StandardMaterial3D.new()
	_point_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_point_material.vertex_color_use_as_albedo = true
	# VG-B23b-dotcolour (FINDING-dot-colour-pixels): main's dot material from before B23 (sRGB vertex colour, no alpha
	# transparency); B23's alpha / non-sRGB values lost the owner colours under the default renderer (Westley 2026-10-12).
	# See also tests/test_vg_b_b23b.gd and TD-VG-B-15 in docs/northstar/plans/push_ledger_2026-09-22.md
	_point_material.vertex_color_is_srgb = true


# R-106-02: filament arcs and faction shells come from the prototype renderers,
# fed by GalaxyAdapter (scenes/galaxy/galaxy_adapter.gd) on every render. The
# renderers read the zoom band from _zoom, which _process feeds from the camera.
func _build_renderers() -> void:
	_adapter = GalaxyAdapter.new()
	_adapter.name = "GalaxyAdapter"
	add_child(_adapter)
	_zoom = ZoomController.new()
	_zoom.name = "ZoomDisclosureController"
	add_child(_zoom)
	var rig := AmbientRig.new()
	rig.name = "AmbientRig"
	add_child(rig)
	var settings: Dictionary = UIDataBus.get_settings()
	for pair in [[ConstellationRenderer, "ConstellationRenderer"], [ShellRenderer, "ShellRenderer"]]:
		var node: Node3D = pair[0].new()
		node.name = pair[1]
		if pair[1] == "ShellRenderer":
			_quality["tier"] = GalaxyQuality.apply(node, settings)
			_quality["res_divisor"] = node.res_divisor
		add_child(node)
		node.setup(_adapter, _zoom)


func get_positions() -> Dictionary:
	return _positions


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
	if not _bridge.ensure_world(seed, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES):
		push_error("galaxy_view: live snapshot failed: %s" % _bridge.last_error())
		_show_load_error(_bridge.last_error())
		_bridge = null
		return
	if _error_panel != null:
		_error_panel.hide_error()
	_bridge.snapshot_changed.connect(_on_bridge_changed)
	set_snapshot(_bridge.snapshot())


func _show_load_error(reason: String) -> void:
	if _error_panel == null:
		_error_panel = load("res://scenes/shared/error_panel.tscn").instantiate()
		_error_panel.retry_pressed.connect(_load_live_snapshot)
		$UI.add_child(_error_panel)
	_error_panel.show_error(reason if reason != "" else "galaxy load failed")


func _on_bridge_changed(_tick) -> void:
	_bridge_dirty = true


func _process(delta: float) -> void:
	_zoom.update_from_distance(_camera_rig.get_distance())
	_update_dot_scales()
	_step_flashes(delta)
	_feed_tween(Time.get_ticks_msec() / 1000.0)
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
	var player_faction := int(snapshot.get("player_faction", -1))
	if player_faction != _player_faction:
		_player_faction = player_faction
		_owner_colours_cache.clear()
	_note_owner_changes()
	_note_unknown_factions(snapshot)
	_relayout()
	_render()
	_feed_tween(Time.get_ticks_msec() / 1000.0)


func _note_owner_changes() -> void:
	var now := Time.get_ticks_msec() / 1000.0
	var owners := {}
	for r in _regions:
		var i := int(r.get("i", -1))
		var owner := int(r.get("owner", -1))
		owners[i] = owner
		if _prev_owners.has(i) and _prev_owners[i] != owner:
			_tween.start(i, _prev_owners[i], owner, now)
	_prev_owners = owners


# B7: a tweened region is fed through the same territory signal the renderer binds, owner colour
# and radius = significance x scale, so the field shrinks the old owner then grows the new one.
func _feed_tween(now: float) -> void:
	for e in _tween.step(now):
		var region := int(e["region"])
		var owner := int(e["owner"])
		if not _positions.has(region):
			continue
		var key := str(region)
		if owner < 0:
			_adapter.remove_territory(key)
			continue
		var colour: Color = _owner_colours_cache.get(owner, _colour_for_owner(owner))
		var sig: float = _significance.get(region, 1.0)
		_adapter.set_territory(key, _positions[region], sig * float(e["scale"]), colour)


func _note_unknown_factions(snapshot: Dictionary) -> void:
	var owner_ids: Array = []
	for r in _regions:
		owner_ids.append(int(r.get("owner", -1)))
	var known: Array = []
	if snapshot.has("factions"):
		for f in snapshot["factions"]:
			known.append(int(f.get("id", -1)) if f is Dictionary else int(f))
	else:
		known = owner_ids.duplicate()
	var shell := get_node_or_null("ShellRenderer")
	if shell != null:
		shell.known_faction_ids = known
	_unknown_factions = []
	for id in UnknownLabel.unknown_ids(owner_ids, known):
		if id >= 0:
			_unknown_factions.append(id)


# R-106-04: one flash per region GalaxyFlash names, on the drawn system; returns how many spawned.
func flash_from_delta(delta: Dictionary) -> int:
	var n := 0
	for f in GalaxyFlash.flashes_for_delta(delta):
		var region := int(f["region"])
		if not _positions.has(region):
			continue
		var mat := StandardMaterial3D.new()
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mat.albedo_color = FLASH_COLOURS.get(f["kind"], Color.WHITE)
		mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
		var quad := QuadMesh.new()
		quad.size = Vector2(FLASH_SIZE, FLASH_SIZE)
		var mesh := MeshInstance3D.new()
		mesh.mesh = quad
		mesh.material_override = mat
		mesh.position = _positions[region]
		add_child(mesh)
		_flashes.append({"node": mesh, "mat": mat, "left": FLASH_SECONDS})
		n += 1
	return n


func _step_flashes(dt: float) -> void:
	for fl in _flashes.duplicate():
		fl["left"] = float(fl["left"]) - dt
		if fl["left"] <= 0.0:
			fl["node"].queue_free()
			_flashes.erase(fl)
		else:
			var c: Color = fl["mat"].albedo_color
			c.a = float(fl["left"]) / FLASH_SECONDS
			fl["mat"].albedo_color = c


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
		if _camera_rig.is_behind(_positions[i]):
			continue
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
		"scene": "galaxy_view",
		"tick": int(_bridge.snapshot().get("tick", 0)) if _bridge != null else 0,
		"plants": PLANTS.duplicate(),
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
		"shell_renderer": {"present": get_node_or_null("ShellRenderer") != null, "significance": _significance.duplicate()},
		"unknown_factions": _unknown_factions.duplicate(),
		"ambient_rig": {"present": get_node_or_null("AmbientRig") != null, "tier": _quality["tier"]},
		"galaxy_quality": _quality.duplicate(),
		"quality_tier": _quality["tier"],
		"camera_autonomous": _camera_rig.has_method("is_autonomous") and _camera_rig.is_autonomous(),
		"flashes_active": _flashes.size(),
		"layout_fallbacks": _gen.last_fallbacks(),
		"error_panel": _error_panel != null and _error_panel.visible and _error_panel.get_node("ErrorPanel").visible,
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
		_render_points()
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
	_significance.clear()
	for r in _regions:
		_significance[int(r.get("i", -1))] = TIER_SIGNIFICANCE[clampi(int(r.get("tier", 0)), 0, 2)]
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
	if owner < 0:
		return NEUTRAL_COLOUR
	var hue := fposmod(float(owner) * GOLDEN_ANGLE, 1.0)
	var val := PLAYER_OWNER_VAL if owner == _player_faction else OWNER_VAL
	return Color.from_hsv(hue, OWNER_SAT, val, OWNER_ALPHA)


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
	var drawn_edges: Array = [] if _plants.get("edges-2d-overlay", false) else _edges
	_adapter.apply(_regions, drawn_edges, _positions, _region_colours)
	if _plants.get("edges-2d-overlay", false):
		_render_filaments_2d()


# Draws each galaxy edge as a Line2D in a CanvasLayer overlay, using the
# camera's canvas-space projection of the 3D system positions. Called only
# when the edges-2d-overlay plant is active; replaces the 3D filament arcs.
func _render_filaments_2d() -> void:
	if _edge_canvas == null:
		var layer := CanvasLayer.new()
		layer.layer = 10
		add_child(layer)
		_edge_canvas = Node2D.new()
		layer.add_child(_edge_canvas)
	else:
		for child in _edge_canvas.get_children():
			child.free()
	var cam: Camera3D = _camera_rig.get_camera()
	for e in _edges:
		var a := int(e.get("a", -1))
		var b := int(e.get("b", -1))
		if not (_positions.has(a) and _positions.has(b)):
			continue
		var pa: Vector2 = cam.unproject_position(_positions[a])
		var pb: Vector2 = cam.unproject_position(_positions[b])
		var line := Line2D.new()
		line.add_point(pa)
		line.add_point(pb)
		line.width = EDGE_2D_WIDTH
		line.default_color = EDGE_2D_COLOUR
		_edge_canvas.add_child(line)


func _render_points() -> void:
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	var sphere := SphereMesh.new()
	sphere.radius = POINT_RADIUS
	sphere.height = POINT_RADIUS * 2.0
	sphere.radial_segments = 12   # prototype galaxy_view.gd:109-110
	sphere.rings = 8
	mm.mesh = sphere
	_point_ids = _positions.keys()
	mm.instance_count = _point_ids.size()
	for idx in range(_point_ids.size()):
		mm.set_instance_color(idx, _region_colours.get(_point_ids[idx], FLAT_COLOUR))
	_points.multimesh = mm
	_points.material_override = _point_material
	_update_dot_scales()


# Per-instance dot transform: the prototype's scale (0.6 + 1.4 * significance) * lerp(1, 0.6, overview_weight)
# (galaxy_view.gd:228, 243 on origin/push/galaxy-field; the focus boost and flash factors are not ported).
# overview_weight = 1 - blend_factor in the overview band, else 0 (legacy_zoom_disclosure_controller.gd:24-46);
# blend_factor moves between 65 and 75 and band_changed fires only at the edges, so this runs every frame.
func _update_dot_scales() -> void:
	var mm: MultiMesh = _points.multimesh
	if mm == null:
		return
	var overview_weight: float = 1.0 - _zoom.blend_factor if _zoom.current_band == "overview" else 0.0
	var band_scale: float = lerpf(1.0, 0.6, overview_weight)
	for idx in range(_point_ids.size()):
		var i = _point_ids[idx]
		var dot_scale: float = (0.6 + 1.4 * float(_significance.get(i, 1.0))) * band_scale
		mm.set_instance_transform(idx, Transform3D(Basis().scaled(Vector3.ONE * dot_scale), _positions[i]))


# --- driven mode (S-069): the old world_view_shell API, answered here ---

func add_region_node(region_id: String, _pos: Vector3, significance: float, _colour: Color, faction_id: String) -> void:
	_driven_model.set_region(region_id, significance, faction_id)
	_driven_refresh()


func update_region_node(region_id: String, significance: float, _colour: Color) -> void:
	_driven_model.set_tier(region_id, significance)
	_driven_refresh()


# The old shell took ownership as a colour; the galaxy view keys it by faction.
func set_region_owner(region_id: String, faction_id: String) -> void:
	_driven_model.set_owner(region_id, faction_id)
	_driven_refresh()


func set_territory(region_id: String, _pos: Vector3, _size: float, _colour: Color) -> void:
	_driven_model.index_for(region_id)


func update_territory(region_id: String, _size: float, _colour: Color) -> void:
	_driven_model.index_for(region_id)


func remove_territory(region_id: String) -> void:
	_driven_model.clear_owner(region_id)
	_driven_refresh()


func add_connection(from_id: String, to_id: String, edge_type: String, _colour: Color) -> void:
	_driven_model.add_edge(from_id, to_id, edge_type)
	_driven_refresh()


# Flashes arrive from sim events (VG-B B6); until then a driven flash is silent.
func flash_military_activity(_region_id: String, _intensity: float) -> void:
	pass


func flash_conflict(_attacker_id: String, _defender_id: String, _intensity: float) -> void:
	pass


func highlight_region(region_id: String) -> void:
	_camera_rig.focus_region(_driven_model.index_for(region_id))


func clear_highlight() -> void:
	pass


func move_camera_to_region(region_id: String, _duration: float) -> void:
	_camera_rig.focus_region(_driven_model.index_for(region_id))
	_emit_camera_done()


func move_camera_to_regions(region_ids: Array, duration: float) -> void:
	if region_ids.is_empty():
		move_camera_to_overview(duration)
		return
	var sum := Vector3.ZERO
	var n := 0
	for rid in region_ids:
		var i := _driven_model.index_for(str(rid))
		if _positions.has(i):
			sum += _positions[i]
			n += 1
	if n > 0:
		_camera_rig.set_view(BAND_SPLIT_LOW + 10.0, sum / float(n))
	_emit_camera_done()


func move_camera_to_overview(_duration: float) -> void:
	_camera_rig.set_view(DEFAULT_DISTANCE, DEFAULT_TARGET)
	_emit_camera_done()


func start_auto_camera() -> void:
	_auto_camera = true
	if _camera_rig.has_method("set_autonomous"):
		_camera_rig.set_autonomous(true)


func stop_auto_camera() -> void:
	_auto_camera = false
	if _camera_rig.has_method("set_autonomous"):
		_camera_rig.set_autonomous(false)


func _emit_camera_done() -> void:
	await get_tree().create_timer(_camera_rig.FOCUS_SEC).timeout
	camera_move_completed.emit()


func _driven_refresh() -> void:
	if driven:
		set_snapshot(_driven_model.snapshot())

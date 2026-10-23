extends Node
class_name Ground3D

## SubViewport host for the 3D ground (visible-game lane C, C5; S-236 R-236-01). Holds the C2/C2b mesh and the
## C3 rig inside its own world, shown through a SubViewportContainer under the 2D shell. The rig is driven by the
## owner (process disabled): the tactical view pans and zooms it and reads camera {x,y} and scale back as the map
## band's equivalents (rulebook rows 3, 5, 12, 31). units_px and objects_px stay screen pixels.

const GroundMesh := preload("res://scenes/ground3d/ground_mesh.gd")
const CameraRig := preload("res://scenes/ground3d/camera_rig_3d.gd")
const GroundProjection := preload("res://scenes/ground3d/projection.gd")
const GroundUnits := preload("res://scenes/ground3d/ground_units.gd")
const GroundPick := preload("res://scenes/ground3d/ground_pick.gd")
const SlopeViewNode := preload("res://scenes/ground3d/slope_view.gd")

const SCREEN_SIZE := Vector2(1920.0, 1080.0)
const SKY_COLOUR := Color(0.55, 0.68, 0.82)
const SUN_ROTATION_DEG := Vector3(-55.0, -35.0, 0.0)
# VG-C-land-marks: a unit whose pick hit is nearer the camera than the unit's point by more than this is behind terrain.
const OCCLUSION_SLACK_WU := 20.0 # DRAFT-occlusion-slack
const OCCLUSION_RECOMPUTE_MS := 100 # DRAFT-occlusion-recompute-ms
const OCCLUSION_UNITS := [1, 4, 16] # cells per side of each occlusion DDA level, finest first
const OCCLUSION_MARGIN_US := 100 # the slice stops this early: one unit can run over its average, and the swap follows
const OCCLUSION_SLICE_US := 2000 # DRAFT-occlusion-slice-ms 2 per frame; a full pass completes within DRAFT-occlusion-pass-ms 500

var _terrain: Dictionary = {}
var _frame: Dictionary = {}
var _mission: Dictionary = {}
var _vertices := 0
var _container: SubViewportContainer
var _viewport: SubViewport
var _mesh: MeshInstance3D
var _cell_max: PackedFloat32Array = PackedFloat32Array() # wu, highest corner height per bilinear cell (occlusion DDA)
var _rig: Node3D
var _units3d: Node3D
var _slope_view: Node3D
var _layers: Array = []
var _units_drawn := 0
var _occluded: Dictionary = {}
var _occlusion_xf := Transform3D()
var _occlusion_ms := 0
var _cw := 0
var _grids: Array = [] # per OCCLUSION_UNITS level: highest corner height (wu) per block of that many cells per side
var _grid_w: Array = []
var _top_wu := 0.0 # highest corner height of the terrain
var _ch := 0
var _hs := PackedInt32Array()
var _units_cells: Dictionary = {} # unit id -> cell key at the last set_frame (a changed cell requests a pass)
var _requested := false
var _pass_units: Array = []
var _pass_from := Vector3.ZERO
var _pass_i := 0
var _pass_now: Dictionary = {}
var _pass_running := false
var _pass_start_us := 0
var _max_slice_us := 0
var _slice_frame := -1
var _last_pass_ms := 0.0
var _passes := 0

signal occlusion_changed


func _ready() -> void:
	_container = SubViewportContainer.new()
	_container.stretch = true
	_container.size = SCREEN_SIZE
	_container.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_container.z_index = -1
	add_child(_container)
	_viewport = SubViewport.new()
	_viewport.size = SCREEN_SIZE
	_viewport.own_world_3d = true
	_container.add_child(_viewport)
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = SKY_COLOUR
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.6, 0.6, 0.65)
	var we := WorldEnvironment.new()
	we.environment = env
	_viewport.add_child(we)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = SUN_ROTATION_DEG
	_viewport.add_child(sun)
	_rig = CameraRig.new()
	_rig.process_mode = Node.PROCESS_MODE_DISABLED
	_viewport.add_child(_rig)
	_units3d = GroundUnits.new()
	_viewport.add_child(_units3d)
	_slope_view = SlopeViewNode.new()
	_viewport.add_child(_slope_view)


# E1p-a hook: a layer node (SettlementLayer, later StrongpointLayer) lives inside the SubViewport after SlopesView and is
# handed the terrain and the frame when it has set_terrain / set_frame. Units3D is added before SlopesView in _ready, so
# "after SlopesView" also places it after Units3D (3D sibling order has no depth effect); test_vg_e_e1p.gd pins this.
func add_layer(node: Node3D) -> void:
	_viewport.add_child(node)
	_layers.append(node)


func container() -> Control:
	return _container


func camera_rig() -> Node3D:
	return _rig


func terrain() -> Dictionary:
	return _terrain


func set_terrain(t: Dictionary) -> void:
	_terrain = t
	if _mesh != null:
		_mesh.queue_free()
		_viewport.remove_child(_mesh)
		_mesh = null
	_vertices = 0
	_slope_view.set_terrain(t)
	for n in _layers:
		if n.has_method("set_terrain"):
			n.set_terrain(t)
	if t.is_empty():
		_rig.set_terrain({})
		return
	_cell_max = _cell_maxima(t)
	_grids = [_cell_max]
	_grid_w = [int(t.get("cells_w", 0)) - 1]
	for lv in range(1, OCCLUSION_UNITS.size()):
		var ratio: int = OCCLUSION_UNITS[lv] / OCCLUSION_UNITS[lv - 1]
		_grids.append(_coarsen(_grids[lv - 1], _grid_w[lv - 1], ratio))
		_grid_w.append(ceili(_grid_w[lv - 1] / float(ratio)))
	_top_wu = 0.0
	for m in _cell_max:
		_top_wu = maxf(_top_wu, m)
	_cw = int(t.get("cells_w", 0))
	_ch = int(t.get("cells_h", 0))
	_hs = t.get("heights", PackedInt32Array())
	_units_cells = {}
	_pass_running = false
	_mesh = GroundMesh.build(t)
	_viewport.add_child(_mesh)
	_vertices = (int(t["cells_w"]) - 1) * (int(t["cells_h"]) - 1) * 6
	_rig.set_terrain(t)


func set_frame(frame: Dictionary, mission: Dictionary) -> void:
	_frame = frame
	_mission = mission
	for n in _layers:
		if n.has_method("set_frame"):
			n.set_frame(frame)
	if _terrain.is_empty():
		return
	var local := int(frame.get("player_faction", 0))
	_units3d.local_faction = local
	var seen := {}
	for v in frame.get("visible", {}).get(str(local), []):
		seen[int(v)] = true
	var own: Array = []
	for u in frame.get("units", []):
		if int(u.get("faction", 0)) == local or seen.has(int(u.get("id"))):
			own.append(u)
	_units_drawn = own.size()
	_units3d.set_units(own, _terrain, _terrain.get("layer_floors_wu", []), _terrain.get("flyer_types", []))
	_slope_view.set_units(frame.get("units", []))
	var cells := {}
	for u in frame.get("units", []):
		cells[int(u.get("id"))] = int(float(u.get("x", 0.0)) / GroundPick.CELL_WU) * 65536 + int(float(u.get("y", 0.0)) / GroundPick.CELL_WU)
	if cells != _units_cells:
		_units_cells = cells
		_requested = true
		if not _pass_running:
			_run_slice()


# VG-C-land-marks: the host recomputes from the rig camera's own transform, no rig hooks (camera_rig_3d.gd is not edited).
# A pass over the units is time-sliced (Architect ruling 2026-10-23): each _process takes as many pending units as fit in
# OCCLUSION_SLICE_US, then yields, and occluded_ids is swapped in whole when the pass completes. A pass is requested by
# set_frame when a unit's cell changed and by the camera settle check (at most once per OCCLUSION_RECOMPUTE_MS while the
# camera keeps changing; the cached transform stays the old one until a pass starts, so the first pass after the camera
# stops is the settle pass). A request while a pass runs is served by the next pass once this one completes.
func _process(_delta: float) -> void:
	if _terrain.is_empty():
		return
	if not _pass_running:
		var moved: bool = _rig.get_camera().global_transform != _occlusion_xf
		if not (_requested or (moved and Time.get_ticks_msec() - _occlusion_ms >= OCCLUSION_RECOMPUTE_MS)):
			return
	_run_slice()


# One slice per frame: set_frame runs the first slice of the pass it requests, so a small frame is answered at once, and
# _process then skips its own slice in that same frame.
func _run_slice() -> void:
	var frame := Engine.get_process_frames()
	if frame == _slice_frame:
		return
	_slice_frame = frame
	var t0 := Time.get_ticks_usec()
	if not _pass_running:
		_start_pass(t0)
	while _pass_i < _pass_units.size():
		_occlude_unit(_pass_units[_pass_i])
		_pass_i += 1
		var spent := Time.get_ticks_usec() - t0
		if spent + spent * 2 / _pass_i >= OCCLUSION_SLICE_US - OCCLUSION_MARGIN_US:
			break
	if _pass_i >= _pass_units.size():
		_finish_pass()
	_max_slice_us = maxi(_max_slice_us, Time.get_ticks_usec() - t0)


func _start_pass(now_us: int) -> void:
	var cam: Camera3D = _rig.get_camera()
	_occlusion_xf = cam.global_transform
	_occlusion_ms = Time.get_ticks_msec()
	_requested = false
	_pass_from = cam.global_position
	_pass_units = _frame.get("units", [])
	_pass_i = 0
	_pass_now = {}
	_pass_running = true
	_pass_start_us = now_us


func _finish_pass() -> void:
	_pass_running = false
	_last_pass_ms = (Time.get_ticks_usec() - _pass_start_us) / 1000.0
	_passes += 1
	if _pass_now != _occluded:
		_occluded = _pass_now
		occlusion_changed.emit()


# {max_slice_us (largest single-frame occlusion cost since the previous call, reset by the read), last_pass_ms (pass start
# to swap), passes (completed), pending (units left in the running pass)}.
func occlusion_stats() -> Dictionary:
	var out := {"max_slice_us": _max_slice_us, "last_pass_ms": _last_pass_ms, "passes": _passes,
			"pending": (_pass_units.size() - _pass_i) if _pass_running else 0}
	_max_slice_us = 0
	return out


func _occlude_unit(u: Dictionary) -> void:
	var ux := float(u.get("x", 0.0))
	var uz := float(u.get("y", 0.0))
	var d := Vector3(ux, _height(ux, uz), uz) - _pass_from
	var dist := d.length()
	if dist - OCCLUSION_SLACK_WU > 0.0 and _ray_blocked(_pass_from, d / dist, dist - OCCLUSION_SLACK_WU):
		_pass_now[int(u.get("id"))] = true


# Cell DDA (replaces GroundPick.pick here, same result): walks the bilinear cells (corners at cell centres) the ray crosses
# and compares the ray height at each cell boundary with the cell's highest corner; only a cell whose maximum rises above
# the ray is sampled, at GroundPick's own STEP multiples, and the first sample under the terrain is bisected as pick does.
# s_end is the unit's distance less the slack: a hit nearer than that is an occluder. The walk runs one STEP past s_end
# because a hit sampled there can still bisect to a crossing before it. The walk starts at the coarsest
# OCCLUSION_UNITS level (blocks with their own maxima) and descends into a block only when its maximum rises above the ray.
func _ray_blocked(from: Vector3, dir: Vector3, s_end: float) -> bool:
	var cw := _cw
	var ch := _ch
	if cw < 2 or ch < 2 or _cell_max.is_empty():
		return false
	var ox := from.x
	var oz := from.z
	var dx := dir.x
	var dz := dir.z
	var dy := dir.y
	if dy >= 0.0 and from.y > _height(ox, oz):
		return false
	var c := GroundPick.CELL_WU
	var s0 := 0.0
	var s1 := s_end + GroundPick.STEP
	var w_wu := cw * c
	var h_wu := ch * c
	if absf(dx) < 1e-9:
		if ox < 0.0 or ox > w_wu:
			return false
	else:
		var ta := -ox / dx
		var tb := (w_wu - ox) / dx
		s0 = maxf(s0, minf(ta, tb))
		s1 = minf(s1, maxf(ta, tb))
	if absf(dz) < 1e-9:
		if oz < 0.0 or oz > h_wu:
			return false
	else:
		var ta := -oz / dz
		var tb := (h_wu - oz) / dz
		s0 = maxf(s0, minf(ta, tb))
		s1 = minf(s1, maxf(ta, tb))
	# Above the terrain's highest corner no cell can block: start where the ray first dips to it.
	if from.y > _top_wu:
		if dy >= 0.0:
			return false
		s0 = maxf(s0, (from.y - _top_wu) / -dy)
	if s0 >= s1:
		return false
	return _walk(from, dir, s0, s1, s_end, OCCLUSION_UNITS.size() - 1) == 1


# One DDA level (index into OCCLUSION_UNITS); returns 1 when the first terrain hit is nearer than s_end, 0 when the first hit
# is not, -1 when the ray meets no terrain between s0 and s1.
func _walk(from: Vector3, dir: Vector3, s0: float, s1: float, s_end: float, level: int) -> int:
	var ox := from.x
	var oz := from.z
	var oy := from.y
	var dx := dir.x
	var dz := dir.z
	var dy := dir.y
	var c: float = GroundPick.CELL_WU * OCCLUSION_UNITS[level]
	var half := GroundPick.CELL_WU * 0.5
	var kx := int(floor(((ox + dx * (s0 + 0.001)) - half) / c))
	var kz := int(floor(((oz + dz * (s0 + 0.001)) - half) / c))
	var sx := 1 if dx > 0.0 else -1
	var sz := 1 if dz > 0.0 else -1
	var tmx := 1e30
	var tmz := 1e30
	var dtx := 1e30
	var dtz := 1e30
	if absf(dx) > 1e-9:
		tmx = (half + (kx + (1.0 if sx > 0 else 0.0)) * c - ox) / dx
		dtx = c / absf(dx)
	if absf(dz) > 1e-9:
		tmz = (half + (kz + (1.0 if sz > 0 else 0.0)) * c - oz) / dz
		dtz = c / absf(dz)
	var grid: PackedFloat32Array = _grids[level]
	var nx: int = _grid_w[level]
	var mx := nx - 1
	var mz := (grid.size() / nx) - 1
	var step := GroundPick.STEP
	var s := s0
	while s < s1:
		var sn := tmx if tmx < tmz else tmz
		if sn > s1:
			sn = s1
		var y_lo := oy + dy * (s if dy >= 0.0 else sn)
		var ix := 0 if kx < 0 else (mx if kx > mx else kx)
		var iz := 0 if kz < 0 else (mz if kz > mz else kz)
		if grid[iz * nx + ix] > y_lo:
			if level > 0:
				var r := _walk(from, dir, s, sn, s_end, level - 1)
				if r >= 0:
					return r
			else:
				var k := ceili(s / step)
				while k * step < sn:
					var sq := k * step
					if oy + dy * sq <= _height(ox + dx * sq, oz + dz * sq):
						# The crossing is at or before sq: a sample a wu inside s_end needs no bisection (its
						# error is far under a wu).
						if sq < s_end - 1.0:
							return 1
						return 1 if _bisect_hit(from, dir, maxf(sq - step, 0.0), sq) < s_end else 0
					k += 1
		s = sn
		if tmx <= tmz:
			kx += sx
			tmx += dtx
		else:
			kz += sz
			tmz += dtz
	return -1


func _bisect_hit(from: Vector3, dir: Vector3, a: float, b: float) -> float:
	for _k in GroundPick.BISECT:
		var m := (a + b) * 0.5
		var pm := from + dir * m
		if pm.y <= _height(pm.x, pm.z):
			b = m
		else:
			a = m
	var hit := from + dir * b
	return (Vector3(hit.x, _height(hit.x, hit.z), hit.z) - from).length()


# GroundPick.height_at on the arrays cached at set_terrain (same arithmetic, no per-call dictionary reads).
func _height(wx: float, wz: float) -> float:
	var c := GroundPick.CELL_WU
	var fx := clampf(wx / c - 0.5, 0.0, _cw - 1.0)
	var fy := clampf(wz / c - 0.5, 0.0, _ch - 1.0)
	var i0 := maxi(mini(int(floor(fx)), _cw - 2), 0)
	var j0 := maxi(mini(int(floor(fy)), _ch - 2), 0)
	var i1 := mini(i0 + 1, _cw - 1)
	var j1 := mini(j0 + 1, _ch - 1)
	var tx := fx - i0
	var ty := fy - j0
	var a := lerpf(_hs[j0 * _cw + i0], _hs[j0 * _cw + i1], tx)
	var b := lerpf(_hs[j1 * _cw + i0], _hs[j1 * _cw + i1], tx)
	return lerpf(a, b, ty) / 100.0


static func _coarsen(cells: PackedFloat32Array, nx: int, ratio: int) -> PackedFloat32Array:
	var out := PackedFloat32Array()
	if nx < 1 or cells.is_empty():
		return out
	var ny := cells.size() / nx
	var bw := ceili(nx / float(ratio))
	out.resize(bw * ceili(ny / float(ratio)))
	for j in ny:
		for i in nx:
			var b := (j / ratio) * bw + i / ratio
			out[b] = maxf(out[b], cells[j * nx + i])
	return out


static func _cell_maxima(t: Dictionary) -> PackedFloat32Array:
	var w := int(t.get("cells_w", 0))
	var h := int(t.get("cells_h", 0))
	var hs: PackedInt32Array = t.get("heights", PackedInt32Array())
	var out := PackedFloat32Array()
	if w < 2 or h < 2 or hs.size() < w * h:
		return out
	out.resize((w - 1) * (h - 1))
	for j in h - 1:
		for i in w - 1:
			out[j * (w - 1) + i] = maxi(maxi(hs[j * w + i], hs[j * w + i + 1]), maxi(hs[(j + 1) * w + i], hs[(j + 1) * w + i + 1])) / 100.0
	return out


func occluded_ids() -> Dictionary:
	return _occluded


func arrow_count() -> int:
	return _units3d.arrow_count()


func to_screen(wx: float, wy: float) -> Vector2:
	return GroundProjection.to_screen(_rig.get_camera(), _terrain, wx, wy)


func to_world(screen: Vector2) -> Variant:
	return GroundProjection.to_world(_rig.get_camera(), _terrain, screen)


func objects_px() -> Array:
	var out: Array = []
	var nodes: Array = _frame.get("map", {}).get("nodes", [])
	for o in _mission.get("objectives", []):
		var n := int(o.get("node", -1))
		if n >= 0 and n < nodes.size():
			var p := to_screen(float(nodes[n]["x"]), float(nodes[n]["y"]))
			out.append([p.x, p.y])
	return out


func qa_state() -> Dictionary:
	var out := {"ground3d": {"present": false}, "units_px": {}, "objects_px": []}
	if _terrain.is_empty():
		return out
	var q: Dictionary = _rig.qa_camera()
	out["ground3d"] = {
		"present": true,
		"cells_w": int(_terrain["cells_w"]),
		"cells_h": int(_terrain["cells_h"]),
		"vertices": _vertices,
		"band": _rig.band(),
		"camera_height": _rig.camera_height(),
		"camera": {"x": q["x"], "y": q["y"]},
		"scale": q["scale"],
		"slope_view": _slope_view.qa_state(),
		"units3d": _units_drawn,
		"units3d_heights": _units3d.heights(),
		"units3d_shadows": _units3d.shadow_ids(),
		"occluded_ids": _sorted_ids(_occluded),
	}
	var upx := {}
	for u in _frame.get("units", []):
		var p := to_screen(float(u.get("x", 0.0)), float(u.get("y", 0.0)))
		upx[str(int(u.get("id")))] = [p.x, p.y]
	out["units_px"] = upx
	out["objects_px"] = objects_px()
	return out


func _sorted_ids(d: Dictionary) -> Array:
	var out: Array = d.keys()
	out.sort()
	return out

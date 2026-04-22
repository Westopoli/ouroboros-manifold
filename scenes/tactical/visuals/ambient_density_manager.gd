## Two-layer ambient system: particle haze emitter + battle-biased flyby ship pool.
## Haze covers the engagement zone. Flybys spawn on a timer, biased toward combat
## hotspots via the combat heatmap. Floor density ensures quiet areas get flybys too.
## See also: combat_heatmap.gd, flyby_ship_pool.gd
extends Node3D

const HAZE_PARTICLE_COUNT := 200
const HAZE_AREA := 5000.0
const HAZE_LIFETIME := 8.0
const HAZE_Y := 30.0

const FLYBY_INTERVAL_BASE := 2.0
const FLYBY_INTERVAL_MIN := 0.8
const FLYBY_MARGIN := 500.0
const FLYBY_Y_MIN := 30.0
const FLYBY_Y_MAX := 80.0
const FLOOR_SPAWN_INTERVAL := 100.0

var _heatmap: RefCounted
var _flyby_pool: Node3D

var _haze_emitter: GPUParticles3D
var _flyby_timer: float = 0.0
var _floor_timer: float = 0.0

var _map_width: float = 4000.0
var _map_height: float = 4000.0

var camera_zoom: float = 0.0

var _total_spawned: int = 0


func _ready() -> void:
	_heatmap = preload("res://scenes/tactical/visuals/combat_heatmap.gd").new()

	_flyby_pool = preload("res://scenes/tactical/visuals/flyby_ship_pool.gd").new()
	_flyby_pool.name = "FlybyShipPool"
	add_child(_flyby_pool)

	_setup_haze()

	TacticalBridge.snapshot_received.connect(_on_snapshot)


func _on_snapshot(snap: Dictionary) -> void:
	var map_info: Dictionary = snap.get("map", {})
	var canvas: Array = map_info.get("canvas_size", [4000, 4000])
	_map_width = float(canvas[0])
	_map_height = float(canvas[1])
	_heatmap.set_map_size(_map_width, _map_height)

	_haze_emitter.position = Vector3(_map_width * 0.5, HAZE_Y, _map_height * 0.5)
	var proc_mat: ParticleProcessMaterial = _haze_emitter.process_material
	proc_mat.emission_box_extents = Vector3(_map_width * 0.5, 20.0, _map_height * 0.5)


func _setup_haze() -> void:
	_haze_emitter = GPUParticles3D.new()
	_haze_emitter.amount = HAZE_PARTICLE_COUNT
	_haze_emitter.lifetime = HAZE_LIFETIME
	_haze_emitter.one_shot = false
	_haze_emitter.fixed_fps = 10
	_haze_emitter.visibility_aabb = AABB(
		Vector3(-HAZE_AREA, -100, -HAZE_AREA),
		Vector3(HAZE_AREA * 2, 200, HAZE_AREA * 2)
	)

	var proc_mat := ParticleProcessMaterial.new()
	proc_mat.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	proc_mat.emission_box_extents = Vector3(HAZE_AREA * 0.5, 20.0, HAZE_AREA * 0.5)
	proc_mat.direction = Vector3(1, 0.2, 0.5).normalized()
	proc_mat.spread = 30.0
	proc_mat.initial_velocity_min = 5.0
	proc_mat.initial_velocity_max = 15.0
	proc_mat.gravity = Vector3.ZERO
	proc_mat.scale_min = 1.0
	proc_mat.scale_max = 3.0
	proc_mat.color = Color(0.3, 0.35, 0.5, 0.04)
	_haze_emitter.process_material = proc_mat

	var draw_mesh := SphereMesh.new()
	draw_mesh.radius = 4.0
	draw_mesh.height = 8.0
	var draw_mat := StandardMaterial3D.new()
	draw_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	draw_mat.albedo_color = Color(0.3, 0.35, 0.5, 0.03)
	draw_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	draw_mesh.surface_set_material(0, draw_mat)
	_haze_emitter.draw_pass_1 = draw_mesh

	_haze_emitter.position = Vector3(HAZE_AREA * 0.5, HAZE_Y, HAZE_AREA * 0.5)
	add_child(_haze_emitter)
	_haze_emitter.emitting = true


func _process(delta: float) -> void:
	_heatmap.update(delta)
	_flyby_pool.process_ships(delta)
	_update_flyby_spawns(delta)


func _update_flyby_spawns(delta: float) -> void:
	# At extreme zoom, flybys are invisible — skip spawning
	if camera_zoom > 4500.0:
		return

	var intensity: float = _heatmap.get_total_intensity()
	var interval: float = maxf(FLYBY_INTERVAL_BASE / maxf(1.0 + intensity * 0.1, 1.0), FLYBY_INTERVAL_MIN)

	_flyby_timer += delta
	if _flyby_timer >= interval:
		_flyby_timer = 0.0
		_spawn_combat_flyby()

	_floor_timer += delta
	if _floor_timer >= FLOOR_SPAWN_INTERVAL:
		_floor_timer = 0.0
		_spawn_floor_flyby()


func _spawn_combat_flyby() -> void:
	var hotspot: Vector2 = _heatmap.get_hotspot()
	var radius: float = randf_range(300.0, 800.0)
	var angle_start: float = randf_range(0.0, TAU)
	var angle_end: float = angle_start + randf_range(PI * 0.5, PI * 1.5)

	var start := Vector3(
		hotspot.x + cos(angle_start) * radius,
		randf_range(FLYBY_Y_MIN, FLYBY_Y_MAX),
		hotspot.y + sin(angle_start) * radius,
	)
	var end_pos := Vector3(
		hotspot.x + cos(angle_end) * radius * randf_range(0.8, 1.3),
		randf_range(FLYBY_Y_MIN, FLYBY_Y_MAX),
		hotspot.y + sin(angle_end) * radius * randf_range(0.8, 1.3),
	)
	var ctrls: Array[Vector3] = _build_curved_controls(start, end_pos)

	_flyby_pool.spawn_ship(start, ctrls[0], ctrls[1], end_pos)
	_total_spawned += 1


func _spawn_floor_flyby() -> void:
	var start: Vector3 = _random_boundary_point()
	var end_pos: Vector3 = _opposite_boundary_point(start)
	var ctrls: Array[Vector3] = _build_curved_controls(start, end_pos)

	_flyby_pool.spawn_ship(start, ctrls[0], ctrls[1], end_pos)
	_total_spawned += 1


func _build_curved_controls(start: Vector3, end_pos: Vector3) -> Array[Vector3]:
	var dx: float = end_pos.x - start.x
	var dz: float = end_pos.z - start.z
	var path_len: float = sqrt(dx * dx + dz * dz)
	var perp_x: float = -dz / maxf(path_len, 1.0)
	var perp_z: float = dx / maxf(path_len, 1.0)

	# Gentle arc — sin wave handles the wiggle, base path just curves slightly
	var sweep: float = randf_range(0.2, 0.5) * path_len
	if randf() > 0.5:
		sweep = -sweep

	var c1 := Vector3(
		lerpf(start.x, end_pos.x, 0.33) + perp_x * sweep,
		randf_range(FLYBY_Y_MIN, FLYBY_Y_MAX),
		lerpf(start.z, end_pos.z, 0.33) + perp_z * sweep,
	)
	var c2 := Vector3(
		lerpf(start.x, end_pos.x, 0.66) + perp_x * sweep * 0.5,
		randf_range(FLYBY_Y_MIN, FLYBY_Y_MAX),
		lerpf(start.z, end_pos.z, 0.66) + perp_z * sweep * 0.5,
	)
	return [c1, c2]


func _random_boundary_point() -> Vector3:
	var side: int = randi() % 4
	var y: float = randf_range(FLYBY_Y_MIN, FLYBY_Y_MAX)
	match side:
		0: return Vector3(-FLYBY_MARGIN, y, randf_range(0.0, _map_height))
		1: return Vector3(_map_width + FLYBY_MARGIN, y, randf_range(0.0, _map_height))
		2: return Vector3(randf_range(0.0, _map_width), y, -FLYBY_MARGIN)
		_: return Vector3(randf_range(0.0, _map_width), y, _map_height + FLYBY_MARGIN)


func _opposite_boundary_point(start: Vector3) -> Vector3:
	var y: float = randf_range(FLYBY_Y_MIN, FLYBY_Y_MAX)
	var center := Vector3(_map_width * 0.5, 0.0, _map_height * 0.5)
	var dir: Vector3 = (center - start).normalized()
	var exit_dist: float = maxf(_map_width, _map_height) + FLYBY_MARGIN * 2.0
	var exit: Vector3 = start + dir * exit_dist
	exit.y = y
	return exit


func get_stats() -> Dictionary:
	return {
		"active_flybys": _flyby_pool.get_active_count(),
		"peak_flybys": _flyby_pool.get_peak(),
		"total_spawned": _total_spawned,
		"heatmap_intensity": _heatmap.get_total_intensity(),
		"haze_active": _haze_emitter.emitting,
	}

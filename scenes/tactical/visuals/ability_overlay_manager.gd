## Manages ability overlay visuals: ring telegraphs, unit glow, screen-space distortion.
## Consumes ability events from TacticalBridge.ability_event_received signal.
## See also: attack_visual_manager.gd — spawns area_pulse for area abilities.
extends Node3D

const ABILITY_OVERLAYS := {
	"surge":     {"base_enhance": true,  "overlays": ["unit_glow"]},
	"intercept": {"base_enhance": true,  "overlays": ["unit_glow"]},
	"brace":     {"base_enhance": false, "overlays": ["unit_glow"]},
	"rally":     {"base_enhance": true,  "overlays": ["ring_telegraph", "distortion"]},
	"barrage":   {"base_enhance": true,  "overlays": ["ring_telegraph", "distortion"]},
	"fortify":   {"base_enhance": false, "overlays": ["ring_telegraph"]},
}

const FRIENDLY_COLOR := Color(0.3, 0.6, 1.0, 0.7)
const HOSTILE_COLOR := Color(1.0, 0.3, 0.2, 0.7)

const RING_POOL_SIZE := 16
const GLOW_POOL_SIZE := 32
const DISTORTION_DURATION := 0.15
const DISTORTION_FOV_DELTA := 2.0

var _ring_pool: Array[MeshInstance3D] = []
var _active_rings: Array[Dictionary] = []

var _glow_pool: Array[Dictionary] = []
var _active_glows: Array[Dictionary] = []

var _distortion_timer: float = 0.0
var _camera: Camera3D
var _base_fov: float = 75.0
var _player_faction: int = -1

var _torus_mesh: TorusMesh
var _glow_mesh: SphereMesh

var _attack_visual_manager: Node3D


func _ready() -> void:
	_torus_mesh = TorusMesh.new()
	_torus_mesh.inner_radius = 1.0
	_torus_mesh.outer_radius = 1.0 + 5.0
	_torus_mesh.rings = 48
	_torus_mesh.ring_segments = 16

	for i in RING_POOL_SIZE:
		var mi := MeshInstance3D.new()
		mi.mesh = _torus_mesh
		mi.visible = false
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mi)
		_ring_pool.append(mi)

	_glow_mesh = SphereMesh.new()
	_glow_mesh.radius = 1.0
	_glow_mesh.height = 2.0

	for i in GLOW_POOL_SIZE:
		var mi := MeshInstance3D.new()
		mi.mesh = _glow_mesh
		mi.visible = false
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mi)
		_glow_pool.append({"mi": mi, "mat": null})

	TacticalBridge.ability_event_received.connect(_on_ability_event)


func setup(camera: Camera3D, player_faction: int, attack_visuals: Node3D) -> void:
	_camera = camera
	_base_fov = camera.fov if camera else 75.0
	_player_faction = player_faction
	_attack_visual_manager = attack_visuals


func _on_ability_event(event: Dictionary) -> void:
	var ability_id: String = str(event.get("ability_id", ""))
	var cfg: Dictionary = ABILITY_OVERLAYS.get(ability_id, {})
	if cfg.is_empty():
		return

	var uid: int = int(event.get("uid", -1))
	var faction: int = int(event.get("faction", 0))
	var is_friendly: bool = faction == _player_faction
	var target_pos: Array = event.get("target_pos", [0.0, 0.0])
	var radius: float = float(event.get("radius", 0.0))
	var duration_ticks: int = int(event.get("duration_ticks", 0))
	var duration_sec: float = float(duration_ticks) * TacticalBridge.TICK_DURATION

	var overlays: Array = cfg.get("overlays", [])

	for overlay_name in overlays:
		var oname: String = str(overlay_name)
		if oname == "ring_telegraph" and radius > 0.0:
			var color: Color = FRIENDLY_COLOR if is_friendly else HOSTILE_COLOR
			_spawn_ring(target_pos, radius, maxf(duration_sec, 0.6), color)
		elif oname == "unit_glow" and uid >= 0:
			_spawn_glow(uid, maxf(duration_sec, 0.5), is_friendly)
		elif oname == "distortion":
			_distortion_timer = DISTORTION_DURATION

	if cfg.get("base_enhance", false) and _attack_visual_manager and radius > 0.0:
		var center := Vector3(float(target_pos[0]), 0.0, float(target_pos[1]))
		var color: Color = FRIENDLY_COLOR if is_friendly else HOSTILE_COLOR
		_attack_visual_manager.spawn_area_pulse(center, radius, maxf(duration_sec, 0.6), color)


func _spawn_ring(target_pos: Array, radius: float, duration: float, color: Color) -> void:
	if _ring_pool.is_empty():
		return
	var mi: MeshInstance3D = _ring_pool.pop_back()

	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.emission_enabled = true
	mat.emission = Color(color.r, color.g, color.b, 1.0)
	mat.emission_energy_multiplier = 3.0
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mi.material_override = mat

	mi.position = Vector3(float(target_pos[0]), 0.5, float(target_pos[1]))
	var scale_factor: float = radius / 6.0
	mi.scale = Vector3(scale_factor, scale_factor, scale_factor)
	mi.visible = true

	_active_rings.append({
		"mi": mi,
		"mat": mat,
		"elapsed": 0.0,
		"duration": duration,
		"color": color,
	})


func _spawn_glow(uid: int, duration: float, is_friendly: bool) -> void:
	if _glow_pool.is_empty():
		return
	var entry: Dictionary = _glow_pool.pop_back()
	var mi: MeshInstance3D = entry.mi

	var color: Color = FRIENDLY_COLOR if is_friendly else HOSTILE_COLOR

	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(color.r, color.g, color.b, 0.4)
	mat.emission_enabled = true
	mat.emission = color
	mat.emission_energy_multiplier = 5.0
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mi.material_override = mat
	entry.mat = mat

	mi.scale = Vector3.ONE * 40.0
	mi.visible = true

	_active_glows.append({
		"entry": entry,
		"uid": uid,
		"elapsed": 0.0,
		"duration": duration,
		"color": color,
	})


func _process(delta: float) -> void:
	_process_rings(delta)
	_process_glows(delta)
	_process_distortion(delta)


func _process_rings(delta: float) -> void:
	var i := 0
	while i < _active_rings.size():
		var ring: Dictionary = _active_rings[i]
		ring.elapsed += delta
		var t: float = clampf(ring.elapsed / maxf(ring.duration, 0.001), 0.0, 1.0)

		if t >= 1.0:
			ring.mi.visible = false
			_ring_pool.append(ring.mi)
			_active_rings.remove_at(i)
			continue

		var mat: StandardMaterial3D = ring.mat
		var color: Color = ring.color
		var pulse: float = 0.7 + 0.3 * sin(ring.elapsed * 4.0 * TAU)
		var fade: float = 1.0 - t * t
		mat.albedo_color = Color(color.r, color.g, color.b, color.a * fade * pulse)
		mat.emission_energy_multiplier = 3.0 * fade

		i += 1


func _process_glows(delta: float) -> void:
	var i := 0
	while i < _active_glows.size():
		var glow: Dictionary = _active_glows[i]
		glow.elapsed += delta
		var t: float = clampf(glow.elapsed / maxf(glow.duration, 0.001), 0.0, 1.0)

		if t >= 1.0:
			glow.entry.mi.visible = false
			_glow_pool.append(glow.entry)
			_active_glows.remove_at(i)
			continue

		var uid: int = int(glow.uid)
		var mi: MeshInstance3D = glow.entry.mi
		if uid < TacticalBridge.unit_count and TacticalBridge.display_alive[uid] == 1:
			mi.position = Vector3(
				TacticalBridge.display_x[uid],
				0.0,
				TacticalBridge.display_y[uid]
			)

		var mat: StandardMaterial3D = glow.entry.mat
		var color: Color = glow.color
		var shimmer: float = 0.8 + 0.2 * sin(glow.elapsed * 6.0 * TAU)
		var fade: float = 1.0 - t
		mat.albedo_color = Color(color.r, color.g, color.b, 0.4 * fade * shimmer)
		mat.emission_energy_multiplier = 5.0 * fade * shimmer

		i += 1


func _process_distortion(delta: float) -> void:
	if _distortion_timer <= 0.0:
		return
	if not _camera:
		_distortion_timer = 0.0
		return

	_distortion_timer -= delta
	if _distortion_timer <= 0.0:
		_camera.fov = _base_fov
		_distortion_timer = 0.0
		return

	var t: float = _distortion_timer / DISTORTION_DURATION
	var offset: float = sin(t * PI) * DISTORTION_FOV_DELTA
	_camera.fov = _base_fov + offset


func get_stats() -> Dictionary:
	return {
		"active_rings": _active_rings.size(),
		"active_glows": _active_glows.size(),
		"distortion_active": _distortion_timer > 0.0,
	}

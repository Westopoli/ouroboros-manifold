## Isolated B2 test — seeds TacticalBridge directly so the real
## attack_visual_manager and impact_feedback_manager run without a sim.
extends Node3D

const PLAYER_FACTION := 0
const ENEMY_FACTION := 1

const PAN_SPEED := 1500.0
const ZOOM_STEP := 500.0
const HP_PULSE_INTERVAL := 0.4
const HP_PULSE_AMOUNT := 8.0

# Force layout (centered around (4000, 4000) in world space)
const PLAYER_X := 3500.0
const ENEMY_X := 4500.0
const Z_BASE := 3500.0
const Z_SPACING := 250.0

var _attack_visuals: Node3D
var _impact_feedback: Node3D
var _hp_pulse_timer: float = 0.0

@onready var _camera: Camera3D = $Camera3D


func _ready() -> void:
	_camera.position = Vector3(4000.0, 5000.0, 7500.0)
	_camera.look_at(Vector3(4000.0, 0.0, 4500.0), Vector3.UP)
	_camera.far = 30000.0

	_seed_units()

	# Mirror tactical.tscn child layout: AttackVisualManager and
	# ImpactFeedbackManager are peers of UnitRenderer under the scene root.
	_attack_visuals = preload("res://scenes/tactical/visuals/attack_visual_manager.gd").new()
	_attack_visuals.name = "AttackVisualManager"
	add_child(_attack_visuals)

	_impact_feedback = preload("res://scenes/tactical/visuals/impact_feedback_manager.gd").new()
	_impact_feedback.name = "ImpactFeedbackManager"
	add_child(_impact_feedback)

	# Tell UnitRenderer to do a full rebuild against the seeded units.
	TacticalBridge.snapshot_received.emit({})

	print("[B2-TEST] seeded %d units (%d player, %d enemy). " % [
		TacticalBridge.unit_count, _count_faction(PLAYER_FACTION), _count_faction(ENEMY_FACTION)
	])
	print("[B2-TEST] arrows pan, +/- zoom, Esc quits.")


func _seed_units() -> void:
	# Wipe any prior state in case the autoload was already touched.
	TacticalBridge.units.clear()
	TacticalBridge.player_visible_unit_uids.clear()
	for i in range(TacticalBridge.MAX_UNITS):
		TacticalBridge.display_alive[i] = 0
		TacticalBridge.display_x[i] = 0.0
		TacticalBridge.display_y[i] = 0.0
		TacticalBridge.display_facing[i] = 0.0

	var uid := 0

	# Player force (faction 0): 4 raiders (squad 4) + 2 bombards (squad 1, 5-volley)
	for i in 4:
		_add_unit(uid, "raider", PLAYER_FACTION, PLAYER_X, Z_BASE + i * Z_SPACING, 0.0)
		uid += 1
	for i in 2:
		_add_unit(uid, "bombard", PLAYER_FACTION, PLAYER_X - 250.0, Z_BASE + 200.0 + i * 600.0, 0.0)
		uid += 1

	# Enemy force (faction 1): 4 interceptors (squad 4) + 2 bombards
	for i in 4:
		_add_unit(uid, "interceptor", ENEMY_FACTION, ENEMY_X, Z_BASE + i * Z_SPACING, PI)
		uid += 1
	for i in 2:
		_add_unit(uid, "bombard", ENEMY_FACTION, ENEMY_X + 250.0, Z_BASE + 200.0 + i * 600.0, PI)
		uid += 1

	TacticalBridge.unit_count = uid
	_assign_attack_targets()


func _add_unit(uid: int, unit_type: String, faction: int, x: float, z: float, facing: float) -> void:
	TacticalBridge.units[uid] = {
		"uid": uid,
		"type": unit_type,
		"tier": 1,
		"faction": faction,
		"layer": 0,
		"hp": 1000.0,
		"max_hp": 1000.0,
		"attack_target": -1,
		"attack_interval": 1.5,
		"attack_range": 3000.0,
		"selection_eligible": 1,
		"preferred_layer": 0,
		"velocity": [0.0, 0.0],
		"pos": [x, z],
		"ability_cd_sec": 0.0,
	}
	TacticalBridge.display_x[uid] = x
	TacticalBridge.display_y[uid] = z
	TacticalBridge.display_facing[uid] = facing
	TacticalBridge.display_alive[uid] = 1
	# Make all enemy uids visible to the player (otherwise the fog gate in
	# unit_renderer / impact bursts in attack_visual_manager would skip them).
	if faction == ENEMY_FACTION:
		TacticalBridge.player_visible_unit_uids[uid] = true


func _assign_attack_targets() -> void:
	for uid in TacticalBridge.units:
		var unit: Dictionary = TacticalBridge.units[uid]
		var my_faction: int = int(unit.faction)
		var my_x: float = TacticalBridge.display_x[uid]
		var my_z: float = TacticalBridge.display_y[uid]
		var best_target := -1
		var best_dist := INF
		for other_uid in TacticalBridge.units:
			if other_uid == uid:
				continue
			var other: Dictionary = TacticalBridge.units[other_uid]
			if int(other.faction) == my_faction:
				continue
			var dx: float = TacticalBridge.display_x[other_uid] - my_x
			var dz: float = TacticalBridge.display_y[other_uid] - my_z
			var d: float = dx * dx + dz * dz
			if d < best_dist:
				best_dist = d
				best_target = int(other_uid)
		unit.attack_target = best_target


func _count_faction(faction: int) -> int:
	var n := 0
	for uid in TacticalBridge.units:
		if int(TacticalBridge.units[uid].faction) == faction:
			n += 1
	return n


func _process(delta: float) -> void:
	# Drive impact bursts by pulse-decrementing HP on units that are being
	# shot at. impact_feedback_manager spawns a burst whenever a unit's HP
	# drops by ≥0.5 (per-unit cooldown gates the rate). HP is restored before
	# zero so units never die during the harness run.
	_hp_pulse_timer -= delta
	if _hp_pulse_timer <= 0.0:
		_hp_pulse_timer = HP_PULSE_INTERVAL
		var attacked: Dictionary = {}  # target_uid → true
		for uid in TacticalBridge.units:
			var unit: Dictionary = TacticalBridge.units[uid]
			var t: int = int(unit.get("attack_target", -1))
			if t >= 0:
				attacked[t] = true
		for target_uid in attacked:
			var target: Dictionary = TacticalBridge.units.get(target_uid, {})
			if target.is_empty():
				continue
			var new_hp: float = float(target.get("hp", 0.0)) - HP_PULSE_AMOUNT
			if new_hp <= 50.0:
				new_hp = float(target.get("max_hp", 1000.0))
			target.hp = new_hp

	# Camera pan (arrow keys)
	var pan := Vector3.ZERO
	if Input.is_key_pressed(KEY_LEFT):
		pan.x -= PAN_SPEED * delta
	if Input.is_key_pressed(KEY_RIGHT):
		pan.x += PAN_SPEED * delta
	if Input.is_key_pressed(KEY_UP):
		pan.z -= PAN_SPEED * delta
	if Input.is_key_pressed(KEY_DOWN):
		pan.z += PAN_SPEED * delta
	if pan != Vector3.ZERO:
		_camera.position += pan


func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed:
		var k: int = (event as InputEventKey).keycode
		if k == KEY_ESCAPE:
			get_tree().quit()
		elif k == KEY_EQUAL or k == KEY_PLUS or k == KEY_KP_ADD:
			_camera.position.y = maxf(_camera.position.y - ZOOM_STEP, 1000.0)
		elif k == KEY_MINUS or k == KEY_KP_SUBTRACT:
			_camera.position.y += ZOOM_STEP

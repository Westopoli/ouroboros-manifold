extends Node

const SAMPLE_INTERVAL := 1.0

const TYPE_TO_CATEGORY := {
	"Raider": "strike", "Interceptor": "strike",
	"Vanguard": "line", "Warden": "line",
	"Bombard": "siege", "Bastion": "siege",
}

var _recording := false
var _elapsed := 0.0
var _timer := 0.0
var _samples: Array[Dictionary] = []


func start_recording() -> void:
	_samples.clear()
	_elapsed = 0.0
	_timer = 0.0
	_recording = true
	_take_sample()


func stop_recording() -> void:
	_recording = false


func get_metrics() -> Dictionary:
	return {
		"sample_interval_sec": SAMPLE_INTERVAL,
		"samples": _samples.duplicate(),
	}


func clear() -> void:
	_samples.clear()
	_recording = false
	_elapsed = 0.0
	_timer = 0.0


func _process(delta: float) -> void:
	if not _recording:
		return
	_timer += delta
	if _timer >= SAMPLE_INTERVAL:
		_timer -= SAMPLE_INTERVAL
		_elapsed += SAMPLE_INTERVAL
		_take_sample()


func _take_sample() -> void:
	var player_hp := 0.0
	var enemy_hp := 0.0
	var player_count := 0
	var enemy_count := 0
	var player_by_cat: Dictionary = {}
	var enemy_by_cat: Dictionary = {}
	var structures_player := 0
	var structures_enemy := 0
	var structures_neutral := 0

	for uid: int in TacticalBridge.units:
		var u: Dictionary = TacticalBridge.units[uid]
		if uid < TacticalBridge.display_alive.size() and TacticalBridge.display_alive[uid] == 0:
			continue
		var hp: float = u.get("hp", 0.0)
		var unit_type: String = u.get("type", "")
		var cat: String = TYPE_TO_CATEGORY.get(unit_type, "unknown")
		if u.get("selection_eligible", false):
			player_hp += hp
			player_count += 1
			player_by_cat[cat] = player_by_cat.get(cat, 0) + 1
		else:
			enemy_hp += hp
			enemy_count += 1
			enemy_by_cat[cat] = enemy_by_cat.get(cat, 0) + 1

	for sid in TacticalBridge.structures:
		var s: Dictionary = TacticalBridge.structures[sid]
		var owner: int = s.get("owner", -1)
		if owner == 0:
			structures_player += 1
		elif owner > 0:
			structures_enemy += 1
		else:
			structures_neutral += 1

	var obj_progress: Dictionary = {}
	for obj in TacticalBridge.objectives:
		obj_progress[obj.get("id", "")] = obj.get("progress", 0.0)

	_samples.append({
		"tick": TacticalBridge.current_tick,
		"elapsed_sec": _elapsed,
		"player_force_hp": player_hp,
		"enemy_force_hp": enemy_hp,
		"player_unit_count": player_count,
		"enemy_unit_count": enemy_count,
		"player_unit_counts_by_category": player_by_cat,
		"enemy_unit_counts_by_category": enemy_by_cat,
		"objective_progress": obj_progress,
		"structures_player": structures_player,
		"structures_enemy": structures_enemy,
		"structures_neutral": structures_neutral,
	})

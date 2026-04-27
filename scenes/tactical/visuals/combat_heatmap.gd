## Lightweight spatial grid tracking combat intensity.
## Cells gain score when units in them are attacking. Decays over time.
## Consumed by ambient_density_manager for flyby spawn biasing.
extends RefCounted

const GRID_SIZE := 10
const DECAY_RATE := 0.15
const ATTACK_SCORE := 1.0

var _grid: Array[float] = []
var _map_width: float = 8000.0
var _map_height: float = 8000.0
var _cell_w: float = 800.0
var _cell_h: float = 800.0


func _init() -> void:
	_grid.resize(GRID_SIZE * GRID_SIZE)
	for i in _grid.size():
		_grid[i] = 0.0


func set_map_size(w: float, h: float) -> void:
	_map_width = maxf(w, 1.0)
	_map_height = maxf(h, 1.0)
	_cell_w = _map_width / float(GRID_SIZE)
	_cell_h = _map_height / float(GRID_SIZE)


func update(delta: float) -> void:
	for i in _grid.size():
		_grid[i] = maxf(0.0, _grid[i] - DECAY_RATE * delta)

	for uid in range(TacticalBridge.unit_count):
		if TacticalBridge.display_alive[uid] == 0:
			continue
		var unit: Dictionary = TacticalBridge.units.get(uid, {})
		var target: int = int(unit.get("attack_target", -1))
		if target < 0:
			continue

		var cx: int = clampi(int(TacticalBridge.display_x[uid] / _cell_w), 0, GRID_SIZE - 1)
		var cy: int = clampi(int(TacticalBridge.display_y[uid] / _cell_h), 0, GRID_SIZE - 1)
		_grid[cy * GRID_SIZE + cx] += ATTACK_SCORE * delta


func get_hotspot() -> Vector2:
	var best_idx := 0
	var best_val: float = _grid[0]
	for i in range(1, _grid.size()):
		if _grid[i] > best_val:
			best_val = _grid[i]
			best_idx = i
	var row: int = best_idx / GRID_SIZE
	var col: int = best_idx % GRID_SIZE
	return Vector2(
		(float(col) + 0.5) * _cell_w,
		(float(row) + 0.5) * _cell_h,
	)


func get_intensity_at(world_x: float, world_y: float) -> float:
	var cx: int = clampi(int(world_x / _cell_w), 0, GRID_SIZE - 1)
	var cy: int = clampi(int(world_y / _cell_h), 0, GRID_SIZE - 1)
	return _grid[cy * GRID_SIZE + cx]


func get_total_intensity() -> float:
	var total: float = 0.0
	for v in _grid:
		total += v
	return total

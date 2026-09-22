class_name FogCellGrid
extends RefCounted

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")

const NEVER_SEEN := 0
const EXPLORED := 1
const VISIBLE := 2

var dim: int = 64
var cell_size: float = 100.0
var memory: bool = true
var cells: PackedByteArray = PackedByteArray()


func setup(p_dim: int, p_cell_size: float) -> void:
	dim = p_dim
	cell_size = p_cell_size
	cells.resize(dim * dim)
	reset_never_seen()


func reset_never_seen() -> void:
	for i in range(cells.size()):
		cells[i] = NEVER_SEEN


func cell_index(pos: Vector2) -> int:
	var gx: int = clampi(int(pos.x / cell_size), 0, dim - 1)
	var gy: int = clampi(int(pos.y / cell_size), 0, dim - 1)
	return gy * dim + gx


func state_at(pos: Vector2) -> int:
	return cells[cell_index(pos)]


func state_name(state: int) -> String:
	match state:
		VISIBLE:
			return "visible"
		EXPLORED:
			return "explored"
		_:
			return "never_seen"


func update(circles: Array) -> void:
	var mem_on: bool = memory and not QaPlants.is_active("no-memory")
	var now_visible := PackedByteArray()
	now_visible.resize(cells.size())
	for c in circles:
		var r: float = c.radius_eff
		if r <= 0.0:
			continue
		var pos: Vector2 = c.pos
		var min_gx: int = clampi(int((pos.x - r) / cell_size), 0, dim - 1)
		var max_gx: int = clampi(int((pos.x + r) / cell_size), 0, dim - 1)
		var min_gy: int = clampi(int((pos.y - r) / cell_size), 0, dim - 1)
		var max_gy: int = clampi(int((pos.y + r) / cell_size), 0, dim - 1)
		for gy in range(min_gy, max_gy + 1):
			for gx in range(min_gx, max_gx + 1):
				var cell_center := Vector2((gx + 0.5) * cell_size, (gy + 0.5) * cell_size)
				if cell_center.distance_to(pos) <= r:
					now_visible[gy * dim + gx] = 1

	for i in range(cells.size()):
		if now_visible[i] == 1:
			cells[i] = VISIBLE
		elif cells[i] == VISIBLE:
			cells[i] = EXPLORED if mem_on else NEVER_SEEN
		elif cells[i] == EXPLORED and not mem_on:
			cells[i] = NEVER_SEEN


func counts() -> Dictionary:
	var never := 0
	var explored := 0
	var visible := 0
	for i in range(cells.size()):
		match cells[i]:
			VISIBLE:
				visible += 1
			EXPLORED:
				explored += 1
			_:
				never += 1
	return {"never_seen": never, "explored": explored, "visible": visible}

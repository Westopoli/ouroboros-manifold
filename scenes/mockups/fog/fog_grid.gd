class_name FogCellGrid
extends RefCounted

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


func update(_circles: Array) -> void:
	pass


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

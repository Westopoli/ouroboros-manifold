class_name Places
extends RefCounted

const CELL := 100.0
const HAZARD_BLOCK_RADIUS := 150.0
const HAZARD_INFLUENCE_RADIUS := 1200.0
const HAZARD_BLOCK_CHANCE := 0.05

var canvas: float = 24000.0
var seed_value: int = 0
var nodes: Array = []
var dim: int = 0

var _astar: AStarGrid2D
var _route_cache: Dictionary = {}


func load_path(path: String) -> void:
	var text := FileAccess.get_file_as_string(path)
	load_dict(JSON.parse_string(text))


func load_dict(d: Dictionary) -> void:
	canvas = float(d.get("canvas", 24000.0))
	seed_value = int(d.get("seed", 0))
	nodes = []
	var counts := {}
	for n in d.get("nodes", []):
		var t := String(n.type)
		counts[t] = int(counts.get(t, -1)) + 1
		nodes.append({"id": "%s_%d" % [t, counts[t]], "type": t, "pos": Vector2(n.pos[0], n.pos[1])})
	_build_grid()


func nodes_of(t: String) -> Array:
	var out: Array = []
	for n in nodes:
		if n.type == t:
			out.append(n.pos)
	return out


func candidates(t: String) -> Array:
	var out: Array = []
	for n in nodes:
		if n.type == t:
			out.append({"id": n.id, "pos": n.pos})
	return out


func player_spawn() -> Dictionary:
	var sp := candidates("spawn_point")
	return sp[0] if sp.size() > 0 else {"id": "", "pos": Vector2.ZERO}


func enemy_spawn() -> Dictionary:
	var sp := candidates("spawn_point")
	if sp.size() <= 1:
		return sp[0] if sp.size() == 1 else {}
	var origin: Vector2 = sp[0].pos
	var best: Dictionary = sp[1]
	var best_d: float = origin.distance_to(sp[1].pos)
	for i in range(1, sp.size()):
		var d: float = origin.distance_to(sp[i].pos)
		if d > best_d:
			best_d = d
			best = sp[i]
	return best


func route_length(a: Vector2, b: Vector2) -> float:
	var path := route_path(a, b)
	if path.is_empty():
		return INF
	var total := 0.0
	for i in range(1, path.size()):
		total += path[i - 1].distance_to(path[i])
	return total


func route_path(a: Vector2, b: Vector2) -> Array:
	var ga := _to_grid(a)
	var gb := _to_grid(b)
	var key := "%d,%d|%d,%d" % [ga.x, ga.y, gb.x, gb.y]
	if _route_cache.has(key):
		return _route_cache[key]
	var path: Array = []
	if not (_astar.is_point_solid(ga) or _astar.is_point_solid(gb)):
		for id in _astar.get_id_path(ga, gb):
			path.append(Vector2(id.x, id.y) * CELL)
	_route_cache[key] = path
	return path


func _to_grid(p: Vector2) -> Vector2i:
	return Vector2i(clampi(int(round(p.x / CELL)), 0, dim - 1), clampi(int(round(p.y / CELL)), 0, dim - 1))


func _build_grid() -> void:
	dim = int(canvas / CELL) + 1
	_route_cache.clear()
	_astar = AStarGrid2D.new()
	_astar.region = Rect2i(0, 0, dim, dim)
	_astar.cell_size = Vector2(CELL, CELL)
	_astar.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_ALWAYS
	_astar.default_compute_heuristic = AStarGrid2D.HEURISTIC_EUCLIDEAN
	_astar.default_estimate_heuristic = AStarGrid2D.HEURISTIC_EUCLIDEAN
	_astar.update()
	var hazards := nodes_of("hazard_anchor")
	if hazards.is_empty():
		return
	for gy in range(dim):
		for gx in range(dim):
			if _cell_blocked(gx, gy, hazards):
				_astar.set_point_solid(Vector2i(gx, gy), true)


func _cell_blocked(gx: int, gy: int, hazards: Array) -> bool:
	var wpos := Vector2(gx, gy) * CELL
	var min_d := INF
	for h in hazards:
		min_d = min(min_d, wpos.distance_to(h))
	if min_d <= HAZARD_BLOCK_RADIUS:
		return true
	if min_d <= HAZARD_INFLUENCE_RADIUS:
		var r := RandomNumberGenerator.new()
		r.seed = seed_value ^ (gx * 92821) ^ (gy * 68917)
		return r.randf() < HAZARD_BLOCK_CHANCE
	return false

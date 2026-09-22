class_name Galaxy
extends RefCounted

var seed_used: int = 0
var systems: Array = []
var factions: Array = []
var edges: Array = []


func compute_hash() -> int:
	var h := 1469598103
	for sys in systems:
		h = _mix(h, sys.id)
		h = _mix(h, int(round(sys.pos.x * 100.0)))
		h = _mix(h, int(round(sys.pos.y * 100.0)))
		h = _mix(h, int(round(sys.pos.z * 100.0)))
		h = _mix(h, int(round(sys.significance * 1000.0)))
		h = _mix(h, sys.owner)
		h = _mix(h, sys.name.hash())
	for e in edges:
		h = _mix(h, e.a)
		h = _mix(h, e.b)
		h = _mix(h, e.kind.hash())
	for f in factions:
		h = _mix(h, f.id)
		h = _mix(h, f.name.hash())
		h = _mix(h, f.capital)
		h = _mix(h, int(round(f.hue * 1000.0)))
	return h


func _mix(h: int, v: int) -> int:
	return (h * 1099511628211) ^ v

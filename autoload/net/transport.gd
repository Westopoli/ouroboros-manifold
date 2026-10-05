extends RefCounted
# Packet transport used by the lockstep session (spec 2026-10-05, gd lane).
# Subclasses carry PackedByteArray datagrams between numbered endpoints.


func attach(_id: int) -> void:
	pass


func send(_from: int, _to: int, _data: PackedByteArray) -> void:
	pass


# Returns [{"from": int, "data": PackedByteArray}] in arrival order.
func poll(_id: int) -> Array:
	return []

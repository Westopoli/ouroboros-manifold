class_name GalaxyFlash
extends RefCounted

# R-106-04: war flashes from a delta frame. Built on the frame shape in docs/architecture.md;
# K-a's bridge feeds the real frame. Attacker side has no region in the delta (faction id only).


static func flashes_for_delta(delta: Dictionary) -> Array:
	var out: Array = []
	for a in delta.get("attacks", []):
		var kind := "conquest" if int(a.get("conquest", 0)) == 1 else "attack"
		out.append({"kind": kind, "region": int(a.get("target", -1))})
	for r in delta.get("revolts", []):
		out.append({"kind": "revolt", "region": int(r.get("region", -1))})
	return out

class_name UnknownLabel
extends RefCounted


static func text_for(owner_id: int, known_ids: Array) -> String:
	if owner_id < 0 or not known_ids.has(owner_id):
		return "Unknown"
	return "Faction %d" % owner_id


static func unknown_ids(owner_ids: Array, known_ids: Array) -> Array:
	var out: Array = []
	for o in owner_ids:
		var id := int(o)
		if (id < 0 or not known_ids.has(id)) and not out.has(id):
			out.append(id)
	return out

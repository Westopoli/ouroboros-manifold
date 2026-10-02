extends RefCounted

# Local ownership store {"owned": [era ids]} (A58 04). A debug build ignores it.


func owned_from_store(path: String, installed_ids: Array) -> Array:
	if not FileAccess.file_exists(path):
		return installed_ids.duplicate()
	var v = JSON.parse_string(FileAccess.get_file_as_string(path))
	var listed: Array = v.get("owned", []) if v is Dictionary else []
	var out := []
	for id in installed_ids:
		if id in listed:
			out.append(id)
	return out


func owned_ids(installed_ids: Array, path := "user://era_ownership.json") -> Array:
	if OS.is_debug_build():
		return installed_ids.duplicate()
	return owned_from_store(path, installed_ids)

extends RefCounted

# C transport v1 bridge (docs/architecture.md "C transport v1"). Loaded and
# instantiated directly (res://autoload/c_bridge.gd).new()), never as a
# project autoload. Parses a snapshot JSON file written by the sim and
# exposes it to callers without transmitting anything beyond the wire shape
# (no positions, no names — C5 rule).

var _snapshot: Dictionary = {}


func load_snapshot_file(path: String) -> bool:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return false
	var text := file.get_as_text()
	file.close()

	var parsed = JSON.parse_string(text)
	if not (parsed is Dictionary):
		return false
	if not parsed.has("regions"):
		return false

	_snapshot = parsed
	return true


func regions() -> Array:
	return _snapshot.get("regions", [])


func owner_of(i: int) -> int:
	for r in regions():
		if int(r.get("i", -999)) == i:
			return int(r.get("owner", -1))
	return -1


func checksum() -> int:
	return int(_snapshot.get("checksum", -1))


func edges() -> Array:
	return _snapshot.get("edges", [])

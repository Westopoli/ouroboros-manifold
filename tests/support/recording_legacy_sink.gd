extends RefCounted

# Recording stand-in for the legacy SimBridge autoload's command pipe (A77).
# SimBridge.send_command writes JSON lines to its _cmd_file; begin() swaps that
# handle for a scratch file, sent() reads back every command written, end()
# puts the original handle back. The autoload keeps its own script and state.
# Used by tests/test_chronicle_scene_open.gd: opening a scene sends no command.

var _root: Window
var _saved_file
var _path := ""
var _sink: FileAccess


static func begin(root: Window) -> RefCounted:
	var s = load("res://tests/support/recording_legacy_sink.gd").new()
	s._root = root
	var bridge: Node = root.get_node("SimBridge")
	s._saved_file = bridge.get("_cmd_file")
	s._path = "user://recording_legacy_sink_%d.jsonl" % Time.get_ticks_usec()
	s._sink = FileAccess.open(s._path, FileAccess.WRITE)
	bridge.set("_cmd_file", s._sink)
	return s


# Command names written through SimBridge.send_command since begin().
func sent() -> Array:
	var out: Array = []
	var f := FileAccess.open(_path, FileAccess.READ)
	if f == null:
		return out
	while not f.eof_reached():
		var line := f.get_line().strip_edges()
		if line == "":
			continue
		var d = JSON.parse_string(line)
		if d is Dictionary:
			out.append(str(d.get("cmd", d.get("name", d.get("type", "?")))))
	return out


func end() -> void:
	_root.get_node("SimBridge").set("_cmd_file", _saved_file)
	_sink = null
	DirAccess.remove_absolute(ProjectSettings.globalize_path(_path))

extends RefCounted

# Piece C2-6: the one pipe session of the run. Every scene that needs sim data
# asks SimSession.bridge() -- the same c_bridge.gd instance for the whole
# process, created on first use and never replaced -- so the world the galaxy
# steps is the world the briefing, debrief, chronicle and tactical scenes
# read, and it survives scene changes. Scenes never close the session. A
# static holder rather than a project autoload: it needs no project.godot
# line, and the bridge is pumped by whoever waits on it (its blocking
# requests) and by the galaxy's _process.
# See also: autoload/c_bridge.gd (the session itself), docs/architecture.md
# "persistent client session (v1.1)".

static var _bridge = null


static func bridge():
	if _bridge == null:
		_bridge = load("res://autoload/c_bridge.gd").new()
	return _bridge


# Closes the session and forgets the bridge (tests, and a new campaign).
static func reset() -> void:
	if _bridge != null:
		_bridge.close_session()
	_bridge = null

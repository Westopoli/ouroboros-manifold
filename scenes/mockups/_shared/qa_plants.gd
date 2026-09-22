static var _active: Dictionary = {}
static var _env_loaded := false


static func activate(id: String) -> void:
	_active[id] = true


static func is_active(id: String) -> bool:
	if not _env_loaded:
		_env_loaded = true
		for p in OS.get_environment("MOCKUP_PLANT").split(",", false):
			_active[p] = true
	return _active.has(id)


static func active() -> Array:
	return _active.keys()

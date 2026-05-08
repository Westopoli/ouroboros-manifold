extends Node

signal pause_changed(paused: bool)

var _holders: Dictionary = {}


func acquire(holder: String) -> void:
	var was_paused := is_paused()
	_holders[holder] = true
	if was_paused != is_paused():
		pause_changed.emit(is_paused())


func release(holder: String) -> void:
	if not _holders.has(holder):
		return
	var was_paused := is_paused()
	_holders.erase(holder)
	if was_paused != is_paused():
		pause_changed.emit(is_paused())


func is_paused() -> bool:
	return not _holders.is_empty()


func is_held_by(holder: String) -> bool:
	return _holders.has(holder)


func active_holders() -> Array:
	return _holders.keys()


func clear() -> void:
	if _holders.is_empty():
		return
	_holders.clear()
	pause_changed.emit(false)

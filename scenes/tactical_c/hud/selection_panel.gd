extends Control

# VG-A A7 (S-105): selection summary, ability ring, control groups 1..10 (digit 0 is 10), double-click same type.
# See also: tests/test_vg_a_selection_panel.gd. Frames come from set_frame (fixtures in tests, c_bridge in play).

signal selection_changed(ids: Array)
signal centre_requested(world: Vector2)

var _units := {}
var _profiles := {}
var _tick := 0
var _player := 0
var _visible := {}
var _selection: Array = []
var _groups := {}
var _last_digit := -1
var _readout := Label.new()


func _ready() -> void:
	add_child(_readout)


func set_frame(frame: Dictionary) -> void:
	_tick = int(frame.get("tick", _tick))
	_player = int(frame.get("player_faction", _player))
	_units.clear()
	for u in frame.get("units", []):
		_units[int(u["id"])] = u
	_profiles.clear()
	for p in frame.get("profiles", []):
		_profiles[int(p["type"])] = p
	_visible.clear()
	var vis: Dictionary = frame.get("visible", {})
	for id in vis.get(str(_player), []):
		_visible[int(id)] = true


func set_selection(ids: Array) -> void:
	_selection = ids.duplicate()
	_last_digit = -1
	_show_summary()
	selection_changed.emit(_selection)


# A19: the summary as a text readout, one "type xN" line per selected type, stacked upward from the selection count line.
func _show_summary() -> void:
	var names := {}
	for n in EraConfig.TYPE_IDS:
		names[EraConfig.TYPE_IDS[n]] = n
	var lines: PackedStringArray = []
	for row in summary():
		lines.append("%s x%d" % [names.get(int(row["type"]), "unit"), int(row["count"])])
	_readout.text = "\n".join(lines)
	_readout.position = Vector2(20.0, 1015.0 - 24.0 * lines.size())


func summary() -> Array:
	var counts := {}
	for id in _selection:
		if _units.has(id):
			var t := int(_units[id]["type"])
			counts[t] = int(counts.get(t, 0)) + 1
	var out := []
	var types := counts.keys()
	types.sort()
	for t in types:
		out.append({"type": t, "count": counts[t]})
	return out


func hp_fraction() -> float:
	var hp := 0.0
	var mx := 0.0
	for id in _selection:
		if _units.has(id):
			var u: Dictionary = _units[id]
			hp += float(u["hp"])
			mx += float(_profiles.get(int(u["type"]), {}).get("max_hp", 0.0))
	return hp / mx if mx > 0.0 else 0.0


func ability_slots() -> Array:
	var worst := {}
	for id in _selection:
		if not _units.has(id):
			continue
		var u: Dictionary = _units[id]
		var t := int(u["type"])
		var amax := float(_profiles.get(t, {}).get("acd_max", 0))
		var cd := 0.0
		if u.has("acd") and amax > 0.0:
			cd = clampf((float(u["acd"]) - _tick) / amax, 0.0, 1.0)
		worst[t] = maxf(float(worst.get(t, 0.0)), cd)
	var out := []
	var types := worst.keys()
	types.sort()
	for t in types:
		out.append({"type": t, "cooldown": worst[t]})
	return out


func bind_group(n: int, ids: Array) -> void:
	for k in _groups.keys():
		var kept := []
		for id in _groups[k]:
			if not ids.has(id):
				kept.append(id)
		if kept.is_empty():
			_groups.erase(k)
		else:
			_groups[k] = kept
	if not ids.is_empty():
		_groups[n] = ids.duplicate()


func group(n: int) -> Array:
	return _groups.get(n, []).duplicate()


func group_tabs() -> Array:
	var out := []
	var ns := _groups.keys()
	ns.sort()
	for n in ns:
		var ids: Array = _groups[n]
		var type := -1
		if _units.has(ids[0]):
			type = int(_units[ids[0]]["type"])
		out.append({"n": n, "type": type, "count": ids.size()})
	return out


# A second press of the digit whose group is already the selection centres on the group; no timing number is needed.
func press_digit(n: int, _t_ms: int) -> Dictionary:
	var ids := group(n)
	var centre = null
	if ids.is_empty():
		return {"selection": _selection.duplicate(), "centre": null}
	if _last_digit == n and _selection == ids:
		centre = _centroid(ids)
		centre_requested.emit(centre)
	else:
		set_selection(ids)
	_last_digit = n
	return {"selection": ids, "centre": centre}


func select_same_type(id: int) -> Array:
	var out := []
	if not _units.has(id):
		return out
	var t := int(_units[id]["type"])
	for k in _units.keys():
		var u: Dictionary = _units[k]
		if int(u["type"]) == t and int(u["faction"]) == _player and _visible.has(int(k)):
			out.append(int(k))
	out.sort()
	set_selection(out)
	return out


func _centroid(ids: Array) -> Variant:
	var sum := Vector2.ZERO
	var n := 0
	for id in ids:
		if _units.has(id):
			sum += Vector2(float(_units[id]["x"]), float(_units[id]["y"]))
			n += 1
	return sum / n if n > 0 else null


func _unhandled_key_input(event: InputEvent) -> void:
	var k := event as InputEventKey
	if k == null or not k.pressed or k.echo:
		return
	var n := -1
	if k.keycode >= KEY_1 and k.keycode <= KEY_9:
		n = k.keycode - KEY_0
	elif k.keycode == KEY_0:
		n = 10
	if n < 0:
		return
	if k.ctrl_pressed:
		bind_group(n, _selection)
	else:
		press_digit(n, Time.get_ticks_msec())

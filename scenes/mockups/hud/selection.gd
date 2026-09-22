extends RefCounted

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")

const PLAYER_FACTION := "player"
const RECALL_WINDOW_MS := 400

var selected: Array[int] = []
var groups: Dictionary = {}
var focus_layer: int = 1

var last_recall_digit: int = -1
var _last_recall_ms: int = -100000


func click(uid: int, units: Dictionary) -> void:
	selected.clear()
	if units.has(uid) and units[uid].faction == PLAYER_FACTION:
		selected.append(uid)


func shift_click(uid: int, units: Dictionary) -> void:
	if not units.has(uid) or units[uid].faction != PLAYER_FACTION:
		return
	var idx := selected.find(uid)
	if idx >= 0:
		selected.remove_at(idx)
	else:
		selected.append(uid)


func box(rect: Rect2, project: Callable, units: Dictionary) -> void:
	selected.clear()
	for uid in units:
		var rec: Dictionary = units[uid]
		if rec.faction != PLAYER_FACTION:
			continue
		if QaPlants.is_active("box-one-layer") and rec.layer != focus_layer:
			continue
		var p: Vector2 = project.call(uid)
		if rect.has_point(p):
			selected.append(uid)


func narrow(layer: int, units: Dictionary) -> void:
	var kept: Array[int] = []
	for uid in selected:
		if units.has(uid) and units[uid].layer == layer:
			kept.append(uid)
	selected = kept
	if QaPlants.is_active("narrow-moves-focus"):
		focus_layer = layer


func bind(digit: int, units: Dictionary) -> void:
	if selected.is_empty():
		return
	var members: Dictionary = {}
	for uid in selected:
		members[uid] = true
	if not QaPlants.is_active("group-shared"):
		for other in groups.keys():
			if other == digit:
				continue
			var filtered: Array[int] = []
			for uid in groups[other]:
				if not members.has(uid):
					filtered.append(uid)
			groups[other] = filtered
	groups[digit] = selected.duplicate()


func recall(digit: int, units: Dictionary, now_ms: int) -> Dictionary:
	var result := {"centre_requested": false, "centre": Vector2.ZERO}
	if not groups.has(digit):
		return result
	var live: Array[int] = []
	for uid in groups[digit]:
		if units.has(uid):
			live.append(uid)
	groups[digit] = live
	selected = live.duplicate()

	if digit == last_recall_digit and now_ms - _last_recall_ms <= RECALL_WINDOW_MS:
		result.centre_requested = true
		result.centre = _centroid(live, units)
	last_recall_digit = digit
	_last_recall_ms = now_ms
	return result


func commands() -> Array[String]:
	var cmds: Array[String] = ["click", "shift_click", "box", "narrow", "bind", "recall"]
	if QaPlants.is_active("select-all-exists"):
		cmds.append("select_all")
	return cmds


func prune_dead(units: Dictionary) -> void:
	var kept: Array[int] = []
	for uid in selected:
		if units.has(uid):
			kept.append(uid)
	selected = kept
	for digit in groups.keys():
		var filtered: Array[int] = []
		for uid in groups[digit]:
			if units.has(uid):
				filtered.append(uid)
		groups[digit] = filtered


func _centroid(uids: Array[int], units: Dictionary) -> Vector2:
	if uids.is_empty():
		return Vector2.ZERO
	var sum := Vector2.ZERO
	for uid in uids:
		sum += units[uid].pos
	return sum / uids.size()

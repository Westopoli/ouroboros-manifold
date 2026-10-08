class_name TerritoryTween
extends RefCounted

const DURATION_S := 2.0

var _tweens: Dictionary = {}


func start(region_id: int, old_owner: int, new_owner: int, now_s: float) -> void:
	_tweens[region_id] = {"old": old_owner, "new": new_owner, "t0": now_s}


func step(now_s: float) -> Array:
	var out: Array = []
	var done: Array = []
	var ids: Array = _tweens.keys()
	ids.sort()
	for region in ids:
		var tw: Dictionary = _tweens[region]
		var f: float = clampf((now_s - float(tw["t0"])) / DURATION_S, 0.0, 1.0)
		if f >= 1.0:
			out.append({"region": region, "owner": tw["new"], "scale": 1.0})
			done.append(region)
		else:
			out.append({"region": region, "owner": tw["old"], "scale": 1.0 - f})
			out.append({"region": region, "owner": tw["new"], "scale": f})
	for region in done:
		_tweens.erase(region)
	return out


func active_count() -> int:
	return _tweens.size()

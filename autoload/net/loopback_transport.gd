extends "res://autoload/net/transport.gd"
# In-process transport for tests: no real time, delay counted in receiver polls.

var _queues := {}       # id -> Array of {"from", "data", "wait"}
var _sent := {}         # "from:to" -> sends so far on that link
var _drop := {}         # "from:to" -> {index: true}
var _delay := {}        # "from:to" -> polls
var _reorder := {}      # "from:to" -> bool


func _key(from: int, to: int) -> String:
	return "%d:%d" % [from, to]


func attach(id: int) -> void:
	if not _queues.has(id):
		_queues[id] = []


func send(from: int, to: int, data: PackedByteArray) -> void:
	var k := _key(from, to)
	var idx: int = _sent.get(k, 0)
	_sent[k] = idx + 1
	if _drop.has(k) and _drop[k].has(idx):
		return
	if not _queues.has(to):
		return
	_queues[to].append({"from": from, "data": data, "wait": _delay.get(k, 0)})


func poll(id: int) -> Array:
	var out: Array = []
	if not _queues.has(id):
		return out
	var keep: Array = []
	for e in _queues[id]:
		if int(e["wait"]) <= 0:
			out.append(e)
		else:
			e["wait"] = int(e["wait"]) - 1
			keep.append(e)
	_queues[id] = keep
	var froms := {}
	for i in out.size():
		var f: int = out[i]["from"]
		if _reorder.get(_key(f, id), false):
			if not froms.has(f):
				froms[f] = []
			froms[f].append(i)
	for f in froms:
		var pos: Array = froms[f]
		var items: Array = []
		for p in pos:
			items.append(out[p])
		items.reverse()
		for j in pos.size():
			out[pos[j]] = items[j]
	var res: Array = []
	for e in out:
		res.append({"from": e["from"], "data": e["data"]})
	return res


func drop_indices(from: int, to: int, idxs: Array) -> void:
	var k := _key(from, to)
	if not _drop.has(k):
		_drop[k] = {}
	var base: int = _sent.get(k, 0)
	for i in idxs:
		_drop[k][base + int(i)] = true


func set_delay(from: int, to: int, polls: int) -> void:
	_delay[_key(from, to)] = polls


func set_reorder(from: int, to: int, on: bool) -> void:
	_reorder[_key(from, to)] = on

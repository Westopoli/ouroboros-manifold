extends RefCounted
# Lockstep session (spec 2026-10-05, gd lane; E-19 R-139-03, R-139-04, R-140-02 to R-140-04).
# No real time: everything advances on poll(). Each poll receives, sends one
# packet for the next tick, and releases at most one tick to the sim.

const REPEAT_DEFAULT := 5

var _local := 0
var _peers: Array = []      # sorted peer ids, local included
var _live: Array = []
var _net = null
var _sim = null
var _delay := 3
var _repeat := REPEAT_DEFAULT
var _stall_ticks := 0
var _drop_ticks := 0

var _sent := 0              # packets sent; "now"
var _released := 0          # ticks handed to the sim
var _seq := 0
var _cmds := {}             # peer -> {tick: {seq: cmd}}
var _covered := {}          # peer -> {tick: true}
var _silent := {}           # peer -> polls since its last packet
var _stalled := false
var _my_sums := {}          # tick -> sections
var _peer_sums := {}        # peer -> {tick: sections}
var _sum_ticks: Array = []  # recent own checksum ticks, for repetition
var _desync := {}


func setup(local_id: int, peer_ids: Array, transport, sim, opts: Dictionary) -> void:
	_local = local_id
	_peers = peer_ids.duplicate()
	_peers.sort()
	_live = _peers.duplicate()
	_net = transport
	_sim = sim
	_delay = int(opts.get("input_delay", 3))
	_repeat = int(opts.get("repeat", REPEAT_DEFAULT))
	_stall_ticks = int(opts.get("stall_ticks", 1000))
	_drop_ticks = int(opts.get("drop_ticks", 2000))
	for p in _peers:
		_cmds[p] = {}
		_covered[p] = {}
		_silent[p] = 0
		_peer_sums[p] = {}


func command(cmd: Dictionary) -> int:
	var stamp := _sent + _delay
	cmd["tick"] = stamp
	cmd["peer"] = _local
	cmd["seq"] = _seq
	_seq += 1
	if not _cmds[_local].has(stamp):
		_cmds[_local][stamp] = {}
	_cmds[_local][stamp][int(cmd["seq"])] = cmd
	return stamp


func is_stalled() -> bool:
	return _stalled


func live_peers() -> Array:
	return _live.duplicate()


func desync() -> Dictionary:
	return _desync


func poll() -> void:
	for p in _live:
		if p != _local:
			_silent[p] = int(_silent[p]) + 1
	for pkt in _net.poll(_local):
		_receive(int(pkt["from"]), pkt["data"])
	_send()
	_drop_silent()
	_release()


func _send() -> void:
	_sent += 1
	var n := _sent
	var cmds: Array = []
	for t in range(maxi(1, n - _repeat + 1), n + 1):
		if _cmds[_local].has(t):
			var by_seq: Dictionary = _cmds[_local][t]
			for s in by_seq:
				cmds.append([t, by_seq[s]])
	var sums: Array = []
	for t in _sum_ticks:
		sums.append([t, _my_sums[t]])
	var data := var_to_bytes([n, cmds, sums])
	for p in _peers:
		if p != _local:
			_net.send(_local, p, data)


func _receive(from: int, data: PackedByteArray) -> void:
	if not _cmds.has(from) or from == _local:
		return
	var pkt = bytes_to_var(data)
	if typeof(pkt) != TYPE_ARRAY or pkt.size() != 3:
		return
	_silent[from] = 0
	var n: int = pkt[0]
	for t in range(maxi(1, n - _repeat + 1), n + 1):
		if t > _released:
			_covered[from][t] = true
	for e in pkt[1]:
		var t: int = e[0]
		if t <= _released:
			continue
		if not _cmds[from].has(t):
			_cmds[from][t] = {}
		_cmds[from][t][int(e[1]["seq"])] = e[1]
	for r in pkt[2]:
		_peer_sums[from][int(r[0])] = r[1]
		_check(int(r[0]))


func _drop_silent() -> void:
	for p in _live.duplicate():
		if p != _local and int(_silent[p]) >= _drop_ticks:
			_live.erase(p)


func _ready_for(t: int) -> bool:
	if _sent < t:
		return false
	for p in _live:
		if p != _local and not _covered[p].has(t):
			return false
	return true


func _release() -> void:
	var t := _released + 1
	if not _ready_for(t):
		_stalled = false
		for p in _live:
			if p != _local and int(_silent[p]) >= _stall_ticks:
				_stalled = true
		return
	_stalled = false
	for p in _live:
		if _cmds[p].has(t):
			var by_seq: Dictionary = _cmds[p][t]
			var seqs: Array = by_seq.keys()
			seqs.sort()
			for s in seqs:
				_sim.submit(by_seq[s])
	for p in _peers:
		_cmds[p].erase(t)
		_covered[p].erase(t)
	var r: Dictionary = _sim.step()
	_released = t
	if r.has("sections"):
		_my_sums[t] = r["sections"]
		_sum_ticks.append(t)
		while _sum_ticks.size() > _repeat:
			_my_sums.erase(_sum_ticks.pop_front())
		_check(t)


func _check(t: int) -> void:
	if not _my_sums.has(t):
		return
	var mine: Array = _my_sums[t]
	for p in _peers:
		if p == _local or not _peer_sums[p].has(t):
			continue
		var theirs: Array = _peer_sums[p][t]
		for i in mini(mine.size(), theirs.size()):
			if mine[i] != theirs[i]:
				if _desync.is_empty() or t < int(_desync["tick"]):
					_desync = {"tick": t, "section": i}
				break

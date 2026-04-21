extends RefCounted

# Godot-side perf logger for Stage 8.5.
# Writes JSONL to logs/godot_perf.jsonl. Three event types:
#   - "snapshot": per full-snapshot arrival
#   - "delta":    per delta arrival with pos updates
#   - "periodic": every PERIODIC_INTERVAL_FRAMES, display-vs-buffer divergence
# See also: autoload/tactical_bridge.gd (wires this in).

const LOG_PATH := "/Users/westley/ouroboros/logs/godot_perf.jsonl"
const PERIODIC_INTERVAL_FRAMES := 30
const TOP_N_STOMPS := 10
const DIVERGENCE_THRESHOLD_WU := 5.0

var _file: FileAccess
var _frame_count: int = 0
var _enabled: bool = false


func _init() -> void:
	_file = FileAccess.open(LOG_PATH, FileAccess.WRITE)
	if _file == null:
		push_warning("TacticalPerfLogger: cannot open %s (err=%d)" % [LOG_PATH, FileAccess.get_open_error()])
		return
	_enabled = true
	_write({"event": "header", "format": "jsonl", "started_at": Time.get_unix_time_from_system()})


func _write(d: Dictionary) -> void:
	if not _enabled:
		return
	_file.store_line(JSON.stringify(d))
	_file.flush()


func log_snapshot(snap: Dictionary, disp_x: PackedFloat32Array, disp_y: PackedFloat32Array,
				  disp_alive: PackedByteArray, uc: int) -> void:
	if not _enabled:
		return
	var stomps: Array = []
	var backward := 0
	var forward := 0
	var stationary := 0
	for u in snap.get("units", []):
		var uid: int = int(u["uid"])
		if uid >= uc or disp_alive[uid] == 0:
			continue
		var pre_x: float = disp_x[uid]
		var pre_y: float = disp_y[uid]
		var new_x: float = float(u["pos"][0])
		var new_y: float = float(u["pos"][1])
		var dx: float = new_x - pre_x
		var dy: float = new_y - pre_y
		var dist: float = sqrt(dx * dx + dy * dy)
		# No velocity available in flat-array model at snapshot time — classify as stationary
		stationary += 1
		stomps.append({"uid": uid, "stomp_wu": dist, "backward": false, "vmag": 0.0})
	stomps.sort_custom(func(a, b): return a["stomp_wu"] > b["stomp_wu"])
	var mags: Array = []
	for s in stomps:
		mags.append(s["stomp_wu"])
	_write({
		"event": "snapshot",
		"tick": snap.get("tick", 0),
		"units": stomps.size(),
		"stomp_p50": _pct(mags, 0.5),
		"stomp_p95": _pct(mags, 0.95),
		"stomp_max": mags[0] if mags.size() > 0 else 0.0,
		"backward": backward,
		"forward": forward,
		"stationary": stationary,
		"top": stomps.slice(0, TOP_N_STOMPS),
	})


func log_delta(d: Dictionary, disp_x: PackedFloat32Array, disp_y: PackedFloat32Array,
			   disp_alive: PackedByteArray, uc: int) -> void:
	if not _enabled:
		return
	var stomps: Array = []
	var backward := 0
	var forward := 0
	for u in d.get("units_updated", []):
		if not u.has("pos"):
			continue
		var uid: int = int(u["uid"])
		if uid >= uc or disp_alive[uid] == 0:
			continue
		var pre_x: float = disp_x[uid]
		var pre_y: float = disp_y[uid]
		var new_x: float = float(u["pos"][0])
		var new_y: float = float(u["pos"][1])
		var dx: float = new_x - pre_x
		var dy: float = new_y - pre_y
		var dist: float = sqrt(dx * dx + dy * dy)
		forward += 1
		stomps.append({"uid": uid, "stomp_wu": dist, "backward": false, "vmag": 0.0})
	if stomps.size() == 0:
		return
	stomps.sort_custom(func(a, b): return a["stomp_wu"] > b["stomp_wu"])
	var mags: Array = []
	for s in stomps:
		mags.append(s["stomp_wu"])
	_write({
		"event": "delta",
		"tick": d.get("tick", 0),
		"pos_updates": stomps.size(),
		"stomp_p50": _pct(mags, 0.5),
		"stomp_p95": _pct(mags, 0.95),
		"stomp_max": mags[0] if mags.size() > 0 else 0.0,
		"backward": backward,
		"forward": forward,
		"top": stomps.slice(0, TOP_N_STOMPS),
	})


func log_frame(disp_x: PackedFloat32Array, disp_y: PackedFloat32Array,
			   disp_alive: PackedByteArray, uc: int,
			   latest_positions: PackedFloat32Array, current_tick: int) -> void:
	if not _enabled:
		return
	_frame_count += 1
	if _frame_count % PERIODIC_INTERVAL_FRAMES != 0:
		return
	var lag_count := 0
	var max_lag := 0.0
	var tracked := 0
	for uid in range(uc):
		if disp_alive[uid] == 0:
			continue
		tracked += 1
		var idx: int = uid * 2
		var dx: float = disp_x[uid] - latest_positions[idx]
		var dy: float = disp_y[uid] - latest_positions[idx + 1]
		var dist: float = sqrt(dx * dx + dy * dy)
		if dist > DIVERGENCE_THRESHOLD_WU:
			lag_count += 1
			if dist > max_lag:
				max_lag = dist
	_write({
		"event": "periodic",
		"tick": current_tick,
		"frame": _frame_count,
		"tracked": tracked,
		"interp_lag_count": lag_count,
		"max_lag_wu": max_lag,
	})


func _pct(values: Array, p: float) -> float:
	if values.size() == 0:
		return 0.0
	var s := values.duplicate()
	s.sort()
	var k: int = clamp(int(round(p * (s.size() - 1))), 0, s.size() - 1)
	return s[k]

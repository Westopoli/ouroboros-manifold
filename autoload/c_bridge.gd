extends RefCounted

# C transport v1 bridge (docs/architecture.md "C transport v1"). Loaded and
# instantiated directly (res://autoload/c_bridge.gd).new()), never as a
# project autoload. Parses a snapshot JSON file written by the sim and
# exposes it to callers without transmitting anything beyond the wire shape
# (no positions, no names — C5 rule).
#
# load_snapshot_live spawns pipe/ouroboros_pipe directly and talks the same
# 4-byte-big-endian-length-prefix + UTF-8 JSON framing sim_bridge.gd uses for
# reading (see autoload/sim_bridge.gd's header comment for the Godot 4.6
# stdio caveat, including that the pipe FileAccess only ever answers with
# whatever bytes are already queued — there is no non-blocking peek, so
# reads that wait on a frame that never comes would hang forever). Unlike
# sim_bridge.gd, om_pipe.c has no temp-file command channel — it reads
# commands framed on stdin only — so this writes its whole command script
# (set_seed, step n, snapshot, quit) to the bidirectional stdio handle in a
# single store_buffer call, then only reads afterward, never writing again.
# The script steps the sim LIVE_SNAPSHOT_STEPS ticks before requesting the
# snapshot so the checksum lands on the same post-step cadence
# tests/transport/test_pipe_shapes.py verifies via ctypes — a tick-0
# snapshot (no step) would carry a different checksum. A below-floor
# n_regions makes set_seed answer an error frame instead of silence
# (csrc/pipe/om_pipe.c write_error); the read loop below stops the instant
# it sees that frame and kills the process, so the already-queued step and
# snapshot commands are never acted on by the sim even though their bytes
# were sent.

const PIPE_BIN_RES_PATH := "res://pipe/ouroboros_pipe"
const LIVE_READ_TIMEOUT_MSEC := 5000
const LIVE_SNAPSHOT_STEPS := 10
const DEFAULT_N_REGIONS := 80
# Every strategic om_feature id (csrc/ouroboros_sim.h OM_FEAT_EVENTS ..
# OM_FEAT_LIFECYCLE); OM_FEAT_TACTICAL (8) stays off. With [6] alone nothing
# ever changes owner (docs/architecture.md "session commands (v1.1)").
const DEFAULT_FEATURES := [0, 1, 2, 3, 4, 5, 6, 7]

signal frame_received(frame)
signal snapshot_changed(tick)

var _snapshot: Dictionary = {}
var _region_index: Dictionary = {}
var _session_pid: int = -1
var _session_stdio: FileAccess = null
var _reader: Thread = null
var _mutex := Mutex.new()
var _queue: Array = []
var _last_error: String = ""
var _mission: Dictionary = {}
var _debrief: Dictionary = {}
var _chronicle: Dictionary = {}
var _chronicle_snapshot: Dictionary = {}
var _tactical: Dictionary = {}


func load_snapshot_file(path: String) -> bool:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return false
	var text := file.get_as_text()
	file.close()

	var parsed = JSON.parse_string(text)
	if not (parsed is Dictionary):
		return false
	if not parsed.has("regions"):
		return false

	_snapshot = parsed
	return true


func regions() -> Array:
	return _snapshot.get("regions", [])


func owner_of(i: int) -> int:
	for r in regions():
		if int(r.get("i", -999)) == i:
			return int(r.get("owner", -1))
	return -1


func checksum() -> int:
	return int(_snapshot.get("checksum", -1))


func edges() -> Array:
	return _snapshot.get("edges", [])


func snapshot() -> Dictionary:
	return _snapshot


func last_error() -> String:
	return _last_error


# The --seed user arg the game was launched with (the galaxy reads the same
# arg), 1 when absent.
func live_seed() -> int:
	var args := OS.get_cmdline_user_args()
	var idx := args.find("--seed")
	if idx == -1 or idx + 1 >= args.size():
		return 1
	return int(args[idx + 1])


func mission_frame() -> Dictionary:
	return _mission


func debrief_frame() -> Dictionary:
	return _debrief


func chronicle_frame() -> Dictionary:
	return _chronicle


func chronicle_snapshot() -> Dictionary:
	return _chronicle_snapshot


func tactical_frame() -> Dictionary:
	return _tactical


# Save slots (docs/architecture.md "Save slots (T2g-2 rulings)"): the slot
# directory is user://saves passed absolute; a slot id is the file name
# without ".omsave". The live mission/debrief/chronicle loads autosave to
# campaign_<seed> (R-111-01); the tactical load never does (R-111-04).
func saves_dir() -> String:
	var dir := ProjectSettings.globalize_path("user://saves")
	DirAccess.make_dir_recursive_absolute(dir)
	return dir


func list_saves() -> Array:
	var frames: Dictionary = _run_live_script(0, 0, [], [{"type": "cmd", "name": "list_saves", "dir": saves_dir()}], ["saves"], false)
	var rows := []
	for slot in frames.get("saves", {}).get("slots", []):
		rows.append({
			"slot": String(slot.get("path", "")).get_file().get_basename(),
			"tick": int(slot.get("tick", 0)),
			"chapter": int(slot.get("chapter", 0)),
			"version": int(slot.get("format_version", 0)),
		})
	return rows


# The post-load snapshot, or {} with last_error() set ("corrupt" covers a
# version mismatch too, csrc/pipe/om_pipe.c handle_load; R-111-03). The pipe
# can only load into a world with the save's region count, so the script
# sets that world up first from the sidecar's seed and n_regions.
func load(slot_id: String) -> Dictionary:
	var path := saves_dir().path_join(slot_id + ".omsave")
	var sidecar = JSON.parse_string(FileAccess.get_file_as_string(path + ".json"))
	if not (sidecar is Dictionary) or not sidecar.has("seed") or not sidecar.has("n_regions"):
		_last_error = "save sidecar missing or unreadable"
		return {}
	var frames: Dictionary = _run_live_script(int(sidecar["seed"]), int(sidecar["n_regions"]), DEFAULT_FEATURES,
		[{"type": "cmd", "name": "load", "path": path}], ["snapshot"])
	return frames.get("snapshot", {})


func _autosave_cmd(seed: int) -> Dictionary:
	return {"type": "cmd", "name": "save", "path": saves_dir().path_join("campaign_%d.omsave" % seed)}


# Persistent session (docs/architecture.md "persistent client session
# (v1.1)"): one pipe process for the whole run. A reader Thread decodes
# frames into a mutex-guarded queue (reads block, so they cannot run on the
# main thread), pump() applies them in order on the main thread (the owning
# scene calls it from its _process; this RefCounted has no _process), and
# writes happen on the main thread only. A delta is merged into the current
# snapshot in place: region rows by index, faction rows by id, the tick, and
# the checksum on the cadence ticks that carry one (kept from the last
# cadence tick otherwise). Deltas carry no edges, so the edge list is the one
# the last snapshot frame had; request a snapshot to refresh it. Replies are
# not matched against a FIFO of sent commands: an error frame names its
# command and sets last_error(), every other frame is announced through
# frame_received for whoever awaits that type. The owner must call
# close_session() (a RefCounted cannot do it from its own destructor).
func open_session(seed: int, n_regions: int, features: Array) -> bool:
	close_session()
	_last_error = ""
	var exe := ProjectSettings.globalize_path(PIPE_BIN_RES_PATH)
	if not FileAccess.file_exists(exe):
		_last_error = "pipe binary missing"
		return false
	var result: Dictionary = OS.execute_with_pipe(exe, PackedStringArray())
	if result.is_empty() or not result.has("pid"):
		_last_error = "pipe spawn failed"
		return false
	_session_pid = result["pid"]
	_session_stdio = result.get("stdio") as FileAccess
	if _session_stdio == null:
		close_session()
		_last_error = "pipe has no stdio"
		return false
	_snapshot = {}
	_region_index = {}
	_mutex.lock()
	_queue = []
	_mutex.unlock()
	_reader = Thread.new()
	_reader.start(_reader_loop)
	send_command({"type": "cmd", "name": "set_seed", "seed": seed, "n_regions": n_regions, "features": features})
	send_command({"type": "cmd", "name": "snapshot"})
	return true


func send_command(cmd: Dictionary) -> void:
	if _session_stdio != null:
		_session_stdio.store_buffer(_frame_cmd(cmd))


func step(n: int) -> void:
	send_command({"type": "cmd", "name": "step", "n": n})


func pump() -> int:
	_mutex.lock()
	var frames: Array = _queue
	_queue = []
	_mutex.unlock()
	for frame in frames:
		var changed := false
		match String(frame.get("type", "")):
			"snapshot":
				_snapshot = frame
				_region_index = {}
				var rows: Array = _snapshot.get("regions", [])
				for idx in range(rows.size()):
					_region_index[int(rows[idx].get("i", -1))] = idx
				changed = true
			"delta":
				_apply_delta(frame)
				changed = true
			"error":
				_last_error = String(frame.get("reason", ""))
		frame_received.emit(frame)
		if changed:
			snapshot_changed.emit(int(_snapshot.get("tick", 0)))
	return frames.size()


func close_session() -> void:
	if _session_pid > 0 and OS.is_process_running(_session_pid):
		OS.kill(_session_pid)
	if _reader != null:
		_reader.wait_to_finish()
		_reader = null
	_session_pid = -1
	_session_stdio = null


func _reader_loop() -> void:
	while true:
		var msg: Variant = _read_live_frame(_session_stdio)
		if msg == null:
			return
		_mutex.lock()
		_queue.append(msg)
		_mutex.unlock()


func _apply_delta(delta: Dictionary) -> void:
	if _snapshot.is_empty():
		return
	var rows: Array = _snapshot.get("regions", [])
	for row in delta.get("regions", []):
		var idx: int = _region_index.get(int(row.get("i", -1)), -1)
		if idx >= 0:
			(rows[idx] as Dictionary).merge(row, true)
	var factions: Array = _snapshot.get("factions", [])
	for row in delta.get("factions", []):
		for f in factions:
			if int(f.get("id", -1)) == int(row.get("id", -2)):
				(f as Dictionary).merge(row, true)
	_snapshot["tick"] = delta.get("tick", _snapshot.get("tick", 0))
	var checksum: int = int(delta.get("checksum", 0))
	if checksum != 0:
		_snapshot["checksum"] = checksum


# Same script-up-front pattern as load_snapshot_live (a blocking pipe read
# cannot be interleaved with writes): a fresh world, 10 steps, mission_start
# answers the mission frame.
func load_mission_live(seed: int, n_regions: int, features: Array) -> bool:
	_mission = {}
	var frames: Dictionary = _run_live_script(seed, n_regions, features,
		[{"type": "cmd", "name": "mission_start", "faction": 0}, _autosave_cmd(seed)], ["mission", "ack:save"])
	if frames.is_empty():
		return false
	_mission = frames["mission"]
	return true


# ... and mission_end after it answers the debrief frame.
func load_debrief_live(seed: int, n_regions: int, features: Array) -> bool:
	_debrief = {}
	var frames: Dictionary = _run_live_script(seed, n_regions, features,
		[{"type": "cmd", "name": "mission_start", "faction": 0}, {"type": "cmd", "name": "mission_end"}, _autosave_cmd(seed)], ["debrief", "ack:save"])
	if frames.is_empty():
		return false
	_debrief = frames["debrief"]
	return true


# ... and a 50-tick jump after it answers the chronicle frame, then a
# snapshot of the world after the jump.
func load_chronicle_live(seed: int, n_regions: int, features: Array) -> bool:
	_chronicle = {}
	_chronicle_snapshot = {}
	var frames: Dictionary = _run_live_script(seed, n_regions, features,
		[{"type": "cmd", "name": "jump", "ticks": 50}, _autosave_cmd(seed)], ["chronicle", "snapshot", "ack:save"])
	if frames.is_empty():
		return false
	_chronicle = frames["chronicle"]
	_chronicle_snapshot = frames["snapshot"]
	return true


# ... and mission_start plus one tactical_step answers the first tactical
# frame (a static first frame: units moving over time needs C2-4's
# persistent session).
func load_tactical_live(seed: int, n_regions: int, features: Array) -> bool:
	_tactical = {}
	var frames: Dictionary = _run_live_script(seed, n_regions, features,
		[{"type": "cmd", "name": "mission_start", "faction": 0}, {"type": "cmd", "name": "tactical_step", "n": 1}], ["tactical"])
	if frames.is_empty():
		return false
	_tactical = frames["tactical"]
	return true


# See also: load_snapshot_live above, the v1 stopgap that goes when C2-4's
# persistent session lands; this shares its framing and read loop, and
# returns the first frame of each type in want ({type: frame}); {} on any
# error frame, timeout, closed pipe or spawn failure, with last_error() set.
# An ack is keyed "ack:<command name>"; with_world false skips the leading
# set_seed and step for commands that need no world (list_saves, load).
func _run_live_script(seed: int, n_regions: int, features: Array, tail: Array, want: Array, with_world: bool = true) -> Dictionary:
	_last_error = ""
	var exe := ProjectSettings.globalize_path(PIPE_BIN_RES_PATH)
	if not FileAccess.file_exists(exe):
		_last_error = "pipe binary missing"
		return {}
	var result: Dictionary = OS.execute_with_pipe(exe, PackedStringArray())
	if result.is_empty() or not result.has("pid"):
		_last_error = "pipe spawn failed"
		return {}
	var pid: int = result["pid"]
	var stdio: FileAccess = result.get("stdio") as FileAccess
	if stdio == null:
		if OS.is_process_running(pid):
			OS.kill(pid)
		_last_error = "pipe has no stdio"
		return {}

	var script := PackedByteArray()
	if with_world:
		script.append_array(_frame_cmd({"type": "cmd", "name": "set_seed", "seed": seed, "n_regions": n_regions, "features": features}))
		script.append_array(_frame_cmd({"type": "cmd", "name": "step", "n": LIVE_SNAPSHOT_STEPS}))
	for cmd in tail:
		script.append_array(_frame_cmd(cmd))
	script.append_array(_frame_cmd({"type": "cmd", "name": "quit"}))
	stdio.store_buffer(script)

	var found: Dictionary = {}
	var deadline_msec := Time.get_ticks_msec() + LIVE_READ_TIMEOUT_MSEC
	while Time.get_ticks_msec() < deadline_msec:
		var msg: Variant = _read_live_frame(stdio)
		if msg == null:
			_last_error = "pipe closed before every wanted frame (%s)" % ", ".join(want)
			break
		if not (msg is Dictionary):
			continue
		var msg_type: String = msg.get("type", "")
		if msg_type == "error":
			_last_error = String(msg.get("reason", ""))
			break
		var key: String = msg_type if msg_type != "ack" else "ack:%s" % msg.get("name", "")
		if want.has(key) and not found.has(key):
			found[key] = msg
			if found.size() == want.size():
				break

	if OS.is_process_running(pid):
		OS.kill(pid)
	if found.size() != want.size():
		if _last_error == "":
			_last_error = "timed out waiting for %s" % ", ".join(want)
		return {}
	return found


# The pipe's stdio FileAccess.get_buffer() blocks at the OS level when no
# bytes are queued (there is no non-blocking peek available here), so
# set_seed, step, snapshot and quit are all written up front in one buffer,
# exactly as before, and the reply is classified frame by frame instead of
# holding step/snapshot back: the pipe writes an unsolicited "hello" frame
# on startup (skipped), then either an error frame ({"type":"error",
# "name":"set_seed","reason":...}, csrc/pipe/om_pipe.c write_error) if
# n_regions is below the feasibility floor for the requested faction count,
# or nothing at all for set_seed on success (om_pipe.c handle_set_seed
# comment: "no frame at all on success, not even an ack") before the
# step/snapshot replies arrive. Reading stops the instant an error frame is
# seen -- the process is killed immediately after, so step/snapshot/quit are
# never acted on by the sim even though their bytes were already queued on
# its stdin.
func load_snapshot_live(seed: int, n_regions: int, features: Array, steps: int = LIVE_SNAPSHOT_STEPS) -> bool:
	_last_error = ""
	var exe := ProjectSettings.globalize_path(PIPE_BIN_RES_PATH)
	if not FileAccess.file_exists(exe):
		return false

	var result: Dictionary = OS.execute_with_pipe(exe, PackedStringArray())
	if result.is_empty() or not result.has("pid"):
		return false

	var pid: int = result["pid"]
	var stdio: FileAccess = result.get("stdio") as FileAccess
	if stdio == null:
		if OS.is_process_running(pid):
			OS.kill(pid)
		return false

	var script := PackedByteArray()
	script.append_array(_frame_cmd({"type": "cmd", "name": "set_seed", "seed": seed, "n_regions": n_regions, "features": features}))
	if steps > 0:
		script.append_array(_frame_cmd({"type": "cmd", "name": "step", "n": steps}))
	script.append_array(_frame_cmd({"type": "cmd", "name": "snapshot"}))
	script.append_array(_frame_cmd({"type": "cmd", "name": "quit"}))

	stdio.store_buffer(script)
	if stdio.get_error() != OK:
		if OS.is_process_running(pid):
			OS.kill(pid)
		return false

	var snapshot_msg: Variant = null
	var failed := false
	var deadline_msec := Time.get_ticks_msec() + LIVE_READ_TIMEOUT_MSEC
	while Time.get_ticks_msec() < deadline_msec:
		var msg: Variant = _read_live_frame(stdio)
		if msg == null:
			break
		if not (msg is Dictionary):
			continue
		var msg_type: String = msg.get("type", "")
		if msg_type == "error":
			_last_error = String(msg.get("reason", ""))
			failed = true
			break
		if msg_type == "snapshot":
			snapshot_msg = msg
			break

	if OS.is_process_running(pid):
		OS.kill(pid)

	if failed:
		return false
	if not (snapshot_msg is Dictionary) or not snapshot_msg.has("regions"):
		return false
	var regions_arr: Array = snapshot_msg.get("regions", [])
	if regions_arr.is_empty():
		return false

	_snapshot = snapshot_msg
	return true


func _frame_cmd(cmd: Dictionary) -> PackedByteArray:
	var body := JSON.stringify(cmd).to_utf8_buffer()
	var n := body.size()
	var framed := PackedByteArray()
	framed.push_back((n >> 24) & 0xFF)
	framed.push_back((n >> 16) & 0xFF)
	framed.push_back((n >> 8) & 0xFF)
	framed.push_back(n & 0xFF)
	framed.append_array(body)
	return framed


func _read_live_frame(stdio: FileAccess) -> Variant:
	var header := PackedByteArray()
	while header.size() < 4:
		var chunk: PackedByteArray = stdio.get_buffer(4 - header.size())
		if chunk.size() > 0:
			header.append_array(chunk)
		elif stdio.eof_reached():
			return null
		elif stdio.get_error() != OK:
			return null
		else:
			OS.delay_msec(5)

	var length: int = (header[0] << 24) | (header[1] << 16) | (header[2] << 8) | header[3]
	if length <= 0 or length > 10 * 1024 * 1024:
		return null

	var body := PackedByteArray()
	while body.size() < length:
		var chunk: PackedByteArray = stdio.get_buffer(length - body.size())
		if chunk.size() > 0:
			body.append_array(chunk)
		elif stdio.eof_reached():
			return null
		elif stdio.get_error() != OK:
			return null
		else:
			OS.delay_msec(5)

	var text := body.get_string_from_utf8()
	var json := JSON.new()
	if json.parse(text) != OK:
		return null
	var data: Variant = json.get_data()

	# om_pipe.c writes "checksum" as a decimal uint64 (jb_uint, om_pipe.c).
	# Godot's JSON parser has no uint64/int64-overflow-safe integer type: a
	# literal above INT64_MAX (as the real checksum here is) silently
	# round-trips through a double first, which is nowhere near precise
	# enough to hold a 19-20 digit integer, then int()-casting that garbled
	# double saturates to INT64_MIN. Re-read the checksum digits straight
	# off the wire text and store the exact value as its int64 two's-
	# complement bit pattern instead (the same bits the C uint64_t has),
	# since GDScript has no native unsigned 64-bit type to hold it directly.
	# "delta" frames carry the same "checksum" field (nonzero on cadence
	# ticks, per docs/architecture.md "C transport v1"), so the same
	# precision-loss bug and fix apply there too.
	if data is Dictionary and (data.get("type", "") == "snapshot" or data.get("type", "") == "delta"):
		var raw_checksum := _extract_raw_checksum(text)
		if raw_checksum != "":
			data["checksum"] = _decimal_to_i64(raw_checksum)

	return data


func _extract_raw_checksum(text: String) -> String:
	var re := RegEx.new()
	re.compile("\"checksum\"\\s*:\\s*(-?\\d+)")
	var m := re.search(text)
	if m == null:
		return ""
	return m.get_string(1)


const _INT64_MAX_STR := "9223372036854775807"
const _UINT64_MOD_STR := "18446744073709551616"  # 2^64


func _decimal_to_i64(s: String) -> int:
	if s.is_empty():
		return -1
	if not _decimal_gt(s, _INT64_MAX_STR):
		return int(s)
	# s is in (INT64_MAX, 2^64): the int64 bit pattern equals s - 2^64,
	# computed as -(2^64 - s) via string subtraction (both fit in int64).
	return -int(_decimal_sub(_UINT64_MOD_STR, s))


func _decimal_gt(a: String, b: String) -> bool:
	if a.length() != b.length():
		return a.length() > b.length()
	return a > b


func _decimal_sub(a: String, b: String) -> String:
	# a - b, decimal digit strings, a >= b >= 0.
	var ai := a.length() - 1
	var bi := b.length() - 1
	var borrow := 0
	var digits := PackedStringArray()
	while ai >= 0:
		var da := a.unicode_at(ai) - 48
		var db := (b.unicode_at(bi) - 48) if bi >= 0 else 0
		var d := da - db - borrow
		if d < 0:
			d += 10
			borrow = 1
		else:
			borrow = 0
		digits.append(str(d))
		ai -= 1
		bi -= 1
	digits.reverse()
	var result := "".join(digits)
	var start := 0
	while start < result.length() - 1 and result[start] == "0":
		start += 1
	return result.substr(start)

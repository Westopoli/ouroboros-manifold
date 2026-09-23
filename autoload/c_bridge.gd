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
# stdio caveat). Unlike sim_bridge.gd, om_pipe.c has no temp-file command
# channel — it reads commands framed on stdin only — so this writes its
# whole command script to the bidirectional stdio handle in a single
# store_buffer call, then only reads afterward, never writing again. The
# script steps the sim LIVE_SNAPSHOT_STEPS ticks before requesting the
# snapshot (set_seed, step n, snapshot, quit) so the checksum lands on the
# same post-step cadence tests/transport/test_pipe_shapes.py verifies via
# ctypes — a tick-0 snapshot (no step) would carry a different checksum.

const PIPE_BIN_RES_PATH := "res://pipe/ouroboros_pipe"
const LIVE_READ_TIMEOUT_MSEC := 5000
const LIVE_SNAPSHOT_STEPS := 10

var _snapshot: Dictionary = {}


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


func load_snapshot_live(seed: int, n_regions: int, features: Array, steps: int = LIVE_SNAPSHOT_STEPS) -> bool:
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
	var deadline_msec := Time.get_ticks_msec() + LIVE_READ_TIMEOUT_MSEC
	while Time.get_ticks_msec() < deadline_msec:
		var msg: Variant = _read_live_frame(stdio)
		if msg == null:
			break
		if msg is Dictionary and msg.get("type", "") == "snapshot":
			snapshot_msg = msg
			break

	if OS.is_process_running(pid):
		OS.kill(pid)

	if not (snapshot_msg is Dictionary) or not snapshot_msg.has("regions"):
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

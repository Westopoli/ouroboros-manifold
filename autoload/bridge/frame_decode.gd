extends RefCounted
# Wire-level helpers of autoload/c_bridge.gd (plain script, preloaded there): frame encode and decode, exact uint64 checksums.

static func frame_cmd(cmd: Dictionary) -> PackedByteArray:
	var body := JSON.stringify(cmd).to_utf8_buffer()
	var n := body.size()
	var framed := PackedByteArray()
	framed.push_back((n >> 24) & 0xFF)
	framed.push_back((n >> 16) & 0xFF)
	framed.push_back((n >> 8) & 0xFF)
	framed.push_back(n & 0xFF)
	framed.append_array(body)
	return framed


static func read_live_frame(stdio: FileAccess) -> Variant:
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
		var raw_checksum := extract_raw_checksum(text)
		if raw_checksum != "":
			data["checksum"] = decimal_to_i64(raw_checksum)
	elif data is Dictionary and data.get("type", "") == "net_ack":
		# net_ack carries uint64 words too (R-139-04): checksum and every sections entry, read as int64 bit patterns.
		var raw_ack := extract_raw_checksum(text)
		if raw_ack != "":
			data["checksum"] = decimal_to_i64(raw_ack)
		var secs := extract_raw_sections(text)
		if not secs.is_empty():
			var words: Array = []
			for w in secs:
				words.append(decimal_to_i64(w))
			data["sections"] = words

	return data


static func extract_raw_sections(text: String) -> PackedStringArray:
	var out := PackedStringArray()
	var re := RegEx.new()
	re.compile("\"sections\"\\s*:\\s*\\[([^\\]]*)\\]")
	var m := re.search(text)
	if m == null:
		return out
	for part in m.get_string(1).split(",", false):
		out.append(part.strip_edges())
	return out


static func extract_raw_checksum(text: String) -> String:
	var re := RegEx.new()
	re.compile("\"checksum\"\\s*:\\s*(-?\\d+)")
	var m := re.search(text)
	if m == null:
		return ""
	return m.get_string(1)


const _INT64_MAX_STR := "9223372036854775807"
const _UINT64_MOD_STR := "18446744073709551616"  # 2^64


static func decimal_to_i64(s: String) -> int:
	if s.is_empty():
		return -1
	if not decimal_gt(s, _INT64_MAX_STR):
		return int(s)
	# s is in (INT64_MAX, 2^64): the int64 bit pattern equals s - 2^64,
	# computed as -(2^64 - s) via string subtraction (both fit in int64).
	return -int(decimal_sub(_UINT64_MOD_STR, s))


static func decimal_gt(a: String, b: String) -> bool:
	if a.length() != b.length():
		return a.length() > b.length()
	return a > b


static func decimal_sub(a: String, b: String) -> String:
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

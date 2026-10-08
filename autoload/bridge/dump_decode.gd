extends RefCounted
# Once-per-mission dump decoders of autoload/c_bridge.gd (plain script, preloaded there).

static func decode_heights(hex: String) -> PackedInt32Array:
	var raw := hex.hex_decode()
	var out := PackedInt32Array()
	for i in range(raw.size() / 4):
		out.append(raw.decode_s32(i * 4))
	return out


static func terrain_from_frame(f: Dictionary) -> Dictionary:
	return {
		"cells_w": int(f.get("cells_w", 0)),
		"cells_h": int(f.get("cells_h", 0)),
		"bands": String(f.get("bands", "")).hex_decode(),
		"walkable": String(f.get("walkable", "")).hex_decode(),
		"slopes": f.get("slopes", []),
		"heights": decode_heights(String(f.get("heights", ""))),
	}

class_name GroundBands
extends RefCounted

const BAND_COLOURS := [Color(0.40, 0.72, 0.42), Color(0.72, 0.80, 0.38), Color(0.90, 0.68, 0.30), Color(0.72, 0.48, 0.30), Color(0.92, 0.90, 0.88)]
const STEEP_COLOUR := Color(0.85, 0.10, 0.85)
const STEEP_MIX := 0.5


static func colour(band: int, walkable: bool) -> Color:
	var c: Color = BAND_COLOURS[clampi(band, 1, 5) - 1]
	return c if walkable else c.lerp(STEEP_COLOUR, STEEP_MIX)


static func cell_colours(terrain: Dictionary) -> PackedColorArray:
	var bands: PackedByteArray = terrain["bands"]
	var walk: PackedByteArray = terrain["walkable"]
	var out := PackedColorArray()
	out.resize(bands.size())
	for i in bands.size():
		out[i] = colour(bands[i], walk[i] != 0)
	return out

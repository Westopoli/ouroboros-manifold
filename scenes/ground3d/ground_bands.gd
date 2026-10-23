class_name GroundBands
extends RefCounted

const GROUND_COLOUR := Color(0.40, 0.72, 0.42)  # DRAFT-ground-colour
const STEEP_COLOUR := Color(0.85, 0.10, 0.85)
const STEEP_MIX := 0.5


static func colour(band: int, walkable: bool) -> Color:
	return GROUND_COLOUR if walkable else GROUND_COLOUR.lerp(STEEP_COLOUR, STEEP_MIX)


static func cell_colours(terrain: Dictionary) -> PackedColorArray:
	var bands: PackedByteArray = terrain["bands"]
	var walk: PackedByteArray = terrain["walkable"]
	var out := PackedColorArray()
	out.resize(bands.size())
	for i in bands.size():
		out[i] = colour(bands[i], walk[i] != 0)
	return out

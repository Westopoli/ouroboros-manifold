extends Node

signal band_changed(new_band: String, old_band: String)

var overview_min := 75.0
var overview_regional_blend := 65.0
var regional_min := 40.0
var regional_local_blend := 25.0

var current_band: String = "regional"
var blend_factor: float = 0.0
var blend_direction: String = "none"


func update_from_distance(dist: float) -> void:
	var old_band := current_band

	if dist >= overview_min:
		current_band = "overview"
		blend_factor = 0.0
		blend_direction = "none"
	elif dist >= overview_regional_blend:
		current_band = "overview"
		blend_factor = 1.0 - (dist - overview_regional_blend) / (overview_min - overview_regional_blend)
		blend_direction = "down"
	elif dist >= regional_min:
		current_band = "regional"
		blend_factor = 0.0
		blend_direction = "none"
	elif dist >= regional_local_blend:
		current_band = "regional"
		blend_factor = 1.0 - (dist - regional_local_blend) / (regional_min - regional_local_blend)
		blend_direction = "down"
	else:
		current_band = "local"
		blend_factor = 0.0
		blend_direction = "none"

	if old_band != current_band:
		band_changed.emit(current_band, old_band)

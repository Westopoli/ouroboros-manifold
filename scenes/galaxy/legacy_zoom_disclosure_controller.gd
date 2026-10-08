extends Node

# Copied from scenes/shared/world_view/zoom_disclosure_controller.gd
# (2026-09-22) for the pass-2 galaxy mockup. Thresholds reconciled with pass
# 1's own band math (galaxy_view.gd's _band_weights() and orbit_camera.gd's
# BAND_SPLIT_LOW/HIGH): 25/40/65/75 are exactly the numbers _band_weights()
# already used, and their midpoints (32.5, 70) are exactly BAND_SPLIT_LOW/
# HIGH — so this drives filament/shell alpha through the same three bands
# (Overview/Regional/Local) the camera and HUD already report, just lower-
# cased to match this controller's own band-name convention.

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
